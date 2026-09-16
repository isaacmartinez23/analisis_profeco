# Caso de estudio · cómo se construyó este pipeline

Qué problemas reales aparecieron, qué se decidió y por qué. Las cifras de resultado están en
[`reports/memo_ejecutivo.md`](../reports/memo_ejecutivo.md); las decisiones completas, en
[`decisiones.md`](decisiones.md).

## El encargo

PROFECO publica cada quincena los precios que levanta en tiendas de todo el país. Son datos abiertos, pero no
responden por sí solos la pregunta que le importa a un hogar: *¿dónde conviene comprar y cuánto se ahorra?* Nadie
puede comparar 36 millones de filas de texto libre donde "1 L", "1000 ML" y "1LT" son el mismo litro.

El encargo fue construir un proyecto de portafolio completo: pipeline reproducible, modelo dimensional, reglas de
calidad, publicación a una base accesible desde un dashboard y automatización semanal.

## Punto de partida: nada del origen era confiable

Los archivos llegaron sin diccionario. La primera regla del proyecto fue no asumir nada y verificarlo todo. El
perfilado encontró, entre otras cosas:

- Dos codificaciones (UTF-8 con BOM y Latin-1) y dos formatos de fecha (`aaaa/mm/dd` y `dd/mm/aaaa`), que cambian
  de un archivo a otro.
- Un archivo donde PROFECO perdió las letras acentuadas y publicó `Papeler?as`.
- La misma observación repetida en varios catálogos (614,653 grupos) y precios en conflicto el mismo día.
- Un medicamento a 3,041,791 pesos.
- Cobertura real: 30 estados y 75 municipios, casi siempre la capital. No hay Colima ni Nayarit.

Cada hallazgo quedó registrado con su tratamiento en [`diccionario_validado.md`](diccionario_validado.md), antes de
escribir una sola transformación.

## Cinco problemas y cómo se resolvieron

### 1. El equipo se apagaba

Una consulta de perfilado con todos los hilos al 100% durante minutos provocó un apagado por protección térmica.
En lugar de bajar el alcance del análisis, se acotaron los recursos: DuckDB con 4 hilos y 8 GB, consultas archivo
por archivo y agrupaciones por enteros locales en vez de textos largos (D-004, D-005). Los mismos límites sirven
tal cual en GitHub Actions, que también tiene 4 vCPU.

### 2. Comparar peras con peras

Un precio no se puede comparar sin normalizar la presentación. El pipeline interpreta el texto libre a una unidad
base (kg, l, pieza), calcula el precio unitario y solo compara artículos equivalentes. Lo que no se puede
interpretar con confianza **no se adivina**: va a una cola de revisión humana, y las decisiones manuales se
versionan aparte de las automáticas.

La canasta se definió después de medir la disponibilidad real, no antes: 16 alimentos que están presentes en las 4
cadenas de referencia en la mayoría de los municipio-semanas (D-022). Con esa canasta, el 81% de las celdas de
referencia tienen la canasta completa.

### 3. Dos ejecuciones idénticas daban resultados distintos

Con `approx_quantile`, dos corridas de los mismos datos daban 0.0357% y 0.0356% de atípicos. El *t-digest* en
paralelo no es determinista. Se cambió a medianas exactas: los resultados dejaron de moverse y además el modelo
tardó menos (D-021). Un proyecto de datos que no da el mismo número dos veces no es verificable.

### 4. ¿Y si el modelo está mal?

Las pruebas de dbt verifican unicidad, integridad y coherencia, pero no que la lógica de negocio sea correcta:
pueden pasar todas y el costo de la canasta estar mal calculado. Por eso existe una **compuerta independiente**:
`src/analysis/validacion.py` recalcula en Python, desde la capa cruda, el costo y el ahorro de una muestra
determinista de municipio-semanas y los compara con los marts, con tolerancia de un centavo. Si no coinciden, el
pipeline se detiene y no publica.

### 5. Publicar sin romper el dashboard

Publicar reemplazando tablas deja el dashboard inconsistente mientras dura la carga, y un fallo a mitad lo deja
roto. La publicación carga todo en un esquema temporal, verifica los conteos y **cambia el esquema completo en una
sola transacción** (D-029). Un fallo simulado a mitad de la carga, probado contra PostgreSQL 16 real, conserva
intacta la versión anterior.

Después llegó un límite práctico: el plan gratuito de Supabase pone la base en solo lectura al pasar de 500 MB, y
la publicación completa medía 213 MB con picos de 425 MB durante el intercambio. Se publican agregados y el detalle
más reciente en lugar del histórico completo: 91 MB con las mismas vistas disponibles (D-036).

## La prueba de fuego: el origen cambió

Tres días después de automatizar el pipeline, PROFECO publicó junio y julio de 2026. Las tres ejecuciones
siguientes fallaron, y cada falla demostró que una compuerta servía:

| Qué pasó | Qué lo detectó | Qué habría pasado sin la compuerta |
|---|---|---|
| Junio trae 3 columnas nuevas sin documentar (`folio`, `cv_producto`, `cv_marca`) | Validación de esquema en `inspect` | Lectura desalineada o carga silenciosamente incompleta |
| Junio perdió los acentos en el 32% de las filas, incluido el municipio | Revisión de los datos antes de tocar el código | 21 municipios duplicados (`Coyoac?n` junto a `Coyoacán`) y la serie semanal partida, **sin que fallara ninguna prueba** |
| Julio renombró 4 catálogos (`Basicos` → `Básicos`, `Pacic` → `PACIC`) | Prueba de integridad referencial contra el seed de catálogos | `Básicos` y `PACIC` fuera de la canasta en julio: costos incompletos publicados como si fueran normales |

Las correcciones siguieron la misma regla: aceptar lo que ya se revisó y seguir deteniéndose ante lo desconocido.
Se admiten esas tres columnas por nombre y se conservan en la capa cruda sin modelarlas (D-037); la corrección de
caracteres perdidos por candidato único se extendió a estado y municipio (D-038); y los catálogos se relacionan por
llave canónica, de modo que un cambio de acentos ya no rompe nada pero un catálogo realmente nuevo sí (D-039).

El caso del municipio es el más interesante: **ninguna prueba fallaba**. Los conteos cuadraban, las llaves eran
únicas y la integridad referencial se cumplía. El error solo aparecía al leer los datos. Por eso el cambio de
esquema se revisó a mano antes de adaptar el código, y por eso ahora hay una prueba que impide que una llave de
geografía contenga `?`.

## Qué quedó

- Un pipeline que corre completo con un comando y procesa 36 millones de filas en unos 10 minutos en GitHub
  Actions, incluida la descarga.
- 83 pruebas de Python, 153 de dbt y una validación independiente que recalcula el resultado desde cero.
- Publicación atómica a Supabase y ejecución semanal en GitHub Actions con alertas.
- 39 decisiones y 23 limitaciones documentadas, cada una con su efecto en los resultados.

## Qué haría después

1. **Consolidar establecimientos por coordenadas.** Hoy una tienda se identifica por nombre y dirección: si PROFECO
   reescribe la dirección, aparece como sucursal nueva (L-07). `folio`, la columna nueva de junio, podría
   resolverlo si PROFECO la mantiene.
2. **Una canasta con cantidades de una fuente oficial** en lugar de la presentación modal observada, para pasar de
   un índice comparable a un gasto interpretable como tal (L-11).
3. **Canasta complementaria de limpieza e higiene**, que hoy queda fuera (L-19).
4. **Comparar por marca además de por artículo genérico**, para separar cuánto del ahorro es precio y cuánto es
   mezcla de marcas (L-10, L-18).
