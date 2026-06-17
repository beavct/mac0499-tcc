# ETL — PostgreSQL para Neo4j

Scripts que extraem os dados da plataforma CulturaEduca (PostgreSQL remoto) e carregam no Neo4j local, montando o grafo de propriedades usado no TCC.

Cada script conecta no Postgres, faz a query, e manda pro Neo4j via driver Python, sem precisar copiar os dados do bando de dados relacional remoto e passar para a pasta de import do Neo4j.

## TODO

- [ ] Adicionar instruções para instalar o Neo4j Desktop e outras configurações que eu posso não ter comentado antes

## Conteúdo

<a name="tc"></a>
1. [Pré-requisitos](#pre_requisitos)
2. [Instalando as dependências do sistema](#dependencias)
3. [Instalando as libs Python](#libs_python)
4. [Configuração](#config)
5. [Como rodar](#como_rodar)
6. [O que cada script faz](#scripts)
7. [CSVs intermediários](#csv)
8. [Estrutura dos arquivos](#estr_arqs)
9. [Pasta `auxiliares/`](#auxiliares)
10. [Troubleshooting](#trouble)
11. [Referências](#refs)
12. [](#)
13. [](#)
14. [](#)
15. [](#)
16. [](#)

<a name="pre_requisitos"></a>
## Pré-requisitos

Você precisa ter instalado:

- **Python 3.10+**
- **Neo4j 5.x** rodando localmente (Community ou Desktop)
- Acesso ao PostgreSQL remoto da CulturaEduca (host, user, senha)

<a name="dependencias"></a>
### Instalando as dependências do sistema

O `psycopg2` precisa da lib `libpq` do Postgres pra compilar. Se você usar a versão `psycopg2-binary` (que é o que tá no requirements.txt), não precisa disso — já vem pré-compilado. Mas se der erro na instalação, instale a lib nativa:

**macOS (Homebrew):**

```bash
brew install postgresql libpq
```

**Debian/Ubuntu:**

```bash
sudo apt install python3-pip python3-venv libpq-dev
```

**Arch Linux:**

```bash
sudo pacman -S python python-pip postgresql-libs
```

<a name="libs_python"></a>
### Instalando as libs Python

```bash
cd mac0499-tcc/etl

# (Opcional mas recomendado) criar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

As libs usadas são:

| Lib | Pra quê |
|-----|---------|
| `psycopg2-binary` | Conectar no PostgreSQL e rodar as queries |
| `neo4j` | Driver oficial do Neo4j pra Python — envia Cypher direto |
| `python-dotenv` | Lê o arquivo `.env` com as credenciais |

---

<a name="config"></a>
## Configuração

Copie o arquivo de exemplo e preencha as senhas:

```bash
cp .env.example .env
```

Edite o `.env` com as credenciais reais. O arquivo já vem com host, porta, database e user preenchidos — só falta a senha do PG e a senha do seu Neo4j local.

O Neo4j precisa estar rodando antes de executar os scripts. Se estiver usando o Neo4j Desktop, é só abrir o projeto e dar Start no banco.

<a name="como_rodar"></a>
## Como rodar

Você pode rodar tudo de uma vez:

```bash
python run_all.py
```

Ou etapa por etapa (útil pra debugar ou conferir os CSVs intermediários):

```bash
python 01_geografia.py   # Monta a hierarquia territorial
python 02_educacao.py    # Carrega escolas
python 03_saude.py       # Carrega equipamentos de saúde
python 04_perfis.py      # Carrega os 8 perfis censitários
```

**A ordem importa!** A etapa 1 cria os nós de SetorCensitario que as etapas 2, 3 e 4 referenciam. Se rodar fora de ordem, o `MATCH` no Cypher não vai encontrar o setor e os dados ficam soltos.

<a name="scripts"></a>
## O que cada script faz

### `01_geografia.py`

Cria a espinha dorsal do grafo — a hierarquia territorial:

```
UF → Município → Distrito → [Bairro] → SetorCensitário
```

O bairro é condicional (São Paulo não tem bairro mapeado, mas São Bernardo do Campo tem). As 7 variáveis básicas do Censo (v0001 a v0007) ficam como propriedades do nó de setor censitário, junto com o polígono em WKT.

### `02_educacao.py`

Carrega as escolas de educação básica (INEP 2024) e conecta cada uma ao setor censitário onde ela está fisicamente localizada via aresta `[:LOCALIZADA_EM]`.

A associação escola→setor já é resolvida no PostgreSQL usando `ST_Contains` do PostGIS, então o Neo4j não precisa fazer cálculo geométrico nenhum.

### `03_saude.py`

Mesmo esquema da educação, mas para os equipamentos de saúde (CNES 2025). Cada unidade de saúde vira um nó `EquipamentoSaude` com as 35 colunas de atendimento/convênio como propriedades.

### `04_perfis.py`

Carrega as 8 tabelas de agregados censitários como nós de perfil, cada um conectado ao seu setor via `[:TEM_PERFIL]`:

- PerfilAlfabetizacao
- PerfilDemografia
- PerfilParentesco
- PerfilRacaCor
- PerfilDomiciliosParte1
- PerfilDomiciliosParte2
- PerfilDomiciliosParte3
- PerfilEntornoDomicilios

Cada perfil tem centenas de colunas `v*` que são carregadas dinamicamente (o script detecta as colunas e seta todas como propriedades numéricas).

<a name="csv"></a>
## CSVs intermediários

Cada etapa pode salvar um CSV na pasta `output/` antes de mandar pro Neo4j. Isso é pra conferir visualmente se os dados estão saindo certos do Postgres.

O comportamento é controlado pela variável `SALVAR_CSV` no `.env`:

```bash
# Gera CSVs para conferência
SALVAR_CSV=true

# Desativa geração de CSVs (quando já estiver tudo validado)
SALVAR_CSV=false
```

A pasta `output/` está no `.gitignore`, então não vai pro repositório.

<a name="estr_arqs"></a>
## Estrutura dos arquivos

```
etl/
├── .env.example              ← template de credenciais (copiar pra .env)
├── .gitignore
├── requirements.txt
├── config.py                 ← carrega .env e define as 3 cidades-alvo
├── db.py                     ← funções utilitárias (conexão PG, conexão Neo4j, save_csv)
├── 01_geografia.py           ← hierarquia territorial
├── 02_educacao.py            ← escolas de educação básica
├── 03_saude.py               ← equipamentos de saúde
├── 04_perfis.py              ← perfis censitários (7 tabelas)
├── run_all.py                ← executa tudo em sequência
└── auxiliares/
    ├── colunas_educacao.txt  ← lista de colunas a importar da tabela de educação
    ├── colunas_saude.txt     ← lista de colunas a importar da tabela de saúde
    └── config_perfis.txt     ← lista de perfis censitários (label | tabela)
```

<a name="auxiliares"></a>
### Pasta `auxiliares/`

Os scripts de educação e saúde lêem as colunas a importar de arquivos `.txt` dentro da pasta `auxiliares/`. Isso permite editar quais colunas entram no grafo sem mexer no código Python. O formato é simples: uma coluna por linha, linhas começando com `#` são ignoradas.

Para os perfis censitários, o `config_perfis.txt` lista quais tabelas importar (formato `Label | tabela_no_pg`). Como cada tabela de perfil tem centenas de colunas `v*`, todas são importadas automaticamente — o script detecta e carrega todas exceto as internas do PG.

<a name="trouble"></a>
## Troubleshooting

**"Connection refused" no Neo4j:** o banco não está rodando. Abre o Neo4j Desktop e dá Start, ou roda `neo4j start` no terminal.

**"Authentication failed" no Neo4j:** confere a senha no `.env`. A senha padrão do Neo4j na primeira vez é `neo4j`, mas ele pede pra trocar no primeiro acesso.

**Timeout no PostgreSQL:** o host remoto pode estar fora do ar ou sua rede pode estar bloqueando a porta 5432. Testa com `pg_isready -h 200.144.245.101 -p 5432`.

**"relation does not exist" no PostgreSQL:** confere se o schema é `culturaeduca.datasets` e se as tabelas existem com esses nomes exatos. Os nomes podem mudar entre ambientes.

<a name="refs"></a>
## Referências

- [Neo4j Python Driver — Documentação oficial](https://neo4j.com/docs/python-manual/current/)
- [psycopg2 — Documentação](https://www.psycopg.org/docs/)
- [python-dotenv — GitHub](https://github.com/theskumar/python-dotenv)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [PostGIS — ST_Contains](https://postgis.net/docs/ST_Contains.html)