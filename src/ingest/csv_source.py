"""Lectura declarativa de los CSV de PROFECO con DuckDB.

Centraliza cómo se lee un archivo (codificación, delimitador, comillas) para que
el perfilado y la ingesta usen exactamente la misma interpretación. Todas las
columnas se leen como texto: la conversión de tipos es responsabilidad de
staging, donde las fallas quedan medidas y no se pierden.
"""

from __future__ import annotations

from pathlib import Path

from src.ingest.sniff import FileSniff

# Esquema del diccionario oficial, observado en 2024-01 a 2026-05 y 2026-07 (ver docs/diccionario_validado.md).
EXPECTED_COLUMNS = [
    "producto",
    "presentacion",
    "marca",
    "categoria",
    "catalogo",
    "precio",
    "fecha_registro",
    "cadena_comercial",
    "giro",
    "nombre_comercial",
    "direccion",
    "estado",
    "municipio",
    "latitud",
    "longitud",
]

# Columnas no documentadas que PROFECO agregó al final de los archivos de 2026-06 (D-037). Ya fueron revisadas: se
# conservan en la capa cruda y no se modelan. Cualquier otra columna nueva sigue siendo un cambio de esquema inesperado.
COLUMNAS_ADICIONALES = ["folio", "cv_producto", "cv_marca"]

DUCKDB_ENCODING = {"utf-8": "utf-8", "utf-8-sig": "utf-8", "cp1252": "latin-1", "latin-1": "latin-1"}


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def columnas_adicionales(header: list[str], archivo: str) -> list[str]:
    """Valida el encabezado y devuelve sus columnas adicionales conocidas.

    Las 15 columnas esenciales deben estar completas y en su orden original; después solo se aceptan columnas de
    ``COLUMNAS_ADICIONALES``, sin repetir.
    """
    n = len(EXPECTED_COLUMNS)
    extra = header[n:]
    if (
        header[:n] != EXPECTED_COLUMNS
        or len(set(extra)) != len(extra)
        or set(extra) - set(COLUMNAS_ADICIONALES)
    ):
        raise ValueError(f"Esquema inesperado en {archivo}: {header}")
    return extra


def read_csv_sql(path: Path, sniff: FileSniff, rejects_table: str | None = None) -> str:
    """Construye la expresión ``read_csv(...)`` para un archivo ya inspeccionado.

    Devuelve todas las columnas del encabezado; quien consulte debe seleccionarlas por nombre.
    """
    columnas_adicionales(sniff.header, path.name)
    encoding = DUCKDB_ENCODING[sniff.encoding]
    columns = ", ".join(f"{sql_literal(c)}: 'VARCHAR'" for c in sniff.header)
    rejects = ""
    if rejects_table:
        rejects = f", store_rejects = true, rejects_table = {sql_literal(rejects_table)}"
    return (
        f"read_csv({sql_literal(path.as_posix())}, delim = {sql_literal(sniff.delimiter)}, "
        f"quote = '\"', escape = '\"', header = true, encoding = {sql_literal(encoding)}, "
        f"columns = {{{columns}}}, auto_detect = false, null_padding = false{rejects})"
    )
