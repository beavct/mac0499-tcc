"""
Etapa 1: Cria a espinha dorsal do grafo (hierarquia territorial).
UF -> Municipio -> Distrito -> Subdistrito -> [Bairro] -> SetorCensitario
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))

from config import ESCOPO, filtro_territorial
from db import get_neo4j_driver, pg_fetch_all, neo4j_write, save_csv

# ---------------------------------------------------------------------------
# EXTRAÇÃO DO POSTGRESQL
# ---------------------------------------------------------------------------

def build_query_geografia():
    clausula, _ = filtro_territorial()
    return f"""
SELECT DISTINCT
    cd_uf,
    nm_uf,
    cd_mun,
    nm_mun,
    cd_dist,
    nm_dist,
    cd_subdist,
    nm_subdist,
    NULLIF(TRIM(cd_bairro), '.') AS cd_bairro,
    NULLIF(TRIM(nm_bairro), '.') AS nm_bairro,
    cd_setor,
    situacao,
    v0001,
    v0002,
    v0003,
    v0004,
    v0005,
    v0006,
    v0007,
    ST_AsText(_geom) AS geom_wkt
FROM culturaeduca.datasets.dtb_setores_censitarios_2022
WHERE {clausula};
"""

# ---------------------------------------------------------------------------
# CARGA NO NEO4J
# ---------------------------------------------------------------------------

CYPHER_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:UF) REQUIRE u.sg_uf IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Municipio) REQUIRE m.cd_mun IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Distrito) REQUIRE d.cd_dist IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (sd:Subdistrito) REQUIRE sd.cd_subdist IS UNIQUE",
    # cd_bairro não é único no IBGE (reaparece em subdistritos distintos);
    # a chave precisa ser composta para não criar caminhos múltiplos.
    "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Bairro) REQUIRE (b.cd_bairro, b.cd_subdist) IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:SetorCensitario) REQUIRE s.cd_setor IS UNIQUE",
]

CYPHER_LOAD = """
UNWIND $batch AS row

MERGE (uf:UF {sg_uf: row.cd_uf})
ON CREATE SET uf.nm_uf = row.nm_uf

MERGE (mun:Municipio {cd_mun: row.cd_mun})
ON CREATE SET mun.nm_mun = row.nm_mun

MERGE (dist:Distrito {cd_dist: row.cd_dist})
ON CREATE SET dist.nm_dist = row.nm_dist

MERGE (subdist:Subdistrito {cd_subdist: row.cd_subdist})
ON CREATE SET subdist.nm_subdist = row.nm_subdist

MERGE (setor:SetorCensitario {cd_setor: row.cd_setor})
ON CREATE SET
    setor.situacao = row.situacao,
    setor.v0001 = toInteger(row.v0001),
    setor.v0002 = toInteger(row.v0002),
    setor.v0003 = toInteger(row.v0003),
    setor.v0004 = toInteger(row.v0004),
    setor.v0005 = toFloat(row.v0005),
    setor.v0006 = toFloat(row.v0006),
    setor.v0007 = toInteger(row.v0007),
    setor.geometry = row.geom_wkt

// Hierarquia fixa: Municipio -> UF, Distrito -> Municipio, Subdistrito -> Distrito
MERGE (mun)-[:PARTE_DE]->(uf)
MERGE (dist)-[:PARTE_DE]->(mun)
MERGE (subdist)-[:PARTE_DE]->(dist)

// Condicional: se tem bairro, cria o nó intermediário entre subdistrito e setor
FOREACH (_ IN CASE WHEN row.cd_bairro IS NOT NULL THEN [1] ELSE [] END |
    MERGE (b:Bairro {cd_bairro: row.cd_bairro, cd_subdist: row.cd_subdist})
    ON CREATE SET b.nm_bairro = row.nm_bairro
    MERGE (setor)-[:PARTE_DE]->(b)
    MERGE (b)-[:PARTE_DE]->(subdist)
)

// Cenário sem bairro: setor liga direto no subdistrito
FOREACH (_ IN CASE WHEN row.cd_bairro IS NULL THEN [1] ELSE [] END |
    MERGE (setor)-[:PARTE_DE]->(subdist)
)
"""


def main():
    print("=" * 60)
    print("ETAPA 1: Geografia (hierarquia territorial)")
    print("=" * 60)

    # Extração
    _, params = filtro_territorial()
    print(f"\n[PG] Extraindo setores (escopo: {ESCOPO})")
    data = pg_fetch_all(build_query_geografia(), params)
    print(f"[PG] {len(data)} registros extraídos")

    save_csv(data, "01_geografia.csv")

    # Conversão de tipos para o Neo4j (ele recebe tudo como string via parâmetros)
    for row in data:
        row["v0001"] = int(row["v0001"]) if row["v0001"] is not None else None
        row["v0002"] = int(row["v0002"]) if row["v0002"] is not None else None
        row["v0003"] = int(row["v0003"]) if row["v0003"] is not None else None
        row["v0004"] = int(row["v0004"]) if row["v0004"] is not None else None
        row["v0005"] = float(row["v0005"]) if row["v0005"] is not None else None
        row["v0006"] = float(row["v0006"]) if row["v0006"] is not None else None
        row["v0007"] = int(row["v0007"]) if row["v0007"] is not None else None

    # Carga
    driver = get_neo4j_driver()

    print("\n[Neo4j] Criando constraints...")
    with driver.session() as session:
        for c in CYPHER_CONSTRAINTS:
            session.run(c)

    print("[Neo4j] Carregando nós e arestas da hierarquia territorial...")
    neo4j_write(driver, CYPHER_LOAD, data)

    driver.close()
    print("\n[OK] Etapa 1 concluída!")


if __name__ == "__main__":
    main()
