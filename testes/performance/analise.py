"""
Análise dos resultados do benchmark: lê os CSVs gerados por bench_postgres.py e
bench_neo4j.py e produz os gráficos comparativos para a monografia.

Os gráficos são salvos em output/graficos/ no formato PDF.

Uso:
  python analise.py

Para escolher quais gráficos gerar, edite a lista GRAFICOS_ATIVOS abaixo.
"""
import os
import csv
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # Apenas salvar em arquivo (PDF)
import matplotlib.pyplot as plt

_AQUI = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(_AQUI, "output")
GRAFICOS_DIR = os.path.join(OUTPUT_DIR, "graficos")

CSV_POSTGRES = os.path.join(OUTPUT_DIR, "resultados_postgres.csv")
CSV_NEO4J = os.path.join(OUTPUT_DIR, "resultados_neo4j.csv")

# Cores para os dois bancos em todos os gráficos
COR_PG = "steelblue"   # PostgreSQL
COR_NEO = "tomato"     # Neo4j

# Parâmetros de estilo usados em vários gráficos.
ALTURA_FIG = 5        # altura (polegadas) padrão das figuras
LARGURA_FIG = 8       # largura (polegadas) das figuras de tamanho fixo
ALPHA_PREENCH = 0.6   # opacidade do preenchimento de caixas e barras
ALPHA_GRADE = 0.3     # opacidade da grade de fundo
DESLOC_PAR = 0.2      # deslocamento de cada elemento do par PG/Neo em torno do centro

# Gráficos a gerar.
GRAFICOS_ATIVOS = [
    # por grupo de operação, uma métrica por arquivo, query a query — o conjunto central
    "latencia_por_grupo",    # boxplot de latência por consulta, PG vs Neo4j
    "memoria_por_grupo",     # boxplot de memória de trabalho por consulta, PG vs Neo4j
    # visão agregada: distribuição por tipo de operação
    "boxplot_latencia_por_operacao",  # boxplot de latência por tipo de operação
    "boxplot_memoria_por_operacao",   # boxplot de memória por tipo de operação
]


# ---------------------------------------------------------------------------
# LEITURA E AGREGAÇÃO
# ---------------------------------------------------------------------------

def carregar(caminho):
    """Lê um CSV de resultados e converte os campos numéricos."""
    if not os.path.exists(caminho):
        print(f"[AVISO] arquivo não encontrado: {caminho}")
        return []
    linhas = []
    with open(caminho, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["query"] = int(r["query"])
            r["execucao"] = int(r["execucao"])
            r["warmup"] = r["warmup"] == "True"
            r["latencia_ms"] = float(r["latencia_ms"])
            r["linhas"] = int(float(r["linhas"]))
            r.setdefault("grupo", "sem_grupo")
            r["mem_kb"] = float(r["mem_kb"]) if r.get("mem_kb") else 0.0
            linhas.append(r)
    return linhas

# Ordem e rótulos dos grupos de operação (espelha perguntas/grupos.json).
# Definida para que os gráficos por operação saiam sempre na mesma ordem.
GRUPOS_ORDEM = ["filtro", "agregacao", "anti_join", "multi_hop", "espacial"]
GRUPOS_ROTULO = {
    "filtro": "Filtro",
    "agregacao": "Agregação",
    "anti_join": "Anti-junção",
    "multi_hop": "Multi-salto",
    "espacial": "Espacial",
}


def medianas_por_grupo(linhas, campo="latencia_ms"):
    """Retorna {grupo: [mediana quente de cada query daquele grupo]}, para o campo dado.

    Cada ponto é a mediana de UMA query, para o boxplot por operação refletir a
    variação entre consultas do grupo, e não o ruído de repetição de uma query.
    """
    med_por_query = defaultdict(list)   # (eixo, query) -> valores quentes
    grupo_da_query = {}                 # (eixo, query) -> grupo
    for r in linhas:
        if r["warmup"]:
            continue
        chave = (r["eixo"], r["query"])
        med_por_query[chave].append(r[campo])
        grupo_da_query[chave] = r["grupo"]

    grupos = defaultdict(list)
    for chave, vals in med_por_query.items():
        if vals:
            grupos[grupo_da_query[chave]].append(statistics.median(vals))
    return grupos


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# GRÁFICOS POR GRUPO DE OPERAÇÃO (uma métrica por arquivo, query a query)
# ---------------------------------------------------------------------------
# Para cada grupo (filtro, agregacao, ...), estes gráficos dispõem as consultas
# daquele grupo no eixo x e comparam PostgreSQL e Neo4j em cada uma, gerando um
# arquivo por (métrica, grupo): grupo_latencia_<grupo>.pdf e grupo_memoria_<grupo>.pdf.
# As duas métricas (latência em ms e memória de trabalho em KB) têm a mesma
# unidade nos dois bancos, o que torna a comparação direta.

def _rotulo_query(eixo, query):
    """Rótulo curto de uma query para o eixo x (ex.: 'ed/Q10')."""
    abrev = {"ed_basica": "ed", "saude": "sau", "intersetorial": "int"}.get(eixo, eixo)
    return f"{abrev}/Q{query:02d}"


def _por_query(linhas, grupo, agregador):
    """Aplica `agregador` às execuções quentes de cada query do grupo.

    Retorna {(eixo, query): valor}, com valor = agregador(lista_de_linhas).
    """
    baldes = defaultdict(list)
    for r in linhas:
        if r["warmup"] or r["grupo"] != grupo:
            continue
        baldes[(r["eixo"], r["query"])].append(r)
    return {chave: agregador(rs) for chave, rs in baldes.items()}


def _grupos_presentes(pg, neo):
    """Grupos (na ordem canônica) que aparecem em algum dos dois CSVs."""
    presentes = {r["grupo"] for r in pg} | {r["grupo"] for r in neo}
    return [g for g in GRUPOS_ORDEM if g in presentes]


def _chaves_ordenadas(*dicts):
    """União das chaves (eixo, query) de vários dicts, em ordem estável."""
    chaves = set()
    for d in dicts:
        chaves |= set(d)
    return sorted(chaves)


# Máximo de consultas por figura. Grupos maiores (filtro e agregação têm 21
# consultas) são divididos em várias figuras, para as caixas/pontos ficarem
# legíveis. O nome do arquivo recebe o número da página (ex.: _p1, _p2).
MAX_QUERIES_POR_FIGURA = 12


def _paginar(chaves):
    """Divide a lista de chaves em páginas de até MAX_QUERIES_POR_FIGURA."""
    n = MAX_QUERIES_POR_FIGURA
    return [chaves[i:i + n] for i in range(0, len(chaves), n)]


def _sufixo_pagina(pagina, total_paginas):
    """'' quando há uma só página; '_p1', '_p2'... quando há várias."""
    return "" if total_paginas == 1 else f"_p{pagina}"


# Ver depois se fica melhor em escala logarítmica 
def _boxplot_por_query(ax, chaves, dist_pg, dist_neo, ylabel):
    """Boxplots pareados (PG e Neo4j) por consulta, dado o conjunto de valores
    de cada execução de cada query. Cada caixa resume a variação entre as
    execuções (repetições) daquela query."""
    x = list(range(len(chaves)))
    desloc = DESLOC_PAR
    dados_pg = [dist_pg.get(c, []) for c in chaves]
    dados_neo = [dist_neo.get(c, []) for c in chaves]
    bp_pg = ax.boxplot(dados_pg, positions=[i - desloc for i in x], widths=0.32,
                       patch_artist=True, showmeans=True, showfliers=False)
    bp_neo = ax.boxplot(dados_neo, positions=[i + desloc for i in x], widths=0.32,
                        patch_artist=True, showmeans=True, showfliers=False)
    for caixa in bp_pg["boxes"]:
        caixa.set_facecolor(COR_PG)
        caixa.set_alpha(ALPHA_PREENCH)
    for caixa in bp_neo["boxes"]:
        caixa.set_facecolor(COR_NEO)
        caixa.set_alpha(ALPHA_PREENCH)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels([_rotulo_query(*c) for c in chaves], rotation=45, ha="right")
    ax.set_xlim(-0.6, len(chaves) - 0.4)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=COR_PG, alpha=ALPHA_PREENCH, label="PostgreSQL"),
                       Patch(facecolor=COR_NEO, alpha=ALPHA_PREENCH, label="Neo4j")])
    ax.grid(axis="y", alpha=ALPHA_GRADE)


def _distribuicao_quente(linhas, grupo, campo):
    """{(eixo, query): [valor de cada execução quente]} para um grupo e campo."""
    return _por_query(linhas, grupo, lambda rs: [r[campo] for r in rs if not r["warmup"]])


def _plot_por_grupo(pg, neo, extrair, desenhar, ylabel, titulo, prefixo, ajustar=None):
    """Gera um gráfico por grupo de operação, uma métrica por arquivo.

    Faz o comum a todos os gráficos por grupo (percorrer os grupos, paginar as
    consultas, montar título e salvar); o que varia entra por callbacks:
      extrair(linhas, grupo) -> {(eixo, query): dados_da_consulta}
      desenhar(ax, chaves, dados_pg, dados_neo, ylabel) -> desenha os eixos
      ajustar(ax) -> ajustes opcionais no eixo (ex.: limites do y)
    """
    for g in _grupos_presentes(pg, neo):
        dpg, dneo = extrair(pg, g), extrair(neo, g)
        chaves = _chaves_ordenadas(dpg, dneo)
        if not chaves:
            continue
        paginas = _paginar(chaves)
        for i, pag in enumerate(paginas, start=1):
            fig, ax = plt.subplots(figsize=(max(7, len(pag) * 0.95), ALTURA_FIG))
            desenhar(ax, pag, dpg, dneo, ylabel)
            if ajustar:
                ajustar(ax)
            sufixo_num = f" ({i}/{len(paginas)})" if len(paginas) > 1 else ""
            ax.set_title(f"{titulo} — grupo {GRUPOS_ROTULO[g]}{sufixo_num}")
            _salvar(fig, f"{prefixo}_{g}{_sufixo_pagina(i, len(paginas))}.pdf")


def latencia_por_grupo(pg, neo):
    """Boxplot da latência de cada consulta, por grupo. Cada caixa resume as
    execuções quentes de uma consulta; grupos grandes são paginados."""
    _plot_por_grupo(pg, neo,
                    lambda ls, g: _distribuicao_quente(ls, g, "latencia_ms"),
                    _boxplot_por_query, "Latência (ms)",
                    "Latência por consulta", "grupo_latencia")


def memoria_por_grupo(pg, neo):
    """Boxplot da memória de trabalho de cada consulta, por grupo (PG vs Neo4j)."""
    _plot_por_grupo(pg, neo,
                    lambda ls, g: _distribuicao_quente(ls, g, "mem_kb"),
                    _boxplot_por_query, "Memória de trabalho (KB)",
                    "Memória de trabalho por consulta", "grupo_memoria")


def _espalhar(n, largura=0.12):
    """Deslocamentos horizontais determinísticos para n pontos (strip plot).

    Distribui n pontos simetricamente em torno de 0, dentro de +-largura, sem
    usar aleatoriedade — assim o gráfico é reproduzível execução após execução.
    """
    if n <= 1:
        return [0.0]
    return [largura * (2 * i / (n - 1) - 1) for i in range(n)]


def _boxplot_por_operacao(pg, neo, campo, unidade, titulo, arquivo, rotulo_console):
    """
    Distribuição de uma métrica por tipo de operação, comparando os bancos.

    Para cada grupo de operação (filtro, agregação, anti-junção, multi-salto,
    espacial), desenha duas caixas lado a lado — PostgreSQL e Neo4j — e sobrepõe,
    sobre cada caixa, um ponto por consulta do grupo (a sua mediana quente).
    Assim a caixa dá o resumo (mediana e quartis) e os pontos mostram como cada
    consulta individual se distribui dentro do grupo.

    Também imprime no console uma tabela de média ± desvio padrão por grupo.
    """
    med_pg = medianas_por_grupo(pg, campo)
    med_neo = medianas_por_grupo(neo, campo)

    grupos = [g for g in GRUPOS_ORDEM if g in med_pg or g in med_neo]
    if not grupos:
        print(f"  [{arquivo}] nenhum grupo encontrado — pulando")
        return

    # tabela de apoio no console (média ± desvio por grupo e banco)
    print(f"\n  {rotulo_console} por operação ({unidade}) — mediana por consulta:")
    print(f"    {'operação':<12} {'n':>3}  {'PostgreSQL (méd±dp)':>22}  {'Neo4j (méd±dp)':>22}")
    for g in grupos:
        vpg, vneo = med_pg.get(g, []), med_neo.get(g, [])

        def fmt(v):
            if not v:
                return "—"
            media = statistics.mean(v)
            dp = statistics.stdev(v) if len(v) > 1 else 0.0
            return f"{media:8.1f} ± {dp:7.1f}"

        n = max(len(vpg), len(vneo))
        print(f"    {GRUPOS_ROTULO[g]:<12} {n:>3}  {fmt(vpg):>22}  {fmt(vneo):>22}")

    # posições: cada grupo ocupa um "slot"; dentro dele, PG à esquerda e Neo à direita
    dados_pg = [med_pg.get(g, []) for g in grupos]
    dados_neo = [med_neo.get(g, []) for g in grupos]
    x = range(len(grupos))
    desloc = DESLOC_PAR

    fig, ax = plt.subplots(figsize=(max(LARGURA_FIG, len(grupos) * 1.7), ALTURA_FIG + 0.5))
    # caixas sem os pontos extremos do boxplot (showfliers=False): os outliers
    # já aparecem como pontos individuais sobrepostos, evitando duplicatas
    bp_pg = ax.boxplot(dados_pg, positions=[i - desloc for i in x], widths=0.32,
                       patch_artist=True, showmeans=True, showfliers=False)
    bp_neo = ax.boxplot(dados_neo, positions=[i + desloc for i in x], widths=0.32,
                        patch_artist=True, showmeans=True, showfliers=False)
    for caixa in bp_pg["boxes"]:
        caixa.set_facecolor(COR_PG)
        caixa.set_alpha(ALPHA_PREENCH)
    for caixa in bp_neo["boxes"]:
        caixa.set_facecolor(COR_NEO)
        caixa.set_alpha(ALPHA_PREENCH)

    # overlay: um ponto por consulta, espalhado horizontalmente sobre cada caixa
    for i, g in enumerate(grupos):
        for centro, valores, cor in ((i - desloc, dados_pg[i], COR_PG),
                                     (i + desloc, dados_neo[i], COR_NEO)):
            if not valores:
                continue
            xs = [centro + dx for dx in _espalhar(len(valores))]
            ax.scatter(xs, valores, s=26, color=cor, edgecolor="white",
                       linewidth=0.6, zorder=3)

    ax.set_yscale("log")   # grupos têm ordens de grandeza distintas; log torna todos legíveis
    ax.set_ylabel(f"{rotulo_console} mediana por consulta ({unidade}, escala log)")
    ax.set_title(titulo)
    ax.set_xticks(list(x))
    ax.set_xticklabels([GRUPOS_ROTULO[g] for g in grupos])
    # legenda manual (as duas cores)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=COR_PG, alpha=ALPHA_PREENCH, label="PostgreSQL"),
                       Patch(facecolor=COR_NEO, alpha=ALPHA_PREENCH, label="Neo4j")])
    ax.grid(axis="y", alpha=ALPHA_GRADE)
    _salvar(fig, arquivo)


def boxplot_latencia_por_operacao(pg, neo):
    """Boxplot da latência por tipo de operação, PG vs Neo4j."""
    _boxplot_por_operacao(pg, neo, "latencia_ms", "ms",
                          "Distribuição das latências por tipo de operação",
                          "boxplot_latencia_por_operacao.pdf", "Latência")


def boxplot_memoria_por_operacao(pg, neo):
    """Boxplot da memória de trabalho por tipo de operação, PG vs Neo4j."""
    _boxplot_por_operacao(pg, neo, "mem_kb", "KB",
                          "Distribuição da memória de trabalho por tipo de operação",
                          "boxplot_memoria_por_operacao.pdf", "Memória")


# ---------------------------------------------------------------------------
# Latência vs. complexidade (esqueleto / a definir)
# ---------------------------------------------------------------------------
# IDEIA: relacionar a latência de cada query com uma medida de complexidade,
# para investigar a hipótese de que o grafo se destaca quanto mais camadas 
# a consulta cruza.
#
# Falta definir como medir complexidade. Duas opções levantadas:
#   (a) automática: contar JOINs no SQL e setas (-->/<--) no Cypher;
#   (b) manual: rotular cada query com um nível (simples/média/complexa) num
#       arquivo de apoio.
#
# def latencia_vs_complexidade(pg, neo):
#     # 1. obter complexidade por query (automática ou de um arquivo de rótulos)
#     # 2. plt.scatter(complexidade, latencia) para cada banco
#     # 3. opcional: linha de tendência
#     ...


# ---------------------------------------------------------------------------

def _salvar(fig, nome):
    os.makedirs(GRAFICOS_DIR, exist_ok=True)
    caminho = os.path.join(GRAFICOS_DIR, nome)
    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    print(f"  [gráfico] {caminho}")


FUNCOES = {
    "latencia_por_grupo": latencia_por_grupo,
    "memoria_por_grupo": memoria_por_grupo,
    "boxplot_latencia_por_operacao": boxplot_latencia_por_operacao,
    "boxplot_memoria_por_operacao": boxplot_memoria_por_operacao,
}


def main():
    pg = carregar(CSV_POSTGRES)
    neo = carregar(CSV_NEO4J)
    if not pg and not neo:
        print("Nenhum resultado encontrado. Rode bench_postgres.py e bench_neo4j.py antes.")
        return

    print("Gerando gráficos...")
    for nome in GRAFICOS_ATIVOS:
        funcao = FUNCOES.get(nome)
        if funcao:
            funcao(pg, neo)
        else:
            print(f"  [ignorado] {nome} (sem função associada)")

    print(f"\nGráficos salvos em: {GRAFICOS_DIR}")


if __name__ == "__main__":
    main()
