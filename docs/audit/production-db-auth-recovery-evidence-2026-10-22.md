# Production database credential rotation: recovery verification (2026-10-22)

## Scope / evidence
This is a documentation-only, read-only audit. No secret, DATABASE_URL, credential, IP address or user data is reproduced. References: Render service `jinja-backend`, connected Supabase project `kami-musubi-db`, user-provided Render/API screenshots on 2026-10-22, read-only Render deploy and application log inspection.

## Confirmed
- User-provided screenshot showed `GET /api/shrines/135/` returning `HTTP 200 OK` and a JSON Shrine record on 2026-10-22 11:18 JST.
- Render application access log at **2026-10-22 11:18:09 JST** independently records `GET /api/shrines/135/ HTTP/1.1` with **200** status. This is an actual ORM/API read path and confirms Render-side DB read at this instant.
- Render service's latest deployment was reported `live` by the deployment inspection during this verification.
- Render health checks responded 200, but the `/healthz/` code does **not** query DB. Therefore health 200 alone is not evidence of DB authentication.
- Immediately prior to the recovery, logs showed `psycopg.OperationalError` / `password authentication failed`; the observed post-rotation 200 is a successful read after the earlier failure.

## Not confirmed / explicit STOP
- **OLD_PASSWORD_INVALIDATED = NOT_VERIFIED.** We have not received a database credential rotation confirmation record proving that the previous credential has been revoked. A successful new login does not establish old-credential invalidation. Do **not** paste a password, complete connection string, or test the old secret in this conversation, PR, or logs.
- **ADDITIONAL_MAJOR_API_SMOKE_TEST = NOT_VERIFIED.** The remote fetch environment could not directly access the service to execute fresh smoke tests. Do not elevate a past successful shrine detail endpoint into blanket coverage of shrine lists, benefit tags, popular shrines, concierge, authenticated flows, or write APIs.
- **SECURITY_INCIDENT / DATA_EXFILTRATION = NOT_ESTABLISHED.** Previously shared connection-string screenshot constitutes potential credential exposure, not evidence of data exfiltration. No sweeping security conclusion is inferred.

## Follow-up (Mother Ship / operations)
1. Confirm the Supabase password reset operation completed for the intended production DB account, note only the confirmation time/status, and ensure no other integrations still rely on old credentials. Treat old credential as compromised, avoid printing or testing it.
2. Read-only checks through the live Render endpoint: `GET /api/shrines/?page_size=1`, `GET /api/goriyaku-tags/`, `GET /api/populars/` (verify actual configured routes before asserting expected status). Record returned HTTP status and relevant Render access log timestamps, without recording personal or sensitive response bodies.
3. Confirm monitored authenticated and concierge routes using authorized QA accounts separately, with no production writes except explicitly planned tests.
4. If follow-up results support completion, issue a **separate** final closure record/PR. This evidence PR does not declare credential rotation or cross-API smoke testing complete.

```text
RENDER_LATEST_DEPLOY = LIVE
RENDER_DB_READ_SHRINE_135 = PASS (2026-10-22 11:18:09 JST)
OLD_DB_CREDENTIAL_REVOKED = NOT_VERIFIED
OTHER_MAJOR_ENDPOINTS = NOT_VERIFIED
CREDENTIAL_ROTATION_FORMAL_CLOSURE = OPEN
PRODUCTION_MODIFICATIONS_IN_THIS_AUDIT = NONE
```
