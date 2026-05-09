#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table

echo "Backfilling concierge recommendation tags..."
python manage.py backfill_goriyaku_tags --with-visit-style --force

echo "Starting gunicorn..."
exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT}
