"""Interpretación de presentaciones: contenido en unidad base (kg, l o pieza).

Principio: no se inventan equivalencias. Cuando el texto es ambiguo (cantidades
alternativas, dimensiones mixtas, separador de miles dudoso, varias cantidades
distintas) se devuelve la mejor lectura disponible con ``requiere_revision=True``
y un motivo; esas presentaciones no se usan para comparar precios hasta que una
decisión manual las confirme.

Ejemplos que deben quedar comparables::

    LECHE ENTERA 1 L      → 1.0 l
    LECHE ENT. 1000 ML    → 1.0 l
    LECHE ENTERA 1LT      → 1.0 l
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.normalize.text import llave

NUM = r"(\d+(?:[.,]\d+)?)"
_UNIDAD = r"(KILOGRAMOS?|KILOS?|KGS?|GRAMOS?|GRS?|G|MILILITROS?|MLS?|LITROS?|LTS?|L)"
_FIN = r"(?![A-Z])"

FACTORES = {
    "KILOGRAMO": ("kg", 1.0),
    "KILOGRAMOS": ("kg", 1.0),
    "KILO": ("kg", 1.0),
    "KILOS": ("kg", 1.0),
    "KG": ("kg", 1.0),
    "KGS": ("kg", 1.0),
    "GRAMO": ("kg", 0.001),
    "GRAMOS": ("kg", 0.001),
    "GR": ("kg", 0.001),
    "GRS": ("kg", 0.001),
    "G": ("kg", 0.001),
    "LITRO": ("l", 1.0),
    "LITROS": ("l", 1.0),
    "LT": ("l", 1.0),
    "LTS": ("l", 1.0),
    "L": ("l", 1.0),
    "MILILITRO": ("l", 0.001),
    "MILILITROS": ("l", 0.001),
    "ML": ("l", 0.001),
    "MLS": ("l", 0.001),
}

_ENVASES = (
    r"(?:LATAS|BOTELLAS|SOBRES|CUBOS|PIEZAS|STICKS?|ENVASES|VASOS|BOLSITAS|BARRAS|FRASCOS|TABLETAS|CAJITAS)"
)

RX_CANTIDAD = re.compile(r"(?<![A-Z0-9/.,])" + NUM + r"\s*" + _UNIDAD + _FIN)
RX_ALTERNATIVAS = re.compile(
    r"(?P<num>\d+(?:[.,]\d+)?)\s*(?:"
    + _UNIDAD
    + r"\.?\s*)?(?:O|/)\s*\d+(?:[.,]\d+)?\s*(?P<unidad>"
    + _UNIDAD[1:-1]
    + r")"
    + _FIN
)
_CONTEO_UNIDADES = (
    r"(PIEZASS|PIEZAS?|PZAS?|PZ|ROLLOS?|TOALLITAS|SOBRES|TABLETAS|CAPSULAS|UNIDADES|BARRAS|HOJAS)"
)
RX_CONTEO_ALTERNATIVO = re.compile(r"(?<![A-Z0-9])(\d+)\s*(?:O|/)\s*(\d+)\s*" + _CONTEO_UNIDADES + _FIN)
RX_CONTEO_CON = re.compile(r"\bCON\s*(\d+)(?![\d.,]*\s*[A-Z]*\s*\d)")
RX_RANGO = re.compile(r"DE\s*" + NUM + r"\s*A\s*" + NUM + r"\s*" + _UNIDAD + _FIN)
RX_MULTIPACK = re.compile(
    r"(?:(?<![A-Z0-9])(\d+)\s*|C/\s*(\d+)\s*)" + _ENVASES + r"\s*(?:DE\s*)?" + NUM + r"\s*" + _UNIDAD + _FIN
)
RX_MULTIPACK_X = re.compile(r"(?<![A-Z0-9])(\d+)\s*X\s*" + NUM + r"\s*" + _UNIDAD + _FIN)
RX_CONTEO_C = re.compile(r"C/\s*(\d+)(?!\s*[A-Z]*\s*\d)")
RX_CONTEO = re.compile(r"(?<![A-Z0-9])(\d+)\s*" + _CONTEO_UNIDADES + _FIN)
RX_PALABRA_CONTEO = re.compile(r"\b(PIEZA|MANOJO|ROLLO|RACIMO|DOCENA)\b")
RX_SEPARADOR_AMBIGUO = re.compile(r"^\d{1,3}[.,]\d{3}$")

SUBTIPO = {
    "PIEZASS": "PIEZA",
    "PIEZAS": "PIEZA",
    "PIEZA": "PIEZA",
    "PZAS": "PIEZA",
    "PZA": "PIEZA",
    "PZ": "PIEZA",
    "ROLLOS": "ROLLO",
    "ROLLO": "ROLLO",
    "TOALLITAS": "TOALLITA",
    "SOBRES": "SOBRE",
    "TABLETAS": "TABLETA",
    "CAPSULAS": "CAPSULA",
    "UNIDADES": "PIEZA",
    "BARRAS": "BARRA",
    "HOJAS": "HOJA",
}


@dataclass(frozen=True)
class Presentacion:
    presentacion_key: str
    unidad_base: str | None
    contenido_base: float | None
    cantidad: float | None
    unidad_original: str | None
    unidades_empaque: int | None
    subtipo_conteo: str | None
    regla: str
    confianza: str
    requiere_revision: bool
    motivo_revision: str | None


def _numero(texto: str, unidad: str) -> tuple[float, bool]:
    """Convierte el número; indica si el separador de miles/decimal es ambiguo."""
    if RX_SEPARADOR_AMBIGUO.match(texto):
        _, factor = FACTORES[unidad]
        # "3.564 GR" es 3,564 g (miles); "3.785 LT" es 3.785 l (decimal).
        valor = (
            float(texto.replace(".", "").replace(",", "")) if factor < 1 else float(texto.replace(",", "."))
        )
        return valor, True
    return float(texto.replace(",", ".")), False


def _base(valor: float, unidad: str) -> tuple[str, float]:
    dimension, factor = FACTORES[unidad]
    return dimension, round(valor * factor, 6)


def _resultado(key: str, **kw) -> Presentacion:
    campos = {
        "unidad_base": None,
        "contenido_base": None,
        "cantidad": None,
        "unidad_original": None,
        "unidades_empaque": None,
        "subtipo_conteo": None,
        "confianza": "alta",
        "requiere_revision": False,
        "motivo_revision": None,
    }
    campos.update(kw)
    if campos["contenido_base"] is not None and campos["contenido_base"] <= 0:
        campos.update(requiere_revision=True, motivo_revision="contenido_no_positivo", confianza="baja")
    return Presentacion(presentacion_key=key, **campos)


def interpretar(presentacion: str) -> Presentacion:
    key = llave(presentacion) or ""

    if m := RX_ALTERNATIVAS.search(key):
        valor, _ = _numero(m.group("num"), m.group("unidad"))
        dim, base = _base(valor, m.group("unidad"))
        return _resultado(
            key,
            unidad_base=dim,
            contenido_base=base,
            cantidad=valor,
            unidad_original=m.group("unidad"),
            regla="cantidades_alternativas",
            confianza="baja",
            requiere_revision=True,
            motivo_revision="cantidades_alternativas",
        )

    cantidades = list(RX_CANTIDAD.finditer(key))

    for rx in (RX_MULTIPACK, RX_MULTIPACK_X):
        if m := rx.search(key):
            grupos = [g for g in m.groups() if g is not None]
            n, num, unidad = int(grupos[0]), grupos[1], grupos[2]
            valor, ambiguo = _numero(num, unidad)
            dim, base_unit = _base(valor, unidad)
            total = round(n * base_unit, 6)
            fuera = [c for c in cantidades if not (m.start() <= c.start() < m.end())]
            explicitos = {_base(_numero(c.group(1), c.group(2))[0], c.group(2)) for c in fuera}
            misma_dim = {b for d, b in explicitos if d == dim}
            if misma_dim and all(abs(b - total) <= 0.02 * total for b in misma_dim):
                confianza, revision, motivo = "alta", False, None
            elif misma_dim:
                confianza, revision, motivo = "baja", True, "empaque_inconsistente_con_total"
            else:
                confianza, revision, motivo = "media", False, None
            if ambiguo:
                revision, motivo, confianza = True, "separador_ambiguo", "media"
            return _resultado(
                key,
                unidad_base=dim,
                contenido_base=total,
                cantidad=valor,
                unidad_original=unidad,
                unidades_empaque=n,
                regla="empaque_multiple",
                confianza=confianza,
                requiere_revision=revision,
                motivo_revision=motivo,
            )

    if (m := RX_RANGO.search(key)) and RX_PALABRA_CONTEO.search(key):
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=1.0,
            cantidad=1.0,
            unidad_original="PIEZA",
            subtipo_conteo="PIEZA",
            regla="pieza_con_rango_de_peso",
            confianza="media",
        )

    if cantidades:
        lecturas = [(c, *_numero(c.group(1), c.group(2))) for c in cantidades]
        bases = [(_base(valor, c.group(2)), valor, c.group(2), amb) for c, valor, amb in lecturas]
        dimensiones = {d for (d, _), *_ in bases}
        (dim, base), valor, unidad, ambiguo = bases[0]
        if len(dimensiones) > 1:
            return _resultado(
                key,
                unidad_base=dim,
                contenido_base=base,
                cantidad=valor,
                unidad_original=unidad,
                regla="cantidad_explicita",
                confianza="baja",
                requiere_revision=True,
                motivo_revision="dimensiones_mixtas",
            )
        distintos = {b for (_, b), *_ in bases}
        resto = sum(b for (_, b), *_ in bases[1:])
        regla = "cantidad_explicita"
        if len(distintos) > 1 and abs(resto - base) <= 0.02 * base:
            # "Caja 85 Gr. (35 Gr. Flan y 50 Gr. Caramelo)": el total cuadra con el desglose.
            regla = "cantidad_explicita_con_desglose"
            revision, motivo, confianza = False, None, "alta"
            if ambiguo:
                revision, motivo, confianza = True, "separador_ambiguo", "media"
        elif len(distintos) > 1:
            revision, motivo, confianza = True, "multiples_cantidades", "baja"
        elif ambiguo:
            revision, motivo, confianza = True, "separador_ambiguo", "media"
        else:
            revision, motivo, confianza = False, None, "alta"
        return _resultado(
            key,
            unidad_base=dim,
            contenido_base=base,
            cantidad=valor,
            unidad_original=unidad,
            regla=regla,
            confianza=confianza,
            requiere_revision=revision,
            motivo_revision=motivo,
        )

    if "CONTENIDO VARIABLE" in key and re.search(r"\bKG\b", key):
        return _resultado(
            key,
            unidad_base="kg",
            contenido_base=1.0,
            cantidad=1.0,
            unidad_original="KG",
            regla="precio_por_kg_contenido_variable",
            confianza="media",
        )

    if m := RX_CONTEO_ALTERNATIVO.search(key):
        n = int(m.group(1))
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=float(n),
            cantidad=float(n),
            unidad_original=m.group(3),
            subtipo_conteo=SUBTIPO[m.group(3)],
            regla="cantidades_alternativas",
            confianza="baja",
            requiere_revision=True,
            motivo_revision="cantidades_alternativas",
        )

    if m := RX_CONTEO_C.search(key):
        n = int(m.group(1))
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=float(n),
            cantidad=float(n),
            unidad_original="C/",
            subtipo_conteo="PIEZA",
            regla="conteo_con_diagonal",
        )

    if conteos := list(RX_CONTEO.finditer(key)):
        m = conteos[0]
        n = int(m.group(1))
        otros = {c.group(2) for c in conteos[1:]}
        por_unidad = bool(re.search(r"\bC/U\b", key))
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=float(n),
            cantidad=float(n),
            unidad_original=m.group(2),
            subtipo_conteo=SUBTIPO[m.group(2)],
            regla="conteo_explicito",
            confianza="baja" if por_unidad else ("alta" if not otros else "media"),
            requiere_revision=por_unidad,
            motivo_revision="conteo_por_unidad_de_empaque" if por_unidad else None,
        )

    if m := RX_CONTEO_CON.search(key):
        n = int(m.group(1))
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=float(n),
            cantidad=float(n),
            unidad_original="CON",
            subtipo_conteo="PIEZA",
            regla="conteo_con_palabra_con",
            confianza="media",
        )

    if m := RX_PALABRA_CONTEO.search(key):
        palabra = m.group(1)
        n = 12.0 if palabra == "DOCENA" else 1.0
        return _resultado(
            key,
            unidad_base="pieza",
            contenido_base=n,
            cantidad=n,
            unidad_original=palabra,
            subtipo_conteo="PIEZA" if palabra == "DOCENA" else palabra,
            regla="conteo_implicito",
            confianza="media",
        )

    return _resultado(
        key, regla="sin_cantidad", confianza="baja", requiere_revision=True, motivo_revision="sin_cantidad"
    )
