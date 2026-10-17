# text2cypher — Consulta em linguagem natural

Esta pasta transforma uma pergunta em **linguagem natural** numa consulta **Cypher** sobre o grafo do CulturaEduca no Neo4j. Não há ajuste fino, os modelos são usados só para inferência, e o modelo pode ser trocado por configuração.

O código é construído sobre o CyVerACT, que gera a consulta, valida com o CyVer e corrige em laço. O que foi acrescentado aqui é, principalmente, um **RAG das propriedades**: ele encontra as propriedades do grafo pela descrição, já que nomes como `v00644` ou `in_agua_potavel` não dizem nada sobre o conteúdo.

## Conteúdo

1. [Visão geral](#visao)
2. [Estrutura](#estrutura)
3. [Camada A — dicionário das propriedades](#camada_a)
4. [Experimentos e avaliação](#avaliacao)
5. [Referências](#refs)

---

<a name="visao"></a>
## Visão geral

O CyVerACT escolhe quais partes do esquema mandar para o modelo comparando as palavras da pergunta com os nomes das propriedades do grafo. Isso não funciona aqui, pois as variáveis do Censo (`v*`) e as colunas das escolas e da saúde (`at_03_conv_01`, …) têm nomes que não dizem nada.

Por isso, as propriedades são buscadas pela descrição, em duas partes, que na monografia são as Camadas A e B:

- **Camada A — dicionário das propriedades (RAG):** cada propriedade vira um documento com o tema do nó e a descrição, indexado no Chroma. Para cada pergunta, só as propriedades mais parecidas com ela vão para o esquema, junto com a estrutura do grafo (rótulos, códigos, nomes e relações), que vai sempre.
- **Camada B — valores dos filtros (opcional):** os nomes de lugares e de equipamentos citados na pergunta vão para o modelo do jeito que estão escritos no grafo, para ele usar nos filtros (ver [Camada B](workflow/README.md#camada_b)).

A divisão em duas camadas vem do artigo de Macedo et al. (SBBD 2026). Só a Camada B corresponde a uma camada do artigo: lá, a outra camada recupera exemplos de consultas já validadas, e aqui a Camada A recupera as propriedades do esquema.

As descrições vêm dos `COMMENT ON COLUMN` do PostgreSQL da CulturaEduca, nas tabelas de agregados do Censo e nos microdados de educação e saúde. Os valores das colunas categóricas (ex.: `tp_dependencia`: 1 = Federal, 2 = Estadual…) vêm do `metadata.attribute`, o catálogo de colunas da plataforma, e o tipo de cada propriedade é lido do próprio Neo4j. Os nomes das propriedades são os mesmos nos dois bancos.

<a name="estrutura"></a>
## Estrutura

```
text2cypher/
├── README.md
├── config.py                      ← caminhos, credenciais e listas fixas do RAG
├── dicionario/                    ← dicionário das propriedades (Camada A) e valores (Camada B)
│   ├── 01_extrair_dicionario.py   ← descrições, tipos e valores (PG + Neo4j) → corpus/variaveis.json
│   ├── 02_indexar_chroma.py       ← gera os embeddings do corpus e indexa no Chroma
│   ├── run_all.py                 ← roda as etapas 01 e 02 em ordem
│   ├── retriever.py               ← busca híbrida (Chroma + BM25) e montagem do trecho do esquema
│   ├── stopwords_pt.py            ← stopwords em português do Snowball, para o BM25 (BSD)
│   ├── inspecionar.py             ← inspeciona a coleção do Chroma pelo terminal
│   ├── valores.py                 ← Camada B: acha na pergunta os nomes que existem no grafo
│   ├── bridge.py                  ← funções de casamento do BRIDGE (BSD-3, ver o cabeçalho)
│   └── corpus/variaveis.json      ← dicionário gerado pela etapa 01 (fora do git; regenerável)
├── vectorstore/                   ← índice do Chroma (fora do git)
└── workflow/                      ← workflow sobre o CyVerACT (ver workflow/README.md)
```

<a name="camada_a"></a>
## Camada A — dicionário das propriedades

> Pré-requisitos: o **PostgreSQL** da CulturaEduca acessível (as descrições vêm de lá) e o **Neo4j** já carregado pelo ETL (a etapa 01 confere quais propriedades existem no grafo). As credenciais dos dois ficam em `../compartilhado/.env`, e as dependências, em `compartilhado/requirements.txt` (ver o [README da raiz](../README.md)).

As duas etapas podem ser rodadas juntas, com `python run_all.py`, ou na ordem:

```bash
cd text2cypher/dicionario
python 01_extrair_dicionario.py   # PG (COMMENTs) → corpus/variaveis.json
python 02_indexar_chroma.py       # corpus → índice do Chroma em ../vectorstore/
```

### `01_extrair_dicionario.py`

Lê os comentários de coluna (`col_description`) e monta um documento por propriedade:

- **variáveis `v*`** das tabelas de agregados (`datasets.agregado_setores_censitarios_2022_*`) e da tabela de setores (`datasets.dtb_setores_censitarios_2022`);
- **colunas da `Escola`** e **do `EquipamentoSaude`**, restritas às que o ETL carrega no grafo.

Cada documento junta o **tema** com a **descrição** da fonte, porque a descrição sozinha é ambígua ("15 a 19 anos" de quê?).

Antes de tudo, o script lê do Neo4j quais propriedades existem e o **tipo** de cada uma (`INTEGER`, `FLOAT`, `BOOLEAN`, `STRING`). O que não está no grafo fica de fora: o ETL grava algumas colunas com outro nome (`co_entidade` → `id_aparelho`, `no_entidade` → `nm_aparelho`) e não grava as colunas vazias no recorte.

Os **valores** das colunas categóricas saem do `metadata.attribute` e são escritos como o modelo deve usá-los na consulta: `1 = Federal` para inteiros, `'1' = Municipal` para texto e `true = Sim` para booleanas. Cada documento guarda o tipo e os valores, mas o texto buscado só recebe os valores das colunas que não são booleanas: nas booleanas, o mesmo `true = Sim, false = Não` repetido em centenas de textos atrapalha a busca (ver [`../testes/rag_valores/`](../testes/rag_valores)).

Algumas listas ficam no `config.py` em vez de virem do PostgreSQL:

- `PROPRIEDADES_FIXAS`: as propriedades que aparecem sempre no esquema (código, nome e `location` dos equipamentos, `tp_gestao` e `situacao`), com a descrição copiada do PostgreSQL ou, quando o ETL criou a propriedade, escrita à mão;
- `PROPRIEDADES_FORA_DO_ESQUEMA`: as que não vão para o esquema, como o `geometry` do setor (o polígono em WKT, que nenhuma consulta usa);
- `DESCRICOES_INFERIDAS`: o `qt_mat_prof_tec`, sem descrição no PostgreSQL e na planilha de metadados; a descrição foi inferida pelas colunas vizinhas;
- `COMPLEMENTOS_DESCRICAO`: palavras que as perguntas usam e a descrição oficial não, acrescentadas ao texto logo depois da descrição. Por exemplo, "Dependência Administrativa (rede pública ou privada)", porque as perguntas falam em "escolas públicas". São seis colunas categóricas com nome técnico; o ganho foi medido em [`../testes/rag_buscas/`](../testes/rag_buscas), mas só na `tp_dependencia`, a única delas que está no gabarito.

As listas de origem vêm dos arquivos do ETL (`../etl/auxiliares/config_perfis.txt`, `colunas_educacao.txt` e `colunas_saude.txt`), para ficarem em sincronia com ele. A saída é o `corpus/variaveis.json`.

### `02_indexar_chroma.py`

Transforma o texto de cada propriedade em vetor (*embedding*) com o modelo multilíngue `intfloat/multilingual-e5-base`, escolhido no [teste dos modelos](../testes/rag_modelos), e grava a coleção no Chroma em `vectorstore/`, com similaridade de cosseno.

O E5 foi treinado com o prefixo `passage: ` nos textos e `query: ` nas perguntas; sem eles, o recall cai. Por isso o indexador e o `retriever.py` usam os prefixos definidos no `config.py`. Se o modelo for trocado, confira os prefixos na página dele no Hugging Face e rode esta etapa de novo.

Variável, nó, tema, tabela, descrição, tipo e valores ficam como metadados: voltam junto com cada resultado, mas não entram na busca. A etapa pode ser rodada de novo sem problema, porque recria a coleção do zero.

### `retriever.py`

Recebe a pergunta e faz duas buscas: a vetorial, no Chroma, com o mesmo modelo do índice, e o BM25, pelas palavras em comum (reduzidas ao radical com o stemmer de português do Snowball). As duas listas são unidas pela fusão por posição recíproca (*Reciprocal Rank Fusion*, RRF), e ficam as `k` primeiras (`TOP_K`, 20 por padrão). O BM25 e a fusão usam o `BM25Retriever` e o `EnsembleRetriever` do LangChain, porque o Chroma local não tem índice de palavras.

Essa busca híbrida foi a melhor no [teste das formas de busca](../testes/rag_buscas). Depois, o retriever agrupa as propriedades por nó e anota a aresta que liga cada nó ao setor: `(:SetorCensitario)-[:TEM_PERFIL]->(:Perfil*)` para os perfis e `(:Escola)-[:LOCALIZADA_EM]->(:SetorCensitario)` para os equipamentos.

O resultado é o trecho do esquema com as propriedades relevantes, cada uma com a descrição, o tipo e os valores, por exemplo:

```
tp_dependencia   // Dependência Administrativa (INTEGER: 1 = Federal, 2 = Estadual, 3 = Municipal, 4 = Privada)
in_agua_potavel  // Fornece água potável para o consumo humano (BOOLEAN: true = Sim, false = Não)
```

A estrutura do grafo (rótulos, códigos, nomes e relações) e a hierarquia territorial entram depois, no nó de esquema do workflow. Para uma consulta rápida pelo terminal:

```bash
python retriever.py "número de domicílios sem água encanada por setor" 12
```

### `inspecionar.py`

Os scripts usam o Chroma em modo **embarcado** (`PersistentClient`, que lê o diretório `vectorstore/` direto), sem servidor. Para conferir o conteúdo do índice pelo terminal:

```bash
python inspecionar.py                    # resumo e os 10 primeiros registros
python inspecionar.py 20                 # os 20 primeiros registros
python inspecionar.py 20 PerfilRacaCor   # filtra por nó do grafo
```

O script mostra o total de registros e, para cada um, o `id`, o texto indexado e os metadados.

<a name="avaliacao"></a>
## Experimentos e avaliação

As escolhas da Camada A vêm de três experimentos, cada um com o seu README em [`../testes/`](../testes):

| Experimento | Pergunta | Resultado |
|-------------|----------|-----------|
| [`rag_valores/`](../testes/rag_valores) | colocar os valores das colunas no texto indexado ajuda? | sim, nas categóricas; nas booleanas, atrapalha |
| [`rag_modelos/`](../testes/rag_modelos) | qual modelo de embedding recupera melhor? | entre dez modelos avaliados no MTEB-BR, o `multilingual-e5-base` empata no topo com o Qwen3 e o e5-large na busca da Camada A, sendo menor e sem depender de instrução |
| [`rag_buscas/`](../testes/rag_buscas) | qual forma de busca entrega mais propriedades certas? | a híbrida (vetorial + BM25) com os complementos de descrição |

A avaliação do workflow completo, com os modelos locais e o Claude, fica em [`../testes/avaliacao/`](../testes/avaliacao).

<a name="refs"></a>
## Referências

- Androna et al., *CyVerACT: An Agentic Cypher Translation Workflow over Knowledge Graphs*, Information Processing and Management, 2026 ([GitLab](https://gitlab.com/netmode/CyVerACT))
- Macedo et al., *Two-Layer RAG for Value Grounding and Schema Linking in LLM-Based Text-to-SQL Systems*, SBBD 2026
- Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, arXiv:2402.05672, 2024
- [Chroma — documentação](https://docs.trychroma.com/docs/overview/introduction)
- [LangChain — documentação](https://docs.langchain.com/oss/python/langchain/overview)
- Cormack, Clarke e Büttcher, *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*, SIGIR 2009
- [Snowball](https://snowballstem.org)
