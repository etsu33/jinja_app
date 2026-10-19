# NIIGATA-001-VPG001 — nsrc-000024 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000024
name_jp             = 秋葉神社
address             = 新潟県新潟市秋葉区秋葉3丁目8番19号

FORMAL_G5           = PASS
ELIGIBILITY_STATUS  = ELIGIBLE
G5_CLOSED           = PASS

usable Deity Fact   = 3
usable History Fact = 2
usable Fact total   = 5

runtime implementation change = NONE
Ranking / Score change        = NONE
Production write              = NONE

NEXT_GATE = G6 Runtime QA
G6        = NOT_EXECUTED
```

- Recorded at: 2026-10-19
- Base: `develop@31e15dbd14b13b0e882b7f4a0a1a1382f9f7ae29`（PR #3276 merge, VPG001 Formal G4 closure）
- Branch: `feature/niigata-vpg001-g5-recommendation-eligibility`

## 2. Upstream state

```text
G0 = PASS
G1 = PASS / CLOSED / SAME_NAME_DIFFERENT_SHRINE
G2 = CLOSED / PASS（FROZEN）
G3 = CLOSED / NORMAL_MODEL_FIT / PRODUCT_SURFACE = RECOMMENDATION
G4 = CLOSED / PASS
```

G4 authority: `docs/audit/niigata-vpg001-nsrc-000024-g4-formal-pass.md`

## 3. Rule used

Authority: `docs/knowledge/recommendation-eligibility-contract.md`, `docs/knowledge/shrine-expansion-gate-contract.md` §8

```text
Recommendation eligibility
= usable Deity Fact >= 1
OR usable History Fact >= 1
```

No new rule is introduced. The rule is applied by the existing `is_recommendation_eligible()` on the
Facts returned by `shrine_knowledge_selector`, whose usability authority is `evidence_gate.decide_fact_usability()`.
`Shrine.goriyaku`, legacy `history_theme`, `popular_score`, ranking weights, direction, distance and purpose
match are not used.

## 4. Measurement setup

Isolated pytest PostgreSQL DB:

1. current Base Shrine Seed（unchanged）
2. `nsrc_000024_seed.json`（unchanged）
3. read-only Shared Recommendation Eligibility verifier / shared partition / runtime candidate filter

A second setup imports all four VPG001 Knowledge Seeds together, to check that no other candidate's Facts
change this target's result. Production is not connected.

## 5. Exact identity

```text
秋葉神社 / 新潟県新潟市秋葉区秋葉3丁目8番19号
```

`ShrineIdentity(name, address)` resolves to exactly one Shrine row（`shrine_id` = the target pk）.
Name-only resolution is not used for the measurement.

## 6. Shared verifier result（measured）

```text
status                    = ELIGIBLE
shrine_id                 = exact target pk
usable_deity_fact_count   = 3
usable_history_fact_count = 2
usable_fact_count         = 5
summary_counts()          = (1, 0, 0)
all_eligible              = True
```

Usable Facts returned:

```text
Deity    大己貴神
Deity    大物主命
Deity    菅原道真公
History  historical_event / 桂家の守り神から秋葉町内への移譲
History  historical_event / 創建250年
```

## 7. Shared partition / runtime filter（measured）

```text
partition_recommendation_eligible_shrines([target])
  source_count     = 1
  eligible_count   = 1
  ineligible_count = 0
  eligible[0].shrine = exact target
  attached knowledge_deities   = 3
  attached knowledge_histories = 2

filter_recommendation_eligible_candidates([{"id", "shrine_id", "name"}])
  = [candidate]（retained）
```

Goriyaku boundary: `goriyaku = ""`, `goriyaku_tags = 0`, `history_theme = ""`. Their absence does not make
the target INELIGIBLE; usable Knowledge is the authority.

## 8. Same-name boundary

The frozen same-name / different-address identities recorded in G1 are not materialized in the Base Seed.
The verifier returns `UNRESOLVED` for each, with `shrine_id = None`:

```text
秋葉神社 / 新潟県新潟市中央区古町通11番町1688番地  -> UNRESOLVED
秋葉神社 / 新潟県新発田市下山田459番地  -> UNRESOLVED
summary_counts() = (0, 0, 2)
```

They do not inherit this target's eligibility. Eligibility belongs to the exact Shrine row only.

## 9. Candidate-specific boundary

The 明治3年（1872）chronology conflict and any derived founding year are not materialized Facts. Neither
appears in the eligible Knowledge returned by the partition（no 明治3 / 1870 / 1872 / 1763）. The conflict stays
`REMAINS_LOCALIZED / NON_BLOCKING`（G4）.

## 10. Formal G5 evaluation

| Condition | Result |
|---|---|
| Exact canonical identity resolves | PASS |
| usable Fact >= 1 | PASS, Deity = 3 / History = 2 |
| Shared verifier = ELIGIBLE | PASS |
| Shared partition retains exact target | PASS（1 / 1 / 0） |
| Runtime filter retains target | PASS |
| goriyaku absence does not affect eligibility | PASS |
| Same-name / foreign identities do not inherit eligibility | PASS |
| Eligibility implementation unchanged | PASS |
| Ranking / Score unchanged | PASS |
| Production write | NONE |

```text
FORMAL_G5 = PASS
ELIGIBILITY_STATUS = ELIGIBLE
G5_CLOSED = PASS
```

## 11. Meaning boundary

G5 PASS means only that the target may participate in the shared Recommendation candidate set.

It does not mean:

- Top1 or any ranking position
- strong purpose match
- final Concierge recommendation
- final Compass recommendation
- good Recommendation copy
- Production imported
- CORE_READY

## 12. Impact boundary

```text
Knowledge Seed / Base Seed / Candidate Master      NONE
Source Packet / G1 / G2 / G3 / G4 audits           NONE
Eligibility implementation / Evidence Gate         NONE
shrine_knowledge_selector                          NONE
Ranking / Score / purpose mapping / goriyaku       NONE
Direction / Distance                               NONE
Concierge / Compass                                NONE
models / migrations / serializers / frontend       NONE
Production                                         NONE
nsrc-000023                                        NONE（G5 NOT_APPLICABLE / NOT_EXECUTED）
```

## 13. STOP

```text
NSRC_000024_G5 = CLOSED / PASS / ELIGIBLE
NEXT_GATE     = G6 Runtime QA
G6 / G7 / G8  = NOT EXECUTED
```

Do not execute G6 in this PR.
Do not write Production.
