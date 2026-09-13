{#
  Vista 3 del dashboard: ranking de diferencias por producto.
  Grano: versión × semana × artículo (nacional).
  `diferencia_acumulada` es sumable en el tiempo: el ranking de un periodo es SUM(diferencia_acumulada) por
  artículo, y su suma sobre artículos es el ahorro total de cambiarse a la cadena más barata (prueba
  assert_bi_diferencias_suman_ahorro).
#}
with productos as (
    select p.*, a.es_mas_barata
    from {{ ref('mart_precio_producto') }} as p
    left join {{ ref('mart_ahorro_por_cadena') }} as a
        using (canasta_version, geografia_id, semana_inicio, cadena_key)
)

select
    canasta_version,
    semana_inicio,
    articulo_id,
    articulo,
    grupo,
    count(*) filter (where es_celda_comparable and not es_mas_barata) as celdas_comparadas,
    round(coalesce(sum(diferencia_vs_cadena_mas_barata) filter (where es_celda_comparable and not es_mas_barata), 0), 4)
        as diferencia_acumulada,
    count(*) filter (where cadenas_con_articulo >= 2 and not es_cadena_mas_barata_articulo) as celdas_con_sobreprecio,
    round(median(diferencia_vs_minimo_pct) filter (where cadenas_con_articulo >= 2 and not es_cadena_mas_barata_articulo), 2)
        as sobreprecio_mediano_pct,
    round(median(mediana_precio_unitario), 4) as precio_unitario_mediano,
    any_value(unidad_base) as unidad_base
from productos
group by canasta_version, semana_inicio, articulo_id, articulo, grupo
