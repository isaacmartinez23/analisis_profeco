{#
  Grano: observación de precio (mismo que la tabla de hechos), limitada a productos asignados a un
  artículo de la canasta vigente, con presentación comparable y sin marca de atípico.
#}
select
    f.producto_id,
    f.establecimiento_id,
    f.fecha,
    d.semana_inicio,
    p.articulo_id,
    e.cadena_key,
    e.geografia_id,
    f.precio,
    f.precio_unitario
from {{ ref('fct_precio_observado') }} as f
inner join {{ ref('dim_producto') }} as p
    on p.producto_id = f.producto_id
    and p.articulo_id is not null
    and p.es_comparable
inner join {{ ref('dim_establecimiento') }} as e on e.establecimiento_id = f.establecimiento_id
inner join {{ ref('dim_fecha') }} as d on d.fecha = f.fecha
where not f.es_atipico
