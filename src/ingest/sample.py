"""Genera una muestra pequeña, reproducible y versionable de los CSV reales.

La muestra conserva el formato físico de cada archivo de origen (codificación,
BOM, fin de línea CRLF, formato de fecha), de modo que la ingesta, las pruebas y
GitHub Actions ejercitan las mismas rutas de lectura que los datos completos.

Criterios deterministas (sin aleatoriedad):

1. Archivos: la quincena 2025-12 Q2 (estados sin acento) y las cuatro quincenas
   de abril-mayo 2026 (cambio de codificación, fecha y caracteres perdidos).
2. Municipios: Venustiano Carranza (CDMX) y Santiago de Querétaro, con las 4
   cadenas de referencia y cambio de acentos en el nombre del estado.
3. Filas: todas las de los productos candidatos a canasta en esos municipios,
   un 3% determinista (por hash) del resto de filas de esos municipios y un 10%
   determinista de las filas con caracteres perdidos (`?`) de cualquier municipio.

Uso::

    python -m src.ingest.sample     # requiere los CSV extraídos (data/interim/csv)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect
from src.ingest.csv_source import EXPECTED_COLUMNS, read_csv_sql, sql_literal
from src.ingest.extract import crc32_file
from src.ingest.sniff import sniff_file
from src.normalize.text import llave

ARCHIVOS = [
    "QQP_2025/12-2025_02.csv",
    "QQP_2026/04-2026_Q1.csv",
    "QQP_2026/04-2026_Q2.csv",
    "QQP_2026/05-2026_Q1.csv",
    "QQP_2026/05-2026_Q2.csv",
]
MUNICIPIOS = [("CIUDAD DE MEXICO", "VENUSTIANO CARRANZA"), ("QUERETARO", "SANTIAGO DE QUERETARO")]
CATALOGOS_CANASTA = ["Basicos", "Frutas y Legumbres", "Pacic"]
PCT_RESTO = 3
PCT_CORRUPTAS = 10

ESCRITURA = {"utf-8-sig": "utf-8-sig", "utf-8": "utf-8", "cp1252": "latin-1"}


def _sql_filtro(source: str, productos: list[str]) -> str:
    cols = ", ".join(EXPECTED_COLUMNS)
    geo = " OR ".join(
        f"(upper(strip_accents(trim(estado))) = {sql_literal(e)} AND upper(strip_accents(trim(municipio))) = {sql_literal(m)})"
        for e, m in MUNICIPIOS
    )
    en_canasta = (
        f"upper(strip_accents(trim(producto))) IN ({', '.join(sql_literal(p) for p in productos)}) "
        f"AND catalogo IN ({', '.join(sql_literal(c) for c in CATALOGOS_CANASTA)})"
    )
    corrupta = "concat_ws('|', producto, marca, giro, nombre_comercial, direccion) LIKE '%?%'"
    return f"""
    WITH src AS (SELECT *, hash({cols}) AS h, ({geo}) AS en_geo FROM {source})
    SELECT {cols} FROM src WHERE en_geo AND {en_canasta}
    UNION ALL
    SELECT {cols} FROM src WHERE en_geo AND NOT ({en_canasta}) AND h % 100 < {PCT_RESTO}
    UNION ALL
    SELECT {cols} FROM src WHERE NOT en_geo AND {corrupta} AND h % 100 < {PCT_CORRUPTAS}
    ORDER BY ALL
    """


def run(source_dir: Path = config.EXTRACTED_DIR, out_dir: Path = config.SAMPLE_CSV_DIR) -> dict:
    productos = [
        llave(p) for p in pd.read_csv(config.MAPPINGS_DIR / "canasta_candidatos_v0.csv")["producto_generico"]
    ]
    resumen = {
        "criterios": __doc__.split("Criterios deterministas (sin aleatoriedad):")[1].split("Uso::")[0].strip()
    }
    resumen["archivos"] = []
    with connect(":memory:") as con:
        for nombre in ARCHIVOS:
            src_path = source_dir / nombre
            if not src_path.exists():
                raise FileNotFoundError(
                    f"Falta {src_path}; ejecuta primero la extracción de los datos completos."
                )
            sniff = sniff_file(src_path)
            rows = con.execute(_sql_filtro(read_csv_sql(src_path, sniff), productos)).fetchall()
            dest = out_dir / nombre
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", encoding=ESCRITURA[sniff.encoding], newline="") as fh:
                writer = csv.writer(fh, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
                writer.writerow(EXPECTED_COLUMNS)
                writer.writerows(rows)
            resumen["archivos"].append(
                {
                    "archivo": nombre,
                    "filas": len(rows),
                    "bytes": dest.stat().st_size,
                    "crc32": crc32_file(dest),
                    "codificacion": sniff.encoding,
                }
            )
            print(f"[sample] {nombre}: {len(rows):,} filas ({dest.stat().st_size / 1e6:.2f} MB)", flush=True)
    (out_dir.parent / "muestra.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resumen


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
