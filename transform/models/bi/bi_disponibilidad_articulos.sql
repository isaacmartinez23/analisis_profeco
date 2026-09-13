{#
  Vista 5 del dashboard: productos disponibles en cada canasta.
  Grano: versión × semana × cadena de referencia × municipio × artículo, incluyendo los artículos SIN
  observaciones (disponible = false), que es lo que explica por qué una canasta está incompleta.
#}
with celdas as (
    select
        canasta_version,
        semana_inicio,
        cadena_key,
        cadena,
        geografia_id,
        estado,
        municipio,
        articulos_disponibles,
        es_canasta_completa,
        ventana_completa
    from {{ ref('mart_canasta_semanal') }}
    where es_cadena_referencia
),

articulos as (
    select articulo_id, articulo, grupo
    from {{ ref('dim_canasta') }}
    where es_version_vigente
),

disponibles as (
    select semana_inicio, cadena_key, geografia_id, articulo_id, n_observaciones, n_establecimientos
    from {{ ref('int_canasta_articulo_semanal') }}
)

select
    c.canasta_version,
    c.semana_inicio,
    c.cadena_key,
    c.cadena,
    c.geografia_id,
    c.estado,
    c.municipio,
    a.articulo_id,
    a.articulo,
    a.grupo,
    d.articulo_id is not null as disponible,
    coalesce(d.n_observaciones, 0) as n_observaciones,
    coalesce(d.n_establecimientos, 0) as n_establecimientos,
    c.articulos_disponibles,
    c.es_canasta_completa,
    c.ventana_completa
from celdas as c
cross join articulos as a
left join disponibles as d
    on d.semana_inicio = c.semana_inicio
    and d.cadena_key = c.cadena_key
    and d.geografia_id = c.geografia_id
    and d.articulo_id = a.articulo_id
