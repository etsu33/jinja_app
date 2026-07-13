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
| Taxonomy | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | 🟦 | Status表記・重複管理を確認、Meaning⇔Consultation Taxonomyの重複1件は判断保留 |
| Visit / Reflection | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | 🟦 | Status表記付与・historyTheme命名揺れ（境界→縁）を修正 |
| Archive | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | 🟦 | Archive4件のStatus表記・置き換え先参照を確認 |

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

- `visit-style-taxonomy.md` 自体のTODO・PR候補除去状況の確認（`concierge-filter-area.md`側は`visit-style-taxonomy.md`への委譲構造に統一済み）

### ChatGPT判断

未着手

### 修正内容

【再監査結果（PASS / WARNING / FAIL）の反映】

- FAIL（`concierge-entry-final-wireframe.md`／`concierge-filter-area.md`／`need-mode-ui-flow.md`／`compat-mode-ui-flow.md`にTODO・次PR候補が残存し、台帳の「除外済み」記載と矛盾）: 解消。4ファイルとも`Status: Reference`バナーを保持し、TODO・次PR候補セクションは存在しないことをgrepで再確認済み。
- WARNING（`concierge-entry-final-wireframe.md`／`concierge-filter-area.md`の一部にMarkdownのコードブロックが閉じられておらず、見出し・箇条書き・表が未整形のまま残存）: `concierge-entry-final-wireframe.md`と`compat-mode-ui-flow.md`のコードブロック未クローズを修正し、`##`/`###`見出し・表・コードブロックを他ファイルと同じ規約へ復元。
- WARNING（相談テーマ8項目が`consultation-theme-taxonomy.md`と`concierge-entry-final-wireframe.md`／`need-mode-ui-flow.md`に重複掲載）: 解消。両Reference文書とも一覧を保持せず`consultation-theme-taxonomy.md`へ委譲する記述に統一済みであることを確認。
- WARNING（Archive化済み`concierge-first.md`への参照が`meaning-translation-mapping.md`／`concierge-modes.md`／`explore-integration-design.md`に残存）: 解消。3ファイルの関連ドキュメント・責務境界表の参照先を`concierge-first-final-spec.md`へ変更。
- WARNING（`action_suggestion_v4.md`の関連ドキュメントに自己参照）: 解消。自己参照行を削除。
- 参照切れ確認：`docs/product/`配下を`concierge-first.md`でgrepし、残存する言及はREADME.md・product-document-audit.mdのArchive分類表内の正当な記載のみであることを確認。

【未対応（今回のスコープ外）】

- `concierge-first.md`／`concierge-first-wireframe.md`のArchive文書内に残る「## 現行仕様」という見出し名の紛らわしさ
- `product-doc-consolidation.md`の「## 統合方針」見出しの重複
- `visit-style-taxonomy.md`本体のTODO・次PR候補除去状況（Taxonomyカテゴリで別途確認予定）

【追加対応（Product最終監査時）】

- `concierge-first-final-spec.md`と`concierge-modes.md`にStatus表記が欠落していた（正本8件中、Taxonomy側3件は既にStatus表記済みだったがConcierge側2件が未対応だった）ため、`Status: Active`バナーを追加。
- `explore-integration-design.md`（Referenceだが台帳のどのカテゴリ対象にも未登録）にもStatus表記が欠落していたため`Status: Reference`バナーを追加。台帳への対象追加は見送り、本注記でのみ記録する。

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

【PASS / WARNING / FAIL】

- `consultation-theme-taxonomy.md`: PASS（Status表記・正本責務・TODO/PR候補なし・重複管理なし・関連ドキュメント・更新ルールすべて確認済み）
- `history-theme-taxonomy.md`: PASS（同上）
- `visit-style-taxonomy.md`: PASS（Status: Reference、TODO/PR候補なし、参拝スタイル一覧の一次情報源として重複なし）
- `meaning-translation-mapping.md`: WARNING（下記「重複管理」参照）

【重複管理】

- `meaning-translation-mapping.md`の「相談テーマから推薦入力への接続」節の対応表（theme_key／consultation_axis候補／need_tags／history_theme候補）が、`consultation-theme-taxonomy.md`が正本と自認する3つの対応表（consultation_axis対応・need_tags対応・history_theme対応）と同一データを保持している。`meaning-translation-mapping.md`冒頭の委譲宣言は「表示文言・内部キー」のみを対象としており、この対応表自体の重複は解消されていない。正本をどちらにするかは判断保留。

### ChatGPT判断

未着手

### 修正内容

- 4ファイルとも`Status`バナー（Active/Reference）が付与済みであることを確認。
- `meaning-translation-mapping.md`の関連ドキュメントにあったArchive文書`concierge-first.md`への参照を`concierge-first-final-spec.md`へ変更済み（Concierge作業ログの参照整合対応と合わせて実施）。
- TODO・次PR候補の残存はgrepで確認し、4ファイルとも該当なし。

### PR

-

---

## Visit / Reflection

### 対象

- visit-reflection-flow.md
- reflection-funnel-dashboard.md

### 監査結果

【PASS / WARNING / FAIL】

- `visit-reflection-flow.md`: PASS（正本、TODO/PR候補なし、Event/Payload契約・保存責務が明確）。Status表記が欠落していたためFAIL相当だったが本対応で解消。
- `reflection-funnel-dashboard.md`: WARNING → 解消。以下の問題を修正。
  - Status表記が欠落していた（Reference文書として付与）
  - `## 更新ルール`節が存在しなかった（他文書と同じ規約で追加）
  - historyTheme別breakdownの例に、7カテゴリ（守り・静寂・再出発・復興・勝負・学び・縁）に存在しない「境界」という誤った名称が残存していた（「縁」へ修正）

### ChatGPT判断

未着手

### 修正内容

- `visit-reflection-flow.md`に`Status: Active`バナーを追加。
- `reflection-funnel-dashboard.md`に`Status: Reference`バナー、関連ドキュメント節、更新ルール節を追加し、historyTheme命名揺れ（境界→縁）を修正。
- TODO・次PR候補の残存はgrepで確認し、2ファイルとも該当なし。

### PR

-

---

## Archive

### 対象

- concierge-first.md
- concierge-first-wireframe.md
- action-suggestion-layer.md
- product-doc-consolidation.md

（旧版では`home-hero-final-wireframe.md`と「その他Archive候補」を対象に含めていたが、`home-hero-final-wireframe.md`は実際にはReference分類のため対象から除外し、README.md・product-document-audit.mdが確定しているArchive4件へ同期した）

### 監査結果

【PASS / WARNING / FAIL】

- `concierge-first.md`: PASS（`Status: Archive`明記、現行仕様への置き換え先明記）。WARNING：本文中の「## 現行仕様」という見出し名がArchive方針と紛らわしい（未修正、残課題として維持）。
- `concierge-first-wireframe.md`: PASS（同上の構造）。同様のWARNING（「## 現行仕様」見出し名）が残存。
- `action-suggestion-layer.md`: PASS（`Status: Archive`、Archive理由表、現行正本一覧が明確）。
- `product-doc-consolidation.md`: PASS（`Status: Archive`、置き換え先明記）。WARNING：「## 統合方針」という同名見出しが本文中に2箇所存在（未修正、残課題として維持）。

4ファイルとも、TODO・次PR候補の残存はgrepで確認し該当なし。現行仕様判断への使用を禁止する旨と置き換え先は、いずれも冒頭Statusブロックに明記済み。

### ChatGPT判断

未着手

### 修正内容

Archiveカテゴリ自体への追加修正は今回実施していない（既存のStatus表記・置き換え先明記は前回セッションで完了済みのため）。台帳の対象ファイル一覧を実態（README.md・product-document-audit.mdのArchive分類）へ同期した。

【未対応（残課題）】

- `concierge-first.md`／`concierge-first-wireframe.md`の「## 現行仕様」見出し名の紛らわしさ
- `product-doc-consolidation.md`の「## 統合方針」見出しの重複

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
