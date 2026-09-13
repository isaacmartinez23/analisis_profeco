"""Rutas y parámetros compartidos del pipeline.

Todas las rutas pueden sobreescribirse con variables de entorno para que el
mismo código funcione con los datos completos, con la muestra versionada y en
GitHub Actions.

``QQP_MODO=muestra`` apunta el pipeline a ``data/sample/csv`` y a una base
DuckDB separada, sin necesidad de los archivos comprimidos originales.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODO = os.getenv("QQP_MODO", "completo")
if MODO not in {"completo", "muestra"}:
    raise ValueError(f"QQP_MODO debe ser 'completo' o 'muestra', no {MODO!r}")
ES_MUESTRA = MODO == "muestra"

RAW_DIR = Path(os.getenv("QQP_RAW_DIR", ROOT / "data" / "raw"))
INTERIM_DIR = Path(os.getenv("QQP_INTERIM_DIR", ROOT / "data" / "interim"))
EXTRACTED_DIR = INTERIM_DIR / "csv"
SAMPLE_DIR = Path(os.getenv("QQP_SAMPLE_DIR", ROOT / "data" / "sample"))
SAMPLE_CSV_DIR = SAMPLE_DIR / "csv"
MAPPINGS_DIR = ROOT / "data" / "mappings"
MANUAL_MAPPINGS_DIR = MAPPINGS_DIR / "manual"
PROCESSED_DIR = Path(os.getenv("QQP_PROCESSED_DIR", ROOT / "data" / "processed"))
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"
TRANSFORM_DIR = ROOT / "transform"

# Directorio de CSV que consume la ingesta y base DuckDB de destino.
CSV_DIR = Path(os.getenv("QQP_CSV_DIR", SAMPLE_CSV_DIR if ES_MUESTRA else EXTRACTED_DIR))
_DEFAULT_DB = PROCESSED_DIR / ("qqp_muestra.duckdb" if ES_MUESTRA else "qqp.duckdb")
DUCKDB_PATH = Path(os.getenv("QQP_DUCKDB_PATH", _DEFAULT_DB))

# Salidas generadas. Los mapeos y reportes de los datos completos se versionan;
# los de la muestra van a un directorio ignorado para no sobrescribirlos.
SALIDAS_MUESTRA_DIR = PROCESSED_DIR / "muestra"
MAPPINGS_OUT_DIR = SALIDAS_MUESTRA_DIR / "mappings" if ES_MUESTRA else MAPPINGS_DIR
REPORTS_OUT_DIR = SALIDAS_MUESTRA_DIR / "reports" if ES_MUESTRA else REPORTS_DIR

ARCHIVE_SUFFIXES = {".zip", ".rar"}

# Límites de DuckDB. Con todos los hilos al 100% durante minutos, el equipo de
# desarrollo se apagó por protección térmica (ver docs/bitacora.md). Los valores
# por defecto coinciden con un runner estándar de GitHub Actions (4 vCPU, 16 GB).
DUCKDB_THREADS = int(os.getenv("QQP_DUCKDB_THREADS", "4"))
DUCKDB_MEMORY_LIMIT = os.getenv("QQP_DUCKDB_MEMORY_LIMIT", "8GB")
DUCKDB_TEMP_DIR = Path(os.getenv("QQP_DUCKDB_TEMP_DIR", INTERIM_DIR / "duckdb_tmp"))
