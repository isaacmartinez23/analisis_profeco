"""Extracción reproducible de los archivos comprimidos de PROFECO.

Los archivos de ``data/raw/`` son inmutables: solo se leen. Cada CSV contenido
se extrae a ``data/interim/csv/<archivo>/<csv>`` y se verifica contra el tamaño
y el CRC32 declarados en el propio archivo comprimido. Una segunda ejecución
omite los CSV que ya existen íntegros.

Se genera ``data/interim/manifest_extraccion.json`` con el SHA-256 de cada
archivo original, lo que permite comprobar después que ``data/raw/`` no cambió.

Uso::

    python -m src.ingest.extract            # extrae lo que falte
    python -m src.ingest.extract --verify   # además recalcula CRC32 de lo existente
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
import zlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import rarfile

from src import config

CHUNK = 8 * 1024 * 1024


@dataclass
class Member:
    archive: str
    member: str
    target: str
    size: int
    crc32: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def crc32_file(path: Path) -> int:
    crc = 0
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


def list_members(archive: Path, out_dir: Path) -> list[Member]:
    """Lista los CSV de un .zip o .rar sin extraerlos."""
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as zf:
            infos = [(i.filename, i.file_size, i.CRC) for i in zf.infolist() if not i.is_dir()]
    else:
        with rarfile.RarFile(archive) as rf:
            infos = [(i.filename, i.file_size, i.CRC) for i in rf.infolist() if not i.is_dir()]

    members = []
    for name, size, crc in infos:
        if not name.lower().endswith(".csv"):
            continue
        target = out_dir / archive.stem / Path(name).name
        members.append(Member(archive.name, name, str(target), size, crc & 0xFFFFFFFF))
    return members


def _rar_tool() -> list[str]:
    """Devuelve el comando base para extraer RAR con la herramienta disponible."""
    for exe in ("unrar", "7z", "7zz"):
        if path := shutil.which(exe):
            return [path]
    for exe in ("bsdtar", "tar"):
        path = shutil.which(exe)
        if path and "bsdtar" in subprocess.run([path, "--version"], capture_output=True, text=True).stdout:
            return [path]
    raise RuntimeError(
        "No se encontró herramienta para extraer RAR. Instala una de: "
        "unrar, 7-Zip (7z) o bsdtar (libarchive-tools)."
    )


def _extract_rar(archive: Path, members: list[Member], tmp: Path) -> None:
    tool = _rar_tool()
    name = Path(tool[0]).stem.lower()
    names = [m.member for m in members]
    if name == "unrar":
        cmd = [*tool, "x", "-o+", "-idq", str(archive), *names, str(tmp) + "/"]
    elif name in {"7z", "7zz"}:
        cmd = [*tool, "x", "-y", f"-o{tmp}", str(archive), *names]
    else:
        cmd = [*tool, "-xf", str(archive), "-C", str(tmp), *names]
    subprocess.run(cmd, check=True)


def _extract_zip(archive: Path, members: list[Member], tmp: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for m in members:
            dest = tmp / m.member
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m.member) as src, dest.open("wb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)


def is_intact(m: Member, verify_crc: bool) -> bool:
    target = Path(m.target)
    if not target.exists() or target.stat().st_size != m.size:
        return False
    return not verify_crc or crc32_file(target) == m.crc32


def extract_archive(archive: Path, out_dir: Path, verify_crc: bool = False) -> list[dict]:
    members = list_members(archive, out_dir)
    pending = [m for m in members if not is_intact(m, verify_crc)]
    status = {m.member: "existente" for m in members}

    if pending:
        tmp_root = out_dir / ".tmp"
        tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as tmp_name:
            tmp = Path(tmp_name)
            if archive.suffix.lower() == ".zip":
                _extract_zip(archive, pending, tmp)
            else:
                _extract_rar(archive, pending, tmp)
            for m in pending:
                extracted = tmp / m.member
                crc = crc32_file(extracted)
                if extracted.stat().st_size != m.size or crc != m.crc32:
                    raise RuntimeError(f"Integridad fallida en {archive.name}:{m.member}")
                Path(m.target).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(extracted), m.target)
                status[m.member] = "extraido"

    return [{**asdict(m), "estado": status[m.member]} for m in members]


def run(
    raw_dir: Path = config.RAW_DIR, out_dir: Path = config.EXTRACTED_DIR, verify_crc: bool = False
) -> dict:
    archives = sorted(p for p in raw_dir.iterdir() if p.suffix.lower() in config.ARCHIVE_SUFFIXES)
    if not archives:
        raise FileNotFoundError(f"No hay archivos .zip/.rar en {raw_dir}")

    manifest = {"generado_utc": datetime.now(UTC).isoformat(timespec="seconds"), "archivos": []}
    for archive in archives:
        print(f"[extract] {archive.name} ...", flush=True)
        members = extract_archive(archive, out_dir, verify_crc)
        manifest["archivos"].append(
            {
                "archivo": archive.name,
                "bytes": archive.stat().st_size,
                "sha256": sha256_file(archive),
                "csv": members,
            }
        )
        nuevos = sum(m["estado"] == "extraido" for m in members)
        print(f"[extract] {archive.name}: {len(members)} CSV ({nuevos} extraídos)", flush=True)

    manifest_path = out_dir.parent / "manifest_extraccion.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true", help="recalcula CRC32 de los CSV existentes")
    args = parser.parse_args(argv)
    run(verify_crc=args.verify)
    return 0


if __name__ == "__main__":
    sys.exit(main())
