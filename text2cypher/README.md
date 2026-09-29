# text2cypher — Consulta em linguagem natural (NL → Cypher)

Aqui fica a parte que transforma uma pergunta em **linguagem natural** numa consulta **Cypher** sobre o grafo do CulturaEduca (Neo4j). Não tem **fine-tuning**: o modelo só é usado para inferência, e dá pra trocar de modelo.

O código é construído sobre o [CyVerACT](../../referencias_codigo/CyVerACT), que gera a consulta, valida com o CyVer e corrige em laço. O que é nosso é um **RAG por metadados**: ele acha as propriedades do grafo pela descrição, já que nomes como `v00644` ou `in_agua_potavel` não dizem nada.

## Conteúdo

1. [Visão geral](#visao)
2. [Estrutura](#estrutura)
3. [Camada A — dicionário de variáveis (RAG)](#camada_a)
4. [Referências](#refs)

---

<a name="visao"></a>
## Visão geral

O CyVerACT escolhe quais partes do esquema mandar pro modelo comparando as palavras da pergunta com os **nomes** das propriedades. Isso não funciona aqui: as variáveis do Censo (`v*`) e as colunas das escolas e da saúde (`at_03_conv_01`, …) têm nomes que não dizem nada.

Por isso, a gente busca as propriedades pela **descrição**. São duas partes (na monografia, Camadas A e B):

- **Dicionário das propriedades (RAG):** cada propriedade vira um documento com o tema do nó e a descrição, guardado no Chroma. Na hora da pergunta, só as propriedades mais parecidas com ela vão pro esquema, junto da estrutura do grafo (rótulos, códigos, nomes e relações), que vai sempre.
- **Valores dos filtros:** (a fazer) usar nos `WHERE` os valores que existem de fato no grafo (*value grounding*).

As descrições vêm dos `COMMENT ON COLUMN` do PostgreSQL da CulturaEduca: das tabelas de agregados do Censo e dos microdados de educação e saúde. Os nomes das propriedades são os mesmos no grafo.

<a name="estrutura"></a>
## Estrutura

```
text2cypher/
├── README.md
├── config.py                 ← caminhos + credenciais
├── dicionario/               ← dicionário das propriedades (RAG)
│   ├── 01_extrair_dicionario.py   ← lê os COMMENTs do PG → corpus/variaveis.json
│   ├── 02_indexar_chroma.py       ← embeda o corpus e indexa no Chroma
│   ├── run_all.py                 ← roda as etapas 01 e 02 em ordem
│   ├── retriever.py               ← consulta o Chroma e monta o trecho do esquema
│   ├── inspecionar.py             ← inspeciona a coleção do Chroma pelo terminal
│   └── corpus/variaveis.json      ← dicionário gerado pela etapa 01 (fora do git; regenerável)
├── vectorstore/              ← índice Chroma persistido (fora do git)
├── workflow/                 ← pipeline sobre o CyVerACT (ver workflow/README.md)
└── avaliacao/                ← (a fazer) métricas EX / CM / AST
```

<a name="camada_a"></a>
## Camada A — dicionário de variáveis (RAG)

> Pré-requisitos: o **PostgreSQL** da CulturaEduca acessível (as descrições vêm de lá) e o **Neo4j** já carregado pelo ETL (a etapa 01 confere quais propriedades existem no grafo). As credenciais dos dois ficam em `../compartilhado/.env`. As dependências são as de `compartilhado/requirements.txt` (ver [README da raiz](../README.md)).

Você pode rodar tudo com `python run_all.py`, ou os dois passos na ordem:

```bash
cd text2cypher/dicionario
python 01_extrair_dicionario.py   # PG (COMMENTs) → corpus/variaveis.json
python 02_indexar_chroma.py       # corpus → índice Chroma em ../vectorstore/
```

### `01_extrair_dicionario.py`

Lê os comentários de coluna (`col_description`) e monta um documento por propriedade:

- **variáveis `v*`** das tabelas de agregados (`datasets.agregado_setores_censitarios_2022_*`)
  e da tabela de setores (`datasets.dtb_setores_censitarios_2022`);
- **colunas da `Escola`** e **do `EquipamentoSaude`**, restritas às que o ETL carrega no grafo.

Cada documento junta o **tema** com a **descrição** da fonte, porque a descrição
sozinha é ambígua ("15 a 19 anos" de quê?).

No fim, ele confere no Neo4j quais propriedades existem de fato e descarta as outras.
O ETL grava algumas colunas com outro nome (`co_entidade` → `id_aparelho`,
`no_entidade` → `nm_aparelho`) e não grava colunas vazias no recorte.

As listas de origem vêm dos arquivos do ETL (`../etl/auxiliares/config_perfis.txt`,
`colunas_educacao.txt` e `colunas_saude.txt`), pra ficar em sincronia com ele. A saída é
o `corpus/variaveis.json`.

### `02_indexar_chroma.py`

Transforma o campo `texto` de cada propriedade em vetor (embedding), com um modelo
multilíngue, e grava a coleção no Chroma em `vectorstore/`, usando similaridade de cosseno.
Variável, nó, tema, tabela e descrição ficam como metadados, que o retriever usa pra
montar o esquema. Pode rodar de novo sem medo: ele recria a coleção do zero.

### `retriever.py`

Recebe a pergunta, transforma em vetor com o mesmo modelo e busca no Chroma as `k`
propriedades mais parecidas (`config.TOP_K`). Depois agrupa por nó e anota a aresta que
liga cada nó ao setor: `(:SetorCensitario)-[:TEM_PERFIL]->(:Perfil*)` pros perfis e
`(:Escola)-[:LOCALIZADA_EM]->(:SetorCensitario)` pros equipamentos.

O resultado é o trecho do esquema com as propriedades relevantes. A estrutura do grafo
(rótulos, códigos, nomes e relações) entra depois, no nó de esquema do workflow.
Pra uma olhada rápida, você pode rodar pelo terminal:

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

TODO

- **Hierarquia e não permitir repetição de consultas**
- **Camada A**: Adicionar categorização das propriedades junto das descrições
- **Camada B** (value grounding) para os filtros `WHERE` — opcional/plugável (ablação).
- **Descrições e valores das propriedades fixas** (`location`, `geometry`, `tp_*`) — junto da questão das categorias.
- **Avaliação** por EX / CM / AST, tentativas até acertar e cobertura do RAG.

<a name="refs"></a>
## Referências

- [ChromaDB - Documentação](https://docs.trychroma.com/docs/overview/introduction)
