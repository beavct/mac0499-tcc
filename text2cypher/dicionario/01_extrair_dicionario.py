"""
Etapa 1: Extrai do PostgreSQL a descrição das propriedades do grafo (COMMENT ON COLUMN)
e monta o corpus do RAG em corpus/variaveis.json.

Só entram as propriedades que existem no grafo, então o Neo4j precisa estar carregado.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from neo4j import GraphDatabase
from config import (
    PG_CONFIG, PG_SCHEMA, NEO4J_CONFIG, CORPUS_DIR, CORPUS_JSON, GEOGRAFIA, EQUIPAMENTOS,
    COLUNAS_IGNORAR, TEMA_POR_LABEL, load_perfis_config, load_colunas,
)

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

# Regex que identifica variáveis do Censo ("v" + dígitos)
RE_VARIAVEL = re.compile(r"^v\d+$")


# ---------------------------------------------------------------------------
# EXTRAÇÃO
# ---------------------------------------------------------------------------


def comentarios_da_tabela(cur, tabela):
    """Retorna [(coluna, comentario)] das colunas da tabela, na ordem física."""
    cur.execute(
        """
        SELECT a.attname, col_description(a.attrelid, a.attnum)
        FROM pg_attribute a
        JOIN pg_class c     ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum;
        """,
        (PG_SCHEMA, tabela),
    )
    return cur.fetchall()


def docs_de_uma_fonte(cur, no_label, tabela, colunas=None):
    """Monta os documentos de uma tabela do PG (só v*, ou só as `colunas` informadas)."""
    tema = TEMA_POR_LABEL.get(no_label, no_label)
    docs, sem_comentario = [], []
    for coluna, comentario in comentarios_da_tabela(cur, tabela):
        if coluna in COLUNAS_IGNORAR:
            continue
        if colunas is None and not RE_VARIAVEL.match(coluna):
            continue
        if colunas is not None and coluna not in colunas:
            continue
        descricao = (comentario or "").strip()
        if not descricao:
            sem_comentario.append(coluna)
            continue
        docs.append({
            "id": f"{no_label}:{coluna}",
            "variavel": coluna,
            "no_label": no_label,
            "tema": tema,
            "tabela_pg": tabela,
            "descricao": descricao,
            "texto": f"{tema}: {descricao}",
        })
    return docs, sem_comentario


def propriedades_no_grafo(labels):
    """{rótulo: set(propriedades)} realmente presentes nos nós do grafo."""
    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
    )
    por_no = {}
    for label in labels:
        reg, _, _ = driver.execute_query(
            f"MATCH (n:`{label}`) UNWIND keys(n) AS k RETURN DISTINCT k"
        )
        por_no[label] = {r["k"] for r in reg}
    driver.close()
    return por_no


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("ETAPA 1: Extração do dicionário de propriedades")
    print("=" * 60)

    fontes = [{"no_label": GEOGRAFIA["no_label"], "tabela": GEOGRAFIA["tabela"]}]
    fontes += load_perfis_config()
    fontes += [{**eq, "colunas": load_colunas(eq["colunas"])} for eq in EQUIPAMENTOS]

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    todos, faltando = [], {}
    for fonte in fontes:
        docs, sem = docs_de_uma_fonte(cur, fonte["no_label"], fonte["tabela"], fonte.get("colunas"))
        todos.extend(docs)
        if sem:
            faltando[fonte["no_label"]] = sem
        print(f"  {fonte['no_label']:26} ({fonte['tabela']}): {len(docs)} propriedades")
    conn.close()

    # Mantém só o que existe no grafo
    print("\n[Neo4j] Conferindo quais propriedades existem no grafo...")
    no_grafo = propriedades_no_grafo({f["no_label"] for f in fontes})
    fora_do_grafo = [d for d in todos if d["variavel"] not in no_grafo[d["no_label"]]]
    todos = [d for d in todos if d["variavel"] in no_grafo[d["no_label"]]]
    if fora_do_grafo:
        print(f"[aviso] {len(fora_do_grafo)} propriedades não existem no grafo (ignoradas):")
        for d in fora_do_grafo:
            print(f"        {d['no_label']}.{d['variavel']}  ({d['descricao']})")

    os.makedirs(CORPUS_DIR, exist_ok=True)
    with open(CORPUS_JSON, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {len(todos)} propriedades salvas em {CORPUS_JSON}")
    if faltando:
        total = sum(len(v) for v in faltando.values())
        print(f"[aviso] {total} propriedades sem comentário no PG (ignoradas):")
        for label, cols in faltando.items():
            print(f"        {label}: {', '.join(cols)}")


if __name__ == "__main__":
    main()
