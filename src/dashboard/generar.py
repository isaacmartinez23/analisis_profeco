"""Genera el dashboard HTML a partir de DuckDB.

El resultado es un único archivo sin dependencias de servidor: la plantilla (``plantilla.html``) con los datos
de ``datos.extraer`` incrustados como JSON. Se abre directamente en el navegador, se publica como página estática
(GitHub Pages) y no necesita credenciales.

Uso::

    python -m src.cli dashboard                        # reports/dashboard/index.html
    python -m src.dashboard.generar --fragmento RUTA   # además, versión sin <html>/<head>/<body> para incrustar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src import config
from src.dashboard import datos as datos_dashboard
from src.db import connect

PLANTILLA = Path(__file__).with_name("plantilla.html")
MARCA_DATOS = "__DATOS_QQP__"
MARCA_CUERPO = "<!-- cuerpo -->"


def destino_predeterminado() -> Path:
    return config.REPORTS_OUT_DIR / "dashboard" / "index.html"


def renderizar(datos: dict[str, Any], completo: bool = True, plantilla: str | None = None) -> str:
    """Inserta los datos en la plantilla.

    ``completo=False`` devuelve el fragmento (título, estilos, marcado y script) para anfitriones que ya aportan
    el esqueleto del documento.
    """
    plantilla = plantilla if plantilla is not None else PLANTILLA.read_text(encoding="utf-8")
    for marca in (MARCA_DATOS, MARCA_CUERPO):
        if plantilla.count(marca) != 1:
            raise ValueError(f"[dashboard] la plantilla debe contener {marca!r} exactamente una vez")
    # `<` escapado: ningún texto de los datos puede cerrar la etiqueta <script> que los contiene.
    carga = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = plantilla.replace(MARCA_DATOS, carga)
    cabeza, cuerpo = html.split(MARCA_CUERPO)
    if not completo:
        return cabeza + cuerpo
    return (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"{cabeza}</head>\n<body>\n{cuerpo}</body>\n</html>\n"
    )


def run(destino: Path | None = None, fragmento: Path | None = None) -> Path:
    destino = destino or destino_predeterminado()
    con = connect(read_only=True)
    try:
        datos = datos_dashboard.extraer(con)
    finally:
        con.close()
    datos_dashboard.validar(datos)

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(renderizar(datos), encoding="utf-8")
    if fragmento:
        fragmento.parent.mkdir(parents=True, exist_ok=True)
        fragmento.write_text(renderizar(datos, completo=False), encoding="utf-8")

    meta = datos["meta"]
    print(
        f"[dashboard] {destino} ({destino.stat().st_size / 1e6:.1f} MB) · canasta {meta['canasta_version']} · "
        f"{len(datos['semanas'])} semanas hasta {datos['semanas'][-1]} · datos al {meta['ultima_fecha_datos']}"
    )
    return destino


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--destino", type=Path, help="ruta del HTML (predeterminado: reports/dashboard/index.html)"
    )
    parser.add_argument(
        "--fragmento", type=Path, help="escribe también la versión sin esqueleto de documento"
    )
    args = parser.parse_args(argv)
    run(args.destino, args.fragmento)
    return 0


if __name__ == "__main__":
    sys.exit(main())
