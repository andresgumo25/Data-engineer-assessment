# Execution Guide — SQLite Flow

Runs entirely locally with no Docker or Postgres. Ideal for development and quick exploration.

## Prerequisites

- Python 3.10+
- `data_jobs.csv` placed in the project root or `Docs/` folder

---

## Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 2 — Ingest CSV into SQLite

```bash
python tools/ingest_sqlite.py
```

Creates `jobs_db.sqlite` in the project root with a `staging_jobs` table containing all raw rows.

Expected log output:
```
INFO Found CSV at Docs/data_jobs.csv
INFO Read XXXXX rows from CSV
INFO Wrote staging table `staging_jobs` to jobs_db.sqlite (XXXXX rows)
INFO Staging row count: XXXXX
```

Environment variable to change the DB path (optional):
```bash
export JOBS_DB_PATH=custom_path/jobs.sqlite
python tools/ingest_sqlite.py
```

---

## Step 3 — Transform to 3NF

```bash
python tools/transform_sqlite.py
```

Creates the following tables inside `jobs_db.sqlite`:

| Table | Description |
|---|---|
| `companies` | Unique companies with surrogate key |
| `locations` | Unique location strings + country |
| `skills` | Unique skills with surrogate key |
| `jobs` | Core job postings with FK to companies and locations |
| `job_skills` | Junction table (job ↔ skill, many-to-many) |

---

## Step 4 — (Optional) Simulate dbt run on SQLite

```bash
python tools/run_dbt_sqlite.py
```

Simulates `dbt run` and `dbt test` logic against SQLite — useful to validate model logic without a Postgres connection.

---

## Step 5 — (Optional) Query the results

```bash
python tools/query_sqlite.py
```

Runs sample queries against the 3NF tables and prints results to the console.

---

## Step 6 — Run unit tests

```bash
pytest
```

Runs tests for the ingestion helpers (`parse_semi_struct`, `_to_bool_int`).

---

## Summary

```bash
pip install -r requirements.txt
python tools/ingest_sqlite.py
python tools/transform_sqlite.py
pytest
```

| Step | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Ingest | `python tools/ingest_sqlite.py` |
| Transform | `python tools/transform_sqlite.py` |
| Simulate dbt | `python tools/run_dbt_sqlite.py` |
| Query | `python tools/query_sqlite.py` |
| Unit tests | `pytest` |
