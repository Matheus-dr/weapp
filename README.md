# 🎬 Meus Filmes — MVP

Aplicação pessoal para avaliar filmes: você busca o filme, a sinopse aparece
automaticamente (via API OMDb), e você avalia **Roteiro, História, Trilha
Sonora, Final e Plot Twist** (0 a 10). Se marcar "é filme de terror", surge
um campo extra de **Medo**. A média é calculada automaticamente e tudo fica
salvo para sempre em um banco SQLite local (`movies.db`) — sobrevive a
reiniciar o PC, fechar o VSCode ou parar o servidor, porque os dados ficam
em arquivo, não em memória.

Feito para rodar na sua rede local: qualquer dispositivo conectado ao mesmo
Wi-Fi/rede consegue acessar pelo IP do computador que estiver rodando o
servidor.

---

## 1. Pré-requisitos

- Python 3.9+ instalado ([python.org](https://www.python.org/downloads/))
- (Opcional, mas recomendado) uma chave gratuita da **OMDb API**, para a
  busca automática de sinopse/poster/gênero funcionar. Sem ela, você ainda
  pode usar o app com o botão **"+ Manual"** para digitar o filme na mão.

### Como pegar a chave grátis da OMDb
1. Acesse https://www.omdbapi.com/apikey.aspx
2. Escolha o plano **FREE** (1.000 requisições/dia, grátis)
3. Preencha e-mail, confirme pelo e-mail recebido
4. Copie a chave (ex: `a1b2c3d4`)

---

## 2. Instalação

Abra um terminal na pasta do projeto (`filmes-app/`) e rode:

```bash
pip install -r requirements.txt
```

### Configurar a chave da OMDb

**Linux/Mac:**
```bash
export OMDB_API_KEY=sua_chave_aqui
```

**Windows (PowerShell):**
```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

> Dica: para não precisar repetir isso toda vez, você pode salvar essa
> linha em um script `.sh`/`.bat` que exporta a variável e já roda o
> `python app.py` em seguida.

---

## 3. Rodar o servidor

```bash
python app.py
```

Você verá algo como:

```
* Running on http://0.0.0.0:5000
```

- No **próprio PC**, acesse: `http://localhost:5000`
- Em **qualquer outro dispositivo na mesma rede** (celular, notebook,
  tablet), acesse: `http://IP_DO_SEU_PC:5000`

### Como descobrir o IP do seu PC na rede local
- **Windows:** `ipconfig` → veja "Endereço IPv4" (ex: `192.168.0.10`)
- **Mac/Linux:** `ifconfig` ou `ip a` → procure algo como `192.168.x.x`

O servidor fica rodando enquanto o terminal estiver aberto. Para parar,
`Ctrl+C`. Os dados salvos **não se perdem** — eles continuam no arquivo
`movies.db`, e ao rodar `python app.py` de novo tudo volta como estava.

---

## 4. Como usar

1. Digite o nome do filme e clique em **Buscar** (ou tecle Enter)
2. Clique no resultado desejado → aparece o poster + sinopse + gênero
3. Se o gênero contiver "Horror", o app já sugere marcar o filme como
   terror (você pode desmarcar se quiser)
4. Ajuste os sliders de cada categoria (0 a 10, passos de 0.5)
5. Veja a **média** sendo calculada em tempo real, com cor (vermelho →
   laranja → verde conforme a nota)
6. Clique em **Salvar avaliação**
7. O filme aparece na galeria "Filmes avaliados" logo abaixo, com pôster,
   nota média colorida e mini-resumo das notas

Use **"+ Manual"** para adicionar um filme sem depender da API (você digita
título, ano e sinopse na mão).

---

## 5. Estrutura de arquivos

```
filmes-app/
├── app.py            → backend Flask (rotas da API + banco de dados)
├── index.html         → interface (dark, com sliders e cards)
├── requirements.txt   → dependências Python
├── movies.db           → criado automaticamente no 1º run (seus dados)
└── README.md
```

---

## 6. Próximos passos possíveis (fora do MVP)

- Editar avaliações já salvas (hoje dá pra excluir e recriar)
- Ordenar/filtrar por nota, gênero, ano
- Autenticação simples se for expor além da rede local
- Rodar como serviço (systemd / Task Scheduler) para não precisar abrir o
  terminal manualmente toda vez
- Trocar OMDb por TMDb (mais imagens/metadados) se preferir

---

## 7. Aviso sobre a chave da API

O arquivo não inclui nenhuma chave — cada pessoa usa a sua própria, gratuita.
A OMDb tem um limite de 1.000 buscas/dia no plano free, mais que suficiente
para uso pessoal.
