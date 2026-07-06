# ETL — PostgreSQL para Neo4j

Scripts que extraem os dados da plataforma CulturaEduca (PostgreSQL, remoto ou cópia local) e carregam no Neo4j local, montando o grafo de propriedades usado no TCC.

Cada script conecta no Postgres, faz a query, e manda pro Neo4j via driver Python, sem precisar copiar os dados do banco de dados relacional e passar para a pasta de import do Neo4j. A fonte PostgreSQL (remota ou local) é definida no `../compartilhado/.env` — ver [README da raiz](../README.md#pg).

## Conteúdo

<a name="tc"></a>
1. [Pré-requisitos](#pre_requisitos)
2. [Configuração](#config)
3. [Como rodar](#como_rodar)
4. [O que cada script faz](#scripts)
5. [CSVs intermediários](#csv)
6. [Carga em batches e uso de memória](#batches)
7. [Estrutura dos arquivos](#estr_arqs)
8. [Pasta `auxiliares/`](#auxiliares)
9. [Troubleshooting](#trouble)
10. [Referências](#refs)

<a name="pre_requisitos"></a>
## Pré-requisitos

O setup geral (venv, pip install, credenciais) está documentado no [README da raiz](../README.md). Resumindo:

- **Python 3.10+** com as dependências instaladas (`pip install -r ../compartilhado/requirements.txt`)
- **Neo4j 5.x** rodando localmente (Community ou Desktop)
- **Credenciais** preenchidas em `../compartilhado/.env`

<a name="config"></a>
## Configuração

O Neo4j precisa estar rodando antes de executar os scripts. Se estiver usando o Neo4j Desktop, é só abrir o projeto e dar Start no banco.

Duas variáveis em `../compartilhado/.env` controlam o comportamento da carga:

| Variável | Valores | O que faz |
|----------|---------|-----------|
| `ESCOPO` | `cidades` / `estado` | Define o recorte territorial (ver abaixo) |
| `SALVAR_CSV` | `true` / `false` | Gera ou não CSVs intermediários para conferência |

### Escopo territorial

O mesmo ETL carrega dois recortes diferentes, controlados pela variável `ESCOPO`:

```bash
# Apenas os 3 municípios (São Paulo, São Bernardo do Campo, Campinas)
ESCOPO=cidades

# Todos os municípios do estado de São Paulo (UF=35)
ESCOPO=estado
UF=35
```

O escopo `cidades` usa o filtro `cd_mun IN (...)` com os 3 municípios; o escopo `estado` usa `cd_uf = '35'`, carregando os 645 municípios de SP (~103 mil setores). A lógica é centralizada na função `filtro_territorial()` em `compartilhado/config.py`, então os dois recortes usam exatamente os mesmos scripts — só muda o filtro.

> **Atenção:** ao trocar de escopo, limpe o banco Neo4j antes de recarregar, senão os dois recortes se misturam no mesmo grafo. O comando de limpezad o banco de dados pode ser encontrado no diretório 'ferramentas'.

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
UF → Município → Distrito → Subdistrito → [Bairro] → SetorCensitário
```

O subdistrito está presente nas 3 cidades. O bairro é condicional (São Paulo não tem bairro mapeado, mas São Bernardo do Campo tem). As 7 variáveis básicas do Censo (v0001 a v0007) ficam como propriedades do nó de setor censitário, junto com o polígono em WKT.

### `02_educacao.py`

Carrega as escolas de educação básica (INEP 2024) e conecta cada uma ao setor censitário onde ela está fisicamente localizada via aresta `[:LOCALIZADA_EM]`.

A associação escola→setor já é resolvida no PostgreSQL usando `ST_Contains` do PostGIS, então o Neo4j não precisa fazer cálculo geométrico nenhum.

### `03_saude.py`

Mesmo esquema da educação, mas para os equipamentos de saúde (CNES 2025). Cada unidade de saúde vira um nó `EquipamentoSaude` com as 35 colunas de atendimento/convênio como propriedades.

### `04_perfis.py`

Carrega as tabelas de agregados censitários como nós de perfil, cada um conectado ao seu setor via `[:TEM_PERFIL]`:

- PerfilAlfabetizacao
- PerfilDemografia
- PerfilParentesco
- PerfilRacaCor
- PerfilDomiciliosParte1
- PerfilDomiciliosParte2
- PerfilDomiciliosParte3
- PerfilEntornoDomicilios

A lista de perfis é lida do arquivo `auxiliares/config_perfis.txt`. Cada perfil tem centenas de colunas `v*` que são carregadas dinamicamente.

<a name="csv"></a>
## CSVs intermediários

Cada etapa pode salvar um CSV na pasta `output/` antes de mandar pro Neo4j. Isso é pra conferir visualmente se os dados estão saindo certos do Postgres.

Controlado pela variável `SALVAR_CSV` em `../compartilhado/.env`:

```bash
SALVAR_CSV=true   # gera CSVs para conferência
SALVAR_CSV=false  # desativa (quando já validado)
```

A pasta `output/` está no `.gitignore`, então não vai pro repositório.

<a name="batches"></a>
## Carga em batches e uso de memória

A carga no Neo4j é feita em lotes (batches) via `UNWIND` — cada batch é uma transação. O custo de memória de uma transação é aproximadamente:

```
nº de nós no batch  ×  nº de propriedades por nó
```

Para as tabelas de unidade de saúde e escolas o uso da memória heap é controlado, mas **os perfis censitários são um caso especial**: cada nó de perfil carrega dezenas ou centenas de colunas `v*`. Elas variam bastante — de ~36 colunas em `PerfilDemografia` a ~406 em `PerfilDomiciliosParte2`. Um batch fixo, nesse cenário, ou fica lento demais para os perfis leves ou estoura o heap do Neo4j nos pesados.

### Por que batch adaptativo

Durante a carga do estado de São Paulo inteiro (~103 mil setores), um batch de **5000 nós × 406 colunas** (~2 milhões de valores numa única transação) estourou o heap padrão do Neo4j (`OutOfMemoryError`, heap de 1 GB).

Para evitar isso sem depender de aumentar o heap, o `04_perfis.py` calcula o tamanho do batch dinamicamente para cada perfil, mirando um teto seguro de **~200 mil valores por transação** (cerca de 10× de margem abaixo do ponto de falha observado):

```python
batch_size = 200_000 / nº_de_colunas   # limitado entre 200 e 5000
```

Assim, na prática:

| Perfil | Colunas | Batch |
|--------|---------|-------|
| PerfilDemografia | ~36 | 5000 (teto) |
| PerfilParentesco | ~182 | ~1000 |
| PerfilDomiciliosParte2 | ~406 | ~490 |

O valor de 200 mil é **empírico**, não uma conta teórica exata — é uma margem folgada a partir do ponto de falha que observamos. Se ainda ocorrer `OutOfMemoryError`, há duas saídas: reduzir esse alvo no código (`VALORES_POR_TRANSACAO` em `04_perfis.py`) ou aumentar o heap do Neo4j (`server.memory.heap.max_size`) nas configurações do DBMS. Para os testes rodados localmente, o heap foi alterado para 2G no arquivo de configuração do Neo4j. 

<a name="estr_arqs"></a>
## Estrutura dos arquivos

```
etl/
├── 01_geografia.py           ← hierarquia territorial
├── 02_educacao.py            ← escolas de educação básica
├── 03_saude.py               ← equipamentos de saúde
├── 04_perfis.py              ← perfis censitários
├── run_all.py                ← executa tudo em sequência
└── auxiliares/
    ├── colunas_educacao.txt  ← colunas a importar (educação)
    ├── colunas_saude.txt     ← colunas a importar (saúde)
    └── config_perfis.txt     ← perfis censitários (label | tabela)
```

<a name="auxiliares"></a>
### Pasta `auxiliares/`

Os scripts de educação e saúde lêem as colunas a importar de arquivos `.txt` dentro da pasta `auxiliares/`. Isso permite editar quais colunas entram no grafo sem mexer no código Python. O formato é simples: uma coluna por linha, linhas começando com `#` são ignoradas.

Para os perfis censitários, o `config_perfis.txt` lista quais tabelas importar (formato `Label | tabela_no_pg`). Como cada tabela de perfil tem centenas de colunas `v*`, todas são importadas automaticamente — o script detecta e carrega todas exceto as internas do PG.

<a name="trouble"></a>
## Troubleshooting

**"Connection refused" no Neo4j:** o banco não está rodando. Abre o Neo4j Desktop e dá Start, ou roda `neo4j start` no terminal.

**"Authentication failed" no Neo4j:** conferir a senha em `../compartilhado/.env`. A senha padrão do Neo4j na primeira vez é `neo4j`, mas ele pede pra trocar no primeiro acesso.

**Timeout no PostgreSQL:** se estiver usando o banco remoto, o host pode estar fora do ar ou a rede bloqueando a porta 5432. Se for local, confira se o PostgreSQL está rodando (`brew services list`).

**"cross-database references are not implemented":** o banco local precisa se chamar `culturaeduca`. As queries usam referência de 3 partes (`culturaeduca.datasets.tabela`) e o PostgreSQL trata um nome de banco diferente como cross-database, que não é suportado. Renomeie com `ALTER DATABASE ... RENAME TO culturaeduca`.

**"relation does not exist" no PostgreSQL:** conferir se o schema é `culturaeduca.datasets` e se as tabelas existem com esses nomes exatos. Numa cópia local, confirme também que a extensão PostGIS foi instalada antes do restore (senão as tabelas com `_geom` não são criadas).

<a name="refs"></a>
## Referências

- [Neo4j Python Driver — Documentação oficial](https://neo4j.com/docs/python-manual/current/)
- [psycopg2 — Documentação](https://www.psycopg.org/docs/)
- [python-dotenv — GitHub](https://github.com/theskumar/python-dotenv)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [PostGIS — ST_Contains](https://postgis.net/docs/ST_Contains.html)