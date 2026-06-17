import csv
import os

import psycopg2
from neo4j import GraphDatabase
from config import PG_CONFIG, NEO4J_CONFIG, SALVAR_CSV

CSV_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)


def get_neo4j_driver():
    return GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]),
    )


def pg_fetch_all(query, params=None):
    """Executa query no PG e retorna lista de dicts."""
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def neo4j_write(driver, cypher, batch, batch_size=5000):
    """Envia dados para o Neo4j em batches via UNWIND."""
    with driver.session() as session:
        for i in range(0, len(batch), batch_size):
            chunk = batch[i : i + batch_size]
            session.run(cypher, batch=chunk)
    print(f"  -> {len(batch)} registros carregados no Neo4j")


def save_csv(data, filename):
    """Salva lista de dicts como CSV para conferência manual (se SALVAR_CSV=true)."""
    if not SALVAR_CSV:
        return

    if not data:
        print(f"  [CSV] Nenhum dado para salvar em {filename}")
        return

    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(CSV_OUTPUT_DIR, filename)

    keys = data[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"  [CSV] Salvo: {filepath} ({len(data)} linhas)")
