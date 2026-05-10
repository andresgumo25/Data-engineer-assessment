Data Engineer Assessment — Implementation README

Design decisions
- Ingestion: lightweight Python script (ingest_sqlite.py) to ingest data_jobs.csv into a local SQLite staging table for ease of local testing without Docker.
- Transformations: dbt-core project (models/) implements the 3NF model (Jobs, Companies, Skills, Locations, Job_Skills). dbt is configured for Postgres in profiles.yml.example; use PostgreSQL for production runs.
- Schema: schema.sql contains DDL for the 3NF model (Postgres dialect) and serves as the ERD textual artifact.
- Testing: pytest tests for ingestion utilities; dbt schema.yml includes basic dbt tests (unique/not_null).

Execution instructions (local)
1. Prepare environment
   - Copy .env.example to .env and adjust if needed.
   - Install Python deps: python -m pip install -r requirements.txt

2. Ingest (SQLite)
   - Place data_jobs.csv in project root or Docs/
   - Run: python ingest_sqlite.py
   - This creates jobs_db.sqlite with a table `staging_jobs`.

3. Run dbt (Postgres recommended)
   - dbt requires a Postgres target. Use docker-compose.yml to start Postgres locally (or supply your own DB).
   - Populate the Postgres table `staging_jobs` (e.g., use the same ingestion script adapted to Postgres or use psql to import the CSV).
   - Configure ~/.dbt/profiles.yml based on profiles.yml.example.
   - Run: dbt run && dbt test

4. Tests
   - Unit tests (ingest utilities): pytest
   - DB tests: dbt test (after connecting to Postgres and running models)

Notes

See docs/explicacion.md for full implementation details and run instructions.
- Credentials are not hardcoded; use .env and profiles.yml for dbt.
- For quick local experimentation, SQLite is provided; for full dbt runs use Postgres.

Note: The dataset Docs/data_jobs.csv has been intentionally excluded from this repository and is not provided here.

Next steps / Bonus
- Add CI: GitHub Actions to run pytest and (optionally) dbt tests against a Postgres service.
- Add orchestration with Prefect/Airflow as needed.
