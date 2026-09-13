# Registro de decisiones

Formato: contexto → decisión → consecuencias. Las decisiones se numeran y no se
borran; si una cambia, se agrega una nueva que la reemplaza.

---

## D-001 · Python 3.12 en un entorno virtual gestionado con `uv`

- **Fecha:** 2026-09-12 · **Fase:** 0
- **Contexto:** El equipo tiene Python 3.14. dbt-core declara compatibilidad hasta versiones anteriores y el
  ecosistema de adaptadores suele ir atrasado.
- **Decisión:** Crear `.venv` con Python 3.12 (`uv venv --python 3.12`). `pyproject.toml` restringe a
  `>=3.11,<3.14`.
- **Consecuencias:** Mismo intérprete en local y en GitHub Actions (`actions/setup-python` 3.12).

## D-002 · Los originales comprimidos se extraen a `data/interim/`, nunca se modifican

- **Contexto:** PROFECO entregó `QQP_2024.rar`, `QQP_2025.rar` y `QQP_2026.zip` (58 CSV, 9.85 GB
  descomprimidos). `data/raw/` es inmutable por contrato.
- **Decisión:** `src/ingest/extract.py` lista cada archivo con `rarfile`/`zipfile`, extrae con la herramienta
  disponible (`unrar`, `7z` o `bsdtar`) a `data/interim/csv/<archivo>/`, verifica tamaño y CRC32 y registra el
  SHA-256 de cada original en `data/interim/manifest_extraccion.json`.
- **Alternativas descartadas:** leer directamente del comprimido (DuckDB no lee RAR); descomprimir dentro de
  `data/raw/` (viola la inmutabilidad).
- **Consecuencias:** `data/interim/` no se versiona; es reproducible con `make extract`. Se añade un directorio
  que no estaba en la estructura propuesta, justificado aquí.

## D-003 · Todos los CSV se leen como texto con parámetros explícitos por archivo

- **Contexto:** Los archivos no son homogéneos: 56 están en UTF-8 con BOM y fecha `yyyy/mm/dd`; los dos de mayo
  de 2026 están en Latin-1 sin BOM y con fecha `dd/mm/yyyy`. No se recibió diccionario de datos.
- **Decisión:** `src/ingest/sniff.py` detecta codificación, BOM, delimitador y formato de fecha de cada archivo.
  `src/ingest/csv_source.py` construye un `read_csv` sin autodetección, con las 15 columnas como `VARCHAR`,
  y falla si el encabezado difiere del esquema esperado. La conversión de tipos se hace en staging.
- **Consecuencias:** Ningún valor se pierde por una conversión fallida en la carga; las fallas se miden.
  Un cambio de esquema detiene la ingesta en lugar de cargar columnas desplazadas.

## D-004 · Límites de recursos de DuckDB configurables (4 hilos, 8 GB)

- **Contexto:** Una consulta de duplicados con 24 hilos sobre 33.5 M de filas mantuvo el CPU al 100% durante
  minutos y el equipo se apagó dos veces (evento Kernel-Power 41, sin pantalla azul): protección térmica.
- **Decisión:** Toda conexión se abre con `src/db.py::connect`, que fija `threads`, `memory_limit`,
  `temp_directory` y `preserve_insertion_order=false`. Valores por defecto: 4 hilos y 8 GB, sobreescribibles con
  `QQP_DUCKDB_THREADS` y `QQP_DUCKDB_MEMORY_LIMIT`.
- **Consecuencias:** Coinciden con un runner estándar de GitHub Actions (4 vCPU, 16 GB). Las consultas tardan
  algo más, pero la carga de CPU medida bajó a ~15% en consultas por archivo.

## D-005 · Consultas pesadas archivo por archivo y agrupación por hash

- **Contexto:** Agrupar 33.5 M de filas por 8 columnas de texto es costoso en memoria y CPU.
- **Decisión:** Los cálculos de duplicados se ejecutan por archivo. Es equivalente al cálculo global porque los
  rangos de fecha de los archivos no se traslapan (verificado en el perfil) y el grano incluye la fecha. Las
  llaves compuestas se agrupan por `hash(...)` de 64 bits.
- **Consecuencias:** 58 consultas de ~1 s. La probabilidad de colisión de hash con ~700 mil filas por archivo es
  del orden de 10⁻⁸; aceptable para perfilado. En los modelos de producción las llaves se validan con columnas
  reales, no con hash.

## D-006 · El catálogo no forma parte del grano de la observación

- **Contexto:** De los grupos duplicados en producto + presentación + marca + tienda + fecha, 614,653 son la
  misma observación publicada en dos catálogos (`Basicos + Pacic`, `Frutas y Legumbres + Pacic`,
  `Electrodomesticos + Juguetes`, entre otros); solo 20,816 tienen precios en conflicto dentro de un catálogo.
- **Decisión (preliminar, se valida en Fase 1):** La tabla de hechos tendrá una fila por observación de precio;
  la pertenencia a catálogos se modela como atributo o tabla puente, sin multiplicar observaciones.
- **Consecuencias:** Evita contar dos veces un mismo precio en medianas y coberturas.

## D-007 · `ruff format` controla el largo de línea; E501 desactivado

- **Contexto:** El SQL embebido en Python excede la longitud de línea y partirlo reduce legibilidad.
- **Decisión:** Se usa `ruff format` (línea de 110) para el código y se ignora `E501` en `ruff check`.

## D-008 · Sin subagentes en paralelo para cómputo pesado

- **Contexto:** CLAUDE.md propone agentes especializados en paralelo, pero el equipo local tiene un límite
  térmico demostrado.
- **Decisión:** Las tareas que consultan el dataset completo se ejecutan en serie. El paralelismo se reserva para
  trabajo sin cómputo pesado (documentación, diseño de dashboard, estructura de pruebas).

## D-009 · Canasta genérica con precio por unidad base (aprobada)

- **Fecha:** 2026-09-12 · **Fase:** 0 → 1 · **Aprobó:** responsable del proyecto
- **Contexto:** Una canasta de SKU idénticos no es comparable entre cadenas: la mejor marca de frijol está en el
  3.3% de las celdas municipio×quincena de la cadena con menor presencia y la de arroz en el 9.4%. La canasta
  de 20 productos con marca fija se completa en 0–20% de las celdas; la genérica, en 70–80%.
- **Decisión:** Cada artículo de la canasta es un producto genérico con variante definida (p. ej. frijol negro,
  leche entera) y se valora con la **mediana del precio por unidad base** (kg, L o pieza) de las observaciones
  normalizadas en la celda. La lista de 20 candidatos (`data/mappings/canasta_candidatos_v0.csv`) es el punto de
  partida; el número final se fija después de medir la completitud por artículo con presentaciones normalizadas.
- **Consecuencias:** La normalización de presentaciones es crítica. La mezcla de marcas difiere entre cadenas;
  se documentará como limitación y se publicará el número de observaciones por celda.

## D-010 · Serie semanal con ventana móvil de 14 días (aprobada)

- **Contexto:** Las tiendas se visitan ~2 días por quincena. La canasta genérica por municipio×semana se completa
  en 52–65%; con ventana de 14 días, en 68–78%.
- **Decisión:** El costo de la semana *S* usa las observaciones con fecha en *[inicio(S) − 7 días, fin(S)]*.
  Cada métrica publica el número de observaciones y los días efectivos de la ventana.
- **Consecuencias:** Semanas consecutivas comparten datos; las variaciones semana a semana se suavizan y no deben
  interpretarse como cambios independientes. Se documentará en `docs/limitaciones.md` y en el dashboard.

## D-011 · Cadenas de referencia: Wal-mart, Bodega Aurrera, Hipermercado Soriana, Chedraui (aprobada)

- **Contexto:** Son las únicas cadenas con 21 o más estados y las 126 semanas en el catálogo Básicos.
- **Decisión:** La comparación inicial de canastas se limita a estas cuatro. Las demás cadenas se ingieren y
  modelan igual, para ampliar el alcance sin rehacer el pipeline.
- **Consecuencias:** Wal-mart y Bodega Aurrera pertenecen al mismo grupo; el ahorro entre ellas se reporta como
  diferencia de formato, no de competencia.

## D-012 · Geografía a nivel municipio, agregable a estado y nacional (aprobada)

- **Contexto:** 75 municipios en 30 estados; en la mayoría de los estados se muestrea solo la capital. Sin datos
  de Colima ni Nayarit.
- **Decisión:** El grano geográfico es estado + municipio normalizados. Estado y nacional son agregaciones en los
  marts, calculadas a partir de canastas completas por municipio.
- **Consecuencias:** Los indicadores estatales describen las ciudades muestreadas, no la entidad completa.

---

## D-013 · Muestra real, pequeña y versionada con el formato físico original

- **Fecha:** 2026-09-12 · **Fase:** 1
- **Contexto:** Los datos completos (300 MB comprimidos) no se versionan y GitHub Actions necesita datos para
  probar. Una muestra sintética no ejercitaría las rarezas reales (Latin-1, fechas `dd/mm/yyyy`, `?`, acentos).
- **Decisión:** `src/ingest/sample.py` extrae filas reales con criterios deterministas (5 quincenas, 2 municipios
  con las 4 cadenas y cambio de acentos, productos de canasta + 3% por hash) y reescribe cada archivo en su
  codificación, BOM, CRLF y formato de fecha originales. 15,278 filas, 4.9 MB en `data/sample/csv/`.
- **Consecuencias:** `python -m src.cli --muestra pipeline` corre en ~15 s sin `data/raw`. El hash de DuckDB no
  garantiza estabilidad entre versiones: regenerar la muestra con otra versión puede cambiar filas; por eso la
  muestra se versiona en lugar de regenerarse en CI. Los mapeos de la muestra se escriben en
  `data/processed/muestra/` para no sobrescribir los versionados.

## D-014 · Orquestación con `python -m src.cli` y `Makefile` delgado

- **Contexto:** `make` no existe en el equipo Windows; CLAUDE.md pide `make pipeline`.
- **Decisión:** Toda la lógica de pasos vive en `src/cli.py`. El `Makefile` solo delega (`make pipeline` →
  `python -m src.cli pipeline`). `--desde <paso>` reanuda un pipeline interrumpido.
- **Consecuencias:** Mismo comportamiento en Windows, Linux y CI; sin lógica duplicada.

## D-015 · dbt en subproceso y límites de DuckDB como `config_options`

- **Contexto:** (1) dbt dentro del mismo proceso dejaba abierta una conexión a DuckDB y el paso de calidad no podía
  abrir la base con otra configuración. (2) Con `settings`, dbt-duckdb repite `SET temp_directory` en cada
  conexión y DuckDB falla tras haber usado el directorio temporal.
- **Decisión:** `src/cli.py` ejecuta dbt como subproceso; `profiles.yml` pasa hilos, memoria y directorio temporal en
  `config_options`, aplicados una sola vez al abrir la base.
- **Consecuencias:** Memoria de dbt liberada al terminar cada comando; límites de D-004 garantizados también en dbt.

## D-016 · Consolidación por enteros locales y textos recuperados después

- **Contexto:** Agrupar 33.5 M de filas por textos largos fue lo que sobrecalentó el equipo en la Fase 0.
- **Decisión:** `int_observaciones` agrupa por enteros locales a la ejecución (`producto_num`, `establecimiento_num`,
  `archivo_num`) más fecha y precio; los textos originales, identificadores md5 y datos de carga se recuperan con
  uniones a tablas pequeñas. `id_carga` y hora de carga se obtienen de `raw.archivos` (dependencia funcional).
- **Consecuencias:** El modelo más pesado tarda ~37 s y la tabla de hechos ~70 s con 4 hilos. Los enteros locales no
  se publican porque cambian entre ejecuciones.

## D-017 · Pertenencia a catálogos como máscara de bits

- **Contexto:** D-006 (catálogo fuera del grano). Guardar la lista de catálogos por observación costaba memoria.
- **Decisión:** Seed `catalogos` asigna un bit por catálogo; la observación guarda `catalogos_mask = bit_or(...)`.
  `dim_producto.catalogos` lo traduce a texto.
- **Consecuencias:** Un catálogo nuevo en los datos hace fallar la prueba de relación en la fuente, en lugar de
  perderse silenciosamente. Desde D-039 la relación se hace por llave canónica en `int_catalogos`.

## D-018 · Atípicos con magnitud mínima

- **Contexto:** En la muestra, la regla MAD sola marcó 1.8% de observaciones, incluyendo leche a 0.95× la mediana:
  en productos de precio estable la MAD es casi cero.
- **Decisión:** Q-ATIP-02 exige además que el precio esté a más de 3× o menos de 1/3 de la mediana; Q-ATIP-01 marca
  diferencias de 10×. Parámetros en `transform/dbt_project.yml`.
- **Consecuencias:** 0.036% de observaciones marcadas en datos completos (11,862 de 32,985,030); el error de captura
  de $3,041,791 queda marcado. Pendiente Fase 2: verificar si ofertas agresivas (p. ej. papa a $10/kg contra mediana
  $34.90) deben seguir marcándose.

## D-019 · Canasta v0: reglas por expresión regular y cantidad de referencia modal

- **Contexto:** D-009 aprobó una canasta genérica por unidad base; hacía falta una definición operable y auditable.
- **Decisión:** `transform/seeds/canasta_articulos.csv` define 20 artículos con `producto_key`, unidad base, regex de
  inclusión/exclusión sobre la presentación normalizada y `cantidad_referencia` igual a la presentación modal
  observada (1 kg, 1 l, 18 huevos, 4 rollos, 400 g de jabón, 200 g de pasta, 140 g de atún).
- **Consecuencias:** El costo de canasta es un índice de referencia, no el gasto real de un hogar. En datos completos
  la canasta está completa en 50.7% de las celdas de referencia; los artículos que más la rompen son carne molida
  especial, pierna de pollo, harina de maíz y artículos de limpieza en Bodega Aurrera. La selección final se revisa
  en la Fase 2.

## D-020 · Decisiones manuales propuestas por el asistente se marcan como tales

- **Contexto:** Dos presentaciones de detergente (`Bolsa 3.564 Gr.`) quedaron en revisión por separador ambiguo.
- **Decisión:** Se registraron en `data/mappings/manual/presentaciones_manual.csv` como `confirmar` (3.564 kg) con
  `decidido_por = propuesta del asistente (Claude), validar en Fase 2`.
- **Consecuencias:** El flujo manual queda demostrado sin presentar una propuesta automática como validación humana.

## D-022 · Canasta v1: 16 alimentos (aprobada)

- **Fecha:** 2026-09-12 · **Fase:** 2 · **Aprobó:** responsable del proyecto
- **Contexto:** Con v0 solo 50.7% de las celdas de referencia tenían la canasta completa (Chedraui 28%). Se
  evaluaron definiciones alternativas por cobertura y homogeneidad de precio entre cadenas, y composiciones por
  completitud y por municipio-semanas donde se pueden comparar al menos dos cadenas (evidencia reproducible en
  `reports/seleccion_canasta.md`). Presentado al aprobar:

  | Composición | Celdas completas | Municipio-semanas comparables |
  |---|---|---|
  | v0 (20) | 50.7% | 50.6% |
  | 19 con limpieza | 72.7% | 77.1% |
  | **16 alimentos con res (v1)** | **81.0%** | **85.2%** |
  | 15 sin res | 89.7% | 90.4% |

- **Decisión:**
  - Pierna de pollo → **pollo entero** (cobertura ≥96.9% en las 4 cadenas; medianas $44–49/kg). Se descartó
    "pierna o muslo" por mezclar calidades (medianas $60–89/kg); se excluye pollo amarillo.
  - Carne molida especial → **milanesa de res** (74.6% mínima frente a 39%; medianas $218–229/kg). Se descartó
    "molida de cualquier grado" por mezclar 80/20 y 90/10.
  - Se retiran harina de maíz (la tortilla ya representa el maíz) y jabón, detergente y papel higiénico.
  - v0 se conserva en el seed; `canasta_version = v1` en `dbt_project.yml`.
- **Consecuencias:** La canasta es alimentaria; el costo no incluye limpieza ni higiene. Cambiar de versión
  recalcula todos los marts.

## D-023 · Ahorro como comparación pareada en la misma celda

- **Contexto:** Comparar el costo mediano nacional de cada cadena mezcla ciudades distintas (en la Fase 1 cada cadena
  tenía canasta completa en conjuntos diferentes de municipios).
- **Decisión:** `mart_ahorro_por_cadena` solo compara cadenas de referencia con canasta completa y ventana completa
  en el mismo municipio y semana, con al menos dos cadenas. `mart_precio_producto` descompone ese ahorro por
  artículo y una prueba verifica que la descomposición suma el ahorro total.
- **Consecuencias:** Los municipio-semanas sin dos canastas completas no aportan a métricas de ahorro; su cobertura se
  reporta en `mart_cobertura_datos` y en `reports/resultados_canasta.md`.

## D-024 · Validación independiente como compuerta del pipeline

- **Contexto:** Las pruebas dbt verifican consistencia interna, pero no que el cálculo sea correcto desde los datos
  crudos.
- **Decisión:** `src/analysis/validacion.py` recalcula en Python (normalización, reglas de canasta, consolidación y
  medianas) el costo y el ahorro de 6 municipio-semanas deterministas y los compara con los marts. Es un paso de
  `pipeline` y detiene la publicación si hay diferencias.
- **Consecuencias:** Omite celdas con atípicos (la detección usa estadísticas de todo el periodo). Comparte con el
  pipeline el parser de presentaciones y los mapeos versionados, que tienen sus propias pruebas.

## D-025 · Atípicos y decisiones manuales validados con datos

- **Contexto:** Pendientes de la Fase 1 (D-018, D-020).
- **Decisión:** Se mantienen las reglas de atípicos: en artículos de canasta hay 119 observaciones marcadas y solo 4
  en cadenas de referencia; no se concentran en martes (se descarta el sesgo por "Martes de Frescura"); la mayoría
  son pierna de pollo a ~$24/kg en Tijuana y Juárez (2024) frente a una mediana de $84. Las bolsas de detergente
  "3.564 Gr." cuestan $160 ($44.89/kg), igual que la bolsa de 1 kg ($44.90/kg): se confirma 3.564 kg.
- **Consecuencias:** Las decisiones manuales siguen marcadas como propuesta del asistente, ahora con evidencia; el
  detergente ya no forma parte de la canasta v1.

## D-026 · Evolución con índice directo de panel fijo, no encadenado

- **Contexto:** El primer reporte usaba un índice encadenado (mediana del cambio semanal de pares cadena-municipio).
  Mostraba una caída a ~94 a fines de 2025. Contra un índice directo con panel fijo (mismos pares, costo frente a
  su propio periodo base), el encadenado terminaba 3 puntos abajo (98.9 frente a 101.9): la mediana de razones
  encadenada acumula deriva con datos ruidosos.
- **Decisión:** La evolución se mide con un índice directo: pares cadena-municipio con canasta completa en las
  primeras 8 semanas; cada semana, media geométrica de costo / costo base de los pares presentes.
- **Consecuencias:** Sin deriva por encadenamiento; el panel pierde pares si una cadena deja de tener canasta completa
  en un municipio (se publica el número de pares).

## D-027 · Nivel de precios municipal controlando la mezcla de cadenas

- **Contexto:** Ordenar municipios por costo mediano favorece a los municipios donde solo se mide una cadena barata
  (Álvaro Obregón aparecía como barato sin tener semanas comparables).
- **Decisión:** Nivel municipal = media geométrica, entre las cadenas presentes, del costo de la cadena en el
  municipio entre su mediana nacional (100 = nacional).
- **Consecuencias:** Compara cada cadena consigo misma; se publica cuántas cadenas respaldan el nivel.

## D-028 · Variantes de nombre de cadena y giro con corrección manual

- **Contexto:** Además de acentos y `?`, hay variantes con otra letra: `Central de Abastos`/`Central de Abasto` (57 y
  152 tiendas) y `Tienda Departamentales`/`Tiendas Departamentales`. Una búsqueda por distancia de edición ≤ 2 no
  encontró otras variantes seguras (Papelería Dabo/Dany/Tony son negocios distintos).
- **Decisión:** `texto_correcciones_manual.csv` admite correcciones de valores sin `?`; se registran las dos variantes
  como propuesta del asistente. No afectan a las cadenas de referencia.
- **Consecuencias:** Cobertura por cadena sin duplicar la central de abasto.

## D-029 · Publicación atómica por intercambio de esquemas

- **Fecha:** 2026-09-12 · **Fase:** 3
- **Contexto:** CLAUDE.md exige no publicar parcialmente. Una carga tabla por tabla deja a Looker Studio viendo una
  mezcla de versiones si falla a la mitad.
- **Decisión:** `src/publish/postgres.py` carga todo en `<esquema>_carga` con `COPY`, verifica filas contra DuckDB,
  crea índices y en **una transacción** renombra `<esquema>` → `<esquema>_anterior`, `<esquema>_carga` → `<esquema>`,
  borra el anterior y otorga lectura al rol configurado. Bitácora en `qqp_meta.publicaciones` (fuera del esquema
  intercambiado) y fila de `metadatos` dentro.
- **Consecuencias:** Probado contra PostgreSQL 16 real: reemplazo sin duplicados, fallo simulado a mitad de carga
  conserva la versión anterior. Los permisos se re-otorgan en cada publicación (las tablas son nuevas).

## D-030 · Se publican marts y tablas BI, no la tabla de hechos

- **Contexto:** `fct_precio_observado` tiene 33 millones de filas; el dashboard necesita agregados.
- **Decisión:** Se publican 4 marts, 5 tablas BI (`transform/models/bi/`, construidas y probadas en dbt), `dim_canasta`
  vigente y `dim_geografia` (~783 mil filas en total). Las vistas del dashboard son tablas precalculadas en dbt, no
  vistas SQL en PostgreSQL, para que su lógica tenga pruebas y una sola fuente.
- **Consecuencias:** El reporte `resultados_canasta.md` y el dashboard leen el índice de la misma tabla
  (`bi_indice_canasta`). La trazabilidad hasta el dato crudo se hace en DuckDB.

## D-031 · Conexión a Supabase por el pooler en modo sesión

- **Contexto:** Según la documentación de Supabase, la conexión directa es IPv6 y GitHub Actions solo acepta IPv4; el
  modo transacción del pooler no admite *prepared statements* (psycopg los activa automáticamente).
- **Decisión:** Secretos `SUPABASE_DB_*` con el host y usuario del **Session pooler** (puerto 5432), `sslmode=require`
  por defecto. Looker Studio usa el mismo pooler con un rol de solo lectura.
- **Consecuencias:** No se requiere el complemento de IPv4 de pago.

## D-032 · Descarga de fuentes oficiales con enlaces versionados

- **Contexto:** El portal https://datos.profeco.gob.mx/datos_abiertos/qqp.php publica un archivo por año con enlaces
  de token opaco; una petición HEAD confirmó que devuelven `QQP_2024.rar`, `QQP_2025.rar` y `QQP_2026.zip`, sin `ETag`
  ni `Last-Modified`.
- **Decisión:** `data/fuentes_profeco.csv` versiona los enlaces; `src/ingest/download.py` verifica nombre declarado y
  firma ZIP/RAR, y nunca sobrescribe un original distinto salvo con `QQP_DESCARGA_REEMPLAZAR=1` (usado en CI, donde el
  runner empieza vacío). En local los archivos se siguen colocando a mano.
- **Consecuencias:** Un año nuevo requiere agregar su enlace. Como no hay metadatos de cambio, CI descarga los ~300 MB
  cada semana.

## D-033 · GitHub Actions: pruebas en cada cambio y pipeline completo semanal

- **Decisión:** Un workflow con dos jobs. `pruebas` (push y pull request): lint, pytest con PostgreSQL de servicio y
  pipeline de la muestra con publicación de prueba. `pipeline` (lunes 13:00 UTC y a demanda): descarga, un paso de
  GitHub por paso del pipeline, borrado de CSV extraídos tras la ingesta para no agotar el disco del runner,
  publicación solo si todo pasa, artefactos de reportes y un issue `alerta-pipeline` si algo falla.
- **Consecuencias:** El pipeline con datos completos no se ha ejecutado aún en GitHub (el repositorio no tiene remoto);
  los tiempos estimados se basan en la ejecución local.

## D-034 · Alertas: resumen de ejecución, webhook opcional y frescura de datos

- **Decisión:** `src/alertas.py` escribe el resumen en `$GITHUB_STEP_SUMMARY` y, si existe `ALERTA_WEBHOOK_URL`, notifica
  fallas y reglas en alerta (Slack, Teams o Discord). `src/cli.py` genera la alerta de falla automáticamente en
  cualquier paso. Nueva regla M-08 (advertencia): más de 35 días desde el último dato.
- **Consecuencias:** Con los archivos actuales M-08 ya está en alerta (106 días: datos al 2026-05-29).

## D-035 · dbt en modo UTF-8

- **Contexto:** En Windows dbt leyó `dbt_project.yml` con cp1252 y falló con un carácter acentuado; otros acentos se
  habrían leído mal sin error.
- **Decisión:** `src/cli.py` ejecuta dbt con `PYTHONUTF8=1` (también en el workflow).

## D-036 · Publicación compacta para el plan gratuito de Supabase (aprobada)

- **Fecha:** 2026-09-13 · **Fase:** 3 · **Aprobó:** responsable del proyecto
- **Contexto:** El proyecto de Supabase está en el plan gratuito, que pone la base en solo lectura al superar 500 MB
  de tamaño de base de datos (un proyecto nuevo ya ocupa 40–60 MB). La publicación completa medía 213 MB y el
  intercambio atómico mantiene dos copias un momento (pico ~425 MB + base), además del crecimiento semanal. Las dos
  tablas más pesadas eran de detalle: `mart_precio_producto` (95 MB) y `bi_disponibilidad_articulos` (73 MB).
- **Decisión:** Se publica `bi_disponibilidad_semanal` (agregado nacional) y `bi_articulos_faltantes` (solo
  `disponible = false`) en lugar del detalle completo de disponibilidad, y `mart_precio_producto` limitado a las
  últimas `QQP_PG_SEMANAS_DETALLE` semanas (52 por defecto). El intercambio atómico se conserva.
- **Consecuencias:** Todas las vistas del dashboard siguen disponibles; el detalle precio-producto-municipio anterior a
  52 semanas solo está en DuckDB. Con un plan de pago basta `QQP_PG_SEMANAS_DETALLE=0`.

## D-037 · Columnas adicionales conocidas en los CSV de PROFECO (aprobada)

- **Fecha:** 2026-09-13 · **Fase:** 3 (operación) · **Aprobó:** responsable del proyecto (autorizó descargar y adaptar)
- **Contexto:** La primera ejecución completa en GitHub Actions se detuvo en `inspect`: `06-2026_Q1.csv` y
  `06-2026_Q2.csv` traen 18 columnas, las 15 documentadas en su orden más `folio`, `cv_producto` y `cv_marca`. El
  diccionario oficial no las menciona y julio vuelve a 15 columnas (diccionario validado §6).
- **Opciones:** (a) seguir fallando hasta que PROFECO corrija; (b) aceptar cualquier columna extra; (c) aceptar solo
  las columnas ya revisadas y seguir deteniendo cualquier otro cambio.
- **Decisión:** (c). `COLUMNAS_ADICIONALES` en `src/ingest/csv_source.py`. Las 15 columnas esenciales deben estar
  completas y en orden; después solo se admiten columnas de esa lista, sin repetir. La lectura y la inserción se hacen
  por nombre: las adicionales se guardan en `raw.qqp_precios` (nulas en los demás archivos) y
  `raw.archivos.columnas_adicionales` registra cuáles trajo cada archivo. `inspect` las reporta como aviso. Staging
  no las selecciona.
- **Consecuencias:** El pipeline procesa junio y julio. Una columna nueva distinta, faltante o reordenada sigue
  deteniendo el pipeline. `folio` podría resolver L-07 (establecimientos por dirección), pero solo existe en dos
  archivos; se reevaluará si PROFECO lo mantiene.

## D-038 · Corrección de caracteres perdidos en estado y municipio

- **Fecha:** 2026-09-13 · **Fase:** 3 (operación)
- **Contexto:** En 2026-06 el 32% de las filas trae `?` en `municipio` (`Coyoac?n`, `Le?n`). Las llaves de geografía
  se calculaban sin corregir: esas filas habrían creado 21 municipios duplicados y partido la serie semanal y las
  comparaciones de junio y la primera semana de julio. En mayo 2026 la geografía no estaba afectada.
- **Decisión:** Agregar `estado` y `municipio` a las columnas con corrección por candidato único
  (`src/normalize/build.py`) y calcular `estado_key`, `municipio_key` y los nombres de `dim_geografia` con el valor
  corregido. La validación independiente aplica las mismas correcciones. Nueva prueba dbt: ninguna `municipio_key`
  contiene `?`.
- **Consecuencias:** Los 21 valores de junio se corrigen automáticamente. Si aparece un municipio con `?` sin
  candidato único, `dbt test` detiene el pipeline en lugar de publicar una geografía partida; se resuelve con una
  fila en `texto_correcciones_manual.csv`.

## D-039 · Catálogos relacionados por llave canónica

- **Fecha:** 2026-09-13 · **Fase:** 3 (operación)
- **Contexto:** Con D-037 y D-038, la ejecución completa en CI (run 34772772277) llegó a `dbt test` y falló en dos
  pruebas: 971,622 filas con catálogo fuera del seed y 439 combinaciones sin `catalogos_mask`. En 2026-07 PROFECO
  escribe `Básicos`, `PACIC`, `Útiles Escolares` y `Electrodomésticos` en lugar de `Basicos`, `Pacic`,
  `Utiles Escolares` y `Electrodomesticos`: mismos productos en Básicos (203), PACIC (25) y Electrodomésticos (33), y
  Útiles Escolares crece de 35 a 46 por la temporada escolar. Sin la prueba,
  `Básicos` y `PACIC` habrían quedado fuera de la canasta en julio.
- **Decisión:** Nuevo modelo `int_catalogos` (valor original → catálogo del seed por la macro `llave`), usado por
  `int_productos_sku` e `int_observaciones`. Pruebas: `catalogo_original` único y `bit` no nulo; sustituyen a la
  relación exacta en la fuente. El alcance de la cola de revisión (`src/normalize/build.py`) también compara por
  llave.
- **Consecuencias:** Un cambio de acentos o mayúsculas en un catálogo ya no detiene el pipeline; un catálogo realmente
  nuevo sí. Julio se comporta igual que junio: 128 a 139 celdas completas por semana en la prueba local, frente a
  130 a 137 en junio.

## D-021 · Medianas exactas para resultados deterministas

- **Contexto:** Con `approx_quantile`, dos ejecuciones idénticas dieron 0.0357% y 0.0356% de atípicos y 50.744% y
  50.749% de canastas completas: el t-digest en paralelo no es determinista.
- **Decisión:** Mediana y MAD por producto con `median` exacto.
- **Consecuencias:** Dos ejecuciones consecutivas produjeron exactamente los mismos atípicos (11,862) y la misma
  completitud (50.7494%). La tabla de hechos tardó 61 s, menos que con la versión aproximada (70 s).
