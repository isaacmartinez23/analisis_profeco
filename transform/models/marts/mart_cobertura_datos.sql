{#
  Cobertura y representatividad de la información.

  Grano: cadena × municipio × semana (todas las cadenas). Las métricas de observación usan solo la propia
  semana; la disponibilidad de la canasta usa la ventana móvil del mart de canasta (D-010).
  Responde: ¿qué tan completa y representativa es la información usada?
#}
with observaciones as (
    select
        e.cadena_key,
        e.geografia_id,
        d.semana_inicio,
        f.establecimiento_id,
        f.producto_id,
        f.fecha,
        f.es_atipico,
        f.es_comparable,
        f.n_registros_origen
    from {{ ref('fct_precio_observado') }} as f
    inner join {{ ref('dim_establecimiento') }} as e using (establecimiento_id)
    inner join {{ ref('dim_fecha') }} as d using (fecha)
),

agregado as (
    select
        cadena_key,
        geografia_id,
        semana_inicio,
        count(*) as n_observaciones,
        cast(sum(n_registros_origen) as bigint) as n_registros_origen,
        count(distinct establecimiento_id) as n_establecimientos,
        count(distinct producto_id) as n_productos,
        count(distinct fecha) as n_dias_con_observacion,
        count(*) filter (where es_atipico) as n_atipicas,
        count(*) filter (where not es_comparable) as n_no_comparables
    from observaciones
    group by cadena_key, geografia_id, semana_inicio
),

cadenas as (
    select
        cadena_key,
        arg_max(cadena, ultima_fecha) as cadena,
        arg_max(giro, ultima_fecha) as giro,
        bool_or(es_cadena_referencia) as es_cadena_referencia
    from {{ ref('dim_establecimiento') }}
    group by cadena_key
),

canasta as (
    select cadena_key, geografia_id, semana_inicio, articulos_disponibles, es_canasta_completa
    from {{ ref('mart_canasta_semanal') }}
),

total_articulos as (
    select count(*) as articulos_canasta_totales from {{ ref('dim_canasta') }} where es_version_vigente
)

select
    '{{ var("canasta_version") }}' as canasta_version,
    a.semana_inicio,
    a.semana_inicio + 6 as semana_fin,
    a.cadena_key,
    cad.cadena,
    cad.giro,
    cad.es_cadena_referencia,
    a.geografia_id,
    g.estado,
    g.municipio,
    a.n_observaciones,
    a.n_registros_origen,
    a.n_establecimientos,
    a.n_productos,
    a.n_dias_con_observacion,
    a.n_atipicas,
    a.n_no_comparables,
    round(100.0 * a.n_atipicas / a.n_observaciones, 3) as pct_atipicas,
    round(100.0 * a.n_no_comparables / a.n_observaciones, 2) as pct_no_comparables,
    coalesce(k.articulos_disponibles, 0) as articulos_canasta_disponibles,
    t.articulos_canasta_totales,
    coalesce(k.es_canasta_completa, false) as es_canasta_completa
from agregado as a
cross join total_articulos as t
inner join cadenas as cad using (cadena_key)
inner join {{ ref('dim_geografia') }} as g using (geografia_id)
left join canasta as k using (cadena_key, geografia_id, semana_inicio)
