"""Create the target Postgres database if it does not exist."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB','jobs_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')

# Connect to default 'postgres' database to create target
conn = psycopg2.connect(dbname='postgres', user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_DB,))
exists = cur.fetchone()
if not exists:
    print(f"Creating database {POSTGRES_DB}...")
    cur.execute(f"CREATE DATABASE {POSTGRES_DB}")
    print('Created')
else:
    print(f"Database {POSTGRES_DB} already exists")
cur.close()
conn.close()
