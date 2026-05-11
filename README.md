# Data Engineer Technical Assessment

Pipeline that ingests, normalizes, and models job postings from a raw CSV into a 3NF relational database. Two fully working execution flows are provided: a lightweight **SQLite** path for local development and a production-grade **PostgreSQL + dbt** path.

---

## Architecture

```
data_jobs.csv
     │
     ▼
┌─────────────┐     ┌──────────────────────────────┐
│  Ingestion  │────▶│  staging_jobs  (raw table)   │
└─────────────┘     └──────────────────────────────┘
                                  │
                       ┌──────────▼──────────┐
                       │  Transformation     │
                       │  (dbt  or  Python)  │
                       └──────────┬──────────┘
                                  │
             ┌────────────────────┼───────────────────┐
             ▼                    ▼                   ▼
        companies             locations            skills
             │                                       │
             └─────────────▶ jobs ◀──────────────────┘
                                  │
                                  ▼
                             job_skills
```

---

## Repository Structure

```
├── tools/
│   ├── ingest_sqlite.py           # Ingest CSV → SQLite staging
│   ├── ingest_postgres.py         # Ingest CSV → Postgres staging
│   ├── transform_sqlite.py        # 3NF transform (SQLite, no dbt)
│   ├── transform_postgres.py      # 3NF transform (Postgres, no dbt)
│   ├── query_sqlite.py            # Query helper (SQLite)
│   ├── query_postgres.py          # Query helper (Postgres)
│   ├── data_quality.py            # Post-load data quality checks
│   └── run_dbt_sqlite.py          # Simulates dbt run on SQLite
├── dbt/
│   ├── models/
│   │   ├── staging/stg_jobs.sql   # Deduplication + casting
│   │   └── marts/                 # companies, locations, skills, jobs, job_skills
│   ├── dbt_project.yml
│   └── profiles.yml.example
├── Docs/
│   ├── assessment.md              # Original assessment instructions
│   ├── schema.sql                 # DDL for the 3NF model (Postgres)
│   ├── erd.png                    # Entity-Relationship Diagram
│   ├── erd.dbml                   # ERD source (dbdiagram.io)
│   ├── guide_sqlite_flow.md       # Step-by-step: SQLite flow
│   └── guide_postgres_dbt_flow.md # Step-by-step: Postgres + dbt flow
├── tests/
│   └── test_ingest_utils.py       # Unit tests for parse/normalize helpers
├── .github/workflows/
│   ├── ci.yml                     # Unit tests on every push
│   └── ci_dbt_quality.yml         # Postgres + dbt + data quality on push
├── docker-compose.yml             # Postgres 15 service
├── .env.example                   # Environment variables template
├── requirements.txt
└── pytest.ini
```

---

## Design Decisions

### 3NF Model

The raw CSV collapses company, location, and skills into every row. Normalizing to 3NF:

- **`companies`** and **`locations`** eliminate repeating scalar attributes.
- **`skills`** + **`job_skills`** (junction table) resolve the many-to-many relationship — one row per `(job, skill)` pair.
- `job_id` is a deterministic MD5 hash of `(job_title || company_name || job_posted_date)`, enabling idempotent loads and deduplication without a sequence column.

### Tool Choices

| Decision | Choice | Reason |
|---|---|---|
| Transformation layer | dbt (primary) | Modular SQL, built-in tests, lineage graph |
| Alternative transform | Python scripts | Same logic without dbt; easier to debug in isolation |
| Local development DB | SQLite | Zero-config, no Docker needed to iterate |
| Production DB | PostgreSQL 15 | `JSONB` for semi-structured fields, referential integrity |
| Semi-structured parsing | `ast.literal_eval` → JSON | CSV stores Python-literal lists (`['Python','SQL']`), not standard JSON |
| Boolean normalization | Explicit string mapping | Raw values are strings (`'True'`/`'False'`), not SQL booleans |

### Dual-Flow Strategy

Both flows produce the same 3NF output and can be run independently:

| | SQLite flow | Postgres + dbt flow |
|---|---|---|
| Use case | Local dev, quick validation | CI, staging, production |
| Ingestion | `tools/ingest_sqlite.py` | `tools/ingest_postgres.py` |
| Transform | `tools/transform_sqlite.py` | `dbt run` |
| Tests | `pytest` | `dbt test` + `pytest` |

---

## Prerequisites

- Python 3.10+
- Docker (Postgres + dbt flow only)
- dbt-core 1.5 (installed via `requirements.txt`)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in Postgres credentials if using that flow
```

---

## Running the Pipeline

See the step-by-step guides:

- **[SQLite flow](Docs/guide_sqlite_flow.md)** — no Docker, runs in minutes
- **[Postgres + dbt flow](Docs/guide_postgres_dbt_flow.md)** — production-grade, uses Docker Compose

---

## Testing

```bash
# Unit tests (parse + normalize helpers)
pytest

# dbt data quality tests (requires Postgres flow to have run first)
cd dbt
dbt test --profiles-dir .
```

CI runs both automatically on every push — see `.github/workflows/`.

---

## CI/CD

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push / PR | Installs deps, runs `pytest` |
| `ci_dbt_quality.yml` | push / PR | Spins Postgres, runs ingest → dbt run → dbt test → data_quality.py |

---

## OLAP / Star Schema — Conceptual Design

> Describes a Star Schema layer that could be built on top of the 3NF model to power BI dashboards.

### Fact Table — `fact_job_postings`

One row per job posting (same grain as the 3NF `jobs` table).

| Column | Type | Notes |
|---|---|---|
| `job_id` (PK) | TEXT | Surrogate from 3NF |
| `company_key` | INT | FK → `dim_company` |
| `location_key` | INT | FK → `dim_location` |
| `date_key` | INT | FK → `dim_date` |
| `flags_key` | INT | FK → `dim_job_flags` (junk dimension) |
| `salary_year_avg` | NUMERIC | Measure |
| `salary_hour_avg` | NUMERIC | Measure |

### Dimensions

| Dimension | Grain | Key columns |
|---|---|---|
| `dim_company` | One row per company | `company_key`, `company_name` |
| `dim_location` | One row per location string | `location_key`, `location_string`, `country` |
| `dim_date` | One row per calendar day | `date_key`, `year`, `month`, `quarter`, `day_of_week` |
| `dim_job_flags` | One row per boolean combination | `flags_key`, `is_remote`, `no_degree_mention`, `health_insurance` |

### Bridge Table — `bridge_job_skills`

Skills are many-to-many and cannot be flattened into the fact table (unbounded columns) or into a dimension without row fanout. A bridge table avoids both problems:

```
fact_job_postings  ◀──  bridge_job_skills  ──▶  dim_skill
```

Each row is a `(job_id, skill_key)` pair. BI tools join via the bridge to count skills per job or aggregate across skill categories.

### Junk Dimension — `dim_job_flags`

The three boolean flags (`job_work_from_home`, `job_no_degree_mention`, `job_health_insurance`) have only 2³ = 8 possible combinations. A junk dimension pre-materializes all combinations, replacing three FK columns in the fact table with a single `flags_key`. This keeps the fact table narrow and simplifies filter queries in dashboards.

### Key Measures

| Measure | Aggregation |
|---|---|
| `salary_year_avg` | AVG, MIN, MAX per dimension |
| `salary_hour_avg` | AVG, MIN, MAX per dimension |
| `COUNT(job_id)` | Total postings (fully additive) |
| Remote salary premium | `AVG(salary_year_avg) FILTER (WHERE is_remote = true)` vs overall AVG |
