"""Recorte geográfico del Aglomerado Rafaela (departamento Castellanos, Santa Fe).

El INDEC identifica cada radio censal con un código de 9 dígitos (REDCODE):

    REDCODE = IDPROV (2) + IDDPTO (3) + IDFRAC (2) + IDRADIO (2)
    ej.:       82       +   021      +   04      +   01      = 820210401

Los componentes vienen como números en los microdatos, así que hay que
rellenarlos con ceros a la izquierda antes de concatenarlos: sin eso,
la fracción 4 y el radio 1 darían "8202141" en lugar de "820210401".
"""

from __future__ import annotations

import pandas as pd

CODIGO_SANTA_FE = "82"
CODIGO_CASTELLANOS = "021"

LOCALIDADES = ("Rafaela", "Lehmann", "Bella Italia", "Roca", "Susana")

# Radios de las localidades del aglomerado distintas de Rafaela.
# Todo radio del aglomerado que no figure acá pertenece a Rafaela ciudad.
# Los radios 138, 139, 337, 338 y 341 aparecen en 2022 pero no en los
# microdatos de 2001 y 2010.
LOCALIDAD_POR_RADIO: dict[str, str] = {
    "820210124": "Lehmann", "820210125": "Lehmann", "820210126": "Lehmann",
    "820210132": "Lehmann", "820210134": "Lehmann",
    "820210138": "Lehmann", "820210139": "Lehmann",
    "820210311": "Bella Italia", "820210327": "Bella Italia",
    "820210337": "Bella Italia", "820210338": "Bella Italia",
    "820210309": "Roca", "820210310": "Roca", "820210333": "Roca",
    "820210313": "Susana", "820210314": "Susana", "820210341": "Susana",
}

# Fracciones de Rafaela ciudad y último radio de cada una, por censo.
# La ciudad creció entre censos, por eso cambia la cantidad de radios.
_RADIOS_RAFAELA = {
    2001: {"04": 17, "05": 11, "06": 16, "08": 13, "09": 10},
    2010: {"04": 22, "05": 14, "06": 20, "08": 15, "09": 14},
}

# Radios de las otras localidades presentes en los microdatos de cada censo.
_RADIOS_OTRAS_LOCALIDADES = {
    anio: [r for r in LOCALIDAD_POR_RADIO if r[-3:] not in {"138", "139", "337", "338", "341"}]
    for anio in (2001, 2010)
}


def normalizar_codigo(valor) -> str:
    """Devuelve un código como texto sin decimales ("820210401.0" -> "820210401")."""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return texto


def construir_redcode(
    iddpto: pd.Series,
    idfrac: pd.Series,
    idradio: pd.Series,
    idprov: pd.Series | str = CODIGO_SANTA_FE,
) -> pd.Series:
    """Arma el REDCODE de 9 dígitos preservando los ceros a la izquierda."""
    if isinstance(idprov, str):
        prov = pd.Series(idprov, index=iddpto.index)
    else:
        prov = idprov.astype(str)
    return (
        prov.str.zfill(2)
        + iddpto.astype(str).str.zfill(3)
        + idfrac.astype(str).str.zfill(2)
        + idradio.astype(str).str.zfill(2)
    )


def radios_aglomerado(anio: int) -> set[str]:
    """Conjunto de REDCODE que forman el Aglomerado Rafaela en un censo."""
    if anio not in _RADIOS_RAFAELA:
        raise ValueError(f"No hay recorte de microdatos definido para {anio}")
    prefijo = CODIGO_SANTA_FE + CODIGO_CASTELLANOS
    radios = {
        f"{prefijo}{frac}{radio:02d}"
        for frac, ultimo in _RADIOS_RAFAELA[anio].items()
        for radio in range(1, ultimo + 1)
    }
    return radios | set(_RADIOS_OTRAS_LOCALIDADES[anio])


def asignar_localidad(redcode) -> str:
    """Localidad del aglomerado a la que pertenece un radio."""
    return LOCALIDAD_POR_RADIO.get(normalizar_codigo(redcode), "Rafaela")


def agregar_columna_localidad(df: pd.DataFrame, col_radio: str = "REDCODE") -> pd.DataFrame:
    """Inserta la columna LOCALIDAD justo después de la columna de radio."""
    df = df.drop(columns=["LOCALIDAD"], errors="ignore").copy()
    posicion = df.columns.get_loc(col_radio) + 1
    df.insert(posicion, "LOCALIDAD", df[col_radio].map(asignar_localidad))
    return df
