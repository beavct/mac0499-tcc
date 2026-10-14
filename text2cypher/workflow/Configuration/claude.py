"""
Claude pela API da Anthropic, no formato de modelo de chat do LangChain, com cache de prompt
até o fim do esquema. 
"""
import os
import sys

import anthropic
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

COMPARTILHADO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "compartilhado") 
load_dotenv(os.path.join(COMPARTILHADO_DIR, ".env"))

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

MODELO = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
ESFORCO = os.getenv("CLAUDE_EFFORT", "medium")   # de low a max
# o raciocínio conta dentro do limite de saída, então os 512 tokens do CyVerACT cortariam a
# resposta
MAX_TOKENS = 16000

# Trechos que vêm logo depois do esquema nos prompts do gerador e do corretor: o cache vai até
# o primeiro que aparecer
FIM_DO_ESQUEMA = ["Question:", "Note: Do not include any explanations"]

# ---------------------------------------------------------------------------
# CUSTO
# ---------------------------------------------------------------------------

# US$ por milhão de tokens: entrada, escrita no cache (5 min), leitura do cache e saída
# (preços de outubro de 2026, em platform.claude.com/docs/en/about-claude/pricing)
PRECOS = {
    "claude-sonnet-5-5": (2.00, 2.50, 0.10, 10.00),
}

# uso de cada chamada, na ordem em que foram feitas
USO = []


def custo(uso):
    """Custo em US$ de uma chamada (um item de USO)."""
    entrada, escrita, leitura, saida = PRECOS[uso["modelo"]]
    return (uso["entrada"] * entrada + uso["escrita_cache"] * escrita
            + uso["leitura_cache"] * leitura + uso["saida"] * saida) / 1_000_000


# ---------------------------------------------------------------------------
# CLIENTE E MENSAGENS
# ---------------------------------------------------------------------------

_cliente = None


def get_cliente():
    """Cliente da API, criado na primeira chamada; a chave vem de ANTHROPIC_API_KEY."""
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic()
    return _cliente


def _blocos(texto):
    """Texto do usuário em dois blocos, com o cache até o fim do esquema."""
    posicoes = []
    for marca in FIM_DO_ESQUEMA:
        if marca in texto:
            posicoes.append(texto.index(marca))
    if not posicoes:
        return [{"type": "text", "text": texto}]
    corte = min(posicoes)
    return [
        {"type": "text", "text": texto[:corte], "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": texto[corte:]},
    ]


def _separar(mensagens):
    """(system, blocos do usuário) a partir das mensagens do prompt do LangChain."""
    sistema = []
    usuario = []
    for m in mensagens:
        if m.type == "system":
            sistema.append(m.content)
        else:
            usuario.append(m.content)
    return "\n".join(sistema), _blocos("\n".join(usuario))


# ---------------------------------------------------------------------------
# MODELO
# ---------------------------------------------------------------------------


class ChatClaude(BaseChatModel):
    """Modelo de chat do LangChain que chama o Claude pelo SDK oficial."""

    modelo: str = MODELO
    esforco: str = ESFORCO

    @property
    def _llm_type(self):
        return "claude"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        sistema, blocos = _separar(messages)
        resposta = get_cliente().messages.create(
            model=self.modelo,
            max_tokens=MAX_TOKENS,
            output_config={"effort": self.esforco},
            system=sistema,
            messages=[{"role": "user", "content": blocos}],
        )

        texto = "".join(b.text for b in resposta.content if b.type == "text")
        if resposta.stop_reason == "refusal":
            print(f"Claude: recusou a resposta ({resposta.stop_details})")
        if resposta.stop_reason == "max_tokens":
            print("Claude: resposta cortada no limite de tokens")

        u = resposta.usage
        uso = {
            "modelo": self.modelo,
            "entrada": u.input_tokens,
            "escrita_cache": u.cache_creation_input_tokens or 0,
            "leitura_cache": u.cache_read_input_tokens or 0,
            "saida": u.output_tokens,
            "stop_reason": resposta.stop_reason,
        }
        USO.append(uso)

        # o input_tokens do LangChain é a entrada toda, com e sem cache
        entrada_total = uso["entrada"] + uso["escrita_cache"] + uso["leitura_cache"]
        mensagem = AIMessage(
            content=texto,
            response_metadata={"model_name": self.modelo},
            usage_metadata={
                "input_tokens": entrada_total,
                "output_tokens": uso["saida"],
                "total_tokens": entrada_total + uso["saida"],
                "input_token_details": {"cache_read": uso["leitura_cache"],
                                        "cache_creation": uso["escrita_cache"]},
            },
        )
        return ChatResult(generations=[ChatGeneration(message=mensagem)])


def get_claude():
    """Claude pela API da Anthropic (modelo em CLAUDE_MODEL, esforço em CLAUDE_EFFORT)."""
    # sem o preço, o custo só daria erro depois de a chamada já ter sido paga
    if MODELO not in PRECOS:
        sys.exit(f"Sem preço para {MODELO}: adicione em PRECOS (claude.py)")
    return ChatClaude()
