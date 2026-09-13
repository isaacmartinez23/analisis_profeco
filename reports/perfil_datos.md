# Perfil de datos — Quién es Quién en los Precios (PROFECO)

_Generado automáticamente por `python -m src.ingest.profile` el 2026-09-12 17:39._
_No editar a mano: las interpretaciones viven en `docs/diccionario_validado.md` y `docs/bitacora.md`._

## Resumen

- Archivos originales: **3** comprimidos → **58** CSV (10.57 GB sin comprimir)
- Filas: **33,581,522** · periodo **2024-01-02** a **2026-05-29**
- Estados (normalizados): **30** · municipios: **75**

## Alertas automáticas

- **Codificación distinta** en 2 archivo(s): `QQP_2026/05-2026_Q1.csv` (cp1252), `QQP_2026/05-2026_Q2.csv` (cp1252)
- **Formato de fecha distinto** (`dd/mm/yyyy` vs `yyyy/mm/dd`) en: `QQP_2026/05-2026_Q1.csv`, `QQP_2026/05-2026_Q2.csv`
- Filas rechazadas por el lector CSV: **0**
- **Precio extremo**: Prevefem Complex (Caja con 30 Tabletas) a $3,041,791 en Hipermercado Soriana — más de 100× el percentil 99 ($12,599)
- Duplicados exactos: **211** filas; en grano candidato: **636,840** (1.90%), de los cuales 614,653 grupos son la misma observación publicada en varios catálogos y 20,816 tienen precios en conflicto
- **Caracteres perdidos (`?` en lugar de letra acentuada)** en: `QQP_2026/05-2026_Q2.csv` (12,378 filas)
- **Nombres de estado con variantes** (acentos): 7 estados (37 valores originales → 30 normalizados)
- **Marca genérica con variantes de mayúsculas**: `S/m`, `S/M`

## 1. Archivos originales (`data/raw/`, inmutables)

| archivo      |     MB |   csv | sha256            |
|:-------------|-------:|------:|:------------------|
| QQP_2024.rar |  96.06 |    24 | 740e1498e9d7fae7… |
| QQP_2025.rar |  85.14 |    24 | 41ca4cd962e696f9… |
| QQP_2026.zip | 127.65 |    10 | 3d89842186f949c5… |

## 2. Inventario de CSV

| archivo                 |    MB | codificacion   | bom   |   lineas_fisicas |   filas_cargadas | formato_fecha   | min_fecha   | max_fecha   |   dias |
|:------------------------|------:|:---------------|:------|-----------------:|-----------------:|:----------------|:------------|:------------|-------:|
| QQP_2024/01-2024_01.csv | 176.4 | utf-8-sig      | True  |          560,730 |          560,729 | yyyy/mm/dd      | 2024-01-02  | 2024-01-15  |     10 |
| QQP_2024/01-2024_02.csv | 224.2 | utf-8-sig      | True  |          710,527 |          710,526 | yyyy/mm/dd      | 2024-01-16  | 2024-01-31  |     13 |
| QQP_2024/02-2024_01.csv | 187.9 | utf-8-sig      | True  |          596,334 |          596,333 | yyyy/mm/dd      | 2024-02-01  | 2024-02-15  |     11 |
| QQP_2024/02-2024_02.csv | 196.8 | utf-8-sig      | True  |          624,759 |          624,758 | yyyy/mm/dd      | 2024-02-16  | 2024-02-29  |     10 |
| QQP_2024/03-2024_01.csv | 213.2 | utf-8-sig      | True  |          676,519 |          676,518 | yyyy/mm/dd      | 2024-03-01  | 2024-03-15  |     11 |
| QQP_2024/03-2024_02.csv | 144.9 | utf-8-sig      | True  |          458,900 |          458,899 | yyyy/mm/dd      | 2024-03-19  | 2024-03-27  |      7 |
| QQP_2024/04-2024_01.csv | 201.2 | utf-8-sig      | True  |          637,340 |          637,339 | yyyy/mm/dd      | 2024-04-01  | 2024-04-15  |     11 |
| QQP_2024/04-2024_02.csv | 214.1 | utf-8-sig      | True  |          678,353 |          678,352 | yyyy/mm/dd      | 2024-04-16  | 2024-04-30  |     11 |
| QQP_2024/05-2024_01.csv | 180.7 | utf-8-sig      | True  |          573,584 |          573,583 | yyyy/mm/dd      | 2024-05-02  | 2024-05-15  |     10 |
| QQP_2024/05-2024_02.csv | 219.9 | utf-8-sig      | True  |          699,080 |          699,079 | yyyy/mm/dd      | 2024-05-16  | 2024-05-31  |     12 |
| QQP_2024/06-2024_01.csv | 186.6 | utf-8-sig      | True  |          592,208 |          592,207 | yyyy/mm/dd      | 2024-06-03  | 2024-06-14  |     10 |
| QQP_2024/06-2024_02.csv | 193.7 | utf-8-sig      | True  |          614,526 |          614,525 | yyyy/mm/dd      | 2024-06-17  | 2024-06-28  |     10 |
| QQP_2024/07-2024_01.csv | 218.9 | utf-8-sig      | True  |          693,723 |          693,722 | yyyy/mm/dd      | 2024-07-01  | 2024-07-15  |     11 |
| QQP_2024/07-2024_02.csv | 246.6 | utf-8-sig      | True  |          781,175 |          781,174 | yyyy/mm/dd      | 2024-07-16  | 2024-07-31  |     12 |
| QQP_2024/08-2024_01.csv | 231.8 | utf-8-sig      | True  |          735,697 |          735,696 | yyyy/mm/dd      | 2024-08-01  | 2024-08-15  |     11 |
| QQP_2024/08-2024_02.csv | 220.6 | utf-8-sig      | True  |          700,638 |          700,637 | yyyy/mm/dd      | 2024-08-16  | 2024-08-30  |     11 |
| QQP_2024/09-2024_01.csv | 177.5 | utf-8-sig      | True  |          561,264 |          561,263 | yyyy/mm/dd      | 2024-09-02  | 2024-09-13  |     10 |
| QQP_2024/09-2024_02.csv | 173.0 | utf-8-sig      | True  |          549,216 |          549,215 | yyyy/mm/dd      | 2024-09-17  | 2024-09-30  |     10 |
| QQP_2024/10-2024_01.csv | 177.9 | utf-8-sig      | True  |          564,007 |          564,006 | yyyy/mm/dd      | 2024-10-02  | 2024-10-15  |     10 |
| QQP_2024/10-2024_02.csv | 206.9 | utf-8-sig      | True  |          656,834 |          656,833 | yyyy/mm/dd      | 2024-10-16  | 2024-10-31  |     12 |
| QQP_2024/11-2024_01.csv | 185.7 | utf-8-sig      | True  |          586,210 |          586,209 | yyyy/mm/dd      | 2024-11-01  | 2024-11-15  |     11 |
| QQP_2024/11-2024_02.csv | 188.3 | utf-8-sig      | True  |          591,279 |          591,278 | yyyy/mm/dd      | 2024-11-16  | 2024-11-29  |     12 |
| QQP_2024/12-2024_01.csv | 173.3 | utf-8-sig      | True  |          549,253 |          549,252 | yyyy/mm/dd      | 2024-12-02  | 2024-12-13  |     10 |
| QQP_2024/12-2024_02.csv | 156.7 | utf-8-sig      | True  |          497,087 |          497,086 | yyyy/mm/dd      | 2024-12-16  | 2024-12-30  |     10 |
| QQP_2025/01-2025_01.csv | 172.9 | utf-8-sig      | True  |          547,783 |          547,782 | yyyy/mm/dd      | 2025-01-02  | 2025-01-15  |     10 |
| QQP_2025/01-2025_02.csv | 218.8 | utf-8-sig      | True  |          696,183 |          696,182 | yyyy/mm/dd      | 2025-01-16  | 2025-01-31  |     12 |
| QQP_2025/02-2025_01.csv | 168.9 | utf-8-sig      | True  |          536,079 |          536,078 | yyyy/mm/dd      | 2025-02-04  | 2025-02-14  |      9 |
| QQP_2025/02-2025_02.csv | 190.8 | utf-8-sig      | True  |          606,777 |          606,776 | yyyy/mm/dd      | 2025-02-17  | 2025-02-28  |     10 |
| QQP_2025/03-2025_01.csv | 184.3 | utf-8-sig      | True  |          587,059 |          587,058 | yyyy/mm/dd      | 2025-03-03  | 2025-03-14  |     10 |
| QQP_2025/03-2025_02.csv | 186.9 | utf-8-sig      | True  |          594,321 |          594,320 | yyyy/mm/dd      | 2025-03-18  | 2025-03-31  |     10 |
| QQP_2025/04-2025_01.csv | 186.6 | utf-8-sig      | True  |          594,888 |          594,887 | yyyy/mm/dd      | 2025-04-01  | 2025-04-15  |     11 |
| QQP_2025/04-2025_02.csv | 135.3 | utf-8-sig      | True  |          430,974 |          430,973 | yyyy/mm/dd      | 2025-04-16  | 2025-04-30  |      9 |
| QQP_2025/05-2025_01.csv | 137.3 | utf-8-sig      | True  |          437,834 |          437,833 | yyyy/mm/dd      | 2025-05-02  | 2025-05-15  |      9 |
| QQP_2025/05-2025_02.csv | 165.2 | utf-8-sig      | True  |          526,970 |          526,969 | yyyy/mm/dd      | 2025-05-16  | 2025-05-30  |     11 |
| QQP_2025/06-2025_01.csv | 168.3 | utf-8-sig      | True  |          534,835 |          534,834 | yyyy/mm/dd      | 2025-06-02  | 2025-06-13  |     10 |
| QQP_2025/06-2025_02.csv | 180.8 | utf-8-sig      | True  |          573,714 |          573,713 | yyyy/mm/dd      | 2025-06-16  | 2025-06-30  |     11 |
| QQP_2025/07-2025_01.csv | 209.0 | utf-8-sig      | True  |          664,947 |          664,946 | yyyy/mm/dd      | 2025-07-01  | 2025-07-15  |     11 |
| QQP_2025/07-2025_02.csv | 224.5 | utf-8-sig      | True  |          715,247 |          715,246 | yyyy/mm/dd      | 2025-07-16  | 2025-07-31  |     12 |
| QQP_2025/08-2025_01.csv | 217.5 | utf-8-sig      | True  |          692,570 |          692,569 | yyyy/mm/dd      | 2025-08-01  | 2025-08-15  |     11 |
| QQP_2025/08-2025_02.csv | 153.5 | utf-8-sig      | True  |          489,956 |          489,955 | yyyy/mm/dd      | 2025-08-18  | 2025-08-29  |     10 |
| QQP_2025/09-2025_01.csv | 170.6 | utf-8-sig      | True  |          542,923 |          542,922 | yyyy/mm/dd      | 2025-09-01  | 2025-09-15  |     11 |
| QQP_2025/09-2025_02.csv | 167.0 | utf-8-sig      | True  |          534,093 |          534,092 | yyyy/mm/dd      | 2025-09-17  | 2025-09-30  |     10 |
| QQP_2025/10-2025_01.csv | 166.4 | utf-8-sig      | True  |          528,493 |          528,492 | yyyy/mm/dd      | 2025-10-01  | 2025-10-15  |     12 |
| QQP_2025/10-2025_02.csv | 186.7 | utf-8-sig      | True  |          595,063 |          595,062 | yyyy/mm/dd      | 2025-10-16  | 2025-10-31  |     13 |
| QQP_2025/11-2025_01.csv | 153.8 | utf-8-sig      | True  |          486,183 |          486,182 | yyyy/mm/dd      | 2025-11-03  | 2025-11-15  |     11 |
| QQP_2025/11-2025_02.csv | 138.9 | utf-8-sig      | True  |          437,364 |          437,363 | yyyy/mm/dd      | 2025-11-16  | 2025-11-29  |     13 |
| QQP_2025/12-2025_01.csv | 151.9 | utf-8-sig      | True  |          481,459 |          481,458 | yyyy/mm/dd      | 2025-12-01  | 2025-12-15  |     12 |
| QQP_2025/12-2025_02.csv | 136.7 | utf-8-sig      | True  |          434,833 |          434,832 | yyyy/mm/dd      | 2025-12-16  | 2025-12-31  |     13 |
| QQP_2026/01-2026_Q1.csv | 156.1 | utf-8-sig      | True  |          496,727 |          496,726 | yyyy/mm/dd      | 2026-01-02  | 2026-01-15  |     11 |
| QQP_2026/01-2026_Q2.csv | 198.0 | utf-8-sig      | True  |          630,372 |          630,371 | yyyy/mm/dd      | 2026-01-16  | 2026-01-30  |     11 |
| QQP_2026/02-2026_Q1.csv | 156.1 | utf-8-sig      | True  |          496,646 |          496,645 | yyyy/mm/dd      | 2026-02-03  | 2026-02-13  |      9 |
| QQP_2026/02-2026_Q2.csv | 172.4 | utf-8-sig      | True  |          547,812 |          547,811 | yyyy/mm/dd      | 2026-02-16  | 2026-02-27  |     10 |
| QQP_2026/03-2026_Q1.csv | 175.8 | utf-8-sig      | True  |          558,147 |          558,146 | yyyy/mm/dd      | 2026-03-02  | 2026-03-13  |     11 |
| QQP_2026/03-2026_Q2.csv | 190.1 | utf-8-sig      | True  |          606,523 |          606,522 | yyyy/mm/dd      | 2026-03-17  | 2026-03-31  |     11 |
| QQP_2026/04-2026_Q1.csv | 151.4 | utf-8-sig      | True  |          480,843 |          480,842 | yyyy/mm/dd      | 2026-04-01  | 2026-04-15  |     10 |
| QQP_2026/04-2026_Q2.csv | 187.4 | utf-8-sig      | True  |          597,635 |          597,634 | yyyy/mm/dd      | 2026-04-16  | 2026-04-30  |     11 |
| QQP_2026/05-2026_Q1.csv | 149.7 | cp1252         | False |          479,994 |          479,993 | dd/mm/yyyy      | 2026-05-01  | 2026-05-15  |     15 |
| QQP_2026/05-2026_Q2.csv | 164.3 | cp1252         | False |          527,090 |          527,089 | dd/mm/yyyy      | 2026-05-16  | 2026-05-29  |     14 |

## 3. Esquema observado

Las 15 columnas son idénticas y en el mismo orden en todos los archivos.

| columna          |   distintos |   vacios |
|:-----------------|------------:|---------:|
| cadena_comercial |      264.00 |     0.00 |
| catalogo         |       12.00 |     0.00 |
| categoria        |       56.00 |     0.00 |
| coordenadas      |    2,228.00 |   nan    |
| direccion        |    3,224.00 |     0.00 |
| estado           |       37.00 |     0.00 |
| fecha_registro   |      630.00 |     0.00 |
| giro             |       18.00 |     0.00 |
| latitud          |      nan    |   791.00 |
| longitud         |      nan    |   791.00 |
| marca            |    1,382.00 |     0.00 |
| municipio        |       73.00 |     0.00 |
| nombre_comercial |    2,422.00 |     0.00 |
| precio           |   88,404.00 |     0.00 |
| presentacion     |    5,537.00 |     0.00 |
| producto         |      821.00 |     0.00 |

## 4. Precio

|   no_convertible |   negativos |   ceros |   minimo |   p01 |   mediana |       p99 |       maximo |
|-----------------:|------------:|--------:|---------:|------:|----------:|----------:|-------------:|
|             0.00 |        0.00 |    0.00 |     1.15 |  7.00 |     61.00 | 12,599.00 | 3,041,791.00 |

Diez precios más altos:

| producto         | presentacion                                                                   | marca   | catalogo          |       precio | cadena_comercial        | archivo                 |
|:-----------------|:-------------------------------------------------------------------------------|:--------|:------------------|-------------:|:------------------------|:------------------------|
| Prevefem Complex | Caja con 30 Tabletas                                                           | S/m     | Medicamentos      | 3,041,791.00 | Hipermercado Soriana    | QQP_2024/12-2024_01.csv |
| Pantallas        | 100 Qned 86 As. 100 Plgs. Qned. Puerto USB. Smart TV.                          | Lg      | Electrodomesticos |   107,691.00 | Liverpool               | QQP_2026/05-2026_Q2.csv |
| Pantallas        | 100 Qned 86 As. 100 Plgs. Qned. Puerto USB. Smart TV.                          | Lg      | Electrodomesticos |   107,691.00 | Liverpool               | QQP_2026/05-2026_Q2.csv |
| Pantallas        | 100 Qned 86 As. 100 Plgs. Qned. Puerto USB. Smart TV.                          | Lg      | Electrodomesticos |   107,691.00 | Liverpool               | QQP_2026/05-2026_Q2.csv |
| Lavadoras        | Lma 78113 Cbab0 o Cbab00 o Cbab01. 18 Kg. Agitador. Centrifugado. Color Blanco | Mabe    | Electrodomesticos |    99,999.00 | Elektra                 | QQP_2025/07-2025_01.csv |
| Pantallas        | Un 98du9000f. 98 Plgs. Crystal. Puerto USB. Smart TV.                          | Samsung | Electrodomesticos |    85,713.00 | Sears Roebuck de México | QQP_2026/05-2026_Q2.csv |
| Pantallas        | Oled 77 C5 Psa. 77 Plgs. Oled. Puerto Usb. Smart Tv.                           | Lg      | Electrodomesticos |    84,999.00 | Liverpool               | QQP_2026/01-2026_Q2.csv |
| Pantallas        | Oled 77 C5 Psa. 77 Plgs. Oled. Puerto Usb. Smart Tv.                           | Lg      | Electrodomesticos |    84,999.00 | Sears Roebuck de Mexico | QQP_2026/02-2026_Q2.csv |
| Pantallas        | Oled 77 C5 Psa. 77 Plgs. Oled. Puerto Usb. Smart Tv.                           | Lg      | Electrodomesticos |    84,999.00 | Sears Roebuck de Mexico | QQP_2026/03-2026_Q1.csv |
| Pantallas        | Oled 77 C5 Psa. 77 Plgs. Oled. Puerto Usb. Smart Tv.                           | Lg      | Electrodomesticos |    84,999.00 | Liverpool               | QQP_2026/03-2026_Q1.csv |

## 5. Coordenadas

|   sin_coordenadas |   latitud_fuera_mexico |   longitud_fuera_mexico |
|------------------:|-----------------------:|------------------------:|
|               791 |                     46 |                      16 |

## 6. Duplicados y caracteres perdidos por archivo

Grano candidato: producto + presentación + marca + nombre comercial + dirección + estado + municipio + fecha.

| archivo                 |   filas |   dup_exactos |   dup_grano |   grupos_multicatalogo |   grupos_precio_en_conflicto |   filas_con_caracter_perdido |
|:------------------------|--------:|--------------:|------------:|-----------------------:|-----------------------------:|-----------------------------:|
| QQP_2024/01-2024_01.csv | 560,729 |             0 |      10,484 |                 10,332 |                          142 |                            0 |
| QQP_2024/01-2024_02.csv | 710,526 |             0 |      13,031 |                 12,762 |                          263 |                            0 |
| QQP_2024/02-2024_01.csv | 596,333 |             0 |      11,590 |                 11,188 |                          398 |                            0 |
| QQP_2024/02-2024_02.csv | 624,758 |             0 |      11,844 |                 11,560 |                          260 |                            0 |
| QQP_2024/03-2024_01.csv | 676,518 |             0 |      12,909 |                 12,728 |                          179 |                            0 |
| QQP_2024/03-2024_02.csv | 458,899 |             0 |       8,851 |                  8,637 |                          201 |                            0 |
| QQP_2024/04-2024_01.csv | 637,339 |             0 |      12,398 |                 12,027 |                          357 |                            0 |
| QQP_2024/04-2024_02.csv | 678,352 |             0 |      12,191 |                 11,937 |                          240 |                            0 |
| QQP_2024/05-2024_01.csv | 573,583 |             0 |      11,243 |                 10,924 |                          317 |                            0 |
| QQP_2024/05-2024_02.csv | 699,079 |             0 |      13,245 |                 12,998 |                          235 |                            0 |
| QQP_2024/06-2024_01.csv | 592,207 |             0 |      11,234 |                 10,945 |                          263 |                            0 |
| QQP_2024/06-2024_02.csv | 614,525 |             0 |      11,032 |                 10,557 |                          433 |                            0 |
| QQP_2024/07-2024_01.csv | 693,722 |             0 |      12,328 |                 11,837 |                          429 |                            0 |
| QQP_2024/07-2024_02.csv | 781,174 |             0 |      14,168 |                 13,286 |                          817 |                            0 |
| QQP_2024/08-2024_01.csv | 735,696 |             0 |      12,779 |                 12,093 |                          650 |                            0 |
| QQP_2024/08-2024_02.csv | 700,637 |             0 |      12,806 |                 12,437 |                          352 |                            0 |
| QQP_2024/09-2024_01.csv | 561,263 |             0 |      10,587 |                 10,464 |                          118 |                            0 |
| QQP_2024/09-2024_02.csv | 549,215 |             0 |      10,329 |                 10,129 |                          188 |                            0 |
| QQP_2024/10-2024_01.csv | 564,006 |             0 |      10,768 |                 10,471 |                          280 |                            0 |
| QQP_2024/10-2024_02.csv | 656,833 |             0 |      12,603 |                 11,955 |                          618 |                            0 |
| QQP_2024/11-2024_01.csv | 586,209 |             0 |      10,619 |                 10,509 |                          108 |                            0 |
| QQP_2024/11-2024_02.csv | 591,278 |             0 |       9,799 |                  9,312 |                          460 |                            0 |
| QQP_2024/12-2024_01.csv | 549,252 |             0 |      10,839 |                 10,705 |                          125 |                            0 |
| QQP_2024/12-2024_02.csv | 497,086 |             0 |      10,984 |                 10,801 |                          180 |                            0 |
| QQP_2025/01-2025_01.csv | 547,782 |             0 |      11,090 |                 11,022 |                           67 |                            0 |
| QQP_2025/01-2025_02.csv | 696,182 |             0 |      13,558 |                 13,311 |                          214 |                            0 |
| QQP_2025/02-2025_01.csv | 536,078 |             0 |      10,693 |                 10,393 |                          282 |                            0 |
| QQP_2025/02-2025_02.csv | 606,776 |             0 |      11,948 |                 11,604 |                          311 |                            0 |
| QQP_2025/03-2025_01.csv | 587,058 |             0 |      11,687 |                 11,362 |                          315 |                            0 |
| QQP_2025/03-2025_02.csv | 594,320 |             0 |      11,259 |                 11,016 |                          225 |                            0 |
| QQP_2025/04-2025_01.csv | 594,887 |             0 |      11,655 |                 11,304 |                          339 |                            0 |
| QQP_2025/04-2025_02.csv | 430,973 |             0 |       8,828 |                  8,573 |                          222 |                            0 |
| QQP_2025/05-2025_01.csv | 437,833 |             0 |       9,559 |                  9,164 |                          384 |                            0 |
| QQP_2025/05-2025_02.csv | 526,969 |             0 |      11,121 |                 10,577 |                          522 |                            0 |
| QQP_2025/06-2025_01.csv | 534,834 |             0 |      10,810 |                 10,405 |                          353 |                            0 |
| QQP_2025/06-2025_02.csv | 573,713 |             0 |      11,415 |                 10,948 |                          421 |                            0 |
| QQP_2025/07-2025_01.csv | 664,946 |             0 |      12,641 |                 11,895 |                          711 |                            0 |
| QQP_2025/07-2025_02.csv | 715,246 |             0 |      13,882 |                 13,040 |                          807 |                            0 |
| QQP_2025/08-2025_01.csv | 692,569 |             0 |      13,330 |                 12,422 |                          847 |                            0 |
| QQP_2025/08-2025_02.csv | 489,955 |             0 |       8,968 |                  8,550 |                          397 |                            0 |
| QQP_2025/09-2025_01.csv | 542,922 |             0 |      11,782 |                 10,915 |                          860 |                            0 |
| QQP_2025/09-2025_02.csv | 534,092 |             0 |      10,473 |                 10,003 |                          457 |                            0 |
| QQP_2025/10-2025_01.csv | 528,492 |             0 |      10,502 |                 10,158 |                          329 |                            0 |
| QQP_2025/10-2025_02.csv | 595,062 |             0 |      11,325 |                 10,745 |                          538 |                            0 |
| QQP_2025/11-2025_01.csv | 486,182 |             0 |       8,447 |                  8,081 |                          366 |                            0 |
| QQP_2025/11-2025_02.csv | 437,363 |             0 |       7,513 |                  7,211 |                          295 |                            0 |
| QQP_2025/12-2025_01.csv | 481,458 |             0 |       9,883 |                  9,463 |                          403 |                            0 |
| QQP_2025/12-2025_02.csv | 434,832 |             0 |       9,086 |                  8,827 |                          252 |                            0 |
| QQP_2026/01-2026_Q1.csv | 496,726 |             0 |       9,847 |                  9,624 |                          221 |                            0 |
| QQP_2026/01-2026_Q2.csv | 630,371 |             0 |      12,203 |                 11,740 |                          433 |                            0 |
| QQP_2026/02-2026_Q1.csv | 496,645 |             0 |       9,498 |                  9,262 |                          232 |                            0 |
| QQP_2026/02-2026_Q2.csv | 547,811 |            59 |       9,308 |                  8,850 |                          371 |                            0 |
| QQP_2026/03-2026_Q1.csv | 558,146 |             8 |       9,188 |                  8,832 |                          341 |                            0 |
| QQP_2026/03-2026_Q2.csv | 606,522 |            31 |      10,093 |                  9,757 |                          292 |                            0 |
| QQP_2026/04-2026_Q1.csv | 480,842 |            12 |       8,804 |                  8,571 |                          215 |                            0 |
| QQP_2026/04-2026_Q2.csv | 597,634 |            59 |      10,606 |                  9,983 |                          529 |                            0 |
| QQP_2026/05-2026_Q1.csv | 479,993 |             8 |       8,401 |                  8,091 |                          296 |                            0 |
| QQP_2026/05-2026_Q2.csv | 527,089 |            34 |       8,776 |                  8,360 |                          356 |                       12,378 |

Combinaciones de catálogo en grupos duplicados:

| combinacion                          |   grupos |
|:-------------------------------------|---------:|
| Basicos + Pacic                      |  340,372 |
| Frutas y Legumbres + Pacic           |  265,077 |
| Electrodomesticos + Juguetes         |    4,295 |
| Frutas y Legumbres + Mercados        |    2,593 |
| Electrodomesticos + Utiles Escolares |    1,392 |
| Basicos + Especial                   |      862 |
| Mercados + Pescados y Mariscos       |       37 |
| Mercados + Pacic                     |       13 |
| Basicos + Mercados                   |       12 |

## 7. Variantes de texto

### Estado

| estado_normalizado   | estado_original     |     filas | primer_archivo          | ultimo_archivo          |
|:---------------------|:--------------------|----------:|:------------------------|:------------------------|
| AGUASCALIENTES       | Aguascalientes      |   722,669 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| BAJA CALIFORNIA      | Baja California     |   642,772 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| BAJA CALIFORNIA SUR  | Baja California Sur |   700,739 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| CAMPECHE             | Campeche            |   753,548 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| CHIAPAS              | Chiapas             |   644,334 | QQP_2024/01-2024_02.csv | QQP_2026/05-2026_Q2.csv |
| CHIHUAHUA            | Chihuahua           | 1,047,662 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| CIUDAD DE MEXICO     | Ciudad de Mexico    | 6,137,934 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| CIUDAD DE MEXICO     | Ciudad de México    | 1,394,570 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| COAHUILA             | Coahuila            |   651,228 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| DURANGO              | Durango             |   653,475 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| ESTADO DE MEXICO     | Estado de Mexico    | 3,656,006 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| ESTADO DE MEXICO     | Estado de México    |   834,222 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| GUANAJUATO           | Guanajuato          | 1,634,155 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| GUERRERO             | Guerrero            |   426,238 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| HIDALGO              | Hidalgo             |   105,359 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q1.csv |
| JALISCO              | Jalisco             | 1,597,905 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| MICHOACAN            | Michoacan           |   528,782 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| MICHOACAN            | Michoacán           |   120,909 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| MORELOS              | Morelos             |   614,921 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| NUEVO LEON           | Nuevo Leon          |   844,369 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| NUEVO LEON           | Nuevo León          |   188,712 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| OAXACA               | Oaxaca              |   638,140 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| PUEBLA               | Puebla              |   731,551 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| QUERETARO            | Queretaro           |   646,145 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| QUERETARO            | Querétaro           |   103,111 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| QUINTANA ROO         | Quintana Roo        |   990,781 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| SAN LUIS POTOSI      | San Luis Potosi     |   560,173 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| SAN LUIS POTOSI      | San Luis Potosí     |   127,879 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| SINALOA              | Sinaloa             |   139,180 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| SONORA               | Sonora              |   504,714 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| TABASCO              | Tabasco             | 1,298,392 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| TAMAULIPAS           | Tamaulipas          |   553,298 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| TLAXCALA             | Tlaxcala            |   680,929 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| VERACRUZ             | Veracruz            |   737,153 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |
| YUCATAN              | Yucatan             |   754,883 | QQP_2024/01-2024_01.csv | QQP_2025/11-2025_02.csv |
| YUCATAN              | Yucatán             |   182,794 | QQP_2025/12-2025_01.csv | QQP_2026/05-2026_Q2.csv |
| ZACATECAS            | Zacatecas           | 1,031,890 | QQP_2024/01-2024_01.csv | QQP_2026/05-2026_Q2.csv |

### Giro

| giro                                  |      filas |   cadenas |   archivos |
|:--------------------------------------|-----------:|----------:|-----------:|
| Supermercado / Tienda de Autoservicio | 26,411,263 |        43 |         58 |
| Farmacias                             |  3,666,396 |        46 |         58 |
| Tienda de Electrodomésticos           |    897,821 |        18 |         58 |
| Mercados                              |    606,214 |        11 |         58 |
| Tienda de Conveniencia                |    521,127 |         9 |         58 |
| Tienda Departamentales                |    488,574 |         5 |         54 |
| Papelerías                            |    426,908 |        39 |         33 |
| Central de Abasto                     |    325,591 |         2 |         58 |
| Tortillerías                          |     64,948 |         1 |         58 |
| Pescaderías                           |     38,452 |        34 |         58 |
| Jugueterías                           |     36,455 |        12 |         32 |
| Uniformes                             |     29,739 |        29 |         34 |
| Tiendas Departamentales               |     28,311 |         5 |          4 |
| Panaderías                            |     22,143 |         1 |         58 |
| Papeler?as                            |     11,325 |        29 |          1 |
| Vinaterías                            |      4,577 |         8 |          9 |
| Zapaterías                            |      1,620 |         9 |          9 |
| Jugueter?as                           |         58 |         1 |          1 |

### Marca genérica

| marca   |   anio |     filas |
|:--------|-------:|----------:|
| S/m     |  2,024 | 4,917,060 |
| S/M     |  2,025 |   331,366 |
| S/m     |  2,025 | 4,294,517 |
| S/M     |  2,026 | 1,867,727 |

## 8. Cobertura

### Catálogo por año

| catalogo            |   anio |     filas |   productos |
|:--------------------|-------:|----------:|------------:|
| Basicos             |  2,024 | 7,755,715 |         202 |
| Basicos             |  2,025 | 6,888,079 |         204 |
| Basicos             |  2,026 | 2,916,960 |         203 |
| Electrodomesticos   |  2,024 | 1,222,507 |          34 |
| Electrodomesticos   |  2,025 |   833,885 |          33 |
| Electrodomesticos   |  2,026 |   305,403 |          34 |
| Especial            |  2,025 |     5,189 |          10 |
| Especial            |  2,026 |    41,178 |          14 |
| Frutas y Legumbres  |  2,024 |   813,287 |          62 |
| Frutas y Legumbres  |  2,025 |   737,179 |          62 |
| Frutas y Legumbres  |  2,026 |   312,233 |          62 |
| Juguetes            |  2,024 |   204,197 |          16 |
| Juguetes            |  2,025 |   141,186 |          16 |
| Juguetes            |  2,026 |     4,109 |          16 |
| Medicamentos        |  2,024 | 3,342,835 |         376 |
| Medicamentos        |  2,025 | 3,372,638 |         383 |
| Medicamentos        |  2,026 | 1,360,813 |         381 |
| Mercados            |  2,024 |   294,405 |         106 |
| Mercados            |  2,025 |   210,338 |         105 |
| Mercados            |  2,026 |   104,707 |         104 |
| Navideños           |  2,024 |    35,607 |          18 |
| Navideños           |  2,025 |    29,259 |          19 |
| Navideños           |  2,026 |         9 |           2 |
| Pacic               |  2,024 |   646,909 |          34 |
| Pacic               |  2,025 |   627,234 |          34 |
| Pacic               |  2,026 |   239,626 |          25 |
| Pescados y Mariscos |  2,024 |   117,871 |          42 |
| Pescados y Mariscos |  2,025 |   108,510 |          42 |
| Pescados y Mariscos |  2,026 |    52,233 |          44 |
| Tenis               |  2,024 |     1,780 |           1 |
| Tenis               |  2,025 |     1,414 |           1 |
| Utiles Escolares    |  2,024 |   454,106 |          46 |
| Utiles Escolares    |  2,025 |   315,613 |          47 |
| Utiles Escolares    |  2,026 |    84,508 |          35 |

### Estados

| estado              |   municipios |   semanas |   tiendas |     filas |
|:--------------------|-------------:|----------:|----------:|----------:|
| AGUASCALIENTES      |            1 |       126 |        53 |   722,669 |
| BAJA CALIFORNIA     |            1 |       126 |        50 |   642,772 |
| BAJA CALIFORNIA SUR |            1 |       125 |        62 |   700,739 |
| CAMPECHE            |            1 |       125 |        58 |   753,548 |
| CHIAPAS             |            1 |       122 |        70 |   644,334 |
| CHIHUAHUA           |            2 |       126 |        81 | 1,047,662 |
| CIUDAD DE MEXICO    |           13 |       126 |       335 | 7,532,504 |
| COAHUILA            |            1 |       126 |        43 |   651,228 |
| DURANGO             |            1 |       126 |        63 |   653,475 |
| ESTADO DE MEXICO    |           17 |       126 |       316 | 4,490,228 |
| GUANAJUATO          |            1 |       126 |        91 | 1,634,155 |
| GUERRERO            |            1 |       123 |        40 |   426,238 |
| HIDALGO             |            2 |        70 |        40 |   105,359 |
| JALISCO             |            4 |       126 |       110 | 1,597,905 |
| MICHOACAN           |            1 |       123 |        58 |   649,691 |
| MORELOS             |            1 |       126 |        61 |   614,921 |
| NUEVO LEON          |            4 |       126 |        93 | 1,033,081 |
| OAXACA              |            3 |       125 |        57 |   638,140 |
| PUEBLA              |            1 |       126 |        49 |   731,551 |
| QUERETARO           |            1 |       126 |        68 |   749,256 |
| QUINTANA ROO        |            2 |       124 |        99 |   990,781 |
| SAN LUIS POTOSI     |            1 |       126 |        57 |   688,052 |
| SINALOA             |            1 |       116 |        27 |   139,180 |
| SONORA              |            1 |       122 |        52 |   504,714 |
| TABASCO             |            1 |       126 |        78 | 1,298,392 |
| TAMAULIPAS          |            3 |       126 |        86 |   553,298 |
| TLAXCALA            |            2 |       126 |        55 |   680,929 |
| VERACRUZ            |            3 |       124 |        59 |   737,153 |
| YUCATAN             |            1 |       126 |        79 |   937,677 |
| ZACATECAS           |            2 |       126 |        71 | 1,031,890 |

### Cadenas con más de 50 mil registros en catálogo Básicos

| cadena                     |   estados |   municipios |   tiendas |   semanas |   productos |     filas |
|:---------------------------|----------:|-------------:|----------:|----------:|------------:|----------:|
| Wal-mart                   |        30 |           48 |        64 |       126 |         201 | 3,395,449 |
| Hipermercado Soriana       |        27 |           44 |        54 |       126 |         203 | 2,912,210 |
| Bodega Aurrera             |        26 |           45 |        62 |       126 |         199 | 2,306,982 |
| Chedraui                   |        21 |           28 |        29 |       126 |         201 | 1,565,276 |
| Mega Soriana               |        12 |           23 |        24 |       126 |         200 | 1,358,646 |
| Wal-mart Express           |         8 |           18 |        30 |       126 |         197 | 1,096,980 |
| Mercado Soriana            |         6 |           11 |        13 |       126 |         191 |   472,643 |
| La Comer                   |         4 |            8 |         8 |       126 |         198 |   432,910 |
| Soriana Super              |         8 |            9 |         9 |       126 |         194 |   391,059 |
| Farmacia Guadalajara       |        20 |           23 |        25 |       125 |         154 |   376,424 |
| Ley                        |         7 |            7 |         8 |       126 |         189 |   373,754 |
| H.e.b.                     |         5 |            7 |         7 |       126 |         193 |   292,395 |
| Superissste                |         3 |           10 |        14 |        93 |         152 |   268,733 |
| Oxxo                       |        24 |           29 |        36 |       123 |         119 |   265,888 |
| Fresko la Comer            |         4 |            4 |         4 |       124 |         198 |   212,036 |
| Chedraui Selecto           |         3 |            4 |         4 |       126 |         195 |   204,627 |
| Sumesa                     |         2 |            3 |         4 |       124 |         192 |   168,472 |
| S Mart                     |         2 |            3 |         3 |       124 |         179 |   136,874 |
| Bodega Aurrera Express     |         3 |            7 |         8 |       123 |         122 |   132,588 |
| Super Chedraui             |         1 |            3 |         3 |       125 |         192 |   130,875 |
| Minisuper                  |         7 |            8 |        10 |       126 |         159 |   112,362 |
| City Market                |         2 |            2 |         2 |       117 |         188 |    93,002 |
| Soriana Express            |         2 |            2 |         2 |       122 |         165 |    90,747 |
| Tortillerias Tradicionales |        30 |           65 |       773 |       126 |         117 |    64,886 |
| Super Aki                  |         1 |            2 |         2 |       117 |         170 |    62,102 |
| Alsuper                    |         2 |            2 |         2 |       115 |         174 |    60,866 |
| Alsuper Fresh Market       |         1 |            1 |         1 |       103 |         182 |    60,732 |
| Benavides                  |         7 |            7 |         8 |       119 |          62 |    53,351 |

### Frecuencia de levantamiento (días con registro por tienda y quincena, cadenas de referencia)

|   dias_con_registro |   tienda_quincenas |
|--------------------:|-------------------:|
|                   1 |              1,006 |
|                   2 |              7,465 |
|                   3 |              1,891 |
|                   4 |                298 |
|                   5 |                113 |
|                   6 |                 10 |
|                   7 |                  1 |

## 9. Viabilidad de la canasta

Candidatos: `data/mappings/canasta_candidatos_v0.csv`. Cadenas de referencia: Wal-mart, Bodega Aurrera, Hipermercado Soriana, Chedraui.

### SKU (marca fija) con mayor presencia mínima entre cadenas, por producto

| producto                | presentacion                                           | marca           |   cadenas |   presencia_min_pct |   presencia_prom_pct |
|:------------------------|:-------------------------------------------------------|:----------------|----------:|--------------------:|---------------------:|
| FRIJOL                  | BOLSA 900 GR. PERUANO                                  | VERDE VALLE     |         4 |                3.30 |                48.90 |
| ARROZ                   | BOLSA 900 GR. SUPER EXTRA. VERDE                       | SCHETTINO       |         4 |                9.40 |                51.30 |
| HUEVO                   | PAQUETE C/12 BLANCO                                    | SAN JUAN        |         4 |               63.00 |                70.40 |
| CARNE RES               | 1 KG. GRANEL. PANZA O MENUDO. CRUDOS                   | S/M             |         4 |               69.70 |                75.00 |
| HARINA DE MAÍZ          | PAQUETE 1 KG.                                          | MASECA          |         4 |               72.00 |                79.80 |
| AZÚCAR                  | BOLSA PLÁSTICO 2 KG. ESTÁNDAR O MORENA                 | ZULKA           |         4 |               73.60 |                82.30 |
| PAPEL HIGIÉNICO         | PAQUETE 4 ROLLOS. XXL HOJAS DOBLES                     | REGIO. LUXURY   |         4 |               73.70 |                77.60 |
| ATÚN                    | BOLSA 78 GR. ALETA AMARILLA. EN TROZOS EN AGUA         | DOLORES         |         4 |               76.50 |                81.10 |
| CARNE POLLO             | 1 KG. GRANEL. PIERNA O PIERNA BATE                     | S/M             |         4 |               77.40 |                81.50 |
| PASTA PARA SOPA         | PAQUETE 200 GR. SPAGHETTI NO. 5                        | BARILLA         |         4 |               78.00 |                87.00 |
| DETERGENTE P/ROPA       | BOLSA 1 KG. POLVO                                      | BLANCA NIEVES   |         4 |               82.10 |                84.30 |
| LIMÓN                   | 1 KG. GRANEL. AGRIO SIN SEMILLA O PERSA                | S/M             |         4 |               83.70 |                91.00 |
| JABÓN DE PASTA          | BARRA 400 GR. CON ENVOLTURA. (ROSA)                    | ZOTE            |         4 |               84.10 |                86.90 |
| TORTILLA DE MAÍZ        | 1 KG. GRANEL                                           | S/M             |         4 |               87.20 |                91.00 |
| ACEITE                  | BOTELLA 850 ML. VEGETAL. SABOR MANTEQUILLA             | SABROSANO       |         4 |               91.30 |                93.30 |
| PAPA                    | 1 KG. GRANEL. ALFA/BLANCA                              | S/M             |         4 |               91.50 |                94.90 |
| JITOMATE                | 1 KG. GRANEL. SALADETTE/HUAJE O TOMATE SALADETTE/HUAJE | S/M             |         4 |               92.00 |                94.90 |
| PLÁTANO                 | 1 KG. GRANEL. TABASCO/CHIAPAS/ROATÁN/PORTALIMÓN        | S/M             |         4 |               92.80 |                94.70 |
| CEBOLLA                 | 1 KG. GRANEL. BLANCA SIN RABO                          | S/M             |         4 |               93.20 |                95.40 |
| LECHE ULTRAPASTEURIZADA | CAJA 1 LT. PARCIALMENTE DESCREMADA. AZUL               | ALPURA. CLÁSICA |         4 |               95.00 |                96.50 |

### % de celdas con la canasta completa

| nivel                                            |   Bodega Aurrera |   Chedraui |   Hipermercado Soriana |   Wal-mart |
|:-------------------------------------------------|-----------------:|-----------:|-----------------------:|-----------:|
| A. SKU exacto · municipio×quincena               |              0.0 |        0.6 |                   19.8 |        4.0 |
| A. SKU exacto · municipio×semana                 |              0.0 |        0.0 |                    6.9 |        1.4 |
| B. Genérico · municipio×mes                      |             79.2 |       84.3 |                   87.5 |       85.4 |
| B. Genérico · municipio×quincena                 |             69.6 |       73.2 |                   79.7 |       77.6 |
| B. Genérico · municipio×semana                   |             52.1 |       55.6 |                   65.2 |       60.7 |
| B. Genérico · municipio×semana (ventana 14 días) |             68.0 |       71.6 |                   78.3 |       76.1 |
