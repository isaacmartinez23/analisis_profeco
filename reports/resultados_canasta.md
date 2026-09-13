# Resultados del análisis de la canasta

_Generado por `python -m src.analysis.resultados` el 2026-09-12 22:00 · modo `completo` · canasta `v1` · semanas 2024-01-08 a 2026-05-25._

Todas las comparaciones entre cadenas son **pareadas**: misma canasta, mismo municipio y misma semana
(5,230 municipio-semanas en 51 municipios).
"Recientes" = últimas 8 semanas desde 2026-04-06.
Definiciones de métricas: `docs/catalogo_metricas.md`. Salvedades: `docs/limitaciones.md`.

## 1. ¿Cuánto cuesta la misma canasta en diferentes cadenas y municipios?

| cadena               | grupo_empresarial        |   municipio_semanas |   costo_mediano |   costo_mediano_recientes |   diferencia_vs_mediana_pct |
|:---------------------|:-------------------------|--------------------:|----------------:|--------------------------:|----------------------------:|
| Chedraui             | Grupo Comercial Chedraui |                2491 |          664.63 |                    689.22 |                       -3.16 |
| Bodega Aurrera       | Walmart de México        |                2898 |          695.19 |                    716.58 |                        0.00 |
| Hipermercado Soriana | Organización Soriana     |                4271 |          705.36 |                    708.06 |                        0.00 |
| Wal-mart             | Walmart de México        |                4593 |          715.35 |                    752.44 |                        1.08 |

Nivel de precios municipal (recientes): cada cadena se compara con su propia mediana nacional y se
promedia geométricamente entre las cadenas presentes (mínimo 2); 100 = nivel nacional. Evita que un
municipio parezca barato solo porque ahí se mide una cadena barata.

| grupo       | estado              | municipio      |   cadenas |   nivel_precios_100_nacional |   costo_mediano |
|:------------|:--------------------|:---------------|----------:|-----------------------------:|----------------:|
| más baratos | Veracruz            | Boca del Río   |         2 |                        96.90 |          710.39 |
| más baratos | Ciudad de México    | Tlalpan        |         2 |                        97.70 |          696.51 |
| más baratos | Estado de México    | Nezahualcóyotl |         2 |                        97.80 |          687.68 |
| más baratos | Campeche            | Campeche       |         4 |                        98.30 |          702.87 |
| más baratos | Jalisco             | Guadalajara    |         2 |                        98.30 |          724.45 |
| más caros   | Tamaulipas          | Reynosa        |         2 |                       102.10 |          728.12 |
| más caros   | Ciudad de México    | Coyoacán       |         4 |                       101.40 |          717.38 |
| más caros   | Baja California Sur | La Paz         |         4 |                       101.20 |          734.86 |
| más caros   | Michoacán           | Morelia        |         3 |                       101.20 |          729.42 |
| más caros   | Coahuila            | Saltillo       |         3 |                       100.90 |          747.82 |

## 2. ¿Cuánto puede ahorrar una familia al elegir la cadena más económica?

Ahorro máximo = diferencia entre la cadena más cara y la más barata del mismo municipio-semana:

| alcance              |   municipio_semanas |   ahorro_maximo_mediano |   ahorro_maximo_mediano_pct |   ahorro_maximo_p90 |
|:---------------------|--------------------:|------------------------:|----------------------------:|--------------------:|
| todas                |                5230 |                   49.52 |                        6.82 |               93.66 |
| con 4 cadenas        |                 735 |                   64.50 |                        8.91 |              106.86 |
| con grupos distintos |                4975 |                   50.63 |                        7.02 |               94.72 |

Por cadena: frecuencia con la que es la más barata y ahorro al cambiarse a la más barata. El equivalente
anual multiplica la mediana semanal por 52 y supone comprar la canasta de referencia cada semana.

| cadena               |   municipio_semanas |   veces_mas_barata_pct |   ahorro_mediano_al_cambiar |   ahorro_mediano_pct |   ahorro_anual_equivalente |
|:---------------------|--------------------:|-----------------------:|----------------------------:|---------------------:|---------------------------:|
| Chedraui             |                2491 |                   69.8 |                         0.0 |                  0.0 |                        0.0 |
| Bodega Aurrera       |                2898 |                   35.0 |                        14.6 |                  2.1 |                      757.0 |
| Hipermercado Soriana |                4271 |                   32.3 |                        23.2 |                  3.3 |                    1,208.0 |
| Wal-mart             |                4593 |                   23.9 |                        31.6 |                  4.4 |                    1,643.0 |

## 3. ¿Cómo cambia el costo semana a semana?

Índice directo con panel fijo (base 100 = mediana de las primeras 8 semanas de cada par cadena-municipio):
media geométrica de costo/costo base de los pares presentes. Se descartó el índice encadenado porque
acumulaba ~3 puntos de deriva (D-026). Promedio mensual de los índices semanales:

| mes     |   indice_promedio |   pares_promedio |
|:--------|------------------:|-----------------:|
| 2024-01 |             100.2 |            132.0 |
| 2024-02 |              99.6 |            134.8 |
| 2024-03 |              98.9 |            134.8 |
| 2024-04 |              97.5 |            133.0 |
| 2024-05 |              95.6 |            136.2 |
| 2024-06 |              97.6 |            138.5 |
| 2024-07 |             101.6 |            135.8 |
| 2024-08 |              99.7 |            127.0 |
| 2024-09 |             100.0 |            117.2 |
| 2024-10 |             103.3 |            116.2 |
| 2024-11 |             102.6 |            114.8 |
| 2024-12 |             101.6 |            113.2 |
| 2025-01 |             100.0 |            114.8 |
| 2025-02 |              98.4 |            117.8 |
| 2025-03 |              98.6 |            121.2 |
| 2025-04 |              98.9 |            110.8 |
| 2025-05 |             101.3 |            113.5 |
| 2025-06 |             101.1 |            120.6 |
| 2025-07 |             100.1 |            128.2 |
| 2025-08 |              98.9 |            128.8 |
| 2025-09 |              99.2 |            123.8 |
| 2025-10 |              98.9 |            125.5 |
| 2025-11 |              97.8 |            116.2 |
| 2025-12 |              97.9 |            106.4 |
| 2026-01 |              97.1 |            123.5 |
| 2026-02 |              96.9 |            122.5 |
| 2026-03 |             102.0 |            110.6 |
| 2026-04 |             104.0 |            115.5 |
| 2026-05 |             102.1 |            124.5 |

## 4. ¿Qué productos explican las mayores diferencias de precio?

Diferencia acumulada = suma, sobre todas las cadenas no ganadoras y municipio-semanas comparables, del
costo del artículo menos su costo en la cadena con la canasta más barata. Suma el ahorro total.

| articulo                       |   diferencia_acumulada |   pct_de_la_diferencia_neta |   diferencia_mediana_por_celda |   pct_celdas_mas_barato_que_ganadora |
|:-------------------------------|-----------------------:|----------------------------:|-------------------------------:|-------------------------------------:|
| Milanesa de res                |               82,900.0 |                        21.1 |                            7.0 |                                 33.2 |
| Limón sin semilla (persa)      |               65,607.0 |                        16.7 |                            6.1 |                                 25.7 |
| Jitomate saladette             |               52,343.0 |                        13.3 |                            5.5 |                                 25.7 |
| Cebolla blanca                 |               48,184.0 |                        12.3 |                            4.5 |                                 29.3 |
| Papa alfa o blanca             |               37,551.0 |                         9.6 |                            3.9 |                                 28.9 |
| Pollo entero                   |               29,353.0 |                         7.5 |                            3.5 |                                 32.7 |
| Frijol negro                   |               22,952.0 |                         5.9 |                            2.1 |                                 39.4 |
| Plátano tabasco                |               16,750.0 |                         4.3 |                            1.8 |                                 30.8 |
| Huevo blanco                   |               13,318.0 |                         3.4 |                            1.1 |                                 35.8 |
| Azúcar estándar                |                7,494.0 |                         1.9 |                            0.5 |                                 41.9 |
| Leche ultrapasteurizada entera |                7,175.0 |                         1.8 |                            0.8 |                                 36.4 |
| Aceite vegetal comestible      |                5,919.0 |                         1.5 |                            0.7 |                                 40.3 |
| Arroz súper extra              |                4,649.0 |                         1.2 |                            0.5 |                                 45.6 |
| Tortilla de maíz a granel      |                2,766.0 |                         0.7 |                            0.5 |                                 32.3 |
| Atún en agua                   |               -1,800.0 |                        -0.5 |                           -0.2 |                                 51.7 |
| Pasta para sopa                |               -2,861.0 |                        -0.7 |                           -0.5 |                                 51.3 |

Sobreprecio mediano de cada artículo frente a la cadena donde ese artículo es más barato:

| articulo                       |   celdas_articulo |   sobreprecio_mediano_vs_cadena_mas_barata_pct |   p90_pct |
|:-------------------------------|------------------:|-----------------------------------------------:|----------:|
| Pasta para sopa                |             12057 |                                          108.7 |     172.2 |
| Limón sin semilla (persa)      |             11278 |                                           41.3 |     121.5 |
| Jitomate saladette             |             11825 |                                           35.1 |     107.5 |
| Cebolla blanca                 |             11907 |                                           34.9 |     100.0 |
| Papa alfa o blanca             |             11868 |                                           21.7 |      60.2 |
| Pollo entero                   |             11859 |                                           21.2 |      50.0 |
| Plátano tabasco                |             11502 |                                           17.1 |      55.8 |
| Frijol negro                   |             12062 |                                           15.9 |      58.1 |
| Arroz súper extra              |             11948 |                                           14.8 |      43.7 |
| Atún en agua                   |             12059 |                                           10.3 |      36.0 |
| Azúcar estándar                |             12047 |                                            9.5 |      27.8 |
| Leche ultrapasteurizada entera |             12054 |                                            8.0 |      40.4 |
| Milanesa de res                |             10110 |                                            7.9 |      23.7 |
| Aceite vegetal comestible      |             12005 |                                            7.9 |      20.9 |
| Tortilla de maíz a granel      |             11911 |                                            6.9 |      15.5 |
| Huevo blanco                   |             11980 |                                            6.3 |      20.8 |

## 5. ¿Qué tan completa y representativa es la información?

| indicador                                   | valor      |
|:--------------------------------------------|:-----------|
| observaciones de precio                     | 32,985,030 |
| estados con datos                           | 30         |
| municipios con datos                        | 75         |
| tiendas de cadenas de referencia            | 212        |
| % observaciones atípicas                    | 0.036      |
| % celdas de referencia con canasta completa | 81         |

| cadena               |   municipios |   semanas |   tiendas_por_celda |   dias_por_semana |   semanas_con_canasta_completa_pct |
|:---------------------|-------------:|----------:|--------------------:|------------------:|-----------------------------------:|
| Wal-mart             |           48 |       126 |                 1.0 |               1.0 |                               88.8 |
| Bodega Aurrera       |           46 |       126 |                 1.0 |               1.0 |                               68.0 |
| Hipermercado Soriana |           44 |       126 |                 1.0 |               1.0 |                               88.0 |
| Chedraui             |           28 |       126 |                 1.0 |               1.0 |                               82.6 |

Municipios sin ninguna semana comparable (24):

| estado           | municipio              |   n_establecimientos |
|:-----------------|:-----------------------|---------------------:|
| Ciudad de México | Iztacalco              |                   11 |
| Ciudad de México | Magdalena Contreras    |                    3 |
| Ciudad de México | Xochimilco             |                   10 |
| Ciudad de México | Álvaro Obregón         |                   20 |
| Estado de México | Atizapán               |                   33 |
| Estado de México | Chicoloapan            |                    4 |
| Estado de México | Cuautitlán             |                    5 |
| Estado de México | Huixquilucan           |                    6 |
| Estado de México | Lerma                  |                    1 |
| Estado de México | Metepec                |                    4 |
| Estado de México | Tecámac                |                    3 |
| Estado de México | Toluca                 |                   52 |
| Estado de México | Tultitlán              |                   38 |
| Estado de México | Zinacantepec           |                    1 |
| Hidalgo          | Mineral de la Reforma  |                    2 |
| Jalisco          | Tlaquepaque            |                    3 |
| Nuevo León       | General Escobedo       |                    1 |
| Nuevo León       | Guadalupe              |                   15 |
| Oaxaca           | Santa Cruz Xoxocotlán  |                    1 |
| Oaxaca           | Santa Lucia del Camino |                    5 |
| Tamaulipas       | Ciudad Madero          |                    5 |
| Tlaxcala         | Apizaco                |                   18 |
| Veracruz         | Orizaba                |                    4 |
| Zacatecas        | Guadalupe              |                   26 |
