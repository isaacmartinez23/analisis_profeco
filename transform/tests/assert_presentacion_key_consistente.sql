-- Todas las variantes de texto con la misma llave de presentación deben tener la misma interpretación.
select
    presentacion_key,
    count(distinct (unidad_base, contenido_base, subtipo_conteo, es_comparable)) as interpretaciones
from {{ source('mappings', 'presentaciones') }}
group by presentacion_key
having count(distinct (unidad_base, contenido_base, subtipo_conteo, es_comparable)) > 1
