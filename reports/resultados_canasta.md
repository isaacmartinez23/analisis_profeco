# Resultados del análisis de la canasta

_Generado por `python -m src.analysis.resultados` el 2026-09-16 12:56 · modo `completo` · canasta `v1` · semanas 2024-01-08 a 2026-07-27._

Todas las comparaciones entre cadenas son **pareadas**: misma canasta, mismo municipio y misma semana
(5,630 municipio-semanas en 51 municipios).
"Recientes" = últimas 8 semanas desde 2026-06-08.
Definiciones de métricas: `docs/catalogo_metricas.md`. Salvedades: `docs/limitaciones.md`.

## 1. ¿Cuánto cuesta la misma canasta en diferentes cadenas y municipios?

| cadena               | grupo_empresarial        |   municipio_semanas |   costo_mediano |   costo_mediano_recientes |   diferencia_vs_mediana_pct |
|:---------------------|:-------------------------|--------------------:|----------------:|--------------------------:|----------------------------:|
| Chedraui             | Grupo Comercial Chedraui |                2656 |          663.94 |                    650.22 |                       -3.14 |
| Bodega Aurrera       | Walmart de México        |                3135 |          693.09 |                    670.07 |                        0.00 |
| Hipermercado Soriana | Organización Soriana     |                4604 |          703.03 |                    682.91 |                        0.00 |
| Wal-mart             | Walmart de México        |                4946 |          713.11 |                    699.88 |                        1.22 |

Nivel de precios municipal (recientes): cada cadena se compara con su propia mediana nacional y se
promedia geométricamente entre las cadenas presentes (mínimo 2); 100 = nivel nacional. Evita que un
municipio parezca barato solo porque ahí se mide una cadena barata.

| grupo       | estado              | municipio            |   cadenas |   nivel_precios_100_nacional |   costo_mediano |
|:------------|:--------------------|:---------------------|----------:|-----------------------------:|----------------:|
| más baratos | Veracruz            | Boca del Río         |         2 |                        97.10 |          671.39 |
| más baratos | Ciudad de México    | Tlalpan              |         3 |                        98.00 |          672.14 |
| más baratos | Tabasco             | Centro               |         4 |                        98.40 |          663.27 |
| más baratos | Oaxaca              | Oaxaca de Juárez     |         2 |                        98.40 |          680.13 |
| más baratos | Estado de México    | Atizapán de Zaragoza |         2 |                        98.50 |          649.07 |
| más caros   | Baja California Sur | La Paz               |         4 |                       102.70 |          693.49 |
| más caros   | San Luis Potosí     | San Luis Potosí      |         2 |                       102.60 |          691.86 |
| más caros   | Tamaulipas          | Reynosa              |         2 |                       102.30 |          691.35 |
| más caros   | Tamaulipas          | Tampico              |         4 |                       102.10 |          705.40 |
| más caros   | Ciudad de México    | Coyoacán             |         4 |                       101.60 |          687.43 |

## 2. ¿Cuánto puede ahorrar una familia al elegir la cadena más económica?

Ahorro máximo = diferencia entre la cadena más cara y la más barata del mismo municipio-semana:

| alcance              |   municipio_semanas |   ahorro_maximo_mediano |   ahorro_maximo_mediano_pct |   ahorro_maximo_p90 |
|:---------------------|--------------------:|------------------------:|----------------------------:|--------------------:|
| todas                |                5630 |                   48.08 |                        6.68 |               92.60 |
| con 4 cadenas        |                 801 |                   64.03 |                        8.82 |              105.22 |
| con grupos distintos |                5352 |                   49.52 |                        6.86 |               93.35 |

Por cadena: frecuencia con la que es la más barata y ahorro al cambiarse a la más barata. El equivalente
anual multiplica la mediana semanal por 52 y supone comprar la canasta de referencia cada semana.

| cadena               |   municipio_semanas |   veces_mas_barata_pct |   ahorro_mediano_al_cambiar |   ahorro_mediano_pct |   ahorro_anual_equivalente |
|:---------------------|--------------------:|-----------------------:|----------------------------:|---------------------:|---------------------------:|
| Chedraui             |                2656 |                   70.7 |                         0.0 |                  0.0 |                        0.0 |
| Bodega Aurrera       |                3135 |                   35.9 |                        13.7 |                  2.0 |                      710.0 |
| Hipermercado Soriana |                4604 |                   32.8 |                        21.7 |                  3.1 |                    1,130.0 |
| Wal-mart             |                4946 |                   22.6 |                        32.0 |                  4.5 |                    1,665.0 |

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
| 2026-06 |              97.9 |            125.8 |
| 2026-07 |              96.8 |            127.0 |

## 4. ¿Qué productos explican las mayores diferencias de precio?

Diferencia acumulada = suma, sobre todas las cadenas no ganadoras y municipio-semanas comparables, del
costo del artículo menos su costo en la cadena con la canasta más barata. Suma el ahorro total.

| articulo                       |   diferencia_acumulada |   pct_de_la_diferencia_neta |   diferencia_mediana_por_celda |   pct_celdas_mas_barato_que_ganadora |
|:-------------------------------|-----------------------:|----------------------------:|-------------------------------:|-------------------------------------:|
| Milanesa de res                |               85,475.0 |                        20.6 |                            6.5 |                                 33.4 |
| Limón sin semilla (persa)      |               71,393.0 |                        17.2 |                            6.4 |                                 25.3 |
| Jitomate saladette             |               54,487.0 |                        13.1 |                            5.2 |                                 25.9 |
| Cebolla blanca                 |               51,239.0 |                        12.3 |                            4.5 |                                 28.9 |
| Papa alfa o blanca             |               41,205.0 |                         9.9 |                            3.9 |                                 29.0 |
| Pollo entero                   |               29,856.0 |                         7.2 |                            3.0 |                                 32.4 |
| Frijol negro                   |               23,467.0 |                         5.6 |                            2.0 |                                 39.8 |
| Plátano tabasco                |               17,894.0 |                         4.3 |                            1.7 |                                 30.2 |
| Huevo blanco                   |               13,837.0 |                         3.3 |                            1.1 |                                 35.3 |
| Leche ultrapasteurizada entera |                8,238.0 |                         2.0 |                            0.8 |                                 36.0 |
| Azúcar estándar                |                8,091.0 |                         1.9 |                            0.6 |                                 41.5 |
| Aceite vegetal comestible      |                7,022.0 |                         1.7 |                            0.8 |                                 39.3 |
| Arroz súper extra              |                5,021.0 |                         1.2 |                            0.5 |                                 45.3 |
| Tortilla de maíz a granel      |                3,173.0 |                         0.8 |                            0.5 |                                 31.7 |
| Atún en agua                   |               -1,313.0 |                        -0.3 |                           -0.1 |                                 50.8 |
| Pasta para sopa                |               -3,182.0 |                        -0.8 |                           -0.5 |                                 51.4 |

Sobreprecio mediano de cada artículo frente a la cadena donde ese artículo es más barato:

| articulo                       |   celdas_articulo |   sobreprecio_mediano_vs_cadena_mas_barata_pct |   p90_pct |
|:-------------------------------|------------------:|-----------------------------------------------:|----------:|
| Pasta para sopa                |             12910 |                                          106.5 |     168.9 |
| Limón sin semilla (persa)      |             12075 |                                           41.3 |     124.1 |
| Cebolla blanca                 |             12757 |                                           34.7 |      98.2 |
| Jitomate saladette             |             12673 |                                           34.4 |     105.0 |
| Papa alfa o blanca             |             12712 |                                           21.5 |      58.7 |
| Pollo entero                   |             12707 |                                           19.1 |      49.4 |
| Plátano tabasco                |             12350 |                                           16.8 |      53.7 |
| Frijol negro                   |             12915 |                                           16.3 |      59.6 |
| Arroz súper extra              |             12790 |                                           14.7 |      43.9 |
| Atún en agua                   |             12911 |                                           10.5 |      36.0 |
| Azúcar estándar                |             12900 |                                            9.5 |      27.6 |
| Leche ultrapasteurizada entera |             12906 |                                            8.2 |      40.4 |
| Aceite vegetal comestible      |             12854 |                                            7.8 |      20.8 |
| Milanesa de res                |             10867 |                                            7.5 |      23.0 |
| Tortilla de maíz a granel      |             12762 |                                            6.9 |      15.4 |
| Huevo blanco                   |             12832 |                                            6.1 |      20.2 |

## 5. ¿Qué tan completa y representativa es la información?

| indicador                                   | valor      |
|:--------------------------------------------|:-----------|
| observaciones de precio                     | 35,609,833 |
| estados con datos                           | 30         |
| municipios con datos                        | 75         |
| tiendas de cadenas de referencia            | 212        |
| % observaciones atípicas                    | 0.035      |
| % celdas de referencia con canasta completa | 81.3       |

| cadena               |   municipios |   semanas |   tiendas_por_celda |   dias_por_semana |   semanas_con_canasta_completa_pct |
|:---------------------|-------------:|----------:|--------------------:|------------------:|-----------------------------------:|
| Wal-mart             |           48 |       135 |                 1.0 |               1.0 |                               89.1 |
| Bodega Aurrera       |           46 |       135 |                 1.0 |               1.0 |                               68.7 |
| Hipermercado Soriana |           44 |       135 |                 1.0 |               1.0 |                               88.3 |
| Chedraui             |           28 |       135 |                 1.0 |               1.0 |                               82.5 |

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
| Estado de México | Toluca                 |                   55 |
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
