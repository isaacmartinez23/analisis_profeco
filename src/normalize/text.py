"""Normalización de texto y corrección de caracteres perdidos.

``llave`` produce la forma canónica usada para comparar valores: mayúsculas, sin
acentos, espacios colapsados y sin puntuación final. Es equivalente a la
expresión SQL ``upper(strip_accents(trim(...)))`` más el colapso de espacios.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

_ESPACIOS = re.compile(r"\s+")


def sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def llave(texto: str | None) -> str | None:
    if texto is None:
        return None
    limpio = _ESPACIOS.sub(" ", sin_acentos(texto).upper()).strip()
    return limpio.rstrip(" .") or limpio


@dataclass(frozen=True)
class Correccion:
    columna: str
    valor_original: str
    valor_corregido: str | None
    candidatos: int
    metodo: str
    requiere_revision: bool


def _patron(valor: str) -> re.Pattern[str]:
    # Cada "?" ocupa el lugar de un carácter no ASCII perdido (á, é, ñ, ü, µ...). Exigir no ASCII
    # evita "corregir" hacia una palabra distinta que solo difiere en una letra común.
    partes = [re.escape(p) for p in valor.split("?")]
    return re.compile("^" + "[^\\x00-\\x7F]".join(partes) + "$", re.IGNORECASE)


def _no_ascii(texto: str) -> int:
    return sum(ord(c) > 127 for c in texto)


def corregir_interrogaciones(columna: str, valores: Iterable[str]) -> list[Correccion]:
    """Propone correcciones para valores con "?" usando los valores intactos de la misma columna.

    Un valor intacto es candidato si coincide carácter por carácter, con un carácter no ASCII
    en cada posición de "?". Las variantes que solo difieren en mayúsculas cuentan como un mismo
    candidato (misma ``llave``).
    Solo se corrige automáticamente con un único candidato; si no, se envía a revisión.
    """
    valores = set(valores)
    intactos = [v for v in valores if "?" not in v]
    correcciones = []
    for valor in sorted(v for v in valores if "?" in v):
        patron = _patron(valor)
        candidatos = [v for v in intactos if len(v) == len(valor) and patron.match(v)]
        llaves = {llave(c) for c in candidatos}
        if len(llaves) == 1:
            elegido = sorted(candidatos, key=lambda c: (-_no_ascii(c), c))[0]
            correcciones.append(
                Correccion(columna, valor, elegido, len(candidatos), "auto_candidato_unico", False)
            )
        else:
            correcciones.append(Correccion(columna, valor, None, len(llaves), "sin_candidato_unico", True))
    return correcciones
