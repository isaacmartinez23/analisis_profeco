{#
  Grano: un producto normalizado (producto + presentación + marca canónicos).
  Variantes de texto (acentos, mayúsculas, caracteres perdidos) se agrupan en un mismo producto_id.
  Incluye la interpretación de la presentación (unidad base y contenido) y la asignación al artículo
  de canasta vigente, si cumple su regla.
#}
with sku as (
    select * from {{ ref('int_productos_sku') }}
),

por_producto as (
    select
        producto_id,
        arg_max(producto_corregido, filas) as producto,
        any_value(producto_key) as producto_key,
        arg_max(presentacion_corregida, filas) as presentacion,
        any_value(presentacion_key) as presentacion_key,
        arg_max(marca_corregida, filas) as marca,
        any_value(marca_key) as marca_key,
        bool_or(es_sin_marca) as es_sin_marca,
        arg_max(categoria, filas) as categoria,
        bit_or(catalogos_mask) as catalogos_mask,
        count(*) as n_variantes_texto,
        cast(sum(filas) as bigint) as filas_origen
    from sku
    group by producto_id
),

presentaciones as (
    -- Todas las variantes con la misma llave tienen la misma interpretación (prueba assert_presentacion_key_consistente).
    select distinct on (presentacion_key)
        presentacion_key,
        unidad_base,
        contenido_base,
        cantidad,
        unidad_original,
        unidades_empaque,
        subtipo_conteo,
        regla as regla_normalizacion,
        confianza as confianza_normalizacion,
        requiere_revision,
        motivo_revision,
        metodo as metodo_normalizacion,
        es_comparable
    from {{ source('mappings', 'presentaciones') }}
    order by presentacion_key, presentacion_original
),

catalogos as (
    select
        p.producto_id,
        string_agg(c.catalogo, ' + ' order by c.bit) as catalogos
    from por_producto as p
    inner join {{ ref('catalogos') }} as c on (p.catalogos_mask >> c.bit) & 1 = 1
    group by p.producto_id
),

canasta as (
    select *
    from {{ ref('canasta_articulos') }}
    where version = '{{ var("canasta_version") }}'
),

asignacion as (
    select
        p.producto_id,
        c.articulo_id
    from por_producto as p
    inner join presentaciones as pr using (presentacion_key)
    inner join canasta as c
        on c.producto_key = p.producto_key
        and c.unidad_base = pr.unidad_base
        and (c.subtipo_conteo is null or c.subtipo_conteo = pr.subtipo_conteo)
        and regexp_matches(p.presentacion_key, c.incluye_regex)
        and (c.excluye_regex is null or not regexp_matches(p.presentacion_key, c.excluye_regex))
)

select
    p.producto_id,
    p.producto,
    p.producto_key,
    p.presentacion,
    p.presentacion_key,
    p.marca,
    p.marca_key,
    p.es_sin_marca,
    p.categoria,
    cat.catalogos,
    pr.unidad_base,
    pr.contenido_base,
    pr.cantidad,
    pr.unidad_original,
    pr.unidades_empaque,
    pr.subtipo_conteo,
    pr.regla_normalizacion,
    pr.confianza_normalizacion,
    pr.metodo_normalizacion,
    pr.requiere_revision,
    pr.motivo_revision,
    pr.es_comparable,
    a.articulo_id,
    p.n_variantes_texto,
    p.filas_origen
from por_producto as p
inner join presentaciones as pr using (presentacion_key)
left join catalogos as cat using (producto_id)
left join asignacion as a using (producto_id)
