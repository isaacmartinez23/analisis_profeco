"""Evidencia reproducible para la selección de artículos de la canasta (D-022).

Evalúa, sobre las observaciones comparables y no atípicas de las cadenas de referencia:

1. La cobertura de definiciones alternativas de artículo (% de celdas cadena × municipio × semana con al
   menos una observación en la ventana de 14 días) y su mediana de precio unitario por cadena, para
   detectar definiciones que mezclan calidades.
2. La completitud de composiciones de canasta alternativas y cuántos municipio-semanas permiten comparar al
   menos dos cadenas.

El universo de celdas no depende de la versión vigente: toda celda donde la cadena tiene alguna observación
de un producto candidato. Genera ``reports/seleccion_canasta.md``.

Uso::

    python -m src.analysis.seleccion_canasta
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect

LIMPIEZA = ["JABON_LAVANDERIA", "PAPEL_HIGIENICO", "DETERGENTE_POLVO"]

# Definiciones alternativas evaluadas además de las de los seeds (v0 y v1).
ALTERNATIVAS = [
    ("RES_MOLIDA_CUALQUIERA", "CARNE RES", "kg", None, "MOLIDA", None),
    ("RES_BISTEC", "CARNE RES", "kg", None, "BISTEC", None),
    ("RES_PARA_ASAR", "CARNE RES", "kg", None, "PARA ASAR", None),
    ("RES_FALDA", "CARNE RES", "kg", None, "FALDA", None),
    ("POLLO_PIERNA_O_MUSLO", "CARNE POLLO", "kg", None, "PIERNA|MUSLO", None),
    ("POLLO_PECHUGA", "CARNE POLLO", "kg", None, "PECHUGA", None),
    ("LIMON_CON_SEMILLA", "LIMON", "kg", None, "CON SEMILLA", None),
]


def _escenarios(v0: list[str], v1: list[str]) -> dict[str, list[str]]:
    def cambiar(lista, viejo, nuevo):
        return [nuevo if a == viejo else a for a in lista]

    pollo = cambiar(v0, "POLLO_PIERNA", "POLLO_ENTERO")
    sin_harina = [a for a in pollo if a != "HARINA_MAIZ"]
    con_milanesa = cambiar(sin_harina, "RES_MOLIDA", "RES_MILANESA")
    return {
        "v0: 20 artículos": v0,
        "v0 con pollo entero (20)": pollo,
        "... sin harina de maíz (19)": sin_harina,
        "... con milanesa en lugar de molida especial (19)": con_milanesa,
        "... sin limpieza, con molida especial (16)": [a for a in sin_harina if a not in LIMPIEZA],
        "v1: sin limpieza, con milanesa (16)": v1,
        "v1 sin res (15)": [a for a in v1 if a != "RES_MILANESA"],
    }


def run(db_path: Path = config.DUCKDB_PATH) -> dict[str, pd.DataFrame]:
    with connect(db_path, read_only=True) as con:
        seeds = con.execute(
            """SELECT version, articulo_id, producto_key, unidad_base, nullif(subtipo_conteo, '') subtipo_conteo,
                      incluye_regex, nullif(excluye_regex, '') excluye_regex
               FROM seeds.canasta_articulos"""
        ).df()
        definiciones = pd.concat(
            [
                seeds.drop(columns="version").drop_duplicates("articulo_id"),
                pd.DataFrame(ALTERNATIVAS, columns=seeds.columns[1:]),
            ],
            ignore_index=True,
        )
        con.register("definiciones", definiciones)
        con.execute(
            """
            CREATE TEMP TABLE obs AS
            SELECT e.cadena_key, e.geografia_id, d.semana_inicio, p.producto_key, p.presentacion_key,
                   p.unidad_base, p.subtipo_conteo, f.precio_unitario
            FROM core.fct_precio_observado f
            JOIN core.dim_producto p USING (producto_id)
            JOIN core.dim_establecimiento e USING (establecimiento_id)
            JOIN core.dim_fecha d USING (fecha)
            WHERE e.es_cadena_referencia AND p.es_comparable AND NOT f.es_atipico
              AND p.producto_key IN (SELECT DISTINCT producto_key FROM definiciones)"""
        )
        con.execute(
            """CREATE TEMP TABLE obs_v AS
               SELECT *, semana_inicio AS semana_v FROM obs UNION ALL SELECT *, semana_inicio + 7 FROM obs"""
        )
        con.execute(
            """CREATE TEMP TABLE celdas AS
               SELECT DISTINCT cadena_key, geografia_id, semana_v FROM obs_v
               WHERE semana_v >= (SELECT min(semana_inicio) + 7 FROM obs)
                 AND semana_v <= (SELECT max(semana_inicio) FROM obs)"""
        )
        con.execute(
            """
            CREATE TEMP TABLE presencia AS
            SELECT d.articulo_id, o.cadena_key, o.geografia_id, o.semana_v, o.precio_unitario
            FROM obs_v o
            JOIN definiciones d ON o.producto_key = d.producto_key AND o.unidad_base = d.unidad_base
                AND (d.subtipo_conteo IS NULL OR d.subtipo_conteo = o.subtipo_conteo)
                AND regexp_matches(o.presentacion_key, d.incluye_regex)
                AND (d.excluye_regex IS NULL OR NOT regexp_matches(o.presentacion_key, d.excluye_regex))
            JOIN celdas c USING (cadena_key, geografia_id, semana_v)"""
        )
        cobertura = con.execute(
            """
            WITH total AS (SELECT cadena_key, count(*) n FROM celdas GROUP BY 1),
            por_def AS (
                SELECT articulo_id, cadena_key, count(DISTINCT (geografia_id, semana_v)) celdas,
                       median(precio_unitario) mediana
                FROM presencia GROUP BY 1, 2)
            SELECT articulo_id, cadena_key, round(100.0 * celdas / n, 1) AS cobertura_pct, round(mediana, 2) AS mediana
            FROM por_def JOIN total USING (cadena_key)"""
        ).df()

        v0 = seeds.loc[seeds["version"] == "v0", "articulo_id"].tolist()
        v1 = seeds.loc[seeds["version"] == "v1", "articulo_id"].tolist()
        filas = []
        for nombre, articulos in _escenarios(v0, v1).items():
            con.execute("CREATE OR REPLACE TEMP TABLE sel (articulo_id VARCHAR)")
            con.executemany("INSERT INTO sel VALUES (?)", [(a,) for a in articulos])
            r = con.execute(
                f"""
                WITH k AS (
                    SELECT c.cadena_key, c.geografia_id, c.semana_v,
                           count(DISTINCT p.articulo_id) = {len(articulos)} AS completa
                    FROM celdas c
                    LEFT JOIN presencia p ON p.cadena_key = c.cadena_key AND p.geografia_id = c.geografia_id
                        AND p.semana_v = c.semana_v AND p.articulo_id IN (SELECT articulo_id FROM sel)
                    GROUP BY ALL),
                mw AS (SELECT geografia_id, semana_v, count(*) cadenas, sum(completa::INT) completas FROM k GROUP BY ALL)
                SELECT
                    {len(articulos)} AS articulos,
                    round(100 * avg(completa::INT), 1) AS celdas_completas_pct,
                    round(100 * avg(completa::INT) FILTER (WHERE cadena_key = 'WAL-MART'), 1) AS wal_mart,
                    round(100 * avg(completa::INT) FILTER (WHERE cadena_key = 'BODEGA AURRERA'), 1) AS bodega_aurrera,
                    round(100 * avg(completa::INT) FILTER (WHERE cadena_key = 'HIPERMERCADO SORIANA'), 1) AS soriana,
                    round(100 * avg(completa::INT) FILTER (WHERE cadena_key = 'CHEDRAUI'), 1) AS chedraui,
                    (SELECT round(100 * avg((completas >= 2)::INT), 1) FROM mw WHERE cadenas >= 2)
                        AS municipio_semanas_comparables_pct,
                    (SELECT count(DISTINCT geografia_id) FROM mw WHERE completas >= 2) AS municipios_con_comparacion
                FROM k"""
            ).df()
            r.insert(0, "composicion", nombre)
            filas.append(r)
        escenarios = pd.concat(filas, ignore_index=True)

    tabla_cob = cobertura.pivot(index="articulo_id", columns="cadena_key", values="cobertura_pct")
    tabla_cob["minima"] = tabla_cob.min(axis=1)
    tabla_cob = tabla_cob.sort_values("minima").reset_index()
    tabla_med = cobertura.pivot(index="articulo_id", columns="cadena_key", values="mediana")
    tabla_med["max/min"] = (tabla_med.max(axis=1) / tabla_med.min(axis=1)).round(2)
    tabla_med = tabla_med.sort_values("max/min", ascending=False).reset_index()

    lineas = [
        "# Selección de artículos de la canasta",
        "",
        f"_Generado por `python -m src.analysis.seleccion_canasta` el {datetime.now():%Y-%m-%d %H:%M} · modo "
        f"`{config.MODO}`. Decisión: D-022 en `docs/decisiones.md`._",
        "",
        "## 1. Completitud por composición de canasta",
        "",
        "Celdas: cadena de referencia × municipio × semana con ventana completa. Una celda está completa si cada",
        "artículo tiene al menos una observación comparable y no atípica en la ventana de 14 días.",
        "",
        escenarios.to_markdown(index=False, floatfmt=".1f"),
        "",
        "## 2. Cobertura por definición de artículo (% de celdas de cada cadena)",
        "",
        tabla_cob.to_markdown(index=False, floatfmt=".1f"),
        "",
        "## 3. Mediana de precio unitario por cadena",
        "",
        "Una razón máximo/mínimo alta indica que la definición puede mezclar calidades o cortes distintos.",
        "",
        tabla_med.to_markdown(index=False, floatfmt=".2f"),
        "",
    ]
    path = config.REPORTS_OUT_DIR / "seleccion_canasta.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lineas), encoding="utf-8")
    print(f"[seleccion-canasta] {len(escenarios)} composiciones evaluadas → {path}", flush=True)
    return {"escenarios": escenarios, "cobertura": tabla_cob, "medianas": tabla_med}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
