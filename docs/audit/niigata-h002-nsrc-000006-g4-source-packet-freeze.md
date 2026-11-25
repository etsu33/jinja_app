# NIIGATA-001-H002 — nsrc-000006 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000006
candidate_name                = 赤井神社
prefecture                    = 新潟県
fact_owner                    = 赤井神社 / 新潟県佐渡市加茂歌代2662番地
upstream_G3                   = PASS
G3_classification             = NORMAL_MODEL_FIT
MOTHER_SHIP_G3_DECISION       = A

SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
NEXT_STATE                    = G4_EVIDENCE_READY

G4_KNOWLEDGE_FACT_EVIDENCE    = NOT_EXECUTED
FACT_READY                    = NO
G5                            = NOT_EXECUTED
PRODUCTION_WRITE              = NONE
```

This document freezes the G4 Source Packet for
`nsrc-000006 / 赤井神社（新潟県佐渡市加茂歌代2662番地）`.

This freeze does not create Knowledge rows, Knowledge Seed data, Evidence Gate PASS,
Candidate Master lifecycle changes, or Production writes.

```text
SOURCE_PACKET_FREEZE = PASS
!= FORMAL_G4 PASS
!= FACT_READY
!= Recommendation Eligible
!= Production Imported
!= CORE_READY
```

## 2. Execution context

```text
audit_date = 2026-10-14
base       = develop@998e2ab4dbe90f7e3a7b89fbdc1e309edaf22850
branch     = audit/nsrc-000006-g4-source-packet-freeze
```

Upstream authority:

- `docs/audit/niigata-h002-nsrc-000006-g3-source-knowledge-fit.md`
- `docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`
- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

## 3. Scope

```text
G4_SOURCE_PACKET_SCOPE = { nsrc-000006 }
```

The only Candidate in scope is:

```text
candidate_id     = nsrc-000006
handoff_id       = NIIGATA-001-H002
source_position  = page001-row006
official_name    = 赤井神社
official_address = 新潟県佐渡市加茂歌代2662番地
```

Explicitly out of scope:

```text
nsrc-000007 / 赤城社 / 十日町市四日町2534番地
nsrc-000008 / 赤城社 / 十日町市上組2059番地子
nsrc-000009 / 赤城社 / 十日町市伊達乙48番地
nsrc-000010 / 赤城社 / 南魚沼市芹田79番地
```

No nearby shrine, temple, cemetery, or same-area cultural context is inherited by proximity.

## 4. Fact owner freeze

```text
candidate_id = nsrc-000006

FACT_OWNER
= 赤井神社
= 新潟県佐渡市加茂歌代2662番地

identity_status
= CONFIRMED

duplicate_status
= NEW
```

The Fact-owner bridge is supported independently by:

```text
S1 current identity / address
S2 current festival owner / address
S3 historical shrine entry / 2662
```

Explicitly excluded as Fact owners:

- 江西院
- 加茂歌代墓地
- 歌代神社
- 堀内神社
- 春日神社
- 諏訪系 shrine
- 羽黒神社
- generic Sado / 加茂歌代 cultural practice not explicitly attached to 赤井神社

```text
FACT_OWNER_FREEZE          = PASS
PROXIMITY_FACT_INHERITANCE = FORBIDDEN
```

## 5. Frozen Source identities

For URL-backed Sources:

```text
semantic Source identity
= source_type + normalized URL
```

S1/S2/S3 are audit labels only.
They are not Production numeric IDs or future stable Seed keys.

### S1 — 新潟県神社庁「県内神社一覧」

```text
audit_label = S1
source_role = identity / listing provenance only
source_type = government
publisher   = 新潟県神社庁
url         = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15224
content_verified_on = 2026-10-14
```

Observed target identity:

- 赤井神社
- あかいじんじゃ
- 佐渡市加茂歌代2662番地

S1 is not a Primary Source for H1/H2/H3.

```text
H1 -> S1 = NO
H2 -> S1 = NO
H3 -> S1 = NO
```

### S2 — 佐渡芸能アーカイブ「加茂歌代まつりの鬼太鼓」

```text
audit_label = S2
source_role = H1 / H2 Primary Source
source_type = tourism_official
title       = 加茂歌代まつりの鬼太鼓
publisher   = 佐渡芸能アーカイブ
url         = https://sado-geinou.com/geinou/kamoutashiro/
content_verified_on = 2026-10-14
```

Observed shrine-specific material:

- 開催地: 加茂歌代集落、赤井神社
- 赤井神社の例祭は4月16日
- 上組・中組・下組の鬼太鼓が朝6時に神社でそろって舞を奉納した後、各地区を門付けする
- 元日の午前0時にも神社で舞を奉納する
- Access住所: 〒952-0028 新潟県佐渡市加茂歌代2662

S2 is frozen as the Primary Source for H1 and H2.

### S3 — 『佐渡神社誌』

```text
audit_label = S3
source_role = H3 Primary Source
source_type = local_history
title       = 佐渡神社誌
publisher   = 新潟県神職会佐渡支部
url         = https://dl.ndl.go.jp/pid/971197
bibliography = 新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602
content_verified_on = 2026-10-14
```

Observed same-shrine historical entry:

```text
村社 赤井神社
大字加茂歌代字赤井
2662番地鎮座

祭神:
- 素盞嗚尊
- 別雷尊

合祀:
- 倉稲魂命
- 菅原道真公

由緒:
- 創立年月不明
- 羽黒神社例祭との舞神子・鈴の振初めに関する記録
- 七度半の使に関する記録
- 堀内・春日・歌代・諏訪・赤井を「加茂の五神社」とする記録
```

S3 is frozen as the Primary Source for H3.

S3 historical Deity wording is not a current Deity Source.

## 6. History Fact freeze

Exactly three History candidates are frozen.

### H1 — 4月16日の赤井神社例祭と鬼太鼓奉納

```text
fact_id       = H1
fact_type     = ShrineHistory
history_type  = regional_context
fact_owner    = nsrc-000006

title
= 4月16日の赤井神社例祭と鬼太鼓奉納

content
= 赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が神社で舞を奉納した後、各地区を門付けする。

period_text
= ""

event_date
= null

Primary Source
= S2
```

Frozen semantic boundary:

```text
semantic_fact
= S2が赤井神社の4月16日の例祭と、3組の鬼太鼓による神社奉納・地区門付けを記録していること
```

Do not add:

- prayer / benefit meaning;
- spiritual efficacy;
- generic 鬼太鼓 origin;
- a claim that every historical year followed the same format;
- an exact event_date for a recurring annual observance.

### H2 — 元日午前0時の鬼太鼓奉納

```text
fact_id       = H2
fact_type     = ShrineHistory
history_type  = tradition
fact_owner    = nsrc-000006

title
= 元日午前0時の鬼太鼓奉納

content
= 加茂歌代の鬼太鼓は、元日の午前0時にも赤井神社で舞を奉納する。

period_text
= ""

event_date
= null

Primary Source
= S2
```

Frozen semantic boundary:

```text
semantic_fact
= S2が現在の加茂歌代の鬼太鼓について、元日午前0時の赤井神社奉納を記録していること
```

The `tradition` type preserves practice wording without promoting it to a historical-event claim.

### H3 — 加茂の五神社としての記録

```text
fact_id       = H3
fact_type     = ShrineHistory
history_type  = regional_context
fact_owner    = nsrc-000006

title
= 加茂の五神社としての記録

content
= 1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を「加茂の五神社」と記録している。

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
= S3の1926年刊行資料が赤井神社を含む5社を「加茂の五神社」と記録していること
```

The Source publication year is not stored as an event_date or as a date of the underlying shrine relation.

This Fact does not assert:

- a current organizational hierarchy;
- a current formal collective;
- subordinate-shrine status;
- ownership of the other four shrines by 赤井神社.

## 7. Fact ↔ Primary Source freeze

```text
S2 佐渡芸能アーカイブ「加茂歌代まつりの鬼太鼓」
├─ H1 4月16日の赤井神社例祭と鬼太鼓奉納
└─ H2 元日午前0時の鬼太鼓奉納

S3 『佐渡神社誌』
└─ H3 加茂の五神社としての記録
```

Exact relation freeze:

```text
H1 -> S2 = YES
H2 -> S2 = YES
H3 -> S3 = YES

H1 -> S1 = NO
H2 -> S1 = NO
H3 -> S1 = NO

H1 -> S3 = NO
H2 -> S3 = NO
H3 -> S2 = NO
```

Counts:

```text
History candidate count       = 3
H1 related Source count       = 1
H2 related Source count       = 1
H3 related Source count       = 1
source-less History candidate = 0
```

## 8. Date precision boundary

All three frozen Facts use:

```text
event_date = null
```

H1/H2 describe recurring/current practices.
Their month/day wording remains in Source-backed content rather than being converted into a fabricated date instance.

H3 records what a 1926 publication says.
The publication year is not the event date of the underlying relation.

```text
SOURCE_DATE_PRECISION >= STORED_DATE_PRECISION
DATE_FABRICATION = NONE
```

## 9. Deity boundary

No current Deity Fact is authorized.

```text
ShrineDeity candidate count           = 0
ShrineDeityCollective candidate count = 0
accepted current deity                = NONE
deity source relation                 = NONE
```

Historical S3 evidence:

```text
祭神:
- 素盞嗚尊
- 別雷尊

合祀:
- 倉稲魂命
- 菅原道真公
```

For this packet:

```text
S3 historical Deity evidence
!= 2026 current ShrineDeity
```

G4 must not:

- create current Deity rows from S3;
- use third-party current Deity listings as accepted current Source;
- infer continuity;
- create placeholder / anonymous Deity values;
- create a ShrineDeityCollective.

## 10. Model Risk / ownership isolation

The accepted History payload requires no representation of:

- incomplete current Deity membership;
- anonymous collective;
- current main/sub-shrine hierarchy;
- current organizational relation among 加茂の五神社;
- associated worship targets;
- cross-shrine Fact ownership.

```text
FACT_OWNER                   = PASS
CROSS_SHRINE_CONTAMINATION  = NONE
MODEL_RISK_IN_ACCEPTED_FACTS = NONE_OBSERVED
HISTORY_TYPE_FIT            = PASS
SOURCE_RELATION             = PASS
DATE_PRECISION              = PASS
DEITY_INFERENCE             = NONE
```

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

```text
鬼太鼓 / 祭礼
!= 赤井神社固有のgoriyaku

歴史上の五神社記録
!= current organizational meaning
```

No Derived interpretation is frozen.

## 12. Verification metadata boundary

Frozen now:

- Source semantic identity;
- Source role;
- Fact owner;
- exact H1/H2/H3 wording;
- exact history_type;
- date precision;
- Fact ↔ Primary Source relation;
- Deity exclusion;
- Derived / Recommendation isolation.

Deferred to G4 Evidence / Seed Preflight:

```text
Source verification_status
Source confidence
Source verified_at

History verification_status
History confidence
History verified_at

stable Source keys
Knowledge Seed serialization
Base Shrine prerequisite
Source reuse conflict check
Evidence Gate usability
isolated DB preflight
idempotency
```

## 13. Acceptance matrix

| Condition | Result | Note |
|---|---|---|
| Scope limited to nsrc-000006 | PASS | other H002 excluded |
| Fact owner matches G1/G3 | PASS | 赤井神社 / 加茂歌代2662 |
| G3 Model Fit | PASS | NORMAL_MODEL_FIT |
| Accepted Knowledge Sources | PASS | S2 / S3 |
| History semantic boundary | PASS | H1 / H2 / H3 |
| Primary Source relation | PASS | H1->S2, H2->S2, H3->S3 |
| source-less frozen History | PASS | 0 |
| date precision boundary | PASS | no synthetic event_date |
| cross-shrine contamination | PASS | none in frozen packet |
| current Deity inference | PASS | none |
| anonymous collective risk | PASS | none |
| Derived / goriyaku isolation | PASS | no writes |
| Recommendation / Ranking isolation | PASS | no changes |
| Verification metadata | DEFERRED | G4 Evidence / Seed Preflight |
| Evidence Gate actual usability | NOT_EXECUTED | next G4 subtask |

No Source Packet HOLD condition is present.

## 14. Source Packet decision

```text
NSRC_000006_SOURCE_PACKET_FREEZE
= PASS / FROZEN / G4_EVIDENCE_READY

SOURCE_PACKET_HOLD
= NO
```

## 15. What this PASS does not authorize

```text
G4 Knowledge Fact + Evidence  = NOT_EXECUTED
FACT_READY                    = NO
G5 Recommendation Eligibility = NOT_EXECUTED
Production write              = NONE
CORE_READY                    = NO
```

It does not authorize Knowledge Seed creation, Base Shrine materialization, G5, or Production writes in this PR.

## 16. Files / data changed

```text
docs/audit/niigata-h002-nsrc-000006-g4-source-packet-freeze.md  ADDED

Candidate Master JSON                           NONE
Base Shrine Seed                               NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
Position Resolution Records                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
```

## 17. Final state

```text
G0 nsrc-000006               = PASS
G1 nsrc-000006               = PASS / NEW
G2 nsrc-000006               = PASS
G3 nsrc-000006               = PASS / NORMAL_MODEL_FIT

G4 Source Packet Freeze      = PASS / FROZEN / G4_EVIDENCE_READY
G4 Knowledge Fact + Evidence = NOT_EXECUTED

G5                           = NOT_EXECUTED
G6                           = NOT_EXECUTED
G7                           = NOT_EXECUTED
G8                           = NOT_REACHED
```

## 18. STOP

```text
STOP

Do not create Knowledge Seed in this PR.
Do not materialize Base Shrine in this PR.
Do not execute G5.
Do not write Production.

Next work item after merge:
nsrc-000006 Base Shrine materialization prerequisite
```
