"""
Retriever do RAG das propriedades: dada uma pergunta, busca no Chroma as propriedades
mais parecidas e monta o trecho do esquema com elas, agrupadas por nó.

Uso (teste rápido pelo terminal):
    python retriever.py "Há quantas pessoas alfabetizadas de 15 a 19 anos por setor?" [k]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTORSTORE_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL, TOP_K, PREFIXO_PERGUNTA

_model = None
_collection = None


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
# RECUPERAÇÃO
# ---------------------------------------------------------------------------


def buscar(pergunta, k=TOP_K):
    """Retorna as top-k propriedades mais similares à pergunta (por cosseno)."""
    emb = _get_model().encode([PREFIXO_PERGUNTA + pergunta], normalize_embeddings=True).tolist()
    res = _get_collection().query(query_embeddings=emb, n_results=k)

    variaveis = []
    for var, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        variaveis.append({
            "variavel": meta["variavel"],
            "no_label": meta["no_label"],
            "tema": meta["tema"],
            "descricao": meta["descricao"],
            "tipo": meta.get("tipo", ""),
            "valores": meta.get("valores", ""),
            "score": round(1 - dist, 4),  # distância de cosseno -> similaridade
        })
    return variaveis


def todas_as_propriedades():
    """Todas as propriedades do índice, no mesmo formato de buscar() (sem score)."""
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
        print(f"  {v['score']:.3f}  {v['no_label']}.{v['variavel']}  ->  {v['descricao']}")
    print("\n--- trecho do esquema ---")
    print(fragmento)


if __name__ == "__main__":
    main()
