{#
  Grano: un municipio (estado + municipio normalizados sin acentos).
  El nombre mostrado es la escritura más reciente (con acentos desde 2026).
  Representa ciudades muestreadas por PROFECO, no la entidad completa (D-012).
#}
select
    geografia_id,
    any_value(estado_key) as estado_key,
    any_value(municipio_key) as municipio_key,
    arg_max(estado, ultima_fecha) as estado,
    arg_max(municipio, ultima_fecha) as municipio,
    count(distinct establecimiento_id) as n_establecimientos,
    min(primera_fecha) as primera_fecha,
    max(ultima_fecha) as ultima_fecha
from {{ ref('int_establecimientos') }}
group by geografia_id
