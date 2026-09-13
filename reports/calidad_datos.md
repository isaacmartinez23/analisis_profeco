# Reporte de calidad de datos

_Generado por `python -m src.quality.checks` el 2026-09-12 22:00 · modo `completo` · base `qqp.duckdb`._

Severidad `error` detiene el pipeline y bloquea la publicación; `advertencia` se reporta sin detenerlo.
Definiciones y justificación de umbrales: `docs/reglas_calidad.md`.

## Capa cruda (`raw`)

10 reglas · 0 fallas · 0 alertas

| id   | regla                                 | severidad   |   valor | condicion   | resultado   | descripcion                                                                                                      |
|:-----|:--------------------------------------|:------------|--------:|:------------|:------------|:-----------------------------------------------------------------------------------------------------------------|
| R-01 | archivos_disponibles_cargados         | error       |  0      | == 0        | cumple      | Todos los CSV disponibles están cargados en raw.archivos (legibles y con esquema válido).                        |
| R-02 | columnas_esenciales_vacias_pct        | error       |  0      | <= 0.1      | cumple      | % de filas con producto, presentación, marca, precio, fecha, cadena, establecimiento, estado o municipio vacíos. |
| R-03 | precio_no_convertible_pct             | error       |  0      | <= 0.01     | cumple      | % de precios que no se pueden convertir a número.                                                                |
| R-04 | precio_no_positivo                    | error       |  0      | == 0        | cumple      | Número de precios negativos o iguales a cero.                                                                    |
| R-05 | fecha_no_convertible_pct              | error       |  0      | <= 0        | cumple      | % de fechas que no se pueden interpretar con el formato detectado para su archivo.                               |
| R-06 | fecha_fuera_de_rango                  | error       |  0      | == 0        | cumple      | Número de fechas anteriores a 2015-01-01 o posteriores a la fecha de ejecución.                                  |
| R-07 | fecha_distinta_al_mes_del_archivo_pct | advertencia |  0      | <= 0.1      | cumple      | % de filas cuyo mes no coincide con el mes indicado en el nombre del archivo (MM-AAAA).                          |
| R-08 | coordenadas_invalidas_pct             | advertencia |  0.0025 | <= 1        | cumple      | % de filas sin coordenadas o fuera del recuadro geográfico de México.                                            |
| R-09 | duplicados_exactos_pct                | advertencia |  0.0006 | <= 0.1      | cumple      | % de filas idénticas en las 15 columnas dentro de un mismo archivo.                                              |
| R-10 | volumen_minimo_relativo_por_archivo   | advertencia |  0.7513 | >= 0.5      | cumple      | Filas del archivo más pequeño entre la mediana de filas por archivo (detecta cargas truncadas).                  |

## Modelo transformado (`marts`)

8 reglas · 0 fallas · 1 alertas

| id   | regla                                              | severidad   |    valor | condicion   | resultado   | descripcion                                                                                                                                                                                            |
|:-----|:---------------------------------------------------|:------------|---------:|:------------|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| M-01 | observaciones_atipicas_pct                         | advertencia |   0.036  | <= 1        | cumple      | % de observaciones marcadas como atípicas (Q-ATIP-01/02).                                                                                                                                              |
| M-02 | observaciones_atipicas_pct_maximo                  | error       |   0.036  | <= 5        | cumple      | % de observaciones atípicas por encima del cual el pipeline se detiene (posible error sistemático).                                                                                                    |
| M-03 | observaciones_no_comparables_catalogos_canasta_pct | advertencia |   2.4591 | <= 5        | cumple      | % de observaciones de catálogos de canasta (Básicos, Frutas y Legumbres, Pacic) sin presentación comparable.                                                                                           |
| M-04 | celdas_referencia_canasta_completa_pct             | advertencia |  80.9632 | >= 50       | cumple      | % de celdas cadena de referencia × municipio × semana (ventana completa) con la canasta completa.                                                                                                      |
| M-05 | articulos_sin_observaciones_ultima_semana          | advertencia |   0      | == 0        | cumple      | Artículos de la canasta sin ninguna observación comparable en la última semana (cadenas de referencia).                                                                                                |
| M-07 | municipio_semanas_comparables_pct                  | advertencia |  85.2069 | >= 70       | cumple      | % de municipio-semanas con al menos dos cadenas de referencia en la canasta (ventana completa) donde al menos dos tienen la canasta completa y por lo tanto se puede calcular ahorro.                  |
| M-08 | dias_desde_ultimo_dato                             | advertencia | 106      | <= 35       | alerta      | Días entre la fecha más reciente con precios y la fecha de ejecución. PROFECO publica por quincena; más de 35 días sugiere que no se descargó el archivo vigente o que la fuente dejó de actualizarse. |
| M-06 | filas_crudas_sin_observacion                       | error       |   0      | == 0        | cumple      | Filas crudas con precio y fecha válidos que no llegaron a la tabla de hechos.                                                                                                                          |
