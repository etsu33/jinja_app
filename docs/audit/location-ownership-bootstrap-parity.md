# Shrine location Ownership / Fresh-Bootstrap Parity Audit

## Status

- Status: `PARTIAL — PRODUCTION EVIDENCE PENDING`
- Recorded at: `2026-09-22`
- Scope: `Shrine.latitude` / `Shrine.longitude` / `Shrine.location` / Base Seed / importer / builder / migrations / fresh bootstrap
- Production DB write: `NONE`
- Base Seed write: `NONE`
- Model / importer / builder change: `NONE`
- Migration created: `NONE`
- Backfill executed: `NONE`

All repository claims below were verified by reading source in this session, not
by citing prior audit prose.

```text
LOCATION_OWNERSHIP = AMBIGUOUS
EXISTING_PRODUCTION_PARITY = NOT_VERIFIED
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

```text
PRODUCTION_COLUMN_TYPE = NOT_VERIFIED
PRODUCTION_USE_GIS_SETTING = NOT_VERIFIED
PRODUCTION_LOCATION_VALUES = NOT_VERIFIED
```

Mother Ship read-only Production evidence was not supplied to this session. The
repository asserts the column is legacy `text` (§6.2), and that assertion is
itself sourced to `docs/audit/temples-0091-production-remediation.md`, but this
audit did not and cannot confirm the live column type. Per the task's own
instruction, no schema state is inferred here.

Required to close this section:

```text
SELECT column_name, data_type, udt_name
  FROM information_schema.columns
 WHERE table_name = 'temples_shrine' AND column_name = 'location';

SELECT id, name_jp, latitude, longitude, location::text
  FROM temples_shrine WHERE id IN (4,2,5,7,8,70);

-- and the effective USE_GIS / DISABLE_GIS_FOR_TESTS values of the Production process
```

## 8. Existing Production Parity

```text
EXISTING_PRODUCTION_PARITY = NOT_VERIFIED
```

Cannot be classified per row without §7. What the repository *predicts*, stated
as a hypothesis to be tested rather than a finding:

| Shrine | pk | remediating migration | predicted `location` state |
| --- | ---: | --- | --- |
| 多摩川浅間神社 | 70 | 0094 | STALE (pre-correction value) |
| 出雲大社 | 4 | 0109 | STALE |
| 伏見稲荷大社 | 2 | 0110 | STALE |
| 春日大社 | 5 | 0111 | STALE |
| 熱田神宮 | 7 | 0112 | STALE |
| 宇佐神宮 | 8 | 0113 | STALE |

Classification vocabulary for when evidence arrives: `MATCH` / `STALE` / `NULL`
/ `UNINTERPRETABLE` (the last for values the GEOS converter cannot parse).

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

**This is the parity gap:** a database built fresh from Seed has
`location == f(latitude, longitude)` for every row, whereas the existing
Production database has six rows where migrations moved lat/lng without moving
`location` (§8, pending verification). Fresh bootstrap and migrated Production
are therefore predicted to **diverge in `location` while agreeing in
`latitude`/`longitude`**.

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

**Finding R-1:** under `USE_GIS=1` + PostgreSQL, a Shrine whose `location` is
stale would be **ranked and distance-labelled from the old coordinate** while
the response's `latitude`/`longitude` fields — and the `location` key itself,
via `get_location` preferring `obj.location` — disagree with each other. Whether
this branch is live in Production is exactly the unknown in §7.

## 11. Drift Matrix

| # | Path | Code | Effect | Live today? |
| --- | --- | --- | --- | --- |
| D-1 | Data migration on historical model | `0094`, `0109`–`0113` | lat/lng updated, `location` stale | **Yes — 6 rows** (pending §7) |
| D-2 | Seed edited top-level only | manual edit; no whole-file test (§3.1) | Seed internally inconsistent; harmless to DB (§5) but misleads readers | Possible; 0 occurrences today |
| D-3 | `backfill_location` SELECTs `location` | `backfill_location.py` L18 `.only("id","latitude","longitude","location")` | GEOSException against a legacy-text column, before any write | **Yes, if run** |
| D-4 | Env-dependent column type | `models.PointField.deconstruct()` L128–L145 | same migration graph yields `geometry` or `jsonb`/`text` per environment | **Yes, structurally** |
| D-5 | Direct SQL / manual DB edit | outside the ORM | either column can move alone | Unknown |
| D-6 | `AUTO_GEOCODE_ON_SAVE` signal | `backend/temples/signals.py` L110–L128 | sets lat/lng **and** location together, then `save()` re-derives | Consistent — not a drift source |

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
BACKFILL_LOCATION_PRODUCTION_SAFETY = NOT_SAFE_AS_WRITTEN (conditional on §7)
```

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

**F. Existing Production parity.** `NOT_VERIFIED`. See §7–§8.

**G. Drift risk.** See §11.

## 15. Recommended Contract Direction — WITHHELD

The task instructs stopping before a final ownership recommendation when
Production evidence is essential. It is essential here: the correct direction
differs materially depending on §7.

```text
If Production location is legacy text AND USE_GIS is off in Production
  -> location is currently inert at runtime; the debt is latent, and the
     remedy is a schema decision, not a data backfill.

If Production location is geometry AND USE_GIS is on
  -> §10.1 means six remediated Shrines are being ranked from stale points
     right now; this is a live correctness defect, not documentation debt.
```

Those two worlds call for different first moves, so no single direction is
recorded as the recommendation.

Directionally stable regardless of §7, and offered as candidates rather than
decisions:

1. Name `latitude`/`longitude` as canonical persisted position and `location`
   as derived, in `docs/knowledge/shrine-position-contract.md` — the Contract
   is currently silent on `location` entirely.
2. Decide the nested Seed `location` object's fate explicitly. It must not be
   deleted silently (per task constraint), but leaving an inert duplicate that
   no writer reads is itself a trap.
3. Add a whole-file Seed equality contract test (C-1) whichever way (2) goes.
4. Do not run `backfill_location` as written (§12).

## 16. Unresolved Questions

```text
Q-1  Production temples_shrine.location: actual data_type / udt_name?
Q-2  Production process: effective USE_GIS / DISABLE_GIS_FOR_TESTS?
Q-3  Do the 6 remediated rows have MATCH / STALE / NULL / UNINTERPRETABLE location?
Q-4  Does any Production traffic reach queries.py's PostGIS branch?
Q-5  If location is legacy text, was it ever populated, or is it NULL throughout?
Q-6  Should the nested Seed location be kept as validation input, or retired?
Q-7  Is a Production location backfill wanted at all, or is a column-type
     decision the real prerequisite?
```

`Q-1`–`Q-5` are answerable only with Mother Ship read-only Production evidence.
`Q-6`–`Q-7` are policy decisions for Mother Ship.

## 17. Scope Statement

This audit performed no Production DB write, no Base Seed write, no model /
importer / builder change, no migration, and no backfill. It executed no command
against any database. The only repository change is the creation of this
document.
