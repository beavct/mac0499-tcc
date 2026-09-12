"""
Inspeciona a coleção do Chroma pelo terminal, sem servidor nem UI.

Uso:
    python inspecionar.py                 # resumo + primeiros registros
    python inspecionar.py 20              # primeiros 20 registros
    python inspecionar.py 20 PerfilRacaCor  # filtra por nó do grafo
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from config import VECTORSTORE_DIR, CHROMA_COLLECTION


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    no_label = sys.argv[2] if len(sys.argv) > 2 else None

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    col = client.get_collection(CHROMA_COLLECTION)

    print(f"coleção: {CHROMA_COLLECTION} | total: {col.count()} registros")

    where = {"no_label": no_label} if no_label else None
    res = col.get(where=where, limit=n, include=["documents", "metadatas"])

    filtro = f" (nó={no_label})" if no_label else ""
    print(f"mostrando {len(res['ids'])}{filtro}:\n")
    for id_, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
        print(f"  {id_}")
        print(f"    texto: {doc}")
        print(f"    meta : {meta}\n")


if __name__ == "__main__":
    main()
