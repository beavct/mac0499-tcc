"""
Valida as queries SQL (PostgreSQL) e Cypher (Neo4j) executando-as e comparando:
  1. Se ambas rodam sem erro
  2. Se o número de linhas retornadas é igual
  3. Se colunas numéricas agregadas (counts/sums) batem entre as duas

Uso:
  python validar_queries.py                    # roda todas
  python validar_queries.py ed_basica          # roda só educação
  python validar_queries.py saude              # roda só saúde
  python validar_queries.py intersetorial      # roda só intersetorial
  python validar_queries.py ed_basica 5        # roda só a Q5 de educação

Resultados são salvos em output/resultados_validacao.csv
"""
import os
import sys
import csv
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "compartilhado"))
from db import get_pg_connection, get_neo4j_driver

PERGUNTAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "perguntas")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def find_query_files(eixo, numero=None):
    """Retorna lista de dicts com paths das queries SQL e Cypher."""
    base = os.path.join(PERGUNTAS_DIR, eixo)
    sql_dir = os.path.join(base, "postgreSQL")
    cypher_dir = os.path.join(base, "neo4j-cypher")

    queries = []
    if not os.path.isdir(sql_dir):
        return queries

    for f in sorted(os.listdir(sql_dir)):
        if not f.startswith("pergunta_") or not f.endswith(".sql"):
            continue
        n = int(f.replace("pergunta_", "").replace(".sql", ""))
        if numero and n != numero:
            continue

        sql_path = os.path.join(sql_dir, f)
        cypher_path = os.path.join(cypher_dir, f.replace(".sql", ".cypher"))

        queries.append({
            "eixo": eixo,
            "numero": n,
            "sql_path": sql_path,
            "cypher_path": cypher_path if os.path.exists(cypher_path) else None,
        })

    return sorted(queries, key=lambda x: x["numero"])


def run_sql(conn, sql_path):
    """Executa query SQL e retorna (colunas, rows, tempo_ms, erro)."""
    with open(sql_path, "r") as f:
        query = f.read()

    cur = conn.cursor()
    start = time.time()
    try:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        elapsed = (time.time() - start) * 1000
        return columns, rows, elapsed, None
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        conn.rollback()
        return [], [], elapsed, str(e)


def run_cypher(driver, cypher_path):
    """Executa query Cypher e retorna (colunas, rows, tempo_ms, erro)."""
    with open(cypher_path, "r") as f:
        query = f.read()

    lines = [l for l in query.split("\n") if not l.strip().startswith("//")]
    query = "\n".join(lines)

    start = time.time()
    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            if records:
                columns = list(records[0].keys())
                rows = [tuple(r.values()) for r in records]
            else:
                columns, rows = [], []
            elapsed = (time.time() - start) * 1000
            return columns, rows, elapsed, None
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return [], [], elapsed, str(e)


def extract_numeric_totals(columns, rows):
    """Extrai somas das colunas numéricas para comparação."""
    totals = {}
    if not rows:
        return totals

    for i, col in enumerate(columns):
        values = []
        for row in rows:
            val = row[i]
            if isinstance(val, (int, float)) and val is not None:
                values.append(val)
        if values:
            totals[col] = sum(values)

    return totals


def compare_results(sql_cols, sql_rows, cypher_cols, cypher_rows):
    """
    Compara resultados de SQL e Cypher.
    Retorna (status, detalhes).
    """
    # Compara número de linhas
    row_match = len(sql_rows) == len(cypher_rows)

    # Extrai totais numéricos
    sql_totals = extract_numeric_totals(sql_cols, sql_rows)
    cypher_totals = extract_numeric_totals(cypher_cols, cypher_rows)

    # Tenta casar colunas numéricas por valor (nomes podem ser diferentes)
    sql_values = sorted(sql_totals.values())
    cypher_values = sorted(cypher_totals.values())

    # Compara os totais mais relevantes (primeiros valores numéricos)
    numeric_match = None
    if sql_values and cypher_values:
        # Compara com tolerância de 1% (float rounding)
        matches = 0
        for sv in sql_values[:5]:
            for cv in cypher_values[:5]:
                if sv == 0 and cv == 0:
                    matches += 1
                elif sv != 0 and abs(sv - cv) / abs(sv) < 0.01:
                    matches += 1
        numeric_match = matches > 0

    # Determina status
    if row_match and (numeric_match is None or numeric_match):
        status = "OK"
    elif row_match and not numeric_match:
        status = "DIVERGENTE_VALORES"
    elif not row_match and numeric_match:
        status = "DIVERGENTE_LINHAS"
    else:
        status = "DIVERGENTE"

    detalhes = (
        f"SQL={len(sql_rows)} linhas | Cypher={len(cypher_rows)} linhas"
    )

    return status, detalhes


def save_query_results(eixo, numero, engine, columns, rows):
    """Salva resultado individual de uma query em CSV pra inspeção manual."""
    dir_path = os.path.join(OUTPUT_DIR, "resultados_por_query", eixo)
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, f"Q{numero:02d}_{engine}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows[:100]:  # Limita a 100 linhas pra não explodir o disco
            writer.writerow(row)


def main():
    eixos = ["ed_basica", "saude", "intersetorial"]
    numero = None

    if len(sys.argv) > 1:
        eixos = [sys.argv[1]]
    if len(sys.argv) > 2:
        numero = int(sys.argv[2])

    print("Conectando ao PostgreSQL...")
    pg_conn = get_pg_connection()
    print("Conectando ao Neo4j...")
    neo4j_driver = get_neo4j_driver()

    resultados = []
    total_ok = 0
    total_divergente = 0
    total_erro = 0

    for eixo in eixos:
        queries = find_query_files(eixo, numero)
        if not queries:
            print(f"\n[SKIP] Nenhuma query encontrada para '{eixo}'")
            continue

        print(f"\n{'=' * 60}")
        print(f" {eixo.upper()} ({len(queries)} queries)")
        print(f"{'=' * 60}")

        for q in queries:
            label = f"{eixo}/Q{q['numero']:02d}"
            print(f"\n--- {label} ---")

            # SQL
            sql_cols, sql_rows, sql_ms, sql_err = run_sql(pg_conn, q["sql_path"])
            if sql_err:
                print(f"  [SQL] ERRO ({sql_ms:.0f}ms): {sql_err[:120]}")
                total_erro += 1
            else:
                print(f"  [SQL] {len(sql_rows)} linhas em {sql_ms:.0f}ms")
                save_query_results(eixo, q["numero"], "sql", sql_cols, sql_rows)

            # Cypher
            if q["cypher_path"]:
                cypher_cols, cypher_rows, cypher_ms, cypher_err = run_cypher(
                    neo4j_driver, q["cypher_path"]
                )
                if cypher_err:
                    print(f"  [Cypher] ERRO ({cypher_ms:.0f}ms): {cypher_err[:120]}")
                    total_erro += 1
                else:
                    print(f"  [Cypher] {len(cypher_rows)} linhas em {cypher_ms:.0f}ms")
                    save_query_results(eixo, q["numero"], "cypher", cypher_cols, cypher_rows)
            else:
                cypher_cols, cypher_rows, cypher_ms, cypher_err = [], [], 0, "arquivo não encontrado"
                print(f"  [Cypher] SKIP: arquivo .cypher não encontrado")

            # Comparação
            if not sql_err and not cypher_err and q["cypher_path"]:
                status, detalhes = compare_results(
                    sql_cols, sql_rows, cypher_cols, cypher_rows
                )
                emoji = "✓" if status == "OK" else "⚠"
                print(f"  [{emoji}] {status}: {detalhes}")
                if status == "OK":
                    total_ok += 1
                else:
                    total_divergente += 1
            elif sql_err or cypher_err:
                status = "ERRO"
                detalhes = sql_err or cypher_err
            else:
                status = "SKIP"
                detalhes = ""

            resultados.append({
                "eixo": eixo,
                "query": q["numero"],
                "status": status,
                "sql_linhas": len(sql_rows),
                "sql_ms": round(sql_ms, 1),
                "sql_erro": sql_err or "",
                "cypher_linhas": len(cypher_rows),
                "cypher_ms": round(cypher_ms, 1),
                "cypher_erro": cypher_err or "",
                "detalhes": detalhes if isinstance(detalhes, str) else "",
            })

    # Salvar resumo
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "resultados_validacao.csv")
    if resultados:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
            writer.writeheader()
            writer.writerows(resultados)

    # Resumo final
    print(f"\n{'=' * 60}")
    print(f" RESUMO")
    print(f"   OK (linhas batem):    {total_ok}")
    print(f"   DIVERGENTE:           {total_divergente}")
    print(f"   ERRO:                 {total_erro}")
    print(f"   Total:                {len(resultados)}")
    print(f"")
    print(f" Resultados salvos em: {output_path}")
    print(f" CSVs por query em:    {OUTPUT_DIR}/resultados_por_query/")
    print(f"{'=' * 60}")

    pg_conn.close()
    neo4j_driver.close()


if __name__ == "__main__":
    main()
