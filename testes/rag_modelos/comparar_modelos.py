"""
Experimento: qual modelo de embedding recupera melhor as propriedades do dicionário?
Cada modelo é testado de duas formas, com o mesmo gabarito e o mesmo recall@k do teste dos
valores (../rag_valores/): só com a busca vetorial exata, sobre o texto da versão B, para isolar
o modelo; e com a busca da Camada A, como
no workflow.

Cada modelo grava os seus resultados em output/<modelo>/ logo depois de rodar, e no fim os de
todos os modelos já rodados são juntados em output/recall_<forma>.csv e output/posicoes_<forma>.csv (forma = vetorial ou hibrida).

Uso (a partir de testes/rag_modelos/, depois da etapa 01 do dicionário):
    python comparar_modelos.py                     # todos os modelos
    python comparar_modelos.py --modelos e5,gemma  # só os que têm esses trechos no nome
    python comparar_modelos.py --limpar-cache      # apaga cada modelo do cache depois de usar
"""
import csv
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag_valores"))

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from sentence_transformers import SentenceTransformer
from comparar_textos import (CORPUS_JSON, EMBEDDING_MODEL, KS, carregar_consultas, grupo,
                             ranking_da_versao)
# o tokenizar (radical e stopwords do Snowball) é o mesmo do workflow
from dicionario.retriever import tokenizar

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CACHE_HF = os.path.expanduser("~/.cache/huggingface/hub")
GRUPOS = ["todas", "v* (Censo)", "categórica", "booleana", "outras dos equipamentos"]

# constante do RRF, a do artigo original e a do workflow
C_RRF = 60

# ---------------------------------------------------------------------------
# MODELOS
# ---------------------------------------------------------------------------

# Instrução que o Qwen3 espera antes da pergunta
INSTRUCAO_QWEN = ("Instruct: Given a question about census, school and health data, "
                  "retrieve the database properties needed to answer it\nQuery:")

# Modelos abertos de até ~600M de parâmetros avaliados no MTEB-BR (ver o README), com os
# prefixos que a página de cada um pede
MODELOS = [
    {"nome": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
     "pergunta": "", "texto": ""},
    {"nome": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
     "pergunta": "", "texto": ""},
    {"nome": "intfloat/multilingual-e5-small", "pergunta": "query: ", "texto": "passage: "},
    {"nome": "intfloat/multilingual-e5-base", "pergunta": "query: ", "texto": "passage: "},
    {"nome": "intfloat/multilingual-e5-large", "pergunta": "query: ", "texto": "passage: "},
    {"nome": "BAAI/bge-m3", "pergunta": "", "texto": ""},
    {"nome": "Qwen/Qwen3-Embedding-0.6B", "pergunta": INSTRUCAO_QWEN, "texto": ""},
    {"nome": "sentence-transformers/all-MiniLM-L6-v2", "pergunta": "", "texto": ""},
    {"nome": "PORTULAN/serafim-100m-portuguese-pt-sentence-encoder-ir",
     "pergunta": "", "texto": ""},
    # aceitar a licença no Hugging Face e fazer login (hf auth login)
    {"nome": "google/embeddinggemma-300m", "pergunta": "task: search result | query: ",
     "texto": "title: none | text: "},
]


def limpar_cache(modelo):
    """Apaga o modelo do cache do Hugging Face, menos o do config.py."""
    if modelo != EMBEDDING_MODEL:
        pasta = "models--" + modelo.replace("/", "--")
        shutil.rmtree(os.path.join(CACHE_HF, pasta), ignore_errors=True)


# ---------------------------------------------------------------------------
# BUSCA HÍBRIDA
# ---------------------------------------------------------------------------


class EmbeddingComPrefixos(Embeddings):
    """
    O modelo no formato do LangChain, como o EmbeddingE5 do retriever.py, mas com os prefixos de pergunta e de texto de cada modelo.
    """

    def __init__(self, model, prefixo_pergunta, prefixo_texto):
        self.model = model
        self.prefixo_pergunta = prefixo_pergunta
        self.prefixo_texto = prefixo_texto

    def embed_documents(self, textos):
        textos = [self.prefixo_texto + t for t in textos]
        return self.model.encode(textos, normalize_embeddings=True).tolist()

    def embed_query(self, texto):
        return self.model.encode(self.prefixo_pergunta + texto, normalize_embeddings=True).tolist()


def ranking_hibrido(model, m, docs, consultas):
    """
    Para cada consulta, as propriedades da busca híbrida sobre o texto que o workflow indexa, com os complementos de descrição.
    """
    documentos = [Document(d["texto"], metadata={"variavel": d["variavel"]}) for d in docs]
    embedding = EmbeddingComPrefixos(model, m["pergunta"], m["texto"])
    vetorial = InMemoryVectorStore.from_documents(documentos, embedding)
    palavras = BM25Retriever.from_documents(documentos, preprocess_func=tokenizar, k=len(docs))
    hibrida = EnsembleRetriever(retrievers=[vetorial.as_retriever(search_kwargs={"k": len(docs)}),
                                            palavras],
                                weights=[1, 1], c=C_RRF, id_key="variavel")
    ranking = []
    for _, pergunta, _ in consultas:
        variaveis = [r.metadata["variavel"] for r in hibrida.invoke(pergunta)]
        ranking.append(variaveis[:max(KS)])
    return ranking


# ---------------------------------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------------------------------


def posicoes_do_gabarito(nome, consultas, ranking, por_nome):
    """Posição de cada propriedade do gabarito no ranking (None = fora do top-20)."""
    posicoes = []
    for (cid, _, gabarito), recuperadas in zip(consultas, ranking):
        for p in sorted(gabarito):
            pos = recuperadas.index(p) + 1 if p in recuperadas else None
            posicoes.append({"modelo": nome, "consulta": cid, "propriedade": p,
                             "grupo": grupo(por_nome[p]), "pos": pos})
    return posicoes


def recall(posicoes, nome_grupo, k):
    """Fração das propriedades do grupo que ficaram até a posição k."""
    if nome_grupo != "todas":
        posicoes = [x for x in posicoes if x["grupo"] == nome_grupo]
    acertos = sum(1 for x in posicoes if x["pos"] and x["pos"] <= k)
    return acertos / len(posicoes)


def perguntas_completas(consultas, ranking):
    """Quantas perguntas têm todas as propriedades do gabarito no top-20."""
    return sum(1 for (_, _, gabarito), recuperadas in zip(consultas, ranking)
               if gabarito <= set(recuperadas))


def resumir(nome, model, consultas, ranking, por_nome):
    """Linha do resumo (recall por grupo e perguntas completas) e posições de um ranking."""
    posicoes = posicoes_do_gabarito(nome, consultas, ranking, por_nome)
    linha = {"modelo": nome, "dimensao": model.get_embedding_dimension(),
             "completas": perguntas_completas(consultas, ranking)}
    for g in GRUPOS:
        for k in KS:
            linha[f"{g}@{k}"] = round(recall(posicoes, g, k), 4)
    return linha, posicoes


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def testar_modelo(m, docs, consultas, por_nome):
    """Roda as duas buscas com um modelo: {forma: (linha do resumo, posições)}."""
    nome = m["nome"].split("/")[-1]
    print(f"\n--- {nome} ---")
    model = SentenceTransformer(m["nome"], device="cpu")

    resultados = {}
    ranking = ranking_da_versao(model, docs, consultas, "B", (m["pergunta"], m["texto"]))
    resultados["vetorial"] = resumir(nome, model, consultas, ranking, por_nome)
    ranking = ranking_hibrido(model, m, docs, consultas)
    resultados["hibrida"] = resumir(nome, model, consultas, ranking, por_nome)

    for forma, (linha, _) in resultados.items():
        print(f"  {forma:8} recall@20 = {linha['todas@20']:.2f}, "
              f"completas = {linha['completas']}/{len(consultas)}")
    return resultados


def salvar_csv(arquivo, linhas, pasta=OUTPUT_DIR):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, arquivo)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"[CSV] {caminho}")


def juntar_e_mostrar(forma):
    """Junta os resultados de todos os modelos já rodados, na ordem de MODELOS, e imprime."""
    resumo = []
    todas_posicoes = []
    for m in MODELOS:
        pasta = os.path.join(OUTPUT_DIR, m["nome"].split("/")[-1])
        if not os.path.exists(os.path.join(pasta, f"recall_{forma}.csv")):
            continue
        with open(os.path.join(pasta, f"recall_{forma}.csv"), encoding="utf-8") as f:
            resumo += list(csv.DictReader(f))
        with open(os.path.join(pasta, f"posicoes_{forma}.csv"), encoding="utf-8") as f:
            todas_posicoes += list(csv.DictReader(f))
    if not resumo:
        return

    print(f"\n[{forma}]")
    print(f"{'recall@20':40} {'todas':>6} {'v*':>6} {'categ.':>6} {'bool':>6} "
          f"{'outras':>6} {'compl.':>6}")
    for linha in resumo:
        valores = " ".join(f"{float(linha[g + '@20']):6.2f}" for g in GRUPOS)
        print(f"{linha['modelo']:40} {valores} {linha['completas']:>6}")

    salvar_csv(f"recall_{forma}.csv", resumo)
    salvar_csv(f"posicoes_{forma}.csv", todas_posicoes)


def main():
    print("=" * 60)
    print("EXPERIMENTO: modelos de embedding")
    print("=" * 60)

    with open(CORPUS_JSON, encoding="utf-8") as f:
        docs = json.load(f)
    por_nome = {d["variavel"]: d for d in docs}
    consultas = carregar_consultas(set(por_nome))
    print(f"\n[Gabarito] {len(consultas)} consultas")

    modelos = MODELOS
    if "--modelos" in sys.argv:
        trechos = sys.argv[sys.argv.index("--modelos") + 1].split(",")
        modelos = [m for m in MODELOS if any(t in m["nome"] for t in trechos)]

    for m in modelos:
        try:
            resultados = testar_modelo(m, docs, consultas, por_nome)
        except OSError as erro:
            # modelo restrito sem login ou sem a licença aceita
            print(f"[Pulando] {m['nome']}: {erro.__class__.__name__}")
            continue
        pasta = os.path.join(OUTPUT_DIR, m["nome"].split("/")[-1])
        for forma, (linha, posicoes) in resultados.items():
            salvar_csv(f"recall_{forma}.csv", [linha], pasta)
            salvar_csv(f"posicoes_{forma}.csv", posicoes, pasta)
        if "--limpar-cache" in sys.argv:
            limpar_cache(m["nome"])

    for forma in ["vetorial", "hibrida"]:
        juntar_e_mostrar(forma)
    print("\n[OK] Experimento concluído!")


if __name__ == "__main__":
    main()
