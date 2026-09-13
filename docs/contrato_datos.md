# Contrato de datos

Base: `data/processed/qqp.duckdb` (muestra: `qqp_muestra.duckdb`). Esquemas: `raw` (ingesta), `mappings`
(normalización), `seeds`, `staging`, `intermediate`, `core` (modelo estrella), `marts` (publicación).

Convenciones comunes a todas las tablas:

- **Frecuencia de actualización:** en cada ejecución del pipeline (semanal en GitHub Actions, Fase 3); PROFECO
  publica un archivo por quincena.
- **Responsable técnico:** mantenedor del repositorio (ver `README.md`). **Responsable de negocio** de las reglas de
  canasta: quien aprueba los cambios a `transform/seeds/canasta_articulos.csv`.
- **Llaves `*_id`:** `md5` en texto de 32 caracteres calculado sobre llaves canónicas; estables entre ejecuciones y
  portables a PostgreSQL.
- Los tipos listados son los de DuckDB.

---

## raw.qqp_precios

| Campo | Valor |
|---|---|
| Descripción | Copia fiel de cada línea de datos de los CSV de PROFECO. |
| Grano | Una fila por línea de datos de un CSV. |
| Llave primaria | No declarada (pueden existir filas idénticas); trazabilidad por `archivo_origen`. |
| Llaves foráneas | `archivo_origen` → `raw.archivos.archivo`; `id_carga` → `raw.cargas.id_carga` |
| Fuente | `data/interim/csv/**/*.csv`, extraídos de `data/raw/*.rar|zip` |
| Reglas de calidad | Ingesta: filas = líneas físicas − 1, encabezado exacto. R-01 a R-10. Pruebas dbt de `not_null` en columnas esenciales y catálogo conocido. |
| Nulos | Se conservan tal cual; solo `latitud`/`longitud` tienen vacíos en el origen (791 filas). |
| Supuestos | Todo como `VARCHAR`; ninguna conversión en esta capa. |

Columnas: `producto`, `presentacion`, `marca`, `categoria`, `catalogo`, `precio`, `fecha_registro`,
`cadena_comercial`, `giro`, `nombre_comercial`, `direccion`, `estado`, `municipio`, `latitud`, `longitud` (todas
`VARCHAR`), `archivo_origen VARCHAR`, `id_carga VARCHAR`, `cargado_utc TIMESTAMP`.

## raw.archivos

| Campo | Valor |
|---|---|
| Descripción | Registro de cada CSV cargado y su formato físico detectado. |
| Grano | Un CSV. |
| Llave primaria | `archivo` |
| Columnas | `archivo VARCHAR`, `crc32 BIGINT`, `bytes BIGINT`, `codificacion VARCHAR`, `bom BOOLEAN`, `formato_fecha VARCHAR` (`yyyy/mm/dd` o `dd/mm/yyyy`), `lineas_fisicas BIGINT`, `filas BIGINT`, `id_carga VARCHAR`, `cargado_utc TIMESTAMP` |
| Reglas | `archivo` único; `formato_fecha` en valores permitidos; un archivo con mismo CRC32 no se recarga. |

## raw.cargas

| Campo | Valor |
|---|---|
| Descripción | Bitácora de ejecuciones de la ingesta. |
| Grano | Una ejecución. |
| Llave primaria | `id_carga` (`cAAAAMMDDTHHMMSS-xxxxxx`) |
| Columnas | `iniciada_utc`, `finalizada_utc TIMESTAMP`, `estado VARCHAR` (`en_proceso`, `exitosa`, `fallida`), `modo`, `directorio_origen VARCHAR`, `archivos_evaluados`, `archivos_cargados`, `archivos_omitidos INTEGER`, `filas_insertadas`, `filas_reemplazadas BIGINT`, `mensaje VARCHAR` |

---

## core.fct_precio_observado

| Campo | Valor |
|---|---|
| Descripción | Observaciones de precio consolidadas, con precio unitario y banderas de calidad. |
| Grano | **Una observación de precio de un producto, en un establecimiento, en una fecha.** Si PROFECO publica dos precios distintos el mismo día para el mismo producto y tienda, se conservan ambos y se marcan. |
| Llave primaria | Compuesta: `producto_id`, `establecimiento_id`, `fecha`, `precio` |
| Llaves foráneas | `producto_id` → `dim_producto`; `establecimiento_id` → `dim_establecimiento`; `fecha` → `dim_fecha` |
| Fuente | `staging.stg_qqp__precios` vía `intermediate.int_observaciones` |
| Reglas de calidad | Unicidad del grano; FKs; `precio > 0`; `precio_unitario > 0`; coherencia de banderas; suma de `n_registros_origen` = filas válidas (M-06); Q-ATIP-01/02; M-01/M-02. |
| Nulos | `precio_unitario`, `unidad_base`, `contenido_base` nulos si la presentación no es comparable. `motivo_atipico` y `regla_calidad` nulos si no es atípico. |
| Supuestos | Filas idénticas y la misma observación en varios catálogos son una sola observación. Las filas sin precio o fecha convertibles no forman observaciones (hoy: 0). |

| Columna | Tipo | Descripción |
|---|---|---|
| `producto_id` | VARCHAR | Producto normalizado |
| `establecimiento_id` | VARCHAR | Establecimiento canónico |
| `fecha` | DATE | Fecha de levantamiento |
| `precio` | DECIMAL(12,2) | Precio observado por la presentación completa (MXN) |
| `precio_unitario` | DOUBLE | `precio / contenido_base` si es comparable |
| `unidad_base` | VARCHAR | `kg`, `l` o `pieza` |
| `contenido_base` | DOUBLE | Contenido de la presentación en la unidad base |
| `es_comparable` | BOOLEAN | Presentación interpretada sin revisión pendiente |
| `precio_original` | VARCHAR | Texto original del precio |
| `producto_original`, `presentacion_original`, `marca_original` | VARCHAR | Texto original de una fila de origen |
| `catalogos_mask` | INTEGER | Bits de catálogos donde se publicó (seed `catalogos`) |
| `n_registros_origen` | BIGINT | Filas crudas consolidadas en la observación |
| `tiene_precio_en_conflicto` | BOOLEAN | Otro precio para el mismo producto, tienda y fecha |
| `precio_mediana_producto` | DOUBLE | Mediana aproximada del producto en todo el periodo |
| `n_observaciones_producto` | BIGINT | Observaciones del producto usadas en la mediana |
| `es_atipico` | BOOLEAN | Marcado por Q-ATIP-01 o Q-ATIP-02 |
| `motivo_atipico` | VARCHAR | Explicación legible |
| `regla_calidad` | VARCHAR | `Q-ATIP-01` o `Q-ATIP-02` |
| `archivo_origen` | VARCHAR | CSV de origen |
| `id_carga` | VARCHAR | Carga que insertó el archivo |
| `cargado_utc` | TIMESTAMP | Fecha de carga |

## core.dim_producto

| Campo | Valor |
|---|---|
| Descripción | Producto normalizado con interpretación de presentación y artículo de canasta. |
| Grano | Producto + presentación + marca canónicos. |
| Llave primaria | `producto_id = md5(producto_key \| presentacion_key \| marca_key)` |
| Llaves foráneas | `articulo_id` → `dim_canasta` (versión vigente) |
| Fuente | `intermediate.int_productos_sku`, `mappings.presentaciones`, seed `canasta_articulos` |
| Reglas | PK única; unidad permitida; `contenido_base > 0`; comparable ⇒ unidad y contenido presentes; un producto pertenece a lo más a un artículo. |
| Nulos | Unidad y contenido nulos si la presentación no se pudo interpretar; `articulo_id` nulo fuera de la canasta. |
| Supuestos | Los textos visibles son la variante más frecuente. |

Columnas: `producto_id`, `producto`, `producto_key`, `presentacion`, `presentacion_key`, `marca`, `marca_key`
(VARCHAR), `es_sin_marca BOOLEAN`, `categoria`, `catalogos` (VARCHAR), `unidad_base VARCHAR`,
`contenido_base DOUBLE`, `cantidad DOUBLE`, `unidad_original VARCHAR`, `unidades_empaque BIGINT`,
`subtipo_conteo`, `regla_normalizacion`, `confianza_normalizacion`, `metodo_normalizacion` (VARCHAR),
`requiere_revision BOOLEAN`, `motivo_revision VARCHAR`, `es_comparable BOOLEAN`, `articulo_id VARCHAR`,
`n_variantes_texto`, `filas_origen` (BIGINT).

## core.dim_establecimiento

| Campo | Valor |
|---|---|
| Grano | Nombre comercial + dirección + estado + municipio canónicos (con caracteres perdidos corregidos). |
| Llave primaria | `establecimiento_id` |
| Llaves foráneas | `geografia_id` → `dim_geografia` |
| Reglas | PK única; FK válida; `cadena_key` no vacío. |
| Nulos | `latitud`/`longitud` nulos si nunca hubo coordenadas dentro de México (`coordenadas_validas = false`). |
| Supuestos | Atributos de la variante más reciente. Una dirección reescrita por PROFECO genera un establecimiento nuevo. |

Columnas: `establecimiento_id`, `establecimiento_key`, `nombre_comercial`, `direccion`, `cadena`, `cadena_key`,
`giro`, `geografia_id` (VARCHAR), `latitud`, `longitud` (DOUBLE), `primera_fecha`, `ultima_fecha` (DATE),
`n_variantes_texto`, `filas_origen` (BIGINT), `coordenadas_validas`, `es_cadena_referencia` (BOOLEAN).

## core.dim_geografia

| Campo | Valor |
|---|---|
| Grano | Municipio (estado + municipio sin acentos). |
| Llave primaria | `geografia_id = md5(estado_key \| municipio_key)` |
| Columnas | `geografia_id`, `estado_key`, `municipio_key`, `estado`, `estado_iso` (ISO 3166-2:MX, seed `estados_iso`), `municipio` (VARCHAR), `n_establecimientos BIGINT`, `primera_fecha`, `ultima_fecha` (DATE) |
| Supuestos | Nombre mostrado = escritura más reciente (con acentos desde 2026). Son ciudades muestreadas, no entidades completas. |

## core.dim_fecha

| Campo | Valor |
|---|---|
| Grano | Día calendario entre la primera y la última fecha observada. |
| Llave primaria | `fecha` |
| Columnas | `fecha DATE`, `anio`, `mes`, `dia`, `dia_semana_iso` (BIGINT), `dia_semana VARCHAR`, `es_fin_de_semana BOOLEAN`, `anio_iso`, `semana_iso` (BIGINT), `semana_inicio`, `semana_fin`, `quincena_inicio`, `mes_inicio` (DATE) |
| Supuestos | Semanas ISO que inician en lunes. |

## core.dim_canasta

| Campo | Valor |
|---|---|
| Grano | Artículo de canasta por versión. |
| Llave primaria | `canasta_version`, `articulo_id` |
| Fuente | Seed versionado `transform/seeds/canasta_articulos.csv` |
| Columnas | `canasta_version`, `articulo_id`, `articulo`, `grupo`, `producto_key`, `incluye_regex`, `excluye_regex`, `unidad_base`, `subtipo_conteo` (VARCHAR), `cantidad_referencia DOUBLE`, `unidad_referencia`, `fuente_cantidad` (VARCHAR), `es_version_vigente BOOLEAN` |
| Supuestos | v0: 20 artículos; cantidades = presentación modal observada (supuesto, no consumo de hogares). |

---

## marts.mart_canasta_semanal

| Campo | Valor |
|---|---|
| Descripción | Costo semanal de la canasta de referencia por cadena y municipio. |
| Grano | Versión de canasta × cadena × municipio × semana. |
| Llave primaria | `canasta_version`, `cadena_key`, `geografia_id`, `semana_inicio` |
| Llaves foráneas | `geografia_id` → `dim_geografia`; `cadena_key` → `dim_establecimiento.cadena_key` |
| Fuente | `int_canasta_articulo_semanal` (medianas de precio unitario por artículo en ventana de 14 días) |
| Reglas | Unicidad; `1 ≤ articulos_disponibles ≤ articulos_totales`; `costo_canasta` presente ⇔ canasta completa; M-04, M-05. |
| Nulos | `costo_canasta` nulo si falta algún artículo (nunca se presenta una canasta incompleta como completa). |
| Supuestos | Ventana: semana actual + semana previa (D-010). Artículo = mediana del precio unitario de observaciones comparables no atípicas, de cualquier marca (D-009). |

| Columna | Tipo | Descripción |
|---|---|---|
| `canasta_version` | VARCHAR | Versión de la definición de canasta |
| `semana_inicio`, `semana_fin` | DATE | Semana ISO reportada |
| `ventana_desde` | DATE | Primer día de la ventana de observaciones |
| `cadena_key`, `cadena` | VARCHAR | Cadena comercial |
| `es_cadena_referencia` | BOOLEAN | Una de las 4 cadenas de D-011 |
| `geografia_id`, `estado`, `municipio` | VARCHAR | Municipio |
| `articulos_disponibles`, `articulos_totales` | BIGINT | Artículos con precio en la ventana / total de la canasta |
| `pct_articulos_disponibles` | DOUBLE | Cobertura de la canasta |
| `es_canasta_completa` | BOOLEAN | Todos los artículos disponibles |
| `costo_canasta` | DOUBLE | Costo total; solo si está completa |
| `costo_articulos_disponibles` | DOUBLE | Suma de los artículos disponibles (para cobertura, no para comparar) |
| `n_observaciones` | BIGINT | Observaciones usadas |
| `min_observaciones_por_articulo` | BIGINT | Artículo con menos respaldo |
| `max_establecimientos_por_articulo` | BIGINT | Tiendas distintas del artículo con más cobertura |
| `ventana_completa` | BOOLEAN | La ventana no está truncada por el inicio de la serie |

## Tablas publicadas en Supabase (esquema `qqp`)

Publicación atómica (D-029). Todas se reemplazan completas en cada ejecución exitosa.

| Tabla | Grano | Llave primaria | Fuente dbt |
|---|---|---|---|
| `mart_canasta_semanal`, `mart_ahorro_por_cadena`, `mart_precio_producto`, `mart_cobertura_datos` | ver secciones de cada mart | ídem | `transform/models/marts/` |
| `bi_costo_semanal_cadena` | versión × semana × cadena | `canasta_version`, `semana_inicio`, `cadena_key` | `transform/models/bi/` |
| `bi_ahorro_semanal` | versión × semana | `canasta_version`, `semana_inicio` | `transform/models/bi/` |
| `bi_diferencias_producto_semanal` | versión × semana × artículo | `canasta_version`, `semana_inicio`, `articulo_id` | `transform/models/bi/` |
| `bi_disponibilidad_articulos` | versión × semana × cadena × municipio × artículo | las cinco columnas | `transform/models/bi/` |
| `bi_indice_canasta` | versión × semana × alcance | `canasta_version`, `semana_inicio`, `alcance` | `transform/models/bi/` |
| `dim_canasta` | artículo de la versión vigente | `articulo_id` | `core.dim_canasta` |
| `dim_geografia` | municipio | `geografia_id` | `core.dim_geografia` (incluye `estado_iso`) |
| `metadatos` | una fila por publicación vigente | `id_publicacion` | generada por `src/publish/postgres.py` |

Tipos: `VARCHAR`→`text`, `DOUBLE`→`double precision`, `DECIMAL(p,s)`→`numeric(p,s)`, `BIGINT`→`bigint`,
`INTEGER`→`integer`, `BOOLEAN`→`boolean`, `DATE`→`date`, `TIMESTAMP`→`timestamp`. Un tipo sin equivalente
(`HUGEINT`) detiene la publicación.

### qqp_meta.publicaciones

Bitácora persistente (no se intercambia): `id_publicacion text PK`, `iniciada_utc`, `finalizada_utc timestamptz`,
`estado text` (`en_proceso`, `exitosa`, `fallida`), `esquema text`, `metadatos jsonb` (versión de canasta, última
semana y fecha de datos, archivos fuente, modo, commit y ejecución de CI), `filas jsonb` (filas por tabla),
`mensaje text` (error si falló).

## marts.mart_ahorro_por_cadena

| Campo | Valor |
|---|---|
| Descripción | Ahorro potencial al elegir la cadena de referencia más barata, en comparación pareada. |
| Grano | Versión × municipio × semana × cadena de referencia. |
| Llave primaria | `canasta_version`, `geografia_id`, `semana_inicio`, `cadena_key` |
| Llaves foráneas | `geografia_id` → `dim_geografia`; `cadena_key` → `seeds.cadenas_referencia` |
| Fuente | `marts.mart_canasta_semanal` (solo canastas completas con ventana completa) |
| Reglas | Unicidad; ≥2 cadenas comparadas; posición y ahorro coherentes; descomposición por artículo (D-023). |
| Nulos | Ninguno: solo contiene celdas comparables. |
| Supuestos | Empate en la más barata se resuelve por `cadena_key`. Walmart y Bodega Aurrera son el mismo grupo (`grupos_comparados`). |

Columnas: `canasta_version VARCHAR`, `semana_inicio`, `semana_fin` (DATE), `geografia_id`, `estado`, `municipio`,
`cadena_key`, `cadena`, `grupo_empresarial` (VARCHAR), `costo_canasta DOUBLE`, `posicion BIGINT`,
`cadenas_comparadas`, `grupos_comparados` (BIGINT), `costo_minimo`, `costo_maximo`, `costo_mediano` (DOUBLE),
`cadena_key_mas_barata`, `cadena_mas_barata`, `cadena_mas_cara` (VARCHAR), `es_mas_barata BOOLEAN`,
`ahorro_vs_mas_barata`, `ahorro_pct`, `diferencia_vs_mediana_pct`, `brecha_max_min`, `brecha_pct` (DOUBLE),
`n_observaciones BIGINT`.

## marts.mart_precio_producto

| Campo | Valor |
|---|---|
| Descripción | Precio unitario y costo por artículo de canasta y cadena de referencia; descompone el ahorro por artículo. |
| Grano | Versión × municipio × semana × cadena de referencia × artículo. |
| Llave primaria | `canasta_version`, `geografia_id`, `semana_inicio`, `cadena_key`, `articulo_id` |
| Llaves foráneas | `articulo_id` → `dim_canasta`; `geografia_id` → `dim_geografia` |
| Fuente | `intermediate.int_canasta_articulo_semanal`, `marts.mart_ahorro_por_cadena` |
| Reglas | Unicidad; mínimo ≤ mediana ≤ máximo; `costo_articulo > 0`; diferencia presente ⇔ celda comparable; suma = ahorro. |
| Nulos | `diferencia_vs_cadena_mas_barata` nulo fuera de celdas comparables. |
| Supuestos | Mediana de cualquier marca comparable (L-10, L-18). |

Columnas: `canasta_version`, `geografia_id`, `estado`, `municipio`, `cadena_key`, `cadena`, `articulo_id`, `articulo`,
`grupo`, `unidad_base` (VARCHAR), `semana_inicio DATE`, `cantidad_referencia`, `mediana_precio_unitario`,
`costo_articulo` (DOUBLE), `n_observaciones`, `n_establecimientos`, `n_productos`, `cadenas_con_articulo` (BIGINT),
`precio_unitario_minimo`, `precio_unitario_maximo` (DOUBLE), `es_cadena_mas_barata_articulo BOOLEAN`,
`diferencia_vs_minimo_pct DOUBLE`, `es_celda_comparable BOOLEAN`, `diferencia_vs_cadena_mas_barata DOUBLE`.

## marts.mart_cobertura_datos

| Campo | Valor |
|---|---|
| Descripción | Cobertura y representatividad de la información por cadena, municipio y semana. |
| Grano | Versión × cadena × municipio × semana (todas las cadenas). |
| Llave primaria | `canasta_version`, `cadena_key`, `geografia_id`, `semana_inicio` |
| Llaves foráneas | `geografia_id` → `dim_geografia`; `cadena_key` → `dim_establecimiento.cadena_key` |
| Fuente | `core.fct_precio_observado` (semana propia), `marts.mart_canasta_semanal` (ventana) |
| Reglas | Unicidad; conteos positivos; días entre 1 y 7; registros ≥ observaciones; artículos ≤ total. |
| Nulos | Ninguno (artículos disponibles = 0 si la cadena no tiene productos de la canasta). |
| Supuestos | Las métricas de observación no usan ventana; la disponibilidad de canasta sí. |

Columnas: `canasta_version VARCHAR`, `semana_inicio`, `semana_fin` (DATE), `cadena_key`, `cadena`, `giro` (VARCHAR),
`es_cadena_referencia BOOLEAN`, `geografia_id`, `estado`, `municipio` (VARCHAR), `n_observaciones`,
`n_registros_origen`, `n_establecimientos`, `n_productos`, `n_dias_con_observacion`, `n_atipicas`, `n_no_comparables`
(BIGINT), `pct_atipicas`, `pct_no_comparables` (DOUBLE), `articulos_canasta_disponibles`,
`articulos_canasta_totales` (BIGINT), `es_canasta_completa BOOLEAN`.
