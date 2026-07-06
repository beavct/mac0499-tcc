import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

PG_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DATABASE"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD"),
}

# ---------------------------------------------------------------------------
# ESCOPO TERRITORIAL
# ---------------------------------------------------------------------------
# Define o recorte geográfico da carga:
#   ESCOPO=cidades  -> apenas os 3 municípios em MUNICIPIOS (padrão)
#   ESCOPO=estado   -> todos os municípios da UF definida em UF
ESCOPO = os.getenv("ESCOPO", "cidades").lower()

MUNICIPIOS = ['3550308', '3509502', '3548708']  # São Paulo, São Bernardo, Campinas
UF = os.getenv("UF", "35")  # 35 = São Paulo


def filtro_territorial(prefixo=""):
    """
    Monta a cláusula WHERE e os parâmetros conforme o ESCOPO escolhido.

    prefixo: alias da tabela de setores na query (ex: "s." para "s.cd_mun").
             Use "" quando a coluna não tem alias.

    Retorna uma tupla (clausula_sql, params) pronta para concatenar na query.
    """
    if ESCOPO == "estado":
        return (f"{prefixo}cd_uf = %s", (UF,))
    return (f"{prefixo}cd_mun IN %s", (tuple(MUNICIPIOS),))


# Se True, salva CSVs intermediários na pasta output/ para conferência manual
SALVAR_CSV = os.getenv("SALVAR_CSV", "true").lower() in ("true", "1", "sim")
