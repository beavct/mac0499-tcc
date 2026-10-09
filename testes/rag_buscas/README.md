# Teste do RAG: formas de busca

Fizemos este script pra rodar os testes e escolher a melhor técnica de busca no RAG do [`text2cypher/`](../../text2cypher). A ideia é ver qual forma de busca entrega ao modelo mais das propriedades de que cada pergunta precisa.

## Como funciona

O teste usa o mesmo gabarito, a mesma métrica e os mesmos grupos de propriedade do [teste dos valores](../rag_valores). Pra cada uma das 65 consultas de [`perguntas/`](../../perguntas) que usam o dicionário, ele conta quantas propriedades do Cypher correto aparecem entre as `k` primeiras (**recall@k**) e quantas perguntas têm todas as suas propriedades no top-20 (**perguntas completas**).

As técnicas comparadas e de onde cada uma veio:

| Busca | O que faz | Implementação | Referência |
|-------|-----------|---------------|------------|
| vetorial | cosseno entre a pergunta e o texto | `sentence-transformers`, `multilingual-e5-base` | Wang et al., 2024 |
| BM25 | palavras em comum, valendo mais as raras | `rank_bm25` com o stemmer de português do Snowball | Robertson e Zaragoza, 2009 |
| híbrida | junta a vetorial e o BM25 pela posição nas duas listas (RRF) | `BM25Retriever`, `InMemoryVectorStore` e `EnsembleRetriever` do LangChain | Cormack, Clarke e Büttcher, 2009 |
| MMR | evita propriedades parecidas demais no topo | `max_marginal_relevance_search` do `InMemoryVectorStore` | Carbonell e Goldstein, 1998 |
| reranker | um *cross-encoder* reordena as 50 primeiras da híbrida | `CrossEncoder` com o `bge-reranker-v2-m3` | Nogueira e Cho, 2019 |

A híbrida usa o RRF do artigo original, com pesos iguais e a constante 60, que também são os padrões do LangChain. Assim ela não tem nenhum parâmetro ajustado no próprio gabarito.

O script também testa a híbrida com os complementos do `COMPLEMENTOS_DESCRICAO` do [`text2cypher/config.py`](../../text2cypher/config.py), como "Dependência Administrativa (rede pública ou privada)". As outras buscas usam o texto sem eles.

> **Atenção:** a busca híbrida não roda dentro do Chroma local, porque o índice do BM25 só existe no Chroma Cloud ("Sparse vector indexing is not enabled in local"). A função de BM25 do Chroma também usa um stemmer de inglês. Por isso, o BM25 e a fusão ficam com o `BM25Retriever` e o `EnsembleRetriever` do LangChain, e o Chroma faz só a busca vetorial. O [`retriever.py`](../../text2cypher/dicionario/retriever.py) do workflow faz a mesma busca, com o mesmo `tokenizar`, e dá o mesmo resultado no gabarito.

## Como rodar

Pré-requisito: o dicionário gerado pela etapa 01 (`text2cypher/dicionario/corpus/variaveis.json`, ver [`text2cypher/README.md`](../../text2cypher/README.md)). O script não usa o PostgreSQL nem o Neo4j.

```bash
cd testes/rag_buscas
python comparar_buscas.py              # todas, menos o reranker
python comparar_buscas.py --reranker   # com o reranker (baixa ~2,3 GB na primeira vez)
```

Ele imprime a tabela e grava em `output/`:
- `recall.csv`: recall por busca, grupo e `k`, e as perguntas completas;
- `posicoes.csv`: a posição de cada propriedade do gabarito em cada busca;
- `notas_reranker.csv`: as notas do reranker. Com esse arquivo, o script roda de novo sem baixar o modelo.

O `DeprecationWarning` que aparece ao rodar vem do `langchain-community`, onde está o `BM25Retriever`: o pacote [está sendo descontinuado](https://github.com/langchain-ai/langchain-community/issues/674), mas continua funcionando.

## Resultados

A rodada usada na monografia está em `resultados/`. Recall@20 por grupo de propriedade:

| Busca | todas | `v*` (Censo) | categórica | booleana | outras | completas |
|-------|------:|-------------:|-----------:|---------:|-------:|----------:|
| vetorial | 0,65 | 0,51 | **0,64** | 0,76 | **0,76** | 30/65 |
| BM25 | 0,66 | 0,54 | 0,09 | **0,95** | 0,70 | 31/65 |
| híbrida | 0,72 | 0,66 | 0,18 | **0,95** | 0,73 | 38/65 |
| **híbrida, com complementos** | **0,75** | 0,66 | 0,55 | **0,95** | 0,73 | **41/65** |
| reranker sobre a híbrida | 0,69 | **0,73** | 0,18 | 0,80 | 0,64 | 31/65 |
| MMR sobre a vetorial | 0,60 | 0,46 | **0,64** | 0,80 | 0,58 | 25/65 |

A melhor foi a **híbrida com os complementos**: 41 perguntas completas, contra 30 da vetorial. A híbrida sozinha já ganha bastante nas `v*` e nas booleanas, mas perde nas categóricas, porque "escolas públicas" não tem palavra em comum com "Dependência Administrativa". O complemento resolve boa parte disso. Ele foi escrito olhando os erros do próprio gabarito, então esse ganho é um pouco otimista.

O resto não compensou. O reranker acha mais `v*`, mas perde nas booleanas e nas outras colunas dos equipamentos, e fica com menos perguntas completas que a própria híbrida que ele reordena (31 contra 38), além de custar um modelo de 2,3 GB. O MMR piora: ao evitar propriedades parecidas, ele tira do top-20 propriedades vizinhas de que a pergunta precisa.

## Estrutura

```
rag_buscas/
├── comparar_buscas.py
├── output/           # CSVs gerados (não versionado)
└── resultados/       # rodada usada na monografia
```

## Referências

- [sentence-transformers — Documentação](https://sbert.net)
- [bge-reranker-v2-m3 — Página do modelo](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [rank_bm25 — GitHub](https://github.com/dorianbrown/rank_bm25)
- [Snowball — Stemmer de português](https://snowballstem.org)
- [LangChain — Documentação](https://docs.langchain.com/oss/python/langchain/overview)
- [Chroma — Busca híbrida](https://docs.trychroma.com/cloud/search-api/hybrid-search)
