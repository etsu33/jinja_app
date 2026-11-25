# NIIGATA-001-H002 — nsrc-000009 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000009
name_jp             = 赤城社
address             = 新潟県十日町市伊達乙48番地

FORMAL_G5           = PASS
ELIGIBILITY_STATUS  = ELIGIBLE

usable Deity Fact   = 0
usable History Fact = 2
usable Fact total   = 2

runtime implementation change = NONE
Ranking / Score change        = NONE
Production write              = NONE
G6                            = NOT EXECUTED
```

- Recorded at: 2026-10-16
- Base: `develop@c6ab9c537c95525a7a1aeb7223174a5ff5397740`
- Branch: `feature/nsrc-000009-g5-recommendation-eligibility`

## 2. Upstream state

```text
G0 = PASS
G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
G2 = CLOSED / PASS
G3 = CLOSED / PASS / NORMAL_MODEL_FIT
G4 = CLOSED / PASS
```

G4 authority:
`docs/audit/niigata-h002-nsrc-000009-g4-formal-pass.md`

## 3. Rule used

Authority: `docs/knowledge/recommendation-eligibility-contract.md`

```text
Recommendation eligibility
= usable Deity Fact >= 1
OR usable History Fact >= 1
```

No new rule is introduced. G5 is only the shared Recommendation candidate-set boundary.

## 4. Measurement setup

Isolated pytest DB:

1. Base Shrine Seed
2. nsrc-000007 Knowledge Seed, reproducing the existing shared municipal Source
3. nsrc-000009 Knowledge Seed
4. read-only Shared Recommendation Eligibility verifier / partition / runtime filter

Production is not connected.

## 5. Exact identity

All measurements use:

```text
赤城社 / 新潟県十日町市伊達乙48番地
```

Name-only resolution is not used.

## 6. Shared verifier result

Expected and regression-locked result:

```text
summary_counts() = (1, 0, 0)
all_eligible     = True
status           = ELIGIBLE

usable_deity_fact_count   = 0
usable_history_fact_count = 2
usable_fact_count         = 2
```

The two usable History Facts are:

- historical_event / 天明3年8月の創立記録
- historical_event / 大正2年の改築記録

## 7. Shared partition / runtime filter

```text
source_count     = 1
eligible_count   = 1
ineligible_count = 0
```

The exact target survives `filter_recommendation_eligible_candidates()`.

`goriyaku` / `goriyaku_tags` remain absent. Their absence is not an eligibility failure because
usable History is the authority.

## 8. Same-name boundary

The unmaterialized same-name identities below remain `UNRESOLVED` and do not inherit nsrc-000009 eligibility:

- 赤城社 / 新潟県十日町市上組2059番地子
- 赤城社 / 新潟県南魚沼市芹田79番地

The already-known nsrc-000007 sibling is intentionally not used as a negative control because it has its
own independently usable Knowledge and is itself ELIGIBLE.

## 9. Formal G5 evaluation

| Condition | Result |
|---|---|
| Exact canonical identity resolves | PASS |
| usable Fact >= 1 | PASS, History = 2 |
| Shared verifier = ELIGIBLE | PASS |
| Shared partition retains target | PASS |
| Runtime filter retains target | PASS |
| Same-name unresolved siblings do not inherit eligibility | PASS |
| Ranking / Score unchanged | PASS |
| Production write | NONE |

```text
FORMAL_G5 = PASS
ELIGIBILITY_STATUS = ELIGIBLE
```

## 10. Meaning boundary

G5 PASS means the target may participate in the shared Recommendation candidate set.

It does not mean:

- Top1 or any ranking position
- strong purpose match
- final Concierge recommendation
- final Compass recommendation
- Production imported
- CORE_READY

## 11. Impact boundary

```text
Knowledge Seed / Base Seed / Candidate Master      NONE
Eligibility implementation                        NONE
Evidence Gate                                      NONE
Ranking / Score / Need / goriyaku                  NONE
Concierge / Compass                                NONE
Production                                         NONE
```

## 12. STOP

```text
G5 nsrc-000009 = PASS / ELIGIBLE
G6 / G7 / G8   = NOT EXECUTED
```

Do not execute G6 in this PR.
Do not write Production.
