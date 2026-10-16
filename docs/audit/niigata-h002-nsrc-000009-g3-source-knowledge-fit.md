# NIIGATA-001-H002 nsrc-000009 赤城社 G3 Source + Knowledge Model Fit

> Status: **PASS — NORMAL_MODEL_FIT**
>
> Recorded at: 2026-10-16
>
> Candidate: `nsrc-000009` / 赤城社（新潟県十日町市伊達乙48番地）
>
> G0: PASS
>
> G1: PASS / `SAME_NAME_DIFFERENT_SHRINE`
>
> G2: CLOSED / PASS
>
> Production write: 0
>
> Candidate Master write: 0
>
> Base Seed write: 0
>
> Knowledge Seed write: 0
>
> G4 execution: 0
>
> Mother Ship G3 decision: **A / PASS / NORMAL_MODEL_FIT**

## Scope

Execute G3 Source + Knowledge Model Fit for `nsrc-000009` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

This task evaluates Source quality, Fact ownership, current Deity boundary, and model fit.

It does not create `ShrineKnowledgeSource`, `ShrineDeity`, `ShrineHistory`, Candidate Master rows, or Production data.

---

## Upstream frozen identity / position

Canonical identity:

```text
candidate_id     = nsrc-000009
official_name    = 赤城社
reading          = あかぎしゃ
official_address = 新潟県十日町市伊達乙48番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

G2 adopted Visitor / Navigation Anchor:

```text
position_status = PASS
latitude        = 37.089683
longitude       = 138.748108
source_type     = Google Maps target marker manual QA
verified_at     = 2026-10-16
```

G3 does not modify identity or coordinate.

---

## Accepted Source Set

### S1 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher   = 新潟県神社庁
url         = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50
verified_on = 2026-10-16
```

Observed current identity:

```text
name    = 赤城社
reading = あかぎしゃ
address = 十日町市伊達乙48番地
```

The repository convention normalizes prefectural Jinja-cho Sources to `government` because the
current Source enum has no shrine-association value. This is an enum compatibility classification,
not a claim that the publisher is a government agency.

S1 is accepted for current identity / address provenance.

S1 does not expose a current Deity set or historical packet.

---

### S2 — 十日町市「歴史文化基本構想 資料集」

```text
source_type = government
publisher   = 十日町市
url         = https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
verified_on = 2026-10-16
bibliography = 中魚沼郡誌上 p.445
```

Observed shrine-specific historical material:

```text
赤城社
祭神：大山祇命
水沢村字天池にあり
天明3年8月の創立
大正2年改築
```

S2 is accepted as historical municipal Knowledge evidence.

The Deity wording is historical Source evidence only.
S2 does not establish the complete 2026 current Deity set.

---

### S3 — 新潟県 current locality corroboration

Current prefectural material identifies `天池` within `十日町市伊達乙`.

Observed current evidence includes:

```text
river observation point:
name     = 天池
location = 十日町市伊達乙

landslide-designation locality:
name     = 天池
location = 十日町市伊達乙
```

Sources:

```text
https://www.pref.niigata.lg.jp/site/tokamachi-seibi/suiidata.html
https://www.sabou-niigata.jp/dosyahou/files/5036_1_20130123135440.pdf
```

S3 is not adopted as a Shrine History Source.
It is used only to explain the locality bridge:

```text
historical 水沢村字天池
-> current 天池 locality
-> 十日町市伊達乙
```

---

## Fact owner

Fact ownership proposal:

```text
FACT_OWNER
= nsrc-000009
= 赤城社 / 新潟県十日町市伊達乙48番地
```

Evidence chain:

1. S1 identifies the current target as `赤城社 / 十日町市伊達乙48番地`.
2. S2 identifies a historical `赤城社` at `水沢村字天池`.
3. S3 establishes that current `天池` locality is in `十日町市伊達乙`.
4. H002 contains no second 赤城社 in the same `伊達乙` locality.
5. G1 already distinguishes the 四日町2534 / 上組2059番地子 siblings.

Therefore the historical S2 entry can be attributed to nsrc-000009 without name-only inference.

Explicit exclusions:

- 赤城社 / 十日町市四日町2534番地
- 赤城社 / 十日町市上組2059番地子
- 赤城社 / 南魚沼市芹田79番地
- other shrines in historical 水沢村 material
- generic 赤城 / Akagi shrine traditions

```text
SAME_NAME != SAME_FACT_OWNER
LOCALITY_BRIDGE + CURRENT_IDENTITY = REQUIRED
```

---

## Current Deity boundary

S2 historically records:

```text
祭神 = 大山祇命
```

This is accepted only as historical evidence.

No accepted current Source reviewed in this G3 execution directly confirms the complete 2026 current Deity set.

Therefore:

```text
HISTORICAL_DEITY_EVIDENCE = 大山祇命
CURRENT_DEITY_CONFIRMED    = NO
CURRENT_DEITY              = NOT_FROZEN

SHRINE_DEITY_ROWS_AUTHORIZED = 0
```

Do not infer current continuity from the historical record.

Do not infer a current Deity from the shrine name or generic Akagi tradition.

---

## Accepted History candidates

G3 freezes candidate shapes only. Exact G4 wording remains G4 responsibility.

### H1 — 天明3年8月の創立記録

```text
fact_type       = ShrineHistory
history_type    = historical_event
fact_owner      = nsrc-000009
accepted_source = S2

title_candidate = 天明3年8月の創立記録
period_text     = 天明3年8月
event_date      = null
```

The Source gives month-level historical wording only.
Do not fabricate an exact calendar date.

### H2 — 大正2年の改築記録

```text
fact_type       = ShrineHistory
history_type    = historical_event
fact_owner      = nsrc-000009
accepted_source = S2

title_candidate = 大正2年の改築記録
period_text     = 大正2年
event_date      = null
```

The Source supports a reconstruction / renovation record at year granularity.

---

## Not promoted into ShrineHistory

Do not create History rows for:

- generic Akagi shrine mythology;
- generic mountain worship;
- prayer / benefit interpretations;
- current Deity claims rewritten as History;
- geographic statements whose owner is merely the locality;
- other shrine entries from the same municipal historical table.

```text
HISTORICAL_DEITY_EVIDENCE != CURRENT_DEITY_FACT
LOCALITY_CORROBORATION    != SHRINE_HISTORY
GENERIC_AKAGI_TRADITION   != TARGET_FACT
```

---

## Sub-shrine / Associated Target boundary

No accepted Source requires a subordinate-shrine or associated-worship-target relation.

```text
SUB_SHRINE_RELATION        = NOT_OBSERVED
ASSOCIATED_TARGET_RELATION = NOT_OBSERVED
CROSS_ENTITY_CONTAMINATION = CLEARED_FOR_ACCEPTED_FACTS
```

---

## Anonymous collective / relation risk

The accepted G4 candidate packet does not require:

- anonymous multiple Deity semantics;
- incomplete current Deity list;
- collective membership;
- shinbutsu-shugo relation representation.

```text
ANONYMOUS_COLLECTIVE                 = NOT_REQUIRED
INCOMPLETE_CURRENT_DEITY_LIST        = NOT_INSERTED
PARTIAL_DEITY_LIST_ASSERTED_COMPLETE = NO
COLLECTIVE_MODEL_REQUIRED            = NO
```

---

## Knowledge Model Fit

### History

The current `ShrineHistory` model can represent H1/H2 without schema extension:

```text
H1 -> historical_event
H2 -> historical_event
```

Existing fields support:

- title;
- content;
- period_text;
- explicit Source relation;
- verification_status;
- confidence;
- verified_at.

```text
SHRINE_HISTORY_SCHEMA_CAPABILITY  = PASS
MODEL_CHANGE_REQUIRED_FOR_HISTORY = NO
```

### Deity

The current model can represent a named Deity in the future, but currentness is not established.

```text
DEITY_SCHEMA_CAPABILITY          = AVAILABLE
CURRENT_DEITY_FACT               = NONE
SHRINE_DEITY_ROWS_AUTHORIZED     = 0
MODEL_CHANGE_REQUIRED_FOR_DEITY  = NO
```

The unresolved current Deity is excluded from the accepted G4 payload rather than hidden by a partial list.

---

## G3 technical classification

The accepted packet establishes:

1. G1-confirmed current identity;
2. G2 PASS Visitor / Navigation Anchor;
3. municipal historical Source with target-specific historical content;
4. an explainable historical-locality -> current-locality bridge;
5. unambiguous Fact owner after same-name sibling exclusion;
6. two Source-backed History candidates;
7. current model capability without meaning loss;
8. no required sub-shrine / collective / relation model extension;
9. current Deity remains explicitly not frozen and is not inserted.

Therefore:

```text
TECHNICAL_G3_PROPOSAL = PASS
classification        = NORMAL_MODEL_FIT

NORMAL_MODEL_FIT                  = YES
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = NO
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO
```

The governing separation is:

```text
未確認のcurrent Deityがある
!=
確認済みHistoryを保存できない
```

---

## Proposed G4 entry boundary

If Mother Ship selects G3 PASS / NORMAL_MODEL_FIT:

```text
G4_ALLOWED_SCOPE_PROPOSAL:

ShrineHistory
- H1 天明3年8月の創立記録 / historical_event
- H2 大正2年の改築記録 / historical_event

ShrineDeity
- 0 rows

ShrineDeityCollective
- 0 rows
```

G4 must still verify:

- exact `ShrineKnowledgeSource` payloads;
- Source identity / normalization;
- exact History wording;
- `period_text`;
- `event_date = null` unless directly supported;
- verification_status;
- confidence;
- verified_at;
- exact Fact-Source relations;
- source-less Fact = 0;
- Evidence Gate usability.

G4 must not:

- insert `大山祇命` as a current Deity;
- infer another Deity from shrine naming;
- create shrine-specific goriyaku from historical founding / reconstruction;
- change Position;
- modify Recommendation / Ranking / Compass;
- reuse facts from the 四日町 or 上組 sibling 赤城社.

---

## Mother Ship G3 decision

```text
MOTHER_SHIP_G3_DECISION = A
```

Technical proposal:

```text
OPTION A
G3 = PASS
classification = NORMAL_MODEL_FIT
CURRENT_DEITY = NOT_FROZEN
SHRINE_DEITY_ROWS_AUTHORIZED = 0
G4_ALLOWED_SCOPE = accepted Source-backed ShrineHistory only
```

No Mother Ship selection is inferred by this audit.

---

## Candidate Master / lifecycle boundary

No Candidate Master lifecycle transition occurs in this G3 audit.

Expected current state remains:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
build_batch            = null
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
```

---

## Files / Data Changed

```text
docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md  ADDED

Candidate Master JSON                           NONE
Base Shrine Seed                               NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
Position Resolution Records                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
other H002 candidates                          NONE
```

---

## Current status

```text
NSRC_000009_G0 = PASS
NSRC_000009_G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
NSRC_000009_G2 = CLOSED / PASS

TECHNICAL_G3_PROPOSAL             = PASS
classification                    = NORMAL_MODEL_FIT
MOTHER_SHIP_G3_DECISION           = PENDING
CURRENT_DEITY                     = NOT_FROZEN
SHRINE_DEITY_ROWS_AUTHORIZED      = 0
G4_ALLOWED_SCOPE_PROPOSAL         = accepted Source-backed ShrineHistory only

G3_STATUS                         = CLOSED / PASS
G4                               = AUTHORIZED_TO_START
STOP                              = TRUE
```

G3 does not close until Mother Ship explicitly selects the G3 option.


## Mother Ship G3 decision — confirmed

Mother Ship explicitly selected:

```text
MOTHER_SHIP_G3_DECISION = A
TARGET                  = nsrc-000009

G3                      = PASS
classification          = NORMAL_MODEL_FIT

CURRENT_DEITY                 = NOT_FROZEN
SHRINE_DEITY_ROWS_AUTHORIZED  = 0

G4_ALLOWED_SCOPE
= accepted Source-backed ShrineHistory only
```

This closes G3.

Authorized G4 scope is limited to:

```text
ShrineHistory
- H1 天明3年8月の創立記録 / historical_event
- H2 大正2年の改築記録 / historical_event

ShrineDeity
- 0 rows

ShrineDeityCollective
- 0 rows
```

No current Deity inference is authorized.

```text
G3_CLOSED = PASS
NEXT_GATE = G4 Knowledge Fact + Evidence
STOP_AT_G3 = FALSE
```
