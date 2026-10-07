"""Pruebas del dashboard estático: extracción desde DuckDB, contrato de datos y armado del HTML."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import pytest

from src import cli
from src.dashboard import datos as datos_dashboard
from src.dashboard import generar

TABLAS = {
    "core.dim_canasta": (
        "canasta_version, articulo_id, articulo, grupo, unidad_base, cantidad_referencia, unidad_referencia, "
        "es_version_vigente",
        [
            "('v1', 'HUEVO_BLANCO', 'Huevo blanco', 'Proteína animal', 'pieza', 18.0, '18 piezas', true)",
            "('v1', 'ARROZ', 'Arroz súper extra', 'Cereales y derivados', 'kg', 1.0, '1 kg', true)",
            "('v0', 'FRIJOL', 'Frijol negro', 'Leguminosas', 'kg', 1.0, '1 kg', false)",
        ],
    ),
    "core.dim_geografia": (
        "geografia_id, estado, estado_iso, municipio",
        [
            "('geo-jal', 'Jalisco', 'MX-JAL', 'Guadalajara')",
            "('geo-agu', 'Aguascalientes', 'MX-AGU', 'Aguascalientes')",
        ],
    ),
    "core.dim_fecha": ("fecha", ["(DATE '2026-07-13')", "(DATE '2026-07-31')"]),
    "core.fct_precio_observado": ("precio", ["(10.0)", "(12.0)", "(14.0)"]),
    "raw.archivos": ("cargado_utc", ["(TIMESTAMP '2026-09-16 18:52:02')"]),
    "bi.bi_ahorro_semanal": (
        "canasta_version, semana_inicio, municipios_comparables, municipios_con_4_cadenas, "
        "municipios_con_grupos_distintos, ahorro_maximo_mediano, ahorro_maximo_mediano_pct, ahorro_maximo_p90, "
        "ahorro_maximo_mediano_competidores, cadena_mas_barata_mas_frecuente",
        [
            "('v1', DATE '2026-07-20', 2, 0, 2, 30.5, 4.5, 60.0, 31.0, 'Chedraui')",
            "('v1', DATE '2026-07-13', 1, 0, 1, 40.0, 5.5, 40.0, 40.0, 'Wal-mart')",
        ],
    ),
    "bi.bi_costo_semanal_cadena": (
        "canasta_version, semana_inicio, cadena_key, cadena, grupo_empresarial, municipios_comparables, "
        "costo_mediano, costo_p25, costo_p75, veces_mas_barata, ahorro_mediano_vs_mas_barata, ahorro_mediano_pct, "
        "n_observaciones",
        [
            "('v1', DATE '2026-07-13', 'CHEDRAUI', 'Chedraui', 'Grupo Comercial Chedraui', 1, 650.0, 640.0, 660.0, "
            "1, 0.0, 0.0, 100)",
            "('v1', DATE '2026-07-13', 'WAL-MART', 'Wal-mart', 'Walmart de México', 1, 690.0, 680.0, 700.0, 0, 40.0, "
            "5.8, 120)",
            "('v0', DATE '2026-07-06', 'SORIANA', 'Soriana', 'Organización Soriana', 1, 1.0, 1.0, 1.0, 0, 0.0, 0.0, 1)",
        ],
    ),
    "bi.bi_indice_canasta": (
        "canasta_version, semana_inicio, alcance, pares, indice_base_100",
        [
            "('v1', DATE '2026-07-13', 'Todas las cadenas de referencia', 2, 98.5)",
            "('v1', DATE '2026-07-13', 'Wal-mart', 1, 99.0)",
            "('v1', DATE '2026-07-13', 'Chedraui', 1, 98.0)",
        ],
    ),
    "bi.bi_diferencias_producto_semanal": (
        "canasta_version, semana_inicio, articulo_id, celdas_comparadas, diferencia_acumulada, "
        "celdas_con_sobreprecio, sobreprecio_mediano_pct, precio_unitario_mediano",
        ["('v1', DATE '2026-07-13', 'ARROZ', 1, 3.456, 1, 12.0, 22.1234)"],
    ),
    "bi.bi_disponibilidad_semanal": (
        "canasta_version, semana_inicio, cadena_key, articulo_id, celdas, celdas_con_articulo, n_observaciones",
        ["('v1', DATE '2026-07-13', 'WAL-MART', 'HUEVO_BLANCO', 2, 1, 5)"],
    ),
    "bi.bi_disponibilidad_articulos": (
        "canasta_version, semana_inicio, geografia_id, cadena_key, articulo_id, disponible",
        [
            "('v1', DATE '2026-07-13', 'geo-jal', 'WAL-MART', 'HUEVO_BLANCO', false)",
            "('v1', DATE '2026-07-13', 'geo-agu', 'WAL-MART', 'HUEVO_BLANCO', true)",
        ],
    ),
    "marts.mart_ahorro_por_cadena": (
        "canasta_version, semana_inicio, geografia_id, cadena_key, posicion, costo_canasta, ahorro_vs_mas_barata, "
        "ahorro_pct, cadenas_comparadas",
        [
            "('v1', DATE '2026-07-13', 'geo-jal', 'WAL-MART', 2, 690.0, 40.0, 5.8, 2)",
            "('v1', DATE '2026-07-13', 'geo-jal', 'CHEDRAUI', 1, 650.0, 0.0, 0.0, 2)",
        ],
    ),
    "marts.mart_precio_producto": (
        "canasta_version, semana_inicio, cadena_key, articulo_id, mediana_precio_unitario",
        [
            "('v1', DATE '2026-07-13', 'CHEDRAUI', 'ARROZ', 10.0)",
            "('v1', DATE '2026-07-13', 'CHEDRAUI', 'ARROZ', 20.0)",
        ],
    ),
    "marts.mart_cobertura_datos": (
        "canasta_version, semana_inicio, cadena_key, es_cadena_referencia, geografia_id, n_observaciones, "
        "n_establecimientos, n_dias_con_observacion, pct_atipicas, pct_no_comparables",
        [
            "('v1', DATE '2026-07-13', 'WAL-MART', true, 'geo-jal', 100, 1, 2, 0.5, 5.0)",
            "('v1', DATE '2026-07-13', 'LA COMER', false, 'geo-jal', 30, 1, 1, 0.0, 10.0)",
            "('v1', DATE '2026-07-13', 'LEY', false, 'geo-jal', 20, 2, 3, 1.0, 20.0)",
        ],
    ),
    "marts.mart_canasta_semanal": (
        "canasta_version, semana_inicio, geografia_id, cadena_key, es_cadena_referencia, es_canasta_completa",
        [
            "('v1', DATE '2026-07-13', 'geo-jal', 'WAL-MART', true, false)",
            "('v1', DATE '2026-07-20', 'geo-jal', 'CHEDRAUI', true, true)",
            "('v1', DATE '2026-07-13', 'geo-jal', 'LA COMER', false, true)",
        ],
    ),
}


@pytest.fixture
def base(tmp_path: Path) -> Path:
    ruta = tmp_path / "dashboard.duckdb"
    con = duckdb.connect(str(ruta))
    for esquema in {t.split(".")[0] for t in TABLAS}:
        con.execute(f"CREATE SCHEMA {esquema}")
    for tabla, (columnas, filas) in TABLAS.items():
        con.execute(f"CREATE TABLE {tabla} AS SELECT * FROM (VALUES {', '.join(filas)}) AS t({columnas})")
    con.close()
    return ruta


@pytest.fixture
def datos(base: Path) -> dict:
    con = duckdb.connect(str(base), read_only=True)
    try:
        return datos_dashboard.extraer(con)
    finally:
        con.close()


def _fila(conjunto: dict, i: int) -> dict:
    return {columna: valores[i] for columna, valores in conjunto.items()}


def test_extrae_solo_la_version_vigente_con_catalogos_indexados(datos):
    assert datos["meta"]["canasta_version"] == "v1"
    assert datos["semanas"] == ["2026-07-13", "2026-07-20"]
    # Orden fijo de la paleta (Wal-mart primero) y sin la cadena de la versión anterior.
    assert [c["key"] for c in datos["cadenas"]] == ["WAL-MART", "CHEDRAUI"]
    assert [a["id"] for a in datos["articulos"]] == ["ARROZ", "HUEVO_BLANCO"]
    assert [g["estado"] for g in datos["geografia"]] == ["Aguascalientes", "Jalisco"]

    costo = datos["costo_cadena"]
    walmart = next(_fila(costo, i) for i in range(len(costo["s"])) if costo["c"][i] == 0)
    assert walmart["costo_mediano"] == 690 and walmart["s"] == 0
    assert datos["ahorro_semanal"]["cadena_mas_barata_mas_frecuente"] == [0, 1]
    assert datos["indice"]["alcance"] == [2, 0, 1]  # Chedraui, Todas, Wal-mart (orden alfabético del alcance)


def test_agregaciones_propias_del_dashboard(datos):
    precio = datos["precio_articulo"]
    assert _fila(precio, 0) == {"s": 0, "c": 1, "a": 0, "mediana_precio_unitario": 15, "municipios": 2}

    cobertura = datos["cobertura"]
    otras = next(_fila(cobertura, i) for i in range(len(cobertura["s"])) if cobertura["c"][i] == 2)
    assert otras == {
        "s": 0,
        "g": 1,
        "c": 2,  # índice len(cadenas): grupo "otras cadenas"
        "n_observaciones": 50,
        "filas": 2,
        "n_establecimientos": 3,
        "n_dias_con_observacion": 4,
        "pct_atipicas": 1,
        "pct_no_comparables": 30,
    }
    assert datos["meta"]["cadenas_no_referencia"] == 2

    assert datos["canasta"]["es_canasta_completa"] == [0, 1]  # solo cadenas de referencia
    assert _fila(datos["faltantes"], 0) == {"s": 0, "g": 1, "c": 0, "a": 1}
    assert len(datos["faltantes"]["s"]) == 1
    assert datos["diferencias"]["precio_unitario_mediano"] == [22.123]


def test_validar_detecta_indices_fuera_de_catalogo_y_columnas_desiguales(datos):
    datos_dashboard.validar(datos)

    datos["ahorro_municipio"]["g"][0] = 99
    datos["disponibilidad"]["celdas"].append(1)
    with pytest.raises(ValueError) as error:
        datos_dashboard.validar(datos)
    assert "ahorro_municipio.g: índices fuera de geografia" in str(error.value)
    assert "disponibilidad: columnas de distinto largo" in str(error.value)


def test_llave_desconocida_detiene_la_extraccion(base):
    con = duckdb.connect(str(base))
    con.execute(
        "INSERT INTO marts.mart_ahorro_por_cadena VALUES ('v1', DATE '2026-07-13', 'geo-x', 'CHEDRAUI', 1, 1, 0, 0, 2)"
    )
    with pytest.raises(ValueError, match="geografia_id: valores fuera del catálogo"):
        datos_dashboard.extraer(con)
    con.close()


def test_renderizar_escapa_los_datos_y_arma_documento_o_fragmento(datos):
    datos["articulos"][0]["nombre"] = "Arroz </script><script>alert(1)</script>"
    completo = generar.renderizar(datos)
    fragmento = generar.renderizar(datos, completo=False)

    assert completo.startswith('<!doctype html>\n<html lang="es">')
    assert "<title>Precios de la canasta QQP</title>" in completo.split("</head>")[0]
    assert "<html" not in fragmento and "<body" not in fragmento
    assert "</script><script>alert" not in completo

    carga = re.search(r'<script type="application/json" id="datos-qqp">(.*?)</script>', completo, re.DOTALL)
    assert json.loads(carga.group(1)) == json.loads(json.dumps(datos))

    with pytest.raises(ValueError, match="exactamente una vez"):
        generar.renderizar(datos, plantilla="<p>sin marcas</p>")


def test_la_plantilla_solo_lee_columnas_que_existen(datos):
    """Contrato entre el JavaScript de la plantilla y los conjuntos que produce Python."""
    js = generar.PLANTILLA.read_text(encoding="utf-8").split("<script>", 1)[1]

    for conjunto in set(re.findall(r"\bD\.(\w+)", js)):
        assert conjunto in datos, f"D.{conjunto} no existe"
    alias = defaultdict(set)
    for nombre, conjunto in re.findall(r"\b(?:const|let)\s+(\w+)\s*=\s*D\.(\w+)\b", js):
        alias[nombre].add(conjunto)
    for nombre, columna in re.findall(r"\b(\w+)\.(\w+)\[", js):
        if nombre in alias and not isinstance(datos[next(iter(alias[nombre]))], list):
            assert any(columna in datos[c] for c in alias[nombre]), (
                f"{nombre}.{columna} no existe en {alias[nombre]}"
            )
    for campo in re.findall(r"\bD\.meta\.(\w+)", js):
        assert campo in datos["meta"]
    iniciar = js.split("function iniciar()", 1)[1]
    for campo in re.findall(r"\bm\.(\w+)", iniciar):
        assert campo in datos["meta"], f"meta.{campo} no existe"
    for catalogo, patron in [
        ("geografia", r"D\.geografia\[[^\[\]]+\]\.(\w+)|\bgeo\.(\w+)"),
        ("cadenas", r"D\.cadenas\[[^\[\]]+\]\.(\w+)"),
        ("articulos", r"D\.articulos\[[^\[\]]+\]\.(\w+)|\bart\.(\w+)"),
    ]:
        for grupos in re.findall(patron, js):
            campo = next(g for g in grupos if g) if isinstance(grupos, tuple) else grupos
            assert campo in datos[catalogo][0], f"{catalogo}.{campo} no existe"


def test_run_escribe_documento_y_fragmento(base, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generar, "connect", lambda read_only: duckdb.connect(str(base), read_only=read_only))
    destino = generar.run(tmp_path / "dashboard" / "index.html", fragmento=tmp_path / "fragmento.html")

    assert destino.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "__DATOS_QQP__" not in (tmp_path / "fragmento.html").read_text(encoding="utf-8")
    assert "canasta v1 · 2 semanas hasta 2026-07-20 · datos al 2026-07-31" in capsys.readouterr().out


def test_el_dashboard_se_genera_antes_de_publicar():
    assert cli.PIPELINE.index("resultados") < cli.PIPELINE.index("dashboard") < cli.PIPELINE.index("publish")
