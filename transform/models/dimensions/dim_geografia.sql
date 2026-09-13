{#
  Grano: un municipio (estado + municipio normalizados sin acentos).
  El nombre mostrado es la escritura más reciente (con acentos desde 2026). El nombre del estado se elige a
  nivel estado para que un municipio sin datos recientes no muestre la grafía antigua.
  Representa ciudades muestreadas por PROFECO, no la entidad completa (D-012).
#}
with municipios as (
    select
        geografia_id,
        any_value(estado_key) as estado_key,
        any_value(municipio_key) as municipio_key,
        arg_max(municipio, ultima_fecha) as municipio,
        count(distinct establecimiento_id) as n_establecimientos,
        min(primera_fecha) as primera_fecha,
        max(ultima_fecha) as ultima_fecha
    from {{ ref('int_establecimientos') }}
    group by geografia_id
),

estados as (
    select estado_key, arg_max(estado, ultima_fecha) as estado
    from {{ ref('int_establecimientos') }}
    group by estado_key
)

select
    m.geografia_id,
    m.estado_key,
    m.municipio_key,
    e.estado,
    m.municipio,
    m.n_establecimientos,
    m.primera_fecha,
    m.ultima_fecha
from municipios as m
inner join estados as e using (estado_key)
