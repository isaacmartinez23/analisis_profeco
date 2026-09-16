from pathlib import Path

import duckdb
import pytest

from src.ingest import load
from tests.conftest import HEADER, ROWS_ISO


def _conteos(db: Path) -> tuple[int, int, list[str]]:
    with duckdb.connect(str(db), read_only=True) as con:
        filas = con.execute("SELECT count(*) FROM raw.qqp_precios").fetchone()[0]
        archivos = con.execute("SELECT count(*) FROM raw.archivos").fetchone()[0]
        estados = [
            r[0] for r in con.execute("SELECT estado FROM raw.cargas ORDER BY iniciada_utc").fetchall()
        ]
    return filas, archivos, estados


def test_segunda_ejecucion_no_duplica(tmp_path: Path, csv_utf8_bom: Path, csv_latin1: Path):
    db = tmp_path / "qqp.duckdb"
    primera = load.run(base_dir=tmp_path, db_path=db)
    segunda = load.run(base_dir=tmp_path, db_path=db)

    assert [r.estado for r in primera] == ["cargado", "cargado"]
    assert [r.estado for r in segunda] == ["omitido", "omitido"]
    assert _conteos(db) == (3, 2, ["exitosa", "exitosa"])


def test_archivo_modificado_se_reemplaza_sin_duplicar(tmp_path: Path, csv_utf8_bom: Path):
    db = tmp_path / "qqp.duckdb"
    load.run(base_dir=tmp_path, db_path=db)
    csv_utf8_bom.write_bytes(b"\xef\xbb\xbf" + ("\r\n".join([HEADER, ROWS_ISO[0]]) + "\r\n").encode("utf-8"))

    [resultado] = load.run(base_dir=tmp_path, db_path=db)

    assert (resultado.estado, resultado.filas, resultado.filas_previas) == ("reemplazado", 1, 2)
    assert _conteos(db)[:2] == (1, 1)


def test_columnas_adicionales_se_conservan_y_migran_una_base_existente(
    tmp_path: Path, csv_utf8_bom: Path, csv_columnas_adicionales: Path
):
    db = tmp_path / "qqp.duckdb"
    csv_columnas_adicionales.rename(csv_columnas_adicionales.with_suffix(".pendiente"))
    load.run(base_dir=tmp_path, db_path=db)
    with duckdb.connect(str(db)) as con:  # simula una base creada antes de existir las columnas adicionales
        for c in ("folio", "cv_producto", "cv_marca"):
            con.execute(f"ALTER TABLE raw.qqp_precios DROP COLUMN {c}")
        con.execute("ALTER TABLE raw.archivos DROP COLUMN columnas_adicionales")
    csv_columnas_adicionales.with_suffix(".pendiente").rename(csv_columnas_adicionales)

    estados = [r.estado for r in load.run(base_dir=tmp_path, db_path=db)]

    assert estados == ["omitido", "cargado"]  # 01-2026_Q1 ya estaba; 06-2026_Q1 es nuevo
    with duckdb.connect(str(db), read_only=True) as con:
        filas = con.execute(
            "SELECT archivo_origen, producto, folio, cv_producto, cv_marca, cargado_utc IS NOT NULL "
            "FROM raw.qqp_precios ORDER BY archivo_origen, producto"
        ).fetchall()
        archivos = dict(con.execute("SELECT archivo, columnas_adicionales FROM raw.archivos").fetchall())
    assert filas == [
        ("QQP_2026/01-2026_Q1.csv", "A.s.cor", None, None, None, True),
        ("QQP_2026/01-2026_Q1.csv", "Aceite", None, None, None, True),
        ("QQP_2026/06-2026_Q1.csv", "Jitomate", "20160", "869", "5", True),
    ]
    assert archivos == {
        "QQP_2026/01-2026_Q1.csv": None,
        "QQP_2026/06-2026_Q1.csv": "folio,cv_producto,cv_marca",
    }


def test_conteo_inconsistente_revierte_la_carga(tmp_path: Path, csv_utf8_bom: Path):
    db = tmp_path / "qqp.duckdb"
    # Un salto de línea dentro de un campo entrecomillado: 3 líneas físicas de datos, 2 filas CSV.
    fila_multilinea = ROWS_ISO[0].replace("Botella 850 Ml. Vegetal", '"Botella 850 Ml.\r\nVegetal"')
    csv_utf8_bom.write_bytes(
        b"\xef\xbb\xbf" + ("\r\n".join([HEADER, fila_multilinea, ROWS_ISO[1]]) + "\r\n").encode("utf-8")
    )

    with pytest.raises(RuntimeError, match="líneas de datos"):
        load.run(base_dir=tmp_path, db_path=db)

    filas, archivos, estados = _conteos(db)
    assert (filas, archivos, estados) == (0, 0, ["fallida"])
