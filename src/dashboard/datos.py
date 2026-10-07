"""Extracción de los datos del dashboard desde DuckDB.

Cada conjunto sale de una tabla publicada en Supabase (``docs/dashboard_looker_studio.md`` §1.3) con su mismo grano,
o de una agregación declarada aquí cuando el detalle no cabe en el HTML. Los conjuntos son columnares: un diccionario
``{columna: [valores]}`` donde las columnas ``s``, ``g``, ``c`` y ``a`` son índices a ``semanas``, ``geografia``,
``cadenas`` y ``articulos``. Las métricas conservan el nombre de la columna publicada para que sean trazables.

Agregaciones propias del dashboard (no existen como tabla publicada):

- ``precio_articulo``: mediana nacional por semana × cadena × artículo de ``mart_precio_producto``.
- ``cobertura``: ``mart_cobertura_datos`` sumado por semana × municipio × cadena de referencia, con el resto de las
  cadenas en un solo grupo (índice ``len(cadenas)``). Guarda sumas y número de filas para promediar en el navegador.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from src import config

# Orden fijo de la paleta categórica: el color sigue a la cadena, no a su posición en un filtro.
ORDEN_CADENAS = ["WAL-MART", "CHEDRAUI", "BODEGA AURRERA", "HIPERMERCADO SORIANA"]
ALCANCE_TODAS = "Todas las cadenas de referencia"

Columnas = dict[str, list[Any]]


def _columnas(con, sql: str, params: list | None = None) -> Columnas:
    cursor = con.execute(sql, params or [])
    nombres = [d[0] for d in cursor.description]
    filas = cursor.fetchall()
    return {nombre: [_valor(f[i]) for f in filas] for i, nombre in enumerate(nombres)}


def _valor(v: Any) -> Any:
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):  # columnas DECIMAL: JSON solo admite números de punto flotante
        v = float(v)
    if isinstance(v, float) and v.is_integer():
        return int(v)  # 12.0 → 12: reduce el tamaño del HTML sin cambiar el valor
    return v


def _indexar(datos: Columnas, columna: str, indice: dict[Any, int], nuevo: str) -> Columnas:
    """Sustituye una llave por su índice en un catálogo; falla si alguna llave no está en el catálogo."""
    faltantes = sorted({str(v) for v in datos[columna] if v not in indice})
    if faltantes:
        raise ValueError(f"[dashboard] {columna}: valores fuera del catálogo {faltantes[:5]}")
    valores = [indice[v] for v in datos.pop(columna)]
    return {nuevo: valores, **datos}


def _version_vigente(con) -> str:
    versiones = [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT canasta_version FROM core.dim_canasta WHERE es_version_vigente"
        ).fetchall()
    ]
    if len(versiones) != 1:
        raise ValueError(f"[dashboard] se esperaba una versión vigente de la canasta y hay {versiones}")
    return versiones[0]


def _commit() -> str | None:
    if sha := os.getenv("GITHUB_SHA"):
        return sha
    try:
        salida = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=config.ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return salida.stdout.strip() or None


def _semanas_base_indice() -> int | None:
    """Semanas del periodo base del índice (variable dbt `indice_semanas_base`, D-026)."""
    proyecto = config.TRANSFORM_DIR / "dbt_project.yml"
    if not proyecto.exists():
        return None
    encontrado = re.search(
        r"^\s*indice_semanas_base:\s*(\d+)", proyecto.read_text(encoding="utf-8"), re.MULTILINE
    )
    return int(encontrado.group(1)) if encontrado else None


def _meta(con, version: str) -> dict[str, Any]:
    fila = con.execute(
        """SELECT (SELECT max(fecha) FROM core.dim_fecha),
                  (SELECT max(cargado_utc) FROM raw.archivos),
                  (SELECT count(*) FROM raw.archivos),
                  (SELECT count(*) FROM core.fct_precio_observado),
                  (SELECT count(DISTINCT cadena_key) FILTER (WHERE NOT es_cadena_referencia)
                   FROM marts.mart_cobertura_datos WHERE canasta_version = ?),
                  (SELECT min(semana_inicio) FROM marts.mart_ahorro_por_cadena WHERE canasta_version = ?),
                  (SELECT max(semana_inicio) FROM marts.mart_ahorro_por_cadena WHERE canasta_version = ?)""",
        [version, version, version],
    ).fetchone()
    return {
        "canasta_version": version,
        "ultima_fecha_datos": _valor(fila[0]),
        "ultima_carga_utc": str(fila[1]) if fila[1] else None,
        "archivos_fuente": fila[2],
        "observaciones": fila[3],
        "cadenas_no_referencia": fila[4],
        "primera_semana_comparable": _valor(fila[5]),
        "ultima_semana_comparable": _valor(fila[6]),
        "indice_semanas_base": _semanas_base_indice(),
        "modo": config.MODO,
        "generado_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit_git": _commit(),
        "ejecucion_ci": os.getenv("GITHUB_RUN_ID"),
    }


def extraer(con) -> dict[str, Any]:
    v = _version_vigente(con)

    semanas = [
        _valor(r[0])
        for r in con.execute(
            """SELECT semana_inicio FROM marts.mart_canasta_semanal WHERE canasta_version = $v
               UNION SELECT semana_inicio FROM marts.mart_cobertura_datos WHERE canasta_version = $v
               UNION SELECT semana_inicio FROM bi.bi_ahorro_semanal WHERE canasta_version = $v
               ORDER BY 1""",
            {"v": v},
        ).fetchall()
    ]
    i_semana = {s: i for i, s in enumerate(semanas)}

    cadenas_bd = con.execute(
        """SELECT cadena_key, any_value(cadena), any_value(grupo_empresarial)
           FROM bi.bi_costo_semanal_cadena WHERE canasta_version = ? GROUP BY 1""",
        [v],
    ).fetchall()
    orden = {k: i for i, k in enumerate(ORDEN_CADENAS)}
    cadenas_bd.sort(key=lambda r: (orden.get(r[0], len(orden)), r[0]))
    cadenas = [{"key": k, "nombre": n, "grupo": g} for k, n, g in cadenas_bd]
    i_cadena_key = {c["key"]: i for i, c in enumerate(cadenas)}
    i_cadena_nombre = {c["nombre"]: i for i, c in enumerate(cadenas)}

    articulos_bd = _columnas(
        con,
        """SELECT articulo_id AS id, articulo AS nombre, grupo, unidad_base, cantidad_referencia,
                  unidad_referencia
           FROM core.dim_canasta WHERE canasta_version = ? ORDER BY grupo, articulo""",
        [v],
    )
    articulos = [
        dict(zip(articulos_bd, fila, strict=True)) for fila in zip(*articulos_bd.values(), strict=True)
    ]
    i_articulo = {a["id"]: i for i, a in enumerate(articulos)}

    geografia_bd = _columnas(
        con,
        """SELECT geografia_id AS id, estado, estado_iso AS iso, municipio
           FROM core.dim_geografia ORDER BY estado, municipio""",
    )
    geografia = [
        {"estado": e, "iso": iso, "municipio": m}
        for e, iso, m in zip(
            geografia_bd["estado"], geografia_bd["iso"], geografia_bd["municipio"], strict=True
        )
    ]
    i_geo = {g: i for i, g in enumerate(geografia_bd["id"])}

    def semanal(sql: str) -> Columnas:
        return _indexar(_columnas(con, sql, [v]), "semana_inicio", i_semana, "s")

    ahorro_semanal = semanal(
        """SELECT semana_inicio, municipios_comparables, municipios_con_4_cadenas, municipios_con_grupos_distintos,
                  ahorro_maximo_mediano, ahorro_maximo_mediano_pct, ahorro_maximo_p90,
                  ahorro_maximo_mediano_competidores, cadena_mas_barata_mas_frecuente
           FROM bi.bi_ahorro_semanal WHERE canasta_version = ? ORDER BY semana_inicio"""
    )
    ahorro_semanal = _indexar(
        ahorro_semanal, "cadena_mas_barata_mas_frecuente", i_cadena_nombre, "cadena_mas_barata_mas_frecuente"
    )

    costo_cadena = semanal(
        """SELECT semana_inicio, cadena_key, municipios_comparables, costo_mediano, costo_p25, costo_p75,
                  veces_mas_barata, ahorro_mediano_vs_mas_barata, ahorro_mediano_pct, n_observaciones
           FROM bi.bi_costo_semanal_cadena WHERE canasta_version = ? ORDER BY semana_inicio, cadena_key"""
    )
    costo_cadena = _indexar(costo_cadena, "cadena_key", i_cadena_key, "c")

    indice = semanal(
        """SELECT semana_inicio, alcance, pares, indice_base_100
           FROM bi.bi_indice_canasta WHERE canasta_version = ? ORDER BY semana_inicio, alcance"""
    )
    i_alcance = {ALCANCE_TODAS: 0} | {nombre: i + 1 for nombre, i in i_cadena_nombre.items()}
    indice = _indexar(indice, "alcance", i_alcance, "alcance")

    diferencias = semanal(
        """SELECT semana_inicio, articulo_id, celdas_comparadas, round(diferencia_acumulada, 2) AS diferencia_acumulada,
                  celdas_con_sobreprecio, sobreprecio_mediano_pct, round(precio_unitario_mediano, 3)
                  AS precio_unitario_mediano
           FROM bi.bi_diferencias_producto_semanal WHERE canasta_version = ? ORDER BY semana_inicio, articulo_id"""
    )
    diferencias = _indexar(diferencias, "articulo_id", i_articulo, "a")

    disponibilidad = semanal(
        """SELECT semana_inicio, cadena_key, articulo_id, celdas, celdas_con_articulo, n_observaciones
           FROM bi.bi_disponibilidad_semanal WHERE canasta_version = ?
           ORDER BY semana_inicio, cadena_key, articulo_id"""
    )
    disponibilidad = _indexar(
        _indexar(disponibilidad, "articulo_id", i_articulo, "a"), "cadena_key", i_cadena_key, "c"
    )

    ahorro_municipio = semanal(
        """SELECT semana_inicio, geografia_id, cadena_key, posicion, costo_canasta, ahorro_vs_mas_barata, ahorro_pct,
                  cadenas_comparadas
           FROM marts.mart_ahorro_por_cadena WHERE canasta_version = ?
           ORDER BY semana_inicio, geografia_id, posicion, cadena_key"""
    )
    ahorro_municipio = _indexar(
        _indexar(ahorro_municipio, "cadena_key", i_cadena_key, "c"), "geografia_id", i_geo, "g"
    )

    precio_articulo = semanal(
        """SELECT semana_inicio, cadena_key, articulo_id,
                  round(median(mediana_precio_unitario), 3) AS mediana_precio_unitario, count(*) AS municipios
           FROM marts.mart_precio_producto WHERE canasta_version = ?
           GROUP BY semana_inicio, cadena_key, articulo_id ORDER BY semana_inicio, cadena_key, articulo_id"""
    )
    precio_articulo = _indexar(
        _indexar(precio_articulo, "articulo_id", i_articulo, "a"), "cadena_key", i_cadena_key, "c"
    )

    cobertura = semanal(
        """SELECT semana_inicio, geografia_id,
                  CASE WHEN es_cadena_referencia THEN cadena_key ELSE '__OTRAS__' END AS cadena_key,
                  sum(n_observaciones)::BIGINT AS n_observaciones,
                  count(*) AS filas,
                  sum(n_establecimientos)::BIGINT AS n_establecimientos,
                  sum(n_dias_con_observacion)::BIGINT AS n_dias_con_observacion,
                  round(sum(pct_atipicas), 3) AS pct_atipicas,
                  round(sum(pct_no_comparables), 2) AS pct_no_comparables
           FROM marts.mart_cobertura_datos WHERE canasta_version = ?
           GROUP BY ALL ORDER BY 1, 2, 3"""
    )
    i_cobertura = i_cadena_key | {"__OTRAS__": len(cadenas)}
    cobertura = _indexar(_indexar(cobertura, "cadena_key", i_cobertura, "c"), "geografia_id", i_geo, "g")

    canasta = semanal(
        """SELECT semana_inicio, geografia_id, cadena_key, es_canasta_completa::INT AS es_canasta_completa
           FROM marts.mart_canasta_semanal WHERE canasta_version = ? AND es_cadena_referencia
           ORDER BY semana_inicio, geografia_id, cadena_key"""
    )
    canasta = _indexar(_indexar(canasta, "cadena_key", i_cadena_key, "c"), "geografia_id", i_geo, "g")

    faltantes = semanal(
        """SELECT semana_inicio, geografia_id, cadena_key, articulo_id
           FROM bi.bi_disponibilidad_articulos WHERE canasta_version = ? AND NOT disponible
           ORDER BY semana_inicio, geografia_id, cadena_key, articulo_id"""
    )
    faltantes = _indexar(
        _indexar(_indexar(faltantes, "articulo_id", i_articulo, "a"), "cadena_key", i_cadena_key, "c"),
        "geografia_id",
        i_geo,
        "g",
    )

    return {
        "meta": _meta(con, v),
        "semanas": semanas,
        "cadenas": cadenas,
        "articulos": articulos,
        "geografia": geografia,
        "ahorro_semanal": ahorro_semanal,
        "costo_cadena": costo_cadena,
        "indice": indice,
        "diferencias": diferencias,
        "disponibilidad": disponibilidad,
        "ahorro_municipio": ahorro_municipio,
        "precio_articulo": precio_articulo,
        "cobertura": cobertura,
        "canasta": canasta,
        "faltantes": faltantes,
    }


CONJUNTOS_OBLIGATORIOS = [
    "ahorro_semanal",
    "costo_cadena",
    "indice",
    "diferencias",
    "disponibilidad",
    "canasta",
]
CATALOGOS = {"s": "semanas", "g": "geografia", "c": "cadenas", "a": "articulos"}


def validar(datos: dict[str, Any]) -> None:
    """Comprueba la forma del contrato antes de escribir el HTML: columnas del mismo largo e índices válidos."""
    problemas = []
    if len(datos["cadenas"]) < 2:
        problemas.append(f"se necesitan al menos 2 cadenas de referencia y hay {len(datos['cadenas'])}")
    for nombre, conjunto in datos.items():
        if not isinstance(conjunto, dict) or "s" not in conjunto:
            continue
        largos = {len(valores) for valores in conjunto.values()}
        if len(largos) != 1:
            problemas.append(f"{nombre}: columnas de distinto largo {sorted(largos)}")
            continue
        if nombre in CONJUNTOS_OBLIGATORIOS and not largos.pop():
            problemas.append(f"{nombre}: sin filas")
        for columna, catalogo in CATALOGOS.items():
            if columna not in conjunto:
                continue
            # La cobertura usa un índice adicional para el grupo "otras cadenas".
            limite = len(datos[catalogo]) + (1 if nombre == "cobertura" and columna == "c" else 0)
            if any(not 0 <= i < limite for i in conjunto[columna]):
                problemas.append(f"{nombre}.{columna}: índices fuera de {catalogo}")
        # Alcance del índice: 0 = todas las cadenas de referencia, 1..n = cada cadena.
        if "alcance" in conjunto and any(not 0 <= i <= len(datos["cadenas"]) for i in conjunto["alcance"]):
            problemas.append(f"{nombre}.alcance: índices fuera de cadenas")
    if problemas:
        raise ValueError("[dashboard] datos inválidos:\n  " + "\n  ".join(problemas))
