"""Paso 2 — Agrega 2001 y 2010 por radio y los fusiona con el 2022.

Requiere:
  - datos/salida/individuos_aglomerado_rafaela_{2001,2010}_COD.csv
    (salida del paso 1, ya codificada con etiquetas legibles)
  - datos/2022/individuos_aglomerado_rafaela_2022.csv
    (una fila por radio, columnas VARIABLE__categoría)

Genera datos/salida/individuos_aglomerado_rafaela_vertical.csv:
una fila por radio y por censo, con columna ANIO y columnas *_UNIF
para comparar categorías entre censos.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import BASES_2022, SALIDA  # noqa: E402
from censo_rafaela.fusion import (  # noqa: E402
    EQUIVALENCIAS,
    agregar_columnas_unificadas,
    agregar_por_radio,
    fusion_vertical,
)


def variables_presentes(df: pd.DataFrame, anio: int) -> list[str]:
    """Columnas de la base (formato "VAR — Etiqueta" o "VAR") que tienen equivalencia."""
    return [c for c in df.columns if c.split(" — ")[0] in EQUIVALENCIAS[anio]]


def a_codigo_corto(df: pd.DataFrame) -> pd.DataFrame:
    """"P2 — Sexo__Mujer" -> "P2__Mujer", para poder aplicar las equivalencias."""
    return df.rename(columns=lambda c: c.split(" — ")[0] + ("__" + c.split("__", 1)[1] if "__" in c else ""))


def main() -> None:
    bases = {}
    for anio in (2001, 2010):
        micro = pd.read_csv(SALIDA / f"individuos_aglomerado_rafaela_{anio}_COD.csv", dtype=str, encoding="utf-8-sig")
        por_radio = agregar_por_radio(micro, variables_presentes(micro, anio))
        bases[anio] = a_codigo_corto(por_radio)
        print(f"{anio}: {len(por_radio)} radios")

    bases[2022] = pd.read_csv(BASES_2022 / "individuos_aglomerado_rafaela_2022.csv", dtype={"RADIO": str}, encoding="utf-8-sig")
    print(f"2022: {len(bases[2022])} radios")

    vertical = agregar_columnas_unificadas(fusion_vertical(bases))
    salida = SALIDA / "individuos_aglomerado_rafaela_vertical.csv"
    vertical.to_csv(salida, index=False, encoding="utf-8-sig")

    print(f"\nFusión vertical: {len(vertical)} filas, {len(vertical.columns)} columnas")
    print(vertical.groupby("ANIO")[[c for c in vertical if c.startswith("CONDACT_UNIF__")]].sum())


if __name__ == "__main__":
    main()
