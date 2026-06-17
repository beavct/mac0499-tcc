"""
Etapa 3: Carrega equipamentos de saúde e conecta aos setores censitários.

As colunas de atendimento são lidas do arquivo colunas_saude.txt.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))

from config import MUNICIPIOS
from db import get_neo4j_driver, pg_fetch_all, neo4j_write, save_csv

# ---------------------------------------------------------------------------
# LEITURA DAS COLUNAS
# ---------------------------------------------------------------------------

COLUNAS_FILE = os.path.join(os.path.dirname(__file__), "auxiliares/colunas_saude.txt")


def load_colunas():
    """Lê colunas do arquivo .txt ignorando comentários e linhas vazias."""
    colunas = []
    with open(COLUNAS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                colunas.append(line)
    return colunas


# ---------------------------------------------------------------------------
# EXTRAÇÃO DO POSTGRESQL
# ---------------------------------------------------------------------------


def build_query(colunas):
    """Monta a query SELECT com colunas de atendimento + identificação + localização."""
    cols_sql = ",\n    ".join(f"a.{col}" for col in colunas)
    return f"""
SELECT DISTINCT
    eq.co_unidade AS id_aparelho,
    eq.no_fantasia AS nm_aparelho,
    eq.tp_gestao2 AS tp_gestao,
    eq.latitude,
    eq.longitude,
    s.cd_setor,
    {cols_sql}
FROM culturaeduca.datasets.eq_saude_2025 eq
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON eq.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
WHERE s.cd_mun IN %s;
"""


# ---------------------------------------------------------------------------
# CARGA NO NEO4J
# ---------------------------------------------------------------------------

CYPHER_CONSTRAINT = (
    "CREATE CONSTRAINT IF NOT EXISTS FOR (es:EquipamentoSaude) REQUIRE es.id_aparelho IS UNIQUE"
)

CYPHER_LOAD = """
UNWIND $batch AS row

MERGE (es:EquipamentoSaude {id_aparelho: toString(row.id_aparelho)})
ON CREATE SET
    es.nm_aparelho = row.nm_aparelho,
    es.tp_gestao = row.tp_gestao,
    es.location = point({latitude: toFloat(row.latitude), longitude: toFloat(row.longitude)})
SET es += row.props

WITH es, row
MATCH (setor:SetorCensitario {cd_setor: toString(row.cd_setor)})
MERGE (es)-[:LOCALIZADA_EM]->(setor)
"""

COLUNAS_ESPECIAIS = {"id_aparelho", "nm_aparelho", "tp_gestao", "latitude", "longitude", "cd_setor"}


def prepare_batch(data, colunas):
    """Transforma os dados crus em formato pronto para o Cypher."""
    batch = []
    for row in data:
        props = {}
        for col in colunas:
            val = row.get(col)
            if val is not None:
                # Todas as colunas at_* são booleanas
                try:
                    props[col] = bool(int(val))
                except (ValueError, TypeError):
                    if str(val).lower() in ("true", "t", "1"):
                        props[col] = True
                    else:
                        props[col] = False

        batch.append({
            "id_aparelho": str(row["id_aparelho"]),
            "nm_aparelho": row.get("nm_aparelho"),
            "tp_gestao": row.get("tp_gestao"),
            "latitude": float(row["latitude"]) if row.get("latitude") else None,
            "longitude": float(row["longitude"]) if row.get("longitude") else None,
            "cd_setor": str(row["cd_setor"]),
            "props": props,
        })
    return batch


def main():
    print("=" * 60)
    print("ETAPA 3: Saúde (equipamentos)")
    print("=" * 60)

    # Carrega colunas do arquivo
    colunas = load_colunas()
    print(f"\n[Config] {len(colunas)} colunas carregadas de {COLUNAS_FILE}")

    # Extração
    query = build_query(colunas)
    print(f"[PG] Extraindo equipamentos de saúde para municípios: {MUNICIPIOS}")
    data = pg_fetch_all(query, (tuple(MUNICIPIOS),))
    print(f"[PG] {len(data)} registros extraídos")

    save_csv(data, "03_saude.csv")

    # Prepara batch
    batch = prepare_batch(data, colunas)

    # Carga no Neo4j
    driver = get_neo4j_driver()

    print("\n[Neo4j] Criando constraint...")
    with driver.session() as session:
        session.run(CYPHER_CONSTRAINT)

    print("[Neo4j] Carregando equipamentos de saúde e conectando aos setores...")
    neo4j_write(driver, CYPHER_LOAD, batch)

    driver.close()
    print("\n[OK] Etapa 3 concluída!")


if __name__ == "__main__":
    main()
