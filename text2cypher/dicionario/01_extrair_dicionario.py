"""
Etapa 1: Extrai do PostgreSQL a descrição, o tipo e os valores das propriedades do grafo
e monta o corpus do RAG em corpus/variaveis.json.

Só entram as propriedades que existem no grafo, então o Neo4j precisa estar carregado.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from neo4j import GraphDatabase
from config import (
    PG_CONFIG, PG_SCHEMA, NEO4J_CONFIG, CORPUS_DIR, CORPUS_JSON, GEOGRAFIA, EQUIPAMENTOS,
    DESCRICOES_INFERIDAS, COMPLEMENTOS_DESCRICAO, COLUNAS_IGNORAR, TEMA_POR_LABEL,
    load_perfis_config, load_colunas,
)

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

# Regex que identifica variáveis do Censo ("v" + dígitos)
RE_VARIAVEL = re.compile(r"^v\d+$")

# Descrições inferidas, para quando o PG não tem nenhuma
INFERIDAS = {(d["no_label"], d["propriedade"]): d["descricao"] for d in DESCRICOES_INFERIDAS}

# Complementos da descrição no texto buscado: "Dependência Administrativa (rede pública...)"
COMPLEMENTOS = {(d["no_label"], d["propriedade"]): d["complemento"]
                for d in COMPLEMENTOS_DESCRICAO}


# ---------------------------------------------------------------------------
# TIPO E VALORES
# ---------------------------------------------------------------------------


def metadados_da_tabela(cur, tabela):
    """{coluna: (descrição, tipo no PG, categorias)} da tabela, lidos de metadata.attribute."""
    cur.execute(
        """
        SELECT a.name, a.description, a.type, a.categories
        FROM metadata.attribute a
        JOIN metadata.section s ON s.id = a.section_id
        WHERE s.table_name = %s OR s.table_name LIKE %s
        """,
        (tabela, f"%.{tabela}"),
    )
    metadados = {}
    for nome, descricao, tipo, categorias in cur.fetchall():
        if isinstance(categorias, str):
            categorias = ast.literal_eval(categorias)
        metadados[nome] = (descricao, tipo, categorias or {})
    return metadados


def texto_valores(tipo, categorias):
    """Valores escritos como o modelo deve usá-los na consulta (ex.: 1 = Federal)."""
    if not categorias:
        return ""
    if tipo == "BOOLEAN":
        return "true = Sim, false = Não"
    formato = "'{}' = {}" if tipo == "STRING" else "{} = {}"
    return ", ".join(formato.format(k, v) for k, v in categorias.items() if str(k).strip())


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


def docs_de_uma_fonte(cur, no_label, tabela, tipos, colunas=None):
    """Monta os documentos de uma tabela do PG, só com as propriedades que estão em `tipos`."""
    tema = TEMA_POR_LABEL.get(no_label, no_label)
    metadados = metadados_da_tabela(cur, tabela)
    docs, sem_comentario, fora_do_grafo = [], [], []
    for coluna, comentario in comentarios_da_tabela(cur, tabela):
        if coluna in COLUNAS_IGNORAR:
            continue
        if colunas is None and not RE_VARIAVEL.match(coluna):
            continue
        if colunas is not None and coluna not in colunas:
            continue
        descricao = (comentario or "").strip() or INFERIDAS.get((no_label, coluna), "")
        if coluna not in tipos:
            fora_do_grafo.append(f"{coluna} ({descricao})")
            continue
        if not descricao:
            sem_comentario.append(coluna)
            continue
        _, _, categorias = metadados.get(coluna, (None, None, {}))
        tipo = tipos[coluna]
        valores = texto_valores(tipo, categorias)
        complemento = COMPLEMENTOS.get((no_label, coluna), "")
        texto = f"{tema}: {descricao}"
        if complemento:
            texto += f" ({complemento})"
        # No texto buscado, os valores só entram nas colunas que não são booleanas
        if valores and tipo != "BOOLEAN":
            texto += f". valores: {valores}"
        docs.append({
            "id": f"{no_label}:{coluna}",
            "variavel": coluna,
            "no_label": no_label,
            "tema": tema,
            "tabela_pg": tabela,
            "descricao": descricao,
            "tipo": tipo,
            "valores": valores,
            "complemento": complemento,
            "texto": texto,
        })
    return docs, sem_comentario, fora_do_grafo


def propriedades_no_grafo(labels):
    """{rótulo: {propriedade: tipo no Neo4j}} das propriedades presentes nos nós do grafo."""
    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
    )
    por_no = {}
    for label in labels:
        reg, _, _ = driver.execute_query(
            f"MATCH (n:`{label}`) UNWIND keys(n) AS k "
            "RETURN k, collect(DISTINCT valueType(n[k])) AS tipos"
        )
        # valueType devolve, por exemplo, "INTEGER NOT NULL"
        por_no[label] = {r["k"]: r["tipos"][0].replace(" NOT NULL", "") for r in reg}
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

    # Primeiro o grafo: quais propriedades existem e com que tipo
    print("[Neo4j] Lendo as propriedades e os tipos do grafo...")
    no_grafo = propriedades_no_grafo({f["no_label"] for f in fontes})

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    todos, faltando, fora_do_grafo = [], {}, []
    for fonte in fontes:
        label = fonte["no_label"]
        docs, sem, fora = docs_de_uma_fonte(
            cur, label, fonte["tabela"], no_grafo[label], fonte.get("colunas")
        )
        todos.extend(docs)
        if sem:
            faltando[label] = sem
        fora_do_grafo += [f"{label}.{x}" for x in fora]
        print(f"  {label:26} ({fonte['tabela']}): {len(docs)} propriedades")
    conn.close()

    if fora_do_grafo:
        print(f"[aviso] {len(fora_do_grafo)} propriedades não existem no grafo (ignoradas):")
        for x in fora_do_grafo:
            print(f"        {x}")

    os.makedirs(CORPUS_DIR, exist_ok=True)
    with open(CORPUS_JSON, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    com_valores = sum(1 for d in todos if d["valores"])
    print(f"\n[OK] {len(todos)} propriedades salvas em {CORPUS_JSON} ({com_valores} com valores)")
    if faltando:
        total = sum(len(v) for v in faltando.values())
        print(f"[aviso] {total} propriedades sem comentário no PG (ignoradas):")
        for label, cols in faltando.items():
            print(f"        {label}: {', '.join(cols)}")


if __name__ == "__main__":
    main()
