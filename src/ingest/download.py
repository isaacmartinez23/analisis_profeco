"""Descarga de los archivos oficiales de PROFECO hacia ``data/raw``.

Fuentes versionadas en ``data/fuentes_profeco.csv`` (portal https://datos.profeco.gob.mx/datos_abiertos/qqp.php).
Los enlaces usan tokens opacos: un año nuevo requiere agregar su fila.

Reglas:

- Se descarga a ``data/interim/descargas`` y se verifica el nombre declarado por el servidor
  (``Content-Disposition``) y la firma del archivo (ZIP o RAR) antes de tocar ``data/raw``.
- Si el archivo no existe en ``data/raw``, se mueve ahí.
- Si existe con el mismo SHA-256, no se hace nada.
- Si existe con otro contenido, **no se sobrescribe** (los originales son inmutables): la versión nueva queda en
  ``data/interim/descargas`` y se reporta. Con ``--reemplazar`` (pensado para ejecuciones limpias en CI) se
  sustituye.

El servidor no publica ``ETag`` ni ``Last-Modified``, así que la única forma de detectar cambios es descargar y
comparar el hash.

Uso::

    python -m src.ingest.download
    python -m src.ingest.download --reemplazar
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from src import config

FUENTES = config.ROOT / "data" / "fuentes_profeco.csv"
DESCARGAS_DIR = config.INTERIM_DIR / "descargas"
FIRMAS = {".zip": b"PK\x03\x04", ".rar": b"Rar!\x1a\x07"}
AGENTE = "profeco-canasta-pipeline/0.1 (+https://github.com)"
CHUNK = 8 * 1024 * 1024


@dataclass
class Descarga:
    archivo: str
    url: str
    bytes: int
    sha256: str
    estado: str  # nuevo | sin_cambios | version_nueva_pendiente | reemplazado
    descargado_utc: str


def leer_fuentes(path: Path = FUENTES) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        fuentes = list(csv.DictReader(fh))
    for f in fuentes:
        if Path(f["archivo"]).suffix.lower() not in FIRMAS:
            raise ValueError(f"{path}: extensión no soportada en {f['archivo']}")
    return fuentes


def _nombre_declarado(content_disposition: str | None) -> str | None:
    if not content_disposition:
        return None
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
    return m.group(1) if m else None


def _descargar(
    url: str, destino: Path, reintentos: int = 3, abrir=urllib.request.urlopen
) -> tuple[str | None, str, int]:
    ultimo_error: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with abrir(peticion, timeout=120) as respuesta, destino.open("wb") as fh:
                nombre = _nombre_declarado(respuesta.headers.get("Content-Disposition"))
                digest = hashlib.sha256()
                total = 0
                while bloque := respuesta.read(CHUNK):
                    fh.write(bloque)
                    digest.update(bloque)
                    total += len(bloque)
            return nombre, digest.hexdigest(), total
        except OSError as exc:
            ultimo_error = exc
            if intento < reintentos:
                time.sleep(5 * intento)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo_error}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while bloque := fh.read(CHUNK):
            digest.update(bloque)
    return digest.hexdigest()


def descargar_fuente(
    fuente: dict[str, str], raw_dir: Path, reemplazar: bool, abrir=urllib.request.urlopen
) -> Descarga:
    archivo = fuente["archivo"]
    DESCARGAS_DIR.mkdir(parents=True, exist_ok=True)
    temporal = DESCARGAS_DIR / f"{archivo}.parcial"
    nombre, sha, total = _descargar(fuente["url"], temporal, abrir=abrir)

    if nombre and nombre != archivo:
        temporal.unlink(missing_ok=True)
        raise RuntimeError(
            f"{fuente['url']} entregó '{nombre}' en lugar de '{archivo}': revisa data/fuentes_profeco.csv"
        )
    with temporal.open("rb") as fh:
        firma = fh.read(8)
    if not firma.startswith(FIRMAS[Path(archivo).suffix.lower()]):
        temporal.unlink(missing_ok=True)
        raise RuntimeError(f"{archivo}: el contenido descargado no tiene firma {Path(archivo).suffix} válida")

    destino = raw_dir / archivo
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        shutil.move(temporal, destino)
        estado = "nuevo"
    elif _sha256(destino) == sha:
        temporal.unlink()
        estado = "sin_cambios"
    elif reemplazar:
        shutil.move(temporal, destino)
        estado = "reemplazado"
    else:
        pendiente = DESCARGAS_DIR / archivo
        shutil.move(temporal, pendiente)
        estado = "version_nueva_pendiente"
    return Descarga(
        archivo, fuente["url"], total, sha, estado, datetime.now(UTC).isoformat(timespec="seconds")
    )


def run(raw_dir: Path = config.RAW_DIR, reemplazar: bool = False) -> list[Descarga]:
    resultados = []
    for fuente in leer_fuentes():
        r = descargar_fuente(fuente, raw_dir, reemplazar)
        resultados.append(r)
        print(
            f"[download] {r.archivo}: {r.estado} ({r.bytes / 1e6:.1f} MB, sha256 {r.sha256[:12]}…)",
            flush=True,
        )
        if r.estado == "version_nueva_pendiente":
            print(
                f"[download] AVISO: PROFECO publicó una versión distinta de {r.archivo}. El original en data/raw no se "
                f"modificó; la nueva está en {DESCARGAS_DIR / r.archivo}. Reemplázala manualmente o usa --reemplazar.",
                flush=True,
            )
    DESCARGAS_DIR.mkdir(parents=True, exist_ok=True)
    (DESCARGAS_DIR / "registro_descargas.json").write_text(
        json.dumps([asdict(r) for r in resultados], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resultados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reemplazar", action="store_true", help="sustituye archivos de data/raw con contenido distinto"
    )
    run(reemplazar=parser.parse_args(argv).reemplazar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
