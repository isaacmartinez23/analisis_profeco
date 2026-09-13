"""Construye los mapeos de normalización y los carga en DuckDB (esquema ``mappings``).

Trabaja sobre valores distintos, no sobre filas: unos miles de textos en vez de
decenas de millones de registros.

Salidas (modo completo → versionadas en ``data/mappings``):

- ``texto_correcciones.csv``: valores con caracteres perdidos (``?``) y su corrección.
- ``productos.csv`` y ``marcas.csv``: texto original → texto corregido → llave canónica.
- ``presentaciones.csv``: presentación → unidad base, contenido y confianza.
- ``reports/revision_manual_productos.csv``: cola priorizada de casos para revisión humana.

Decisiones manuales (siempre en ``data/mappings/manual``, separadas de lo automático):

- ``texto_correcciones_manual.csv``: columna, valor_original, valor_corregido, decidido_por, fecha, justificacion
- ``presentaciones_manual.csv``: presentacion_key, decision (confirmar|corregir|excluir), unidad_base,
  contenido_base, subtipo_conteo, decidido_por, fecha, justificacion

Uso::

    python -m src.normalize.build
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src import config
from src.db import connect
from src.normalize.text import corregir_interrogaciones, llave
from src.normalize.units import interpretar

CATALOGOS_ALCANCE = ["Basicos", "Frutas y Legumbres", "Pacic", "Mercados"]
COLUMNAS_CORRECCION = [
    "producto",
    "presentacion",
    "marca",
    "giro",
    "cadena_comercial",
    "nombre_comercial",
    "direccion",
]
SIN_MARCA = {"S/M", "S/MARCA", "SIN MARCA", "SM"}
DECISIONES_VALIDAS = {"confirmar", "corregir", "excluir"}


def _leer_manual(nombre: str, columnas: list[str]) -> pd.DataFrame:
    path = config.MANUAL_MAPPINGS_DIR / nombre
    if not path.exists():
        return pd.DataFrame(columns=columnas)
    df = pd.read_csv(path, dtype=str, keep_default_na=False).replace({"": None})
    faltantes = set(columnas) - set(df.columns)
    if faltantes:
        raise ValueError(f"{path}: faltan columnas {sorted(faltantes)}")
    return df


def _distintos(con, columna: str) -> pd.DataFrame:
    catalogos = ", ".join(f"'{c}'" for c in CATALOGOS_ALCANCE)
    return con.execute(
        f"""SELECT {columna} AS valor, count(*) AS filas, bool_or(catalogo IN ({catalogos})) AS en_alcance,
                   any_value(producto) AS ejemplo_producto
            FROM raw.qqp_precios WHERE {columna} IS NOT NULL GROUP BY 1"""
    ).df()


def construir_correcciones(distintos: dict[str, pd.DataFrame]) -> pd.DataFrame:
    filas = []
    for columna, df in distintos.items():
        filas += [asdict(c) for c in corregir_interrogaciones(columna, df["valor"])]
    auto = pd.DataFrame(
        filas,
        columns=["columna", "valor_original", "valor_corregido", "candidatos", "metodo", "requiere_revision"],
    )
    manual = _leer_manual(
        "texto_correcciones_manual.csv",
        ["columna", "valor_original", "valor_corregido", "decidido_por", "fecha", "justificacion"],
    )
    nuevas = []
    for _, m in manual.iterrows():
        mask = (auto["columna"] == m["columna"]) & (auto["valor_original"] == m["valor_original"])
        if mask.any():
            auto.loc[mask, ["valor_corregido", "metodo", "requiere_revision"]] = [
                m["valor_corregido"],
                "manual",
                False,
            ]
        else:
            # Variantes sin "?" (p. ej. "Central de Abastos" → "Central de Abasto") también se corrigen a mano.
            nuevas.append(
                {
                    "columna": m["columna"],
                    "valor_original": m["valor_original"],
                    "valor_corregido": m["valor_corregido"],
                    "candidatos": None,
                    "metodo": "manual",
                    "requiere_revision": False,
                }
            )
    if nuevas:
        auto = pd.concat([auto, pd.DataFrame(nuevas)], ignore_index=True)
    return auto.sort_values(["columna", "valor_original"]).reset_index(drop=True)


def _mapa_correcciones(correcciones: pd.DataFrame, columna: str) -> dict[str, str]:
    df = correcciones[(correcciones["columna"] == columna) & correcciones["valor_corregido"].notna()]
    return dict(zip(df["valor_original"], df["valor_corregido"], strict=True))


def construir_productos(valores: pd.Series, correcciones: pd.DataFrame) -> pd.DataFrame:
    mapa = _mapa_correcciones(correcciones, "producto")
    df = pd.DataFrame({"producto_original": sorted(valores)})
    df["producto_corregido"] = df["producto_original"].map(lambda v: mapa.get(v, v))
    df["producto_key"] = df["producto_corregido"].map(llave)
    return df


def construir_marcas(valores: pd.Series, correcciones: pd.DataFrame) -> pd.DataFrame:
    mapa = _mapa_correcciones(correcciones, "marca")
    df = pd.DataFrame({"marca_original": sorted(valores)})
    df["marca_corregida"] = df["marca_original"].map(lambda v: mapa.get(v, v))
    df["marca_key"] = df["marca_corregida"].map(llave)
    df["es_sin_marca"] = df["marca_key"].isin(SIN_MARCA)
    df.loc[df["es_sin_marca"], "marca_key"] = "SIN MARCA"
    return df


def construir_presentaciones(valores: pd.Series, correcciones: pd.DataFrame) -> pd.DataFrame:
    mapa = _mapa_correcciones(correcciones, "presentacion")
    originales = sorted(valores)
    corregidas = [mapa.get(v, v) for v in originales]
    df = pd.DataFrame([asdict(interpretar(c)) for c in corregidas])
    df.insert(0, "presentacion_original", originales)
    df.insert(1, "presentacion_corregida", corregidas)
    df["metodo"] = "auto"

    manual = _leer_manual(
        "presentaciones_manual.csv",
        [
            "presentacion_key",
            "decision",
            "unidad_base",
            "contenido_base",
            "subtipo_conteo",
            "decidido_por",
            "fecha",
            "justificacion",
        ],
    )
    invalidas = set(manual["decision"]) - DECISIONES_VALIDAS
    if invalidas:
        raise ValueError(f"presentaciones_manual.csv: decisiones no válidas {sorted(invalidas)}")
    for _, m in manual.iterrows():
        mask = df["presentacion_key"] == m["presentacion_key"]
        if m["decision"] == "confirmar":
            df.loc[mask, ["requiere_revision", "motivo_revision", "metodo"]] = [
                False,
                None,
                "manual_confirmado",
            ]
        elif m["decision"] == "corregir":
            df.loc[mask, ["unidad_base", "contenido_base", "subtipo_conteo"]] = [
                m["unidad_base"],
                float(m["contenido_base"]),
                m["subtipo_conteo"],
            ]
            df.loc[mask, ["requiere_revision", "motivo_revision", "confianza", "metodo"]] = [
                False,
                None,
                "alta",
                "manual_corregido",
            ]
        else:
            df.loc[mask, ["requiere_revision", "motivo_revision", "metodo"]] = [
                True,
                "excluida_manual",
                "manual_excluido",
            ]

    df["es_comparable"] = (
        ~df["requiere_revision"].astype(bool)
        & df["unidad_base"].notna()
        & (df["contenido_base"].fillna(0) > 0)
    )
    return df


def construir_cola_revision(
    distintos: dict[str, pd.DataFrame], correcciones: pd.DataFrame, presentaciones: pd.DataFrame
) -> pd.DataFrame:
    pres = presentaciones[presentaciones["requiere_revision"].astype(bool)].merge(
        distintos["presentacion"], left_on="presentacion_original", right_on="valor"
    )
    cola_pres = pres.groupby("presentacion_key", as_index=False).agg(
        valor=("presentacion_original", "first"),
        motivo=("motivo_revision", "first"),
        filas=("filas", "sum"),
        en_alcance=("en_alcance", "max"),
        ejemplo_producto=("ejemplo_producto", "first"),
        sugerencia_unidad=("unidad_base", "first"),
        sugerencia_contenido=("contenido_base", "first"),
    )
    cola_pres.insert(0, "tipo", "presentacion")
    cola_pres.insert(1, "columna", "presentacion")

    pendientes = correcciones[correcciones["requiere_revision"].astype(bool)]
    textos = []
    for columna, df in distintos.items():
        sub = pendientes[pendientes["columna"] == columna].merge(
            df, left_on="valor_original", right_on="valor"
        )
        if len(sub):
            textos.append(
                sub.assign(
                    tipo="correccion_texto",
                    presentacion_key=None,
                    motivo=sub["metodo"],
                    sugerencia_unidad=None,
                    sugerencia_contenido=None,
                )[cola_pres.columns]
            )
    cola = pd.concat([cola_pres, *textos], ignore_index=True)
    cola = cola.sort_values(["en_alcance", "filas"], ascending=[False, False]).reset_index(drop=True)
    cola.insert(0, "prioridad", range(1, len(cola) + 1))
    return cola


def run(db_path: Path = config.DUCKDB_PATH) -> dict[str, pd.DataFrame]:
    out_dir = config.MAPPINGS_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as con:
        distintos = {c: _distintos(con, c) for c in COLUMNAS_CORRECCION}
        correcciones = construir_correcciones(distintos)
        productos = construir_productos(distintos["producto"]["valor"], correcciones)
        marcas = construir_marcas(distintos["marca"]["valor"], correcciones)
        presentaciones = construir_presentaciones(distintos["presentacion"]["valor"], correcciones)
        cola = construir_cola_revision(distintos, correcciones, presentaciones)

        salidas = {
            "texto_correcciones": correcciones,
            "productos": productos,
            "marcas": marcas,
            "presentaciones": presentaciones,
        }
        con.execute("CREATE SCHEMA IF NOT EXISTS mappings")
        for nombre, df in salidas.items():
            df.to_csv(out_dir / f"{nombre}.csv", index=False, lineterminator="\n")
            con.register("tmp_df", df)
            con.execute(f"CREATE OR REPLACE TABLE mappings.{nombre} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")

    config.REPORTS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cola.to_csv(config.REPORTS_OUT_DIR / "revision_manual_productos.csv", index=False, lineterminator="\n")

    pres_alc = presentaciones.merge(
        distintos["presentacion"], left_on="presentacion_original", right_on="valor"
    )
    pres_alc = pres_alc[pres_alc["en_alcance"]]
    pct = 100 * pres_alc.loc[pres_alc["es_comparable"], "filas"].sum() / max(pres_alc["filas"].sum(), 1)
    print(
        f"[normalize] {len(productos):,} productos · {len(marcas):,} marcas · {len(presentaciones):,} presentaciones "
        f"· {int(correcciones['valor_corregido'].notna().sum())} correcciones de texto · "
        f"{pct:.1f}% de filas en alcance comparables · {len(cola):,} casos en cola de revisión → {out_dir}",
        flush=True,
    )
    return {**salidas, "cola_revision": cola}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
