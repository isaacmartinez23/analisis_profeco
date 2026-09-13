from dataclasses import replace
from pathlib import Path

import duckdb
import pytest

from src.ingest.csv_source import read_csv_sql
from src.ingest.sniff import sniff_file


def _load(path: Path) -> list[tuple]:
    con = duckdb.connect()
    return con.execute(
        f"SELECT producto, presentacion, precio, fecha_registro, direccion FROM {read_csv_sql(path, sniff_file(path))}"
    ).fetchall()


def test_lee_utf8_con_bom_y_comillas(csv_utf8_bom: Path):
    rows = _load(csv_utf8_bom)
    assert len(rows) == 2
    assert rows[0][0] == "Aceite"  # el BOM no contamina el primer valor
    assert rows[1][1] == "Frasco Gotero 24 Ml. 1.000 G., Solución Gotas"
    assert all(isinstance(r[2], str) for r in rows)  # todo se lee como texto


def test_lee_latin1_sin_perder_acentos(csv_latin1: Path):
    rows = _load(csv_latin1)
    assert rows == [("Jitomate", "1 Kg. Granel. Saladette", "42", "16/05/2026", "Salida a México")]


def test_rechaza_esquema_inesperado(csv_utf8_bom: Path):
    s = sniff_file(csv_utf8_bom)
    with pytest.raises(ValueError, match="Esquema inesperado"):
        read_csv_sql(csv_utf8_bom, replace(s, header=[*s.header[:-1], "lng"]))
