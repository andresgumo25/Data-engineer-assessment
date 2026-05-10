"""Basic data-quality runner (lightweight) for Postgres

Usage: python tools/great_expectations_run_basic_checks.py
Reads connection info from environment variables (POSTGRES_*).
Returns exit code 0 if all checks pass, non-zero otherwise.
"""
import os
import sys
import psycopg2

POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB','jobs_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')

CHECKS = [
    ("staging_jobs_present", "SELECT COUNT(1) FROM staging_jobs" , lambda r: r[0] > 0),
    ("jobs_not_null_id", "SELECT COUNT(1) FROM jobs WHERE job_id IS NULL", lambda r: r[0] == 0),
    ("jobs_unique_ids", "SELECT COUNT(1) as cnt, COUNT(DISTINCT job_id) as distinct_cnt FROM jobs", lambda r: r[0] == r[1]),
    ("companies_count_positive", "SELECT COUNT(1) FROM companies", lambda r: r[0] > 0),
]


def run():
    conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
    cur = conn.cursor()
    failed = []
    for name, q, ok_fn in CHECKS:
        try:
            cur.execute(q)
            res = cur.fetchone()
            if not ok_fn(res):
                failed.append((name, q, res))
                print(f"CHECK FAILED {name}: query={q} result={res}")
            else:
                print(f"CHECK PASS {name}: {res}")
        except Exception as e:
            failed.append((name, q, str(e)))
            print(f"CHECK ERROR {name}: {e}")
    cur.close()
    conn.close()
    if failed:
        print(f"{len(failed)} checks failed")
        return 2
    print("All checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(run())