# Supuestos y limitaciones

Documento vivo: cada limitación indica su efecto en los resultados y, si aplica, la fase en que se atiende.

## Datos de origen

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-01 | Los archivos recibidos no incluían diccionario. En la Fase 3 se localizó el diccionario oficial en línea: confirma las 15 columnas y define precio como "precio de venta al público", pero no documenta catálogos (`Pacic`), moneda ni impuestos. | Moneda (MXN) e IVA siguen siendo supuestos. | `docs/diccionario_validado.md` secciones 4 y 5. |
| L-02 | Cobertura geográfica de ciudades muestreadas: 75 municipios en 30 estados, casi siempre la capital; sin Colima ni Nayarit. | Un indicador "estatal" describe la ciudad muestreada, no la entidad. | Etiquetar como ciudad en el dashboard (D-012). |
| L-03 | Cada tienda se visita ~2 días por quincena y no todos los productos se levantan en cada visita. | La semana aislada es escasa; se usa ventana de 14 días (D-010). | Publicar observaciones y cobertura con cada métrica. |
| L-04 | Mayo 2026 cambió codificación, formato de fecha y mayúsculas; `05-2026_Q2.csv` perdió letras acentuadas (`?`). Junio 2026 volvió a UTF-8 pero perdió acentos en muchas más filas, incluido el municipio (32%). | Riesgo de partir series, establecimientos y municipios. | Lectura por archivo (D-003), llaves canónicas y correcciones con candidato único, también en estado y municipio (D-038); casos sin candidato quedan en revisión. `categoria` no se corrige (1 valor, 496 filas fuera de la canasta). |
| L-23 | Junio 2026 trae `folio`, `cv_producto` y `cv_marca`, sin documentación oficial y ausentes en julio. | No se usan: el establecimiento sigue identificándose por nombre + dirección (L-07). | Se conservan en `raw` (D-037); reevaluar si PROFECO las mantiene. |
| L-05 | La misma observación se publica en varios catálogos y existen precios en conflicto el mismo día. | Doble conteo si no se consolida. | Consolidación (D-006) y bandera `tiene_precio_en_conflicto` (80,286 observaciones, 0.24%). |

## Normalización y modelo

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-06 | 2.5% de las observaciones de catálogos de canasta tienen presentación no comparable (ambigua o sin cantidad). | Quedan fuera de precios unitarios y medianas. | Cola `reports/revision_manual_productos.csv`; decisiones en `data/mappings/manual/`. |
| L-07 | Un establecimiento se identifica por nombre + dirección normalizados. | Si PROFECO reescribe una dirección, la tienda aparece como nueva. | Consolidación por coordenadas en una fase posterior. |
| L-08 | Atípicos por producto sobre todo el periodo (2.5 años), con mediana y MAD exactas. | La inflación no se descuenta; umbrales de 3× y 10× son holgados a propósito. | Validado en Fase 2: 119 observaciones de artículos de canasta marcadas, 4 en cadenas de referencia, sin sesgo de día (D-025). |
| L-09 | Las decisiones manuales (detergente `3.564 Gr.`, variantes de cadena y giro) son propuestas del asistente con evidencia de datos. | El detergente ya no está en la canasta v1; las variantes no afectan a cadenas de referencia. | Validación humana pendiente (D-025, D-028). |

## Canasta

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-10 | La canasta v0 es genérica: cada artículo es la mediana de precio unitario de cualquier marca comparable. | Diferencias entre cadenas combinan precio y mezcla de marcas (p. ej. marcas propias). | Documentado en D-009; explicar en dashboard y memo. |
| L-11 | `cantidad_referencia` = presentación modal observada, no consumo de un hogar. | El costo es un índice comparable entre cadenas y semanas, no el gasto real de una familia. | Sustituir por cantidades de una fuente oficial en una versión posterior de la canasta. |
| L-12 | Ventana móvil: semanas consecutivas comparten la mitad de sus observaciones. | Cambios semanales suavizados y no independientes. | Mostrar la ventana (`ventana_desde`); evolución con índice directo de panel fijo (D-026). |
| L-13 | Con la canasta v1, 81% de celdas de referencia tienen canasta completa y 85% de municipio-semanas permiten comparar al menos dos cadenas; Bodega Aurrera es la más baja (~68%). 24 de 75 municipios nunca tienen dos cadenas de referencia completas en la misma semana (p. ej. Toluca: 1 tienda de referencia). | El ahorro se estima en 51 municipios; los demás solo aportan cobertura. | Documentado en `reports/resultados_canasta.md` (sección 5). |
| L-17 | En la mediana de las celdas, cada cadena de referencia está representada por 1 tienda y 1 día de levantamiento por semana. | El costo de una celda puede reflejar una sola sucursal; hay ruido semana a semana. | Ventana de 14 días, medianas, publicación de `n_observaciones` y análisis sobre muchas celdas. |
| L-18 | La canasta genérica mezcla marcas: el sobreprecio mediano de pasta para sopa frente a la cadena más barata es ~109% (marca propia frente a marca comercial). | Parte del ahorro refleja la oferta de marcas de cada cadena, no solo su precio. | Mostrar diferencias por artículo (`mart_precio_producto`) y advertirlo en el dashboard y el memo. |
| L-19 | La canasta v1 es alimentaria: no incluye limpieza ni higiene (D-022). | El costo subestima el gasto básico total del hogar. | Posible canasta complementaria en una versión posterior. |
| L-14 | Wal-mart y Bodega Aurrera pertenecen al mismo grupo empresarial. | Su diferencia es de formato de tienda, no de competencia. | Columna `grupo_empresarial` en `seeds.cadenas_referencia` (D-011). |

## Operación

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-15 | El equipo de desarrollo se apaga por protección térmica con consultas de muchos hilos sostenidas. | Rendimiento acotado a 4 hilos y 8 GB. | Límites configurables (D-004); los mismos valores sirven para GitHub Actions. |
| L-16 | Los enlaces oficiales de descarga usan tokens opacos y el servidor no publica fecha de modificación. | Un año nuevo requiere agregar su enlace a `data/fuentes_profeco.csv`; CI descarga ~300 MB cada semana. Si PROFECO cambia un token, la descarga falla (y alerta). | D-032. |
| L-20 | Los archivos locales terminan el 2026-05-29. La versión de PROFECO descargada el 2026-09-13 llega al 2026-07-31 (44 días de rezago). | Los resultados locales no reflejan junio y julio; aun con la versión vigente, M-08 (≤ 35 días) queda en alerta mientras PROFECO no publique agosto. | La ejecución completa en CI descarga la versión vigente. `data/raw/` no se reemplaza automáticamente (D-032). |
| L-22 | Plan gratuito de Supabase: límite de 500 MB y pausa de proyectos con poca actividad en 7 días. | En Supabase el detalle precio-producto-municipio cubre solo 52 semanas (D-036); si el proyecto se pausa, el dashboard deja de responder hasta reanudarlo. | Consultas del dashboard generan actividad; un plan de pago elimina ambos límites. |
| L-21 | La primera ejecución completa en GitHub Actions con publicación en Supabase terminó bien el 2026-09-13 (run 34773616518, ~10 min), pero desde la rama del PR #3 y no desde `main`. La ejecución semanal programada todavía no ha corrido. | Hasta integrar el PR #3, la ejecución programada del lunes corre el código de `main` y fallaría con los archivos de junio. | Integrar el PR #3 antes del próximo lunes. |
