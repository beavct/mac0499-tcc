"""
Etapa 4: Carrega perfis censitários (tabelas de agregados) e conecta aos setores.

A lista de perfis (label + tabela) é lida do arquivo config_perfis.txt.
Cada tabela de agregados vira um nó de perfil com label própria, conectado
ao SetorCensitario via [:TEM_PERFIL].

Todas as colunas da tabela (exceto as internas do PG e cd_setor) são
importadas dinamicamente como propriedades numéricas.
"""
import os
from config import MUNICIPIOS
from db import get_neo4j_driver, pg_fetch_all, neo4j_write, save_csv

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "auxiliares/config_perfis.txt")

COLUNAS_IGNORAR = {"_id", "_data_ingestion_id", "_created_at", "_updated_at", "_geom", "_geog", "cd_setor"}


def load_perfis_config():
    """Lê config_perfis.txt e retorna lista de dicts {label, tabela}."""
    perfis = []
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 2:
                    perfis.append({"label": parts[0], "tabela": parts[1]})
    return perfis


# ---------------------------------------------------------------------------
# EXTRAÇÃO E CARGA
# ---------------------------------------------------------------------------


def query_perfil(tabela):
    """Monta query que pega todas as colunas de uma tabela de agregados."""
    return f"""
        SELECT a.*
        FROM {tabela} a
        JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
          ON a.cd_setor = s.cd_setor
        WHERE s.cd_mun IN %s;
    """


def cypher_perfil(label):
    """Monta Cypher que cria o nó de perfil e seta propriedades via +=."""
    return f"""
        UNWIND $batch AS row

        MATCH (setor:SetorCensitario {{cd_setor: toString(row.cd_setor)}})

        MERGE (setor)-[:TEM_PERFIL]->(perfil:{label} {{cd_setor: toString(row.cd_setor)}})
        SET perfil += row.props
    """


def prepare_batch(data):
    """Separa cd_setor das propriedades numéricas para enviar ao Cypher."""
    batch = []
    for row in data:
        cd_setor = str(row["cd_setor"])
        props = {}
        for key, val in row.items():
            if key in COLUNAS_IGNORAR:
                continue
            if val is not None:
                try:
                    props[key] = float(val)
                except (ValueError, TypeError):
                    props[key] = str(val)
        batch.append({"cd_setor": cd_setor, "props": props})
    return batch


def main():
    print("=" * 60)
    print("ETAPA 4: Perfis censitários")
    print("=" * 60)

    perfis_config = load_perfis_config()
    print(f"\n[Config] {len(perfis_config)} perfis carregados de {CONFIG_FILE}")

    driver = get_neo4j_driver()

    for perfil in perfis_config:
        label = perfil["label"]
        tabela = perfil["tabela"]

        print(f"\n--- {label} ---")
        print(f"[PG] Extraindo de {tabela}...")

        data = pg_fetch_all(query_perfil(tabela), (tuple(MUNICIPIOS),))
        print(f"[PG] {len(data)} registros extraídos")

        if not data:
            print(f"[SKIP] Nenhum dado para {label}")
            continue

        save_csv(data, f"04_{label}.csv")

        batch = prepare_batch(data)

        print(f"[Neo4j] Carregando {label}...")
        cypher = cypher_perfil(label)
        neo4j_write(driver, cypher, batch)

    driver.close()
    print("\n[OK] Etapa 4 concluída!")


if __name__ == "__main__":
    main()
