"""
Fábricas de modelos de linguagem do workflow.

Adaptado do Configuration/models.py do CyVerACT: ficam só modelos abertos, acessados
por uma API compatível com a da OpenAI. A escolha é feita por MODEL_NAME (config_workflow.py).
"""
import os

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Parâmetros de geração do CyVerACT. O limite de 512 tokens vai em extra_body porque o
# langchain-openai troca max_tokens por max_completion_tokens, que o Ollama ignora.
PARAMS_GERACAO = {
    "temperature": 0.01,
    "top_p": 0.9,
    "extra_body": {"max_tokens": 512},
    "streaming": False,
}


def get_ollama_local():
    """Modelo servido localmente pelo Ollama (roda na CPU/GPU da máquina)."""
    return ChatOpenAI(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",  # o Ollama ignora a chave, mas o cliente exige uma
        **PARAMS_GERACAO,
    )


def get_servidor_externo():
    """Modelo aberto em servidor compatível com a API da OpenAI (vLLM, Ollama remoto...)."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY", "sem-chave"),
        **PARAMS_GERACAO,
    )


models = {
    "ollama_local": get_ollama_local,
    "servidor_externo": get_servidor_externo,
}
