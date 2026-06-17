# ETL — PostgreSQL para Neo4j

Scripts que extraem os dados da plataforma CulturaEduca (PostgreSQL remoto) e carregam no Neo4j local, montando o grafo de propriedades usado no TCC.

Cada script conecta no Postgres, faz a query, e manda pro Neo4j via driver Python, sem precisar copiar os dados do bando de dados relacional remoto e passar para a pasta de import do Neo4j.

## TODO

- [ ] Adicionar instruções para instalar o Neo4j Desktop e outras configurações que eu posso não ter comentado antes

## Conteúdo

<a name="tc"></a>
1. [Pré-requisitos](#pre_requisitos)
2. [Configuração](#config)
3. [Como rodar](#como_rodar)
4. [O que cada script faz](#scripts)
5. [CSVs intermediários](#csv)
6. [Estrutura dos arquivos](#estr_arqs)
7. [Pasta `auxiliares/`](#auxiliares)
8. [Troubleshooting](#trouble)
9. [Referências](#refs)

<a name="pre_requisitos"></a>
## Pré-requisitos

O setup geral (venv, pip install, credenciais) está documentado no [README da raiz](../README.md). Resumindo:

- **Python 3.10+** com as dependências instaladas (`pip install -r ../compartilhado/requirements.txt`)
- **Neo4j 5.x** rodando localmente (Community ou Desktop)
- **Credenciais** preenchidas em `../compartilhado/.env`

<a name="config"></a>
## Configuração

O Neo4j precisa estar rodando antes de executar os scripts. Se estiver usando o Neo4j Desktop, é só abrir o projeto e dar Start no banco.

A variável `SALVAR_CSV` em `../compartilhado/.env` controla se os scripts geram CSVs intermediários para conferência.

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

**Timeout no PostgreSQL:** o host remoto pode estar fora do ar ou a rede pode estar bloqueando a porta 5432.

**"relation does not exist" no PostgreSQL:** conferir se o schema é `culturaeduca.datasets` e se as tabelas existem com esses nomes exatos.

<a name="refs"></a>
## Referências

- [Neo4j Python Driver — Documentação oficial](https://neo4j.com/docs/python-manual/current/)
- [psycopg2 — Documentação](https://www.psycopg.org/docs/)
- [python-dotenv — GitHub](https://github.com/theskumar/python-dotenv)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [PostGIS — ST_Contains](https://postgis.net/docs/ST_Contains.html)