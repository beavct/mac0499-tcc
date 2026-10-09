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
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

# O E5 foi treinado com esses prefixos na pergunta e no texto; se trocar de modelo,
# confira na página dele no Hugging Face quais prefixos usar
PREFIXO_PERGUNTA = "query: "
PREFIXO_TEXTO = "passage: "

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

# Propriedades que o ETL grava fora das listas de colunas: aparecem sempre no esquema,
# sem passar pela busca. As descrições e valores foram copiados do metadata.attribute
# do PG, da coluna original (o ETL mudou o nome: id_aparelho era co_entidade/co_unidade,
# nm_aparelho era no_entidade/no_fantasia, tp_gestao era tp_gestao2). location e geometry
# foram criadas pelo ETL e não existem no PG.
DESCRICAO_LOCATION = "Localização (latitude/longitude); usar com point.distance"

PROPRIEDADES_FIXAS = [
    {"no_label": "Escola", "propriedade": "id_aparelho", "tipo": "STRING",
     "descricao": "Código da Escola"},
    {"no_label": "Escola", "propriedade": "nm_aparelho", "tipo": "STRING",
     "descricao": "Nome da Escola"},
    {"no_label": "Escola", "propriedade": "location", "tipo": "POINT",
     "descricao": DESCRICAO_LOCATION},
    {"no_label": "EquipamentoSaude", "propriedade": "id_aparelho", "tipo": "STRING",
     "descricao": "Código do Estabelecimento"},
    {"no_label": "EquipamentoSaude", "propriedade": "nm_aparelho", "tipo": "STRING",
     "descricao": "Nome Fantasia"},
    {"no_label": "EquipamentoSaude", "propriedade": "tp_gestao", "tipo": "STRING",
     "descricao": "Tipo de Gestão",
     "valores": "'1' = Municipal, '2' = Estadual, '3' = Dupla, '4' = Sem Gestão"},
    {"no_label": "EquipamentoSaude", "propriedade": "location", "tipo": "POINT",
     "descricao": DESCRICAO_LOCATION},
    {"no_label": "SetorCensitario", "propriedade": "situacao", "tipo": "STRING",
     "descricao": "Situação do Setor Censitário"},
    {"no_label": "SetorCensitario", "propriedade": "geometry", "tipo": "STRING",
     "descricao": "Polígono do setor em texto WKT; não usar em consultas"},
]

# Hierarquia territorial que vai no esquema enviado ao modelo. É fixa porque o ETL sempre
# monta o grafo assim (etl/01_geografia.py). Como nem todo setor tem Bairro, o nº de saltos
# do setor até cada nível varia, e o modelo erra se usar um salto só.
HIERARQUIA_TERRITORIAL = """\
UF <- Municipio <- Distrito <- Subdistrito <- Bairro <- SetorCensitario, todos por PARTE_DE.
Só parte dos setores tem Bairro: os outros ligam direto no Subdistrito. Do setor até cada
nível, use o intervalo de saltos:
(:SetorCensitario)-[:PARTE_DE*1..2]->(:Subdistrito)
(:SetorCensitario)-[:PARTE_DE*2..3]->(:Distrito)
(:SetorCensitario)-[:PARTE_DE*3..4]->(:Municipio)
(:SetorCensitario)-[:PARTE_DE*4..5]->(:UF)
(:SetorCensitario)-[:PARTE_DE]->(:Bairro)  // só os setores que têm bairro"""

# Descrições que faltam no PG e na planilha de metadados, inferidas pelas colunas irmãs
DESCRICOES_INFERIDAS = [
    {"no_label": "Escola", "propriedade": "qt_mat_prof_tec",
     "descricao": "Número de Matrículas da Educação Profissional Técnica"},
]

# Complementos que entram no texto buscado logo depois da descrição, com as palavras que as
# perguntas usam e a descrição do PG não usa. Só o da tp_dependencia foi medido (é a única
# categórica do gabarito); os outros foram escritos para as categóricas de termo técnico.
# Ver testes/rag_buscas/.
COMPLEMENTOS_DESCRICAO = [
    {"no_label": "Escola", "propriedade": "tp_dependencia",
     "complemento": "rede pública ou privada"},
    {"no_label": "Escola", "propriedade": "tp_situacao_funcionamento",
     "complemento": "escolas ativas, fechadas ou desativadas"},
    {"no_label": "Escola", "propriedade": "tp_aee",
     "complemento": "educação especial, alunos com deficiência"},
    {"no_label": "Escola", "propriedade": "tp_localizacao",
     "complemento": "zona urbana ou rural"},
    {"no_label": "Escola", "propriedade": "tp_rede_local",
     "complemento": "internet, wi-fi"},
    {"no_label": "Escola", "propriedade": "tp_atividade_complementar",
     "complemento": "contraturno, atividades extracurriculares"},
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

# --- Valores dos filtros (Camada B) ---------------------------------------
# Propriedades de nome cujos valores são lidos do grafo para ancorar os filtros, e as
# palavras que indicam na pergunta o tipo do lugar ("distrito da Saúde"). Os tipos vão sem
# acento, porque a pergunta é comparada sem acento.
# O Subdistrito não entra porque no grafo ele só tem código.
PROPRIEDADES_VALORES = [
    {"no_label": "UF", "propriedade": "nm_uf", "tipos": ["estado"]},
    {"no_label": "Municipio", "propriedade": "nm_mun", "tipos": ["municipio", "cidade"]},
    # Muitas cidades não possuem bairros propriamente ditos, mas é costume chamar o distrito de bairro
    {"no_label": "Distrito", "propriedade": "nm_dist", "tipos": ["distrito", "bairro"]}, 
    {"no_label": "Bairro", "propriedade": "nm_bairro", "tipos": ["bairro"]},
    {"no_label": "Escola", "propriedade": "nm_aparelho", "tipos": ["escola", "colegio"]},
    {"no_label": "EquipamentoSaude", "propriedade": "nm_aparelho",
     "tipos": ["unidade", "hospital", "posto", "ubs", "aps", "upa", "ama", "ame"]},
]

# Semelhança mínima para o BRIDGE devolver um casamento, e a nota mínima para ele ficar,
# os dois valores do CodeS
LIMIAR_CASAMENTO = 0.85
NOTA_MINIMA_CASAMENTO = 0.9

# O CodeS guarda até 25 valores por propriedade; aqui ficam 5, o bastante para uma pergunta
# que cita vários lugares do mesmo tipo ("escolas em Campinas, Sorocaba e Santos")
MAX_VALORES_POR_COLUNA = 5

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
