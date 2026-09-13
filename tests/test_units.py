import pytest

from src.normalize.units import interpretar


@pytest.mark.parametrize(
    "texto", ["LECHE ENTERA 1 L", "LECHE ENT. 1000 ML", "LECHE ENTERA 1LT", "Caja 1 Lt. Entera"]
)
def test_ejemplos_de_leche_son_comparables(texto):
    p = interpretar(texto)
    assert (p.unidad_base, p.contenido_base, p.requiere_revision) == ("l", 1.0, False)


@pytest.mark.parametrize(
    ("texto", "unidad", "contenido"),
    [
        ("1 Kg. Granel. Alfa/blanca", "kg", 1.0),
        ("Bolsa 900 Gr. Super Extra", "kg", 0.9),
        ("Botella 850 Ml. Vegetal. Sabor Mantequilla", "l", 0.85),
        ("Lata 140 Gr. Aleta Amarilla en Hojuelas en Agua", "kg", 0.14),
        ("Botella 1.36 Lt. Liquido. Delicada", "l", 1.36),
        ("Bolsa Plástico 2 Kg. Estándar o Morena", "kg", 2.0),
        ("Barra 350 Gr.con Envoltura. (rosa)", "kg", 0.35),
        ("1 Kg. Granel. Molida Top Sirlion 90/10 o de Sirlion 90/10", "kg", 1.0),
        ("Botella 500 Ml. 30 Meq. Sabor Coco", "l", 0.5),
        ("Paquete con 2 Pinguinos (80 Gr.)", "kg", 0.08),
    ],
)
def test_cantidad_explicita(texto, unidad, contenido):
    p = interpretar(texto)
    assert p.unidad_base == unidad
    assert p.contenido_base == pytest.approx(contenido)
    assert not p.requiere_revision


def test_empaque_multiple():
    p = interpretar("Paquete con 12 Latas de 355 Ml. C/u")
    assert (p.unidad_base, p.unidades_empaque, p.regla) == ("l", 12, "empaque_multiple")
    assert p.contenido_base == pytest.approx(4.26)
    assert not p.requiere_revision


def test_empaque_multiple_confirmado_por_total_explicito():
    p = interpretar("Caja 200 Gr. (50 Sobres de 4 Gr. C/u). Mascabado")
    assert p.contenido_base == pytest.approx(0.2)
    assert p.confianza == "alta"


def test_empaque_inconsistente_con_total_va_a_revision():
    p = interpretar("Caja 300 Gr. (50 Sobres de 4 Gr. C/u)")
    assert p.requiere_revision
    assert p.motivo_revision == "empaque_inconsistente_con_total"


@pytest.mark.parametrize(
    ("texto", "contenido", "subtipo"),
    [
        ("Paquete C/18 Blanco", 18, "PIEZA"),
        ("Paquete 4 Rollos. 200 Hojas Dobles", 4, "ROLLO"),
        ("Bolsa 14 Piezas. Invisible. Delgada con Alas", 14, "PIEZA"),
        ("Pieza", 1, "PIEZA"),
        ("Manojo. Cambray", 1, "MANOJO"),
    ],
)
def test_conteos(texto, contenido, subtipo):
    p = interpretar(texto)
    assert (p.unidad_base, p.contenido_base, p.subtipo_conteo) == ("pieza", contenido, subtipo)
    assert not p.requiere_revision


def test_pieza_con_rango_de_peso_se_cuenta_por_pieza():
    p = interpretar("Concha. Pieza de 68 a 90 Gr. (12 Cm. de Diámetro Aprox.)")
    assert (p.unidad_base, p.contenido_base, p.regla) == ("pieza", 1.0, "pieza_con_rango_de_peso")


@pytest.mark.parametrize(
    ("texto", "motivo"),
    [
        ("Paquete 800 Ó 880 Gr.", "cantidades_alternativas"),
        ("Frasco Gotero 24 Ml. 1.000 G., Solución Gotas", "dimensiones_mixtas"),
        ("Caja", "sin_cantidad"),
        ("Bolsa 1 Kg. Contiene 900 Gr.", "multiples_cantidades"),
    ],
)
def test_ambiguedades_van_a_revision(texto, motivo):
    p = interpretar(texto)
    assert p.requiere_revision
    assert p.motivo_revision == motivo


def test_separador_ambiguo_depende_de_la_unidad():
    gramos = interpretar("Bolsa 3.564 Gr. Polvo. Limpieza Instantánea")
    litros = interpretar("Botella 3.785 Lt. Entera")
    assert gramos.contenido_base == pytest.approx(3.564)  # 3,564 g
    assert litros.contenido_base == pytest.approx(3.785)  # 3.785 l
    assert gramos.motivo_revision == litros.motivo_revision == "separador_ambiguo"


def test_total_con_desglose_no_requiere_revision():
    p = interpretar("Caja 85 Gr. (35 Gr. Flan y 50 Gr. Caramelo). con Caramelo. Sabor Vainilla")
    assert (p.contenido_base, p.regla, p.requiere_revision) == (
        0.085,
        "cantidad_explicita_con_desglose",
        False,
    )


@pytest.mark.parametrize(
    ("texto", "motivo"),
    [
        ("Paquete 40 o 44 Piezas. Grande", "cantidades_alternativas"),
        ("Paquete 1 Kg. Ó 1.1 Kg.", "cantidades_alternativas"),
        ("Paquete 10 Cajas. 50 Piezas C/u", "conteo_por_unidad_de_empaque"),
    ],
)
def test_conteos_ambiguos_van_a_revision(texto, motivo):
    p = interpretar(texto)
    assert p.requiere_revision
    assert p.motivo_revision == motivo


@pytest.mark.parametrize(
    ("texto", "contenido", "subtipo"),
    [
        ("Paquete con 2. Venus. Sensitive", 2, "PIEZA"),
        ("Paquete con 30. Toallitas Húmedas", 30, "PIEZA"),
        ("Paquete 420 Hojas", 420, "HOJA"),
    ],
)
def test_conteos_adicionales(texto, contenido, subtipo):
    p = interpretar(texto)
    assert (p.unidad_base, p.contenido_base, p.subtipo_conteo, p.requiere_revision) == (
        "pieza",
        contenido,
        subtipo,
        False,
    )


def test_no_confunde_miligramos_con_gramos():
    p = interpretar("Caja con 30 Tabletas de 50 Mg.")
    assert (p.unidad_base, p.contenido_base, p.subtipo_conteo) == ("pieza", 30.0, "TABLETA")
