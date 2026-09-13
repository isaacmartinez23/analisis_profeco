-- La suma por cadena de las diferencias por artículo contra la cadena más barata debe reproducir el ahorro
-- de la canasta completa. Tolerancia de 5 centavos por el redondeo a 2 decimales del costo de canasta.
with por_articulo as (
    select
        canasta_version,
        geografia_id,
        semana_inicio,
        cadena_key,
        sum(diferencia_vs_cadena_mas_barata) as ahorro_por_articulos
    from {{ ref('mart_precio_producto') }}
    where es_celda_comparable
    group by all
)

select a.canasta_version, a.geografia_id, a.semana_inicio, a.cadena_key, a.ahorro_vs_mas_barata, p.ahorro_por_articulos
from {{ ref('mart_ahorro_por_cadena') }} as a
left join por_articulo as p using (canasta_version, geografia_id, semana_inicio, cadena_key)
where p.ahorro_por_articulos is null
    or abs(a.ahorro_vs_mas_barata - p.ahorro_por_articulos) > 0.05
