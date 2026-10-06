"""Pruebas con datos sintéticos (los microdatos reales no se incluyen en el repo)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from censo_rafaela.codificacion import codificar, reparar_texto
from censo_rafaela.extraccion import extraer_aglomerado
from censo_rafaela.fusion import agregar_columnas_unificadas, agregar_por_radio, fusion_vertical
from censo_rafaela.geografia import asignar_localidad, construir_redcode, radios_aglomerado
from censo_rafaela.hogares import construir_hogar_integrantes
from censo_rafaela.lectura import leer_filtrado


# ── Geografía ─────────────────────────────────────────────────────────────

def test_redcode_preserva_ceros_a_la_izquierda():
    redcode = construir_redcode(pd.Series(["21"]), pd.Series(["4"]), pd.Series(["1"]))
    assert redcode.tolist() == ["820210401"]


def test_asignar_localidad():
    assert asignar_localidad("820210124") == "Lehmann"
    assert asignar_localidad("820210311.0") == "Bella Italia"
    assert asignar_localidad(820210401) == "Rafaela"


def test_radios_aglomerado_por_censo():
    r2001, r2010 = radios_aglomerado(2001), radios_aglomerado(2010)
    assert len(r2001) == 67 + 12  # 67 radios de Rafaela + 12 de otras localidades
    assert len(r2010) == 85 + 12
    assert "820210417" in r2001 and "820210418" not in r2001
    assert "820210422" in r2010
    assert "820210138" not in r2001  # radio que solo existe en 2022


# ── Lectura por bloques ───────────────────────────────────────────────────

def test_leer_filtrado_por_bloques(tmp_path):
    ruta = tmp_path / "PERSONA.csv"
    pd.DataFrame({"HOGAR_REF_ID": [str(i % 10) for i in range(1000)], "P2": "1"}).to_csv(
        ruta, sep=";", index=False
    )
    resultado = leer_filtrado(ruta, "HOGAR_REF_ID", {"3", "7"}, tamanio_bloque=37)
    assert len(resultado) == 200
    assert set(resultado["HOGAR_REF_ID"]) == {"3", "7"}


# ── Extracción jerárquica completa ────────────────────────────────────────

def _escribir(carpeta, nombre, filas):
    pd.DataFrame(filas).to_csv(carpeta / nombre, sep=";", index=False)


@pytest.fixture
def microdatos_2001(tmp_path):
    _escribir(tmp_path, "DPTO.csv", [
        {"DPTO_REF_ID": "469", "IDDPTO": "21", "NOMDEPTO": "Castellanos"},
        {"DPTO_REF_ID": "470", "IDDPTO": "28", "NOMDEPTO": "Las Colonias"},
    ])
    _escribir(tmp_path, "FRAC.csv", [
        {"FRAC_REF_ID": "1", "DPTO_REF_ID": "469", "IDFRAC": "4"},
        {"FRAC_REF_ID": "2", "DPTO_REF_ID": "469", "IDFRAC": "1"},
        {"FRAC_REF_ID": "3", "DPTO_REF_ID": "470", "IDFRAC": "4"},
    ])
    _escribir(tmp_path, "RADIO.csv", [
        {"RADIO_REF_ID": "10", "FRAC_REF_ID": "1", "IDRADIO": "1"},   # 820210401 Rafaela
        {"RADIO_REF_ID": "11", "FRAC_REF_ID": "2", "IDRADIO": "24"},  # 820210124 Lehmann
        {"RADIO_REF_ID": "12", "FRAC_REF_ID": "2", "IDRADIO": "99"},  # fuera del aglomerado
        {"RADIO_REF_ID": "13", "FRAC_REF_ID": "3", "IDRADIO": "1"},   # otro departamento
    ])
    _escribir(tmp_path, "SEG.csv", [
        {"SEG_REF_ID": str(100 + r), "RADIO_REF_ID": str(r)} for r in (10, 11, 12, 13)
    ])
    _escribir(tmp_path, "VIVIENDA.csv", [
        {"VIVIENDA_REF_ID": "1", "SEG_REF_ID": "110", "TIPOVIV": "1"},
        {"VIVIENDA_REF_ID": "2", "SEG_REF_ID": "110", "TIPOVIV": "2"},  # colectiva: se excluye
        {"VIVIENDA_REF_ID": "3", "SEG_REF_ID": "111", "TIPOVIV": "1"},
        {"VIVIENDA_REF_ID": "4", "SEG_REF_ID": "112", "TIPOVIV": "1"},
        {"VIVIENDA_REF_ID": "5", "SEG_REF_ID": "113", "TIPOVIV": "1"},
    ])
    _escribir(tmp_path, "HOGAR.csv", [
        {"HOGAR_REF_ID": str(v), "VIVIENDA_REF_ID": str(v), "H1": "2"} for v in range(1, 6)
    ])
    _escribir(tmp_path, "PERSONA.csv", [
        {"PERSONA_REF_ID": str(p), "HOGAR_REF_ID": str(h), "P2": "1"}
        for p, h in enumerate([1, 1, 2, 3, 3, 4, 5], start=1)
    ])
    return tmp_path


def test_extraer_aglomerado_2001(microdatos_2001):
    hogares, personas = extraer_aglomerado(microdatos_2001, 2001)
    assert sorted(hogares["HOGAR_REF_ID"]) == ["1", "3"]
    assert dict(zip(hogares["HOGAR_REF_ID"], hogares["LOCALIDAD"])) == {"1": "Rafaela", "3": "Lehmann"}
    assert dict(zip(hogares["HOGAR_REF_ID"], hogares["REDCODE"])) == {"1": "820210401", "3": "820210124"}
    assert len(personas) == 4
    assert list(personas.columns[:5]) == ["PERSONA_REF_ID", "HOGAR_REF_ID", "REDCODE", "LOCALIDAD", "P2"]


# ── Codificación ──────────────────────────────────────────────────────────

def test_reparar_texto_mal_decodificado():
    for original in ("Categorías", "Situación educacional", "Año"):
        corrupto = original.encode("cp1252").decode("cp932")  # ej. "Categor僘s"
        assert reparar_texto(corrupto) == original
    assert reparar_texto("Educación") == "Educación"
    assert reparar_texto("Sexo") == "Sexo"


def test_codificar():
    df = pd.DataFrame({"P2": ["1", "2", "9"]})
    out = codificar(df, {"P2": "Sexo"}, {"P2": {"1": "Varón", "2": "Mujer"}})
    assert out.columns.tolist() == ["P2 — Sexo"]
    assert out["P2 — Sexo"].tolist() == ["Varón", "Mujer", "9"]


# ── Fusión ────────────────────────────────────────────────────────────────

def test_agregar_por_radio():
    micro = pd.DataFrame({
        "REDCODE": ["820210401", "820210401", "820210402"],
        "P2": ["Varón", "Mujer", "Mujer"],
    })
    out = agregar_por_radio(micro, ["P2"]).set_index("RADIO")
    assert out.loc["820210401", "P2__Varón"] == 1
    assert out.loc["820210402", "P2__Mujer"] == 1
    assert out.loc["820210402", "P2__Varón"] == 0


def test_fusion_vertical_y_columnas_unificadas():
    b2001 = pd.DataFrame({"RADIO": ["820210401"], "P2__Varón": [10], "P2__Mujer": [12],
                          "CP63__Solo trabaja": [5], "CP63__Trabaja/estudia": [2],
                          "CP63__Solo busca trabajo": [1]})
    b2010 = pd.DataFrame({"RADIO": ["820210401"], "P02__Varón": [11], "P02__Mujer": [13],
                          "CONDACT__Ocupado": [8]})
    b2022 = pd.DataFrame({"RADIO": ["820210401", "820210138"],
                          "PERSONA_P02__Varón/Masculino": [9, 4],
                          "PERSONA_P02__Mujer/Femenino": [14, 5],
                          "PERSONA_CONDACT__Ocupado": [9, 3]})

    v = agregar_columnas_unificadas(fusion_vertical({2001: b2001, 2010: b2010, 2022: b2022}))

    assert len(v) == 4
    assert v.columns[:3].tolist() == ["RADIO", "LOCALIDAD", "ANIO"]
    fila = v.set_index(["RADIO", "ANIO"])
    assert fila.loc[("820210401", 2001), "CONDACT_UNIF__Ocupado"] == 7
    assert fila.loc[("820210401", 2001), "CONDACT_UNIF__Desocupado"] == 1
    assert fila.loc[("820210401", 2010), "CONDACT_UNIF__Ocupado"] == 8
    assert fila.loc[("820210401", 2022), "SEXO_UNIF__Mujer"] == 14
    assert fila.loc[("820210138", 2022), "LOCALIDAD"] == "Lehmann"
    assert fila.loc[("820210401", 2010), "SEXO__Varón/Masculino"] == 0


# ── Base hogar-integrantes ────────────────────────────────────────────────

def test_hogar_integrantes():
    hogares = pd.DataFrame({"HOGAR_REF_ID": ["1", "2"], "REDCODE": ["820210401"] * 2})
    personas = pd.DataFrame({
        "HOGAR_REF_ID": ["1", "1", "1", "1", "2"],
        "PAR": ["Jefe(a) de hogar", "Cónyuge o pareja", "Hijo(a)/Hijastro(a)",
                "Hijo(a)/Hijastro(a)", "Jefe(a) de hogar"],
        "SEXO": ["Varón", "Mujer", "Mujer", "Varón", "Mujer"],
    })
    out = construir_hogar_integrantes(
        hogares, personas, variables={"SEXO": "P2"},
        parentescos={"Jefe(a) de hogar": "Jefe", "Cónyuge o pareja": "Conyuge",
                     "Hijo(a)/Hijastro(a)": "Hijo"},
        col_parentesco="PAR",
    ).set_index("HOGAR_REF_ID")

    assert out.columns.tolist() == ["REDCODE", "Jefe_P2", "Conyuge_P2", "Hijo1_P2", "Hijo2_P2"]
    assert out.loc["1", "Hijo2_P2"] == "Varón"
    assert pd.isna(out.loc["2", "Conyuge_P2"])
    assert len(out) == 2
