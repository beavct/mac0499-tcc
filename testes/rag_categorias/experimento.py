"""
Experimento: colocar os valores das colunas (ex.: 1 = Federal) no texto indexado ajuda
ou atrapalha o RAG a recuperar as propriedades? Compara três versões do texto:
  A: "tema: descrição"
  B: A + valores só das colunas de código (o que o workflow usa)
  C: A + valores de todas as colunas, inclusive as booleanas

A busca é exata (similaridade de cosseno com todos os textos), para o resultado não
variar entre execuções como no índice HNSW, que é aproximado. O gabarito são as
propriedades usadas no Cypher de cada consulta de perguntas/; a métrica é o recall@k.
Os resultados vão para output/<modelo>/recall.csv e output/<modelo>/posicoes.csv.

Uso (a partir de testes/rag_categorias/, depois da etapa 01 do dicionário):
    python experimento.py                # modelo do text2cypher/config.py
    python experimento.py <modelo>       # um dos modelos de PREFIXOS
"""
import csv
import glob
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "text2cypher"))

import numpy as np
from sentence_transformers import SentenceTransformer
from config import CORPUS_JSON, EMBEDDING_MODEL, PREFIXO_PERGUNTA, PREFIXO_TEXTO

PERGUNTAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "perguntas")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
EIXOS = ["ed_basica", "saude", "intersetorial"]
KS = [5, 10, 20]
VERSOES = ["A", "B", "C"]

# Prefixos (pergunta, texto) de cada modelo com rodada em resultados/
PREFIXOS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": ("", ""),
    "intfloat/multilingual-e5-base": ("query: ", "passage: "),
    EMBEDDING_MODEL: (PREFIXO_PERGUNTA, PREFIXO_TEXTO),
}

# ---------------------------------------------------------------------------
# GABARITO
# ---------------------------------------------------------------------------


def carregar_consultas(nomes_no_dicionario):
    """[(id, pergunta, propriedades do gabarito)] das consultas que usam o dicionário."""
    consultas = []
    for eixo in EIXOS:
        for arq in glob.glob(os.path.join(PERGUNTAS_DIR, eixo, "neo4j-cypher", "*.cypher")):
            n = re.findall(r"\d+", os.path.basename(arq))[0]
            cypher = open(arq, encoding="utf-8").read()
            txt = os.path.join(PERGUNTAS_DIR, eixo, "linguagem-natural", f"pergunta_{n}.txt")
            pergunta = open(txt, encoding="utf-8").read().strip()
            # propriedades acessadas como x.prop ou dentro de {prop: valor}
            usados = set(re.findall(r"\.(\w+)", cypher))
            usados |= set(re.findall(r"[{,]\s*(\w+)\s*:", cypher))
            gabarito = usados & nomes_no_dicionario
            if gabarito:
                consultas.append((f"{eixo}/{n}", pergunta, gabarito))
    return sorted(consultas, key=lambda c: (c[0].split("/")[0], int(c[0].split("/")[1])))


# ---------------------------------------------------------------------------
# VERSÕES DO TEXTO
# ---------------------------------------------------------------------------


def texto_da_versao(doc, versao):
    base = f"{doc['tema']}: {doc['descricao']}"
    if versao == "A":
        return base
    if versao == "B":
        return doc["texto"]  # o corpus já traz os valores das colunas de código
    return f"{base}. valores: {doc['valores']}" if doc["valores"] else base


def grupo(doc):
    if doc["no_label"] not in ("Escola", "EquipamentoSaude"):
        return "v* (Censo)"
    if doc["tipo"] == "BOOLEAN":
        return "booleana"
    if doc["valores"]:
        return "código (tp_*)"
    return "outras (qt_* etc.)"


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def cita_categoria(pergunta, valores):
    """A pergunta cita algum rótulo dos valores (ex.: 'municipais' para 'Municipal')?"""
    pergunta = sem_acento(pergunta)
    for par in valores.split(", "):
        rotulo = par.split(" = ", 1)[-1]
        for palavra in rotulo.split():
            if len(palavra) >= 4 and re.search(r"\b" + sem_acento(palavra)[:6], pergunta):
                return True
    return False


# ---------------------------------------------------------------------------
# RECUPERAÇÃO
# ---------------------------------------------------------------------------


def ranking_da_versao(model, docs, consultas, versao, prefixo=("", "")):
    """Para cada consulta, as propriedades recuperadas (top-20) na versão dada."""
    textos = [prefixo[1] + texto_da_versao(d, versao) for d in docs]
    embeddings = model.encode(textos, normalize_embeddings=True, batch_size=256)
    perguntas = model.encode([prefixo[0] + c[1] for c in consultas], normalize_embeddings=True)
    # vetores normalizados: o produto escalar é a similaridade de cosseno
    similaridade = perguntas @ embeddings.T
    melhores = np.argsort(-similaridade, axis=1)[:, :max(KS)]
    return [[docs[j]["variavel"] for j in linha] for linha in melhores]


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def main():
    modelo = sys.argv[1] if len(sys.argv) > 1 else EMBEDDING_MODEL
    if modelo not in PREFIXOS:
        sys.exit(f"Modelo sem prefixos definidos: {modelo} (adicione em PREFIXOS)")

    print("=" * 60)
    print("EXPERIMENTO: valores das colunas no texto indexado")
    print(f"modelo: {modelo}")
    print("=" * 60)

    docs = json.load(open(CORPUS_JSON, encoding="utf-8"))
    por_nome = {d["variavel"]: d for d in docs}
    consultas = carregar_consultas(set(por_nome))
    total = sum(len(c[2]) for c in consultas)
    print(f"[gabarito] {len(consultas)} consultas, {total} propriedades")

    model = SentenceTransformer(modelo)
    rankings = {v: ranking_da_versao(model, docs, consultas, v, PREFIXOS[modelo])
                for v in VERSOES}

    # Posição de cada propriedade do gabarito em cada versão (None = fora do top-20)
    posicoes = []
    for i, (cid, pergunta, gabarito) in enumerate(consultas):
        for p in sorted(gabarito):
            doc = por_nome[p]
            cita = bool(doc["valores"]) and cita_categoria(pergunta, doc["valores"])
            linha = {"consulta": cid, "propriedade": p, "grupo": grupo(doc), "cita_categoria": cita}
            for v in VERSOES:
                rec = rankings[v][i]
                linha[f"pos_{v}"] = rec.index(p) + 1 if p in rec else None
            posicoes.append(linha)

    # Recall@k por grupo: fração das propriedades do gabarito que ficaram até a posição k
    recortes = [("todas", posicoes)]
    for g in ["v* (Censo)", "código (tp_*)", "booleana", "outras (qt_* etc.)"]:
        recortes.append((g, [x for x in posicoes if x["grupo"] == g]))
    codigos = [x for x in posicoes if x["grupo"] == "código (tp_*)"]
    recortes.append(("código, pergunta cita", [x for x in codigos if x["cita_categoria"]]))
    recortes.append(("código, não cita", [x for x in codigos if not x["cita_categoria"]]))

    print(f"\n{'grupo':22} {'n':>4} " + " ".join(f"{v}@{k:<3}" for k in KS for v in VERSOES))
    resumo = []
    for nome, linhas in recortes:
        valores = []
        for k in KS:
            for v in VERSOES:
                r = sum(1 for x in linhas if x[f"pos_{v}"] and x[f"pos_{v}"] <= k) / len(linhas)
                valores.append(f"{r:6.2f}")
                resumo.append({"grupo": nome, "n": len(linhas), "versao": v, "k": k,
                               "recall": round(r, 4)})
        print(f"{nome:22} {len(linhas):>4} " + " ".join(valores))

    pasta = os.path.join(OUTPUT_DIR, modelo.split("/")[-1])
    os.makedirs(pasta, exist_ok=True)
    for arquivo, linhas in [("recall.csv", resumo), ("posicoes.csv", posicoes)]:
        caminho = os.path.join(pasta, arquivo)
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0]))
            w.writeheader()
            w.writerows(linhas)
        print(f"[CSV] {caminho}")


if __name__ == "__main__":
    main()
