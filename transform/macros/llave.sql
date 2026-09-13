{#
  Forma canónica de un texto para compararlo: mayúsculas, sin acentos, espacios colapsados
  y sin puntuación final. Equivale a src/normalize/text.py::llave.
#}
{% macro llave(columna) -%}
    nullif(rtrim(upper(strip_accents(trim(regexp_replace({{ columna }}, '\s+', ' ', 'g')))), ' .'), '')
{%- endmacro %}
