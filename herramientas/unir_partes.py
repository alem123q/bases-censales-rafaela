"""Une las partes de una base que se dividió para poder compartirla.

La base hogar-integrantes 2001 tiene más de 800 columnas y se entregó al
equipo partida en tres archivos Excel. Este script las vuelve a unir.

Uso:
    python herramientas/unir_partes.py CARPETA NOMBRE_BASE [CANTIDAD_DE_PARTES]

Ejemplo:
    python herramientas/unir_partes.py datos/salida hogares_individuos_aglomerado_rafaela_2001 3
"""

import sys
from pathlib import Path

import pandas as pd


def unir_partes(carpeta: Path, nombre_base: str, n_partes: int = 3) -> pd.DataFrame | None:
    partes = []
    for i in range(1, n_partes + 1):
        archivo = carpeta / f"{nombre_base}_parte{i:02d}.xlsx"
        if not archivo.exists():
            print(f"  ✗ No encontrado: {archivo.name}")
            continue
        parte = pd.read_excel(archivo, dtype=str)
        partes.append(parte)
        print(f"  ✓ {archivo.name}: {len(parte):,} filas")

    if not partes:
        return None
    completo = pd.concat(partes, ignore_index=True)
    print(f"  Total: {len(completo):,} filas, {len(completo.columns)} columnas")
    return completo


def main() -> None:
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    carpeta, nombre = Path(sys.argv[1]), sys.argv[2]
    n_partes = int(sys.argv[3]) if len(sys.argv) == 4 else 3

    completo = unir_partes(carpeta, nombre, n_partes)
    if completo is None:
        sys.exit("No se encontró ninguna parte.")
    salida = carpeta / f"{nombre}_COMPLETO.xlsx"
    completo.to_excel(salida, index=False)
    print(f"Guardado en {salida}")


if __name__ == "__main__":
    main()
