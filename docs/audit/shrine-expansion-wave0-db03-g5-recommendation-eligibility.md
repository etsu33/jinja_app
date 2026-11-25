# W0-DB03 G5 Shared Recommendation Eligibility

## Status

- Status: `W0_DB03_G5_PASS_4_OF_4`
- Recorded at: `2026-09-25`
- Branch: `audit/w0-db03-g5-recommendation-eligibility`
- Base: `develop@f58b184060a9dea69795031f97810dbaa17c0267`
- Gate: `G5 Shared Recommendation Eligibility`（`docs/knowledge/shrine-expansion-gate-contract.md` §8）
- Upstream: G4 `W0_DB03_G4_PASS_4_OF_4`（`docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md`）
- Execution subset: `wave0-012` / `wave0-013` / `wave0-015` / `wave0-016`
- Excluded: `wave0-014 宮城縣護國神社`（G3 `MODEL_CHANGE_REQUIRED`）
- Production access: `NONE`
- G6 Runtime QA: `NOT EXECUTED`

本書は監査記録のみである。Recommendation eligibility logic、Evidence Gate、Candidate Master、
Base Seed、Knowledge Seed、Ranking、Compass、schema / migration、wave0-014 はいずれも変更していない。

---

## 1. 判定の正本

```text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1
```

正本は `docs/knowledge/recommendation-eligibility-contract.md`。本 G5 は新しい rule を追加せず、
既存の read-only verifier service だけを実行した。

```text
temples.services.recommendation_eligibility_verifier.verify_recommendation_eligibility()
  -> temples.services.shrine_knowledge_selector
       .fetch_fact_ready_knowledge_deities() / _histories()
         -> temples.services.evidence_gate.decide_fact_usability()
  -> temples.services.concierge_chat_candidates.is_recommendation_eligible()
       （Shared Recommendation Eligibility の唯一の判定式）
```

verifier は判定式を再実装していない（`is_recommendation_eligible()` へ委譲し、usable Fact の取得は
selector 経由で Evidence Gate へ委譲する）。本 G5 でも eligibility 式を別実装していない。

---

## 2. Canonical identities（exactly 4）

`(name_jp, address)` の完全一致で解決した。name-only 推測は使用していない。

| candidate_id | name_jp | address |
| --- | --- | --- |
| wave0-012 | 大神神社 | 奈良県桜井市三輪1422 |
| wave0-013 | 北野天満宮 | 京都府京都市上京区馬喰町 |
| wave0-015 | 平安神宮 | 京都府京都市左京区岡崎西天王町97 |
| wave0-016 | 岡田宮 | 福岡県北九州市八幡西区岡田町1-1 |

4件を `ShrineIdentity` として `verify_recommendation_eligibility(shrine_identities=...)` へ渡した。

補助確認として、4社とも同名の Shrine は DB 上に1行のみで、同名別住所の行は存在しない。

---

## 3. `--batch W0-DB03` を使わなかった理由

```text
python manage.py verify_recommendation_eligibility --batch W0-DB03
```

は**意図的に実行していない**。

- W0-DB03 の original membership は5社（Mother Ship Decision A により監査履歴として保持）
- canonical identity（`official_name` / `official_address`）を持つのは G4 で hydrate した4社のみ
- `wave0-014` は G3 `MODEL_CHANGE_REQUIRED` のため未 hydrate
- `--batch` は batch の candidate 数と canonical identity 数が一致しない場合に fail closed する。
  5 != 4 で失敗するのは正しい挙動である

`--batch` を通すために wave0-014 を hydrate することはしない。代わりに、同じ verifier service へ
承認済み4社の canonical identity だけを明示的に渡した。

---

## 4. Isolated DB setup

```text
database : w0db03_g5（本 G5 専用に新規作成）
host     : localhost:5432（サンドボックス内 PostgreSQL 16 + PostGIS）
engine   : django.contrib.gis.db.backends.postgis
lineage  : temples/migrations（標準 GIS lineage）
code     : develop@f58b184（working tree clean）
```

| Step | Command | 結果 |
| --- | --- | --- |
| 1 | `migrate --noinput` | EXIT 0（`temples` leaf = `0115_canonical_anchor_schema_foundation`） |
| 2 | `bootstrap_production_data` | EXIT 0。3 step すべて SUCCESS。Shrine total 117 |
| 3 | `import_shrine_knowledge wave0_batch_03_seed.json --validate-only` | `validate-only: OK, no errors` |
| 4 | 同 `--dry-run` | `{'source_CREATE': 4, 'deity_CREATE': 18, 'history_CREATE': 5}` |
| 5 | 同 apply | `sources created=4, deities created=18, histories created=5` |

Base Seed は develop の canonical `shrines_seed_clean.json`（117行）を bootstrap 経由でそのまま投入した。
Knowledge は W0-DB03 の Knowledge Seed のみを投入した。

Production への接続・書き込みはない。`DATABASE_URL` は上記 scratch DB のみを指す。

---

## 5. Verifier output（逐語）

```text
Shared Recommendation Eligibility Verification (read-only)
authority: docs/knowledge/recommendation-eligibility-contract.md

大神神社 / 奈良県桜井市三輪1422       ELIGIBLE    id=114  usable_deity=1  usable_history=1
北野天満宮 / 京都府京都市上京区馬喰町      ELIGIBLE    id=115  usable_deity=3  usable_history=1
平安神宮 / 京都府京都市左京区岡崎西天王町97  ELIGIBLE    id=116  usable_deity=2  usable_history=2
岡田宮 / 福岡県北九州市八幡西区岡田町1-1   ELIGIBLE    id=117  usable_deity=12  usable_history=1

requested  = 4
ELIGIBLE   = 4
INELIGIBLE = 0
UNRESOLVED = 0
ALL_ELIGIBLE = PASS
```

`report.as_dict()["summary"]`:

```json
{
  "requested_count": 4,
  "eligible_count": 4,
  "ineligible_count": 0,
  "unresolved_count": 0,
  "all_eligible": true
}
```

---

## 6. Per-shrine result

| candidate_id | Shrine | Shrine id | status | usable_deity_fact_count | usable_history_fact_count | usable_fact_count | G4 expectation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wave0-012 | 大神神社 | 114 | ELIGIBLE | 1 | 1 | 2 | 1 / 1 一致 |
| wave0-013 | 北野天満宮 | 115 | ELIGIBLE | 3 | 1 | 4 | 3 / 1 一致 |
| wave0-015 | 平安神宮 | 116 | ELIGIBLE | 2 | 2 | 4 | 2 / 2 一致 |
| wave0-016 | 岡田宮 | 117 | ELIGIBLE | 12 | 1 | 13 | 12 / 1 一致 |

実測値は G4 の Evidence 記録と完全一致した（期待値へ合わせる操作は行っていない）。

## 7. Summary / Acceptance

| 条件 | 期待 | 実測 | 判定 |
| --- | --- | --- | --- |
| requested_count | 4 | 4 | PASS |
| eligible_count | 4 | 4 | PASS |
| ineligible_count | 0 | 0 | PASS |
| unresolved_count | 0 | 0 | PASS |
| all_eligible | true | true | PASS |

### Read-only / 再現性

verifier の2回目の実行前後で、次の値が完全一致した。

```text
Shrine 117 / Shrine max(updated_at) 不変 / GoriyakuTag 39 / Deity 18 / History 5 / Source 4
pg_stat_user_tables の insert + update + delete 累計 = 9429（前後で不変）
```

2回目の verifier 出力は1回目と逐語一致した。

---

## 8. Candidate-set boundary

4社について、確認したのは次の範囲だけである。ranking / score 比較は実行していない。

| 項目 | 確認 | 根拠 |
| --- | --- | --- |
| 共有 Recommendation candidate set へ参加できる | YES | 共有 gate `filter_recommendation_eligible_candidates()` へ `{"id": 114..117}` を渡し、4件すべてが通過（`passed ids: [114, 115, 116, 117]`） |
| eligibility は ranking score を付与しない | YES | gate 通過後の候補 dict に追加された key は 0（`keys added by gate: []`）。`is_recommendation_eligible()` は bool のみを返す。契約上 eligibility は ranking signal ではない |
| Top1 保証 | なし | eligibility は candidate set の境界であり順位を決めない |
| Purpose match 保証 | なし | Purpose / Need の評価は ranking 側の責務で、G5 の対象外 |
| legacy goriyaku / history_theme fallback が必要か | 不要 | 4社とも usable Knowledge Fact で eligible。`is_recommendation_eligible()` は legacy field から eligibility を推定しない |

---

## 9. wave0-014 exclusion

```text
wave0-014 宮城縣護國神社
G3 = MODEL_CHANGE_REQUIRED
G4 = NOT EXECUTED
G5 = NOT EXECUTED
```

- 本 G5 の verifier 入力に含めていない
- isolated DB 上にも Shrine 行は存在しない（`name_jp="宮城縣護國神社"` の行 = 0）
- **INELIGIBLE とは分類しない。** eligibility を判定していないため、状態は `G5 NOT EXECUTED` である
- hydrate / import / eligible としての試験のいずれも行っていない

---

## 10. Not executed / Not changed

```text
Production DB                               NOT ACCESSED / NOT WRITTEN
verify_recommendation_eligibility --batch   NOT RUN（§3）
G6 Runtime QA                               NOT EXECUTED
  - Concierge runtime QA                    なし
  - Compass direction / distance QA         なし
  - Shrine Detail display QA                なし
Ranking / score comparison                  NOT EXECUTED
Recommendation eligibility logic            UNCHANGED
Evidence Gate                               UNCHANGED
Candidate Master / Base Seed / Knowledge Seed UNCHANGED
Compass / schema / migration                UNCHANGED
wave0-014                                   UNCHANGED
```

---

## 11. Final

```text
W0_DB03_G5_PASS_4_OF_4

G5_PASS          = wave0-012 / wave0-013 / wave0-015 / wave0-016
G5_NOT_EXECUTED  = wave0-014（upstream G3 MODEL_CHANGE_REQUIRED）
NEXT             = G6 Runtime QA（別 PR / 別指示）
```
