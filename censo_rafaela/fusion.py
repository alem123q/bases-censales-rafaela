"""Fusión de los censos 2001, 2010 y 2022 a nivel de radio censal.

El Censo 2022 no tiene microdatos públicos: solo está disponible como
conteos por radio. Para compararlo con 2001 y 2010 se llevan esos censos
al mismo nivel (una fila por radio, una columna por categoría) y después
se apilan los tres con una columna ANIO (fusión vertical).
"""

from __future__ import annotations

import pandas as pd

from .geografia import agregar_columna_localidad, normalizar_codigo

SEPARADOR = "__"

# Variables comparables entre censos y su nombre común.
EQUIVALENCIAS: dict[int, dict[str, str]] = {
    2001: {
        "P1": "PARENTESCO", "P2": "SEXO", "P3": "EDAD", "P5": "JUBILACION",
        "P9A": "PAIS_NACIMIENTO", "CP63": "CONDICION_ACTIVIDAD",
        "CP7": "CATEGORIA_OCUPACIONAL", "CP9": "APORTE_JUBILATORIO",
        "RAMA2": "RAMA_ACTIVIDAD", "EDADQUI": "EDAD_QUINQUENAL",
        "EDADAGRU": "EDAD_GRUPOS",
    },
    2010: {
        "P01": "PARENTESCO", "P02": "SEXO", "P03": "EDAD",
        "P05": "PAIS_NACIMIENTO", "CONDACT": "CONDICION_ACTIVIDAD",
        "EDADQUI": "EDAD_QUINQUENAL", "EDADAGRU": "EDAD_GRUPOS",
    },
    2022: {
        "P02": "SEXO", "EDAD": "EDAD", "P13": "PAIS_NACIMIENTO",
        "P20": "JUBILACION", "DESCAPOR": "APORTE_JUBILATORIO",
        "CONDACT": "CONDICION_ACTIVIDAD", "P30": "CATEGORIA_OCUPACIONAL",
        "LETRA": "RAMA_ACTIVIDAD", "EDADQUI": "EDAD_QUINQUENAL",
        "EDADGRU": "EDAD_GRUPOS",
    },
}

# El 2001 registra 13 situaciones de actividad; 2010 y 2022 usan 3.
CONDICION_ACTIVIDAD_UNIF: dict[str, str] = {
    "Solo trabaja": "Ocupado",
    "Trabaja/estudia": "Ocupado",
    "Trabaja/es jubilado": "Ocupado",
    "Trabaja/estudia/es jubilado": "Ocupado",
    "Solo busca trabajo": "Desocupado",
    "Busca trabajo/estudia": "Desocupado",
    "Busca trabajo/es jubilado": "Desocupado",
    "Busca trabajo/estudia/es jubilado": "Desocupado",
    "Solo estudia": "Inactivo",
    "Solo es jubilado": "Inactivo",
    "Es jubilado/estudia": "Inactivo",
    "Otra situación": "Inactivo",
    "Ocupado": "Ocupado",
    "Desocupado": "Desocupado",
    "Inactivo": "Inactivo",
    "NOTAPPLICABLE": "NOTAPPLICABLE",
}

SEXO_UNIF: dict[str, str] = {
    "Varón": "Varon", "Varón/Masculino": "Varon",
    "Mujer": "Mujer", "Mujer/Femenino": "Mujer",
}


def agregar_por_radio(df: pd.DataFrame, variables: list[str], col_radio: str = "REDCODE") -> pd.DataFrame:
    """Convierte microdatos en conteos por radio: una columna por VARIABLE__categoría.

    Ojo: al agregar se pierde el cruce entre variables. Se sabe cuántas mujeres
    y cuántos ocupados hay en un radio, pero no cuántas mujeres ocupadas.
    """
    radios = df[col_radio].map(normalizar_codigo)
    tablas = []
    for variable in variables:
        tabla = pd.crosstab(radios, df[variable])
        tabla.columns = [f"{variable}{SEPARADOR}{categoria}" for categoria in tabla.columns]
        tablas.append(tabla)
    resultado = pd.concat(tablas, axis=1).fillna(0).astype(int)
    resultado.index.name = "RADIO"
    return resultado.reset_index()


def renombrar_variables(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Pasa columnas como "P02__Mujer" o "PERSONA_P02__Mujer" a "SEXO__Mujer"."""
    equivalencias = EQUIVALENCIAS[anio]
    nuevos = {}
    for columna in df.columns:
        if SEPARADOR not in columna:
            continue
        variable, categoria = columna.split(SEPARADOR, 1)
        for prefijo in ("PERSONA_", "HOGAR_"):
            variable = variable.removeprefix(prefijo)
        if variable in equivalencias:
            nuevos[columna] = f"{equivalencias[variable]}{SEPARADOR}{categoria}"
    return df.rename(columns=nuevos)


def fusion_vertical(bases_por_anio: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Apila las bases por radio de cada censo con una columna ANIO.

    Una categoría que no existe en un censo queda en 0 para ese año.
    """
    partes = []
    for anio, base in sorted(bases_por_anio.items()):
        base = renombrar_variables(base, anio)
        base = base.assign(RADIO=base["RADIO"].map(normalizar_codigo))
        base.insert(1, "ANIO", anio)
        partes.append(base)

    fusion = pd.concat(partes, ignore_index=True)
    conteos = [c for c in fusion.columns if SEPARADOR in c]
    fusion[conteos] = fusion[conteos].fillna(0).astype(int)
    fusion = agregar_columna_localidad(fusion, col_radio="RADIO")
    return fusion.sort_values(["RADIO", "ANIO"], ignore_index=True)


def unificar_categorias(
    df: pd.DataFrame, variable: str, mapa: dict[str, str], nombre: str | None = None
) -> pd.DataFrame:
    """Suma las columnas de categorías equivalentes en columnas NOMBRE_UNIF__grupo.

    Ejemplo: "Solo trabaja" (2001) y "Ocupado" (2010/2022) terminan en
    CONDACT_UNIF__Ocupado, que sí se puede comparar entre censos.
    """
    nombre = nombre or variable
    df = df.copy()
    grupos: dict[str, list[str]] = {}
    for columna in df.columns:
        if columna.startswith(f"{variable}{SEPARADOR}"):
            categoria = columna.split(SEPARADOR, 1)[1]
            if categoria in mapa:
                grupos.setdefault(mapa[categoria], []).append(columna)
    for grupo, columnas in grupos.items():
        df[f"{nombre}_UNIF{SEPARADOR}{grupo}"] = df[columnas].sum(axis=1)
    return df


def agregar_columnas_unificadas(df: pd.DataFrame) -> pd.DataFrame:
    df = unificar_categorias(df, "SEXO", SEXO_UNIF)
    return unificar_categorias(df, "CONDICION_ACTIVIDAD", CONDICION_ACTIVIDAD_UNIF, nombre="CONDACT")
