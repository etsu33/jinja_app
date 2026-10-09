# NIIGATA-001-H001 — nsrc-000004 G4 Evidence Preflight

## 1. Status

~~~text
G4_EVIDENCE_PREFLIGHT = HOLD
reason_code            = BASE_SHRINE_NOT_MATERIALIZED

EVIDENCE_SEMANTIC_READINESS = PASS
KNOWLEDGE_PAYLOAD_DESIGN    = PASS
G4_ISOLATION                = PASS
KNOWLEDGE_IMPORT_READY      = HOLD
FORMAL_G4_PASS              = NOT YET
~~~

- Recorded at: 2026-10-09
- Candidate: nsrc-000004 / 青海神社（新潟県加茂市）
- Branch: audit/nsrc-000004-g4-evidence-preflight
- Base: develop@3724f2bb9ebe2f0f785a52c960d18c08d9d4d4e5
- Upstream Source Packet: docs/audit/niigata-h001-g4-source-packet-freeze.md
- Upstream G3: PASS / CURATION_RELEASE_CANDIDATE
- Production write: NONE
- G5 / G6 / G7 / G8: NOT EXECUTED

本書は Source Packet Freeze 後の G4 Knowledge Fact + Evidence / Seed Preflight を固定する。
Source Packet が PASS であることを、Knowledge import ready または G4 PASS と同一視しない。

---

## 2. Governing authority

- docs/knowledge/shrine-expansion-gate-contract.md §7 G4 Knowledge Fact + Evidence Gate
- docs/knowledge/shrine-knowledge-contract.md
- backend/temples/services/evidence_gate.py
- backend/temples/services/knowledge_seed.py
- backend/temples/management/commands/import_shrine_knowledge.py
- backend/temples/models.py
- docs/knowledge/shrine-expansion-candidate-master-contract.md
- docs/knowledge/shrine-position-contract.md

G4 PASS条件:

~~~text
- Fact ownerがG1/G3と一致
- source-less Fact = 0
- Source identity conflict = 0
- Fact / Source verificationが契約に適合
- Evidence Gateで少なくとも1件のusable DeityまたはHistoryを作れる
- 伝承を確定史実へ昇格させない
- AI生成のみをconfirmed Sourceとして扱わない
~~~

G4 STOP条件:

~~~text
- SOURCE_REUSE_CONFLICT / AMBIGUOUS
- Shrine NOT_FOUND / IMPORT_IDENTITY_AMBIGUOUS
- Source不十分
- FactがSource本文を越えている
- Model RiskをFact本文で隠している
~~~

---

## 3. Execution scope

~~~text
G4_EVIDENCE_SCOPE = { nsrc-000004 }
~~~

対象外:

| candidate_id | Shrine | Current state |
|---|---|---|
| nsrc-000001 | 相吉神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000002 | 青澤神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000003 | 蒼柴神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000005 | 青山稲荷神社 | G2 HOLD_POSITION_REVIEW |

4社について G3 / G4 は実行しない。

---

## 4. Candidate identity and ownership boundary

G1 / G3 authority:

~~~text
candidate_id       = nsrc-000004
official_name      = 青海神社
G1 identity        = 加茂市大字加茂字宮山229番地
duplicate_status   = SAME_NAME_DIFFERENT_SHRINE
G3                 = PASS
G3 classification  = CURATION_RELEASE_CANDIDATE
Fact owner         = 青海神社（加茂市）
~~~

同名の糸魚川市の青海神社とは別identityである。

Deity owner boundary:

~~~text
INCLUDE in nsrc-000004 ShrineDeity:
- 椎根津彦命
- 大国魂命

EXCLUDE:
賀茂神社:
- 賀茂別雷命

賀茂御祖神社:
- 多多須玉依媛命
- 賀茂建角身命
~~~

共有された歴史事象は、共有Fact ownershipまたはDeity owner移転を意味しない。

---

## 5. Knowledge Source materialization set

~~~text
KNOWLEDGE_SOURCE_MATERIALIZATION = { S1, S2, S4 }

S3 = provenance-only
     Knowledge Seed materialization対象外
~~~

### S1 — AOMI_OFFICIAL_DEITY

~~~text
source_type         = shrine_official
title               = 御祭神｜青海神社公式サイト｜新潟県加茂市鎮座
publisher           = 青海神社
url                 = https://www.aomi-jinjya.or.jp/history/gosaisin.html
language            = ja
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:09:11+09:00
verification_status = source_confirmed
confidence          = high
~~~

S1 supports D1 / D2 directly.

### S2 — AOMI_OFFICIAL_HISTORY

~~~text
source_type         = shrine_official
title               = 由緒,年表｜青海神社公式サイト｜新潟県加茂市鎮座
publisher           = 青海神社
url                 = https://www.aomi-jinjya.or.jp/history/yuisyo.html
language            = ja
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:09:11+09:00
verification_status = source_confirmed
confidence          = high
~~~

S2 supports H1 / H2 directly.

### S3 — NIIGATA_JINJACHO_DIRECTORY

~~~text
source_type = government
publisher   = 新潟県神社庁
url         = https://niigata-jinjacho.jp/shrine_niigata/search.php
~~~

government はrepository enum compatibility値であり、行政機関であることを意味しない。
S3はidentity / listing provenanceに使用し、D/H Primary Sourceとしてrelationしない。

### S4 — AOMI_OFFICIAL_PRAYER_GUIDE

~~~text
source_type         = shrine_official
title               = 御祈祷種類｜青海神社公式サイト｜新潟県加茂市鎮座
publisher           = 青海神社
url                 = https://www.aomi-jinjya.or.jp/gokitou/syurui.html
bibliography        = ""
accessed_at          = 2026-10-09
verified_at          = 2026-10-09T12:35:59+09:00
verification_status = source_confirmed
confidence          = high
language            = ja
note                = ""
~~~

URL-backed Source semantic identity:

~~~text
source_type + normalized URL
~~~

source_id_candidate はaudit labelであり、semantic identityではない。

---

## 6. Deity Fact freeze

### D1 椎根津彦命

~~~text
display_name         = 椎根津彦命
reading              = しいねつひこのみこと
canonical_name       = NOT FROZEN
role                 = unknown
verification_status  = source_confirmed
confidence           = high
verified_at          = 2026-10-09T12:40:22+09:00
Primary Source       = S1
~~~

### D2 大国魂命

~~~text
display_name         = 大国魂命
reading              = おおくにたまのみこと
canonical_name       = NOT FROZEN
role                 = unknown
verification_status  = source_confirmed
confidence           = high
verified_at          = 2026-10-09T12:41:49+09:00
Primary Source       = S1
~~~

公式Sourceは奉斎を確認するが、主祭神 / 配祀 / 相殿等の序列を明示しない。
そのため role=unknown を維持する。

---

## 7. History Fact freeze

### H1 神亀3年の創建

~~~text
history_type         = founding
title                = 神亀3年の創建
content              = 神亀3年（726）、青海首一族が加茂山山麓に青海神社を創建した。
period_text          = 神亀3年（726）
event_date           = null
verification_status  = source_confirmed
confidence           = high
verified_at          = 2026-10-09T12:42:36+09:00
Primary Source       = S2
~~~

このFactは現在地での創建、現在の建物、三社合殿構造が726年に存在したことを意味しない。

### H2 明治5年の三社本殿合殿

~~~text
history_type         = historical_event
title                = 明治5年の三社本殿合殿
content              = 明治5年（1872）、青海・賀茂・御祖三社本殿を現在地に合殿した。
period_text          = 明治5年（1872）
event_date           = null
verification_status  = source_confirmed
confidence           = high
verified_at          = 2026-10-09T12:43:46+09:00
Primary Source       = S2
~~~

H2は遷座、法人・宗教的entity統合、Deity owner移転、現在建物の1872年新築を意味しない。

---

## 8. D/H Fact-Source relation

~~~text
D1 椎根津彦命           -> S1
D2 大国魂命             -> S1
H1 神亀3年の創建         -> S2
H2 明治5年の三社本殿合殿 -> S2
~~~

~~~text
current adopted D/H Fact count = 4
source-less D/H Fact count     = 0
~~~

S3へのrelationは作らない。

---

## 9. Evidence Gate preflight

現行 decide_fact_usability() の usable=True 条件:

~~~text
Fact verification_status in {source_confirmed, reviewed}
AND
at least one related Source verification_status in {source_confirmed, reviewed}
~~~

Preflight result:

| Fact | Fact status | Source | Source status | Expected usability |
|---|---|---|---|---|
| D1 椎根津彦命 | source_confirmed | S1 | source_confirmed | usable=True |
| D2 大国魂命 | source_confirmed | S1 | source_confirmed | usable=True |
| H1 神亀3年の創建 | source_confirmed | S2 | source_confirmed | usable=True |
| H2 明治5年の三社本殿合殿 | source_confirmed | S2 | source_confirmed | usable=True |

~~~text
usable Deity candidate  = 2 / 2
usable History candidate = 2 / 2
usable total candidate   = 4 / 4
~~~

これはpayload preflightであり、DB materialization後の実測値ではない。

---

## 10. S4 ShrineSourceFact wording freeze

S4からmaterializeするSource Factは11件。

| # | source_attested_wording | stable_key |
|---|---|---|
| SF01 | 家内安全 | aomi_jinja_kamo__prayer__kanai_anzen |
| SF02 | 子授祈願 | aomi_jinja_kamo__prayer__kosazuke_kigan |
| SF03 | 安産祈願 | aomi_jinja_kamo__prayer__anzan_kigan |
| SF04 | 交通安全 | aomi_jinja_kamo__prayer__kotsu_anzen |
| SF05 | 厄祓 | aomi_jinja_kamo__prayer__yakubarai |
| SF06 | 方位祓 | aomi_jinja_kamo__prayer__hoi_barai |
| SF07 | 病気平癒祈願 | aomi_jinja_kamo__prayer__byoki_heiyu_kigan |
| SF08 | 身の安全祈願 | aomi_jinja_kamo__prayer__mi_no_anzen_kigan |
| SF09 | 合格祈願 | aomi_jinja_kamo__prayer__gokaku_kigan |
| SF10 | 商売繁盛 | aomi_jinja_kamo__prayer__shobai_hanjo |
| SF11 | 必勝祈願 | aomi_jinja_kamo__prayer__hissho_kigan |

Common Fact metadata:

~~~text
evidence_characterization = official_prayer_supported
verification_status       = source_confirmed
confidence                = high
verified_at               = 2026-10-09T13:14:51+09:00
Primary Source            = S4
~~~

stable_key policy:

~~~text
{shrine_slug}__{fact_type}__{fact_slug}

shrine_slug = aomi_jinja_kamo
fact_type   = prayer
~~~

stable_keyは明示identityであり、runtimeでwordingから生成しない。
canonical GoriyakuTag / Need / Mapping Registry resultをstable_keyへ埋め込まない。

---

## 11. Goriyaku boundary

~~~text
official prayer wording
!= KAMIMUSUBI goriyaku_tags
~~~

このG4 preflightでは以下を行わない。

~~~text
Shrine.goriyaku update             = NONE
Shrine.goriyaku_tags write         = NONE
GoriyakuTag create/update          = NONE
ShrineGoriyakuAssignment write     = NONE
canonical concept mapping          = NONE
Need mapping                       = NONE
Recommendation score write         = NONE
~~~

Source Fact -> canonical concept mappingはMapping Registryの別責務とする。

---

## 12. Knowledge Seed payload preflight

Candidate payload shape:

~~~text
schema_version = 1.2

Sources       = 3   (S1 / S2 / S4)
Shrines       = 1
Deities       = 2
Histories     = 2
SourceFacts   = 11
Collectives   = 0
~~~

Semantic relations:

~~~text
D1 / D2 -> S1
H1 / H2 -> S2
SF01-SF11 -> S4
~~~

S3はSeedへmaterializeしない。

Payload structureとしては現行schema 1.2で表現可能である。

---

## 13. Base Shrine / shrine_ref prerequisite freeze

Current develop Base Seed:

~~~text
青海神社（加茂市） row = ABSENT
~~~

Base Shrine identityは次でfreezeする。

~~~text
name_jp        = 青海神社
address        = 新潟県加茂市大字加茂字宮山229番地
latitude       = 37.65657387
longitude      = 139.0536436
goriyaku       = ""
goriyaku_tags  = KEY ABSENT
kyusei         = null
astro_elements = []
visit_style_tags = KEY ABSENT
location.lat   = 37.65657387
location.lng   = 139.0536436
~~~

住所はG1 canonical identityへ新潟県を前置した、nsrc-000004限定のBase Seed decision。
公式visitor pageの短い表記「新潟県加茂市大字加茂229番地」へidentityを書き換えない。

Knowledge Seed shrine_ref:

~~~text
name_jp = 青海神社
address = 新潟県加茂市大字加茂字宮山229番地
~~~

Base SeedとKnowledge Seedでexact identityを一致させる。

---

## 14. Import blocker

現行 import_shrine_knowledge は既存Shrineを先にresolveする。

Current developではBase Shrineが存在しないため、Knowledge Seedだけをimportすると:

~~~text
Shrine NOT_FOUND
~~~

になる。

Shrine NOT_FOUNDはG4 ContractのSTOP条件である。

したがって:

~~~text
KNOWLEDGE_PAYLOAD_STRUCTURAL_PREFLIGHT = PASS
KNOWLEDGE_IMPORT_READY                  = HOLD
G4_EVIDENCE_PREFLIGHT                   = HOLD
~~~

HOLD理由はEvidence不足ではない。

~~~text
reason_code = BASE_SHRINE_NOT_MATERIALIZED
~~~

---

## 15. Isolation verification

G4 Source Packet merge commit 3724f2bb9ebe2f0f785a52c960d18c08d9d4d4e5 と current develop を比較。

### Candidate Master

~~~text
backend/temples/data/shrine_expansion_candidate_master.json
diff = 0
~~~

nsrc-000004は以下を維持:

~~~text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
build_batch            = null
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
identity_status        = CONFIRMED
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
~~~

### G2 HOLD 4 candidates

G2 gate文書および4 Position Resolution Recordはbaselineとcurrent developでexact match。

~~~text
nsrc-000001 = HOLD_POSITION_REVIEW / diff 0
nsrc-000002 = HOLD_POSITION_REVIEW / diff 0
nsrc-000003 = HOLD_POSITION_REVIEW / diff 0
nsrc-000005 = HOLD_POSITION_REVIEW / diff 0
~~~

### Production

~~~text
Production write = NONE
~~~

本preflightでProduction DBへのcreate/update/importを実行していない。

---

## 16. G4 acceptance matrix

| G4 condition | Result | Note |
|---|---|---|
| Fact ownerがG1/G3と一致 | PASS | 青海神社（加茂市） |
| source-less Fact = 0 | PASS | adopted D/H 4件 |
| Source identity conflict = 0 | PARTIAL | repository-known collision 0、isolated DB実測未実施 |
| Fact / Source verification適合 | PASS | D1/D2/H1/H2 + S1/S2 |
| usable Deity / History >= 1 | PASS in deterministic preflight | expected 4/4、DB実測前 |
| 伝承を確定史実へ昇格させない | PASS | H1/H2 boundary維持 |
| AIのみをconfirmed Source扱いしない | PASS | official Sources使用 |
| Ranking / Score isolation | PASS | changeなし |
| Candidate identity isolation | PASS | Candidate Master diff 0 |
| G2 HOLD isolation | PASS | 4社diff 0 |
| Shrine resolve | HOLD | Base Shrine未materialize |

STOP condition review:

~~~text
SOURCE_REUSE_CONFLICT / AMBIGUOUS = NOT OBSERVED IN REPOSITORY
Shrine NOT_FOUND risk              = ACTIVE
Source insufficient                = NO
Fact exceeds Source                = NO
Hidden Model Risk                  = NO
~~~

---

## 17. Final classification

~~~text
G4_EVIDENCE_PREFLIGHT
= HOLD / READY_FOR_DATA_MATERIALIZATION_REENTRY

BLOCKER
= BASE_SHRINE_NOT_MATERIALIZED

Evidence semantic readiness
= PASS

Knowledge payload design
= PASS

Isolation
= PASS

Formal G4
= NOT YET PASS
~~~

このHOLDをEvidence不足として扱わない。
Base Shrine materialization後にisolated DB preflightで実測し、G4へre-entryする。

---

## 18. Re-entry contract

次の実装PRでは最低限以下を実施する。

~~~text
1. nsrc-000004 Base Shrine row materialization
2. Knowledge Seed schema 1.2 materialization
3. isolated DBへBase Seed import
4. Base identity exactly 1 row確認
5. Knowledge Seed --validate-only
6. Knowledge Seed --dry-run
7. Knowledge apply
8. Shrine NOT_FOUND = 0
9. IMPORT_IDENTITY_AMBIGUOUS = 0
10. SOURCE_REUSE_CONFLICT / AMBIGUOUS = 0
11. source-less D/H Fact = 0
12. Evidence Gate actual usable Deity / History >= 1
13. SourceFact 11件 relation / idempotency確認
14. goriyaku_tags direct write = 0
~~~

その実測後にのみFormal G4 PASSを再判定する。

---

## 19. Not changed / Not executed

~~~text
Candidate Master                      UNCHANGED
G2 HOLD four                          UNCHANGED
Base Seed                             UNCHANGED
Knowledge Seed                        NOT CREATED
Production DB                         NOT WRITTEN
goriyaku_tags                         UNCHANGED
GoriyakuTag                           UNCHANGED
ShrineGoriyakuAssignment              UNCHANGED
Mapping Registry                      UNCHANGED
Recommendation / Ranking / Score      UNCHANGED
Compass                               UNCHANGED
G5 / G6 / G7 / G8                     NOT EXECUTED
~~~

---

## 20. Completion checklist

- [x] developがPR #3127 merge後の最新状態であることを確認
- [x] PR #3127のSource PacketをG4入力正本として固定
- [x] nsrc-000004のみをG4 Evidence対象として固定
- [x] S1 / S2 / S3 / S4のmaterialization対象を確認
- [x] S4のaccessed_atを実確認
- [x] S4のverified_atを実時刻でfreeze
- [x] S4のSource identity metadataを最終freeze
- [x] D1 / D2 Fact verification metadataをfreeze
- [x] H1 / H2 Fact verification metadataをfreeze
- [x] D1 / D2 -> S1 relationをEvidence Gate観点で確認
- [x] H1 / H2 -> S2 relationをEvidence Gate観点で確認
- [x] source-less Factが0件になることを確認
- [x] S4から作るShrineSourceFactの対象wordingをfreeze
- [x] ShrineSourceFact stable_key方針をfreeze
- [x] goriyaku_tagsへ直接書き込まないことを確認
- [x] S1 / S2 Source-level verification metadataをfreeze
- [x] Evidence Gateでusable Deity / Historyを最低1件作れることを確認
- [x] Knowledge Seed payload候補をpreflight
- [x] S4由来11 ShrineSourceFactのverification metadataをfreeze
- [x] nsrc-000004のBase Shrine / shrine_ref import prerequisiteを確定
- [x] Candidate Masterを変更しない
- [x] G2 HOLD 4社を変更しない
- [x] Production writeを行わない
- [x] G4 Evidence PreflightをPASS / HOLDで確定
- [x] 監査文書を作成
- [x] STOP

---

## STOP

~~~text
STOP

Do not materialize Base Seed or Knowledge Seed in this audit PR.
Do not execute G5.
Do not write Production.
Next work item is a separate data-materialization / isolated-preflight PR.
~~~
