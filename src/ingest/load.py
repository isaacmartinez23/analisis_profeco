"""Ingesta idempotente de los CSV hacia DuckDB (esquema ``raw``).

Reglas:

- Un archivo se identifica por su ruta relativa (``QQP_2026/05-2026_Q2.csv``) y
  su CRC32. Si ya se cargó con el mismo CRC32, se omite.
- Si el contenido cambió, sus filas se reemplazan dentro de una transacción.
- Cada archivo se carga en su propia transacción y se valida que el número de
  filas insertadas sea igual a las líneas físicas menos el encabezado. Si no,
  se revierte: nunca quedan cargas parciales.
- Todas las columnas se guardan como texto, junto con el archivo de origen, el
  identificador de carga y la hora de carga.
- Las columnas adicionales conocidas (``folio``, ``cv_producto``, ``cv_marca``,
  presentes solo en algunos archivos) se guardan por nombre; en los demás archivos
  quedan nulas. ``raw.archivos.columnas_adicionales`` registra cuáles trajo cada uno.

Uso::

    python -m src.ingest.load
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src import config
from src.db import connect
from src.ingest.csv_source import COLUMNAS_ADICIONALES, EXPECTED_COLUMNS, columnas_adicionales, read_csv_sql
from src.ingest.extract import crc32_file
from src.ingest.sniff import sniff_file

FORMATOS_FECHA = {"%Y/%m/%d": "yyyy/mm/dd", "%d/%m/%Y": "dd/mm/yyyy"}

DDL = f"""
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.cargas (
    id_carga VARCHAR PRIMARY KEY,
    iniciada_utc TIMESTAMP NOT NULL,
    finalizada_utc TIMESTAMP,
    estado VARCHAR NOT NULL,
    modo VARCHAR NOT NULL,
    directorio_origen VARCHAR NOT NULL,
    archivos_evaluados INTEGER,
    archivos_cargados INTEGER,
    archivos_omitidos INTEGER,
    filas_insertadas BIGINT,
    filas_reemplazadas BIGINT,
    mensaje VARCHAR
);
CREATE TABLE IF NOT EXISTS raw.archivos (
    archivo VARCHAR PRIMARY KEY,
    crc32 BIGINT NOT NULL,
    bytes BIGINT NOT NULL,
    codificacion VARCHAR NOT NULL,
    bom BOOLEAN NOT NULL,
    formato_fecha VARCHAR NOT NULL,
    lineas_fisicas BIGINT NOT NULL,
    filas BIGINT NOT NULL,
    id_carga VARCHAR NOT NULL,
    cargado_utc TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.qqp_precios (
    {", ".join(f"{c} VARCHAR" for c in EXPECTED_COLUMNS)},
    archivo_origen VARCHAR NOT NULL,
    id_carga VARCHAR NOT NULL,
    cargado_utc TIMESTAMP NOT NULL
);
-- Agregadas después de la primera versión: ALTER mantiene el mismo orden en bases nuevas y existentes.
ALTER TABLE raw.archivos ADD COLUMN IF NOT EXISTS columnas_adicionales VARCHAR;
{"".join(f"ALTER TABLE raw.qqp_precios ADD COLUMN IF NOT EXISTS {c} VARCHAR;" for c in COLUMNAS_ADICIONALES)}
"""


@dataclass
class ResultadoArchivo:
    archivo: str
    estado: str  # cargado | reemplazado | omitido
    filas: int
    filas_previas: int = 0


def archivo_id(path: Path, base_dir: Path) -> str:
    return path.relative_to(base_dir).as_posix()


def listar_csv(base_dir: Path) -> list[Path]:
    files = sorted(base_dir.glob("*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No hay CSV en {base_dir}")
    return files


def _crc_desde_manifest(base_dir: Path) -> dict[str, tuple[int, int]]:
    """CRC32 y tamaño declarados en el manifiesto de extracción, si existe."""
    manifest = base_dir.parent / "manifest_extraccion.json"
    if not manifest.exists():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    out = {}
    for arch in data["archivos"]:
        for m in arch["csv"]:
            target = Path(m["target"])
            out[f"{target.parent.name}/{target.name}"] = (m["crc32"], m["size"])
    return out


def _formato_fecha(date_formats: dict[str, int], archivo: str) -> str:
    conocidos = {f: n for f, n in date_formats.items() if f in FORMATOS_FECHA}
    if len(conocidos) != 1 or set(date_formats) - set(conocidos):
        raise ValueError(f"{archivo}: formato de fecha no reconocido o mezclado: {date_formats}")
    return FORMATOS_FECHA[next(iter(conocidos))]


def cargar_archivo(con, path: Path, base_dir: Path, crc: int, id_carga: str) -> ResultadoArchivo:
    nombre = archivo_id(path, base_dir)
    previo = con.execute("SELECT crc32 FROM raw.archivos WHERE archivo = ?", [nombre]).fetchone()
    if previo and previo[0] == crc:
        return ResultadoArchivo(nombre, "omitido", 0)

    sniff = sniff_file(path)
    formato = _formato_fecha(sniff.date_formats, nombre)
    adicionales = columnas_adicionales(sniff.header, nombre)
    ahora = datetime.now(UTC).replace(tzinfo=None)

    con.execute("BEGIN TRANSACTION")
    try:
        filas_previas = con.execute(
            "SELECT count(*) FROM raw.qqp_precios WHERE archivo_origen = ?", [nombre]
        ).fetchone()[0]
        con.execute("DELETE FROM raw.qqp_precios WHERE archivo_origen = ?", [nombre])
        filas = con.execute(
            f"""INSERT INTO raw.qqp_precios BY NAME
                SELECT *, ? AS archivo_origen, ? AS id_carga, ? AS cargado_utc FROM {read_csv_sql(path, sniff)}""",
            [nombre, id_carga, ahora],
        ).fetchone()[0]
        if filas != sniff.lines - 1:
            raise RuntimeError(
                f"{nombre}: se insertaron {filas} filas pero el archivo tiene {sniff.lines - 1} líneas de datos"
            )
        con.execute("DELETE FROM raw.archivos WHERE archivo = ?", [nombre])
        con.execute(
            """INSERT INTO raw.archivos (archivo, crc32, bytes, codificacion, bom, formato_fecha, lineas_fisicas,
                   filas, id_carga, cargado_utc, columnas_adicionales)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                nombre,
                crc,
                sniff.bytes,
                sniff.encoding,
                sniff.has_bom,
                formato,
                sniff.lines,
                filas,
                id_carga,
                ahora,
                ",".join(adicionales) or None,
            ],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    estado = "reemplazado" if previo else "cargado"
    return ResultadoArchivo(nombre, estado, filas, filas_previas)


def run(base_dir: Path = config.CSV_DIR, db_path: Path = config.DUCKDB_PATH) -> list[ResultadoArchivo]:
    files = listar_csv(base_dir)
    manifest = _crc_desde_manifest(base_dir)
    id_carga = f"c{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    with connect(db_path) as con:
        con.execute(DDL)
        con.execute(
            "INSERT INTO raw.cargas (id_carga, iniciada_utc, estado, modo, directorio_origen) VALUES (?, ?, ?, ?, ?)",
            [id_carga, datetime.now(UTC).replace(tzinfo=None), "en_proceso", config.MODO, str(base_dir)],
        )
        resultados: list[ResultadoArchivo] = []
        try:
            for path in files:
                nombre = archivo_id(path, base_dir)
                crc, size = manifest.get(nombre, (None, None))
                if crc is None or size != path.stat().st_size:
                    crc = crc32_file(path)
                r = cargar_archivo(con, path, base_dir, crc, id_carga)
                resultados.append(r)
                if r.estado != "omitido":
                    print(f"[ingest] {r.estado} {r.archivo}: {r.filas:,} filas", flush=True)
            estado, mensaje = "exitosa", None
        except Exception as exc:
            estado, mensaje = "fallida", str(exc)
            raise
        finally:
            con.execute(
                """UPDATE raw.cargas SET finalizada_utc = ?, estado = ?, archivos_evaluados = ?,
                   archivos_cargados = ?, archivos_omitidos = ?, filas_insertadas = ?, filas_reemplazadas = ?,
                   mensaje = ? WHERE id_carga = ?""",
                [
                    datetime.now(UTC).replace(tzinfo=None),
                    estado,
                    len(files),
                    sum(r.estado != "omitido" for r in resultados),
                    sum(r.estado == "omitido" for r in resultados),
                    sum(r.filas for r in resultados),
                    sum(r.filas_previas for r in resultados),
                    mensaje,
                    id_carga,
                ],
            )
    omitidos = sum(r.estado == "omitido" for r in resultados)
    print(
        f"[ingest] carga {id_carga}: {len(files) - omitidos} archivos cargados, {omitidos} sin cambios "
        f"({time.time() - t0:.0f}s) → {db_path}",
        flush=True,
    )
    return resultados


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
