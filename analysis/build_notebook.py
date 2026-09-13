"""Construye y ejecuta ``analysis/00_reconocimiento.ipynb``.

El notebook solo lee las tablas de ``data/interim/profile`` generadas por
``python -m src.ingest.profile``; no repite cómputo pesado.

Uso::

    python analysis/build_notebook.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "analysis" / "00_reconocimiento.ipynb"

md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell

CELLS = [
    md(
        "# 00 · Reconocimiento del dataset QQP (PROFECO)\n\n"
        "**Objetivo:** decidir si los datos permiten comparar el costo de una canasta entre cadenas, municipios "
        "y semanas, y con qué definición.\n\n"
        "**Reproducir:** `python -m src.ingest.extract` → `python -m src.ingest.profile` → "
        "`python analysis/build_notebook.py`.\n\n"
        "Las interpretaciones están en `docs/diccionario_validado.md` y las decisiones en `docs/decisiones.md`."
    ),
    code(
        "import sys\n"
        "from pathlib import Path\n\n"
        "import pandas as pd\n\n"
        "ROOT = Path.cwd().parent if Path.cwd().name == 'analysis' else Path.cwd()\n"
        "sys.path.insert(0, str(ROOT))\n"
        "from src.ingest.profile import PROFILE_DIR  # noqa: E402\n"
        "from src.ingest.profile_report import alertas  # noqa: E402\n\n"
        "pd.set_option('display.max_colwidth', 70)\n"
        "pd.set_option('display.float_format', '{:,.2f}'.format)\n"
        "t = {p.stem: pd.read_parquet(p) for p in sorted(PROFILE_DIR.glob('*.parquet'))}\n"
        "sorted(t)"
    ),
    md("## 1. Inventario y formato físico"),
    code(
        "arch = t['archivos'].merge(t['fechas_por_archivo'], on='archivo')\n"
        'print(f"{len(arch)} CSV · {arch.filas_cargadas.sum():,} filas · "\n'
        '      f"{arch.bytes.sum() / 1e9:.2f} GB · {arch.min_fecha.min():%Y-%m-%d} a {arch.max_fecha.max():%Y-%m-%d}")\n'
        "arch.groupby(['codificacion', 'bom', 'formato_fecha']).agg(archivos=('archivo', 'count'), "
        "filas=('filas_cargadas', 'sum'), primero=('archivo', 'min'), ultimo=('archivo', 'max'))"
    ),
    code(
        "# Integridad de carga: cada línea física (sin encabezado) debe ser una fila\n"
        "check = arch.assign(diferencia=arch.lineas_fisicas - 1 - arch.filas_cargadas)\n"
        "print('archivos con diferencia:', int((check.diferencia != 0).sum()), '· filas rechazadas:', len(t['rechazos']))\n"
        "check[['archivo', 'filas_cargadas', 'min_fecha', 'max_fecha', 'dias']].tail(6)"
    ),
    md("## 2. Alertas automáticas"),
    code("for a in alertas(t):\n    print('•', a)"),
    md("## 3. Esquema, nulos y cardinalidad"),
    code("t['cardinalidades'].merge(t['nulos_por_columna'], on='columna', how='outer')"),
    md("## 4. Precio"),
    code("display(t['precio_resumen'])\nt['precios_maximos']"),
    md(
        "El máximo es un error evidente de captura (medicamento de caja con 30 tabletas). "
        "Los siguientes son electrodomésticos plausibles: la detección de atípicos debe ser **por producto**, "
        "no global."
    ),
    md("## 5. Duplicados"),
    code(
        "dup = t['duplicados_por_archivo']\n"
        "tot = dup.sum(numeric_only=True)\n"
        'print(f"duplicados exactos: {tot.dup_exactos:,} · en grano: {tot.dup_grano:,} "\n'
        '      f"({100 * tot.dup_grano / tot.filas:.2f}%)")\n'
        "t['duplicados_multicatalogo']"
    ),
    md(
        "La mayoría de los duplicados es la misma observación listada en dos catálogos (p. ej. `Basicos + Pacic`). "
        "**El catálogo no es parte del grano** (D-006)."
    ),
    md("## 6. Variantes de texto que partirían series"),
    code(
        "ev = t['estado_variantes']\n"
        "display(ev[ev.duplicated('estado_normalizado', keep=False)])\n"
        "t['marca_sin_marca_variantes']"
    ),
    md("## 7. Cobertura"),
    code(
        "t['catalogo_por_anio'].pivot(index='catalogo', columns='anio', values='filas').fillna(0).astype(int)"
    ),
    code("t['cobertura_estados'].sort_values('semanas')"),
    code("t['cobertura_cadenas_basicos'].head(12)"),
    code(
        "v = t['visitas_tienda_quincena']\nv.assign(pct=100 * v.tienda_quincenas / v.tienda_quincenas.sum())"
    ),
    md(
        "Una tienda de las cadenas de referencia se visita típicamente **2 días por quincena**: "
        "la semana aislada es un grano demasiado fino para exigir la canasta completa por tienda."
    ),
    md("## 8. Viabilidad de la canasta"),
    code("t['canasta_sku_mejor_presencia']"),
    code("t['canasta_completitud'].pivot(index='nivel', columns='cadena', values='pct_completa')"),
    md(
        "## Conclusiones\n\n"
        "1. **El dataset es utilizable**: esquema estable, 0 filas rechazadas, precios y fechas 100% convertibles.\n"
        "2. **Requiere normalización antes de comparar**: dos formatos de archivo, variantes de estado, marca y "
        "presentación, caracteres perdidos en un archivo.\n"
        "3. **Una canasta de marca fija no es comparable entre las 4 cadenas grandes**: no existe una marca de frijol "
        "o arroz presente en todas.\n"
        "4. **Una canasta genérica con precio por unidad base es viable**, con mejor completitud a nivel quincena o "
        "con ventana móvil de 14 días.\n"
        "5. La cobertura geográfica es de ciudades muestreadas (75 municipios en 30 estados), no de estados completos."
    ),
]


def build() -> Path:
    nb = nbformat.v4.new_notebook(cells=CELLS)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    NotebookClient(
        nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
    ).execute()
    nbformat.write(nb, NOTEBOOK)
    print(f"notebook ejecutado: {NOTEBOOK}")
    return NOTEBOOK


if __name__ == "__main__":
    build()
