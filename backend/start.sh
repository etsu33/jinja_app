
#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Repairing FeatureUsage table..."
python manage.py repair_featureusage_table

echo "Starting gunicorn..."
exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT}


