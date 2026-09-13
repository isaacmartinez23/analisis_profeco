"""Punto de entrada único del pipeline (equivalente multiplataforma del Makefile).

Uso::

    python -m src.cli pipeline            # datos completos
    python -m src.cli --muestra pipeline  # muestra versionada en data/sample (no requiere data/raw)
    python -m src.cli <paso>              # setup | download | inspect | ingest | quality | normalize | dbt-run |
                                          # dbt-test | quality-marts | validate | resultados | publish | alertas |
                                          # sample | profile | seleccion-canasta | test | clean

Orden de `pipeline`: inspect → ingest → quality → normalize → dbt-run → dbt-test → quality-marts → validate →
resultados → publish → alertas. `download` (datos oficiales de PROFECO) se usa en CI; en local los archivos se
colocan a mano en data/raw. Cualquier fallo detiene la ejecución con código distinto de cero y dispara una alerta;
la publicación solo ocurre si todo lo anterior pasó y hay credenciales configuradas.
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
        # En Windows dbt abriría los YAML con cp1252 y leería mal los acentos de las descripciones.
        "PYTHONUTF8": "1",
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
    """Extrae los comprimidos (modo completo) y valida formato y esquema de cada CSV.

    Las columnas adicionales ya revisadas (D-037) se reportan como aviso; cualquier otro cambio detiene el pipeline.
    """
    from src import config
    from src.ingest import extract
    from src.ingest.csv_source import columnas_adicionales
    from src.ingest.load import listar_csv
    from src.ingest.sniff import sniff_file

    if not config.ES_MUESTRA:
        extract.run()
    problemas, avisos = [], []
    for path in listar_csv(config.CSV_DIR):
        s = sniff_file(path, sample_rows=2000)
        try:
            if extra := columnas_adicionales(s.header, path.name):
                avisos.append(f"{path.name}: columnas adicionales conocidas {extra}")
        except ValueError:
            problemas.append(f"{path.name}: encabezado distinto {s.header}")
        if s.sample_bad_width:
            problemas.append(f"{path.name}: {s.sample_bad_width} filas con número de columnas incorrecto")
    if avisos:
        print("[inspect] aviso (se conservan en raw, no se modelan):\n  " + "\n  ".join(avisos))
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


def paso_validate() -> None:
    from src.analysis import validacion

    validacion.run()


def paso_seleccion_canasta() -> None:
    from src.analysis import seleccion_canasta

    seleccion_canasta.run()


def paso_resultados() -> None:
    from src.analysis import resultados

    resultados.run()


def paso_publish() -> None:
    from src.publish import postgres

    postgres.run()


def paso_download() -> None:
    from src.ingest import download

    download.run(reemplazar=os.getenv("QQP_DESCARGA_REEMPLAZAR") == "1")


def paso_alertas() -> None:
    from src import alertas

    alertas.run(estado="exito")


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
    "download": paso_download,
    "inspect": paso_inspect,
    "ingest": paso_ingest,
    "quality": paso_quality,
    "normalize": paso_normalize,
    "dbt-run": paso_dbt_run,
    "dbt-test": paso_dbt_test,
    "quality-marts": paso_quality_marts,
    "validate": paso_validate,
    "resultados": paso_resultados,
    "seleccion-canasta": paso_seleccion_canasta,
    "publish": paso_publish,
    "alertas": paso_alertas,
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
    "validate",
    "resultados",
    "publish",
    "alertas",
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
    _cargar_env_local()
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
        try:
            PASOS[nombre]()
        except BaseException as exc:
            if nombre != "alertas" and not isinstance(exc, KeyboardInterrupt):
                _notificar_fallo(nombre, exc)
            raise
        print(f"=== {nombre} ok ({time.time() - t0:.0f}s) ===", flush=True)
    if args.paso == "pipeline":
        print(f"\nPipeline completo en {time.time() - inicio:.0f}s", flush=True)
    return 0


def _cargar_env_local() -> None:
    """Carga `.env` si existe (conveniencia local). No sobrescribe variables ya definidas, como los secretos de CI."""
    from dotenv import load_dotenv

    ruta = Path(__file__).resolve().parents[1] / ".env"
    if ruta.exists():
        load_dotenv(ruta, override=False)


def _notificar_fallo(paso: str, exc: BaseException) -> None:
    try:
        from src import alertas

        alertas.run(estado="fallo", paso=paso, detalle=f"{type(exc).__name__}: {exc}"[:500])
    except Exception as error_alerta:  # nunca ocultar el error original
        print(f"[alertas] no se pudo generar la alerta: {error_alerta}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
