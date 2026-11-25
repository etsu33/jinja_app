-- SELECT-only. Safe to run against Production. Reports the latest applied
-- migration per app.
SELECT app, name, applied
FROM django_migrations
ORDER BY app, applied DESC;
