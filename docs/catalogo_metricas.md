# Catálogo de métricas

Cada métrica indica definición, fórmula, grano, fuente y salvedades. Todas se calculan en dbt
(`transform/models/marts/`) salvo las marcadas como "derivada en reporte" (`src/analysis/resultados.py`), que
deben replicarse igual en el dashboard.

Trazabilidad general:
`raw.qqp_precios` → `staging.stg_qqp__precios` → `intermediate.int_observaciones` → `core.fct_precio_observado`
→ `intermediate.int_canasta_observaciones` → `intermediate.int_canasta_articulo_semanal` → marts.

Conceptos base:

| Concepto | Definición |
|---|---|
| Observación | Un precio de un producto normalizado, en un establecimiento, en una fecha (`fct_precio_observado`). |
| Precio observado | Precio en MXN de la presentación completa (`precio`). |
| Precio unitario | `precio / contenido_base` en kg, l o pieza; solo para presentaciones comparables. |
| Artículo | Grupo de productos comparables de la canasta vigente (`dim_canasta`), sin importar la marca. |
| Ventana | Semana *S* + semana anterior: observaciones con fecha en [inicio(S) − 7, inicio(S) + 6] (D-010). |
| Celda | Cadena × municipio × semana. |
| Celda comparable | Municipio × semana con al menos dos cadenas de referencia con canasta completa y ventana completa. |
| Cadenas de referencia | Wal-mart, Bodega Aurrera, Hipermercado Soriana, Chedraui (D-011). |

---

## Costo de la canasta

| Métrica | Fórmula | Grano | Fuente |
|---|---|---|---|
| `mediana_precio_unitario` | mediana(precio unitario) de observaciones comparables y no atípicas del artículo en la ventana | cadena × municipio × semana × artículo | `int_canasta_articulo_semanal`, `mart_precio_producto` |
| `costo_articulo` | `mediana_precio_unitario × cantidad_referencia` | cadena × municipio × semana × artículo | `mart_precio_producto` |
| `articulos_disponibles` | artículos con al menos una observación en la ventana | celda | `mart_canasta_semanal` |
| `es_canasta_completa` | `articulos_disponibles = articulos_totales` | celda | `mart_canasta_semanal` |
| `costo_canasta` | Σ `costo_articulo` si la canasta está completa; NULL si no | celda | `mart_canasta_semanal` |
| `costo_articulos_disponibles` | Σ `costo_articulo` de los disponibles (**no comparable** entre celdas incompletas) | celda | `mart_canasta_semanal` |
| `n_observaciones` | observaciones usadas en la ventana | celda | `mart_canasta_semanal` |

Salvedades: canasta genérica por mediana de cualquier marca (L-10); cantidades de referencia = presentación modal
(L-11); ventana móvil suaviza cambios semanales (L-12).

## Ahorro entre cadenas

Solo en celdas comparables (misma canasta, municipio y semana).

| Métrica | Fórmula | Grano | Fuente |
|---|---|---|---|
| `costo_minimo`, `costo_maximo`, `costo_mediano` | mínimo, máximo y mediana de `costo_canasta` entre cadenas comparadas | municipio × semana | `mart_ahorro_por_cadena` |
| `cadena_mas_barata` | cadena con `costo_minimo` (empate: menor `cadena_key`) | municipio × semana | `mart_ahorro_por_cadena` |
| `posicion` | rango de costo (1 = más barata; empates comparten rango) | cadena × municipio × semana | `mart_ahorro_por_cadena` |
| `ahorro_vs_mas_barata` | `costo_canasta − costo_minimo` | cadena × municipio × semana | `mart_ahorro_por_cadena` |
| `ahorro_pct` | `100 × ahorro_vs_mas_barata / costo_canasta` | cadena × municipio × semana | `mart_ahorro_por_cadena` |
| `diferencia_vs_mediana_pct` | `100 × (costo_canasta − costo_mediano) / costo_mediano` | cadena × municipio × semana | `mart_ahorro_por_cadena` |
| `brecha_max_min` ("ahorro máximo") | `costo_maximo − costo_minimo` | municipio × semana | `mart_ahorro_por_cadena` |
| `brecha_pct` | `100 × brecha_max_min / costo_maximo` | municipio × semana | `mart_ahorro_por_cadena` |
| `grupos_comparados` | grupos empresariales distintos entre las cadenas comparadas | municipio × semana | `mart_ahorro_por_cadena` |
| Frecuencia como más barata | % de celdas comparables de la cadena con `es_mas_barata` | cadena | derivada en reporte |
| Ahorro anual equivalente | mediana semanal de `ahorro_vs_mas_barata` × 52 | cadena | derivada en reporte |

Salvedades: el ahorro entre Wal-mart y Bodega Aurrera es diferencia de formato del mismo grupo (L-14; filtrar
`grupos_comparados ≥ 2` para comparar competidores). El equivalente anual supone comprar la canasta de referencia
cada semana en la misma cadena.

## Diferencias por producto

| Métrica | Fórmula | Grano | Fuente |
|---|---|---|---|
| `precio_unitario_minimo`, `precio_unitario_maximo` | mínimo y máximo de la mediana del artículo entre cadenas de referencia | municipio × semana × artículo | `mart_precio_producto` |
| `diferencia_vs_minimo_pct` | `100 × (mediana_precio_unitario − precio_unitario_minimo) / precio_unitario_minimo` | cadena × municipio × semana × artículo | `mart_precio_producto` |
| `diferencia_vs_cadena_mas_barata` | `costo_articulo − costo_articulo en la cadena con la canasta más barata` (solo celdas comparables) | cadena × municipio × semana × artículo | `mart_precio_producto` |
| Diferencia acumulada por artículo | Σ `diferencia_vs_cadena_mas_barata` en cadenas no ganadoras | artículo | derivada en reporte |
| % de la diferencia neta | diferencia acumulada del artículo / Σ de todos los artículos | artículo | derivada en reporte |

Propiedad verificada por prueba (`assert_descomposicion_ahorro`): Σ artículos `diferencia_vs_cadena_mas_barata` =
`ahorro_vs_mas_barata` (±0.05 MXN). Una diferencia negativa indica que ese artículo es más barato en la cadena
que perdió.

## Evolución

| Métrica | Fórmula | Grano | Fuente |
|---|---|---|---|
| `indice_base_100` | 100 × exp(promedio(ln(`costo_canasta / costo_base`))) sobre pares cadena-municipio con canasta completa; `costo_base` = mediana del par en las primeras 8 semanas | semana × alcance | `bi_indice_canasta` |

No se usa el promedio simple del costo por semana porque cambia la mezcla de municipios con canasta completa, ni un
índice encadenado porque acumula deriva (D-026).

## Tablas BI para el dashboard

Precalculadas en dbt (`transform/models/bi/`) y publicadas en Supabase. Medianas y percentiles **no son sumables**:
en Looker Studio usar Mediana o Promedio sobre semanas, nunca Suma.

| Tabla | Grano | Métricas | Sumables |
|---|---|---|---|
| `bi_costo_semanal_cadena` | semana × cadena | `costo_mediano`, `costo_p25`, `costo_p75`, `ahorro_mediano_vs_mas_barata`, `ahorro_mediano_pct`, `pct_veces_mas_barata` | `municipios_comparables`, `veces_mas_barata`, `n_observaciones` |
| `bi_ahorro_semanal` | semana | `ahorro_maximo_mediano`, `ahorro_maximo_mediano_pct`, `ahorro_maximo_p90`, `ahorro_maximo_mediano_competidores`, `cadena_mas_barata_mas_frecuente` | `municipios_comparables`, `municipios_con_4_cadenas`, `municipios_con_grupos_distintos` |
| `bi_diferencias_producto_semanal` | semana × artículo | `sobreprecio_mediano_pct`, `precio_unitario_mediano` | `diferencia_acumulada`, `celdas_comparadas`, `celdas_con_sobreprecio` |
| `bi_disponibilidad_articulos` | semana × cadena × municipio × artículo | `disponible` | `n_observaciones`, `n_establecimientos` |
| `bi_indice_canasta` | semana × alcance | `indice_base_100` | `pares` |

`ahorro_maximo_mediano_competidores` excluye municipio-semanas donde solo se comparan cadenas del mismo grupo
empresarial. Consistencia con los marts probada por `assert_bi_consistente_con_marts`.

## Cobertura y calidad

| Métrica | Fórmula | Grano | Fuente |
|---|---|---|---|
| `n_observaciones`, `n_registros_origen` | observaciones y filas crudas de la propia semana | cadena × municipio × semana | `mart_cobertura_datos` |
| `n_establecimientos`, `n_productos`, `n_dias_con_observacion` | conteos distintos de la propia semana | cadena × municipio × semana | `mart_cobertura_datos` |
| `pct_atipicas` | `100 × n_atipicas / n_observaciones` | cadena × municipio × semana | `mart_cobertura_datos` |
| `pct_no_comparables` | `100 × n_no_comparables / n_observaciones` | cadena × municipio × semana | `mart_cobertura_datos` |
| `articulos_canasta_disponibles` | artículos de la canasta con precio en la ventana | cadena × municipio × semana | `mart_cobertura_datos` |
| Celdas de referencia completas (M-04) | % celdas de referencia (ventana completa) con canasta completa | global | `src/quality/checks.py` |
| Municipio-semanas comparables (M-07) | % municipio-semanas con ≥2 cadenas de referencia donde ≥2 están completas | global | `src/quality/checks.py` |
