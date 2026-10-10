# NIIGATA-001-H001 — nsrc-000002 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000002
candidate_name                = 青澤神社
prefecture                    = 新潟県
fact_owner                    = 青澤神社（糸魚川市）
upstream_G3                   = PASS
G3_classification             = NORMAL_MODEL_FIT
SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
NEXT_STATE                    = G4_EVIDENCE_READY
G4_KNOWLEDGE_FACT_EVIDENCE    = NOT EXECUTED
PRODUCTION_WRITE              = NONE
```

This document freezes the Source Packet for `nsrc-000002 / 青澤神社（糸魚川市）`.

It does **not** create Knowledge rows, run the full G4 Knowledge Fact + Evidence Gate, change
Candidate Master lifecycle state, or write Production data.

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
audit_date = 2026-10-10
base       = develop
branch     = audit/nsrc-000002-g4-source-packet-freeze
```

Upstream:

- PR #3143: G2 Position PASS
- PR #3144: G3 PASS / NORMAL_MODEL_FIT
- `docs/audit/niigata-h001-nsrc-000002-g3-source-knowledge-fit.md`
- `docs/audit/shrine-position/niigata-h001-aosawa-jinja-position-resolution.md`

## 3. Scope

```text
G4_SOURCE_PACKET_SCOPE = { nsrc-000002 }
```

This packet does not modify or re-evaluate:

- nsrc-000001 / 相吉神社
- nsrc-000003 / 蒼柴神社
- nsrc-000004 / 青海神社
- nsrc-000005 / 青山稲荷神社

## 4. Fact owner

The Fact owner is frozen as:

```text
candidate_id = nsrc-000002
fact_owner   = 青澤神社（糸魚川市）
```

Canonical G1 identity:

```text
official_name    = 青澤神社
official_address = 新潟県糸魚川市大字青海2696番地
```

The accepted Knowledge Source writes the shrine name as `青沢神社`.

The orthographic difference:

```text
青澤神社
青沢神社
```

is controlled by:

- matching reading `あおさわじんじゃ`;
- matching 糸魚川市 / 青海地域 locality;
- G1-confirmed canonical identity;
- G2-confirmed same-shrine Mapion POI;
- no competing same-locality shrine identity observed in the accepted packet.

The packet does not rename the canonical Candidate.

## 5. Frozen Source identities

### S1 — 新潟県神社庁 directory

```text
source_id_candidate = NIIGATA_JINJACHO_AOSAWA
source_type          = government
title                = 検索結果 | 新潟県神社庁
publisher            = 新潟県神社庁
url                  = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15216
language             = ja
accessed_at          = 2026-10-10
```

S1 supports canonical identity / listing provenance.

S1 does not directly support the History Fact frozen below and is not assigned as that Fact's
Primary Source.

The repository currently uses `government` as the enum-compatible Source type for prefectural
Jinja-cho material. This is an enum compatibility classification, not a legal-status claim.

### S2 — 糸魚川市「地域のまつり紹介サイト」4月の地域の祭り

```text
source_id_candidate = ITOIGAWA_AOSAWA_SPRING_FESTIVAL
source_type          = government
title                = 4月の地域の祭り | 新潟県糸魚川市 - 地域のまつり紹介サイト
publisher            = 糸魚川市 / 糸魚川ジオパーク協議会
url                  = https://matsuri.geo-itoigawa.com/calendar/m04/
language             = ja
accessed_at          = 2026-10-10
```

Current page provenance:

```text
site operator = 糸魚川ジオパーク協議会
office        = 糸魚川市ジオパーク推進室内
copyright     = 糸魚川市
```

Observed shrine-specific section:

```text
event   = 青沢神社 春季祭礼（春まつり）
timing  = 毎年4月第3日曜日
region  = 青海地域 大沢地区
venue   = 青沢神社

eve:
- 19:00から神楽奉納

festival day:
- 9:00 祭礼
- 9:40 神輿・子供みこし 地区巡回
- 11:00 神楽奉納
- 11:30 手踊り
```

S2 is the Primary Source for the History Fact candidate frozen below.

## 6. History freeze

### H1 — 青沢神社の春季祭礼

```text
history_type = regional_context
title        = 青沢神社の春季祭礼
content      = 青沢神社では毎年4月第3日曜日に春季祭礼が行われ、前日の宵宮には神楽が奉納される。祭礼当日は神輿・子供みこしの地区巡回、神楽奉納、手踊りが行われる。
period_text  = 毎年4月第3日曜日
event_date   = null
Primary Source = S2
```

Frozen semantic boundary:

```text
semantic_fact
= 青沢神社で毎年行われる春季祭礼の現在の地域祭礼文脈
```

This is classified as `regional_context` because the Source describes a recurring local shrine
festival and its current ritual / community structure rather than founding, official origin, or a
single dated historical event.

Do not add:

- an ancient origin for the festival;
- a founding date for 青澤神社;
- an interpretation that the listed practices have continued unchanged for any unsupported
  historical duration;
- religious efficacy or promised outcomes;
- a precise calendar date as a permanent `event_date`;
- any deity identity.

## 7. Date precision boundary

The page contains both a page-instance date and a recurrence rule:

```text
4月16日(日)
※毎年4月第3日曜日
```

The reusable Fact is the recurring practice, not the page-instance calendar occurrence.

Therefore:

```text
period_text = 毎年4月第3日曜日
event_date  = null
```

No year or synthetic exact date is created.

## 8. Deity boundary

G3 identified a secondary-source research lead for `沼河比賣命 / 沼河比売命`, but no accepted
Deity Source was frozen.

Therefore:

```text
ShrineDeity candidate count = 0
accepted deity              = NONE
deity source relation       = NONE
```

This packet does not infer a deity from:

- shrine naming;
- regional mythology;
- secondary shrine directories;
- visitor pages;
- repeated secondary-source agreement.

The absence of a Deity Fact does not invalidate the Source-backed History path.

## 9. Fact ↔ Primary Source freeze

```text
S2 糸魚川市 地域のまつり紹介サイト
└─ H1 青沢神社の春季祭礼
```

Frozen Source relation:

```text
H1 -> S2
```

S1 remains identity / listing provenance only:

```text
H1 -> S1 = NO
```

## 10. Verification metadata boundary

This Source Packet freezes semantic ownership and Source relation only.

The following remain G4 Evidence / Seed preflight responsibilities:

```text
S2 verification_status
S2 confidence
S2 verified_at

H1 verification_status
H1 confidence
H1 verified_at

stable source key
Knowledge Seed serialization
Evidence Gate usability
isolated import preflight
```

The packet does not fabricate timestamp precision that has not yet been frozen in an Evidence
preflight.

## 11. Model Risk / ownership review

The accepted Fact candidate requires no representation of:

- anonymous collective deities;
- unresolved current deity identity relations;
- main-shrine / sub-shrine hierarchy;
- associated worship targets;
- shinbutsu-shugo identity relations;
- cross-shrine Fact ownership.

The Fact is directly attached to 青沢神社 by the Source's event heading and venue.

Therefore:

```text
FACT_OWNER                         = PASS
CROSS_SHRINE_CONTAMINATION        = NONE
MODEL_RISK                        = NONE OBSERVED
HISTORY_TYPE_FIT                  = PASS
SOURCE_RELATION                   = PASS
DATE_PRECISION                    = PASS
```

## 12. Derived / recommendation isolation

This Source Packet does not generate or modify:

```text
goriyaku
goriyaku_tags
history_theme
culture_translation
shrine_meaning_profile
Need mapping
Recommendation score
Ranking
Concierge
Compass
```

A current regional festival Fact may support later Derived curation, but it is not itself a
derived recommendation interpretation.

## 13. Source Packet PASS decision

```text
Fact owner                        = PASS
G3 Model Fit                      = PASS / NORMAL_MODEL_FIT
accepted Knowledge Source         = PASS
History semantic boundary         = PASS
date precision boundary           = PASS
Primary Source relation           = PASS
source-less frozen Fact           = 0
cross-shrine contamination        = NONE
unresolved model-risk structure   = NONE
Deity inference                   = NONE
```

Therefore:

```text
NSRC_000002_SOURCE_PACKET_FREEZE
= PASS / FROZEN / G4_EVIDENCE_READY

SOURCE_PACKET_HOLD
= NO
```

## 14. What this PASS does not authorize

```text
G4 Knowledge Fact + Evidence = NOT EXECUTED
FACT_READY                   = NO
G5 Recommendation Eligibility = NOT EXECUTED
Production write             = NONE
CORE_READY                   = NO
```

The next G4 task must execute Evidence / Seed preflight and may only use the frozen Source-bounded
History candidate unless a separately accepted Source is added through the appropriate Gate.

## 15. Isolation / no-write record

No changes are made to:

```text
Candidate Master
Base Shrine Seed
Knowledge Seed
Production DB
Position Resolution Records
Model / Migration / Serializer
Recommendation / Ranking
Concierge / Compass
```

## 16. Final state

```text
G0 nsrc-000002               = PASS
G1 nsrc-000002               = PASS / NEW
G2 nsrc-000002               = PASS
G3 nsrc-000002               = PASS / NORMAL_MODEL_FIT
G4 Source Packet Freeze      = PASS / FROZEN / G4_EVIDENCE_READY
G4 Knowledge Fact + Evidence = NOT EXECUTED
G5                           = NOT EXECUTED
G6                           = NOT EXECUTED
G7                           = NOT EXECUTED
G8                           = NOT REACHED
```

STOP at Source Packet Freeze.
