# Diccionario de datos validado — QQP PROFECO

**Fuente:** 58 CSV quincenales extraídos de `QQP_2024.rar`, `QQP_2025.rar` y `QQP_2026.zip`
(2024-01-02 a 2026-05-29).
**Método:** PROFECO no entregó diccionario ni metadatos. Cada definición se dedujo de los datos y se marca con su
nivel de certeza: **Verificado** (comprobado en las 33.5 M filas) o **Inferido** (interpretación razonable, a
confirmar con la documentación oficial).
Cifras reproducibles en `reports/perfil_datos.md`.

## 1. Formato físico

| Propiedad | 2024-01 a 2026-04 (56 archivos) | 2026-05 Q1 y Q2 (2 archivos) |
|---|---|---|
| Codificación | UTF-8 con BOM | **ISO-8859-1 (Latin-1) sin BOM** |
| Delimitador | `,` | `,` |
| Comillas | `"` solo cuando el campo contiene coma | igual |
| Fin de línea | CRLF | CRLF |
| Encabezado | 15 columnas | mismas 15 columnas, mismo orden |
| Formato `fecha_registro` | `yyyy/mm/dd` | **`dd/mm/yyyy`** |
| Nombre de archivo | `MM-AAAA_01.csv` / `MM-AAAA_02.csv` (2026: `_Q1`/`_Q2`) | `MM-2026_Q1.csv` / `_Q2` |

- **Verificado:** no hay saltos de línea dentro de campos (filas cargadas = líneas físicas − 1 en los 58
  archivos) y DuckDB no rechazó ninguna fila.
- **Verificado:** en los archivos Latin-1 no hay bytes 0x80–0x9F ni secuencias UTF-8 mezcladas.
- Cada archivo cubre una quincena: `_01`/`Q1` = días 1–15 y `_02`/`Q2` = días 16–fin de mes. No hay traslape de
  fechas entre archivos (**Verificado**).

## 2. Columnas

| # | Columna | Tipo destino | Nulos/vacíos | Distintos | Descripción | Certeza |
|---|---|---|---|---|---|---|
| 1 | `producto` | texto | 0 | 821 | Nombre genérico del producto (p. ej. `Leche Ultrapasteurizada`, `Tortilla de Maíz`). | Verificado |
| 2 | `presentacion` | texto | 0 | 5,537 | Descripción libre de empaque, contenido y variante (`Caja 1 Lt. Entera`, `1 Kg. Granel. Alfa/blanca`). Contiene la cantidad y unidad a normalizar. | Verificado |
| 3 | `marca` | texto | 0 | 1,382 | Marca; `S/m`/`S/M` = sin marca (granel). Puede incluir submarca separada por punto (`Alpura. Clásica`). | Verificado |
| 4 | `categoria` | texto | 0 | 56 | Agrupación de productos dentro del catálogo (`Derivados de Leche`, `Hortalizas Frescas`). | Verificado |
| 5 | `catalogo` | texto | 0 | 12 | Programa o catálogo de levantamiento: `Basicos`, `Medicamentos`, `Electrodomesticos`, `Frutas y Legumbres`, `Pacic`, `Utiles Escolares`, `Mercados`, `Juguetes`, `Pescados y Mariscos`, `Navideños`, `Especial`, `Tenis`. | Verificado |
| 6 | `precio` | decimal(12,2) | 0 | — | Precio observado en pesos mexicanos por la presentación indicada. 100% convertible a número; sin negativos ni ceros; mínimo 1.15. | Verificado (moneda: Inferido) |
| 7 | `fecha_registro` | fecha | 0 | — | Día del levantamiento. Dos formatos según archivo (sección 1). 100% convertible. | Verificado |
| 8 | `cadena_comercial` | texto | 0 | 264 | Cadena o razón comercial (`Wal-mart`, `Bodega Aurrera`, `Chedraui`). | Verificado |
| 9 | `giro` | texto | 0 | 18 | Tipo de establecimiento (`Supermercado / Tienda de Autoservicio`, `Farmacias`). | Verificado |
| 10 | `nombre_comercial` | texto | 0 | 2,422 | Nombre de la sucursal. | Verificado |
| 11 | `direccion` | texto | 0 | 3,224 | Dirección libre de la sucursal. | Verificado |
| 12 | `estado` | texto | 0 | 37 → 30 normalizados | Entidad federativa. | Verificado |
| 13 | `municipio` | texto | 0 | 75 combinaciones estado-municipio normalizadas | Municipio o alcaldía. | Verificado |
| 14 | `latitud` | decimal | 791 | — | Latitud de la sucursal (WGS84). | Verificado (datum: Inferido) |
| 15 | `longitud` | decimal | 791 | — | Longitud de la sucursal. | Verificado |

## 3. Discrepancias y anomalías registradas

| ID | Hallazgo | Alcance | Tratamiento propuesto |
|---|---|---|---|
| A-01 | Codificación Latin-1 y fecha `dd/mm/yyyy` en mayo 2026 | 2 archivos, 1.0 M filas | Lectura con parámetros por archivo (D-003); prueba automatizada. |
| A-02 | Caracteres perdidos: `?` en lugar de letra acentuada (`Papeler?as`, `Jugueter?as`) | 12,378 filas, solo `05-2026_Q2.csv` | Es pérdida en el origen, no error de lectura. Mapeo de corrección en normalización y bandera de calidad. |
| A-03 | Estados con y sin acento (`Ciudad de Mexico` 2024–2025, `Ciudad de México` 2026) | 7 estados | Normalizar con mayúsculas y sin acentos para la llave; conservar el nombre oficial en la dimensión. |
| A-04 | `S/m` (hasta 2025) vs `S/M` (2026) en marca | Productos a granel | Normalizar mayúsculas antes de comparar. |
| A-05 | Cambio de mayúsculas en presentación (`Puerto Usb` → `Puerto USB`, `Oled` → `OLED`) | Mayo 2026 | Llave de presentación normalizada en mayúsculas. |
| A-06 | Misma observación en dos catálogos (`Basicos + Pacic` 340 mil grupos, `Frutas y Legumbres + Pacic` 265 mil, `Electrodomesticos + Juguetes` 4 mil, otros) | 614,653 grupos; casi todos los duplicados en el grano | Una sola observación en hechos; catálogo como pertenencia (D-006). |
| A-07 | Precios distintos para el mismo producto, tienda, fecha y catálogo | 20,816 grupos en 2.5 años | Conservar ambos, marcar y usar mediana. |
| A-08 | Filas idénticas en las 15 columnas | 211 filas (2026-02 Q2 en adelante) | Deduplicar en staging con conteo registrado. |
| A-09 | Precio extremo: medicamento a $3,041,791 | 1 fila | Marcar como atípico; no eliminar. |
| A-10 | Variantes de giro (`Tienda Departamentales` / `Tiendas Departamentales`) y de cadena (`Sears Roebuck de Mexico` / `de México`) | Varias | Mapeo versionado en `data/mappings/`. |
| A-11 | Coordenadas vacías o fuera de México | 791 vacías; 46 latitudes y 16 longitudes fuera de rango | Bandera de calidad en la dimensión establecimiento. |
| A-12 | Sin cobertura en Colima ni Nayarit; Hidalgo con 70 de 126 semanas | Geografía | Documentar como limitación; no imputar. |
| A-13 | Pocas zonas urbanas: la mayoría de los estados tiene 1 municipio (la capital); CDMX 13 alcaldías y Estado de México 17 municipios | Geografía | Interpretar como “ciudades muestreadas”, no representatividad estatal. |

## 4. Interpretaciones pendientes de confirmar

- **`Pacic`**: probablemente el *Paquete Contra la Inflación y la Carestía* (programa federal de precios de
  productos básicos). Sus productos se repiten en `Basicos` y `Frutas y Legumbres`.
- **Unidad del precio**: se asume precio por presentación completa en MXN con IVA incluido (precio de anaquel).
- **Grano de levantamiento**: una tienda se visita típicamente 2 días por quincena; no se sabe si todos los
  productos se levantan en cada visita.
