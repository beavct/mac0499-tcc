# text2cypher — Consulta em linguagem natural (NL → Cypher)

Camada que traduz perguntas em **linguagem natural** para **Cypher** sobre o grafo do CulturaEduca (Neo4j), gerando consultas válidas e semanticamente corretas **sem fine-tuning** — só inferência via API, com modelo trocável.

É construída sobre o [CyVerACT](../../referencias_codigo/CyVerACT) (workflow agêntico + validação determinística do CyVer). A contribuição própria é uma camada de **RAG por metadados** para recuperar as variáveis censitárias `v*`, cujos nomes são opacos (`v00644`, `v01031`, …) e por isso não casam com os termos da pergunta.

## Conteúdo

1. [Visão geral](#visao)
2. [Estrutura](#estrutura)
3. [Camada A — dicionário de variáveis (RAG)](#camada_a)
4. [Próximos passos](#proximos)
5. [Referências](#refs)

---

<a name="visao"></a>
## Visão geral

O CyVerACT filtra o esquema do grafo casando os termos da pergunta com os **nomes** de rótulos, relações e propriedades. Isso funciona para nomes legíveis, mas falha para as centenas de variáveis `v*` do Censo, cujos nomes não dizem nada. Nossa camada resolve isso recuperando as variáveis por **descrição**:

- **Camada A — schema-linking (RAG):** cada `v*` vira um documento (`tema do nó + descrição do IBGE`), indexado num banco vetorial (Chroma). Na hora da pergunta, recupera-se as variáveis mais prováveis por similaridade semântica, montando um esquema enxuto e aterrado que alimenta o gerador de Cypher.
- **Camada B — value grounding:** (a fazer) Definir os valores dos filtros `WHERE` nos valores reais do grafo.

As descrições das variáveis vêm dos `COMMENT ON COLUMN` das tabelas de agregados do Censo no PostgreSQL da CulturaEduca — os nomes `v*` são os mesmos no grafo.

<a name="estrutura"></a>
## Estrutura

```
text2cypher/
├── README.md
├── config.py                 ← caminhos + credenciais
├── dicionario/               ← Camada A (schema-linking)
│   ├── 01_extrair_dicionario.py   ← lê os COMMENTs do PG → corpus/variaveis.json
│   ├── 02_indexar_chroma.py       ← embeda o corpus e indexa no Chroma
│   ├── run_all.py                 ← roda as etapas 01 e 02 em ordem
│   ├── retriever.py               ← consulta o Chroma e monta o fragmento de esquema
│   ├── inspecionar.py             ← inspeciona a coleção do Chroma pelo terminal
│   └── corpus/variaveis.json      ← dicionário gerado pela etapa 01 (fora do git; regenerável)
├── vectorstore/              ← índice Chroma persistido (fora do git)
├── workflow/                 ← (a fazer) pipeline sobre o CyVerACT
└── avaliacao/                ← (a fazer) métricas EX / CM / AST
```

<a name="camada_a"></a>
## Camada A — dicionário de variáveis (RAG)

> Pré-requisito: o **PostgreSQL** da CulturaEduca acessível (as descrições das variáveis vêm de lá; credenciais em `../compartilhado/.env`) e as dependências instaladas via `compartilhado/requirements.txt` (ver [README da raiz](../README.md)).

Dois passos, na ordem:

```bash
cd text2cypher/dicionario
python 01_extrair_dicionario.py   # PG (COMMENTs) → corpus/variaveis.json
python 02_indexar_chroma.py       # corpus → índice Chroma em ../vectorstore/
```

### `01_extrair_dicionario.py`

Lê os comentários de coluna (`col_description`) das tabelas de agregados
(`datasets.agregado_setores_censitarios_2022_*`) e da tabela de setores
(`datasets.dtb_setores_censitarios_2022`), e monta um documento por variável
`v*`. Cada documento junta o **tema** com a **descrição** crua do IBGE — porque a
descrição sozinha é ambígua sem o tema.

O mapeamento de nó para tabela dos perfis é lido de `../etl/auxiliares/config_perfis.txt`,
para ficar em sincronia com o ETL. Saída: `corpus/variaveis.json`.

### `02_indexar_chroma.py`

Embeda o campo `texto` de cada variável com um modelo multilíngue e
grava a coleção no Chroma persistente em `vectorstore/`, com similaridade de
cosseno. Variável, nó, tema, tabela e descrição ficam como metadados, para o
retriever montar o esquema filtrado. A indexação é idempotente (recria a coleção).

### `retriever.py`

Dada uma pergunta, embeda-a com o mesmo modelo e recupera as top-`k`
(`config.TOP_K`) variáveis `v*` mais similares no Chroma. Agrupa por nó do grafo
e anota a aresta de ligação `(:SetorCensitario)-[:TEM_PERFIL]->(:Perfil*)`,
produzindo o fragmento de esquema com as variáveis relevantes. O backbone
estrutural (hierarquia territorial, escolas, equipamentos) é acrescentado depois
pelo nó de esquema do workflow, a partir do próprio grafo. Também roda pelo
terminal para inspeção rápida:

```bash
python retriever.py "número de domicílios sem água encanada por setor" 12
```

### `inspecionar.py`

Os scripts usam o Chroma em modo **embarcado** (`PersistentClient`, lê o diretório
`vectorstore/` direto) — não precisam de servidor. Para conferir o conteúdo do
índice pelo terminal:

```bash
python inspecionar.py                    # resumo + 10 primeiros registros
python inspecionar.py 20                 # primeiros 20 registros
python inspecionar.py 20 PerfilRacaCor   # filtra por nó do grafo
```

Mostra o total de registros da coleção e, para cada um, o `id`, o `texto`
embeddado e os metadados (variável, nó, tema, tabela, descrição).

<a name="proximos"></a>
## Próximos passos

- **Camada B** (value grounding) para os filtros `WHERE` — opcional/plugável (ablação).
- **Workflow** sobre o CyVerACT com modelos abertos por API (Qwen), reusando `cyver_evaluator` + `cypher_corrector`.
- **Avaliação** por EX / CM / AST, reportada por nível de dificuldade.

<a name="refs"></a>
## Referências

- [ChromaDB - Documentação](https://docs.trychroma.com/docs/overview/introduction)
