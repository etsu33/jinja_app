# Shrine Orientation Evidence Pilot — 5 Shrines

## Status

- Status: `EXECUTED_VERIFIED_EVIDENCE`
- Recorded at: `2026-09-23`
- Pilot Shrines: 5
- Layer decisions: 15
- Verified Mother Ship evidence packet: `APPLIED`
- Production write: `NONE`
- Base Seed write: `NONE`
- Shrine model change: `NONE`
- Position Contract change: `NONE`
- Recommendation / Compass logic change: `NONE`
- Orientation Evidence Contract created: `NO`

This document is an audit result, not a Contract.
`docs/knowledge/shrine-position-contract.md` remains authoritative and unchanged.

---

## 0. Executive Result

The pilot tested whether shrine orientation can be collected reproducibly from
published cultural-property, shrine-official, municipal, and scholarly evidence
without inferring unsupported meaning from geometry.

Five shrines were evaluated across three independent layers:

```text
A. PHYSICAL_ORIENTATION
B. RITUAL_AXIS
C. SYMBOLIC_ORIENTATION
```

Final normalized result:

```text
TOTAL_CELLS = 15

CONFIRMED               = 11 / 15 = 73.3 %
NOT_DETERMINED          =  4 / 15 = 26.7 %
HOLD_ORIENTATION_REVIEW =  0 / 15 =  0.0 %
```

Per layer:

```text
PHYSICAL_ORIENTATION
  CONFIRMED      = 4 / 5 =  80.0 %
  NOT_DETERMINED = 1 / 5 =  20.0 %
  HOLD           = 0 / 5 =   0.0 %

RITUAL_AXIS
  CONFIRMED      = 5 / 5 = 100.0 %
  NOT_DETERMINED = 0 / 5 =   0.0 %
  HOLD           = 0 / 5 =   0.0 %

SYMBOLIC_ORIENTATION
  CONFIRMED      = 2 / 5 =  40.0 %
  NOT_DETERMINED = 3 / 5 =  60.0 %
  HOLD           = 0 / 5 =   0.0 %
```

Pilot decision:

```text
ORIENTATION_EVIDENCE_PIPELINE = VIABLE
```

This does **not** mean every shrine will yield every layer.

It means the pilot established a reproducible process that can:

1. confirm physical orientation where accepted evidence supports it;
2. identify ritual axes from explicit worship / ritual documentation;
3. confirm symbolic orientation only when documentary evidence states the target or
   ritual relation;
4. return `NOT_DETERMINED` instead of guessing where evidence is insufficient; and
5. reserve `HOLD_ORIENTATION_REVIEW` for actual accepted-source conflicts.

The lower symbolic-orientation acquisition rate is not a pipeline failure.
Correct refusal to infer symbolic intent from geometry is part of the success criteria.

---

## 1. Scope and Non-Goals

### 1.1 Purpose

Test whether orientation evidence can be acquired and classified reproducibly for a
small but structurally diverse shrine sample.

### 1.2 Pilot shrines

```text
1. 伏見稲荷大社
2. 日光東照宮
3. 宇佐神宮
4. 春日大社
5. 建勲神社
```

### 1.3 Non-goals

This pilot does not:

- modify Production;
- modify Base Seed;
- modify the Shrine model;
- change `docs/knowledge/shrine-position-contract.md`;
- change recommendation logic;
- change Compass logic;
- change route logic;
- create the formal Orientation Evidence Contract;
- assign exact degree values where only cardinal prose is supported;
- infer symbolic meaning from map geometry or visual alignment.

---

## 2. Evidence Model

### 2.1 Independent layers

#### A. `PHYSICAL_ORIENTATION`

Question:

> What direction does the relevant shrine building, sanctuary, or explicitly scoped
> shrine complex physically face?

Acceptable evidence includes:

- direct cultural-property prose such as 東面 / 南面;
- official or scholarly architectural documentation;
- measured plans where orientation is explicit and traceable.

Physical direction does **not** prove symbolic intent.

#### B. `RITUAL_AXIS`

Question:

> Does accepted evidence establish a worship / ritual spatial relation between
> documented places or structures?

Examples:

- 拝殿 → 本殿;
- 遥拝所 → sacred target;
- documented worship sequence;
- a gate explicitly described as standing in front of a principal sanctuary.

A physical layout alone does not automatically prove a ritual axis.

#### C. `SYMBOLIC_ORIENTATION`

Question:

> Does accepted documentary evidence explicitly establish an intentional ritual or
> symbolic target?

Examples:

- a documented 遥拝 target;
- an explicit statement that a structure faces a named sacred place;
- an authoritative explanation of an intended symbolic spatial relation.

Geometry alone is not evidence of symbolic meaning.

### 2.2 Governing rule

```text
GEOMETRY PROVES DIRECTION.
DOCUMENTARY EVIDENCE PROVES MEANING.
```

`SYMBOLIC_ORIENTATION` is never derived from `PHYSICAL_ORIENTATION` alone.

### 2.3 Status values

```text
CONFIRMED
  accepted evidence directly supports the normalized cell claim

NOT_DETERMINED
  accepted evidence does not establish the normalized cell claim

HOLD_ORIENTATION_REVIEW
  accepted sources conflict or remain materially ambiguous after review
```

Missing evidence is not `HOLD`.

### 2.4 Evidence strength

```text
E1_AUTHORITATIVE
  shrine official / Cultural Affairs / government / municipal cultural-property source

E2_SCHOLARLY
  university / academic society / specialist architectural or historical research

E3_MEASURED
  official or scholarly measured drawing / plan / GIS-quality spatial evidence

E4_CORROBORATION
  map / aerial imagery / non-semantic spatial corroboration
```

`E4` alone may not establish `RITUAL_AXIS` or `SYMBOLIC_ORIENTATION`.

---

## 3. Source Authority by Domain

The pilot does not use one universal hierarchy for every claim.

Instead, authority is assigned by information domain.

### 3.1 Shrine meaning / worship / ritual target

Preferred:

```text
- shrine official material
- shrine-side authoritative material
- government / municipal documentation explicitly describing worship or ritual function
```

### 3.2 Physical building orientation / arrangement

Preferred:

```text
- Cultural Affairs
- municipal / prefectural cultural-property authority
- repair / measured architectural documentation
- specialist architectural research
```

### 3.3 Historical / symbolic orientation

Preferred:

```text
- explicit shrine-official documentary statement
- cultural-historical source
- scholarly source
```

A documented religious relationship between two places does not by itself establish
that one structure was intentionally oriented toward the other.

---

## 4. Execution Note — Initial Codex Egress Block

The first Codex-side acquisition attempt could not open the candidate evidence hosts.

```text
INITIAL_CODEX_EXECUTION = BLOCKED_BY_EGRESS
```

That execution produced:

```text
PRIMARY_SOURCE_DOCUMENTS_READ = 0
CONFIRMED_CELLS               = 0 / 15
```

This was an environment result, not an evidence-domain result.

The initial run correctly refused to promote search-result snippets, prompt-provided
claims, inferred geometry, or reversed directional relationships into accepted
evidence.

Mother Ship subsequently acquired and verified the source material using accepted
primary / scholarly sources and recorded the evidence in the evidence ledger.

The verified Mother Ship evidence packet supersedes the initial `0 / 15` result for
pilot assessment.

The initial block is retained only as an execution note because its refusal discipline
remains relevant:

```text
CLASSIFICATION_DETERMINISM_HELD = YES
REFUSAL_DISCIPLINE_HELD         = YES
```

---

## 5. Verified Source Inventory

The inventory below lists sources actually used in the verified evidence packet.

### 5.1 日光東照宮

#### Physical orientation

- Owner: 文化庁
- Source: 神社 比較一覧（別添資料3）
- Type: cultural-property / government material
- URL:
  `https://www.bunka.go.jp/seisaku/bunkashingikai/isanbukai/sekaiisanbukai_nittei/2_01/pdf/r1404325_11.pdf`
- Evidence level: `E1_AUTHORITATIVE`
- Supported scope: shrine / principal site orientation
- Supported claim: 日光東照宮 is recorded as `南面、山裾`
- Limitation: does not establish an exact degree value or a symbolic reason for the
  south-facing orientation.

#### Ritual structure

- Owner: 日光市教育委員会事務局 文化財課
- Source: 建造物一覧-東照宮1
- Type: municipal cultural-property material
- URL:
  `https://www.city.nikko.lg.jp/soshiki/10/1041/1_1/2/1/2427.html`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 本殿 is the shrine building for 東照大権現, 石の間 connects 本殿
  and 拝殿, and 拝殿 is the worship building.

#### Architectural corroboration

- Owner: 栃木県
- Source: 東照宮本殿、石の間及び拝殿
- Type: prefectural cultural-property material
- URL:
  `https://bunkazai.pref.tochigi.lg.jp/cultural/%E3%80%90%E6%9D%B1%E7%85%A7%E5%AE%AE%E6%9C%AC%E6%AE%BF%E3%80%81%E7%9F%B3%E3%81%AE%E9%96%93%E5%8F%8A%E3%81%B3%E6%8B%9D%E6%AE%BF%E3%80%91/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 拝殿 and 本殿 are connected by 石の間 as the 権現造 composition.

#### Counter-evidence / directional non-transfer

- Owner: 国土交通省
- Source: 日光山輪王寺 本殿、拝殿［大猷院内］
- Type: government public interpretation
- URL:
  `https://www.mlit.go.jp/tagengo-db/H30-00288.html`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 大猷院 is documented as oriented toward 東照宮.
- Limitation: this relation may not be reversed into a claim that 東照宮 is
  symbolically oriented toward 江戸 or 大猷院.

### 5.2 伏見稲荷大社

#### Precinct physical orientation

- Owner: 文化庁
- Source: 伏見稲荷大社
- Type: Cultural Affairs material
- URL:
  `https://kunishitei.bunka.go.jp/heritage/detail/102/00004715`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: the shrine precinct is on the west foot of 稲荷山 and is composed
  with west as its front.
- Limitation: precinct-facing direction is not automatically Honden-facing direction.

#### Honden record

- Owner: 文化庁
- Source: 伏見稲荷大社本殿
- Type: Cultural Affairs material
- URL:
  `https://kunishitei.bunka.go.jp/heritage/detail/102/1925`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: architectural form / structure of the Honden.
- Limitation: the reviewed record does not directly establish the Honden cardinal
  orientation.

#### Ritual / symbolic target

- Owner: 伏見稲荷大社
- Source: 奥社奉拝所
- Type: shrine official
- URL:
  `https://inari.jp/sp/map/spot_08/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 奥社奉拝所 is a place from which 稲荷山 / 三ヶ峰 is worshipped from
  afar.
- Limitation: no exact true-north degree value is adopted.

### 5.3 宇佐神宮

#### Physical orientation

- Owner: 文化庁
- Source: 宇佐神宮本殿
- Type: Cultural Affairs material
- URL:
  `https://kunishitei.bunka.go.jp/heritage/detail/102/3599`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 第一殿・第二殿・第三殿 face south and are arranged east-west.
- Limitation: `SOUTH` is not converted into an invented `180.0°`.

#### Worship relation

- Owner: 宇佐市
- Source: 宇佐神宮 上宮
- Type: municipal official material
- URL:
  `https://www.city.usa.oita.jp/tourist/touristspot/touristspot2/touristspot3/10171.html`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: worshippers face the three Honden in the documented worship
  arrangement.

#### Central architectural relation

- Owner: 大分県
- Source: 南中楼門
- Type: prefectural cultural-property material
- URL:
  `https://oita-digitalzukan.jp/cultural_property/%E5%8D%97%E4%B8%AD%E6%A5%BC%E9%96%80/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 南中楼門 is the southern principal gate and stands in front of
  第二殿.

#### Related sacred place

- Owner: 文化庁
- Source: 宇佐神宮境内
- Type: cultural-property / historical material
- URL:
  `https://online.bunka.go.jp/heritages/detail/206773`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 御許山 has an important religious / historical relation to the
  shrine and the 比売神 tradition.
- Limitation: does not establish that the Honden were intentionally oriented toward
  御許山.

### 5.4 春日大社

#### Physical orientation

- Owner: 日本建築学会 / J-STAGE
- Source: scholarly architectural research concerning Kasuga Taisha and shrine
  orientation
- Type: specialist architectural research
- URL:
  `https://www.jstage.jst.go.jp/article/aija/65/530/65_KJ00004225732/_pdf`
- Evidence level: `E2_SCHOLARLY`
- Supported claim: the principal Kasuga Taisha sanctuary buildings are south-facing.
- Limitation: no exact degree value or documented symbolic cause is adopted.

#### Ritual / symbolic target

- Owner: 春日大社
- Source: 御蓋山浮雲峰遙拝所
- Type: shrine official
- URL:
  `https://www.kasugataisha.or.jp/guidance/index/modal-26/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: the worship point is for the 浮雲峰 at the summit of 御蓋山,
  associated with the descent tradition of 武甕槌命.
- Supported symbolic relation: the official material also describes a broader spatial /
  religious relation involving 浮雲峰, the Honden, and 平城京大極殿.
- Limitation: this does not establish that the Honden were built south-facing for the
  purpose of facing the Great Audience Hall.

### 5.5 建勲神社

#### Physical orientation

- Owner: 文化庁
- Source: 建勲神社本殿
- Type: Cultural Affairs material
- URL:
  `https://kunishitei.bunka.go.jp/heritage/detail/101/00007058`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: the Honden stands on 船岡山 and faces east.
- Limitation: no exact degree value or symbolic reason is established.

#### Ritual structure

- Owner: 建勲神社
- Source: 境内案内
- Type: shrine official
- URL:
  `https://kenkun-jinja.org/precincts/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 神門 is in front of the Honden and 拝殿 is east of the Honden.

#### Formal worship relation

- Owner: 建勲神社
- Source: 正式参拝
- Type: shrine official
- URL:
  `https://kenkun-jinja.org/worship/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: formal worship enters within the 神門 and worship is directed to the
  Honden.
- Limitation: the worship vector is not stored as `WEST` unless a source explicitly
  states that cardinal direction.

#### Symbolic geography

- Owner: 建勲神社
- Source: 船岡大祭 宮司講話「京都の玄武の守りとされる船岡山」
- Type: shrine official
- URL:
  `https://kenkun-jinja.org/greeting/%E8%88%B9%E5%B2%A1%E5%A4%A7%E7%A5%AD-%E5%AE%AE%E5%8F%B8%E8%AC%9B%E8%A9%B1%E3%80%8C%E4%BA%AC%E9%83%BD%E3%81%AE%E7%8E%84%E6%AD%A6%E3%81%AE%E5%AE%88%E3%82%8A%E3%81%A8%E3%81%95%E3%82%8C%E3%82%8B%E8%88%B9/`
- Evidence level: `E1_AUTHORITATIVE`
- Supported claim: 船岡山 has a symbolic / directional relation to 平安京 as a
  northern reference / protective landscape.
- Limitation: no accepted source establishes that the Honden was built east-facing
  toward a specific symbolic target.

---

## 6. Normalized 15-Cell Result Matrix

One normalized decision per shrine × layer.

| # | Shrine | Layer | Status | Normalized basis |
| ---: | --- | --- | --- | --- |
| 01 | 日光東照宮 | `PHYSICAL_ORIENTATION` | `CONFIRMED` | shrine / principal site recorded as south-facing |
| 02 | 日光東照宮 | `RITUAL_AXIS` | `CONFIRMED` | 拝殿 → 石の間 → 本殿 ritual / architectural function documented |
| 03 | 日光東照宮 | `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | no accepted source establishes a Toshogu symbolic target such as 江戸 |
| 04 | 伏見稲荷大社 | `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | precinct WEST is confirmed, Honden cardinal orientation is not directly established |
| 05 | 伏見稲荷大社 | `RITUAL_AXIS` | `CONFIRMED` | 奥社奉拝所 → 稲荷山三ヶ峰 documented as 遥拝 relation |
| 06 | 伏見稲荷大社 | `SYMBOLIC_ORIENTATION` | `CONFIRMED` | explicit ritual target = 稲荷山三ヶ峰 |
| 07 | 宇佐神宮 | `PHYSICAL_ORIENTATION` | `CONFIRMED` | three Honden explicitly south-facing |
| 08 | 宇佐神宮 | `RITUAL_AXIS` | `CONFIRMED` | worship side / 南中楼門 relation to principal Honden documented |
| 09 | 宇佐神宮 | `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | 御許山 relationship does not prove orientation toward 御許山 |
| 10 | 春日大社 | `PHYSICAL_ORIENTATION` | `CONFIRMED` | scholarly architectural evidence supports south-facing Honden |
| 11 | 春日大社 | `RITUAL_AXIS` | `CONFIRMED` | 御蓋山浮雲峰遙拝所 → 浮雲峰 documented |
| 12 | 春日大社 | `SYMBOLIC_ORIENTATION` | `CONFIRMED` | explicit worship target = 御蓋山頂 浮雲峰 |
| 13 | 建勲神社 | `PHYSICAL_ORIENTATION` | `CONFIRMED` | Honden explicitly east-facing |
| 14 | 建勲神社 | `RITUAL_AXIS` | `CONFIRMED` | Haiden / Shinmon worship relation to Honden documented |
| 15 | 建勲神社 | `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | symbolic geography exists, Honden symbolic target does not |

### 6.1 Fushimi normalization rule

The evidence ledger contains both:

```text
PRECINCT_FRONT = WEST (CONFIRMED)
HONDEN_CARDINAL_ORIENTATION = NOT_DETERMINED
```

The pilot matrix asks whether the relevant shrine building / sanctuary orientation is
established.

Therefore the single normalized Fushimi `PHYSICAL_ORIENTATION` cell is
`NOT_DETERMINED`.

No new `PARTIAL` status is introduced.

---

## 7. Rates

### 7.1 PHYSICAL_ORIENTATION

```text
CONFIRMED      = 4 / 5 = 80.0 %
NOT_DETERMINED = 1 / 5 = 20.0 %
HOLD           = 0 / 5 =  0.0 %
```

### 7.2 RITUAL_AXIS

```text
CONFIRMED      = 5 / 5 = 100.0 %
NOT_DETERMINED = 0 / 5 =   0.0 %
HOLD           = 0 / 5 =   0.0 %
```

### 7.3 SYMBOLIC_ORIENTATION

```text
CONFIRMED      = 2 / 5 = 40.0 %
NOT_DETERMINED = 3 / 5 = 60.0 %
HOLD           = 0 / 5 =  0.0 %
```

### 7.4 Overall

```text
TOTAL_CELLS                      = 15
OVERALL_EVIDENCE_ACQUISITION_RATE = 11 / 15 = 73.3 %
OVERALL_NOT_DETERMINED_RATE       =  4 / 15 = 26.7 %
OVERALL_HOLD_RATE                 =  0 / 15 =  0.0 %
```

`NOT_DETERMINED` and `HOLD` are not combined.

---

## 8. Evidence Findings and Boundary Rules

### 8.1 Structure scope must be explicit

`orientation_subject` is mandatory.

A statement about:

- 境内;
- 本殿;
- 拝殿;
- 楼門;
- 遥拝所;
- mountain / sacred place;

must not be transferred across subjects without evidence.

Fushimi Inari demonstrates this directly:

```text
precinct front = WEST
does not automatically mean
Honden front = WEST
```

### 8.2 Physical orientation and ritual direction are separate

A building may physically face one direction while ritual attention is directed
elsewhere.

The pilot therefore requires separate storage for:

```text
PHYSICAL_ORIENTATION
RITUAL_AXIS
SYMBOLIC_ORIENTATION
```

### 8.3 Related sacred place is not automatically symbolic orientation

Usa Jingu demonstrates:

```text
religious / historical relation to 御許山 = supported
Honden intentionally oriented toward 御許山 = not established
```

### 8.4 Explicit 遥拝 is strong ritual / symbolic evidence

Fushimi Inari and Kasuga Taisha demonstrate that shrine-official descriptions of
`遥拝` can support:

```text
RITUAL_AXIS = CONFIRMED
SYMBOLIC_ORIENTATION = CONFIRMED
```

without requiring an invented compass degree.

### 8.5 Symbolic spatial relation is not automatically construction intent

Kasuga Taisha documents a broader symbolic spatial relation involving 浮雲峰, the
Honden, and 平城京大極殿.

The pilot preserves that relation while refusing to convert it into:

```text
"The Honden was built south-facing in order to face the Daigokuden."
```

without an explicit source.

### 8.6 Directional relation may not be reversed

The documented:

```text
大猷院 -> 東照宮
```

relationship may not be inverted into:

```text
東照宮 -> 江戸
or
東照宮 -> 大猷院
```

without independent evidence.

---

## 9. Reproducibility Assessment

### 9.1 Physical evidence

```text
4 / 5 confirmed
```

Physical orientation was reproducibly obtainable for most pilot shrines.

The one normalized non-confirmed case is not a source contradiction.
It is a scope-discipline case: Fushimi precinct orientation is known while the Honden
orientation remains unestablished under the accepted evidence.

### 9.2 Ritual evidence

```text
5 / 5 confirmed
```

The sample shows that ritual-axis evidence can often be obtained from:

- explicit shrine-official worship descriptions;
- documented role relationships among Honden, Haiden, gates, and worship spaces;
- explicit 遥拝 descriptions.

### 9.3 Symbolic evidence

```text
2 / 5 confirmed
3 / 5 not determined
```

This lower rate is expected under the evidence rules.

The pipeline is not designed to maximize symbolic coverage.
It is designed to reject unsupported symbolic claims.

### 9.4 HOLD behavior

```text
HOLD = 0 / 15
```

No accepted-source conflict was found in this pilot.

The absence of HOLD does not mean HOLD is unnecessary.
It means the pilot produced source insufficiency cases, not accepted-source conflicts.

---

## 10. Pilot Decision

The original deterministic decision criteria were:

### `VIABLE`

- PHYSICAL orientation is reproducibly obtainable for most Pilot Shrines; and
- source hierarchy / STOP rules operate deterministically.

### `PARTIALLY_VIABLE`

- PHYSICAL evidence is usable;
- RITUAL / SYMBOLIC have substantial source gaps; and
- the system correctly returns `NOT_DETERMINED` instead of guessing.

### `NOT_YET_VIABLE`

- even PHYSICAL orientation cannot be reproduced reliably from accepted sources; or
- evidence classification is non-deterministic.

Observed:

```text
PHYSICAL confirmed = 4 / 5
RITUAL confirmed   = 5 / 5
classification rules behaved deterministically
unsupported symbolic claims were refused
missing evidence remained NOT_DETERMINED
```

Therefore:

```text
ORIENTATION_EVIDENCE_PIPELINE = VIABLE
```

This decision concerns evidence acquisition and classification only.

It does not decide whether orientation data must become a Production model field.

---

## 11. Contract Drafting Inputs

The pilot supports drafting a formal Orientation Evidence Contract.

```text
ORIENTATION_EVIDENCE_CONTRACT_SUPPORTABLE = YES
FORMAL_CONTRACT_CREATED                    = NO
```

At minimum, a future Contract should define:

1. `orientation_subject` as mandatory.
2. Independent `PHYSICAL_ORIENTATION`, `RITUAL_AXIS`, and
   `SYMBOLIC_ORIENTATION` layers.
3. Domain-specific source authority.
4. `CONFIRMED / NOT_DETERMINED / HOLD_ORIENTATION_REVIEW`.
5. A prohibition on converting cardinal prose into invented exact degree values.
6. A prohibition on inferring symbolic intent from geometry.
7. A prohibition on transferring precinct orientation to a building without evidence.
8. A prohibition on transferring a sacred-place relationship into an orientation claim.
9. A prohibition on reversing directional relationships.
10. Separate handling of a confirmed symbolic spatial relation versus documented
    construction intent.

---

## 12. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No Shrine model was changed.
4. No Position Contract was changed.
5. No Recommendation / Compass / Route behavior was changed.
6. No formal Orientation Evidence Contract was created.
7. No symbolic meaning was inferred from geometry.
8. Missing evidence was not classified as HOLD.
9. No exact degree value was invented from cardinal prose.
10. The verified Mother Ship evidence packet supersedes the initial blocked 0/15 run
    for pilot assessment.
```

---

## 13. Final Summary

```text
PILOT_SHRINES = 5
LAYER_DECISIONS = 15

PHYSICAL_CONFIRMED = 4 / 5 = 80.0 %
RITUAL_CONFIRMED   = 5 / 5 = 100.0 %
SYMBOLIC_CONFIRMED = 2 / 5 = 40.0 %

OVERALL_CONFIRMED      = 11 / 15 = 73.3 %
OVERALL_NOT_DETERMINED =  4 / 15 = 26.7 %
OVERALL_HOLD           =  0 / 15 =  0.0 %

ORIENTATION_EVIDENCE_PIPELINE = VIABLE
ORIENTATION_EVIDENCE_CONTRACT_SUPPORTABLE = YES
FORMAL_CONTRACT_CREATED = NO
```

The pilot's main result is not that every orientation field can be filled.

The result is that supported orientation claims can be acquired with traceable
evidence, while unsupported claims can be stopped reproducibly before they enter the
canonical knowledge layer.
