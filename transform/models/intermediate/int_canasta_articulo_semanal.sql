{#
  Grano: cadena × municipio × semana × artículo de canasta.

  Ventana móvil (D-010): la semana S usa las observaciones de S y de las
  `semanas_ventana_previas` semanas anteriores. Cada observación se replica en su semana y en las
  siguientes que la incluyen. El valor del artículo es la mediana del precio unitario de todas las
  observaciones comparables de la ventana.
#}
{% set previas = var('semanas_ventana_previas') %}

with observaciones as (
    select * from {{ ref('int_canasta_observaciones') }}
),

limites as (
    select min(semana_inicio) as primera_semana, max(semana_inicio) as ultima_semana
    from observaciones
),

ventana as (
    select
        o.*,
        o.semana_inicio + 7 * k.desplazamiento as semana_ventana
    from observaciones as o
    cross join (select cast(unnest(range(0, {{ previas }} + 1)) as integer) as desplazamiento) as k
)

select
    v.cadena_key,
    v.geografia_id,
    v.semana_ventana as semana_inicio,
    v.articulo_id,
    median(v.precio_unitario) as mediana_precio_unitario,
    min(v.precio_unitario) as min_precio_unitario,
    max(v.precio_unitario) as max_precio_unitario,
    count(*) as n_observaciones,
    count(distinct v.establecimiento_id) as n_establecimientos,
    count(distinct v.producto_id) as n_productos,
    count(distinct v.fecha) as n_dias_con_observacion,
    v.semana_ventana >= any_value(l.primera_semana) + 7 * {{ previas }} as ventana_completa
from ventana as v
cross join limites as l
where v.semana_ventana <= l.ultima_semana
group by v.cadena_key, v.geografia_id, v.semana_ventana, v.articulo_id
