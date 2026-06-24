# Render startup operations

This app is configured so normal Render Web Service startups bind the web port quickly.

## Normal deploy

Use the default startup environment for ordinary deploys:

- `RUN_MIGRATIONS_ON_START` unset or `0`
- repair flags unset or `0`
- bootstrap flags unset or `0`

With this mode, `backend/start.sh` skips `python manage.py migrate --noinput` and starts gunicorn on `0.0.0.0:${PORT}`. This reduces the risk of Render port bind timeout during normal deploys, especially on the free plan.

## Migration deploy

Render free instances do not provide an interactive Shell, so migrations need to be run through a controlled deploy.

For a migration deploy:

1. Set `RUN_MIGRATIONS_ON_START=1` in the Render service environment.
2. Trigger a manual deploy.
3. Wait for the deploy logs to show migrations completed and gunicorn started.
4. Set `RUN_MIGRATIONS_ON_START=0` or remove the variable.
5. Trigger another normal deploy so future restarts skip migrations.

Only enable `RUN_MIGRATIONS_ON_START=1` for deploys that intentionally need schema migrations. Leaving it enabled makes every restart run migrations before port binding.

## Repair and bootstrap flags

The existing repair and bootstrap flags remain separate from migrations:

- `RUN_SHRINE_REFLECTION_REPAIR`
- `RUN_FAVORITE_REPAIR_ON_START`
- `RUN_FEATUREUSAGE_REPAIR_ON_START`
- `RUN_BOOTSTRAP_ON_START`

Enable these only when the matching recovery or data bootstrap operation is needed. They should stay disabled during ordinary deploys.
