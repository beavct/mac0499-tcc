"""
Experimento: qual modelo de embedding recupera melhor as propriedades do dicionário?
Usa o texto da versão B (o que o workflow usa), o mesmo gabarito, a mesma busca exata e
o mesmo recall@k do teste de categorias (../rag_categorias/).
Os resultados vão para output/recall.csv e output/posicoes.csv.

Uso (a partir de testes/rag_modelos/, depois da etapa 01 do dicionário):
    python comparar_modelos.py                 # todos os modelos
    python comparar_modelos.py --limpar-cache  # apaga cada modelo do cache depois de usar
"""
import csv
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag_categorias"))

from sentence_transformers import SentenceTransformer
from experimento import (CORPUS_JSON, EMBEDDING_MODEL, KS, carregar_consultas, grupo,
                         ranking_da_versao)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CACHE_HF = os.path.expanduser("~/.cache/huggingface/hub")
GRUPOS = ["todas", "v* (Censo)", "código (tp_*)", "booleana", "outras (qt_* etc.)"]

# ---------------------------------------------------------------------------
# MODELOS
# ---------------------------------------------------------------------------

# Prefixos que cada modelo espera na pergunta e no texto, segundo a página dele no Hugging Face
INSTRUCAO_QWEN = ("Instruct: Given a question about census, school and health data, "
                  "retrieve the database properties needed to answer it\nQuery:")

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
]


def limpar_cache(modelo):
    """Apaga o modelo do cache do Hugging Face, menos o do config.py."""
    if modelo != EMBEDDING_MODEL:
        pasta = "models--" + modelo.replace("/", "--")
        shutil.rmtree(os.path.join(CACHE_HF, pasta), ignore_errors=True)


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


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------


def testar_modelo(m, docs, consultas, por_nome):
    """Roda a busca com um modelo e devolve a linha do resumo e as posições."""
    nome = m["nome"].split("/")[-1]
    print(f"\n[modelo] {nome}")
    model = SentenceTransformer(m["nome"])

    inicio = time.time()
    ranking = ranking_da_versao(model, docs, consultas, "B", (m["pergunta"], m["texto"]))
    segundos = round(time.time() - inicio, 1)

    posicoes = posicoes_do_gabarito(nome, consultas, ranking, por_nome)
    linha = {"modelo": nome, "dimensao": model.get_embedding_dimension(),
             "segundos": segundos, "completas": perguntas_completas(consultas, ranking)}
    for g in GRUPOS:
        for k in KS:
            linha[f"{g}@{k}"] = round(recall(posicoes, g, k), 4)

    print(f"  recall@20 = {linha['todas@20']:.2f}, "
          f"completas = {linha['completas']}/{len(consultas)}")
    return linha, posicoes


def salvar_csv(arquivo, linhas):
    caminho = os.path.join(OUTPUT_DIR, arquivo)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"[CSV] {caminho}")


def main():
    print("=" * 60)
    print("EXPERIMENTO: modelos de embedding")
    print("=" * 60)

    docs = json.load(open(CORPUS_JSON, encoding="utf-8"))
    por_nome = {d["variavel"]: d for d in docs}
    consultas = carregar_consultas(set(por_nome))
    print(f"[gabarito] {len(consultas)} consultas")

    resumo = []
    todas_posicoes = []
    for m in MODELOS:
        linha, posicoes = testar_modelo(m, docs, consultas, por_nome)
        resumo.append(linha)
        todas_posicoes += posicoes
        if "--limpar-cache" in sys.argv:
            limpar_cache(m["nome"])

    print(f"\n{'recall@20':40} {'todas':>6} {'v*':>6} {'código':>6} {'bool':>6} "
          f"{'outras':>6} {'compl.':>6}")
    for linha in resumo:
        valores = " ".join(f"{linha[g + '@20']:6.2f}" for g in GRUPOS)
        print(f"{linha['modelo']:40} {valores} {linha['completas']:>6}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    salvar_csv("recall.csv", resumo)
    salvar_csv("posicoes.csv", todas_posicoes)


if __name__ == "__main__":
    main()
