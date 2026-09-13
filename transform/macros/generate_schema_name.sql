{#
  Usa el nombre de esquema declarado (staging, intermediate, core, marts, seeds) tal cual,
  en lugar del prefijo por defecto de dbt ("main_staging").
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
