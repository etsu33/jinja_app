# Canonical Shrine Anchor Contract — Impact Audit

## Status

- Status: `ASSESSMENT_ONLY`
- Recorded at: `2026-09-23`
- Subject: proposed `Canonical Shrine Anchor Contract`
- Authoritative contract at time of writing: `docs/knowledge/shrine-position-contract.md` (`ACTIVE`)
- Proposed contract state: `PROPOSED` (not adopted)
- Production write: `NONE`
- Base Seed write: `NONE`
- Candidate Master write: `NONE`
- Position status change: `NONE`

本書は Contract の変更でも移行でもない。現行 Contract の authority は
`docs/knowledge/shrine-position-contract.md` のままであり、本書はその変更を提案するものでもない。

## 1. Scope

This audit answers one question only:

```text
If Shrine.latitude / Shrine.longitude were redefined from
  Visitor / Navigation Anchor
to
  Canonical Shrine Anchor (religious / ritual center)
under the proposed P1–P5 adjudication priority,
what breaks, what survives, and what new evidence would be required?
```

### Non-Goals

- This is **not** a re-adjudication. No `PASS` / `HOLD_POSITION_REVIEW` status is changed.
- This is **not** a Contract migration. `docs/knowledge/shrine-position-contract.md` is not modified.
- This is **not** a coordinate remediation task. No coordinate is proposed, adopted, or written.
- No Production, Base Seed, Candidate Master, migration, or `Shrine.latitude` / `Shrine.longitude` write is performed.
- No Recommendation / Ranking / Concierge / Compass logic is changed.
- No decision gate is selected.

## 2. Contract Comparison

### 2.1 Currently active canonical meaning

`docs/knowledge/shrine-position-contract.md`:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

Declared primary uses (§Canonical Meaning, 主用途):

```text
1. 地図上のShrine表示
2. 現在地からのdistance計算
3. Compassのdirection計算
4. route guidance
5. Shrine detailからの地図導線
```

Declared non-anchors (点を自動的にVisitor / Navigation Anchorとはみなさない):

```text
- 法人登記上の本店所在地
- 歴史資料上の旧所在地
- 境内を含む行政地番の任意点
- 山域・御神体・境内全体のcentroid
- 駐車場・社務所・登山口など、Shrineそのものと確認できない補助地点
```

### 2.2 Proposed canonical meaning

```text
Shrine.latitude / Shrine.longitude
= Canonical Shrine Anchor (religious / ritual center)
```

Adjudication priority:

```text
P1  identified Honden / Shoden / Hongu functioning as primary ritual center
P2  principal ritual complex or main sanctuary area
P3  confirmed non-building ritual center (iwakura, sacred object, sacred mountain site)
P4  multiple principal ritual sites -> adopt only with an authoritative primary
    ritual center or explicit canonical relationship
P5  ritual center undeterminable or not geographically traceable -> HOLD_POSITION_REVIEW
```

Explicitly excluded by the proposal:

```text
- postal address geocode
- precinct centroid
- main entrance
- parking area
- shrine office
- generic map-provider POI
```

### 2.3 Structural relationship between the two contracts

Three relationships are observable, and they are not the same kind of change.

```text
RELATION_1 = NARROWING
RELATION_2 = DIRECT_INVERSION
RELATION_3 = SOURCE_CLASS_INVALIDATION
```

**RELATION_1 — NARROWING.** `precinct centroid`, `main entrance`, `parking area`,
`shrine office` are excluded by both contracts. On these terms the proposal narrows
an existing exclusion rather than reversing it.

**RELATION_2 — DIRECT_INVERSION.** The active Contract lists
`山域・御神体・境内全体のcentroid` among the points that are **not** automatically the
anchor. Proposed `P3` adopts precisely that class — `iwakura, sacred object, sacred
mountain site` — as the canonical anchor when the shrine is centered on it. This is
not a gap between the two contracts; it is a reversal of one specific rule. Any
migration must state that reversal explicitly rather than absorb it silently.

**RELATION_3 — SOURCE_CLASS_INVALIDATION.** The proposal excludes
`a generic map-provider POI`. In Batch 01, **10 of 10** records recorded
`primary_source_type = map_provider_poi`, and it is the only source class that
produced traceable coordinates in any record. This is examined in §6.

## 3. Evidence Basis

| Evidence | Location | Used for |
| --- | --- | --- |
| Batch 01 adjudication records (10 shrines, §4–§13) | `docs/audit/position-audit-v2/legacy-position-provenance-batch01.md` | status, adopted coordinate, anchor semantics, evidence type |
| Batch 01 remediation table (§15) and execution record (§16) | same | Production / Base Seed remediation state |
| Active Position Contract | `docs/knowledge/shrine-position-contract.md` | current canonical meaning, declared consumers, exclusion list |
| Location ownership audit | `docs/audit/location-ownership-bootstrap-parity.md` | Production state, downstream `location` / lat-lng read paths |
| Repository source inspection | see §8 | downstream semantic consumers |

All ten Batch 01 records carry:

```text
primary_source_type = map_provider_poi
```

Providers: Mapion (`出雲大社`, `明治神宮`, `熱田神宮`, `宇佐神宮`, `日光東照宮`, `鶴岡八幡宮`),
MapFan (`伏見稲荷大社`, `伊勢神宮（内宮）`, `春日大社`, `太宰府天満宮`).

Eight `PASS` records carry `anchor_type = SHRINE_POI / PRECINCT_CORE`.
`太宰府天満宮` carries `candidate_anchor_type = SHRINE_POI`; `鶴岡八幡宮` carries
`anchor_type = NOT_DETERMINED`.

## 4. Impact Class Definitions

```text
PRESERVED_BY_EXISTING_EVIDENCE
  The existing record already evidences the adopted point as the ritual center.
  The adopted coordinate would survive the redefinition without new evidence.

REQUIRES_READJUDICATION
  The existing record explicitly names a ritual center AND explicitly places it
  outside the adopted anchor. The redefinition inverts the record's own reasoning,
  so the record must be re-adjudicated.

REQUIRES_NEW_EVIDENCE
  The existing record is silent on the ritual center. Neither preservation nor
  invalidation can be established from the record; new evidence is required before
  the record can be classified at all.

POTENTIALLY_RESOLVABLE_HOLD
  Currently HOLD. The proposed contract removes the specific semantic ambiguity
  that caused the HOLD, so the HOLD becomes resolvable in principle — but is not
  resolved, because a remaining evidence gap still blocks adoption.

UNCHANGED_HOLD
  Currently HOLD, and the proposed contract neither removes the cause nor adds one.

INDETERMINATE
  The record does not support any of the above classifications.
```

## 5. Impact Matrix

Twelve columns, one row per Batch 01 shrine. `Prod.` / `Seed` = remediation already
executed for the currently adopted Visitor / Navigation Anchor (`docs/audit/position-audit-v2/legacy-position-provenance-batch01.md` §15).

| # | Shrine | Current status | Current anchor semantics | Current coordinate | Current evidence type | Prod. remediated? | Seed remediated? | Proposed P1–P5 candidate | Existing ritual-center evidence sufficient? | Impact class | Reason | Required next evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 明治神宮 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; `pedestrian_entry_anchor` / `vehicle_entry_anchor` / `parking_anchor` = SEPARATE_CONCEPT | 35.67623602, 139.69934113 (adopted) | `map_provider_poi` (Mapion) | NOT_YET_PERFORMED | NOT_YET_PERFORMED | P1 (社殿 / 本殿) — not identified in record | NO — record names no ritual point | REQUIRES_NEW_EVIDENCE | The record establishes only that the point is not a gate, parking or vehicle destination. It makes no claim about the ritual center. | Georeferenced authoritative source locating the 本殿 / 社殿, traceable to a coordinate |
| 02 | 伏見稲荷大社 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; `station_access_point` / `parking_anchor` / `specific_gate_anchor` / `mountain_or_trail_route_point` = SEPARATE_CONCEPT | 34.967133624329, 135.77318468005 (adopted) | `map_provider_poi` (MapFan) | PERFORMED (0110) | PERFORMED | P1 (本殿) or P3 (稲荷山) — not determined in record | NO — record names no ritual point | REQUIRES_NEW_EVIDENCE | The record explicitly sets aside the mountain/trail route point as a navigation concept, but never adjudicates 稲荷山 as a ritual center. P1 and P3 are both open. | Authoritative evidence establishing whether the ritual center is the 本殿 or the mountain site, then a traceable coordinate for it |
| 03 | 伊勢神宮（内宮） | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; **`shogu_building_anchor` = SEPARATE_CONCEPT**; `uji_bridge_entry_anchor` / `parking_anchor` = SEPARATE_CONCEPT | 34.4549588, 136.7251689 (adopted) | `map_provider_poi` (MapFan) | NOT_YET_PERFORMED | NOT_YET_PERFORMED | P1 (正宮) | NO — record names the 正宮 and rules it out | REQUIRES_READJUDICATION | The record states the adopted point is "not an assertion that the same coordinate represents … the Shogu building itself". Under the proposal the 正宮 is exactly what the anchor must represent. | Traceable coordinate for the 正宮, plus resolution of the recorded ≈68 m primary/corroboration spread under ritual-center semantics |
| 04 | 出雲大社 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; no auxiliary term recorded | 35.40190463, 132.68547534 (adopted) | `map_provider_poi` (Mapion) | PERFORMED (0109) | PERFORMED | P1 (御本殿) — not identified in record | NO — record names no ritual point | REQUIRES_NEW_EVIDENCE | The record's anchor-semantics block contains only `anchor_type` and `anchor_semantics`. It rules out parking and auxiliary facilities but never locates the 御本殿. | Georeferenced authoritative source locating the 御本殿, traceable to a coordinate |
| 05 | 春日大社 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; **`main_sanctuary_anchor` = SEPARATE_CONCEPT**; `parking` / `bus_stop` / `museum` / `botanical_garden` = SEPARATE_CONCEPT | 34.6812901, 135.8482531 (adopted) | `map_provider_poi` (MapFan) | PERFORMED (0111) | PERFORMED | P1 / P2 (本殿・中門御廊を含む本社域) | NO — record names the main sanctuary and rules it out | REQUIRES_READJUDICATION | `main_sanctuary_anchor = SEPARATE_CONCEPT` is a direct statement that the adopted point is not the main sanctuary. The proposal requires the opposite. | Traceable coordinate for the main sanctuary; determination of whether P1 (single building) or P2 (sanctuary area) applies |
| 06 | 太宰府天満宮 | HOLD_POSITION_REVIEW | `candidate_anchor_type = SHRINE_POI`, `REVIEW_REQUIRED`; **`main_sanctuary_anchor` = DISTINCT_VISITOR_POINT**; `roumon` / `taiko_bridge_shinji_ike` / `information_center` = DISTINCT_VISITOR_POINT | `ADOPTED_COORDINATE = NOT_DETERMINED`; Production retains 33.5213, 130.5351 (`LEGACY_UNTRACED`) | `map_provider_poi` (MapFan) — candidate only, `TRACEABLE_SAME_ENTITY_NOT_ADOPTED` | NONE | NONE | P1 (御本殿) | NO — the 御本殿 is named but not georeferenced | POTENTIALLY_RESOLVABLE_HOLD | The recorded HOLD cause is that the Contract "does not define which internal concept owns the canonical anchor". The proposal defines it (P1 = 御本殿), removing that specific ambiguity. The HOLD does not clear, because the record also states the official material "does not expose georeferenced coordinates". That is a P5 condition, not a semantic one. | Georeferenced coordinate for the 御本殿 from a source that survives the proposal's exclusion of generic map-provider POIs |
| 07 | 熱田神宮 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; **`hongu_anchor` = DISTINCT_VISITOR_POINT**; east/west/south gate, `parking`, `kyucho` = SEPARATE_CONCEPT; `access_map_center` = SEPARATE_ACCESS_OVERVIEW_CONCEPT | 35.12737043, 136.90868002 (adopted) | `map_provider_poi` (Mapion) | PERFORMED (0112) | PERFORMED | P1 (本宮) | NO — the 本宮 is recorded as a *distinct* point from the adopted anchor | REQUIRES_READJUDICATION | `hongu_anchor = DISTINCT_VISITOR_POINT` states the 本宮 is a different point from the adopted one. Under the proposal the 本宮 is the P1 target. | Traceable coordinate for the 本宮 from a source admissible under the proposal |
| 08 | 宇佐神宮 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; **`upper_shrine_anchor` = DISTINCT_VISITOR_POINT**; `lower_shrine_area` = DISTINCT_VISITOR_CONCEPT; `kurehashi_west_approach` / `treasure_museum` / `parking` / `bus_stop` = SEPARATE_CONCEPT | 33.52344557, 131.37716659 (adopted) | `map_provider_poi` (Mapion) | PERFORMED (0113) | PERFORMED | P1, P2 or P4 — undetermined | NO — the 上宮 is recorded as a *distinct* point from the adopted anchor | REQUIRES_READJUDICATION | The record separates 上宮 and 下宮 as distinct internal concepts and adopts neither. The proposal requires one to be designated. The record does not establish whether a single 本殿 within the 上宮 is the primary ritual center, so P1 / P2 / P4 cannot be chosen from the record alone. | Authoritative determination of the primary ritual center between 上宮 / 下宮 and within the 上宮; then a traceable coordinate for it |
| 09 | 日光東照宮 | PASS | `SHRINE_POI / PRECINCT_CORE`, `CONFIRMED`; **`main_sanctuary_anchor` = DISTINCT_VISITOR_POINT**; `worship_area_anchor` = DISTINCT_VISITOR_CONCEPT; `entrance` / `gate` / `parking` / `office` / `museum` / `bus_stop` = SEPARATE_CONCEPT | 36.75811138, 139.59874963 (adopted) | `map_provider_poi` (Mapion), surrounding-view QA confirmed precinct | NOT_YET_PERFORMED | NOT_YET_PERFORMED | P1 / P2 (御本社 — 本殿・石の間・拝殿) | NO — the main sanctuary is recorded as a *distinct* point from the adopted anchor | REQUIRES_READJUDICATION | The record separates `main_sanctuary_anchor` and `worship_area_anchor` from the adopted anchor. The surrounding-view QA established that the adopted point lies inside the 東照宮 precinct — which is precinct evidence, not ritual-center evidence. | Traceable coordinate for the 御本社; determination of whether P1 (本殿) or P2 (本社域) applies |
| 10 | 鶴岡八幡宮 | HOLD_POSITION_REVIEW | `anchor_type = NOT_DETERMINED`, `REVIEW_REQUIRED`; **`hongu_upper_shrine_anchor`** / **`wakamiya_lower_shrine_anchor`** / **`shamusho_office_anchor`** = DISTINCT_VISITOR_POINT; `maidono` / `shirahata_shrine` / `treasure_hall` / `museum` / `parking` = SEPARATE_CONCEPT | `ADOPTED_COORDINATE = NOT_DETERMINED`; Production retains 35.3256, 139.5566 (`LEGACY_UNTRACED`) | `map_provider_poi` (Mapion) — candidate resolves to 社務所, not adopted | NONE | NONE | P1 (本宮 / 上宮) | NO — 本宮/上宮 is named, but only via an OSM-class corroboration source | POTENTIALLY_RESOLVABLE_HOLD | The recorded HOLD is a three-way conflict between 社務所 (primary), 若宮/下宮 (stored legacy) and 本宮/上宮 (corroboration), unresolvable because the active Contract does not say which internal concept owns the anchor. The proposal answers that directly: P1 selects 本宮/上宮, and the proposal's own exclusions eliminate both the 社務所 (shrine office) and the map-provider POI. The HOLD does not clear, because the only source pointing at 本宮/上宮 is the corroboration source, which may not be promoted to primary. | A primary-class source that georeferences the 本宮/上宮, independent of the OSM-class corroboration |

### 5.1 Impact class distribution

```text
PRESERVED_BY_EXISTING_EVIDENCE = 0
REQUIRES_READJUDICATION        = 5
REQUIRES_NEW_EVIDENCE          = 3
POTENTIALLY_RESOLVABLE_HOLD    = 2
UNCHANGED_HOLD                 = 0
INDETERMINATE                  = 0
TOTAL                          = 10
```

The `PRESERVED_BY_EXISTING_EVIDENCE = 0` result is the central finding of this audit.
Not one Batch 01 record, including the eight `PASS` records, contains evidence that
the adopted coordinate represents the shrine's ritual center. This is not an oversight
in those records: the active Contract never asked that question, so no record was
built to answer it.

## 6. Explicit Inspection — was the ritual center deliberately excluded?

The following five records were inspected individually to determine whether the
ritual-center terms they contain were *deliberately excluded* under the active
Contract, or merely absent.

This distinction matters because the two cases imply different migration costs.
A deliberate exclusion means a decision exists and can be revisited. An absence
means no decision was ever made and the question is open from zero.

### 6.1 伏見稲荷大社 — NOT deliberately excluded (absent)

Recorded anchor-semantics block (§6.5):

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED

station_access_point = SEPARATE_CONCEPT
parking_anchor = SEPARATE_CONCEPT
specific_gate_anchor = SEPARATE_CONCEPT
mountain_or_trail_route_point = SEPARATE_CONCEPT
```

```text
RITUAL_CENTER_TERM_PRESENT   = NO
DELIBERATE_EXCLUSION         = NOT_ESTABLISHED
```

No 本殿, 奥社, or 稲荷山-as-ritual-site term appears anywhere in the record. The
`mountain_or_trail_route_point` term is set aside explicitly, but the record's own
prose frames it as a *route* concept — "rather than a station, parking location,
specific gate, or mountain/trail route point" — not as an adjudication of 稲荷山 as a
sacred mountain site under proposed `P3`.

**Correction to a plausible reading:** it would be easy to read
`mountain_or_trail_route_point = SEPARATE_CONCEPT` as a deliberate rejection of the
`P3` sacred-mountain candidate. It is not. The record rejects it as a navigation
waypoint class, on navigation grounds. Proposed `P3` would ask a different question
that this record never poses.

### 6.2 伊勢神宮（内宮） — deliberately excluded

```text
shogu_building_anchor = SEPARATE_CONCEPT
```

Record prose (§7.5): "The adopted candidate is treated as the Shrine-level
representative POI, not as an assertion that the same coordinate represents Uji
Bridge, a parking facility, or the Shogu building itself."

```text
RITUAL_CENTER_TERM_PRESENT   = YES (正宮 / Shogu)
DELIBERATE_EXCLUSION         = YES
EXCLUSION_GROUND             = Shrine-level representative POI semantics
```

The exclusion is explicit and reasoned. Under the active Contract it is correct.
Under the proposal it is exactly backwards.

### 6.3 熱田神宮 — deliberately excluded

```text
hongu_anchor = DISTINCT_VISITOR_POINT
```

```text
RITUAL_CENTER_TERM_PRESENT   = YES (本宮)
DELIBERATE_EXCLUSION         = YES
EXCLUSION_GROUND             = 本宮 is a distinct visitor point within the precinct
```

The record additionally classifies the source's own access-map center as
`SEPARATE_ACCESS_OVERVIEW_CONCEPT`, confirming the record was reasoning in
visitor/navigation terms throughout, not ritual terms.

### 6.4 宇佐神宮 — deliberately excluded

```text
upper_shrine_anchor = DISTINCT_VISITOR_POINT
lower_shrine_area   = DISTINCT_VISITOR_CONCEPT
```

```text
RITUAL_CENTER_TERM_PRESENT   = YES (上宮 / 下宮)
DELIBERATE_EXCLUSION         = YES
EXCLUSION_GROUND             = both treated as internal visitor concepts, neither adopted
RITUAL_PRIMACY_BETWEEN_THEM  = NOT_ADJUDICATED
```

The record explicitly states the auxiliary coordinates "are not used as canonical
Shrine Position evidence". It treats 上宮 and 下宮 symmetrically as internal visitor
concepts. It does not rank them, because under the active Contract there was no
reason to. Proposed `P1` / `P4` would require exactly that ranking.

### 6.5 鶴岡八幡宮 — deliberately excluded, and the exclusion is the recorded HOLD cause

```text
hongu_upper_shrine_anchor   = DISTINCT_VISITOR_POINT
wakamiya_lower_shrine_anchor = DISTINCT_VISITOR_POINT
shamusho_office_anchor       = DISTINCT_VISITOR_POINT
```

Record prose (§13.8): "three coordinates identify the same Shrine while resolving to
three different internal visitor concepts — 社務所 (Primary), 若宮/下宮 (stored
legacy), and 本宮/上宮 (corroboration) — and the active Position Contract does not
define which internal concept owns the canonical Shrine-level anchor for a large
multi-concept precinct."

```text
RITUAL_CENTER_TERM_PRESENT   = YES (本宮/上宮, 若宮/下宮)
DELIBERATE_EXCLUSION         = YES
EXCLUSION_GROUND             = active Contract defines no owner among internal concepts
HOLD_CAUSE_ADDRESSED_BY_P1_P5 = YES (semantic ownership), NO (source admissibility)
```

This is the one record whose recorded HOLD-resolution condition (§13, and §9.8 for
太宰府天満宮) explicitly anticipates a policy decision of the kind the proposal makes:
"an explicit Position policy decision defining which precinct semantic … owns the
canonical `Shrine.latitude / Shrine.longitude`."

### 6.6 Inspection summary

```text
DELIBERATE_EXCLUSION = YES         : 伊勢神宮（内宮）, 熱田神宮, 宇佐神宮, 鶴岡八幡宮  (4)
DELIBERATE_EXCLUSION = NOT_ESTABLISHED : 伏見稲荷大社                                (1)
```

Extending the same test to the remaining five Batch 01 records:

```text
出雲大社     ritual-center term absent      -> NOT_ESTABLISHED
明治神宮     ritual-center term absent      -> NOT_ESTABLISHED
春日大社     main_sanctuary_anchor present  -> DELIBERATE_EXCLUSION = YES
太宰府天満宮 main_sanctuary_anchor present  -> DELIBERATE_EXCLUSION = YES
日光東照宮   main_sanctuary_anchor present  -> DELIBERATE_EXCLUSION = YES
```

```text
BATCH01_DELIBERATE_EXCLUSION_YES            = 7
BATCH01_RITUAL_CENTER_QUESTION_NEVER_POSED  = 3  (出雲大社, 明治神宮, 伏見稲荷大社)
```

### 6.7 Source-class observation

```text
BATCH01_RECORDS_WITH_primary_source_type = map_provider_poi : 10 / 10
```

The proposed contract excludes "a generic map-provider POI" from automatically being
the Canonical Shrine Anchor. Taken together with §5.1, this yields an observation that
the migration decision should confront directly:

```text
OBSERVATION: the only source class that produced traceable coordinates in any
Batch 01 record is the one source class the proposal excludes.
```

Two readings are possible and this audit does not choose between them:

- **Reading 1 (narrow):** the proposal excludes map-provider POIs only from
  *automatic* adoption. A map-provider POI that a source explicitly labels as the
  本殿 / 本宮 would still be admissible. Under this reading the exclusion is a
  labelling requirement, not a source ban.
- **Reading 2 (broad):** the proposal requires evidence "that it represents the
  Shrine's ritual center", which map-provider shrine POIs structurally do not
  express — they publish one representative point per entity without internal
  semantics. Under this reading the source class is effectively unavailable.

```text
SOURCE_CLASS_READING = NOT_RESOLVED_BY_THIS_AUDIT
```

**Hypothesis, not finding:** if Reading 2 holds, the proposed contract may be
non-satisfiable at the currently available evidence supply for most shrines, and
would convert a large share of records to `P5` / `HOLD_POSITION_REVIEW` for an
indefinite period. This is stated as a hypothesis because no evidence-availability
survey has been performed. §9 Gate D exists to test it.

## 7. Blast Radius

```text
BATCH01_PASS_AT_RISK                = 8
BATCH01_HOLD_REVIEW_IMPACT          = 2
PRODUCTION_REMEDIATED_ROWS_AFFECTED = 5
BASE_SEED_REMEDIATED_ROWS_AFFECTED  = 5
```

### 7.1 `BATCH01_PASS_AT_RISK = 8`

All eight `PASS` records. "At risk" means the recorded `PASS` was adjudicated against
a canonical meaning that the proposal replaces; it does **not** mean any `PASS` is
wrong, and this audit invalidates none of them (§10).

```text
REQUIRES_READJUDICATION : 伊勢神宮（内宮）, 春日大社, 熱田神宮, 宇佐神宮, 日光東照宮  (5)
REQUIRES_NEW_EVIDENCE   : 出雲大社, 明治神宮, 伏見稲荷大社                          (3)
```

### 7.2 `BATCH01_HOLD_REVIEW_IMPACT = 2`

```text
太宰府天満宮 : POTENTIALLY_RESOLVABLE_HOLD
鶴岡八幡宮   : POTENTIALLY_RESOLVABLE_HOLD
```

Both HOLDs were caused by `UNRESOLVED_ANCHOR_SEMANTICS_CONFLICT` — the active
Contract not defining which internal precinct concept owns the anchor. The proposal
defines it. Neither HOLD is resolved here, and both remain `HOLD_POSITION_REVIEW`.

### 7.3 `PRODUCTION_REMEDIATED_ROWS_AFFECTED = 5`

Rows already written to Production with a coordinate adopted under the *Visitor /
Navigation Anchor* meaning:

| Shrine | pk | migration | written coordinate |
| --- | ---: | --- | --- |
| 伏見稲荷大社 | 2 | `0110` | 34.967133624329, 135.77318468005 |
| 出雲大社 | 4 | `0109` | 35.40190463, 132.68547534 |
| 春日大社 | 5 | `0111` | 34.6812901, 135.8482531 |
| 熱田神宮 | 7 | `0112` | 35.12737043, 136.90868002 |
| 宇佐神宮 | 8 | `0113` | 33.52344557, 131.37716659 |

A redefinition does not silently invalidate these writes — the coordinates are
unchanged and traceable — but it changes what they are *claimed to mean*. Three of the
five (`春日大社`, `熱田神宮`, `宇佐神宮`) are `REQUIRES_READJUDICATION`, i.e. their own
records state the adopted point is not the ritual center.

### 7.4 `BASE_SEED_REMEDIATED_ROWS_AFFECTED = 5`

The same five shrines in `backend/temples/data/shrines_seed_clean.json`. Each seed row
was synced to match the adopted Production coordinate (`latitude`, `longitude`,
`location.lat`, `location.lng`).

### 7.5 Scope note — rows outside this blast radius

Two populations are deliberately **not** counted above, and both are larger than the
counted set.

```text
UNCOUNTED_1 = 多摩川浅間神社 (pk=70, migration 0094)
```

A sixth Production-remediated position row exists, recorded in
`docs/audit/location-ownership-bootstrap-parity.md`. It predates Batch 01 and was never
adjudicated under either contract. It is not counted in
`PRODUCTION_REMEDIATED_ROWS_AFFECTED` because that counter is Batch 01-scoped, but a
Contract migration would reach it.

```text
UNCOUNTED_2 = 103 non-Batch-01 Production Shrine rows
```

Production holds 113 Shrine rows. Ten are adjudicated. The remaining 103 — pk=70
among them — carry no anchor-semantics record under *either* contract. A redefinition does not change their
recorded state, because they have none — but it changes what a future audit of them
must establish, from a navigation claim to a ritual-center claim.

```text
PRODUCTION_ROWS_IN_SCOPE          = 113
  BATCH01_ADJUDICATED             =  10  (8 PASS + 2 HOLD)
  UNADJUDICATED                   = 103  (includes pk=70, position-remediated by 0094)
BLAST_RADIUS_COUNTERS_COVER      =   5 Production rows + 5 Seed rows (Batch 01 only)
```

## 8. Downstream Semantic Consumers

The active Contract declares five primary uses. Each was traced to code. No code was
modified.

### 8.1 Map display — `SEMANTICALLY_COMPATIBLE`

```text
backend/temples/api/serializers/shrine.py L143, L146-151  location SerializerMethodField / get_location() (prefers obj.location, falls back to lat/lng)
backend/temples/api/serializers/shrine.py L163-164, L176-178, L208-215  latitude / longitude serialized
```

A marker rendered at the ritual center is still a correct "this shrine is here"
marker. Display carries no promise about which internal point is shown.

```text
CLASSIFICATION = SEMANTICALLY_COMPATIBLE
CAVEAT         = at high zoom inside a large precinct the marker would move to a
                 different building; this is a presentation change, not a contract break
```

### 8.2 Distance — `INDETERMINATE`

```text
backend/temples/queries.py L58-75, L109-120, L142-155   haversine over latitude / longitude
backend/temples/queries.py L34-45, L47-57, L90-100, L126-133  PostGIS branch over location (_use_real_gis(), L15-18 — DISABLED in Production)
backend/temples/api/views/search.py L37 (def), L402 (call)  _haversine_m(lat, lng, rlat, rlng)
apps/web/src/components/shrines/ShrineCard.tsx L110     distanceM rendered to the user
apps/web/src/components/shrines/ShrineCardLite.tsx L68  distanceM rendered to the user
```

Distance serves two jobs through one number. As a **ranking key** ("which shrines are
near me") a ritual-center anchor is as valid as a navigation anchor. As a **rendered
figure** ("420m") it reads to the user as how far they must travel, which is a
navigation claim.

The magnitude of divergence is not established. Batch 01 recorded intra-shrine
separations from ≈7 m (`宇佐神宮` primary vs corroboration) to ≈857 m (`宇佐神宮`
adopted vs legacy Production). Proposed `P3` (sacred mountain site) admits anchors that
could sit kilometres from any visitor approach, but no `P3` case has been adjudicated.

```text
CLASSIFICATION = INDETERMINATE
DECIDING_QUESTION = does the rendered distanceM figure constitute a navigation
                    promise to the user, or a proximity indicator?
```

This audit does not answer that question; it is a product decision, not a repository fact.

### 8.3 Compass direction — `SEMANTICALLY_COMPATIBLE`

```text
backend/temples/services/direction_reference.py L35-44   _bearing() / _direction_label()
backend/temples/services/direction_reference.py L71-74   origin lat/lng, shrine latitude/longitude
backend/temples/services/direction_reference.py L48, L96 build_direction_reference() / attach_direction_references()
backend/temples/services/compass_direction_filter.py L21, L29, L53-54, L71-77  filter_candidates_by_direction()
```

Bearing answers "which way is the shrine". A ritual center is a defensible — arguably
a better — answer to that question than a precinct POI.

```text
CLASSIFICATION = SEMANTICALLY_COMPATIBLE
CAVEAT         = bearing is scale-sensitive. At 10 km, an 800 m anchor shift moves the
                 bearing by under 5°. At 200 m, the same shift can invert the direction
                 label. compass_direction_filter.py filters candidates on this bearing,
                 so near-field filtering results would change.
```

### 8.4 Route guidance — `NEEDS_NAVIGATION_ANCHOR_SPLIT`

```text
apps/web/src/features/map/components/NearbyShrineCardListClient.tsx L282  buildGoogleMapsDirUrl({ origin, destination: { lat, lng, address, fallbackName } })
apps/web/src/lib/maps/googleMaps.ts L26-38                               destination= resolveDestination(...) -> "lat,lng"
apps/web/src/lib/maps/destinationContract.ts L35-47, L75-80              toValidDestinationCoords() / resolveDestination() — coords take priority over address and name
```

This path takes the shrine's stored coordinate and emits it verbatim as Google Maps
`destination=<lat>,<lng>`. It is the single most literal consumer of the
*Visitor / Navigation Anchor* meaning: the field **is** the navigation destination,
with no intermediate layer.

Under the proposal, `P1` would route users to a 本殿 that typically sits inside a
precinct with no vehicle access and often no addressable footpath node; `P3` would
route them to a sacred object or mountain site. `resolveDestination()` prefers
coordinates over address, so a valid-but-unroutable coordinate silently wins over the
address that would have produced a usable route.

```text
CLASSIFICATION = NEEDS_NAVIGATION_ANCHOR_SPLIT
```

Not affected: `buildGoogleMapsSearchUrl()` (`apps/web/src/lib/maps/googleMaps.ts` L10-13)
builds a query from name + address and reads no coordinate.

### 8.5 Shrine detail map link — `NEEDS_NAVIGATION_ANCHOR_SPLIT`

```text
apps/web/src/app/shrines/[id]/page.tsx L290-298   toValidDestinationCoords({ lat: Number(s.latitude), lng: Number(s.longitude) })
                                                   -> gmapsDirUrl({ dest: destCoords, mode: "walk" })
apps/web/src/lib/maps.ts L15-31                    gmapsDirUrl() -> destination=<lat>,<lng>&travelmode=walking
apps/web/src/components/shrine/ShrineDetailShell.tsx L26, L50, L65, L89-91  googleDirHref -> GoogleMapRouteLink href
apps/web/src/components/shrine/GoogleMapRouteLink.tsx L20, L34              href consumed as-is
```

Same class as §8.4 and slightly sharper: this path hard-codes `mode: "walk"`, so the
shrine's stored coordinate is emitted as a **walking** destination. A ritual-center
anchor inside a precinct, or a `P3` mountain site, is precisely the input for which
walking navigation degrades.

`GoogleMapRouteLink` itself is not a producer — it receives `href` as a prop and
applies only analytics plus an `https:`-only protocol guard (L47-55, which renders an
unavailable notice for any other scheme). The coordinate semantics are fixed upstream
at `page.tsx` L290-298.

```text
CLASSIFICATION = NEEDS_NAVIGATION_ANCHOR_SPLIT
```

### 8.6 Consumer classification summary

```text
SEMANTICALLY_COMPATIBLE       = 2  (map display, compass direction)
NEEDS_NAVIGATION_ANCHOR_SPLIT = 2  (route guidance, Shrine detail map link)
INDETERMINATE                 = 1  (distance)
```

The two `NEEDS_NAVIGATION_ANCHOR_SPLIT` consumers share one upstream contract
(`destinationContract.ts` / `gmapsDirUrl()`), so a navigation-anchor split has a single
insertion point on the web side rather than five. That is a cost observation, not a
recommendation.

This matches the proposal's own sentence: "Navigation destinations are a separate
concern and must not silently redefine the Canonical Shrine Anchor." The repository
currently has no field in which that separate concern could live.

```text
NAVIGATION_ANCHOR_FIELD_EXISTS = NO
```

## 9. Migration Decision Gate

Four gates are set out below with the evidence bearing on each.

**Provenance note:** the labels and content of gates A–D below were derived by this
audit from the evidence in §5–§8. They are not quoted from an external specification.
If the Mother Ship holds a canonical A–D formulation, replace this section with it
before any gate is selected; the evidence in §5–§8 is independent of how the gates
are labelled.

### Gate A — `NO_CHANGE`

Keep `Shrine.latitude / longitude = Visitor / Navigation Anchor`. Record the Canonical
Shrine Anchor as a recognised but unmodeled concept.

```text
FOR      : 0 downstream consumers break; 8 PASS records keep their evidentiary basis;
           5 Production rows and 5 Seed rows keep a meaning matching their adoption record
AGAINST  : both open HOLDs (太宰府天満宮, 鶴岡八幡宮) stay blocked on exactly the
           semantic question the proposal answers; §6.6 shows 7/10 records already had
           to name and set aside a ritual center, so the concept is being encountered
           repeatedly without a home
COST     : 0 rows rewritten, 0 code changes
```

### Gate B — `REDEFINE_IN_PLACE`

Adopt the Canonical Shrine Anchor as the meaning of `Shrine.latitude / longitude`.
Re-adjudicate, then remediate Production and Seed. Navigation consumers keep reading
the same field.

```text
FOR      : single field, no schema change; both HOLDs become resolvable in principle
AGAINST  : 2 downstream consumers (§8.4, §8.5) would emit a ritual-center coordinate
           as a walking navigation destination, which the proposal's own closing
           sentence warns against; 1 consumer (§8.2) is INDETERMINATE
COST     : 8 PASS records re-adjudicated; 5 Production rows + 5 Seed rows rewritten;
           the 103 unadjudicated rows (pk=70 among them) inherit a claim no audit
           has made; blocked by the §6.7 source-class question
```

### Gate C — `DUAL_ANCHOR_SPLIT`

Introduce a separate navigation-anchor field. `Shrine.latitude / longitude` becomes the
Canonical Shrine Anchor; route guidance and the detail map link read the new field.

```text
FOR      : the only gate that satisfies "Navigation destinations are a separate concern"
           without degrading navigation; §8.6 shows a single web-side insertion point
AGAINST  : schema change on a model whose write paths are already recorded as carrying
           active debt (docs/audit/location-ownership-bootstrap-parity.md:
           ROOT_CAUSE = DUAL_WRITE_PATH_WITH_ASYMMETRIC_DERIVATION); adding a second
           coordinate pair to a model that already mis-synchronises one (6/6 STALE
           location rows) increases the surface of the existing defect
COST     : schema + migration + serializer + 2 web consumers + backfill for 113 rows;
           every row needs two anchors adjudicated instead of one
```

### Gate D — `DEFER_PENDING_EVIDENCE_FEASIBILITY`

Keep the proposal at `PROPOSED`. First establish, on a bounded sample, whether a `P1`–`P4`
ritual center is determinable and traceable under the proposal's own evidence rules.

```text
FOR      : §5.1 (PRESERVED = 0) and §6.7 (10/10 records rest on the excluded source
           class) mean no evidence currently shows the proposal is satisfiable at scale;
           §6.7 Reading 2, if correct, would push most rows to P5 indefinitely
AGAINST  : both HOLDs stay open for the duration; the ritual-center question keeps
           recurring in new audits without a rule
COST     : audit-only; 0 rows rewritten
```

```text
GATE_SELECTED = NONE
```

This audit selects no gate. Selection is a Mother Ship decision.

## 10. Required Statements

```text
1. No existing PASS is invalidated by this audit.
   All eight Batch 01 PASS records retain POSITION_STATUS = PASS.

2. No existing HOLD is resolved by this audit.
   太宰府天満宮 and 鶴岡八幡宮 retain POSITION_STATUS = HOLD_POSITION_REVIEW.

3. No Production and no Base Seed change is made or proposed by this audit.
   Production write = NONE. Base Seed write = NONE. Candidate Master write = NONE.

4. The proposed P1–P5 Canonical Shrine Anchor Contract remains PROPOSED.
   It is not adopted, not partially adopted, and not scheduled.

5. docs/knowledge/shrine-position-contract.md remains the authoritative contract.
   Shrine.latitude / Shrine.longitude = Visitor / Navigation Anchor remains ACTIVE.
```

## 11. Open Questions

```text
A-1  Does "a generic map-provider POI" exclude the source class, or only its automatic
     adoption without ritual-center labelling? (§6.7)  -> OPEN

A-2  Does proposed P3 intentionally reverse the active Contract's exclusion of
     山域・御神体・境内全体のcentroid, or is a narrower reading intended? (§2.3)  -> OPEN

A-3  Is the rendered distanceM figure a navigation promise or a proximity indicator?
     (§8.2)  -> OPEN

A-4  Under P1/P4, which internal ritual site is primary for 宇佐神宮 (上宮 / 下宮) and
     for 鶴岡八幡宮 (本宮・上宮 / 若宮・下宮)?  -> OPEN

A-5  If a gate other than A is selected, what becomes of the 103 unadjudicated
     Production rows, pk=70 among them? (§7.5)  -> OPEN

A-6  Is a ritual center determinable and traceable, under the proposal's own evidence
     rules, for a bounded sample? (§9 Gate D)  -> NOT_TESTED
```

## 12. STOP

```text
IMPACT_ASSESSMENT        = COMPLETE
READJUDICATION           = NOT_PERFORMED
CONTRACT_MIGRATION       = NOT_PERFORMED
COORDINATE_REMEDIATION   = NOT_PERFORMED
GATE_SELECTED            = NONE
ACTIVE_CONTRACT          = UNCHANGED
```

Next action requires a Mother Ship decision on §9 and on the open questions in §11.
