import io
import zipfile
from pathlib import Path

import pytest

from src.ingest import download


class RespuestaFalsa(io.BytesIO):
    def __init__(self, contenido: bytes, nombre: str | None):
        super().__init__(contenido)
        self.headers = {"Content-Disposition": f"inline; filename={nombre}"} if nombre else {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _zip_bytes(texto: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("01-2026_Q1.csv", texto)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _descargas_temporales(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "DESCARGAS_DIR", tmp_path / "descargas")


def _abrir(contenido: bytes, nombre: str | None = "QQP_2026.zip"):
    return lambda peticion, timeout: RespuestaFalsa(contenido, nombre)


FUENTE = {"archivo": "QQP_2026.zip", "url": "https://ejemplo/file.php?t=abc"}


def test_archivo_nuevo_se_mueve_a_raw(tmp_path: Path):
    raw = tmp_path / "raw"
    r = download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("a")))
    assert r.estado == "nuevo"
    assert (raw / "QQP_2026.zip").read_bytes() == _zip_bytes("a")


def test_mismo_contenido_no_cambia_nada(tmp_path: Path):
    raw = tmp_path / "raw"
    download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("a")))
    r = download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("a")))
    assert r.estado == "sin_cambios"


def test_version_distinta_no_sobrescribe_el_original(tmp_path: Path):
    raw = tmp_path / "raw"
    download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("original")))
    r = download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("nueva")))
    assert r.estado == "version_nueva_pendiente"
    assert (raw / "QQP_2026.zip").read_bytes() == _zip_bytes("original")
    assert (download.DESCARGAS_DIR / "QQP_2026.zip").read_bytes() == _zip_bytes("nueva")


def test_reemplazar_sustituye_con_la_version_nueva(tmp_path: Path):
    raw = tmp_path / "raw"
    download.descargar_fuente(FUENTE, raw, reemplazar=False, abrir=_abrir(_zip_bytes("original")))
    r = download.descargar_fuente(FUENTE, raw, reemplazar=True, abrir=_abrir(_zip_bytes("nueva")))
    assert r.estado == "reemplazado"
    assert (raw / "QQP_2026.zip").read_bytes() == _zip_bytes("nueva")


def test_rechaza_nombre_distinto_o_firma_invalida(tmp_path: Path):
    raw = tmp_path / "raw"
    with pytest.raises(RuntimeError, match="entregó"):
        download.descargar_fuente(FUENTE, raw, False, abrir=_abrir(_zip_bytes("a"), nombre="otro.zip"))
    with pytest.raises(RuntimeError, match="firma"):
        download.descargar_fuente(FUENTE, raw, False, abrir=_abrir(b"<html>error</html>"))
    assert not raw.exists() or not any(raw.iterdir())


def test_fuentes_versionadas_son_validas():
    fuentes = download.leer_fuentes()
    assert {f["archivo"] for f in fuentes} >= {"QQP_2024.rar", "QQP_2025.rar", "QQP_2026.zip"}
    assert all(f["url"].startswith("https://datos.profeco.gob.mx/") for f in fuentes)
