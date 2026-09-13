# Diccionario de datos validado — QQP PROFECO

**Fuente:** 58 CSV quincenales extraídos de `QQP_2024.rar`, `QQP_2025.rar` y `QQP_2026.zip`
(2024-01-02 a 2026-05-29). Sección 6: la versión de `QQP_2026.zip` descargada el 2026-09-13 agrega 4 archivos
(2026-06 y 2026-07) con cambios de formato.
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
| A-14 | Tres columnas no documentadas al final del encabezado (`folio`, `cv_producto`, `cv_marca`) | Solo 2026-06 (2 archivos) | Se aceptan por nombre y se conservan en `raw`; no se modelan (D-037). |
| A-15 | Caracteres perdidos también en `municipio` (32% de las filas de junio), además de producto, presentación y dirección | 2026-06 | Corrección por candidato único extendida a `estado` y `municipio` (D-038). |

## 4. Contraste con el diccionario oficial (Fase 3)

El portal de datos abiertos de PROFECO publica un diccionario en https://datos.profeco.gob.mx/diccionarioDatosQQP.php
(consultado el 2026-09-12). Coincide con el esquema observado:

| Diccionario oficial | Tipo oficial | Columna en los CSV | Diferencia |
|---|---|---|---|
| PRODUCTO | Carácter (65) | `producto` | Solo nombre: los CSV usan minúsculas y guion bajo. |
| PRESENTACIÓN | Carácter (180) | `presentacion` | |
| MARCA | Carácter (65) | `marca` | |
| CATEGORÍA | Carácter (65) | `categoria` | |
| CATÁLOGO | Carácter (65) | `catalogo` | El diccionario no enumera los catálogos ni explica `Pacic`. |
| PRECIO | Número (18,2) | `precio` | Confirma: "precio del producto de venta al público". No indica moneda ni impuestos. |
| FECHAREGISTRO | Fecha y hora (8) | `fecha_registro` | No documenta el formato de texto; los archivos usan dos (sección 1). |
| CADENACOMERCIAL | Carácter (65) | `cadena_comercial` | |
| GIRO | Carácter (65) | `giro` | |
| NOMBRECOMERCIAL | Carácter (120) | `nombre_comercial` | |
| DIRECCIÓN | Carácter (255) | `direccion` | |
| ESTADO | Carácter (120) | `estado` | |
| MUNICIPIO | Carácter (120) | `municipio` | Define "municipio o demarcación territorial" (incluye alcaldías de CDMX). |
| LATITUD | Número (18,6) | `latitud` | Confirma grados decimales. |
| LONGITUD | Número (18,6) | `longitud` | Confirma grados decimales. |

El portal ofrece además un archivo de metadatos que no se descargó en esta fase. En una nueva consulta del
2026-09-13 el diccionario sigue documentando solo estas 15 columnas.

## 5. Interpretaciones pendientes de confirmar

- **`Pacic`**: probablemente el *Paquete Contra la Inflación y la Carestía* (programa federal de precios de
  productos básicos). Sus productos se repiten en `Basicos` y `Frutas y Legumbres`.
- **Unidad del precio**: se asume precio por presentación completa en MXN con IVA incluido (precio de anaquel).
- **Grano de levantamiento**: una tienda se visita típicamente 2 días por quincena; no se sabe si todos los
  productos se levantan en cada visita.
- **`folio`, `cv_producto`, `cv_marca`** (sección 6): no documentadas; no se usan en el modelo.

## 6. Archivos 2026-06 y 2026-07 (descarga del 2026-09-13)

La primera ejecución completa en GitHub Actions descargó una versión nueva de `QQP_2026.zip` (195.6 MB, SHA-256
`172bd1a4…`) y se detuvo en `inspect` por cambio de esquema. Revisión hecha sobre una copia en
`data/interim/descargas/` (el original de `data/raw/` no se modificó):

- Los 10 CSV de enero a mayo son idénticos a los ya cargados (mismo tamaño y CRC32). Dentro del zip ahora están en
  una carpeta `QQP_2026/`; la extracción ya usaba solo el nombre del archivo.
- Se agregan `06-2026_Q1` (622,490 filas), `06-2026_Q2` (632,548), `07-2026_Q1` (665,909) y `07-2026_Q2` (744,623),
  con fechas del 2026-06-01 al 2026-07-31.

| Propiedad | 2026-06 Q1 y Q2 | 2026-07 Q1 y Q2 |
|---|---|---|
| Codificación | UTF-8 con BOM (vuelve al formato de 2024–2026-04) | UTF-8 con BOM |
| Formato `fecha_registro` | `yyyy/mm/dd` | `yyyy/mm/dd` |
| Encabezado | **18 columnas**: las 15 documentadas en el mismo orden + `folio`, `cv_producto`, `cv_marca` | 15 columnas |
| Filas cargadas = líneas − 1 | Verificado | Verificado |
| Fechas, precios inválidos | 0 | 0 |

Columnas adicionales de 2026-06 (sin documentación oficial; todo como texto):

| Columna | Observado en los 2 archivos | Interpretación | Certeza |
|---|---|---|---|
| `folio` | Numérico, sin vacíos. 1,640 y 1,753 valores; relación 1 a 1 con nombre comercial + dirección. | Identificador del establecimiento. | Inferido |
| `cv_producto` | Numérico, sin vacíos. Cada código corresponde a un solo `producto` (797 códigos para 739 productos). | Clave de producto de PROFECO, más fina que el nombre. | Inferido |
| `cv_marca` | Numérico, sin vacíos. 313 códigos aparecen con más de una `marca`. | No es una llave de marca por sí sola; significado desconocido. | Inferido |

Anomalía de 2026-06: **caracteres perdidos masivos** (A-15). En julio no hay ninguno.

| Columna | Filas con `?` en 2026-06 | Valores distintos | Sin corrección automática |
|---|---|---|---|
| `municipio` | 401,781 (32%) | 21 (`Coyoac?n`, `Le?n`, `Ju?rez`…) | 0 |
| `presentacion` | 230,839 | 619 | 3 valores, 294 filas |
| `producto` | 163,819 | 75 (`Az?car`, `Caf?`…) | 0 |
| `direccion` | 147,248 | 287 | 0 |
| `marca` | 64,968 | 99 | 2 valores, 1,435 filas |
| `nombre_comercial` | 60,862 | 608 | 1 valor, 4 filas |
| `giro` | 34,953 | 5 | 0 |
| `categoria` | 496 | 1 (`Art?culos Deportivos`) | no se corrige (no es llave ni se usa en la canasta) |
| `estado`, `cadena_comercial`, `catalogo` | 0 | — | — |

"Sin corrección automática" se midió con el método de candidato único (`docs/normalizacion.md` §2) sobre los valores
de los 58 archivos cargados, los de 2026-06 y los de `07-2026_Q2`.
