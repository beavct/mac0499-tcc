"""
Limpeza da resposta do modelo antes da validação: tira o bloco de código em Markdown
(```cypher ... ```) que alguns modelos põem em volta da consulta, mesmo com o prompt pedindo
que não ponham. Usada pelo gerador e pelo corretor.
"""
import re

# ``` ou ```cypher no começo e ``` no fim, com espaços e quebras de linha em volta
INICIO_DO_BLOCO = re.compile(r"^\s*```[a-zA-Z]*\s*\n?")
FIM_DO_BLOCO = re.compile(r"\n?\s*```\s*$")


def limpar_resposta(texto):
    """(consulta sem o bloco de código, se havia bloco). Sem bloco, o texto volta igual."""
    if not INICIO_DO_BLOCO.match(texto):
        return texto, False
    texto = INICIO_DO_BLOCO.sub("", texto)
    texto = FIM_DO_BLOCO.sub("", texto)
    return texto.strip(), True
