# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado sem alterações de lógica; corrigidos comentários que trocavam k e n.
from langchain_core.runnables.config import RunnableConfig
from collections import Counter
from Nodes.States.states import OverallState

from CyVer import SyntaxValidator, PropertiesValidator, SchemaValidator

#Create cypher evaluator node
def cyver_evaluator(state: OverallState, config:RunnableConfig) -> OverallState:

    cypher_statement = state.get("cypher_statement")
    database_name = state.get("database_name")
    total_attempts = config['configurable']['total_attempts']
    attempts_w_filtered = config['configurable']['attempts_w_filtered']

    # Connect to the database
    driver = state.get("neo4j_driver")

    #---------------CyVer evaluation------------------
    print('CyVer Evaluator: START')
    print('CyVer Evaluation of {}:'.format(cypher_statement))

    cypher_errors = []

    #SyntaxValidator
    syntax_validator =  SyntaxValidator(driver)
    _, syntax_validation_metadata = syntax_validator.validate(cypher_statement, database_name=database_name)

    #SchemaValidator
    schema_validator = SchemaValidator(driver)
    _, schema_validation_metadata = schema_validator.validate(cypher_statement, database_name=database_name)

    #PropertiesValidator
    properties_validator = PropertiesValidator(driver)
    _, properties_validation_metadata = properties_validator.validate(cypher_statement, database_name=database_name)


    if syntax_validation_metadata:
        for error in syntax_validation_metadata:
            cypher_errors.append(error['code']+': '+ error['description'])

    if schema_validation_metadata:
        for error in schema_validation_metadata:
            cypher_errors.append(error['code'] +': '+ error['description'])

    if properties_validation_metadata:
        for error in properties_validation_metadata:
            cypher_errors.append(error['code']+': '+  error['description'])

    current_path = state.get("path", [])
    frequency = Counter(current_path)

    if cypher_errors:
        print('CyVer Errors from generated query:')
        for error in cypher_errors:
            print('-', error)
            print()
        # If Cypher Corrector exists in the path exactly k times (attempts_w_filtered) then:
        if frequency['cypher_corrector'] == attempts_w_filtered:
            # If the second to last elemet is schema retriever (it means that the schema filtering has failed and
            # also exists errors, so we need to go to the cypher_corrector to increase the frequency)
            if current_path[-2]=='schema_retriever':
                next_action = "cypher_corrector"
            # Else, meaning that the second to last element is cypher corrector, then we need to go to the schema retriever
            # to access the full schema
            else:
                next_action = "schema_retriever"
        # If Cypher Corrector exists in the path exactly n times (total_attempts) then we need to end the workflow and give unavailable output.
        elif frequency['cypher_corrector'] == total_attempts:
            next_action = "unavailable_output"
        # Else if frequency<k or k<frequency<n then we need to go to the cypher corrector
        else:
            next_action = "cypher_corrector"
    # Else, if there are no errors, we need to go to the cypher executor
    else:
        next_action = "cypher_executor"

    return{
        'next_action': next_action,
        'cypher_errors': cypher_errors,
        'path':['cyver_evaluator'],
        'internal_cypher_errors_history':[cypher_errors],
        "total_tokens": [-1],
        "prompt_tokens": [-1],
        "completion_tokens": [-1]
        }
