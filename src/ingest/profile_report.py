"""Genera ``reports/perfil_datos.md`` a partir de las tablas de perfil.

Las cifras del reporte se calculan siempre desde ``data/interim/profile``; nada
se escribe a mano, de modo que el reporte se regenera con cada inspección.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from src import config
from src.ingest.profile import PROFILE_DIR

REPORT_PATH = config.REPORTS_DIR / "perfil_datos.md"


def _load(name: str) -> pd.DataFrame:
    return pd.read_parquet(PROFILE_DIR / f"{name}.parquet")


def _md(df: pd.DataFrame, floatfmt: str = ",.2f") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt, intfmt=",")


def _n(x: float | int) -> str:
    return f"{int(x):,}"


def alertas(t: dict[str, pd.DataFrame]) -> list[str]:
    """Reglas automáticas que convierten el perfil en hallazgos accionables."""
    out: list[str] = []
    arch = t["archivos"]
    no_utf8 = arch[~arch["codificacion"].str.startswith("utf-8")]
    if len(no_utf8):
        out.append(
            f"**Codificación distinta** en {len(no_utf8)} archivo(s): "
            + ", ".join(f"`{a}` ({c})" for a, c in zip(no_utf8.archivo, no_utf8.codificacion, strict=True))
        )
    fechas = t["fechas_por_archivo"]
    formatos = fechas["formato_fecha"].value_counts()
    if len(formatos) > 1:
        minor = fechas[fechas["formato_fecha"] != formatos.index[0]]
        out.append(
            f"**Formato de fecha distinto** (`{minor.formato_fecha.iloc[0]}` vs `{formatos.index[0]}`) en: "
            + ", ".join(f"`{a}`" for a in minor.archivo)
        )
    if (fechas["fecha_no_convertible"] > 0).any():
        out.append(f"**Fechas no convertibles**: {_n(fechas.fecha_no_convertible.sum())} filas")
    rech = t["rechazos"]
    out.append(f"Filas rechazadas por el lector CSV: **{_n(len(rech))}**")
    carga = arch[arch["lineas_fisicas"] - 1 != arch["filas_cargadas"]]
    if len(carga):
        out.append(f"**Filas cargadas ≠ líneas físicas** en {len(carga)} archivo(s)")
    orden = fechas.sort_values("min_fecha")
    traslapes = orden[orden["min_fecha"].shift(-1) <= orden["max_fecha"]]
    if len(traslapes):
        out.append(f"**Traslape de fechas** entre archivos: {', '.join(traslapes.archivo)}")
    precio = t["precio_resumen"].iloc[0]
    if precio["maximo"] > 100 * precio["p99"]:
        top = t["precios_maximos"].iloc[0]
        out.append(
            f"**Precio extremo**: {top.producto} ({top.presentacion}) a ${top.precio:,.0f} en {top.cadena_comercial}"
            f" — más de 100× el percentil 99 (${precio['p99']:,.0f})"
        )
    dup = t["duplicados_por_archivo"].sum(numeric_only=True)
    out.append(
        f"Duplicados exactos: **{_n(dup.dup_exactos)}** filas; en grano candidato: **{_n(dup.dup_grano)}** "
        f"({100 * dup.dup_grano / dup.filas:.2f}%), de los cuales {_n(dup.grupos_multicatalogo)} grupos son la misma "
        f"observación publicada en varios catálogos y {_n(dup.grupos_precio_en_conflicto)} tienen precios en conflicto"
    )
    perdidos = t["duplicados_por_archivo"].query("filas_con_caracter_perdido > 0")
    if len(perdidos):
        out.append(
            "**Caracteres perdidos (`?` en lugar de letra acentuada)** en: "
            + ", ".join(
                f"`{a}` ({_n(n)} filas)"
                for a, n in zip(perdidos.archivo, perdidos.filas_con_caracter_perdido, strict=True)
            )
        )
    variantes = t["estado_variantes"].groupby("estado_normalizado").size()
    if (variantes > 1).any():
        out.append(
            f"**Nombres de estado con variantes** (acentos): {int((variantes > 1).sum())} estados "
            f"({len(t['estado_variantes'])} valores originales → {len(variantes)} normalizados)"
        )
    sm = t["marca_sin_marca_variantes"]["marca"].unique()
    if len(sm) > 1:
        out.append(f"**Marca genérica con variantes de mayúsculas**: {', '.join(f'`{m}`' for m in sm)}")
    return out


def write(path: Path = REPORT_PATH) -> Path:
    names = [p.stem for p in PROFILE_DIR.glob("*.parquet")]
    t = {n: _load(n) for n in names}
    arch = t["archivos"].merge(t["fechas_por_archivo"], on="archivo")
    arch["MB"] = arch["bytes"] / 1e6
    arch["min_fecha"] = pd.to_datetime(arch["min_fecha"]).dt.date
    arch["max_fecha"] = pd.to_datetime(arch["max_fecha"]).dt.date
    total_filas = arch["filas_cargadas"].sum()

    manifest_path = config.INTERIM_DIR / "manifest_extraccion.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"archivos": []}
    )
    originales = pd.DataFrame(
        [
            {
                "archivo": a["archivo"],
                "MB": a["bytes"] / 1e6,
                "csv": len(a["csv"]),
                "sha256": a["sha256"][:16] + "…",
            }
            for a in manifest["archivos"]
        ]
    )

    dup = t["duplicados_por_archivo"]
    completitud = (
        t["canasta_completitud"].pivot(index="nivel", columns="cadena", values="pct_completa").reset_index()
    )

    lines = [
        "# Perfil de datos — Quién es Quién en los Precios (PROFECO)",
        "",
        f"_Generado automáticamente por `python -m src.ingest.profile` el {datetime.now():%Y-%m-%d %H:%M}._",
        "_No editar a mano: las interpretaciones viven en `docs/diccionario_validado.md` y `docs/bitacora.md`._",
        "",
        "## Resumen",
        "",
        f"- Archivos originales: **{len(originales)}** comprimidos → **{len(arch)}** CSV "
        f"({arch.MB.sum() / 1000:,.2f} GB sin comprimir)",
        f"- Filas: **{_n(total_filas)}** · periodo **{arch.min_fecha.min():%Y-%m-%d}** a "
        f"**{arch.max_fecha.max():%Y-%m-%d}**",
        f"- Estados (normalizados): **{len(t['cobertura_estados'])}** · municipios: "
        f"**{_n(t['cobertura_estados'].municipios.sum())}**",
        "",
        "## Alertas automáticas",
        "",
        *[f"- {a}" for a in alertas(t)],
        "",
        "## 1. Archivos originales (`data/raw/`, inmutables)",
        "",
        _md(originales),
        "",
        "## 2. Inventario de CSV",
        "",
        _md(
            arch[
                [
                    "archivo",
                    "MB",
                    "codificacion",
                    "bom",
                    "lineas_fisicas",
                    "filas_cargadas",
                    "formato_fecha",
                    "min_fecha",
                    "max_fecha",
                    "dias",
                ]
            ],
            floatfmt=",.1f",
        ),
        "",
        "## 3. Esquema observado",
        "",
        "Las 15 columnas son idénticas y en el mismo orden en todos los archivos.",
        "",
        _md(t["cardinalidades"].merge(t["nulos_por_columna"], on="columna", how="outer")),
        "",
        "## 4. Precio",
        "",
        _md(t["precio_resumen"]),
        "",
        "Diez precios más altos:",
        "",
        _md(t["precios_maximos"]),
        "",
        "## 5. Coordenadas",
        "",
        _md(t["coordenadas_resumen"]),
        "",
        "## 6. Duplicados y caracteres perdidos por archivo",
        "",
        "Grano candidato: producto + presentación + marca + nombre comercial + dirección + estado + municipio + fecha.",
        "",
        _md(dup),
        "",
        "Combinaciones de catálogo en grupos duplicados:",
        "",
        _md(t["duplicados_multicatalogo"]),
        "",
        "## 7. Variantes de texto",
        "",
        "### Estado",
        "",
        _md(t["estado_variantes"]),
        "",
        "### Giro",
        "",
        _md(t["giro_valores"]),
        "",
        "### Marca genérica",
        "",
        _md(t["marca_sin_marca_variantes"]),
        "",
        "## 8. Cobertura",
        "",
        "### Catálogo por año",
        "",
        _md(t["catalogo_por_anio"]),
        "",
        "### Estados",
        "",
        _md(t["cobertura_estados"]),
        "",
        "### Cadenas con más de 50 mil registros en catálogo Básicos",
        "",
        _md(t["cobertura_cadenas_basicos"]),
        "",
        "### Frecuencia de levantamiento (días con registro por tienda y quincena, cadenas de referencia)",
        "",
        _md(t["visitas_tienda_quincena"]),
        "",
        "## 9. Viabilidad de la canasta",
        "",
        "Candidatos: `data/mappings/canasta_candidatos_v0.csv`. Cadenas de referencia: "
        "Wal-mart, Bodega Aurrera, Hipermercado Soriana, Chedraui.",
        "",
        "### SKU (marca fija) con mayor presencia mínima entre cadenas, por producto",
        "",
        _md(t["canasta_sku_mejor_presencia"]),
        "",
        "### % de celdas con la canasta completa",
        "",
        _md(completitud, floatfmt=".1f"),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[profile] reporte escrito en {path}", flush=True)
    return path
