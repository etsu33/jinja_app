# NIIGATA-H001 nsrc-000002 青澤神社 G5 Shared Recommendation Eligibility

## Status

- Recorded at: `2026-10-10`
- Candidate: `nsrc-000002`
- Shrine: 青澤神社（新潟県糸魚川市大字青海2696番地）
- Gate: `G5 Shared Recommendation Eligibility`（`docs/knowledge/shrine-expansion-gate-contract.md` §8）
- Authority: `docs/knowledge/recommendation-eligibility-contract.md`

```text
UPSTREAM_G4           = PASS   (docs/audit/niigata-h001-nsrc-000002-g4-formal-redecision.md, PR #3149)
G5_SHARED_ELIGIBILITY = PASS
ELIGIBILITY_STATUS    = ELIGIBLE
FORMAL_G5             = PASS

G6 / G7 / G8          = NOT EXECUTED
PRODUCTION_WRITE      = NONE
```

---

## 1. Authority

新しい eligibility rule は作っていない。既存の authority だけを使った。

```text
shrine_knowledge_selector
  -> fetch_fact_ready_knowledge_deities()
  -> fetch_fact_ready_knowledge_histories()
  -> evidence_gate.decide_fact_usability()
  -> is_recommendation_eligible()
```

## 2. 測定方法

`backend/temples/tests/test_nsrc_000002_g5_recommendation_eligibility.py` が isolated PostgreSQL test DB で次を行う。

1. canonical Base Seed（`backend/temples/data/shrines_seed_clean.json`）を `import_shrines_seed --skip-goriyaku-tags` で import
2. `backend/temples/data/knowledge_seeds/nsrc_000002_seed.json` を import
3. exact canonical identity（青澤神社 + 新潟県糸魚川市大字青海2696番地）で Shrine を解決（name-only では解決しない）
4. read-only verifier / shared partition / runtime candidate filter を実行

## 3. 実測

### read-only verifier

```text
verify_recommendation_eligibility(
    shrine_identities=[ShrineIdentity(name="青澤神社", address="新潟県糸魚川市大字青海2696番地")]
)

summary_counts()          = (1, 0, 0)
all_eligible              = True
status                    = ELIGIBLE
name_jp                   = 青澤神社
shrine_id                 = target Shrine の PK（isolated test DB では 123。Production id ではない）
usable_deity_fact_count   = 0
usable_history_fact_count = 1
usable_fact_count         = 1
```

### shared partition

```text
partition_recommendation_eligible_shrines([shrine])

source_count        = 1
eligible_count      = 1
ineligible_count    = 0
eligible[0].shrine  = target Shrine
knowledge_deities   = 0
knowledge_histories = 1  (regional_context / 青沢神社の春季祭礼)
```

### runtime candidate filter

```text
candidate = {"id": shrine.pk, "shrine_id": shrine.pk, "name": "青澤神社"}
filter_recommendation_eligible_candidates([candidate]) == [candidate]  -> True
```

shared runtime eligibility path は nsrc-000002 を受け入れる。

### goriyaku boundary

```text
Shrine.goriyaku             = ""
Shrine.goriyaku_tags.count  = 0
status                      = ELIGIBLE
```

```text
goriyaku_tags absence != G5 INELIGIBLE
usable History        =  G5 authority
```

goriyaku tag は作っていない。

### 対照

Seed の History を一時的に空にした状態では、同じ test が失敗した（usable History が無いと ELIGIBLE にならない）。
Seed は元に戻し、diff は 0。

## 4. 判定

```text
FORMAL_G5          = PASS
ELIGIBILITY_STATUS = ELIGIBLE
```

理由:

```text
usable History >= 1
AND canonical identity resolves exactly
AND read-only verifier returns ELIGIBLE
AND shared partition passes the Shrine
AND runtime candidate filter preserves the Shrine
```

## 5. G5 PASS が意味しないこと

G5 PASS は「Shared Recommendation Eligibility の入口を通る」ことだけを示す。次は意味しない。

- Ranking 上位
- Top1
- 強い Purpose 一致
- 高い Need score
- 推薦文の品質
- Concierge の最終推薦に必ず出ること
- Compass の最終推薦に必ず出ること
- Production へ import 済みであること
- CORE_READY

## 6. Tests

| check | 結果 |
| --- | --- |
| `test_nsrc_000002_g5_recommendation_eligibility.py` | 1 passed |
| eligibility / Evidence Gate / nsrc / knowledge seed import test（14 file） | 162 passed |
| `scripts/tests` | 685 passed |
| backend full suite | 4934 passed, 12 skipped |
| `makemigrations --check` | No changes detected |
| ruff / black（新規 test） | PASS |
| `git diff --check` | clean |

## 7. Isolation

本 PR が変更したのは G5 test と本書だけ。次は変更していない。

```text
Recommendation logic / Ranking / Score
Knowledge Seed / Base Seed / Candidate Master
goriyaku / goriyaku_tags / Mapping Registry
Concierge / Compass
models / migrations / Production configuration
```

```text
PRODUCTION_WRITE = NONE
```

## 8. Next

G6 Runtime QA、G7 Production Import、Candidate Master の lifecycle transition は開始していない。
