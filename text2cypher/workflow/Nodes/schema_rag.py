"""
Nó de esquema por RAG, que substitui o schema_filtering do CyVerACT: busca no Chroma
as propriedades relevantes para a pergunta e junta com a estrutura do grafo (rótulos,
códigos, nomes e relações), lida do Neo4j.
"""
import atexit
import os
import sys

from neo4j import GraphDatabase, basic_auth

from Nodes.States.states import InputState, OverallState

# sobe até text2cypher/ para importar o retriever e o config
TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
from config import TOP_K, PROPRIEDADES_FIXAS
from dicionario.retriever import montar_fragmento_schema, propriedades_indexadas, descrever

# nº de nós amostrados por rótulo para descobrir as propriedades
AMOSTRA_PROPRIEDADES = 10

# conexão e estrutura do grafo são criadas uma vez só e reaproveitadas
_driver = None
_backbone = None


def _get_driver(url, user, password):
    global _driver
    if _driver is None: # singleton
        _driver = GraphDatabase.driver(url, auth=basic_auth(user, password))
        atexit.register(_driver.close)  # fecha a conexão ao fim do processo
    return _driver


# ---------------------------------------------------------------------------
# ESTRUTURA DO GRAFO
# ---------------------------------------------------------------------------


def _labels(driver, database_name):
    reg, _, _ = driver.execute_query(
        "CALL db.labels() YIELD label RETURN label", database_=database_name
    )
    return sorted(r["label"] for r in reg)


def _relacoes(driver, database_name):
    """Padrões (start)-[rel]->(end) presentes no grafo."""
    reg, _, _ = driver.execute_query(
        "MATCH (a)-[r]->(b) "
        "RETURN DISTINCT labels(a)[0] AS start, type(r) AS rel, labels(b)[0] AS end",
        database_=database_name,
    )
    return sorted((r["start"], r["rel"], r["end"]) for r in reg)


def _propriedades(driver, database_name, label):
    """Propriedades dos nós do rótulo, olhando os que têm mais propriedades."""
    reg, _, _ = driver.execute_query(
        f"MATCH (n:`{label}`) WITH n ORDER BY size(keys(n)) DESC LIMIT {AMOSTRA_PROPRIEDADES} "
        "UNWIND keys(n) AS k RETURN DISTINCT k",
        database_=database_name,
    )
    return sorted(r["k"] for r in reg)


def montar_backbone(driver, database_name):
    """Monta a estrutura do grafo (nós e relações); só lê do banco na primeira chamada."""
    global _backbone
    if _backbone is None:
        no_dicionario = propriedades_indexadas()
        linhas_nos = []
        for label in _labels(driver, database_name):
            ocultas = no_dicionario.get(label, set())
            visiveis = [p for p in _propriedades(driver, database_name, label) if p not in ocultas]
            aviso = ""
            if ocultas:
                aviso = "  // demais propriedades: só as relevantes, listadas abaixo"
            descritas = {d["propriedade"]: d for d in PROPRIEDADES_FIXAS if d["no_label"] == label}
            if descritas:
                # uma por linha, com a descrição de quem tem
                linhas_nos.append(f"- {label}{aviso}")
                for p in visiveis:
                    if p in descritas:
                        d = descritas[p]
                        desc = descrever(d["descricao"], d["tipo"], d.get("valores", ""))
                        linhas_nos.append(f"    {p}  // {desc}")
                    else:
                        linhas_nos.append(f"    {p}")
            else:
                linhas_nos.append(f"- {label} {{{', '.join(visiveis)}}}{aviso}")

        linhas_rels = [f"(:{s})-[:{rel}]->(:{e})" for s, rel, e in _relacoes(driver, database_name)]
        _backbone = ("\n".join(linhas_nos), "\n".join(linhas_rels))
    return _backbone


# ---------------------------------------------------------------------------
# MONTAGEM DO ESQUEMA
# ---------------------------------------------------------------------------


def construir_schema(driver, database_name, question, k):
    """Junta a estrutura do grafo e as propriedades recuperadas em uma única string."""
    fragmento, _ = montar_fragmento_schema(question, k)
    nos, rels = montar_backbone(driver, database_name)
    return (
        "Propriedades dos nós:\n" + nos
        + "\n\nPropriedades relevantes para a pergunta:\n" + fragmento
        + "\n\nRelações:\n" + rels
    )


# ---------------------------------------------------------------------------
# NÓ
# ---------------------------------------------------------------------------


def schema_rag(state: InputState) -> OverallState:
    """Recupera as propriedades relevantes e monta o esquema filtrado da pergunta."""
    question = state.get("question")
    database_url = state.get("database_url")
    database_name = state.get("database_name")
    database_user = state.get("database_user")
    database_password = state.get("database_password")

    driver = _get_driver(database_url, database_user, database_password)
    print('Schema RAG Agent: START')

    schema = construir_schema(driver, database_name, question, k=TOP_K)

    return {"schema": schema,
            "neo4j_driver": driver,
            "path": ["schema_rag"],
            "total_tokens": [-1],
            "prompt_tokens": [-1],
            "completion_tokens": [-1]}
