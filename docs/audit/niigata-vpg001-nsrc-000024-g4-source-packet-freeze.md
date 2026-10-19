# NIIGATA-001-VPG001 — nsrc-000024 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000024
candidate_name                = 秋葉神社
prefecture                    = 新潟県
fact_owner                    = 秋葉神社 / 新潟県新潟市秋葉区秋葉3丁目8番19号
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
G4_SOURCE_PACKET_SCOPE = { nsrc-000024 }
handoff_id             = NIIGATA-001-H006
```

Out of scope: nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE, G4 NOT_AUTHORIZED）and every other VPG001
candidate.

## 4. Fact owner freeze

```text
FACT_OWNER = 秋葉神社 = 新潟県新潟市秋葉区秋葉3丁目8番19号
identity / Base Shrine row = resolves exactly（Base Seed, PR #3273）
```

Explicitly not Fact owners: 10 other frozen 秋葉神社 rows and 2 秋葉社 rows（different addresses）; 秋葉山 / 秋葉信仰 in general.

```text
FACT_OWNER_FREEZE          = PASS
PROXIMITY_FACT_INHERITANCE = FORBIDDEN
```

## 5. Frozen Source identities

Semantic Source identity = `source_type + normalized URL`. Audit labels（S1, S2）are not Seed keys.

### S1

```text
audit_label         = S1
source_role         = D1 / D2 / D3 / H1 / H2 Primary Source
source_type         = government
title               = 文化資源ガイド（秋葉区）
publisher           = 新潟市
url                 = https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf
language            = ja
accessed_at         = 2026-10-19
verified_at         = 2026-10-19T14:35:38+09:00
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
bibliography        = NONE（not supplied; not invented）
page_locator        = NONE（not supplied; not invented）
```

Verified supported content（Mother Ship verification session）:

- 御祭神 = 大己貴神 / 大物主命 / 菅原道真公
- 桂家の守り神
- 昭和39年（1964）秋葉町内に移譲
- 平成25年（2013）創建250年
- 明治3年（1872）（chronology conflict, §8）

`source_type = government`（municipal document; precedent）.

## 6. Fact candidates

### 6.1 Deity

### D1 — 大己貴神

```text
fact_id             = D1
fact_type           = ShrineDeity
display_name        = 大己貴神
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### D2 — 大物主命

```text
fact_id             = D2
fact_type           = ShrineDeity
display_name        = 大物主命
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### D3 — 菅原道真公

```text
fact_id             = D3
fact_type           = ShrineDeity
display_name        = 菅原道真公
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### 6.2 History

### H1 — 桂家の守り神から秋葉町内への移譲

```text
fact_id             = H1
fact_type           = ShrineHistory
history_type        = historical_event
title               = 桂家の守り神から秋葉町内への移譲
content             = 秋葉神社は桂家の守り神であり、昭和39年（1964）に秋葉町内に移譲された。
period_text         = 昭和39年（1964）
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

```text
semantic_fact = S1 が、秋葉神社が桂家の守り神であったこと、昭和39年（1964）に秋葉町内に移譲されたことを記録していること
```

Do not add: who 桂家 were, the reason for the transfer, or an exact transfer date.

### H2 — 創建250年

```text
fact_id             = H2
fact_type           = ShrineHistory
history_type        = historical_event
title               = 創建250年
content             = 秋葉神社は平成25年（2013）に創建250年を迎えた。
period_text         = 平成25年（2013）
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

```text
semantic_fact = S1 が平成25年（2013）を創建250年として記録していること
```

The founding year is **not** derived from this（no 1763 / 宝暦13年 founding Fact）.

## 7. Fact ↔ Primary Source freeze

```text
S1 新潟市「文化資源ガイド（秋葉区）」
├─ D1 大己貴神
├─ D2 大物主命
├─ D3 菅原道真公
├─ H1 桂家の守り神から秋葉町内への移譲
└─ H2 創建250年

D1 / D2 / D3 / H1 / H2 -> S1 = YES
```

```text
Deity candidates = 3 / History candidates = 2
source-less candidate Fact = 0
```

## 8. Date precision boundary

```text
S1 writes 明治3年（1872）
明治3年 = 1870

CHRONOLOGY_CONFLICT = YES
adopted normalized year = NONE（neither 1870 nor 1872）
event_date from the pair = NONE
Fact depending on it = NONE
```

H1 / H2 era years and Gregorian years agree（昭和39 = 1964, 平成25 = 2013）. The conflict is localized.

```text
event_date = null for every frozen Fact
SOURCE_DATE_PRECISION >= STORED_DATE_PRECISION
DATE_FABRICATION = NONE
```

## 9. Excluded material

| material | reason |
|---|---|
| 明治3年（1872）の記載（社殿関連） | CHRONOLOGY_CONFLICT（明治3年 = 1870）; not corrected, not adopted, no event_date |
| 祭礼 / その他の地域史文脈 | the exact supported statement was not supplied; not paraphrased |
| 創建年（2013 − 250） | derived, not stated; not authorized |
| 主祭神 / 配祀の区別 | not supplied; `role = unknown` for all three |
| goriyaku / 火防・学業等のご利益 | not authorized; not inferred from deity attributes |

## 10. Result

```text
SOURCE_PACKET_FREEZE        = PASS
PACKET_STATE                = FROZEN
FACT_OWNER_FREEZE           = PASS
SOURCE_IDENTITY_CONFLICT    = 0
SOURCE_AMBIGUITY            = 0
SOURCE_LESS_CANDIDATE_FACTS = 0
CHRONOLOGY_CONFLICT         = YES
frozen Facts                = Deity 3 / History 2
NEXT_STATE                  = G4_EVIDENCE_READY
```

Not executed: Knowledge Seed materialization, Evidence Gate measurement, FORMAL_G4, G5–G8, Production import.
