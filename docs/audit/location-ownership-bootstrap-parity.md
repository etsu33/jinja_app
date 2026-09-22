# Shrine location Ownership / Fresh-Bootstrap Parity Audit

## Status

- Status: `COMPLETE — PRODUCTION EVIDENCE RECEIVED`
- Recorded at: `2026-09-22`
- Production evidence received at: `2026-09-22` (Mother Ship, read-only; schema, all 6 remediation rows, and deployed runtime flags)
- Scope: `Shrine.latitude` / `Shrine.longitude` / `Shrine.location` / Base Seed / importer / builder / migrations / fresh bootstrap
- Production DB write: `NONE`
- Base Seed write: `NONE`
- Model / importer / builder change: `NONE`
- Migration created: `NONE`
- Backfill executed: `NONE`

All repository claims below were verified by reading source in this session, not
by citing prior audit prose. Production claims in §7–§8 come from Mother Ship
read-only evidence; this session re-checked the decoded values against the
migration constants (§8.2) but did not itself query Production.

```text
LOCATION_OWNERSHIP = AMBIGUOUS
EXISTING_PRODUCTION_PARITY = FAIL
FRESH_BOOTSTRAP_PARITY = PASS
SEED_NESTED_LOCATION_ROLE = REDUNDANT
```

## 1. Current Ownership Graph

```text
Base Seed row (shrines_seed_clean.json)
  ├─ latitude / longitude ──────────────┐
  └─ location.lat / location.lng        │   (never read by any writer)
                                        │
                     import_shrines_seed │
                                        ▼
                         payload.latitude / payload.longitude
                                        │
                         payload.location = Point(lng, lat)   [USE_GIS=1 only]
                                        │
                              Shrine.objects.create() / obj.save()
                                        ▼
                              Shrine.save()  ← RE-DERIVES location
                                        ▼
                    DB: latitude, longitude, location

Historical data migrations (0094 / 0109–0113)
                    apps.get_model("temples","Shrine")   ← NO custom save()
                                        ▼
                    DB: latitude, longitude ONLY   (location untouched)
```

Two writers reach the same table with different contracts. That is the origin of
the ambiguity.

## 2. Model Field Contract

Source: `backend/temples/models.py`

```text
L243  latitude  = models.FloatField(null=True, blank=True)
L246  longitude = models.FloatField(null=True, blank=True)
L249  location  = PointField(srid=4326, null=True, blank=True)
```

`PointField` is an environment switch, not a fixed type
(`backend/temples/models.py` L26–L41, L128–L145):

```text
USE_REAL_GIS = settings.USE_GIS and not settings.DISABLE_GIS_FOR_TESTS

USE_REAL_GIS  -> django.contrib.gis.db.models.PointField
otherwise     -> django.db.models.JSONField
```

`PointField.deconstruct()` rewrites the migration path accordingly, so **the same
migration graph declares a different physical column type depending on the
environment that ran it.**

### 2.1 `Shrine.save()` — the real model derives location

`backend/temples/models.py` L353–L399:

```text
lat = _norm(self.latitude); lng = _norm(self.longitude)

new_location = None
if lat is not None and lng is not None:
    USE_REAL_GIS -> Point(float(lng), float(lat), srid=4326)
    else         -> {"type":"Point","coordinates":[float(lng),float(lat)],"srid":4326}

if _loc_changed(self.location, new_location):
    self.location = new_location
    if update_fields is not None:
        update_fields.add("location")      # ← auto-widens the write
```

Three verified consequences:

1. `location` is **always** recomputed from `latitude`/`longitude` on the real
   model. A caller cannot persist a `location` that disagrees with lat/lng.
2. GIS point order is `Point(longitude, latitude)` — verified at L373.
3. `save(update_fields=[...])` **silently adds `"location"`** when the derived
   value differs. A caller that passes `update_fields=["latitude","longitude",
   "updated_at"]` on the *real* model still writes `location`.

Point 3 is the hinge for §6.

## 3. Base Seed Contract

Source: `backend/temples/data/shrines_seed_clean.json`, 113 rows.

Each row carries the coordinate twice:

```text
"latitude": 33.52344557,
"longitude": 131.37716659,
...
"location": { "lat": 33.52344557, "lng": 131.37716659 }
```

Measured in this session across all 113 rows:

```text
rows total                                   113
rows without a "location" key                  0
rows where latitude != location.lat
        or longitude != location.lng           0
```

So the Seed is **currently** self-consistent. Nothing enforces that it stays so —
see §3.1.

### 3.1 Equality is only asserted for named subsets

`latitude == location.lat` is asserted in exactly two places, and neither is a
whole-file contract:

```text
backend/temples/tests/test_shrine_base_batch17_seed.py:87
    for name, expected in TARGETS.items():          # named subset only
        assert entry["location"] == {"lat": expected["latitude"], ...}

backend/temples/tests/test_wave0_db02_shrine_seed.py:426,450
    for candidate_id in CANDIDATE_IDS:              # named subset only
        assert base_row["location"] == {"lat": base_row["latitude"], ...}
```

The canonical builder contract test only checks **key order**, not values:

```text
backend/temples/tests/test_base_shrine_seed_build_contract.py:95
    tuple(row["location"].keys()) == builder.CANONICAL_LOCATION_KEY_ORDER
```

**Finding B-1:** no test guarantees `latitude == location.lat` for every row. A
Seed edit that changed only the top-level pair for a Shrine outside `TARGETS` /
`CANDIDATE_IDS` would pass CI.

## 4. Builder Behavior

Source: `scripts/build_base_shrine_seed.py`

```text
L60–L72   CANONICAL_KEY_ORDER includes "location"
L82–L83   CANONICAL_LOCATION_KEY_ORDER = ("lat", "lng")
L215–L233 canonicalize_row():  """key順だけを固定する。値は一切変換しない。"""
              canonical["location"] = {k: location[k] for k in ("lat","lng") if k in location}
```

Verified: the builder **reorders `location`'s keys and nothing else**. It does
not derive `location.lat`/`location.lng` from the top-level `latitude`/
`longitude`, does not validate agreement between them, and does not fail the
build when they disagree.

`SOURCE_PATH == OUTPUT_PATH == shrines_seed_clean.json`, so the Seed is its own
canonical source; the builder is a normalizer, not a generator.

**Finding B-2:** the builder is value-preserving by design, therefore it cannot
be the component that keeps the duplicated coordinate in agreement.

## 5. Importer Behavior

Source: `backend/temples/management/commands/import_shrines_seed.py`

```text
L283–L284  lat = row.get("latitude");  lng = row.get("longitude")
L286–L297  payload = {..., "latitude": lat, "longitude": lng, ...}
L304–L307  if use_gis and lat is not None and lng is not None:
               payload["location"] = Point(float(lng), float(lat), srid=4326)
L317–L319  CREATE:  Shrine.objects.create(name_jp=name, **payload)
L359–L378  UPDATE:  location compared via str(); coordinates via tolerance
L383       obj.save(update_fields=changed_fields)
```

Verified by grep over the whole file: **the importer never reads
`row["location"]`.** The nested Seed object is not importer input.

`COORDINATE_ABS_TOLERANCE` (L21–L41) suppresses float8 round-trip noise on
`latitude`/`longitude` only; `location` is compared by string equality (L364).

Both write paths land on the **real** `Shrine.save()`, which re-derives
`location` from lat/lng regardless of what the importer put in `payload`. The
importer's own `payload["location"]` is therefore redundant with `save()` — it
changes nothing about the persisted result.

**Finding I-1:** a stale nested Seed `location` can never reach the database
through `import_shrines_seed`. Fresh bootstrap is immune to Seed nested drift.

## 6. Migration Behavior

### 6.1 Historical models bypass `Shrine.save()`

`apps.get_model("temples", "Shrine")` returns a **historical** model
reconstructed from migration state. Historical models carry fields and managers
but **not custom methods**, so `shrine.save(...)` inside a `RunPython` is
`django.db.models.Model.save`, not the override in §2.1.

Consequence, verified against each file: in
`0094_fix_shrine_70_coordinates.py` and `0109`–`0113`, the call

```text
shrine.save(update_fields=["latitude", "longitude", "updated_at"])
```

writes **exactly those three columns**. `location` is not recomputed and not
written. The identical call on the real model would also write `location`.

**This is the single most important asymmetry in this audit.** The same line of
code has different effects depending on which model class executes it.

### 6.2 The exclusion is deliberate and documented

All six migrations exclude `location` from the SELECT projection as well:

```text
LOOKUP_FIELDS = ("id", "name_jp", "address", "latitude", "longitude", "updated_at")
Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=SHRINE_ID).first()
```

Stated reason, quoted from `0094_fix_shrine_70_coordinates.py` L11–L22:

> production's `temples_shrine.location` column is a legacy `text` type, while
> every migration's historical model state declares it as a PostGIS
> `PointField` […] Selecting `location` without `.only()` triggers Django's
> GeometryField converter on the raw text value and raises GEOSException before
> any row is touched.

`0109`–`0113` repeat the same rationale in their module docstrings.

So the exclusion protects against a **schema-type mismatch**, and the resulting
`location` staleness is an accepted, recorded side effect — 0094 calls it
"intentionally deferred".

**Finding M-1:** every Production coordinate remediation performed so far
(shrine 70, and Batch 01's 出雲 / 伏見 / 春日 / 熱田 / 宇佐) updated
`latitude`/`longitude` while leaving `location` at its previous value.

## 7. Production Schema Evidence

### 7.1 Physical column type — VERIFIED

Mother Ship read-only query against Production:

```text
PRODUCTION_COLUMN_TYPE = VERIFIED_LEGACY_TEXT

data_type = text
udt_name  = text
```

This closes `Q-1`. The repository's long-standing assertion — carried in the
docstrings of `0094` and `0109`–`0113` (§6.2) — is now confirmed against the
live database rather than inherited from `docs/audit/temples-0091-production-
remediation.md`.

Consequences that follow directly:

- `temples_shrine.location` is **not** a PostGIS `geometry` column in
  Production. The migrations' `only()` exclusion was necessary, not defensive
  over-caution.
- `backfill_location`'s `.only(..., "location")` (§12) would select a text
  column into a field the model declares as `PointField`. The hazard recorded
  as `D-3` is real, not hypothetical.

### 7.2 Deployed application USE_GIS — VERIFIED

```text
PRODUCTION_USE_GIS_SETTING = VERIFIED_FALSE
PRODUCTION_REAL_GIS_BRANCH = DISABLED
```

Mother Ship inspected the deployed Render service directly:

```text
service        = jinja-backend
branch         = develop
start command  = bash start.sh
```

`backend/start.sh` L14 echoes the environment variable on every boot:

```text
echo "USE_GIS=${USE_GIS:-unset}"
```

Render Production startup logs show `USE_GIS=False` repeatedly across deploy and
startup events from 2026-09-15 through 2026-09-22, most recently:

```text
2026-09-22T05:21:26Z   USE_GIS=False
```

### 7.3 How `USE_GIS=False` resolves — verified from source

The startup line prints the **environment variable**, so the chain from that
string to runtime behaviour was traced in this session:

```text
backend/shrine_project/settings.py L19-23
    def env_bool(name, default=False):
        v = os.getenv(name)
        if v is None: return default
        return v.strip().lower() in {"1", "true", "yes", "on"}

    "False".strip().lower() == "false"  ->  NOT in the accepted set  ->  False

backend/shrine_project/settings.py L72
    USE_GIS = env_bool("USE_GIS", default=True)   ->  False

backend/temples/queries.py L16-17
    _use_real_gis() = settings.USE_GIS and not settings.DISABLE_GIS_FOR_TESTS
                    = False and (...)             ->  False  (short-circuit)
```

`DISABLE_GIS_FOR_TESTS` does not need to be known: `USE_GIS` is already false,
so the conjunction short-circuits. `PRODUCTION_REAL_GIS_BRANCH = DISABLED`
follows from the source, not from an assumption about the deployment.

`Q-2` and `Q-4` are closed by this. See §10.4 for the runtime consequence and
§7.4 for a second consequence that is easy to miss.

### 7.4 Second-order consequence — the model's own field type in Production

`backend/temples/models.py` L26-30 computes the same expression:

```text
USE_REAL_GIS = settings.USE_GIS and not settings.DISABLE_GIS_FOR_TESTS
```

With `USE_GIS=False`, `USE_REAL_GIS` is false in the deployed service, so
(L31-41) `PointField` resolves to `django.db.models.JSONField` and `Point` is
`None`. Consequently `Shrine.save()` (§2.1) takes its **non-GIS** branch and
derives:

```text
{"type": "Point", "coordinates": [lng, lat], "srid": 4326}
```

Production's `location` column holds legacy **EWKB hex text** (§8.1). These are
two different serialisations in the same text column. Any write through the real
model in the deployed service would therefore replace a row's EWKB with a JSON
document — a format change, not merely a value change.

This audit does not assert how often a real-model save actually runs in
Production; that is a separate question. It records the consequence because it
materially affects what a future `location` repair would have to decide (§15).

### 7.5 A guard worth noting

`settings.py` L96-97 sets `TEMPLES_USE_NOGIS_MIGRATIONS = IS_PYTEST and
DISABLE_GIS_FOR_TESTS and not USE_SQLITE`. The in-repo comment (L76-94) records
a past incident in which this condition was briefly reduced to
`not USE_GIS and not USE_SQLITE`, and Production — running with `USE_GIS` false,
exactly as it does today — silently switched to the `temples/migrations_nogis`
lineage.

Production is protected today only because `IS_PYTEST` cannot be true there.
Recorded as context: the "`USE_GIS` is false in Production" fact this section
establishes is the same precondition that incident depended on.

## 8. Existing Production Parity

```text
EXISTING_PRODUCTION_PARITY = FAIL

VERIFIED_REMEDIATED_ROWS = 6/6
STALE_LOCATION_ROWS      = 6/6
```

### 8.1 Verified rows

Mother Ship decoded the EWKB text held in `temples_shrine.location` for every
known coordinate-remediation row — the five Batch 01 rows remediated by
`0109`–`0113`, and `0094`'s 多摩川浅間神社:

| Shrine | pk | migration | current `latitude` / `longitude` | decoded `location` | class |
| --- | ---: | --- | --- | --- | --- |
| 伏見稲荷大社 | 2 | 0110 | 34.967133624329 / 135.77318468005 | 34.9671 / 135.7727 | **STALE** |
| 出雲大社 | 4 | 0109 | 35.40190463 / 132.68547534 | 35.4016 / 132.6853 | **STALE** |
| 春日大社 | 5 | 0111 | 34.6812901 / 135.8482531 | 34.6814 / 135.8481 | **STALE** |
| 熱田神宮 | 7 | 0112 | 35.12737043 / 136.90868002 | 35.1279 / 136.9114 | **STALE** |
| 宇佐神宮 | 8 | 0113 | 33.52344557 / 131.37716659 | 33.531 / 131.379 | **STALE** |
| 多摩川浅間神社 | 70 | 0094 | 35.5875263 / 139.6687549 | 35.5898 / 139.6688 | **STALE** |

`location` is **populated, not NULL**, in every one of the six rows. It holds
stale legacy EWKB text.

Raw value as stored for pk=70 (a `text` column, §7.1):

```text
0101000020e610000013f241cf667561402497ff907ecb4140
```

### 8.2 Cross-check against the migration constants

This session parsed the AST constants of `0094` and `0109`–`0113` and compared
them to the supplied evidence. All six rows match on all three axes:

```text
pk=2  0110  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
pk=4  0109  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
pk=5  0111  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
pk=7  0112  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
pk=8  0113  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
pk=70 0094  identity OK   location == OLD_LATITUDE/OLD_LONGITUDE OK   lat/lng == NEW_* OK
```

For pk=70 the raw EWKB hex was supplied, so this session decoded it directly
with `struct` rather than relying on the supplied decode:

```text
byte_order  = little
geom_type   = 1 (Point), SRID flag set
SRID        = 4326
X longitude = 139.6688
Y latitude  = 35.5898
```

The independent decode reproduces the Mother Ship values exactly, and both
equal `0094`'s `OLD_LATITUDE` / `OLD_LONGITUDE`.

The decoded `location` of each row is **exactly** the `OLD_LATITUDE` /
`OLD_LONGITUDE` its migration replaced, and the current `latitude`/`longitude`
is **exactly** that migration's `NEW_*`. There is no rounding slack and no
partial application.

This is not merely consistent with `DUAL_WRITE_PATH_WITH_ASYMMETRIC_DERIVATION`
(§13) — it is a direct positive confirmation of it. The historical model wrote
two columns and left the third holding the pre-migration value in **six out of
six cases**, across two independent migration generations (`0094`, written
2026-08, and `0109`–`0113`, written 2026-09). The defect is systematic, not an
artefact of one authoring session.

### 8.3 Coverage

None. Every coordinate-remediation row known to this audit is now directly
verified against Production:

```text
0094  pk=70  多摩川浅間神社   STALE
0109  pk=4   出雲大社        STALE
0110  pk=2   伏見稲荷大社     STALE
0111  pk=5   春日大社        STALE
0112  pk=7   熱田神宮        STALE
0113  pk=8   宇佐神宮        STALE
```

Six of six. No `MATCH`, no `NULL`, no `UNINTERPRETABLE`.

This audit does not claim that these are the only rows in Production whose
`location` disagrees with `latitude`/`longitude` — only that every row a
coordinate-remediation migration touched is stale. A full-table sweep was not
performed and is not asserted.

## 9. Fresh-Bootstrap Parity

```text
FRESH_BOOTSTRAP_PARITY = PASS   (repository-side determinism only)
```

Given a canonical Base Seed row, tracing §5 and §2.1:

```text
latitude  <- row["latitude"]                           (top-level)
longitude <- row["longitude"]                          (top-level)
location  <- Point(row["longitude"], row["latitude"])  (derived in save())
row["location"] -> discarded; never read
```

The DB result is deterministic and internally consistent, in both the GIS branch
(`Point`) and the NoGIS branch (GeoJSON-shaped JSON). Nested Seed `location`
cannot influence it.

**This is the parity gap, and it is now measured rather than predicted:** a
database built fresh from Seed has `location == f(latitude, longitude)` for
every row, whereas Production holds six verified rows (§8.1) whose `location`
is the pre-remediation coordinate. Fresh bootstrap and migrated Production
**do diverge in `location` while agreeing in `latitude`/`longitude`**.

A Shrine's persisted position therefore depends on how its database was
built, which is the defect `FRESH_BOOTSTRAP_PARITY = PASS` alone does not
express: bootstrap is internally consistent, but it is not reproducible from
the migrated Production state.

## 10. Runtime Authority — which field is actually consumed

This is where the staleness stops being cosmetic.

### 10.1 `location` is read for distance and nearest-ordering

`backend/temples/queries.py` L34–L45 (PostGIS branch):

```text
qs.filter(location__isnull=False).annotate(
    distance_m=RawSQL("ST_DistanceSphere(location, ST_SetSRID(ST_Point(%s,%s),4326))"),
    _knn=RawSQL("location <-> ST_SetSRID(ST_Point(%s,%s),4326)"),
).order_by("_knn", "d_m")
```

Also L47–L57 (Spatialite), L90–L100 and L126–L133 (the same pattern in the
second query helper).

### 10.2 `latitude`/`longitude` are read on the non-GIS path

`backend/temples/queries.py` L58–L75 and L109–L120 annotate a haversine
expression over `latitude` / `longitude`; L142–L155 computes haversine in
Python from `obj.longitude` / `obj.latitude`.
`backend/temples/api/views/search.py` L395–L402 likewise uses
`_haversine_m(lat, lng, rlat, rlng)`.

The branch is selected by
`_use_real_gis()` (`queries.py` L16–L17: `settings.USE_GIS and not
settings.DISABLE_GIS_FOR_TESTS`) **and** `connection.vendor`.

### 10.3 API exposes both, preferring `location`

`backend/temples/api/serializers/shrine.py` L143–L151:

```text
location = SerializerMethodField()
def get_location(self, obj):
    d = to_lat_lng_dict(getattr(obj, "location", None))
    if d: return d
    if obj.latitude is not None and obj.longitude is not None:
        return {"lat": float(obj.latitude), "lng": float(obj.longitude)}
```

`latitude` and `longitude` are also serialized as their own fields (L163–L164,
L176–L178, L208–L215).

**Finding R-1 (resolved after §7.2).** The Production column is confirmed
`text` (§7.1) **and** the deployed service runs with `USE_GIS=False` (§7.2), so
`_use_real_gis()` is false and Production traffic **does not enter** the PostGIS
branches at `queries.py` L34-45 / L47-57 / L90-100 / L126-133. Neither
`ST_DistanceSphere(location, …)` nor `location <-> point` executes.

Current Production nearest / distance behaviour is the PostgreSQL **NoGIS
haversine branch over `latitude` / `longitude`** (`queries.py` L58-75, L109-120,
L142-155), plus `search.py` L395-402.

```text
PRODUCTION_RANKING_INPUT = latitude / longitude   (canonical, post-remediation)
PRODUCTION_LOCATION_ROLE_AT_RUNTIME = not consumed for ranking
```

The earlier "Case 1 / Case 2" fork recorded in this section is **withdrawn**;
Case 1 is the live configuration.

### 10.4 What this does and does not mean

**It does not mean the stale values are harmless.** `EXISTING_PRODUCTION_PARITY`
remains `FAIL`: six rows (§8.1) hold a `location` that contradicts their own
`latitude`/`longitude`, and fresh bootstrap produces a different state than
migrated Production (§9).

**It does mean there is no observed ranking defect.** This audit makes **no
claim** that Production currently ranks or labels distance from stale
coordinates. The coordinates that feed ranking today are the corrected ones.

The distinction matters for prioritisation: this is schema / synchronisation /
contract debt, not a live user-visible correctness defect. It would *become*
one if `USE_GIS` were ever flipped true against the current data — which is
precisely the state the six stale rows make hazardous.

`get_location()` in the API serializer (§10.3) is a separate surface and is not
gated by `_use_real_gis()`; whether it currently returns the stale value or the
lat/lng fallback depends on how `to_lat_lng_dict()` handles EWKB hex text, which
this audit did not test.

## 11. Drift Matrix

| # | Path | Code | Effect | Live today? |
| --- | --- | --- | --- | --- |
| D-1 | Data migration on historical model | `0094`, `0109`–`0113` | lat/lng updated, `location` stale | **Yes — 6 rows VERIFIED (§8.1)** |
| D-2 | Seed edited top-level only | manual edit; no whole-file test (§3.1) | Seed internally inconsistent; harmless to DB (§5) but misleads readers | Possible; 0 occurrences today |
| D-3 | `backfill_location` SELECTs `location` | `backfill_location.py` L18 `.only("id","latitude","longitude","location")` | selects a confirmed `text` column into a `PointField` | **Yes, if run — column type now VERIFIED (§7.1)** |
| D-4 | Env-dependent column type | `models.PointField.deconstruct()` L128–L145 | same migration graph yields `geometry` or `jsonb`/`text` per environment | **Yes, structurally** |
| D-5 | Direct SQL / manual DB edit | outside the ORM | either column can move alone | Unknown |
| D-6 | `AUTO_GEOCODE_ON_SAVE` signal | `backend/temples/signals.py` L110–L128 | sets lat/lng **and** location together, then `save()` re-derives | Consistent — not a drift source |

Runtime note: with `USE_GIS=False` verified in Production (§7.2), none of the
above drift makes Production *ranking* wrong today (§10.4); the drift is in
persisted state and in bootstrap reproducibility.

`location` changed without lat/lng: no ORM path produces it (`save()` always
overwrites `location` from lat/lng). Only D-5 can.

## 12. `backfill_location` Safety

Source: `backend/temples/management/commands/backfill_location.py`

```text
L4   from temples.models import Shrine          ← REAL model
L18  qs = Shrine.objects.only("id","latitude","longitude","location")
L21  s.save(update_fields={"latitude","longitude","location"})
```

- It uses the real model, so `save()` re-derives `location` from lat/lng. As a
  *repair* mechanism its logic is correct and would fix D-1.
- **But it selects `location`** (L18). That is precisely the operation the six
  migrations avoid because it invokes the GEOS converter on a legacy-text
  column (§6.2). If the Production column is legacy text, this command raises
  before writing anything.
- It has no `--dry-run`, no id filter, and wraps every row in one
  `transaction.atomic()`.

```text
BACKFILL_LOCATION_PRODUCTION_SAFETY = NOT_SAFE_AS_WRITTEN
```

No longer conditional: §7.1 confirms the column is `text`, which is the
precondition this hazard depended on.

Not executed in this session against any database.

## 13. Root-Cause Classification

```text
ROOT_CAUSE = DUAL_WRITE_PATH_WITH_ASYMMETRIC_DERIVATION
```

`location` is *designed* as a derived field (§2.1) but is *stored* as an
independent column and *read* as an authoritative one on the GIS path (§10.1).
Derivation is enforced in exactly one of the two writers:

```text
real model save()        -> derives location    (importer, admin, signals, backfill)
historical model save()  -> does NOT derive     (every data migration)
```

Contributing, not causal:

- `C-1` no whole-file Seed equality contract (§3.1)
- `C-2` builder is value-preserving and cannot enforce agreement (§4)
- `C-3` nested Seed `location` is read by no writer, so it looks authoritative
  while being inert (§5)
- `C-4` physical column type is environment-dependent (§2, D-4), which is why
  the migrations must avoid the column at all

The Batch 01 remediation work was correct given these constraints — refusing to
touch `location` was the safe choice. The debt is that nothing has yet
reconciled it.

## 14. Answers to the Required Ownership Questions

**A. Runtime authority.** Split. GIS path (`USE_GIS=1` + PostgreSQL /
Spatialite): `location` for distance, KNN ordering and nearest. Non-GIS path:
`latitude`/`longitude` via haversine. API serializes both and prefers
`location` for the `location` key. Which path Production runs is `NOT_VERIFIED`.

**B. Persistence authority.** `latitude` / `longitude`. They are the only
coordinates every writer sets, the only ones the importer reads, the only ones
the remediation migrations move, and the input from which `save()` derives
`location`.

**C. Derived field.** `Shrine.location` is *logically derived* from
`latitude`/`longitude` — unconditionally so on the real model. It is not
independently authoritative by design. It nonetheless behaves as an independent
store whenever a historical-model migration writes lat/lng without it.

**D. Base Seed nested `location`.** `REDUNDANT`. Not importer input (§5), not
builder-derived (§4), not covered by a whole-file equality test (§3.1). Its only
present function is partial duplication asserted for two named Shrine subsets.

**E. Fresh bootstrap parity.** `PASS`. See §9.

**F. Existing Production parity.** `FAIL`. All six known coordinate-remediation
rows (pk 2/4/5/7/8/70) are directly verified **STALE**: each holds a populated
legacy EWKB `location` equal to the exact pre-remediation coordinate, while
`latitude`/`longitude` hold the post-remediation value. `VERIFIED_REMEDIATED_ROWS
= 6/6`, `STALE_LOCATION_ROWS = 6/6`. See §8.

**G. Drift risk.** See §11.

## 15. Recommended Contract Direction — PRODUCTION STATE RESOLVED

Production state is now fully characterised. The fork recorded in earlier
revisions of this section is closed:

```text
physical location column   = legacy text, populated with EWKB hex   (§7.1, §8.1)
deployed USE_GIS           = False                                   (§7.2)
real-GIS branch            = DISABLED                                (§7.3)
ranking input              = latitude / longitude                    (§10)
remediated rows stale      = 6/6                                     (§8.1)
fresh bootstrap            = internally consistent, diverges from Production (§9)
```

### 15.1 Classification of the debt

```text
ACTIVE_DEBT = SCHEMA / SYNCHRONIZATION / CONTRACT
NOT         = observed PostGIS ranking correctness defect
```

The six stale rows are a real and verified parity failure, but they are not
currently consumed by Production's nearest / distance path. Treating this as an
urgent ranking bug would misprioritise it; treating it as harmless would ignore
that the persisted state is self-contradictory and that bootstrap is not
reproducible from it.

### 15.2 Candidate directions — decisions for Mother Ship, not taken here

1. Name `latitude`/`longitude` as canonical persisted position and `location`
   as derived, in `docs/knowledge/shrine-position-contract.md`. The Contract is
   currently silent on `location` entirely, and §8.1 shows the cost of that
   silence.
2. Decide the nested Seed `location` object's fate explicitly. It must not be
   deleted silently (per task constraint), but leaving an inert duplicate that
   no writer reads is itself a trap.
3. Add a whole-file Seed equality contract test (C-1) whichever way (2) goes.
4. Do not run `backfill_location` as written (§12).
5. Settle the column-type question **before** any Production `location` write.
   §7.4 sharpens this: with `USE_GIS=False` the real model would write a
   GeoJSON-shaped JSON document into a column that currently holds EWKB hex, so
   a naive repair changes the serialisation format rather than reconciling it.
6. Decide whether `location` should exist in Production at all. It is currently
   a text column, populated, unread by the live ranking path, contradicted in
   6/6 remediated rows, and written in two incompatible formats depending on a
   flag. Retiring it is a legitimate option alongside repairing it.

### 15.3 A flag-flip precondition worth recording

Because ranking currently reads `latitude`/`longitude`, the stale `location`
values are latent. They would become live the moment `USE_GIS` were set true
against the present data — the PostGIS branch would then rank six known Shrines
from their pre-remediation coordinates. That is not a prediction about anyone's
plans; it is the reason the debt should be closed before any such change, and
it is why §7.5's note about `USE_GIS` false in Production is recorded rather
than treated as incidental.

## 16. Unresolved Questions

```text
Q-1  RESOLVED  Production temples_shrine.location: data_type = text, udt_name = text (§7.1)

Q-2  RESOLVED  Deployed Render service jinja-backend runs USE_GIS=False, observed in
               startup logs 2026-09-15 .. 2026-09-22 (latest 2026-09-22T05:21:26Z).
               DISABLE_GIS_FOR_TESTS is immaterial: the conjunction short-circuits (§7.3).

Q-3  RESOLVED  All 6 remediation rows classified: pk 2/4/5/7/8/70 = STALE (§8.1).
               VERIFIED_REMEDIATED_ROWS = 6/6, STALE_LOCATION_ROWS = 6/6.

Q-4  RESOLVED  No. _use_real_gis() is false in Production, so the PostGIS branches
               are unreachable. Ranking uses the NoGIS lat/lng haversine branch
               (§10). The "text column under PostGIS operators" question is
               therefore moot for the current configuration.

Q-5  RESOLVED  For all 6 rows, location is populated — not NULL — and holds
               stale legacy EWKB text (§8.1).

Q-6  OPEN      Should the nested Seed location be kept as validation input, or retired?

Q-7  OPEN      Is a Production location backfill wanted at all, or is a column-type
               decision the real prerequisite? (§15 candidate 5)

Q-8  RESOLVED  pk=70 (多摩川浅間神社, migration 0094) = STALE. Raw EWKB supplied
               and independently decoded in this session (§8.2).
```

Every factual question this audit raised is now closed. `Q-6` and `Q-7` remain
open because they are **policy decisions for Mother Ship**, not missing evidence.

One question was opened rather than closed by the runtime evidence:

```text
Q-9  OPEN      Does any real-model save path run against Production today
               (admin, importer, signals)? Under USE_GIS=False such a save
               writes a GeoJSON document into the EWKB text column (§7.4).
               Not tested by this audit.
```

## 17. Scope Statement

This audit update performed no Production DB write, no Base Seed write, no model /
importer / builder change, no migration, and no backfill. It executed no command
against any database. The only repository change is the creation of this
document. The Production evidence in §7–§8 was obtained read-only by
Mother Ship and supplied to this session; this session issued no database
query of its own.
