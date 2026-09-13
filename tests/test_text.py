from src.normalize.text import corregir_interrogaciones, llave


def test_llave_unifica_acentos_mayusculas_y_espacios():
    assert llave("Ciudad de México") == llave("CIUDAD DE MEXICO") == "CIUDAD DE MEXICO"
    assert llave("  Paquete   1 Kg. ") == "PAQUETE 1 KG"
    assert llave("S/m") == llave("S/M")


def test_corrige_con_candidato_unico_y_prefiere_acentos():
    valores = ["Papelerías", "Papelerias", "Papeler?as", "Farmacias"]
    [c] = corregir_interrogaciones("giro", valores)
    assert c.valor_corregido == "Papelerías"
    assert not c.requiere_revision


def test_sin_candidato_se_manda_a_revision():
    [c] = corregir_interrogaciones("presentacion", ["Reparación (néctar de Miel?)", "Otra"])
    assert c.valor_corregido is None
    assert c.requiere_revision


def test_no_corrige_hacia_una_letra_ascii_distinta():
    [c] = corregir_interrogaciones("nombre", ["Pe?a", "Pera"])
    assert c.valor_corregido is None


def test_candidatos_distintos_no_se_corrigen():
    [c] = corregir_interrogaciones("nombre", ["Pe?a", "Peña", "Peóa"])
    assert c.valor_corregido is None
    assert c.candidatos == 2
