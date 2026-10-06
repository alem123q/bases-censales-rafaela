"""Consultas de ejemplo sobre la base hogar-integrantes 2001.

Pensado para el equipo de investigación: muestra cómo responder preguntas
frecuentes con pandas sin tener que armar cada consulta desde cero.

Uso:
    python herramientas/consultas_ejemplo.py RUTA_A_LA_BASE.csv
"""

import sys

import pandas as pd


def mostrar(titulo: str, df: pd.DataFrame, *columnas: str) -> None:
    """Imprime una frecuencia (1 columna) o un cruce (2 columnas) si las columnas existen."""
    faltantes = [c for c in columnas if c not in df]
    if faltantes:
        print(f"── {titulo}: no disponible (faltan {', '.join(faltantes)}) ──\n")
        return
    print(f"── {titulo} ──")
    if len(columnas) == 1:
        print(df[columnas[0]].value_counts(), "\n")
    else:
        print(pd.crosstab(df[columnas[0]], df[columnas[1]]), "\n")


def main(ruta: str) -> None:
    df = pd.read_csv(ruta, dtype=str, encoding="utf-8-sig")
    print(f"{len(df):,} hogares, {len(df.columns)} columnas\n")

    mostrar("Hogares por localidad", df, "LOCALIDAD")
    mostrar("Condición de actividad de los jefes y jefas de hogar", df, "Jefe_CP63")
    mostrar("Sexo del jefe/a por localidad", df, "LOCALIDAD", "Jefe_P2")
    mostrar("NBI (al menos un indicador) por localidad", df, "LOCALIDAD", "CHNBI — Al menos un indicador NBI")

    if "Conyuge_CP63" in df:
        trabaja = df["Conyuge_CP63"].str.contains("trabaja", case=False, na=False)
        print(f"── Hogares donde el cónyuge trabaja: {trabaja.sum():,} ──\n")

    hijos = [c for c in df.columns if c.startswith("Hijo") and c.endswith("_P2")]
    if hijos:
        print("── Cantidad de hijos/as por hogar ──")
        print(df[hijos].notna().sum(axis=1).value_counts().sort_index())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
