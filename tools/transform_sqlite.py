"""Transform staging_jobs in jobs_db.sqlite into 3NF tables (SQLite).

Creates tables: companies, locations, skills, jobs, job_skills.
Prints row counts and sample rows.
"""
import os
import json
import hashlib
from pathlib import Path
import sqlite3
import pandas as pd
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    def load_dotenv():
        return None

DB_PATH = Path(os.getenv('JOBS_DB_PATH', 'jobs_db.sqlite'))

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


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
            # try python literal
            try:
                from ast import literal_eval
                obj = literal_eval(s)
                if isinstance(obj, (list, tuple)):
                    return [str(x).strip() for x in obj if x is not None]
            except Exception:
                # maybe comma-separated
                return [x.strip() for x in s.split(',') if x.strip()]
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if x is not None]
    return [str(val).strip()]


def main():
    if not DB_PATH.exists():
        print(f"Database {DB_PATH} not found. Run ingest_sqlite.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query('SELECT * FROM staging_jobs', conn)
        print(f'Read {len(df)} rows from staging_jobs')

        # Compute job_id
        def make_job_id(r):
            title = str(r.get('job_title') or '')
            company = str(r.get('company_name') or '')
            posted = r.get('job_posted_date')
            posted_str = ''
            if pd.notna(posted) and posted is not None:
                posted_str = str(posted)
            return md5(title + '||' + company + '||' + posted_str)

        df['job_id'] = df.apply(make_job_id, axis=1)

        # Companies
        companies = df[['company_name']].dropna().drop_duplicates().copy()
        companies['company_id'] = companies['company_name'].apply(lambda x: md5(str(x)))
        companies = companies[['company_id','company_name']]
        companies.to_sql('companies', conn, if_exists='replace', index=False)

        # Locations
        locations = df[['job_location','job_country']].dropna(subset=['job_location']).drop_duplicates().copy()
        locations['location_id'] = locations['job_location'].apply(lambda x: md5(str(x)))
        locations = locations[['location_id','job_location','job_country']]
        locations.rename(columns={'job_location':'location_string','job_country':'country'}, inplace=True)
        locations.to_sql('locations', conn, if_exists='replace', index=False)

        # Skills
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
            # create empty table
            pd.DataFrame(columns=['skill_id','skill']).to_sql('skills', conn, if_exists='replace', index=False)

        # job_skills junction
        if job_skill_rows:
            js_df = pd.DataFrame(job_skill_rows).drop_duplicates()
            # join to skills to get skill_id
            sk = pd.read_sql_query('SELECT * FROM skills', conn)
            js_df = js_df.merge(sk, left_on='skill', right_on='skill', how='left')
            js_df['id'] = js_df.apply(lambda r: md5(str(r['job_id']) + '||' + str(r['skill'])), axis=1)
            js_df = js_df[['id','job_id','skill_id']]
            js_df.to_sql('job_skills', conn, if_exists='replace', index=False)
        else:
            pd.DataFrame(columns=['id','job_id','skill_id']).to_sql('job_skills', conn, if_exists='replace', index=False)

        # Jobs table
        jobs = df.copy()
        # map company_id and location_id
        comp_map = pd.read_sql_query('SELECT company_id, company_name FROM companies', conn)
        jobs = jobs.merge(comp_map, left_on='company_name', right_on='company_name', how='left')
        loc_map = pd.read_sql_query('SELECT location_id, location_string FROM locations', conn)
        jobs = jobs.merge(loc_map, left_on='job_location', right_on='location_string', how='left')

        jobs_table = jobs[['job_id','job_title','job_title_short','company_id','location_id','job_via','job_schedule_type',
                           'job_work_from_home','job_posted_date','job_no_degree_mention','job_health_insurance',
                           'salary_rate','salary_year_avg','salary_hour_avg','search_location']].copy()
        jobs_table.to_sql('jobs', conn, if_exists='replace', index=False)

        # Print counts and samples
        def print_info(table):
            cur = conn.execute(f"SELECT COUNT(1) FROM {table}")
            cnt = cur.fetchone()[0]
            print(f"{table}: {cnt} rows")
            cur = conn.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cur.fetchall()
            if rows:
                print(f"Sample from {table}:")
                for r in rows:
                    print(r)

        print_info('companies')
        print_info('locations')
        print_info('skills')
        print_info('jobs')
        print_info('job_skills')

    finally:
        conn.close()

if __name__ == '__main__':
    main()
