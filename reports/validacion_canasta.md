# Validación independiente de la canasta

_Generado por `python -m src.analysis.validacion` el 2026-09-16 12:56 · modo `completo` · canasta `v1`._

Recalcula en Python, desde `raw.qqp_precios`, el costo de canasta y el ahorro de una muestra determinista
de municipio-semanas comparables (sin atípicos en la canasta) y lo compara con los marts de dbt.
Método y límites en el docstring de `src/analysis/validacion.py`.

**Resultado: 24 de 24 comparaciones coinciden** (tolerancia ±0.011 MXN en costo,
±0.022 MXN en ahorro).

| municipio                      | semana     | cadena               |   articulos_mart |   articulos_python |   observaciones_python |   costo_mart |   costo_python |   ahorro_mart |   ahorro_python | resultado   |
|:-------------------------------|:-----------|:---------------------|-----------------:|-------------------:|-----------------------:|-------------:|---------------:|--------------:|----------------:|:------------|
| Tuxtla Gutiérrez, Chiapas      | 2024-05-20 | Wal-mart             |               16 |                 16 |                     91 |       626.78 |         626.78 |         34.66 |           34.66 | coincide    |
| Tuxtla Gutiérrez, Chiapas      | 2024-05-20 | Bodega Aurrera       |               16 |                 16 |                     92 |       592.12 |         592.12 |          0.00 |            0.00 | coincide    |
| Tuxtla Gutiérrez, Chiapas      | 2024-05-20 | Hipermercado Soriana |               16 |                 16 |                    213 |       663.77 |         663.77 |         71.65 |           71.65 | coincide    |
| Tuxtla Gutiérrez, Chiapas      | 2024-05-20 | Chedraui             |               16 |                 16 |                     84 |       664.93 |         664.93 |         72.81 |           72.81 | coincide    |
| Centro, Tabasco                | 2026-03-16 | Hipermercado Soriana |               16 |                 16 |                    132 |       702.91 |         702.91 |          1.63 |            1.63 | coincide    |
| Centro, Tabasco                | 2026-03-16 | Bodega Aurrera       |               16 |                 16 |                    176 |       748.45 |         748.45 |         47.17 |           47.17 | coincide    |
| Centro, Tabasco                | 2026-03-16 | Chedraui             |               16 |                 16 |                     90 |       701.28 |         701.28 |          0.00 |            0.00 | coincide    |
| Centro, Tabasco                | 2026-03-16 | Wal-mart             |               16 |                 16 |                    104 |       724.73 |         724.73 |         23.45 |           23.45 | coincide    |
| Aguascalientes, Aguascalientes | 2024-07-08 | Bodega Aurrera       |               16 |                 16 |                     90 |       720.67 |         720.67 |         48.48 |           48.48 | coincide    |
| Aguascalientes, Aguascalientes | 2024-07-08 | Chedraui             |               16 |                 16 |                     90 |       672.19 |         672.19 |          0.00 |            0.00 | coincide    |
| Aguascalientes, Aguascalientes | 2024-07-08 | Wal-mart             |               16 |                 16 |                    103 |       680.64 |         680.64 |          8.45 |            8.45 | coincide    |
| Aguascalientes, Aguascalientes | 2024-07-08 | Hipermercado Soriana |               16 |                 16 |                    101 |       754.71 |         754.71 |         82.52 |           82.52 | coincide    |
| León, Guanajuato               | 2026-07-20 | Hipermercado Soriana |               16 |                 16 |                    122 |       687.62 |         687.62 |         28.34 |           28.34 | coincide    |
| León, Guanajuato               | 2026-07-20 | Bodega Aurrera       |               16 |                 16 |                    167 |       665.58 |         665.58 |          6.30 |            6.30 | coincide    |
| León, Guanajuato               | 2026-07-20 | Chedraui             |               16 |                 16 |                     87 |       659.28 |         659.28 |          0.00 |            0.00 | coincide    |
| León, Guanajuato               | 2026-07-20 | Wal-mart             |               16 |                 16 |                    191 |       697.27 |         697.27 |         37.99 |           37.99 | coincide    |
| Campeche, Campeche             | 2026-07-20 | Chedraui             |               16 |                 16 |                     76 |       640.76 |         640.76 |          0.00 |            0.00 | coincide    |
| Campeche, Campeche             | 2026-07-20 | Hipermercado Soriana |               16 |                 16 |                    104 |       691.96 |         691.96 |         51.20 |           51.20 | coincide    |
| Campeche, Campeche             | 2026-07-20 | Bodega Aurrera       |               16 |                 16 |                     81 |       671.69 |         671.69 |         30.93 |           30.93 | coincide    |
| Campeche, Campeche             | 2026-07-20 | Wal-mart             |               16 |                 16 |                     91 |       673.96 |         673.96 |         33.20 |           33.20 | coincide    |
| Mérida, Yucatán                | 2025-08-11 | Chedraui             |               16 |                 16 |                     93 |       655.53 |         655.53 |         21.07 |           21.07 | coincide    |
| Mérida, Yucatán                | 2025-08-11 | Hipermercado Soriana |               16 |                 16 |                    117 |       710.82 |         710.82 |         76.36 |           76.36 | coincide    |
| Mérida, Yucatán                | 2025-08-11 | Bodega Aurrera       |               16 |                 16 |                     88 |       634.46 |         634.46 |          0.00 |            0.00 | coincide    |
| Mérida, Yucatán                | 2025-08-11 | Wal-mart             |               16 |                 16 |                    201 |       691.76 |         691.76 |         57.30 |           57.30 | coincide    |
