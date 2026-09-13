"""Conexión única a DuckDB con límites de recursos explícitos.

Todo el código del proyecto debe abrir DuckDB mediante :func:`connect` para que
los límites de hilos, memoria y derrame a disco se apliquen siempre.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from src import config


def connect(
    path: Path | str = config.DUCKDB_PATH,
    read_only: bool = False,
    threads: int | None = None,
    memory_limit: str | None = None,
) -> duckdb.DuckDBPyConnection:
    temp_dir = Path(config.DUCKDB_TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(
        str(path),
        read_only=read_only,
        config={
            "threads": threads or config.DUCKDB_THREADS,
            "memory_limit": memory_limit or config.DUCKDB_MEMORY_LIMIT,
            "temp_directory": temp_dir.as_posix(),
            # No se necesita orden de inserción en agregaciones; reduce memoria.
            "preserve_insertion_order": False,
        },
    )
    return con


def settings(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    rows = con.execute(
        "SELECT name, value FROM duckdb_settings() "
        "WHERE name IN ('threads', 'memory_limit', 'temp_directory', 'preserve_insertion_order')"
    ).fetchall()
    return dict(rows)
