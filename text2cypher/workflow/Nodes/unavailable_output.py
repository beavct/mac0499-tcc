# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado; única alteração: database_records passa de [''] a None (não houve execução).
from Nodes.States.states import  OverallState, OutputState

def unavailable_output(state: OverallState) -> OutputState:
    """
    Returns the unvailable answer.
    """
    print('Unvailable Output: START')
    return {
        "path": ["unavailable_output"],
        "cypher_statement": state.get("cypher_statement"),
        "database_records": None,  # no original: ['']
        'is_KG_Valid_correct': False,
        'answer': "I couldn't find any relevant information in the database",
        'cypher_errors_history': state.get("internal_cypher_errors_history")   ,
        'cypher_errors': state.get("cypher_errors"),
        "total_tokens": [-1],
        "prompt_tokens": [-1],
        "completion_tokens": [-1]
    }
