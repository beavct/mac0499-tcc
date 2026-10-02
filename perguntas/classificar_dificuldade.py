"""
Classifica as consultas Cypher em fácil, média, difícil e extra, com os critérios do
Spider (Yu et al., 2018) adaptados para o benchmark. A saída vai para dificuldade.json.

Uso (a partir de perguntas/):
    python classificar_dificuldade.py
"""
import glob
import json
import os
import re

PERGUNTAS_DIR = os.path.dirname(os.path.abspath(__file__))
SAIDA_JSON = os.path.join(PERGUNTAS_DIR, "dificuldade.json")
EIXOS = ["ed_basica", "saude", "intersetorial"]
NIVEIS = ["facil", "media", "dificil", "extra"]

AGREGACOES = ["count", "sum", "avg", "min", "max", "collect", "percentileCont",
              "percentileDisc", "stDev", "stDevP"]
CLAUSULAS = ["OPTIONAL MATCH", "MATCH", "WHERE", "WITH", "RETURN", "ORDER BY", "SKIP",
             "LIMIT", "UNWIND"]
NOS_DE_DADOS = ["Escola", "EquipamentoSaude", "Perfil"]

# As consultas do benchmark seguem um mesmo estilo, e o script parte dele: palavras-chave em
# maiúsculas, agregações em minúsculas, textos entre aspas simples e subconsultas escritas
# como EXISTS { } ou CALL (x) { }. Elas não usam UNION, STARTS WITH nem ENDS WITH.

# ---------------------------------------------------------------------------
# COMPONENTES
# ---------------------------------------------------------------------------

# Como no Spider, os componentes de cada consulta são somados em três grupos: 1 (cláusulas
# e junções), 2 (subconsultas) e 3 ("outros", que contam 1 quando há mais de um).
# Não contam o que toda consulta do benchmark tem: localizar os dados no território,
# agrupar por território, ordenar e devolver o município junto do nível pedido.
COMPONENTES = [
    {"nome": "where", "grupo": 1},
    {"nome": "limit", "grupo": 1},
    {"nome": "cruzamentos", "grupo": 1},
    {"nome": "filtro_agregacao", "grupo": 1},
    {"nome": "or", "grupo": 1},
    {"nome": "like", "grupo": 1},
    {"nome": "subconsultas", "grupo": 2},
    {"nome": "varias_agregacoes", "grupo": 3},
    {"nome": "varias_condicoes", "grupo": 3},
    {"nome": "etapas_with", "grupo": 3},
]

# ---------------------------------------------------------------------------
# LEITURA DO CYPHER
# ---------------------------------------------------------------------------


def limpar(cypher):
    """Tira comentários e textos entre aspas, que podem conter palavras como OR e WITH."""
    linhas = [linha.split("//")[0] for linha in cypher.splitlines()]
    # texto entre aspas, ex.: 'Campinas' -> ''
    return re.sub(r"'[^']*'", "''", "\n".join(linhas))


def fim_do_bloco(texto, inicio):
    """Posição logo depois da chave que fecha a chave aberta em texto[inicio]."""
    nivel = 0
    for i in range(inicio, len(texto)):
        if texto[i] == "{":
            nivel += 1
        elif texto[i] == "}":
            nivel -= 1
            if nivel == 0:
                return i + 1
    return len(texto)


def tirar_subconsultas(cypher):
    """Tira os blocos EXISTS { } e CALL { } e conta quantos eram."""
    total = 0
    # EXISTS ou CALL e tudo até a chave que abre o bloco: EXISTS {, CALL (diag) {
    achou = re.search(r"(EXISTS|CALL)[^{]*\{", cypher)
    while achou:
        fim = fim_do_bloco(cypher, achou.end() - 1)
        cypher = cypher[:achou.start()] + " SUBCONSULTA " + cypher[fim:]
        total += 1
        achou = re.search(r"(EXISTS|CALL)[^{]*\{", cypher)
    return cypher, total


def dividir_clausulas(cypher):
    """[(cláusula, corpo)] na ordem em que aparecem."""
    # corta antes de cada palavra de CLAUSULAS e guarda a palavra: [antes, MATCH, corpo, ...]
    partes = re.split(r"\b(" + "|".join(CLAUSULAS) + r")\b", cypher)
    clausulas = []
    for i in range(1, len(partes), 2):
        nome = " ".join(partes[i].split())
        clausulas.append((nome, partes[i + 1]))
    return clausulas


def dividir_no_topo(texto, separador):
    """Divide o texto pelo separador, menos onde ele está dentro de parênteses."""
    pedacos = []
    atual = ""
    nivel = 0
    # pedaços de texto, parênteses e colchetes, e o separador, cada um como um item da lista
    for t in re.split(r"([()\[\]]|" + separador + ")", texto):
        if t in ("(", "["):
            nivel += 1
        elif t in (")", "]"):
            nivel -= 1
        if nivel == 0 and re.fullmatch(separador, t):
            pedacos.append(atual)
            atual = ""
        else:
            atual += t
    pedacos.append(atual)
    return [p.strip() for p in pedacos if p.strip()]


def contar_agregacoes(texto):
    """Quantas funções de AGREGACOES aparecem no texto, ex.: count( ou sum (."""
    padrao = r"\b(" + "|".join(AGREGACOES) + r")\s*\("
    return len(re.findall(padrao, texto))


def eh_subconsulta(condicao):
    """EXISTS { } já trocado pelo marcador, ou um padrão como NOT (s)<-[:LOCALIZADA_EM]-()."""
    return "SUBCONSULTA" in condicao or ")<-[" in condicao


# ---------------------------------------------------------------------------
# CONTAGEM POR CLÁUSULA
# ---------------------------------------------------------------------------


def contar_match(corpo, contagem):
    """Nós de dados e filtros escritos no próprio padrão ({nm_mun: ...})."""
    # cada nó de dado com a sua variável: (ef:Escola) e (em:Escola) são dois papéis
    # (o que vem entre "(" e ":" é a variável, e a palavra depois do ":" é o rótulo)
    for variavel, rotulo in re.findall(r"\((\w*):(\w+)", corpo):
        if any(rotulo.startswith(no) for no in NOS_DE_DADOS):
            contagem["nos_de_dados"].add(f"{variavel}:{rotulo}")
    # o que está entre chaves, ex.: (m:Municipio {nm_mun: 'Campinas'}) -> nm_mun: ''
    for filtro in re.findall(r"\{([^}]*)\}", corpo):
        contagem["where"] = 1
        contagem["condicoes"] += len(dividir_no_topo(filtro, ","))


def contar_where(corpo, depois_de_agregar, contagem):
    """Condições, OR e LIKE. Depois de um WITH que agrega, o WHERE é o HAVING do SQL."""
    contagem["where"] = 1
    if depois_de_agregar:
        contagem["filtro_agregacao"] = 1
    else:
        # a condição que é uma subconsulta (NOT EXISTS {...}) já conta como subconsulta
        condicoes = dividir_no_topo(corpo, "AND")
        contagem["condicoes"] += len([cond for cond in condicoes if not eh_subconsulta(cond)])
    contagem["or"] += corpo.count(" OR ")
    # o equivalente do LIKE: CONTAINS e =~ (expressão regular)
    contagem["like"] += corpo.count("CONTAINS") + corpo.count("=~")
    # padrão usado como condição, ex.: WHERE NOT (s)<-[:LOCALIZADA_EM]-()
    contagem["subconsultas"] += corpo.count(")<-[")
    contagem["agregacoes"] += contar_agregacoes(corpo)


def contar_projecao(corpo, contagem):
    """Agregações de um WITH ou RETURN, e os filtros escritos dentro delas."""
    itens = dividir_no_topo(corpo, ",")
    for item in itens:
        contagem["agregacoes"] += contar_agregacoes(item)
        # count(CASE WHEN e.x > 0 THEN e END) é um filtro escrito dentro da agregação
        if contar_agregacoes(item) and "CASE WHEN" in item:
            contagem["where"] = 1
            contagem["condicoes"] += item.count("WHEN")


def contar(cypher):
    """Conta os componentes de uma consulta."""
    cypher, subconsultas = tirar_subconsultas(limpar(cypher))
    clausulas = dividir_clausulas(cypher)
    nomes = [nome for nome, _ in clausulas]

    contagem = {
        "where": 0,
        "limit": int("LIMIT" in nomes),
        "nos_de_dados": set(),
        "etapas_with": 0,
        "filtro_agregacao": 0,
        "or": 0,
        "like": 0,
        "subconsultas": subconsultas,
        "agregacoes": 0,
        "condicoes": 0,
    }

    nome_anterior, corpo_anterior = None, ""
    for i, (nome, corpo) in enumerate(clausulas):
        if nome in ("MATCH", "OPTIONAL MATCH"):
            contar_match(corpo, contagem)
        elif nome == "WHERE":
            depois_de_agregar = False
            if nome_anterior == "WITH" and contar_agregacoes(corpo_anterior) > 0:
                depois_de_agregar = True
            contar_where(corpo, depois_de_agregar, contagem)
        elif nome in ("WITH", "RETURN"):
            contar_projecao(corpo, contagem)
            # WITH seguido de um novo MATCH: no SQL seria uma subconsulta no FROM
            if nome == "WITH":
                for seguinte in nomes[i + 1:]:
                    if seguinte in ("MATCH", "OPTIONAL MATCH", "UNWIND"):
                        contagem["etapas_with"] += 1
                        break
        elif nome == "ORDER BY":
            contagem["agregacoes"] += contar_agregacoes(corpo)
        nome_anterior, corpo_anterior = nome, corpo

    contagem["cruzamentos"] = max(len(contagem["nos_de_dados"]) - 1, 0)
    contagem["varias_agregacoes"] = int(contagem["agregacoes"] > 1)
    contagem["varias_condicoes"] = int(contagem["condicoes"] > 1)
    contagem["consulta_direta"] = consulta_direta(contagem, nomes)
    contagem["nos_de_dados"] = sorted(contagem["nos_de_dados"])
    return contagem


def consulta_direta(contagem, nomes):
    """Um só tipo de dado num só MATCH, sem etapas, subconsultas nem filtro sobre agregação."""
    if len(contagem["nos_de_dados"]) > 1 or nomes.count("MATCH") != 1:
        return False
    if "OPTIONAL MATCH" in nomes or contagem["etapas_with"] > 0:
        return False
    if contagem["subconsultas"] > 0 or contagem["filtro_agregacao"]:
        return False
    return contagem["agregacoes"] <= 1


# ---------------------------------------------------------------------------
# NÍVEIS
# ---------------------------------------------------------------------------


def somar_grupos(contagem):
    """(grupo 1, grupo 2, grupo 3) da consulta."""
    grupos = [0, 0, 0]
    for comp in COMPONENTES:
        grupos[comp["grupo"] - 1] += contagem[comp["nome"]]
    return tuple(grupos)


def nivel(contagem):
    """
    Faixas inspiradas nas do Spider: quanto mais componentes, mais difícil, e uma subconsulta
    pesa mais que uma cláusula. A consulta direta (um tipo de dado, um MATCH, no máximo uma
    agregação) é sempre fácil.
    """
    g1, g2, g3 = somar_grupos(contagem)
    if contagem["consulta_direta"] or (g1 <= 1 and g2 == 0 and g3 == 0):
        return "facil"
    if g2 >= 2 or (g2 == 1 and g1 + g3 >= 2) or g1 + g3 >= 7:
        return "extra"
    if g2 == 1 or g1 + g3 >= 4 or g3 >= 3:
        return "dificil"
    return "media"


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def numero(arquivo):
    """Número da pergunta no nome do arquivo: pergunta_12.cypher -> 12."""
    return int(re.findall(r"\d+", os.path.basename(arquivo))[0])


def main():
    detalhe = {}
    for eixo in EIXOS:
        arquivos = glob.glob(os.path.join(PERGUNTAS_DIR, eixo, "neo4j-cypher", "*.cypher"))
        for arq in sorted(arquivos, key=numero):
            contagem = contar(open(arq, encoding="utf-8").read())
            contagem["grupos"] = somar_grupos(contagem)
            contagem["nivel"] = nivel(contagem)
            detalhe[f"{eixo}/{numero(arq)}"] = contagem

    print(f"{'consulta':18} {'nível':8}  grupo1 grupo2 grupo3")
    for cid, contagem in detalhe.items():
        g1, g2, g3 = contagem["grupos"]
        print(f"{cid:18} {contagem['nivel']:8}  {g1:>6} {g2:>6} {g3:>6}")

    niveis = {}
    for n in NIVEIS:
        niveis[n] = [cid for cid, contagem in detalhe.items() if contagem["nivel"] == n]
    print(", ".join(f"{n}: {len(lista)}" for n, lista in niveis.items()))

    saida = {
        "_descricao": "Nível de dificuldade de cada consulta Cypher, pelos critérios do "
                      "Spider adaptados. Gerado por classificar_dificuldade.py.",
        "niveis": niveis,
        "detalhe": detalhe,
    }
    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"[JSON] {SAIDA_JSON}")


if __name__ == "__main__":
    main()
