# Memo ejecutivo · costo de la canasta y ahorro entre cadenas

**Periodo:** 8 de enero de 2024 a 27 de julio de 2026 (135 semanas) · **Fuente:** Quién es Quién en los Precios,
PROFECO · **Canasta:** v1, 16 alimentos · **Base:** 35.6 millones de observaciones de precio en 30 estados y 75
municipios.

Todas las comparaciones son **pareadas**: la misma canasta, en el mismo municipio, en la misma semana. Eso deja
5,630 municipio-semanas comparables en 51 municipios. Detalle completo en
[`resultados_canasta.md`](resultados_canasta.md); definiciones en [`docs/catalogo_metricas.md`](../docs/catalogo_metricas.md).

## Lo esencial

1. **Elegir bien la tienda vale entre 48 y 64 pesos por canasta y semana**, según cuántas cadenas compitan en el
   municipio. Es 6.7% del costo con dos cadenas y 8.8% donde están las cuatro.
2. **Chedraui es la más barata en 7 de cada 10 municipio-semanas** donde está presente; Wal-mart es la más cara del
   grupo comparado y cambiarse desde ahí equivale a unos **1,665 pesos al año**.
3. **Cinco productos frescos explican el 73% de la diferencia total**: milanesa de res, limón, jitomate, cebolla y
   papa. Los abarrotes empaquetados casi no mueven la aguja.

## 1. Cuánto cuesta la canasta

| Cadena | Costo mediano (histórico) | Últimas 8 semanas | Frente a la mediana |
|---|---:|---:|---:|
| Chedraui | $663.94 | $650.22 | −3.1% |
| Bodega Aurrera | $693.09 | $670.07 | 0.0% |
| Hipermercado Soriana | $703.03 | $682.91 | 0.0% |
| Wal-mart | $713.11 | $699.88 | +1.2% |

La distancia entre la más barata y la más cara es estable en el tiempo: no es un efecto de una promoción puntual.

Entre municipios las diferencias son chicas: el más barato y el más caro se separan menos de 6 puntos del nivel
nacional (Boca del Río 97.1, La Paz 102.7). **Dónde se compra dentro de la ciudad importa más que en qué ciudad.**

## 2. Cuánto se puede ahorrar

| Escenario | Municipio-semanas | Ahorro mediano | % | Ahorro alto (p90) |
|---|---:|---:|---:|---:|
| Todas las celdas comparables | 5,630 | $48.08 | 6.7% | $92.60 |
| Municipios con las 4 cadenas | 801 | $64.03 | 8.8% | $105.22 |
| Solo entre grupos distintos | 5,352 | $49.52 | 6.9% | $93.35 |

Por cadena, el ahorro de cambiarse a la más barata del mismo municipio y semana:

| Cadena | Veces que es la más barata | Ahorro al cambiarse | Equivalente anual |
|---|---:|---:|---:|
| Chedraui | 70.7% | — | — |
| Bodega Aurrera | 35.9% | $13.70 (2.0%) | $710 |
| Hipermercado Soriana | 32.8% | $21.70 (3.1%) | $1,130 |
| Wal-mart | 22.6% | $32.00 (4.5%) | $1,665 |

El equivalente anual supone comprar la canasta de referencia cada semana en la misma cadena. Wal-mart y Bodega
Aurrera son del mismo grupo: comparar entre ellas mide formato de tienda, no competencia.

## 3. Cómo evoluciona el costo

El índice de panel fijo (base 100 = primeras 8 semanas de 2024) se movió en una banda estrecha, entre 95.6 y 104.0,
durante dos años y medio. Lo relevante es el cierre del periodo: después del pico de **104.0 en abril de 2026**, el
índice bajó a **97.9 en junio y 96.8 en julio**, el nivel más bajo desde mayo de 2024. La canasta cuesta hoy
alrededor de **7% menos que en abril**, y la caída coincide con la temporada de frescos.

## 4. Qué productos explican las diferencias

| Artículo | % de la diferencia total | Sobreprecio mediano frente a la cadena más barata |
|---|---:|---:|
| Milanesa de res | 20.6% | 7.5% |
| Limón sin semilla | 17.2% | 41.3% |
| Jitomate saladette | 13.1% | 34.4% |
| Cebolla blanca | 12.3% | 34.7% |
| Papa alfa o blanca | 9.9% | 21.5% |

Dos lecturas distintas:

- **Por peso en el bolsillo**, manda la carne: la milanesa aporta la quinta parte de la diferencia aunque su
  sobreprecio relativo sea de apenas 7.5%, porque es el artículo más caro de la canasta.
- **Por diferencia relativa**, mandan los frescos: limón, jitomate y cebolla llegan a costar entre 34% y 41% más
  según la tienda, en la misma ciudad y la misma semana.

Caso aparte: la **pasta para sopa** tiene un sobreprecio mediano de 106.5%, el más alto de la canasta. Ahí se está
comparando marca propia contra marca comercial, no solo precio (L-18).

## 5. Qué tan sólida es esta información

| Indicador | Valor |
|---|---|
| Observaciones de precio | 35,609,833 |
| Celdas de referencia con canasta completa | 81.3% |
| Observaciones marcadas como atípicas | 0.035% (se conservan, no se eliminan) |
| Validación independiente | 24 de 24 comparaciones coinciden con el recálculo desde el dato crudo |

**Lo que estos números no dicen:**

- La canasta es **genérica**: cada artículo es la mediana de cualquier marca comparable, así que parte de la
  diferencia entre cadenas refleja su mezcla de marcas.
- Las cantidades son la presentación más frecuente observada, no el consumo de un hogar: el costo es un **índice
  comparable**, no el gasto real de una familia.
- En la mediana de las celdas cada cadena está representada por **una tienda y un día** de levantamiento por semana.
- **24 de los 75 municipios nunca tienen dos cadenas de referencia completas la misma semana**, así que el ahorro se
  estima sobre 51 municipios. Bodega Aurrera es la cadena con más huecos (68.7% de semanas completas).
- Los datos más recientes son del 31 de julio de 2026: **47 días de rezago** en la publicación de PROFECO.

Lista completa en [`docs/limitaciones.md`](../docs/limitaciones.md).

## Recomendaciones

**Para un hogar.** El ahorro está en los frescos, no en los abarrotes: comprar carne y verdura donde salen más
baratas rinde más que mover toda la despensa. Con las cuatro cadenas cerca, elegir bien vale cerca de $64 por
canasta semanal.

**Para seguir el tema con datos.** El pipeline ya corre solo cada semana y publica las tablas del dashboard; la
señal a vigilar es si la baja de junio y julio se sostiene o revierte con la próxima publicación de PROFECO.

**Para robustecer el análisis.** Tres mejoras cambiarían la calidad de la respuesta, en orden de valor: comparar
también por marca (separa precio de mezcla de marcas), usar cantidades de una fuente oficial en lugar de la
presentación modal, y consolidar establecimientos por coordenadas para no perder tiendas cuando PROFECO reescribe
una dirección.

---

_Generado a partir de `reports/resultados_canasta.md` (ejecución del 2026-09-16, datos al 2026-07-27). Método:
[`docs/arquitectura.md`](../docs/arquitectura.md) · decisiones: [`docs/decisiones.md`](../docs/decisiones.md)._
