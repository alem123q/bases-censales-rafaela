"""Rutas del proyecto. Los datos no se versionan: van en la carpeta datos/."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"

# Microdatos del INDEC tal como se descargan (un CSV por nivel geográfico).
MICRODATOS = {
    2001: DATOS / "microdatos" / "2001",
    2010: DATOS / "microdatos" / "2010",
}

# Bases del Censo 2022 agregadas por radio (exportadas de RedatamX / censoargentino).
BASES_2022 = DATOS / "2022"

# Todo lo que generan los scripts.
SALIDA = DATOS / "salida"
