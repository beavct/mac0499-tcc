"""
Ponto de entrada do workflow: recebe uma pergunta e imprime o Cypher, os registros
e o caminho percorrido.

Uso (a partir de text2cypher/workflow/):
    python executar.py "quantas escolas há em Campinas?"
"""
import os
import sys

TEXT2CYPHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TEXT2CYPHER_DIR)
from config import NEO4J_CONFIG

from graph import app
from config_workflow import montar_configuracao

NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def responder(pergunta):
    entrada = {
        "question": pergunta,
        "database_url": NEO4J_CONFIG["uri"],
        "database_name": NEO4J_DATABASE,
        "database_user": NEO4J_CONFIG["user"],
        "database_password": NEO4J_CONFIG["password"],
    }
    return app.invoke(entrada, config=montar_configuracao())


def main():
    if len(sys.argv) < 2:
        print('Uso: python executar.py "sua pergunta"')
        sys.exit(1)

    resultado = responder(sys.argv[1])

    print("\n=== Cypher gerado ===")
    print(resultado.get("cypher_statement"))
    print("\n=== Registros ===")
    print(resultado.get("database_records"))
    print("\n=== Caminho percorrido ===")
    print(" -> ".join(resultado.get("path", [])))
    if resultado.get("cypher_errors"):
        print("\n=== Erros do CyVer ===")
        print(resultado.get("cypher_errors"))
    if resultado.get("execution_error"):
        print("\n=== Erro na execução (Neo4j) ===")
        print(resultado.get("execution_error"))


if __name__ == "__main__":
    main()
