"""Alertas y resumen de ejecución.

- Escribe un resumen en Markdown: estado, reglas de calidad en alerta o falla, validación independiente y cifras
  clave. En GitHub Actions se agrega a ``$GITHUB_STEP_SUMMARY``; en local se imprime.
- Si ``ALERTA_WEBHOOK_URL`` está configurada, envía el resumen como JSON compatible con Slack (``text``), Microsoft
  Teams y Discord (``content``). Se notifica siempre ante fallas y, salvo ``ALERTA_SOLO_FALLOS=1``, también
  cuando hay reglas de calidad en alerta.
- Un error al enviar la alerta nunca oculta el error original del pipeline: se registra y se continúa.

Uso::

    python -m src.alertas --estado exito
    python -m src.alertas --estado fallo --paso dbt-test --detalle "dbt test falló"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime

import pandas as pd

from src import config


def _url_ejecucion() -> str | None:
    servidor, repo, run = (os.getenv(v) for v in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return f"{servidor}/{repo}/actions/runs/{run}" if servidor and repo and run else None


def _calidad() -> pd.DataFrame:
    partes = []
    for etapa in ("raw", "marts"):
        path = config.REPORTS_OUT_DIR / f".calidad_{etapa}.parquet"
        if path.exists():
            partes.append(pd.read_parquet(path))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def _validacion() -> str | None:
    path = config.REPORTS_OUT_DIR / "validacion_canasta.md"
    if not path.exists():
        return None
    m = re.search(r"\*\*Resultado: (.+?)\*\*", path.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _cifras() -> dict[str, str]:
    if not config.DUCKDB_PATH.exists():
        return {}
    try:
        from src.db import connect

        with connect(config.DUCKDB_PATH, read_only=True) as con:
            fila = con.execute(
                """SELECT (SELECT max(fecha) FROM core.dim_fecha),
                          (SELECT max(semana_inicio) FROM bi.bi_ahorro_semanal),
                          (SELECT round(median(ahorro_maximo_mediano), 2) FROM bi.bi_ahorro_semanal
                           WHERE semana_inicio > (SELECT max(semana_inicio) - 28 FROM bi.bi_ahorro_semanal)),
                          (SELECT indice_base_100 FROM bi.bi_indice_canasta
                           WHERE alcance = 'Todas las cadenas de referencia' ORDER BY semana_inicio DESC LIMIT 1)"""
            ).fetchone()
    except Exception as exc:  # el resumen no debe fallar por no poder leer la base
        return {"aviso": f"no se pudieron leer cifras: {type(exc).__name__}"}
    return {
        "última fecha con datos": str(fila[0]),
        "última semana publicada": str(fila[1]),
        "ahorro máximo mediano (últimas 4 semanas)": f"${fila[2]}",
        "índice de la canasta (base 100)": str(fila[3]),
    }


def construir_resumen(estado: str, paso: str | None = None, detalle: str | None = None) -> tuple[str, int]:
    calidad = _calidad()
    no_cumplen = calidad[calidad["resultado"] != "cumple"] if len(calidad) else calidad
    icono = {"exito": "✅", "fallo": "❌"}.get(estado, "ℹ️")
    lineas = [
        f"## {icono} Pipeline PROFECO QQP · {estado}",
        "",
        f"- Fecha: {datetime.now():%Y-%m-%d %H:%M} · modo `{config.MODO}`",
    ]
    if url := _url_ejecucion():
        lineas.append(f"- Ejecución: {url}")
    if paso:
        lineas.append(f"- Paso: `{paso}`")
    if detalle:
        lineas.append(f"- Detalle: {detalle}")
    if validacion := _validacion():
        lineas.append(f"- Validación independiente: {validacion}")
    for nombre, valor in _cifras().items():
        lineas.append(f"- {nombre}: {valor}")
    lineas.append("")
    if len(no_cumplen):
        lineas += ["### Reglas de calidad en alerta o falla", ""]
        lineas += [
            f"- `{r.id}` {r.regla}: {r.valor} (esperado {r.condicion}) → **{r.resultado}**"
            for r in no_cumplen.itertuples()
        ]
    elif len(calidad):
        lineas.append(f"Todas las reglas de calidad cumplen ({len(calidad)}).")
    return "\n".join(lineas) + "\n", len(no_cumplen)


def enviar_webhook(texto: str, url: str | None = None) -> bool:
    url = url or os.getenv("ALERTA_WEBHOOK_URL")
    if not url:
        return False
    cuerpo = json.dumps({"text": texto, "content": texto[:1900]}).encode("utf-8")
    peticion = urllib.request.Request(
        url, data=cuerpo, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15) as respuesta:
            return 200 <= respuesta.status < 300
    except Exception as exc:
        print(f"[alertas] no se pudo enviar la alerta al webhook: {type(exc).__name__}", flush=True)
        return False


def run(estado: str, paso: str | None = None, detalle: str | None = None) -> str:
    texto, en_alerta = construir_resumen(estado, paso, detalle)
    if destino := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(destino, "a", encoding="utf-8") as fh:
            fh.write(texto)
    else:
        print(texto, flush=True)
    solo_fallos = os.getenv("ALERTA_SOLO_FALLOS") == "1"
    if estado == "fallo" or (en_alerta and not solo_fallos):
        enviado = enviar_webhook(texto)
        print(
            f"[alertas] notificación {'enviada' if enviado else 'no enviada (sin webhook configurado)'}",
            flush=True,
        )
    return texto


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--estado", choices=["exito", "fallo"], required=True)
    parser.add_argument("--paso")
    parser.add_argument("--detalle")
    args = parser.parse_args(argv)
    run(args.estado, args.paso, args.detalle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
