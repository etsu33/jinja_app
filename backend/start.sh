#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

if ls temples/migrations/0083_*.py >/dev/null 2>&1; then
  echo "Applying bootstrap migration explicitly..."
  python manage.py migrate temples 0083 --noinput
else
  echo "Skipping explicit temples 0083 migration: file not found"
fi

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table

if python manage.py showmigrations temples | grep -q "\[X\] 0083"; then
  echo "Bootstrapping production data..."
  python manage.py bootstrap_production_data
else
  echo "Bootstrap migration is not applied. Falling back to direct seed/backfill..."
  python manage.py import_shrines_seed
  python manage.py backfill_goriyaku_tags --with-visit-style --force
fi

echo "Starting gunicorn on PORT=${PORT:-10000}..."
exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 --access-logfile - --error-logfile - --capture-output
