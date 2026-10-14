# NIIGATA-001-H002 — nsrc-000006 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000006
name_jp             = 赤井神社
address             = 新潟県佐渡市加茂歌代2662番地

G0                  = PASS
G1                  = PASS / NEW
G2                  = PASS
G3                  = PASS / NORMAL_MODEL_FIT
G4                  = PASS / CLOSED

FORMAL_G5           = PENDING_CI_MEASUREMENT
ELIGIBILITY_STATUS  = PENDING_CI_MEASUREMENT

expected usable Deity Fact   = 0
expected usable History Fact = 3

runtime implementation change = NONE
Ranking / Score change        = NONE
Knowledge Seed change         = NONE
Base Seed change              = NONE
Candidate Master change       = NONE
Production write              = NONE
G6                            = NOT EXECUTED
```

- Recorded at: 2026-10-14
- Base: `develop@b748dfb12cdde5f17b0d9f8fe0e69f65bb5bad68`
- Branch: `feature/nsrc-000006-g5-recommendation-eligibility`

## 2. Authority

Primary:

- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md`

Runtime authority:

```text
shrine_knowledge_selector
  -> fetch_fact_ready_knowledge_deities()
  -> fetch_fact_ready_knowledge_histories()
  -> evidence_gate.decide_fact_usability()
  -> is_recommendation_eligible()
```

G5 does not add a new readiness rule.

## 3. Existing rule only

```text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1
```

For nsrc-000006 the G4 result is:

```text
usable Deity Fact   = 0
usable History Fact = 3
```

Therefore the expected G5 result is:

```text
ELIGIBLE
```

This expectation is not accepted until the shared verifier and partition path pass on an isolated test DB.

## 4. Measurement setup

The G5 regression imports the current repository seeds unchanged:

```text
import_shrines_seed
  --source backend/temples/data/shrines_seed_clean.json
  --skip-goriyaku-tags

import_shrine_knowledge
  backend/temples/data/knowledge_seeds/nsrc_000006_seed.json
```

Production is not connected.

Canonical identity:

```text
赤井神社 / 新潟県佐渡市加茂歌代2662番地
```

No name-only resolution is used.

## 5. Expected verifier result

```text
verify_recommendation_eligibility(
  shrine_identities=[
    ShrineIdentity(
      name="赤井神社",
      address="新潟県佐渡市加茂歌代2662番地"
    )
  ]
)
```

Expected:

```text
summary_counts() = (1, 0, 0)
all_eligible     = True

status                    = ELIGIBLE
usable_deity_fact_count   = 0
usable_history_fact_count = 3
usable_fact_count         = 3
```

## 6. Expected shared partition

```text
partition_recommendation_eligible_shrines([target])

source_count     = 1
eligible_count   = 1
ineligible_count = 0
```

Expected target Knowledge:

```text
Deity = 0

History = 3
- regional_context / 4月16日の赤井神社例祭と鬼太鼓奉納
- tradition        / 元日午前0時の鬼太鼓奉納
- regional_context / 加茂の五神社としての記録
```

The `tradition` row remains a tradition. G5 does not reinterpret it.

## 7. Runtime candidate filter

Expected:

```text
candidate = {
  id: target.pk,
  shrine_id: target.pk,
  name: "赤井神社"
}

filter_recommendation_eligible_candidates([candidate])
== [candidate]
```

G5 proves only shared candidate-set participation.

It does not prove Top1 ranking, purpose match, reason-copy quality, or Compass selection.

## 8. goriyaku boundary

Expected current Base values:

```text
Shrine.goriyaku              = ""
Shrine.goriyaku_tags.count() = 0
```

This must not prevent G5 PASS because usable History is the authority.

```text
goriyaku absence != G5 INELIGIBLE
```

No goriyaku data is inferred or added.

## 9. Identity boundary

Research observed noncanonical addresses:

```text
新潟県佐渡市加茂歌代2622番地
新潟県佐渡市加茂歌代1164-7
```

Neither may inherit the canonical target's G5 eligibility.

Expected verifier result:

```text
summary_counts() = (0, 0, 2)
status           = UNRESOLVED / UNRESOLVED
shrine_id        = None / None
```

## 10. Acceptance matrix

| Condition | Pre-CI state |
|---|---|
| exact canonical identity resolves | PENDING |
| shared verifier status = ELIGIBLE | PENDING |
| usable Deity count = 0 | PENDING |
| usable History count = 3 | PENDING |
| usable Fact total = 3 | PENDING |
| shared partition keeps target | PENDING |
| runtime candidate filter keeps target | PENDING |
| goriyaku absent but eligibility preserved | PENDING |
| noncanonical addresses remain UNRESOLVED | PENDING |
| Ranking / Score change | NONE |
| runtime implementation change | NONE |
| Production write | NONE |

## 11. Files / data changed

Planned G5-only change:

```text
backend/temples/tests/test_nsrc_000006_g5_recommendation_eligibility.py  ADDED
docs/audit/niigata-h002-nsrc-000006-g5-recommendation-eligibility.md     ADDED
```

Not modified:

```text
Base Shrine Seed
Knowledge Seed
Candidate Master
Evidence Gate
eligibility implementation
Ranking / Score
goriyaku / tags
Concierge / Compass
models / migrations
other H002 candidates
Production DB
```

## 12. Current classification

Before CI:

```text
FORMAL_G5          = PENDING_CI_MEASUREMENT
ELIGIBILITY_STATUS = PENDING_CI_MEASUREMENT
G6                 = NOT_EXECUTED
PRODUCTION_WRITE   = NONE
STOP               = TRUE
```

If any verifier or shared-partition assertion fails, G5 becomes HOLD and no runtime contract is changed to force PASS.

## 13. STOP

Do not execute G6 in this PR.
Do not write Production.
