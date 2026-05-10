"""Transform staging_jobs in Postgres into 3NF tables (companies, locations, skills, jobs, job_skills).

Usage: python transform_postgres.py
Reads connection from .env (POSTGRES_*) and writes tables into the same database.
"""
import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import pandas as pd

load_dotenv()
POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB','jobs_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def parse_skills(val):
    # Handle None
    if val is None:
        return []
    # If it's already a list or tuple
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if x is not None]
    # If it's a dict (e.g., json object), try to extract lists inside
    if isinstance(val, dict):
        # flatten dict values that are lists
        res = []
        for v in val.values():
            if isinstance(v, (list, tuple)):
                res.extend([str(x).strip() for x in v if x is not None])
        return res
    # If it's a string
    if isinstance(val, str):
        s = val.strip()
        if s == '':
            return []
        try:
            obj = json.loads(s)
            if isinstance(obj, list):
                return [str(x).strip() for x in obj if x is not None]
            if isinstance(obj, dict):
                res = []
                for v in obj.values():
                    if isinstance(v, (list, tuple)):
                        res.extend([str(x).strip() for x in v if x is not None])
                return res
        except Exception:
            pass
        try:
            from ast import literal_eval
            obj = literal_eval(s)
            if isinstance(obj, (list, tuple)):
                return [str(x).strip() for x in obj if x is not None]
        except Exception:
            pass
        return [x.strip() for x in s.split(',') if x.strip()]
    # Fallback
    return [str(val).strip()]


def main():
    conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
    try:
        # Ensure target tables exist (create from schema if needed)
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS job_skills')
        cur.execute('DROP TABLE IF EXISTS jobs')
        cur.execute('DROP TABLE IF EXISTS skills')
        cur.execute('DROP TABLE IF EXISTS locations')
        cur.execute('DROP TABLE IF EXISTS companies')
        conn.commit()

        create_sql = '''
        CREATE TABLE IF NOT EXISTS companies (
          company_id TEXT PRIMARY KEY,
          company_name TEXT
        );
        CREATE TABLE IF NOT EXISTS locations (
          location_id TEXT PRIMARY KEY,
          location_string TEXT,
          country TEXT
        );
        CREATE TABLE IF NOT EXISTS skills (
          skill_id TEXT PRIMARY KEY,
          skill TEXT
        );
        CREATE TABLE IF NOT EXISTS jobs (
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
          salary_year_avg NUMERIC,
          salary_hour_avg NUMERIC,
          search_location TEXT
        );
        CREATE TABLE IF NOT EXISTS job_skills (
          id TEXT PRIMARY KEY,
          job_id TEXT REFERENCES jobs(job_id),
          skill_id TEXT REFERENCES skills(skill_id)
        );
        '''
        cur.execute(create_sql)
        conn.commit()

        # Read staging into pandas in chunks to avoid memory pressure
        sql = 'SELECT * FROM staging_jobs'
        df_iter = pd.read_sql_query(sql, conn, chunksize=100000)

        # We'll accumulate companies, locations, skills, job_skills, and jobs in DB tables progressively

        companies_set = set()
        locations_set = set()
        skills_set = set()

        # Temporary lists to bulk insert at end
        jobs_rows = []
        job_skills_rows = []

        total = 0
        for chunk in df_iter:
            chunk = chunk.copy()
            # compute job_id
            def make_job_id(r):
                title = str(r.get('job_title') or '')
                company = str(r.get('company_name') or '')
                posted = r.get('job_posted_date')
                posted_str = ''
                if pd.notna(posted) and posted is not None:
                    posted_str = str(posted)
                return md5(title + '||' + company + '||' + posted_str)

            chunk['job_id'] = chunk.apply(make_job_id, axis=1)

            # dedupe within chunk: keep first occurrence
            chunk.drop_duplicates(subset=['job_id'], inplace=True)

            for _, r in chunk.iterrows():
                total += 1
                # companies
                comp = r.get('company_name')
                if comp and comp not in companies_set:
                    companies_set.add(comp)
                # locations
                loc = r.get('job_location')
                ctry = r.get('job_country')
                if loc and loc not in locations_set:
                    locations_set.add((loc, ctry))
                # skills
                skills = parse_skills(r.get('job_skills'))
                for s in skills:
                    if s and s not in skills_set:
                        skills_set.add(s)
                    job_skills_rows.append((md5(str(r['job_id']) + '||' + s), r['job_id'], md5(s)))
                # jobs row
                jobs_rows.append((r['job_id'], r.get('job_title'), r.get('job_title_short'), md5(str(comp)) if comp else None,
                                  md5(str(loc)) if loc else None, r.get('job_via'), r.get('job_schedule_type'),
                                  bool(r.get('job_work_from_home')) if r.get('job_work_from_home') not in (None,'') else None,
                                  pd.to_datetime(r.get('job_posted_date')) if r.get('job_posted_date') not in (None,'') else None,
                                  bool(r.get('job_no_degree_mention')) if r.get('job_no_degree_mention') not in (None,'') else None,
                                  bool(r.get('job_health_insurance')) if r.get('job_health_insurance') not in (None,'') else None,
                                  float(r.get('salary_year_avg')) if r.get('salary_year_avg') not in (None,'') else None,
                                  float(r.get('salary_hour_avg')) if r.get('salary_hour_avg') not in (None,'') else None,
                                  r.get('search_location')))

        print(f'Accumulated: companies={len(companies_set)} locations={len(locations_set)} skills={len(skills_set)} jobs={len(jobs_rows)} job_skills={len(job_skills_rows)}')

        # Insert companies
        comp_rows = [(md5(c), c) for c in companies_set]
        if comp_rows:
            psycopg2.extras.execute_values(cur, "INSERT INTO companies (company_id, company_name) VALUES %s ON CONFLICT (company_id) DO NOTHING", comp_rows)
            conn.commit()
        # Insert locations
        loc_rows = [(md5(l[0]), l[0], l[1]) for l in locations_set]
        if loc_rows:
            psycopg2.extras.execute_values(cur, "INSERT INTO locations (location_id, location_string, country) VALUES %s ON CONFLICT (location_id) DO NOTHING", loc_rows)
            conn.commit()
        # Insert skills
        skill_rows = [(md5(s), s) for s in skills_set]
        if skill_rows:
            psycopg2.extras.execute_values(cur, "INSERT INTO skills (skill_id, skill) VALUES %s ON CONFLICT (skill_id) DO NOTHING", skill_rows)
            conn.commit()
        # Insert jobs (in chunks)
        if jobs_rows:
            psycopg2.extras.execute_values(cur, "INSERT INTO jobs (job_id, job_title, job_title_short, company_id, location_id, job_via, job_schedule_type, job_work_from_home, job_posted_date, job_no_degree_mention, job_health_insurance, salary_year_avg, salary_hour_avg, search_location) VALUES %s ON CONFLICT (job_id) DO NOTHING", jobs_rows, page_size=1000)
            conn.commit()
        # Insert job_skills
        if job_skills_rows:
            psycopg2.extras.execute_values(cur, "INSERT INTO job_skills (id, job_id, skill_id) VALUES %s ON CONFLICT (id) DO NOTHING", job_skills_rows, page_size=1000)
            conn.commit()

        print('Transform to 3NF completed in Postgres')

    finally:
        conn.close()

if __name__ == '__main__':
    main()
