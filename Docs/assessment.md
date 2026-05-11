# Data Engineer Technical Assessment

## 1. Introduction and Purpose

This technical assessment is a practical challenge designed to evaluate data engineering skills, design capabilities, and technical reasoning. The mission is to develop a data pipeline that transforms a raw data source into a well-structured and normalized relational model.

---

## 2. Dataset and Data Dictionary

**Context:** You are working at a technology market intelligence consulting firm. The goal is to process and model job postings to create a robust database that will serve as the "single source of truth" for future analysis and applications.

**Dataset:** `data_jobs.csv`

| Column Name | Description | Type | Source |
|---|---|---|---|
| `job_title_short` | Cleaned/standardized job title (e.g., Data Scientist) | Calculated | From `job_title` |
| `job_title` | Full original job title as scraped | Raw | Scraped |
| `job_location` | Location string shown in the job posting | Raw | Scraped |
| `job_via` | Platform where the job was posted (e.g., LinkedIn) | Raw | Scraped |
| `job_schedule_type` | Type of schedule (Full-time, Contractor, etc.) | Raw | Scraped |
| `job_work_from_home` | Indicates whether the job is remote (true/false) | Boolean | Parsed |
| `search_location` | Location used for the search that generated the data | Generated | Bot logic |
| `job_posted_date` | Date and time when the job was posted | Raw | Scraped |
| `job_no_degree_mention` | Indicates if "no degree required" is mentioned | Boolean | Parsed |
| `job_health_insurance` | Indicates if the posting mentions health insurance | Boolean | Parsed |
| `job_country` | Country extracted from the location | Calculated | Parsed |
| `salary_rate` | Indicates if the salary is annual or hourly | Raw | Scraped |
| `salary_year_avg` | Average yearly salary (calculated) | Calculated | Derived |
| `salary_hour_avg` | Average hourly salary (calculated) | Calculated | Derived |
| `company_name` | Name of the company posting the job | Raw | Scraped |
| `job_skills` | List of skills (e.g., `['Python', 'SQL']`) | Parsed List | NLP Extracted |
| `job_type_skills` | Dictionary grouping skills by type | Parsed Dict | NLP Extracted |

---

## 3. Pipeline Implementation and 3NF Model

### Phase 1: Ingestion and Initial Load

Develop a Python script that reads `data_jobs.csv` and loads it into a database table.

> **Ingestion Challenge:** The script must correctly handle semi-structured columns like `job_skills` (lists) and `job_type_skills` (dictionaries), loading them as appropriate data types.

### Phase 2: Relational Model Design and Implementation (3NF)

This is the core part of the assessment. The task is to design and implement the transformation of data from the initial table into a normalized relational model (3rd Normal Form).

**Implementation options** (use the one you are most comfortable with):
- A Python script for the transformation logic
- Transformation models in **dbt**
- A combination of both
- Raw SQL

**Key Model Requirements:**

1. **Normalization:** Create separate tables for the main entities (`Jobs`, `Companies`, `Skills`, `Locations`, etc.), connected by foreign keys.
2. **Relationships:** Correctly resolve the many-to-many relationship between `Jobs` and `Skills`.
3. **Cleaning and Standardization:** The process should unify and clean the data.

**Required Deliverable:** A clear Entity-Relationship Diagram (e.g., created with [dbdiagram.io](https://dbdiagram.io)) or a `schema.sql` file defining the DDL of the 3NF model.

---

## 4. Technical Requirements

| Requirement | Detail |
|---|---|
| **Database** | PostgreSQL orchestrated with Docker Compose (SQLite or another DB is acceptable with justification) |
| **Git** | Repository with a clean and semantic commit history |
| **Dependencies** | `requirements.txt` required. Use of Poetry, PDM, or `uv` is a plus |
| **Security** | Do not hardcode credentials — use environment variables (`.env`) |
| **Logging** | Implement clear logging to track pipeline execution |

### Testing

- **Unit Tests:** pytest for critical functions of transformation or extraction logic in Python.
- **Data Quality Tests:**
  - If using dbt: include `dbt test`
  - If using Python: consider libraries like [Pandera](https://pandera.readthedocs.io) or [Great Expectations](https://greatexpectations.io) to validate dataframes before loading

---

## 5. Documentation (README.md)

Documentation is a fundamental deliverable. The README must include:

- **Design Decisions:** The most important section. Justify your architecture, the decisions made when designing the 3NF model, and why certain tools or ETL methods were chosen.
- **Execution Instructions:** Clear steps for anyone to set up the environment and run the complete pipeline.
- **Testing Guide:** How to run the implemented tests.

---

## 6. Bonus Points

### 6.1. Orchestration and CI/CD

- **Orchestration:** Integrate the pipeline into an orchestrator like Airflow, Prefect, or Dagster.
- **CI/CD:** Implement a basic GitHub Actions pipeline for linting and testing.

### 6.2. Conceptual Design of an Analytical Model (OLAP)

> **Note:** Implementation is not required — a conceptual description in the README is sufficient.

Describe how you would design a **Star Schema** from the 3NF model to power a Business Intelligence dashboard. Cover the following points:

- **Fact Table:** What would it be? What would be the granularity of each row?
- **Dimensions:** What would be the main dimensions? (e.g., `dim_company`, `dim_date`)
- **Measures:** What would be the key numerical metrics in the fact table?
- **Design Challenges:**
  - How would you handle `job_skills` in the OLAP model? (e.g., bridge table)
  - How would you handle the multiple boolean flags (e.g., `job_work_from_home`, `job_no_degree_mention`, `job_health_insurance`)? (e.g., junk dimension)

---

## 7. Submission

Deliver a link to your Git repository.

> We look forward to seeing your solution and, above all, understanding the engineering reasoning behind it. Best of luck!
