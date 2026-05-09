#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table

echo "Debugging concierge candidate counts..."
python manage.py debug_concierge_candidates

echo "Backfilling concierge recommendation tags..."
python manage.py backfill_goriyaku_tags --with-visit-style --force

echo "Debugging concierge candidate counts after backfill..."
python manage.py debug_concierge_candidates

echo "Starting gunicorn on PORT=${PORT:-10000}..."
exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 --access-logfile - --error-logfile - --capture-output
