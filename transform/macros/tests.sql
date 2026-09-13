{#
  Pruebas genéricas del proyecto (sin paquetes externos para no depender de red).
#}

{#
  Unicidad de una combinación de columnas. Con usar_hash=true agrupa por un hash de 64 bits,
  útil en tablas de decenas de millones de filas: una colisión solo puede producir un falso
  fallo, nunca ocultar un duplicado real.
#}
{% test unique_combination(model, columns, usar_hash=false, column_name=none) %}
    {% if usar_hash %}
    select hash({{ columns | join(', ') }}) as llave_hash, count(*) as n
    from {{ model }}
    group by 1
    having count(*) > 1
    {% else %}
    select {{ columns | join(', ') }}, count(*) as n
    from {{ model }}
    group by all
    having count(*) > 1
    {% endif %}
{% endtest %}

{% test expression_is_true(model, expression, column_name=none) %}
    select *
    from {{ model }}
    where not ({{ expression }})
{% endtest %}
