{#
  Grano: un artículo de canasta por versión. Fuente: seed versionado canasta_articulos.
#}
select
    version as canasta_version,
    articulo_id,
    articulo,
    grupo,
    producto_key,
    incluye_regex,
    excluye_regex,
    unidad_base,
    subtipo_conteo,
    cantidad_referencia,
    unidad_referencia,
    fuente_cantidad,
    version = '{{ var("canasta_version") }}' as es_version_vigente
from {{ ref('canasta_articulos') }}
