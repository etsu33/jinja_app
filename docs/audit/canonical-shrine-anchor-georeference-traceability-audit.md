# Canonical Shrine Anchor — Georeference Traceability Audit

## Status

- Status: `ASSESSMENT_ONLY`
- Recorded at: `2026-09-23`
- Open question: `A-6` from `docs/audit/canonical-shrine-anchor-contract-impact.md`
- Subject: whether a ritual-center semantic owner can be converted reproducibly into one latitude / longitude pair
- Active Position Contract: `docs/knowledge/shrine-position-contract.md`
- Orientation Evidence Contract: `docs/knowledge/shrine-orientation-evidence-contract.md`
- Multiple Ritual Center Audit: `docs/audit/canonical-shrine-anchor-multi-ritual-center-audit.md`
- Canonical Shrine Anchor Contract state: `PROPOSED`
- Production write: `NONE`
- Base Seed write: `NONE`
- Position status change: `NONE`
- Migration Gate selection: `NONE`

This audit does not adopt the proposed Canonical Shrine Anchor Contract and does not
change `Shrine.latitude / Shrine.longitude = Visitor / Navigation Anchor`.

---

## 1. Question

A-6 asks:

```text
For how many shrines can authoritative evidence identify a specific georeferenced
point as the ritual center, at a level the proposal's evidence requirements accept?
```

The key distinction is:

```text
SEMANTIC OWNER
!=
GEOREFERENCED OBJECT
!=
SINGLE CANONICAL POINT
```

A shrine can have a clearly established ritual owner and still lack a non-arbitrary
single point if that owner is a multi-building ritual complex.

---

## 2. Audit Sample

Five shrines were selected to cover the structures already surfaced by the Orientation
Pilot and A-4 audit.

```text
1. 日光東照宮
2. 伏見稲荷大社
3. 宇佐神宮
4. 春日大社
5. 鶴岡八幡宮
```

The sample intentionally includes:

```text
- one connected principal shrine complex
- one single Honden containing multiple enshrined seats
- two multi-building co-principal Honden complexes
- one explicit main shrine complex with authoritative hierarchy
```

No coordinate is written to Production or Base Seed.

---

## 3. Acceptance Rule

A single Canonical Shrine Anchor point is considered reproducibly traceable only when
all of the following are true.

```text
G1  Authoritative evidence identifies the ritual semantic owner.

G2  The geospatial source can be matched to that same subject, not merely to the
    overall Shrine POI.

G3  The source exposes a traceable numeric coordinate or object-level geometry from
    which the source itself provides a representative point.

G4  No co-principal ritual subject is silently discarded.

G5  No first-in-order / center / oldest / most famous / highest / map-pin rule is
    invented to select among co-principal subjects.

G6  A generic Shrine POI does not become a ritual-center coordinate merely because it
    lies inside the precinct.
```

The proposed contract already allows a map-provider / corroboration coordinate to be
used for traceability **after** authoritative evidence establishes the ritual subject.
Therefore semantic authority and coordinate traceability may come from different
sources, provided the subject identity is exact and explainable.

---

## 4. Result Classes

```text
SINGLE_POINT_REPRODUCIBLE
  The ritual semantic owner is established and one subject-matched point is
  traceable without discarding a co-principal ritual subject.

COMPLEX_TRACEABLE_POINT_POLICY_MISSING
  The ritual complex and its component locations are traceable, but no accepted rule
  makes one component or derived point the single Canonical owner.

NOT_TRACEABLE
  The semantic owner or its geographic identity cannot be traced to an accepted
  geospatial subject.

HOLD_GEOREFERENCE_REVIEW
  Accepted geospatial evidence materially conflicts after subject matching.
```

Missing point policy is not a geospatial-source conflict.

---

## 5. Case 1 — 日光東照宮

### 5.1 Ritual subject

日光市 official cultural-property material identifies:

```text
Honden
= Shrine building where Tosho Daigongen is enshrined

Ishinoma
= connection between Honden and Haiden

Haiden
= worship building
```

Source:

```text
https://www.city.nikko.lg.jp/soshiki/10/1041/1_1/2/6/1395.html
```

文化庁 registers the connected unit as:

```text
東照宮 本殿、石の間及び拝殿
員数 = 1棟
```

Source:

```text
https://kunishitei.bunka.go.jp/heritage/detail/102/269
```

This supports the principal connected shrine unit as one identifiable geospatial
subject while preserving the internal ritual role of the Honden.

### 5.2 Georeference

奈良文化財研究所 Heritage Map exposes the Cultural Affairs-derived record:

```text
RecNo = 98002610
Subject = 東照宮_本殿、石の間及び拝殿
Latitude  = 36.75808
Longitude = 139.5987
Source lineage = 文化庁 国指定文化財等データベース
                 (2021-01-29 snapshot)
```

Source:

```text
https://heritagemap.nabunken.go.jp/statistic/98002610-東照宮_本殿、石の間及び拝殿.html
```

Independent object-level corroboration also exists for the same named principal
structure in OpenStreetMap-based data.

### 5.3 Result

```text
NIKKO_TOSHOGU
= SINGLE_POINT_REPRODUCIBLE
```

This result does not claim that the coordinate is a navigation destination.

---

## 6. Case 2 — 伏見稲荷大社

### 6.1 Ritual subject

伏見稲荷大社 official material states that the five enshrined seats are all housed
in one Honden.

Source:

```text
https://inari.jp/about/saijin/
```

The official Honden page and precinct map independently identify the same building.

```text
https://inari.jp/sp/map/spot_03/
https://inari.jp/sp/map/
```

文化庁 separately registers:

```text
伏見稲荷大社
棟名 = 本殿
員数 = 1棟
```

Source:

```text
https://kunishitei.bunka.go.jp/heritage/detail/102/1925
```

The five ritual seats therefore do not create five competing buildings for A-6.

### 6.2 Georeference

An object-level OpenStreetMap feature exists for the exact subject:

```text
Subject = 伏見稲荷大社 本殿
OSM way = 1385045207
Latitude  = 34.96713
Longitude = 135.77329
```

Traceability surface:

```text
https://mapcarta.com/W1385045207
```

This coordinate is used only as geospatial traceability after the Honden identity and
ritual role are established by shrine-official / Cultural Affairs evidence.

It is not treated as authority for ritual meaning.

### 6.3 Result

```text
FUSHIMI_INARI_TAISHA
= SINGLE_POINT_REPRODUCIBLE
```

The result depends on strict subject matching to `本殿`, not the generic Fushimi
Inari Shrine POI.

---

## 7. Case 3 — 宇佐神宮

### 7.1 Ritual owner

A-4 resolved:

```text
PRIMARY_RITUAL_COMPLEX = 上宮
SINGLE_PRIMARY_HONDEN  = NOT_DETERMINED
```

Within 上宮:

```text
一之御殿
二之御殿
三之御殿
```

are co-principal ritual subjects.

文化庁 confirms that the three Honden are distinct structures arranged east-west and
that the divine seats are located within the Honden.

Source example:

```text
https://kunishitei.bunka.go.jp/bsys/maindetails/102/3600
```

### 7.2 Georeference supply exists

The problem is **not** that the ritual complex is geographically untraceable.

奈良文化財研究所 Heritage Map exposes a Cultural Affairs-derived object record, for
example:

```text
Subject = 宇佐神宮本殿
棟名 = 第三殿
Latitude  = 33.52349
Longitude = 131.3773
```

Source:

```text
https://heritagemap.nabunken.go.jp/statistic/98032356-宇佐神宮本殿.html
```

This proves that component-level georeference data exists.

### 7.3 Why one point cannot yet be selected

A-4 explicitly prohibits selecting one of the three Honden merely because it is:

```text
- first in numbering
- central
- oldest
- easiest to map
- represented by an available point
```

No accepted rule currently says:

```text
use 第一殿
use 第二殿
use 第三殿
use centroid of the three
use polygon center of 上宮
```

as the Canonical Shrine Anchor.

Therefore, using the available 第三殿 coordinate would solve a data-supply problem by
silently creating a semantic rule.

### 7.4 Result

```text
USA_JINGU
= COMPLEX_TRACEABLE_POINT_POLICY_MISSING
```

The blocker is representative-point semantics, not coordinate availability.

---

## 8. Case 4 — 春日大社

### 8.1 Ritual owner

春日大社 official material identifies the Main Sanctuary as four Honden:

```text
第一殿 = 武甕槌命
第二殿 = 経津主命
第三殿 = 天児屋根命
第四殿 = 比売神
```

Source:

```text
https://www.kasugataisha.or.jp/guidance/keidai-map3/modal-01/
```

文化庁 registers the Honden separately, e.g. 第一殿:

```text
https://kunishitei.bunka.go.jp/heritage/detail/102/2533
```

The ritual center is therefore a multi-building four-Honden sanctuary complex.

### 8.2 Component georeference exists

Object-level geospatial records distinguish the individual Honden.

Example:

```text
First Hall / 春日大社本殿第一殿
OSM way = 1134481290
Latitude  = 34.68158
Longitude = 135.84854
```

Traceability surface:

```text
https://mapcarta.com/W1134481290
```

Equivalent object-level records exist for the other Honden.

### 8.3 Why one point cannot yet be selected

No accepted source in this audit establishes:

```text
第一殿 = sole canonical owner
第二殿 = sole canonical owner
第三殿 = sole canonical owner
第四殿 = sole canonical owner
```

and no ACTIVE rule authorizes:

```text
centroid of four Honden
midpoint of sanctuary row
first-Honden coordinate
official-map icon location
```

as the Canonical Shrine Anchor.

### 8.4 Result

```text
KASUGA_TAISHA
= COMPLEX_TRACEABLE_POINT_POLICY_MISSING
```

Again, this is not a data-supply failure.

---

## 9. Case 5 — 鶴岡八幡宮

### 9.1 Ritual owner

A-4 resolved:

```text
PRIMARY_RITUAL_SITE = 本宮（上宮）
```

鶴岡八幡宮 official material calls 本宮（上宮）:

```text
当宮の中心となる御社殿
```

Source:

```text
https://www.hachimangu.or.jp/sightseeing/keidai/
```

国土交通省's shrine interpretation is stronger still for A-6 semantics:

```text
御本殿 = 鶴岡八幡宮で最も神聖な場所
```

and states that Honden, Heiden and Haiden are integrated under one roof.

Source:

```text
https://www.mlit.go.jp/tagengo-db/R2-01184.html
```

文化庁 registers the same connected unit as one building:

```text
鶴岡八幡宮上宮
棟名 = 本殿、幣殿及び拝殿
員数 = 1棟
```

Source:

```text
https://kunishitei.bunka.go.jp/heritage/detail/102/607
```

### 9.2 Georeference

奈良文化財研究所 Heritage Map exposes:

```text
RecNo = 98007951
Subject = 鶴岡八幡宮上宮
棟名 = 本殿、幣殿及び拝殿
Latitude  = 35.32611
Longitude = 139.5564
Source lineage = 文化庁 国指定文化財等データベース
```

Source:

```text
https://heritagemap.nabunken.go.jp/statistic/98007951-鶴岡八幡宮上宮.html
```

### 9.3 Result

```text
TSURUGAOKA_HACHIMANGU
= SINGLE_POINT_REPRODUCIBLE
```

---

## 10. Pilot Result

```text
SAMPLE = 5

SINGLE_POINT_REPRODUCIBLE
= 3 / 5
= 60.0 %

COMPLEX_TRACEABLE_POINT_POLICY_MISSING
= 2 / 5
= 40.0 %

NOT_TRACEABLE
= 0 / 5
= 0.0 %

HOLD_GEOREFERENCE_REVIEW
= 0 / 5
= 0.0 %
```

Per shrine:

| Shrine | Semantic owner | Geospatial traceability | Single point |
| --- | --- | --- | --- |
| 日光東照宮 | principal connected 御本社 | object-level | `REPRODUCIBLE` |
| 伏見稲荷大社 | single Honden | object-level | `REPRODUCIBLE` |
| 宇佐神宮 | 上宮, three co-principal Honden | component-level | `POINT_POLICY_MISSING` |
| 春日大社 | four-Honden Main Sanctuary | component-level | `POINT_POLICY_MISSING` |
| 鶴岡八幡宮 | 本宮（上宮） connected main shrine | object-level | `REPRODUCIBLE` |

---

## 11. A-6 Resolution

A-6 is no longer `NOT_TESTED`.

The result is:

```text
A-6_GEOREFERENCE_SUPPLY
= AVAILABLE_IN_SAMPLE

A-6_SINGLE_POINT_REPRODUCIBILITY
= PARTIAL

SINGLE_POINT_REPRODUCIBLE = 3 / 5 = 60.0 %

PRIMARY_BLOCKER
= MULTI_BUILDING_REPRESENTATIVE_POINT_POLICY
```

The original supply hypothesis is therefore refined.

The observed problem is **not primarily that authoritative ritual evidence or
geospatial data is unavailable**.

The observed problem is:

```text
For a P2 multi-building ritual complex, the current proposal does not define how the
semantic owner becomes one canonical latitude / longitude pair without discarding a
co-principal sanctuary or inventing a geometric representative-point rule.
```

---

## 12. Deterministic Rule Supported by A-6

This audit supports only the following bounded rule.

```text
GEO-1
If authoritative evidence identifies one single ritual building or one connected
registered principal shrine unit, and subject-matched georeference data exists,
a single Canonical point can be traceable.

GEO-2
If authoritative evidence identifies a multi-building ritual complex with
co-principal sanctuaries, component coordinates do not authorize selecting one
component as the Canonical point.

GEO-3
Do not derive centroid / midpoint / first-building / central-building / oldest-building
as Canonical point unless a future Contract explicitly adopts that representative-point
semantics.

GEO-4
A generic Shrine POI is not a substitute for a subject-matched ritual-center point.

GEO-5
Coordinate-source availability does not resolve semantic ownership.
```

No centroid or representative-point algorithm is adopted by this audit.

---

## 13. Migration Gate Impact

A-6 materially changes the Migration Gate evidence.

### Gate A — KEEP_CURRENT_CONTRACT

No new implementation blocker is introduced.

The active Visitor / Navigation Anchor semantics remain internally consistent.

A-6 neither strengthens nor weakens the current coordinate's navigation role.

### Gate B — ADOPT_CANONICAL_SHRINE_ANCHOR_AND_READJUDICATE

A-6 shows that this Gate is **not yet fully specified** for a single lat/lng model.

```text
single-unit cases = reproducibly traceable
multi-building P2 cases = representative-point rule missing
```

Therefore re-adjudication under B cannot be deterministic for every observed shrine
until the P2 point-representation rule is defined.

This is separate from the already-recorded navigation regression.

### Gate C — SPLIT_CANONICAL_AND_NAVIGATION_ANCHORS

A-6 confirms that separating Navigation Anchor solves the route-destination semantic
collision.

It does **not** solve the new Canonical field's internal representation problem.

If the Canonical Anchor remains one latitude / longitude pair, the same P2
representative-point question remains for 宇佐神宮 / 春日大社-like cases.

Therefore:

```text
NAVIGATION_SPLIT
!=
CANONICAL_POINT_POLICY
```

### Gate D — OTHER / INDETERMINATE

The previous "run a bounded evidence-availability sample" example has now been
performed.

The remaining unresolved policy is narrower:

```text
How should a multi-building P2 semantic owner be represented?

- one source-provided representative point?
- one explicitly defined deterministic derived point?
- a geometry / set of ritual subjects rather than a single point?
- another Mother Ship-defined representation?
```

This audit does not choose among those options.

---

## 14. Gate Return

```text
A-4 = RESOLVED_AT_SEMANTIC_OWNER_LEVEL

A-6_GEOREFERENCE_SUPPLY
= AVAILABLE_IN_SAMPLE

A-6_SINGLE_POINT_REPRODUCIBILITY
= PARTIAL (3 / 5)

NEW_OPEN_QUESTION
= P2_MULTI_BUILDING_REPRESENTATIVE_POINT_POLICY

MIGRATION_GATE_READY_FOR_SELECTION
= NO

GATE_SELECTED
= NONE
```

The Gate is closer to decision, but B and C are not yet deterministic for the
multi-building P2 class.

---

## 15. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No existing PASS / HOLD_POSITION_REVIEW status was changed.
4. The ACTIVE Position Contract remains unchanged.
5. The proposed Canonical Shrine Anchor Contract remains PROPOSED.
6. No Canonical coordinate was adopted.
7. No centroid / midpoint / first-building rule was introduced.
8. Component coordinate availability was not treated as permission to discard a
   co-principal ritual subject.
9. No Migration Gate option was selected.
```
