# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# No original a execução estava desativada; aqui ela roda, com timeout, registro do erro e só em
# modo de leitura (a consulta vem do modelo e não pode alterar o grafo).
from langchain_core.runnables.config import RunnableConfig
from neo4j import Query, RoutingControl

from Nodes.States.states import  OverallState


def cypher_executor(state: OverallState, config: RunnableConfig) -> OverallState:
    """
    Executes the given Cypher statement over the knowledge graph.
    """
    cypher_statement = state.get("cypher_statement")
    database_name = state.get("database_name")
    driver = state.get("neo4j_driver")
    timeout = config['configurable']['timeout_execucao']

    print('Cypher Executor: START')

    database_records = None
    execution_error = None
    try:
        records, _, _ = driver.execute_query(
            Query(cypher_statement, timeout=timeout), database_=database_name,
            routing_=RoutingControl.READ,
        )
        database_records = [record.data() for record in records]
    except Exception as e:
        # pode falhar mesmo aprovada pelo CyVer (ex.: divisão por zero, timeout, escrita)
        execution_error = f"{type(e).__name__}: {e}"

    return {
        "database_records": database_records,
        "execution_error": execution_error,
        "next_action": "output_generator",
        "path": ["cypher_executor"],
        "total_tokens": [-1],
        "prompt_tokens": [-1],
        "completion_tokens": [-1]
    }
