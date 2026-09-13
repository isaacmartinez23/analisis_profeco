-- Toda combinación original de producto, presentación y marca debe tener producto normalizado.
-- Falla si algún valor crudo no aparece en los mapeos (p. ej. datos cargados después de normalizar).
with crudas as (
    select count(*) as n
    from (
        select distinct producto_original, presentacion_original, marca_original
        from {{ ref('stg_qqp__precios') }}
    )
),

mapeadas as (
    select count(*) as n from {{ ref('int_productos_sku') }}
)

select crudas.n as combinaciones_crudas, mapeadas.n as combinaciones_mapeadas
from crudas, mapeadas
where crudas.n <> mapeadas.n
