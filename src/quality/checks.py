"""Reglas de calidad de datos con umbrales de aceptación.

Dos etapas:

- ``raw``: sobre la capa cruda, antes de normalizar y transformar.
- ``marts``: sobre el modelo dbt ya construido (complementa las pruebas dbt con métricas de cobertura).

Severidades: ``error`` detiene el pipeline (y por lo tanto la publicación); ``advertencia`` se reporta
sin detenerlo. Cada regla calcula un valor numérico y lo compara contra su umbral.
El catálogo y la justificación de cada regla está en docs/reglas_calidad.md.

Uso::

    python -m src.quality.checks raw
    python -m src.quality.checks marts
"""

from __future__ import annotations

import argparse
import operator
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect

COMPARADORES = {"<=": operator.le, ">=": operator.ge, "==": operator.eq}


@dataclass(frozen=True)
class Regla:
    id: str
    etapa: str
    nombre: str
    descripcion: str
    severidad: str
    comparador: str
    umbral: float
    medir: Callable  # (con) -> float


def _escalar(sql: str) -> Callable:
    return lambda con: float(con.execute(sql).fetchone()[0] or 0)


def _archivos_esperados(con) -> float:
    from src.ingest.load import archivo_id, listar_csv

    esperados = {archivo_id(p, config.CSV_DIR) for p in listar_csv(config.CSV_DIR)}
    cargados = {r[0] for r in con.execute("SELECT archivo FROM raw.archivos").fetchall()}
    return float(len(esperados - cargados))


def _duplicados_exactos_pct(con) -> float:
    from src.ingest.csv_source import EXPECTED_COLUMNS

    # Por archivo para acotar memoria (D-005): las fechas de los archivos no se traslapan.
    archivos = [r[0] for r in con.execute("SELECT archivo FROM raw.archivos").fetchall()]
    total = sobrantes = 0
    for archivo in archivos:
        filas, dup = con.execute(
            f"""WITH k AS (SELECT hash({", ".join(EXPECTED_COLUMNS)}) AS h
                          FROM raw.qqp_precios WHERE archivo_origen = $1)
               SELECT (SELECT count(*) FROM k),
                      (SELECT coalesce(sum(n - 1), 0) FROM (SELECT count(*) n FROM k GROUP BY h HAVING n > 1))""",
            [archivo],
        ).fetchone()
        total += filas
        sobrantes += dup
    return 100.0 * sobrantes / max(total, 1)


FECHA_SQL = """
    CASE a.formato_fecha
        WHEN 'yyyy/mm/dd' THEN try_strptime(p.fecha_registro, '%Y/%m/%d')
        WHEN 'dd/mm/yyyy' THEN try_strptime(p.fecha_registro, '%d/%m/%Y')
    END::DATE
"""
BASE_RAW = "FROM raw.qqp_precios p JOIN raw.archivos a ON a.archivo = p.archivo_origen"

REGLAS_RAW = [
    Regla(
        "R-01",
        "raw",
        "archivos_disponibles_cargados",
        "Todos los CSV disponibles están cargados en raw.archivos (legibles y con esquema válido).",
        "error",
        "==",
        0,
        _archivos_esperados,
    ),
    Regla(
        "R-02",
        "raw",
        "columnas_esenciales_vacias_pct",
        "% de filas con producto, presentación, marca, precio, fecha, cadena, establecimiento, estado o municipio vacíos.",
        "error",
        "<=",
        0.1,
        _escalar(
            "SELECT 100.0 * count(*) FILTER (WHERE "
            + " OR ".join(
                f"nullif(trim({c}), '') IS NULL"
                for c in [
                    "producto",
                    "presentacion",
                    "marca",
                    "precio",
                    "fecha_registro",
                    "cadena_comercial",
                    "nombre_comercial",
                    "estado",
                    "municipio",
                ]
            )
            + ") / greatest(count(*), 1) FROM raw.qqp_precios"
        ),
    ),
    Regla(
        "R-03",
        "raw",
        "precio_no_convertible_pct",
        "% de precios que no se pueden convertir a número.",
        "error",
        "<=",
        0.01,
        _escalar(
            "SELECT 100.0 * count(*) FILTER (WHERE try_cast(precio AS DECIMAL(12,2)) IS NULL) / greatest(count(*), 1) "
            "FROM raw.qqp_precios"
        ),
    ),
    Regla(
        "R-04",
        "raw",
        "precio_no_positivo",
        "Número de precios negativos o iguales a cero.",
        "error",
        "==",
        0,
        _escalar("SELECT count(*) FROM raw.qqp_precios WHERE try_cast(precio AS DECIMAL(12,2)) <= 0"),
    ),
    Regla(
        "R-05",
        "raw",
        "fecha_no_convertible_pct",
        "% de fechas que no se pueden interpretar con el formato detectado para su archivo.",
        "error",
        "<=",
        0.0,
        _escalar(
            f"SELECT 100.0 * count(*) FILTER (WHERE {FECHA_SQL} IS NULL) / greatest(count(*), 1) {BASE_RAW}"
        ),
    ),
    Regla(
        "R-06",
        "raw",
        "fecha_fuera_de_rango",
        "Número de fechas anteriores a 2015-01-01 o posteriores a la fecha de ejecución.",
        "error",
        "==",
        0,
        lambda con: float(
            con.execute(
                f"SELECT count(*) {BASE_RAW} WHERE {FECHA_SQL} < DATE '2015-01-01' OR {FECHA_SQL} > ?",
                [date.today()],
            ).fetchone()[0]
        ),
    ),
    Regla(
        "R-07",
        "raw",
        "fecha_distinta_al_mes_del_archivo_pct",
        "% de filas cuyo mes no coincide con el mes indicado en el nombre del archivo (MM-AAAA).",
        "advertencia",
        "<=",
        0.1,
        _escalar(
            f"""SELECT 100.0 * count(*) FILTER (WHERE strftime({FECHA_SQL}, '%m-%Y') <>
                   regexp_extract(p.archivo_origen, '(\\d{{2}}-\\d{{4}})', 1)) / greatest(count(*), 1) {BASE_RAW}"""
        ),
    ),
    Regla(
        "R-08",
        "raw",
        "coordenadas_invalidas_pct",
        "% de filas sin coordenadas o fuera del recuadro geográfico de México.",
        "advertencia",
        "<=",
        1.0,
        _escalar(
            """SELECT 100.0 * count(*) FILTER (WHERE NOT (coalesce(try_cast(latitud AS DOUBLE) BETWEEN 14 AND 33, false)
                   AND coalesce(try_cast(longitud AS DOUBLE) BETWEEN -119 AND -86, false))) / greatest(count(*), 1)
               FROM raw.qqp_precios"""
        ),
    ),
    Regla(
        "R-09",
        "raw",
        "duplicados_exactos_pct",
        "% de filas idénticas en las 15 columnas dentro de un mismo archivo.",
        "advertencia",
        "<=",
        0.1,
        _duplicados_exactos_pct,
    ),
    Regla(
        "R-10",
        "raw",
        "volumen_minimo_relativo_por_archivo",
        "Filas del archivo más pequeño entre la mediana de filas por archivo (detecta cargas truncadas).",
        "advertencia",
        ">=",
        0.5,
        _escalar("SELECT min(filas) / median(filas) FROM raw.archivos"),
    ),
]

REGLAS_MARTS = [
    Regla(
        "M-01",
        "marts",
        "observaciones_atipicas_pct",
        "% de observaciones marcadas como atípicas (Q-ATIP-01/02).",
        "advertencia",
        "<=",
        1.0,
        _escalar("SELECT 100.0 * avg(es_atipico::INT) FROM core.fct_precio_observado"),
    ),
    Regla(
        "M-02",
        "marts",
        "observaciones_atipicas_pct_maximo",
        "% de observaciones atípicas por encima del cual el pipeline se detiene (posible error sistemático).",
        "error",
        "<=",
        5.0,
        _escalar("SELECT 100.0 * avg(es_atipico::INT) FROM core.fct_precio_observado"),
    ),
    Regla(
        "M-03",
        "marts",
        "observaciones_no_comparables_catalogos_canasta_pct",
        "% de observaciones de catálogos de canasta (Básicos, Frutas y Legumbres, Pacic) sin presentación comparable.",
        "advertencia",
        "<=",
        5.0,
        _escalar(
            """SELECT 100.0 * avg((NOT f.es_comparable)::INT) FROM core.fct_precio_observado f
               WHERE f.catalogos_mask & ((1 << 0) | (1 << 3) | (1 << 4)) <> 0"""
        ),
    ),
    Regla(
        "M-04",
        "marts",
        "celdas_referencia_canasta_completa_pct",
        "% de celdas cadena de referencia × municipio × semana (ventana completa) con la canasta completa.",
        "advertencia",
        ">=",
        50.0,
        _escalar(
            """SELECT 100.0 * avg(es_canasta_completa::INT) FROM marts.mart_canasta_semanal
               WHERE es_cadena_referencia AND ventana_completa"""
        ),
    ),
    Regla(
        "M-05",
        "marts",
        "articulos_sin_observaciones_ultima_semana",
        "Artículos de la canasta sin ninguna observación comparable en la última semana (cadenas de referencia).",
        "advertencia",
        "==",
        0,
        _escalar(
            """WITH ultima AS (SELECT max(semana_inicio) s FROM intermediate.int_canasta_articulo_semanal)
               SELECT count(*) FROM core.dim_canasta c
               WHERE c.es_version_vigente AND c.articulo_id NOT IN (
                   SELECT a.articulo_id FROM intermediate.int_canasta_articulo_semanal a
                   JOIN seeds.cadenas_referencia r ON r.cadena_key = a.cadena_key
                   CROSS JOIN ultima
                   WHERE a.semana_inicio = ultima.s)"""
        ),
    ),
    Regla(
        "M-06",
        "marts",
        "filas_crudas_sin_observacion",
        "Filas crudas con precio y fecha válidos que no llegaron a la tabla de hechos.",
        "error",
        "==",
        0,
        _escalar(
            """SELECT (SELECT count(*) FROM staging.stg_qqp__precios WHERE precio IS NOT NULL AND fecha IS NOT NULL)
                    - (SELECT sum(n_registros_origen) FROM core.fct_precio_observado)"""
        ),
    ),
]

REGLAS = {"raw": REGLAS_RAW, "marts": REGLAS_MARTS}


def evaluar(con, etapa: str) -> pd.DataFrame:
    filas = []
    for regla in REGLAS[etapa]:
        valor = regla.medir(con)
        cumple = COMPARADORES[regla.comparador](round(valor, 6), regla.umbral)
        filas.append(
            {
                "id": regla.id,
                "regla": regla.nombre,
                "severidad": regla.severidad,
                "valor": round(valor, 4),
                "condicion": f"{regla.comparador} {regla.umbral:g}",
                "resultado": "cumple" if cumple else ("FALLA" if regla.severidad == "error" else "alerta"),
                "descripcion": regla.descripcion,
            }
        )
    return pd.DataFrame(filas)


def escribir_reporte(resultados: dict[str, pd.DataFrame], path: Path) -> None:
    lineas = [
        "# Reporte de calidad de datos",
        "",
        f"_Generado por `python -m src.quality.checks` el {datetime.now():%Y-%m-%d %H:%M} · modo `{config.MODO}` · "
        f"base `{config.DUCKDB_PATH.name}`._",
        "",
        "Severidad `error` detiene el pipeline y bloquea la publicación; `advertencia` se reporta sin detenerlo.",
        "Definiciones y justificación de umbrales: `docs/reglas_calidad.md`.",
        "",
    ]
    for etapa, df in resultados.items():
        titulo = "Capa cruda" if etapa == "raw" else "Modelo transformado"
        fallas = int((df["resultado"] == "FALLA").sum())
        alertas = int((df["resultado"] == "alerta").sum())
        lineas += [
            f"## {titulo} (`{etapa}`)",
            "",
            f"{len(df)} reglas · {fallas} fallas · {alertas} alertas",
            "",
            df.to_markdown(index=False),
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lineas), encoding="utf-8")


def run(etapa: str, db_path: Path = config.DUCKDB_PATH) -> pd.DataFrame:
    with connect(db_path, read_only=True) as con:
        df = evaluar(con, etapa)

    salida = config.REPORTS_OUT_DIR / "calidad_datos.md"
    previos = {}
    for otra in REGLAS:
        cache = config.REPORTS_OUT_DIR / f".calidad_{otra}.parquet"
        if otra == etapa:
            cache.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(cache, index=False)
        if cache.exists():
            previos[otra] = pd.read_parquet(cache)
    escribir_reporte(previos, salida)

    for _, r in df.iterrows():
        marca = {"cumple": "ok ", "alerta": "!! ", "FALLA": "XX "}[r["resultado"]]
        print(f"[quality] {marca}{r['id']} {r['regla']}: {r['valor']} ({r['condicion']})", flush=True)
    fallas = df[df["resultado"] == "FALLA"]
    if len(fallas):
        raise SystemExit(
            f"[quality] {len(fallas)} regla(s) de severidad error fallaron: {', '.join(fallas['id'])}"
        )
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("etapa", choices=sorted(REGLAS))
    run(parser.parse_args(argv).etapa)
    return 0


if __name__ == "__main__":
    sys.exit(main())
