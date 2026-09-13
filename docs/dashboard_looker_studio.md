# Especificación del dashboard en Looker Studio

Dashboard reproducible sobre las tablas que publica `python -m src.cli publish` en Supabase (esquema `qqp`).
Definiciones de métricas: `docs/catalogo_metricas.md`. Salvedades obligatorias: sección 6.

## 1. Conexión

### 1.1 Rol de solo lectura (una vez, en el SQL Editor de Supabase)

Looker Studio no debe usar el usuario `postgres`. Crea un rol de solo lectura. La contraseña la eliges tú en el
momento; no se guarda en el repositorio.

```sql
create role looker_lector login password '<define-una-contraseña-fuerte>';
```

No otorgues permisos todavía: el esquema `qqp` no existe hasta la primera publicación. Define la variable de
repositorio `QQP_PG_ROL_LECTURA=looker_lector` en GitHub (Settings → Secrets and variables → Actions → Variables):
cada publicación reemplaza el esquema completo y otorga `USAGE` y `SELECT` a ese rol. Crea el rol **antes** de definir
la variable; si la variable apunta a un rol inexistente, la publicación falla (y conserva la versión anterior).

### 1.2 Cadena de conexión

Supabase expone la conexión directa solo por IPv6 (salvo con el complemento de IPv4). Tanto GitHub Actions como
Looker Studio deben usar el **pooler compartido en modo sesión**, que es IPv4
([documentación de Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)). No uses el modo
transacción (puerto 6543): no admite *prepared statements* y el publicador usa psycopg, que los activa.

En el panel de Supabase: **Connect → Session pooler**.

| Campo de Looker Studio (conector PostgreSQL) | Valor |
|---|---|
| Nombre de host o IP | `aws-<región>.pooler.supabase.com` (el que muestre tu proyecto) |
| Puerto | `5432` |
| Base de datos | `postgres` |
| Nombre de usuario | `looker_lector.<project-ref>` (el pooler requiere el sufijo del proyecto) |
| Contraseña | la del rol `looker_lector` |
| Habilitar SSL | Sí |

Para el pipeline se usan los mismos host y puerto, con el usuario `postgres.<project-ref>`, en los secretos
`SUPABASE_DB_*` de GitHub Actions.

### 1.3 Fuentes de datos

Crea una fuente por tabla. Todas se actualizan semanalmente; configura la frescura de datos en 12 horas.

| Fuente en Looker Studio | Tabla | Grano | Uso |
|---|---|---|---|
| QQP · Costo por cadena | `qqp.bi_costo_semanal_cadena` | semana × cadena | Página 2 |
| QQP · Ahorro semanal | `qqp.bi_ahorro_semanal` | semana | Páginas 1 y 3 |
| QQP · Ahorro por municipio | `qqp.mart_ahorro_por_cadena` | municipio × semana × cadena | Página 3 (detalle) |
| QQP · Diferencias por producto | `qqp.bi_diferencias_producto_semanal` | semana × artículo | Página 4 |
| QQP · Precio por producto | `qqp.mart_precio_producto` | municipio × semana × cadena × artículo (**últimas 52 semanas**) | Página 4 (detalle) |
| QQP · Cobertura | `qqp.mart_cobertura_datos` | cadena × municipio × semana | Página 5 |
| QQP · Canasta semanal | `qqp.mart_canasta_semanal` | cadena × municipio × semana | Página 6 |
| QQP · Disponibilidad | `qqp.bi_disponibilidad_semanal` | semana × cadena × artículo (nacional) | Página 6 |
| QQP · Artículos faltantes | `qqp.bi_articulos_faltantes` | cadena × municipio × semana × artículo sin precio | Página 6 (detalle) |
| QQP · Índice | `qqp.bi_indice_canasta` | semana × alcance | Páginas 1 y 2 |
| QQP · Canasta | `qqp.dim_canasta` | artículo | Página 6 y notas |
| QQP · Geografía | `qqp.dim_geografia` | municipio | Mapa (`estado_iso` como región ISO) |
| QQP · Metadatos | `qqp.metadatos` | una fila | Encabezado |

Tipos a revisar al crear las fuentes: `semana_inicio` como **Fecha (AAAAMMDD)**; `estado_iso` como
**Geo → Código de región ISO 3166-2**; columnas `pct_*` como **Número** (ya están en porcentaje, no como fracción).

## 2. Controles globales

Presentes en todas las páginas, arriba a la derecha:

| Control | Campo | Predeterminado |
|---|---|---|
| Periodo | `semana_inicio` | Últimas 12 semanas |
| Cadena | `cadena` | Todas |
| Estado | `estado` | Todos (solo en páginas con geografía) |
| Grupo empresarial | `grupo_empresarial` | Todos |

Filtro fijo a nivel de informe: `canasta_version = v1` (evita mezclar versiones si se publica otra).

Encabezado: texto con `metadatos.ultima_fecha_datos` ("Datos al …") y `metadatos.publicado_utc`.

## 3. Páginas

### Página 1 · Resumen

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Ahorro máximo mediano | Cuadro de resultados | Ahorro semanal | Métrica `ahorro_maximo_mediano`, agregación **Mediana**; comparación con el periodo anterior |
| Ahorro máximo (%) | Cuadro de resultados | Ahorro semanal | `ahorro_maximo_mediano_pct`, **Mediana** |
| Municipio-semanas comparables | Cuadro de resultados | Ahorro semanal | `municipios_comparables`, **Suma** |
| Índice de la canasta | Cuadro de resultados | Índice | Filtro `alcance = Todas las cadenas de referencia`; `indice_base_100` de la última semana (**Máx.** con orden por fecha) |
| Evolución del índice | Serie temporal | Índice | Dimensión `semana_inicio`; desglose `alcance`; métrica `indice_base_100` (**Promedio**) |
| Cadena más barata con más frecuencia | Tabla | Costo por cadena | Dimensión `cadena`; métrica `veces_mas_barata` (**Suma**) y campo calculado *Frecuencia como más barata* |

### Página 2 · Costo de la canasta por cadena (vista 1)

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Costo mediano semanal | Serie temporal | Costo por cadena | Dimensión `semana_inicio`; desglose `cadena`; métrica `costo_mediano` (**Promedio**) |
| Rango intercuartil | Tabla con barras | Costo por cadena | `cadena`, `costo_p25`, `costo_mediano`, `costo_p75` (**Promedio**) |
| Municipios comparables | Gráfico de barras | Costo por cadena | `cadena` × `municipios_comparables` (**Suma**) |

Nota visible: "Costos en municipio-semanas donde al menos dos cadenas tienen la canasta completa. Las cadenas se
comparan en las mismas ciudades y semanas."

### Página 3 · Ahorro potencial entre cadenas (vista 2)

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Ahorro máximo por semana | Serie temporal | Ahorro semanal | `ahorro_maximo_mediano` y `ahorro_maximo_p90` (**Promedio**) |
| Solo competidores | Cuadro de resultados | Ahorro semanal | `ahorro_maximo_mediano_competidores` (**Mediana**); excluye celdas donde solo compiten Wal-mart y Bodega Aurrera |
| Ahorro al cambiarse a la más barata | Gráfico de barras | Costo por cadena | `cadena` × `ahorro_mediano_vs_mas_barata` (**Mediana**) y campo calculado *Ahorro anual equivalente* |
| Detalle por municipio | Tabla | Ahorro por municipio | `estado`, `municipio`, `semana_inicio`, `cadena`, `posicion`, `costo_canasta`, `ahorro_vs_mas_barata`, `ahorro_pct` |

### Página 4 · Diferencias por producto (vista 3)

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Ranking de artículos | Gráfico de barras horizontal | Diferencias por producto | Dimensión `articulo`; métrica `diferencia_acumulada` (**Suma**), orden descendente; comparación "porcentaje del total" |
| Sobreprecio mediano | Tabla | Diferencias por producto | `articulo`, `sobreprecio_mediano_pct` (**Mediana**), `precio_unitario_mediano` (**Mediana**), `unidad_base` |
| Precio por cadena y artículo | Tabla dinámica | Precio por producto | Filas `articulo`; columnas `cadena`; métrica `mediana_precio_unitario` (**Mediana**) |

Nota visible: "La suma de las diferencias de todos los artículos es el ahorro total de cambiarse a la cadena más
barata. Un valor negativo indica que ese artículo es más barato en la cadena que perdió."

### Página 5 · Cobertura por municipio, cadena y semana (vista 4)

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Mapa de observaciones | Mapa geográfico | Cobertura combinada con Geografía por `geografia_id` | Región `estado_iso`; métrica `n_observaciones` (**Suma**) |
| Mapa de calor | Tabla dinámica con mapa de calor | Cobertura | Filas `municipio`; columnas `semana_inicio` (por mes); métrica `n_observaciones` (**Suma**) |
| Calidad por cadena | Tabla | Cobertura | `cadena`, `n_establecimientos` (**Promedio**), `n_dias_con_observacion` (**Promedio**), `pct_atipicas` (**Promedio**), `pct_no_comparables` (**Promedio**) |

Filtro de la página: `es_cadena_referencia = true` (con un control para quitarlo).

### Página 6 · Productos disponibles en cada canasta (vista 5)

| Elemento | Tipo | Fuente | Configuración |
|---|---|---|---|
| Disponibilidad por artículo y cadena | Tabla dinámica con mapa de calor | Disponibilidad | Filas `articulo`; columnas `cadena`; campo calculado *Disponibilidad* |
| Canastas completas | Cuadro de resultados | Canasta semanal | Filtro `es_cadena_referencia = true`; campo calculado *Canastas completas (%)* |
| Artículos faltantes | Tabla | Artículos faltantes | `semana_inicio`, `estado`, `municipio`, `cadena`, `articulo` |

Nota visible: "Mapa de disponibilidad nacional. El detalle por municipio lista solo los artículos sin precio en la
ventana, que son los que dejan incompleta una canasta."

## 4. Campos calculados

Sintaxis de Looker Studio. Todos son trazables a columnas publicadas.

| Nombre | Fuente | Fórmula |
|---|---|---|
| Frecuencia como más barata | Costo por cadena | `SUM(veces_mas_barata) / SUM(municipios_comparables)` (formato porcentaje) |
| Ahorro anual equivalente | Costo por cadena | `ahorro_mediano_vs_mas_barata * 52` |
| Disponibilidad | Disponibilidad | `SUM(celdas_con_articulo) / SUM(celdas)` (formato porcentaje) |
| Canastas completas (%) | Canasta semanal | `SUM(CASE WHEN es_canasta_completa THEN 1 ELSE 0 END) / COUNT(cadena_key)` (formato porcentaje) |
| Etiqueta de semana | cualquiera con `semana_inicio` | `CONCAT("Semana del ", FORMAT_DATETIME("%d/%m/%Y", semana_inicio))` |

## 5. Trazabilidad

| Indicador | Tabla publicada | Modelo dbt | Origen |
|---|---|---|---|
| Costo mediano por cadena | `bi_costo_semanal_cadena` | `transform/models/bi/bi_costo_semanal_cadena.sql` | `mart_ahorro_por_cadena` → `mart_canasta_semanal` → `int_canasta_articulo_semanal` → `fct_precio_observado` |
| Ahorro máximo | `bi_ahorro_semanal` | `bi_ahorro_semanal.sql` | `mart_ahorro_por_cadena` |
| Diferencia por artículo | `bi_diferencias_producto_semanal` | `bi_diferencias_producto_semanal.sql` | `mart_precio_producto` (descomposición probada con `assert_descomposicion_ahorro`) |
| Cobertura | `mart_cobertura_datos` | `marts/mart_cobertura_datos.sql` | `fct_precio_observado` |
| Disponibilidad | `bi_disponibilidad_semanal`, `bi_articulos_faltantes` | `bi_disponibilidad_semanal.sql`, `bi_disponibilidad_articulos.sql` (publicada solo con `disponible = false`) | `mart_canasta_semanal`, `int_canasta_articulo_semanal` (consistencia probada con `assert_bi_consistente_con_marts`) |

**Tamaño publicado (D-036).** Para respetar el límite de 500 MB del plan gratuito de Supabase, el detalle de
precio por producto se publica para las últimas `QQP_PG_SEMANAS_DETALLE` semanas (52 por defecto; `0` = todo) y la
disponibilidad por municipio solo con los artículos faltantes. La historia completa de los indicadores está en las
tablas BI y en DuckDB.
| Índice | `bi_indice_canasta` | `bi_indice_canasta.sql` | `mart_canasta_semanal` |

Cada publicación registra en `qqp_meta.publicaciones` el commit, la ejecución de GitHub Actions, la canasta y el
número de filas por tabla. La validación independiente (`reports/validacion_canasta.md`) recalcula en Python el
costo y el ahorro de municipio-semanas deterministas antes de publicar.

## 6. Salvedades que deben aparecer en el dashboard

Colocar en una caja de texto al pie de las páginas 2, 3 y 4:

1. La canasta es de referencia (16 alimentos, presentaciones más comunes), no el gasto real de un hogar.
2. Cada artículo es la mediana de precio de cualquier marca comparable: parte de la diferencia entre cadenas es la
   mezcla de marcas que ofrece cada una.
3. Wal-mart y Bodega Aurrera pertenecen al mismo grupo empresarial.
4. La serie semanal usa una ventana de 14 días: semanas consecutivas comparten observaciones.
5. En la mayoría de las celdas cada cadena está representada por una sola tienda por semana.
6. Solo se incluyen las ciudades que muestrea PROFECO (75 municipios en 30 estados).

## 7. Reproducción

1. Ejecuta el pipeline con publicación (GitHub Actions o `python -m src.cli pipeline` con `.env`).
2. Crea el rol de lectura (1.1) y las fuentes (1.3).
3. Construye las páginas según la sección 3 y los campos de la sección 4.
4. Comparte el informe con acceso de lectura; las credenciales de la fuente quedan en la fuente de datos, no en el
   informe.
