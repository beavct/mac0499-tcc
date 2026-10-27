"""
Exemplos resolvidos (pergunta + Cypher) para o prompt do gerador. Para cada pergunta, vão os
exemplos de pergunta mais parecida, escolhidos pelo e5, em pares como em Chang e
Fosler-Lussier (2023).
"""
import json
import os
import sys

from langchain_core.vectorstores import InMemoryVectorStore

TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
# o _get_model devolve o modelo já carregado pela Camada A, para não carregar o e5 duas vezes
from dicionario.retriever import EmbeddingE5, _get_model

EXEMPLOS_JSON = os.path.join(os.path.dirname(__file__), "..", "exemplos", "exemplos.json")

_exemplos = None
_indice = None


def _get_exemplos():
    """{id: exemplo}, lido do exemplos.json na primeira chamada."""
    global _exemplos
    if _exemplos is None:
        with open(EXEMPLOS_JSON, encoding="utf-8") as f:
            _exemplos = {ex["id"]: ex for ex in json.load(f)["exemplos"]}
    return _exemplos


def _get_indice():
    """Índice em memória com as perguntas dos exemplos."""
    global _indice
    if _indice is None:
        exemplos = _get_exemplos()
        _indice = InMemoryVectorStore(EmbeddingE5(_get_model()))
        _indice.add_texts([ex["pergunta"] for ex in exemplos.values()], ids=list(exemplos))
    return _indice


# ---------------------------------------------------------------------------
# BLOCO DO PROMPT
# ---------------------------------------------------------------------------


def montar_bloco_exemplos(pergunta, n):
    """Os n exemplos mais parecidos, do menos para o mais parecido, que fica junto da pergunta."""
    docs = _get_indice().similarity_search(pergunta, k=n)
    pares = []
    for doc in reversed(docs):
        ex = _get_exemplos()[doc.id]
        pares.append(f"Question: {ex['pergunta']}\nCypher statement:\n{ex['cypher']}")
    return "\n\n".join(pares)
