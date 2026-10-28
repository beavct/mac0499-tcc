"""
Etapa 3: Embeda as perguntas dos exemplos resolvidos do gerador (workflow/exemplos/) e indexa
no Chroma, numa coleção à parte da das propriedades, com similaridade de cosseno.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from sentence_transformers import SentenceTransformer
from config import (EXEMPLOS_JSON, VECTORSTORE_DIR, CHROMA_COLECAO_EXEMPLOS, EMBEDDING_MODEL,
                    PREFIXO_TEXTO)

# ---------------------------------------------------------------------------
# CARGA
# ---------------------------------------------------------------------------


def carregar_exemplos():
    with open(EXEMPLOS_JSON, encoding="utf-8") as f:
        return json.load(f)["exemplos"]


def indexar(exemplos):
    """Embeda as perguntas e (re)cria a coleção no Chroma."""
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    # apaga a coleção antiga, para rodar de novo sem duplicar os itens
    if CHROMA_COLECAO_EXEMPLOS in [c.name for c in client.list_collections()]:
        client.delete_collection(CHROMA_COLECAO_EXEMPLOS)
    col = client.create_collection(CHROMA_COLECAO_EXEMPLOS, metadata={"hnsw:space": "cosine"})

    perguntas = [ex["pergunta"] for ex in exemplos]
    embeddings = model.encode([PREFIXO_TEXTO + p for p in perguntas],
                              normalize_embeddings=True).tolist()
    # só a pergunta é embeddada; o Cypher vai junto, nos metadados
    col.add(
        ids=[ex["id"] for ex in exemplos],
        embeddings=embeddings,
        documents=perguntas,
        metadatas=[{"id": ex["id"], "cypher": ex["cypher"]} for ex in exemplos],
    )
    return col


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("ETAPA 3: Indexação dos exemplos resolvidos no Chroma")
    print("=" * 60)

    exemplos = carregar_exemplos()
    print(f"[exemplos] {len(exemplos)} | modelo: {EMBEDDING_MODEL}")

    col = indexar(exemplos)
    print(f"\n[OK] coleção '{CHROMA_COLECAO_EXEMPLOS}' com {col.count()} itens em "
          f"{VECTORSTORE_DIR}")


if __name__ == "__main__":
    main()
