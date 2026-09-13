"""Pruebas del publicador.

Las pruebas de integración usan un PostgreSQL real: el de ``QQP_TEST_PG_DSN`` (servicio de GitHub Actions) o,
si no está definido, uno embebido con ``pgserver`` cuando está instalado. Si no hay ninguno, se omiten.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import psycopg
import pytest

from src.publish import postgres


def test_tipos_postgres():
    assert postgres.tipo_postgres("VARCHAR") == "text"
    assert postgres.tipo_postgres("DECIMAL(12,2)") == "numeric(12,2)"
    assert postgres.tipo_postgres("DOUBLE") == "double precision"
    with pytest.raises(TypeError, match="HUGEINT"):
        postgres.tipo_postgres("HUGEINT")


def test_sin_configuracion_no_publica(monkeypatch, capsys):
    for variable in postgres.VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    assert postgres.run() is None
    assert "no está configurado" in capsys.readouterr().out


def test_config_no_expone_password_y_valida_identificadores(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "secreto-de-prueba")
    cfg = postgres.ConfigPostgres.desde_entorno()
    assert "secreto-de-prueba" not in repr(cfg)
    with pytest.raises(ValueError):
        postgres.ConfigPostgres(esquema='qqp"; drop schema public; --').validar()


# --- Integración -------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dsn(tmp_path_factory):
    if dsn := os.getenv("QQP_TEST_PG_DSN"):
        yield dsn
        return
    pgserver = pytest.importorskip("pgserver", reason="sin QQP_TEST_PG_DSN ni pgserver instalado")
    servidor = pgserver.get_server(tmp_path_factory.mktemp("pg"), cleanup_mode="stop")
    yield servidor.get_uri()


def _config(dsn: str, esquema: str) -> postgres.ConfigPostgres:
    p = psycopg.conninfo.conninfo_to_dict(dsn)
    return postgres.ConfigPostgres(
        host=p.get("host", "localhost"),
        port=str(p.get("port", 5432)),
        dbname=p.get("dbname", "postgres"),
        user=p.get("user", "postgres"),
        password=p.get("password", "") or None,
        sslmode="disable",
        esquema=esquema,
    )


@pytest.fixture
def duckdb_minimo(tmp_path: Path, monkeypatch) -> Path:
    """Base DuckDB con la forma mínima de las tablas publicadas (sin correr dbt)."""
    db = tmp_path / "mini.duckdb"
    con = duckdb.connect(str(db))
    for esquema in ("raw", "core", "marts", "bi"):
        con.execute(f"CREATE SCHEMA {esquema}")
    con.execute(
        "CREATE TABLE raw.archivos AS SELECT 'QQP_2026/01-2026_Q1.csv' archivo, now()::TIMESTAMP cargado_utc"
    )
    con.execute("CREATE TABLE core.dim_fecha AS SELECT DATE '2026-05-29' fecha")
    for tabla in postgres.TABLAS:
        # Tres semanas consecutivas; solo la primera fila tiene el artículo disponible.
        con.execute(
            f"""CREATE TABLE {tabla.origen} AS
                SELECT 'v1' canasta_version, DATE '2026-05-25' - 7 * range::INT semana_inicio,
                       'WAL-MART' cadena_key, 'g1' geografia_id, 'ARROZ' articulo_id,
                       123.45::DECIMAL(12,2) costo, 'Querétaro' municipio, true es_version_vigente,
                       range = 0 disponible
                FROM range(3)"""
        )
    con.close()
    return db


def test_publicacion_atomica_y_reemplazo(dsn, duckdb_minimo):
    cfg = _config(dsn, "qqp_prueba")
    filas = postgres.publicar(cfg, duckdb_minimo)
    assert set(filas) == {t.nombre for t in postgres.TABLAS}
    assert filas.pop("bi_articulos_faltantes") == 2  # solo artículos no disponibles
    assert all(n == 3 for n in filas.values())

    postgres.publicar(cfg, duckdb_minimo)  # segunda publicación reemplaza, no duplica
    with psycopg.connect(dsn) as pg:
        assert pg.execute("SELECT count(*) FROM qqp_prueba.mart_canasta_semanal").fetchone()[0] == 3
        assert (
            pg.execute("SELECT municipio FROM qqp_prueba.mart_canasta_semanal LIMIT 1").fetchone()[0]
            == "Querétaro"
        )
        esquemas = {
            r[0] for r in pg.execute("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'qqp_prueba%'")
        }
        assert esquemas == {"qqp_prueba"}  # sin restos de carga ni versión anterior
        estados = [
            r[0] for r in pg.execute("SELECT estado FROM qqp_meta.publicaciones WHERE esquema = 'qqp_prueba'")
        ]
        assert estados.count("exitosa") >= 2
        assert pg.execute("SELECT canasta_version FROM qqp_prueba.metadatos").fetchone()[0] == "v1"


def test_detalle_limitado_a_semanas_recientes(dsn, duckdb_minimo):
    cfg = _config(dsn, "qqp_semanas")
    cfg.semanas_detalle = 2
    filas = postgres.publicar(cfg, duckdb_minimo)
    assert filas["mart_precio_producto"] == 2  # semanas 2026-05-25 y 2026-05-18
    assert filas["mart_canasta_semanal"] == 3  # tablas sin límite conservan toda la historia

    cfg.semanas_detalle = 0  # 0 = publicar todo
    assert postgres.publicar(cfg, duckdb_minimo)["mart_precio_producto"] == 3
    with psycopg.connect(dsn) as pg:
        assert pg.execute("SELECT semanas_detalle FROM qqp_semanas.metadatos").fetchone()[0] == 0


def test_falla_a_mitad_conserva_la_version_publicada(dsn, duckdb_minimo, monkeypatch):
    cfg = _config(dsn, "qqp_fallo")
    postgres.publicar(cfg, duckdb_minimo)

    original = postgres._copiar_tabla

    def copiar_y_fallar(con, pg, tabla, esquema_carga):
        if tabla.nombre == "bi_indice_canasta":
            raise RuntimeError("fallo simulado durante la carga")
        return original(con, pg, tabla, esquema_carga)

    monkeypatch.setattr(postgres, "_copiar_tabla", copiar_y_fallar)
    with pytest.raises(RuntimeError, match="fallo simulado"):
        postgres.publicar(cfg, duckdb_minimo)

    with psycopg.connect(dsn) as pg:
        # La publicación anterior sigue completa y visible; no quedó el esquema de carga.
        assert pg.execute("SELECT count(*) FROM qqp_fallo.bi_indice_canasta").fetchone()[0] == 3
        assert not pg.execute("SELECT 1 FROM pg_namespace WHERE nspname = 'qqp_fallo_carga'").fetchone()
        ultimo = pg.execute(
            "SELECT estado, mensaje FROM qqp_meta.publicaciones WHERE esquema = 'qqp_fallo' ORDER BY iniciada_utc DESC LIMIT 1"
        ).fetchone()
        assert ultimo[0] == "fallida" and "fallo simulado" in ultimo[1]
