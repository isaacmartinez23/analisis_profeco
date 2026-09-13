"""Detección de propiedades físicas de cada CSV sin cargarlo en memoria.

No se asume nada del archivo: se lee en bloques y se determina BOM,
codificación válida, fin de línea, encabezado, delimitador, uso de comillas y
formato de fecha observado en una muestra de filas.
"""

from __future__ import annotations

import codecs
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

CHUNK = 8 * 1024 * 1024
BOM = codecs.BOM_UTF8

DATE_PATTERNS = {
    "%Y/%m/%d": re.compile(r"^\d{4}/\d{2}/\d{2}$"),
    "%d/%m/%Y": re.compile(r"^\d{2}/\d{2}/\d{4}$"),
    "%Y-%m-%d": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "%d-%m-%Y": re.compile(r"^\d{2}-\d{2}-\d{4}$"),
}


@dataclass
class FileSniff:
    path: str
    bytes: int
    has_bom: bool
    encoding: str
    invalid_utf8_offset: int | None
    lines: int
    crlf_lines: int
    delimiter: str
    header: list[str]
    quote_chars: int
    sample_rows: int
    sample_bad_width: int
    date_formats: dict[str, int] = field(default_factory=dict)


def _detect_encoding(path: Path) -> tuple[bool, str, int | None, int, int, int]:
    """Recorre el archivo completo validando UTF-8 y contando líneas y comillas."""
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    offset = 0
    invalid_at: int | None = None
    lines = crlf = quotes = 0
    prev_last = b""
    with path.open("rb") as fh:
        first = fh.read(3)
        has_bom = first == BOM
        fh.seek(0)
        while chunk := fh.read(CHUNK):
            lines += chunk.count(b"\n")
            # Un "\r\n" puede quedar partido entre dos bloques.
            crlf += chunk.count(b"\r\n") + (prev_last == b"\r" and chunk[:1] == b"\n")
            quotes += chunk.count(b'"')
            prev_last = chunk[-1:]
            if invalid_at is None:
                try:
                    decoder.decode(chunk)
                except UnicodeDecodeError as exc:
                    invalid_at = offset + exc.start
            offset += len(chunk)
    # Bytes 0x80-0xFF que no forman UTF-8 válido en texto en español corresponden a
    # Windows-1252 / Latin-1; la muestra se decodifica en modo estricto para confirmarlo.
    encoding = ("utf-8-sig" if has_bom else "utf-8") if invalid_at is None else "cp1252"
    return has_bom, encoding, invalid_at, lines, crlf, quotes


def sniff_file(path: Path, sample_rows: int = 20000) -> FileSniff:
    has_bom, encoding, invalid_at, lines, crlf, quotes = _detect_encoding(path)

    with path.open("r", encoding=encoding, errors="strict", newline="") as fh:
        head = fh.read(64 * 1024)
        dialect = csv.Sniffer().sniff(head.splitlines()[0])
        fh.seek(0)
        reader = csv.reader(fh, delimiter=dialect.delimiter)
        header = [h.strip() for h in next(reader)]
        width = len(header)
        date_idx = next((i for i, h in enumerate(header) if "fecha" in h.lower()), None)
        bad_width = 0
        formats: dict[str, int] = {}
        n = 0
        for row in reader:
            n += 1
            if len(row) != width:
                bad_width += 1
            elif date_idx is not None:
                value = row[date_idx].strip()
                fmt = next((f for f, rx in DATE_PATTERNS.items() if rx.match(value)), "otro")
                formats[fmt] = formats.get(fmt, 0) + 1
            if n >= sample_rows:
                break

    return FileSniff(
        path=str(path),
        bytes=path.stat().st_size,
        has_bom=has_bom,
        encoding=encoding,
        invalid_utf8_offset=invalid_at,
        lines=lines,
        crlf_lines=crlf,
        delimiter=dialect.delimiter,
        header=header,
        quote_chars=quotes,
        sample_rows=n,
        sample_bad_width=bad_width,
        date_formats=formats,
    )


def context_at(path: Path, offset: int, width: int = 60) -> str:
    """Devuelve bytes alrededor de un desplazamiento, útil para documentar anomalías."""
    with path.open("rb") as fh:
        fh.seek(max(0, offset - width))
        return repr(fh.read(2 * width))
