import sqlite3
from pathlib import Path
DB_PATH = Path('jobs_db.sqlite')
if not DB_PATH.exists():
    print('Database not found:', DB_PATH)
    raise SystemExit(1)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

tables = ['staging_jobs','companies','locations','skills','jobs','job_skills']
for t in tables:
    print('\n-- {} (first 5) --'.format(t))
    try:
        cur.execute(f"SELECT * FROM {t} LIMIT 5")
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('Error querying', t, e)

conn.close()
