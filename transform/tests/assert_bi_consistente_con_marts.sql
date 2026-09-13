-- Las vistas BI deben ser consistentes con los marts de los que salen:
-- (1) la suma de diferencias por artículo reproduce el ahorro total (tolerancia relativa 0.01%);
-- (2) el número de artículos disponibles por canasta coincide con mart_canasta_semanal.
with diferencias as (
    select coalesce(sum(diferencia_acumulada), 0) as total from {{ ref('bi_diferencias_producto_semanal') }}
),

ahorro as (
    select coalesce(sum(ahorro_vs_mas_barata), 0) as total from {{ ref('mart_ahorro_por_cadena') }}
),

disponibilidad as (
    select canasta_version, semana_inicio, cadena_key, geografia_id,
           count(*) filter (where disponible) as disponibles, any_value(articulos_disponibles) as esperados
    from {{ ref('bi_disponibilidad_articulos') }}
    group by all
)

select 'diferencias_vs_ahorro' as prueba, d.total as valor, a.total as esperado
from diferencias as d, ahorro as a
where abs(d.total - a.total) > greatest(0.0001 * abs(a.total), 1)

union all

select 'disponibilidad_vs_canasta', disponibles, esperados
from disponibilidad
where disponibles <> esperados
