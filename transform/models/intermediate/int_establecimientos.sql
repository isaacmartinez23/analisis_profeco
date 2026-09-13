{#
  Grano: una fila por combinación original (nombre comercial, dirección, estado, municipio).
  Aplica las correcciones de caracteres perdidos y construye las llaves canónicas de establecimiento,
  geografía y cadena. Cadena, giro y coordenadas se toman del registro más reciente.
  Coordenadas fuera de México se descartan (regla R-08).
#}
with combinaciones as (
    select
        nombre_comercial,
        direccion,
        estado,
        municipio,
        arg_max(cadena_comercial, fecha) as cadena_comercial,
        arg_max(giro, fecha) as giro,
        arg_max(latitud, fecha) filter (
            where latitud between 14 and 33 and longitud between -119 and -86
        ) as latitud,
        arg_max(longitud, fecha) filter (
            where latitud between 14 and 33 and longitud between -119 and -86
        ) as longitud,
        min(fecha) as primera_fecha,
        max(fecha) as ultima_fecha,
        count(*) as filas
    from {{ ref('stg_qqp__precios') }}
    group by nombre_comercial, direccion, estado, municipio
),

correcciones as (
    select columna, valor_original, valor_corregido
    from {{ source('mappings', 'texto_correcciones') }}
    where valor_corregido is not null
),

corregidas as (
    select
        c.*,
        coalesce(cn.valor_corregido, c.nombre_comercial) as nombre_comercial_corregido,
        coalesce(cd.valor_corregido, c.direccion) as direccion_corregida,
        coalesce(cc.valor_corregido, c.cadena_comercial) as cadena_corregida,
        coalesce(cg.valor_corregido, c.giro) as giro_corregido
    from combinaciones as c
    left join correcciones as cn on cn.columna = 'nombre_comercial' and cn.valor_original = c.nombre_comercial
    left join correcciones as cd on cd.columna = 'direccion' and cd.valor_original = c.direccion
    left join correcciones as cc on cc.columna = 'cadena_comercial' and cc.valor_original = c.cadena_comercial
    left join correcciones as cg on cg.columna = 'giro' and cg.valor_original = c.giro
),

llaves as (
    select
        *,
        coalesce({{ llave('estado') }}, '') as estado_key,
        coalesce({{ llave('municipio') }}, '') as municipio_key,
        coalesce({{ llave('cadena_corregida') }}, '') as cadena_key,
        coalesce({{ llave('nombre_comercial_corregido') }}, '') || '|' || coalesce({{ llave('direccion_corregida') }}, '')
            as establecimiento_key
    from corregidas
)

select
    row_number() over (order by nombre_comercial, direccion, estado, municipio) as establecimiento_original_num,
    md5(establecimiento_key || '|' || estado_key || '|' || municipio_key) as establecimiento_id,
    md5(estado_key || '|' || municipio_key) as geografia_id,
    *
from llaves
