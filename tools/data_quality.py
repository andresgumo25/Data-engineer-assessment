"""Simple data quality checks using SQL against Postgres.
Exits with non-zero code if any check fails.
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

load_dotenv()
USER = os.getenv('POSTGRES_USER','postgres')
PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
DB = os.getenv('POSTGRES_DB','jobs_db')
HOST = os.getenv('POSTGRES_HOST','localhost')
PORT = os.getenv('POSTGRES_PORT','5432')

conn = psycopg2.connect(dbname=DB, user=USER, password=PASSWORD, host=HOST, port=PORT)
cur = conn.cursor()
failed = False

checks = [
    ("staging_job_id_not_null", "SELECT COUNT(1) FROM staging_jobs WHERE job_title IS NULL OR job_title = ''"),
    ("stg_job_id_duplicates", "SELECT COUNT(1) - COUNT(DISTINCT md5(coalesce(job_title,'') || '||' || coalesce(company_name,'') || '||' || coalesce(job_posted_date::text,''))) FROM staging_jobs"),
    ("jobs_count_positive", "SELECT COUNT(1) FROM jobs"),
    ("companies_present", "SELECT COUNT(1) FROM companies"),
    ("skills_present", "SELECT COUNT(1) FROM skills"),
]

for name, q in checks:
    try:
        cur.execute(q)
        res = cur.fetchone()
        val = res[0] if res else None
        print(f"{name}: {val}")
        # basic failure conditions
        if name == 'stg_job_id_duplicates' and val and int(val) > 0:
            print('FAIL: staging has duplicate computed job ids')
            failed = True
        if name == 'jobs_count_positive' and (not val or int(val) == 0):
            print('FAIL: jobs table empty')
            failed = True
        if name == 'companies_present' and (not val or int(val) == 0):
            print('FAIL: companies empty')
            failed = True
        if name == 'skills_present' and (not val or int(val) == 0):
            print('FAIL: skills empty')
            failed = True
    except Exception as e:
        print(f"ERROR running check {name}: {e}")
        failed = True

cur.close()
conn.close()

if failed:
    print('\nData quality checks FAILED')
    sys.exit(2)
else:
    print('\nAll data quality checks passed')
    sys.exit(0)
