{#
  Vista 2 del dashboard: ahorro potencial entre cadenas (nacional).
  Grano: versión × semana. Resume, sobre los municipio-semanas comparables, cuánto separa a la cadena más cara
  de la más barata. Los conteos son sumables; medianas y percentiles no.
#}
with celdas as (
    select distinct
        canasta_version,
        semana_inicio,
        semana_fin,
        geografia_id,
        cadenas_comparadas,
        grupos_comparados,
        brecha_max_min,
        brecha_pct,
        cadena_mas_barata
    from {{ ref('mart_ahorro_por_cadena') }}
)

select
    canasta_version,
    semana_inicio,
    semana_fin,
    count(*) as municipios_comparables,
    count(*) filter (where cadenas_comparadas = 4) as municipios_con_4_cadenas,
    count(*) filter (where grupos_comparados >= 2) as municipios_con_grupos_distintos,
    round(median(brecha_max_min), 2) as ahorro_maximo_mediano,
    round(median(brecha_pct), 2) as ahorro_maximo_mediano_pct,
    round(quantile_cont(brecha_max_min, 0.9), 2) as ahorro_maximo_p90,
    round(median(brecha_max_min) filter (where grupos_comparados >= 2), 2) as ahorro_maximo_mediano_competidores,
    first(cadena_mas_barata order by n desc, cadena_mas_barata) as cadena_mas_barata_mas_frecuente
from (
    select *, count(*) over (partition by canasta_version, semana_inicio, cadena_mas_barata) as n
    from celdas
)
group by canasta_version, semana_inicio, semana_fin
