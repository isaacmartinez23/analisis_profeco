{#
  Tipado de la capa cruda. Grano: una fila por línea de CSV (igual que raw.qqp_precios).
  La fecha se interpreta con el formato detectado para cada archivo en la ingesta; no se adivina
  fila por fila. Los valores originales se conservan para trazabilidad.
#}
with precios as (
    select * from {{ source('raw', 'qqp_precios') }}
),

archivos as (
    select archivo, formato_fecha from {{ source('raw', 'archivos') }}
)

select
    p.producto as producto_original,
    p.presentacion as presentacion_original,
    p.marca as marca_original,
    p.categoria,
    p.catalogo,
    p.precio as precio_original,
    try_cast(p.precio as decimal(12, 2)) as precio,
    p.fecha_registro as fecha_original,
    case a.formato_fecha
        when 'yyyy/mm/dd' then try_strptime(p.fecha_registro, '%Y/%m/%d')
        when 'dd/mm/yyyy' then try_strptime(p.fecha_registro, '%d/%m/%Y')
    end::date as fecha,
    p.cadena_comercial,
    p.giro,
    p.nombre_comercial,
    p.direccion,
    p.estado,
    p.municipio,
    try_cast(p.latitud as double) as latitud,
    try_cast(p.longitud as double) as longitud,
    p.archivo_origen,
    p.id_carga,
    p.cargado_utc
from precios as p
inner join archivos as a
    on a.archivo = p.archivo_origen
