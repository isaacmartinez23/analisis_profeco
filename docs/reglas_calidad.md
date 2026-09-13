# Reglas de calidad de datos

Tres niveles complementarios:

| Nivel | Dónde | Qué valida | Si falla |
|---|---|---|---|
| Ingesta | `src/ingest/load.py`, `src.cli inspect` | Archivo legible, encabezado exacto de 15 columnas, formato de fecha reconocido, filas cargadas = líneas físicas − 1 | Se revierte la carga del archivo y el pipeline se detiene |
| Reglas con umbral | `src/quality/checks.py` | Métricas de completitud, validez, cobertura y atípicos | `error` detiene el pipeline; `advertencia` se reporta |
| Pruebas dbt | `transform/models/**/_*.yml`, `transform/tests/` | Llaves únicas, integridad referencial, valores permitidos, conservación de registros | `dbt test` falla y el pipeline se detiene |

El reporte generado está en `reports/calidad_datos.md`. La publicación (Fase 3) solo ocurre si todo lo anterior pasa.

## Reglas sobre la capa cruda (`raw`)

| ID | Regla | Severidad | Umbral | Justificación |
|---|---|---|---|---|
| R-01 | Todos los CSV disponibles están cargados | error | faltantes = 0 | Un archivo sin cargar produce huecos silenciosos en la serie. |
| R-02 | Columnas esenciales vacías | error | ≤ 0.1% | En el perfil hay 0%; un aumento indica cambio de formato de PROFECO. |
| R-03 | Precio no convertible a número | error | ≤ 0.01% | En el perfil hay 0%; sin precio no hay observación. |
| R-04 | Precio ≤ 0 | error | = 0 | Un precio no positivo es imposible. |
| R-05 | Fecha no interpretable con el formato de su archivo | error | = 0% | La fecha define semana y ventana; no se imputa. |
| R-06 | Fecha antes de 2015 o en el futuro | error | = 0 | Detecta inversión día/mes u otro error de formato. |
| R-07 | Mes de la fecha distinto al del nombre del archivo | advertencia | ≤ 0.1% | En el perfil hay 0%; señala archivos mal nombrados o mezclados. |
| R-08 | Coordenadas vacías o fuera de México | advertencia | ≤ 1% | En el perfil 0.003% vacías; afecta mapas, no precios. |
| R-09 | Filas idénticas dentro de un archivo | advertencia | ≤ 0.1% | En el perfil 0.001%; se consolidan en la tabla de hechos. |
| R-10 | Filas del archivo más pequeño / mediana | advertencia | ≥ 0.5 | Detecta archivos truncados; el mínimo observado es ~0.75. |

Además, `src.cli inspect` detiene el pipeline ante un **cambio de esquema** (encabezado distinto o filas con
número incorrecto de columnas) y la ingesta rechaza formatos de fecha no reconocidos o mezclados.

## Reglas sobre el modelo transformado (`marts`)

| ID | Regla | Severidad | Umbral | Justificación |
|---|---|---|---|---|
| M-01 | Observaciones atípicas | advertencia | ≤ 1% | Los atípicos deben ser excepcionales; más indica umbrales mal calibrados. |
| M-02 | Observaciones atípicas (máximo) | error | ≤ 5% | Un porcentaje alto sugiere un error sistemático (p. ej. unidades) y bloquea la publicación. |
| M-03 | Observaciones de catálogos de canasta sin presentación comparable | advertencia | ≤ 5% | Mide cuánto queda fuera por normalización pendiente. |
| M-04 | Celdas cadena de referencia × municipio × semana con canasta completa | advertencia | ≥ 50% | Cobertura mínima para comparar cadenas; ver D-009 a D-012. |
| M-05 | Artículos sin observaciones en la última semana | advertencia | = 0 | Un artículo que desaparece rompe la canasta completa. |
| M-06 | Filas válidas que no llegaron a la tabla de hechos | error | = 0 | Garantiza que la consolidación no pierde registros. |
| M-07 | Municipio-semanas con ≥2 cadenas de referencia donde ≥2 tienen canasta completa | advertencia | ≥ 70% | Base mínima para estimar ahorro con comparaciones pareadas (D-023). |
| M-08 | Días desde la fecha más reciente con precios | advertencia | ≤ 35 | PROFECO publica por quincena; más de 35 días indica que no se descargó el archivo vigente o que la fuente se detuvo (D-034). |

## Alertas

Cualquier paso que falle dispara `src/alertas.py` con estado `fallo`; al final de una ejecución exitosa se reportan
las reglas en alerta. Destinos: resumen de GitHub Actions, webhook opcional (`ALERTA_WEBHOOK_URL`) e issue
`alerta-pipeline` en el repositorio (workflow). La publicación nunca ocurre si falló una regla `error`, una prueba dbt
o la validación independiente.

## Validación independiente (compuerta)

`python -m src.cli validate` (`src/analysis/validacion.py`) recalcula en Python, desde `raw.qqp_precios`, el costo de
canasta y el ahorro de 6 municipio-semanas comparables y deterministas, y los compara con los marts (±0.011 MXN en
costo, ±0.022 MXN en ahorro). Cualquier diferencia detiene el pipeline antes de publicar. Reporte:
`reports/validacion_canasta.md` (D-024).

## Atípicos (marcados, nunca eliminados)

La tabla `core.fct_precio_observado` conserva el precio original y agrega `es_atipico`, `motivo_atipico` y
`regla_calidad`:

| Código | Condición | Parámetros (`transform/dbt_project.yml`) |
|---|---|---|
| Q-ATIP-01 | precio > 10 × mediana del producto, o < mediana / 10 | `atipico_factor_mediana` |
| Q-ATIP-02 | \|ln(precio) − mediana ln\| > 5 × 1.4826 × MAD **y** precio > 3 × mediana o < mediana / 3, con ≥ 30 observaciones del producto | `atipico_umbral_mad`, `atipico_factor_minimo_mad`, `atipico_min_observaciones` |

Las estadísticas son por producto normalizado (producto + presentación + marca) sobre todo el periodo, con
mediana y MAD exactas (D-021: la versión aproximada no era determinista). La magnitud mínima de Q-ATIP-02 se agregó tras validar en la muestra que, sin ella, la MAD casi
nula de productos de precio estable marcaba precios normales (leche a 0.95× la mediana) como atípicos.

Los atípicos se excluyen del cálculo de medianas de la canasta (`int_canasta_observaciones`), pero siguen en la
tabla de hechos para auditoría.

## Pruebas dbt principales

- **Unicidad**: `dim_producto.producto_id`, `dim_establecimiento.establecimiento_id`, `dim_geografia.geografia_id`,
  `dim_fecha.fecha`, `dim_canasta (versión, artículo)`, grano de `fct_precio_observado` y de `mart_canasta_semanal`.
- **Integridad referencial**: hechos → cuatro dimensiones; establecimiento → geografía; producto → canasta;
  `raw.qqp_precios.catalogo` → seed `catalogos` (un catálogo nuevo falla).
- **Validez**: precio > 0, precio unitario > 0, contenido base > 0, unidades permitidas, reglas de atípico permitidas.
- **Coherencia**: `es_atipico` ⇔ regla y motivo presentes; precio unitario presente ⇔ presentación comparable;
  `costo_canasta` presente ⇔ canasta completa.
- **Conservación** (`transform/tests/`): toda combinación cruda está mapeada; suma de `n_registros_origen` = filas
  válidas de staging; una misma llave de presentación tiene una sola interpretación.
- **Ahorro**: posición entre 1 y cadenas comparadas; costo entre mínimo y máximo; ahorro ≥ 0 y 0 en la más barata;
  la suma por artículo de `diferencia_vs_cadena_mas_barata` reproduce el ahorro (`assert_descomposicion_ahorro`).
- **Cobertura**: días con observación entre 1 y 7; registros de origen ≥ observaciones; artículos disponibles ≤ total.
