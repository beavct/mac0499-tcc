"""
Exemplos resolvidos (pergunta + Cypher) para o prompt do gerador. Para cada pergunta, vão os
exemplos de pergunta mais parecida, buscados no Chroma (coleção indexada pela etapa 03 do
dicionário), em pares como em Chang e Fosler-Lussier (2023).
"""
import os
import sys

from langchain_chroma import Chroma

TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
from config import VECTORSTORE_DIR, CHROMA_COLECAO_EXEMPLOS
# o _get_model devolve o modelo já carregado pela Camada A, para não carregar o e5 duas vezes
from dicionario.retriever import EmbeddingE5, _get_model

_indice = None


def _get_indice():
    """Coleção dos exemplos no Chroma."""
    global _indice
    if _indice is None:
        _indice = Chroma(collection_name=CHROMA_COLECAO_EXEMPLOS,
                         persist_directory=VECTORSTORE_DIR,
                         embedding_function=EmbeddingE5(_get_model()))
    return _indice


# ---------------------------------------------------------------------------
# BLOCO DO PROMPT
# ---------------------------------------------------------------------------


def exemplos_similares(pergunta, n):
    """Os n exemplos mais parecidos, do menos para o mais parecido."""
    docs = _get_indice().similarity_search(pergunta, k=n)
    exemplos = []
    for doc in reversed(docs):
        exemplos.append({"id": doc.metadata["id"], "pergunta": doc.page_content,
                         "cypher": doc.metadata["cypher"]})
    return exemplos


def montar_bloco_exemplos(pergunta, n):
    """Pares pergunta/Cypher; o mais parecido fica por último, junto da pergunta."""
    pares = []
    for ex in exemplos_similares(pergunta, n):
        pares.append(f"Question: {ex['pergunta']}\nCypher statement:\n{ex['cypher']}")
    return "\n\n".join(pares)
