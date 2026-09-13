{#
  Costo semanal de la canasta de referencia.

  Grano: versión de canasta × cadena × municipio × semana.
  - costo_canasta solo se publica cuando la canasta está completa (todos los artículos con al menos
    una observación comparable en la ventana); una canasta incompleta nunca se presenta como completa.
  - costo_articulos_disponibles se publica siempre, con el número de artículos, para análisis de cobertura.
  - costo de un artículo = mediana del precio unitario × cantidad de referencia (D-009).
#}
with articulos as (
    select * from {{ ref('int_canasta_articulo_semanal') }}
),

canasta as (
    select * from {{ ref('dim_canasta') }} where es_version_vigente
),

total_articulos as (
    select count(*) as articulos_totales from canasta
),

costos as (
    select
        a.*,
        a.mediana_precio_unitario * c.cantidad_referencia as costo_articulo
    from articulos as a
    inner join canasta as c using (articulo_id)
),

celdas as (
    select
        cadena_key,
        geografia_id,
        semana_inicio,
        count(*) as articulos_disponibles,
        sum(costo_articulo) as costo_articulos_disponibles,
        -- DuckDB promueve sum(BIGINT) a HUGEINT, que PostgreSQL no admite al publicar.
        cast(sum(n_observaciones) as bigint) as n_observaciones,
        min(n_observaciones) as min_observaciones_por_articulo,
        max(n_establecimientos) as max_establecimientos_por_articulo,
        bool_and(ventana_completa) as ventana_completa
    from costos
    group by cadena_key, geografia_id, semana_inicio
),

cadenas as (
    select
        cadena_key,
        arg_max(cadena, ultima_fecha) as cadena,
        bool_or(es_cadena_referencia) as es_cadena_referencia
    from {{ ref('dim_establecimiento') }}
    group by cadena_key
)

select
    '{{ var("canasta_version") }}' as canasta_version,
    c.semana_inicio,
    c.semana_inicio + 6 as semana_fin,
    c.semana_inicio - 7 * {{ var('semanas_ventana_previas') }} as ventana_desde,
    c.cadena_key,
    cad.cadena,
    cad.es_cadena_referencia,
    c.geografia_id,
    g.estado,
    g.municipio,
    c.articulos_disponibles,
    t.articulos_totales,
    round(100.0 * c.articulos_disponibles / t.articulos_totales, 1) as pct_articulos_disponibles,
    c.articulos_disponibles = t.articulos_totales as es_canasta_completa,
    case when c.articulos_disponibles = t.articulos_totales then round(c.costo_articulos_disponibles, 2) end
        as costo_canasta,
    round(c.costo_articulos_disponibles, 2) as costo_articulos_disponibles,
    c.n_observaciones,
    c.min_observaciones_por_articulo,
    c.max_establecimientos_por_articulo,
    c.ventana_completa
from celdas as c
cross join total_articulos as t
inner join cadenas as cad using (cadena_key)
inner join {{ ref('dim_geografia') }} as g using (geografia_id)
