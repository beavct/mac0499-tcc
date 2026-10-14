"""
Bloqueio de repetição: acha a consulta que repete uma tentativa que já falhou e monta o bloco
das tentativas anteriores para o corretor.

As consultas ficam em cypher_history (uma por chamada ao gerador ou ao corretor) e os erros
em internal_cypher_errors_history (uma lista por avaliação). Como toda consulta é avaliada
uma vez, o i-ésimo item de uma lista corresponde ao i-ésimo da outra.
"""

# ---------------------------------------------------------------------------
# COMPARAÇÃO
# ---------------------------------------------------------------------------


def _normalizar(consulta):
    """Junta os espaços e quebras de linha, para comparar consultas que só mudam no layout."""
    return " ".join(consulta.split())


def erros_da_repetida(consulta, consultas_anteriores, erros_anteriores):
    """Erros de uma tentativa anterior idêntica à consulta, ou None se a consulta é nova."""
    alvo = _normalizar(consulta)
    for anterior, erros in zip(consultas_anteriores, erros_anteriores):
        if _normalizar(anterior) == alvo:
            return erros
    return None


# ---------------------------------------------------------------------------
# BLOCO PARA O CORRETOR
# ---------------------------------------------------------------------------


def _tentativas_distintas(consulta_atual, consultas, erros, maximo):
    """As últimas tentativas distintas (até maximo), sem a atual, em ordem cronológica."""
    vistas = {_normalizar(consulta_atual)}
    escolhidas = []
    for consulta, erros_consulta in zip(reversed(consultas), reversed(erros)):
        if len(escolhidas) == maximo:
            break
        chave = _normalizar(consulta)
        if chave in vistas:
            continue
        vistas.add(chave)
        escolhidas.append((consulta, erros_consulta))
    escolhidas.reverse()
    return escolhidas


def montar_bloco_tentativas(consulta_atual, consultas, erros, maximo):
    """Texto das tentativas anteriores para o prompt do corretor (vazio se não houver)."""
    linhas = []
    tentativas = _tentativas_distintas(consulta_atual, consultas, erros, maximo)
    for i, (consulta, erros_consulta) in enumerate(tentativas, start=1):
        linhas.append(f"{i}. {_normalizar(consulta)}")
        linhas.append(f"   Errors: {'; '.join(erros_consulta)}")
    return "\n".join(linhas)
