# Canasta de precios PROFECO · pipeline reproducible

Pipeline de datos que toma los archivos abiertos de **Quién es Quién en los Precios** (PROFECO), normaliza
productos y presentaciones, modela un esquema estrella, calcula el costo semanal de una canasta de 16 alimentos y
publica tablas analíticas listas para un dashboard.

De 36 millones de precios crudos a cuatro marts que responden cinco preguntas, con pruebas en cada paso, una
ejecución semanal automatizada y un dashboard que se genera con el pipeline.

**Stack:** Python 3.12 · DuckDB · dbt · PostgreSQL (Supabase) · GitHub Actions · HTML/SVG · Looker Studio · pytest ·
ruff

## Preguntas que responde

1. ¿Cuánto cuesta la misma canasta en diferentes cadenas y municipios?
2. ¿Cuánto puede ahorrar una familia al elegir la cadena más económica?
3. ¿Cómo cambia el costo de la canasta semana a semana?
4. ¿Qué productos explican las mayores diferencias de precio?
5. ¿Qué tan completa y representativa es la información utilizada?

Las respuestas, con sus salvedades, están en [`reports/memo_ejecutivo.md`](reports/memo_ejecutivo.md) (versión
ejecutiva) y [`reports/resultados_canasta.md`](reports/resultados_canasta.md) (versión con todas las tablas).

## Dashboard

**En vivo: <https://isaacmartinez.space/analisis_profeco/>** · se regenera cada lunes con la ejecución semanal.

[![Resumen del dashboard con datos al 2026-07-27](docs/img/dashboard_resumen.png)](https://isaacmartinez.space/analisis_profeco/)

Seis páginas, una por vista de la especificación: resumen, costo por cadena, ahorro, productos, cobertura y
disponibilidad. Tiene filtros de periodo, cadena, grupo empresarial y estado, y cada cifra es trazable a una tabla
publicada. Es un solo HTML sin servidor ni credenciales que genera el pipeline:

```bash
python -m src.cli dashboard   # reports/dashboard/index.html
```

Detalle, agregaciones y verificación en [`docs/dashboard.md`](docs/dashboard.md). La especificación para Looker
Studio sobre Supabase sigue disponible en [`docs/dashboard_looker_studio.md`](docs/dashboard_looker_studio.md).

## Arquitectura

```mermaid
flowchart LR
    P[PROFECO<br/>datos abiertos] --> D[descarga y<br/>validación de esquema]
    D --> I[ingesta idempotente<br/>DuckDB]
    I --> Q[reglas de calidad<br/>R-01 a R-10]
    Q --> N[normalización<br/>unidades y texto]
    N --> M[dbt · esquema estrella<br/>marts y vistas BI]
    M --> V[pruebas dbt y<br/>validación independiente]
    V --> H[dashboard<br/>HTML estático]
    H --> G[GitHub Pages<br/>página pública]
    H -.bajo demanda.-> S[(Supabase<br/>publicación atómica)]
    S --> L[Looker Studio]
    V -.falla.-> A[alerta e issue<br/>no se publica]
```

Detalle en [`docs/arquitectura.md`](docs/arquitectura.md): componentes, modelo dimensional, modos de ejecución,
compuertas de calidad, publicación y seguridad.

## Cómo ejecutarlo

Requisitos: Python 3.11 a 3.13 y, para leer los RAR de PROFECO, una de estas herramientas: `bsdtar`
(`libarchive-tools`), `unrar` o 7-Zip.

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Sin descargar nada** (muestra versionada de 5 archivos, termina en menos de un minuto):

```bash
python -m src.cli --muestra pipeline
```

**Con los datos completos** (~377 MB, unos 10 minutos):

```bash
python -m src.cli download     # o coloca los archivos a mano en data/raw/
python -m src.cli pipeline
```

`make pipeline` y `make pipeline MUESTRA=1` hacen lo mismo donde hay `make`. Cada paso se puede ejecutar por
separado: `inspect`, `ingest`, `quality`, `normalize`, `dbt-run`, `dbt-test`, `quality-marts`, `validate`,
`resultados`, `dashboard`, `publish`, `alertas`. `pipeline --desde <paso>` reanuda desde un paso.

Sin credenciales de Supabase configuradas, el pipeline termina correctamente después de validar los marts y avisa
que no publicará.

### Publicación en PostgreSQL (bajo demanda)

El pipeline publica los marts en Supabase con intercambio atómico de esquemas, verificación de conteos y un rol de
solo lectura:

```bash
python -m src.cli publish   # requiere .env con las variables SUPABASE_DB_*
```

No se ejecuta cada semana: el dashboard ya no depende de la base y el plan gratuito pausa los proyectos inactivos
(D-040, D-041, L-22). Para activarla en la ejecución semanal, define la variable `QQP_PUBLICAR_SUPABASE=true`; en
una ejecución manual basta con marcar la casilla. El publicador se prueba en cada push contra un PostgreSQL 16
real, y el pipeline de la muestra hace una publicación de prueba en cada corrida de CI.

La guía de conexión, el rol de solo lectura y la especificación del tablero de Looker Studio están en
[`docs/dashboard_looker_studio.md`](docs/dashboard_looker_studio.md).

### Pruebas

```bash
pytest -q          # 91 pruebas, incluidas las de integración contra PostgreSQL real
ruff check .
python -m src.cli --muestra pipeline
```

Las pruebas de integración del publicador usan el PostgreSQL de `QQP_TEST_PG_DSN` o uno embebido
(`pip install -e ".[pg-local]"`); si no hay ninguno, se omiten.

## Qué hay en el repositorio

```text
src/           ingesta, calidad, normalización, análisis, dashboard y publicación
transform/     proyecto dbt: staging → intermediate → core → marts → bi
tests/         pruebas unitarias y de integración
docs/          arquitectura, decisiones, contratos, reglas, limitaciones, bitácora
reports/       perfil de datos, calidad, resultados, memo ejecutivo (y el dashboard generado, no versionado)
data/          raw (inmutable), sample (versionada), mappings, processed (ignorado)
.github/       ejecución semanal y pruebas en cada push
```

## Documentación

| Documento | Para qué |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Cómo funciona el pipeline de punta a punta |
| [`docs/decisiones.md`](docs/decisiones.md) | Registro de decisiones (D-001 a D-040) con contexto y consecuencias |
| [`docs/contrato_datos.md`](docs/contrato_datos.md) | Contrato de cada tabla: grano, llaves, tipos, nulos, supuestos |
| [`docs/catalogo_metricas.md`](docs/catalogo_metricas.md) | Definición y fórmula de cada métrica, con su trazabilidad |
| [`docs/reglas_calidad.md`](docs/reglas_calidad.md) | Reglas, umbrales y qué pasa cuando fallan |
| [`docs/diccionario_validado.md`](docs/diccionario_validado.md) | Esquema real de los CSV, contrastado con el diccionario oficial |
| [`docs/normalizacion.md`](docs/normalizacion.md) | Llaves canónicas, caracteres perdidos y unidades base |
| [`docs/limitaciones.md`](docs/limitaciones.md) | Supuestos y limitaciones (L-01 a L-25) |
| [`docs/dashboard.md`](docs/dashboard.md) | Dashboard HTML: páginas, datos incrustados, agregaciones y verificación |
| [`docs/dashboard_looker_studio.md`](docs/dashboard_looker_studio.md) | Especificación para Looker Studio: conexión, fuentes, páginas y campos calculados |
| [`docs/caso_estudio.md`](docs/caso_estudio.md) | Cómo se construyó: problemas reales y decisiones de ingeniería |
| [`docs/bitacora.md`](docs/bitacora.md) | Bitácora por fase, con evidencia de pruebas |

## Automatización

El workflow [`pipeline-semanal.yml`](.github/workflows/pipeline-semanal.yml) tiene tres trabajos:

- **Pruebas** en cada push y pull request: lint, pruebas unitarias y de integración (servicio PostgreSQL 16) y el
  pipeline completo con la muestra, incluida una publicación de prueba.
- **Pipeline completo** los lunes a las 13:00 UTC y a demanda: descarga los archivos vigentes, ejecuta cada paso
  por separado y genera el dashboard. Ante cualquier falla escribe un resumen, opcionalmente notifica a un webhook
  y abre o actualiza un issue de alerta. Publica en Supabase solo bajo demanda (D-041).
- **Dashboard en GitHub Pages**: despliega la página pública si el dashboard llegó a generarse, es decir, después
  de las pruebas dbt, la calidad del modelo y la validación independiente. No depende de Supabase.

## Alcance y límites

- Los precios provienen de ciudades muestreadas por PROFECO (una por estado en la mayoría de los casos), no de la
  entidad completa.
- La canasta v1 es **genérica**: cada artículo es la mediana del precio unitario de cualquier marca comparable, así
  que parte de la diferencia entre cadenas refleja su mezcla de marcas (marca propia frente a marca comercial).
- El costo de la canasta es un **índice comparable** entre cadenas y semanas, no el gasto real de un hogar.
- Las comparaciones entre cadenas siempre son pareadas: misma canasta, mismo municipio y misma semana.

La lista completa está en [`docs/limitaciones.md`](docs/limitaciones.md).

## Licencia y datos

Los datos son de PROFECO, publicados en [datos abiertos](https://datos.profeco.gob.mx/datos_abiertos/qqp.php);
este repositorio no los redistribuye: solo versiona una muestra pequeña para pruebas.
