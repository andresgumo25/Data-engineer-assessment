# Explicación detallada del proyecto

Este documento resume todo lo implementado en el repositorio "Data engineer Technical assessment" y cómo usar los dos flujos disponibles (dbt y SQL/Python sin orquestación).

## Resumen del objetivo
Construir un pipeline reproducible que ingresa el CSV `data_jobs.csv`, lo normaliza a un modelo 3NF (jobs, companies, locations, skills, job_skills), incluya pruebas de calidad, documentación y un ERD.

## Estructura del repositorio (tras reorganización)
- dbt/                       -> Contiene el proyecto dbt: models/, dbt_project.yml, profiles.yml.example
- docs/                      -> Documentos y artefactos: data_jobs.csv (copia), erd.png, erd.dbml, explicacion.md (este archivo)
- tools/                     -> Scripts ejecutables (ingest, transform, calidad, helpers)
- .github/workflows/         -> CI workflows (actualizados para usar tools/)
- requirements.txt           -> Dependencias Python
- jobs_db.sqlite             -> (opcional) SQLite para desarrollo local

## Qué se hizo (detallado)
1. Ingesta
- tools/ingest_sqlite.py: lee `data_jobs.csv`, parsea campos semi-estructurados (job_skills, job_type_skills), normaliza booleanos y fechas, escribe `staging_jobs` en `jobs_db.sqlite`.
- tools/ingest_postgres.py: lee el CSV, convierte arrays/objetos a JSONB y hace inserciones por lotes a Postgres en la tabla `staging_jobs`.

2. Transformación (3NF)
- dbt models (dbt/models/): modelos de staging (`stg_jobs.sql`) y marts (companies, locations, skills, job_skills, jobs). Normalizan booleans, manejan deduplicación por `job_id` (MD5 de title||company||posted_date) y explotan arrays JSONB.
- tools/transform_sqlite.py: script Python que transforma `staging_jobs` (SQLite) a tablas 3NF y crea tablas de ejemplo.
- tools/transform_postgres.py: transforma `staging_jobs` en Postgres creando tablas con FK, PK y realizando cargas idempotentes (ON CONFLICT DO NOTHING). Usa chunking para memoria.

3. Pruebas y calidad
- models/schema.yml (dbt): contiene tests dbt (unique, not_null) que forzaron correcciones en staging y deduplicación.
- tools/run_dbt_sqlite.py: simula `dbt run` y `dbt test` contra SQLite (útil sin Postgres).
- tools/data_quality.py: comprobaciones SQL simples ejecutadas en CI para detectar anomalías (puede ampliarse con Great Expectations).

4. CI
- .github/workflows/ci_dbt_quality.yml: workflow que levanta un servicio Postgres, ejecuta ingest_postgres.py, ejecuta dbt (configura ~/.dbt/profiles.yml en runner) y luego ejecuta data_quality.py. Se actualizaron rutas al directorio tools/.

5. ERD y documentación
- docs/erd.dbml y docs/erd.png generados y añadidos.
- README en la raíz conserva la visión general; este archivo explica el detalle técnico.

## Comandos principales (rápido)
Requisitos: Python 3.10+, pip install -r requirements.txt

Flujo SQLite (desarrollo rápido):
- python tools/ingest_sqlite.py
- python tools/run_dbt_sqlite.py   # crea modelos y corre tests simulados
- (opcional) python tools/transform_sqlite.py

Flujo Postgres + dbt (producción/local con Postgres):
- Levantar Postgres (local o Docker). Por ejemplo con Docker compose o instalar localmente.
- Crear DB: psql -U postgres -h localhost -c "CREATE DATABASE jobs_db;"
- export POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT (o usar .env)
- pip install -r requirements.txt
- python tools/ingest_postgres.py
- dbt run --profiles-dir dbt   # usa dbt/profiles.yml.example o configurar ~/.dbt/profiles.yml
- dbt test --profiles-dir dbt
- (opcional) python tools/transform_postgres.py  # implementación alternativa a dbt si prefieres Python/SQL directo

Nota: CI usa dbt ejecutado con un profiles.yml temporal en ~/.dbt creado durante el job.

## ¿Tenemos 2 flujos?
Sí. Hay dos caminos implementados y soportados:

1) Flujo dbt (recomendado para transformaciones mantenibles):
- Ingesta en staging (Postgres) con tools/ingest_postgres.py.
- Transformaciones expresadas en SQL modular dentro de dbt (staging → marts).
- Ventajas: pruebas integradas (dbt test), documentación, lineage, mejores prácticas para despliegue/CI.

2) Flujo SQL/Python (scripts "normales"):
- tools/transform_postgres.py y tools/transform_sqlite.py son scripts que realizan la misma transformación sin dbt.
- Ventajas: más control imperativo, fácil de ejecutar sin instalar dbt, útil para debugging o entornos limitados.
- Inconveniente: menos integrable con ecosistema dbt (documentación automática, tests como parte de la plataforma).

Ambos flujos producen el mismo modelo 3NF y comparten lógica (deduplicación, parseo de skills, hashing de ids). Se pueden mantener ambos para compatibilidad o migrar por completo a dbt si se prioriza estandarización.

## Siguientes pasos recomendados
- Actualizar README principal con enlaces a este documento.
- Añadir un `dbt/profiles.yml` de ejemplo con instrucciones para usuarios locales (o documentar uso de `--profiles-dir dbt`).
- Añadir suites de data-quality más ricas (Great Expectations) y exponer resultados en CI.
- Añadir índices/DDL final en `schema.sql` para la base de producción.

---

Si querés, actualizo el README principal para enlazar a este `docs/explicacion.md` y actualizo otros workflows o archivos que aún apunten a rutas antiguas. ¿Procedo con eso?