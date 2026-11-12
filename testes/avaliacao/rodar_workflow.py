"""
Roda o workflow Text-to-Cypher nas perguntas do benchmark para um dos cenários de CENARIOS (o
modelo e as flags do workflow de cada um).

Cada pergunta vira uma linha em output/<cenario>/resultados.csv e um registro em
output/<cenario>/detalhes.jsonl, gravados assim que ela termina; as perguntas que já estão no
CSV são puladas. Com o Claude, a execução para quando o custo do cenário chega a LIMITE_CUSTO
(padrão US$ 20).

Uso (a partir de testes/avaliacao/):
  python rodar_workflow.py qwen_rag                 # todas as perguntas
  python rodar_workflow.py qwen_rag ed_basica       # só um eixo
  python rodar_workflow.py qwen_rag ed_basica 5     # só a Q5 de educação
  LIMITE_CUSTO=10 python rodar_workflow.py claude_rag
"""
import csv
import json
import os
import re
import sys
import time
from collections import Counter

AVALIACAO_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AVALIACAO_DIR, "..", "..")
PERGUNTAS_DIR = os.path.join(RAIZ, "perguntas")
WORKFLOW_DIR = os.path.join(RAIZ, "text2cypher", "workflow")
OUTPUT_DIR = os.path.join(AVALIACAO_DIR, "output")
EIXOS = ["ed_basica", "saude", "intersetorial"]
LIMITE_CUSTO = float(os.getenv("LIMITE_CUSTO", "20"))   # US$ por cenário, só com o Claude

# o workflow e o gabarito das propriedades (../rag_valores/)
sys.path.insert(0, WORKFLOW_DIR)
sys.path.insert(0, os.path.join(AVALIACAO_DIR, "..", "rag_valores"))

# Cenários da avaliação (Tabela de cenários do Cap. 4): modelo, Camada A e Camada B. As demais
# flags são as mesmas em todos (FLAGS_COMUNS) ou ficam no padrão do workflow
CENARIOS = {
    "qwen_rag": ("qwen2.5-coder:7b", True, False),
    "qwen_rag_vg": ("qwen2.5-coder:7b", True, True),
    "llama_rag": ("llama3.1:8b", True, False),
    "llama_rag_vg": ("llama3.1:8b", True, True),
    "claude_rag": ("claude", True, False),
    "claude_rag_vg": ("claude", True, True),
    "claude_sem_rag": ("claude", False, False),
    "claude_sem_rag_vg": ("claude", False, True),
}
FLAGS_COMUNS = {"BLOQUEAR_REPETICAO": "true", "MAX_TENTATIVAS_MEMORIA": "0",
                "USAR_EXEMPLOS": "true"}

# Variáveis de ambiente que definem o cenário
VARIAVEIS_DO_CENARIO = [
    "MODEL_NAME", "OLLAMA_MODEL", "LLM_MODEL", "CLAUDE_MODEL", "CLAUDE_EFFORT", "USAR_RAG",
    "USAR_VALUE_GROUNDING", "BLOQUEAR_REPETICAO", "MAX_TENTATIVAS_MEMORIA", "TOP_K",
    "TOP_K_FALLBACK", "ATTEMPTS_W_FILTERED", "TOTAL_ATTEMPTS", "TIMEOUT_EXECUCAO",
    "USAR_EXEMPLOS", "N_EXEMPLOS", "EMBEDDING_MODEL",
]

CAMPOS = [
    # identificação
    "cenario", "consulta", "eixo", "dificuldade", "tipo_operacao", "pergunta", "modelo",
    "flags",
    # resposta
    "cypher_final", "valida", "erro_execucao", "n_registros",
    # caminho no workflow
    "caminho", "correcoes", "tentativa_valida", "fallback",
    "valida_apos_fallback", "bloqueio_repeticao", "tentativas_repetidas", "limpeza_bloco",
    "erros_cyver", "erros_cyver_frequentes",
    # custo
    "segundos", "chamadas_llm", "tokens_entrada", "tokens_saida", "tokens_cache_leitura",
    "tokens_cache_escrita", "custo_usd", "custo_acumulado_usd",
    # Camada A
    "n_propriedades_recuperadas", "propriedades_gabarito", "propriedades_faltando",
    "gabarito_recuperado", "gabarito_recuperado_fallback",
    # Camada B e exemplos
    "nomes_camada_b", "exemplos_usados",
]


# ---------------------------------------------------------------------------
# PERGUNTAS
# ---------------------------------------------------------------------------


def carregar_rotulos():
    """{consulta: dificuldade} e {consulta: tipo de operação}, dos arquivos de perguntas/."""
    with open(os.path.join(PERGUNTAS_DIR, "dificuldade.json"), encoding="utf-8") as f:
        niveis = json.load(f)["niveis"]
    dificuldade = {}
    for nivel, consultas in niveis.items():
        for c in consultas:
            dificuldade[c] = nivel

    with open(os.path.join(PERGUNTAS_DIR, "grupos.json"), encoding="utf-8") as f:
        grupos = json.load(f)["grupos"]
    operacao = {}
    for nome, consultas in grupos.items():
        for c in consultas:
            operacao[c] = nome
    return dificuldade, operacao


def carregar_perguntas(eixo=None, numero=None):
    """[{consulta, eixo, numero, pergunta}] das perguntas pedidas, na ordem dos eixos."""
    perguntas = []
    for e in EIXOS:
        if eixo and e != eixo:
            continue
        pasta = os.path.join(PERGUNTAS_DIR, e, "linguagem-natural")
        for arq in os.listdir(pasta):
            achou = re.fullmatch(r"pergunta_(\d+)\.txt", arq)
            if not achou:
                continue
            if numero and int(achou.group(1)) != numero:
                continue
            consulta = f"{e}/{achou.group(1)}"
            with open(os.path.join(pasta, arq), encoding="utf-8") as f:
                pergunta = f.read().strip()
            perguntas.append({"consulta": consulta, "eixo": e, "numero": int(achou.group(1)),
                              "pergunta": pergunta})
    return sorted(perguntas, key=lambda p: (EIXOS.index(p["eixo"]), p["numero"]))


def carregar_gabarito_propriedades():
    """{consulta: propriedades do dicionário usadas no Cypher de referência}."""
    from comparar_textos import carregar_consultas
    from config import CORPUS_JSON
    with open(CORPUS_JSON, encoding="utf-8") as f:
        nomes = {d["variavel"] for d in json.load(f)}
    return {cid: gabarito for cid, _, gabarito in carregar_consultas(nomes)}


# ---------------------------------------------------------------------------
# CENÁRIO
# ---------------------------------------------------------------------------


def flags_do_cenario():
    """Valores efetivos das flags (os do workflow, depois de lidos do ambiente)."""
    import config_workflow
    import config
    from Nodes import schema_retriever
    efetivos = {
        "MODEL_NAME": config_workflow.MODEL_NAME,
        "USAR_RAG": config_workflow.USAR_RAG,
        "USAR_VALUE_GROUNDING": config_workflow.USAR_VALUE_GROUNDING,
        "BLOQUEAR_REPETICAO": config_workflow.BLOQUEAR_REPETICAO,
        "MAX_TENTATIVAS_MEMORIA": config_workflow.MAX_TENTATIVAS_MEMORIA,
        "ATTEMPTS_W_FILTERED": config_workflow.ATTEMPTS_W_FILTERED,
        "TOTAL_ATTEMPTS": config_workflow.TOTAL_ATTEMPTS,
        "TIMEOUT_EXECUCAO": config_workflow.TIMEOUT_EXECUCAO,
        "TOP_K": config.TOP_K,
        "TOP_K_FALLBACK": schema_retriever.TOP_K_FALLBACK,
        "EMBEDDING_MODEL": config.EMBEDDING_MODEL,
        "USAR_EXEMPLOS": config_workflow.USAR_EXEMPLOS,
        "N_EXEMPLOS": config_workflow.N_EXEMPLOS,
    }
    flags = {}
    for nome in VARIAVEIS_DO_CENARIO:
        flags[nome] = efetivos.get(nome, os.getenv(nome))
    # só as variáveis do modelo usado, para o nome do modelo não ficar ambíguo
    for nome in ("OLLAMA_MODEL", "LLM_MODEL", "CLAUDE_MODEL", "CLAUDE_EFFORT"):
        flags[nome] = None
    if flags["MODEL_NAME"] == "ollama_local":
        flags["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    if flags["MODEL_NAME"] == "servidor_externo":
        flags["LLM_MODEL"] = os.getenv("LLM_MODEL")
    if flags["MODEL_NAME"] == "claude":
        from Configuration import claude
        flags["CLAUDE_MODEL"] = claude.MODELO
        flags["CLAUDE_EFFORT"] = claude.ESFORCO
    return flags


def nome_do_modelo(flags):
    """Nome do modelo de linguagem usado no cenário."""
    if flags["MODEL_NAME"] == "claude":
        return flags["CLAUDE_MODEL"]
    if flags["MODEL_NAME"] == "servidor_externo":
        return flags["LLM_MODEL"] or ""
    return flags["OLLAMA_MODEL"]


def ler_resultados(caminho_csv):
    """Linhas que já estão no CSV do cenário."""
    if not os.path.exists(caminho_csv):
        return []
    with open(caminho_csv, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# CUSTO DO CLAUDE
# ---------------------------------------------------------------------------


def custo_gasto(linhas):
    """Soma da coluna custo_usd (vazia sem o Claude)."""
    return sum(float(linha["custo_usd"]) for linha in linhas if linha["custo_usd"])


def custo_das_chamadas(inicio):
    """Chamadas ao Claude feitas desde a posição inicio de claude.USO, com o custo de cada uma."""
    from Configuration import claude
    return [dict(uso, custo_usd=round(claude.custo(uso), 6)) for uso in claude.USO[inicio:]]


# ---------------------------------------------------------------------------
# EXECUÇÃO DE UMA PERGUNTA
# ---------------------------------------------------------------------------


def _somar_tokens(lista):
    """Soma os tokens das chamadas ao LLM (os nós sem LLM guardam -1)."""
    return sum(t for t in lista if t and t > 0)


def rodar_pergunta(app, entrada, configuracao, bloquear_repeticao):
    """Roda o workflow nó a nó (stream_mode="updates") e devolve o resumo da execução."""
    from Nodes.tentativas import erros_da_repetida
    execucao = {"caminho": [], "tentativas": [], "schemas": {}, "grounded_values": "",
                "prompt_tokens": [], "completion_tokens": [], "cypher_final": None,
                "registros": None, "erro_execucao": None, "bloqueios": 0}
    consultas, erros = [], []
    for passo in app.stream(entrada, config=configuracao, stream_mode="updates"):
        for no, atualizacao in passo.items():
            atualizacao = atualizacao or {}
            anterior = execucao["caminho"][-1] if execucao["caminho"] else None
            execucao["caminho"].append(no)
            execucao["prompt_tokens"] += atualizacao.get("prompt_tokens", [])
            execucao["completion_tokens"] += atualizacao.get("completion_tokens", [])
            if "schema" in atualizacao and no != "value_grounding":
                execucao["schemas"][no] = atualizacao["schema"]
            if no == "value_grounding":
                execucao["grounded_values"] = atualizacao.get("grounded_values") or ""
            if "cypher_history" in atualizacao:
                consulta = atualizacao["cypher_history"][0]
                consultas.append(consulta)
                execucao["tentativas"].append({
                    "ordem": len(consultas), "no": no, "cypher": consulta,
                    "limpeza_bloco": atualizacao.get("cleaned_responses", [False])[0],
                    "depois_do_fallback": "schema_retriever" in execucao["caminho"],
                    "repetida": erros_da_repetida(consulta, consultas[:-1], erros) is not None,
                    "bloqueada": False, "erros": None})
            if no == "cyver_evaluator":
                tentativa = execucao["tentativas"][-1]
                if bloquear_repeticao and anterior == "cypher_corrector" and tentativa["repetida"]:
                    tentativa["bloqueada"] = True
                    execucao["bloqueios"] += 1
                tentativa["erros"] = atualizacao.get("internal_cypher_errors_history", [[]])[0]
                erros.append(tentativa["erros"])
            if no == "cypher_executor":
                execucao["registros"] = atualizacao.get("database_records")
                execucao["erro_execucao"] = atualizacao.get("execution_error")
            if no in ("output_generator", "unavailable_output"):
                execucao["cypher_final"] = atualizacao.get("cypher_statement")
    return execucao


# ---------------------------------------------------------------------------
# DIAGNÓSTICO DAS CAMADAS A E B
# ---------------------------------------------------------------------------


def propriedades_do_esquema(schema):
    """Propriedades do trecho recuperado do esquema (lista vazia sem esquema)."""
    if not schema:
        return []
    achou = re.search(r"(Propriedades relevantes para a pergunta:|Todas as propriedades:)\n"
                      r"(.*?)\n\nRelações:", schema, re.S)
    if not achou:
        return []
    # linhas como "    tp_dependencia  // Dependência Administrativa (INTEGER: ...)"
    return re.findall(r"^    (\w+)  //", achou.group(2), re.M)


def nomes_da_camada_b(bloco):
    """[(rótulo, propriedade, valor)] do bloco de valores montado pela Camada B."""
    return re.findall(r"(\w+)\.(\w+) = (?:'([^']*)'|\"([^\"]*)\")", bloco or "")


def exemplos_usados(pergunta, flags):
    """Ids dos exemplos resolvidos que o gerador recebe (vazio sem USAR_EXEMPLOS)."""
    if not flags["USAR_EXEMPLOS"]:
        return []
    from Nodes.exemplos import exemplos_similares
    return [e["id"] for e in exemplos_similares(pergunta, flags["N_EXEMPLOS"])]


# ---------------------------------------------------------------------------
# LINHA DO CSV E DETALHES
# ---------------------------------------------------------------------------


def _codigo_do_erro(erro):
    """Código do erro do CyVer ('Neo.ClientError...: descrição' -> 'Neo.ClientError...')."""
    return erro.split(":", 1)[0].strip()


def montar_saida(p, cenario, flags, rotulos, gabarito_props, execucao, segundos, chamadas,
                 acumulado):
    """(linha do CSV, registro do JSONL) de uma pergunta."""
    dificuldade, operacao = rotulos
    caminho = execucao["caminho"]
    tentativas = execucao["tentativas"]
    valida = "cypher_executor" in caminho
    registros = execucao["registros"]

    codigos = Counter()
    for t in tentativas:
        for erro in t["erros"] or []:
            codigos[_codigo_do_erro(erro)] += 1

    recuperadas = propriedades_do_esquema(execucao["schemas"].get("schema_rag")
                                          or execucao["schemas"].get("schema_completo"))
    do_fallback = propriedades_do_esquema(execucao["schemas"].get("schema_retriever"))
    gabarito = sorted(gabarito_props.get(p["consulta"], set()))
    faltando = [g for g in gabarito if g not in recuperadas]
    nomes_b = [f"{r}.{prop} = {v1 or v2}" for r, prop, v1, v2
               in nomes_da_camada_b(execucao["grounded_values"])]
    exemplos = exemplos_usados(p["pergunta"], flags)

    # sem o Claude, os campos de custo ficam vazios
    custo, custo_acumulado = "", ""
    if acumulado is not None:
        custo = round(sum(c["custo_usd"] for c in chamadas), 6)
        custo_acumulado = round(acumulado, 6)
    tentativa_valida = len(tentativas) if valida else None
    fallback = "schema_retriever" in caminho

    linha = {
        "cenario": cenario,
        "consulta": p["consulta"],
        "eixo": p["eixo"],
        "dificuldade": dificuldade.get(p["consulta"], ""),
        "tipo_operacao": operacao.get(p["consulta"], ""),
        "pergunta": p["pergunta"],
        "modelo": nome_do_modelo(flags),
        "flags": json.dumps(flags, ensure_ascii=False),
        "cypher_final": execucao["cypher_final"] or "",
        "valida": valida,
        "erro_execucao": execucao["erro_execucao"] or "",
        "n_registros": len(registros) if registros is not None else "",
        "caminho": " > ".join(caminho),
        "correcoes": caminho.count("cypher_corrector"),
        "tentativa_valida": tentativa_valida or "",
        "fallback": fallback,
        "valida_apos_fallback": valida and fallback,
        "bloqueio_repeticao": execucao["bloqueios"] > 0,
        "tentativas_repetidas": sum(t["repetida"] for t in tentativas),
        "limpeza_bloco": sum(t["limpeza_bloco"] for t in tentativas),
        "erros_cyver": sum(codigos.values()),
        "erros_cyver_frequentes": "; ".join(f"{c} x{n}" for c, n in codigos.most_common(3)),
        "segundos": round(segundos, 1),
        "chamadas_llm": sum(no in ("cypher_generator", "cypher_corrector") for no in caminho),
        "tokens_entrada": _somar_tokens(execucao["prompt_tokens"]),
        "tokens_saida": _somar_tokens(execucao["completion_tokens"]),
        "tokens_cache_leitura": sum(c["leitura_cache"] for c in chamadas) if chamadas else "",
        "tokens_cache_escrita": sum(c["escrita_cache"] for c in chamadas) if chamadas else "",
        "custo_usd": custo,
        "custo_acumulado_usd": custo_acumulado,
        "n_propriedades_recuperadas": len(recuperadas),
        "propriedades_gabarito": " ".join(gabarito),
        "propriedades_faltando": " ".join(faltando),
        "gabarito_recuperado": not faltando,
        "gabarito_recuperado_fallback": all(g in do_fallback for g in gabarito) if fallback
        else "",
        "nomes_camada_b": "; ".join(nomes_b),
        "exemplos_usados": " ".join(exemplos),
    }
    detalhe = dict(linha)
    detalhe["flags"] = flags
    detalhe.update({
        "registros": registros,
        "tentativas": tentativas,
        "propriedades_recuperadas": recuperadas,
        "propriedades_fallback": do_fallback,
        "valores_camada_b": execucao["grounded_values"],
        "chamadas_claude": chamadas,
    })
    return linha, detalhe


def gravar(pasta, linha, detalhe):
    """Acrescenta a pergunta ao CSV e ao JSONL do cenário."""
    caminho_csv = os.path.join(pasta, "resultados.csv")
    novo = not os.path.exists(caminho_csv)
    with open(caminho_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerow(linha)
    with open(os.path.join(pasta, "detalhes.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(detalhe, ensure_ascii=False, default=str) + "\n")


# ---------------------------------------------------------------------------
# EXECUÇÃO DO CENÁRIO
# ---------------------------------------------------------------------------


def rodar_cenario(cenario, eixo, numero):
    """Roda as perguntas que faltam do cenário e grava cada uma assim que termina."""
    # o workflow lê as flags do ambiente na importação
    from executar import NEO4J_DATABASE
    from graph import app
    from config import NEO4J_CONFIG
    from config_workflow import montar_configuracao
    from Configuration import claude

    flags = flags_do_cenario()
    pasta = os.path.join(OUTPUT_DIR, cenario)
    caminho_csv = os.path.join(pasta, "resultados.csv")
    os.makedirs(pasta, exist_ok=True)
    print(f"[Cenário] {cenario}: {nome_do_modelo(flags)}")
    print("[Flags] " + ", ".join(f"{n}={v}" for n, v in flags.items() if v is not None))

    anteriores = ler_resultados(caminho_csv)
    usa_claude = flags["MODEL_NAME"] == "claude"
    gasto = custo_gasto(anteriores)
    if usa_claude:
        print(f"[Custo] US$ {gasto:.4f} já gastos no cenário, limite de US$ {LIMITE_CUSTO:.2f}")

    perguntas = carregar_perguntas(eixo, numero)
    feitas = {linha["consulta"] for linha in anteriores}
    faltam = [p for p in perguntas if p["consulta"] not in feitas]
    print(f"\n--- {cenario} --- {len(faltam)} perguntas (já feitas: "
          f"{len(perguntas) - len(faltam)})")
    for p in perguntas:
        if p["consulta"] in feitas:
            print(f"[Pulando] {p['consulta']}: já está no CSV")

    rotulos = carregar_rotulos()
    gabarito_props = carregar_gabarito_propriedades()
    entrada_base = {"database_url": NEO4J_CONFIG["uri"], "database_name": NEO4J_DATABASE,
                    "database_user": NEO4J_CONFIG["user"],
                    "database_password": NEO4J_CONFIG["password"]}

    falhas = 0
    for i, p in enumerate(faltam, start=1):
        if usa_claude and gasto >= LIMITE_CUSTO:
            print(f"\n[Custo] US$ {gasto:.4f} gastos, limite de US$ {LIMITE_CUSTO:.2f}: "
                  f"execução interrompida antes de {p['consulta']}")
            break
        inicio_uso = len(claude.USO)
        inicio = time.time()
        try:
            execucao = rodar_pergunta(app, dict(entrada_base, question=p["pergunta"]),
                                      montar_configuracao(), flags["BLOQUEAR_REPETICAO"])
        except Exception as e:
            # a pergunta não é gravada, para ser refeita na próxima execução
            gasto += sum(c["custo_usd"] for c in custo_das_chamadas(inicio_uso))
            print(f"[ERRO] {p['consulta']}: {type(e).__name__}: {e}")
            falhas += 1
            continue
        segundos = time.time() - inicio

        chamadas = custo_das_chamadas(inicio_uso)
        gasto += sum(c["custo_usd"] for c in chamadas)
        linha, detalhe = montar_saida(p, cenario, flags, rotulos, gabarito_props, execucao,
                                      segundos, chamadas, gasto if usa_claude else None)
        gravar(pasta, linha, detalhe)
        custo = f", US$ {linha['custo_usd']:.4f}" if usa_claude else ""
        print(f"[OK] [{i}/{len(faltam)}] {p['consulta']}: válida={linha['valida']}, "
              f"registros={linha['n_registros']}, correções={linha['correcoes']}, "
              f"{linha['segundos']}s{custo}")

    print(f"\n[CSV] {caminho_csv}")
    print(f"[JSONL] {os.path.join(pasta, 'detalhes.jsonl')}")
    if usa_claude:
        print(f"[Custo] US$ {gasto:.4f} gastos no cenário")
    if falhas:
        print(f"[ERRO] {falhas} pergunta(s) com erro, não gravadas (rode de novo para refazer)")


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python rodar_workflow.py <cenario> [eixo] [numero]")
    cenario = sys.argv[1]
    if cenario not in CENARIOS:
        sys.exit(f"[ERRO] Cenário desconhecido: {cenario} (use {', '.join(CENARIOS)})")
    eixo = sys.argv[2] if len(sys.argv) > 2 else None
    numero = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if eixo and eixo not in EIXOS:
        sys.exit(f"[ERRO] Eixo desconhecido: {eixo} (use {', '.join(EIXOS)})")

    # flags do cenário, definidas antes de o workflow ser importado
    modelo, camada_a, camada_b = CENARIOS[cenario]
    os.environ.update(FLAGS_COMUNS)
    os.environ["USAR_RAG"] = str(camada_a).lower()
    os.environ["USAR_VALUE_GROUNDING"] = str(camada_b).lower()
    if modelo == "claude":
        os.environ["MODEL_NAME"] = "claude"
    else:
        os.environ["MODEL_NAME"] = "ollama_local"
        os.environ["OLLAMA_MODEL"] = modelo

    print("=" * 60)
    print("AVALIAÇÃO: workflow Text-to-Cypher nas perguntas do benchmark")
    print("=" * 60)
    rodar_cenario(cenario, eixo, numero)
    print("\n[OK] Execução concluída!")


if __name__ == "__main__":
    main()
