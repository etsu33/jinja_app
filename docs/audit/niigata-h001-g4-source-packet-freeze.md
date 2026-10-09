# NIIGATA-001-H001 — nsrc-000004 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000004
candidate_name                = 青海神社
prefecture                    = 新潟県
fact_owner                    = 青海神社（加茂市）
upstream_G3                   = PASS
G3_classification             = CURATION_RELEASE_CANDIDATE
SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
NEXT_STATE                    = G4_EVIDENCE_READY
G4_KNOWLEDGE_FACT_EVIDENCE    = NOT EXECUTED
PRODUCTION_WRITE              = NONE
```

This document freezes the Source Packet for `nsrc-000004 / 青海神社（加茂市）`.

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
audit_date = 2026-10-09
base       = develop@62e1f4b424acf79cb6e21fb1ad8aa9c982eeaa23
branch     = audit/nsrc-000004-g4-source-packet-freeze
```

Upstream G3 record:

- `docs/audit/niigata-h001-g3-source-knowledge-fit.md`
- G3 result: `PASS / CURATION_RELEASE_CANDIDATE`

G3 remains the authority for Source / Knowledge Model Fit and the cross-shrine ownership
boundary. This packet narrows those accepted Sources into G4-ready Fact inputs without
executing G4 Evidence.

## 3. Scope

The Source Packet scope is exactly:

```text
G4_SOURCE_PACKET_SCOPE = { nsrc-000004 }
```

The following G2 HOLD Candidates are outside this packet:

```text
nsrc-000001 相吉神社      = HOLD_POSITION_REVIEW
nsrc-000002 青澤神社      = HOLD_POSITION_REVIEW
nsrc-000003 蒼柴神社      = HOLD_POSITION_REVIEW
nsrc-000005 青山稲荷神社  = HOLD_POSITION_REVIEW
```

No G3/G4 evaluation, lifecycle mutation, or data write is performed for those four Candidates.

## 4. Fact owner

The Fact owner is frozen as:

```text
nsrc-000004 Fact owner = 青海神社（加茂市）
```

The accepted official Source distinguishes:

```text
青海神社
賀茂神社
賀茂御祖神社
```

The three-shrine combined-honden structure does not collapse those shrine identities into one
Knowledge owner.

```text
same official page
!= same Fact owner

combined honden
!= merged ShrineDeity set
```

## 5. Frozen Source identities

### S1 — 青海神社公式「御祭神」

```text
source_id_candidate = AOMI_OFFICIAL_DEITY
source_type          = shrine_official
title                = 御祭神｜青海神社公式サイト｜新潟県加茂市鎮座
publisher            = 青海神社
url                  = https://www.aomi-jinjya.or.jp/history/gosaisin.html
language             = ja
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:09:11+09:00
```

The common `verified_at` above records the Mother Ship content-verification completion time
for the frozen Source review. It is not the page update date.

S1 directly supports the current 青海神社 Deity set used in this packet.

### S2 — 青海神社公式「由緒・年表」

```text
source_id_candidate = AOMI_OFFICIAL_HISTORY
source_type          = shrine_official
title                = 由緒,年表｜青海神社公式サイト｜新潟県加茂市鎮座
publisher            = 青海神社
url                  = https://www.aomi-jinjya.or.jp/history/yuisyo.html
language             = ja
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:09:11+09:00
```

S2 directly supports the founding and later historical-event candidates frozen below.

### S3 — 新潟県神社庁 directory

```text
source_id_candidate = NIIGATA_JINJACHO_DIRECTORY
source_type          = government
title                = 検索結果 | 新潟県神社庁
publisher            = 新潟県神社庁
url                  = https://niigata-jinjacho.jp/shrine_niigata/search.php
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:09:11+09:00
```

`government` is the current repository enum compatibility value. It does not assert that
新潟県神社庁 is a government administrative agency.

S3 supports identity / listing provenance. It is not a Primary Source for the Deity / History
Facts in this packet.

### S4 — 青海神社公式「御祈祷種類」

```text
source_id_candidate = AOMI_OFFICIAL_PRAYER_GUIDE
source_type          = shrine_official
title                = 御祈祷種類｜青海神社公式サイト｜新潟県加茂市鎮座
publisher            = 青海神社
url                  = https://www.aomi-jinjya.or.jp/gokitou/syurui.html
```

S4 is recorded only as the direct official Source supporting the goriyaku-evidence
characterization in this Source Packet.

This packet does **not** fabricate Source-level `accessed_at` / `verified_at` for S4.
Those metadata must be confirmed in the later G4 Evidence / Seed preflight if S4 is materialized
as a `ShrineKnowledgeSource`.

## 6. Deity freeze

### D1 — 椎根津彦命

```text
display_name         = 椎根津彦命
source_relationship  = 奉斎
explicit_source_role = NONE
model_role           = unknown
Primary Source       = S1
```

Boundary:

- Source reading is not appended to `display_name`.
- `canonical_name` is not frozen by this packet.
- Source order does not imply `primary`.
- `奉斎` confirms enshrinement relationship but does not establish a rank / position enum.

### D2 — 大国魂命

```text
display_name         = 大国魂命
source_relationship  = 奉斎
explicit_source_role = NONE
model_role           = unknown
Primary Source       = S1
```

Boundary:

- Source reading is not appended to `display_name`.
- `canonical_name` is not frozen by this packet.
- Source order does not imply `primary`.
- Explanatory relationship wording is not merged into `display_name`.

### Role decision

Current Knowledge Contract meaning:

```text
primary   = 主祭神
enshrined = 祀られている神（主祭神とは限らない一般的な位置付け）
secondary = 配祀神・相殿神
unknown   = 神社側の記載から序列・位置付けが判別できない
```

The accepted Source gives no explicit `主祭神 / 配祀 / 相殿` distinction between D1 and D2.

Therefore:

```text
D1 role = unknown
D2 role = unknown
```

No role is inferred from listing order or prose length.

## 7. Explicit Deity exclusions

The following Source-backed deities belong to separately named shrines and are excluded from
`nsrc-000004 ShrineDeity`.

```text
賀茂神社
- 賀茂別雷命

賀茂御祖神社
- 多多須玉依媛命
- 賀茂建角身命
```

Frozen ownership boundary:

```text
nsrc-000004 ShrineDeity
= 椎根津彦命
= 大国魂命

賀茂別雷命
= EXCLUDED from nsrc-000004 ShrineDeity

多多須玉依媛命
= EXCLUDED from nsrc-000004 ShrineDeity

賀茂建角身命
= EXCLUDED from nsrc-000004 ShrineDeity
```

A shared official page or combined-honden history does not transfer these Deity Facts to the
青海神社 Candidate row.

## 8. History freeze

### H1 — 神亀3年の創建

```text
history_type = founding
title        = 神亀3年の創建
content      = 神亀3年（726）、青海首一族が加茂山山麓に青海神社を創建した。
period_text  = 神亀3年（726）
event_date   = null
Primary Source = S2
```

Frozen semantic boundary:

```text
semantic_fact
= 青海首一族が加茂山山麓に青海神社を創建した
```

Do not add:

- an exact month / day;
- `726-01-01`;
- an interpretation that the shrine was founded at the current site;
- an interpretation that the current buildings date from 726;
- an interpretation that the present three-shrine combined-honden structure existed in 726;
- later 賀茂系 history;
- the 1872 combination event.

S2 contains founding-context deity wording, but the packet does not duplicate Deity Facts into
this History payload. Current Deity identity is handled through D1 / D2 and S1.

### H2 — 明治5年の三社本殿合殿

```text
history_type = historical_event
title        = 明治5年の三社本殿合殿
content      = 明治5年（1872）、青海・賀茂・御祖三社本殿を現在地に合殿した。
period_text  = 明治5年（1872）
event_date   = null
Primary Source = S2
```

Frozen semantic boundary:

```text
semantic_fact
= 青海・賀茂・御祖三社本殿を現在地に合殿した
```

Do not add:

- an exact month / day;
- `1872-01-01`;
- `遷座` as an editorial replacement unless a later accepted Source explicitly supports it;
- an interpretation that the three shrines became one shrine entity;
- an interpretation that 賀茂神社 / 賀茂御祖神社 Deities became 青海神社 Deities;
- an interpretation that current buildings were constructed in 1872;
- the prefectural-shrine designation recorded in the same annual chronology entry.

The prefectural-shrine designation is a separate semantic event and is not merged into H2.

## 9. Date precision boundary

For both History candidates:

```text
Source supplies year / era-year
-> period_text

Source does not supply exact month/day
-> event_date = null
```

Therefore:

```text
H1 event_date = null
H2 event_date = null
```

No synthetic January 1 date is created.

## 10. Fact ↔ Primary Source freeze

```text
S1 御祭神
├─ D1 椎根津彦命
└─ D2 大国魂命

S2 由緒・年表
├─ H1 神亀3年の創建
└─ H2 明治5年の三社本殿合殿
```

Frozen Source relation:

```text
D1 -> S1
D2 -> S1
H1 -> S2
H2 -> S2
```

S3 is identity / listing support only:

```text
D1 -> S3 = NO
D2 -> S3 = NO
H1 -> S3 = NO
H2 -> S3 = NO
```

The future Knowledge Seed may use file-local `source_keys`, but this packet does not create
those keys or a Seed file.

## 11. goriyaku evidence boundary

The official 青海神社 prayer guide provides direct current prayer-category evidence.

Frozen characterization:

```text
goriyaku_evidence         = PRESENT
evidence_type             = OFFICIAL_PRAYER_SUPPORTED
model characterization    = official_prayer_supported
Primary Source            = S4
```

This means only:

```text
official prayer wording is Source-backed
```

It does **not** mean:

```text
Source wording
= canonical KAMIMUSUBI GoriyakuTag
```

This Source Packet does not freeze a complete `ShrineSourceFact` inventory, stable keys,
verification fields, or canonical mapping records for S4. Those belong to later G4 Evidence /
Seed preflight.

## 12. goriyaku taxonomy isolation

The following are not executed in this packet:

```text
goriyaku_tags mapping       = NOT EXECUTED
Shrine.goriyaku update      = NOT EXECUTED
ShrineGoriyakuAssignment    = NOT EXECUTED
canonical concept mapping   = NOT EXECUTED
Need mapping                = NOT EXECUTED
Recommendation score write  = NOT EXECUTED
```

`ShrineSourceFact` evidence and `goriyaku_tags` taxonomy remain separate responsibilities.

## 13. Derived boundary

This Source Packet does not generate:

```text
history_theme
culture_translation
shrine_meaning_profile
```

Frozen principle:

```text
Stored Fact may support later Derived curation
!= Derived value is a Source Fact
!= Derived value may be auto-generated during Source Packet Freeze
```

No interpretive theme is derived from the 726 founding, the 1872 combination event, Deity names,
or prayer evidence in this task.

## 14. Source Packet PASS decision

The packet satisfies the Source Packet freeze boundary:

```text
Fact owner                         = PASS
G3 Model Fit                       = PASS / CURATION_RELEASE_CANDIDATE
Deity ownership                    = PASS
cross-shrine contamination         = NONE
anonymous collective               = NONE
unresolved current deity relation  = NONE
Deity role inference               = NONE
History semantic boundary          = PASS
date precision boundary            = PASS
Primary Source relation            = PASS
goriyaku evidence typing           = PASS
goriyaku_tags mapping              = NOT EXECUTED
Derived generation                 = NOT EXECUTED
Source identity conflict           = NONE OBSERVED
```

Therefore:

```text
NSRC_000004_SOURCE_PACKET_FREEZE
= PASS / FROZEN / G4_EVIDENCE_READY

SOURCE_PACKET_HOLD
= NO
```

## 15. What this PASS does not authorize

This document does not freeze or execute Fact-level G4 Evidence metadata.

The following remain later-G4 responsibilities:

```text
Deity verification_status
Deity confidence
Deity Fact verified_at

History verification_status
History confidence
History Fact verified_at

S4 full Source verification metadata if materialized
ShrineSourceFact stable keys / exact inventory
Evidence Gate usability
Knowledge Seed creation
isolated import preflight
```

The full G4 Gate remains:

```text
G4 Knowledge Fact + Evidence = NOT EXECUTED
```

## 16. Isolation / no-write record

This Source Packet is docs-only.

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
goriyaku taxonomy / mapping
G2 HOLD 4 Candidates
```

Specifically:

```text
Candidate Master write = NONE
Knowledge Seed write   = NONE
Production write       = NONE
```

## 17. Handoff

After this Source Packet PR is merged, the next task is a separate G4 Knowledge Fact + Evidence /
Seed preflight.

That task may validate and freeze:

- exact `ShrineKnowledgeSource` materialization plan;
- Fact `verification_status`;
- Fact `confidence`;
- Fact `verified_at`;
- Knowledge Seed structure;
- exact S4 / `ShrineSourceFact` inventory if included;
- isolated Evidence Gate usability.

It must preserve the frozen boundaries in this document and STOP if current contracts or fresh
Source evidence conflict with the packet.

## 18. Final state

```text
G2 nsrc-000004                 = PASS
G3 nsrc-000004                 = PASS / CURATION_RELEASE_CANDIDATE
G4 Source Packet Freeze        = PASS / FROZEN / G4_EVIDENCE_READY
G4 Knowledge Fact + Evidence   = NOT EXECUTED
G5 Shared Eligibility          = NOT EXECUTED
G6 Runtime QA                  = NOT EXECUTED
G7 Production Import           = NOT EXECUTED
G8 CORE READY                  = NOT REACHED
```

STOP at Source Packet Freeze.
