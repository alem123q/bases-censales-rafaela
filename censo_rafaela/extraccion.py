"""Extracción de hogares y personas del Aglomerado Rafaela desde los microdatos.

Los microdatos de los censos 2001 y 2010 vienen como un CSV por nivel de la
jerarquía geográfica, enlazados por identificadores internos (*_REF_ID):

    2001:  PROV → DPTO → FRAC → RADIO → SEG → VIVIENDA → HOGAR → PERSONA
    2010:  PROV → DPTO → FRAC → RADIO       → VIVIENDA → HOGAR → PERSONA

Para quedarse con el aglomerado hay que bajar nivel por nivel: ubicar el
departamento Castellanos, sus fracciones y radios, armar el REDCODE de cada
radio, quedarse con los radios del aglomerado y seguir hasta las personas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .geografia import agregar_columna_localidad, construir_redcode, radios_aglomerado
from .lectura import leer_filtrado


@dataclass(frozen=True)
class EsquemaCenso:
    """Nombres de columnas que cambian de un censo a otro."""

    anio: int
    col_nombre_dpto: str
    col_tipo_vivienda: str
    tiene_segmentos: bool


ESQUEMAS = {
    2001: EsquemaCenso(2001, "NOMDEPTO", "TIPOVIV", tiene_segmentos=True),
    2010: EsquemaCenso(2010, "NOMDPTO", "TIPVV", tiene_segmentos=False),
}

VIVIENDA_PARTICULAR = "1"


def _leer(carpeta: Path, archivo: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(carpeta / archivo, sep=";", dtype=str, **kwargs)


def radios_del_aglomerado(carpeta: Path, esquema: EsquemaCenso) -> pd.DataFrame:
    """Tabla RADIO_REF_ID → REDCODE con los radios del aglomerado."""
    dpto = _leer(carpeta, "DPTO.csv")
    castellanos = dpto[dpto[esquema.col_nombre_dpto].str.contains("Castellanos", na=False)]
    if len(castellanos) != 1:
        raise ValueError(f"Se esperaba un único departamento Castellanos y hay {len(castellanos)}")

    frac = _leer(carpeta, "FRAC.csv").merge(
        castellanos[["DPTO_REF_ID", "IDDPTO"]], on="DPTO_REF_ID"
    )
    radio = _leer(carpeta, "RADIO.csv").merge(
        frac[["FRAC_REF_ID", "IDDPTO", "IDFRAC"]], on="FRAC_REF_ID"
    )
    radio["REDCODE"] = construir_redcode(radio["IDDPTO"], radio["IDFRAC"], radio["IDRADIO"])
    return radio.loc[
        radio["REDCODE"].isin(radios_aglomerado(esquema.anio)), ["RADIO_REF_ID", "REDCODE"]
    ]


def viviendas_del_aglomerado(carpeta: Path, esquema: EsquemaCenso, radios: pd.DataFrame) -> pd.DataFrame:
    """Viviendas particulares del aglomerado con su REDCODE."""
    if esquema.tiene_segmentos:
        seg = _leer(carpeta, "SEG.csv", usecols=["SEG_REF_ID", "RADIO_REF_ID"]).merge(
            radios, on="RADIO_REF_ID"
        )
        enlace, tabla_enlace = "SEG_REF_ID", seg[["SEG_REF_ID", "REDCODE"]]
    else:
        enlace, tabla_enlace = "RADIO_REF_ID", radios

    viviendas = leer_filtrado(
        carpeta / "VIVIENDA.csv",
        columna=enlace,
        valores=tabla_enlace[enlace],
        usecols=["VIVIENDA_REF_ID", esquema.col_tipo_vivienda],
    )
    viviendas = viviendas[viviendas[esquema.col_tipo_vivienda] == VIVIENDA_PARTICULAR]
    return viviendas.merge(tabla_enlace, on=enlace)[["VIVIENDA_REF_ID", "REDCODE"]]


def extraer_aglomerado(carpeta: Path | str, anio: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (hogares, personas) del Aglomerado Rafaela con REDCODE y LOCALIDAD."""
    carpeta = Path(carpeta)
    esquema = ESQUEMAS[anio]

    radios = radios_del_aglomerado(carpeta, esquema)
    viviendas = viviendas_del_aglomerado(carpeta, esquema, radios)

    hogares = leer_filtrado(carpeta / "HOGAR.csv", "VIVIENDA_REF_ID", viviendas["VIVIENDA_REF_ID"])
    hogares = hogares.merge(viviendas, on="VIVIENDA_REF_ID")

    personas = leer_filtrado(carpeta / "PERSONA.csv", "HOGAR_REF_ID", hogares["HOGAR_REF_ID"])
    personas = personas.merge(hogares[["HOGAR_REF_ID", "REDCODE"]], on="HOGAR_REF_ID")

    return _ordenar(hogares, "HOGAR_REF_ID"), _ordenar(personas, "PERSONA_REF_ID")


def _ordenar(df: pd.DataFrame, id_principal: str) -> pd.DataFrame:
    """Pone los identificadores primero y agrega LOCALIDAD después de REDCODE."""
    primeras = [c for c in (id_principal, "HOGAR_REF_ID", "VIVIENDA_REF_ID", "REDCODE") if c in df]
    primeras = list(dict.fromkeys(primeras))
    df = df[primeras + [c for c in df.columns if c not in primeras]]
    return agregar_columna_localidad(df, "REDCODE")
