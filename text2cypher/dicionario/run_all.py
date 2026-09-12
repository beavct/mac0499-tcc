"""
Executa as etapas da Camada A (schema-linking) em ordem.
Uso: python run_all.py
"""
import subprocess
import sys

ETAPAS = [
    "01_extrair_dicionario.py",
    "02_indexar_chroma.py",
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
    print("# CAMADA A COMPLETA!")
    print(f"{'#' * 60}")


if __name__ == "__main__":
    main()
