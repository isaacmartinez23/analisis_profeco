"""Publicación atómica de marts y vistas BI de DuckDB a Supabase/PostgreSQL.

Configuración exclusivamente por variables de entorno (ver ``.env.example``); nada de credenciales en el código.

Flujo (D-029):

1. Verifica en DuckDB que existan todas las tablas a publicar y registra la publicación en
   ``qqp_meta.publicaciones`` con estado ``en_proceso``.
2. Crea el esquema temporal ``<esquema>_carga``, crea cada tabla con tipos equivalentes y copia las filas con
   ``COPY``; verifica que el número de filas coincida con DuckDB y crea índices.
3. En **una sola transacción** renombra el esquema publicado a ``<esquema>_anterior``, el temporal a
   ``<esquema>``, borra el anterior y otorga lectura al rol de consulta (si se configuró). Looker Studio nunca ve
   una publicación a medias; si algo falla, la versión anterior queda intacta.
4. Marca la publicación como ``exitosa`` o ``fallida``.

Solo se ejecuta si el pipeline llegó hasta aquí sin errores (pruebas dbt, calidad y validación independiente).

Uso::

    python -m src.publish.postgres
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg import sql

from src import config
from src.db import connect

VARIABLES = [
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PORT",
    "SUPABASE_DB_NAME",
    "SUPABASE_DB_USER",
    "SUPABASE_DB_PASSWORD",
]
LOTE = 50_000


@dataclass(frozen=True)
class Tabla:
    origen: str  # esquema.tabla en DuckDB
    indices: tuple[tuple[str, ...], ...] = ()
    filtro: str | None = None

    @property
    def nombre(self) -> str:
        return self.origen.split(".")[1]


TABLAS = [
    Tabla("marts.mart_canasta_semanal", (("semana_inicio",), ("cadena_key", "geografia_id"))),
    Tabla("marts.mart_ahorro_por_cadena", (("semana_inicio",), ("geografia_id",))),
    Tabla(
        "marts.mart_precio_producto", (("semana_inicio",), ("articulo_id",), ("geografia_id", "cadena_key"))
    ),
    Tabla("marts.mart_cobertura_datos", (("semana_inicio",), ("cadena_key", "geografia_id"))),
    Tabla("bi.bi_costo_semanal_cadena", (("semana_inicio",),)),
    Tabla("bi.bi_ahorro_semanal", (("semana_inicio",),)),
    Tabla("bi.bi_diferencias_producto_semanal", (("semana_inicio",), ("articulo_id",))),
    Tabla(
        "bi.bi_disponibilidad_articulos",
        (("semana_inicio",), ("articulo_id",), ("cadena_key", "geografia_id")),
    ),
    Tabla("bi.bi_indice_canasta", (("semana_inicio",),)),
    Tabla("core.dim_canasta", (), "es_version_vigente"),
    Tabla("core.dim_geografia", ()),
]


@dataclass
class ConfigPostgres:
    host: str | None = None
    port: str | None = None
    dbname: str | None = None
    user: str | None = None
    password: str | None = field(default=None, repr=False)
    sslmode: str = "require"
    esquema: str = "qqp"
    rol_lectura: str | None = None

    @classmethod
    def desde_entorno(cls) -> ConfigPostgres:
        return cls(
            host=os.getenv("SUPABASE_DB_HOST") or None,
            port=os.getenv("SUPABASE_DB_PORT") or None,
            dbname=os.getenv("SUPABASE_DB_NAME") or None,
            user=os.getenv("SUPABASE_DB_USER") or None,
            password=os.getenv("SUPABASE_DB_PASSWORD") or None,
            sslmode=os.getenv("SUPABASE_DB_SSLMODE") or "require",
            esquema=os.getenv("QQP_PG_SCHEMA") or "qqp",
            rol_lectura=os.getenv("QQP_PG_ROL_LECTURA") or None,
        )

    def faltantes(self) -> list[str]:
        valores = dict(
            zip(VARIABLES, [self.host, self.port, self.dbname, self.user, self.password], strict=True)
        )
        return [nombre for nombre, valor in valores.items() if not valor]

    def conninfo(self) -> str:
        return psycopg.conninfo.make_conninfo(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            sslmode=self.sslmode,
            connect_timeout=30,
            application_name="profeco-canasta-pipeline",
        )

    def validar(self) -> None:
        for nombre in filter(None, [self.esquema, self.rol_lectura]):
            if not re.fullmatch(r"[a-z_][a-z0-9_]{0,50}", nombre):
                raise ValueError(f"Identificador no permitido: {nombre!r} (solo minúsculas, dígitos y _)")


def tipo_postgres(tipo_duckdb: str) -> str:
    """Traduce un tipo de DuckDB a PostgreSQL; falla ante tipos sin equivalente seguro."""
    t = tipo_duckdb.upper()
    if m := re.fullmatch(r"DECIMAL\((\d+),\s*(\d+)\)", t):
        return f"numeric({m.group(1)},{m.group(2)})"
    equivalentes = {
        "VARCHAR": "text",
        "BOOLEAN": "boolean",
        "TINYINT": "smallint",
        "SMALLINT": "smallint",
        "INTEGER": "integer",
        "BIGINT": "bigint",
        "FLOAT": "real",
        "DOUBLE": "double precision",
        "DATE": "date",
        "TIMESTAMP": "timestamp",
        "TIMESTAMP WITH TIME ZONE": "timestamptz",
    }
    if t not in equivalentes:
        raise TypeError(
            f"Tipo DuckDB sin equivalente en PostgreSQL: {tipo_duckdb} (convierte en el modelo dbt)"
        )
    return equivalentes[t]


def _columnas(con, tabla: Tabla) -> list[tuple[str, str]]:
    esquema, nombre = tabla.origen.split(".")
    filas = con.execute(
        """SELECT column_name, data_type FROM information_schema.columns
           WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position""",
        [esquema, nombre],
    ).fetchall()
    if not filas:
        raise RuntimeError(f"No existe {tabla.origen} en DuckDB: ejecuta dbt-run antes de publicar")
    return [(c, tipo_postgres(t)) for c, t in filas]


def _metadatos(con) -> dict:
    datos = con.execute(
        """SELECT (SELECT any_value(canasta_version) FROM marts.mart_canasta_semanal),
                  (SELECT max(semana_inicio) FROM marts.mart_canasta_semanal),
                  (SELECT max(fecha) FROM core.dim_fecha),
                  (SELECT max(cargado_utc) FROM raw.archivos),
                  (SELECT count(*) FROM raw.archivos)"""
    ).fetchone()
    return {
        "canasta_version": datos[0],
        "ultima_semana": str(datos[1]),
        "ultima_fecha_datos": str(datos[2]),
        "ultima_carga_utc": str(datos[3]),
        "archivos_fuente": datos[4],
        "modo": config.MODO,
        "commit_git": os.getenv("GITHUB_SHA"),
        "ejecucion_ci": os.getenv("GITHUB_RUN_ID"),
    }


def _preparar_meta(pg) -> None:
    pg.execute("CREATE SCHEMA IF NOT EXISTS qqp_meta")
    pg.execute(
        """CREATE TABLE IF NOT EXISTS qqp_meta.publicaciones (
               id_publicacion text PRIMARY KEY,
               iniciada_utc timestamptz NOT NULL,
               finalizada_utc timestamptz,
               estado text NOT NULL,
               esquema text NOT NULL,
               metadatos jsonb,
               filas jsonb,
               mensaje text)"""
    )


def _copiar_tabla(con, pg, tabla: Tabla, esquema_carga: str) -> int:
    columnas = _columnas(con, tabla)
    destino = sql.Identifier(esquema_carga, tabla.nombre)
    definicion = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(t)) for c, t in columnas
    )
    pg.execute(sql.SQL("CREATE TABLE {} ({})").format(destino, definicion))

    nombres = ", ".join(f'"{c}"' for c, _ in columnas)
    consulta = f"SELECT {nombres} FROM {tabla.origen}" + (f" WHERE {tabla.filtro}" if tabla.filtro else "")
    lector = con.execute(consulta)
    copiadas = 0
    copia = sql.SQL("COPY {} ({}) FROM STDIN").format(
        destino, sql.SQL(", ").join(sql.Identifier(c) for c, _ in columnas)
    )
    with pg.cursor().copy(copia) as cp:
        while lote := lector.fetchmany(LOTE):
            for fila in lote:
                cp.write_row(fila)
            copiadas += len(lote)

    esperadas = con.execute(
        f"SELECT count(*) FROM {tabla.origen}" + (f" WHERE {tabla.filtro}" if tabla.filtro else "")
    ).fetchone()[0]
    en_destino = pg.execute(sql.SQL("SELECT count(*) FROM {}").format(destino)).fetchone()[0]
    if not (copiadas == esperadas == en_destino):
        raise RuntimeError(
            f"{tabla.nombre}: DuckDB tiene {esperadas} filas, se copiaron {copiadas} y PostgreSQL tiene {en_destino}"
        )
    for i, cols in enumerate(tabla.indices):
        pg.execute(
            sql.SQL("CREATE INDEX {} ON {} ({})").format(
                sql.Identifier(f"ix_{tabla.nombre}_{i}"),
                destino,
                sql.SQL(", ").join(map(sql.Identifier, cols)),
            )
        )
    return en_destino


def publicar(cfg: ConfigPostgres, db_path: Path = config.DUCKDB_PATH) -> dict[str, int]:
    cfg.validar()
    esquema, carga, anterior = cfg.esquema, f"{cfg.esquema}_carga", f"{cfg.esquema}_anterior"
    id_publicacion = f"p{datetime.now(UTC):%Y%m%dT%H%M%S%f}-{uuid.uuid4().hex[:6]}"
    inicio = time.time()
    filas: dict[str, int] = {}

    with connect(db_path, read_only=True) as con, psycopg.connect(cfg.conninfo()) as pg:
        metadatos = _metadatos(con)
        for tabla in TABLAS:
            _columnas(con, tabla)  # falla antes de tocar PostgreSQL si falta una tabla o un tipo

        _preparar_meta(pg)
        pg.execute(
            "INSERT INTO qqp_meta.publicaciones (id_publicacion, iniciada_utc, estado, esquema, metadatos) "
            "VALUES (%s, now(), 'en_proceso', %s, %s)",
            [id_publicacion, esquema, json.dumps(metadatos)],
        )
        pg.commit()

        try:
            pg.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(carga)))
            pg.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(carga)))
            pg.commit()
            for tabla in TABLAS:
                filas[tabla.nombre] = _copiar_tabla(con, pg, tabla, carga)
                pg.commit()
                print(f"[publish] {tabla.nombre}: {filas[tabla.nombre]:,} filas", flush=True)

            pg.execute(
                sql.SQL(
                    "CREATE TABLE {} AS SELECT %s::text AS id_publicacion, now() AS publicado_utc, *"
                ).format(sql.Identifier(carga, "metadatos"))
                + sql.SQL(" FROM jsonb_to_record(%s::jsonb) AS m(canasta_version text, ultima_semana date, ")
                + sql.SQL("ultima_fecha_datos date, ultima_carga_utc text, archivos_fuente int, modo text, ")
                + sql.SQL("commit_git text, ejecucion_ci text)"),
                [id_publicacion, json.dumps(metadatos)],
            )

            # Intercambio atómico: todo o nada.
            pg.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(anterior)))
            existe = pg.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", [esquema]).fetchone()
            if existe:
                pg.execute(
                    sql.SQL("ALTER SCHEMA {} RENAME TO {}").format(
                        sql.Identifier(esquema), sql.Identifier(anterior)
                    )
                )
            pg.execute(
                sql.SQL("ALTER SCHEMA {} RENAME TO {}").format(sql.Identifier(carga), sql.Identifier(esquema))
            )
            pg.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(anterior)))
            if cfg.rol_lectura:
                pg.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(esquema), sql.Identifier(cfg.rol_lectura)
                    )
                )
                pg.execute(
                    sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(
                        sql.Identifier(esquema), sql.Identifier(cfg.rol_lectura)
                    )
                )
            pg.execute(
                "UPDATE qqp_meta.publicaciones SET estado = 'exitosa', finalizada_utc = now(), filas = %s "
                "WHERE id_publicacion = %s",
                [json.dumps(filas), id_publicacion],
            )
            pg.commit()
        except Exception as exc:
            pg.rollback()
            pg.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(carga)))
            pg.execute(
                "UPDATE qqp_meta.publicaciones SET estado = 'fallida', finalizada_utc = now(), mensaje = %s "
                "WHERE id_publicacion = %s",
                [str(exc)[:2000], id_publicacion],
            )
            pg.commit()
            raise

    print(
        f"[publish] publicación {id_publicacion} exitosa en esquema '{esquema}': {len(filas)} tablas, "
        f"{sum(filas.values()):,} filas ({time.time() - inicio:.0f}s)",
        flush=True,
    )
    return filas


def run() -> dict[str, int] | None:
    cfg = ConfigPostgres.desde_entorno()
    if faltantes := cfg.faltantes():
        print(
            "[publish] Supabase no está configurado (faltan "
            + ", ".join(faltantes)
            + "). Los marts quedaron "
            "creados y validados en DuckDB; no se publicó nada.",
            flush=True,
        )
        return None
    return publicar(cfg)


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
