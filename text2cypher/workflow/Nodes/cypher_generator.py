# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Reusado; alterações: contagem de tokens, print de início, cypher_history, limpeza da resposta e
# bloco opcional de exemplos resolvidos (NOTICE.md).
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.config import RunnableConfig
from langchain_core.callbacks import get_usage_metadata_callback


from Nodes.States.states import  OverallState
from Nodes.resposta import limpar_resposta
from Nodes.exemplos import montar_bloco_exemplos

system_prompt = """
                Task: Generate Cypher statement to query a graph database.
                Instructions: Use only the provided relationship types and properties in the schema.
                Do not use any other relationship types or properties that are not provided in the schema.
                Do not include any explanations or apologies in your responses.
                Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
                Do not include any text except the generated Cypher statement.
                """
# dividido em duas partes para os exemplos entrarem entre o esquema e a pergunta
human_schema_prompt =  """
                Generate Cypher statement to query a graph database,as plain text without any code block formatting or backticks.
                Use only the provided relationship types and properties in the schema.
                \nSchema: {schema}
"""
human_question_prompt = """                \nQuestion: {question}
                \nCypher statement:

                """
human_prompt = human_schema_prompt + human_question_prompt
# exemplos resolvidos (USAR_EXEMPLOS), em pares pergunta/consulta
examples_prompt = """                \nExamples of questions and their Cypher statements:
{examples}
"""
human_prompt_with_examples = human_schema_prompt + examples_prompt + human_question_prompt
text2cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                system_prompt
            ),
        ),
        (   #as plain text without any code block formatting or backticks : ADDED
            "human",
            (
              human_prompt
            ),
        ),
    ]
)

text2cypher_prompt_flattened = ChatPromptTemplate.from_messages(
    [
        (   #as plain text without any code block formatting or backticks : ADDED
            "human",
            (
              system_prompt + human_prompt
            ),
        ),
    ]
)

text2cypher_examples_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", human_prompt_with_examples),
    ]
)

text2cypher_examples_prompt_flattened = ChatPromptTemplate.from_messages(
    [
        ("human", system_prompt + human_prompt_with_examples),
    ]
)

## Create the node for the Cypher generator
def cypher_generator(state: OverallState, config:RunnableConfig) -> OverallState:
    """
    Generates a cypher statement based on the provided schema and user input
    """
    model_name = config['configurable']['model_name']
    schema = state.get("schema")
    question = state.get("question")

    chat_model = config['configurable']['model']

    if model_name == 'gemma2_9b' or model_name == 'finetuned_gemma2_9b' or model_name =='finetuned_gemma2_9b_local':
        prompt = text2cypher_prompt_flattened
        prompt_with_examples = text2cypher_examples_prompt_flattened
    else:
        prompt = text2cypher_prompt
        prompt_with_examples = text2cypher_examples_prompt

    inputs = {
        "question": question,
        "schema": schema,
    }
    if config['configurable']['usar_exemplos']:
        prompt = prompt_with_examples
        inputs["examples"] = montar_bloco_exemplos(question, config['configurable']['n_exemplos'])
    text2cypher_chain = prompt | chat_model | StrOutputParser()

    print('Cypher Generator: START')
    with get_usage_metadata_callback() as cb:
        generated_cypher = text2cypher_chain.invoke(inputs)

    # usage_metadata = {nome_do_modelo: {input_tokens, output_tokens, total_tokens}}
    uso = cb.usage_metadata.values()
    total_tokens = sum(u.get("total_tokens", 0) for u in uso)
    prompt_tokens = sum(u.get("input_tokens", 0) for u in uso)
    completion_tokens = sum(u.get("output_tokens", 0) for u in uso)

    if model_name == 'llama3_2_3b_local':
        generated_cypher = generated_cypher.split('assistant<|end_header_id|>')[1].strip()
    elif model_name == 'finetuned_gemma2_9b_local':
        generated_cypher = generated_cypher.split('<start_of_turn>model\n')[1].strip()
    generated_cypher, limpou = limpar_resposta(generated_cypher)

    return {"cypher_statement": generated_cypher,
            "cypher_history": [generated_cypher],
            "cleaned_responses": [limpou],
            "path": ["cypher_generator"],
            "total_tokens": [total_tokens],
            "prompt_tokens": [prompt_tokens],
            "completion_tokens": [completion_tokens]
            }
