# mac0499-tcc

Repositório do Trabalho de Conclusão de Curso — **Potencializando a Análise Intersetorial do CulturaEduca com Banco de Dados em Grafos e LLMs**.

Bacharelado em Ciência da Computação, IME-USP. Orientadora: Profa. Dra. Kelly Rosa Braghetto.

## Conteúdo

1. [Visão geral](#visao)
2. [Setup](#setup)
3. [Estrutura do repositório](#estrutura)
4. [Como usar](#uso)
5. [Fontes de dados](#fontes)
6. [Recorte territorial](#recorte)
7. [Referências](#refs)

---

<a name="visao"></a>
## Visão geral

O trabalho tem duas frentes, sobre os dados geoespaciais e socioeconômicos da plataforma [CulturaEduca.cc](https://plataforma.culturaeduca.cc/).

**Banco de dados em grafos.** Os dados saem do banco relacional da plataforma (PostgreSQL/PostGIS) e são carregados num grafo de propriedades no Neo4j, com a hierarquia territorial do IBGE, as escolas, os equipamentos de saúde e os perfis do Censo. Um conjunto de 66 consultas analíticas, escritas em SQL e em Cypher, serve de benchmark para comparar os dois modelos sobre o estado de São Paulo.

**Consulta em linguagem natural (Text-to-Cypher).** Um workflow agêntico traduz perguntas em português para consultas Cypher, valida cada consulta com o CyVer e a corrige em laço quando há erros. Ele é adaptado do CyVerACT, com quatro mudanças:

- **Camada A:** as propriedades do grafo são recuperadas pela descrição (RAG com busca híbrida no Chroma), já que nomes como `v00644` não dizem nada;
- **Camada B** (opcional): os nomes de lugares e equipamentos citados na pergunta vão para o modelo escritos como estão no grafo;
- **hierarquia territorial no esquema:** o modelo recebe o número de saltos entre o setor e cada nível;
- **bloqueio de repetição:** o laço para quando o corretor repete uma consulta que já falhou.

A avaliação usa dois modelos abertos executados localmente pelo Ollama (`qwen2.5-coder:7b` e `llama3.1:8b`) e o Claude (`claude-sonnet-5-5`), pela API da Anthropic, como referência de modelo grande.

---

<a name="setup"></a>
## Setup

### Pré-requisitos

- Python 3.10+
- Neo4j rodando localmente (Community ou Desktop; os experimentos usaram a versão 2026.03)
- Acesso ao PostgreSQL da CulturaEduca — remoto ou numa cópia local (ver [Fonte de dados PostgreSQL](#pg))
- Para a consulta em linguagem natural: o [Ollama](https://ollama.com) com o modelo baixado (ver [`text2cypher/workflow/`](text2cypher/workflow))
- Opcional, para os cenários com o Claude: uma chave da API da Anthropic (`ANTHROPIC_API_KEY`) em `compartilhado/.env`

### Instalação

```bash
# clonar o repositório
git clone <url>
cd mac0499-tcc

# criar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# instalar as dependências
pip install -r compartilhado/requirements.txt

# configurar as credenciais
cp compartilhado/.env.example compartilhado/.env
# editar compartilhado/.env com as credenciais reais
```

Se o `psycopg2-binary` der erro na instalação, instale a biblioteca nativa do PostgreSQL:

```bash
# macOS
brew install postgresql libpq

# Debian/Ubuntu
sudo apt install libpq-dev

# Arch Linux
sudo pacman -S postgresql-libs
```

<a name="pg"></a>
### Fonte de dados PostgreSQL

O ETL lê os dados da CulturaEduca de um PostgreSQL. Há duas formas de acessá-lo, configuráveis no `compartilhado/.env`.

**Opção A — PostgreSQL remoto**

Aponte o `.env` para o servidor da CulturaEduca:

```
PG_HOST=200.144.245.101
PG_DATABASE=culturaeduca
PG_USER=<usuario>
PG_PASSWORD=<senha>
```

Depende de acesso à rede e de credenciais válidas.

**Opção B — cópia local** (funciona offline e é mais justa para os benchmarks de tempo)

Restaure um dump do banco num PostgreSQL local. É preciso ter a extensão PostGIS, porque as tabelas usam colunas geométricas (`_geom`).

**1. Instalar o PostgreSQL e o PostGIS**

```bash
# macOS
brew install postgresql@18 postgis

# Debian/Ubuntu
sudo apt install postgresql postgresql-postgis

# Arch Linux
sudo pacman -S postgresql postgis
```

**2. Criar o usuário e o banco**

> **Importante:** o banco precisa se chamar `culturaeduca`. As consultas usam referências em três partes (`culturaeduca.datasets.tabela`), e o PostgreSQL não aceita referência entre bancos se o nome for diferente.

```bash
psql -d postgres -c "CREATE ROLE <usuario> WITH LOGIN PASSWORD '<senha>' CREATEDB;"
psql -d postgres -c "CREATE DATABASE culturaeduca OWNER <usuario>;"
psql -d culturaeduca -c "CREATE EXTENSION postgis;"
```

**3. Restaurar o dump**

```bash
pg_restore -h localhost -U <usuario> -d culturaeduca \
  --no-owner --no-privileges caminho/do/backup.dump
```

É normal o restore mostrar cerca de 400 erros ignorados. São `GRANT`s para papéis que não existem e visões materializadas de outros esquemas (`plataforma`), que não afetam o esquema `datasets` usado pelo ETL.

Aponte o `.env` para o banco local:

```
PG_HOST=localhost
PG_DATABASE=culturaeduca
PG_USER=<usuario>
PG_PASSWORD=<senha>
```

---

<a name="estrutura"></a>
## Estrutura do repositório

```
mac0499-tcc/
├── compartilhado/            ← configuração e utilitários compartilhados
│   ├── .env.example          ← modelo do arquivo de credenciais
│   ├── .env                  ← credenciais reais (fora do git)
│   ├── requirements.txt      ← dependências Python
│   ├── config.py             ← carrega o .env e define o recorte territorial
│   └── db.py                 ← funções de conexão (PostgreSQL e Neo4j)
│
├── etl/                      ← carga PostgreSQL → Neo4j
│   ├── 01_geografia.py       ← hierarquia territorial
│   ├── 02_educacao.py        ← escolas (INEP 2024)
│   ├── 03_saude.py           ← equipamentos de saúde (CNES 2025)
│   ├── 04_perfis.py          ← perfis censitários (IBGE 2022)
│   ├── 05_indices.py         ← índices (espaciais e, opcionalmente, de nome)
│   ├── run_all.py            ← executa tudo em sequência
│   └── auxiliares/           ← listas de colunas e de perfis
│
├── perguntas/                ← as 66 consultas (linguagem natural, SQL e Cypher)
│   ├── ed_basica/            ← 27 consultas de educação
│   ├── saude/                ← 27 consultas de saúde
│   └── intersetorial/        ← 12 consultas que cruzam educação e saúde
│
├── text2cypher/              ← consulta em linguagem natural
│   ├── dicionario/           ← RAG das propriedades (Camada A) e valores dos filtros (Camada B)
│   └── workflow/             ← workflow agêntico adaptado do CyVerACT (CC BY-SA 4.0)
│
├── testes/
│   ├── validacao/            ← confere se SQL e Cypher devolvem o mesmo resultado
│   ├── performance/          ← benchmark de desempenho PostgreSQL × Neo4j
│   ├── rag_valores/          ← valores das colunas no texto indexado do RAG
│   ├── rag_modelos/          ← comparação de modelos de embedding
│   ├── rag_buscas/           ← comparação de formas de busca
│   └── avaliacao/            ← avaliação do Text-to-Cypher (piloto de custo do Claude)
│
├── ferramentas/              ← utilitários de administração dos bancos
└── docs/
    └── Proposta_de_TCC.pdf
```

Cada pasta tem o seu README, com os detalhes.

---

<a name="uso"></a>
## Como usar

### 1. Carregar os dados no Neo4j

Com o Neo4j rodando:

```bash
cd etl
python run_all.py
```

As etapas também podem ser rodadas uma a uma; a ordem e os detalhes estão em [`etl/`](etl).

### 2. Validar as consultas

```bash
cd testes/validacao
python validar_queries.py              # todas
python validar_queries.py ed_basica    # só um eixo
python validar_queries.py saude 5      # só uma consulta
```

O script executa cada consulta nos dois bancos e compara as linhas e os valores devolvidos (ver [`testes/validacao/`](testes/validacao)).

### 3. Medir o desempenho

```bash
cd testes/performance
python bench_postgres.py
python bench_neo4j.py
python analise.py          # gera os gráficos a partir dos CSVs
```

As métricas e os gráficos estão descritos em [`testes/performance/`](testes/performance).

### 4. Consultar em linguagem natural (Text-to-Cypher)

Com o PostgreSQL e o Neo4j no ar e o grafo já carregado:

```bash
# monta o dicionário das propriedades e indexa no Chroma (uma vez, ou quando o grafo mudar)
cd text2cypher/dicionario
python run_all.py

# faz uma pergunta ao workflow (com o Ollama rodando e o modelo baixado)
cd ../workflow
python executar.py "quantas escolas sem água potável há em Campinas?"
```

Para usar o Claude no lugar do modelo local, basta `MODEL_NAME=claude`. Os detalhes estão em [`text2cypher/`](text2cypher) e [`text2cypher/workflow/`](text2cypher/workflow), e os experimentos que embasaram o RAG, em `testes/rag_*`.

### 5. Administrar os bancos

A pasta `ferramentas/` tem utilitários para inspecionar e limpar o Neo4j:

```bash
python ferramentas/neo4j_admin.py labels     # lista os rótulos e as contagens
python ferramentas/neo4j_admin.py contar     # conta todos os nós
python ferramentas/neo4j_admin.py isolados   # nós sem nenhuma aresta
python ferramentas/neo4j_admin.py reset      # apaga tudo (nós e constraints)
```

Use o `reset` antes de trocar o `ESCOPO` (cidades ↔ estado); senão, os dois recortes se misturam no mesmo grafo.

O `pg_admin.py` reúne comandos de leitura para conferir a base de origem:

```bash
python ferramentas/pg_admin.py tabelas               # lista as tabelas e conta as linhas
python ferramentas/pg_admin.py contar eq_saude_2025  # conta as linhas de uma tabela
python ferramentas/pg_admin.py ufs                   # confere se a base está restrita a SP
python ferramentas/pg_admin.py bairros               # bairros que cruzam mais de um subdistrito
```

A cópia local do banco vem com o Brasil inteiro. Como o trabalho usa só o estado de São Paulo, o `limpar_pg_sp.py` apaga as linhas das outras UFs nas tabelas usadas e remove as tabelas que o projeto não usa (agregados de bairro, distrito, município, subdistrito e UF, CRAS, CREAS, IES, bibliotecas e centros POP):

```bash
python ferramentas/limpar_pg_sp.py             # simulação: só mostra o que faria
python ferramentas/limpar_pg_sp.py --executar  # aplica
```

É uma operação **destrutiva e irreversível**; faça um dump antes de rodar com `--executar`:

```bash
pg_dump -h localhost -U <usuario> -d culturaeduca -Fc -f backup_brasil.dump
```

Os `DELETE` não liberam espaço em disco sozinhos; para recuperá-lo, rode `VACUUM FULL` depois.

---

<a name="fontes"></a>
## Fontes de dados

| Fonte | Ano | Conteúdo |
|-------|-----|----------|
| IBGE — Censo Demográfico | 2022 | Malha territorial, setores censitários, variáveis socioeconômicas |
| INEP — Censo Escolar | 2024 | Microdados de educação básica |
| CNES/DATASUS | 2025 | Cadastro de estabelecimentos de saúde |

<a name="recorte"></a>
## Recorte territorial

O recorte usado nos experimentos é o **estado de São Paulo** (`cd_uf: 35`, `ESCOPO=estado` em `compartilhado/.env`).

O ETL também aceita um recorte reduzido, de três municípios (`ESCOPO=cidades`), usado no começo do desenvolvimento:
- São Paulo (`cd_mun`: 3550308)
- Campinas (`cd_mun`: 3548708)
- São Bernardo do Campo (`cd_mun`: 3509502)

<a name="refs"></a>
## Referências

- [CulturaEduca.cc](https://plataforma.culturaeduca.cc/)
- [Neo4j — documentação](https://neo4j.com/docs/)
- [PostgreSQL — documentação](https://www.postgresql.org/docs/) e [PostGIS — documentação](https://postgis.net/documentation/)
- Androna et al., *CyVerACT: An Agentic Cypher Translation Workflow over Knowledge Graphs*, Information Processing and Management, 2026 (base do workflow)
- [Ollama](https://ollama.com) e [Claude — documentação da API](https://platform.claude.com/docs/en/home)
