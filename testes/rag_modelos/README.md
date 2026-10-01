# Teste do RAG: modelos de embedding

Compara modelos de embedding abertos e multilíngues pra ver qual recupera melhor as propriedades do dicionário do [`text2cypher/`](../../text2cypher) a partir das perguntas.

## Como funciona

O teste usa o mesmo gabarito, a mesma busca exata e a mesma métrica do [teste das categorias](../rag_categorias): pra cada uma das 65 consultas de [`perguntas/`](../../perguntas) que usam o dicionário, conta quantas das propriedades do Cypher correto aparecem entre as `k` mais parecidas com a pergunta (**recall@k**, com k = 5, 10 e 20). O texto indexado é o da versão B (tema, descrição e os valores das colunas de código), que é o que o workflow usa.

Além do recall, o script conta as **perguntas completas**: aquelas em que todas as propriedades do gabarito estão no top-20. É o caso em que o modelo gerador recebe tudo de que precisa.

Os modelos comparados:

| Modelo | Parâmetros | Dimensão | Prefixos |
|--------|-----------:|---------:|----------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 118M | 384 | nenhum |
| `paraphrase-multilingual-mpnet-base-v2` | 278M | 768 | nenhum |
| `multilingual-e5-small` | 118M | 384 | `query: ` / `passage: ` |
| `multilingual-e5-base` | 278M | 768 | `query: ` / `passage: ` |
| `multilingual-e5-large` | 560M | 1024 | `query: ` / `passage: ` |
| `bge-m3` | 568M | 1024 | nenhum |
| `Qwen3-Embedding-0.6B` | 600M | 1024 | instrução na pergunta |

Cada modelo recebe os prefixos que a sua página no Hugging Face (o *model card*) pede. Os E5 foram treinados com `query: ` nas perguntas e `passage: ` nos textos, e a [página do modelo](https://huggingface.co/intfloat/multilingual-e5-base) avisa que sem eles o resultado piora.

## Como rodar

Pré-requisito: o dicionário gerado pela etapa 01 (`text2cypher/dicionario/corpus/variaveis.json`, ver [`text2cypher/README.md`](../../text2cypher/README.md)). O script não usa o PostgreSQL nem o Neo4j.

```bash
cd testes/rag_modelos
python comparar_modelos.py                 # baixa e testa os sete modelos
python comparar_modelos.py --limpar-cache  # apaga cada modelo do cache depois de usar
```

Os modelos juntos ocupam uns 9 GB no cache do Hugging Face (`~/.cache/huggingface/hub`). Se o disco estiver muito cheio, use o `--limpar-cache`: ele apaga cada modelo depois do teste, menos o que está no `config.py`.

Ele imprime a tabela e grava em `output/`:
- `recall.csv`: recall por modelo, grupo e `k` e as perguntas completas;
- `posicoes.csv`: a posição de cada propriedade do gabarito em cada modelo (vazio = fora do top-20).

## Resultados

A rodada usada na monografia está em `resultados/`. Recall@20 por grupo de propriedade:

| Modelo | todas | `v*` (Censo) | código | booleana | outras | completas |
|--------|------:|-------------:|-------:|---------:|-------:|----------:|
| MiniLM | 0,37 | 0,19 | 0,36 | 0,39 | 0,67 | 12/65 |
| mpnet | 0,41 | 0,32 | 0,09 | 0,44 | 0,64 | 15/65 |
| e5-small | 0,58 | 0,59 | 0,09 | 0,78 | 0,45 | 24/65 |
| **e5-base** | 0,65 | 0,51 | 0,64 | 0,76 | 0,76 | 30/65 |
| e5-large | 0,65 | 0,69 | 0,27 | 0,68 | 0,67 | 31/65 |
| bge-m3 | 0,49 | 0,53 | 0,18 | 0,46 | 0,55 | 20/65 |
| Qwen3 | **0,67** | 0,53 | 0,64 | **0,88** | 0,70 | **32/65** |

O Qwen3 tem o maior recall, mas o `multilingual-e5-base` fica praticamente empatado (duas perguntas completas a menos), é menor e não depende de uma instrução escrita por nós. Os dois sobem o recall de 0,37 pra perto de 0,65 e mais que dobram as perguntas completas. 

## Estrutura

```
rag_modelos/
├── comparar_modelos.py
├── output/        # CSVs gerados (não versionado)
└── resultados/    # rodada usada na monografia
```
