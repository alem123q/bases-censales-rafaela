"""Codificación de variables: de códigos numéricos a etiquetas legibles."""

from __future__ import annotations

import pandas as pd


def reparar_texto(texto):
    """Repara etiquetas leídas con la codificación equivocada.

    Algunos archivos de etiquetas exportados con Redatam Converter tienen texto
    en Windows-1252 que fue interpretado como japonés (Shift-JIS), y aparecen
    caracteres como "Categor僘s" en lugar de "Categorías". Volver a codificar
    en Shift-JIS y decodificar en Windows-1252 recupera el texto original.
    Si el texto no tiene ese problema, se devuelve sin cambios.
    """
    if not isinstance(texto, str) or texto.isascii():
        return texto
    try:
        return texto.encode("cp932").decode("cp1252")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def codificar(
    df: pd.DataFrame,
    etiquetas_variables: dict[str, str],
    etiquetas_valores: dict[str, dict[str, str]],
) -> pd.DataFrame:
    """Reemplaza códigos por etiquetas y renombra columnas como "VAR — Etiqueta".

    `etiquetas_variables`: {"P2": "Sexo", ...}
    `etiquetas_valores`:   {"P2": {"1": "Varón", "2": "Mujer"}, ...}

    Los códigos sin etiqueta se conservan tal cual, para no perder información.
    """
    df = df.copy()
    for variable, etiquetas in etiquetas_valores.items():
        if variable in df:
            df[variable] = df[variable].map(lambda v: etiquetas.get(v, v))

    nombres = {
        var: f"{var} — {reparar_texto(etiqueta)}"
        for var, etiqueta in etiquetas_variables.items()
        if var in df
    }
    return df.rename(columns=nombres)
