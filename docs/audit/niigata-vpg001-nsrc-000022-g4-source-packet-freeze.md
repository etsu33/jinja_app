# NIIGATA-001-VPG001 — nsrc-000022 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000022
candidate_name                = 五十嵐神社
prefecture                    = 新潟県
fact_owner                    = 五十嵐神社 / 新潟県三条市大字飯田2283番地
upstream_G3                   = NORMAL_MODEL_FIT
PRODUCT_SURFACE               = RECOMMENDATION
G4_AUTHORIZATION              = AUTHORIZED_TO_START

SOURCE_PACKET_FREEZE          = PASS
PACKET_STATE                  = FROZEN
FACT_OWNER_FREEZE             = PASS
SOURCE_IDENTITY_CONFLICT      = 0
SOURCE_AMBIGUITY              = 0
SOURCE_LESS_CANDIDATE_FACTS   = 0
CHRONOLOGY_CONFLICT           = NO
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
G4_SOURCE_PACKET_SCOPE = { nsrc-000022 }
handoff_id             = NIIGATA-001-H019
```

Out of scope: nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE, G4 NOT_AUTHORIZED）and every other VPG001
candidate.

## 4. Fact owner freeze

```text
FACT_OWNER = 五十嵐神社 = 新潟県三条市大字飯田2283番地
identity / Base Shrine row = resolves exactly（Base Seed, PR #3273）
```

Explicitly not Fact owners: 八木神社（式内社 伊加良志神社 論社, screening only）; any shrine of the 下田郷 area not explicitly 五十嵐神社.

```text
FACT_OWNER_FREEZE          = PASS
PROXIMITY_FACT_INHERITANCE = FORBIDDEN
```

## 5. Frozen Source identities

Semantic Source identity = `source_type + normalized URL`. Audit labels（S1, S2）are not Seed keys.

### S1

```text
audit_label         = S1
source_role         = D1 Primary Source
source_type         = government
title               = 五十嵐神社
publisher           = 三条市
url                 = https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html
language            = ja
accessed_at         = 2026-10-19
verified_at         = 2026-10-19T14:35:38+09:00
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
bibliography        = NONE（not supplied; not invented）
page_locator        = NONE（not supplied; not invented）
```

Verified supported content（Mother Ship verification session）:

- 御祭神 = 五十日帯日子命（exact spelling; not normalized to 五十日帯彦命）
- 越国 / 頸城 / 上田郷 / 下田郷の開拓伝承
- 飯田宮沢 / 舞鶴の丘への埋葬伝承
- 江戸期「若一王子」
- 安産信仰
- 明治期「御陵墓伝説地」
- framing wording such as 「といわれています」

## 6. Fact candidates

### 6.1 Deity

### D1 — 五十日帯日子命

```text
fact_id             = D1
fact_type           = ShrineDeity
display_name        = 五十日帯日子命
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### 6.2 History

No History Fact is frozen in this packet（see §9）.

## 7. Fact ↔ Primary Source freeze

```text
S1 三条市「五十嵐神社」
└─ D1 五十日帯日子命

D1 -> S1 = YES
```

```text
Deity candidates = 1 / History candidates = 0
source-less candidate Fact = 0
```

## 8. Date precision boundary

```text
CHRONOLOGY_CONFLICT = NO
dated Fact in this packet = NONE
```

```text
event_date = null for every frozen Fact
SOURCE_DATE_PRECISION >= STORED_DATE_PRECISION
DATE_FABRICATION = NONE
```

## 9. Excluded material

| material | reason |
|---|---|
| 越国 / 頸城 / 上田郷 / 下田郷の開拓伝承 | exact Source sentence not in packet; its 「といわれています」 modality and narrative structure cannot be reproduced from a topic label |
| 飯田宮沢 / 舞鶴の丘への埋葬伝承 | same |
| 江戸期「若一王子」 | same（whether it is a name, a 社号 or a 呼称, and its modality, are not in the packet） |
| 安産信仰 | same; also benefit-adjacent, so it must not become goriyaku |
| 明治期「御陵墓伝説地」 | same（who recorded it, and its wording, are not in the packet） |
| 式内社 伊加良志神社 比定 / 治水・農耕 | screening-only（secondary sources）; not in the accepted Source packet |

These five Source-backed topics are **deferred, not rejected**. Each can be added as a `tradition`（or other
correct type）History Fact by a packet amendment that freezes the exact Source sentence.

## 10. Result

```text
SOURCE_PACKET_FREEZE        = PASS
PACKET_STATE                = FROZEN
FACT_OWNER_FREEZE           = PASS
SOURCE_IDENTITY_CONFLICT    = 0
SOURCE_AMBIGUITY            = 0
SOURCE_LESS_CANDIDATE_FACTS = 0
CHRONOLOGY_CONFLICT         = NO
frozen Facts                = Deity 1 / History 0
NEXT_STATE                  = G4_EVIDENCE_READY
```

Not executed: Knowledge Seed materialization, Evidence Gate measurement, FORMAL_G4, G5–G8, Production import.
