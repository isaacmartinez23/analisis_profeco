"""Lectura declarativa de los CSV de PROFECO con DuckDB.

Centraliza cómo se lee un archivo (codificación, delimitador, comillas) para que
el perfilado y la ingesta usen exactamente la misma interpretación. Todas las
columnas se leen como texto: la conversión de tipos es responsabilidad de
staging, donde las fallas quedan medidas y no se pierden.
"""

from __future__ import annotations

from pathlib import Path

from src.ingest.sniff import FileSniff

# Esquema observado en los 58 archivos 2024-01 a 2026-05 (ver docs/diccionario_validado.md).
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

DUCKDB_ENCODING = {"utf-8": "utf-8", "utf-8-sig": "utf-8", "cp1252": "latin-1", "latin-1": "latin-1"}


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def read_csv_sql(path: Path, sniff: FileSniff, rejects_table: str | None = None) -> str:
    """Construye la expresión ``read_csv(...)`` para un archivo ya inspeccionado."""
    if sniff.header != EXPECTED_COLUMNS:
        raise ValueError(f"Esquema inesperado en {path.name}: {sniff.header}")
    encoding = DUCKDB_ENCODING[sniff.encoding]
    columns = ", ".join(f"{sql_literal(c)}: 'VARCHAR'" for c in EXPECTED_COLUMNS)
    rejects = ""
    if rejects_table:
        rejects = f", store_rejects = true, rejects_table = {sql_literal(rejects_table)}"
    return (
        f"read_csv({sql_literal(path.as_posix())}, delim = {sql_literal(sniff.delimiter)}, "
        f"quote = '\"', escape = '\"', header = true, encoding = {sql_literal(encoding)}, "
        f"columns = {{{columns}}}, auto_detect = false, null_padding = false{rejects})"
    )
