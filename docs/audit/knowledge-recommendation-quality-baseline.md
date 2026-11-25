> **Status: `KNOWLEDGE_RECOMMENDATION_QUALITY_BASELINE_READY_WITH_LIMITATIONS`。**
>
> Knowledge推薦理由の品質を再現可能な指標として計測できるFoundation
> （measurement service・tests・CLI report entry point）を追加した。
> Recommendation candidate / ranking / score / reason生成 / action suggestion
> のいずれも変更していない（read-only observer）。Production write・
> Recommendation Runtime POSTは一切実行していない。

---

## 1. develop SHA

`cd1bf881b8202a8bc1ade1068efe7f4dfaa2384f`（2026-08-12 12:15:43 +0900）

PR #2381（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Measurement Definition（分類契約）

[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
で定義した4分類を、実際のReason生成ロジック
（`concierge_chat._build_score_v3_candidate_profile` /
`recommendation_reason_v4._build_fact`）を直接再利用する形でコード化した
（`temples/services/recommendation_quality_measurement.py`）。

分類はfield（deity/shrine_history）単位の`FieldStatus`
（`KNOWLEDGE_USED`/`LEGACY_USED`/`EMPTY`）から決定する:

| deity_status | history_status | classification |
|---|---|---|
| KNOWLEDGE_USEDを含み、LEGACY_USEDを含まない | | `FULLY_KNOWLEDGE_BACKED` |
| KNOWLEDGE_USEDとLEGACY_USEDを両方含む | | `PARTIALLY_KNOWLEDGE_BACKED` |
| LEGACY_USEDを含み、KNOWLEDGE_USEDを含まない | | `LEGACY_BACKED` |
| 両方EMPTY | | `UNKNOWN` |

`FieldStatus`の判定（`_field_status()`）:

- `fact[field] is None`（Reason生成内部でsuppress済み、またはそもそも値がない）→ `EMPTY`
- `fact[field]`が非None かつ `candidate_profile[f"{field}_confidence"] is not None`（Knowledge由来） → `KNOWLEDGE_USED`
- `fact[field]`が非None かつ `candidate_profile[f"{field}_confidence"] is None`（Legacy fallback由来） → `LEGACY_USED`

**重要**: confidence=low/mixedでsuppressされたKnowledge Factは`EMPTY`扱いとし、
`LEGACY_USED`とは区別する。「Knowledgeが存在したが表示されなかった」ことと
「Legacyが使われた」ことを混同しない。

---

## 3. Dataset

Production write禁止のため、以下2種類のデータセットのみを使用した。

### 3.1 Unit-level fixture（`test_recommendation_quality_measurement.py`）

21テストケース。complete/partial/none/deity-only/history-only/mixed-fallback/
suppressed-low-confidence/mixed-confidence-sentinelの各パターンを個別の
candidate dictとして構築し、分類の正確性を検証した。

### 3.2 Local dev DB（`127.0.0.1/jinja_db`、Production ではない）

`python manage.py measure_knowledge_recommendation_quality`をローカル開発DBに
対して実行した（書き込みなし、SELECT のみ）。**このDBはProductionではない**
（`DATABASES['default']['HOST'] == '127.0.0.1'`で確認済み）。

sample_count=100・Fact-ready Deity+History合計415件・全件`source_confirmed`
という結果は、Batch 16 Production Import Execution Record
（[knowledge-batch16-production-import-execution.md](knowledge-batch16-production-import-execution.md)、
Deity 233 + History 182 = 415）と完全に一致する。このため、このローカルDBは
Batch 16実行時点のProductionスナップショットに由来すると推定されるが、
**本タスクでは live Productionとの同一性を追加検証していない**
（Shrine総数が下記4章の通りProduction側とは異なるため、完全な同一DBではない）。

---

## 4. Production Read-only Feasibility（Phase 15）

`scripts/migration_safety/readonly_query.sh`（既存の安全なread-onlyチャネル）
経由でProduction実データを直接確認した（2026-08-12、書き込みなし）:

| 項目 | Production実測値 |
|---|---:|
| audit target shrine数（QA fixture除外後） | 104 |
| Fact-ready ShrineDeity数 | 233 |
| Fact-ready ShrineHistory数 | 182 |
| うち`source_confirmed` | 415/415（100%） |

Fact件数（415、全件`source_confirmed`）は3.2のローカルDB結果と完全一致した。
一方、audit target shrine数はProduction=104、ローカルDB=100と一致しない
（ローカルDBがBatch 16以降に追加された非Knowledge神社を含んでいない
可能性が高い）。

**分類判定（FULLY/PARTIALLY/LEGACY/UNKNOWN）自体をライブProductionに対して
実行することは、本タスクでは行っていない。** 理由:

- 本measurementのcore関数（`_build_score_v3_candidate_profile`/`_build_fact`）
  はDjango ORMのモデルインスタンスではなくdictを扱うが、実データ取得には
  Django ORM（`Shrine.objects.filter(...)`等）を使う設計である。ライブ
  ProductionへDjango ORM接続するには`DATABASE_URL`をProduction向けに切り替える
  必要があり、これは本セッションで確立された`readonly_query.sh`
  （SQL文自体をread-onlyかguard.pyで検証してから接続する）とは異なる、
  より緩やかなアクセス経路になる。
- 代替として分類ロジックを生SQLで再実装する案は、Reason生成の実装
  （`_build_fact`のsuppression・confidence変換）との重複・driftを生むため
  意図的に避けた（このモジュール自体の設計方針そのものと矛盾するため）。

**分類: `PRODUCTION_RECOMMENDATION_BASELINE_NOT_AVAILABLE`**（分類breakdownの
み。Fact件数・verification_status等の集計値は上表の通りread-onlyで直接
確認済み）。

---

## 5. Baseline Measurement（ローカルDB実測値、Production代表値ではない点に注意）

`python manage.py measure_knowledge_recommendation_quality --format json`
（ローカル`jinja_db`、2026-08-12）:

| 指標 | 値 |
|---|---:|
| sample_count | 100 |
| fully_knowledge_backed | 85（85.00%） |
| partially_knowledge_backed | 0（0.00%） |
| legacy_backed | 0（0.00%） |
| unknown | 15（15.00%） |
| knowledge_backed_rate（Fully+Partially） | 85.00% |
| deity_knowledge_usage_rate | 85.00% |
| history_knowledge_usage_rate | 84.00% |
| deity_legacy_fallback_rate | 0.00% |
| history_legacy_fallback_rate | 0.00% |
| source_confirmed_fact_rate | 415/415（100.00%） |

`partially_knowledge_backed`・`legacy_backed`がいずれも0件である点は、
このローカルDBに`sajin`/`description`（Legacy由来fallback元）を持つ神社が
1件も含まれていないことを示唆する。**これは「Legacy fallbackが本番で
機能していない」ことの証拠ではなく、このローカルDBのデータ内容の特徴**
である（4章の通りProduction側との完全同一性は確認していない）。

---

## 6. Quality Guard Metrics（Phase 9）

generic wording率・duplicate phrase率は、既存コードに文字列類似度・
一般性判定の仕組みが存在しないため本PRには含めない。
`NEXT_PR_CANDIDATE`として記録する（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
Phase 15のQuality Measurement PR候補と統合可能）。

---

## 7. Recommendation Behavior Regression（Phase 10-11）

- 既存ファイルへの変更は一切なし（新規ファイル3件のみ追加）。
- `temples/`配下の既存テストスイート全件を実行し、**1137 passed, 9 skipped
  （GDAL/PostGIS環境依存のskipのみ、既存から不変）**、失敗0件を確認した。
- Score v3関連テスト（`test_score_v3_history_signal.py`/
  `test_score_v3_feature_flag.py`/`test_score_v3_observer.py`/
  `test_score_v3_observation_summary.py`/`test_score_v3_dashboard_api.py`）を
  含め全件成功。current score（`_score_total`）・shadow score（`score_v3`）・
  rank・`SCORE_V3_MODE`のいずれも本PRで一切変更していない
  （`concierge_chat_ranking.py`・`concierge_chat.py`・
  `recommendation_algorithm_v3.py`への変更なし）。
- `measure_knowledge_recommendation_quality`コマンド自体もSELECTのみで構成され
  （`build_recommendation_quality_measurement_report`内で`.save()`/`.create()`/
  `.delete()`等の書き込みAPIを一切呼び出さない）、read-only observerであることを
  `test_report_builder_is_read_only_and_classifies_db_backed_shrines`で
  レコード数不変を明示的に確認した。

---

## 8. Analytics Linkage 再確認（Phase 16）

[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
12章の`KNOWLEDGE_RECOMMENDATION_PRODUCT_EFFECT_NOT_MEASURED`は本PRでも
変化なし。本PRで追加した`knowledge_backed_rate`等のmeasurement出力は、
`route_open`/`visit_done`/`reflection_saved`/`shrine_decision`等の行動指標
イベントとは現状joinできる共通キー（shrineId等をイベント側が送っていても、
本PR出力側にthreadId/timestampが存在しない）を持たない。

**分類: `KNOWLEDGE_ANALYTICS_LINKAGE_MISSING`**（本PRでは実装しない、
Analytics実装は絶対禁止事項のため）。

---

## 9. Acceptance Criteria（Phase 17）

| 条件 | 結果 |
|---|---|
| deterministic classification | PASS（`test_aggregate_measurements_is_deterministic`） |
| history_theme collision防止 | PASS（3テスト: history_theme単独/Knowledge併存/Legacy description併存） |
| recommendation behavior不変 | PASS（既存ファイル変更0、全1137テストpass） |
| ranking不変 | PASS（ranking関連コード変更0） |
| score不変 | PASS（score関連コード変更0） |
| measurement tests PASS | PASS（21/21） |
| existing recommendation tests PASS | PASS（1137/1137、9 skipはGDAL/PostGIS環境依存で既存から不変） |
| report生成PASS | PASS（`--format text`/`--format json`とも動作確認済み） |
| Production write 0 | PASS（新規コードにwrite操作なし、Production接続自体もreadonly_query.sh経由のSELECTのみ） |

---

## 10. 既知の計測限界（Limitations）

1. ライブProductionに対する分類breakdown（FULLY/PARTIALLY/LEGACY/UNKNOWN内訳）
   の直接実行は行っていない（4章、`PRODUCTION_RECOMMENDATION_BASELINE_NOT_AVAILABLE`）。
   Fact件数・verification_status distributionのみread-only直接確認済み。
2. ローカルDBの結果（5章）はBatch 16時点のProductionスナップショットに由来する
   可能性が高いが、Shrine総数の不一致（100 vs 104）により完全な同一性は
   未確認。Production代表値として扱ってはならない。
3. generic wording率・duplicate phrase率は計測未実装（6章、`NEXT_PR_CANDIDATE`）。
4. Analytics（行動指標との相関）は引き続き計測不可（8章）。
5. `_build_score_v3_candidate_profile`/`_build_fact`の"private"関数を意図的に
   直接importしている。これらの関数のsignatureが将来変更された場合、本
   モジュールも追従が必要になる（テストスイートで検知可能）。

---

## 11. Next PR Candidates（Phase 19、優先順位は決定しない）

A. **Analytics Contract**: `knowledge_backed_rate`等の計測結果をAnalytics
   イベント（`route_open`/`visit_done`/`reflection_saved`等）とjoin可能に
   する共通キー設計（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
   PR候補Bと同一）。

B. **Shadow Ranking Comparison**: 既存`score_v3_shadow_observation`を候補
   集合全体へ拡張する設計の実装（同PR候補C）。

C. **Reason Quality Improvement**: 6章のQuality Guard Metrics
   （generic wording率・duplicate phrase率）の計測実装。

D. **Runtime Evidence UX**: Source/confidence/roleをWeb Detail画面へ
   表示する対応（[post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md)
   Track B）。

---

## 12. Final Classification

**`KNOWLEDGE_RECOMMENDATION_QUALITY_BASELINE_READY_WITH_LIMITATIONS`**

measurement service・tests（21件）・CLI report entry point・本baseline
audit docを作成した。Recommendation behavior（candidate/ranking/score/
reason/action suggestion/API response）はいずれも変更していない
（既存1137テスト全件pass）。Production writeは0件。

上記10.の限界（特にライブProductionでの分類breakdown未実行）は、次の
実装PR着手前に解消可否を検討すべき事項として引き継ぐ。**本Baselineは
次のPR候補（11章）のどれを選ぶべきかを結論づけない。**
