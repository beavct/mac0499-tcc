import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPARTILHADO_DIR = os.path.join(BASE_DIR, "..", "compartilhado")

# Carrega as credenciais do PostgreSQL e Neo4j
load_dotenv(os.path.join(COMPARTILHADO_DIR, ".env"))

PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DATABASE", "culturaeduca"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}
PG_SCHEMA = os.getenv("PG_SCHEMA", "datasets")

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD"),
}

# --- Caminhos -------------------------------------------------------------
CORPUS_DIR = os.path.join(BASE_DIR, "dicionario", "corpus")
CORPUS_JSON = os.path.join(CORPUS_DIR, "variaveis.json")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
CHROMA_COLLECTION = "variaveis_v"

# --- Modelo de embedding --------------------------------------------------
# Multilíngue (as descrições estão em PT-BR).
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Nº de propriedades recuperadas por pergunta no retriever
TOP_K = int(os.getenv("TOP_K", "20"))

# --- Mapeamento nó do grafo -> origem das descrições no Postgres ----------
# Os perfis vêm de etl/auxiliares/config_perfis.txt; as variáveis v0001..v0007
# ficam no nó SetorCensitario.
CONFIG_PERFIS = os.path.join(BASE_DIR, "..", "etl", "auxiliares", "config_perfis.txt")

GEOGRAFIA = {
    "no_label": "SetorCensitario",
    "tabela": "dtb_setores_censitarios_2022",
}

# Equipamentos: mesmas listas de colunas do ETL, descrições das tabelas de microdados
AUXILIARES_ETL = os.path.join(BASE_DIR, "..", "etl", "auxiliares")
EQUIPAMENTOS = [
    {"no_label": "Escola", "tabela": "microdados_ed_basica_2024",
     "colunas": os.path.join(AUXILIARES_ETL, "colunas_educacao.txt")},
    {"no_label": "EquipamentoSaude", "tabela": "microdados_saude_2025_atendimentos",
     "colunas": os.path.join(AUXILIARES_ETL, "colunas_saude.txt")},
]

# Colunas internas do PG que nunca viram documento
COLUNAS_IGNORAR = {
    "_id", "_data_ingestion_id", "_created_at", "_updated_at",
    "_geom", "_geog", "cd_setor",
}

# Tema legível a partir do label do nó
TEMA_POR_LABEL = {
    "PerfilAlfabetizacao": "Alfabetização",
    "PerfilDemografia": "Demografia",
    "PerfilParentesco": "Parentesco / responsável pelo domicílio",
    "PerfilRacaCor": "Raça ou cor",
    "PerfilDomiciliosParte1": "Domicílios (parte 1)",
    "PerfilDomiciliosParte2": "Domicílios (parte 2)",
    "PerfilDomiciliosParte3": "Domicílios (parte 3)",
    "PerfilEntornoDomicilios": "Entorno dos domicílios",
    "SetorCensitario": "Geografia / setor censitário",
    "Escola": "Escola de educação básica",
    "EquipamentoSaude": "Equipamento de saúde",
}

def load_perfis_config():
    """Lê config_perfis.txt -> lista de dicts {no_label, tabela}."""
    perfis = []
    with open(CONFIG_PERFIS, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 2:
                # a tabela no config vem com prefixo culturaeduca.datasets.
                perfis.append({"no_label": parts[0], "tabela": parts[1].split(".")[-1]})
    return perfis


def load_colunas(path):
    """Lê uma lista de colunas do ETL (uma por linha; # é comentário) -> set."""
    with open(path, "r", encoding="utf-8") as f:
        return {l.strip() for l in f if l.strip() and not l.strip().startswith("#")}
