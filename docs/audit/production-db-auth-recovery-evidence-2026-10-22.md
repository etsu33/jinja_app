# Production database credential rotation: recovery verification (2026-10-22)

## Scope / evidence
This is a documentation-only, read-only audit. No secret, DATABASE_URL, credential, IP address or user data is reproduced. References: Render service `jinja-backend`, connected Supabase project `kami-musubi-db`, user-provided Render/API screenshots on 2026-10-22, read-only Render deploy and application log inspection.

## Confirmed
- User-provided screenshot showed `GET /api/shrines/135/` returning `HTTP 200 OK` and a JSON Shrine record on 2026-10-22 11:18 JST.
- Render application access log at **2026-10-22 11:18:09 JST** independently records `GET /api/shrines/135/ HTTP/1.1` with **200** status. This is an actual ORM/API read path and confirms Render-side DB read at this instant.
- Render service's latest deployment was reported `live` by the deployment inspection during this verification.
- Render health checks responded 200, but the `/healthz/` code does **not** query DB. Therefore health 200 alone is not evidence of DB authentication.
- Immediately prior to the recovery, logs showed `psycopg.OperationalError` / `password authentication failed`; the observed post-rotation 200 is a successful read after the earlier failure.

## Post-recovery Mother Ship testimony and API screenshots (2026-10-22)
- Mother Ship reported that the Supabase DB password was **reset** and Render's `DATABASE_URL` was **updated** to the new credential. Evidence classification: `MOTHER_SHIP_OPERATION_REPORT`; not an independent Supabase reset-event log and not a retained secret.
- Three Mother Ship-supplied screenshots dated 2026-10-22 show Django REST framework responses with `HTTP 200 OK` and JSON for:
  - `GET /api/shrines/?page_size=1`: shrine list, response `count=133`
  - `GET /api/goriyaku-tags/`: benefit-tag list
  - `GET /api/populars/`: popular-shrine list, response `count=133`
- The existing shrine detail screenshot and Render access-log evidence also show `GET /api/shrines/135/` 200. These screenshots substantiate **four public read-endpoint smoke checks**; they do not substantiate authenticated routes, concierge workflows, full end-to-end coverage, or security posture.
- These three screenshots were provided in the conversation, not committed to the repository; this record includes endpoint/status only and excludes screenshots' response payloads and query tracking parameters.
- A Supabase password reset generally replaces the previous password; however, the independent old-credential revocation state and other DB accounts/connection secrets were not tested or independently attested. There is no need to request or reuse the old password for this audit.

## Not confirmed / explicit STOP
- **OLD_PASSWORD_INVALIDATED = NOT_VERIFIED.** Mother Ship reported a completed password reset, but no independent Supabase reset event receipt is attached and the old password was not tested. A successful new login does not establish old-credential invalidation. Do **not** paste a password, complete connection string, or test the old secret in this conversation, PR, or logs.
- **PUBLIC_READ_API_SMOKE_TEST = PASS (USER_SCREENSHOTS, four endpoints).** The three additional public read endpoints above returned HTTP 200 in Mother Ship screenshots. Concierge, authenticated flows, write APIs, and comprehensive regression coverage remain **NOT_VERIFIED**.
- **SECURITY_INCIDENT / DATA_EXFILTRATION = NOT_ESTABLISHED.** Previously shared connection-string screenshot constitutes potential credential exposure, not evidence of data exfiltration. No sweeping security conclusion is inferred.

## Follow-up (Mother Ship / operations)
1. Mother Ship reported the Supabase password reset completed for the production DB account. For independent credential-revocation evidence, consult Supabase's reset/audit receipt if available and confirm no other integrations rely on old credentials; record only status/time, never the secret. Treat old credential as compromised, avoid printing or testing it.
2. The three public read-endpoint checks are evidenced by user screenshots with HTTP 200. Additional Render-side access-log corroboration can be pursued separately without copying personal or sensitive response bodies.
3. Confirm monitored authenticated and concierge routes using authorized QA accounts separately, with no production writes except explicitly planned tests.
4. If follow-up results support completion, issue a **separate** final closure record/PR. This evidence PR does not declare credential rotation or cross-API smoke testing complete.

```text
RENDER_LATEST_DEPLOY = LIVE
RENDER_DB_READ_SHRINE_135 = PASS (2026-10-22 11:18:09 JST)
OLD_DB_CREDENTIAL_REVOKED = NOT_VERIFIED
PUBLIC_READ_APIS_SHRINES_TAGS_POPULARS = PASS (MOTHER_SHIP_SCREENSHOTS)
AUTHENTICATED_AND_CONCIERGE_ENDPOINTS = NOT_VERIFIED
PASSWORD_RESET = REPORTED_BY_MOTHER_SHIP
CREDENTIAL_ROTATION_FORMAL_CLOSURE = OPEN
PRODUCTION_MODIFICATIONS_IN_THIS_AUDIT = NONE
```
