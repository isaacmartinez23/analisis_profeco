{#
  Evolución del costo de la canasta: índice directo de panel fijo (D-026).
  Grano: versión × semana × alcance ('Todas las cadenas de referencia' o el nombre de una cadena).
  Base = mediana del costo de cada par cadena-municipio en las primeras `indice_semanas_base` semanas; cada semana
  se calcula la media geométrica de costo / costo base de los pares presentes.
#}
{% set semanas_base = var('indice_semanas_base') %}

with completas as (
    select cadena_key, cadena, geografia_id, semana_inicio, costo_canasta
    from {{ ref('mart_canasta_semanal') }}
    where es_cadena_referencia and es_canasta_completa and ventana_completa
),

inicio as (
    select min(semana_inicio) as primera_semana from completas
),

base as (
    select c.cadena_key, c.geografia_id, median(c.costo_canasta) as costo_base
    from completas as c
    cross join inicio as i
    where c.semana_inicio < i.primera_semana + 7 * {{ semanas_base }}
    group by c.cadena_key, c.geografia_id
),

pares as (
    select c.*, ln(c.costo_canasta / b.costo_base) as log_razon
    from completas as c
    inner join base as b using (cadena_key, geografia_id)
)

select
    '{{ var("canasta_version") }}' as canasta_version,
    semana_inicio,
    'Todas las cadenas de referencia' as alcance,
    count(*) as pares,
    round(100 * exp(avg(log_razon)), 2) as indice_base_100
from pares
group by semana_inicio

union all

select
    '{{ var("canasta_version") }}' as canasta_version,
    semana_inicio,
    cadena as alcance,
    count(*) as pares,
    round(100 * exp(avg(log_razon)), 2) as indice_base_100
from pares
group by semana_inicio, cadena
