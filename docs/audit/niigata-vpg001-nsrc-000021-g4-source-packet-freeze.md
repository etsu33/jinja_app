# NIIGATA-001-VPG001 — nsrc-000021 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000021
candidate_name                = 荒川神社
prefecture                    = 新潟県
fact_owner                    = 荒川神社 / 新潟県胎内市桃崎浜187番地
upstream_G3                   = NORMAL_MODEL_FIT
PRODUCT_SURFACE               = RECOMMENDATION
G4_AUTHORIZATION              = AUTHORIZED_TO_START

SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
FACT_OWNER_FREEZE             = PASS
SOURCE_IDENTITY_CONFLICT      = 0
SOURCE_AMBIGUITY              = 0
SOURCE_LESS_CANDIDATE_FACTS   = 0
CHRONOLOGY_CONFLICT           = YES
NEXT_STATE                    = G4_EVIDENCE_READY

G4_KNOWLEDGE_FACT_EVIDENCE    = NOT_EXECUTED
FACT_READY                    = NO
G5                            = NOT_EXECUTED
PRODUCTION_WRITE              = NONE
```

```text
SOURCE_PACKET_FREEZE = PASS
!= FORMAL_G4 PASS
!= FACT_READY
!= G5 PASS / Recommendation eligible
!= Production imported
!= CORE_READY
```

This freeze creates no Knowledge row, no Knowledge Seed, no Evidence Gate result, no Candidate Master
change and no Production write.

## 2. Execution context

```text
audit_date            = 2026-10-19
base                  = develop@4219c2f552971d6cf21eb978b00b542cf40bff92
branch                = audit/niigata-vpg001-g4-source-packet-freeze
verification_session  = Mother Ship verified Source session
accessed_at           = 2026-10-19
verified_at           = 2026-10-19T14:35:38+09:00（Source verification session time; not a publication time）
evidence_level        = MOTHER_SHIP_SUPPLIED（this environment cannot reach the Source hosts; the
                        verified content below is recorded exactly as supplied, not re-fetched）
```

Upstream authority:

- `docs/audit/niigata-vpg001-g1-identity-duplicate.md`
- `docs/audit/niigata-vpg001-g2-position-review.md`
- `docs/audit/niigata-vpg001-g3-source-knowledge-fit.md`
- `docs/audit/niigata-vpg001-base-shrine-materialization.md`
- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/fact-source-citation-contract.md`

## 3. Scope

```text
G4_SOURCE_PACKET_SCOPE = { nsrc-000021 }
handoff_id             = NIIGATA-001-H015
```

Out of scope: nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE, G4 NOT_AUTHORIZED）and every other VPG001
candidate.

## 4. Fact owner freeze

```text
FACT_OWNER = 荒川神社 = 新潟県胎内市桃崎浜187番地
identity / Base Shrine row = resolves exactly（Base Seed, PR #3273）
```

Explicitly not Fact owners: 荒川神社 / 新発田市荒川5431番地, 荒川神社 / 村上市小岩内463番地, 荒川神社 / 村上市荒川542番地（Frozen Ready Set same-name rows）.

```text
FACT_OWNER_FREEZE          = PASS
PROXIMITY_FACT_INHERITANCE = FORBIDDEN
```

## 5. Frozen Source identities

Semantic Source identity = `source_type + normalized URL`. Audit labels（S1, S2）are not Seed keys.

### S1

```text
audit_label         = S1
source_role         = D1 / H1 Primary Source
source_type         = government
title               = 北前船の魅力を訪ねて
publisher           = 新潟県
url                 = https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html
language            = ja
accessed_at         = 2026-10-19
verified_at         = 2026-10-19T14:35:38+09:00
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
bibliography        = NONE（not supplied; not invented）
page_locator        = NONE（not supplied; not invented）
```

Verified supported content（Mother Ship verification session）:

- 御祭神 = 天鈿女命
- 桃崎浜 / 北前船に関する神社固有の文脈
- 船主が航海安全を祈願して船絵馬を奉納
- 船絵馬86枚
- 荒川神社 / 模型和船に関する文化的文脈
- 建築年代の記載: 天保12年（1814年）（chronology conflict, §8）

### S2

```text
audit_label         = S2
source_role         = chronology-conflict evidence only（no Fact relation in this packet）
source_type         = government
title               = NOT_SUPPLIED（G3 label: 新潟県 cultural-property material）
publisher           = 新潟県
url                 = https://www.pref.niigata.lg.jp/uploaded/attachment/180012.pdf
language            = ja
accessed_at         = 2026-10-19
verified_at         = 2026-10-19T14:35:38+09:00
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
bibliography        = NONE（not supplied; not invented）
page_locator        = NONE（not supplied; not invented）
```

Verified supported content（Mother Ship verification session）:

- 荒川神社本殿・拝殿及び幣殿
- 建築年代 = 天保12年（1841）

The URL is the G3-accepted S2（`docs/audit/niigata-vpg001-g3-source-knowledge-fit.md` §3.1）. Its exact title
was not supplied. S2 has no Fact relation in this packet, so the missing title blocks nothing here. It must
be recorded before S2 is used as a Fact Source.

`source_type = government`: repository precedent uses `cultural_property` only for 文化庁 heritage-database
pages. Prefectural and municipal documents are `government`.

## 6. Fact candidates

### 6.1 Deity

### D1 — 天鈿女命

```text
fact_id             = D1
fact_type           = ShrineDeity
display_name        = 天鈿女命
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### 6.2 History

### H1 — 船主による船絵馬の奉納

```text
fact_id             = H1
fact_type           = ShrineHistory
history_type        = regional_context
title               = 船主による船絵馬の奉納
content             = 荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。
period_text         = ""
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

```text
semantic_fact = S1 が、船主の航海安全祈願による船絵馬奉納と、その数 86枚を荒川神社について記録していること
```

Do not add: a benefit / goriyaku meaning, a dating of the votives, a claim about all 北前船 ports, or any
construction year.

## 7. Fact ↔ Primary Source freeze

```text
S1 新潟県「北前船の魅力を訪ねて」
├─ D1 天鈿女命
└─ H1 船主による船絵馬の奉納

S2 新潟県 cultural-property material
└─ （no Fact; chronology-conflict evidence only）

D1 -> S1 = YES    D1 -> S2 = NO
H1 -> S1 = YES    H1 -> S2 = NO
```

```text
Deity candidates = 1 / History candidates = 1
source-less candidate Fact = 0
```

## 8. Date precision boundary

```text
S1  天保12年（1814年）
S2  天保12年（1841）
天保12年 = 1841

CHRONOLOGY_CONFLICT = YES
adopted normalized year = NONE（neither 1814 nor 1841）
Fact depending on the year = NONE
```

The conflict is localized. H1 and D1 do not depend on it.

```text
event_date = null for every frozen Fact
SOURCE_DATE_PRECISION >= STORED_DATE_PRECISION
DATE_FABRICATION = NONE
```

## 9. Excluded material

| material | reason |
|---|---|
| 本殿・拝殿及び幣殿の建築年代（天保12年 1814 / 1841） | CHRONOLOGY_CONFLICT across S1 / S2; no normalized year is adopted |
| 荒川神社 / 模型和船の文化的文脈 | the exact supported statement was not supplied; not paraphrased |
| 文化財指定・登録の区分 | only the conflicted building year was supplied for S2; designation details not supplied |
| 桃崎浜 / 北前船の一般的な寄港史 | not shrine-specific beyond H1; no proximity inheritance |
| goriyaku / 航海安全のご利益化 | not authorized; H1 records an act of prayer, not a benefit |

## 10. Result

```text
SOURCE_PACKET_FREEZE        = PASS
PACKET_STATE                = FROZEN
FACT_OWNER_FREEZE           = PASS
SOURCE_IDENTITY_CONFLICT    = 0
SOURCE_AMBIGUITY            = 0
SOURCE_LESS_CANDIDATE_FACTS = 0
CHRONOLOGY_CONFLICT         = YES
frozen Facts                = Deity 1 / History 1
NEXT_STATE                  = G4_EVIDENCE_READY
```

Not executed: Knowledge Seed materialization, Evidence Gate measurement, FORMAL_G4, G5–G8, Production import.
