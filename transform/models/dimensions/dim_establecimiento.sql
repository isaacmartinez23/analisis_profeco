{#
  Grano: un establecimiento canónico (nombre comercial + dirección + estado + municipio normalizados).
  Atributos descriptivos tomados de la variante más reciente.
  Limitación conocida: si PROFECO reescribe la dirección de una tienda, aparece como establecimiento nuevo.
#}
with variantes as (
    select * from {{ ref('int_establecimientos') }}
),

agregado as (
    select
        establecimiento_id,
        any_value(establecimiento_key) as establecimiento_key,
        arg_max(nombre_comercial_corregido, ultima_fecha) as nombre_comercial,
        arg_max(direccion_corregida, ultima_fecha) as direccion,
        arg_max(cadena_corregida, ultima_fecha) as cadena,
        arg_max(cadena_key, ultima_fecha) as cadena_key,
        arg_max(giro_corregido, ultima_fecha) as giro,
        any_value(geografia_id) as geografia_id,
        arg_max(latitud, ultima_fecha) filter (where latitud is not null) as latitud,
        arg_max(longitud, ultima_fecha) filter (where longitud is not null) as longitud,
        min(primera_fecha) as primera_fecha,
        max(ultima_fecha) as ultima_fecha,
        count(*) as n_variantes_texto,
        cast(sum(filas) as bigint) as filas_origen
    from variantes
    group by establecimiento_id
)

select
    a.*,
    a.latitud is not null and a.longitud is not null as coordenadas_validas,
    r.cadena_key is not null as es_cadena_referencia
from agregado as a
left join {{ ref('cadenas_referencia') }} as r on r.cadena_key = a.cadena_key
