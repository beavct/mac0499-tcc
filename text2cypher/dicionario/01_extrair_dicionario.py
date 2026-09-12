"""
Etapa 1 (Camada A / schema-linking): extrai o dicionário das variáveis v* do
PostgreSQL e monta o corpus do RAG.

As descrições de cada variável estão em COMMENT ON COLUMN nas tabelas de
agregados do Censo (datasets.agregado_setores_censitarios_2022_*) e na tabela
de setores (datasets.dtb_setores_censitarios_2022). Este script lê esses
comentários via col_description() e gera dicionario/corpus/variaveis.json.

Cada documento junta TEMA (derivado do rótulo do nó no grafo) + DESCRIÇÃO
crua do IBGE. É o campo `texto` que será embeddado no Chroma (etapa 02).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from config import (
    PG_CONFIG, PG_SCHEMA, CORPUS_DIR, CORPUS_JSON,
    GEOGRAFIA, COLUNAS_IGNORAR, TEMA_POR_LABEL, load_perfis_config,
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


def docs_de_uma_fonte(cur, no_label, tabela):
    """Monta os documentos de uma fonte (tabela do PG -> nó do grafo)."""
    tema = TEMA_POR_LABEL.get(no_label, no_label)
    docs, sem_comentario = [], []
    for coluna, comentario in comentarios_da_tabela(cur, tabela):
        if coluna in COLUNAS_IGNORAR or not RE_VARIAVEL.match(coluna):
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


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("ETAPA 1: CAMADA A — Extração do dicionário de variáveis v*")
    print("=" * 60)

    fontes = [{"no_label": GEOGRAFIA["no_label"], "tabela": GEOGRAFIA["tabela"]}]
    fontes += load_perfis_config()

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    todos, faltando = [], {}
    for fonte in fontes:
        docs, sem = docs_de_uma_fonte(cur, fonte["no_label"], fonte["tabela"])
        todos.extend(docs)
        if sem:
            faltando[fonte["no_label"]] = sem
        print(f"  {fonte['no_label']:26} ({fonte['tabela']}): {len(docs)} variáveis")
    conn.close()

    os.makedirs(CORPUS_DIR, exist_ok=True)
    with open(CORPUS_JSON, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {len(todos)} variáveis salvas em {CORPUS_JSON}")
    if faltando:
        total = sum(len(v) for v in faltando.values())
        print(f"[aviso] {total} variáveis v* sem comentário no PG (ignoradas):")
        for label, cols in faltando.items():
            print(f"        {label}: {', '.join(cols)}")


if __name__ == "__main__":
    main()
