"""
Etapa 2: Embeda o corpus da etapa 1 e indexa no Chroma (vectorstore/), com
similaridade de cosseno.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from sentence_transformers import SentenceTransformer
from config import (CORPUS_JSON, VECTORSTORE_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL,
                    PREFIXO_TEXTO)

# ---------------------------------------------------------------------------
# CARGA
# ---------------------------------------------------------------------------


def carregar_corpus():
    with open(CORPUS_JSON, encoding="utf-8") as f:
        return json.load(f)


def indexar(docs, batch_size=256):
    """Embeda os textos e (re)cria a coleção no Chroma."""
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    # recria do zero para a indexação ser idempotente
    if CHROMA_COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(CHROMA_COLLECTION)
    col = client.create_collection(CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})

    # guardados junto, mas fora da busca (só o "texto" é embeddado)
    metadados = ["variavel", "no_label", "tema", "tabela_pg", "descricao", "tipo", "valores"]
    for i in range(0, len(docs), batch_size):
        lote = docs[i : i + batch_size]
        textos = [d["texto"] for d in lote]
        embeddings = model.encode([PREFIXO_TEXTO + t for t in textos],
                                  normalize_embeddings=True).tolist()
        col.add(
            ids=[d["id"] for d in lote],
            embeddings=embeddings,
            documents=textos,
            metadatas=[{k: d[k] for k in metadados} for d in lote],
        )
        print(f"  indexadas {min(i + batch_size, len(docs))}/{len(docs)}")

    return model, col


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("ETAPA 2: Indexação no Chroma")
    print("=" * 60)

    docs = carregar_corpus()
    print(f"[corpus] {len(docs)} propriedades | modelo: {EMBEDDING_MODEL}")

    model, col = indexar(docs)
    print(f"\n[OK] coleção '{CHROMA_COLLECTION}' com {col.count()} itens em {VECTORSTORE_DIR}")
    

if __name__ == "__main__":
    main()
