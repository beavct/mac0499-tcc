"""
Teste rápido da Camada B (value grounding) com um LLM falso. A pergunta escreve o nome do
município sem acento e em minúsculas; o teste confere que o value_grounding entra no
caminho, que o gerador recebe o nome como está no grafo e que, com ele, a consulta acha
escolas, enquanto o nome escrito como na pergunta não acha nenhuma. O resto roda de
verdade, então precisa do Neo4j carregado e do índice Chroma.

Uso (a partir de text2cypher/workflow/):
    python teste_value_grounding.py
"""
import os
import sys

# liga a Camada B só neste teste; precisa vir antes de importar o grafo
os.environ["USAR_VALUE_GROUNDING"] = "true"

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from neo4j import GraphDatabase, basic_auth

from executar import responder, NEO4J_CONFIG, NEO4J_DATABASE
from dicionario.valores import montar_bloco_valores
import config_workflow

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

PERGUNTA = "Quantas escolas há em sao jose dos campos?"

# o que o gerador precisa receber no esquema
VALOR_ESPERADO = "Municipio.nm_mun = 'São José dos Campos'"

CONSULTA = (
    "MATCH (e:Escola)-[:LOCALIZADA_EM]->(:SetorCensitario)-[:PARTE_DE*]->"
    "(m:Municipio {{nm_mun: '{}'}}) RETURN count(e) AS escolas"
)
# resposta do LLM falso: a consulta com o nome como está no grafo
CYPHER_COM_VALOR = CONSULTA.format("São José dos Campos")
# o que um LLM sem a Camada B tende a escrever: o nome como veio na pergunta
CYPHER_SEM_VALOR = CONSULTA.format("sao jose dos campos")

CAMINHO_ESPERADO = [
    "schema_rag", "value_grounding", "cypher_generator", "cyver_evaluator",
    "cypher_executor", "output_generator",
]

# pergunta do benchmark sem nome próprio: não deve receber nenhum valor
PERGUNTA_SEM_NOME = "Quantas escolas de educação básica existem em cada município?"

prompts = []


class ModeloFalso(GenericFakeChatModel):
    """LLM falso que guarda os prompts recebidos, para conferir o que chegou ao gerador."""

    def _generate(self, messages, *args, **kwargs):
        prompts.append("\n".join(m.content for m in messages))
        return super()._generate(messages, *args, **kwargs)


def modelo_falso():
    return ModeloFalso(messages=iter([AIMessage(content=CYPHER_COM_VALOR)]))


def contar_escolas(driver, cypher):
    reg, _, _ = driver.execute_query(cypher, database_=NEO4J_DATABASE)
    return reg[0]["escolas"]


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("TESTE RÁPIDO: Camada B (value grounding) com LLM falso")
    print("=" * 60)

    config_workflow.models[config_workflow.MODEL_NAME] = modelo_falso
    resultado = responder(PERGUNTA)

    driver = GraphDatabase.driver(NEO4J_CONFIG["uri"],
                                  auth=basic_auth(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
    sem_valor = contar_escolas(driver, CYPHER_SEM_VALOR)
    bloco, _ = montar_bloco_valores(PERGUNTA, driver, NEO4J_DATABASE)
    bloco_sem_nome, _ = montar_bloco_valores(PERGUNTA_SEM_NOME, driver, NEO4J_DATABASE)
    driver.close()

    path = resultado.get("path", [])
    com_valor = 0
    if resultado.get("database_records"):
        com_valor = resultado["database_records"][0].get("escolas", 0)
    prompt_gerador = prompts[0] if prompts else ""
    checagens = [
        ("caminho passa pelo value_grounding", path == CAMINHO_ESPERADO),
        ("valores trazem o nome como está no grafo", VALOR_ESPERADO in bloco),
        ("gerador recebeu os valores no esquema", bool(bloco) and bloco in prompt_gerador),
        ("consulta com o nome do grafo acha escolas", com_valor > 0),
        ("consulta com o nome da pergunta volta vazia", sem_valor == 0),
        ("pergunta sem nome próprio não recebe valores", bloco_sem_nome == ""),
    ]

    print(f"\nCaminho:  {' -> '.join(path)}")
    print(f"Valores enviados ao gerador:\n{bloco or '-'}")
    print(f"Escolas com o nome do grafo:     {com_valor}")
    print(f"Escolas com o nome da pergunta:  {sem_valor}")
    if resultado.get("execution_error"):
        print(f"Erro de execução: {resultado.get('execution_error')}")

    print()
    for descricao, ok in checagens:
        print(f"  [{'OK' if ok else 'FALHOU'}] {descricao}")

    falhas = len([ok for _, ok in checagens if not ok])
    print(f"\n{'[OK] tudo certo' if not falhas else f'[ERRO] {falhas} checagem(ns) falharam'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
