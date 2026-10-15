# Validação — SQL vs. Cypher

Script que roda cada consulta do benchmark ([`../../perguntas/`](../../perguntas)) nos dois bancos e confere se o SQL (PostgreSQL) e o Cypher (Neo4j) devolvem o mesmo resultado.

## Como funciona

Para cada consulta, o script:

1. executa a versão SQL e a versão Cypher;
2. compara o número de linhas;
3. compara os valores linha a linha. Os números são arredondados em 2 casas, e os floats são comparados com tolerância (0,01 absoluta ou 0,5% relativa), para absorver diferenças de arredondamento e de cálculo de distância entre os dois bancos. As linhas são pareadas pelos campos que não são números, então a ordem em que cada banco devolve não importa.

Cada consulta termina com um destes status:

| Status | Quando |
|--------|--------|
| `OK` | mesmas linhas e mesmos valores |
| `DIVERGENTE_LINHAS` | número de linhas diferente |
| `DIVERGENTE_VALORES` | mesmo número de linhas, mas algum valor diferente |
| `ERRO` | uma das duas versões deu erro ao rodar |
| `SKIP` | nenhuma das duas rodou (ex.: arquivo faltando) |

## Como rodar

Com os dois bancos carregados com o mesmo recorte (ver o README da raiz):

```bash
cd testes/validacao
python validar_queries.py                 # todas
python validar_queries.py ed_basica       # só um eixo
python validar_queries.py saude 5         # só uma consulta
```

Os resultados vão para `output/`:
- `resultados_validacao.csv`: uma linha por consulta, com o status e os detalhes;
- `resultados_por_query/<eixo>/`: o resultado de cada consulta em cada banco, para conferir na mão.
