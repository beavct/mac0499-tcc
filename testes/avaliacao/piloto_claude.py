"""
Piloto do Claude: roda uma pergunta do conjunto no workflow e mostra o uso de tokens e o custo
de cada chamada, com a estimativa para as 66 perguntas de um cenário. Com --conexao, só faz uma
chamada mínima para conferir a chave (custa uma fração de centavo).

Uso (a partir de testes/avaliacao/, com ANTHROPIC_API_KEY no compartilhado/.env):
    MODEL_NAME=claude python piloto_claude.py --conexao
    MODEL_NAME=claude python piloto_claude.py intersetorial/12                  # com a Camada A
    MODEL_NAME=claude USAR_RAG=false python piloto_claude.py intersetorial/12   # esquema completo
"""
import os
import sys

from neo4j import GraphDatabase

# o workflow fica em text2cypher/workflow/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "text2cypher", "workflow"))

from Configuration import claude
from executar import responder, NEO4J_DATABASE
from config import NEO4J_CONFIG
import config_workflow

PERGUNTAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "perguntas")
TOTAL_PERGUNTAS = 66

# ---------------------------------------------------------------------------
# CONEXÃO
# ---------------------------------------------------------------------------


def testar_conexao():
    """Uma chamada mínima, para conferir a chave e o modelo."""
    resposta = claude.get_cliente().messages.create(
        model=claude.MODELO,
        max_tokens=200,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": "Responda só com a palavra: ok"}],
    )
    texto = "".join(b.text for b in resposta.content if b.type == "text")
    print(f"[OK] {resposta.model} respondeu {texto.strip()!r} "
          f"({resposta.usage.input_tokens} tokens de entrada, "
          f"{resposta.usage.output_tokens} de saída)")


# ---------------------------------------------------------------------------
# PILOTO
# ---------------------------------------------------------------------------


def ler_pergunta(consulta):
    """(pergunta, Cypher de referência) de uma consulta como 'intersetorial/12'."""
    eixo, n = consulta.split("/")
    with open(os.path.join(PERGUNTAS_DIR, eixo, "linguagem-natural", f"pergunta_{n}.txt"),
              encoding="utf-8") as f:
        pergunta = f.read().strip()
    with open(os.path.join(PERGUNTAS_DIR, eixo, "neo4j-cypher", f"pergunta_{n}.cypher"),
              encoding="utf-8") as f:
        gabarito = f.read()
    return pergunta, gabarito


def registros_do_gabarito(cypher):
    """Registros da consulta de referência, para comparar com os da gerada."""
    driver = GraphDatabase.driver(NEO4J_CONFIG["uri"],
                                  auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
    registros, _, _ = driver.execute_query(cypher, database_=NEO4J_DATABASE)
    driver.close()
    return registros


def mostrar_uso():
    """Tabela do uso de cada chamada e o custo total."""
    print(f"\n{'chamada':>7} {'entrada':>8} {'escrita':>8} {'leitura':>8} {'saída':>7} "
          f"{'US$':>8}  parada")
    for i, uso in enumerate(claude.USO, start=1):
        print(f"{i:>7} {uso['entrada']:>8} {uso['escrita_cache']:>8} {uso['leitura_cache']:>8} "
              f"{uso['saida']:>7} {claude.custo(uso):>8.4f}  {uso['stop_reason']}")
    total = sum(claude.custo(uso) for uso in claude.USO)
    print(f"{'total':>7} {'':>34} {total:>8.4f}")
    return total


def estimar_cenario(total):
    """
    Custo das 66 perguntas se todas gastassem como esta. Sem a Camada A, o cache escrito na
    primeira pergunta é lido nas outras; com ela, o esquema muda e o cache não é reaproveitado.
    """
    if config_workflow.USAR_RAG:
        estimativa = TOTAL_PERGUNTAS * total
        print(f"\n[Estimativa] {TOTAL_PERGUNTAS} perguntas como esta: US$ {estimativa:.2f}")
        return
    com_cache_quente = 0
    for uso in claude.USO:
        quente = dict(uso)
        quente["leitura_cache"] += quente["escrita_cache"]
        quente["escrita_cache"] = 0
        com_cache_quente += claude.custo(quente)
    estimativa = total + (TOTAL_PERGUNTAS - 1) * com_cache_quente
    print(f"\n[Estimativa] {TOTAL_PERGUNTAS} perguntas como esta: US$ {estimativa:.2f} "
          f"(US$ {com_cache_quente:.4f} por pergunta com o cache já escrito)")


def main():
    print("=" * 60)
    print(f"PILOTO: {claude.MODELO}, esforço {claude.ESFORCO}, "
          f"USAR_RAG={config_workflow.USAR_RAG}")
    print("=" * 60)

    if "--conexao" in sys.argv:
        testar_conexao()
        return

    consulta = sys.argv[1] if len(sys.argv) > 1 else "intersetorial/12"
    pergunta, gabarito = ler_pergunta(consulta)
    print(f"\n[Pergunta] {consulta}: {pergunta}")

    resultado = responder(pergunta)
    registros = resultado.get("database_records") or []
    referencia = registros_do_gabarito(gabarito)

    print("\n=== Cypher gerado ===")
    print(resultado.get("cypher_statement"))
    print(f"\n[Caminho] {' -> '.join(resultado.get('path', []))}")
    print(f"[Registros] gerado: {len(registros)}, gabarito: {len(referencia)}")
    print(f"[Gerado] {registros[:3]}")
    print(f"[Gabarito] {[dict(r) for r in referencia[:3]]}")
    if resultado.get("execution_error"):
        print(f"[Erro na execução] {resultado['execution_error']}")

    total = mostrar_uso()
    estimar_cenario(total)
    print("\n[OK] Piloto concluído!")


if __name__ == "__main__":
    main()
