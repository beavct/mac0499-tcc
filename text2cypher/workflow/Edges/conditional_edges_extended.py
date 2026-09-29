# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado sem alterações de lógica.
from Nodes.States.states import  OverallState
from typing import Literal


def select_next_action(state: OverallState,) -> Literal[ "cypher_corrector", "cypher_executor",
                                                               'schema_retriever','unavailable_output']:
    if state.get("next_action") == "cypher_executor":
        return "cypher_executor"
    elif state.get("next_action") == "cypher_corrector":
        return "cypher_corrector"
    elif state.get("next_action") == 'unavailable_output':
        return 'unavailable_output'
    elif state.get("next_action") == 'schema_retriever':
        return 'schema_retriever'
