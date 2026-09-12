"""
Retriever da Camada A (schema-linking): dada uma pergunta em linguagem natural,
recupera no índice Chroma as variáveis v* mais prováveis (por descrição) e monta
o fragmento de esquema que alimenta o gerador de Cypher do workflow.

As variáveis vêm agrupadas pelo nó do grafo onde vivem, já anotadas com a aresta
de ligação (SetorCensitario)-[:TEM_PERFIL]->(Perfil*), que o gerador precisa para
chegar às propriedades a partir do setor.

Uso (teste rápido pelo terminal):
    python retriever.py "Há quantas pessoas alfabetizadas de 15 a 19 anos por setor?" [k]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTORSTORE_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL, TOP_K

# Perfis censitários ligam-se ao setor por esta aresta; SetorCensitario é a raiz.
ARESTA_PERFIL = "(:SetorCensitario)-[:TEM_PERFIL]->(:{label})"

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
    """Retorna as top-k variáveis v* mais similares à pergunta (por cosseno)."""
    emb = _get_model().encode([pergunta], normalize_embeddings=True).tolist()
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
            "score": round(1 - dist, 4),  # distância de cosseno -> similaridade
        })
    return variaveis


def agrupar_por_no(variaveis):
    """Agrupa as variáveis recuperadas por rótulo de nó, preservando a ordem."""
    grupos = {}
    for v in variaveis:
        grupos.setdefault(v["no_label"], []).append(v)
    return grupos


# ---------------------------------------------------------------------------
# MONTAGEM DO ESQUEMA (fragmento das variáveis v*)
# ---------------------------------------------------------------------------


def montar_fragmento_schema(pergunta, k=TOP_K):
    """
    Monta o fragmento de esquema com as variáveis v* relevantes, agrupadas por nó
    e anotadas com a aresta de ligação. Retorna (texto, variaveis).

    O backbone estrutural (hierarquia territorial, escolas, equipamentos) é
    acrescentado depois pelo nó de esquema do workflow, a partir do próprio grafo.
    """
    variaveis = buscar(pergunta, k)
    linhas = []
    for label, vs in agrupar_por_no(variaveis).items():
        if label == "SetorCensitario":
            linhas.append(f"{label}:")
        else:
            linhas.append(f"{label}  // ligado por {ARESTA_PERFIL.format(label=label)}")
        for v in vs:
            linhas.append(f"    {v['variavel']}  // {v['descricao']}")
    return "\n".join(linhas), variaveis


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
    print("\n--- fragmento de esquema ---")
    print(fragmento)


if __name__ == "__main__":
    main()
