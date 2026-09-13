-- Ningún registro con precio y fecha válidos se pierde al consolidar observaciones:
-- la suma de n_registros_origen de la tabla de hechos debe igualar las filas válidas de staging.
with validas as (
    select count(*) as n
    from {{ ref('stg_qqp__precios') }}
    where precio is not null and fecha is not null
),

consolidadas as (
    select sum(n_registros_origen) as n from {{ ref('fct_precio_observado') }}
)

select validas.n as filas_validas, consolidadas.n as filas_en_hechos
from validas, consolidadas
where validas.n <> consolidadas.n
