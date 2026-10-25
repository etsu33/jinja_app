# CSRF V-1 MS-8/MS-9: 保存先・保持期間・アクセス権限の選択肢（2026-10-25）

## Scope / STOP

Design review and authenticated **read-only** project metadata inspection. Mother Ship selected **MS-8=A** (durable server-side aggregation), **MS-9=A** (explicit retention/access policy), **MS-11=A** (no Log Drains for this phase). **Specific storage product, schema, credential, access policy, retention days, deletion automation and cost remain unapproved.** A-0/L4-O/L4-E **NOT APPROVED**. No schema, grants, RLS, env, server, logging, deployment, production routing, or data changed.

Baseline: `develop@5a05540689595dd2efcbd82bf0eec2bbc0108266`; #3338 Mother Ship decisions and #3339 contract/readiness review.

## Actual environment observations (metadata only)

- Supabase authenticated `list_projects`: project `kami-musubi-db` (`uigvlbwnsthqqklzpfml`) in ap-northeast-1, `ACTIVE_HEALTHY` at inspection time, PostgreSQL 17.
- Authenticated `list_tables(schemas=['public'],verbose=false)`: existing Django-oriented application tables including user, session, concierge and shrine data. **No dedicated CSRF audit aggregation table was identified among the returned public table names.** An independent private schema or other backend may exist, not established here.
- The Supabase metadata advisory flagged **59 public tables with RLS disabled**. This is a significant **separate authorization review trigger**, not proof of public data exposure. No grant, schema-exposure, API setting, role membership, or permission-effective evaluation was done; none should be assumed. **Do not enable RLS or revoke grants globally without checking Django compatibility and API boundaries first.**
- Vercel previously evidenced Hobby plan. Official Vercel Runtime Logs documentation (2026) states Hobby logs retain **one hour**, so logs are not a demonstrated durable store for multi-day AC-8 evidence. Sources: https://vercel.com/docs/logs/runtime and https://vercel.com/docs/plans/hobby.
- Official Supabase documentation distinguishes schema/table privileges from RLS policy; an exposed schema may be accessible when roles retain grants. Source: https://supabase.com/docs/guides/database/postgres/row-level-security. This is general platform information, not proof of exposure for the project.

## MS-8 — concrete architecture candidates

| Option | Design | Tradeoffs | Status |
| --- | --- | --- | --- |
| A1 existing Supabase PostgreSQL, **dedicated non-exposed private schema and least-privilege role** | BFF-side server-only aggregation writer with **separate bounded privileges**, no connection via Django BFF `djFetch` / `bffFetchWithAuthFromReq`, no browser keys; server-side atomic aggregate counters and durable evidence snapshots | Reuses known database, but connection role separation, HTTP/direct-DB access, latency, availability, load, cost, RLS/grant controls, and rejection-side zero-Django invariant require testing | **TECHNICAL LEAD CANDIDATE — NOT APPROVED** |
| A2 independent audit database/service | Separate credentials, isolated retention and failure domain | Added operations, vendor, cost, deletion/access policy | Candidate |
| A3 Vercel Runtime Logs only | Simple logging | Hobby retention insufficient; no approved drains; no authoritative multi-instance aggregate | **Not acceptable alone for multi-day evidence** |

**Critical boundary:** `MS-8=A` chooses **durable server-side aggregation** but does not choose Supabase or authorize a new database, new server credentials, service-role usage, Data API exposure, or writing from CSRF reject path. Reject-side must never invoke Django or cause response/cookie behavior changes. Candidate design must prove whether its persistence side effects comply with #3323 §5 and aggregation contract; if not, STOP and obtain a separate contract decision. Do not promise synchronous remote persistence will be reliable or latency-neutral.

### Storage/aggregation acceptance contract (proposal)

- No request body, raw headers, token, cookie, IP, user-agent, email, user ID, free text, or client-provided request ID in audit store. Minimal approved dimensions: route ID (canonical), UTC time bucket, mode, outcome, reason code, QA classification and numeric count.
- Separate writer from reader and schema owner; browser, `anon`, `authenticated`, ordinary Django application role have **no grant** to audit schema. Metadata/schema/grants/RLS/exposure must be verified, not inferred.
- Safe atomic aggregation across server instances; duplicate retry and write-failure semantics explicitly tested; counters must not be corrupted or requests held/altered when storage is unavailable.
- Encryption, backup policy, restoration, monitoring of dropped events, read access, and vendor usage/cost ceilings reviewed before A-0.
- Rollout and schema creation require distinct Mother Ship approval, PR and CI checks.

## MS-9 — retention and role policy proposal (NOT APPROVED)

| Data category | Suggested duration | Readers | Writers | Removal |
| --- | --- | --- | --- | --- |
| Minimized per-window aggregate counters | **90 days** (candidate only) | Named audit reviewer/owner, least privilege | Server-only aggregation role | Scheduled expiry; deletion proof and exception handling |
| Signed/hashed review evidence exports | **180 days** (candidate only) | Explicitly authorized reviewer/owner | Authorized export job | Expiry after incident/legal hold check |
| Audit-store administrative access events | **180 days** (candidate only) | Owner/security reviewer | Auditable administrator operations | Approved expiry policy |

These are planning values, **not approved retention commitments**. Avoid persistent raw per-request logs by default. Any regulatory, incident, privacy policy, plan/cost or product requirements may necessitate different durations. Backup copies require a separate retention schedule. A hash alone does not establish authorship; preserve origin, review, and verification records. Implement no scheduled purge or access changes in this PR.

**Required unanswered Mother Ship parameters:** choose A1 vs A2, numeric retention for each data class, named access responsibilities, backup and deletion policy, budget ceiling, and evidence on call/failure behavior. Explicitly test whether the service-side write path complies with the denial contract and does not call Django.

## Distinct security observation: Supabase public RLS advisory

A separate docs-first read-only audit should inspect **schema exposure, grants, RLS, Django's actual connection role and Data API configuration**, without inspecting personal record values or changing schema. The 59-table warning is an indicator to investigate, **not a demonstrated breach**. Any remediation requires impact analysis for Django/authentication and a separately approved PR/migration. Do not conflate this with CSRF MS-8/MS-9 approval.

## Readiness and approvals

MS-8 **architecture option comparison complete; storage selection OPEN**.
MS-9 **retention/access policy candidate recorded; days and roles OPEN**.
UD-1/4/5/6/7/8/11 still require direct runtime evidence; RV and other UD contracts unchanged.
A-0 / L4-O / L4-E = **NOT APPROVED**; EU-8=A retained; no runtime/Production operation or storage/RLS/grant/env changes.
