"""
Retriever do RAG das propriedades: dada uma pergunta, busca as propriedades mais parecidas e
monta o trecho do esquema com elas, agrupadas por nó.

A busca é híbrida: a vetorial, no Chroma, e o BM25, pelas palavras em comum, juntadas pelo RRF. 
O Chroma local não tem índice de palavras, então o BM25 e a fusão são o BM25Retriever e o 
EnsembleRetriever do LangChain, montados com os textos da própria coleção do Chroma.

Uso (teste rápido pelo terminal):
    python retriever.py "Há quantas pessoas alfabetizadas de 15 a 19 anos por setor?" [k]
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
import snowballstemmer
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from config import (VECTORSTORE_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL, TOP_K,
                    PREFIXO_PERGUNTA, PREFIXO_TEXTO)
from dicionario.stopwords_pt import STOPWORDS

# Constante do RRF, a do artigo original e a padrão do LangChain
C_RRF = 60

_model = None
_collection = None
_hibrida = None
_stemmer = snowballstemmer.stemmer("portuguese")


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        _collection = client.get_collection(CHROMA_COLLECTION)
    return _collection


# ---------------------------------------------------------------------------
# PEÇAS DA BUSCA HÍBRIDA
# ---------------------------------------------------------------------------


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def tokenizar(texto):
    """Palavras em minúsculas, sem stopwords, reduzidas ao radical: 'escolas' -> 'escol'."""
    radicais = []
    for palavra in re.findall(r"\w+", texto.lower()):
        if sem_acento(palavra) not in STOPWORDS:
            radicais.append(sem_acento(_stemmer.stemWord(palavra)))
    return radicais


class EmbeddingE5(Embeddings):
    """O LangChain pede o modelo neste formato; aqui entram os prefixos do E5."""

    def __init__(self, model):
        self.model = model

    def embed_documents(self, textos):
        textos = [PREFIXO_TEXTO + t for t in textos]
        return self.model.encode(textos, normalize_embeddings=True).tolist()

    def embed_query(self, texto):
        return self.model.encode(PREFIXO_PERGUNTA + texto, normalize_embeddings=True).tolist()


def _get_hibrida():
    """
    Monta a busca híbrida só na primeira chamada. Os dois retrievers devolvem todas as
    propriedades, para o RRF não usar só as primeiras de cada um; o id_key junta as duas
    listas pela variável, porque 21 textos se repetem.
    """
    global _hibrida
    if _hibrida is None:
        colecao = _get_collection()
        n = colecao.count()
        vetorial = Chroma(collection_name=CHROMA_COLLECTION, persist_directory=VECTORSTORE_DIR,
                          embedding_function=EmbeddingE5(_get_model()))
        dados = colecao.get(include=["documents", "metadatas"])
        documentos = []
        for texto, meta in zip(dados["documents"], dados["metadatas"]):
            documentos.append(Document(texto, metadata=meta))
        palavras = BM25Retriever.from_documents(documentos, preprocess_func=tokenizar, k=n)
        _hibrida = EnsembleRetriever(retrievers=[vetorial.as_retriever(search_kwargs={"k": n}),
                                                 palavras],
                                     weights=[1, 1], c=C_RRF, id_key="variavel")
    return _hibrida


# ---------------------------------------------------------------------------
# RECUPERAÇÃO
# ---------------------------------------------------------------------------


def buscar(pergunta, k=TOP_K):
    """As top-k propriedades da busca híbrida para a pergunta, da mais para a menos relevante."""
    variaveis = []
    for posicao, doc in enumerate(_get_hibrida().invoke(pergunta)[:k], start=1):
        meta = doc.metadata
        variaveis.append({
            "variavel": meta["variavel"],
            "no_label": meta["no_label"],
            "tema": meta["tema"],
            "descricao": meta["descricao"],
            "tipo": meta.get("tipo", ""),
            "valores": meta.get("valores", ""),
            "posicao": posicao,
        })
    return variaveis


def todas_as_propriedades():
    """Todas as propriedades do índice, no mesmo formato de buscar() (sem posição)."""
    variaveis = []
    for meta in _get_collection().get(include=["metadatas"])["metadatas"]:
        variaveis.append({
            "variavel": meta["variavel"],
            "no_label": meta["no_label"],
            "tema": meta["tema"],
            "descricao": meta["descricao"],
            "tipo": meta.get("tipo", ""),
            "valores": meta.get("valores", ""),
        })
    return sorted(variaveis, key=lambda v: (v["no_label"], v["variavel"]))


def descrever(descricao, tipo, valores):
    """Descrição para o prompt, ex.: 'Dependência Administrativa (INTEGER: 1 = Federal, ...)'."""
    if not tipo:
        return descricao
    return f"{descricao} ({tipo}: {valores})" if valores else f"{descricao} ({tipo})"


def agrupar_por_no(variaveis):
    """Agrupa as variáveis recuperadas por rótulo de nó, preservando a ordem."""
    grupos = {}
    for v in variaveis:
        grupos.setdefault(v["no_label"], []).append(v)
    return grupos


def propriedades_indexadas():
    """{rótulo: set(propriedades)} de tudo que está no índice."""
    por_no = {}
    for meta in _get_collection().get(include=["metadatas"])["metadatas"]:
        por_no.setdefault(meta["no_label"], set()).add(meta["variavel"])
    return por_no


def _aresta(label):
    """Aresta que liga o nó ao SetorCensitario (a raiz, que não precisa de aresta)."""
    if label == "SetorCensitario":
        return None
    if label.startswith("Perfil"):
        return f"(:SetorCensitario)-[:TEM_PERFIL]->(:{label})"
    return f"(:{label})-[:LOCALIZADA_EM]->(:SetorCensitario)"  # Escola, EquipamentoSaude


# ---------------------------------------------------------------------------
# MONTAGEM DO ESQUEMA
# ---------------------------------------------------------------------------


def montar_fragmento_schema(pergunta, k=TOP_K):
    """Monta o trecho do esquema com as propriedades relevantes. Retorna (texto, variaveis)."""
    variaveis = buscar(pergunta, k)
    return formatar_fragmento(variaveis), variaveis


def formatar_fragmento(variaveis):
    """Propriedades agrupadas por nó, cada uma com a descrição, o tipo e os valores."""
    linhas = []
    for label, vs in agrupar_por_no(variaveis).items():
        aresta = _aresta(label)
        linhas.append(f"{label}  // ligado por {aresta}" if aresta else f"{label}:")
        for v in vs:
            desc = descrever(v["descricao"], v["tipo"], v["valores"])
            linhas.append(f"    {v['variavel']}  // {desc}")
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# EXECUÇÃO (teste rápido)
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print('Uso: python retriever.py "sua pergunta" [k]')
        sys.exit(1)
    pergunta = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_K

    fragmento, variaveis = montar_fragmento_schema(pergunta, k)
    print(f"Pergunta: {pergunta!r}  (top-{k})\n")
    for v in variaveis:
        print(f"  {v['posicao']:2}.  {v['no_label']}.{v['variavel']}  ->  {v['descricao']}")
    print("\n--- trecho do esquema ---")
    print(fragmento)


if __name__ == "__main__":
    main()
