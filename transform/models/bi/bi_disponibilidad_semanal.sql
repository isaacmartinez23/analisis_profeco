{#
  Vista 5 (resumen) del dashboard: disponibilidad de cada artículo por cadena de referencia (nacional).
  Grano: versión × semana × cadena × artículo. Versión compacta de bi_disponibilidad_articulos para el plan
  gratuito de Supabase (D-036): el porcentaje de un periodo es SUM(celdas_con_articulo) / SUM(celdas).
#}
select
    canasta_version,
    semana_inicio,
    cadena_key,
    cadena,
    articulo_id,
    articulo,
    grupo,
    count(*) as celdas,
    count(*) filter (where disponible) as celdas_con_articulo,
    round(100.0 * avg(disponible::int), 1) as pct_disponible,
    cast(sum(n_observaciones) as bigint) as n_observaciones
from {{ ref('bi_disponibilidad_articulos') }}
group by canasta_version, semana_inicio, cadena_key, cadena, articulo_id, articulo, grupo
