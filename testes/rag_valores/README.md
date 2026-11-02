# RAG — valores das colunas no texto indexado

Mede se colocar os valores das colunas no texto que o Chroma busca (ex.: `tp_dependencia`: 1 = Federal, 2 = Estadual, 3 = Municipal, 4 = Privada) ajuda ou atrapalha o RAG do [`text2cypher/`](../../text2cypher) a encontrar as propriedades certas para cada pergunta.

## Como funciona

O script compara três versões do texto de cada propriedade do dicionário:

| Versão | Texto buscado |
|--------|---------------|
| **A** | `tema: descrição` |
| **B** | A + os valores das colunas que não são booleanas (é o que o workflow usa) |
| **C** | A + os valores de todas as colunas, inclusive as booleanas (`true = Sim, false = Não`) |

O gabarito sai das próprias consultas do benchmark: para cada pergunta de [`perguntas/`](../../perguntas), são as propriedades do dicionário que o Cypher correto usa. 65 das 66 consultas usam alguma, somando 144 propriedades.

Para cada versão, o script transforma os textos e as perguntas em vetores e pega as 20 propriedades mais parecidas com cada pergunta. A métrica é o **recall@k** (k = 5, 10 e 20): das propriedades do gabarito, quantas aparecem entre as `k` primeiras.

Os resultados saem separados em quatro grupos de propriedade:
- **`v*` (Censo)**: as variáveis do Censo, nos nós de setor, município etc.;
- **categórica**: colunas das escolas e dos equipamentos de saúde cujo valor é um código de categoria, como a `tp_dependencia`. No gabarito, só aparece a `tp_dependencia`, em 11 perguntas;
- **booleana**: colunas de sim ou não dos equipamentos, como `in_biblioteca`;
- **outras dos equipamentos**: as demais colunas dos equipamentos, como as contagens `qt_*`, o endereço e o bairro.

Algumas contagens e CNPJs também têm valores nos metadados, mas são **códigos especiais**, e não categorias: `88888` marca um valor extremo nas `qt_*`, e `99999999999999` marca um CNPJ sem declaração. Essas 28 colunas entram nos textos B e C com os valores, mas ficam no grupo "outras dos equipamentos". A lista desses códigos é a `CODIGOS_ESPECIAIS` do script.

Nas categóricas, o script também separa as perguntas que citam uma das categorias ("escolas **municipais**") das que não citam.

A busca é **exata** (similaridade de cosseno com todos os textos), então o resultado é o mesmo toda vez que roda. O índice HNSW do workflow é aproximado, mas coincide em 99% com a busca exata no top-20.

## Como rodar

Pré-requisito: o dicionário gerado pela etapa 01 (`text2cypher/dicionario/corpus/variaveis.json`, ver [`text2cypher/README.md`](../../text2cypher/README.md)). O script não usa o PostgreSQL nem o Neo4j.

```bash
cd testes/rag_valores
python comparar_textos.py                                # os dois modelos
python comparar_textos.py intfloat/multilingual-e5-base  # só um deles
```

Os modelos testados ficam no `PREFIXOS` do script. Para cada um, o script imprime a tabela de recall e grava em `output/<modelo>/`:
- `recall.csv`: recall por grupo, versão e `k`;
- `posicoes.csv`: a posição de cada propriedade do gabarito em cada versão (vazio = fora do top-20).

Os grupos e a lista `CODIGOS_ESPECIAIS` ficam neste script, e o [teste dos modelos](../rag_modelos) e o [teste das formas de busca](../rag_buscas) usam os mesmos.

## Resultados

As rodadas usadas na monografia estão em `resultados/`, uma pasta por modelo. Recall@20:

| Grupo | n | MiniLM A | MiniLM B | MiniLM C | e5 A | e5 B | e5 C |
|-------|---|---:|---:|---:|---:|---:|---:|
| categórica | 11 | 0,27 | 0,45 | **0,55** | 0,09 | **0,82** | **0,82** |
| booleana | 41 | **0,37** | **0,37** | 0,22 | **0,93** | **0,93** | 0,80 |
| `v*` (Censo) | 59 | 0,22 | 0,22 | **0,24** | **0,54** | **0,54** | 0,53 |
| outras dos equipamentos | 33 | **0,70** | **0,70** | **0,70** | **0,82** | **0,82** | 0,73 |
| todas | 144 | 0,38 | **0,39** | 0,36 | 0,68 | **0,74** | 0,67 |


## Estrutura

```
rag_valores/
├── comparar_textos.py
├── output/      ← CSVs gerados, uma pasta por modelo (não versionado)
└── resultados/  ← rodadas usadas na monografia
```

## Referências

- Reimers e Gurevych, *Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation*, EMNLP 2020 (MiniLM multilíngue)
- Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, arXiv:2402.05672, 2024
- [sentence-transformers — documentação](https://sbert.net)
