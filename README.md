# Bases censales del Aglomerado Rafaela (2001 · 2010 · 2022)

Construcción, limpieza y fusión de datos de los Censos Nacionales de Población
del INDEC para el Aglomerado Rafaela (Santa Fe, Argentina), con Python y pandas.

Trabajo realizado en una beca de investigación de la **Universidad Nacional de
Rafaela (UNRaf)**, en el proyecto *«Hogares rafaelinos entre la
producción-reproducción: prácticas de provisión en la primera década del siglo XXI»*.

📄 [Caso de estudio en PDF (2 páginas)](docs/caso_de_estudio.pdf)

---

## El problema

El equipo de investigación necesitaba comparar los hogares de Rafaela a lo
largo de veinte años, pero los datos estaban repartidos en tres censos que no
encajan entre sí:

| | 2001 | 2010 | 2022 |
|---|---|---|---|
| Formato | Microdatos de todo el país | Microdatos de todo el país | Solo conteos por radio censal |
| Código de radio | Hay que construirlo | Hay que construirlo | Incluido |
| Nivel extra de la jerarquía | Segmento (SEG) | — | — |
| Condición de actividad | 13 categorías | 3 categorías | 3 categorías |

A eso se sumaban archivos de decenas de millones de filas, límites geográficos
que no coincidían entre fuentes y etiquetas con caracteres corruptos.

## La solución

```
Microdatos INDEC ──► Recorte geográfico ──► Codificación ──► Agregación ──► Fusión vertical
 (2001 y 2010)       Castellanos → radios    códigos →         por radio      + columna ANIO
                     del aglomerado          etiquetas                         + columnas _UNIF
                                                                   ▲
Censo 2022 (conteos por radio) ────────────────────────────────────┘

Microdatos 2001 ──► Base hogar-integrantes (una fila por hogar, columnas por parentesco)
```

1. **Recorte geográfico** ([`extraccion.py`](censo_rafaela/extraccion.py)): baja por la
   jerarquía provincia → departamento → fracción → radio → (segmento) → vivienda →
   hogar → persona, arma el código de radio de 9 dígitos (REDCODE) y se queda con
   las viviendas particulares de los radios del aglomerado.
2. **Lectura por bloques** ([`lectura.py`](censo_rafaela/lectura.py)): el archivo de
   personas de 2001 tiene más de 36 millones de filas. Se lee de a 500.000 y se
   filtra en el camino, así entra en la memoria de una PC común.
3. **Codificación** ([`codificacion.py`](censo_rafaela/codificacion.py)): reemplaza
   códigos numéricos por etiquetas y repara texto mal decodificado.
4. **Fusión** ([`fusion.py`](censo_rafaela/fusion.py)): lleva 2001 y 2010 al nivel
   de radio, renombra las variables con nombres comunes, apila los tres censos
   y crea columnas unificadas (`SEXO_UNIF`, `CONDACT_UNIF`) para comparar
   categorías que cada censo registra distinto.
5. **Base hogar-integrantes** ([`hogares.py`](censo_rafaela/hogares.py)): pasa cada
   persona a columnas del hogar según su parentesco (`Jefe_`, `Conyuge_`,
   `Hijo1_`, `Hijo2_`…), para analizar a los integrantes junto con su vivienda.

## Resultados

| Base | Unidades |
|---|---|
| Hogares del aglomerado 2001 | 25.910 |
| Personas del aglomerado 2001 | 88.674 |
| Hogares del aglomerado 2010 | 31.684 |
| Personas del aglomerado 2010 | 99.052 |
| Personas del aglomerado 2022 | 110.078 (151 radios) |
| Fusión vertical | 327 filas (radio × censo) |
| Base hogar-integrantes 2001 | 25.910 hogares × 845 columnas |

**Validación:** los totales se contrastaron con
[mapa.poblaciones.org](https://mapa.poblaciones.org). En 2010 la diferencia fue
de 1 hogar sobre 31.684; las diferencias en personas (~650) se explican por 5
radios que el mapa incluye y los microdatos no.

## Estructura del repositorio

```
censo_rafaela/       Módulos con la lógica (geografía, lectura, extracción, codificación, fusión, hogares)
scripts/             Pasos del proceso, en orden
herramientas/        Utilidades entregadas al equipo (unir partes, consultas de ejemplo)
tests/               Pruebas con datos sintéticos
docs/                Diccionario de variables, manual de usuario, guías y caso de estudio
config.py            Rutas de entrada y salida
```

## Cómo usarlo

```bash
pip install -r requirements.txt
python -m pytest            # pruebas con datos sintéticos
```

Los datos no están en el repositorio por su tamaño. Para reproducir el proceso:

1. Descargar los microdatos 2001 y 2010 del INDEC (un CSV por nivel geográfico,
   separados por `;`) en `datos/microdatos/2001/` y `datos/microdatos/2010/`.
2. Guardar la base 2022 por radio en `datos/2022/` (exportada de RedatamX o con
   el paquete [`censoargentino`](https://pypi.org/project/censoargentino/)).
3. Correr los pasos:

```bash
python scripts/01_extraer_microdatos.py 2001
python scripts/01_extraer_microdatos.py 2010
python scripts/02_fusion_vertical.py
python scripts/03_hogar_integrantes_2001.py
```

## Decisiones y limitaciones

- **Recorte por radio, no por localidad.** Algunos radios figuran en los
  microdatos como «Zona rural» o «Nueva Lehmann» aunque el mapa los ubica en
  el aglomerado. Se filtró por código de radio para tener control explícito.
- **Al agregar por radio se pierde el cruce entre variables:** se sabe cuántas
  mujeres y cuántos ocupados hay en un radio, pero no cuántas mujeres ocupadas.
  Por eso la base hogar-integrantes 2001 se construyó sobre los microdatos.
- **Rama de actividad no es comparable** entre 2001 (CIIU Rev. 3) y 2022 (CIIU Rev. 4).
- **2010 sin variables de ocupación a nivel de radio:** solo están en el
  cuestionario ampliado, publicado a nivel departamental.
- **Las columnas `_UNIF` son una propuesta** y quedaron sujetas a revisión
  metodológica del equipo de investigación.

## Tecnologías

Python · pandas · pytest · REDATAM / RedatamX · Excel

---

Francisco Alemandi — Estudiante de Ingeniería en Computación, UNRaf
