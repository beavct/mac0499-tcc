"""
Ferramentas de inspeção do banco PostgreSQL de origem (CulturaEduca.cc).

Comandos de leitura para conferir o estado da base durante o desenvolvimento do
ETL — contagem de linhas, checagem do recorte territorial e verificação dos
bairros que cruzam subdistritos/distritos.

Uso:
  python pg_admin.py tabelas               # lista as tabelas do schema e conta as linhas
  python pg_admin.py contar <tabela>       # conta as linhas de uma tabela
  python pg_admin.py ufs                    # verifica se há dados fora de São Paulo (UF 35)
  python pg_admin.py bairros                # bairros que cruzam >1 subdistrito/distrito

Para reduzir a base ao recorte de São Paulo (operação destrutiva), use o script
separado limpar_pg_sp.py.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))
from db import pg_fetch_all

SCHEMA = "culturaeduca.datasets"
UF_ALVO = "35"  # São Paulo
SETORES = f"{SCHEMA}.dtb_setores_censitarios_2022"

# Só bairros de verdade: cd_bairro nulo ou "." é ausência de bairro, não bairro.
FILTRO_BAIRRO = "cd_bairro IS NOT NULL AND cd_bairro <> '.'"


# ---------------------------------------------------------------------------
# TABELAS E CONTAGENS
# ---------------------------------------------------------------------------

def tabelas(arg=None):
    """Lista as tabelas do schema datasets com a contagem de linhas de cada uma."""
    nomes = pg_fetch_all(f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'datasets' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    if not nomes:
        print("Nenhuma tabela no schema datasets.")
        return
    print(f"{'Tabela':<52} | Linhas")
    print("-" * 66)
    for r in nomes:
        t = r["table_name"]
        n = pg_fetch_all(f"SELECT count(*) AS n FROM {SCHEMA}.{t}")[0]["n"]
        print(f"{t:<52} | {n}")


def contar(tabela=None):
    """Conta as linhas de uma tabela específica."""
    if not tabela:
        print("Informe o nome da tabela. Ex: python pg_admin.py contar eq_saude_2025")
        return
    n = pg_fetch_all(f"SELECT count(*) AS n FROM {SCHEMA}.{tabela}")[0]["n"]
    print(f"{tabela}: {n} linhas")


# ---------------------------------------------------------------------------
# RECORTE TERRITORIAL
# ---------------------------------------------------------------------------

def ufs(arg=None):
    """Verifica se restam dados fora de São Paulo (prefixo de código != 35)."""
    fora = pg_fetch_all(f"""
        SELECT left(cd_setor, 2) AS uf, count(*) AS n
        FROM {SETORES}
        WHERE left(cd_setor, 2) <> %s
        GROUP BY left(cd_setor, 2) ORDER BY n DESC
    """, (UF_ALVO,))
    total_sp = pg_fetch_all(f"""
        SELECT count(*) AS n FROM {SETORES} WHERE left(cd_setor, 2) = %s
    """, (UF_ALVO,))[0]["n"]

    print(f"Setores de São Paulo (UF 35): {total_sp}")
    if not fora:
        print("Nenhum setor de outra UF — base restrita a São Paulo.")
    else:
        print("Setores de outras UFs ainda presentes:")
        for r in fora:
            print(f"  UF {r['uf']}: {r['n']}")


# ---------------------------------------------------------------------------
# BAIRROS QUE CRUZAM SUBDISTRITOS/DISTRITOS
# ---------------------------------------------------------------------------

def bairros(arg=None):
    """Conta e lista os bairros que se estendem por mais de um subdistrito/distrito."""
    total = pg_fetch_all(f"""
        SELECT count(DISTINCT cd_bairro) AS n FROM {SETORES} WHERE {FILTRO_BAIRRO}
    """)[0]["n"]
    multi_subdist = pg_fetch_all(f"""
        SELECT count(*) AS n FROM (
            SELECT cd_bairro FROM {SETORES} WHERE {FILTRO_BAIRRO}
            GROUP BY cd_bairro HAVING count(DISTINCT cd_subdist) > 1
        ) t
    """)[0]["n"]
    multi_dist = pg_fetch_all(f"""
        SELECT count(*) AS n FROM (
            SELECT cd_bairro FROM {SETORES} WHERE {FILTRO_BAIRRO}
            GROUP BY cd_bairro HAVING count(DISTINCT cd_dist) > 1
        ) t
    """)[0]["n"]

    print(f"Total de bairros distintos no estado: {total}")
    print(f"Bairros que cruzam >1 subdistrito:    {multi_subdist}")
    print(f"Bairros que cruzam >1 distrito:       {multi_dist}")

    detalhe = pg_fetch_all(f"""
        SELECT nm_bairro, nm_mun,
               string_agg(DISTINCT nm_dist, ' + ' ORDER BY nm_dist) AS distritos
        FROM {SETORES}
        WHERE cd_bairro IN (
            SELECT cd_bairro FROM {SETORES} WHERE {FILTRO_BAIRRO}
            GROUP BY cd_bairro HAVING count(DISTINCT cd_dist) > 1
        )
        GROUP BY nm_bairro, nm_mun
        ORDER BY nm_mun, nm_bairro
    """)
    if detalhe:
        print("\nDetalhe (nome do bairro | município | distritos):")
        for r in detalhe:
            print(f"  {r['nm_mun']}: {r['nm_bairro']}  [{r['distritos']}]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMANDOS = {
    "tabelas": tabelas,
    "contar": contar,
    "ufs": ufs,
    "bairros": bairros,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(1)

    comando = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    COMANDOS[comando](arg)


if __name__ == "__main__":
    main()
