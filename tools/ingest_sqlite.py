"""Ingest data_jobs.csv into a local SQLite staging table.

Usage: python ingest_sqlite.py

The script searches for data_jobs.csv in common locations, parses semi-structured
columns (job_skills, job_type_skills), normalizes boolean/date fields, and
writes a staging table `staging_jobs` into jobs_db.sqlite.
"""
import os
import csv
import json
import ast
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    def load_dotenv():
        return None
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
load_dotenv()

CANDIDATE_PATHS = [
    Path('data_jobs.csv'),
    Path('Docs') / 'data_jobs.csv',
    Path('docs') / 'data_jobs.csv',
    Path('data') / 'data_jobs.csv',
]

DB_PATH = Path(os.getenv('JOBS_DB_PATH', 'jobs_db.sqlite'))
TABLE_NAME = 'staging_jobs'


def find_csv():
    for p in CANDIDATE_PATHS:
        if p.exists():
            logging.info(f'Found CSV at {p}')
            return p
    logging.error('data_jobs.csv not found. Please place the dataset in project root or Docs/')
    return None


def parse_semi_struct(value):
    if pd.isna(value):
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        s = value.strip()
        if s == '':
            return None
        # Try JSON
        try:
            obj = json.loads(s)
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            pass
        # Try Python literal (e.g., "['Python', 'SQL']")
        try:
            obj = ast.literal_eval(s)
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            pass
        # Fallback: return string
        return s
    return str(value)


def normalize_booleans(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: _to_bool_int(x))
    return df


def _to_bool_int(x):
    if pd.isna(x):
        return None
    if isinstance(x, bool):
        return int(x)
    s = str(x).strip().lower()
    if s in ('true', 't', 'yes', '1'):
        return 1
    if s in ('false', 'f', 'no', '0'):
        return 0
    return None


def main():
    csv_path = find_csv()
    if not csv_path:
        return

    df = pd.read_csv(csv_path)
    logging.info(f'Read {len(df)} rows from CSV')

    # Parse semi-structured columns
    for col in ('job_skills', 'job_type_skills'):
        if col in df.columns:
            df[col] = df[col].apply(parse_semi_struct)

    # Normalize booleans
    df = normalize_booleans(df, ['job_work_from_home', 'job_no_degree_mention', 'job_health_insurance'])

    # Parse dates
    if 'job_posted_date' in df.columns:
        df['job_posted_date'] = pd.to_datetime(df['job_posted_date'], errors='coerce')

    # Ensure the DB file exists (sqlite will create it)
    conn = sqlite3.connect(DB_PATH)
    try:
        # Write to staging table
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
        logging.info(f'Wrote staging table `{TABLE_NAME}` to {DB_PATH} ({len(df)} rows)')

        # Quick sanity checks
        cur = conn.execute(f"SELECT COUNT(1) FROM {TABLE_NAME}")
        count = cur.fetchone()[0]
        logging.info(f'Staging row count: {count}')

    finally:
        conn.close()


if __name__ == '__main__':
    main()
