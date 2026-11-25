# NIIGATA-001-VPG001 — nsrc-000021 G4 Formal PASS

## 1. Status

```text
candidate_id                 = nsrc-000021
name_jp                      = 荒川神社
address                      = 新潟県胎内市桃崎浜187番地
BASE_SHA                     = 05c9830dbb176398210b6ba8853751a8d8505237

G0                           = PASS
G1                           = PASS / CLOSED / SAME_NAME_DIFFERENT_SHRINE
G2                           = CLOSED / PASS（FROZEN）
G3 classification            = NORMAL_MODEL_FIT
Product Surface              = RECOMMENDATION（Mother Ship, 2026-10-19）
Source Packet                = PASS / FROZEN（unchanged）
Knowledge Seed schema        = 1.0（merged, PR #3275）

Source count                 = 1
Deity count                  = 1
History count                = 1
source-less Fact             = 0
Source conflict              = 0
Source ambiguity             = 0

Evidence Gate                = measured / every Fact usable=True
usable Deity                 = 1 / 1
usable History               = 1 / 1

validate-only                = PASS（0 writes）
dry-run                      = PASS（0 writes）
apply                        = PASS（exact frozen counts）
second import                = IDEMPOTENT

Production write             = NONE
Candidate Master write       = NONE

FORMAL_G4                    = PASS

G5                           = NOT EXECUTED
G6                           = NOT EXECUTED
G7                           = NOT EXECUTED
G8                           = NOT EXECUTED
```

- Recorded at: 2026-10-19
- Base: `develop@05c9830dbb176398210b6ba8853751a8d8505237`（PR #3275 merge, VPG001 G4 Knowledge materialization）
- Branch: `docs/niigata-vpg001-g4-formal-closure`

## 2. Authority

This closure is evaluated under:

- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/fact-source-citation-contract.md`
- `docs/audit/niigata-vpg001-nsrc-000021-g4-source-packet-freeze.md`
- `docs/audit/niigata-vpg001-g4-knowledge-materialization.md`（measured results）
- `backend/temples/services/evidence_gate.py`
- Precedent: `docs/audit/niigata-h002-nsrc-000009-g4-formal-pass.md`（latest Formal G4 closure on develop）

This document records the G4 result only. The measurements are the ones merged in PR #3275. Nothing was
re-materialized or re-measured for this closure. It does not execute G5, G6, G7 or G8.

Citation contract: no `ShrineFactSourceCitation` is used（schema 1.0; no locator_text in the frozen packet）.
Citation count for this candidate = 0. No page number or locator was invented.

## 3. Upstream state check

```text
develop HEAD              = 05c9830dbb176398210b6ba8853751a8d8505237（expected value; verified）
merged #3275 content      = identical to the measured branch（seed, tests, audit）
Source Packet audit       = unchanged since #3274
G1 / G2 / G3 audits       = unchanged
```

No upstream change since the measurement. The merged measurements are used as-is.

## 4. Fact owner and Source

```text
FACT_OWNER = nsrc-000021 = 荒川神社 / 新潟県胎内市桃崎浜187番地
```

Source（the only one serialized）:

```text
key                  = NIIGATA_PREF_KITAMAEBUNE02
source_type          = government
title                = 北前船の魅力を訪ねて
publisher            = 新潟県
url                  = https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html
language             = ja
accessed_at          = 2026-10-19
verified_at          = 2026-10-19T14:35:38+09:00（Source verification session time）
verification_status  = source_confirmed
confidence           = high
first import         = CREATE（REUSE_EXISTING 0）
```

Facts:

```text
Deity    天鈿女命
History  [regional_context] 船主による船絵馬の奉納
```

## 5. Measured execution and Evidence Gate（from PR #3275）

```text
validate-only   validate-only: OK, no errors; DB writes 0
dry-run         plan summary = {source_CREATE 1, deity_CREATE 1, history_CREATE 1}; DB writes 0
apply           delta = Source 1 / Deity 1 / History 1 / Collective 0 / SourceFact 0 / Citation 0
second import   plan summary = {source_REUSE_EXISTING 1, deity_SKIP_EXISTS 1, history_SKIP_EXISTS 1}; created 0; state unchanged
```

Every persisted Fact, evaluated with its actual Source relation:

```text
Fact verification_status     = source_confirmed
Fact confidence              = high
Source verification_statuses = [source_confirmed]

usable          = True
display_mode    = full
reason_strength = assertive
reason          = fact_ready_with_source
```

```text
USABLE_DEITY_COUNT         = 1
USABLE_HISTORY_COUNT       = 1
G4_USABLE_FACT_MINIMUM_MET = YES
```

## 6. Chronology conflict boundary

```text
S1  天保12年（1814年）
S2  天保12年（1841）
adopted normalized year = NONE
materialized Fact containing 1814 / 1841 = 0

CHRONOLOGY_CONFLICT = REMAINS_LOCALIZED / NON_BLOCKING
```

The conflict is **not resolved** by this closure. It stays outside the materialized Facts, so it does not
reach any usable Deity or History. A later Fact about the building year needs a new Source decision.

## 7. Formal G4 evaluation

| # | G4 condition | Evidence | Result |
|---|---|---|---|
| 1 | Fact owner matches G1 / G3 | every Fact owned by 荒川神社 / 新潟県胎内市桃崎浜187番地 | PASS |
| 2 | exact Base Shrine exists | resolve_shrine = OK; exact (name_jp, address) = 1 | PASS |
| 3 | source-less Fact = 0 | each Fact linked to `NIIGATA_PREF_KITAMAEBUNE02`; whole-DB source-less = 0 | PASS |
| 4 | Source identity conflict = 0 | SOURCE_REUSE_CONFLICT not observed | PASS |
| 5 | Source ambiguity = 0 | SOURCE_REUSE_AMBIGUOUS not observed | PASS |
| 6 | Fact / Source verification contract | source_confirmed / high / verified_at 2026-10-19T14:35:38+09:00 | PASS |
| 7 | usable Deity or History >= 1 | usable Deity 1/1, usable History 1/1 | PASS |
| 8 | Fact wording within frozen Source Packet | seed wording = frozen packet wording | PASS |
| 9 | tradition not promoted to historical_event | no tradition Fact; H1 = regional_context（unchanged） | PASS |
| 10 | forbidden / derived Fact = 0 | S2（180012.pdf）not serialized; 天保12年 building year not materialized; no 1814 / 1841 Fact | PASS |
| 11 | chronology conflict not silently normalized | 1814 / 1841 excluded; no normalized year | PASS |
| 12 | importer idempotent | second import created = 0; ids / counts unchanged | PASS |
| 13 | goriyaku unchanged | goriyaku "", tags 0, assignments 0 before = after | PASS |
| 14 | Ranking / Score / Position unchanged | no change to coordinates, ranking, score | PASS |
| 15 | Production write = NONE | no Production connection | PASS |

No active G4 STOP condition remains.

```text
FORMAL_G4 = PASS
```

## 8. Impact boundary

```text
Knowledge Seed / Source rows / Facts   unchanged（already merged）
Knowledge importer / Evidence Gate     unchanged
Base Shrine Seed                       NONE
Candidate Master                       NONE
G1 / G2 / G3 / Source Packet audits    NONE
Product Surface                        NONE
Position                               NONE
goriyaku / tags                        NONE
Recommendation / Ranking / Score       NONE
Concierge / Compass                    NONE
Production DB                          NONE
nsrc-000023                            NONE
```

## 9. Final state / STOP

```text
NSRC_000021_G0 = PASS
NSRC_000021_G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
NSRC_000021_G2 = CLOSED / PASS
NSRC_000021_G3 = CLOSED / NORMAL_MODEL_FIT / PRODUCT_SURFACE = RECOMMENDATION
NSRC_000021_G4 = CLOSED / PASS

NSRC_000023_G3 = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE
NSRC_000023_G4 = NOT_AUTHORIZED

G5 = NOT EXECUTED
G6 = NOT EXECUTED
G7 = NOT EXECUTED
G8 = NOT EXECUTED

Production write = NONE
```

Do not infer a G5 outcome from G4 PASS.
Do not update Candidate Master lifecycle in this closure.
Do not write Production.
