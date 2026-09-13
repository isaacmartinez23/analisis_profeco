{#
  Vista 1 del dashboard: costo semanal de la canasta por cadena de referencia (nacional).
  Grano: versión × semana × cadena. Solo municipio-semanas comparables (mart_ahorro_por_cadena), para que las
  cadenas se comparen en las mismas ciudades y semanas. Las medianas no son sumables: el dashboard debe mostrar
  estos valores semanales o promediarlos, no sumarlos.
#}
select
    canasta_version,
    semana_inicio,
    semana_fin,
    cadena_key,
    cadena,
    grupo_empresarial,
    count(*) as municipios_comparables,
    round(median(costo_canasta), 2) as costo_mediano,
    round(quantile_cont(costo_canasta, 0.25), 2) as costo_p25,
    round(quantile_cont(costo_canasta, 0.75), 2) as costo_p75,
    count(*) filter (where es_mas_barata) as veces_mas_barata,
    round(100.0 * avg(es_mas_barata::int), 1) as pct_veces_mas_barata,
    round(median(ahorro_vs_mas_barata), 2) as ahorro_mediano_vs_mas_barata,
    round(median(ahorro_pct), 2) as ahorro_mediano_pct,
    cast(sum(n_observaciones) as bigint) as n_observaciones
from {{ ref('mart_ahorro_por_cadena') }}
group by canasta_version, semana_inicio, semana_fin, cadena_key, cadena, grupo_empresarial
