# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado; alterações: contagem de tokens, cypher_history, memória das tentativas e limpeza da
# resposta (NOTICE.md).
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import get_usage_metadata_callback


from Nodes.States.states import OverallState
from Nodes.tentativas import montar_bloco_tentativas
from Nodes.resposta import limpar_resposta

system_prompt = '''
                You are a Cypher expert reviewing a statement.
                Given an input Cypher statement and the errors it has, correct the Cypher statement.  No pre-amble.
                Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
            '''
human_prompt = '''
                Fix the Cypher statememnt based on the given errors.
                The Cypher statement should valid for the given knowledge graph schema.
                Use only the provided labels and relationship types and properties in the schema.
                Do not use any other node labels, relationship types or properties that are not provided in the schema.

                Schema:
                {schema}

                Note: Do not include any explanations or apologies in your responses.
                Do not wrap the response in any backticks or anything else.
                Respond with a Cypher statement only!

                The question is:
                {question}

                The Cypher statement is:
                {cypher}

                The errors for the Cypher statement are:
                {errors}
'''
# bloco das tentativas anteriores (memória), inserido antes do pedido final
memory_prompt = '''
                Previous Cypher statements that also failed, with their errors.
                Do not return any of them again, nor the Cypher statement above:
                {previous_attempts}
'''
request_prompt = '''
                Corrected Cypher statement:

                '''

fix_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (system_prompt
            ),
        ),
        (
            "human",
            (
                human_prompt + request_prompt
            ),
        ),
    ]
)

fix_cypher_prompt_flattened = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            (
                system_prompt + human_prompt + request_prompt
            ),
        ),
    ]
)

fix_cypher_memory_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", human_prompt + memory_prompt + request_prompt),
    ]
)

fix_cypher_memory_prompt_flattened = ChatPromptTemplate.from_messages(
    [
        ("human", system_prompt + human_prompt + memory_prompt + request_prompt),
    ]
)

def cypher_corrector(state: OverallState, config:RunnableConfig) -> OverallState:
    """
    Correct the Cypher statement based on the provided errors.
    """
    model_name = config['configurable']['model_name']
    question = state.get("question")
    cypher = state.get("cypher_statement")
    schema = state.get("schema")
    cypher_errors_list = state.get("cypher_errors")
    cypher_errors = "\n".join(
        f"{i + 1}. {error}" for i, error in enumerate(cypher_errors_list)
    )
    chat_model = config['configurable']['model']

    if model_name == 'gemma2_9b' or model_name == 'finetuned_gemma2_9b' or model_name == 'finetuned_gemma2_9b_local':
        prompt = fix_cypher_prompt_flattened
        prompt_with_memory = fix_cypher_memory_prompt_flattened
    else:
        prompt = fix_cypher_prompt
        prompt_with_memory = fix_cypher_memory_prompt

    inputs = {
        "question": question,
        "schema": schema,
        "cypher": cypher,
        "errors": cypher_errors
    }
    previous_attempts = ""
    if config['configurable']['bloquear_repeticao']:
        previous_attempts = montar_bloco_tentativas(
            cypher,
            state.get("cypher_history", []),
            state.get("internal_cypher_errors_history", []),
            config['configurable']['max_tentativas_memoria'],
        )
    if previous_attempts:
        prompt = prompt_with_memory
        inputs["previous_attempts"] = previous_attempts
    fix_cypher_chain = prompt | chat_model | StrOutputParser()

    print('Cypher Corrector: START')
    with get_usage_metadata_callback() as cb:
        corrected_cypher = fix_cypher_chain.invoke(inputs)

    # usage_metadata = {nome_do_modelo: {input_tokens, output_tokens, total_tokens}}
    uso = cb.usage_metadata.values()
    total_tokens = sum(u.get("total_tokens", 0) for u in uso)
    prompt_tokens = sum(u.get("input_tokens", 0) for u in uso)
    completion_tokens = sum(u.get("output_tokens", 0) for u in uso)

    if model_name == 'llama3_2_3b_local':
        corrected_cypher = corrected_cypher.split('assistant<|end_header_id|>')[1].strip()
    elif model_name == 'finetuned_gemma2_9b_local':
        corrected_cypher = corrected_cypher.split('<start_of_turn>model\n')[1].strip()
    corrected_cypher, limpou = limpar_resposta(corrected_cypher)

    return {
        'next_action': 'cypher_evaluator',
        'cypher_statement': corrected_cypher,
        'cypher_history': [corrected_cypher],
        'cleaned_responses': [limpou],
        'path': ['cypher_corrector'],
        "total_tokens": [total_tokens],
        "prompt_tokens": [prompt_tokens],
        "completion_tokens": [completion_tokens]
    }
