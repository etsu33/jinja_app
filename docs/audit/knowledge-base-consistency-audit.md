# Knowledge Base Consistency Audit

## 1. 目的

## 2. 監査対象


## 3. 監査上の記載区分

本監査では、事実・推測・設計判断を混在させないため、以下の区分で記録する。

### 3.1 事実（Fact）

リポジトリ内のドキュメント、コード、DB定義から直接確認できる内容。

例：

- `history_theme` は `Shrine` モデルに保持されている
- `goriyaku_tags` が現行DBに存在する
- `Recommendation Readiness` が `shrine-data-guide.md` に定義されている

監査では、確認可能な内容のみを記載する。

---

### 3.2 実装事実（Implementation Fact）

現行実装の挙動から確認できる内容。

ドキュメントと一致しているかは問わず、実際のコードを正本として記録する。

例：

- Recommendation生成時に `history_theme` が利用されている
- `goriyaku_tag_ids` がスコア計算へ渡されている
- `consultationSummary` が表示用コピーとして生成されている

ドキュメントとの差異がある場合は、その差異も併せて記録する。

---

### 3.3 推測（Inference）

事実および実装事実から合理的に推測できる内容。

十分な根拠があるものの、コードや仕様として明文化されていない事項を指す。

例：

- 将来的に `culture_translation` が Meaning Layer に属すると考えられる
- `confidence` は Trust Layer の責務として扱われる可能性が高い

推測は、必ず根拠となる事実または実装事実を併記する。

---

### 3.4 仮説（Hypothesis）

今後検証が必要な設計案や改善案。

現時点では採用を決定していないものを記録する。

例：

- `Trust` を独立モデルとして分離する
- `Reflection` 専用モデルを追加する
- `Recommendation Readiness` を自動算出へ変更する

仮説は実装前提とせず、検証対象として扱う。

---

### 3.5 仕様判断（Design Decision）

本監査において採用する設計方針。

複数案を比較した結果、採用すると決定した内容を記録する。

例：

- Runtime情報は神社固定プロフィールへ保存しない
- Recommendationの責務は Meaning Layer と分離する
- Stored / Derived / Runtime / Governance の4分類を採用する

仕様判断は、以降のドキュメントおよび実装の基準（Single Source of Truth）として扱う。

## 4. 用語差分

### 4.1 目的

Knowledge Base 8文書で使用される用語を比較し、
表記揺れ・責務の重複・意味の不一致を抽出する。

Glossary を用語定義の正本（Single Source of Truth）とし、
他文書との差分を確認する。

### 4.2 監査対象

- README
- shrine-profile-spec
- shrine-data-guide
- meaning-layer-spec
- recommendation-copy-guide
- action-guide
- reflection-guide
- glossary

### 4.3 確認観点

- 表記揺れ
- 同義語
- 未定義用語
- 定義の不一致
- 責務の重複

### 4.4 監査結果

| 用語 | 定義元 | 利用箇所 | 差分 | 優先度 |
|------|--------|----------|------|--------|

## 5. Stored / Derived / Runtime / Governance対応表

### 5.1 目的

Knowledge Base に登場する概念項目を、
Stored / Derived / Runtime / Governance の4分類へ整理する。

各項目の責務を統一し、
保存対象・計算対象・実行時のみ利用する情報を明確にする。

### 5.2 分類ルール

#### Stored

DBへ永続保存する情報。

対象例：

- Shrine Profile
- history_theme
- goriyaku_tags
- deity
- place_context

---

#### Derived

Stored情報から計算・生成できる情報。

対象例：

- Recommendation Readiness
- Coverage
- culture_translation
- completeness_score

---

#### Runtime

推薦実行時のみ利用し、永続保存しない情報。

対象例：

- consultation_result
- recommendation_reason
- action_suggestion
- reflection_question
- score_v3

---

#### Governance

データ品質・運用管理のための情報。

対象例：

- source
- verified_at
- confidence
- trust_level

### 5.3 監査結果

| 項目 | 現在の分類 | 妥当性 | 修正要否 | 備考 |
|------|------------|--------|----------|------|

## 6. レイヤー依存関係監査

### 6.1 目的

Knowledge Base に定義される各レイヤーの責務と依存関係を確認し、
責務の重複・逆方向依存・循環依存を抽出する。

### 6.2 対象レイヤー

- Fact
- Meaning
- Consultation
- Recommendation
- Action
- Reflection

### 6.3 想定依存関係

```text
Fact
↓
Meaning
↓
Consultation
↓
Recommendation
↓
Action
↓
Reflection
```

### 6.4 確認観点

- 上位レイヤーが下位レイヤーへ依存していないか
- 事実と解釈が混在していないか
- Recommendation が Fact を直接参照していないか
- Action が Recommendation を経由しているか
- Reflection が Recommendation を再定義していないか

### 6.5 監査結果

| レイヤー | 依存先 | 妥当性 | 修正要否 | 備考 |
|----------|--------|--------|----------|------|

## 7. 現行DB対応表

### 7.1 目的

Knowledge Base の概念項目と現行DBの物理フィールドを対応付け、
保存済み・未実装・再利用可能な項目を整理する。

### 7.2 対象モデル

- Shrine
- Favorite
- Visit
- ShrineReflection
- ConciergeThread
- その他関連モデル

### 7.3 対応区分

- 完全対応
- 部分対応
- 未対応
- Runtimeのみ
- Governanceのみ

### 7.4 対応表

| 概念項目 | 現行DB | 対応状況 | 保存区分 | 備考 |
|----------|---------|----------|----------|------|

## 8. 未実装概念

### 8.1 目的

Knowledge Base に定義されているが、
現行実装では未対応となっている概念を整理する。

### 8.2 分類

- P0（実装優先）
- P1（次フェーズ）
- P2（将来検討）

### 8.3 確認観点

- DB未実装
- Runtimeのみ存在
- ドキュメントのみ存在
- Governance未実装
- Trust Layer未実装

### 8.4 一覧

| 概念 | 現状 | 優先度 | 対応方針 | 備考 |
|------|------|--------|----------|------|

## 9. 重複責務

### 9.1 目的

Knowledge Base内で複数文書が同一責務を持っていないかを確認し、
責務境界を明確化する。

### 9.2 確認観点

- 同じ概念が複数文書で管理されていないか
- 正本（Single Source of Truth）が一意になっているか
- 派生文書が正本を書き換えていないか

### 9.3 監査結果

| 責務 | 重複文書 | 正本候補 | 修正要否 | 備考 |
|------|----------|----------|----------|------|

## 10. 矛盾する必須条件

### 10.1 目的

Knowledge Base 8文書間で、必須条件・前提条件・責務定義が矛盾していないかを確認する。

### 10.2 確認観点

- MUST / SHOULD / Optional の不一致
- 同一項目の必須条件の違い
- レイヤー責務の矛盾
- Runtime / Stored の扱いの矛盾
- Recommendation条件の不一致

### 10.3 監査結果

| 対象 | 文書 | 矛盾内容 | 優先度 | 対応方針 |
|------|------|----------|--------|----------|

## 11. Recommendation Readiness監査

### 11.1 目的

Recommendation Readiness の定義・計算条件・利用箇所を整理し、
Knowledge Base全体で単一の定義へ統一する。

### 11.2 確認観点

- Readiness定義
- Coverageとの関係
- sourceとの関係
- verified_atとの関係
- confidenceとの関係
- Ready判定条件
- 利用箇所

### 11.3 監査結果

| 項目 | 現状 | 問題点 | 修正方針 | 優先度 |
|------|------|--------|----------|--------|

## 12. Trust / source / verified_at監査

### 12.1 目的

Trust Layer の責務を整理し、
保存対象・運用対象・Runtime対象を明確化する。

### 12.2 確認観点

- source
- verified_at
- confidence
- trust_level
- 更新責務
- 保存責務

### 12.3 監査結果

| 項目 | 現状 | 保存区分 | 修正要否 | 備考 |
|------|------|----------|----------|------|

## 13. P0 / P1 / P2分類

### 13.1 目的

監査結果を優先順位ごとに整理し、
実装フェーズへ引き継ぐ。

### 13.2 分類基準

#### P0

リリース前に必須。

#### P1

実装優先度は高いが、P0完了後でも問題ない。

#### P2

将来対応・運用改善。

### 13.3 分類結果

| 項目 | 優先度 | 理由 | 次PR |
|------|--------|------|------|

## 14. DB適用設計

### 14.1 目的

Knowledge Baseで定義した概念項目を、現行DBへどのように適用するかを整理する。

既存フィールドの再利用、新規フィールド追加、別モデル化、Runtimeの非保存を分離し、
実装前に物理設計の責務を明確にする。

### 14.2 設計区分

- 既存フィールドを再利用
- 既存フィールドを拡張
- 新規フィールドを追加
- 別モデルとして分離
- Runtimeのため保存しない
- Governanceとして保持方法を別途決定

### 14.3 フィールド型の判断基準

#### TextField

単一の説明文、由緒、解釈文など、順序を持つ文章を保存する場合に使用する。

#### JSONField

構造がまだ変化する可能性があり、複数の属性を一括で保持する必要がある場合に使用する。

ただし、検索・集計・参照整合性が必要な項目を恒久的にJSONFieldへ閉じ込めない。

#### ManyToManyField

複数の神社で共有され、検索・絞り込み・集計に利用するタグや分類に使用する。

#### 別モデル

出典、確認履歴、更新者、複数レコード、監査履歴など、
独立したライフサイクルを持つ情報に使用する。

### 14.4 適用候補

| 概念項目 | 現行DB | 適用方針 | 候補型 | 優先度 | 備考 |
|----------|---------|----------|--------|--------|------|

### 14.5 非保存対象

以下は相談・推薦ごとに変化するRuntime情報であり、
Shrine固定プロフィールへ保存しない。

- matched_need_tags
- consultation_axis_fit
- recommendation_reason
- action_suggestion
- reflection_question
- text_score
- score_element
- evidence
- visit_fit

必要な場合は、推薦生成時点のスナップショットとして
ConciergeThreadまたは推薦履歴側へ保存する。

## 15. Migration分割案

### 15.1 目的

DB変更を一度に投入せず、
後戻り可能な単位へ分割する。

スキーマ変更、既存データ補完、制約追加を分離し、
各段階でデータ状態を確認できる構成とする。

### 15.2 分割原則

- nullableなフィールド追加を先行する
- データ補完前に必須制約を付けない
- スキーマ変更とBackfillを同一Migrationへ含めない
- M2M・別モデル追加はShrine更新と分離する
- Index追加はデータ移行後に行う
- Rename・削除は互換期間を設ける

### 15.3 Migration候補

| Migration | 変更内容 | Data Migration | Rollback | 前提 |
|-----------|----------|----------------|----------|------|
| Migration 1 | nullable追加 | なし | ○ | 監査完了 |
| Migration 2 | Backfill | あり | △ | Migration1 |
| Migration 3 | Readiness再計算 | あり | △ | Backfill完了 |
| Migration 4 | Index・制約追加 | なし | ○ | データ確認 |
| Migration 5 | 旧構造整理 | 必要時 | △ | 互換期間終了 |

### 15.4 データ移行方針

- 推測でデータを補完しない
- 出典未確認は未確認として扱う
- Derived情報はStored情報からのみ生成する
- Backfill件数・失敗件数を記録する
- 再実行可能なMigrationまたはManagement Commandとする

## 16. Rollout / Rollback方針

### 16.1 目的

Knowledge BaseのDB適用を段階的に有効化し、
問題発生時に安全に戻せる状態を維持する。

### 16.2 Rollout方針

1. nullable構造のみ追加
2. 旧構造を正本として維持
3. Backfill実施
4. 新旧差分監査
5. 新構造へ読み取り切替
6. ReadinessをShadow判定
7. 問題なければ正本化
8. 互換期間終了後に旧構造を整理

### 16.3 Rollback方針

- 読み取り先のみ旧構造へ戻す
- ReadinessはFeature Flagで停止可能とする
- Backfill前データは変更しない
- 新旧Dual Write期間を設ける
- 破壊的変更は別リリースとする

### 16.4 監視項目

- Backfill成功率
- source未設定率
- verified_at未設定率
- Readiness分布
- reason_facts生成率
- fallback_rate
- recommendation生成エラー率
- detail_open_rate
- save_rate
- route_open_rate

### 16.5 中止条件

以下のいずれかが発生した場合は新構造を有効化しない。

- 推薦生成エラー率が増加
- reason_facts生成率が低下
- Readiness判定で推薦件数が大幅減少
- source・verified_at欠損が増加
- 新旧表示で情報差異が発生

## 17. 次PR候補

### 17.1 目的

本監査で抽出した課題を、
責務が重ならない単位でPRへ分割する。

本PRでは実装を行わず、
各PRの目的と完了条件のみ整理する。

### 17.2 PR候補一覧

| PR候補 | 目的 | 変更範囲 | 完了条件 | 優先度 |
|--------|------|----------|----------|--------|
| Knowledge Base用語統一 | Glossaryを正本へ統一 | docs/knowledge | 用語差分解消 | P0 |
| Recommendation Readiness統一 | 判定条件統一 | docs/knowledge | Readiness定義確定 | P0 |
| Shrine DB物理設計 | 概念項目とDB対応 | docs/knowledge・docs/architecture | DB設計確定 | P0 |
| Trust Layer最小実装 | source・verified_at追加 | backend | Migration・テスト完了 | P1 |
| Shrine Fact Backfill | Fact補完 | backend・scripts | Backfill完了 | P1 |
| Readiness Shadow監査 | Readiness分布確認 | backend・docs/audit | Shadow監査完了 | P1 |
| culture_translation設計 | Meaning Layer整理 | docs/knowledge | 設計確定 | P2 |
| Reflection Layer設計 | Reflection専用項目整理 | docs/knowledge | 設計確定 | P2 |

### 17.3 次PR選定ルール

- P0をDB実装より先に完了する
- Docs修正とDB実装を同一PRに含めない
- MigrationとBackfillを分離する
- Trust LayerとReflection Layerを同時実装しない
- 破壊的変更は最後に実施する
