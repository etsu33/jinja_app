#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput
python manage.py migrate temples 0083 --noinput

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table

echo "Bootstrapping production data..."
python manage.py bootstrap_production_data

echo "Starting gunicorn on PORT=${PORT:-10000}..."
exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 --access-logfile - --error-logfile - --capture-output
