from collections import defaultdict

from src.analysis.validacion import _originales_corregidos


def test_incluye_grafias_con_caracteres_perdidos_que_corrigen_a_la_llave():
    correcciones = defaultdict(dict)
    correcciones["municipio"] = {"Coyoac?n": "Coyoacán", "Le?n": "León"}
    correcciones["producto"] = {"Az?car": "Azúcar", "Caf?": "Café"}

    assert _originales_corregidos(correcciones, "municipio", {"COYOACAN"}) == ["Coyoac?n"]
    assert _originales_corregidos(correcciones, "producto", {"AZUCAR", "ARROZ"}) == ["Az?car"]
    assert _originales_corregidos(correcciones, "estado", {"JALISCO"}) == []
