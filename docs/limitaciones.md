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
| L-08 | Atípicos por producto sobre todo el periodo (2.5 años), con mediana y MAD exactas. | La inflación no se descuenta; umbrales de 3× y 10× son holgados a propósito. Ofertas muy agresivas pueden quedar marcadas. | Validación manual en Fase 2 (D-018). |
| L-09 | Las decisiones sobre `Bolsa 3.564 Gr.` de detergente son propuestas del asistente. | Afectan precio unitario de ese artículo. | Validar en Fase 2 (D-020). |

## Canasta

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-10 | La canasta v0 es genérica: cada artículo es la mediana de precio unitario de cualquier marca comparable. | Diferencias entre cadenas combinan precio y mezcla de marcas (p. ej. marcas propias). | Documentado en D-009; explicar en dashboard y memo. |
| L-11 | `cantidad_referencia` = presentación modal observada, no consumo de un hogar. | El costo es un índice comparable entre cadenas y semanas, no el gasto real de una familia. | Sustituir por cantidades de una fuente oficial en una versión posterior de la canasta. |
| L-12 | Ventana móvil: semanas consecutivas comparten la mitad de sus observaciones. | Cambios semanales suavizados y no independientes. | Mostrar la ventana (`ventana_desde`) y evitar pruebas estadísticas semana contra semana. |
| L-13 | En datos completos solo 50.7% de celdas cadena de referencia × municipio × semana tienen la canasta completa. | Comparaciones posibles en la mitad de las celdas; las incompletas no publican costo. | Revisión de la selección de artículos en Fase 2 (carne molida especial, pierna de pollo, harina de maíz, limpieza). |
| L-14 | Wal-mart y Bodega Aurrera pertenecen al mismo grupo empresarial. | Su diferencia es de formato de tienda, no de competencia. | Columna `grupo_empresarial` en `seeds.cadenas_referencia` (D-011). |

## Operación

| # | Limitación | Efecto | Mitigación |
|---|---|---|---|
| L-15 | El equipo de desarrollo se apaga por protección térmica con consultas de muchos hilos sostenidas. | Rendimiento acotado a 4 hilos y 8 GB. | Límites configurables (D-004); los mismos valores sirven para GitHub Actions. |
| L-16 | GitHub Actions no tiene acceso a `data/raw` (no se versiona). | La ejecución semanal requiere descargar los datos de PROFECO o usar la muestra. | Definir fuente de descarga en la Fase 3. |
