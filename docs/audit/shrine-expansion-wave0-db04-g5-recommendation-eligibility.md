# W0-DB04 G5 Shared Recommendation Eligibility

## 1. Status

```text
W0_DB04_G5 = PASS_3_OF_3（execution subset）

wave0-019 建勲神社   = G5 PASS（ELIGIBLE、usable Deity 2 / History 5）
wave0-021 大阪天満宮 = G5 PASS（ELIGIBLE、usable Deity 1 / History 3）
wave0-025 大崎八幡宮 = G5 PASS（ELIGIBLE、usable Deity 3 / History 4）
```

G5 PASS は Gate Contract §8 の意味に限る（「Candidate setへ参加するための構造条件を満たす」）。
Ranking 上位・Top1・Purpose match・Need score を意味しない。

本書は次の3つを分けて記録する。

| 観点 | 結果 | 節 |
|---|---|---|
| G5 eligibility（判定式） | 3 / 3 ELIGIBLE → **G5 PASS** | §13、§17 |
| Scoring-path quality（`score_need`） | 3社とも scoring に到達するが `score_need = 0`（F1、G5 の判定対象外） | §14、§15 |
| Runtime candidate-pool reachability | Compass: 到達 / Concierge 既定: scratch 再現では非到達、Production は未測定（F2、G5 の判定対象外） | §14、§19 |

F1 / F2 はいずれも G5 の判定式（eligibility predicate）の外にあり、本書では修正していない。
F1 は**未解決**であり、Mother Ship により G6 前の一時 HOLD が置かれている（§21）。
F2 は local で確認した挙動であり、**Production への影響は未測定**である。

- G6 Runtime QA / G7 / G8: **NOT EXECUTED**（G6 は PRE_G6_HOLD。§21）
- Candidate lifecycle: **変更なし**
- Production access / write: **NONE**

## 2. Execution date

`2026-10-04`

## 3. Branch

`audit/shrine-expansion-wave0-db04-g5-recommendation-eligibility`

## 4. Base SHA

`develop@ac8d1b438452db01c7a34c382cf00600f74091f3`（PR #3074 merged）

## 5. Governing contracts

| 領域 | 正本 |
|---|---|
| G5 の位置づけ / PASS の意味 | `docs/knowledge/shrine-expansion-gate-contract.md` §8 |
| Shared Recommendation Eligibility（G5 authority） | `docs/knowledge/recommendation-eligibility-contract.md` |
| Fact usability | `backend/temples/services/evidence_gate.py` + `docs/knowledge/shrine-knowledge-contract.md` |
| Upstream G4 | `docs/audit/shrine-expansion-wave0-db04-g4-reentry.md` |
| Precedent | `docs/audit/shrine-expansion-wave0-db03-g5-recommendation-eligibility.md` |

Gate Contract §8 の現行文言（本書で適用したもの）:

```text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1

FAIL: INELIGIBLEのShrineをfallbackでRecommendationへ戻さない。
      Legacy goriyaku / history_theme でEligibilityを代替しない。
```

Recommendation Eligibility Contract の現行文言:

```text
Shrine DB presence != Recommendation eligibility
Recommendation eligibility = at least one usable Deity or History Fact
Shared eligibility != F5 Qualified Evidence gating != ranking signal
ineligible Shrine: legacy Shrine.goriyaku / Shrine.history_theme から eligibility を推定しない
```

W0-DB03 precedent の判定方法は現行 code と照合し、変わっていないことを確認した上で使った（§9）。

## 6. Dependency on merged PR #3074

- PR #3074（`ac8d1b4`）の Candidate Master / Base Seed（120行）/ `wave0_batch_04_seed.json` を入力として使った。
  内容は承認済み commit `e2b1aec` と同一（`git diff` で確認）。
- G4 結果: `W0_DB04_G4_PASS_3_OF_3`、Fact Evidence 18 / 18 usable。

## 7. Execution subset

| candidate_id | Shrine | canonical identity（name_jp / address） |
|---|---|---|
| wave0-019 | 建勲神社 | 京都府京都市北区紫野北舟岡町49 |
| wave0-021 | 大阪天満宮 | 大阪府大阪市北区天神橋2丁目1番8号 |
| wave0-025 | 大崎八幡宮 | 宮城県仙台市青葉区八幡4-6-1 |

## 8. Excluded candidates

| candidate_id | Shrine | 理由 | 本書での扱い |
|---|---|---|---|
| wave0-020 | 水堂須佐男神社 | G2 `HOLD_POSITION_REVIEW` | G5 NOT EXECUTED。isolated DB に Shrine 行なし（0行）。INELIGIBLE とは分類しない |
| wave0-022 | 毛谷黒龍神社 | G3 `MODEL_REVIEW_REMAINS` | 同上 |

## 9. Runtime eligibility path（現行 code で確認）

| # | 項目 | 現行 code |
|---|---|---|
| 1 | Entry point | `temples/services/concierge_chat_candidates.py` `build_chat_candidates_with_eligibility()`。Concierge は `build_chat_candidates()`（薄い adapter）経由で `api_views_concierge.py` `_build_chat_candidates_pipeline()` から、Compass は `compass_recommendation_orchestrator.py` から直接呼ぶ |
| 2 | Eligibility predicate | `is_recommendation_eligible(knowledge_deities, knowledge_histories)` = `bool(deities) or bool(histories)`。唯一の判定式 |
| 3 | Fields read by predicate | `shrine_knowledge_selector.fetch_fact_ready_knowledge_deities()` / `_histories()` が返す usable Fact list のみ。各 Fact は `evidence_gate.decide_fact_usability()`（Fact の `verification_status` / `confidence`、relation 先 Source の `verification_status`）を通過したもの |
| 4 | Required mappings | なし。predicate は goriyaku / NEED / consultation_axis の mapping を要求しない |
| 5 | Exclusion conditions | usable Deity と usable History がともに 0 件 → ineligible（低スコアで残さない、fallback しない）。shrine id 未解決の request 由来候補 → fail closed |
| 6 | Fallback behavior | なし。ineligible の埋め戻しも legacy field からの推定もしない |
| 7 | Deity / History Knowledge | 参加する（判定入力そのもの） |
| 8 | goriyaku / goriyaku_tags | **predicate には参加しない**。ただし predicate より前の source pool 構築で、request が `goriyaku_tag_ids` を明示した場合だけ `qs.filter(goriyaku_tags__id__in=...)` が効く（ユーザーの明示条件。Level 3-B Explicit Constraint） |
| 9 | consultation_axis / Need mapping | **predicate には参加しない**。gate 通過後の scoring（`concierge_chat.build_chat_recommendations()` → `NEED_TO_GORIYAKU_IDS` 経由の `score_need`）で使われる |
| 10 | Scoring への到達 | gate 通過候補は Concierge では `build_chat_recommendations()`、Compass では direction filter 後の ranking へ渡る |

Gate より前に効く source pool 構築（`build_chat_candidates_with_eligibility()`）:

```text
qs = Shrine.objects.all()
   [+ filter(goriyaku_tags__id__in=goriyaku_tag_ids)]   ← request が明示した場合のみ
   [+ area 文字列 filter]                                ← 座標がない場合のみ
   -> exclude_qa_fixture_shrines()
   -> filter(latitude/longitude not null).exclude(address="")
   -> order_by("-popular_score", "id")
   -> [:pool_limit]   pool_limit = max(limit * 5, 50)    ← gate と距離 sort より前
   -> Shared Recommendation Eligibility gate
   -> 距離 / 人気順 sort
```

`pool_limit` slice が gate より前に効くことは Recommendation Eligibility Contract「pool_limit との関係」に明記されている。

## 10. Fields consumed

| 層 | 読む field |
|---|---|
| Eligibility predicate | `ShrineDeity` / `ShrineHistory` の `verification_status` / `confidence`、relation 先 `ShrineKnowledgeSource.verification_status` |
| Source pool（gate 前） | `latitude` / `longitude` / `address` / `popular_score` / `id`、QA fixture 判定、（明示時のみ）`goriyaku_tags` |
| 読まない（predicate） | `goriyaku` / `goriyaku_tags` / `history_theme` / NEED / consultation_axis / F5 Evidence qualification |

## 11. Mapping dependencies

```text
Eligibility predicate が要求する mapping = NONE
```

W0-DB04 用に凍結されていない mapping（goriyaku_tags / NEED 対応）を G5 で要求されることはない。

## 12. Per-candidate stored inputs（isolated DB 実測）

Isolated DB: scratch PostgreSQL 16（NoGIS migration 系列）、`develop@ac8d1b4`。
`bootstrap_production_data`（3 step すべて SUCCESS、Shrine 120 / GoriyakuTag 39）の後、repository の Knowledge Seed
16 件をすべて import した（Source 132 / Deity 293 / History 226、collective 6 / membership 23）。

| candidate | Shrine id | 行数（name + address） | 同名行 | lat / lng | goriyaku | goriyaku_tags | history_theme | popular_score | Deity / History（DB） |
|---|---|---|---|---|---|---|---|---|---|
| wave0-019 | 118 | 1 | 1 | 35.0386537 / 135.7431512 | `""` | [] | `""` | 0.0 | 2 / 5 |
| wave0-021 | 119 | 1 | 1 | 34.6958917 / 135.5126472 | `""` | [] | `""` | 0.0 | 1 / 3 |
| wave0-025 | 120 | 1 | 1 | 38.2725678 / 140.8449622 | `""` | [] | `""` | 0.0 | 3 / 4 |

Shrine id は scratch DB の値であり identity ではない。

## 13. Per-candidate eligibility result

Read-only verifier（`recommendation_eligibility_verifier.verify_recommendation_eligibility()`）へ
3件の canonical identity を渡した出力（逐語）:

```text
Shared Recommendation Eligibility Verification (read-only)
authority: docs/knowledge/recommendation-eligibility-contract.md

建勲神社 / 京都府京都市北区紫野北舟岡町49     ELIGIBLE    id=118  usable_deity=2  usable_history=5
大阪天満宮 / 大阪府大阪市北区天神橋2丁目1番8号  ELIGIBLE    id=119  usable_deity=1  usable_history=3
大崎八幡宮 / 宮城県仙台市青葉区八幡4-6-1    ELIGIBLE    id=120  usable_deity=3  usable_history=4

requested  = 3
ELIGIBLE   = 3
INELIGIBLE = 0
UNRESOLVED = 0
ALL_ELIGIBLE = PASS
```

- `verify_recommendation_eligibility --batch W0-DB04` は fail closed した
  （「5件中 3件しか canonical identity を持たない」）。W0-DB04 の original membership は5社、hydrate 済みは3社のため、
  これは正しい挙動である（W0-DB03 precedent §3 と同じ）。--batch を通すために 020 / 022 を hydrate しない。
- 共有 gate への直接適用: `filter_recommendation_eligible_candidates([{"id": 118}, {"id": 119}, {"id": 120}])` → 3件すべて通過、
  gate が候補 dict に追加した key = 0（score を付与しない）。
- `partition_recommendation_eligible_shrines()`: source 3 / eligible 3 / ineligible 0。
- usable Fact 数は G4 の Evidence 記録（7 / 4 / 7）と一致した。

| candidate | Knowledge | usable Deity | usable History | consumed inputs | predicate | exclusion |
|---|---|---:|---:|---|---|---|
| wave0-019 | あり | 2 | 5 | usable Deity / History list | ELIGIBLE | なし |
| wave0-021 | あり | 1 | 3 | 同上 | ELIGIBLE | なし |
| wave0-025 | あり | 3 | 4 | 同上 | ELIGIBLE | なし |

## 14. Per-candidate scoring-path reachability

Runtime の共有 builder（`build_chat_candidates_with_eligibility()`）を、手組みの object ではなく isolated DB の実データで実行した。

| 実行条件 | source | eligible | ineligible | 019 | 021 | 025 |
|---|---:|---:|---:|---|---|---|
| Concierge 既定（limit=20 → pool_limit=100）、座標なし | 100 | 86 | 14 | OUT | OUT | OUT |
| Concierge 既定、origin = 各神社自身の座標（3通り） | 100 | 86 | 14 | OUT | OUT | OUT |
| Compass（candidate_pool_limit=60 → pool_limit=300） | 120 | 106 | 14 | IN | IN | IN |
| limit=200（pool_limit=1000、DB 全体） | 120 | 106 | 14 | IN | IN | IN |
| 明示条件 `goriyaku_tag_ids=[1]`、limit=200 | 38 | 34 | 4 | OUT | OUT | OUT |

- `OUT` はいずれも gate より前（source pool 構築）で落ちたものであり、eligibility predicate の結果ではない（§19 F2）。
- `goriyaku_tag_ids` を明示した request では、goriyaku_tags を持たない3社は source pool に入らない（§15 F1）。

Scoring への到達（builder が返した候補 dict を `build_chat_recommendations(llm_enabled=False)` へ渡した reachability probe。
順位・品質は判定していない）:

| need_tags | wave0-025 大崎八幡宮 | 対照: 北野天満宮（W0-DB03、tag 6） | 対照: 大神神社（W0-DB03、tag 6） |
|---|---|---|---|
| study | score_need 0 / matched [] | 1 / ["study"] | 0 / [] |
| protection | 0 / [] | 1 / ["protection"] | 1 / ["protection"] |
| health | 0 / [] | 0 / [] | 1 / ["health"] |

- 3社とも scoring 処理へ到達し breakdown を持つ（3社だけを渡した probe でも、need の有無に関わらず `score_need = 0`、`matched_need_tags = []`）。
- 対照の W0-DB03 神社は同じ経路で `score_need = 1` を得る。差は goriyaku_tags の有無である。

| candidate | shared candidate pool | scoring path |
|---|---|---|
| wave0-019 | Compass: YES / Concierge 既定: NO（scratch 再現）/ Production: 未確定（§19 F2） | 到達 YES / Need score 0 |
| wave0-021 | 同上 | 同上 |
| wave0-025 | 同上 | 同上 |

## 15. goriyaku boundary result

```text
D. G5 には無関係。ただし G6 / G8 の下流 blocker として残る
```

根拠（current contract + runtime）:

- Gate Contract §8 と Recommendation Eligibility Contract は、legacy goriyaku から eligibility を推定することを禁止している。
- `is_recommendation_eligible()` は goriyaku / goriyaku_tags を読まない（§9）。3社は goriyaku_tags = [] のまま ELIGIBLE になった（§13）。
- したがって A（G5 を block）ではない。contract と runtime は一致しているので C（mismatch）でもない。
  G4 の結論を流用したものではなく、G5 の contract と runtime から独立に導いた。

**F1: Need score path がない（下流 blocker）**

- goriyaku_tags がないため、gate 通過後の scoring で `NEED_TO_GORIYAKU_IDS` 経由の `score_need` が常に 0 になる（§14）。
- `goriyaku_tag_ids` を明示した Concierge request では source pool から外れる（§14）。
- Wave0 Data Build Plan の Post-Import QA（Concierge「safe tagに対応するNeedでscore pathが存在する」、
  Goriyaku「expected goriyaku_tags set」）を、G6 / G8 で満たせない見込みである。
- Layer: **MAPPING**（goriyaku typed evidence / taxonomy mapping = `HOLD_MODEL_BOUNDARY`）。

## 16. Contract / runtime consistency result

```text
CONSISTENT
```

| Contract の要求 | Runtime |
|---|---|
| eligibility = usable Deity OR usable History | `is_recommendation_eligible()` が唯一の判定式 |
| usable 判定は Evidence Gate へ委譲 | selector → `decide_fact_usability()` |
| legacy goriyaku / history_theme から推定しない | predicate は読まない |
| eligibility は ranking signal ではない | gate は候補 dict に key を追加しない（score 付与 0） |
| Concierge / Compass の分岐の手前で1回だけ適用 | 共有 builder 内で適用。request 由来候補は同じ関数で再適用 |
| ineligible を埋め戻さない / fail closed | 実装どおり |
| pool_limit slice は gate より前 | 実装どおり（Contract「pool_limit との関係」に記載済み） |

eligibility と ranking は code 上分離されている（判定は bool のみ、score は後段）。

## 17. Formal candidate G5 result

| candidate | predicate | G5 |
|---|---|---|
| wave0-019 建勲神社 | ELIGIBLE（Deity 2 / History 5） | **PASS** |
| wave0-021 大阪天満宮 | ELIGIBLE（Deity 1 / History 3） | **PASS** |
| wave0-025 大崎八幡宮 | ELIGIBLE（Deity 3 / History 4） | **PASS** |

## 18. Batch-level G5 result

```text
W0_DB04_G5 = PASS_3_OF_3（execution subset）
wave0-020 = G5 NOT EXECUTED（G2 HOLD_POSITION_REVIEW）
wave0-022 = G5 NOT EXECUTED（G3 MODEL_REVIEW_REMAINS）
```

## 19. Failure classification

G5 の不合格: **なし**。

G5 の外で記録する観測:

| ID | 観測 | Layer | W0-DB04 固有か | G5 への影響 |
|---|---|---|---|---|
| F1 | goriyaku_tags がなく、Need score path がない（§15） | MAPPING | W0-DB04 固有（goriyaku `HOLD_MODEL_BOUNDARY`） | なし（G6 / G8 blocker 見込み） |
| F2 | Concierge 既定の source pool から外れる | RECOMMENDATION（source pool 構築） | **No**（既存の挙動） | なし（Contract 記載済みの gate 前 slice） |

**F2 の詳細:**

- `build_chat_candidates_with_eligibility()` は `order_by("-popular_score", "id")[:pool_limit]` を gate と距離 sort より前に適用する。
  Concierge 既定（`DEFAULT_LIMIT = 20` → `pool_limit = 100`）では、並び順で101位以降の Shrine は利用者の位置に関係なく
  gate に到達しない。
- Isolated DB（120 Shrine、`popular_score` はすべて 0.0、つまり id 順）では、pool から外れた20社はすべて eligible だった。
  - id 101〜103: 北海道神宮 / 建部大社 / 波上宮
  - W0-DB01〜DB03 の14社（id 104〜117）: 三輪神社 / 大鳥大社 / 御岩神社 / 烏森神社 / 榴岡天満宮 / 射水神社 / 別小江神社 /
    戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社 / 大神神社 / 北野天満宮 / 平安神宮 / 岡田宮
  - W0-DB04 の3社（id 118〜120）
- `popular_score` を書くのは手動 command `recalc_popular_shrines`（views / favorites から算出）だけで、repository 内に定期実行の
  設定は見当たらない。Production の `popular_score` 分布と Shrine 数は local で再現できない。
  したがって **Production の Concierge 既定 pool に3社が入るかどうかは本書では確定できない**。
- Compass（`pool_limit = 300`）では3社とも pool に入る。

```text
F2 status
  isolated / local runtime : CONFIRMED（上記 scratch DB で再現）
  Production impact        : NOT YET MEASURED（Production の defect とは確認していない）
```

## 20. Next remediation boundary

G5 の修正は不要である。本書では何も修正していない。下流へ進む前の最小タスク:

1. **F1（MAPPING、未解決）:** goriyaku architecture の判断（typed evidence storage か、凍結した taxonomy mapping か）を、
   別 task / 別 PR で行う。G6 実行の前提条件である（§21 PRE_G6_HOLD）。本 PR の範囲外であり、goriyaku_tags を推測で作らない。
2. **F2（RECOMMENDATION）:** まず Production の read-only 測定を行う（Mother Ship 実行。`popular_score` 分布と、
   Concierge 既定 pool に W0-DB01〜DB04 の Shrine が入るか）。修正が必要なら Gate Contract §16 に従い
   Recommendation Quality PR として分ける。Data Build PR に混ぜない。

## 21. Downstream authorization / prohibition

```text
PRE_G6_HOLD = ACTIVE（Mother Ship decision）
```

- G5 PASS は gate chain 上の前進を許すが、Mother Ship は G6 の前に一時 HOLD を置いた。
  解除条件は **F1 の解決**（goriyaku architecture の判断と、その結果の反映）である。
- **G6 Runtime QA は現時点で authorize しない。** F1 解決後、Mother Ship の明示指示で着手する。
- F2 は本 G5 PR を閉じる前提ではない。別の read-only Recommendation Quality audit（Production 測定）で扱う。

Prohibited（本書の範囲外）:

- G6 / G7 / G8 の実行
- Recommendation / ranking / pool_limit / Concierge / Compass の変更
- goriyaku_tags / NEED mapping / taxonomy の作成・変更
- Knowledge Seed / Base Seed / Candidate Master の変更
- `FACT_READY` / `IMPORTED` / `CORE_READY` への昇格
- wave0-020 / wave0-022 の変更・評価

Candidate Master（本書時点）: 019 / 021 / 025 は `BUILD_READY` / knowledge_status 既定値のまま（変更なし）。

## 22. Production write

```text
Production DB access = NONE
Production write     = NONE
```

## Validation

- 変更ファイル: 本書のみ（data / code / test の変更なし）。
- Eligibility 経路の focused tests（`test_shared_recommendation_eligibility.py` / `test_recommendation_eligibility_verifier.py` /
  `test_concierge_build_chat_candidates_contract.py` / `test_w0_db01_eligibility_reproduction.py` /
  `test_compass_direction_only_core.py`）+ `test_wave0_db04_shrine_seed.py` + `test_shrine_expansion_candidate_master.py`: 203 passed。
- `git diff --check`: pass。
