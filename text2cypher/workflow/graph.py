"""
Monta o grafo de estados (LangGraph) do workflow.

Adaptado do extended_workflow/graph.py do CyVerACT (CC BY-SA 4.0; ver NOTICE.md):
o schema_filtering foi substituído pelo schema_rag.
"""
import sys

from langgraph.graph import END, START, StateGraph

from Nodes.States.states import OverallState, InputState, OutputState
from Nodes.schema_rag import schema_rag
from Nodes.schema_retriever import schema_retriever
from Nodes.cypher_generator import cypher_generator
from Nodes.cyver_evaluator import cyver_evaluator
from Nodes.cypher_corrector import cypher_corrector
from Nodes.cypher_executor import cypher_executor
from Nodes.output_generator import output_generator
from Nodes.unavailable_output import unavailable_output
from Edges.conditional_edges_extended import select_next_action

sys.path.append('Nodes')

# Define the graph
# parâmetros atualizados para o langgraph 1.x
workflow = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)

# Add nodes
workflow.add_node(schema_rag)
workflow.add_node(schema_retriever)
workflow.add_node(cypher_generator)
workflow.add_node(cyver_evaluator)
workflow.add_node(cypher_corrector)
workflow.add_node(cypher_executor)
workflow.add_node(output_generator)
workflow.add_node(unavailable_output)

# Add edges
workflow.add_edge(START, "schema_rag")
workflow.add_edge("schema_rag", "cypher_generator")
workflow.add_edge("schema_retriever", "cypher_generator")
workflow.add_edge("cypher_generator", "cyver_evaluator")
workflow.add_conditional_edges("cyver_evaluator", select_next_action)
workflow.add_edge("cypher_corrector", "cyver_evaluator")
workflow.add_edge("cypher_executor", "output_generator")
workflow.add_edge("output_generator", END)
workflow.add_edge("unavailable_output", END)

app = workflow.compile()
