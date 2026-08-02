"""
Utilitários compartilhados por bench_postgres.py e bench_neo4j.py: busca das
queries, carregamento do agrupamento por tipo de operação e gravação do CSV.
"""
import os
import csv
import json
import statistics

# Diretórios
_AQUI = os.path.dirname(__file__)
PERGUNTAS_DIR = os.path.join(_AQUI, "..", "..", "perguntas")
GRUPOS_JSON = os.path.join(PERGUNTAS_DIR, "grupos.json")
OUTPUT_DIR = os.path.join(_AQUI, "output")

# Número de execuções por query. A 1ª é aquecimento (warm-up), marcada como tal
# no CSV e descartada na análise; as demais são as execuções quentes medidas.
N_EXECUCOES = 21

EIXOS = ["ed_basica", "saude", "intersetorial"]


# ---------------------------------------------------------------------------
# GRUPOS (tipo de operação dominante)
# ---------------------------------------------------------------------------
# O agrupamento por operação (filtro, agregacao, anti_join, multi_hop, espacial)
# fica em perguntas/grupos.json e é a dimensão pela qual o benchmark é analisado
# (boxplots por grupo). Aqui carregamos esse mapa e o anexamos a cada query.

def carregar_grupos():
    """Lê grupos.json e devolve o mapa {"eixo/numero": grupo}."""
    with open(GRUPOS_JSON, "r", encoding="utf-8") as f:
        dados = json.load(f)
    mapa = {}
    for grupo, ids in dados["grupos"].items():
        for id_pergunta in ids:
            mapa[id_pergunta] = grupo
    return mapa


def grupo_de(eixo, numero, mapa=None):
    """Devolve o grupo de uma query (ou 'sem_grupo' se não classificada)."""
    mapa = mapa or carregar_grupos()
    return mapa.get(f"{eixo}/{numero}", "sem_grupo")


# ---------------------------------------------------------------------------
# DESCOBERTA DAS QUERIES
# ---------------------------------------------------------------------------

def encontrar_queries(extensao, subpasta, eixos=None, numero=None):
    """
    Localiza os arquivos de query de um dos bancos.

    extensao: 'sql' ou 'cypher'
    subpasta: 'postgreSQL' ou 'neo4j-cypher'
    Retorna lista de dicts: {eixo, numero, grupo, caminho}.
    """
    eixos = eixos or EIXOS
    mapa_grupos = carregar_grupos()
    queries = []
    for eixo in eixos:
        pasta = os.path.join(PERGUNTAS_DIR, eixo, subpasta)
        if not os.path.isdir(pasta):
            continue
        for f in sorted(os.listdir(pasta)):
            if not f.startswith("pergunta_") or not f.endswith(f".{extensao}"):
                continue
            n = int(f.replace("pergunta_", "").replace(f".{extensao}", ""))
            if numero and n != numero:
                continue
            queries.append({
                "eixo": eixo,
                "numero": n,
                "grupo": grupo_de(eixo, n, mapa_grupos),
                "caminho": os.path.join(pasta, f),
            })
    return sorted(queries, key=lambda q: (q["eixo"], q["numero"]))


def ler_query(caminho):
    """Lê o texto de uma query. Remove comentários de linha do Cypher (//)."""
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()
    if caminho.endswith(".cypher"):
        linhas = [l for l in texto.split("\n") if not l.strip().startswith("//")]
        texto = "\n".join(linhas)
    return texto.strip().rstrip(";")


# ---------------------------------------------------------------------------
# SAÍDA (CSV)
# ---------------------------------------------------------------------------

# Colunas comuns aos dois bancos. Cada script acrescenta as suas de I/O.
COLUNAS_BASE = [
    "banco", "eixo", "query", "grupo", "execucao", "warmup",
    "latencia_ms", "linhas", "mem_kb",
]


def salvar_csv(nome_arquivo, linhas, colunas):
    """Grava as medições em output/<nome_arquivo>."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    caminho = os.path.join(OUTPUT_DIR, nome_arquivo)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(linhas)
    print(f"\n[CSV] Resultados salvos em: {caminho} ({len(linhas)} medições)")
    return caminho


def resumo_estatistico(latencias):
    """Média, mediana, desvio, mín e máx de uma lista de latências (ms)."""
    if not latencias:
        return {}
    return {
        "media_ms": round(statistics.mean(latencias), 2),
        "mediana_ms": round(statistics.median(latencias), 2),
        "desvio_ms": round(statistics.stdev(latencias), 2) if len(latencias) > 1 else 0.0,
        "min_ms": round(min(latencias), 2),
        "max_ms": round(max(latencias), 2),
    }
