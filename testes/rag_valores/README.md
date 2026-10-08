# Teste do RAG: valores das colunas no texto indexado

Mede se colocar os valores das colunas no texto que o Chroma busca (ex.: `tp_dependencia`: 1 = Federal, 2 = Estadual, 3 = Municipal, 4 = Privada) ajuda ou atrapalha o RAG do [`text2cypher/`](../../text2cypher) a encontrar as propriedades certas pra cada pergunta.

## Como funciona

O script compara três versões do texto de cada propriedade do dicionário:

| Versão | Texto buscado |
|--------|---------------|
| **A** | `tema: descrição` |
| **B** | A + os valores das colunas que não são booleanas (é o que o workflow usa) |
| **C** | A + os valores de todas as colunas, inclusive as booleanas (`true = Sim, false = Não`) |

O **gabarito** sai das próprias consultas do benchmark: pra cada pergunta de [`perguntas/`](../../perguntas), são as propriedades do dicionário que o Cypher correto usa. 65 das 66 consultas usam alguma, somando 144 propriedades.

Pra cada versão, o script transforma os textos e as perguntas em vetores e pega as 20 propriedades mais parecidas com cada pergunta. A métrica é o **recall@k** (k = 5, 10 e 20): das propriedades do gabarito, quantas aparecem entre as `k` primeiras.

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

Os modelos testados ficam no `PREFIXOS` do script: o `paraphrase-multilingual-MiniLM-L12-v2`, usado no começo do projeto, e o `multilingual-e5-base`, escolhido depois pelo [teste dos modelos](../rag_modelos). Pra cada um, o script imprime a tabela de recall e grava em `output/<modelo>/`:
- `recall.csv`: recall por grupo, versão e `k`;
- `posicoes.csv`: a posição de cada propriedade do gabarito em cada versão (vazio = fora do top-20).

Os grupos e a lista `CODIGOS_ESPECIAIS` ficam neste script, e o [teste dos modelos](../rag_modelos) e o [teste das formas de busca](../rag_buscas) usam os mesmos.

## Resultados

As rodadas usadas na monografia estão em `resultados/`, uma pasta por modelo. Recall@20:

| Grupo | n | MiniLM A | MiniLM B | MiniLM C | e5 A | e5 B | e5 C |
|-------|---|---:|---:|---:|---:|---:|---:|
| categórica | 11 | 0,18 | **0,36** | 0,36 | 0,00 | **0,64** | 0,64 |
| booleana | 41 | 0,39 | **0,39** | 0,29 | **0,80** | 0,76 | 0,73 |
| `v*` (Censo) | 59 | 0,19 | 0,19 | 0,24 | 0,51 | 0,51 | 0,53 |
| outras dos equipamentos | 33 | 0,67 | 0,67 | 0,70 | **0,76** | **0,76** | 0,70 |
| todas | 144 | 0,35 | **0,37** | 0,37 | 0,61 | **0,65** | 0,63 |

- Nas **categóricas**, os valores fazem a maior diferença: com o e5, sem eles nenhuma é encontrada (0,00 contra 0,64), e com o MiniLM o recall dobra. A palavra da pergunta ("municipal", "privadas") só aparece no texto quando os valores estão lá.
- Nas **booleanas**, pôr os valores piora. O mesmo `true = Sim, false = Não` em centenas de textos deixa todos parecidos, e com o MiniLM o recall@10 cai de 0,39 pra 0,17.
- No geral, a **versão B** é a melhor com os dois modelos, e por isso o workflow usa ela.
- Nas **outras dos equipamentos**, B e A empatam nos dois modelos. Nenhuma das 28 colunas com códigos especiais está no gabarito, então o teste não mede se esses códigos ajudam a achar as próprias colunas. O [teste das formas de busca](../rag_buscas) tira os códigos especiais do texto e mostra que eles também não atrapalham as outras.

## Estrutura

```
rag_valores/
├── comparar_textos.py
├── output/        # CSVs gerados, uma pasta por modelo (não versionado)
└── resultados/    # rodadas usadas na monografia
```
