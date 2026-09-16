# Bitácora del orquestador

Registro cronológico de fases, evidencia y aprobaciones. Las cifras detalladas están en
`reports/perfil_datos.md`; aquí se registra qué se hizo, qué se verificó y qué se decidió.

---

## 2026-09-12 · Fase 0 — Viabilidad

### Estado inicial del repositorio

- Solo existían `CLAUDE.md` y `data/raw/` con tres comprimidos: `QQP_2024.rar` (96 MB), `QQP_2025.rar` (85 MB),
  `QQP_2026.zip` (128 MB).
- **No se recibieron diccionario de datos ni metadatos.** El esquema se validó contra los datos
  (`docs/diccionario_validado.md`).
- Herramientas: Python 3.14 (sistema), `uv`, `git`, `bsdtar` de Windows. No hay `make`, `duckdb` ni `dbt`
  instalados globalmente.

### Trabajo realizado

1. Entorno `.venv` con Python 3.12: DuckDB 1.5.5, dbt-core 1.12.4, dbt-duckdb 1.11.0, pytest 9.1.1,
   ruff 0.16.7 (D-001).
2. Extracción verificada de 58 CSV (D-002).
3. Detección física por archivo: codificación, BOM, fin de línea, delimitador, encabezado, formato de fecha
   (D-003).
4. Carga de las 33,581,522 filas como texto en una base de perfilado separada
   (`data/interim/profile/perfil.duckdb`).
5. Perfil de contenido: fechas, nulos, cardinalidades, precio, coordenadas, duplicados, variantes de texto,
   cobertura por catálogo, estado y cadena.
6. Evaluación de viabilidad de la canasta con 20 productos candidatos (`data/mappings/canasta_candidatos_v0.csv`).
7. Código reproducible: `python -m src.ingest.profile` regenera tablas y `reports/perfil_datos.md`.

### Incidente: apagado del equipo

- **Qué pasó:** La consulta global de duplicados (24 hilos, 33.5 M filas, agrupación por 8 columnas de texto)
  apagó el equipo dos veces (15:46 y 16:59). El registro de Windows muestra Kernel-Power 41 sin error de
  detención: corte por protección térmica o de energía, no falta de memoria.
- **Datos afectados:** Ninguno. La base de perfilado se consultaba en solo lectura; los CSV extraídos siguen
  íntegros.
- **Corrección:** Límites de DuckDB configurables (D-004) y consultas por archivo con agrupación por hash
  (D-005). La misma consulta corrió en 17 s para los 58 archivos con ~15% de CPU.

### Rendimiento del perfilado

- La primera corrida completa de `python -m src.ingest.profile` tardó 899 s. La causa fue una agregación ordenada
  (`string_agg ... ORDER BY`) sobre ~600 mil grupos por archivo, de un solo hilo. Se corrigió filtrando primero
  los grupos con más de un catálogo; los resultados se compararon con `assert_frame_equal` y son idénticos.
- Consultas de perfil tras la corrección: **26 s** (con `--reuse-db`).

### Pruebas ejecutadas

| Comando | Resultado |
|---|---|
| `pytest -q` | 10 pruebas pasan (extracción, idempotencia, re-extracción de CSV corrupto, detección de codificación, CRLF partido, lectura UTF-8/Latin-1, cambio de esquema) |
| `ruff check .` (incluye notebook) | Sin errores |
| `ruff format --check .` | Sin cambios pendientes |
| Conteo de carga | 58/58 archivos: filas cargadas = líneas físicas − 1; 0 filas rechazadas |
| Inmutabilidad de `data/raw/` | SHA-256 de los 3 originales igual al manifiesto de extracción |
| `analysis/build_notebook.py` | Notebook ejecutado: 14 celdas de código, 0 errores |
| `dbt debug` / `dbt run` / `dbt test` | No aplica aún: no hay proyecto dbt (Fase 1) |
| `make pipeline` | No aplica aún; además `make` no está instalado (pendiente de resolver en Fase 1) |

### Entregables de la fase

- `reports/perfil_datos.md` (generado), `docs/diccionario_validado.md`, `analysis/00_reconocimiento.ipynb`
- `docs/decisiones.md` (D-001 a D-008), esta bitácora
- `src/ingest/{extract,sniff,csv_source,profile,profile_report}.py`, `src/db.py`, `src/config.py`
- `data/mappings/canasta_candidatos_v0.csv`, `tests/`

### Hallazgos que condicionan el diseño

1. Dos formatos físicos de archivo (mayo 2026 distinto).
2. Variantes de texto: estados con y sin acento desde 2026; `S/m` → `S/M`; mayúsculas de presentación en mayo
   2026; `Papeler?as`/`Jugueter?as` con caracteres perdidos en el archivo de origen `05-2026_Q2.csv`.
3. La misma observación aparece en varios catálogos (D-006).
4. Precio extremo evidente (medicamento a $3,041,791).
5. Las tiendas se visitan ~2 días por quincena: la semana suelta es un grano demasiado fino por tienda.
6. **Una canasta de SKU idénticos (marca fija) no es comparable entre las 4 cadenas grandes**: no existe una
   marca de frijol ni de arroz presente en las cuatro. Una canasta genérica por unidad base sí es viable.

### Aprobación del alcance

- [x] 2026-09-12 · Aprobado por el responsable del proyecto:
  - Canasta genérica por unidad base con mediana (D-009)
  - Serie semanal con ventana móvil de 14 días (D-010)
  - Cadenas de referencia: Wal-mart, Bodega Aurrera, Hipermercado Soriana, Chedraui (D-011)
  - Geografía municipio, agregable a estado y nacional (D-012)

**Fase 0 cerrada.** Siguiente: Fase 1 — MVP local (ingesta a `qqp.duckdb`, calidad, normalización, dbt, mart
de canasta, pruebas).

### Pendientes que pasan a Fase 1

- `make` no está instalado en Windows: el `Makefile` servirá en Linux/GitHub Actions; en local se ofrecerá un
  equivalente en Python con los mismos comandos.
- Confirmar el significado de `Pacic` con documentación oficial de PROFECO.

---

## 2026-09-12 · Fase 1 — MVP local

### Trabajo realizado

| Componente | Entregable | Evidencia |
|---|---|---|
| Orquestación | `src/cli.py`, `Makefile` (D-014) | `python -m src.cli pipeline` de principio a fin, código 0 |
| Ingesta | `src/ingest/load.py` → `raw.qqp_precios`, `raw.archivos`, `raw.cargas` | 58 archivos, 33,581,522 filas; segunda ejecución: 58 omitidos, 0 filas nuevas |
| Muestra | `src/ingest/sample.py` → `data/sample/csv/` (D-013) | 15,278 filas reales, 4.9 MB, 5 formatos físicos originales |
| Calidad | `src/quality/checks.py`, `docs/reglas_calidad.md`, `reports/calidad_datos.md` | 10 reglas raw + 6 marts, todas cumplen |
| Normalización | `src/normalize/`, `data/mappings/*.csv`, `docs/normalizacion.md` | 97.7% de filas en catálogos de canasta comparables; 43 correcciones de texto; 2,315 casos en cola |
| Modelado dbt | `transform/` (staging, intermediate, 5 dimensiones, hechos, mart) | 13 modelos, 3 seeds, 110 pruebas |
| Documentación | `docs/contrato_datos.md`, `docs/limitaciones.md`, D-013 a D-021 | Tipos del contrato verificados contra `information_schema` |

### Tiempos con datos completos (4 hilos, 8 GB)

| Paso | Primera carga | Reejecución |
|---|---|---|
| inspect | 18 s | 19 s |
| ingest | ~3 min | 1 s (sin cambios) |
| quality (raw) | 5 s | 5 s |
| normalize | 12 s | 2 s |
| dbt seed + run | 140 s (hechos 70 s) | 124 s (hechos 61 s con medianas exactas) |
| dbt test | 8 s | 9 s |
| quality (marts) | 1 s | 1 s |
| **Pipeline completo** | — | **162 s** |

### Incidentes y correcciones

1. **Pruebas genéricas sin `column_name`** → firma de macros corregida.
2. **`DATE + BIGINT`** en la ventana móvil → conversión a `INTEGER`.
3. **Atípicos sobredetectados (1.8% en la muestra)**: la MAD casi nula de precios estables marcaba precios normales →
   magnitud mínima de 3× (D-018). Datos completos: 0.036%.
4. **Conexión DuckDB con otra configuración** al correr calidad tras dbt en el mismo proceso → dbt en subproceso
   (D-015).
5. **`Cannot switch temporary directory`** en la tabla de hechos → límites en `config_options` (D-015).
6. **`HUGEINT`** en sumas (no publicable en PostgreSQL) → conversión a `BIGINT`, detectado al verificar el contrato.
7. **Resultados no deterministas** entre ejecuciones idénticas por `approx_quantile` → medianas exactas (D-021);
   dos ejecuciones consecutivas idénticas (11,862 atípicos, 50.7494% de canastas completas).

Ninguno de los incidentes dañó datos: la ingesta es transaccional y los modelos se reconstruyen completos.

### Validación manual de resultados

- El precio de $3,041,791 (Prevefem Complex) quedó marcado Q-ATIP-01 contra una mediana de $345.11.
- Medianas de precio unitario plausibles: atún en agua ~$160/kg, huevo ~$2.66/pieza, papel higiénico ~$5/rollo.
- Estados con y sin acento unificados (`Querétaro`, `Ciudad de México`); 2,452 establecimientos canónicos frente a
  4,162 llaves sin normalizar.
- Decisión manual de detergente aplicada (`manual_confirmado`, comparable, asignado a `DETERGENTE_POLVO`).
- Costo de canasta completa (mediana entre municipios, última semana): Hipermercado Soriana $725.52, Chedraui
  $755.04, Bodega Aurrera $780.89, Wal-mart $821.74. **No es aún una comparación válida entre cadenas**: cada una
  se mide en un conjunto distinto de municipios; la comparación pareada es trabajo de la Fase 2.

### Pruebas ejecutadas

| Comando | Resultado |
|---|---|
| `pytest -q` | 54 pruebas pasan |
| `ruff check .` / `ruff format --check .` | Sin errores / sin cambios pendientes |
| `dbt debug` | All checks passed (dbt 1.12.4, duckdb 1.11.0, Python 3.12.13) |
| `dbt run` / `dbt test` (datos completos) | 13/13 modelos, 110/110 pruebas |
| `python -m src.cli pipeline` (datos completos) | Código 0 en 162 s |
| `python -m src.cli --muestra pipeline` | Código 0 en 15 s |
| `make pipeline` | No ejecutable en este equipo (sin `make`); el `Makefile` delega en el comando anterior |

### Riesgos y pendientes para la Fase 2

- Canasta completa en 50.7% de celdas de referencia (Wal-mart 64%, Soriana 54%, Bodega Aurrera 47%, Chedraui 28%).
  Artículos que más la rompen: carne molida especial (39% en Chedraui), pierna de pollo, harina de maíz y
  limpieza en Bodega Aurrera.
- Validar si ofertas agresivas marcadas como atípicas (p. ej. papa a $10/kg) deben excluirse.
- Validar las dos decisiones manuales propuestas por el asistente (D-020).
- Comparación pareada de cadenas en el mismo municipio y semana; marts de ahorro, precio por producto y cobertura.

**Fase 1 lista para aprobación.** Aprobada por el responsable del proyecto el 2026-09-12; commit inicial `48838ea`.

---

## 2026-09-12 · Fase 2 — Análisis

### Pendientes de Fase 1 resueltos con datos (D-025)

| Pendiente | Evidencia | Resultado |
|---|---|---|
| Detergente `Bolsa 3.564 Gr.` | $160 por bolsa = $44.89/kg; bolsa de 1 kg = $44.90/kg; bolsa de 5 kg = $39.20/kg | Se confirma 3.564 kg |
| ¿Atípicos que son ofertas? | 119 observaciones marcadas en artículos de canasta; 4 en cadenas de referencia; sin concentración en martes | Se mantienen las reglas |

### Definición de la canasta (D-022, aprobada)

- Evaluación de 17 definiciones de artículo y 7 composiciones (`reports/seleccion_canasta.md`,
  `python -m src.cli seleccion-canasta`).
- Aprobada la **v1 de 16 alimentos**: pollo entero en lugar de pierna, milanesa de res en lugar de molida especial,
  sin harina de maíz ni limpieza. Completitud de celdas de referencia: 50.7% → 81.0%; municipio-semanas comparables:
  50.6% → 85.2%.

### Construido

| Componente | Entregable |
|---|---|
| Ahorro | `marts.mart_ahorro_por_cadena` (comparación pareada, D-023) |
| Diferencias por producto | `marts.mart_precio_producto` (descomposición del ahorro por artículo) |
| Cobertura | `marts.mart_cobertura_datos` |
| Validación manual | `src/analysis/validacion.py` → `reports/validacion_canasta.md`, paso `validate` del pipeline (D-024) |
| Respuestas de negocio | `src/analysis/resultados.py` → `reports/resultados_canasta.md`, paso `resultados` |
| Métricas | `docs/catalogo_metricas.md` |
| Calidad | M-07 (municipio-semanas comparables), 20 pruebas dbt nuevas |

### Validación manual de resultados

1. **Recálculo independiente en Python**: 6 municipio-semanas, 24 comparaciones cadena-celda: 24 coinciden al centavo
   en costo y ahorro.
2. **Descomposición**: la suma por artículo reproduce el ahorro de cada cadena (prueba dbt).
3. **Revisión crítica de los primeros resultados**, que llevó a tres correcciones:
   - Índice encadenado con deriva de ~3 puntos → índice directo de panel fijo (D-026).
   - Ranking de municipios sesgado por la mezcla de cadenas → nivel de precios que compara cada cadena consigo
     misma, con al menos 2 cadenas (D-027).
   - Estado mostrado sin acento en un municipio sin datos recientes → nombre elegido a nivel estado.
4. **Municipios sin comparación**: se verificó que no es un error (p. ej. Toluca tiene 52 tiendas pero solo 1 de
   cadena de referencia).
5. **Variantes de nombre**: búsqueda por distancia de edición; dos variantes corregidas (D-028).

### Resultados principales (datos completos, canasta v1, 2024-01 a 2026-05)

- 5,230 municipio-semanas comparables en 51 municipios.
- Ahorro máximo mediano al pasar de la cadena más cara a la más barata del mismo municipio y semana: **$49.52
  (6.8%)** por canasta; con las 4 cadenas presentes, $64.50 (8.9%).
- Frecuencia como cadena más barata en sus celdas comparables: Chedraui 69.8%, Bodega Aurrera 35.0%, Hipermercado
  Soriana 32.3%, Wal-mart 23.9%.
- Artículos que más explican las diferencias: milanesa de res (21%), limón (17%), jitomate (13%), cebolla (12%) y
  papa (10%).
- Índice directo de la canasta: 100 → 102.1 en mayo de 2026, con un mínimo de 95.6 (mayo 2024) y un máximo de 104.0
  (abril 2026).
- Nivel de precios entre ciudades con ≥2 cadenas: 96.9 a 102.1; elegir cadena pesa más que la ciudad.

### Pruebas ejecutadas

| Comando | Resultado |
|---|---|
| `python -m src.cli pipeline --desde normalize` (datos completos) | Código 0 en 143 s |
| `dbt run` / `dbt test` | 16/16 modelos, 130/130 pruebas |
| Reglas de calidad | 10 raw + 7 marts cumplen (M-04 81.0%, M-07 85.2%) |
| `validate` | 24/24 coincidencias |
| `pytest -q` | 55 pruebas pasan |
| `ruff check .` | Sin errores |

### Riesgos y pendientes

- Decisiones manuales propuestas por el asistente pendientes de validación humana (D-025, D-028).
- Representatividad: mediana de 1 tienda y 1 día por celda (L-17); la canasta genérica mezcla marcas (L-18).
- Siguiente fase: publicación en Supabase, vistas para Looker Studio, GitHub Actions y alertas.

**Fase 2 lista para aprobación.** Aprobada; commit `59e5c83`.

---

## 2026-09-12 · Fase 3 — Publicación y automatización

### Fuentes externas verificadas

| Qué | Cómo se verificó | Resultado |
|---|---|---|
| Enlaces oficiales de descarga | Portal https://datos.profeco.gob.mx/datos_abiertos/qqp.php + petición HEAD (sin descargar) | Devuelven `QQP_2024.rar`, `QQP_2025.rar`, `QQP_2026.zip`; sin `ETag` ni `Last-Modified` |
| Diccionario oficial | https://datos.profeco.gob.mx/diccionarioDatosQQP.php | Mismas 15 columnas; precio = "venta al público"; no documenta catálogos, moneda ni IVA |
| Conexión a Supabase desde CI | Documentación oficial de Supabase | Conexión directa IPv6; GitHub Actions es solo IPv4 → pooler en modo sesión (D-031) |
| Actualizaciones retroactivas de PROFECO | Página de datos.gob.mx | No verificado (HTTP 403); no se asume |

### Construido

| Componente | Entregable |
|---|---|
| Descarga | `src/ingest/download.py`, `data/fuentes_profeco.csv` (D-032) |
| Vistas BI | `transform/models/bi/` (5 tablas), seed `estados_iso`, `dim_geografia.estado_iso` (D-030) |
| Publicación | `src/publish/postgres.py`: carga a esquema temporal, verificación de filas, intercambio atómico, bitácora `qqp_meta.publicaciones` (D-029) |
| Automatización | `.github/workflows/pipeline-semanal.yml` (D-033) |
| Alertas | `src/alertas.py`, alerta automática ante cualquier falla en `src/cli.py`, regla M-08 (D-034) |
| Configuración | `.env.example` (solo nombres), carga opcional de `.env` local |
| Dashboard | `docs/dashboard_looker_studio.md` (conexión, rol de lectura, 11 fuentes, 6 páginas, campos calculados, trazabilidad) |

### Incidentes y correcciones

1. **dbt leía YAML con cp1252 en Windows** (falló con "Índice") → dbt en modo UTF-8 (D-035).
2. **Colisión de `id_publicacion`** con resolución de segundos, detectada por la prueba de integración (dos
   publicaciones en el mismo segundo) → microsegundos + sufijo aleatorio.
3. **`commit` como nombre de columna** (palabra reservada de PostgreSQL) → `commit_git`, `ejecucion_ci`.
4. **Prioridad de herramienta RAR**: `7z` de Ubuntu puede no traer el códec RAR → `bsdtar` primero y
   `libarchive-tools` en el workflow.

### Evidencia

| Prueba | Resultado |
|---|---|
| `pytest -q` | 72 pruebas pasan, incluidas 2 de integración contra PostgreSQL 16 real (embebido con `pgserver`) |
| Publicación atómica | Reemplazo sin duplicados ni esquemas residuales; fallo simulado a mitad de carga conserva la versión anterior y registra `fallida` |
| Pipeline completo + publicación en PostgreSQL local | `pipeline --desde dbt-run`: 21 modelos, 148 pruebas dbt, 24/24 validaciones, 11 tablas y 782,970 filas publicadas en 6 s; código 0 en 154 s |
| Fidelidad de la publicación | Sumas de control idénticas entre DuckDB y PostgreSQL en 6 tablas; tipos `date`, `double precision`, `bigint`, `boolean`, `text` |
| Pipeline de la muestra | Código 0 en 17 s |
| Workflow | YAML válido; 2 jobs, 27 pasos; los 13 pasos del CLI que invoca existen |
| `ruff check .` / `ruff format --check .` | Sin errores |

### No verificado todavía

- El workflow no se ha ejecutado en GitHub (no hay remoto) y no se ha publicado contra Supabase (no hay credenciales).
- La descarga real de los ~300 MB desde PROFECO no se ejecutó en local (se probó con respuestas simuladas y HEAD).
- El dashboard de Looker Studio está especificado, no construido.

**Fase 3 lista para aprobación.**

## 2026-09-13 · Fase 3 — Primeras ejecuciones en GitHub Actions

### Ejecuciones

| Ejecución | Modo | Resultado | Causa |
|---|---|---|---|
| 34769006755 | muestra | Falla en publicación | `SUPABASE_DB_HOST` no resolvía en DNS. Se agregó validación previa de la conexión con mensajes que no muestran secretos (PR #2). |
| 34769025081 | completo | Falla en `inspect` | Descarga y extracción correctas; `06-2026_Q1/Q2` con 18 columnas (D-037). |
| 34769738774 | muestra | Falla en publicación | Mismo host inválido, antes de corregir los secretos. |
| 34771164262 | muestra (rama del PR #2) | **Éxito** | Publicación `exitosa` en Supabase en 3 s: 13 tablas en `qqp`. `looker_lector` lee `qqp`; `anon` y `authenticated` sin acceso a `qqp` ni `qqp_meta`. Sin alertas del asesor de seguridad. |
| 34772772277 | completo (rama del PR #3, D-037 y D-038) | Falla en `dbt test` | Inspección, ingesta (160 s), calidad, normalización y `dbt run` (192 s) correctos. 2 de 151 pruebas fallan: catálogos de julio con otra grafía (D-039). No se publicó nada. |
| 34773616518 | completo (rama del PR #3, con D-039) | **Éxito** | Ver "Primera publicación completa". |

### Primera publicación completa

| Paso | Resultado |
|---|---|
| Descarga | 3 archivos oficiales (376.8 MB) en 12 s |
| Inspección | 62 archivos válidos; aviso de columnas adicionales en `06-2026_Q1/Q2` (80 s con extracción) |
| Ingesta | 62 archivos en 125 s |
| Normalización | 898 productos, 6,588 presentaciones, 1,717 correcciones de texto, 97.7% de filas en alcance comparables (11 s) |
| dbt | 23 modelos en 163 s; 153 pruebas pasan en 10 s |
| Calidad y validación | Solo M-08 en alerta (44 días desde el último dato, 2026-07-31); validación independiente 24/24 |
| Publicación | `exitosa` en 12 s: 12 tablas, 317,745 filas; `metadatos` con 62 archivos, modo `completo`, última semana 2026-07-27 |
| Supabase | Base de 96 MB (esquema `qqp` 91 MB) de 500 MB del plan gratuito; sin esquemas residuales; `dim_geografia` con 75 municipios, los mismos que antes de junio; `looker_lector` lee las 13 tablas; `anon` y `authenticated` sin acceso; asesor de seguridad sin alertas |
| Continuidad | Ahorro máximo mediano semanal de 30.78 a 45.34 MXN entre 2026-05-11 y 2026-07-27, sin saltos en el cambio de formato de junio ni en el de julio |

La corrida fallida anterior abrió el issue #1 de alerta, que ya puede cerrarse.

### Cambio de esquema de PROFECO (junio 2026)

Con autorización del responsable se descargó la versión vigente de `QQP_2026.zip` a `data/interim/descargas/`
(`data/raw/` intacto) y se revisó antes de cambiar código (diccionario validado §6):

- Enero a mayo idénticos; nuevos 2026-06 y 2026-07 (2.66 M filas, hasta el 2026-07-31).
- Junio: 3 columnas no documentadas al final (D-037) y caracteres perdidos en un tercio de las filas, incluido el
  municipio (D-038). Julio: formato de 2024, sin anomalías.
- Hallazgo que habría pasado inadvertido: sin D-038, 21 municipios se habrían duplicado en junio y la serie semanal
  se habría partido sin que fallara ninguna prueba.
- Julio renombró 4 catálogos con acentos o mayúsculas (D-039); la prueba de relación con el seed lo detectó en CI.
  Se revisaron las demás columnas llave de junio y julio contra la historia: fuera del catálogo y los `?`, solo hay
  valores realmente nuevos (3 tiendas de uniformes y zapatos, 1 producto escolar; 175 filas).

### Evidencia

| Prueba | Resultado |
|---|---|
| Carga real de `05-2026_Q2`, `06-2026_Q1`, `06-2026_Q2`, `07-2026_Q2` en una base temporal | Filas = líneas − 1 en los 4; 0 fechas y 0 precios inválidos; columnas adicionales pobladas solo en junio |
| Corrección por candidato único sobre valores reales | 21 de 21 municipios y 75 de 75 productos de junio corregidos; quedan 6 valores menores (1,733 filas) para revisión |
| `pytest -q` | 83 pruebas pasan (nuevas: encabezados aceptados y rechazados, migración de una base existente, aviso de `inspect`, corrección de geografía, alcance de catálogos por llave, filtro de la validación) |
| Pipeline de la muestra en local (sin publicar) | 22 modelos, 151 pruebas dbt, validación independiente 8/8; M-08 en alerta como se esperaba (antes de D-039) |
| Normalización, dbt y validación con datos reales `05-2026_Q2` a `07-2026_Q2` (3.19 M filas, base temporal) | 23 modelos, 153 pruebas dbt, 24/24 validaciones en 6 municipio-semanas de junio y julio (incluida Coyoacán, que llegó como `Coyoac?n`); 72 municipios, ninguno con `?`; 128–139 celdas completas por semana |
| `ruff check .` / `ruff format --check .` | Sin errores |

### Pendientes

- Revisar los valores con `?` sin candidato único en la cola de revisión (27 al 2026-09-16, ninguno en la geografía).

## 2026-09-16 · Fase 4 — Portafolio

### Datos actualizados en local

El responsable sustituyó `data/raw/QQP_2026.zip` por la versión vigente (misma que descargó CI). El pipeline
completo corrió en local en **5 min** (inspección 30 s, ingesta 21 s con 4 archivos nuevos y 58 sin cambios,
calidad 19 s, normalización 5 s, `dbt run` 192 s, `dbt test` 13 s, calidad del modelo 2 s, validación 6 s):
153 pruebas dbt, validación independiente 24/24, solo M-08 en alerta (47 días desde el último dato).
`data/mappings/` y `reports/` versionados quedaron regenerados con datos al 2026-07-27.

### Construido

| Entregable | Qué contiene |
|---|---|
| `README.md` | Qué resuelve, arquitectura en una imagen, instalación y ejecución desde cero, estructura, índice de documentación, alcance y límites |
| `docs/arquitectura.md` | Flujo completo, componentes, modelo dimensional, modos de ejecución, rendimiento, compuertas de calidad, publicación atómica y seguridad |
| `reports/memo_ejecutivo.md` | Respuesta ejecutiva a las cinco preguntas con cifras al 2026-07-27, salvedades y recomendaciones |
| `docs/caso_estudio.md` | Cómo se construyó: cinco problemas reales, la prueba de fuego del cambio de esquema y qué haría después |

### Resultados con datos al 2026-07-27

- 35.6 M observaciones, 135 semanas, 5,630 municipio-semanas comparables en 51 municipios.
- Ahorro máximo mediano $48.08 (6.7%); $64.03 (8.8%) donde están las 4 cadenas.
- Chedraui es la más barata en 70.7% de las celdas; cambiarse desde Wal-mart equivale a $1,665 al año.
- Cinco frescos explican el 73% de la diferencia total (milanesa, limón, jitomate, cebolla, papa).
- El índice bajó de 104.0 en abril de 2026 a 96.8 en julio: el nivel más bajo desde mayo de 2024.

### Pendientes

- Capturas del dashboard: requieren construir el tablero en Looker Studio con la especificación ya escrita.
- `reports/perfil_datos.md` sigue siendo el perfilado de la Fase 0 (58 archivos, hasta 2026-05-29); el esquema y las
  anomalías de junio y julio están en `docs/diccionario_validado.md` §6. Regenerarlo implica releer 10.6 GB de CSV.
- Integrar los PR #2 y #3 en `main` para que la ejecución programada deje de fallar (L-21).
