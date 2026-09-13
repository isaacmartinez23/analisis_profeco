{#
  Consolida las filas crudas en observaciones de precio.

  Grano: producto normalizado × establecimiento × fecha × precio.
  - Filas idénticas y la misma observación publicada en varios catálogos se cuentan una vez
    (`n_registros_origen` conserva cuántas filas crudas la respaldan; `catalogos_mask`, en qué catálogos).
  - Dos precios distintos para el mismo producto, establecimiento y fecha se conservan como dos
    observaciones y se marcan con `tiene_precio_en_conflicto`.
  - Filas sin precio o fecha convertibles no forman observaciones; las cuenta la regla R-03/R-05.

  Rendimiento: se agrupa por enteros locales (producto_num, establecimiento_num) y los textos originales
  se recuperan después con uniones a tablas pequeñas (D-005).
#}
with precios as (
    select *
    from {{ ref('stg_qqp__precios') }}
    where precio is not null and fecha is not null
),

sku as (
    select producto_original, presentacion_original, marca_original, sku_original_num, producto_num
    from {{ ref('int_productos_sku') }}
),

establecimientos as (
    select
        nombre_comercial,
        direccion,
        estado,
        municipio,
        establecimiento_original_num,
        dense_rank() over (order by establecimiento_id) as establecimiento_num
    from {{ ref('int_establecimientos') }}
),

archivos as (
    select
        archivo,
        id_carga,
        cargado_utc,
        row_number() over (order by archivo) as archivo_num
    from {{ source('raw', 'archivos') }}
),

catalogos as (
    select catalogo, 1 << bit as bit_catalogo from {{ ref('catalogos') }}
),

agrupado as (
    select
        s.producto_num,
        e.establecimiento_num,
        p.fecha,
        p.precio,
        min(s.sku_original_num) as sku_original_num,
        min(e.establecimiento_original_num) as establecimiento_original_num,
        min(p.precio_original) as precio_original,
        bit_or(c.bit_catalogo) as catalogos_mask,
        count(*) as n_registros_origen,
        min(a.archivo_num) as archivo_num
    from precios as p
    inner join sku as s using (producto_original, presentacion_original, marca_original)
    inner join establecimientos as e using (nombre_comercial, direccion, estado, municipio)
    inner join archivos as a on a.archivo = p.archivo_origen
    left join catalogos as c on c.catalogo = p.catalogo
    group by s.producto_num, e.establecimiento_num, p.fecha, p.precio
),

conflictos as (
    select producto_num, establecimiento_num, fecha
    from agrupado
    group by all
    having count(*) > 1
)

select
    g.producto_num,
    sku.producto_id,
    est.establecimiento_id,
    g.fecha,
    g.precio,
    g.precio_original,
    sku.producto_original,
    sku.presentacion_original,
    sku.marca_original,
    g.catalogos_mask,
    g.n_registros_origen,
    cf.producto_num is not null as tiene_precio_en_conflicto,
    a.archivo as archivo_origen,
    a.id_carga,
    a.cargado_utc
from agrupado as g
inner join {{ ref('int_productos_sku') }} as sku on sku.sku_original_num = g.sku_original_num
inner join {{ ref('int_establecimientos') }} as est on est.establecimiento_original_num = g.establecimiento_original_num
inner join archivos as a on a.archivo_num = g.archivo_num
left join conflictos as cf
    on cf.producto_num = g.producto_num
    and cf.establecimiento_num = g.establecimiento_num
    and cf.fecha = g.fecha
