# Knowledge Base Refactoring

## 目的

Knowledge Base 全体の責務を整理し、重複・矛盾・旧仕様を解消する。

本ドキュメントは **監査 → 設計判断 → 修正 → PR → マージ** の進捗管理を行うための作業台帳とする。

---

## 運用ルール

### Claude

担当範囲

- ディレクトリ監査
- 重複抽出
- 矛盾抽出
- Legacy / Archive / Delete候補抽出
- 依存関係整理

Claudeが更新してよい項目

- 監査

Claudeは禁止

- 修正
- リライト
- 要約
- ファイル移動
- ファイル削除
- PR作成

---

### ChatGPT

担当範囲

- 設計判断
- Archive可否判断
- 正本判断
- ドキュメント修正
- Git運用
- PR作成
- Merge

---

## ステータス

| 状態 | 意味 |
|------|------|
| ⬜ | 未着手 |
| 🟨 | 作業中 |
| 🟦 | レビュー待ち |
| 🟩 | 完了 |

---

# Progress

| カテゴリ | 監査 | ChatGPTレビュー | 修正 | PR | Merge | 状態 | 備考 |
|----------|:---:|:--------------:|:---:|:--:|:----:|:----:|------|
| README / 管理文書 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ | 🟦 | README・監査文書の分類と役割境界を同期済み |
| Concierge | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ | 🟦 | 現行正本・Reference・Archiveの責務整理済み |
| Taxonomy | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Theme・Visit Style・Meaning |
| Visit / Reflection | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Visit・Reflection・Analytics |
| Archive | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Legacy・Archive整理 |

---

# 作業ログ

## README / 管理文書

### 対象

- README.md
- product-document-audit.md
- product-doc-consolidation.md

### 監査結果

【状態】

- `docs/product/README.md`: Active
- `docs/product/product-document-audit.md`: Active
- `docs/product/product-doc-consolidation.md`: Archive

【確定事項】

- `README.md` は `docs/product` の入口として、読む順番・分類・役割境界のみを管理する。
- `product-document-audit.md` は文書分類・監査根拠・統合履歴を管理する。
- `product-doc-consolidation.md` は統合作業履歴を保持するArchive文書として扱う。
- READMEと監査表の分類は、正本8件・Reference9件・Archive4件で一致している。
- Archive文書には `Status: Archive` と現在の正本への参照を明記した。
- READMEには詳細仕様、TODO、PR候補、実装履歴を記載しない。

【解消した問題】

- READMEの読む順番が未完成だった問題
- READMEと監査表の分類不一致
- READMEと監査文書の役割重複
- `product-doc-consolidation.md` が現行仕様に見える問題
- 正本・Reference・Archiveの入口上の不明確さ

【残課題】

- 正本・Reference・Archiveの変更時にREADMEと監査表を同時更新する運用を維持する。

### ChatGPT判断

README / 管理文書カテゴリの責務分離は完了した。

文書管理の判断順序は以下とする。

```text
README.md
↓
各正本ドキュメント
↓
Reference文書
```

文書の分類根拠や変更履歴を確認する場合は、`product-document-audit.md` を参照する。

`product-doc-consolidation.md` はArchiveとして保持し、現行仕様判断には使用しない。

### 修正内容

未着手

### PR

-

---

## Concierge

### 対象

- concierge-first-final-spec.md
- concierge-first.md
- concierge-first-wireframe.md
- concierge-entry-final-wireframe.md
- concierge-filter-area.md
- concierge-modes.md
- need-mode-ui-flow.md
- compat-mode-ui-flow.md

### 監査結果

【状態】

- 正本:
  - `concierge-first-final-spec.md`
  - `concierge-modes.md`
  - `consultation-theme-taxonomy.md`
- Reference:
  - `concierge-entry-final-wireframe.md`
  - `concierge-filter-area.md`
  - `need-mode-ui-flow.md`
  - `compat-mode-ui-flow.md`
- Archive:
  - `concierge-first.md`
  - `concierge-first-wireframe.md`

【確定事項】

- Concierge First全体仕様は `concierge-first-final-spec.md` を正本とする。
- 推薦Modeの責務は `concierge-modes.md` を正本とする。
- 相談テーマの表示文言・内部キー・対応関係は `consultation-theme-taxonomy.md` を正本とする。
- UI詳細文書は正本を補足するReferenceとして扱う。
- `concierge-first.md` と `concierge-first-wireframe.md` はArchiveとして扱い、現行仕様判断には使用しない。
- Archive文書には `Status: Archive` と現在の正本への参照を明記した。
- Home Heroの相談テーマ文言は `consultation-theme-taxonomy.md` を参照する構造へ統一した。
- TODO、PR候補、実装フェーズ、判断保留などの作業管理情報は正本・Referenceから除外した。

【解消した問題】

- Concierge Firstの一次情報源の曖昧さ
- Archive文書の現行仕様との誤認
- 相談テーマ表示文言の重複管理
- Home / Concierge責務の重複
- 作業履歴と現行仕様の混在

【残課題】

- `concierge-filter-area.md` と `visit-style-taxonomy.md` の表示文言統一
- Need Mode / Compat Mode詳細UI文書の重複範囲確認

### ChatGPT判断

未着手

### 修正内容

未着手

### PR

-

---

## Taxonomy

### 対象

- consultation-theme-taxonomy.md
- history-theme-taxonomy.md
- meaning-translation-mapping.md
- visit-style-taxonomy.md

### 監査結果

未着手

### ChatGPT判断

未着手

### 修正内容

未着手

### PR

-

---

## Visit / Reflection

### 対象

- visit-reflection-flow.md
- reflection-funnel-dashboard.md

### 監査結果

未着手

### ChatGPT判断

未着手

### 修正内容

未着手

### PR

-

---

## Archive

### 対象

- action-suggestion-layer.md
- home-hero-final-wireframe.md
- その他 Archive候補

### 監査結果

未着手

### ChatGPT判断

未着手

### 修正内容

未着手

### PR

-

---

# 完了条件

以下を満たした時点で本リファクタリングは完了とする。

- README が正しい入口になっている
- 正本・Reference・Archive が明確になっている
- Archive文書に Status が付与されている
- 重複が解消されている
- 命名揺れが解消されている
- Knowledge Base 全体で責務が明確になっている
- すべて develop にマージ済み
