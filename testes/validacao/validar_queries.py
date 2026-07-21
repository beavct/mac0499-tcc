"""
Valida as queries SQL (PostgreSQL) e Cypher (Neo4j) executando-as e comparando:
  1. Se ambas rodam sem erro
  2. Se o número de linhas retornadas é igual
  3. Se os valores batem linha a linha

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


# Tolerância para comparar floats (arredondamento entre PG e Neo4j, distâncias).
TOL_FLOAT = 0.01


def normalizar_valor(val):
    """Normaliza um valor de célula para comparação entre PG e Neo4j.

    - Números viram float arredondado.
    - Strings são trimadas.
    - None permanece None.
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    # Decimal do psycopg, ou outros numéricos
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return str(val).strip()


def normalizar_linha(row):
    return tuple(normalizar_valor(v) for v in row)


def floats_proximos(x, y):
    """True se dois floats são iguais dentro de tolerância absoluta OU relativa.

    A tolerância relativa (0,5%) acomoda diferenças de arredondamento em valores
    grandes — notadamente as distâncias em metros das consultas espaciais, em que
    PostGIS (elipsoide) e Neo4j (esfera) divergem alguns metros.
    """
    if abs(x - y) <= TOL_FLOAT:
        return True
    maior = max(abs(x), abs(y))
    return maior > 0 and abs(x - y) / maior <= 0.005


def linhas_iguais(a, b):
    """Compara duas linhas normalizadas, com tolerância em floats."""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if isinstance(x, float) and isinstance(y, float):
            if not floats_proximos(x, y):
                return False
        elif x != y:
            return False
    return True


def comparar_linha_a_linha(sql_rows, cypher_rows):
    """
    Compara os conjuntos de linhas de SQL e Cypher como multiconjuntos de valores.

    Cada linha é normalizada e comparada por presença nos dois lados, e não por posição 
    — assim uma diferença de poucas linhas não desalinha o resto. A comparação de floats
    usa tolerância, então as linhas são chaveadas por uma versão "quantizada" que 
    preserva a tolerância.
    Retorna (num_em_comum, num_divergentes, exemplo_divergente).
    """
    from collections import defaultdict

    def partes(linha):
        # Separa a linha em (chave não-float, lista de floats). Os campos não-float
        # identificam a linha; os floats são comparados por tolerância à parte.
        chave, floats = [], []
        for v in linha:
            if isinstance(v, float):
                floats.append(v)
            else:
                chave.append(v)
        return tuple(chave), floats

    # Indexa as linhas do SQL por chave não-float (lista de vetores de floats).
    sql_idx = defaultdict(list)
    for r in sql_rows:
        ch, fl = partes(normalizar_linha(r))
        sql_idx[ch].append(fl)

    em_comum = 0
    exemplo = None
    cy_sobra = 0
    for r in cypher_rows:
        ch, fl = partes(normalizar_linha(r))
        candidatos = sql_idx.get(ch)
        achou = None
        if candidatos:
            for i, fl_sql in enumerate(candidatos):
                if len(fl_sql) == len(fl) and all(floats_proximos(a, b) for a, b in zip(fl_sql, fl)):
                    achou = i
                    break
        if achou is not None:
            em_comum += 1
            candidatos.pop(achou)  # consome o match (multiconjunto)
        else:
            cy_sobra += 1
            if exemplo is None:
                exemplo = ("só no Cypher", ch + tuple(fl))

    # O que sobrou no índice SQL é "só no SQL"
    sql_sobra = sum(len(v) for v in sql_idx.values())
    if exemplo is None and sql_sobra:
        for ch, listas in sql_idx.items():
            if listas:
                exemplo = ("só no SQL", ch + tuple(listas[0]))
                break

    divergentes = cy_sobra + sql_sobra
    return em_comum, divergentes, exemplo


def compare_results(sql_cols, sql_rows, cypher_cols, cypher_rows):
    """
    Compara resultados de SQL e Cypher — contagem de linhas e valores linha a linha.
    Retorna (status, detalhes).
    """
    row_match = len(sql_rows) == len(cypher_rows)
    em_comum, divergentes, exemplo = comparar_linha_a_linha(sql_rows, cypher_rows)

    if divergentes == 0:
        status = "OK"
    elif row_match:
        # mesmo nº de linhas, mas há valores que divergem
        status = "DIVERGENTE_VALORES"
    else:
        status = "DIVERGENTE_LINHAS"

    detalhes = f"SQL={len(sql_rows)} | Cypher={len(cypher_rows)} | em comum={em_comum}, divergentes={divergentes}"
    if exemplo is not None and status != "OK":
        lado, valores = exemplo
        detalhes += f"\n      ex. divergente ({lado}): {valores}"

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
