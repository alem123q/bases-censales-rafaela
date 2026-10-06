"""Paso 1 — Extrae hogares y personas del Aglomerado Rafaela (2001 y 2010).

Uso:
    python scripts/01_extraer_microdatos.py 2001
    python scripts/01_extraer_microdatos.py 2010

Genera en datos/salida/ cuatro bases por censo: hogares e individuos del
aglomerado completo y de Rafaela ciudad.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import MICRODATOS, SALIDA  # noqa: E402
from censo_rafaela.extraccion import extraer_aglomerado  # noqa: E402


def main(anio: int) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    print(f"Extrayendo Censo {anio} desde {MICRODATOS[anio]} ...")
    hogares, personas = extraer_aglomerado(MICRODATOS[anio], anio)

    bases = {
        f"hogares_aglomerado_rafaela_{anio}": hogares,
        f"individuos_aglomerado_rafaela_{anio}": personas,
        f"hogares_rafaela_ciudad_{anio}": hogares[hogares["LOCALIDAD"] == "Rafaela"],
        f"individuos_rafaela_ciudad_{anio}": personas[personas["LOCALIDAD"] == "Rafaela"],
    }
    for nombre, df in bases.items():
        # utf-8-sig: Excel abre bien las tildes y la ñ con doble clic.
        df.to_csv(SALIDA / f"{nombre}.csv", index=False, encoding="utf-8-sig")
        print(f"  {nombre}: {len(df):,} filas")

    print("\nHogares por localidad:")
    print(hogares["LOCALIDAD"].value_counts().to_string())


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"2001", "2010"}:
        sys.exit("Uso: python scripts/01_extraer_microdatos.py 2001|2010")
    main(int(sys.argv[1]))
