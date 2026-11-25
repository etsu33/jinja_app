# Canonical Shrine Anchor — Multiple Ritual Center Audit

## Status

- Status: `ASSESSMENT_ONLY`
- Recorded at: `2026-09-23`
- Open question: `A-4` from `docs/audit/canonical-shrine-anchor-contract-impact.md`
- Subject: selection rule when a Shrine contains multiple principal ritual sites
- Active Position Contract: `docs/knowledge/shrine-position-contract.md`
- Orientation Evidence Contract: `docs/knowledge/shrine-orientation-evidence-contract.md`
- Canonical Shrine Anchor Contract state: `PROPOSED`
- Production write: `NONE`
- Base Seed write: `NONE`
- Position status change: `NONE`
- Migration Gate selection: `NONE`

This audit does not adopt the proposed Canonical Shrine Anchor Contract and does not
change `Shrine.latitude / Shrine.longitude = Visitor / Navigation Anchor`.

---

## 1. Question

The open question is:

```text
A-4

Under P1/P4, which internal ritual site is primary for:

- 宇佐神宮: 上宮 / 下宮
- 鶴岡八幡宮: 本宮・上宮 / 若宮・下宮
```

The proposed Canonical Shrine Anchor priority is:

```text
P1  identified Honden / Shoden / Hongu functioning as primary ritual center
P2  principal ritual complex or main sanctuary area
P3  confirmed non-building ritual center
P4  multiple principal ritual sites -> adopt only with an authoritative primary
    ritual center or explicit canonical relationship
P5  ritual center undeterminable or not geographically traceable
    -> HOLD_POSITION_REVIEW
```

This audit tests whether P4 can be applied deterministically without selecting a site
from visual layout, naming order, popularity, or intuition.

---

## 2. Decision Principle Under Test

For a Shrine with multiple important ritual sites, selection must proceed in this
order:

```text
1. Identify the actual ritual subjects.
2. Search authoritative evidence for an explicit hierarchy or canonical relationship.
3. Separate ritual completeness from canonical ownership.
4. If one ritual complex is explicitly primary, assign semantic ownership to that
   complex.
5. If the primary complex itself contains multiple co-principal sanctuaries, do not
   arbitrarily collapse them to one building.
6. Georeferencing a multi-building primary complex is a separate coordinate-selection
   problem.
7. If no authoritative hierarchy / canonical relationship exists, do not choose.
```

The rule intentionally distinguishes:

```text
PRIMARY RITUAL COMPLEX
!=
SINGLE PRIMARY BUILDING
!=
FINAL CANONICAL COORDINATE
```

---

## 3. Source Authority

This audit follows the ACTIVE Orientation Evidence Contract's domain-specific
authority rule.

### Shrine hierarchy / ritual role

Preferred evidence:

```text
- Shrine official material
- public / municipal material explicitly describing shrine ritual hierarchy
- Cultural Affairs material where it establishes structural or historical relation
```

### Prohibited substitutes

The following are not sufficient to establish ritual primacy by themselves:

```text
- map pin position
- highest elevation
- geometric center
- first item in a map or list
- oldest building alone
- National Treasure / Important Cultural Property status alone
- visitor traffic
- "most famous" building
- one deity being popularly treated as more important
```

---

## 4. Case A — 宇佐神宮

### 4.1 Candidate ritual sites

At the level relevant to A-4:

```text
Candidate A = 上宮
Candidate B = 下宮
```

Within 上宮:

```text
一之御殿
二之御殿
三之御殿
```

are all principal Honden subjects that must not be silently collapsed.

### 4.2 Authoritative evidence — 上宮

宇佐神宮公式 identifies the Shrine's three enshrined deities by
一之御殿 / 二之御殿 / 三之御殿 and explains the successive establishment of the three
Honden at the present site.

Source:

```text
Owner: 宇佐神宮
Title: 由緒
URL: https://www.usajinguu.com/lineage/
```

The official account states that the first sanctuary for 八幡大神 at the current site
was established in 725, followed by 二之御殿 and 三之御殿, and describes the three
together as the Shrine's Honden / central sacred architecture.

宇佐市's official tourism / cultural material is more explicit about the internal
ritual structure:

```text
Owner: 宇佐市
Title: 上宮
URL:
https://www.city.usa.oita.jp/tourist/touristspot/touristspot2/touristspot3/usachiku/syuyumap/kami/12884.html
```

It records:

- 上宮 enshrines 宇佐神宮's three principal deities in three 御殿;
- 一之御殿 at 小椋山 was the 725 foundation point of 宇佐神宮;
- the three 御殿 form the present 上宮 ritual structure.

宇佐市's annual-festival material provides an additional hierarchy signal:

```text
Owner: 宇佐市
Title: 例祭
URL:
https://www.city.usa.oita.jp/tourist/touristspot/touristspot2/touristspot3/usachiku/sinbutusyugou/12871.html
```

The Shrine's most important annual festival proceeds to 上宮, where rites are
performed at each of the three 御殿. The 下宮 / 若宮神社 / 春宮神社 festivals are
performed on the preceding day.

This supports 上宮 as the principal ritual complex without selecting one of the
three Honden as the sole internal ritual center.

### 4.3 Authoritative evidence — 下宮

宇佐市 records:

```text
Owner: 宇佐市
Title: 下宮
URL:
https://www.city.usa.oita.jp/sougo/soshiki/14/toshikeikaku/keikan/matidukuri/usachiku/syuyumap/kami/12750.html
```

The 下宮:

- enshrines the same three deities as 上宮;
- is one of the two major sacred precincts representing 宇佐神宮;
- is associated with the saying `下宮参らにゃ片参り`;
- has an independent historical ritual role;
- is currently used principally for daily rites by priests.

The same source distinguishes historical ritual roles:

```text
上宮 = 国家の神としての崇敬
下宮 = 民衆の神としての崇敬
```

The evidence therefore establishes that 下宮 is ritually important and necessary to
the complete traditional visit.

It does **not** establish that 上宮 and 下宮 are semantically interchangeable for
canonical-anchor ownership.

### 4.4 Ritual completeness vs canonical ownership

The following inference is prohibited:

```text
"下宮参らにゃ片参り"
therefore
上宮 and 下宮 must be equal canonical coordinate owners
```

The saying establishes a complete-worship relation.

It does not override the independent evidence that:

- the Shrine's founding Honden sequence is the 上宮 complex;
- the three principal deities are enshrined there in the principal Honden;
- the major annual rite proceeds to the three 上宮 Honden.

Therefore:

```text
USA_JINGU_A4_PRIMARY_COMPLEX
= 上宮
```

### 4.5 Internal 上宮 selection

The evidence does **not** justify selecting:

```text
一之御殿
or
二之御殿
or
三之御殿
```

as the sole canonical ritual point.

Reasons:

- all three principal deities are ritually represented;
- official / public material directs worship to all three 御殿;
- the Orientation Pilot documented the three-Honden ritual structure;
- no accepted source in this audit states that one of the three alone owns the
  Shrine's canonical ritual center.

Therefore:

```text
USA_JINGU_PRIMARY_COMPLEX = CONFIRMED: 上宮

USA_JINGU_SINGLE_PRIMARY_HONDEN
= NOT_DETERMINED
```

Under the proposed P1–P5 model, this is a **P2-shaped case**, not a justification for
forcing P1 onto one Honden.

### 4.6 A-4 result — 宇佐神宮

```text
UPPER_VS_LOWER_PRIMARY_RELATION = RESOLVED
PRIMARY_RITUAL_COMPLEX          = 上宮

SINGLE_HONDEN_OWNER             = NOT_DETERMINED
FINAL_CANONICAL_COORDINATE      = NOT_ADJUDICATED
```

A-4 resolves the semantic owner at the complex level.

It does not yet resolve the coordinate point inside that complex.

---

## 5. Case B — 鶴岡八幡宮

### 5.1 Candidate ritual sites

```text
Candidate A = 本宮（上宮）
Candidate B = 若宮（下宮）
```

### 5.2 Shrine-official evidence — 本宮

鶴岡八幡宮 official precinct guidance states:

```text
Owner: 鶴岡八幡宮
Title: 境内巡り
URL: https://www.hachimangu.or.jp/sightseeing/keidai/
```

For 本宮（上宮）, the official page explicitly describes it as:

```text
当宮の中心となる御社殿
```

and identifies its principal enshrined deities.

This is direct authoritative hierarchy evidence.

### 5.3 Shrine-official evidence — 若宮

The same official precinct guidance identifies 若宮（下宮） separately.

The Shrine's official festival page further states:

```text
Owner: 鶴岡八幡宮
Title: 祭り — 若宮例祭
URL: https://www.hachimangu.or.jp/matsuri/
```

若宮 is the Shrine's only `摂社`, and the official explanation defines it as an
associated sanctuary ranked next to the main Shrine.

This directly distinguishes:

```text
本宮 = central / main sanctuary
若宮 = sessha, next in relation to the main shrine
```

### 5.4 Historical corroboration

The official treasure page explains the formation of the current upper / lower
arrangement:

```text
Owner: 鶴岡八幡宮
Title: 宝物 — 上下両宮
URL: https://www.hachimangu.or.jp/sightseeing/homotsu/
```

It records the establishment of the current 上宮（本宮） and 下宮（若宮） arrangement
after the 1191 fire.

Cultural Affairs independently recognizes 鶴岡八幡宮摂社若宮 as a distinct
Important Cultural Property:

```text
Owner: 文化庁
Title: 鶴岡八幡宮摂社若宮
URL: https://kunishitei.bunka.go.jp/heritage/detail/102/606
```

This corroborates the separate architectural / institutional identity of 若宮.

### 5.5 A-4 result — 鶴岡八幡宮

The hierarchy is explicit.

```text
TSURUGAOKA_A4_PRIMARY_SITE
= 本宮（上宮）

WAKAMIYA_ROLE
= 摂社 / 下宮

PRIMARY_RELATION
= CONFIRMED
```

No geometric inference or popularity judgment is required.

Under the proposed P1–P5 model, 本宮（上宮） satisfies the semantic requirement for
an identified primary Honden / Hongu candidate.

The final coordinate is not adopted by this audit.

---

## 6. Cross-Case Rule

The two cases show that "multiple ritual sites" must be split into at least two
different structures.

### Pattern 1 — Explicit main/subordinate hierarchy

Example:

```text
鶴岡八幡宮
本宮（上宮） = official center
若宮（下宮） = 摂社
```

Rule:

```text
If an authoritative source explicitly identifies one sanctuary as
main / central / 本宮 / 本社 and another as subordinate / 摂社,
the primary semantic owner may be selected from that hierarchy.
```

### Pattern 2 — Multiple major ritual precincts, one principal complex

Example:

```text
宇佐神宮
上宮 = principal Honden complex / foundation / major annual rite
下宮 = ritually essential complementary precinct
```

Rule:

```text
A complementary ritual obligation does not by itself create equal canonical
ownership when authoritative evidence establishes a principal ritual complex.
```

### Pattern 3 — Multiple co-principal sanctuaries inside the selected complex

Example:

```text
宇佐神宮 上宮
一之御殿
二之御殿
三之御殿
```

Rule:

```text
If the selected primary ritual complex contains multiple co-principal sanctuaries
and no authoritative source makes one the sole owner, do not select one arbitrarily.
Treat the complex as the semantic owner.
```

The conversion from that semantic owner to a single latitude / longitude is a separate
geospatial-adjudication question.

---

## 7. Proposed Deterministic Selection Rule

This audit supports the following rule for a future Canonical Shrine Anchor Contract.

```text
M1  Enumerate all plausible principal ritual subjects.

M2  Require authoritative evidence for hierarchy / canonical relationship.

M3  If one subject is explicitly main / central / Hongu / Honsha and another is
    subordinate / Sessha / complementary, adopt the main subject as semantic owner.

M4  Do not treat "complete worship requires both" as proof of equal anchor ownership.

M5  If the semantic owner is a ritual complex containing multiple co-principal
    sanctuaries, stop at the complex level unless authoritative evidence selects a
    single sanctuary.

M6  Do not derive a point from first-in-order, central placement, oldest construction,
    highest elevation, cultural-property rank, map-provider POI, or visitor popularity.

M7  If authoritative evidence cannot establish a primary subject or canonical
    relationship among multiple principal candidates, the proposed position workflow
    must stop rather than choose.
```

If the future Position Contract retains the proposed P5 semantics, M7 would terminate
as:

```text
HOLD_POSITION_REVIEW
```

This audit does not activate that future rule.

---

## 8. Interaction with Orientation Evidence Contract

The ACTIVE Orientation Evidence Contract remains complementary.

It can establish:

```text
- which structure faces which direction
- which worship relation exists
- which symbolic target is documented
```

It does not automatically establish:

```text
- which ritual subject owns the Canonical Shrine Anchor
- which exact point inside a multi-building complex becomes latitude / longitude
```

Therefore:

```text
RITUAL_AXIS confirmed
!=
CANONICAL_ANCHOR_OWNER automatically confirmed
```

A-4 requires hierarchy / canonical-role evidence in addition to orientation evidence.

---

## 9. A-4 Resolution

### 宇佐神宮

```text
PRIMARY_RITUAL_COMPLEX = 上宮
UPPER_VS_LOWER         = RESOLVED
SINGLE_PRIMARY_HONDEN  = NOT_DETERMINED
COORDINATE             = NOT_ADJUDICATED
```

### 鶴岡八幡宮

```text
PRIMARY_RITUAL_SITE = 本宮（上宮）
HONGU_VS_WAKAMIYA   = RESOLVED
COORDINATE          = NOT_ADJUDICATED
```

### Open-question result

```text
A-4_MULTIPLE_RITUAL_CENTER_SELECTION_RULE
= RESOLVED_AT_SEMANTIC_OWNER_LEVEL

A-4_FINAL_COORDINATE_SELECTION
= OUT_OF_SCOPE / NOT_ADJUDICATED
```

This is sufficient to remove the ambiguity between:

```text
宇佐神宮: 上宮 vs 下宮
鶴岡八幡宮: 本宮（上宮） vs 若宮（下宮）
```

It is **not** sufficient to select a single coordinate for 宇佐神宮 上宮.

That remaining question belongs to the georeferencing / traceability audit currently
represented by A-6.

---

## 10. Migration Gate Impact

This audit does not select A / B / C / D.

It changes the evidence state of the Gate as follows:

```text
A-4 = RESOLVED_AT_SEMANTIC_OWNER_LEVEL

宇佐神宮
  semantic owner = 上宮
  single point   = unresolved

鶴岡八幡宮
  semantic owner = 本宮（上宮）
  single point   = not adjudicated here
```

The result reduces semantic ambiguity for a future Canonical Shrine Anchor migration,
but does not resolve schema, navigation-anchor separation, distance semantics, or
geographic traceability.

---

## 11. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No existing PASS / HOLD_POSITION_REVIEW status was changed.
4. The ACTIVE Position Contract remains unchanged.
5. The proposed Canonical Shrine Anchor Contract remains PROPOSED.
6. No Canonical coordinate was adopted.
7. "Complete worship requires both sites" was not treated as automatic equal
   canonical ownership.
8. No one of 宇佐神宮's three 上宮 Honden was arbitrarily selected.
9. No Migration Gate option was selected.
```
