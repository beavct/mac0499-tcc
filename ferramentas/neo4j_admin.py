"""
Ferramentas de administração do banco Neo4j.

Comandos úteis para inspecionar e limpar o grafo durante o desenvolvimento do ETL.

Uso:
  python neo4j_admin.py contar                    # conta todos os nós
  python neo4j_admin.py contar SetorCensitario    # conta nós de uma label
  python neo4j_admin.py labels                     # lista todas as labels e contagens
  python neo4j_admin.py isolados                   # lista nós sem nenhuma aresta
  python neo4j_admin.py isolados Escola            # nós isolados de uma label
  python neo4j_admin.py constraints                # lista as constraints existentes
  python neo4j_admin.py limpar-constraints         # remove todas as constraints
  python neo4j_admin.py limpar                     # apaga TODOS os nós e arestas (em batches)
  python neo4j_admin.py reset                      # limpar + limpar-constraints (banco do zero)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))
from db import get_neo4j_driver

BATCH_SIZE = 5000


# ---------------------------------------------------------------------------
# CONTAGEM
# ---------------------------------------------------------------------------

def contar(driver, label=None):
    """Conta nós — todos ou de uma label específica."""
    with driver.session() as session:
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) AS total"
            total = session.run(query).single()["total"]
            print(f"{label}: {total} nós")
        else:
            total = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
            print(f"Total de nós no banco: {total}")


def labels(driver):
    """Lista todas as labels e a contagem de nós de cada uma."""
    with driver.session() as session:
        labels_list = [r["label"] for r in session.run("CALL db.labels()")]
        if not labels_list:
            print("Nenhuma label no banco.")
            return
        print(f"{'Label':<30} | Nós")
        print("-" * 45)
        for lbl in sorted(labels_list):
            total = session.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS total").single()["total"]
            print(f"{lbl:<30} | {total}")


# ---------------------------------------------------------------------------
# NÓS ISOLADOS
# ---------------------------------------------------------------------------

def isolados(driver, label=None):
    """Lista nós sem nenhuma aresta (isolados)."""
    with driver.session() as session:
        if label:
            query = f"MATCH (n:{label}) WHERE NOT (n)--() RETURN count(n) AS total"
        else:
            query = "MATCH (n) WHERE NOT (n)--() RETURN count(n) AS total"
        total = session.run(query).single()["total"]

        alvo = f"da label {label}" if label else "no banco"
        if total == 0:
            print(f"Nenhum nó isolado {alvo}.")
        else:
            print(f"{total} nós isolados {alvo}.")


# ---------------------------------------------------------------------------
# CONSTRAINTS
# ---------------------------------------------------------------------------

def listar_constraints(driver):
    """Lista as constraints existentes. Retorna os nomes."""
    with driver.session() as session:
        result = list(session.run("SHOW CONSTRAINTS"))
        if not result:
            print("Nenhuma constraint no banco.")
            return []
        nomes = []
        for r in result:
            nome = r.get("name")
            nomes.append(nome)
            tipo = r.get("type", "")
            labels_c = r.get("labelsOrTypes", "")
            props = r.get("properties", "")
            print(f"  {nome} | {tipo} | {labels_c} {props}")
        return nomes


def limpar_constraints(driver):
    """Remove todas as constraints do banco."""
    nomes = listar_constraints(driver)
    if not nomes:
        return
    with driver.session() as session:
        for nome in nomes:
            session.run(f"DROP CONSTRAINT {nome}")
            print(f"  [removida] {nome}")
    print(f"{len(nomes)} constraints removidas.")


# ---------------------------------------------------------------------------
# LIMPEZA
# ---------------------------------------------------------------------------

def limpar(driver):
    """Apaga todos os nós e arestas em batches (evita estourar a memória)."""
    with driver.session() as session:
        total = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
        if total == 0:
            print("Banco já está vazio.")
            return

        print(f"Apagando {total} nós em batches de {BATCH_SIZE}...")
        while True:
            # Apaga um batch e retorna quantos foram apagados
            deleted = session.run(
                """
                MATCH (n)
                WITH n LIMIT $batch_size
                DETACH DELETE n
                RETURN count(n) AS deleted
                """,
                batch_size=BATCH_SIZE,
            ).single()["deleted"]

            restantes = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
            print(f"  apagados {deleted} | restam {restantes}")

            if deleted == 0 or restantes == 0:
                break

    print("Todos os nós e arestas foram apagados.")


def reset(driver):
    """Limpa tudo: nós, arestas e constraints (banco do zero)."""
    print("=== RESET COMPLETO DO BANCO ===\n")
    print("1. Apagando nós e arestas...")
    limpar(driver)
    print("\n2. Removendo constraints...")
    limpar_constraints(driver)
    print("\n[OK] Banco resetado.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMANDOS = {
    "contar": contar,
    "labels": labels,
    "isolados": isolados,
    "constraints": listar_constraints,
    "limpar-constraints": limpar_constraints,
    "limpar": limpar,
    "reset": reset,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        # Uso:
        print(__doc__)
        sys.exit(1)

    comando = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None

    driver = get_neo4j_driver()
    try:
        # Comandos que aceitam label opcional
        if comando in ("contar", "isolados"):
            COMANDOS[comando](driver, arg)
        else:
            COMANDOS[comando](driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
