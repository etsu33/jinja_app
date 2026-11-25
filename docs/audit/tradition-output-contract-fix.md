> **Status: Active**
>
> 本ドキュメントは`docs/audit/recommendation-fact-integrity-negative-pilot.md`のPhase 12「Mother Ship Decisions Required」で提起された`RECOMMENDATION_REASON_CONTRACT_GAP`（Tradition Confidence Gap）への対応記録である。契約自体の正本は`docs/core/recommendation-reason-contract.md`「Fact表現強度（confidence / history_type）」を参照する。

# Tradition Output Contract Fix

## 背景

前回のReal Negative Evidence Pilotで、`recommendation_reason_v4.py`の
confidence→表現強度変換は`history_type`を一切見ていないことをコードレベルで確認した。
`history_type="tradition"`（Source自身が伝承と明記した記述）のFactでも、
`confidence=high`であれば断定表現（assertive）テンプレートが適用され、
伝承が確定史実であるかのように出力される可能性がある。この時点では
`content`本文を手動でhedge表現込みに執筆することで回避していたが、
執筆規律への依存であり、システムによる保証ではなかった。

## Mother Ship Gate

以下は母艦から固定されたDecisionであり、本Auditでは変更しない。

- Phase 1: `TRADITION_ALWAYS_HEDGED` — `history_type="tradition"`はconfidenceに関わらず断定表現禁止
- Phase 5: `KEEP_FULL_SUPPRESSION_FOR_NOW` — `CONFIDENCE_MIXED`の現行挙動（全suppression）は変更しない
- Phase 6: `KEEP_CURRENT_EVIDENCE_LEVEL` — 阿佐ヶ谷神明宮の`secondary_editorial`祭神のconfidenceは変更しない

## Phase 2 — Runtime Audit（実施結果）

`history_type`がRecommendation Reason V4まで渡っているかを追跡した結果:

| 層 | history_typeの扱い | 結果 |
|---|---|---|
| `shrine_knowledge_selector.fetch_fact_ready_knowledge_histories()` | dictへ含めて返す | 保持されている |
| `concierge_chat._pick_primary_knowledge_history_content/_confidence()` | `content`/`confidence`のみ抽出 | **ここで消失** |
| `concierge_chat._build_score_v3_candidate_profile()` | `shrine_history`/`shrine_history_confidence`のみ設定 | history_type未設定 |
| `recommendation_reason_v4._build_fact()` | `shrine_history_confidence`のみ参照 | history_typeを受け取る手段自体が無かった |

情報が失われる層は`concierge_chat.py`（selector→candidate_profile変換部）であり、
`shrine_knowledge_selector.py`自体は改修不要と判明した。

## Phase 3 — Implementation Design

候補A（Fact payloadへhistory_type保持）は既にselector層で満たされていたため対象外。
候補B（selector段階でtradition flagへ変換）は、selector側へ「表現戦略の判断」という
Reason生成の責務を混入させることになり、Fact取得責務（selectorのdocstringが明記する
「Factを使えるか判断する責務はevidence_gateへ一本化」という既存分離）と衝突するため不採用。

**候補C（Reason builderへ明示的にhistory_typeを渡す）を採用した。**
理由:

- Fact責務を維持: selector/candidate_profile builderは値の受け渡しのみを行い、
  「tradition→hedge」の判断はこれまでconfidence→strength変換を行ってきた
  `recommendation_reason_v4.py`内に閉じる（既存の責務境界と一致する）
- Source/raw metadataをReasonへ露出しない: `history_type`はFact自身のenum値であり
  Source metadataではない。既にShrine Detail APIでも公開されている情報。
- existing deity pathを壊さない: `deity`にはhistory_type概念が無く無関係
- migration不要: `history_type`はモデルに既存のfield、新規列は追加していない
- Score/Rankingへ影響しない: `recommendation_reason_v4.py`はReason生成専用であり、
  スコアリング・ランキングを一切扱わない

具体的な変更:

- `backend/temples/services/concierge_chat.py`: `_pick_primary_knowledge_history_type()`を追加し、
  `candidate_profile["shrine_history_type"]`として（confidenceと同一選定基準のHistory 1件から）値を渡す
- `backend/temples/services/recommendation_reason_v4.py`: `_apply_tradition_hedge_floor()`を追加し、
  `history_type == "tradition"`かつ`reason_strength == "assertive"`の場合のみ`"weakened"`へ引き下げる
  （`suppressed`は最も安全側のためそのまま維持し、引き上げはしない）

`_build_fact_text()`自体は変更していない。既存の`weakened`分岐（「〜と伝えられています」）が
そのまま使われるため、テンプレート文言の追加・変更は不要だった。

## Phase 4 — Regression Tests

新規: `backend/temples/tests/services/test_tradition_output_contract.py`（6件、全てPASS）

| ケース | 結果 |
|---|---|
| tradition + high → hedged | PASS（新規で保護） |
| tradition + medium → hedged | PASS（既存契約のまま、回帰なし） |
| historical_event + high → assertive可 | PASS（floor対象外、回帰なし） |
| founding + high → 現行契約維持 | PASS（floor対象外と明示、回帰なし） |
| tradition + low → suppressed維持（weakenedへ引き上げない） | PASS（floorの片方向性を確認） |
| Legacy fallback → history_type概念自体が無くfloor不作用 | PASS（PR-B契約と同じ扱い） |

既存回帰（disputed/sourceなし→suppression、deity high/medium現状維持）は
`test_reason_strength_pilot_and_regression.py`・`test_reason_strength_mixed_confidence.py`
含むバックエンド全1031テストで再確認済み（0 failure、9 skip[PostGIS/GDAL未導入起因のみ]）。

## Phase 5 — CONFIDENCE_MIXED（Decision: KEEP_FULL_SUPPRESSION_FOR_NOW）

現行挙動を変更していない。実データfixtureとして再確認した結果:

```
阿佐ヶ谷神明宮: deity = 天照大神、月読命、須佐之男命 / confidence = __mixed__
  → fact.deity = None（suppressed、reason_textはgenericフォールバックへ）
```

DB全体で複数Deityかつconfidence不一致のshrineは1件（阿佐ヶ谷神明宮のみ）。
high subsetのpartial assertionは別Audit候補として送る（本Auditでは実装しない）。
Score/Rankingは変更していない。

## Phase 6 — Secondary Deity（Decision: KEEP_CURRENT_EVIDENCE_LEVEL）

阿佐ヶ谷神明宮の月読命・須佐之男命（`secondary_editorial`/`medium`）はconfidenceを変更していない。
公式Sourceが見つかるまで`high`へ格上げしない。Fact削除もしていない。
mixed suppression回避を目的としたconfidence変更は行っていない。

## Phase 7 — KPI再計測

対象: `build_chat_candidates()`が返す全100件（QA fixture除外後の監査対象Shrine）。

| KPI | 値 |
|---|---|
| Knowledge Coverage | 21/100（21.0%） |
| Verified Source Count | 36 |
| Unsupported Claim Rate | 0/100（0%） — 全Fact-ready出力がKnowledge selectorまたはLegacy由来であることを確認 |
| Tradition Misstatement Rate（fix後） | 0/13（0%） — Fact-ready tradition History 13件、全てassertiveへ到達しないことを確認 |
| Disputed Fact Usage Rate | 0%（Evidence Gate仕様上、disputedはFact-ready集合に含まれない。既存テストで保証） |
| Source-less Fact Usage Rate | 0%（Evidence Gate仕様上、Source未確認のFactはusable=Falseで除外。既存テストで保証） |
| Mixed Confidence Suppression Rate | 1/1（100%） — 複数confidence混在Deityを持つShrine 1件中1件がsuppressedになることを確認（阿佐ヶ谷神明宮） |
| Zero-Knowledge Fallback成功率 | 79/79（100%） — Knowledge未登録79件全てでreason_text生成が例外なく成功 |

### Tradition Misstatement Rateの実測（fix前後比較）

fix前のロジック（`_reason_strength_from_confidence()`のみ、`history_type`未参照）で
同じ100件を再計算したところ、以下5件が実際に`assertive`（断定表現）に該当していたことを確認した。

```
三峯神社 / 出雲大社 / 妙義神社 / 武蔵御嶽神社 / 鹿島神宮（いずれもconfidence=high, history_type=tradition）
```

この5件はいずれも同じShrineに`deity` Factも存在するため、`_build_fact_text()`の
deity優先ルールにより`reason_text`上には実際には出力されていなかった（結果的に無事故）。
ただし`fact.shrine_history`（構造化出力、`recommendation_reason_v4_detail.fact.shrine_history`
としてAPIにも露出する）自体は`content`そのままであり、deity非存在のshrineが将来1件でも
Fact-readyになれば、reason_text上に断定表現として出力されるリスクが現実だった。
今回の修正によりこの5件を含む全13件のtradition Factが、confidenceに関わらずhedge表現の
対象になることを確認した（deityの有無に依存しない構造的な保証へ変わった）。

## Phase 8 — Final Classification

`FACT_INTEGRITY_READY_WITH_LIMITATIONS`
+ `TRADITION_OUTPUT_CONTRACT_FIXED`（前回の`RECOMMENDATION_REASON_CONTRACT_GAP`を解消）
+ `MIXED_CONFIDENCE_POLICY_DEFERRED`（high subset partial assertionは未着手のまま、別Audit候補）

Fact Integrityの構造的な安全性（Evidence Gate、Source-less/disputed排除、
CONFIDENCE_MIXED suppression、Tradition hedge floor）は確認できたが、
以下は依然として未解決であり「Ready for Rollout」への昇格条件ではない。

- `low confidence`/`disputed`の実データ実例がDB全体でゼロ
- Mixed Confidence partial assertionポリシー自体が未確定
- Knowledge Coverageは21/100に留まる（Batch 4以降は本Audit範囲外）

## Phase 9 — Stop

本Auditでは以下へ進まない。

- Batch 4着手
- 81社一括投入
- Mixed confidence partial assertion実装
- user-facing Source citation UI
- confidence UI
- Score/Ranking変更
- Readiness candidate gateへの接続

## Repository Changes

- `backend/temples/services/concierge_chat.py`: `_pick_primary_knowledge_history_type()`追加、`candidate_profile["shrine_history_type"]`追加
- `backend/temples/services/recommendation_reason_v4.py`: `_apply_tradition_hedge_floor()`追加、`_build_fact()`内で適用
- `backend/temples/tests/services/test_tradition_output_contract.py`: 新規（6テスト）
- `docs/core/recommendation-reason-contract.md`: 「Fact表現強度（confidence / history_type）」節追加、禁止事項に1件追加
- `docs/knowledge/shrine-knowledge-contract.md`: 3軸分離節へRecommendation Reason側強制への相互参照を追加
- `docs/audit/tradition-output-contract-fix.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Evidence Gate判定ロジック/API contract/Score/Ranking: 変更なし
- DB書き込み: なし（本Auditは既存local DBデータの読み取り測定のみ）
