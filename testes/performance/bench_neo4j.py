"""
Benchmark de desempenho das consultas Cypher no Neo4j.

Para cada query do benchmark, executa N vezes e registra, por execução:
  - latência: tempo interno do servidor reportado pelo protocolo Bolt, somando
    o tempo até o primeiro registro (t_first / result_available_after) e até o
    último ser consumido (t_last / result_consumed_after)
  - linhas retornadas
  - I/O: db hits (operações de acesso de baixo nível) e page cache hits/misses
    (dados servidos da memória vs. lidos do disco)
  - memória de trabalho da consulta: memória global de pico reportada pelo
    PROFILE (GlobalMemory, em bytes)

A 1ª execução de cada query é o aquecimento (warmup): fica registrada no CSV,
mas é descartada na análise, que usa só as execuções quentes.

Uso:
  python bench_neo4j.py                 # todas as queries
  python bench_neo4j.py ed_basica       # só um eixo
  python bench_neo4j.py ed_basica 5     # só a Q5 de educação
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "compartilhado"))
from db import get_neo4j_driver

import comum

COLUNAS = comum.COLUNAS_BASE + ["db_hits", "page_cache_hits", "page_cache_misses"]


def coletar_db_hits(plano):
    """Soma recursivamente os dbHits de todos os operadores do plano PROFILE.

    No driver atual, o plano PROFILE vem como um dict com as chaves
    'dbHits' e 'children'.
    """
    total = plano.get("dbHits", 0)
    for filho in plano.get("children", []):
        total += coletar_db_hits(filho)
    return total


def coletar_page_cache(plano):
    """Soma recursivamente PageCacheHits e PageCacheMisses do plano PROFILE.

    Esses valores ficam em plano['args'] (nem todo operador os expõe).
    """
    args = plano.get("args", {})
    hits = args.get("PageCacheHits", 0)
    misses = args.get("PageCacheMisses", 0)
    for filho in plano.get("children", []):
        h, m = coletar_page_cache(filho)
        hits += h
        misses += m
    return hits, misses


def coletar_memoria_global_bytes(plano):
    """Maior GlobalMemory do plano PROFILE — a memória de pico de toda a consulta.

    Costuma vir só no operador raiz; percorremos a árvore e tomamos o máximo
    para não depender de onde o campo aparece.
    """
    maior = plano.get("args", {}).get("GlobalMemory", 0) or 0
    for filho in plano.get("children", []):
        maior = max(maior, coletar_memoria_global_bytes(filho))
    return maior


def executar_com_metricas(session, query):
    """
    Executa a query com PROFILE e extrai latência interna, linhas, I/O e memória.
    """
    result = session.run(f"PROFILE {query}")
    registros = list(result)          # consome o resultado
    resumo = result.consume()

    # latência interna do servidor (ms): tempo até o 1º resultado + consumo
    disponivel = resumo.result_available_after or 0
    consumido = resumo.result_consumed_after or 0
    latencia_ms = disponivel + consumido

    db_hits = coletar_db_hits(resumo.profile) if resumo.profile else 0
    pc_hits, pc_misses = coletar_page_cache(resumo.profile) if resumo.profile else (0, 0)
    mem_bytes = coletar_memoria_global_bytes(resumo.profile) if resumo.profile else 0

    return {
        "latencia_ms": latencia_ms,
        "linhas": len(registros),
        # bytes p/ KB, para alinhar a unidade com a memória de trabalho do PostgreSQL
        "mem_kb": round(mem_bytes / 1024, 1),
        "db_hits": db_hits,
        "page_cache_hits": pc_hits,
        "page_cache_misses": pc_misses,
    }


def main():
    eixos = [sys.argv[1]] if len(sys.argv) > 1 else None
    numero = int(sys.argv[2]) if len(sys.argv) > 2 else None

    queries = comum.encontrar_queries("cypher", "neo4j-cypher", eixos, numero)
    if not queries:
        print("Nenhuma query encontrada.")
        return

    driver = get_neo4j_driver()
    resultados = []

    print(f"Neo4j — {len(queries)} queries, {comum.N_EXECUCOES} execuções cada\n")

    for q in queries:
        label = f"{q['eixo']}/Q{q['numero']:02d}"
        texto = comum.ler_query(q["caminho"])
        latencias_quentes = []
        metricas = None

        with driver.session() as session:
            for i in range(1, comum.N_EXECUCOES + 1):
                warmup = (i == 1)
                try:
                    metricas = executar_com_metricas(session, texto)
                except Exception as e:
                    print(f"  [ERRO] {label} exec {i}: {str(e)[:100]}")
                    break

                resultados.append({
                    "banco": "neo4j",
                    "eixo": q["eixo"],
                    "query": q["numero"],
                    "grupo": q["grupo"],
                    "execucao": i,
                    "warmup": warmup,
                    "latencia_ms": metricas["latencia_ms"],
                    "linhas": metricas["linhas"],
                    "mem_kb": metricas["mem_kb"],
                    "db_hits": metricas["db_hits"],
                    "page_cache_hits": metricas["page_cache_hits"],
                    "page_cache_misses": metricas["page_cache_misses"],
                })
                if not warmup:
                    latencias_quentes.append(metricas["latencia_ms"])

        stats = comum.resumo_estatistico(latencias_quentes)
        if stats:
            print(f"  {label}: mediana {stats['mediana_ms']}ms "
                  f"(min {stats['min_ms']} / max {stats['max_ms']}) | {metricas['linhas']} linhas")

    driver.close()
    comum.salvar_csv("resultados_neo4j.csv", resultados, COLUNAS)


if __name__ == "__main__":
    main()
