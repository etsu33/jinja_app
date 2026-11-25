# Mobile EAS production API endpoint and Django effective DB role — evidence status (2026-10-25)

## Authorized scope

Mother Ship requested confirmation of Mobile production build **actual** API destination and Django's effective DB role, preserving no-secrets, read-only and no runtime/Production mutation. Baseline `develop@7cf17823c053102e5f20c18f4d2fc672948267e7`. Inspected GitHub source and existing Render/Supabase read-only metadata. No production API requests, runtime probes, EAS build execution, environment value retrieval or secrets were accessed.

## Mobile production endpoint

- `apps/mobile/eas.json` build profile `production` sets EAS `environment: production`. Profile `android-map-qa` also uses EAS `production` environment but builds internal APK; this is **not evidence** that any of these profiles was used for an actual released build.
- `apps/mobile/lib/http.ts:2-3`: `const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api'`; token refresh and fetch requests use `BASE_URL`. Other callers can have distinct external endpoints (maps/analytics), so these findings apply to the **main API client**.
- Repository code search for `EXPO_PUBLIC_API_BASE_URL` found references, not any production EAS resolved environment value or immutable artifact metadata.
- **Actual shipped build endpoint: NOT VERIFIED**. EAS production environment name alone does not prove its actual variable value, or which build was distributed. Must compare identified deployed build ID/profile/build fingerprint/commit with **resolved environment variable name + non-secret API URL** and built runtime behavior in an explicitly authorized isolated test. Do not download/execute builds or make production requests under current authorization.
- Suggested safe evidence: Expo account owner's EAS Dashboard read-only screenshots of Build ID, build profile, environment name, build date, commit, and the **non-secret** API base URL variable's value if verified non-secret. Do not disclose tokens, signing certificates, secret env variables or build credentials. If the console hides the value, mark UNKNOWN rather than circumventing.

## Django effective DB role

- Owner-reported Render `jinja-backend` has `DATABASE_URL` present; `DB_USER`, `POSTGRES_USER` absent.
- `backend/shrine_project/settings.py:144-205` parses `DATABASE_URL` via `dj_database_url.parse`. Owner reported a possible Supabase pooler-style username (`postgres.<project-ref>`); this is **configuration candidate only**, not a live DB `current_user`.
- Prior authenticated Supabase catalog `pg_roles` read: `postgres` has LOGIN and BYPASSRLS; `authenticator` has LOGIN but not BYPASSRLS; `anon`/`authenticated` no LOGIN/BYPASSRLS; `service_role` BYPASSRLS. This is **role capability metadata, not Django identity evidence**.
- **Effective Django DB role: NOT VERIFIED**. Read-only Render `get_service` exposes service metadata but not runtime username. The Supabase SQL editor `current_user=postgres` is **SQL editor session**, not Django. No observed Django connection uniquely attributable to Render service was available in the approved metadata.
- Only later, under separately authorized safe process, obtain **one redacted attestation** of authenticated Django connection `SELECT current_user` and target DB identity (safe identifiers only) from the actual Django service, with no URL, password, tokens, client data or logged secrets; runtime execution may need explicit authorization and must not be treated as covered by docs-only permission.
- Alternatively, an owner may independently verify the **URL username only** from Render, but it does not meet the stronger requirement of **effective** role and server identity.

## Risks and boundaries

- Supabase Data API exposes `public` and `graphql_public` according to Mother Ship screenshots. Prior inspection found RLS disabled for 59 public tables with broad `anon` GRANT. These risks remain regardless of Mobile API target and Django connection role.
- Missing evidence cannot be closed by static deductions. Neither execution, production request probing, DB/GRANT/RLS change nor env reading is authorized. No production or runtime security gate approval inferred.

## Status

| Task | Design/static readiness | Actual observed evidence |
| --- | --- | --- |
| Mobile API endpoint | Code/profiles mapped | **OPEN**: shipped EAS build and resolved `EXPO_PUBLIC_API_BASE_URL` unverified |
| Django role | URL precedence and role capabilities mapped | **OPEN**: live `current_user` not attested |

A-0 / L4-O / L4-E = NOT APPROVED. EU-8=A remains read-only. This document-only PR must not be merged without CI/diff review and explicit Mother Ship authorization.

## Mother Ship Expo Dashboard evidence (2026-10-25)

Owner-provided screenshot of Expo project `morietsu/jinja-app` Environment variables and explicit owner text confirm `EXPO_PUBLIC_API_BASE_URL` scoped to `production` currently equals `https://jinja-backend.onrender.com/api`. The value is a public API origin/path, not an API secret. Render read-only service metadata previously identified `jinja-backend` at `https://jinja-backend.onrender.com`.

- **Current production environment configured API endpoint: VERIFIED** (`https://jinja-backend.onrender.com/api`).
- **Build used EAS production environment:** VERIFIED from Expo Build Details for July 27, 2026 successful internal APK, Build ID `5f1b4311-df8c-402b-89c4-85bfee27a792`, profile `android-map-qa`, commit `dd3b224`.
- **Historical APK-embedded value at build time:** NOT VERIFIED. Env entry shown as created July 27, but matching date does not establish ordering, mutation history, or build embedded value. Build artifacts/logs show Expired. Do not conflate current variable with historic artifact.
- No Supabase Data API endpoint appears in the confirmed **current main Mobile API base URL**; does not rule out other third-party or old binary traffic.
- No environment values changed, APK fetched, build executed or production API probed. A-0/L4-O/L4-E remain NOT APPROVED.
