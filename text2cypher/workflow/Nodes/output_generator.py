# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado; único acréscimo: repassa o campo execution_error para a saída.
''' Return the generated query'''
from Nodes.States.states import  OverallState, OutputState

def output_generator(state: OverallState) -> OutputState:
    """
    Returns the final query based on the user question and the retieved results.
    """
    print('Output Generator: START')

    return {
        "path": ["output_generator"],
        "cypher_statement": state.get("cypher_statement"),
        "database_records": state.get("database_records"),
        "execution_error": state.get("execution_error"),
        'answer': "I found relevant information in the database",
        'is_KG_Valid_correct':True,
        'cypher_errors_history': state.get("internal_cypher_errors_history"),
        'cypher_errors': [],
        "total_tokens": [-1],
        "prompt_tokens": [-1],
        "completion_tokens": [-1]
    }
