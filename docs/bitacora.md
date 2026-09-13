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

**Fase 1 lista para aprobación.**
