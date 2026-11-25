> **Status: `INSUFFICIENT_SESSION_DIVERSITY`（変化なし）。**
>
> [Recommendation Quality再計測条件を監査](posthog-recommendation-quality-observation-cadence.md)
> （`INSUFFICIENT_SESSION_DIVERSITY`）で設計した再計測条件を、**固定の
> 観測運用契約（Observation Operations Contract）として明文化**する。
> 新機能実装ではない。現在のProduction状態（`recommendation_quality`=3・
> distinct threadId=1）は前回監査から変化しておらず、単一threadのため
> 品質比較は引き続き禁止のまま。本ドキュメントは、今後この監査サイクル
> を繰り返すたびに参照する固定契約として機能する。

---

## 1. Base State（Phase 0）

- **PR #2394** merge確認済み（`79dcebb4`、2026-08-12 09:36:04 UTC）
- develop最新化・origin/developと同期・working tree clean
- **HEAD SHA**: `7228d10b15f98217310bb8c182a8de13c6b5ef64`

**Base State時の発見（記録のため明記）**: develop HEADには、本タスク
開始時点でPR #2395（`Audit/posthog production event reachability`、
2026-08-12 09:39:12 UTC merge）も含まれていた。調査の結果、これは
本セッション中盤で誤って生成した孤立ブランチ
（`audit/posthog-production-event-reachability`、PR #2391 merge後に
追記コミットをpushしてしまったもの）に対しGitHub側が自動生成した
PRであり、その時点で内容は既にPR #2392経由でdevelopへ反映済み
だったため、**mergeによるファイル変更は0件**（`git diff-tree
--no-commit-id --name-only -r 7228d10b`が空、
`docs/audit/posthog-production-event-reachability.md`の内容もbyte
単位で一致）であることを確認した。重複・破損は存在しない。

- `scripts/analytics_safety/`のdrift確認: PR #2390以降変更なし
- Foundation tests: **90 passed**
- credential gate: PASS（値・project id・hostname非表示）

---

## 2. Current State Recheck（Phase 1）

`2026-08-12T04:12:15Z` 〜 `2026-08-12T09:42:00Z`でfresh再実行。

| 指標 | 値 | 前回（PR #2394時点）比 |
|---|---|---|
| `recommendation_quality`総件数 | 3 | 変化なし |
| distinct threadId（`recommendation_quality`内） | **1** | 変化なし |
| `FULLY_KNOWLEDGE_BACKED` | 2 | 変化なし |
| `UNKNOWN` | 1 | 変化なし |
| `PARTIALLY_KNOWLEDGE_BACKED` / `LEGACY_BACKED` | 0 / 0 | 変化なし |
| property completeness | 3/3・3/3・3/3（0%欠損） | 変化なし |
| `concierge_result_impression` | 3 | 変化なし |
| `shrine_detail_transition` | 2 | 変化なし |
| `save_count` / `route_open_count` | 0 / 0 | 変化なし |

raw event rowは取得していない（すべてaggregate count / GROUP BY /
count(DISTINCT)）。新規の自然利用トラフィックは本監査時点でも到達
していない。

---

## 3. Observation Operations Contract（Phase 2）— 固定契約

以下を今後の観測運用における**固定契約**として明文化する:

1. **独立sessionの定義**: `threadId`（= backend `ConciergeThread.id`）。
   `resultSetId`はフロントエンド一時的なde-dup keyのため使用しない
   （[observation-cadence監査](posthog-recommendation-quality-observation-cadence.md)
   4章で確定済み）。
2. **再計測条件**: 「**複数独立thread（`threadId`）の自然利用が蓄積
   したこと**」に固定する。「一定日数後」には依存しない。
3. **sample数threshold**: 根拠のない固定数値は新設しない。
   `SAMPLE_SIZE_THRESHOLD_NOT_DEFINED`を維持する。
4. **単一thread時の運用規則**: distinct threadId = 1の間は、
   **segmented funnel分析（CTR/save率等のKnowledge分類別比較）を
   停止する**。本監査でもこの規則を適用し、2章の再確認以降の分析を
   停止した。

---

## 4. Recheck Trigger（Phase 3）

| 確認項目 | 定義 | 現状 |
|---|---|---|
| 新しい自然利用の発生確認方法 | 本監査と同じ`posthog_baseline_report.py` + ad-hoc aggregate queryをrolloutSince〜現在時刻で再実行し、`recommendation_quality`総件数・distinct threadId数の増減を比較する | 2章で実施、変化なし |
| 次段階へ進む条件 | distinct threadId数が**1より増えた場合のみ** | 未達（引き続き1） |
| classification diversity（session横断） | 複数threadにまたがって異なるclassificationが観測されること（単一thread内の複数値では不十分） | 未評価（thread数が1のため評価不能） |
| property completeness 100%維持 | `property_completeness`queryで3propertyとも欠損0%を確認 | ✅ 維持（2章） |

---

## 5. Segmented CTR Gate（Phase 4）

Join key契約（`threadId`/`shrineId`/`recommendationRank`）をfresh
確認した。1章の通り、develop HEAD更新（PR #2395の実質no-op merge）
以外にコード変更はなく、
[observation-cadence監査](posthog-recommendation-quality-observation-cadence.md)
7章で確認した内容から**drift なし**（`concierge_result_impression`/
`shrine_detail_transition`/`recommendation_quality`はいずれも
`threadId`/`shrineId`/`recommendationRank`を保持）。

- FULLY/PARTIALLY/LEGACY/UNKNOWN別impression取得可否: 理論上可能
  （`GROUP BY knowledge_backing_class`のみ）だが、**複数threadが
  存在する場合のみ**実行候補とする（3章の運用規則）。
- 同分類別detail_transition取得可否: 同様。
- raw row JOINは行っていない（0回）。
- **現状判定**: distinct threadId = 1のため、本monitoring段階では
  aggregate query実行候補にすら**該当しない**。実行は見送った。

---

## 6. Save Gate（Phase 5）

[observation-cadence監査](posthog-recommendation-quality-observation-cadence.md)
8章の発見をfresh再確認した（コード変更なし、1章のdrift確認により
裏付け済み）。

- `shrine_decision`(action=save, `ShrineSaveButton.tsx:65`)は
  `rank`/`recommendationRank`を**一切持たない**ことを再確認。
- property名は`threadId`ではなく**`tid`**であり、他イベント
  （`concierge_result_impression`等）との名称不一致が引き続き存在
  することを再確認。
- **現時点で`JOIN_READY_WITH_LIMITATIONS`を維持**する。

---

## 7. Visit Intent Gate（Phase 6）

同じく[observation-cadence監査](posthog-recommendation-quality-observation-cadence.md)
9章の発見をfresh再確認した。

- `route_open`（`GoogleMapRouteLink.tsx:57`）: `threadId`/`shrineId`
  は保持するが**`rank`/`recommendationRank`は引き続き欠落**。
- `visit_done`（`ShrineDetailArticle.tsx:732`）: `threadId`/`shrineId`
  は保持するが**`rank`/`resultSetId`は引き続き欠落**。
- 両者とも**`JOIN_READY_WITH_LIMITATIONS`を維持**。event schema
  変更は行っていない。

---

## 8. UNKNOWN Monitoring（Phase 7）

- `UNKNOWN`件数のみaggregate確認: **1**（2章、変化なし）。
- 個別event追跡は行っていない（0回）。
- UNKNOWN増加率は、母数が3件のみの現時点では**評価しない**
  （指示通り）。
- `classify_provenance()`のロジック（deity/history両fieldが
  `EMPTY`の場合に`UNKNOWN`を返す）が正常な分類であることは
  [observation-cadence監査](posthog-recommendation-quality-observation-cadence.md)
  10章で整理済みであり、本監査でも維持する。

---

## 9. Decision Gate（Phase 8）

| 条件 | 判定 |
|---|---|
| distinct thread = 1 | ✅ 該当 → **`INSUFFICIENT_SESSION_DIVERSITY`** |
| distinct thread > 1 かつ分類多様性あり | 該当せず |
| segmented funnel安全実行可能 | 該当せず |
| schema不足 | 該当せず（既知のjoin limitation〈6〜7章〉はschema"gap"ではなく既存の設計上の制約として区別する） |

**判定: `INSUFFICIENT_SESSION_DIVERSITY`**（前回監査から変化なし）。

---

## 10. No Premature Changes（Phase 9）

以下はいずれも本監査で**行っていない**: Recommendation Reason変更・
Ranking変更・Score v3 active化・Analytics event変更・Dashboard実装・
Knowledge Model変更。

---

## 11. Security（Phase 10）

```
$ gitleaks detect --source docs/audit/recommendation-quality-observation-operations.md --no-git -v
no leaks found
```

credential・project id・hostname・raw event・PIIはいずれも非表示・
非取得。`git diff --check`でdoc-only変更を確認。

---

## Final Classification

**`INSUFFICIENT_SESSION_DIVERSITY`**

[Recommendation Quality再計測条件を監査](posthog-recommendation-quality-observation-cadence.md)
で設計した再計測条件を固定運用契約として明文化した。現在のthread数は
引き続き**1**であり、Production baseline（`recommendation_quality`=3・
`FULLY_KNOWLEDGE_BACKED`=2・`UNKNOWN`=1・property completeness=100%）
は前回監査から変化していない。次のdecision trigger（3〜4章）は
「distinct threadId数が1より増えること」であり、根拠のない数値
thresholdは`NOT_DEFINED`のまま維持する。Save/Visit Intent側の
join limitation（6〜7章）はいずれも`JOIN_READY_WITH_LIMITATIONS`を
維持し、event schema変更は行っていない。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
Score v3 active化 = 0
Analytics event変更 = 0
