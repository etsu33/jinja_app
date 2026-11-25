# NIIGATA-001-H002 — nsrc-000007 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000007
name_jp             = 赤城社
address             = 新潟県十日町市四日町2534番地

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

- Recorded at: 2026-10-13
- Base: `develop@f4c7a7f4`（#3190 merged）
- Branch: `feature/nsrc-000007-g5-recommendation-eligibility`

## 2. Upstream state

```text
G0 = PASS
G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
G2 = PASS
G3 = PASS / NORMAL_MODEL_FIT
G4 = PASS（docs/audit/niigata-h002-nsrc-000007-g4-knowledge-materialization-reentry.md）
```

## 3. Rule used（existing only）

Authority: `docs/knowledge/recommendation-eligibility-contract.md`

```text
Recommendation eligibility = usable Deity Fact >= 1 OR usable History Fact >= 1

shrine_knowledge_selector
  -> fetch_fact_ready_knowledge_deities() / fetch_fact_ready_knowledge_histories()
  -> evidence_gate.decide_fact_usability()
  -> is_recommendation_eligible()          （concierge_chat_candidates.py, the single rule）
```

No eligibility rule was added or changed. G5 is a candidate-set boundary only. It is not a ranking signal,
score, purpose match, goriyaku inference, or F5 Qualified Evidence gate.

Re-read:

- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/knowledge/shrine-expansion-gate-contract.md`
- `backend/temples/services/concierge_chat_candidates.py`
- `backend/temples/services/recommendation_eligibility_verifier.py`
- `backend/temples/services/shrine_knowledge_selector.py`
- `backend/temples/services/evidence_gate.py`

## 4. Measurement setup（isolated pytest DB）

```text
import_shrines_seed --source backend/temples/data/shrines_seed_clean.json --skip-goriyaku-tags   （123 rows）
import_shrine_knowledge backend/temples/data/knowledge_seeds/nsrc_000007_seed.json
Production = NOT CONNECTED
```

Both seeds are used unchanged from develop.

## 5. Canonical exact identity

```text
Shrine.objects.get(name_jp="赤城社", address="新潟県十日町市四日町2534番地") -> 1 row（test DB pk 124）
```

Every measurement below uses this exact identity. Name-only identity is not used.

## 6. Read-only verifier（actual）

```text
verify_recommendation_eligibility(
    shrine_identities=[ShrineIdentity(name="赤城社", address="新潟県十日町市四日町2534番地")]
)
```

```json
{"summary": {"requested_count": 1, "eligible_count": 1, "ineligible_count": 0, "unresolved_count": 0, "all_eligible": true},
 "results": [{"requested": "赤城社 / 新潟県十日町市四日町2534番地", "status": "ELIGIBLE", "shrine_id": 124,
              "name_jp": "赤城社", "usable_deity_fact_count": 0, "usable_history_fact_count": 2,
              "usable_fact_count": 2, "note": null}]}
```

```text
summary_counts() = (1, 0, 0)
all_eligible     = True
shrine_id        = the exact target row
```

## 7. Shared partition（actual）

```text
partition_recommendation_eligible_shrines([target_shrine])

source_count     = 1
eligible_count   = 1
ineligible_count = 0
eligible[0]      = 赤城社 / 新潟県十日町市四日町2534番地（target row）
knowledge_deities   = 0
knowledge_histories = 2
  historical_event / 安政7年正月の再建
  regional_context / 赤城社に伝わった越後縮幡
```

## 8. Runtime candidate filter（actual）

```text
candidate = {"id": shrine.pk, "shrine_id": shrine.pk, "name": "赤城社"}
filter_recommendation_eligible_candidates([candidate]) == [candidate]   -> True
```

The shared runtime eligibility filter preserves nsrc-000007.

## 9. goriyaku boundary（actual）

```text
Shrine.goriyaku               = ""
Shrine.goriyaku_tags.count()  = 0
status                        = ELIGIBLE
```

```text
goriyaku absence != G5 INELIGIBLE
```

usable History is the authority. No goriyaku data was added or inferred.

## 10. Same-name boundary（actual）

H002 has other distinct shrines named `赤城社`. They are not materialized and are not changed here.

```text
verify_recommendation_eligibility(
  [赤城社 / 新潟県十日町市上組2059番地子, 赤城社 / 新潟県十日町市伊達乙48番地, 赤城社 / 新潟県南魚沼市芹田79番地]
)
summary_counts() = (0, 0, 3)   all UNRESOLVED, shrine_id = None
```

Same-name, different-address identities do not resolve to nsrc-000007 and do not inherit its eligibility.

## 11. Tests

New: `backend/temples/tests/test_nsrc_000007_g5_recommendation_eligibility.py`（2 tests）

1. Current-develop eligibility. Follows the nsrc-000002 G5 precedent: exact identity; verifier（1, 0, 0）/
   ELIGIBLE / 0 / 2 / 2; partition 1 / 1 / 0 with the exact two histories; runtime filter preserves the
   candidate; goriyaku absent.
2. The other H002 `赤城社` identities stay UNRESOLVED（0, 0, 3）.

```text
test_nsrc_000007_g5_recommendation_eligibility.py                     2 passed
related（nsrc G5 ×3, nsrc-000007 base/knowledge, verifier, 3 Evidence Gate suites, G6 handoff）
                                                                     162 passed
test_shared_recommendation_eligibility + test_concierge_chat_candidates_dedupe
                                                                      44 passed
backend full suite（-n auto）                                         5405 passed, 12 skipped
makemigrations --check                                                No changes detected
ruff check / format --check（new test）                               clean
git diff --check                                                      clean
```

The G6 handoff expectation（nsrc-000007 = `INELIGIBLE` in the H002 handoff test）is unaffected, because
that test imports only the nsrc-000002 / nsrc-000004 Knowledge Seeds.

## 12. What G5 PASS means

```text
G5 PASS = the candidate may participate in the shared Recommendation candidate set.
```

It does **not** mean:

- a Ranking top position / Top1 recommendation;
- a strong purpose match or high Need score;
- good recommendation copy;
- a guaranteed Concierge or Compass final recommendation;
- Production imported;
- CORE_READY.

## 13. Impact boundary

```text
changed files:
  backend/temples/tests/test_nsrc_000007_g5_recommendation_eligibility.py   ADDED
  docs/audit/niigata-h002-nsrc-000007-g5-recommendation-eligibility.md      ADDED

Knowledge Seed / Base Shrine Seed / Candidate Master        NONE
Evidence Gate / eligibility implementation                  NONE
Ranking / Score / Need mapping / goriyaku / goriyaku_tags   NONE
Concierge / Compass / models / migrations                   NONE
other H002 candidates                                       NONE
Production                                                  NONE（not connected）
```

## 14. Rollback

Revert the commit. It contains only a test and this audit; no data or runtime state changes.

## 15. STOP

```text
G5 nsrc-000007 = PASS / ELIGIBLE
G6 / G7 / G8   = NOT EXECUTED
```

Do not execute G6. Do not write Production.
