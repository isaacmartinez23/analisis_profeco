"""Respuestas a las preguntas de negocio a partir de los marts.

Genera ``reports/resultados_canasta.md`` con cifras calculadas en cada ejecución. Las interpretaciones
editoriales viven en el memo ejecutivo (Fase 4); aquí solo hay cifras, su definición y sus salvedades.

Preguntas:

1. ¿Cuánto cuesta una misma canasta en diferentes cadenas y municipios?
2. ¿Cuánto puede ahorrar una familia al elegir la cadena más económica?
3. ¿Cómo cambia el costo de la canasta semana a semana?
4. ¿Qué productos explican las mayores diferencias de precio?
5. ¿Qué tan completa y representativa es la información utilizada?

Uso::

    python -m src.analysis.resultados
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect

SEMANAS_RECIENTES = 8


def _df(con, sql: str, params: list | None = None) -> pd.DataFrame:
    return con.execute(sql, params or []).df()


def calcular(con) -> dict[str, pd.DataFrame]:
    r: dict[str, pd.DataFrame] = {}
    ultima = con.execute("SELECT max(semana_inicio) FROM marts.mart_ahorro_por_cadena").fetchone()[0]
    desde = con.execute("SELECT ?::DATE - 7 * ?", [ultima, SEMANAS_RECIENTES - 1]).fetchone()[0]
    r["periodo"] = _df(
        con,
        """SELECT min(semana_inicio) AS primera_semana, max(semana_inicio) AS ultima_semana,
                  ?::DATE AS desde_recientes, any_value(canasta_version) AS canasta_version,
                  count(DISTINCT (geografia_id, semana_inicio)) AS municipio_semanas_comparables,
                  count(DISTINCT geografia_id) AS municipios_con_comparacion
           FROM marts.mart_ahorro_por_cadena""",
        [desde],
    )

    # 1. Costo por cadena en celdas comparables (misma canasta, municipio y semana).
    r["costo_por_cadena"] = _df(
        con,
        """SELECT cadena, grupo_empresarial,
                  count(*) AS municipio_semanas,
                  round(median(costo_canasta), 2) AS costo_mediano,
                  round(median(costo_canasta) FILTER (WHERE semana_inicio >= ?), 2) AS costo_mediano_recientes,
                  round(median(diferencia_vs_mediana_pct), 2) AS diferencia_vs_mediana_pct
           FROM marts.mart_ahorro_por_cadena GROUP BY ALL ORDER BY costo_mediano""",
        [desde],
    )
    # Nivel de precios municipal que controla la mezcla de cadenas: cada cadena se compara consigo misma.
    r["costo_por_municipio"] = _df(
        con,
        """WITH celdas AS (
               SELECT cadena_key, geografia_id, estado, municipio, costo_canasta
               FROM marts.mart_canasta_semanal
               WHERE es_cadena_referencia AND es_canasta_completa AND ventana_completa AND semana_inicio >= ?),
           por_municipio AS (
               SELECT cadena_key, geografia_id, any_value(estado) estado, any_value(municipio) municipio,
                      median(costo_canasta) AS costo, count(*) AS semanas
               FROM celdas GROUP BY 1, 2 HAVING count(*) >= 4),
           nacional AS (SELECT cadena_key, median(costo) AS costo_nacional FROM por_municipio GROUP BY 1),
           indice AS (
               SELECT estado, municipio, count(*) AS cadenas,
                      round(100 * exp(avg(ln(costo / costo_nacional))), 1) AS nivel_precios_100_nacional,
                      round(median(costo), 2) AS costo_mediano
               FROM por_municipio JOIN nacional USING (cadena_key) GROUP BY 1, 2 HAVING count(*) >= 2)
           (SELECT 'más baratos' AS grupo, * FROM indice ORDER BY nivel_precios_100_nacional LIMIT 5)
           UNION ALL
           (SELECT 'más caros' AS grupo, * FROM indice ORDER BY nivel_precios_100_nacional DESC LIMIT 5)""",
        [desde],
    )

    # 2. Ahorro al elegir la cadena más barata.
    r["brecha"] = _df(
        con,
        """WITH celdas AS (
               SELECT DISTINCT geografia_id, semana_inicio, cadenas_comparadas, grupos_comparados,
                      brecha_max_min, brecha_pct, costo_maximo
               FROM marts.mart_ahorro_por_cadena)
           SELECT 'todas' AS alcance, count(*) AS municipio_semanas,
                  round(median(brecha_max_min), 2) AS ahorro_maximo_mediano,
                  round(median(brecha_pct), 2) AS ahorro_maximo_mediano_pct,
                  round(quantile_cont(brecha_max_min, 0.9), 2) AS ahorro_maximo_p90
           FROM celdas
           UNION ALL
           SELECT 'con 4 cadenas', count(*), round(median(brecha_max_min), 2), round(median(brecha_pct), 2),
                  round(quantile_cont(brecha_max_min, 0.9), 2)
           FROM celdas WHERE cadenas_comparadas = 4
           UNION ALL
           SELECT 'con grupos distintos', count(*), round(median(brecha_max_min), 2), round(median(brecha_pct), 2),
                  round(quantile_cont(brecha_max_min, 0.9), 2)
           FROM celdas WHERE grupos_comparados >= 2""",
    )
    r["ahorro_por_cadena"] = _df(
        con,
        """SELECT cadena, count(*) AS municipio_semanas,
                  round(100.0 * avg(es_mas_barata::INT), 1) AS veces_mas_barata_pct,
                  round(median(ahorro_vs_mas_barata), 2) AS ahorro_mediano_al_cambiar,
                  round(median(ahorro_pct), 2) AS ahorro_mediano_pct,
                  round(median(ahorro_vs_mas_barata) * 52, 0) AS ahorro_anual_equivalente
           FROM marts.mart_ahorro_por_cadena GROUP BY 1 ORDER BY veces_mas_barata_pct DESC""",
    )

    # 3. Evolución: índice directo con panel fijo (D-026). Pares cadena-municipio con canasta completa en el
    # periodo base (primeras 8 semanas); cada semana compara su costo contra su propio costo base.
    r["indice"] = _df(
        con,
        """WITH m AS (
               SELECT cadena_key, geografia_id, semana_inicio, costo_canasta
               FROM marts.mart_canasta_semanal
               WHERE es_cadena_referencia AND es_canasta_completa AND ventana_completa),
           inicio AS (SELECT min(semana_inicio) AS s0 FROM m),
           base AS (
               SELECT cadena_key, geografia_id, median(costo_canasta) AS costo_base
               FROM m, inicio WHERE semana_inicio < s0 + 56 GROUP BY 1, 2)
           SELECT semana_inicio, count(*) AS pares,
                  round(100 * exp(avg(ln(costo_canasta / costo_base))), 1) AS indice_base_100
           FROM m JOIN base USING (cadena_key, geografia_id)
           GROUP BY 1 ORDER BY 1""",
    )
    ind = r["indice"]
    if len(ind):
        ind["mes"] = pd.to_datetime(ind["semana_inicio"]).dt.to_period("M").astype(str)
        r["indice_mensual"] = (
            ind.groupby("mes", as_index=False)
            .agg(indice_promedio=("indice_base_100", "mean"), pares_promedio=("pares", "mean"))
            .round(1)
        )

    # 4. Productos que explican las diferencias.
    r["explicacion_productos"] = _df(
        con,
        """WITH d AS (
               SELECT p.articulo, p.diferencia_vs_cadena_mas_barata AS dif
               FROM marts.mart_precio_producto p
               JOIN marts.mart_ahorro_por_cadena a USING (canasta_version, geografia_id, semana_inicio, cadena_key)
               WHERE p.es_celda_comparable AND NOT a.es_mas_barata),
           total AS (SELECT sum(abs(dif)) AS t, sum(dif) AS neto FROM d)
           SELECT articulo,
                  round(sum(dif), 0) AS diferencia_acumulada,
                  round(100 * sum(dif) / any_value(total.neto), 1) AS pct_de_la_diferencia_neta,
                  round(median(dif) FILTER (WHERE dif <> 0), 2) AS diferencia_mediana_por_celda,
                  round(100 * avg((dif < 0)::INT), 1) AS pct_celdas_mas_barato_que_ganadora
           FROM d, total GROUP BY articulo ORDER BY diferencia_acumulada DESC""",
    )
    r["dispersion_productos"] = _df(
        con,
        """SELECT articulo, count(*) AS celdas_articulo,
                  round(median(diferencia_vs_minimo_pct), 1) AS sobreprecio_mediano_vs_cadena_mas_barata_pct,
                  round(quantile_cont(diferencia_vs_minimo_pct, 0.9), 1) AS p90_pct
           FROM marts.mart_precio_producto WHERE cadenas_con_articulo >= 2 AND NOT es_cadena_mas_barata_articulo
           GROUP BY 1 ORDER BY sobreprecio_mediano_vs_cadena_mas_barata_pct DESC""",
    )

    # 5. Cobertura y representatividad.
    general = _df(
        con,
        """SELECT
               (SELECT count(*) FROM core.fct_precio_observado) AS "observaciones de precio",
               (SELECT count(DISTINCT estado_key) FROM core.dim_geografia) AS "estados con datos",
               (SELECT count(*) FROM core.dim_geografia) AS "municipios con datos",
               (SELECT count(*) FROM core.dim_establecimiento WHERE es_cadena_referencia) AS "tiendas de cadenas de referencia",
               (SELECT round(100 * avg(es_atipico::INT), 3) FROM core.fct_precio_observado) AS "% observaciones atípicas",
               (SELECT round(100.0 * avg(es_canasta_completa::INT), 1) FROM marts.mart_canasta_semanal
                WHERE es_cadena_referencia AND ventana_completa) AS "% celdas de referencia con canasta completa" """,
    ).iloc[0]
    r["cobertura_general"] = pd.DataFrame(
        {
            "indicador": general.index,
            "valor": [f"{v:,.3f}".rstrip("0").rstrip(".") for v in general.to_numpy()],
        }
    )
    r["cobertura_por_cadena"] = _df(
        con,
        """SELECT cadena, count(DISTINCT geografia_id) AS municipios, count(DISTINCT semana_inicio) AS semanas,
                  round(median(n_establecimientos), 1) AS tiendas_por_celda,
                  round(median(n_dias_con_observacion), 1) AS dias_por_semana,
                  round(100.0 * avg(es_canasta_completa::INT), 1) AS semanas_con_canasta_completa_pct
           FROM marts.mart_cobertura_datos WHERE es_cadena_referencia GROUP BY 1 ORDER BY municipios DESC""",
    )
    r["municipios_sin_comparacion"] = _df(
        con,
        """SELECT g.estado, g.municipio, g.n_establecimientos
           FROM core.dim_geografia g
           WHERE g.geografia_id NOT IN (SELECT geografia_id FROM marts.mart_ahorro_por_cadena)
           ORDER BY g.estado, g.municipio""",
    )
    return r


def escribir(r: dict[str, pd.DataFrame], path: Path) -> Path:
    p = r["periodo"].iloc[0]
    md = lambda k, fmt=",.2f": r[k].to_markdown(index=False, floatfmt=fmt)  # noqa: E731
    lineas = [
        "# Resultados del análisis de la canasta",
        "",
        f"_Generado por `python -m src.analysis.resultados` el {datetime.now():%Y-%m-%d %H:%M} · modo "
        f"`{config.MODO}` · canasta `{p.canasta_version}` · semanas {p.primera_semana:%Y-%m-%d} a "
        f"{p.ultima_semana:%Y-%m-%d}._",
        "",
        "Todas las comparaciones entre cadenas son **pareadas**: misma canasta, mismo municipio y misma semana",
        f"({p.municipio_semanas_comparables:,} municipio-semanas en {p.municipios_con_comparacion} municipios).",
        f'"Recientes" = últimas {SEMANAS_RECIENTES} semanas desde {p.desde_recientes:%Y-%m-%d}.',
        "Definiciones de métricas: `docs/catalogo_metricas.md`. Salvedades: `docs/limitaciones.md`.",
        "",
        "## 1. ¿Cuánto cuesta la misma canasta en diferentes cadenas y municipios?",
        "",
        md("costo_por_cadena"),
        "",
        "Nivel de precios municipal (recientes): cada cadena se compara con su propia mediana nacional y se",
        "promedia geométricamente entre las cadenas presentes (mínimo 2); 100 = nivel nacional. Evita que un",
        "municipio parezca barato solo porque ahí se mide una cadena barata.",
        "",
        md("costo_por_municipio"),
        "",
        "## 2. ¿Cuánto puede ahorrar una familia al elegir la cadena más económica?",
        "",
        "Ahorro máximo = diferencia entre la cadena más cara y la más barata del mismo municipio-semana:",
        "",
        md("brecha"),
        "",
        "Por cadena: frecuencia con la que es la más barata y ahorro al cambiarse a la más barata. El equivalente",
        "anual multiplica la mediana semanal por 52 y supone comprar la canasta de referencia cada semana.",
        "",
        md("ahorro_por_cadena", ",.1f"),
        "",
        "## 3. ¿Cómo cambia el costo semana a semana?",
        "",
        "Índice directo con panel fijo (base 100 = mediana de las primeras 8 semanas de cada par cadena-municipio):",
        "media geométrica de costo/costo base de los pares presentes. Se descartó el índice encadenado porque",
        "acumulaba ~3 puntos de deriva (D-026). Promedio mensual de los índices semanales:",
        "",
        md("indice_mensual", ",.1f") if "indice_mensual" in r else "_Sin datos suficientes._",
        "",
        "## 4. ¿Qué productos explican las mayores diferencias de precio?",
        "",
        "Diferencia acumulada = suma, sobre todas las cadenas no ganadoras y municipio-semanas comparables, del",
        "costo del artículo menos su costo en la cadena con la canasta más barata. Suma el ahorro total.",
        "",
        md("explicacion_productos", ",.1f"),
        "",
        "Sobreprecio mediano de cada artículo frente a la cadena donde ese artículo es más barato:",
        "",
        md("dispersion_productos", ",.1f"),
        "",
        "## 5. ¿Qué tan completa y representativa es la información?",
        "",
        r["cobertura_general"].to_markdown(index=False, disable_numparse=True),
        "",
        md("cobertura_por_cadena", ",.1f"),
        "",
        f"Municipios sin ninguna semana comparable ({len(r['municipios_sin_comparacion'])}):",
        "",
        md("municipios_sin_comparacion", ",.0f") if len(r["municipios_sin_comparacion"]) else "_Ninguno._",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lineas), encoding="utf-8")
    return path


def run(db_path: Path = config.DUCKDB_PATH) -> dict[str, pd.DataFrame]:
    with connect(db_path, read_only=True) as con:
        r = calcular(con)
    path = escribir(r, config.REPORTS_OUT_DIR / "resultados_canasta.md")
    print(f"[resultados] reporte escrito en {path}", flush=True)
    return r


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
