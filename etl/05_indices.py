"""
Etapa 5: Cria índices sobre as propriedades de nome dos nós.

As consultas em linguagem natural frequentemente buscam entidades pelo nome
(ex: "escolas com 'Professor' no nome", "unidades de saúde no bairro da Sé"),
então indexar os nomes acelera essas buscas e evita varredura completa dos nós.

Este script oferece DUAS abordagens de índice para busca textual. As duas estão
implementadas em blocos separados e independentes: basta ajustar a lista 
ABORDAGENS_ATIVAS abaixo.

  - "texto":    índices TEXT — aceleram =, STARTS WITH e CONTAINS com a
                sintaxe normal de Cypher (WHERE n.nome CONTAINS 'anisio').
                Simétrico ao ILIKE do PostgreSQL.

  - "fulltext": índices FULLTEXT — busca tokenizada e tolerante, acessada por
                CALL db.index.fulltext.queryNodes(...). Acha um termo mesmo no
                meio do nome e permite relevância/fuzzy. Sintaxe própria.

Nota: os nós territoriais já têm CONSTRAINT de unicidade sobre seus códigos
(cd_mun, cd_dist, etc.), criadas no 01_geografia.py, e toda constraint de
unicidade gera um índice automaticamente. Aqui indexamos apenas as
propriedades de NOME, que não são únicas.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))

from db import get_neo4j_driver

# Escolha quais abordagens criar. Opções: "texto", "fulltext".
# ABORDAGENS_ATIVAS = ["texto", "fulltext"]
ABORDAGENS_ATIVAS = []

# (label, propriedade de nome) que representam os nomes buscáveis
CAMPOS_NOME = [
    ("Escola", "nm_aparelho"),
    ("EquipamentoSaude", "nm_aparelho"),
    ("Municipio", "nm_mun"),
    ("Distrito", "nm_dist"),
    ("Bairro", "nm_bairro"),
    ("UF", "nm_uf"),
]


# ---------------------------------------------------------------------------
# ABORDAGEM 1: índices TEXT (igualdade, STARTS WITH, CONTAINS)
# ---------------------------------------------------------------------------

def criar_indices_texto(session):
    print("\n[TEXT] Criando índices de texto...")
    for label, prop in CAMPOS_NOME:
        nome = f"idx_texto_{label.lower()}_{prop}"
        session.run(
            f"CREATE TEXT INDEX {nome} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.{prop})"
        )
        print(f"  [OK] {nome}  ->  (:{label}).{prop}")


# ---------------------------------------------------------------------------
# ABORDAGEM 2: índices FULLTEXT (busca tokenizada / tolerante)
# ---------------------------------------------------------------------------

def criar_indices_fulltext(session):
    print("\n[FULLTEXT] Criando índices full-text...")
    for label, prop in CAMPOS_NOME:
        nome = f"ft_{label.lower()}_{prop}"
        session.run(
            f"CREATE FULLTEXT INDEX {nome} IF NOT EXISTS "
            f"FOR (n:{label}) ON EACH [n.{prop}]"
        )
        print(f"  [OK] {nome}  ->  (:{label}).{prop}")
    print("  Uso: CALL db.index.fulltext.queryNodes('ft_escola_nm_aparelho', 'anisio')")


# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("ETAPA 5: Índices sobre nomes")
    print(f"Abordagens ativas: {ABORDAGENS_ATIVAS}")
    print("=" * 60)

    driver = get_neo4j_driver()

    with driver.session() as session:
        if len(ABORDAGENS_ATIVAS) == 0:
            print(f"Nenhuma abordagem de criação de índice está ativa.")
        if "texto" in ABORDAGENS_ATIVAS:
            criar_indices_texto(session)
        if "fulltext" in ABORDAGENS_ATIVAS:
            criar_indices_fulltext(session)

    # Lista os índices existentes para conferência
    print("\n[Neo4j] Índices no banco:")
    with driver.session() as session:
        for r in session.run("SHOW INDEXES YIELD name, type, labelsOrTypes, properties"):
            print(f"  {r['name']} | {r['type']} | {r['labelsOrTypes']} {r['properties']}")

    driver.close()
    print("\n[OK] Etapa 5 concluída!")


if __name__ == "__main__":
    main()
