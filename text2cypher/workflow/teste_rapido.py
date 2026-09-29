"""
Teste rápido do workflow com um LLM falso, que devolve respostas prontas: a primeira
com uma propriedade inexistente (para forçar uma correção) e a segunda válida. O resto
roda de verdade, então precisa do Neo4j carregado e do índice Chroma (não do Ollama).

Uso (a partir de text2cypher/workflow/):
    python teste_rapido.py
"""
import sys

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from executar import responder
import config_workflow

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

PERGUNTA = "Quantas escolas há em Campinas?"

# 1ª resposta (gerador): propriedade que não existe -> o CyVer deve reprovar
CYPHER_INVALIDO = "MATCH (e:Escola) RETURN count(e.tem_agua_potavel) AS escolas"

# 2ª resposta (corretor): consulta válida
CYPHER_VALIDO = (
    "MATCH (e:Escola)-[:LOCALIZADA_EM]->(:SetorCensitario)-[:PARTE_DE*]->"
    "(m:Municipio {nm_mun: 'Campinas'}) RETURN count(e) AS escolas"
)

CAMINHO_ESPERADO = [
    "schema_rag", "cypher_generator", "cyver_evaluator", "cypher_corrector",
    "cyver_evaluator", "cypher_executor", "output_generator",
]


def modelo_falso():
    return GenericFakeChatModel(messages=iter([
        AIMessage(content=CYPHER_INVALIDO),
        AIMessage(content=CYPHER_VALIDO),
    ]))


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("TESTE RÁPIDO: workflow com LLM falso")
    print("=" * 60)

    # troca a fábrica do modelo pelo modelo falso só neste teste
    config_workflow.models[config_workflow.MODEL_NAME] = modelo_falso
    resultado = responder(PERGUNTA)

    path = resultado.get("path", [])
    historico = resultado.get("cypher_errors_history") or []
    checagens = [
        ("caminho: gera -> reprova -> corrige -> aprova -> executa", path == CAMINHO_ESPERADO),
        ("CyVer reprovou a 1ª consulta", bool(historico) and bool(historico[0])),
        ("CyVer aprovou a consulta corrigida", resultado.get("cypher_errors") == []),
        ("consulta final é a corrigida", resultado.get("cypher_statement") == CYPHER_VALIDO),
        ("executou sem erro", resultado.get("execution_error") is None),
        ("execução retornou registros", bool(resultado.get("database_records"))),
    ]

    print(f"\nCaminho:   {' -> '.join(path)}")
    print(f"Erros da 1ª tentativa: {historico[0] if historico else '-'}")
    print(f"Registros: {resultado.get('database_records')}")
    if resultado.get("execution_error"):
        print(f"Erro de execução: {resultado.get('execution_error')}")

    print()
    for descricao, ok in checagens:
        print(f"  [{'OK' if ok else 'FALHOU'}] {descricao}")

    falhas = sum(not ok for _, ok in checagens)
    print(f"\n{'[OK] tudo certo' if not falhas else f'[ERRO] {falhas} checagem(ns) falharam'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
