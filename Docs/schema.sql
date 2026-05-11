-- Schema DDL for 3NF model (Postgres dialect)

CREATE TABLE companies (
  company_id TEXT PRIMARY KEY,
  company_name TEXT
);

CREATE TABLE locations (
  location_id TEXT PRIMARY KEY,
  location_string TEXT,
  country TEXT
);

CREATE TABLE skills (
  skill_id TEXT PRIMARY KEY,
  skill TEXT
);

CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  job_title TEXT,
  job_title_short TEXT,
  company_id TEXT REFERENCES companies(company_id),
  location_id TEXT REFERENCES locations(location_id),
  job_via TEXT,
  job_schedule_type TEXT,
  job_work_from_home BOOLEAN,
  job_posted_date TIMESTAMP,
  job_no_degree_mention BOOLEAN,
  job_health_insurance BOOLEAN,
  salary_rate TEXT,
  salary_year_avg NUMERIC,
  salary_hour_avg NUMERIC,
  search_location TEXT
);

CREATE TABLE job_skills (
  id TEXT PRIMARY KEY,
  job_id TEXT REFERENCES jobs(job_id),
  skill_id TEXT REFERENCES skills(skill_id)
);

-- Indexes for production / query performance
CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_location_id ON jobs(location_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_job_id ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill_id ON job_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_companies_company_name ON companies(lower(company_name));
CREATE INDEX IF NOT EXISTS idx_skills_skill ON skills(lower(skill));

