"""Perfilado reproducible del dataset QQP (fase de reconocimiento).

Genera tablas de perfil en ``data/interim/profile/*.parquet`` que alimentan
``reports/perfil_datos.md`` y ``analysis/00_reconocimiento.ipynb``.

Control de recursos: toda consulta pesada se ejecuta archivo por archivo. Las
fechas de los archivos no se traslapan, así que un duplicado en el grano (que
incluye la fecha) solo puede ocurrir dentro de un mismo archivo.

Uso::

    python -m src.ingest.profile               # inspección completa
    python -m src.ingest.profile --reuse-db    # reutiliza perfil.duckdb ya cargado
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect
from src.ingest.csv_source import EXPECTED_COLUMNS, read_csv_sql, sql_literal
from src.ingest.sniff import FileSniff, sniff_file

PROFILE_DIR = config.INTERIM_DIR / "profile"
PROFILE_DB = PROFILE_DIR / "perfil.duckdb"
CANASTA_CANDIDATOS = config.MAPPINGS_DIR / "canasta_candidatos_v0.csv"

# Cadenas con mayor cobertura geográfica y temporal en el catálogo Básicos
# (ver reports/perfil_datos.md). Se usan solo para evaluar viabilidad.
CADENAS_REFERENCIA = ["Wal-mart", "Hipermercado Soriana", "Bodega Aurrera", "Chedraui"]
CATALOGOS_CANASTA = ["Basicos", "Frutas y Legumbres"]

NORM = "upper(strip_accents(trim({})))"
QUINCENA = "make_date(year(fecha), month(fecha), CASE WHEN day(fecha) <= 15 THEN 1 ELSE 16 END)"


@contextmanager
def _etapa(nombre: str):
    inicio = time.time()
    yield
    print(f"[profile] {nombre}: {time.time() - inicio:.1f}s", flush=True)


def archivo_id(path: Path) -> str:
    return f"{path.parent.name}/{path.name}"


def list_csv(extracted_dir: Path = config.EXTRACTED_DIR) -> list[Path]:
    files = sorted(extracted_dir.glob("*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No hay CSV extraídos en {extracted_dir}. Ejecuta `make extract`.")
    return files


def sniff_all(files: list[Path], workers: int = config.DUCKDB_THREADS) -> list[FileSniff]:
    with ProcessPoolExecutor(max_workers=workers) as pool:
        sniffs = list(pool.map(sniff_file, files))
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILE_DIR / "sniff.json").write_text(
        json.dumps([asdict(s) for s in sniffs], indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return sniffs


def load_text_tables(con, sniffs: list[FileSniff]) -> None:
    """Carga cada CSV como texto, conservando archivo de origen y filas rechazadas."""
    cols = ", ".join(f"{c} VARCHAR" for c in EXPECTED_COLUMNS)
    con.execute("DROP TABLE IF EXISTS raw_all; DROP TABLE IF EXISTS rechazos; DROP TABLE IF EXISTS archivos")
    con.execute(f"CREATE TABLE raw_all ({cols}, archivo VARCHAR)")
    con.execute(
        "CREATE TABLE rechazos (archivo VARCHAR, linea BIGINT, columna VARCHAR, tipo_error VARCHAR, mensaje VARCHAR)"
    )
    con.execute(
        "CREATE TABLE archivos (archivo VARCHAR, bytes BIGINT, bom BOOLEAN, codificacion VARCHAR, "
        "lineas_fisicas BIGINT, filas_cargadas BIGINT, delimitador VARCHAR)"
    )
    for s in sniffs:
        path = Path(s.path)
        name = archivo_id(path)
        source = read_csv_sql(path, s, rejects_table="reject_errors")
        filas = con.execute(f"INSERT INTO raw_all SELECT *, {sql_literal(name)} FROM {source}").fetchone()[0]
        con.execute(
            f"INSERT INTO rechazos SELECT {sql_literal(name)}, line, column_name, error_type::VARCHAR, "
            "error_message FROM reject_errors"
        )
        con.execute("DROP TABLE IF EXISTS reject_errors; DROP TABLE IF EXISTS reject_scans")
        con.execute(
            "INSERT INTO archivos VALUES (?, ?, ?, ?, ?, ?, ?)",
            [name, s.bytes, s.has_bom, s.encoding, s.lines, filas, s.delimiter],
        )
        print(f"[profile] cargado {name}: {filas} filas", flush=True)


def build_obs(con) -> None:
    """Tabla compacta con fecha interpretada y geografía sin acentos, archivo por archivo."""
    con.execute("DROP TABLE IF EXISTS obs")
    con.execute(
        """CREATE TABLE obs (archivo VARCHAR, producto VARCHAR, presentacion VARCHAR, marca VARCHAR,
        categoria VARCHAR, catalogo VARCHAR, precio DOUBLE, fecha DATE, formato_fecha VARCHAR, semana DATE,
        cadena VARCHAR, giro VARCHAR, tienda UBIGINT, estado VARCHAR, municipio VARCHAR)"""
    )
    archivos = [r[0] for r in con.execute("SELECT archivo FROM archivos ORDER BY archivo").fetchall()]
    tienda = (
        "hash("
        + ", ".join(NORM.format(c) for c in ["nombre_comercial", "direccion", "estado", "municipio"])
        + ")"
    )
    for name in archivos:
        con.execute(
            f"""
            INSERT INTO obs
            SELECT archivo, producto, presentacion, marca, categoria, catalogo, try_cast(precio AS DOUBLE),
                   fecha, formato_fecha, date_trunc('week', fecha)::DATE, cadena_comercial, giro, {tienda},
                   {NORM.format("estado")}, {NORM.format("municipio")}
            FROM (
                SELECT *,
                    COALESCE(try_strptime(fecha_registro, '%Y/%m/%d'), try_strptime(fecha_registro, '%d/%m/%Y'))::DATE
                        AS fecha,
                    CASE WHEN try_strptime(fecha_registro, '%Y/%m/%d') IS NOT NULL THEN 'yyyy/mm/dd'
                         WHEN try_strptime(fecha_registro, '%d/%m/%Y') IS NOT NULL THEN 'dd/mm/yyyy'
                         ELSE 'no_convertible' END AS formato_fecha
                FROM raw_all WHERE archivo = $1
            )""",
            [name],
        )


def _per_file(con, sql: str) -> pd.DataFrame:
    archivos = [r[0] for r in con.execute("SELECT archivo FROM archivos ORDER BY archivo").fetchall()]
    return pd.concat([con.execute(sql, [a]).df() for a in archivos], ignore_index=True)


DUPLICADOS_SQL = r"""
WITH k AS (
    SELECT hash(producto, presentacion, marca, nombre_comercial, direccion, estado, municipio, fecha_registro) AS k_grano,
           hash(producto, presentacion, marca, categoria, catalogo, precio, fecha_registro, cadena_comercial, giro,
                nombre_comercial, direccion, estado, municipio, latitud, longitud) AS k_fila,
           precio, catalogo,
           regexp_matches(concat_ws('|', producto, presentacion, marca, categoria, catalogo, cadena_comercial, giro,
                                    nombre_comercial, direccion, estado, municipio), '[A-Za-z]\?[A-Za-z]') AS interrogacion
    FROM raw_all WHERE archivo = $1),
g AS (SELECT k_grano, count(*) n, count(DISTINCT precio) np, count(DISTINCT catalogo) nc
      FROM k GROUP BY 1 HAVING count(*) > 1),
f AS (SELECT k_fila, count(*) n FROM k GROUP BY 1 HAVING count(*) > 1)
SELECT $1 AS archivo,
       (SELECT count(*) FROM k) AS filas,
       (SELECT coalesce(sum(n - 1), 0) FROM f)::BIGINT AS dup_exactos,
       (SELECT coalesce(sum(n - 1), 0) FROM g)::BIGINT AS dup_grano,
       (SELECT count(*) FILTER (WHERE nc > 1) FROM g) AS grupos_multicatalogo,
       (SELECT count(*) FILTER (WHERE np > 1 AND nc = 1) FROM g) AS grupos_precio_en_conflicto,
       (SELECT count(*) FILTER (WHERE interrogacion) FROM k) AS filas_con_caracter_perdido
"""

# Primero se aíslan los pocos grupos con más de un catálogo; `string_agg ... ORDER BY`
# es una agregación ordenada costosa y no debe correr sobre los ~600 mil grupos por archivo.
MULTICATALOGO_SQL = """
WITH k AS (
    SELECT hash(producto, presentacion, marca, nombre_comercial, direccion, estado, municipio, fecha_registro) AS g,
           catalogo
    FROM raw_all WHERE archivo = $1),
multi AS (SELECT g FROM k GROUP BY g HAVING count(DISTINCT catalogo) > 1)
SELECT combinacion, count(*) AS grupos FROM (
    SELECT g, string_agg(DISTINCT catalogo, ' + ' ORDER BY catalogo) AS combinacion
    FROM k SEMI JOIN multi USING (g) GROUP BY g)
GROUP BY 1
"""

GLOBAL_SQL = {
    "fechas_por_archivo": """
        SELECT archivo, any_value(formato_fecha) AS formato_fecha, count(DISTINCT formato_fecha) AS formatos,
               min(fecha) AS min_fecha, max(fecha) AS max_fecha, count(DISTINCT fecha) AS dias,
               count(*) FILTER (WHERE fecha IS NULL) AS fecha_no_convertible
        FROM obs GROUP BY archivo ORDER BY archivo""",
    "nulos_por_columna": "UNPIVOT (SELECT "
    + ", ".join(f"count(*) FILTER (WHERE {c} IS NULL OR trim({c}) = '') AS {c}" for c in EXPECTED_COLUMNS)
    + " FROM raw_all) ON COLUMNS(*) INTO NAME columna VALUE vacios",
    "cardinalidades": "UNPIVOT (SELECT "
    + ", ".join(f"count(DISTINCT {c}) AS {c}" for c in EXPECTED_COLUMNS if c not in {"latitud", "longitud"})
    + ", count(DISTINCT (latitud, longitud)) AS coordenadas FROM raw_all) ON COLUMNS(*) INTO NAME columna VALUE distintos",
    "precio_resumen": """
        SELECT count(*) FILTER (WHERE try_cast(precio AS DOUBLE) IS NULL) AS no_convertible,
               count(*) FILTER (WHERE try_cast(precio AS DOUBLE) < 0) AS negativos,
               count(*) FILTER (WHERE try_cast(precio AS DOUBLE) = 0) AS ceros,
               min(try_cast(precio AS DOUBLE)) AS minimo,
               quantile_cont(try_cast(precio AS DOUBLE), 0.01) AS p01,
               quantile_cont(try_cast(precio AS DOUBLE), 0.50) AS mediana,
               quantile_cont(try_cast(precio AS DOUBLE), 0.99) AS p99,
               max(try_cast(precio AS DOUBLE)) AS maximo
        FROM raw_all""",
    "precios_maximos": """
        SELECT producto, presentacion, marca, catalogo, try_cast(precio AS DOUBLE) AS precio, cadena_comercial, archivo
        FROM raw_all ORDER BY try_cast(precio AS DOUBLE) DESC LIMIT 10""",
    "coordenadas_resumen": """
        SELECT count(*) FILTER (WHERE try_cast(latitud AS DOUBLE) IS NULL OR try_cast(longitud AS DOUBLE) IS NULL)
                   AS sin_coordenadas,
               count(*) FILTER (WHERE try_cast(latitud AS DOUBLE) NOT BETWEEN 14 AND 33) AS latitud_fuera_mexico,
               count(*) FILTER (WHERE try_cast(longitud AS DOUBLE) NOT BETWEEN -119 AND -86) AS longitud_fuera_mexico
        FROM raw_all""",
    "catalogo_por_anio": """
        SELECT catalogo, year(fecha) AS anio, count(*) AS filas, count(DISTINCT producto) AS productos
        FROM obs GROUP BY ALL ORDER BY catalogo, anio""",
    "giro_valores": """
        SELECT giro, count(*) AS filas, count(DISTINCT cadena_comercial) AS cadenas, count(DISTINCT archivo) AS archivos
        FROM raw_all GROUP BY 1 ORDER BY filas DESC""",
    "estado_variantes": f"""
        SELECT {NORM.format("estado")} AS estado_normalizado, estado AS estado_original, count(*) AS filas,
               min(archivo) AS primer_archivo, max(archivo) AS ultimo_archivo
        FROM raw_all GROUP BY ALL ORDER BY 1, 2""",
    "marca_sin_marca_variantes": """
        SELECT marca, year(fecha) AS anio, count(*) AS filas FROM obs
        WHERE upper(marca) = 'S/M' GROUP BY ALL ORDER BY anio, marca""",
    "cobertura_estados": """
        SELECT estado, count(DISTINCT municipio) AS municipios, count(DISTINCT semana) AS semanas,
               count(DISTINCT tienda) AS tiendas, count(*) AS filas
        FROM obs GROUP BY 1 ORDER BY 1""",
    "cobertura_cadenas_basicos": """
        SELECT cadena, count(DISTINCT estado) AS estados, count(DISTINCT (estado, municipio)) AS municipios,
               count(DISTINCT tienda) AS tiendas, count(DISTINCT semana) AS semanas,
               count(DISTINCT producto) AS productos, count(*) AS filas
        FROM obs WHERE catalogo = 'Basicos' GROUP BY 1 HAVING count(*) > 50000 ORDER BY filas DESC""",
    "visitas_tienda_quincena": f"""
        WITH t AS (SELECT tienda, {QUINCENA} AS quincena, count(DISTINCT fecha) AS dias
                   FROM obs WHERE cadena IN (SELECT cadena FROM cadenas_ref) GROUP BY 1, 2)
        SELECT dias AS dias_con_registro, count(*) AS tienda_quincenas FROM t GROUP BY 1 ORDER BY 1""",
}


def canasta_viabilidad(con) -> dict[str, pd.DataFrame]:
    """Evalúa si una canasta puede compararse entre cadenas con distintas definiciones."""
    candidatos = pd.read_csv(CANASTA_CANDIDATOS)
    con.register("candidatos_df", candidatos)
    cadenas = ", ".join(sql_literal(c) for c in CADENAS_REFERENCIA)
    catalogos = ", ".join(sql_literal(c) for c in CATALOGOS_CANASTA)
    con.execute(
        f"""CREATE OR REPLACE TEMP TABLE canasta_obs AS
        SELECT cadena, estado, municipio, fecha, semana, {QUINCENA} AS quincena,
               date_trunc('month', fecha)::DATE AS mes,
               upper(producto) AS producto, upper(presentacion) AS presentacion, upper(marca) AS marca
        FROM obs
        WHERE catalogo IN ({catalogos}) AND cadena IN ({cadenas})
          AND upper(producto) IN (SELECT producto_generico FROM candidatos_df)"""
    )
    n = len(candidatos)

    def completitud(nivel: str, grano: str, fuente: str, llave: str = "producto") -> str:
        return f"""SELECT '{nivel}' AS nivel, cadena, count(*) AS celdas,
                   round(100 * avg((k = {n})::INT), 1) AS pct_completa,
                   round(100 * avg((k >= {n - 1})::INT), 1) AS pct_falta_max_1
            FROM (SELECT cadena, {grano}, count(DISTINCT {llave}) AS k FROM {fuente} GROUP BY ALL) GROUP BY 1, 2"""

    # Definición A: SKU exacto (marca fija), eligiendo por producto el SKU con mayor presencia mínima entre cadenas.
    sku = con.execute(
        """
        WITH cel AS (SELECT cadena, count(DISTINCT (estado, municipio, quincena)) AS n FROM canasta_obs GROUP BY 1),
        p AS (SELECT producto, presentacion, marca, cadena, count(DISTINCT (estado, municipio, quincena)) AS k
              FROM canasta_obs GROUP BY ALL),
        w AS (SELECT producto, presentacion, marca, count(*) AS cadenas, min(100.0 * k / n) AS min_pct,
                     avg(100.0 * k / n) AS avg_pct
              FROM p JOIN cel USING (cadena) GROUP BY ALL),
        r AS (SELECT *, row_number() OVER (PARTITION BY producto ORDER BY cadenas DESC, min_pct DESC, avg_pct DESC) rk
              FROM w)
        SELECT producto, presentacion, marca, cadenas, round(min_pct, 1) AS presencia_min_pct,
               round(avg_pct, 1) AS presencia_prom_pct
        FROM r WHERE rk = 1 ORDER BY presencia_min_pct"""
    ).df()
    con.register("sku_df", sku)
    con.execute(
        """CREATE OR REPLACE TEMP TABLE canasta_sku AS
        SELECT o.* FROM canasta_obs o JOIN sku_df s USING (producto, presentacion, marca)"""
    )
    con.execute(
        """CREATE OR REPLACE TEMP TABLE canasta_ventana AS
        SELECT cadena, estado, municipio, producto, semana AS semana_ventana FROM canasta_obs
        UNION ALL SELECT cadena, estado, municipio, producto, semana + 7 FROM canasta_obs"""
    )
    escenarios = " UNION ALL ".join(
        [
            completitud("A. SKU exacto · municipio×semana", "estado, municipio, semana", "canasta_sku"),
            completitud("A. SKU exacto · municipio×quincena", "estado, municipio, quincena", "canasta_sku"),
            completitud("B. Genérico · municipio×semana", "estado, municipio, semana", "canasta_obs"),
            completitud(
                "B. Genérico · municipio×semana (ventana 14 días)",
                "estado, municipio, semana_ventana",
                "canasta_ventana",
            ),
            completitud("B. Genérico · municipio×quincena", "estado, municipio, quincena", "canasta_obs"),
            completitud("B. Genérico · municipio×mes", "estado, municipio, mes", "canasta_obs"),
        ]
    )
    return {"canasta_sku_mejor_presencia": sku, "canasta_completitud": con.execute(escenarios).df()}


def run(reuse_db: bool = False) -> dict[str, pd.DataFrame]:
    t0 = time.time()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if not (reuse_db and PROFILE_DB.exists()):
        files = list_csv()
        print(f"[profile] inspeccionando {len(files)} CSV", flush=True)
        with _etapa("sniff"):
            sniffs = sniff_all(files)
        PROFILE_DB.unlink(missing_ok=True)
        with connect(PROFILE_DB) as con:
            with _etapa("carga_texto"):
                load_text_tables(con, sniffs)
            with _etapa("obs"):
                build_obs(con)

    results: dict[str, pd.DataFrame] = {}
    with connect(PROFILE_DB) as con:
        con.execute("CREATE OR REPLACE TEMP TABLE cadenas_ref (cadena VARCHAR)")
        con.executemany("INSERT INTO cadenas_ref VALUES (?)", [(c,) for c in CADENAS_REFERENCIA])
        results["archivos"] = con.execute("SELECT * FROM archivos ORDER BY archivo").df()
        results["rechazos"] = con.execute("SELECT * FROM rechazos").df()
        for name, sql in GLOBAL_SQL.items():
            with _etapa(name):
                results[name] = con.execute(sql).df()
        with _etapa("duplicados_por_archivo"):
            results["duplicados_por_archivo"] = _per_file(con, DUPLICADOS_SQL)
        with _etapa("duplicados_multicatalogo"):
            results["duplicados_multicatalogo"] = (
                _per_file(con, MULTICATALOGO_SQL)
                .groupby("combinacion", as_index=False)["grupos"]
                .sum()
                .sort_values("grupos", ascending=False)
            )
        with _etapa("canasta_viabilidad"):
            results.update(canasta_viabilidad(con))

    for name, df in results.items():
        df.to_parquet(PROFILE_DIR / f"{name}.parquet", index=False)
    print(f"[profile] {len(results)} tablas de perfil en {PROFILE_DIR} ({time.time() - t0:.0f}s)", flush=True)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reuse-db", action="store_true", help="no recarga los CSV si perfil.duckdb existe")
    args = parser.parse_args(argv)
    from src.ingest import profile_report

    run(reuse_db=args.reuse_db)
    profile_report.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
