# Selección de artículos de la canasta

_Generado por `python -m src.analysis.seleccion_canasta` el 2026-09-12 19:05 · modo `completo`. Decisión: D-022 en `docs/decisiones.md`._

## 1. Completitud por composición de canasta

Celdas: cadena de referencia × municipio × semana con ventana completa. Una celda está completa si cada
artículo tiene al menos una observación comparable y no atípica en la ventana de 14 días.

| composicion                                       |   articulos |   celdas_completas_pct |   wal_mart |   bodega_aurrera |   soriana |   chedraui |   municipio_semanas_comparables_pct |   municipios_con_comparacion |
|:--------------------------------------------------|------------:|-----------------------:|-----------:|-----------------:|----------:|-----------:|------------------------------------:|-----------------------------:|
| v0: 20 artículos                                  |          20 |                   50.7 |       64.2 |             47.3 |      54.2 |       27.6 |                                50.6 |                           48 |
| v0 con pollo entero (20)                          |          20 |                   56.6 |       67.9 |             53.9 |      65.1 |       28.5 |                                57.2 |                           49 |
| ... sin harina de maíz (19)                       |          19 |                   62.5 |       77.6 |             58.7 |      69.0 |       32.2 |                                64.3 |                           49 |
| ... con milanesa en lugar de molida especial (19) |          19 |                   72.7 |       79.8 |             56.5 |      80.5 |       74.1 |                                77.1 |                           49 |
| ... sin limpieza, con molida especial (16)        |          16 |                   69.7 |       85.2 |             69.2 |      73.9 |       37.3 |                                71.4 |                           50 |
| v1: sin limpieza, con milanesa (16)               |          16 |                   81.0 |       87.9 |             66.6 |      87.2 |       82.1 |                                85.2 |                           51 |
| v1 sin res (15)                                   |          15 |                   89.7 |       92.5 |             84.6 |      90.1 |       92.4 |                                90.4 |                           52 |

## 2. Cobertura por definición de artículo (% de celdas de cada cadena)

| articulo_id           |   BODEGA AURRERA |   CHEDRAUI |   HIPERMERCADO SORIANA |   WAL-MART |   minima |
|:----------------------|-----------------:|-----------:|-----------------------:|-----------:|---------:|
| RES_FALDA             |             28.4 |       80.8 |                   76.8 |       86.8 |     28.4 |
| RES_PARA_ASAR         |             69.5 |       28.8 |                   99.5 |       90.3 |     28.8 |
| RES_MOLIDA            |             75.7 |       39.1 |                   79.2 |       89.8 |     39.1 |
| POLLO_PIERNA          |             73.2 |       79.6 |                   75.8 |       86.4 |     73.2 |
| RES_MILANESA          |             74.6 |       85.8 |                   94.2 |       93.5 |     74.6 |
| HARINA_MAIZ           |             77.4 |       78.6 |                   87.4 |       80.0 |     77.4 |
| LIMON_CON_SEMILLA     |             87.4 |       79.3 |                   98.4 |       91.6 |     79.3 |
| RES_MOLIDA_CUALQUIERA |             80.0 |       90.1 |                   92.3 |       92.5 |     80.0 |
| RES_BISTEC            |             80.6 |       99.5 |                   96.5 |       94.7 |     80.6 |
| JABON_LAVANDERIA      |             81.3 |       89.3 |                   89.2 |       88.7 |     81.3 |
| PAPEL_HIGIENICO       |             81.6 |       90.3 |                   92.8 |       89.0 |     81.6 |
| DETERGENTE_POLVO      |             81.8 |       89.9 |                   89.2 |       88.4 |     81.8 |
| POLLO_PECHUGA         |             85.5 |       91.1 |                   91.9 |       93.0 |     85.5 |
| LIMON_SIN_SEMILLA     |             90.5 |       99.0 |                   95.3 |       97.2 |     90.5 |
| PLATANO_TABASCO       |             94.6 |       95.5 |                   98.1 |       97.6 |     94.6 |
| POLLO_PIERNA_O_MUSLO  |             95.4 |       97.8 |                   98.7 |       98.6 |     95.4 |
| TORTILLA_MAIZ         |             96.7 |       99.6 |                   99.9 |       99.8 |     96.7 |
| JITOMATE_SALADETTE    |             96.8 |       99.5 |                   99.3 |       99.0 |     96.8 |
| POLLO_ENTERO          |             96.9 |       99.4 |                   99.7 |       99.3 |     96.9 |
| PAPA_BLANCA           |             97.2 |       99.2 |                   99.3 |       99.6 |     97.2 |
| ARROZ_SUPER_EXTRA     |             99.9 |       99.9 |                   97.3 |      100.0 |     97.3 |
| CEBOLLA_BLANCA        |             97.4 |       99.7 |                   99.4 |       99.8 |     97.4 |
| ACEITE_VEGETAL        |             99.0 |       99.8 |                   99.9 |       99.5 |     99.0 |
| HUEVO_BLANCO          |             99.4 |       99.0 |                   99.8 |       99.3 |     99.0 |
| AZUCAR_ESTANDAR       |             99.8 |       99.6 |                   99.7 |       99.9 |     99.6 |
| LECHE_ENTERA          |             99.7 |       99.6 |                   99.8 |       99.9 |     99.6 |
| ATUN_AGUA             |             99.8 |       99.9 |                   99.6 |      100.0 |     99.6 |
| PASTA_SOPA            |             99.8 |       99.9 |                   99.9 |       99.7 |     99.7 |
| FRIJOL_NEGRO          |             99.8 |       99.8 |                   99.8 |      100.0 |     99.8 |

## 3. Mediana de precio unitario por cadena

Una razón máximo/mínimo alta indica que la definición puede mezclar calidades o cortes distintos.

| articulo_id           |   BODEGA AURRERA |   CHEDRAUI |   HIPERMERCADO SORIANA |   WAL-MART |   max/min |
|:----------------------|-----------------:|-----------:|-----------------------:|-----------:|----------:|
| PASTA_SOPA            |            47.50 |      52.50 |                  23.00 |      50.00 |      2.28 |
| LIMON_SIN_SEMILLA     |            38.90 |      23.00 |                  33.90 |      39.90 |      1.73 |
| POLLO_PIERNA_O_MUSLO  |            79.00 |      59.90 |                  59.90 |      89.00 |      1.49 |
| RES_BISTEC            |           174.00 |     138.00 |                 195.90 |     179.00 |      1.42 |
| ARROZ_SUPER_EXTRA     |            28.67 |      26.11 |                  35.83 |      26.67 |      1.37 |
| JITOMATE_SALADETTE    |            23.90 |      22.00 |                  29.90 |      29.90 |      1.36 |
| LIMON_CON_SEMILLA     |            36.90 |      36.50 |                  29.60 |      39.90 |      1.35 |
| POLLO_PIERNA          |            84.00 |      68.90 |                  74.90 |      92.00 |      1.34 |
| CEBOLLA_BLANCA        |            26.90 |      23.00 |                  27.80 |      29.90 |      1.30 |
| RES_PARA_ASAR         |           200.00 |     199.00 |                 159.00 |     205.00 |      1.29 |
| HARINA_MAIZ           |            20.50 |      19.50 |                  20.50 |      24.00 |      1.23 |
| PAPEL_HIGIENICO       |             4.34 |       5.00 |                   5.23 |       4.84 |      1.21 |
| FRIJOL_NEGRO          |            49.61 |      49.11 |                  55.44 |      46.31 |      1.20 |
| RES_MOLIDA_CUALQUIERA |           142.00 |     127.00 |                 149.90 |     147.00 |      1.18 |
| PLATANO_TABASCO       |            24.00 |      22.80 |                  24.90 |      26.90 |      1.18 |
| AZUCAR_ESTANDAR       |            27.78 |      28.89 |                  32.11 |      28.89 |      1.16 |
| RES_MOLIDA            |           118.00 |     117.00 |                 108.00 |     125.00 |      1.16 |
| ATUN_AGUA             |           135.71 |     153.85 |                 146.92 |     153.85 |      1.13 |
| DETERGENTE_POLVO      |            39.68 |      42.00 |                  43.53 |      45.00 |      1.13 |
| POLLO_ENTERO          |            47.00 |      49.00 |                  44.00 |      49.00 |      1.11 |
| JABON_LAVANDERIA      |            60.00 |      58.75 |                  63.75 |      65.00 |      1.11 |
| HUEVO_BLANCO          |             3.14 |       2.90 |                   3.16 |       3.17 |      1.09 |
| RES_FALDA             |           192.00 |     199.00 |                 208.90 |     199.00 |      1.09 |
| TORTILLA_MAIZ         |            13.00 |      12.90 |                  13.90 |      13.90 |      1.08 |
| POLLO_PECHUGA         |           132.00 |     138.00 |                 134.90 |     142.00 |      1.08 |
| ACEITE_VEGETAL        |            36.00 |      37.38 |                  38.24 |      37.50 |      1.06 |
| LECHE_ENTERA          |            29.50 |      28.50 |                  29.50 |      30.00 |      1.05 |
| RES_MILANESA          |           218.00 |     220.00 |                 228.90 |     218.00 |      1.05 |
| PAPA_BLANCA           |            31.50 |      32.00 |                  32.80 |      32.90 |      1.04 |
