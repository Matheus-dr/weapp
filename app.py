"""
Meus Filmes - avaliação pessoal de filmes
Backend Flask.

Funciona com dois bancos, escolhidos automaticamente:
- SQLite local (movies.db) -> quando NÃO existe a variável de ambiente DATABASE_URL.
  Uso: rodar na sua rede local, sem nuvem.
- PostgreSQL na nuvem -> quando existe DATABASE_URL (ex: Neon, Supabase, Render Postgres).
  Uso: hospedar o app na internet com dados persistentes de verdade.

Login (opcional): se as variáveis APP_USERNAME e APP_PASSWORD estiverem definidas,
o app pede usuário/senha (HTTP Basic Auth) antes de liberar qualquer acesso.
Se não estiverem definidas, o app fica aberto (bom para uso só na rede local).
"""
from flask import Flask, request, jsonify, send_from_directory, Response
from functools import wraps
import os
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "movies.db")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "").strip()

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_PG = bool(DATABASE_URL)

if IS_PG:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

APP_USERNAME = os.environ.get("APP_USERNAME", "").strip()
APP_PASSWORD = os.environ.get("APP_PASSWORD", "").strip()
AUTH_ENABLED = bool(APP_USERNAME and APP_PASSWORD)

app = Flask(__name__, static_folder="static", static_url_path="/static")


# ---------- Login (HTTP Basic Auth) ----------

def check_auth(username, password):
    return username == APP_USERNAME and password == APP_PASSWORD


def authenticate():
    return Response(
        "Acesso restrito. Informe usuário e senha para continuar.",
        401,
        {"WWW-Authenticate": 'Basic realm="Meus Filmes"'},
    )


@app.before_request
def require_auth():
    if not AUTH_ENABLED:
        return  # sem credenciais configuradas -> app aberto (uso local na rede)
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()


# ---------- Banco de dados (SQLite local OU Postgres na nuvem) ----------

def get_db():
    if IS_PG:
        return psycopg2.connect(DATABASE_URL)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_cursor(conn):
    if IS_PG:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


def ph(sql):
    """Converte placeholders '?' (estilo SQLite) para '%s' (estilo Postgres)."""
    return sql.replace("?", "%s") if IS_PG else sql


def row_to_dict(row):
    return dict(row)


def init_db():
    conn = get_db()
    cur = get_cursor(conn)
    if IS_PG:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                year TEXT,
                imdb_id TEXT,
                poster_url TEXT,
                synopsis TEXT,
                genre TEXT,
                is_horror INTEGER DEFAULT 0,
                roteiro REAL,
                historia REAL,
                trilha_sonora REAL,
                final REAL,
                plot_twist REAL,
                medo REAL,
                average REAL,
                created_at TEXT
            )
            """
        )
    else:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year TEXT,
                imdb_id TEXT,
                poster_url TEXT,
                synopsis TEXT,
                genre TEXT,
                is_horror INTEGER DEFAULT 0,
                roteiro REAL,
                historia REAL,
                trilha_sonora REAL,
                final REAL,
                plot_twist REAL,
                medo REAL,
                average REAL,
                created_at TEXT
            )
            """
        )
    conn.commit()
    conn.close()


init_db()


# ---------- Páginas ----------

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------- Busca de filmes (OMDb) ----------

@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    if not OMDB_API_KEY:
        return jsonify({
            "results": [],
            "error": "OMDB_API_KEY não configurada. Veja o README, ou use 'Adicionar manualmente'."
        }), 200
    try:
        resp = requests.get(
            "https://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "s": q, "type": "movie"},
            timeout=8,
        )
        data = resp.json()
    except requests.RequestException:
        return jsonify({"results": [], "error": "Falha ao contatar a OMDb. Verifique sua internet."}), 200

    if data.get("Response") == "False":
        return jsonify({"results": [], "error": data.get("Error")})

    results = [
        {
            "imdb_id": m["imdbID"],
            "title": m["Title"],
            "year": m["Year"],
            "poster": m["Poster"] if m.get("Poster") != "N/A" else None,
        }
        for m in data.get("Search", [])
    ]
    return jsonify({"results": results})


@app.route("/api/movie/<imdb_id>")
def movie_detail(imdb_id):
    if not OMDB_API_KEY:
        return jsonify({"error": "OMDB_API_KEY não configurada"}), 400
    try:
        resp = requests.get(
            "https://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "full"},
            timeout=8,
        )
        data = resp.json()
    except requests.RequestException:
        return jsonify({"error": "Falha ao contatar a OMDb."}), 502

    if data.get("Response") == "False":
        return jsonify({"error": data.get("Error")}), 404

    genre = data.get("Genre", "") or ""
    is_horror = "horror" in genre.lower() or "terror" in genre.lower()

    return jsonify({
        "imdb_id": imdb_id,
        "title": data.get("Title"),
        "year": data.get("Year"),
        "poster": data.get("Poster") if data.get("Poster") != "N/A" else None,
        "synopsis": data.get("Plot"),
        "genre": genre,
        "is_horror": is_horror,
    })


# ---------- CRUD de avaliações ----------

def calc_average(fields, is_horror, medo):
    vals = [v for v in fields if v is not None]
    if is_horror and medo is not None:
        vals.append(medo)
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 2)


@app.route("/api/movies", methods=["GET"])
def list_movies():
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute("SELECT * FROM movies ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(ph("SELECT * FROM movies WHERE id=?"), (movie_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "não encontrado"}), 404
    return jsonify(row_to_dict(row))


@app.route("/api/movies", methods=["POST"])
def create_movie():
    d = request.json or {}
    roteiro = d.get("roteiro")
    historia = d.get("historia")
    trilha_sonora = d.get("trilha_sonora")
    final = d.get("final")
    plot_twist = d.get("plot_twist")
    is_horror = 1 if d.get("is_horror") else 0
    medo = d.get("medo") if is_horror else None
    average = calc_average([roteiro, historia, trilha_sonora, final, plot_twist], is_horror, medo)

    conn = get_db()
    cur = get_cursor(conn)
    sql = """
        INSERT INTO movies
        (title, year, imdb_id, poster_url, synopsis, genre, is_horror,
         roteiro, historia, trilha_sonora, final, plot_twist, medo, average, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    params = (
        d.get("title"), d.get("year"), d.get("imdb_id"), d.get("poster_url"),
        d.get("synopsis"), d.get("genre"), is_horror,
        roteiro, historia, trilha_sonora, final, plot_twist, medo,
        average, datetime.now().isoformat(),
    )
    if IS_PG:
        cur.execute(ph(sql) + " RETURNING id", params)
        movie_id = cur.fetchone()["id"]
    else:
        cur.execute(sql, params)
        movie_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": movie_id, "average": average}), 201


@app.route("/api/movies/<int:movie_id>", methods=["PUT"])
def update_movie(movie_id):
    d = request.json or {}
    roteiro = d.get("roteiro")
    historia = d.get("historia")
    trilha_sonora = d.get("trilha_sonora")
    final = d.get("final")
    plot_twist = d.get("plot_twist")
    is_horror = 1 if d.get("is_horror") else 0
    medo = d.get("medo") if is_horror else None
    average = calc_average([roteiro, historia, trilha_sonora, final, plot_twist], is_horror, medo)

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(
        ph("""
        UPDATE movies SET roteiro=?, historia=?, trilha_sonora=?, final=?, plot_twist=?,
            is_horror=?, medo=?, average=?
        WHERE id=?
        """),
        (roteiro, historia, trilha_sonora, final, plot_twist, is_horror, medo, average, movie_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"id": movie_id, "average": average})


@app.route("/api/movies/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(ph("DELETE FROM movies WHERE id=?"), (movie_id,))
    conn.commit()
    conn.close()
    return "", 204


if __name__ == "__main__":
    # host 0.0.0.0 => acessível por qualquer dispositivo na mesma rede local
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=not IS_PG)
