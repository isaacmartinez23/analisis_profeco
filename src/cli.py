"""Punto de entrada único del pipeline (equivalente multiplataforma del Makefile).

Uso::

    python -m src.cli pipeline            # datos completos
    python -m src.cli --muestra pipeline  # muestra versionada en data/sample (no requiere data/raw)
    python -m src.cli <paso>              # setup | inspect | ingest | quality | normalize | dbt-run |
                                          # dbt-test | quality-marts | publish | sample | profile | test | clean

Orden de `pipeline`: inspect → ingest → quality → normalize → dbt-run → dbt-test → quality-marts → publish.
Cualquier fallo detiene la ejecución con código distinto de cero; la publicación solo ocurre si todo lo
anterior pasó y hay credenciales configuradas.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path


def _configurar_entorno(muestra: bool) -> None:
    if muestra:
        os.environ["QQP_MODO"] = "muestra"


def _ejecutable_dbt() -> str:
    carpeta = Path(sys.executable).parent
    for nombre in ("dbt.exe", "dbt"):
        if (carpeta / nombre).exists():
            return str(carpeta / nombre)
    if encontrado := shutil.which("dbt"):
        return encontrado
    raise SystemExit("No se encontró dbt. Instala dependencias: pip install -r requirements.txt")


def _dbt(*args: str) -> None:
    """Ejecuta dbt en un subproceso: libera la conexión a DuckDB y la memoria al terminar."""
    from src import config

    config.DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    entorno = {
        **os.environ,
        "QQP_DUCKDB_PATH": str(config.DUCKDB_PATH.resolve()),
        "QQP_DUCKDB_THREADS": str(config.DUCKDB_THREADS),
        "QQP_DUCKDB_MEMORY_LIMIT": config.DUCKDB_MEMORY_LIMIT,
        "QQP_DUCKDB_TEMP_DIR": config.DUCKDB_TEMP_DIR.resolve().as_posix(),
    }
    _asegurar_profiles()
    comun = ["--project-dir", str(config.TRANSFORM_DIR), "--profiles-dir", str(config.TRANSFORM_DIR)]
    resultado = subprocess.run([_ejecutable_dbt(), *args, *comun], env=entorno)
    if resultado.returncode != 0:
        raise SystemExit(f"dbt {' '.join(args)} falló (código {resultado.returncode})")


def _asegurar_profiles() -> None:
    from src import config

    destino = config.TRANSFORM_DIR / "profiles.yml"
    if not destino.exists():
        shutil.copyfile(config.TRANSFORM_DIR / "profiles.yml.example", destino)
        print(f"[setup] creado {destino} a partir de profiles.yml.example")


def paso_setup() -> None:
    from src import config

    _asegurar_profiles()
    for d in (config.PROCESSED_DIR, config.DUCKDB_TEMP_DIR, config.RAW_DIR):
        d.mkdir(parents=True, exist_ok=True)
    print(f"[setup] modo={config.MODO} · DuckDB={config.DUCKDB_PATH} · CSV={config.CSV_DIR}")


def paso_inspect() -> None:
    """Extrae los comprimidos (modo completo) y valida formato y esquema de cada CSV."""
    from src import config
    from src.ingest import extract
    from src.ingest.csv_source import EXPECTED_COLUMNS
    from src.ingest.load import listar_csv
    from src.ingest.sniff import sniff_file

    if not config.ES_MUESTRA:
        extract.run()
    problemas = []
    for path in listar_csv(config.CSV_DIR):
        s = sniff_file(path, sample_rows=2000)
        if s.header != EXPECTED_COLUMNS:
            problemas.append(f"{path.name}: encabezado distinto {s.header}")
        if s.sample_bad_width:
            problemas.append(f"{path.name}: {s.sample_bad_width} filas con número de columnas incorrecto")
    if problemas:
        raise SystemExit("[inspect] cambios de esquema detectados:\n  " + "\n  ".join(problemas))
    print(f"[inspect] esquema válido en {len(listar_csv(config.CSV_DIR))} archivos de {config.CSV_DIR}")


def paso_ingest() -> None:
    from src.ingest import load

    load.run()


def paso_quality() -> None:
    from src.quality import checks

    checks.run(etapa="raw")


def paso_normalize() -> None:
    from src.normalize import build

    build.run()


def paso_dbt_run() -> None:
    _dbt("seed")
    _dbt("run")


def paso_dbt_test() -> None:
    _dbt("test")


def paso_quality_marts() -> None:
    from src.quality import checks

    checks.run(etapa="marts")


def paso_publish() -> None:
    faltantes = [
        v
        for v in (
            "SUPABASE_DB_HOST",
            "SUPABASE_DB_PORT",
            "SUPABASE_DB_NAME",
            "SUPABASE_DB_USER",
            "SUPABASE_DB_PASSWORD",
        )
        if not os.getenv(v)
    ]
    if faltantes:
        print(
            "[publish] Supabase no está configurado (faltan "
            + ", ".join(faltantes)
            + "). Los marts quedaron creados y validados en DuckDB; no se publicó nada."
        )
        return
    raise SystemExit("[publish] La publicación a Supabase se implementa en la Fase 3.")


def paso_sample() -> None:
    from src.ingest import sample

    sample.run()


def paso_profile() -> None:
    from src.ingest import profile, profile_report

    profile.run()
    profile_report.write()


def paso_test() -> None:
    subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
    subprocess.run([sys.executable, "-m", "ruff", "check", "."], check=True)


def paso_clean() -> None:
    from src import config

    objetivos = [config.DUCKDB_PATH, config.DUCKDB_PATH.with_suffix(".duckdb.wal"), config.DUCKDB_TEMP_DIR]
    objetivos += [config.TRANSFORM_DIR / d for d in ("target", "logs", "dbt_packages")]
    if config.ES_MUESTRA:
        objetivos.append(config.SALIDAS_MUESTRA_DIR)
    for obj in objetivos:
        if obj.is_dir():
            shutil.rmtree(obj)
            print(f"[clean] eliminado {obj}")
        elif obj.exists():
            obj.unlink()
            print(f"[clean] eliminado {obj}")


PASOS: dict[str, Callable[[], None]] = {
    "setup": paso_setup,
    "inspect": paso_inspect,
    "ingest": paso_ingest,
    "quality": paso_quality,
    "normalize": paso_normalize,
    "dbt-run": paso_dbt_run,
    "dbt-test": paso_dbt_test,
    "quality-marts": paso_quality_marts,
    "publish": paso_publish,
    "sample": paso_sample,
    "profile": paso_profile,
    "test": paso_test,
    "clean": paso_clean,
}

PIPELINE = [
    "setup",
    "inspect",
    "ingest",
    "quality",
    "normalize",
    "dbt-run",
    "dbt-test",
    "quality-marts",
    "publish",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline de precios PROFECO QQP")
    parser.add_argument("--muestra", action="store_true", help="usa la muestra versionada en data/sample")
    parser.add_argument("paso", choices=[*PASOS, "pipeline"])
    parser.add_argument(
        "--desde",
        choices=PIPELINE,
        help="reanuda `pipeline` desde este paso (p. ej. tras corregir un modelo)",
    )
    args = parser.parse_args(argv)
    _configurar_entorno(args.muestra)

    pasos = PIPELINE if args.paso == "pipeline" else [args.paso]
    if args.desde:
        if args.paso != "pipeline":
            parser.error("--desde solo aplica a `pipeline`")
        pasos = PIPELINE[PIPELINE.index(args.desde) :]
    inicio = time.time()
    for nombre in pasos:
        t0 = time.time()
        print(f"\n=== {nombre} ===", flush=True)
        PASOS[nombre]()
        print(f"=== {nombre} ok ({time.time() - t0:.0f}s) ===", flush=True)
    if args.paso == "pipeline":
        print(f"\nPipeline completo en {time.time() - inicio:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
