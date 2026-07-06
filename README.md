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

---

<a name="visao"></a>
## Visão geral

Este projeto migra os dados geoespaciais e socioeconômicos da plataforma [CulturaEduca.cc](https://plataforma.culturaeduca.cc/) de um banco relacional (PostgreSQL/PostGIS) para um banco de dados orientado a grafos (Neo4j), e implementa uma interface de consulta em linguagem natural via LLMs (Text-to-Cypher).

O benchmark compara 60 consultas analíticas executadas nos dois modelos (SQL vs. Cypher) sobre os municípios de São Paulo, Campinas e São Bernardo do Campo.

---

<a name="setup"></a>
## Setup

### Pré-requisitos

- Python 3.10+
- Neo4j 5.x rodando localmente (Community ou Desktop)
- Acesso ao PostgreSQL da CulturaEduca — remoto ou uma cópia local (ver [Fonte de dados PostgreSQL](#pg))

### Instalação

```bash
# Clonar o repositório
git clone <url>
cd mac0499-tcc

# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r compartilhado/requirements.txt

# Configurar credenciais
cp compartilhado/.env.example compartilhado/.env
# Editar compartilhado/.env com as credenciais reais
```

Se `psycopg2-binary` der erro na instalação, instale a lib nativa do PostgreSQL:

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

O ETL lê os dados da CulturaEduca de um PostgreSQL. Há duas formas de acessá-lo, configuráveis no `compartilhado/.env`:

**Opção A — PostgreSQL remoto** (mais rápido de começar)

Aponte o `.env` para o servidor da CulturaEduca:

```
PG_HOST=200.144.245.101
PG_DATABASE=culturaeduca
PG_USER=<usuario>
PG_PASSWORD=<senha>
```

Depende de acesso à rede e de credenciais válidas.

**Opção B — cópia local** (offline, e mais justo para benchmarks de tempo)

Restaure um dump do banco num PostgreSQL local. Requer a extensão **PostGIS** (as tabelas usam colunas geométricas `_geom`):

**1. Instalar PostgreSQL e PostGIS**

```bash
# macOS
brew install postgresql@18 postgis

# Debian/Ubuntu
sudo apt install postgresql postgresql-postgis

# Arch Linux
sudo pacman -S postgresql postgis
```

**2. Criar o usuário e o banco**

> **Importante:** o banco precisa se chamar `culturaeduca` — as queries usam
> referência de 3 partes (`culturaeduca.datasets.tabela`) e o PostgreSQL não
> suporta cross-database reference se o nome for diferente.

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

No restore é normal aparecerem ~400 erros ignorados — são GRANTs para roles inexistentes e views materializadas de outros schemas (`plataforma`), que não afetam o schema `datasets` usado pelo ETL.

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
│   ├── .env.example          ← template de credenciais
│   ├── .env                  ← credenciais reais (não vai pro git)
│   ├── requirements.txt      ← dependências Python
│   ├── config.py             ← carrega .env, define municípios-alvo
│   └── db.py                 ← funções de conexão (PG e Neo4j)
│
├── etl/                      ← scripts de carga PostgreSQL → Neo4j
│   ├── README.md
│   ├── 01_geografia.py       ← hierarquia territorial
│   ├── 02_educacao.py        ← escolas (INEP 2024)
│   ├── 03_saude.py           ← equipamentos de saúde (CNES 2025)
│   ├── 04_perfis.py          ← perfis censitários (IBGE 2022)
│   ├── run_all.py            ← executa tudo em sequência
│   └── auxiliares/           ← listas de colunas e configurações
│
├── perguntas/                ← 60 consultas do benchmark
│   ├── README.md             ← mapa de consultas (índice completo)
│   ├── ed_basica/            ← 25 consultas de educação
│   ├── saude/                ← 25 consultas de saúde
│   └── intersetorial/       ← 10 consultas cruzando educação + saúde
│
├── ferramentas/              ← utilitários de administração
│   └── neo4j_admin.py        ← inspeciona e limpa o grafo (contar, reset, etc.)
│
├── testes/
│   ├── validacao/            ← script que roda SQL e Cypher e compara resultados
│   └── performance/          ← benchmarks de tempo de resposta
│
└── docs/
    └── Proposta_de_TCC.pdf
```

---

<a name="uso"></a>
## Como usar

### 1. Carregar dados no Neo4j

Com o Neo4j rodando:

```bash
cd etl
python run_all.py
```

Ou etapa por etapa:

```bash
python 01_geografia.py   # Hierarquia territorial
python 02_educacao.py    # Escolas
python 03_saude.py       # Equipamentos de saúde
python 04_perfis.py      # Perfis censitários
```

### 2. Validar consultas

```bash
cd testes/validacao
python validar_queries.py              # todas
python validar_queries.py ed_basica    # só educação
python validar_queries.py saude 5      # só a Q5 de saúde
```

O script executa cada consulta nos dois bancos e compara número de linhas e valores agregados.

### 3. Administrar o grafo

A pasta `ferramentas/` tem utilitários para inspecionar e limpar o Neo4j:

```bash
python ferramentas/neo4j_admin.py labels    # lista labels e contagens
python ferramentas/neo4j_admin.py contar     # conta todos os nós
python ferramentas/neo4j_admin.py isolados    # nós sem nenhuma aresta
python ferramentas/neo4j_admin.py reset       # apaga tudo (nós + constraints)
```

Use o `reset` antes de trocar o `ESCOPO` (cidades ↔ estado), senão os dois recortes se misturam no mesmo grafo.

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

- São Paulo (cd_mun: 3550308)
- Campinas (cd_mun: 3548708)
- São Bernardo do Campo (cd_mun: 3509502)
