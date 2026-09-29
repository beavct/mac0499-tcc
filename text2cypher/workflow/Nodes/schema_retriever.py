"""
Nó de fallback do esquema, acionado quando as correções com o esquema filtrado se
esgotam. Adaptado do schema_retriever.py do CyVerACT (CC BY-SA 4.0; ver NOTICE.md):
em vez do esquema completo, refaz a busca com um k maior (TOP_K_FALLBACK).
"""
import os
import sys

from Nodes.States.states import OverallState
from Nodes.schema_rag import construir_schema

TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
from config import TOP_K

# k do fallback (padrão: 3x o TOP_K)
TOP_K_FALLBACK = int(os.getenv("TOP_K_FALLBACK", str(TOP_K * 3)))


def schema_retriever(state: OverallState) -> OverallState:
    """Reexecuta o RAG com um k maior para ampliar o esquema recuperado."""
    print('Schema retriever Agent: START')
    question = state.get("question")
    database_name = state.get("database_name")
    driver = state.get("neo4j_driver")

    schema = construir_schema(driver, database_name, question, k=TOP_K_FALLBACK)

    return {"schema": schema,
            "path": ["schema_retriever"],
            "total_tokens": [-1],
            "prompt_tokens": [-1],
            "completion_tokens": [-1]}
