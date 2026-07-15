# Recommendation Document Consolidation Audit

## 目的

Recommendation、Meaning Layer、history_theme、
Action、Reflection関連文書について、
正本・Reference・統合・Archive候補を整理する。

## 結論

Recommendation Reason専用正本が存在しないため、`docs/core/recommendation-reason-contract.md`を新規作成する。

history_themeについては新規正本を増やさず、以下の既存2正本を維持する。

- カテゴリ定義: `docs/product/history-theme-taxonomy.md`
- 変換・接続: `docs/product/meaning-translation-mapping.md`

## 現行正本

| 領域 | 正本 |
|---|---|
| Meaning Layer思想 | `docs/core/meaning-layer.md` |
| Recommendation Readiness | `docs/core/recommendation-readiness.md` |
| history_themeカテゴリ | `docs/product/history-theme-taxonomy.md` |
| Meaning Translation | `docs/product/meaning-translation-mapping.md` |
| Action Suggestion | `docs/product/action_suggestion_v4.md` |
| Visit / Reflection | `docs/product/visit-reflection-flow.md` |

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

判定: 内容は有用だが、`meaning-layer.md`、`meaning-translation-mapping.md`、`recommendation-reason-contract.md`へ分割統合できる可能性が高い。現時点ではReference維持。統合完了後にArchive候補とする。

### `docs/knowledge/meaning-layer-spec.md`

独自情報:

- 現時点では見出し・論点一覧のみ
- 詳細な仕様本文は存在しない

判定: 独自の確定仕様がほぼなく、他の正本に責務が存在する。Archiveまたは削除候補。

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
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

### Reference

- `docs/core/meaning-layer-connection.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/product/reflection-funnel-dashboard.md`
- `docs/audit/recommendation-terminology-contract.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/history-theme-contract-audit.md`

### Archive候補

- `docs/knowledge/meaning-layer-spec.md`

### 保留

- `docs/core/meaning-layer-connection.md`
- `docs/knowledge/recommendation-copy-guide.md`

統合後に独自情報が残っているか再確認する。

## PR分割

### E1

Recommendation Reason正本作成。

### E2

Stored / Translated / Snapshot定義をMeaning Translation正本へ統合。

### E3

Meaning Layer関連文書を統合。

### E4

README・分類表・参照先を更新。

### F

独自情報がなくなった文書をArchiveまたは削除。
