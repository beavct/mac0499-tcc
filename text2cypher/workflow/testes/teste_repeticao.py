"""
Teste rápido do bloqueio de consulta repetida com um LLM falso. O gerador falso devolve sempre
a mesma consulta inválida e o corretor falso devolve sempre uma outra, também inválida (às vezes
com outra quebra de linha). O workflow roda duas vezes: com BLOQUEAR_REPETICAO ligado, o laço
deve parar na primeira repetição de cada etapa e o corretor deve receber no prompt as tentativas
anteriores; desligado, deve ir até as n correções, como no CyVerACT. O resto roda de verdade,
então precisa do Neo4j carregado e do índice Chroma (não do Ollama).

Uso (a partir de text2cypher/workflow/):
    python testes/teste_repeticao.py
"""
import os
import sys

# sobe até workflow/ para importar o grafo e os nós
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from executar import responder
from Nodes.cypher_corrector import memory_prompt
import config_workflow

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

PERGUNTA = "Quantas escolas têm água potável?"

# resposta do gerador: propriedade que não existe
CYPHER_GERADO = "MATCH (e:Escola) RETURN count(e.tem_agua_potavel) AS escolas"

# resposta do corretor: outra consulta com o mesmo erro, nas duas formatações
CYPHER_CORRIGIDO = "MATCH (e:Escola) WHERE e.tem_agua_potavel = 1 RETURN count(e) AS escolas"
CYPHER_CORRIGIDO_QUEBRADO = (
    "MATCH (e:Escola)\n  WHERE e.tem_agua_potavel = 1\n  RETURN count(e) AS escolas"
)

# trecho que só aparece no prompt do corretor
MARCA_CORRETOR = "Fix the Cypher"
# cabeçalho do bloco das tentativas anteriores (o texto antes da lista)
MARCA_MEMORIA = memory_prompt.split("{previous_attempts}")[0].strip()

# sem o primeiro nó, que é o schema_rag ou o schema_completo (USAR_RAG)
CAMINHO_COM_BLOQUEIO = [
    "cypher_generator", "cyver_evaluator",
    "cypher_corrector", "cyver_evaluator",
    "cypher_corrector", "cyver_evaluator",   # repetiu: vai para o fallback
    "schema_retriever", "cypher_generator", "cyver_evaluator",
    "cypher_corrector", "cyver_evaluator",   # repetiu de novo: desiste
    "unavailable_output",
]

prompts_gerador = []
prompts_corretor = []


class ModeloFalso(GenericFakeChatModel):
    """LLM falso que responde conforme o nó que chamou e guarda os prompts recebidos."""

    def _generate(self, messages, *args, **kwargs):
        prompt = "\n".join(m.content for m in messages)
        resposta = CYPHER_GERADO
        if MARCA_CORRETOR in prompt:
            prompts_corretor.append(prompt)
            resposta = CYPHER_CORRIGIDO
            if len(prompts_corretor) % 2 == 0:
                resposta = CYPHER_CORRIGIDO_QUEBRADO
        else:
            prompts_gerador.append(prompt)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=resposta))])


def modelo_falso():
    return ModeloFalso(messages=iter([]))


def rodar(bloquear):
    """Roda o workflow com a flag dada e devolve (resultado, nº de chamadas ao LLM)."""
    config_workflow.BLOQUEAR_REPETICAO = bloquear
    # a memória vem desligada por padrão; aqui ela é ligada para conferir o que o corretor vê
    config_workflow.MAX_TENTATIVAS_MEMORIA = 3
    prompts_gerador.clear()
    prompts_corretor.clear()
    resultado = responder(PERGUNTA)
    return resultado, len(prompts_gerador) + len(prompts_corretor)


def memoria_do_prompt(prompt):
    """O bloco das tentativas anteriores dentro do prompt do corretor (vazio se não houver)."""
    if MARCA_MEMORIA not in prompt:
        return ""
    bloco = prompt.split(MARCA_MEMORIA)[1]
    return bloco.split("Corrected Cypher statement:")[0].strip()


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("TESTE RÁPIDO: bloqueio de consulta repetida com LLM falso")
    print("=" * 60)

    config_workflow.models[config_workflow.MODEL_NAME] = modelo_falso
    k = config_workflow.ATTEMPTS_W_FILTERED
    n = config_workflow.TOTAL_ATTEMPTS

    ligado, chamadas_ligado = rodar(True)
    memorias_ligado = [memoria_do_prompt(p) for p in prompts_corretor]

    desligado, chamadas_desligado = rodar(False)
    memorias_desligado = [memoria_do_prompt(p) for p in prompts_corretor]

    path_ligado = ligado.get("path", [])
    path_desligado = desligado.get("path", [])
    checagens = [
        ("ligado: para na repetição de cada etapa", path_ligado[1:] == CAMINHO_COM_BLOQUEIO),
        ("ligado: 5 chamadas ao LLM", chamadas_ligado == 5),
        ("ligado: 1º corretor sem tentativas anteriores", memorias_ligado[0] == ""),
        ("ligado: 2º corretor recebe a consulta do gerador e os erros",
         CYPHER_GERADO in memorias_ligado[1] and "UnknownPropertyKey" in memorias_ligado[1]),
        ("ligado: corretor do fallback recebe a consulta corrigida",
         CYPHER_CORRIGIDO in memorias_ligado[2]),
        ("desligado: faz as n correções", path_desligado.count("cypher_corrector") == n),
        ("desligado: fallback uma vez só", path_desligado.count("schema_retriever") == 1),
        ("desligado: termina na desistência", path_desligado[-1] == "unavailable_output"),
        ("desligado: n + 2 chamadas ao LLM", chamadas_desligado == n + 2),
        ("desligado: corretor sem tentativas anteriores",
         memorias_desligado == [""] * len(memorias_desligado)),
    ]

    print(f"\nk = {k}, n = {n}")
    print(f"\nLigado ({chamadas_ligado} chamadas ao LLM):\n  {' -> '.join(path_ligado)}")
    print(f"\nDesligado ({chamadas_desligado} chamadas ao LLM):\n  {' -> '.join(path_desligado)}")
    print(f"\nTentativas anteriores no prompt do 2º corretor (ligado):\n{memorias_ligado[1]}")
    print(f"\nNo corretor do fallback (ligado):\n{memorias_ligado[2]}")

    print()
    for descricao, ok in checagens:
        print(f"  [{'OK' if ok else 'FALHOU'}] {descricao}")

    falhas = [descricao for descricao, ok in checagens if not ok]
    print(f"\n{'[OK] tudo certo' if not falhas else f'[ERRO] {len(falhas)} checagem(ns) falharam'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
