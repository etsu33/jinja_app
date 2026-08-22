> **Status: Local correction verified. Production application requires a
> separate, explicitly authorized deploy step (Section 10) — not
> performed by this task.**

# Shrine ID 70 Coordinate Data Fix

## 1. Problem

Production Compass → Route QA found that opening the Google Maps route
for shrine_id=70 (多摩川浅間神社) resolves near/as a nearby bakery
(リトルマーメイド多摩川店), not the shrine itself, even though the shrine's
displayed address was correct. The prior investigation
([this session, same conversation](compass-route-attribution-contract.md)
context) traced DB → API → Shrine Detail → Route URL generation and found
every hop propagates data unmodified — the stored `latitude`/`longitude`
themselves were wrong at the source.

## 2. Affected Shrine

```
id:      70
name:    多摩川浅間神社
address: 東京都大田区田園調布1-55-12
```

## 3. Previous Coordinates (wrong)

```
latitude:  35.5898
longitude: 139.6688
```

Independently verified (this session) to resolve, on live Google Maps, to
**リトルマーメイド多摩川店** (a bakery at 東京都大田区田園調布1丁目53-8,
~7m from this exact point) — not the shrine, which is ~253m away.

## 4. Correct Coordinates

```
latitude:  35.5875263
longitude: 139.6687549
```

**Evidence**: live Google Maps place lookup by name, this session —
searching "多摩川浅間神社" resolves to a place card with address
`〒145-0071 東京都大田区田園調布1丁目55-12 浅間神社` (byte-for-byte match
to the DB's `address` field) and a rating of 4.3★ (2,088 reviews),
confirming this is the genuine, well-established place record, not an
arbitrary geocoder centroid or a road/station. The page URL's own
`@lat,lng` component was read directly:
`@35.5875263,139.6687549,17z`. Re-confirmed again in this task (Section
17 below) by opening the actual generated Route URL and observing Google
Maps label the destination as "多摩川浅間神社、〒145-0071 東京都大田区田園調布
１丁目５５−１２ 浅間神社".

## 5. Root Cause Classification

**A — shrine DB latitude/longitude** (unchanged from the prior
investigation's finding). API serialization, Shrine Detail propagation,
and Google Maps URL generation were all independently re-confirmed
correct (pass-through, no swap, no transform) — see Sections 15-17.

## 6. Synchronization Contract (`latitude`/`longitude` → `location`)

**Automatic — inside `Shrine.save()`** (`backend/temples/models.py:342-388`),
via the real model class only. On every save, `Shrine.save()` reads
`self.latitude`/`self.longitude` and unconditionally recomputes
`self.location` as `Point(float(longitude), float(latitude), srid=4326)`
(confirmed: PostGIS point order is `(lng, lat)`, matching the existing
precedent in `migrations/0020_shrine_popularity_fields.py`'s
`backfill_location_from_latlng`, which uses the identical
`Point(float(s.longitude), float(s.latitude), srid=4326)` construction).

**Critical caveat for migrations**: Django's `apps.get_model(...)`
historical model (used inside any `RunPython` migration function) does
**not** include this custom `save()` override — only the real
`temples.models.Shrine` class does. A migration that calls
`.save(update_fields=[...])` on a historical-model instance triggers only
the generic `Model.save()`; `location` will **not** auto-sync inside a
migration. This is confirmed, not assumed — `0020`'s own migration
constructs the `Point` manually before saving, for exactly this reason.

## 7. Production Schema Drift (why `location` is deliberately not touched here)

`docs/audit/temples-0091-production-remediation.md` Section 2 confirms,
**against a restored production database dump** (not speculation): as of
migration `0090` (three migrations before current HEAD), production's
`temples_shrine.location` column was a legacy **`text`** type, not a real
PostGIS `geometry` column — while every migration's historical model
state (including this task's) declares `location` as a PostGIS
`PointField`. Selecting `location` without excluding it (e.g. a bare
`Shrine.objects.filter(...)`) triggers Django's GeometryField converter
on the raw text value and raises `GEOSException` before any row is
touched — reproduced again, freshly, by this task's own
`test_a_geos_exception_avoided_under_text_location_drift` (Section 13).

No migration between `0090` and current HEAD (`0093`) converts this
column's type. Given this confirmed, current schema drift, this
migration (`0094`) follows the **same established, already-tested
avoidance pattern** as `0091_fill_missing_local_shrine_reason_facts.py`:
`.only()` excludes `location` from the SELECT entirely, and the write
touches only `latitude`/`longitude`. **`location` resync for shrine 70 in
production is deliberately deferred** — it requires first determining
production's actual current column type (a separate, narrower
investigation, likely needing Mother Ship's Render dashboard access or an
authorized read-only credential-bridge query per
`docs/audit/production-db-readonly-audit-access-gate.md` /
`docs/audit/local-mac-direct-migration-execution-safety.md`), which is
out of this task's scope. **This does not block the reported bug fix**:
the frontend never reads `location` for the Shrine Detail address or the
Google Maps Route destination (Section 15-17) — both read `latitude`/
`longitude` directly.

## 8. Source of Truth

**Tracked JSON file**: `backend/temples/data/shrines_seed_clean.json`
(row index 69, matched by `name_jp`/`address`), consumed by
`backend/temples/management/commands/import_shrines_seed.py`. This
command **upserts by `(name_jp, address)`** and overwrites
`latitude`/`longitude`/`location`/several other fields from the JSON
whenever they differ from the DB — meaning a DB-only fix would silently
regress on any future re-import that reads this file. **Corrected in this
PR** (Section 9), independent of whether any specific environment's
bootstrap history would actually re-run the import (see Section 10).

## 9. Repository Changes

```
backend/temples/data/shrines_seed_clean.json
  -- latitude/longitude and the location.lat/location.lng sub-object for
     the 多摩川浅間神社 row corrected (35.5898/139.6688 -> 35.5875263/139.6687549)

backend/temples/migrations/0094_fix_shrine_70_coordinates.py
  -- new, narrow RunPython data migration (Section 11)

backend/temples/tests/test_gis_migration_0094_shrine_70_coordinates.py
  -- new regression tests (Section 13)

docs/audit/shrine-70-coordinate-correction.md
  -- this document
```

No other file changed. No schema migration. No application code touched.

## 10. Production Application Plan

**How this correction reaches production is not fully resolved by this
task, and is intentionally left as an explicit next step**, because two
separate, already-documented constraints apply:

1. **`RUN_MIGRATIONS_ON_START` may not be enabled.** Per
   `docs/audit/production-db-readonly-audit-access-gate.md` Phase 0
   (confirmed from `backend/start.sh` source): if this Render env var is
   unset or `"0"`, migrations do **not** run automatically on deploy.
   Whether it is currently set to `"1"` is Render dashboard
   configuration this session cannot see.
2. **Render Shell and One-Off Jobs are confirmed unavailable** (free
   tier). **Direct Local-Mac-execution of a real (non-`--plan`) production
   `migrate`** was evaluated as "viable with conditions" in
   `docs/audit/local-mac-direct-migration-execution-safety.md`, but that
   document's own open items explicitly state an actual write (`--noinput`)
   has **never been attempted or authorized** — it is recorded as
   "Mother Ship判断待ち" (awaiting the primary stakeholder's decision).
   This task does not unilaterally perform that write.

**Therefore**: this migration is committed, tested, and ready to ship —
but it will reach production only when either (a) `RUN_MIGRATIONS_ON_START=1`
is confirmed set and the next deploy runs `migrate` (the standard,
already-established path every other tracked migration in this repo
uses), or (b) the Mother Ship explicitly authorizes an actual production
`migrate` execution via the vetted Local-Mac-direct path. Neither (a) nor
(b) was performed by this task.

## 11. Data Migration Decision

**Mechanism: A — tracked Django data migration**
(`0094_fix_shrine_70_coordinates.py`), for reasons explicit in Section 10
above: auditable (git history + `django_migrations` record), reproducible
(idempotent — re-running is a no-op once applied, Section 12), minimal
blast radius (single row, `RunPython`, no schema change), and rides the
same, already-established migration pipeline every other tracked change
in this repository uses — it requires no Render Shell, One-Off Job, or
unauthorized direct production write.

Confirmed this repository already uses narrowly-scoped `RunPython` data
migrations for exactly this class of correction:
`0020_shrine_popularity_fields.py` (`backfill_location_from_latlng`),
`0033_fix_location_geometry.py`, and — most directly comparable —
`0091_fill_missing_local_shrine_reason_facts.py` (single/few-row Shrine
field corrections via migration, with the identical `location`-column
schema-drift precedent this task reuses).

## 12. Idempotency

Re-running the migration (forward) after it has already applied sets
`latitude`/`longitude` to the same values again — a no-op in effect, no
error, no duplicate row created (matched by `pk=70`, a single row).
Verified by test (`test_b_forward_corrects_only_the_target_shrine` plus
Django's own migration-state bookkeeping, which prevents a migration from
literally re-running once recorded in `django_migrations` — this
idempotency property is about the *effect* being safe if it ever were
re-applied, e.g. after a rollback-and-reapply cycle).

## 13. Regression Tests

`backend/temples/tests/test_gis_migration_0094_shrine_70_coordinates.py`
(new, `USE_GIS=1`-only, mirroring `test_gis_migration_0091_shrine_reason_facts.py`'s
established pattern — under `USE_GIS=0` the `temples` app uses the
squashed `temples.migrations_nogis` graph, which does not contain 0094 as
a separate step):

| Test | Content | Result without `.only()` guard |
|---|---|---|
| A | No `GEOSException` when `location` is physically `text` with a non-WKB value (reproduces the confirmed production drift condition directly, without needing a real production dump) | **FAILS** — confirmed by temporarily removing the `.only()` guard and re-running: raises the identical `GEOSException` |
| B | Forward migration updates only shrine_id=70's lat/lng; an unrelated shrine is untouched | PASS |
| C | If id=70's name/address no longer match, the row is left untouched (defensive guard) | PASS |
| D | Fresh DB with no shrine_id=70 row: no exception | PASS |
| E | Reverse migration restores the old (wrong) coordinates | PASS |

**Verified the guard is load-bearing**: temporarily reverted the
migration's `.only(*LOOKUP_FIELDS)` call to a bare `.filter(pk=SHRINE_ID)`
and re-ran Test A — it failed with the exact same `GEOSException` this
migration is designed to avoid, then restored the fix and re-confirmed
all 5 tests pass.

**Full `temples` app suite**: `1614 passed, 15 skipped` (skips pre-existing
and unrelated to this change — GDAL/PostGIS local-environment gaps,
missing `GOOGLE_PLACES_API_KEY`, etc.). `makemigrations --check --dry-run
temples`: no changes detected. `manage.py check`: no issues.

## 14. Local DB After Fix

```
latitude:          35.5875263
longitude:         139.6687549
location:          POINT(139.6687549 35.5875263)   -- fully synchronized
address unchanged: YES (東京都大田区田園調布1-55-12)
name unchanged:    YES (多摩川浅間神社)
```

Applied via `python manage.py migrate temples 0094` against the local dev
DB (`postgis://…@127.0.0.1:5432/jinja_db`) — fixes `latitude`/`longitude`.
`location` was then separately resynced **locally only**, via the real
`temples.models.Shrine` ORM class (`Shrine.objects.get(pk=70)`, re-save
with the corrected lat/lng, letting the model's own custom `save()`
auto-derive `location`) — safe here because local's `location` column is
confirmed genuine PostGIS geometry (`ST_AsText`/`ST_SRID` both resolve
correctly), unlike the confirmed-drifted production state (Section 7).
This local-only resync step is **not** part of the tracked migration.

## 15. API Verification

Queried via Django's test client (not ORM-only):

```
GET /api/shrines/70/data/  ->  200
name_jp:   多摩川浅間神社
address:   東京都大田区田園調布1-55-12
latitude:  35.5875263
longitude: 139.6687549
location:  {'lat': 35.5875263, 'lng': 139.6687549}
```

**PASS** — matches the corrected DB values exactly.

## 16. Shrine Detail Verification

Local Next.js dev server + local Django dev server, live browser check of
`http://localhost:3000/shrines/70`:

- Page loads (`GET /shrines/70` → 200)
- Title/heading: `多摩川浅間神社` (unchanged)
- Address shown: `東京都大田区田園調布1-55-12` (unchanged)
- No console/network errors related to this change
- Route button (`Googleマップで経路案内`) present

**PASS**, no frontend regression.

## 17. Google Maps Route Verification

Read the actual rendered link:

```
href="https://www.google.com/maps/dir/?api=1&destination=35.5875263%2C139.6687549&travelmode=walking"
```

Opened this exact URL in the browser. Google Maps' own left panel labels
the destination:

```
多摩川浅間神社、〒145-0071 東京都大田区田園調布１丁目５５−１２ 浅間神社
```

**PASS.**

## 18. Old Wrong Destination — Still Reproduced?

**NO.** With the corrected coordinates, the destination resolves to the
shrine, not リトルマーメイド多摩川店.

## 19. Compass Regression

Directly visited `http://localhost:3000/shrines/70?ctx=compass&recommendation_instance_id=qa12345&recommendation_rank=1`
(the exact URL shape `buildShrineHref` generates for a Compass-originated
recommendation) rather than forcing a live Compass form submission to
naturally recommend shrine 70 — doing so deterministically would require
constructing a specific birthdate/direction/distance combination with no
guaranteed practical outcome, and Ranking is explicitly out of scope
(Section 20 of the task). The rendered Route link under this URL was
identical: `destination=35.5875263,139.6687549`. Since nothing in the
Detail→Route code path branches on `shrineId`, this confirms the fix
applies identically whether shrine 70 is reached via Compass, Concierge,
or direct access — no recommendation ranking placement was required or
forced.

## 20. Ranking

```
Algorithm changed: NO
```

Correcting `latitude`/`longitude` changes this shrine's *position* as an
input to any future distance-based Ranking computation — this is a
**data effect**, not a Ranking algorithm change, per the task's explicit
instruction. No scoring weights were touched.

**Data-driven distance impact**: measured from a stable reference origin
(Tokyo Station, 35.6812, 139.7671), via `ST_Distance(...::geography)`:

```
before: 13,495.05 m
after:  13,688.37 m   (+193.3 m)
```

This is expected and correct given the shrine's real location is ~253m
from the old (wrong) point — not treated as a regression.

## 21. Analytics

```
Changed: NO
```

`route_open`, `ctx`, `recommendationInstanceId`, `source`, and the
PostHog contracts from the recent Route attribution fix (PR5, #2525) are
untouched. Verified directly: the Section 19 check confirms the Route
link's `href` is unaffected by anything other than the corrected
coordinate values.

## 22. Rollback

**Recorded previous (wrong) coordinates**: `35.5898, 139.6688` — not
restored automatically.

**If the migration needs reverting** (e.g. new evidence proves
`35.5875263, 139.6687549` wrong): `python manage.py migrate temples 0093`
runs `revert_shrine_70_coordinates`, which restores the exact previous
values, gated by the same defensive name/address check. Verified safe by
test (Section 13, Test E).

**JSON source file**: has no automatic rollback; a manual revert (Section
3's old values) would be a one-line reversion of the same edit, tracked
in git history.

## 23. Non-goals

This task does not:

- Modify any other shrine's coordinates (no all-shrine geocoding cleanup).
- Change Recommendation Ranking scoring or weights.
- Change Analytics instrumentation, `route_open`, or any PostHog contract.
- Determine or fix production's actual current `location` column type —
  named as a separate, narrower follow-up (Section 7).
- Execute a production database write or a production `manage.py migrate`
  — landing this migration in production requires a separate, explicitly
  authorized step (Section 10).
- Redesign the geocoder or import pipeline.

## 24. Impact

```
Production application code changed: NO
Production DB changed:               NO (local dev DB only, this task)
Analytics changed:                    NO
Recommendation Ranking changed:       NO
Concierge changed:                    NO
Backend/Frontend behavior code:       NO (data + one tracked migration only)
```

## 25. Verification

```
git status --short / git diff --stat: limited to the 4 files in Section 9
makemigrations --check --dry-run temples: no changes detected
manage.py check: no issues
temples app full suite: 1614 passed, 15 skipped (pre-existing, unrelated)
New migration test suite verified load-bearing (guard removed -> fails
  with the exact GEOSException; guard restored -> passes)
API, Shrine Detail, and Google Maps Route independently re-verified
  after the local DB fix (Sections 15-18)
apps/web/AGENTS.md / apps/web/CLAUDE.md not staged
