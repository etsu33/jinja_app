# NIIGATA-001-H001 — nsrc-000004 G5 Shared Recommendation Eligibility

## 1. Status

~~~text
candidate_id          = nsrc-000004
candidate_name        = 青海神社
fact_owner            = 青海神社（加茂市）

UPSTREAM_G4           = PASS
G5_SHARED_ELIGIBILITY = PASS
ELIGIBILITY_STATUS    = ELIGIBLE

Production write      = NONE
G6 / G7 / G8          = NOT EXECUTED
~~~

- Recorded at: 2026-10-10
- Base: `develop@d3dcf1860f0aaae39263814ec96b0d410afd7cf0`
- Branch: `audit/nsrc-000004-g5-recommendation-eligibility`
- G5 test commit before this audit record: `dcee867c78ce785ac4c674f9d4188d4441e1a606`
- Upstream G4 audit: `docs/audit/niigata-h001-g4-data-materialization-reentry.md`
- Authority: `docs/knowledge/recommendation-eligibility-contract.md`

本書は `nsrc-000004 / 青海神社（加茂市）` が、
現行developのShared Recommendation Eligibility実装上、
Recommendation candidate setへ参加する構造資格を持つかを実測した記録である。

---

## 2. Governing contract

Gate Contract §8:

~~~text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1
~~~

Recommendation Eligibility Contract:

~~~text
Shrine DB presence
!= Recommendation eligibility

Recommendation eligibility
= at least one usable Deity or History Fact

Shared eligibility
!= F5 Qualified Evidence gating
!= ranking signal
~~~

Eligibility predicateは以下のみを使用する。

~~~text
shrine_knowledge_selector
-> fetch_fact_ready_knowledge_deities()
-> fetch_fact_ready_knowledge_histories()
-> evidence_gate.decide_fact_usability()
-> is_recommendation_eligible()
~~~

Legacy `Shrine.goriyaku` / `Shrine.history_theme` /
`goriyaku_tags` はG5 predicateの代替根拠にしない。

---

## 3. Execution scope

~~~text
G5_SCOPE = { nsrc-000004 }
~~~

対象外:

| candidate_id | Shrine | State |
|---|---|---|
| nsrc-000001 | 相吉神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000002 | 青澤神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000003 | 蒼柴神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000005 | 青山稲荷神社 | G2 HOLD_POSITION_REVIEW |

4社についてG5は実行しない。

---

## 4. Upstream prerequisite

PR #3129 merge後:

~~~text
develop HEAD
= d3dcf1860f0aaae39263814ec96b0d410afd7cf0

Formal G4
= PASS
~~~

G4 actual Evidence Gate measurement:

~~~text
usable Deity   = 2 / 2
usable History = 2 / 2
usable total   = 4 / 4
~~~

Knowledge Source relations:

~~~text
D1 椎根津彦命           -> S1 AOMI_OFFICIAL_DEITY
D2 大国魂命             -> S1 AOMI_OFFICIAL_DEITY
H1 神亀3年の創建         -> S2 AOMI_OFFICIAL_HISTORY
H2 明治5年の三社本殿合殿 -> S2 AOMI_OFFICIAL_HISTORY
~~~

---

## 5. Canonical identity

G5検証ではname-only解決を使用しない。

~~~text
name_jp = 青海神社
address = 新潟県加茂市大字加茂字宮山229番地
~~~

同名別所在の青海神社が存在するため、
`ShrineIdentity(name, address)` によるcanonical identityで検証した。

---

## 6. Existing Shared Eligibility implementation

現行developの実装:

~~~text
backend/temples/services/concierge_chat_candidates.py

is_recommendation_eligible()
filter_recommendation_eligible_candidates()
partition_recommendation_eligible_shrines()
~~~

Read-only verifier:

~~~text
backend/temples/services/recommendation_eligibility_verifier.py

verify_recommendation_eligibility()
~~~

判定式:

~~~text
bool(knowledge_deities)
OR
bool(knowledge_histories)
~~~

usable判定自体は再実装せず、既存Evidence Gate authorityへ委譲する。

---

## 7. Dedicated isolated PostgreSQL test

Test:

`backend/temples/tests/test_nsrc_000004_g5_recommendation_eligibility.py::test_nsrc_000004_is_shared_recommendation_eligible_on_current_develop`

Execution environment:

~~~text
DB_HOST=127.0.0.1
USE_GIS=0
DISABLE_GIS_FOR_TESTS=1
pytest isolated PostgreSQL test DB
~~~

Observed result:

~~~text
1 passed
0 failed
~~~

Execution time:

~~~text
5.38s
~~~

Production DB access / write:

~~~text
NONE
~~~

---

## 8. Read-only verifier result

The test executes:

~~~text
verify_recommendation_eligibility(
    shrine_identities=[
        ShrineIdentity(
            name="青海神社",
            address="新潟県加茂市大字加茂字宮山229番地"
        )
    ]
)
~~~

Observed / asserted result:

~~~text
requested  = 1
ELIGIBLE   = 1
INELIGIBLE = 0
UNRESOLVED = 0
ALL_ELIGIBLE = PASS

usable_deity_fact_count   = 2
usable_history_fact_count = 2
usable_fact_count         = 4
~~~

Therefore:

~~~text
nsrc-000004 = ELIGIBLE
~~~

---

## 9. Shared partition result

The same materialized Shrine is passed to:

`partition_recommendation_eligible_shrines([shrine])`

Observed / asserted result:

~~~text
source_count     = 1
eligible_count   = 1
ineligible_count = 0

eligible Shrine  = 青海神社
usable Deity     = 2
usable History   = 2
~~~

This confirms the shared Shrine-set gate accepts the candidate.

---

## 10. Runtime candidate filter result

The same Shrine is represented as a runtime candidate dict:

~~~text
{
  "id": shrine.pk,
  "shrine_id": shrine.pk,
  "name": "青海神社"
}
~~~

Then passed to:

`filter_recommendation_eligible_candidates()`

Observed / asserted result:

~~~text
input candidates  = 1
output candidates = 1
青海神社           = PASSED
~~~

Therefore the current shared runtime filter does not exclude nsrc-000004.

---

## 11. Goriyaku boundary

Post-materialization state:

~~~text
Shrine.goriyaku      = ""
Shrine.goriyaku_tags = 0
~~~

Despite this, G5 is ELIGIBLE because the current contract uses usable Deity / History Fact.

~~~text
goriyaku_tags absence
!= G5 INELIGIBLE

usable Knowledge
= G5 authority
~~~

No goriyaku mapping is created in this G5 audit.

---

## 12. Formal G5 decision

Contract input:

~~~text
usable Deity   = 2
usable History = 2
~~~

Predicate:

~~~text
usable Deity >= 1
OR usable History >= 1
~~~

Actual shared implementation:

~~~text
read-only verifier = ELIGIBLE
shared partition   = PASSED
runtime filter     = PASSED
~~~

Formal decision:

~~~text
FORMAL_G5 = PASS
ELIGIBILITY_STATUS = ELIGIBLE
~~~

Reason:

~~~text
at least one usable Deity or History Fact exists
AND
canonical identity resolves exactly
AND
current shared implementation accepts the Shrine
~~~

---

## 13. What this PASS means

~~~text
G5 PASS
= candidate setへ参加するための構造条件を満たす
~~~

It does not mean:

~~~text
Ranking上位
Top1
Purpose matchが強い
Need scoreが高い
Recommendation copy品質が高い
Concierge最終推薦へ必ず到達
Compass最終推薦へ必ず到達
Production imported
CORE_READY
~~~

---

## 14. Downstream boundary

This G5 audit does not evaluate:

~~~text
Ranking / scoring quality
Need / goriyaku mapping quality
Concierge final candidate reachability
Compass direction / distance behavior
Recommendation copy
Runtime presentation
Production behavior
~~~

The absence of `goriyaku_tags` may matter to downstream scoring or explicit goriyaku filters,
but it is not a G5 eligibility failure under the current contract.

No G6 authorization or HOLD decision is made in this audit.

---

## 15. Isolation

Branch diff before this audit document:

~~~text
backend/temples/tests/test_nsrc_000004_g5_recommendation_eligibility.py
~~~

Changes:

~~~text
Recommendation logic = 0
Ranking / Score       = 0
Knowledge Seed        = 0
Base Seed             = 0
Candidate Master      = 0
goriyaku_tags         = 0
Mapping Registry      = 0
Production            = 0
~~~

This G5 work only adds reproducible eligibility verification.

---

## 16. Completion checklist

- [x] PR #3129 merge後developをbaseとして固定
- [x] G5 authorityをRecommendation Eligibility Contractへ固定
- [x] nsrc-000004のみをexecution scopeへ固定
- [x] G2 HOLD 4社をscope外へ固定
- [x] canonical name + addressでShrineを解決
- [x] usable Deity = 2を実測
- [x] usable History = 2を実測
- [x] read-only verifierでELIGIBLE
- [x] shared partitionでeligible
- [x] runtime candidate filterを通過
- [x] legacy goriyaku / history_themeで判定を代替しない
- [x] PostgreSQL isolated pytest PASS
- [x] Formal G5 = PASS
- [x] G5監査文書を作成
- [x] Production writeなし
- [x] Ranking / Score変更なし
- [x] PR作成（#3130）
- [x] STOP

---

## STOP BOUNDARY

~~~text
FORMAL_G5 = PASS

Do not execute G6 in this audit.
Do not write Production.
Do not infer goriyaku_tags.
Do not modify Ranking / Score.
~~~
