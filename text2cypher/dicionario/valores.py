"""
Valores dos filtros (Camada B): acha na pergunta os nomes de lugares e de equipamentos e
devolve os valores que existem de fato no grafo, escritos como estão lá.

Segue a camada semântica de Macedo et al. (SBBD 2026): valores distintos das colunas de
nome, casamento sem acento e sem maiúscula, e um bloco no prompt com os valores achados. No
lugar da extração de entidades por LLM, a pergunta é comparada direto com cada valor pelo
trecho em comum mais longo, como na etapa fina do value retriever do CodeS (Li et al., 2024),
usando as funções do BRIDGE (bridge.py). Como no CodeS, ficam os casamentos com nota a partir
de 0,9, o que pega erros de digitação ('Sorocab' -> 'Sorocaba').

Como muitos lugares têm nome de palavra comum (o distrito da Saúde, o município de Quadra),
entram dois filtros inspirados no TAGME (Ferragina e Scaiella, 2010): o trecho contido em
outro maior é descartado, e o trecho feito só de palavras das descrições do dicionário só
vale se a pergunta disser antes o tipo do lugar.

Uso (teste rápido pelo terminal):
    python valores.py "Quantas escolas há em sao jose dos campos?"
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neo4j import GraphDatabase, basic_auth
from config import (NEO4J_CONFIG, CORPUS_JSON, PROPRIEDADES_VALORES, LIMIAR_CASAMENTO,
                    NOTA_MINIMA_CASAMENTO, MAX_VALORES_POR_COLUNA)
from dicionario.bridge import get_matched_entries

_valores = None
_vocabulario = None

# ---------------------------------------------------------------------------
# CARGA
# ---------------------------------------------------------------------------


def sem_acento(texto):
    """'São José' -> 'Sao Jose'. O BRIDGE compara em minúsculas, mas não tira acentos."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def carregar_valores(driver, database_name="neo4j"):
    """
    Lê do grafo os valores distintos de cada propriedade de PROPRIEDADES_VALORES, só na
    primeira chamada. Para cada uma, guarda os valores sem acento (é com eles que a pergunta
    é comparada) e, para cada valor sem acento, os valores originais.
    """
    global _valores
    if _valores is None:
        _valores = {}
        for p in PROPRIEDADES_VALORES:
            reg, _, _ = driver.execute_query(
                f"MATCH (n:`{p['no_label']}`) WHERE n.`{p['propriedade']}` IS NOT NULL "
                f"RETURN DISTINCT n.`{p['propriedade']}` AS valor",
                database_=database_name,
            )
            originais = {}
            for r in reg:
                originais.setdefault(sem_acento(r["valor"]), []).append(r["valor"])
            # em ordem, para o resultado não variar entre execuções
            _valores[(p["no_label"], p["propriedade"])] = {
                "sem_acento": sorted(originais),
                "originais": originais,
            }
    return _valores


def carregar_vocabulario():
    """Palavras das descrições do dicionário (Camada A), sem acento: 'saude', 'quadra'..."""
    global _vocabulario
    if _vocabulario is None:
        with open(CORPUS_JSON, encoding="utf-8") as f:
            docs = json.load(f)
        _vocabulario = set()
        for d in docs:
            texto = sem_acento(d["tema"] + " " + d["descricao"]).lower()
            _vocabulario.update(re.findall(r"\w+", texto))
    return _vocabulario


# ---------------------------------------------------------------------------
# FILTROS
# ---------------------------------------------------------------------------


def _so_vocabulario(termo):
    """O trecho é feito só de palavras das descrições do dicionário? ('saude', 'quadra')"""
    vocabulario = carregar_vocabulario()
    for palavra in re.findall(r"\w+", termo.lower()):
        if palavra not in vocabulario:
            return False
    return True


def _tipo_antes(pergunta, termo, tipos):
    """A pergunta diz o tipo do lugar logo antes do trecho? ('no distrito da Saude')"""
    # o tipo, no singular ou no plural, e uma preposição opcional antes do trecho
    padrao = (r"\b(" + "|".join(tipos) + r")s?\s+(de|da|do|dos|das)?\s*"
              + re.escape(termo.lower()))
    return re.search(padrao, pergunta.lower()) is not None


def _mais_longos(achados):
    """Tira o trecho contido em outro maior: 'Vila' some quando há 'Vila Sonia'."""
    termos = {a["termo"].lower() for a in achados}
    ficam = []
    for a in achados:
        termo = a["termo"].lower()
        contido = False
        for outro in termos:
            if outro != termo and f" {termo} " in f" {outro} ":
                contido = True
        if not contido:
            ficam.append(a)
    return ficam


# ---------------------------------------------------------------------------
# BUSCA
# ---------------------------------------------------------------------------


def buscar_valores(pergunta, driver, database_name="neo4j"):
    """[{termo, no_label, propriedade, valor}] dos valores do grafo citados na pergunta."""
    valores = carregar_valores(driver, database_name)
    pergunta = sem_acento(pergunta)

    achados = []
    for p in PROPRIEDADES_VALORES:
        coluna = valores[(p["no_label"], p["propriedade"])]
        casados = get_matched_entries(pergunta, coluna["sem_acento"], LIMIAR_CASAMENTO,
                                      LIMIAR_CASAMENTO)
        # o BRIDGE devolve None quando nada casa
        if casados is None:
            continue
        escolhidos = 0
        for _, (valor, termo, nota, nota_termo, _) in casados:
            if nota < NOTA_MINIMA_CASAMENTO:
                continue
            # palavra comum ('centros' -> bairro Centro) só vale com o tipo do lugar antes
            comum = _so_vocabulario(termo) or _so_vocabulario(valor)
            if comum and not _tipo_antes(pergunta, termo, p["tipos"]):
                continue
            for original in coluna["originais"][valor]:
                achados.append({"termo": termo, "no_label": p["no_label"],
                                "propriedade": p["propriedade"], "valor": original})
            escolhidos += 1
            if escolhidos == MAX_VALORES_POR_COLUNA:
                break
    return _mais_longos(achados)


# ---------------------------------------------------------------------------
# MONTAGEM DO BLOCO
# ---------------------------------------------------------------------------


def _literal(valor):
    """Valor como string do Cypher; aspas duplas quando o nome tem apóstrofo (d'Oeste)."""
    if "'" in valor:
        return f'"{valor}"'
    return f"'{valor}'"


def montar_bloco_valores(pergunta, driver, database_name="neo4j"):
    """Monta o trecho do esquema com os valores encontrados. Retorna (texto, achados)."""
    achados = buscar_valores(pergunta, driver, database_name)
    if not achados:
        return "", achados

    por_termo = {}
    for a in achados:
        opcao = f"{a['no_label']}.{a['propriedade']} = {_literal(a['valor'])}"
        por_termo.setdefault(a["termo"], []).append(opcao)

    linhas = ["Valores que existem no grafo para termos da pergunta (use um valor só se a "
              "pergunta estiver se referindo àquele lugar ou equipamento, e escreva-o "
              "exatamente como aparece aqui):"]
    for termo, opcoes in por_termo.items():
        linhas.append(f'- "{termo}": {"; ".join(opcoes)}')
    return "\n".join(linhas), achados


# ---------------------------------------------------------------------------
# EXECUÇÃO (teste rápido)
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print('Uso: python valores.py "sua pergunta"')
        sys.exit(1)

    driver = GraphDatabase.driver(NEO4J_CONFIG["uri"],
                                  auth=basic_auth(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
    database_name = os.getenv("NEO4J_DATABASE", "neo4j")
    bloco, _ = montar_bloco_valores(sys.argv[1], driver, database_name)
    driver.close()

    print(f"Pergunta: {sys.argv[1]!r}\n")
    print(bloco or "(nenhum valor encontrado)")


if __name__ == "__main__":
    main()
