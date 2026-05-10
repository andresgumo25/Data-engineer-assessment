import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB','jobs_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')

conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
cur = conn.cursor()
for t in ['staging_jobs','companies','locations','skills','jobs','job_skills']:
    try:
        cur.execute(f'SELECT COUNT(1) FROM {t}')
        print(t, cur.fetchone()[0])
    except Exception as e:
        print(t, 'ERROR', e)
cur.close()
conn.close()
