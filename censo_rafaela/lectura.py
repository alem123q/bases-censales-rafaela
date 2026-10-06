"""Lectura de archivos censales que no entran en memoria."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

TAMANIO_BLOQUE = 500_000


def leer_filtrado(
    ruta: Path | str,
    columna: str,
    valores: Iterable[str],
    usecols: list[str] | None = None,
    sep: str = ";",
    tamanio_bloque: int = TAMANIO_BLOQUE,
) -> pd.DataFrame:
    """Lee un CSV por bloques y conserva solo las filas cuyo `columna` está en `valores`.

    El PERSONA.csv del Censo 2001 tiene más de 36 millones de filas: leerlo
    entero agota la memoria de una PC común. Leyendo de a 500.000 filas y
    quedándose solo con las del recorte, el consumo se mantiene acotado.
    Todo se lee como texto para no perder ceros a la izquierda en los códigos.
    """
    buscados = set(valores)
    if usecols is not None and columna not in usecols:
        usecols = [columna, *usecols]

    partes = [
        bloque[bloque[columna].isin(buscados)]
        for bloque in pd.read_csv(
            ruta, sep=sep, dtype=str, usecols=usecols, chunksize=tamanio_bloque
        )
    ]
    if not partes:
        return pd.DataFrame(columns=usecols or [columna])
    return pd.concat(partes, ignore_index=True)
