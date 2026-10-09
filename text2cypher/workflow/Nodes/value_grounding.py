"""
Nó de value grounding (Camada B): acha na pergunta os nomes de lugares e de equipamentos
e acrescenta ao esquema os valores que existem no grafo, escritos como estão lá, para o
gerador usar nos filtros. Só entra no workflow com USAR_VALUE_GROUNDING ligado.
"""
import os
import sys

from Nodes.States.states import OverallState

TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
from dicionario.valores import montar_bloco_valores


def value_grounding(state: OverallState) -> OverallState:
    """Acrescenta ao esquema os valores do grafo que casam com termos da pergunta."""
    print('Value Grounding: START')
    question = state.get("question")
    database_name = state.get("database_name")
    driver = state.get("neo4j_driver")

    bloco, _ = montar_bloco_valores(question, driver, database_name)
    schema = state.get("schema")
    if bloco:
        schema += "\n\n" + bloco

    return {"schema": schema,
            "grounded_values": bloco,
            "path": ["value_grounding"],
            "total_tokens": [-1],
            "prompt_tokens": [-1],
            "completion_tokens": [-1]}
