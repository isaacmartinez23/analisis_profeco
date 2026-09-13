{#
  Precio y costo de cada artículo de la canasta por cadena de referencia.

  Grano: versión de canasta × municipio × semana × cadena de referencia × artículo.

  Responde qué productos explican las diferencias entre cadenas: en municipio-semanas comparables
  (mart_ahorro_por_cadena), `diferencia_vs_cadena_mas_barata` es el costo del artículo en esta cadena menos
  su costo en la cadena con la canasta más barata. Sumado sobre los artículos de una cadena, reproduce
  `ahorro_vs_mas_barata` (prueba assert_descomposicion_ahorro).
#}
with canasta as (
    select articulo_id, articulo, grupo, cantidad_referencia, unidad_base, canasta_version
    from {{ ref('dim_canasta') }}
    where es_version_vigente
),

articulos as (
    select
        a.*,
        c.articulo,
        c.grupo,
        c.unidad_base,
        c.cantidad_referencia,
        c.canasta_version,
        a.mediana_precio_unitario * c.cantidad_referencia as costo_articulo
    from {{ ref('int_canasta_articulo_semanal') }} as a
    inner join canasta as c using (articulo_id)
    inner join {{ ref('cadenas_referencia') }} as r using (cadena_key)
),

por_articulo as (
    select
        geografia_id,
        semana_inicio,
        articulo_id,
        count(*) as cadenas_con_articulo,
        min(mediana_precio_unitario) as precio_unitario_minimo,
        max(mediana_precio_unitario) as precio_unitario_maximo,
        first(cadena_key order by mediana_precio_unitario, cadena_key) as cadena_key_mas_barata_articulo
    from articulos
    group by geografia_id, semana_inicio, articulo_id
),

comparables as (
    select geografia_id, semana_inicio, cadena_key, cadena_key_mas_barata
    from {{ ref('mart_ahorro_por_cadena') }}
),

costo_en_mas_barata as (
    select a.geografia_id, a.semana_inicio, a.articulo_id, a.costo_articulo as costo_articulo_en_mas_barata
    from articulos as a
    inner join (select distinct geografia_id, semana_inicio, cadena_key_mas_barata from comparables) as m
        on m.geografia_id = a.geografia_id
        and m.semana_inicio = a.semana_inicio
        and m.cadena_key_mas_barata = a.cadena_key
)

select
    a.canasta_version,
    a.semana_inicio,
    a.geografia_id,
    g.estado,
    g.municipio,
    a.cadena_key,
    r.cadena,
    a.articulo_id,
    a.articulo,
    a.grupo,
    a.unidad_base,
    a.cantidad_referencia,
    round(a.mediana_precio_unitario, 4) as mediana_precio_unitario,
    round(a.costo_articulo, 4) as costo_articulo,
    a.n_observaciones,
    a.n_establecimientos,
    a.n_productos,
    p.cadenas_con_articulo,
    round(p.precio_unitario_minimo, 4) as precio_unitario_minimo,
    round(p.precio_unitario_maximo, 4) as precio_unitario_maximo,
    a.cadena_key = p.cadena_key_mas_barata_articulo as es_cadena_mas_barata_articulo,
    round(100 * (a.mediana_precio_unitario - p.precio_unitario_minimo) / p.precio_unitario_minimo, 2)
        as diferencia_vs_minimo_pct,
    cm.cadena_key is not null as es_celda_comparable,
    case when cm.cadena_key is not null then round(a.costo_articulo - cb.costo_articulo_en_mas_barata, 4) end
        as diferencia_vs_cadena_mas_barata
from articulos as a
inner join por_articulo as p using (geografia_id, semana_inicio, articulo_id)
inner join {{ ref('cadenas_referencia') }} as r using (cadena_key)
inner join {{ ref('dim_geografia') }} as g using (geografia_id)
left join comparables as cm using (geografia_id, semana_inicio, cadena_key)
left join costo_en_mas_barata as cb using (geografia_id, semana_inicio, articulo_id)
