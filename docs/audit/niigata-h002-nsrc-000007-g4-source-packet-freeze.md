# NIIGATA-001-H002 — nsrc-000007 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000007
candidate_name                = 赤城社
prefecture                    = 新潟県
fact_owner                    = 赤城社 / 新潟県十日町市四日町2534番地
upstream_G3                   = PASS
G3_classification             = NORMAL_MODEL_FIT

SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
NEXT_STATE                    = G4_EVIDENCE_READY

G4_KNOWLEDGE_FACT_EVIDENCE    = NOT EXECUTED
FACT_READY                    = NO
G5                            = NOT EXECUTED
PRODUCTION_WRITE              = NONE
```

This document freezes the G4 Source Packet for
`nsrc-000007 / 赤城社（新潟県十日町市四日町2534番地）`.

This Source Packet freeze does not create Knowledge rows, create Knowledge Seed data,
run Evidence Gate against materialized data, modify Candidate Master lifecycle state,
or write Production data.

```text
SOURCE_PACKET_FREEZE = PASS
!= G4 Knowledge Fact + Evidence PASS
!= FACT_READY
!= Recommendation Eligible
!= Production Imported
!= CORE_READY
```

## 2. Execution context

```text
audit_date = 2026-10-13
base       = develop@b4ee6476318e570badcf06d56d09e1adf6299463
branch     = audit/niigata-h002-nsrc-000007-g4-source-packet-freeze
```

Upstream authority:

- `docs/audit/niigata-h002-nsrc-000007-g3-source-knowledge-fit.md`
- `docs/audit/niigata-h002-nsrc-000007-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`
- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

## 3. Scope

```text
G4_SOURCE_PACKET_SCOPE = { nsrc-000007 }
```

The only Candidate in scope is:

```text
candidate_id     = nsrc-000007
handoff_id       = NIIGATA-001-H002
source_position  = page001-row007
official_name    = 赤城社
official_address = 新潟県十日町市四日町2534番地
```

Explicitly out of scope:

```text
nsrc-000006 / 赤井神社 / 佐渡市加茂歌代2662番地
nsrc-000008 / 赤城社 / 十日町市上組2059番地子
nsrc-000009 / 赤城社 / 十日町市伊達乙48番地
nsrc-000010 / 赤城社 / 南魚沼市芹田79番地
```

No same-name Candidate is included by name-only matching.

## 4. Fact owner freeze

The Fact owner is inherited from G3 without reinterpretation:

```text
candidate_id = nsrc-000007

FACT_OWNER
= 赤城社
= 新潟県十日町市四日町2534番地

identity_status
= CONFIRMED

duplicate_status
= SAME_NAME_DIFFERENT_SHRINE
```

Name-only Fact ownership is prohibited because H002 contains multiple distinct shrines named
`赤城社`.

The following are explicitly excluded as Fact owners for this packet:

- 赤城社 / 十日町市上組2059番地子
- 赤城社 / 十日町市伊達乙48番地
- 赤城社 / 南魚沼市芹田79番地
- other shrine owners on the same Source page
- neighboring shrines or same-area shrines without direct Source attribution

```text
FACT_OWNER_FREEZE = PASS
NAME_ONLY_FACT_OWNERSHIP = FORBIDDEN
```

## 5. Frozen Source identities

For URL-backed Sources, the repository Source contract uses:

```text
semantic Source identity
= source_type + normalized URL
```

`S1 / S2 / S3` below are audit labels for this packet.
They are not Production numeric IDs and are not stable Source keys for a future Knowledge Seed.

### S1 — 新潟県神社庁「県内神社一覧」

```text
audit_label = S1

source_role
= identity / listing provenance only

source_type
= government

publisher
= 新潟県神社庁

url
= https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50

semantic_identity
= government
  + https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50

content_verified_on
= 2026-10-13
```

Observed target identity:

- 赤城社
- あかぎしゃ
- 十日町市四日町2534番地

The current repository uses `government` as the enum-compatible Source type for prefectural
Jinja-cho material. This is an enum compatibility classification, not a legal-status claim.

S1 is provenance for identity / listing only.

```text
H1 -> S1 = NO
H2 -> S1 = NO
```

### S2 — 十日町市「歴史文化基本構想 資料集」

```text
audit_label = S2

source_role
= H1 Primary Source

source_type
= government

publisher
= 十日町市

url
= https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf

semantic_identity
= government
  + https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf

bibliography
= 中魚沼郡誌上 p.398

content_verified_on
= 2026-10-13
```

Observed shrine-specific material includes:

- 赤城社
- 中条村大字四日町
- 祭神として「土田岐入彦命」を記録
- 安政7年正月再建を記録

S2 is frozen as the Primary Source for H1.

The deity wording remains historical evidence only and is not promoted into a current
`ShrineDeity`.

### S3 — 十日町市博物館「越後縮幡」

```text
audit_label = S3

source_role
= H2 Primary Source

source_type
= museum_or_archive

publisher
= 十日町市博物館

url
= https://www.tokamachi-museum.jp/archives/bunka023/

semantic_identity
= museum_or_archive
  + https://www.tokamachi-museum.jp/archives/bunka023/

content_verified_on
= 2026-10-13
```

Observed shrine-specific material includes:

- owner: 赤城社（四日町2534）
- 越後縮幡のうち20旒が赤城社へ奉納されていたこと

S3 is frozen as the Primary Source for H2.

The same page contains other shrine owners.
Those rows are not inherited into `nsrc-000007`.

## 6. History Fact freeze

This packet freezes exactly two History candidates.

No `ShrineHistory` row is created by this document.

### H1 — 安政7年正月の再建

```text
fact_id       = H1
fact_type     = ShrineHistory
history_type  = historical_event
fact_owner    = nsrc-000007

title
= 安政7年正月の再建

content
= 赤城社は安政7年正月に再建された。

period_text
= 安政7年正月

event_date
= null

Primary Source
= S2
```

Frozen semantic boundary:

```text
semantic_fact
= S2が四日町の赤城社について「安政7年正月再建」と記録していること
```

Do not add:

- an exact Gregorian date;
- a synthetic `1月1日`;
- a current-building continuity claim;
- a current Deity claim;
- psychological or religious efficacy;
- a goriyaku interpretation.

### H2 — 赤城社に伝わった越後縮幡

```text
fact_id       = H2
fact_type     = ShrineHistory
history_type  = regional_context
fact_owner    = nsrc-000007

title
= 赤城社に伝わった越後縮幡

content
= 越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。

period_text
= ""

event_date
= null

Primary Source
= S3
```

Frozen semantic boundary:

```text
semantic_fact
= 赤城社（四日町2534）と越後縮幡20旒の奉納・所蔵文脈
```

This Fact does not import:

- the complete collection's broader date range;
- cultural-property designation dates as shrine event dates;
- prayer / benefit meanings of the wider 縮幡 practice;
- facts belonging to other owner shrines on the same museum page.

## 7. Fact ↔ Primary Source freeze

The frozen relation graph is:

```text
S2 十日町市「歴史文化基本構想 資料集」
└─ H1 安政7年正月の再建

S3 十日町市博物館「越後縮幡」
└─ H2 赤城社に伝わった越後縮幡
```

Exact relation freeze:

```text
H1 -> S2 = YES
H2 -> S3 = YES

H1 -> S1 = NO
H2 -> S1 = NO

H1 -> S3 = NO
H2 -> S2 = NO
```

Frozen adopted History counts:

```text
History candidate count      = 2
H1 related Source count      = 1
H2 related Source count      = 1
source-less History candidate = 0
```

## 8. Date precision boundary

### H1

S2 supports:

```text
安政7年正月再建
```

The stored precision must not exceed the Source precision.

```text
H1_DATE_PRECISION
= ERA_YEAR_MONTH_LEVEL

period_text
= 安政7年正月

event_date
= null
```

Do not:

- synthesize a Gregorian exact date;
- store `1月1日`;
- treat `正月` as a confirmed exact date;
- increase the stored precision beyond the Source wording.

### H2

The current accepted Source does not establish a shrine-specific date range for the 20
赤城社 items.

```text
H2_DATE_PRECISION
= NOT_CONFIRMED

period_text
= ""

event_date
= null
```

The broader collection-level date range is not copied to H2.

Cultural-property designation dates are not treated as H2 event dates.

Global packet invariant:

```text
SOURCE_DATE_PRECISION
>=
STORED_DATE_PRECISION
```

## 9. Deity boundary

This Source Packet authorizes no current Deity Fact.

```text
ShrineDeity candidate count
= 0

ShrineDeityCollective candidate count
= 0

accepted current deity
= NONE

deity source relation
= NONE
```

### 土田岐入彦命

S2 historically records:

```text
祭神 = 土田岐入彦命
```

For this packet:

```text
土田岐入彦命
= historical Source evidence
!= current ShrineDeity
```

### 経津主命

Third-party research produced a current-ish lead for `経津主命`.

For this packet:

```text
経津主命
= research lead only
!= accepted current ShrineDeity
```

G4 must not:

- create a ShrineDeity row for 土田岐入彦命;
- create a ShrineDeity row for 経津主命;
- infer Deity from the shrine name;
- infer current continuity from historical material;
- treat repeated secondary material as accepted current Deity evidence;
- create anonymous / placeholder Deity values;
- create a ShrineDeityCollective without source-attested collective semantics.

## 10. Model Risk / ownership isolation

The frozen History payload requires no representation of:

- anonymous collective deities;
- incomplete deity membership;
- unresolved current deity identity within the accepted History Facts;
- main-shrine / sub-shrine hierarchy;
- associated worship targets;
- shinbutsu-shugo identity relations;
- cross-shrine Fact ownership.

Therefore:

```text
FACT_OWNER                    = PASS
CROSS_SHRINE_CONTAMINATION   = NONE
MODEL_RISK_IN_ACCEPTED_FACTS  = NONE OBSERVED
HISTORY_TYPE_FIT             = PASS
SOURCE_RELATION              = PASS
DATE_PRECISION               = PASS
DEITY_INFERENCE              = NONE
```

Current Deity research remains open independently.
It is not part of this packet's authorized G4 payload.

## 11. Derived / goriyaku / Recommendation isolation

This Source Packet does not generate or modify:

```text
goriyaku
goriyaku_tags
ShrineGoriyakuAssignment
history_theme
culture_translation
shrine_meaning_profile
Need mapping
Recommendation score
Ranking
Concierge
Compass
```

In particular:

```text
越後縮幡一般の信仰用途
!= 赤城社固有のgoriyaku

安政7年正月の再建
!= 再生 / 再起 / 厄除け等のDerived意味
```

No Derived or recommendation interpretation is frozen by this packet.

```text
DERIVED_KNOWLEDGE_GENERATION = NONE
GORIYAKU_WRITE               = NONE
RECOMMENDATION_CHANGE        = NONE
RANKING_CHANGE               = NONE
G5_EXECUTION                 = NOT EXECUTED
```

## 12. Verification metadata boundary

This Source Packet freezes:

- Source semantic identity;
- Source role;
- Fact owner;
- History semantic boundary;
- date precision;
- Fact ↔ Primary Source relation;
- Deity exclusion boundary;
- Derived / Recommendation isolation.

The following remain the responsibility of the G4 Evidence / Seed Preflight:

```text
Source verification_status
Source confidence
Source verified_at

History verification_status
History confidence
History verified_at

stable Source keys
Knowledge Seed serialization
Base Shrine / shrine_ref prerequisite
Source reuse conflict check
Evidence Gate usability
isolated DB preflight
idempotency
```

This Source Packet does not fabricate verification timestamp precision or stable Source keys.

## 13. Source Packet acceptance matrix

| Condition | Result | Note |
|---|---|---|
| Scope limited to nsrc-000007 | PASS | H002 other candidates excluded |
| Fact owner matches G1/G3 | PASS | 赤城社 / 四日町2534 |
| G3 Model Fit | PASS | NORMAL_MODEL_FIT |
| Accepted Knowledge Sources | PASS | S2 / S3 |
| History semantic boundary | PASS | H1 / H2 |
| Primary Source relation | PASS | H1->S2, H2->S3 |
| source-less frozen History | PASS | 0 |
| date precision boundary | PASS | no synthetic precision |
| cross-shrine contamination | PASS | none in frozen packet |
| current Deity inference | PASS | none |
| anonymous collective risk | PASS | none in frozen packet |
| Derived / goriyaku isolation | PASS | no writes |
| Recommendation / Ranking isolation | PASS | no changes |
| Verification metadata | DEFERRED | G4 Evidence / Seed Preflight |
| Evidence Gate actual usability | NOT EXECUTED | next G4 subtask |

No Source Packet HOLD condition is present.

## 14. Source Packet decision

Therefore:

```text
NSRC_000007_SOURCE_PACKET_FREEZE
= PASS / FROZEN / G4_EVIDENCE_READY

SOURCE_PACKET_HOLD
= NO
```

Rationale:

1. Fact owner is unambiguous and inherited from G3;
2. S2 and S3 are accepted Source-backed Knowledge Sources;
3. H1 and H2 remain within Source scope;
4. each frozen History candidate has exactly one Primary Source;
5. source-less frozen History candidate count is zero;
6. date precision does not exceed Source precision;
7. current Deity uncertainty is excluded rather than inferred;
8. no Model Risk is hidden inside the accepted History candidates;
9. no Derived / goriyaku / Recommendation change is introduced.

## 15. What this PASS does not authorize

```text
G4 Knowledge Fact + Evidence = NOT EXECUTED
FACT_READY                   = NO
G5 Recommendation Eligibility = NOT EXECUTED
Production write             = NONE
CORE_READY                   = NO
```

This PASS only authorizes the next G4 Evidence / Seed Preflight to use the frozen packet.

It does not authorize:

- Knowledge Seed creation in this PR;
- Base Shrine materialization in this PR;
- current Deity rows;
- Evidence Gate PASS claims;
- Recommendation eligibility;
- Production import.

## 16. Isolation / no-write record

No changes are made to:

```text
Candidate Master
Base Shrine Seed
Knowledge Seed
Production DB
Position Resolution Records
Model / Migration / Serializer / Runtime
goriyaku / goriyaku_tags
Recommendation / Ranking
Concierge / Compass
```

## 17. Final state

```text
G0 nsrc-000007               = PASS
G1 nsrc-000007               = PASS / SAME_NAME_DIFFERENT_SHRINE
G2 nsrc-000007               = PASS
G3 nsrc-000007               = PASS / NORMAL_MODEL_FIT

G4 Source Packet Freeze      = PASS / FROZEN / G4_EVIDENCE_READY
G4 Knowledge Fact + Evidence = NOT EXECUTED

G5                           = NOT EXECUTED
G6                           = NOT EXECUTED
G7                           = NOT EXECUTED
G8                           = NOT REACHED
```

## 18. Files / data changed

```text
docs/audit/niigata-h002-nsrc-000007-g4-source-packet-freeze.md  ADDED

Candidate Master JSON                           NONE
Base Shrine Seed                               NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
Position Resolution Records                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
```

## 19. STOP

```text
STOP

Do not execute G4 Evidence / Seed Preflight in this PR.
Do not create Knowledge Seed in this PR.
Do not materialize Base Shrine in this PR.
Do not execute G5.
Do not write Production.

Next work item after merge:
nsrc-000007 G4 Evidence / Seed Preflight
```
