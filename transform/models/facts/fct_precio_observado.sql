{#
  Tabla de hechos del modelo estrella.

  Grano: una observación de precio de un producto, en un establecimiento, en una fecha
  (llave: producto_id + establecimiento_id + fecha + precio; ver int_observaciones).

  Separa precio observado (por presentación) de precio unitario (por kg, l o pieza).
  Los atípicos se marcan, nunca se eliminan:
    Q-ATIP-01  precio > factor × mediana del producto, o < mediana / factor
    Q-ATIP-02  |ln(precio) − mediana ln| > umbral × 1.4826 × MAD, con historia suficiente, y además
               precio > factor_minimo × mediana o < mediana / factor_minimo.
  La magnitud mínima de Q-ATIP-02 evita marcar promociones en productos de precio muy estable, donde la
  MAD es casi cero (en la muestra, sin ella se marcaba leche a 0.95× la mediana).
  Medianas y MAD exactas: approx_quantile es más ligero, pero en paralelo no es determinista y
  cambiaba las banderas entre ejecuciones idénticas (D-021).
#}
{% set factor = var('atipico_factor_mediana') %}
{% set umbral = var('atipico_umbral_mad') %}
{% set factor_minimo = var('atipico_factor_minimo_mad') %}
{% set min_obs = var('atipico_min_observaciones') %}

with observaciones as (
    select * from {{ ref('int_observaciones') }}
),

productos as (
    select producto_id, unidad_base, contenido_base, es_comparable
    from {{ ref('dim_producto') }}
),

estadisticas as (
    select
        producto_num,
        count(*) as n_observaciones_producto,
        median(ln(precio::double)) as mediana_ln
    from observaciones
    group by producto_num
),

dispersion as (
    select
        o.producto_num,
        median(abs(ln(o.precio::double) - e.mediana_ln)) as mad_ln
    from observaciones as o
    inner join estadisticas as e using (producto_num)
    group by o.producto_num
),

evaluado as (
    select
        o.*,
        p.unidad_base,
        p.contenido_base,
        p.es_comparable,
        e.n_observaciones_producto,
        exp(e.mediana_ln) as precio_mediana_producto,
        o.precio::double > {{ factor }} * exp(e.mediana_ln)
            or o.precio::double < exp(e.mediana_ln) / {{ factor }} as regla_01,
        e.n_observaciones_producto >= {{ min_obs }}
            and d.mad_ln > 0
            and abs(ln(o.precio::double) - e.mediana_ln) > {{ umbral }} * 1.4826 * d.mad_ln
            and abs(ln(o.precio::double) - e.mediana_ln) > ln({{ factor_minimo }}) as regla_02
    from observaciones as o
    inner join productos as p using (producto_id)
    inner join estadisticas as e using (producto_num)
    inner join dispersion as d using (producto_num)
)

select
    producto_id,
    establecimiento_id,
    fecha,
    precio,
    case when es_comparable then round(precio::double / contenido_base, 4) end as precio_unitario,
    unidad_base,
    contenido_base,
    es_comparable,
    precio_original,
    producto_original,
    presentacion_original,
    marca_original,
    catalogos_mask,
    n_registros_origen,
    tiene_precio_en_conflicto,
    round(precio_mediana_producto, 2) as precio_mediana_producto,
    n_observaciones_producto,
    regla_01 or regla_02 as es_atipico,
    case
        when regla_01 then 'precio a más de {{ factor }} veces de la mediana del producto'
        when regla_02 then 'desviación robusta mayor a {{ umbral }} MAD y a {{ factor_minimo }} veces de la mediana del producto'
    end as motivo_atipico,
    case when regla_01 then 'Q-ATIP-01' when regla_02 then 'Q-ATIP-02' end as regla_calidad,
    archivo_origen,
    id_carga,
    cargado_utc
from evaluado
