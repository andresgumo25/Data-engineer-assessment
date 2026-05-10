"""Simulate dbt run/test against the SQLite database created earlier.

Creates stg_jobs and marts (companies, locations, skills, job_skills, jobs) and runs simple tests
(unique/not_null) defined in models/schema.yml.
"""
import os
import json
import hashlib
from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path(os.getenv('JOBS_DB_PATH', 'jobs_db.sqlite'))

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def ensure_db():
    if not DB_PATH.exists():
        print(f"Database {DB_PATH} not found. Run ingest_sqlite.py first.")
        raise SystemExit(1)


def create_stg_jobs(conn):
    df = pd.read_sql_query('SELECT * FROM staging_jobs', conn)
    print(f'Creating stg_jobs from staging_jobs ({len(df)} rows)')

    def make_job_id(r):
        title = str(r.get('job_title') or '')
        company = str(r.get('company_name') or '')
        posted = r.get('job_posted_date')
        posted_str = ''
        if pd.notna(posted) and posted is not None:
            posted_str = str(posted)
        return md5(title + '||' + company + '||' + posted_str)

    df['job_id'] = df.apply(make_job_id, axis=1)

    # normalize booleans to 0/1
    for c in ['job_work_from_home','job_no_degree_mention','job_health_insurance']:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: 1 if str(x).lower() in ('1','true','t','yes') else 0 if pd.notna(x) else None)

    # Parse dates for deduplication and consistency
    if 'job_posted_date' in df.columns:
        df['job_posted_date'] = pd.to_datetime(df['job_posted_date'], errors='coerce')

    # Deduplicate by job_id keeping the most recent job_posted_date when available
    before = len(df)
    df.sort_values(['job_id','job_posted_date'], ascending=[True, False], inplace=True)
    df = df.drop_duplicates(subset=['job_id'], keep='first')
    after = len(df)
    print(f'Deduplicated stg_jobs: {before} -> {after} rows')

    # ensure columns exist used later
    df.to_sql('stg_jobs', conn, if_exists='replace', index=False)
    print('stg_jobs created')


def run_models(conn):
    # companies
    df = pd.read_sql_query('SELECT job_id, company_name, job_location, job_country, job_skills FROM stg_jobs', conn)
    companies = df[['company_name']].dropna().drop_duplicates().copy()
    companies['company_id'] = companies['company_name'].apply(lambda x: md5(str(x)))
    companies = companies[['company_id','company_name']]
    companies.to_sql('companies', conn, if_exists='replace', index=False)

    # locations
    locations = df[['job_location','job_country']].dropna(subset=['job_location']).drop_duplicates().copy()
    locations['location_id'] = locations['job_location'].apply(lambda x: md5(str(x)))
    locations = locations[['location_id','job_location','job_country']]
    locations.rename(columns={'job_location':'location_string','job_country':'country'}, inplace=True)
    locations.to_sql('locations', conn, if_exists='replace', index=False)

    # skills and job_skills
    def parse_skills(val):
        if pd.isna(val) or val is None:
            return []
        if isinstance(val, str):
            s = val.strip()
            if s == '':
                return []
            try:
                obj = json.loads(s)
                if isinstance(obj, list):
                    return [str(x).strip() for x in obj if x is not None]
            except Exception:
                try:
                    from ast import literal_eval
                    obj = literal_eval(s)
                    if isinstance(obj, (list, tuple)):
                        return [str(x).strip() for x in obj if x is not None]
                except Exception:
                    return [x.strip() for x in s.split(',') if x.strip()]
        if isinstance(val, (list, tuple)):
            return [str(x).strip() for x in val if x is not None]
        return [str(val).strip()]

    skills_rows = []
    job_skill_rows = []
    for _, r in df.iterrows():
        jid = r['job_id']
        skills = parse_skills(r.get('job_skills'))
        for s in skills:
            if s == '':
                continue
            skills_rows.append({'skill': s})
            job_skill_rows.append({'job_id': jid, 'skill': s})

    if skills_rows:
        skills_df = pd.DataFrame(skills_rows).drop_duplicates().copy()
        skills_df['skill_id'] = skills_df['skill'].apply(lambda x: md5(x))
        skills_df = skills_df[['skill_id','skill']]
        skills_df.to_sql('skills', conn, if_exists='replace', index=False)
    else:
        pd.DataFrame(columns=['skill_id','skill']).to_sql('skills', conn, if_exists='replace', index=False)

    if job_skill_rows:
        js_df = pd.DataFrame(job_skill_rows).drop_duplicates()
        sk = pd.read_sql_query('SELECT * FROM skills', conn)
        if not sk.empty:
            js_df = js_df.merge(sk, on='skill', how='left')
            js_df['id'] = js_df.apply(lambda r: md5(str(r['job_id']) + '||' + str(r['skill'])), axis=1)
            js_df = js_df[['id','job_id','skill_id']]
            js_df.to_sql('job_skills', conn, if_exists='replace', index=False)
        else:
            pd.DataFrame(columns=['id','job_id','skill_id']).to_sql('job_skills', conn, if_exists='replace', index=False)
    else:
        pd.DataFrame(columns=['id','job_id','skill_id']).to_sql('job_skills', conn, if_exists='replace', index=False)

    # jobs table
    jobs = pd.read_sql_query('SELECT * FROM stg_jobs', conn)
    comp_map = pd.read_sql_query('SELECT company_id, company_name FROM companies', conn)
    jobs = jobs.merge(comp_map, left_on='company_name', right_on='company_name', how='left')
    loc_map = pd.read_sql_query('SELECT location_id, location_string FROM locations', conn)
    jobs = jobs.merge(loc_map, left_on='job_location', right_on='location_string', how='left')

    jobs_table = jobs[['job_id','job_title','job_title_short','company_id','location_id','job_via','job_schedule_type',
                       'job_work_from_home','job_posted_date','job_no_degree_mention','job_health_insurance',
                       'salary_rate','salary_year_avg','salary_hour_avg','search_location']].copy()
    # Deduplicate jobs by job_id to ensure primary key uniqueness (keep most recent by job_posted_date if present)
    jobs_table.sort_values(['job_id','job_posted_date'], ascending=[True, False], inplace=True)
    jobs_table = jobs_table.drop_duplicates(subset=['job_id'], keep='first')
    jobs_table.to_sql('jobs', conn, if_exists='replace', index=False)

    print('Models created: companies, locations, skills, job_skills, jobs')


def run_tests(conn):
    tests = []
    # stg_jobs.job_id unique/not_null
    tests.append(('stg_jobs.job_id_not_null', "SELECT COUNT(1) FROM stg_jobs WHERE job_id IS NULL"))
    tests.append(('stg_jobs.job_id_unique', "SELECT COUNT(1) as cnt, COUNT(DISTINCT job_id) as distinct_cnt FROM stg_jobs"))
    # jobs.job_id unique/not_null
    tests.append(('jobs.job_id_not_null', "SELECT COUNT(1) FROM jobs WHERE job_id IS NULL"))
    tests.append(('jobs.job_id_unique', "SELECT COUNT(1) as cnt, COUNT(DISTINCT job_id) as distinct_cnt FROM jobs"))
    # companies.company_id tests
    tests.append(('companies.company_id_not_null', "SELECT COUNT(1) FROM companies WHERE company_id IS NULL"))
    tests.append(('companies.company_id_unique', "SELECT COUNT(1) as cnt, COUNT(DISTINCT company_id) as distinct_cnt FROM companies"))
    # skills.skill_id tests
    tests.append(('skills.skill_id_not_null', "SELECT COUNT(1) FROM skills WHERE skill_id IS NULL"))
    tests.append(('skills.skill_id_unique', "SELECT COUNT(1) as cnt, COUNT(DISTINCT skill_id) as distinct_cnt FROM skills"))
    # job_skills.id tests
    tests.append(('job_skills.id_not_null', "SELECT COUNT(1) FROM job_skills WHERE id IS NULL"))
    tests.append(('job_skills.id_unique', "SELECT COUNT(1) as cnt, COUNT(DISTINCT id) as distinct_cnt FROM job_skills"))

    all_pass = True
    cur = conn.cursor()
    for name, q in tests:
        try:
            cur.execute(q)
            res = cur.fetchone()
            if 'unique' in name:
                cnt, distinct_cnt = res[0], res[1]
                passed = (cnt == distinct_cnt)
                print(f"{name}: {cnt} rows, {distinct_cnt} distinct -> {'PASS' if passed else 'FAIL'}")
                if not passed:
                    all_pass = False
            else:
                val = res[0]
                passed = (val == 0)
                print(f"{name}: {val} nulls -> {'PASS' if passed else 'FAIL'}")
                if not passed:
                    all_pass = False
        except Exception as e:
            print(f"{name}: ERROR executing test: {e}")
            all_pass = False

    return all_pass


def main():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        create_stg_jobs(conn)
        run_models(conn)
        print('\nRunning tests...')
        ok = run_tests(conn)
        if ok:
            print('\nAll tests passed')
        else:
            print('\nSome tests failed')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
