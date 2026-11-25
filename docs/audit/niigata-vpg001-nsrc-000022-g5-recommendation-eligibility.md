# NIIGATA-001-VPG001 — nsrc-000022 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000022
name_jp             = 五十嵐神社
address             = 新潟県三条市大字飯田2283番地

FORMAL_G5           = PASS
ELIGIBILITY_STATUS  = ELIGIBLE
G5_CLOSED           = PASS

usable Deity Fact   = 1
usable History Fact = 0
usable Fact total   = 1

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
G1 = PASS / CLOSED / NEW
G2 = CLOSED / PASS（FROZEN）
G3 = CLOSED / NORMAL_MODEL_FIT / PRODUCT_SURFACE = RECOMMENDATION
G4 = CLOSED / PASS
```

G4 authority: `docs/audit/niigata-vpg001-nsrc-000022-g4-formal-pass.md`

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
2. `nsrc_000022_seed.json`（unchanged）
3. read-only Shared Recommendation Eligibility verifier / shared partition / runtime candidate filter

A second setup imports all four VPG001 Knowledge Seeds together, to check that no other candidate's Facts
change this target's result. Production is not connected.

## 5. Exact identity

```text
五十嵐神社 / 新潟県三条市大字飯田2283番地
```

`ShrineIdentity(name, address)` resolves to exactly one Shrine row（`shrine_id` = the target pk）.
Name-only resolution is not used for the measurement.

## 6. Shared verifier result（measured）

```text
status                    = ELIGIBLE
shrine_id                 = exact target pk
usable_deity_fact_count   = 1
usable_history_fact_count = 0
usable_fact_count         = 1
summary_counts()          = (1, 0, 0)
all_eligible              = True
```

Usable Facts returned:

```text
Deity    五十日帯日子命
```

## 7. Shared partition / runtime filter（measured）

```text
partition_recommendation_eligible_shrines([target])
  source_count     = 1
  eligible_count   = 1
  ineligible_count = 0
  eligible[0].shrine = exact target
  attached knowledge_deities   = 1
  attached knowledge_histories = 0

filter_recommendation_eligible_candidates([{"id", "shrine_id", "name"}])
  = [candidate]（retained）
```

Goriyaku boundary: `goriyaku = ""`, `goriyaku_tags = 0`, `history_theme = ""`. Their absence does not make
the target INELIGIBLE; usable Knowledge is the authority.

## 8. Same-name boundary

G1 = NEW: no frozen same-name identity exists. The Base Seed has exactly one 五十嵐神社 row（the target）.
No negative identity was invented. Eligibility belongs to the exact Shrine row only.

## 9. Candidate-specific boundary

```text
usable Deity   = 1（五十日帯日子命）
usable History = 0
rule           = usable Deity >= 1 OR usable History >= 1  ->  ELIGIBLE
```

History = 0 is not a G5 failure. No History Fact is required. The Deity name returned by the partition is the
Source spelling 五十日帯日子命; 五十日帯彦命 does not appear.

## 10. Formal G5 evaluation

| Condition | Result |
|---|---|
| Exact canonical identity resolves | PASS |
| usable Fact >= 1 | PASS, Deity = 1 / History = 0 |
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
NSRC_000022_G5 = CLOSED / PASS / ELIGIBLE
NEXT_GATE     = G6 Runtime QA
G6 / G7 / G8  = NOT EXECUTED
```

Do not execute G6 in this PR.
Do not write Production.
