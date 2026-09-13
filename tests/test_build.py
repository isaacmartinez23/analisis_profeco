import pandas as pd

from src import config
from src.normalize import build


def test_correccion_manual_sin_interrogacion_se_agrega(tmp_path, monkeypatch):
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "texto_correcciones_manual.csv").write_text(
        "columna,valor_original,valor_corregido,decidido_por,fecha,justificacion\n"
        "cadena_comercial,Central de Abastos,Central de Abasto,prueba,2026-09-12,variante plural\n"
        "giro,Papeler?as,Papelerías,prueba,2026-09-12,confirma automática\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "MANUAL_MAPPINGS_DIR", manual)
    distintos = {
        "giro": pd.DataFrame({"valor": ["Papeler?as", "Papelerías"]}),
        "cadena_comercial": pd.DataFrame({"valor": ["Central de Abastos", "Central de Abasto"]}),
    }

    correcciones = build.construir_correcciones(distintos).set_index(["columna", "valor_original"])

    assert (
        correcciones.loc[("cadena_comercial", "Central de Abastos"), "valor_corregido"] == "Central de Abasto"
    )
    assert correcciones.loc[("cadena_comercial", "Central de Abastos"), "metodo"] == "manual"
    assert correcciones.loc[("giro", "Papeler?as"), "metodo"] == "manual"
    assert len(correcciones) == 2


def test_corrige_caracteres_perdidos_en_la_geografia(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MANUAL_MAPPINGS_DIR", tmp_path)
    assert {"estado", "municipio"} <= set(build.COLUMNAS_CORRECCION)
    distintos = {"municipio": pd.DataFrame({"valor": ["Coyoac?n", "Coyoacán", "COYOACAN", "Juárez"]})}

    correcciones = build.construir_correcciones(distintos)

    assert correcciones[["valor_original", "valor_corregido", "metodo"]].to_dict("records") == [
        {"valor_original": "Coyoac?n", "valor_corregido": "Coyoacán", "metodo": "auto_candidato_unico"}
    ]
