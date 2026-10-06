"""Base hogar-integrantes: una fila por hogar con los datos de cada miembro.

Los microdatos traen hogares y personas en tablas separadas. Para analizar,
por ejemplo, la ocupación del cónyuge junto con las condiciones de la
vivienda, conviene tener todo en una sola fila. Cada integrante ocupa un
bloque de columnas según su parentesco con el jefe o jefa:

    Jefe_P2, Conyuge_P2, Hijo1_P2, Hijo2_P2, ..., Nieto1_P2, ...
"""

from __future__ import annotations

import pandas as pd

# Categorías de parentesco del Censo 2001 y prefijo de columna de cada una.
PARENTESCOS_2001: dict[str, str] = {
    "Jefe(a) de hogar": "Jefe",
    "Cónyuge o pareja": "Conyuge",
    "Hijo(a)/Hijastro(a)": "Hijo",
    "Yerno/Nuera": "YernoNuera",
    "Nieto(a)": "Nieto",
    "Padre/Madre/Suegro(a)": "PadreMadre",
    "Otros familiares": "OtroFamiliar",
    "Otros no familiares": "OtroNoFamiliar",
    "Servicio doméstico y sus familiares": "ServDom",
}

# Variables de persona que se llevan al hogar (nombre en la base → nombre corto).
VARIABLES_PERSONA_2001: dict[str, str] = {
    "P2 — Sexo": "P2",
    "P5 — Recibe jubilación o pensión": "P5",
    "CP1 — Obra social, plan médico": "CP1",
    "P8A — Dónde vivía hace 5 años": "P8A",
    "CP3 — Asistencia establecimiento escolar": "CP3",
    "CP4 — Situación educacional": "CP4",
    "P20 — Estado civil legal": "P20",
    "P21 — Convive en pareja/matrimonio": "P21",
    "EDADQUI — Edad en grupos quinquenales": "EDADQUI",
    "EDADAGRU — Edad en grandes grupos": "EDADAGRU",
    "RAMA2 — Rama de actividad económica publicada": "RAMA2",
    "P295 — Calificación de las ocupaciones": "P295",
    "CP63 — Condición actividad - desagregada": "CP63",
    "CP7 — Categoría ocupacional": "CP7",
    "CP9 — Aporte jubilatorio": "CP9",
}

COLUMNA_PARENTESCO_2001 = "P1 — Relación de parentesco"


def construir_hogar_integrantes(
    hogares: pd.DataFrame,
    personas: pd.DataFrame,
    variables: dict[str, str] = VARIABLES_PERSONA_2001,
    parentescos: dict[str, str] = PARENTESCOS_2001,
    col_parentesco: str = COLUMNA_PARENTESCO_2001,
    id_hogar: str = "HOGAR_REF_ID",
) -> pd.DataFrame:
    """Pasa las personas a columnas del hogar, numeradas dentro de cada parentesco.

    - Jefe y cónyuge llevan el prefijo solo (Jefe_P2).
    - Si en algún hogar hay más de un integrante de un parentesco, se numeran
      en el orden en que aparecen (Hijo1_P2, Hijo2_P2, ...).
    - Una celda vacía significa que ese hogar no tiene un integrante en esa
      posición, no que falte el dato.
    """
    resultado = hogares.copy()

    for parentesco, prefijo in parentescos.items():
        grupo = personas.loc[personas[col_parentesco] == parentesco, [id_hogar, *variables]].copy()
        if grupo.empty:
            continue
        grupo["_orden"] = grupo.groupby(id_hogar).cumcount() + 1
        if prefijo == "Jefe":
            grupo = grupo[grupo["_orden"] == 1]
        maximo = int(grupo["_orden"].max())

        for n in range(1, maximo + 1):
            sufijo = "" if maximo == 1 else str(n)
            columnas = {var: f"{prefijo}{sufijo}_{corto}" for var, corto in variables.items()}
            bloque = grupo.loc[grupo["_orden"] == n, [id_hogar, *variables]].rename(columns=columnas)
            resultado = resultado.merge(bloque, on=id_hogar, how="left")

    return resultado
