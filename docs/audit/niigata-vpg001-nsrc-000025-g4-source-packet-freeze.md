# NIIGATA-001-VPG001 — nsrc-000025 G4 Source Packet Freeze

## 1. Status

```text
candidate_id                  = nsrc-000025
candidate_name                = 天津神社
prefecture                    = 新潟県
fact_owner                    = 天津神社 / 新潟県糸魚川市一の宮1丁目3番34号
upstream_G3                   = CURATION_RELEASE_CANDIDATE
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
G4_SOURCE_PACKET_SCOPE = { nsrc-000025 }
handoff_id             = NIIGATA-001-H014
```

Out of scope: nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE, G4 NOT_AUTHORIZED）and every other VPG001
candidate.

## 4. Fact owner freeze

```text
FACT_OWNER = 天津神社 = 新潟県糸魚川市一の宮1丁目3番34号
identity / Base Shrine row = resolves exactly（Base Seed, PR #3273）
```

Explicitly not Fact owners: **奴奈川神社**（same official page, same precinct, separate Fact owner）; 天津神社 / 上越市大字東京田34番地1（same-name row）.

```text
FACT_OWNER_FREEZE          = PASS
PROXIMITY_FACT_INHERITANCE = FORBIDDEN
```

## 5. Frozen Source identities

Semantic Source identity = `source_type + normalized URL`. Audit labels（S1, S2）are not Seed keys.

### S1

```text
audit_label         = S1
source_role         = D1 / D2 / D3 / H1–H5 Primary Source（天津神社-owned material only）
source_type         = shrine_official
title               = 御由緒・御祭神
publisher           = 天津神社・奴奈川神社
url                 = https://amatsujinja.com/story/
language            = ja
accessed_at         = 2026-10-19
verified_at         = 2026-10-19T14:35:38+09:00
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
bibliography        = NONE（not supplied; not invented）
page_locator        = NONE（not supplied; not invented）
```

Verified supported content（Mother Ship verification session）, 天津神社 side only:

- 天津神社 御祭神 = 天津彦々火瓊々杵尊 / 天児屋根命 / 天太玉命
- 第12代景行天皇の御代に創設されたという公式由緒
- 第36代孝徳天皇の勅願所という公式由緒
- 本殿 寛政9年（1797）建立
- 拝殿 寛文2年（1662）改築
- 幣殿 天明2年（1782）増築

The same page also carries 奴奈川神社 material（御祭神 奴奈川媛命 / 八千矛命）. That material is **not** part
of this packet.

The attribution of the 本殿 / 拝殿 / 幣殿 records to the 天津神社 side is the Mother Ship verification
result. The page covers a two-honden precinct, so this attribution is recorded as part of the frozen
ownership boundary.

## 6. Fact candidates

### 6.1 Deity

### D1 — 天津彦々火瓊々杵尊

```text
fact_id             = D1
fact_type           = ShrineDeity
display_name        = 天津彦々火瓊々杵尊
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### D2 — 天児屋根命

```text
fact_id             = D2
fact_type           = ShrineDeity
display_name        = 天児屋根命
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### D3 — 天太玉命

```text
fact_id             = D3
fact_type           = ShrineDeity
display_name        = 天太玉命
role                = unknown（the Source role is not frozen; not inferred）
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

### 6.2 History

### H1 — 景行天皇御代の創設（公式由緒）

```text
fact_id             = H1
fact_type           = ShrineHistory
history_type        = tradition
title               = 景行天皇御代の創設（公式由緒）
content             = 天津神社の公式由緒では、第12代景行天皇の御代に創設されたと伝えられている。
period_text         = 第12代景行天皇の御代
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

```text
semantic_fact = S1（神社公式）の由緒が、景行天皇の御代の創設を伝えていること
```

`tradition`: a legendary-era founding claim（knowledge contract: 伝承上の年代は `tradition` 側）. It is not a
`founding` Fact, and no year is derived.

### H2 — 孝徳天皇の勅願所（公式由緒）

```text
fact_id             = H2
fact_type           = ShrineHistory
history_type        = tradition
title               = 孝徳天皇の勅願所（公式由緒）
content             = 天津神社の公式由緒では、第36代孝徳天皇の勅願所であったとされている。
period_text         = 第36代孝徳天皇
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

```text
semantic_fact = S1（神社公式）の由緒が、孝徳天皇の勅願所であったとしていること
```

Kept as a Source assertion. It is not promoted to an independently proven historical fact.

### H3 — 本殿の建立

```text
fact_id             = H3
fact_type           = ShrineHistory
history_type        = historical_event
title               = 本殿の建立
content             = 天津神社の本殿は寛政9年（1797）に建立された。
period_text         = 寛政9年（1797）
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

Era / Gregorian year agree（寛政9 = 1797）.

### H4 — 拝殿の改築

```text
fact_id             = H4
fact_type           = ShrineHistory
history_type        = historical_event
title               = 拝殿の改築
content             = 天津神社の拝殿は寛文2年（1662）に改築された。
period_text         = 寛文2年（1662）
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

Era / Gregorian year agree（寛文2 = 1662）.

### H5 — 幣殿の増築

```text
fact_id             = H5
fact_type           = ShrineHistory
history_type        = historical_event
title               = 幣殿の増築
content             = 天津神社の幣殿は天明2年（1782）に増築された。
period_text         = 天明2年（1782）
event_date          = null
verification_status = source_confirmed（candidate）
confidence          = high（candidate）
verified_at         = 2026-10-19T14:35:38+09:00
Primary Source      = S1
```

Era / Gregorian year agree（天明2 = 1782）.

## 7. Fact ↔ Primary Source freeze

```text
S1 天津神社・奴奈川神社 公式サイト「御由緒・御祭神」
├─ D1 天津彦々火瓊々杵尊
├─ D2 天児屋根命
├─ D3 天太玉命
├─ H1 景行天皇御代の創設（公式由緒）
├─ H2 孝徳天皇の勅願所（公式由緒）
├─ H3 本殿の建立
├─ H4 拝殿の改築
└─ H5 幣殿の増築

D1–D3 / H1–H5 -> S1 = YES
```

```text
Deity candidates = 3 / History candidates = 5
source-less candidate Fact = 0
```

## 8. Date precision boundary

```text
CHRONOLOGY_CONFLICT = NO
H1 / H2 = legendary-era wording in period_text; no year derived
H3 / H4 / H5 era years agree with their Gregorian years
```

```text
event_date = null for every frozen Fact
SOURCE_DATE_PRECISION >= STORED_DATE_PRECISION
DATE_FABRICATION = NONE
```

## 9. Excluded material

| material | reason |
|---|---|
| 奴奈川媛命 | 奴奈川神社 Fact; not nsrc-000025 |
| 八千矛命 | 奴奈川神社 Fact; not nsrc-000025 |
| 奴奈川神社の由緒 / 歴史 | other Fact owner, even though it is on the same page |
| 舞楽 / けんか祭り（screening） | not in the supplied verified content of S1; not in this packet |
| 創建年（景行天皇の年代からの換算） | derived; not authorized |
| goriyaku | not authorized; not inferred from deity attributes |

```text
shared page            != shared Fact owner
shared precinct        != shared Fact owner
shared G2 anchor       != shared Fact owner
```

## 10. Result

```text
SOURCE_PACKET_FREEZE        = PASS
PACKET_STATE                = FROZEN
FACT_OWNER_FREEZE           = PASS
SOURCE_IDENTITY_CONFLICT    = 0
SOURCE_AMBIGUITY            = 0
SOURCE_LESS_CANDIDATE_FACTS = 0
CHRONOLOGY_CONFLICT         = NO
frozen Facts                = Deity 3 / History 5
NEXT_STATE                  = G4_EVIDENCE_READY
```

Not executed: Knowledge Seed materialization, Evidence Gate measurement, FORMAL_G4, G5–G8, Production import.
