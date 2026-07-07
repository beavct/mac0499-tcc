"""
Limpeza do PostgreSQL para o escopo do TCC: mantém apenas os dados do estado de
São Paulo (UF 35) nas tabelas usadas pelo ETL/consultas e remove as tabelas que
não são utilizadas.

O banco original traz o Brasil inteiro. Este script:
  1. APAGA (DELETE) as linhas de outras UFs nas tabelas MANTIDAS.
  2. REMOVE (DROP) as tabelas NÃO utilizadas pelo projeto.

É uma operação destrutiva e irreversível. Por segurança, roda em modo de
simulação por padrão (apenas mostra o que faria). Para executar de fato:

  python limpar_pg_sp.py --executar

Recomenda-se ter um dump do banco antes de executar.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "compartilhado"))
from db import get_pg_connection

UF_ALVO = "35"  # São Paulo
SCHEMA = "culturaeduca.datasets"

# ---------------------------------------------------------------------------
# TABELAS MANTIDAS — como filtrar as linhas de SP em cada uma
# ---------------------------------------------------------------------------
# Cada entrada: (tabela, cláusula WHERE que identifica linhas a APAGAR, isto é,
# as que NÃO são de SP). Os prefixos de código do IBGE/INEP começam com a UF.

TABELAS_MANTER = [
    # Territoriais / agregados de setor: cd_setor começa com a UF
    ("dtb_setores_censitarios_2022",                         "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_basico",             "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_alfabetizacao",      "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_demografia",         "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_parentesco",         "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_raca_cor",           "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_domicilios_parte1",  "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_domicilios_parte2",  "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_domicilios_parte3",  "left(cd_setor, 2) <> %s"),
    ("agregado_setores_censitarios_2022_entorno_domicilios", "left(cd_setor, 2) <> %s"),

    # Educação: têm sg_uf (sigla da UF)
    ("eq_educacao_basica_2024",    "sg_uf <> 'SP'"),
    ("microdados_ed_basica_2024",  "sg_uf <> 'SP'"),

    # Saúde (equipamentos): cd_mun começa com a UF. Alguns registros têm cd_mun
    # nulo e são todos de fora de SP (co_unidade com prefixo 53 = Distrito
    # Federal), então também entram na remoção.
    ("eq_saude_2025",  "cd_mun IS NULL OR left(cd_mun, 2) <> %s"),
]

# microdados_saude não tem coluna de UF; filtra pelos equipamentos de saúde
# que sobrarem (só os de SP) após a limpeza de eq_saude_2025.
LIMPEZA_MICRODADOS_SAUDE = """
DELETE FROM culturaeduca.datasets.microdados_saude_2025_atendimentos a
WHERE NOT EXISTS (
    SELECT 1 FROM culturaeduca.datasets.eq_saude_2025 s
    WHERE s.co_unidade = a.co_unidade
)
"""

# ---------------------------------------------------------------------------
# TABELAS A REMOVER — não usadas pelo ETL nem pelas consultas
# ---------------------------------------------------------------------------
# Agregados em outros níveis (bairros, distritos, municípios, subdistritos, ufs);
# tabelas territoriais que o ETL não lê (a hierarquia vem toda de dtb_setores);
# e equipamentos/microdados de outros domínios (CRAS, CREAS, IES, bibliotecas,
# centros POP) fora do escopo educação básica + saúde.

TABELAS_REMOVER = [
    # dtb de outros níveis (o ETL só usa dtb_setores_censitarios_2022)
    "dtb_ufs_2022", "dtb_municipios_2022", "dtb_distritos_2022",
    "dtb_subdistritos_2022", "dtb_bairros_2022",
    # agregados de bairros
    "agregado_bairros_2022_basico", "agregado_bairros_2022_alfabetizacao",
    "agregado_bairros_2022_demografia", "agregado_bairros_2022_parentesco",
    "agregado_bairros_2022_raca_cor", "agregado_bairros_2022_domicilios_parte1",
    "agregado_bairros_2022_domicilios_parte2", "agregado_bairros_2022_domicilios_parte3",
    "agregado_bairros_2022_entorno_domicilios",
    # agregados de distritos
    "agregado_distritos_2022_basico", "agregado_distritos_2022_alfabetizacao",
    "agregado_distritos_2022_demografia", "agregado_distritos_2022_parentesco",
    "agregado_distritos_2022_raca_cor", "agregado_distritos_2022_domicilios_parte1",
    "agregado_distritos_2022_domicilios_parte2", "agregado_distritos_2022_domicilios_parte3",
    "agregado_distritos_2022_entorno_domicilios",
    # agregados de municípios
    "agregado_municipios_2022_basico", "agregado_municipios_2022_alfabetizacao",
    "agregado_municipios_2022_demografia", "agregado_municipios_2022_parentesco",
    "agregado_municipios_2022_raca_cor", "agregado_municipios_2022_domicilios_parte1",
    "agregado_municipios_2022_domicilios_parte2", "agregado_municipios_2022_domicilios_parte3",
    "agregado_municipios_2022_entorno_domicilios",
    # agregados de subdistritos
    "agregado_subdistritos_2022_basico", "agregado_subdistritos_2022_alfabetizacao",
    "agregado_subdistritos_2022_demografia", "agregado_subdistritos_2022_parentesco",
    "agregado_subdistritos_2022_raca_cor", "agregado_subdistritos_2022_domicilios_parte1",
    "agregado_subdistritos_2022_domicilios_parte2", "agregado_subdistritos_2022_domicilios_parte3",
    "agregado_subdistritos_2022_entorno_domicilios",
    # agregados de ufs
    "agregado_ufs_2022_basico", "agregado_ufs_2022_alfabetizacao",
    "agregado_ufs_2022_demografia", "agregado_ufs_2022_parentesco",
    "agregado_ufs_2022_raca_cor", "agregado_ufs_2022_domicilios_parte1",
    "agregado_ufs_2022_domicilios_parte2", "agregado_ufs_2022_domicilios_parte3",
    "agregado_ufs_2022_entorno_domicilios",
    # equipamentos e microdados de outros domínios não contemplados pelo TCC (apenas educação básica e saúde)
    "eq_cras_2023", "eq_creas_2023", "eq_ies_2023",
    "eq_bibliotecas_2023", "eq_centros_pop_2023",
    "microdados_cras_2023", "microdados_creas_2023",
    "microdados_ies_2024", "microdados_centros_pop_2023",
]


def contar(cur, tabela, where=None, params=None):
    q = f"SELECT count(*) FROM {SCHEMA}.{tabela}"
    if where:
        q += f" WHERE {where}"
    cur.execute(q, params)
    return cur.fetchone()[0]


def main():
    executar = "--executar" in sys.argv
    modo = "EXECUÇÃO REAL" if executar else "SIMULAÇÃO (dry-run)"

    print("=" * 64)
    print(f" Limpeza do PostgreSQL para São Paulo — {modo}")
    print("=" * 64)
    if not executar:
        print("Nenhuma alteração será feita. Use --executar para aplicar.\n")

    conn = get_pg_connection()
    conn.autocommit = False
    cur = conn.cursor()

    # ---- 1. Remover tabelas não usadas ----
    # Feito primeiro porque DROP é instantâneo e já libera espaço em disco,
    # dando mais folga para os DELETE grandes (com geometrias) da etapa 2.
    print(f"\n[1] Tabelas a REMOVER (não usadas): {len(TABELAS_REMOVER)} tabelas")
    for tabela in TABELAS_REMOVER:
        print(f"  DROP {tabela}")
        if executar:
            cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{tabela} CASCADE")

    # ---- 2. Apagar linhas de outras UFs nas tabelas mantidas ----
    print("\n[2] Tabelas MANTIDAS — remoção de linhas fora de SP:\n")
    for tabela, where_apagar in TABELAS_MANTER:
        params = (UF_ALVO,) if "%s" in where_apagar else None
        try:
            a_apagar = contar(cur, tabela, where_apagar, params)
            total = contar(cur, tabela)
        except Exception as e:
            print(f"  [ERRO] {tabela}: {str(e)[:80]}")
            conn.rollback()
            continue
        restantes = total - a_apagar
        print(f"  {tabela}: apaga {a_apagar} / mantém {restantes}")
        if executar and a_apagar > 0:
            cur.execute(f"DELETE FROM {SCHEMA}.{tabela} WHERE {where_apagar}", params)

    # microdados_saude (depende de eq_saude já filtrada)
    print("\n  microdados_saude_2025_atendimentos: apaga órfãos (sem equipamento em SP)")
    if executar:
        cur.execute(LIMPEZA_MICRODADOS_SAUDE)

    # ---- Finalizar ----
    if executar:
        conn.commit()
        print("\n[OK] Alterações aplicadas e commitadas.")
        print("Dica: rode VACUUM FULL manualmente para recuperar espaço em disco.")
    else:
        conn.rollback()
        print("\n[SIMULAÇÃO] Nada foi alterado. Reveja a lista acima e, se estiver")
        print("de acordo, rode novamente com --executar.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
