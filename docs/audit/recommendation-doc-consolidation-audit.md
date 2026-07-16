# Recommendation Document Consolidation Audit

## 目的

Recommendation、Meaning Layer、history_theme、Action、Reflection関連文書について、
正本・Reference・統合・Archiveを整理する。

## 結論

Recommendation Reason専用正本が存在しないため、`docs/core/recommendation-reason-contract.md`を新規作成する。

history_themeについては新規正本を増やさず、以下の既存2正本を維持する。

- カテゴリ定義: `docs/product/history-theme-taxonomy.md`
- 変換・接続: `docs/product/meaning-translation-mapping.md`

## 現行正本

| 領域                     | 正本                                          |
| ------------------------ | --------------------------------------------- |
| Meaning Layer思想        | `docs/core/meaning-layer.md`                  |
| Recommendation Readiness | `docs/core/recommendation-readiness.md`       |
| history_themeカテゴリ    | `docs/product/history-theme-taxonomy.md`      |
| Meaning Translation      | `docs/product/meaning-translation-mapping.md` |
| Action Suggestion        | `docs/product/action_suggestion_v4.md`        |
| Visit / Reflection       | `docs/product/visit-reflection-flow.md`       |

## 正本欠落

Recommendation Reasonには、生成・保存・表示・互換境界を一つに固定する正本が存在しない。

監査結果は`docs/audit/recommendation-reason-responsibility-audit.md`に存在するが、Auditは正式仕様の正本にはしない。

## 新規正本

`docs/core/recommendation-reason-contract.md`を新規作成する。

## 文書比較

### `docs/core/meaning-layer.md`

独自情報:

- Meaning Layerの思想
- 神社を意味ある現実空間として扱う考え方
- 非断定方針
- 意味ある移動体験
- AIが解釈する対象

判定: Active正本として維持。

### `docs/core/meaning-layer-connection.md`

独自情報:

- interpretation_profileからComposerまでの接続
- translation_result
- Composerとの境界
- Recommendationとの境界
- fallback
- Runtime Snapshot保存責務

判定（E3で本文確認済み・確定）:

`meaning-layer.md`（思想）とは抽象度が異なり、`meaning-translation-mapping.md`（変換規則）や`recommendation-reason-contract.md`（Recommendation Reason契約）とも扱う範囲が重複しない。

Composerへのフィールドマッピング（`translation_result.history_theme → generated.historyContext`等）とFallback経路は本書にしか存在しない独自の技術仕様であり、分割統合はしない。

**Active正本として維持する**（E1時点の暫定Reference分類を修正）。

### `docs/knowledge/meaning-layer-spec.md`

独自情報:

- 現時点では見出し・論点一覧のみ
- 詳細な仕様本文は存在しない

判定（E3で本文確認済み・確定）: 全節が見出しと箇条書きの論点一覧のみで、本文（プローズ）が一切存在しない。「Stored/Derived/Runtime」は`meaning-translation-mapping.md`「history_themeの生成源」節へ、「Fact/Meaning」の区分は`recommendation-reason-contract.md`・`docs/audit/recommendation-terminology-contract.md`へ、「consultation_axis/need_tag/matched_need_tags」は`meaning-translation-mapping.md`・`recommendation-terminology-contract.md`へ、それぞれ独自情報を失うことなく吸収済み。**参照元3件（`docs/knowledge/README.md`、`docs/knowledge/shrine-data-guide.md`、`docs/knowledge/shrine-profile-spec.md`）の参照を除去した上で、Fフェーズで削除する**。

### `docs/knowledge/recommendation-copy-guide.md`

独自情報:

- Fact → Meaning → User Connection → Recommendation
- 推薦文で利用できる情報
- 禁止表現
- コピー品質基準

判定: コピー運用ガイドとして一部独自性がある。以下のように分離してReference維持する。Contract作成後も直ちに削除しない。

- Contract・責務: `recommendation-reason-contract.md`
- 文言・禁止例: `recommendation-copy-guide.md`

## history_theme統合

Stored / Translated / Snapshotの概念区分は、`docs/product/meaning-translation-mapping.md`へ統合する。

`history-theme-contract-audit.md`は、統合判断の根拠としてReference維持する。

## 分類案

### Active正本

- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

### Reference

- `docs/knowledge/recommendation-copy-guide.md`
- `docs/product/reflection-funnel-dashboard.md`
- `docs/audit/recommendation-terminology-contract.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/history-theme-contract-audit.md`（E2でStatus: Referenceへ変更済み）

Referenceに分類した文書は、現時点で独自情報を持つため維持する。`docs/core/meaning-layer-connection.md`はE3での本文確認によりActive正本へ確定したため、この一覧からは除外した。

### 削除確定

- `docs/knowledge/meaning-layer-spec.md`（Fフェーズで削除）

## PR分割

### E1（完了）

#### 完了条件

- `docs/core/recommendation-reason-contract.md`が作成されている
- Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務が定義されている
- `docs/audit/recommendation-doc-consolidation-audit.md`に文書分類と後続PRが記録されている
- READMEまたは該当する入口文書から新しい正本へ参照できる
- 既存文書の移動・Archive・削除は行わない

### E2（完了）

Stored / Translated / Snapshot定義をMeaning Translation正本へ統合。

`docs/product/meaning-translation-mapping.md`の「history_themeの生成源」節へ吸収し、`docs/audit/history-theme-contract-audit.md`をStatus: Referenceへ変更した。

### E3（完了）

Meaning Layer関連文書を整理した。

本文確認の結果、`meaning-layer.md`と`meaning-layer-connection.md`は責務が分離されており、統合不要と判定したため、Active正本として両方維持する。

`meaning-layer-spec.md`は独自本文が存在しないため削除した。

### E4

README・分類表・参照先を更新。

### F

独自情報がなくなった文書をArchiveまたは削除。
