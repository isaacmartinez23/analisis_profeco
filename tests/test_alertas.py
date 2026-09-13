import json
from pathlib import Path

import pandas as pd

from src import alertas, config


def _preparar_calidad(tmp_path: Path, monkeypatch, resultado: str) -> None:
    monkeypatch.setattr(config, "REPORTS_OUT_DIR", tmp_path)
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp_path / "no_existe.duckdb")
    pd.DataFrame(
        [
            {
                "id": "M-08",
                "regla": "dias_desde_ultimo_dato",
                "valor": 106.0,
                "condicion": "<= 35",
                "resultado": resultado,
            }
        ]
    ).to_parquet(tmp_path / ".calidad_marts.parquet")


def test_resumen_lista_reglas_en_alerta(tmp_path, monkeypatch):
    _preparar_calidad(tmp_path, monkeypatch, "alerta")
    texto, en_alerta = alertas.construir_resumen("exito")
    assert en_alerta == 1
    assert "M-08" in texto and "alerta" in texto


def test_falla_notifica_al_webhook_y_escribe_resumen_de_github(tmp_path, monkeypatch):
    _preparar_calidad(tmp_path, monkeypatch, "cumple")
    enviados = []

    class Respuesta:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def abrir(peticion, timeout):
        enviados.append(json.loads(peticion.data))
        return Respuesta()

    resumen = tmp_path / "summary.md"
    monkeypatch.setenv("ALERTA_WEBHOOK_URL", "https://hooks.ejemplo/abc")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen))
    monkeypatch.setattr(alertas.urllib.request, "urlopen", abrir)

    alertas.run("fallo", paso="dbt-test", detalle="SystemExit: dbt test falló")

    assert "dbt-test" in enviados[0]["text"] and enviados[0]["content"]
    assert "❌" in resumen.read_text(encoding="utf-8")


def test_error_del_webhook_no_propaga(monkeypatch):
    def abrir(peticion, timeout):
        raise OSError("sin red")

    monkeypatch.setattr(alertas.urllib.request, "urlopen", abrir)
    assert alertas.enviar_webhook("hola", url="https://hooks.ejemplo/abc") is False
