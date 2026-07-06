"""
Etapa 2: Carrega escolas de educação básica e conecta aos setores censitários.

As colunas importadas são lidas do arquivo colunas_educacao.txt.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))

from config import ESCOPO, filtro_territorial
from db import get_neo4j_driver, pg_fetch_all, neo4j_write, save_csv

# ---------------------------------------------------------------------------
# LEITURA DAS COLUNAS
# ---------------------------------------------------------------------------

COLUNAS_FILE = os.path.join(os.path.dirname(__file__), "auxiliares/colunas_educacao.txt")


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
    """Monta a query SELECT com todas as colunas + latitude/longitude + cd_setor."""
    cols_sql = ",\n    ".join(f"m.{col}" for col in colunas)
    clausula, _ = filtro_territorial("s.")
    return f"""
SELECT DISTINCT
    {cols_sql},
    eq.latitude,
    eq.longitude,
    s.cd_setor
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
WHERE {clausula};
"""


# ---------------------------------------------------------------------------
# CARGA NO NEO4J
# ---------------------------------------------------------------------------

CYPHER_CONSTRAINT = (
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Escola) REQUIRE e.id_aparelho IS UNIQUE"
)


def build_cypher(colunas):
    """
    Monta o Cypher de carga dinamicamente.
    co_entidade vira id_aparelho, no_entidade vira nm_aparelho.
    As demais colunas são setadas como propriedades via SET e += props.
    """
    return """
UNWIND $batch AS row

MERGE (e:Escola {id_aparelho: toString(row.id_aparelho)})
ON CREATE SET
    e.nm_aparelho = row.nm_aparelho,
    e.location = point({latitude: toFloat(row.latitude), longitude: toFloat(row.longitude)})
SET e += row.props

WITH e, row
MATCH (setor:SetorCensitario {cd_setor: toString(row.cd_setor)})
MERGE (e)-[:LOCALIZADA_EM]->(setor)
"""


# Colunas que não vão no dict de props (já tratadas separadamente)
COLUNAS_ESPECIAIS = {"co_entidade", "no_entidade", "latitude", "longitude", "cd_setor"}


def convert_value(col, val):
    """Converte valor para o tipo correto baseado no prefixo da coluna."""
    if val is None:
        return None
    # Colunas in_* são booleanas (0/1 no PG → true/false no Neo4j)
    if col.startswith("in_"):
        try:
            return bool(int(val))
        except (ValueError, TypeError):
            # Caso já venha como 'true'/'false' string
            if str(val).lower() in ("true", "t", "1"):
                return True
            return False
    # Colunas qt_* e nu_* são inteiros
    if col.startswith("qt_") or col.startswith("nu_"):
        try:
            return int(val)
        except (ValueError, TypeError):
            return None
    # Colunas tp_* e co_* são códigos (int)
    if col.startswith("tp_") or col.startswith("co_"):
        try:
            return int(val)
        except (ValueError, TypeError):
            return str(val)
    # Demais: tenta int → float → string
    try:
        return int(val)
    except (ValueError, TypeError):
        try:
            return float(val)
        except (ValueError, TypeError):
            return str(val)


def prepare_batch(data, colunas):
    """Transforma os dados crus em formato pronto para o Cypher."""
    batch = []
    for row in data:
        props = {}
        for col in colunas:
            if col in COLUNAS_ESPECIAIS:
                continue
            val = row.get(col)
            converted = convert_value(col, val)
            if converted is not None:
                props[col] = converted

        batch.append({
            "id_aparelho": str(row["co_entidade"]),
            "nm_aparelho": row.get("no_entidade"),
            "latitude": float(row["latitude"]) if row.get("latitude") else None,
            "longitude": float(row["longitude"]) if row.get("longitude") else None,
            "cd_setor": str(row["cd_setor"]),
            "props": props,
        })
    return batch


def main():
    print("=" * 60)
    print("ETAPA 2: Educação Básica (escolas)")
    print("=" * 60)

    # Carrega colunas do arquivo
    colunas = load_colunas()
    print(f"\n[Config] {len(colunas)} colunas carregadas de {COLUNAS_FILE}")

    # Extração
    query = build_query(colunas)
    _, params = filtro_territorial("s.")
    print(f"[PG] Extraindo escolas (escopo: {ESCOPO})")
    data = pg_fetch_all(query, params)
    print(f"[PG] {len(data)} registros extraídos")

    save_csv(data, "02_educacao.csv")

    # Prepara batch
    batch = prepare_batch(data, colunas)

    # Carga no Neo4j
    driver = get_neo4j_driver()

    print("\n[Neo4j] Criando constraint...")
    with driver.session() as session:
        session.run(CYPHER_CONSTRAINT)

    print("[Neo4j] Carregando escolas e conectando aos setores...")
    cypher = build_cypher(colunas)
    neo4j_write(driver, cypher, batch)

    driver.close()
    print("\n[OK] Etapa 2 concluída!")


if __name__ == "__main__":
    main()
