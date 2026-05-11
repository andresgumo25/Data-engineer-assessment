# Execution Guide — PostgreSQL + dbt Flow

Production-grade flow using PostgreSQL 15 (via Docker) and dbt for transformations.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- `data_jobs.csv` placed in the project root or `Docs/` folder

---

## Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` — the defaults match the provided `docker-compose.yml` and work out of the box:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=jobs_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

## Step 3 — Start PostgreSQL

```bash
docker-compose up -d
```

Wait until healthy:

```bash
docker-compose ps
# STATUS should show: "healthy"
```

---

## Step 4 — Ingest CSV into PostgreSQL

```bash
python tools/ingest_postgres.py
```

Creates and populates the `staging_jobs` table. Semi-structured columns (`job_skills`, `job_type_skills`) are stored as `JSONB`.

Expected log output:
```
INFO Found CSV at Docs/data_jobs.csv
INFO Read XXXXX rows
INFO Inserted rows into Postgres staging table
```

---

## Step 5 — Configure the dbt profile

### Option A — copy the example profile (quickest)

```bash
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
```

If your credentials differ from the defaults, edit `~/.dbt/profiles.yml`.

### Option B — use environment variables

Export before running dbt (values must match your `.env`):

```bash
export DBT_USER=postgres
export DBT_PASSWORD=postgres
export DBT_HOST=localhost
export DBT_PORT=5432
export DBT_DB=jobs_db
export DBT_SCHEMA=public
```

---

## Step 6 — Run dbt models

```bash
cd dbt
dbt run --profiles-dir .
```

Creates the following tables/views in PostgreSQL:

| Schema | Object | Description |
|---|---|---|
| `staging` | `stg_jobs` | Deduplicated + cast staging view |
| `marts` | `companies` | Unique companies |
| `marts` | `locations` | Unique location strings + country |
| `marts` | `skills` | Unique skills |
| `marts` | `jobs` | Core job postings with FK references |
| `marts` | `job_skills` | Junction table (job ↔ skill) |

---

## Step 7 — Run dbt tests

```bash
dbt test --profiles-dir .
```

Tests defined in `models/schema.yml`:

| Model | Test |
|---|---|
| `stg_jobs` | `unique`, `not_null` on `job_id` |
| `jobs` | `unique`, `not_null` on `job_id`; `not_null` on `company_id` |
| `companies` | `unique`, `not_null` on `company_id` |
| `skills` | `unique`, `not_null` on `skill_id` |
| `job_skills` | `unique`, `not_null` on `id` |

---

## Step 8 — Run data quality checks

```bash
cd ..
python tools/data_quality.py
```

Runs SQL-level assertions (orphaned FK references, empty skill names, row count thresholds).

---

## Step 9 — Run unit tests

```bash
pytest
```

---

## Step 10 — (Optional) Alternative Python transform

If you prefer pure Python/SQL without dbt, run this instead of steps 6–7:

```bash
python tools/transform_postgres.py
```

Produces the same 3NF tables using `ON CONFLICT DO NOTHING` for idempotent loads.

---

## Step 11 — Stop PostgreSQL

```bash
docker-compose down
```

To also delete the data volume (full wipe):

```bash
docker-compose down -v
```

---

## Summary

```bash
pip install -r requirements.txt
cp .env.example .env
docker-compose up -d
python tools/ingest_postgres.py
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
cd .. && python tools/data_quality.py
pytest
```

| Step | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Configure env | `cp .env.example .env` |
| Start Postgres | `docker-compose up -d` |
| Ingest | `python tools/ingest_postgres.py` |
| dbt profile | `cp dbt/profiles.yml.example ~/.dbt/profiles.yml` |
| Transform | `cd dbt && dbt run --profiles-dir .` |
| dbt tests | `dbt test --profiles-dir .` |
| Data quality | `python tools/data_quality.py` |
| Unit tests | `pytest` |
| Stop Postgres | `docker-compose down` |
