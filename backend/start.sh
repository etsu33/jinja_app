#!/usr/bin/env bash
set -e

export PORT="${PORT:-10000}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"

echo "=== Render startup ==="
echo "PWD=$(pwd)"
echo "PORT=${PORT}"
echo "WEB_CONCURRENCY=${WEB_CONCURRENCY}"
echo "DATABASE_URL_SET=$([ -n "${DATABASE_URL:-}" ] && echo 1 || echo 0)"
echo "ALLOWED_HOSTS=${ALLOWED_HOSTS:-unset}"
echo "RENDER_EXTERNAL_HOSTNAME=${RENDER_EXTERNAL_HOSTNAME:-unset}"
echo "USE_GIS=${USE_GIS:-unset}"
echo "USE_SQLITE=${USE_SQLITE:-unset}"

if [ "${RUN_STARTUP_CHECK:-0}" = "1" ]; then
  echo "Running startup system check because RUN_STARTUP_CHECK=1..."
  python manage.py check
fi

if [ "${RUN_MIGRATIONS_ON_START:-0}" = "1" ]; then
  echo "Running migrations because RUN_MIGRATIONS_ON_START=1..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations. Set RUN_MIGRATIONS_ON_START=1 to run them on startup."
fi

if [ "${RUN_SHRINE_REFLECTION_REPAIR:-0}" = "1" ]; then
  echo "Ensuring ShrineReflection table exists because RUN_SHRINE_REFLECTION_REPAIR=1..."
  python manage.py shell <<'PY'
from django.db import connection
from temples.models import ShrineReflection

table_name = ShrineReflection._meta.db_table
exists = table_name in connection.introspection.table_names()
print("HAS ShrineReflection table after migrate=", exists, "table=", table_name)

if not exists:
    print("Creating missing ShrineReflection table via schema_editor because migration state and DB schema are inconsistent")
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(ShrineReflection)
    print("Created ShrineReflection table")

print("HAS ShrineReflection table final=", table_name in connection.introspection.table_names())
PY
else
  echo "Skipping ShrineReflection repair. Set RUN_SHRINE_REFLECTION_REPAIR=1 to run it explicitly."
fi

if [ "${RUN_FAVORITE_REPAIR_ON_START:-0}" = "1" ]; then
  echo "Repairing Favorite table because RUN_FAVORITE_REPAIR_ON_START=1..."
  python manage.py repair_favorite_table || echo "repair_favorite_table failed; continue startup"
else
  echo "Skipping Favorite table repair. Set RUN_FAVORITE_REPAIR_ON_START=1 to run it explicitly."
fi

if [ "${RUN_FEATUREUSAGE_REPAIR_ON_START:-0}" = "1" ]; then
  echo "Repairing FeatureUsage table because RUN_FEATUREUSAGE_REPAIR_ON_START=1..."
  python manage.py repair_featureusage_table
  echo "FeatureUsage repair completed."
else
  echo "Skipping FeatureUsage repair. Set RUN_FEATUREUSAGE_REPAIR_ON_START=1 to run it explicitly."
fi

if [ "${RUN_BOOTSTRAP_ON_START:-0}" = "1" ]; then
  if python manage.py showmigrations temples | grep -q "\[X\] 0083"; then
    echo "Bootstrapping production data because RUN_BOOTSTRAP_ON_START=1..."
    python manage.py bootstrap_production_data
  else
    echo "Bootstrap migration is not applied. Falling back to direct seed/backfill because RUN_BOOTSTRAP_ON_START=1..."
    python manage.py import_shrines_seed
    python manage.py backfill_goriyaku_tags --with-visit-style --force
  fi
else
  echo "Skipping production data bootstrap. Set RUN_BOOTSTRAP_ON_START=1 to run it explicitly."
fi

echo "Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn shrine_project.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY}" --timeout 120 --worker-tmp-dir /dev/shm --access-logfile - --error-logfile - --capture-output
