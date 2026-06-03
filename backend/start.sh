#!/usr/bin/env bash
set -e

echo "=== Render diagnostics ==="
echo "PWD=$(pwd)"
echo "PORT=${PORT:-unset}"
echo "WEB_CONCURRENCY=${WEB_CONCURRENCY:-unset}"
echo "DATABASE_URL_SET=$([ -n "${DATABASE_URL:-}" ] && echo 1 || echo 0)"
echo "ALLOWED_HOSTS=${ALLOWED_HOSTS:-unset}"
echo "RENDER_EXTERNAL_HOSTNAME=${RENDER_EXTERNAL_HOSTNAME:-unset}"
echo "USE_GIS=${USE_GIS:-unset}"
echo "USE_SQLITE=${USE_SQLITE:-unset}"
python manage.py check
python manage.py showmigrations temples | tail -20
python manage.py showmigrations temples | grep 0087 || true

echo "Running migrations..."
python manage.py migrate --noinput
python manage.py repair_favorite_table || echo "repair_favorite_table failed; continue startup"

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table
echo "FeatureUsage repair completed."

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
  echo "Skipping production data bootstrap on start. Set RUN_BOOTSTRAP_ON_START=1 to run it explicitly."
fi

export PORT="${PORT:-10000}"
echo "Final diagnostics before gunicorn:"
echo "PORT=${PORT}"
echo "WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}"
echo "Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn shrine_project.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY:-1}" --timeout 120 --worker-tmp-dir /dev/shm --log-level debug --access-logfile - --error-logfile - --capture-output
