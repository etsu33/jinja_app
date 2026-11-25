# SPH-21 Django TLS probe (read-only, design and offline tests)

- Command: `python manage.py report_db_tls`.
- Read-only: no SQL; opens Django's configured `default` psycopg connection and reads `pgconn.ssl_in_use`, allowlisted TLS protocol and configured `OPTIONS.sslmode`.
- Output: `[db-tls-probe] ssl_in_use=true|false protocol=TLSv1.3|...|unknown sslmode=... certificate_verified=unknown hostname_verified=unknown`.
- Does not print host, port, DB, project ref, username, DATABASE_URL, full `pgconn.info`, password, exception text or stack trace.
- A successful TLS handshake does **not** establish CA/hostname verification; `sslmode` is a configured mode, not proof of verification outcome.
- Command is **NOT** wired into `start.sh`, scheduled startup, a web endpoint or deployment. Use only in separately approved safe runtime execution. Render free Shell may not be available: any later opt-in startup hook is a separate PR and an explicit Mother Ship deployment approval.
- Tests use offline mocks only. No production contact or environment changes. Keep existing `report_db_role` unchanged. This PR is NOT approval to run a production TLS probe.
- Configuration propagation (offline, synthetic URL, mocked `psycopg.connect`): `backend/tests/test_db_tls_options_propagation.py` shows that `sslmode` / `sslrootcert` in `DATABASE_URL` reach Django `OPTIONS` and the psycopg connect kwargs unchanged, alongside `connect_timeout=5`. Neither the settings nor Django add, default or validate TLS options; a URL without them connects with libpq's default. Propagation is **not** evidence of certificate or hostname verification.
