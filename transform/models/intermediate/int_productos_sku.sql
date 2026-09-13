{#
  Grano: una fila por combinación original (producto, presentación, marca) tal como aparece en los CSV.
  Asigna el producto normalizado (producto_id) a partir de los mapeos de src/normalize.
  `sku_original_num` y `producto_num` son enteros locales a la ejecución, usados solo para agrupar
  eficientemente en int_observaciones; no se publican.
#}
with combinaciones as (
    select
        producto_original,
        presentacion_original,
        marca_original,
        catalogo,
        categoria,
        count(*) as filas
    from {{ ref('stg_qqp__precios') }}
    group by all
),

catalogos as (
    select catalogo, 1 << bit as bit_catalogo from {{ ref('catalogos') }}
),

por_combinacion as (
    select
        c.producto_original,
        c.presentacion_original,
        c.marca_original,
        bit_or(cat.bit_catalogo) as catalogos_mask,
        -- Pacic reutiliza productos de otros catálogos con categorías propias: se prefiere la categoría original.
        coalesce(
            arg_max(c.categoria, c.filas) filter (where c.catalogo <> 'Pacic'),
            arg_max(c.categoria, c.filas)
        ) as categoria,
        cast(sum(c.filas) as bigint) as filas
    from combinaciones as c
    left join catalogos as cat on cat.catalogo = c.catalogo
    group by c.producto_original, c.presentacion_original, c.marca_original
),

normalizado as (
    select
        md5(p.producto_key || '|' || pr.presentacion_key || '|' || m.marca_key) as producto_id,
        s.producto_original,
        s.presentacion_original,
        s.marca_original,
        p.producto_corregido,
        p.producto_key,
        pr.presentacion_corregida,
        pr.presentacion_key,
        m.marca_corregida,
        m.marca_key,
        m.es_sin_marca,
        s.categoria,
        s.catalogos_mask,
        s.filas
    from por_combinacion as s
    inner join {{ source('mappings', 'productos') }} as p on p.producto_original = s.producto_original
    inner join {{ source('mappings', 'presentaciones') }} as pr on pr.presentacion_original = s.presentacion_original
    inner join {{ source('mappings', 'marcas') }} as m on m.marca_original = s.marca_original
)

select
    row_number() over (order by producto_original, presentacion_original, marca_original) as sku_original_num,
    dense_rank() over (order by producto_id) as producto_num,
    *
from normalizado
