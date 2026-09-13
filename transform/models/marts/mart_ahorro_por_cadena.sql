{#
  Ahorro potencial al elegir la cadena de referencia más económica.

  Grano: versión de canasta × municipio × semana × cadena de referencia.
  Comparación pareada: solo municipio-semanas donde al menos dos cadenas de referencia tienen la canasta
  completa con ventana completa. Así las cadenas se comparan con la misma canasta, en la misma ciudad y
  en la misma semana, no con promedios de conjuntos distintos de ciudades.

  ahorro_vs_mas_barata = costo de esta cadena − costo de la más barata del municipio-semana.
  Empates en la más barata se resuelven por cadena_key para que el resultado sea determinista.
#}
with canastas as (
    select c.*, r.grupo_empresarial
    from {{ ref('mart_canasta_semanal') }} as c
    inner join {{ ref('cadenas_referencia') }} as r using (cadena_key)
    where c.es_canasta_completa and c.ventana_completa
),

celdas as (
    select
        geografia_id,
        semana_inicio,
        count(*) as cadenas_comparadas,
        count(distinct grupo_empresarial) as grupos_comparados,
        min(costo_canasta) as costo_minimo,
        max(costo_canasta) as costo_maximo,
        median(costo_canasta) as costo_mediano,
        first(cadena_key order by costo_canasta, cadena_key) as cadena_key_mas_barata,
        first(cadena order by costo_canasta, cadena_key) as cadena_mas_barata,
        first(cadena order by costo_canasta desc, cadena_key) as cadena_mas_cara
    from canastas
    group by geografia_id, semana_inicio
    having count(*) >= 2
)

select
    c.canasta_version,
    c.semana_inicio,
    c.semana_fin,
    c.geografia_id,
    c.estado,
    c.municipio,
    c.cadena_key,
    c.cadena,
    c.grupo_empresarial,
    c.costo_canasta,
    rank() over (partition by c.geografia_id, c.semana_inicio order by c.costo_canasta) as posicion,
    k.cadenas_comparadas,
    k.grupos_comparados,
    k.costo_minimo,
    k.costo_maximo,
    round(k.costo_mediano, 2) as costo_mediano,
    k.cadena_key_mas_barata,
    k.cadena_mas_barata,
    k.cadena_mas_cara,
    c.cadena_key = k.cadena_key_mas_barata as es_mas_barata,
    round(c.costo_canasta - k.costo_minimo, 2) as ahorro_vs_mas_barata,
    round(100 * (c.costo_canasta - k.costo_minimo) / c.costo_canasta, 2) as ahorro_pct,
    round(100 * (c.costo_canasta - k.costo_mediano) / k.costo_mediano, 2) as diferencia_vs_mediana_pct,
    round(k.costo_maximo - k.costo_minimo, 2) as brecha_max_min,
    round(100 * (k.costo_maximo - k.costo_minimo) / k.costo_maximo, 2) as brecha_pct,
    c.n_observaciones
from canastas as c
inner join celdas as k using (geografia_id, semana_inicio)
