{#
  Grano: un día calendario entre la primera y la última fecha observada.
  Las semanas inician en lunes (ISO 8601).
#}
with limites as (
    select min(fecha) as desde, max(fecha) as hasta
    from {{ ref('stg_qqp__precios') }}
),

dias as (
    select cast(d as date) as fecha
    from limites, generate_series(limites.desde, limites.hasta, interval 1 day) as t(d)
)

select
    fecha,
    year(fecha) as anio,
    month(fecha) as mes,
    day(fecha) as dia,
    isodow(fecha) as dia_semana_iso,
    case isodow(fecha)
        when 1 then 'lunes' when 2 then 'martes' when 3 then 'miércoles' when 4 then 'jueves'
        when 5 then 'viernes' when 6 then 'sábado' else 'domingo'
    end as dia_semana,
    isodow(fecha) >= 6 as es_fin_de_semana,
    isoyear(fecha) as anio_iso,
    weekofyear(fecha) as semana_iso,
    cast(date_trunc('week', fecha) as date) as semana_inicio,
    cast(date_trunc('week', fecha) as date) + 6 as semana_fin,
    make_date(year(fecha), month(fecha), case when day(fecha) <= 15 then 1 else 16 end) as quincena_inicio,
    cast(date_trunc('month', fecha) as date) as mes_inicio
from dias
