import hashlib
import zipfile
from pathlib import Path

import pytest

from src.ingest import extract


@pytest.fixture
def raw_zip(tmp_path: Path, csv_utf8_bom: Path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "QQP_2026.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_utf8_bom, "01-2026_Q1.csv")
        zf.writestr("LEAME.txt", "no es csv")
    return archive


def test_extrae_verifica_y_no_modifica_originales(tmp_path: Path, raw_zip: Path):
    before = hashlib.sha256(raw_zip.read_bytes()).hexdigest()
    out = tmp_path / "interim" / "csv"

    manifest = extract.run(raw_dir=raw_zip.parent, out_dir=out)

    target = out / "QQP_2026" / "01-2026_Q1.csv"
    assert target.exists()
    [archivo] = manifest["archivos"]
    assert archivo["sha256"] == before
    assert [m["estado"] for m in archivo["csv"]] == ["extraido"]  # solo CSV, se ignora LEAME.txt
    assert hashlib.sha256(raw_zip.read_bytes()).hexdigest() == before


def test_segunda_ejecucion_no_reextrae(tmp_path: Path, raw_zip: Path):
    out = tmp_path / "interim" / "csv"
    extract.run(raw_dir=raw_zip.parent, out_dir=out)
    manifest = extract.run(raw_dir=raw_zip.parent, out_dir=out, verify_crc=True)
    assert [m["estado"] for m in manifest["archivos"][0]["csv"]] == ["existente"]


def test_reextrae_si_el_csv_esta_corrupto(tmp_path: Path, raw_zip: Path):
    out = tmp_path / "interim" / "csv"
    extract.run(raw_dir=raw_zip.parent, out_dir=out)
    target = out / "QQP_2026" / "01-2026_Q1.csv"
    target.write_bytes(target.read_bytes()[:-5])
    manifest = extract.run(raw_dir=raw_zip.parent, out_dir=out)
    assert [m["estado"] for m in manifest["archivos"][0]["csv"]] == ["extraido"]


def test_falla_si_no_hay_archivos(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        extract.run(raw_dir=tmp_path, out_dir=tmp_path / "out")
