# Render startup operations

This app is configured so normal Render Web Service startups bind the web port quickly.

## Normal deploy

Use the default startup environment for ordinary deploys:

- `RUN_MIGRATIONS_ON_START` unset or `0`
- repair flags unset or `0`
- bootstrap flags unset or `0`

With this mode, `backend/start.sh` skips `python manage.py migrate --noinput` and starts gunicorn on `0.0.0.0:${PORT}`. This reduces the risk of Render port bind timeout during normal deploys.

## Migration deploy

The production backend service (`jinja-backend`) runs on a paid Render compute plan (`0.5c-512mb`, confirmed 2026-11-12). Earlier versions of this document assumed the free plan, where no Shell is available. On a paid web service, Render provides both the Dashboard **Shell** tab and SSH (see Render's "SSH and Shell Access" docs), so a one-off command such as `python manage.py migrate` or a single management command can also be run from the Shell instead of a startup flag.

The controlled-deploy flow below still works and is useful when no one can open the Shell (for example, an agent working only through the Render API).

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

### Before enabling `RUN_BOOTSTRAP_ON_START`

`bootstrap_production_data` skips a step only if production already has a row with `status = 'success'` for that step and version in `ProductionDataBootstrapRun`. Do not assume earlier steps are already recorded. Check first, for example from the Shell or the database console:

```sql
select step, version, status, finished_at
from temples_productiondatabootstraprun
order by step, version;
```

Any step without a `success` row will run on that deploy. On 2026-11-12 the three existing steps had no rows, so enabling the flag ran `import_shrines_seed` again and overwrote the `goriyaku` text of four shrines with the seed's empty value. If you only need one new step, prefer running that single command from the Shell.
