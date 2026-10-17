# RAG — modelos de embedding

Compara modelos de embedding abertos para ver qual recupera melhor as propriedades do dicionário do [`text2cypher/`](../../text2cypher) a partir das perguntas.

## Como funciona

O gabarito e as métricas são os do [teste dos valores](../rag_valores): o **recall@k** das propriedades do Cypher correto nas 65 consultas que usam o dicionário e as **perguntas completas**, com todas as propriedades no top-20. Cada modelo é testado de duas formas:
- **vetorial:** só a busca vetorial exata, sobre o texto da versão B, o que isola o modelo;
- **híbrida:** a busca da Camada A, como no workflow (vetorial + BM25 pelo RRF, com os complementos de descrição; ver o [teste das formas de busca](../rag_buscas)).

Os modelos são os abertos de até ~600M de parâmetros avaliados no MTEB-BR (Stekel, 2026), um *benchmark* de *embeddings* em português brasileiro, entre eles os dos *workflows* de referência: o `all-MiniLM-L6-v2` (CyVerACT) e o `Qwen3-Embedding-0.6B` (LitE-SQL). O Serafim é treinado só em português, o `all-MiniLM-L6-v2`, só em inglês, e os demais são multilíngues.

| Modelo | Parâmetros | Dimensão | Prefixos |
|--------|-----------:|---------:|----------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 118M | 384 | nenhum |
| `paraphrase-multilingual-mpnet-base-v2` | 278M | 768 | nenhum |
| `multilingual-e5-small` | 118M | 384 | `query: ` / `passage: ` |
| `multilingual-e5-base` | 278M | 768 | `query: ` / `passage: ` |
| `multilingual-e5-large` | 560M | 1024 | `query: ` / `passage: ` |
| `bge-m3` | 568M | 1024 | nenhum |
| `Qwen3-Embedding-0.6B` | 600M | 1024 | instrução na pergunta |
| `all-MiniLM-L6-v2` | 23M | 384 | nenhum |
| `serafim-100m-portuguese-pt-sentence-encoder-ir` | 109M | 768 | nenhum |
| `embeddinggemma-300m` | 303M | 768 | `task: search result \| query: ` / `title: none \| text: ` |

Os prefixos são os que a página de cada modelo pede (os do EmbeddingGemma, a documentação do Google). O `embeddinggemma-300m` é restrito: é preciso aceitar a licença no Hugging Face e fazer login (`hf auth login`); sem isso, o script o pula.

## Como rodar

Pré-requisito: o dicionário gerado pela etapa 01 (`text2cypher/dicionario/corpus/variaveis.json`, ver [`text2cypher/README.md`](../../text2cypher/README.md)). O script não usa o PostgreSQL nem o Neo4j.

```bash
cd testes/rag_modelos
python comparar_modelos.py                     # todos os modelos (~9 GB de download)
python comparar_modelos.py --modelos e5,gemma  # só os que têm esses trechos no nome
python comparar_modelos.py --limpar-cache      # apaga cada modelo do cache depois de usar
```

Os resultados de cada modelo vão para `output/<modelo>/` assim que ele termina, e os de todos são juntados em `output/recall_<forma>.csv` e `output/posicoes_<forma>.csv` (forma = `vetorial` ou `hibrida`).

## Resultados

A rodada usada na monografia está em `resultados/`. Recall@20 por grupo de propriedade:

| Modelo | vetorial: todas | categórica | completas | híbrida: todas | categórica | completas |
|--------|------:|------:|------:|------:|------:|------:|
| paraphrase-multilingual-MiniLM-L12-v2 | 0,37 | 0,36 | 12 | 0,68 | 0,36 | 31 |
| paraphrase-multilingual-mpnet-base-v2 | 0,42 | 0,09 | 16 | 0,65 | 0,18 | 29 |
| multilingual-e5-small | 0,59 | 0,09 | 25 | 0,69 | 0,09 | 34 |
| **multilingual-e5-base** | 0,67 | **0,64** | 31 | **0,78** | **0,55** | **41** |
| multilingual-e5-large | 0,67 | 0,27 | 30 | 0,76 | 0,45 | **41** |
| bge-m3 | 0,52 | 0,18 | 22 | 0,70 | 0,27 | 35 |
| Qwen3-Embedding-0.6B | **0,69** | 0,55 | **33** | **0,78** | 0,45 | **41** |
| all-MiniLM-L6-v2 | 0,33 | 0,00 | 13 | 0,58 | 0,09 | 23 |
| serafim-100m-portuguese-pt-sentence-encoder-ir | 0,51 | 0,09 | 18 | 0,74 | 0,27 | 36 |
| embeddinggemma-300m | 0,55 | 0,27 | 24 | 0,74 | 0,36 | 36 |

Com a busca da Camada A, o `multilingual-e5-base`, o Qwen3 e o e5-large empatam em 41 perguntas completas, e o e5-base tem o maior recall nas categóricas. Por isso o workflow continua com ele: empata com os melhores, é menor que o Qwen3 e não depende de uma instrução escrita por nós. O `all-MiniLM-L6-v2`, do CyVerACT, fica por último nas duas formas de busca.

## Estrutura

```
rag_modelos/
├── comparar_modelos.py
├── output/        ← CSVs gerados (não versionado)
└── resultados/    ← rodada usada na monografia
```

## Referências

- Stekel, *MTEB-BR: A Text Embedding Benchmark for Brazilian Portuguese*, arXiv:2607.04581, 2026 (critério de escolha dos modelos)
- Androna et al., *CyVerACT*, Information Processing and Management, 2026 (`all-MiniLM-L6-v2`), e Piao, Lee e Park, *LitE-SQL*, EACL 2026 (`Qwen3-Embedding-0.6B`)
- Reimers e Gurevych, *Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation*, EMNLP 2020 (MiniLM e mpnet multilíngues)
- Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, arXiv:2402.05672, 2024
- Chen et al., *M3-Embedding*, arXiv:2402.03216, 2024 (bge-m3)
- Gomes et al., *Open Sentence Embeddings for Portuguese with the Serafim PT\* Encoders Family*, EPIA 2024 (Serafim)
- Schechter Vera et al., *EmbeddingGemma: Powerful and Lightweight Text Representations*, arXiv:2509.20354, 2025
- Zhang et al., *Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models*, arXiv:2506.05176, 2025
- [sentence-transformers — documentação](https://sbert.net)
