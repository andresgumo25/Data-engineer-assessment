"""Ingest data_jobs.csv into PostgreSQL staging table using psycopg2.

Usage: python ingest_postgres.py

Reads DB connection from environment variables (.env): POSTGRES_USER, POSTGRES_PASSWORD,
POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT.
"""
import os
import ast
import json
from pathlib import Path
import logging
import psycopg2
import psycopg2.extras
import pandas as pd
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    def load_dotenv():
        return None

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

CSV_PATHS = [Path('data_jobs.csv'), Path('Docs') / 'data_jobs.csv']

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

TABLE_NAME = 'staging_jobs'


def find_csv():
    for p in CSV_PATHS:
        if p.exists():
            logging.info(f'Found CSV at {p}')
            return p
    logging.error('data_jobs.csv not found')
    return None


def parse_semi_struct(val):
    if pd.isna(val):
        return None
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, str):
        s = val.strip()
        if s == '':
            return None
        try:
            obj = json.loads(s)
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            pass
        try:
            obj = ast.literal_eval(s)
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            pass
        return s
    return str(val)


def to_bool(x):
    if pd.isna(x):
        return None
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in ('true', 't', 'yes', '1'):
        return True
    if s in ('false', 'f', 'no', '0'):
        return False
    return None


def create_table(conn):
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    cur.execute(f"""
    CREATE TABLE {TABLE_NAME} (
      job_title TEXT,
      job_title_short TEXT,
      job_location TEXT,
      job_via TEXT,
      job_schedule_type TEXT,
      job_work_from_home BOOLEAN,
      search_location TEXT,
      job_posted_date TIMESTAMP,
      job_no_degree_mention BOOLEAN,
      job_health_insurance BOOLEAN,
      job_country TEXT,
      salary_rate TEXT,
      salary_year_avg NUMERIC,
      salary_hour_avg NUMERIC,
      company_name TEXT,
      job_skills JSONB,
      job_type_skills JSONB
    )
    """)
    conn.commit()
    cur.close()


def insert_rows(conn, df):
    # Prepare rows
    cols = ['job_title','job_title_short','job_location','job_via','job_schedule_type',
            'job_work_from_home','search_location','job_posted_date','job_no_degree_mention',
            'job_health_insurance','job_country','salary_rate','salary_year_avg','salary_hour_avg',
            'company_name','job_skills','job_type_skills']

    rows = []
    for _, r in df.iterrows():
        # Prepare JSONB values using psycopg2.extras.Json wrapper
        job_skills_val = None
        if r.get('job_skills'):
            try:
                job_skills_val = psycopg2.extras.Json(json.loads(r.get('job_skills')))
            except Exception:
                job_skills_val = psycopg2.extras.Json(r.get('job_skills'))
        job_type_skills_val = None
        if r.get('job_type_skills'):
            try:
                job_type_skills_val = psycopg2.extras.Json(json.loads(r.get('job_type_skills')))
            except Exception:
                job_type_skills_val = psycopg2.extras.Json(r.get('job_type_skills'))

        row = [
            r.get('job_title'),
            r.get('job_title_short'),
            r.get('job_location'),
            r.get('job_via'),
            r.get('job_schedule_type'),
            to_bool(r.get('job_work_from_home')),
            r.get('search_location'),
            pd.to_datetime(r.get('job_posted_date')) if r.get('job_posted_date') is not None else None,
            to_bool(r.get('job_no_degree_mention')),
            to_bool(r.get('job_health_insurance')),
            r.get('job_country'),
            r.get('salary_rate'),
            (float(r.get('salary_year_avg')) if r.get('salary_year_avg') not in (None, '') else None),
            (float(r.get('salary_hour_avg')) if r.get('salary_hour_avg') not in (None, '') else None),
            r.get('company_name'),
            job_skills_val,
            job_type_skills_val,
        ]
        rows.append(row)

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            f"INSERT INTO {TABLE_NAME} ({', '.join(cols)}) VALUES %s",
            rows,
            template=None,
            page_size=1000
        )
    conn.commit()


def main():
    csv_path = find_csv()
    if not csv_path:
        return

    df = pd.read_csv(csv_path)
    logging.info(f'Read {len(df)} rows')

    for col in ('job_skills','job_type_skills'):
        if col in df.columns:
            df[col] = df[col].apply(parse_semi_struct)

    # Connect to Postgres
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

    try:
        create_table(conn)
        insert_rows(conn, df)
        logging.info('Inserted rows into Postgres staging table')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
