"""Fixtures compartidas: CSV sintéticos con las variantes reales observadas en QQP."""

from __future__ import annotations

from pathlib import Path

import pytest

HEADER = (
    "producto,presentacion,marca,categoria,catalogo,precio,fecha_registro,cadena_comercial,giro,"
    "nombre_comercial,direccion,estado,municipio,latitud,longitud"
)

ROWS_ISO = [
    "Aceite,Botella 850 Ml. Vegetal,Ave,Aceites y Grasas,Basicos,28,2026/01/02,Chedraui,Supermercado,"
    "Chedraui Sucursal Ags,Blvd. José Ma. Chávez 1809,Aguascalientes,Aguascalientes,21.854349,-102.294259",
    'A.s.cor,"Frasco Gotero 24 Ml. 1.000 G., Solución Gotas",S/M,Medicamentos,Medicamentos,399,2025/12/17,'
    "Bodega Aurrera,Supermercado,Bodega Aurrera,Convención 1101,Aguascalientes,Aguascalientes,21.88,-102.31",
]

ROWS_DMY = [
    "Jitomate,1 Kg. Granel. Saladette,S/M,Hortalizas Frescas,Frutas y Legumbres,42,16/05/2026,Central de Abasto,"
    "Central de Abasto,Central de Abasto,Salida a México,Aguascalientes,Aguascalientes,21.832072,-102.292976",
]


HEADER_ADICIONALES = HEADER + ",folio,cv_producto,cv_marca"

ROWS_ADICIONALES = [
    "Jitomate,1 Kg. Granel. Saladette/huaje o Tomate Saladette/huaje. Primera,S/M,Hortalizas Frescas,"
    "Frutas y Legumbres,29,2026/06/01,Central de Abasto,Central de Abasto,Central de Abasto,Salida a México,"
    "Aguascalientes,Aguascalientes,21.832072,-102.292976,20160,869,5",
]


@pytest.fixture
def csv_columnas_adicionales(tmp_path: Path) -> Path:
    """Formato de 2026-06: UTF-8 con BOM, CRLF, fechas yyyy/mm/dd y tres columnas no documentadas al final."""
    path = tmp_path / "QQP_2026" / "06-2026_Q1.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\xef\xbb\xbf" + ("\r\n".join([HEADER_ADICIONALES, *ROWS_ADICIONALES]) + "\r\n").encode("utf-8")
    )
    return path


@pytest.fixture
def csv_utf8_bom(tmp_path: Path) -> Path:
    """Formato de 2024-01 a 2026-04: UTF-8 con BOM, CRLF, fechas yyyy/mm/dd."""
    path = tmp_path / "QQP_2026" / "01-2026_Q1.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + ("\r\n".join([HEADER, *ROWS_ISO]) + "\r\n").encode("utf-8"))
    return path


@pytest.fixture
def csv_latin1(tmp_path: Path) -> Path:
    """Formato de 2026-05: Latin-1 sin BOM, CRLF, fechas dd/mm/yyyy."""
    path = tmp_path / "QQP_2026" / "05-2026_Q2.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\r\n".join([HEADER, *ROWS_DMY]) + "\r\n").encode("latin-1"))
    return path
