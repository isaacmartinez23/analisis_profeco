from pathlib import Path

from src.ingest import sniff
from src.ingest.csv_source import EXPECTED_COLUMNS


def test_detecta_utf8_con_bom(csv_utf8_bom: Path):
    s = sniff.sniff_file(csv_utf8_bom)
    assert s.has_bom
    assert s.encoding == "utf-8-sig"
    assert s.invalid_utf8_offset is None
    assert s.header == EXPECTED_COLUMNS
    assert s.delimiter == ","
    assert s.date_formats == {"%Y/%m/%d": 2}
    assert s.sample_bad_width == 0  # la coma dentro de comillas no rompe el ancho


def test_detecta_latin1_y_fecha_dia_mes(csv_latin1: Path):
    s = sniff.sniff_file(csv_latin1)
    assert not s.has_bom
    assert s.encoding == "cp1252"
    assert s.invalid_utf8_offset is not None
    assert s.date_formats == {"%d/%m/%Y": 1}


def test_crlf_partido_entre_bloques_se_cuenta_una_vez(tmp_path: Path, monkeypatch):
    path = tmp_path / "x.csv"
    path.write_bytes(b"a,b\r\n1,2\r\n")
    # Bloques de 4 bytes: "a,b\r" | "\n1,2" | "\r\n"
    monkeypatch.setattr(sniff, "CHUNK", 4)
    _, _, _, lines, crlf, _ = sniff._detect_encoding(path)
    assert lines == 2
    assert crlf == 2
