#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import os
import time
import MySQLdb

db_engine = os.getenv("DB_ENGINE", "sqlite").lower()
if db_engine != "mysql":
    print("SQLite mode enabled. Skipping MySQL wait.")
    raise SystemExit(0)

host = os.getenv("MYSQL_HOST", "mysql")
port = int(os.getenv("MYSQL_PORT", "3306"))
user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD", "")
database = os.getenv("MYSQL_DATABASE", "document_intelligence")

for _ in range(60):
    try:
        conn = MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=database)
        conn.close()
        print("MySQL is ready.")
        raise SystemExit(0)
    except Exception:
        time.sleep(2)

raise SystemExit("MySQL did not become ready in time.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true
exec "$@"
