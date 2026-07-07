"""
Executa todas as etapas do ETL em ordem.
Uso: python run_all.py
"""
import subprocess
import sys

ETAPAS = [
    "01_geografia.py",
    "02_educacao.py",
    "03_saude.py",
    "04_perfis.py",
    "05_indices.py",
]


def main():
    for etapa in ETAPAS:
        print(f"\n{'#' * 60}")
        print(f"# Executando: {etapa}")
        print(f"{'#' * 60}\n")

        result = subprocess.run([sys.executable, etapa], cwd=sys.path[0])

        if result.returncode != 0:
            print(f"\n[ERRO] Falha na etapa {etapa}. Abortando.")
            sys.exit(1)

    print(f"\n{'#' * 60}")
    print("# ETL COMPLETO!")
    print(f"{'#' * 60}")


if __name__ == "__main__":
    main()
