# Teste do RAG: valores das colunas no texto indexado

Mede se colocar os valores das colunas no texto que o Chroma busca (ex.: `tp_dependencia`: 1 = Federal, 2 = Estadual, 3 = Municipal, 4 = Privada) ajuda ou atrapalha o RAG do [`text2cypher/`](../../text2cypher) a encontrar as propriedades certas pra cada pergunta.

## Como funciona

O script compara três versões do texto de cada propriedade do dicionário:

| Versão | Texto buscado |
|--------|---------------|
| **A** | `tema: descrição` |
| **B** | A + os valores só das colunas de código (é o que o workflow usa) |
| **C** | A + os valores de todas as colunas, inclusive as booleanas (`true = Sim, false = Não`) |

O **gabarito** sai das próprias consultas do benchmark: pra cada pergunta de [`perguntas/`](../../perguntas), são as propriedades do dicionário que o Cypher correto usa. 65 das 66 consultas usam alguma, somando 144 propriedades.

Pra cada versão, o script transforma os textos e as perguntas em vetores e pega as 20 propriedades mais parecidas com cada pergunta. A métrica é o **recall@k** (k = 5, 10 e 20): das propriedades do gabarito, quantas aparecem entre as `k` primeiras. Os resultados saem por tipo de propriedade (`v*` do Censo, código, booleana e outras) e, nas colunas de código, separados entre as perguntas que citam uma das categorias ("escolas **municipais**") e as que não citam.

A busca é **exata** (similaridade de cosseno com todos os textos), então o resultado é o mesmo toda vez que roda. O índice HNSW do workflow é aproximado, mas coincide em 99% com a busca exata no top-20.

## Como rodar

Pré-requisito: o dicionário gerado pela etapa 01 (`text2cypher/dicionario/corpus/variaveis.json`, ver [`text2cypher/README.md`](../../text2cypher/README.md)). O script não usa o PostgreSQL nem o Neo4j.

```bash
cd testes/rag_categorias
python experimento.py                                # modelo do text2cypher/config.py
python experimento.py intfloat/multilingual-e5-base  # outro modelo
```

Ele imprime a tabela de recall e grava em `output/<modelo>/`:
- `recall.csv`: recall por grupo, versão e `k`;
- `posicoes.csv`: a posição de cada propriedade do gabarito em cada versão (vazio = fora do top-20).

## Resultados

As rodadas usadas na monografia estão em `resultados/`, uma pasta por modelo. Recall@20 com o MiniLM (`paraphrase-multilingual-MiniLM-L12-v2`):

| Grupo | n | A | B | C |
|-------|---|---|---|---|
| código (`tp_*`) | 11 | 0,18 | **0,36** | 0,36 |
| booleana | 41 | 0,39 | **0,39** | 0,29 |
| `v*` (Censo) | 59 | 0,19 | 0,19 | 0,24 |
| todas | 144 | 0,35 | **0,37** | 0,37 |

Nas colunas de código, os valores dobram o recall, porque a palavra da pergunta ("municipal") só aparece no texto quando os valores estão lá. Nas booleanas, a versão C derruba o recall (de 0,39 pra 0,17 no recall@10): o mesmo `true = Sim, false = Não` em centenas de textos deixa todos parecidos. Por isso o workflow usa a versão B.

Depois, o [teste dos modelos](../rag_modelos) mostrou que o `multilingual-e5-base` recupera bem melhor, e o experimento foi rodado de novo com ele, pra ver se a conclusão mudava. Recall@20:

| Grupo | n | A | B | C |
|-------|---|---|---|---|
| código (`tp_*`) | 11 | 0,00 | **0,64** | 0,64 |
| booleana | 41 | **0,80** | 0,76 | 0,73 |
| `v*` (Censo) | 59 | 0,51 | 0,51 | 0,53 |
| todas | 144 | 0,61 | **0,65** | 0,63 |

A conclusão se mantém: sem os valores, nenhuma coluna de código é encontrada, e pôr os valores também nas booleanas piora. A versão B continua sendo a melhor no geral.

## Estrutura

```
rag_categorias/
├── experimento.py
├── output/        # CSVs gerados, uma pasta por modelo (não versionado)
└── resultados/    # rodadas usadas na monografia
```
