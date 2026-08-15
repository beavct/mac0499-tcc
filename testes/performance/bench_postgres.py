"""
Benchmark de desempenho das consultas SQL no PostgreSQL.

Para cada query do benchmark, executa N vezes e registra, por execução:
  - latência: tempo interno de execução reportado por EXPLAIN ANALYZE
    ("Execution Time"), que exclui o planejamento e o custo de rede
  - linhas retornadas
  - I/O: blocos servidos pelo cache (shared hit) vs. lidos (shared read)
  - memória de trabalho da consulta: pico somado dos nós de ordenação e de
    hash do plano ("Sort Space Used" / "Peak Memory Usage")

A 1ª execução de cada query é o aquecimento (warmup): fica registrada no CSV,
mas é descartada na análise, que usa só as execuções quentes.

Ao final de cada query, o plano de execução em texto (EXPLAIN ANALYZE) também é
salvo em output/planos/postgres/, para inspecionar os operadores escolhidos pelo
planejador (Nested Loop, Hash Join, Index Scan etc.). Essa captura ocorre fora
do laço de medição e não afeta as latências registradas.

Uso:
  python bench_postgres.py                 # todas as queries
  python bench_postgres.py ed_basica       # só um eixo
  python bench_postgres.py ed_basica 5     # só a Q5 de educação
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "compartilhado"))
from db import get_pg_connection

import comum

COLUNAS = comum.COLUNAS_BASE + ["buffers_hit", "buffers_read"]


def coletar_memoria_kb(no):
    """Soma, recursivamente, a memória de trabalho dos nós do plano (em KB).

    Considera a ordenação em memória ("Sort Space Used") e os nós de hash e
    agregação ("Peak Memory Usage"). Ignora ordenações que extravasam para o
    disco, pois o interesse é a memória de trabalho.
    """
    total = 0
    if no.get("Sort Space Type") == "Memory":
        total += no.get("Sort Space Used", 0)
    total += no.get("Peak Memory Usage", 0)
    for filho in no.get("Plans", []):
        total += coletar_memoria_kb(filho)
    return total


def executar_com_metricas(cur, query):
    """
    Executa a query com EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) e extrai
    latência interna, linhas, buffers e memória de trabalho.
    """
    cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
    plano = cur.fetchone()[0][0]  # JSON do plano

    no_raiz = plano["Plan"]
    return {
        "latencia_ms": round(plano["Execution Time"], 3),
        "linhas": no_raiz.get("Actual Rows", 0),
        # a memória de trabalho é reportada por nó (não é cumulativa), então
        # somamos a árvore; já os buffers do PostgreSQL são acumulados no nó
        # raiz (o pai inclui os filhos), então basta lê-los do topo do plano.
        "mem_kb": coletar_memoria_kb(no_raiz),
        "buffers_hit": no_raiz.get("Shared Hit Blocks", 0),
        "buffers_read": no_raiz.get("Shared Read Blocks", 0),
    }


def capturar_plano_texto(cur, query):
    """Devolve o plano de execução em texto (EXPLAIN ANALYZE, com buffers).

    É o formato legível do PostgreSQL, que nomeia os operadores do plano
    (Nested Loop, Hash Join, Index Scan using..., Seq Scan on...). Executa a
    query mais uma vez, então é chamado fora do laço de medição.
    """
    cur.execute(f"EXPLAIN (ANALYZE, BUFFERS) {query}")
    return "\n".join(linha[0] for linha in cur.fetchall())


def main():
    eixos = [sys.argv[1]] if len(sys.argv) > 1 else None
    numero = int(sys.argv[2]) if len(sys.argv) > 2 else None

    queries = comum.encontrar_queries("sql", "postgreSQL", eixos, numero)
    if not queries:
        print("Nenhuma query encontrada.")
        return

    conn = get_pg_connection()
    conn.autocommit = True
    resultados = []

    print(f"PostgreSQL — {len(queries)} queries, {comum.N_EXECUCOES} execuções cada\n")

    for q in queries:
        label = f"{q['eixo']}/Q{q['numero']:02d}"
        texto = comum.ler_query(q["caminho"])
        latencias_quentes = []

        for i in range(1, comum.N_EXECUCOES + 1):
            warmup = (i == 1)
            cur = conn.cursor()
            try:
                metricas = executar_com_metricas(cur, texto)
            except Exception as e:
                print(f"  [ERRO] {label} exec {i}: {str(e)[:100]}")
                break
            finally:
                cur.close()

            resultados.append({
                "banco": "postgresql",
                "eixo": q["eixo"],
                "query": q["numero"],
                "grupo": q["grupo"],
                "execucao": i,
                "warmup": warmup,
                "latencia_ms": metricas["latencia_ms"],
                "linhas": metricas["linhas"],
                "mem_kb": metricas["mem_kb"],
                "buffers_hit": metricas["buffers_hit"],
                "buffers_read": metricas["buffers_read"],
            })
            if not warmup:
                latencias_quentes.append(metricas["latencia_ms"])

        stats = comum.resumo_estatistico(latencias_quentes)
        if stats:
            print(f"  {label}: mediana {stats['mediana_ms']}ms "
                  f"(min {stats['min_ms']} / max {stats['max_ms']}) | {metricas['linhas']} linhas")

        # captura o plano de execução em texto (uma vez, fora da medição)
        try:
            cur = conn.cursor()
            plano_txt = capturar_plano_texto(cur, texto)
            cur.close()
            comum.salvar_plano("postgres", q["eixo"], q["numero"], plano_txt)
        except Exception as e:
            print(f"  [AVISO] plano {label}: {str(e)[:80]}")

    conn.close()
    comum.salvar_csv("resultados_postgres.csv", resultados, COLUNAS)


if __name__ == "__main__":
    main()
