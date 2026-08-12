> **Status: `KNOWLEDGE_RECOMMENDATION_ANALYTICS_PROPERTIES_READY_WITH_LIMITATIONS`。**
>
> [knowledge-recommendation-analytics-contract.md](knowledge-recommendation-analytics-contract.md)
> の最小価値PR（22章）を実装した。既存の`recommendation_quality`イベントへ
> 3 property（`knowledge_backing_class`/`deity_knowledge_used`/
> `history_knowledge_used`）を追加し、PR #2382の
> `build_shrine_reason_provenance()`をそのまま再利用した。新規イベント・
> 新規分類ロジックの実装はゼロ。Ranking/Score/Recommendation本文/UIは
> 一切変更していない。Production writeゼロ。

---

## 1. develop SHA

`d4d461daa72bda6aadcfab61f9de4fed822bd707`（2026-08-12 12:42:04 +0900）

PR #2383（[knowledge-recommendation-analytics-contract.md](knowledge-recommendation-analytics-contract.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Modified Files

| ファイル | 変更内容 |
|---|---|
| `backend/temples/services/concierge_chat.py` | `_attach_recommendation_reason_quality()`で`build_shrine_reason_provenance()`（PR #2382既存関数）を呼び出し、`recommendation_reason_quality` dictへ3 propertyを追加 |
| `apps/web/src/lib/api/concierge/types.ts` | `RecommendationReasonQuality`型へ3 optional propertyを追加、`KnowledgeBackingClass`型を新規定義 |
| `apps/web/src/lib/analytics/searchEvents.ts` | `RecommendationQualityAnalyticsPayload`型へ同3 propertyを追加 |
| `apps/web/src/features/concierge/hooks.ts` | `trackRecommendationQualityFromRecommendations()`で3 propertyを`?? null`フォールバック付きで転送。同関数をexport化（テスト目的のみ、ロジック変更なし） |
| `backend/temples/tests/services/test_recommendation_reason_quality_knowledge_properties.py`（新規） | 10テスト |
| `apps/web/src/features/concierge/__tests__/trackRecommendationQualityFromRecommendations.test.ts`（新規） | 9テスト |

新規イベントの追加・既存イベント名の変更・UI変更・DB migrationはいずれも
含まれない。

---

## 3. `recommendation_quality`既存Property（変更なし）

```
source, threadId, shrineId, recommendationRank, accessLevel,
shrine_data_rate, consultation_reflection_rate, fallback_reason_rate,
evidence_rate, action_grounding_rate, is_ai_inference_only, fallback_source
```

---

## 4. 追加Property

```
knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED" | "PARTIALLY_KNOWLEDGE_BACKED"
                          | "LEGACY_BACKED" | "UNKNOWN"
deity_knowledge_used: boolean
history_knowledge_used: boolean
```

---

## 5. Provenance Reuse（Phase 4）

`_attach_recommendation_reason_quality()`は既に`_build_score_v3_candidate_profile(rec)`
を呼んでいた箇所と同じ`rec`（Recommendation候補dict）をそのまま
`recommendation_quality_measurement.build_shrine_reason_provenance()`
（PR #2382で実装済み）へ渡すだけで、新しい判定ロジックは一切実装していない。

```python
from temples.services.recommendation_quality_measurement import (
    build_shrine_reason_provenance,
)
...
provenance = build_shrine_reason_provenance(rec)
quality["knowledge_backing_class"] = provenance.classification
quality["deity_knowledge_used"] = provenance.deity_status == "KNOWLEDGE_USED"
quality["history_knowledge_used"] = provenance.history_status == "KNOWLEDGE_USED"
```

**循環import対応**: `recommendation_quality_measurement.py`は
`concierge_chat._build_score_v3_candidate_profile`をモジュールトップレベルで
importするため、`concierge_chat.py`側で同モジュールをトップレベルimportすると
循環importになる。関数内（`_attach_recommendation_reason_quality()`の内部）で
importすることで解決した（Pythonの標準的な遅延import解決パターン、
両モジュールの既存構造・責務分離は変更していない）。

---

## 6-9. 分類ごとの挙動

| classification | deity_knowledge_used | history_knowledge_used | 確認テスト |
|---|---|---|---|
| `FULLY_KNOWLEDGE_BACKED` | true または false（片方でも可） | 同左 | `test_fully_knowledge_backed_deity_only`, `test_fully_knowledge_backed_history_only`, `test_both_deity_and_history_knowledge_used` |
| `PARTIALLY_KNOWLEDGE_BACKED` | Knowledge/Legacyが混在 | 同左 | `test_partially_knowledge_backed` |
| `LEGACY_BACKED` | false | false | `test_legacy_backed` |
| `UNKNOWN` | false | false | `test_unknown_when_no_facts` |

`history_theme`（Legacy分類タグ）単独存在時に誤ってKnowledge/Legacy判定
されないことも回帰ガードとして固定化した
（`test_history_theme_alone_does_not_flip_knowledge_backing_class`）。

---

## 10. Privacy結果（Phase 11/13）

新規3 propertyはいずれも列挙値・booleanのみで構成され、Fact本文
（deity表示名・shrine_history本文）・Source URL・publisher名・相談本文は
一切含まれない。

- Backend: `test_quality_payload_does_not_leak_source_url_or_raw_fact_text`
- Frontend: `Fact本文・Source URL・相談本文に相当するkeyをpayloadへ含めない`

いずれもテストで確認済み。

---

## 11. Backward Compatibility

- 既存7 propertyの値・型は変更していない
  （`test_existing_quality_keys_are_preserved`、
  `既存の7 propertyは変更されない`）。
- 新規3 propertyが未定義の場合、Frontend側は`?? null`でフォールバックし、
  既存の`serializeSearchAnalyticsPayload()`のnull-stripping契約
  （`searchEvents.ts`）によりpayloadから自動的に除外される
  （新規propertyが存在しない古いBackendレスポンスでもFrontendは壊れない）。
- `recommendation_quality`イベント名・発火タイミング・発火回数は変更して
  いない。

---

## 12. Recommendation Behavior Regression

`_attach_recommendation_reason_quality()`はRanking確定後、reason_text/
qualityメタデータを候補dictへ付与するだけの処理であり、候補リスト・
順位・スコアには一切触れない。変更ファイルに`concierge_chat_ranking.py`・
`recommendation_algorithm_v3.py`・`recommendation_score_v2.py`は含まれない
（2章のModified Files参照）。

---

## 13. Ranking / Score Regression

- `SCORE_V3_MODE`・`_score_total`計算式・`resolve_score_sort_key`は無変更。
- Score v3関連テスト（`test_score_v3_history_signal.py`等5ファイル）を含む
  Backend全テストスイート実行で確認: **1147 passed, 9 skipped**
  （GDAL/PostGIS環境依存、既存から不変）、失敗0件。

---

## 14. Analytics Regression

- `recommendation_quality`以外のイベント（`concierge_result_impression`/
  `shrine_detail_transition`/`shrine_decision`/`route_open`/`visit_done`等）
  は本PRで一切変更していない。
- `recommendation_quality`イベント自体も、発火回数・発火タイミング・
  event名は不変。追加されるのはpayloadの3 propertyのみ。

---

## 15. Tests

| 対象 | テスト数 | 結果 |
|---|---:|---|
| `test_recommendation_reason_quality_knowledge_properties.py`（新規） | 10 | 全pass |
| `apps/web/.../trackRecommendationQualityFromRecommendations.test.ts`（新規） | 9 | 全pass |
| Backend全体（`temples/`） | 1147（新規10含む） | 全pass（9 skip、既存から不変） |
| Frontend全体（`apps/web`） | 740（新規9含む） | 全pass（116 test files） |
| TypeScript型検査（`tsc --noEmit`） | — | エラー0件 |

---

## 16. Remaining Gaps（Phase 15、意図的に未対応のまま残す）

- `visit_done`のrank/resultSetId欠落
  （[knowledge-recommendation-analytics-contract.md](knowledge-recommendation-analytics-contract.md)
  5章、`ATTRIBUTION_GAP`）
- Retry/相談再入力イベントの新規追加（同12章、`FUNNEL_EVENT_GAP`）
- PostHog Dashboard実装（同21章、`DASHBOARD_GAP`）
- Sample-sizeの具体的根拠（同19章、`SAMPLE_SIZE_NOT_YET_DEFINED`）
- Shadow Ranking Comparison（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
  PR候補B）
- Recommendation Quality改善そのもの（本PRは計測基盤のみ、推薦文言・
  ロジックの改善は含まない）

---

## 17. Final Classification

**`KNOWLEDGE_RECOMMENDATION_ANALYTICS_PROPERTIES_READY_WITH_LIMITATIONS`**

Backend/Frontendとも実装完了、新規19テスト全pass、既存1147+740テストの
回帰なし、TypeScript型検査エラー0件、Ranking/Score/Recommendation本文/
UIいずれも無変更を確認した。16章の残存Gapは本PRのスコープ外として
明示的に残す。

Production writes = 0
Recommendation behavior changes = 0
Ranking changes = 0
