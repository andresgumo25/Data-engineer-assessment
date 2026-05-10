import sqlite3
from pathlib import Path
DB_PATH = Path('jobs_db.sqlite')
if not DB_PATH.exists():
    print('Database not found:', DB_PATH)
    raise SystemExit(1)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

queries = [
    ("Count staging", "SELECT COUNT(1) FROM staging_jobs"),
    ("Sample jobs", "SELECT job_id, job_title, company_id, location_id, job_posted_date FROM jobs LIMIT 5"),
    ("Sample companies", "SELECT * FROM companies LIMIT 5"),
    ("Sample locations", "SELECT * FROM locations LIMIT 5"),
    ("Sample skills", "SELECT * FROM skills LIMIT 5"),
    ("Counts", "SELECT 'staging_jobs' as table, COUNT(1) as cnt FROM staging_jobs UNION ALL SELECT 'jobs', COUNT(1) FROM jobs UNION ALL SELECT 'companies', COUNT(1) FROM companies UNION ALL SELECT 'locations', COUNT(1) FROM locations UNION ALL SELECT 'skills', COUNT(1) FROM skills UNION ALL SELECT 'job_skills', COUNT(1) FROM job_skills")
]

for title, q in queries:
    print('\n--', title, '--')
    try:
        cur.execute(q)
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('Error running query:', e)

conn.close()
