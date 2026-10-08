"""
Experimento: qual forma de busca recupera melhor as propriedades do dicionário?

Compara a busca vetorial, o BM25 e a híbrida, que junta as duas por RRF como o workflow
vai fazer. Também testa a híbrida com os complementos de descrição da etapa 01, o MMR e o
reranker. Todas as buscas usam as peças prontas do LangChain.

O gabarito, a métrica e os grupos de propriedade são os do teste dos valores
(../rag_valores/). Os resultados vão para output/recall.csv e output/posicoes.csv.

Uso (a partir de testes/rag_buscas/, depois da etapa 01 do dicionário):
    python comparar_buscas.py              # sem o reranker
    python comparar_buscas.py --reranker   # com o reranker (baixa ~2,3 GB na primeira vez)
"""
import csv
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag_valores"))

import snowballstemmer
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from sentence_transformers import CrossEncoder, SentenceTransformer

from comparar_textos import CORPUS_JSON, EMBEDDING_MODEL, GRUPOS, carregar_consultas, grupo
from config import PREFIXO_PERGUNTA, PREFIXO_TEXTO
from stopwords_pt import STOPWORDS

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
NOTAS_RERANKER = os.path.join(OUTPUT_DIR, "notas_reranker.csv")
KS = [5, 10, 20, 30]

# Constante do RRF, a do artigo original e a padrão do LangChain
C_RRF = 60

# MMR e reranker reordenam só as 50 primeiras
PESO_MMR = 0.5
CANDIDATOS = 50
RERANKER = "BAAI/bge-reranker-v2-m3"

stemmer = snowballstemmer.stemmer("portuguese")

# ---------------------------------------------------------------------------
# TEXTOS
# ---------------------------------------------------------------------------


def sem_complementos(docs):
    """Cópia dos docs com o texto sem os complementos que a etapa 01 põe na descrição."""
    novos = []
    for d in docs:
        novo = dict(d)
        if d["complemento"]:
            novo["texto"] = d["texto"].replace(f" ({d['complemento']})", "", 1)
        novos.append(novo)
    return novos


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def tokenizar(texto):
    """Palavras em minúsculas, sem stopwords, reduzidas ao radical: 'escolas' -> 'escol'."""
    radicais = []
    for palavra in re.findall(r"\w+", texto.lower()):
        if sem_acento(palavra) not in STOPWORDS:
            radicais.append(sem_acento(stemmer.stemWord(palavra)))
    return radicais


# ---------------------------------------------------------------------------
# BUSCAS
# ---------------------------------------------------------------------------


class EmbeddingE5(Embeddings):
    """O InMemoryVectorStore pede o modelo neste formato; aqui entram os prefixos do E5."""

    def __init__(self, model):
        self.model = model

    def embed_documents(self, textos):
        textos = [PREFIXO_TEXTO + t for t in textos]
        return self.model.encode(textos, normalize_embeddings=True).tolist()

    def embed_query(self, texto):
        return self.model.encode(PREFIXO_PERGUNTA + texto, normalize_embeddings=True).tolist()


def documentos(docs):
    return [Document(d["texto"], metadata={"variavel": d["variavel"]}) for d in docs]


def criar_base_vetorial(model, docs):
    """Busca vetorial exata do LangChain. No workflow é o Chroma, que dá o mesmo resultado."""
    return InMemoryVectorStore.from_documents(documentos(docs), EmbeddingE5(model))


def retriever_bm25(docs):
    return BM25Retriever.from_documents(documentos(docs), preprocess_func=tokenizar,
                                        k=len(docs))


def buscar(retriever, consultas):
    """Para cada pergunta, as variáveis na ordem em que o retriever devolve."""
    ordens = []
    for _, pergunta, _ in consultas:
        ordens.append([r.metadata["variavel"] for r in retriever.invoke(pergunta)])
    return ordens


def buscar_hibrida(retrievers, consultas):
    """RRF do EnsembleRetriever. O id_key junta pela variável, porque 21 textos se repetem."""
    hibrida = EnsembleRetriever(retrievers=retrievers, weights=[1, 1], c=C_RRF,
                                id_key="variavel")
    return buscar(hibrida, consultas)


def buscar_mmr(base_vetorial, consultas, vetorial):
    """MMR do LangChain nas CANDIDATOS primeiras da vetorial; o resto vem depois."""
    ordens = []
    for (_, pergunta, _), lista in zip(consultas, vetorial):
        escolhidos = base_vetorial.max_marginal_relevance_search(
            pergunta, k=CANDIDATOS, fetch_k=CANDIDATOS, lambda_mult=PESO_MMR)
        # o MMR só reordena as CANDIDATOS primeiras, então o resto é o da vetorial
        topo = [r.metadata["variavel"] for r in escolhidos]
        ordens.append(topo + lista[CANDIDATOS:])
    return ordens


# ---------------------------------------------------------------------------
# RERANKER
# ---------------------------------------------------------------------------


def notas_reranker(por_nome, consultas, primeiras):
    """
    Nota do reranker para cada par (pergunta, propriedade). As notas ficam em
    output/notas_reranker.csv, para rodar de novo sem baixar o modelo.
    """
    notas = {}
    if os.path.exists(NOTAS_RERANKER):
        with open(NOTAS_RERANKER, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                notas[(r["consulta"], r["propriedade"])] = float(r["nota"])

    faltam = []
    for (cid, pergunta, _), lista in zip(consultas, primeiras):
        for variavel in lista:
            if (cid, variavel) not in notas:
                faltam.append((cid, pergunta, variavel))
    if not faltam:
        return notas

    modelo = CrossEncoder(RERANKER, max_length=256)
    pares = [(pergunta, por_nome[variavel]["texto"]) for _, pergunta, variavel in faltam]
    for (cid, _, variavel), nota in zip(faltam, modelo.predict(pares, batch_size=32)):
        notas[(cid, variavel)] = float(nota)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(NOTAS_RERANKER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["consulta", "propriedade", "nota"])
        for (cid, variavel), nota in sorted(notas.items()):
            w.writerow([cid, variavel, nota])
    return notas


def buscar_reranker(por_nome, consultas, hibrida):
    """Reordena as CANDIDATOS primeiras da híbrida pela nota do reranker."""
    primeiras = [lista[:CANDIDATOS] for lista in hibrida]
    notas = notas_reranker(por_nome, consultas, primeiras)
    ordens = []
    for (cid, _, _), topo, lista in zip(consultas, primeiras, hibrida):
        topo = sorted(topo, key=lambda variavel: -notas[(cid, variavel)])
        ordens.append(topo + lista[CANDIDATOS:])
    return ordens


# ---------------------------------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------------------------------


def posicoes_do_gabarito(nome, ordens, consultas, por_nome):
    """Posição de cada propriedade do gabarito na ordem de cada pergunta (1 = primeira)."""
    posicoes = []
    for (cid, _, gabarito), lista in zip(consultas, ordens):
        lugar = {variavel: p for p, variavel in enumerate(lista, start=1)}
        for prop in sorted(gabarito):
            posicoes.append({"variante": nome, "consulta": cid, "propriedade": prop,
                             "grupo": grupo(por_nome[prop]), "pos": lugar[prop]})
    return posicoes


def resumo(nome, posicoes, consultas):
    """Recall@k por grupo e perguntas completas (todas as do gabarito no top-k)."""
    linha = {"variante": nome}
    for g in ["todas"] + GRUPOS:
        do_grupo = [x for x in posicoes if g == "todas" or x["grupo"] == g]
        for k in KS:
            acertos = sum(1 for x in do_grupo if x["pos"] <= k)
            linha[f"{g}@{k}"] = round(acertos / len(do_grupo), 4)
    for k in KS:
        completas = 0
        for cid, _, gabarito in consultas:
            achadas = sum(1 for x in posicoes if x["consulta"] == cid and x["pos"] <= k)
            if achadas == len(gabarito):
                completas += 1
        linha[f"completas@{k}"] = completas
    return linha


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def salvar_csv(arquivo, linhas):
    caminho = os.path.join(OUTPUT_DIR, arquivo)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"[CSV] {caminho}")


def main():
    print("=" * 60)
    print("EXPERIMENTO: formas de busca na Camada A")
    print("=" * 60)

    # Gabarito (as buscas usam o texto sem os complementos, que são testados à parte)
    corpus = json.load(open(CORPUS_JSON, encoding="utf-8"))
    docs = sem_complementos(corpus)
    por_nome = {d["variavel"]: d for d in docs}
    consultas = carregar_consultas(set(por_nome))
    print(f"\n[Gabarito] {len(consultas)} consultas, {len(docs)} propriedades")

    # Vetorial e BM25. Cada retriever devolve todas as propriedades, para o RRF não usar
    # só as primeiras
    print("[Busca] Vetorial e BM25...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    base_vetorial = criar_base_vetorial(model, docs)
    retriever_vetorial = base_vetorial.as_retriever(search_kwargs={"k": len(docs)})
    retriever_palavras = retriever_bm25(docs)
    vetorial = buscar(retriever_vetorial, consultas)
    bm25 = buscar(retriever_palavras, consultas)

    # Híbrida
    print("[Busca] Híbrida, com e sem os complementos...")
    hibrida = buscar_hibrida([retriever_vetorial, retriever_palavras], consultas)
    base_vetorial_c = criar_base_vetorial(model, corpus)
    retrievers_c = [base_vetorial_c.as_retriever(search_kwargs={"k": len(corpus)}),
                    retriever_bm25(corpus)]
    hibrida_c = buscar_hibrida(retrievers_c, consultas)

    print("[Busca] MMR...")
    variantes = [
        ("vetorial", vetorial),
        ("BM25", bm25),
        ("híbrida", hibrida),
        ("híbrida, com complementos", hibrida_c),
        ("MMR sobre a vetorial", buscar_mmr(base_vetorial, consultas, vetorial)),
    ]

    if "--reranker" in sys.argv:
        print("[Busca] Reranker...")
        reranker = buscar_reranker(por_nome, consultas, hibrida)
        variantes.append(("reranker sobre a híbrida", reranker))

    resumos = []
    todas_posicoes = []
    for nome, ordens in variantes:
        posicoes = posicoes_do_gabarito(nome, ordens, consultas, por_nome)
        todas_posicoes += posicoes
        resumos.append(resumo(nome, posicoes, consultas))

    print(f"\n{'recall@20':40} {'todas':>6} {'v*':>6} {'categ.':>6} {'bool':>6} "
          f"{'outras':>6} {'compl.':>6}")
    for linha in resumos:
        valores = " ".join(f"{linha[g + '@20']:6.2f}" for g in ["todas"] + GRUPOS)
        print(f"{linha['variante']:40} {valores} {linha['completas@20']:>6}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    salvar_csv("recall.csv", resumos)
    salvar_csv("posicoes.csv", todas_posicoes)
    print("\n[OK] Experimento concluído!")


if __name__ == "__main__":
    main()
