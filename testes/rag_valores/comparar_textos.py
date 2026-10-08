"""
Experimento: colocar os valores das colunas (ex.: 1 = Federal) no texto indexado ajuda
ou atrapalha o RAG a recuperar as propriedades? Compara três versões do texto:
  A: "tema: descrição"
  B: A + valores das colunas que não são booleanas (como a etapa 01 monta o texto)
  C: A + valores de todas as colunas, inclusive as booleanas

A busca é exata (similaridade de cosseno com todos os textos), para o resultado não
variar entre execuções como no índice HNSW, que é aproximado. O gabarito são as
propriedades usadas no Cypher de cada consulta de perguntas/; a métrica é o recall@k.
Roda com cada modelo de PREFIXOS, e os resultados vão para output/<modelo>/recall.csv e
output/<modelo>/posicoes.csv.

Uso (a partir de testes/rag_valores/, depois da etapa 01 do dicionário):
    python comparar_textos.py            # todos os modelos de PREFIXOS
    python comparar_textos.py <modelo>   # só um deles
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
GRUPOS = ["v* (Censo)", "categórica", "booleana", "outras dos equipamentos"]

# Modelos testados, com os prefixos (pergunta, texto) de cada um
PREFIXOS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": ("", ""),
    "intfloat/multilingual-e5-base": ("query: ", "passage: "),
    EMBEDDING_MODEL: (PREFIXO_PERGUNTA, PREFIXO_TEXTO),
}

# Códigos que marcam um valor fora do normal numa coluna de contagem ou de número, e não
# uma categoria (ex.: qt_prof_psicologo = 88888 é "valor extremo").
CODIGOS_ESPECIAIS = ["88888", "99999999999999"]

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
# GRUPOS
# ---------------------------------------------------------------------------


def categorias(valores):
    """Pedaços 'código = rótulo' dos valores, sem os CODIGOS_ESPECIAIS."""
    # separa nas vírgulas seguidas de um novo "código =", e não nas de dentro dos rótulos
    pedacos = re.split(r", (?=\d+ = )", valores) if valores else []
    return [p for p in pedacos if p.split(" = ")[0] not in CODIGOS_ESPECIAIS]


def tem_codigo_especial(valores):
    for codigo in CODIGOS_ESPECIAIS:
        if valores.startswith(f"{codigo} = ") or f", {codigo} = " in valores:
            return True
    return False


def grupo(doc):
    """
    Grupo da propriedade. Uma coluna dos equipamentos só é categórica se tem algum valor
    que não seja um dos CODIGOS_ESPECIAIS: as contagens qt_* e os CNPJs ficam em "outras".
    """
    if doc["no_label"] not in ("Escola", "EquipamentoSaude"):
        return "v* (Censo)"
    if doc["tipo"] == "BOOLEAN":
        return "booleana"
    if categorias(doc["valores"]):
        return "categórica"
    return "outras dos equipamentos"


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def cita_categoria(pergunta, doc):
    """A pergunta cita algum rótulo das categorias (ex.: 'municipais' para 'Municipal')?"""
    pergunta = sem_acento(pergunta)
    for pedaco in categorias(doc["valores"]):
        rotulo = pedaco.split(" = ", 1)[1]
        for palavra in rotulo.split():
            # compara só o começo da palavra, para 'municipais' casar com 'Municipal'
            if len(palavra) >= 4 and re.search(r"\b" + sem_acento(palavra)[:6], pergunta):
                return True
    return False


# ---------------------------------------------------------------------------
# VERSÕES DO TEXTO E RECUPERAÇÃO
# ---------------------------------------------------------------------------


def texto_da_versao(doc, versao):
    base = f"{doc['tema']}: {doc['descricao']}"
    if versao == "A":
        return base
    # as versões não usam os complementos da etapa 01, que o teste das buscas mede à parte
    if versao == "B" and doc["valores"] and doc["tipo"] != "BOOLEAN":
        return f"{base}. valores: {doc['valores']}"
    if versao == "B":
        return base
    if doc["valores"]:
        return f"{base}. valores: {doc['valores']}"
    return base


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
# MÉTRICAS
# ---------------------------------------------------------------------------


def posicoes_do_gabarito(consultas, rankings, por_nome):
    """Posição de cada propriedade do gabarito em cada versão (None = fora do top-20)."""
    posicoes = []
    for i, (cid, pergunta, gabarito) in enumerate(consultas):
        for p in sorted(gabarito):
            doc = por_nome[p]
            linha = {"consulta": cid, "propriedade": p, "grupo": grupo(doc),
                     "cita_categoria": cita_categoria(pergunta, doc)}
            for v in VERSOES:
                recuperadas = rankings[v][i]
                linha[f"pos_{v}"] = recuperadas.index(p) + 1 if p in recuperadas else None
            posicoes.append(linha)
    return posicoes


def recortes(posicoes):
    """[(nome, linhas)]: todas, cada grupo e as categóricas pela pergunta citar ou não."""
    lista = [("todas", posicoes)]
    for g in GRUPOS:
        lista.append((g, [x for x in posicoes if x["grupo"] == g]))
    categoricas = [x for x in posicoes if x["grupo"] == "categórica"]
    lista.append(("categórica, pergunta cita", [x for x in categoricas if x["cita_categoria"]]))
    lista.append(("categórica, não cita", [x for x in categoricas if not x["cita_categoria"]]))
    return lista


def recall(linhas, versao, k):
    """Fração das linhas cuja propriedade ficou até a posição k na versão dada."""
    acertos = [x for x in linhas if x[f"pos_{versao}"] and x[f"pos_{versao}"] <= k]
    return len(acertos) / len(linhas)


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def salvar_csv(pasta, arquivo, linhas):
    caminho = os.path.join(pasta, arquivo)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"[CSV] {caminho}")


def rodar_modelo(modelo, docs, consultas, por_nome):
    """Roda as três versões com um modelo e grava os CSVs em output/<modelo>/."""
    print(f"\n--- {modelo} ---")
    model = SentenceTransformer(modelo)
    rankings = {}
    for v in VERSOES:
        rankings[v] = ranking_da_versao(model, docs, consultas, v, PREFIXOS[modelo])
    posicoes = posicoes_do_gabarito(consultas, rankings, por_nome)

    cabecalho = " ".join(f"{v}@{k:<3}" for k in KS for v in VERSOES)
    print(f"\n{'grupo':26} {'n':>4} {cabecalho}")
    resumo = []
    for nome, linhas in recortes(posicoes):
        valores = []
        for k in KS:
            for v in VERSOES:
                r = recall(linhas, v, k)
                valores.append(f"{r:6.2f}")
                resumo.append({"grupo": nome, "n": len(linhas), "versao": v, "k": k,
                               "recall": round(r, 4)})
        print(f"{nome:26} {len(linhas):>4} " + " ".join(valores))

    pasta = os.path.join(OUTPUT_DIR, modelo.split("/")[-1])
    os.makedirs(pasta, exist_ok=True)
    salvar_csv(pasta, "recall.csv", resumo)
    salvar_csv(pasta, "posicoes.csv", posicoes)


def main():
    modelos = list(PREFIXOS)
    if len(sys.argv) > 1:
        modelos = [sys.argv[1]]
    for modelo in modelos:
        if modelo not in PREFIXOS:
            sys.exit(f"Modelo sem prefixos definidos: {modelo} (adicione em PREFIXOS)")

    print("=" * 60)
    print("EXPERIMENTO: valores das colunas no texto indexado")
    print("=" * 60)

    docs = json.load(open(CORPUS_JSON, encoding="utf-8"))
    por_nome = {d["variavel"]: d for d in docs}
    consultas = carregar_consultas(set(por_nome))
    total = sum(len(c[2]) for c in consultas)
    print(f"\n[Gabarito] {len(consultas)} consultas, {total} propriedades")

    for modelo in modelos:
        rodar_modelo(modelo, docs, consultas, por_nome)
    print("\n[OK] Experimento concluído!")


if __name__ == "__main__":
    main()
