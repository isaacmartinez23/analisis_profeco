import pytest

from src import alertas, cli


@pytest.fixture(autouse=True)
def _restaurar_modo(monkeypatch):
    # cli.main fija QQP_MODO en os.environ; monkeypatch lo restaura al terminar cada prueba.
    monkeypatch.delenv("QQP_MODO", raising=False)


def test_falla_de_un_paso_alerta_y_propaga_el_error(monkeypatch):
    llamadas = []

    def paso_que_falla():
        raise SystemExit("dbt test falló (código 1)")

    monkeypatch.setitem(cli.PASOS, "dbt-test", paso_que_falla)
    monkeypatch.setattr(alertas, "run", lambda **kw: llamadas.append(kw))

    with pytest.raises(SystemExit, match="dbt test falló"):
        cli.main(["--muestra", "dbt-test"])

    assert llamadas == [
        {"estado": "fallo", "paso": "dbt-test", "detalle": "SystemExit: dbt test falló (código 1)"}
    ]


def test_error_al_alertar_no_oculta_el_error_original(monkeypatch):
    def paso_que_falla():
        raise RuntimeError("fallo del paso")

    def alerta_rota(**kw):
        raise OSError("sin red")

    monkeypatch.setitem(cli.PASOS, "normalize", paso_que_falla)
    monkeypatch.setattr(alertas, "run", alerta_rota)

    with pytest.raises(RuntimeError, match="fallo del paso"):
        cli.main(["--muestra", "normalize"])


def test_inspect_avisa_columnas_adicionales_y_detiene_cambios_no_revisados(
    monkeypatch, capsys, tmp_path, csv_utf8_bom, csv_columnas_adicionales
):
    from src import config

    monkeypatch.setattr(config, "ES_MUESTRA", True)
    monkeypatch.setattr(config, "CSV_DIR", tmp_path)

    cli.paso_inspect()
    salida = capsys.readouterr().out
    assert "06-2026_Q1.csv: columnas adicionales conocidas ['folio', 'cv_producto', 'cv_marca']" in salida
    assert "esquema válido en 2 archivos" in salida

    contenido = csv_columnas_adicionales.read_bytes().replace(b"cv_marca", b"cv_tienda")
    csv_columnas_adicionales.write_bytes(contenido)
    with pytest.raises(SystemExit, match="06-2026_Q1.csv: encabezado distinto"):
        cli.paso_inspect()


def test_desde_reanuda_en_el_paso_indicado(monkeypatch):
    ejecutados = []
    for nombre in cli.PIPELINE:
        monkeypatch.setitem(cli.PASOS, nombre, lambda nombre=nombre: ejecutados.append(nombre))

    cli.main(["--muestra", "pipeline", "--desde", "validate"])

    assert ejecutados == ["validate", "resultados", "publish", "alertas"]
