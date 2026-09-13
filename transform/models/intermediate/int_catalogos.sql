{#
  Grano: un valor original de `catalogo` en los CSV → catálogo del seed `catalogos`.
  Se compara por llave canónica: en 2026-07 PROFECO cambió la grafía (`Basicos` → `Básicos`, `Pacic` → `PACIC`,
  `Utiles Escolares` → `Útiles Escolares`), D-039. Un catálogo sin equivalente queda con `bit` nulo y hace fallar
  la prueba `not_null` de esta tabla.
#}
with valores as (
    select catalogo as catalogo_original, count(*) as filas
    from {{ source('raw', 'qqp_precios') }}
    group by catalogo
)

select
    v.catalogo_original,
    c.catalogo,
    c.bit,
    1 << c.bit as bit_catalogo,
    c.en_alcance_canasta,
    v.filas
from valores as v
left join {{ ref('catalogos') }} as c
    on {{ llave('c.catalogo') }} = {{ llave('v.catalogo_original') }}
