# Testes de Desempenho — PostgreSQL vs. Neo4j

Scripts que medem o desempenho das consultas do benchmark nos dois bancos, para comparar o modelo relacional (PostgreSQL/PostGIS) com o modelo em grafos (Neo4j).

## Como funciona

Cada query é executada **N vezes**. A **primeira execução** de cada query é marcada como aquecimento (`warmup`) e descartada da análise, servindo apenas para popular o cache; as demais (execuções quentes) são as que alimentam os gráficos. Todas ficam registradas no CSV.

Para cada execução, são coletadas:

| Métrica | PostgreSQL | Neo4j |
|---------|-----------|-------|
| **Latência** | `Execution Time` de `EXPLAIN (ANALYZE, BUFFERS)` | `result_available_after + result_consumed_after` (Bolt) |
| **Linhas retornadas** | `Actual Rows` do nó raiz | contagem de registros |
| **Memória de trabalho** | `Sort Space Used` + `Peak Memory Usage` dos nós do plano | `GlobalMemory` do `PROFILE` |

As duas métricas comparadas — **latência** (ms) e **memória de trabalho** (KB) — são extraídas **do próprio plano de execução reportado pelo banco** (`EXPLAIN (ANALYZE, BUFFERS)` no PostgreSQL, `PROFILE` no Neo4j), não do sistema operacional. Isso remove, da latência, o custo de rede e de serialização do lado cliente. As colunas de I/O (`buffers`/`page cache`) e de `dbHits` continuam gravadas no CSV, mas **não são usadas na análise** — ver a nota sobre escopo mais abaixo.

### Memória de trabalho por consulta

A **memória de trabalho** é lida do próprio plano de execução, medindo o trabalho **daquela** consulta e não o consumo do processo do servidor (que, no PostgreSQL, é multiprocesso e compartilha os `shared_buffers` entre conexões, e no Neo4j corresponde à JVM inteira). No PostgreSQL é a memória usada pelos nós de ordenação (`Sort Space Used`, quando em memória) e de *hash*/agregação (`Peak Memory Usage`); no Neo4j é o `GlobalMemory` do `PROFILE`, o pico de memória de toda a consulta. Ambas são convertidas para KB no CSV (`mem_kb`).

## Como rodar

Pré-requisitos: os dois bancos carregados com o **mesmo recorte** de dados (ver README da raiz), e o ambiente virtual ativo.

```bash
cd testes/performance

# Rodar tudo
python bench_postgres.py
python bench_neo4j.py

# Ou por eixo / query específica
python bench_postgres.py saude
python bench_neo4j.py ed_basica 5
```

Os resultados são gravados em `output/`:
- `resultados_postgres.csv`
- `resultados_neo4j.csv`

Cada linha do CSV é uma execução (query × repetição), com todas as métricas.

## Observações sobre a medição

- **Só estado quente (sem análise frio vs. quente):** a 1ª execução de cada query serve apenas para aquecer o cache e é descartada; a análise usa somente as execuções quentes. Não se compara cache frio vs. quente porque não há reset de cache entre as consultas — como muitas compartilham as mesmas tabelas, só a primeira consulta do benchmark seria de fato "fria", e as demais já encontrariam o cache populado pelas anteriores. Uma comparação frio/quente honesta exigiria reiniciar os bancos entre medições.
- **I/O e `dbHits` fora da análise:** essas métricas continuam gravadas no CSV, mas não entram nos gráficos. O I/O de cache depende do mesmo problema de cache acima, e as contagens de acesso usam unidades distintas nos dois bancos (blocos no PostgreSQL, páginas de *page cache* / `dbHits` no Neo4j), sem equivalência direta. A comparação se concentra em **latência** e **memória de trabalho**, que têm a mesma unidade nos dois sistemas.
- **Sobrecusto de instrumentação:** tanto `EXPLAIN ANALYZE` quanto `PROFILE` adicionam um sobrecusto de medição à execução (a documentação do PostgreSQL registra que o `ANALYZE` pode tornar a consulta sensivelmente mais lenta). Esse sobrecusto atua na mesma direção nos dois bancos, de modo que a comparação relativa entre eles permanece válida, ainda que os valores absolutos fiquem um pouco acima do tempo de execução sem instrumentação.
- **Justiça da comparação:** ambos rodam localmente, sobre o mesmo recorte territorial, e as métricas são as reportadas internamente por cada banco, não medidas do lado cliente nem do processo do sistema operacional.

## Estrutura

```
performance/
├── comum.py            # descoberta de queries, agrupamento por operação, saída CSV
├── bench_postgres.py   # benchmark do PostgreSQL (EXPLAIN ANALYZE BUFFERS)
├── bench_neo4j.py      # benchmark do Neo4j (PROFILE)
├── analise.py          # lê os CSVs e gera os gráficos comparativos
└── output/             # CSVs e gráficos gerados (não versionado)
    └── graficos/       # PDFs prontos para o LaTeX
```

## Gráficos

Depois de rodar os dois benchmarks, gere os gráficos a partir dos CSVs:

```bash
python analise.py
```

Os gráficos são salvos em `output/graficos/` como **PDF** (vetorial, ideal para o LaTeX). Para escolher quais gerar, edite a lista `GRAFICOS_ATIVOS` no início de `analise.py`. Os disponíveis são:

| Gráfico | O que mostra |
|---------|--------------|
| `latencia_por_grupo` | **Boxplot da latência de cada consulta, um arquivo por grupo, PG vs Neo4j — o conjunto central** |
| `memoria_por_grupo` | Boxplot da memória de trabalho de cada consulta, por grupo, PG vs Neo4j |
| `boxplot_latencia_por_operacao` | Visão agregada: distribuição das latências por tipo de operação, PG vs Neo4j |
| `boxplot_memoria_por_operacao` | Visão agregada: distribuição da memória de trabalho por tipo de operação, PG vs Neo4j |

### Gráficos por grupo de operação (o conjunto central)

`latencia_por_grupo` e `memoria_por_grupo` geram **um arquivo por grupo de operação**
(definido em `../../perguntas/grupos.json`), dispondo as consultas do grupo no eixo x e
comparando PostgreSQL e Neo4j em cada uma. As duas saem como **boxplots pareados** — cada
caixa resume a variação entre as execuções (repetições) daquela consulta.

Grupos grandes (filtro e agregação têm 21 consultas) são divididos em várias figuras,
para as caixas ficarem legíveis. O limite é `MAX_QUERIES_POR_FIGURA` (padrão: 12) no
início da seção de gráficos por grupo em `analise.py`; ao dividir, o nome do arquivo
recebe o número da página (ex.: `grupo_latencia_filtro_p1.pdf`, `..._p2.pdf`).

Os gráficos `boxplot_latencia_por_operacao` e `boxplot_memoria_por_operacao` são a versão
agregada: em vez de uma caixa por consulta, cada grupo de operação vira uma caixa por
banco (com um ponto por consulta sobreposto), e a função imprime no console uma tabela de
média ± desvio padrão por grupo. Um cobre a latência; o outro, a memória de trabalho.

## Dependências

Além das já usadas pelo ETL (`psycopg2`, `neo4j`, `python-dotenv`), os testes de desempenho usam apenas:

- `matplotlib` — geração dos gráficos

As métricas de latência, I/O e memória vêm do próprio plano de execução de cada banco.

## Referências

Documentação oficial que fundamenta a coleta de cada métrica:

- **PostgreSQL — `EXPLAIN`** (`ANALYZE`, `BUFFERS`, `TIMING`): tempo de execução, blocos servidos pelo cache (*shared hit*) vs. lidos (*shared read*) e sobrecusto de instrumentação. <https://www.postgresql.org/docs/current/sql-explain.html>
- **PostgreSQL — Using `EXPLAIN`**: estatísticas de ordenação e *hash* (método em memória ou disco e memória de trabalho utilizada). <https://www.postgresql.org/docs/current/using-explain.html>
- **Neo4j — Execution plans**: `PROFILE`, *db hits*, *page cache hits/misses* e a memória de pico por operador e da consulta. <https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/>
- **Neo4j — Bolt Protocol (Messaging)**: metadados `t_first` / `t_last` (expostos pelo *driver* como `result_available_after` / `result_consumed_after`), os tempos internos do servidor. <https://neo4j.com/docs/bolt/current/bolt/message/>
