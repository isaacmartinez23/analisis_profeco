# Supuestos y limitaciones

Documento vivo: cada limitación indica su efecto en los resultados y, si aplica, la fase en que se atiende.

## Datos de origen

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-01 | PROFECO no entregó diccionario de datos ni metadatos. | Las definiciones son inferidas (`docs/diccionario_validado.md` marca qué está verificado y qué no). | Confirmar con documentación oficial: significado de `Pacic`, IVA incluido, moneda. |
| L-02 | Cobertura geográfica de ciudades muestreadas: 75 municipios en 30 estados, casi siempre la capital; sin Colima ni Nayarit. | Un indicador "estatal" describe la ciudad muestreada, no la entidad. | Etiquetar como ciudad en el dashboard (D-012). |
| L-03 | Cada tienda se visita ~2 días por quincena y no todos los productos se levantan en cada visita. | La semana aislada es escasa; se usa ventana de 14 días (D-010). | Publicar observaciones y cobertura con cada métrica. |
| L-04 | Mayo 2026 cambió codificación, formato de fecha y mayúsculas; `05-2026_Q2.csv` perdió letras acentuadas (`?`). | Riesgo de partir series y establecimientos. | Lectura por archivo (D-003), llaves canónicas y correcciones con candidato único; casos sin candidato quedan en revisión. |
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
| L-16 | GitHub Actions no tiene acceso a `data/raw` (no se versiona). | La ejecución semanal requiere descargar los datos de PROFECO o usar la muestra. | Definir fuente de descarga en la Fase 3. |
