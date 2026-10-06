"""Paso 3 — Base hogar-integrantes del Censo 2001.

Requiere las bases codificadas del paso 1:
  datos/salida/hogares_aglomerado_rafaela_2001_COD.csv
  datos/salida/individuos_aglomerado_rafaela_2001_COD.csv

Genera datos/salida/hogares_individuos_aglomerado_rafaela_2001.csv:
una fila por hogar con las variables de cada integrante según su parentesco.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import SALIDA  # noqa: E402
from censo_rafaela.hogares import (  # noqa: E402
    COLUMNA_PARENTESCO_2001,
    VARIABLES_PERSONA_2001,
    construir_hogar_integrantes,
)


def main() -> None:
    hogares = pd.read_csv(SALIDA / "hogares_aglomerado_rafaela_2001_COD.csv", dtype=str, encoding="utf-8-sig")
    personas = pd.read_csv(
        SALIDA / "individuos_aglomerado_rafaela_2001_COD.csv",
        dtype=str,
        encoding="utf-8-sig",
        usecols=["HOGAR_REF_ID", COLUMNA_PARENTESCO_2001, *VARIABLES_PERSONA_2001],
    )
    print(f"Hogares: {len(hogares):,} — Personas: {len(personas):,}")

    base = construir_hogar_integrantes(hogares, personas)

    # Más de 800 columnas: CSV en vez de Excel, que se cuelga al exportar.
    salida = SALIDA / "hogares_individuos_aglomerado_rafaela_2001.csv"
    base.to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"Base hogar-integrantes: {len(base):,} hogares, {len(base.columns):,} columnas")


if __name__ == "__main__":
    main()
