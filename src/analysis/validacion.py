"""Validación independiente del costo de canasta y del ahorro entre cadenas.

Para una muestra determinista de municipio-semanas comparables, recalcula en Python, a partir de las filas
crudas de ``raw.qqp_precios``, lo que dbt calcula en SQL:

1. fecha con el formato registrado para su archivo;
2. llaves de texto con ``src.normalize.text.llave`` y correcciones versionadas de ``data/mappings``;
3. contenido de la presentación con ``src.normalize.units.interpretar`` y decisiones manuales;
4. pertenencia a artículos con el módulo ``re`` de Python sobre el seed de la canasta;
5. consolidación de observaciones idénticas (mismo producto, tienda, fecha y precio);
6. mediana del precio unitario por cadena y artículo en la ventana de 14 días.

Compara el resultado con ``marts.mart_canasta_semanal`` y ``marts.mart_ahorro_por_cadena``.

Independencia y sus límites: SQL solo se usa para leer filas crudas con un filtro amplio (archivos del
periodo, municipio y productos de la canasta); Python repite todos los filtros exactos. Las celdas con observaciones marcadas como atípicas se omiten, porque la
detección de atípicos usa estadísticas de todo el periodo y no se replica aquí.

Uso::

    python -m src.analysis.validacion
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect
from src.normalize.text import llave
from src.normalize.units import interpretar

CELDAS_A_VALIDAR = 6
TOLERANCIA = 0.011  # costos redondeados a centavos en el mart
SIN_MARCA = {"S/M", "S/MARCA", "SIN MARCA", "SM"}


def _version_vigente() -> str:
    texto = (config.TRANSFORM_DIR / "dbt_project.yml").read_text(encoding="utf-8")
    return re.search(r'canasta_version:\s*"([^"]+)"', texto).group(1)


def _canasta(version: str) -> pd.DataFrame:
    df = pd.read_csv(
        config.TRANSFORM_DIR / "seeds" / "canasta_articulos.csv", dtype=str, keep_default_na=False
    )
    df = df[df["version"] == version].copy()
    df["cantidad_referencia"] = df["cantidad_referencia"].astype(float)
    return df


def _correcciones() -> dict[str, dict[str, str]]:
    path = config.MAPPINGS_OUT_DIR / "texto_correcciones.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = df[df["valor_corregido"] != ""]
    out: dict[str, dict[str, str]] = defaultdict(dict)
    for columna, original, corregido in zip(
        df["columna"], df["valor_original"], df["valor_corregido"], strict=True
    ):
        out[columna][original] = corregido
    return out


def _manual_presentaciones() -> dict[str, dict]:
    path = config.MANUAL_MAPPINGS_DIR / "presentaciones_manual.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {r["presentacion_key"]: r for r in df.to_dict("records")}


def _interpretar(
    presentacion: str, manual: dict[str, dict]
) -> tuple[str | None, float | None, str | None, bool]:
    p = interpretar(presentacion)
    unidad, contenido, subtipo, revision = (
        p.unidad_base,
        p.contenido_base,
        p.subtipo_conteo,
        p.requiere_revision,
    )
    decision = manual.get(p.presentacion_key)
    if decision:
        if decision["decision"] == "confirmar":
            revision = False
        elif decision["decision"] == "corregir":
            unidad, contenido = decision["unidad_base"], float(decision["contenido_base"])
            subtipo, revision = decision["subtipo_conteo"] or None, False
        else:
            revision = True
    comparable = not revision and unidad is not None and (contenido or 0) > 0
    return unidad, contenido, subtipo, comparable


def seleccionar_celdas(con, version: str, n: int) -> pd.DataFrame:
    """Municipio-semanas comparables sin atípicos en la canasta, en orden determinista y en municipios distintos."""
    candidatas = con.execute(
        """
        WITH celdas AS (
            SELECT geografia_id, semana_inicio, max(cadenas_comparadas) AS cadenas
            FROM marts.mart_ahorro_por_cadena WHERE canasta_version = ? GROUP BY ALL
        ),
        atipicas AS (
            SELECT e.geografia_id, d.semana_inicio + k AS semana_inicio
            FROM core.fct_precio_observado f
            JOIN core.dim_producto p USING (producto_id)
            JOIN core.dim_establecimiento e USING (establecimiento_id)
            JOIN core.dim_fecha d USING (fecha)
            CROSS JOIN (SELECT unnest([0, 7]) AS k)
            WHERE f.es_atipico AND p.articulo_id IS NOT NULL AND e.es_cadena_referencia
        )
        SELECT c.*, g.estado_key, g.municipio_key, g.estado, g.municipio
        FROM celdas c JOIN core.dim_geografia g USING (geografia_id)
        WHERE NOT EXISTS (SELECT 1 FROM atipicas a WHERE a.geografia_id = c.geografia_id
                          AND a.semana_inicio = c.semana_inicio)
        ORDER BY c.cadenas DESC, md5(c.geografia_id || c.semana_inicio::VARCHAR)
        """,
        [version],
    ).df()
    candidatas["semana_inicio"] = pd.to_datetime(candidatas["semana_inicio"]).dt.date
    return candidatas.drop_duplicates("geografia_id").head(n).reset_index(drop=True)


def _filas_crudas(con, celda: pd.Series, productos: list[str]) -> pd.DataFrame:
    inicio = celda["semana_inicio"] - timedelta(days=7)
    fin = celda["semana_inicio"] + timedelta(days=6)
    meses = sorted({f"{d:%m-%Y}" for d in (inicio, fin, celda["semana_inicio"])})
    patron = "(" + "|".join(meses) + ")"
    return con.execute(
        """
        SELECT p.producto, p.presentacion, p.marca, p.precio, p.fecha_registro, p.cadena_comercial,
               p.nombre_comercial, p.direccion, p.estado, p.municipio, p.archivo_origen, a.formato_fecha
        FROM raw.qqp_precios p JOIN raw.archivos a ON a.archivo = p.archivo_origen
        WHERE regexp_matches(p.archivo_origen, ?)
          AND upper(strip_accents(p.municipio)) LIKE '%' || ? || '%'
          AND upper(strip_accents(p.producto)) IN (SELECT unnest(?::VARCHAR[]))
        """,
        [patron, celda["municipio_key"], productos],
    ).df()


def recalcular_celda(con, celda: pd.Series, canasta: pd.DataFrame, correcciones, manual) -> dict[str, dict]:
    """Devuelve, por cadena de referencia, costos por artículo recalculados en Python."""
    referencia = set(pd.read_csv(config.TRANSFORM_DIR / "seeds" / "cadenas_referencia.csv")["cadena_key"])
    crudas = _filas_crudas(con, celda, sorted(set(canasta["producto_key"])))
    inicio = celda["semana_inicio"] - timedelta(days=7)
    fin = celda["semana_inicio"] + timedelta(days=6)
    formatos = {"yyyy/mm/dd": "%Y/%m/%d", "dd/mm/yyyy": "%d/%m/%Y"}
    reglas = [
        (
            r,
            re.compile(r["incluye_regex"]),
            re.compile(r["excluye_regex"]) if r["excluye_regex"] else None,
        )
        for r in canasta.to_dict("records")
    ]

    observaciones = set()
    for fila in crudas.itertuples(index=False):
        fecha = datetime.strptime(fila.fecha_registro, formatos[fila.formato_fecha]).date()
        if not (inicio <= fecha <= fin):
            continue
        if llave(fila.estado) != celda["estado_key"] or llave(fila.municipio) != celda["municipio_key"]:
            continue
        cadena = llave(correcciones["cadena_comercial"].get(fila.cadena_comercial, fila.cadena_comercial))
        if cadena not in referencia:
            continue
        producto = llave(correcciones["producto"].get(fila.producto, fila.producto))
        presentacion = correcciones["presentacion"].get(fila.presentacion, fila.presentacion)
        unidad, contenido, subtipo, comparable = _interpretar(presentacion, manual)
        if not comparable:
            continue
        pres_key = llave(presentacion)
        articulo = None
        for regla, incluye, excluye in reglas:
            if (
                regla["producto_key"] == producto
                and regla["unidad_base"] == unidad
                and (not regla["subtipo_conteo"] or regla["subtipo_conteo"] == subtipo)
                and incluye.search(pres_key)
                and not (excluye and excluye.search(pres_key))
            ):
                articulo = regla["articulo_id"]
                break
        if articulo is None:
            continue
        marca = llave(correcciones["marca"].get(fila.marca, fila.marca))
        marca = "SIN MARCA" if marca in SIN_MARCA else marca
        tienda = (
            llave(correcciones["nombre_comercial"].get(fila.nombre_comercial, fila.nombre_comercial)),
            llave(correcciones["direccion"].get(fila.direccion, fila.direccion)),
        )
        precio = round(float(fila.precio), 2)
        # Una observación = producto normalizado × tienda × fecha × precio (duplicados y multi-catálogo cuentan una vez).
        observaciones.add((cadena, articulo, producto, pres_key, marca, tienda, fecha, precio, contenido))

    por_cadena: dict[str, dict] = defaultdict(lambda: {"precios": defaultdict(list)})
    for cadena, articulo, *_, precio, contenido in observaciones:
        por_cadena[cadena]["precios"][articulo].append(round(precio / contenido, 4))

    cantidades = dict(zip(canasta["articulo_id"], canasta["cantidad_referencia"], strict=True))
    resultado = {}
    for cadena, datos in por_cadena.items():
        costos = {a: statistics.median(v) * cantidades[a] for a, v in datos["precios"].items()}
        resultado[cadena] = {
            "articulos": len(costos),
            "observaciones": sum(len(v) for v in datos["precios"].values()),
            "costo": round(sum(costos.values()), 2) if len(costos) == len(cantidades) else None,
            "costos": costos,
        }
    return resultado


def run(db_path: Path = config.DUCKDB_PATH, n: int = CELDAS_A_VALIDAR) -> pd.DataFrame:
    version = _version_vigente()
    canasta = _canasta(version)
    correcciones = _correcciones()
    manual = _manual_presentaciones()
    filas = []
    with connect(db_path, read_only=True) as con:
        celdas = seleccionar_celdas(con, version, n)
        if celdas.empty:
            raise SystemExit("[validate] no hay municipio-semanas comparables para validar")
        for _, celda in celdas.iterrows():
            recalculo = recalcular_celda(con, celda, canasta, correcciones, manual)
            mart = con.execute(
                """SELECT c.cadena_key, c.cadena, c.costo_canasta, c.articulos_disponibles, a.ahorro_vs_mas_barata
                   FROM marts.mart_canasta_semanal c
                   LEFT JOIN marts.mart_ahorro_por_cadena a USING (canasta_version, geografia_id, semana_inicio, cadena_key)
                   WHERE c.canasta_version = ? AND c.geografia_id = ? AND c.semana_inicio = ? AND c.es_cadena_referencia""",
                [version, celda["geografia_id"], celda["semana_inicio"]],
            ).df()
            costos_py = {k: v["costo"] for k, v in recalculo.items() if v["costo"] is not None}
            minimo_py = min(costos_py.values()) if len(costos_py) >= 2 else None
            for m in mart.itertuples(index=False):
                py = recalculo.get(m.cadena_key, {"articulos": 0, "observaciones": 0, "costo": None})
                ahorro_py = (
                    round(py["costo"] - minimo_py, 2) if py["costo"] is not None and minimo_py else None
                )
                costo_ok = (
                    (m.costo_canasta is None or pd.isna(m.costo_canasta)) and py["costo"] is None
                ) or (py["costo"] is not None and abs(m.costo_canasta - py["costo"]) <= TOLERANCIA)
                ahorro_ok = (pd.isna(m.ahorro_vs_mas_barata) and ahorro_py is None) or (
                    ahorro_py is not None and abs(m.ahorro_vs_mas_barata - ahorro_py) <= 2 * TOLERANCIA
                )
                filas.append(
                    {
                        "municipio": f"{celda['municipio']}, {celda['estado']}",
                        "semana": celda["semana_inicio"],
                        "cadena": m.cadena,
                        "articulos_mart": m.articulos_disponibles,
                        "articulos_python": py["articulos"],
                        "observaciones_python": py["observaciones"],
                        "costo_mart": m.costo_canasta,
                        "costo_python": py["costo"],
                        "ahorro_mart": m.ahorro_vs_mas_barata,
                        "ahorro_python": ahorro_py,
                        "resultado": "coincide" if costo_ok and ahorro_ok else "DIFERENTE",
                    }
                )
    df = pd.DataFrame(filas)
    escribir_reporte(df, version)
    diferentes = int((df["resultado"] == "DIFERENTE").sum())
    print(
        f"[validate] {len(celdas)} municipio-semanas, {len(df)} cadenas comparadas: "
        f"{len(df) - diferentes} coinciden, {diferentes} diferentes",
        flush=True,
    )
    if diferentes:
        raise SystemExit("[validate] el recálculo independiente no coincide con los marts")
    return df


def escribir_reporte(df: pd.DataFrame, version: str) -> Path:
    path = config.REPORTS_OUT_DIR / "validacion_canasta.md"
    coincide = int((df["resultado"] == "coincide").sum())
    lineas = [
        "# Validación independiente de la canasta",
        "",
        f"_Generado por `python -m src.analysis.validacion` el {datetime.now():%Y-%m-%d %H:%M} · modo "
        f"`{config.MODO}` · canasta `{version}`._",
        "",
        "Recalcula en Python, desde `raw.qqp_precios`, el costo de canasta y el ahorro de una muestra determinista",
        "de municipio-semanas comparables (sin atípicos en la canasta) y lo compara con los marts de dbt.",
        "Método y límites en el docstring de `src/analysis/validacion.py`.",
        "",
        f"**Resultado: {coincide} de {len(df)} comparaciones coinciden** (tolerancia ±{TOLERANCIA:.3f} MXN en costo,",
        f"±{2 * TOLERANCIA:.3f} MXN en ahorro).",
        "",
        df.to_markdown(index=False, floatfmt=".2f"),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lineas), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--celdas", type=int, default=CELDAS_A_VALIDAR)
    run(n=parser.parse_args(argv).celdas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
