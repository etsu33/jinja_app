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

【状態】README.md=判断保留 / product-document-audit.md=Active / product-doc-consolidation.md=Archive候補

【事実】
- README.mdの「読む順番」節は`1. 2. 3.`のまま空欄。
- product-document-audit.mdは21ファイルを4分類し、本カテゴリ3ファイルをREADME.md=正本、product-document-audit.md=Reference（自己分類）、product-doc-consolidation.md=Archive（置き換え先README.md）としている。
- README.mdとproduct-document-audit.mdのファイル分類が`concierge-first.md`・`explore-integration-design.md`・`concierge-first-final-spec.md`・`consultation-theme-taxonomy.md`について不一致。
- product-doc-consolidation.mdは自らを「Git上で統合方針を固定するための方針書」と説明（恒久文書ではなく一時方針書の性格）。
- product-document-audit.mdはproduct-doc-consolidation.mdの依存ファイルに「README.md」を挙げるが、product-doc-consolidation.md本文にREADME.mdへの言及は確認できず。

【重複】README.md ⇔ product-document-audit.md：「入口・分類・読む順番」の責務重複。正本判断は対象ファイル内情報のみでは不可。

【判断保留】
- README.mdが現在も正確な入口として機能しているか、更新滞留状態かは本カテゴリ内情報だけでは不明。
- product-doc-consolidation.mdが記すGoogle Docs側統合作業の完了有無はリポジトリ外状態に依存し確認不能。
- README.mdとproduct-document-audit.mdのどちらを「入口・分類の正本」とするかは確定不可。

詳細は当該監査セッションの出力を参照。

### ChatGPT判断

未着手

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

【状態】concierge-first-wireframe.md=判断保留 / 他7ファイル=Active

【事実】
- concierge-first-final-spec.mdは自らを「実装前仕様として束ねる正本」と明記し、need-mode-ui-flow.md・compat-mode-ui-flow.md・concierge-entry-final-wireframe.mdを参照ドキュメントとして明示。
- concierge-first.mdとconcierge-modes.mdは責務境界表で相互参照し一貫性あり。
- 相談テーマチップ8項目（concierge-entry-final-wireframe.md／need-mode-ui-flow.md）と参拝スタイル6項目（concierge-first-wireframe.md／concierge-filter-area.md）がそれぞれ完全一致で重複掲載。
- concierge-first-wireframe.mdはTODO全完了だが「実装前に母艦判断へ差し戻す」という判断保留事項を自己申告、Archiveマーカーなし。
- concierge-modes.mdが定義するRoute/Theme/ShrineSearch Modeは他7ファイルに未登場。
- Home/Top主CTA文言が「この相談ではじめる」（concierge-first-final-spec.md）と「言葉を整える」（concierge-first-wireframe.md）で不一致。
- Compat Modeの配置場所呼称が「Filter」「補助条件Accordion」「ConciergeFilterPanel」で揺れ。

【重複】4件：①Need/Compat Mode境界ルール（4ファイル）②相談テーマチップ8項目 ③参拝スタイル6項目 ④ConciergeEntry責務定義。いずれも正本判断は対象ファイル内情報のみでは不可。

【判断保留】
- concierge-first-wireframe.mdの現在位置づけ（現行仕様か検討記録か）。
- concierge-first.mdとconcierge-first-final-spec.mdのどちらが「Concierge First」定義の一次情報か。
- 相談テーマチップ8項目・参拝スタイル6項目の一次情報源。

詳細は当該監査セッションの出力を参照。

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
