"""
Configuração do workflow: modelo, limites do laço de correção (k e n), timeout e
flags de ablação.
"""
import os

from Configuration.models import models

# --- Modelo ----------------------------------------------------------------
MODEL_NAME = os.getenv("MODEL_NAME", "ollama_local")   # chave em Configuration/models.py

# --- Laço de correção (Fig. 2) ---------------------------------------------
# Mesmos valores do CyVerACT; com k > n o fallback não é acionado
# k: tentativas com esquema filtrado
ATTEMPTS_W_FILTERED = int(os.getenv("ATTEMPTS_W_FILTERED", "5"))
TOTAL_ATTEMPTS = int(os.getenv("TOTAL_ATTEMPTS", "10"))           # n: tentativas totais (k < n)

# --- Execução no Neo4j -----------------------------------------------------
# limite (s) para executar a query no Neo4j
TIMEOUT_EXECUCAO = float(os.getenv("TIMEOUT_EXECUCAO", "60"))

# --- Ablação ---------------------------------------------------------------
# RAG das propriedades (Camada A); desligado, o esquema leva todas as ~1.800 propriedades
USAR_RAG = os.getenv("USAR_RAG", "true").lower() in ("true", "1", "sim")
# value grounding (Camada B): acrescenta ao esquema os valores reais dos nomes citados
USAR_VALUE_GROUNDING = os.getenv("USAR_VALUE_GROUNDING", "false").lower() in ("true", "1", "sim")


def montar_configuracao():
    """Monta o config['configurable'] do LangGraph, instanciando o modelo escolhido."""
    return {"configurable": {
        "model": models[MODEL_NAME](),
        "model_name": MODEL_NAME,
        "attempts_w_filtered": ATTEMPTS_W_FILTERED,
        "total_attempts": TOTAL_ATTEMPTS,
        "timeout_execucao": TIMEOUT_EXECUCAO,
        "usar_rag": USAR_RAG,
    }}
