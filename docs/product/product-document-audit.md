# Product Document Audit

## 目的

`docs/product` 配下のプロダクト文書を監査し、今後「正本だけが明確に分かる構成」へ整理するための分類を固定する。

本監査では、現時点で存在するファイルを以下の4分類で整理する。

- **正本**: 実装判断・仕様判断の基準として使用する文書
- **Reference**: 正本を補足する参照文書
- **Archive**: 過去の検討・移行・統合作業を記録した文書
- **Delete**: 内容が他文書へ吸収済みで、削除対象となる文書

削除済みの文書は本表へ残さず、変更履歴はGitおよびPRで追跡する。

---

## 監査サマリー

| 分類 | ファイル数 | 方針 |
|---|---:|---|
| 正本 | 8 | READMEを入口に、体験、モード、分類体系、意味変換、参拝後導線、Action契約を維持する |
| Reference | 9 | UI詳細、補助条件、分析、Explore設計、本監査表として正本を補足する |
| Archive | 4 | 過去の設計過程や統合作業メモとして保持し、現行判断には使わない |
| Delete | 0 | 現時点で追加の削除対象は未確定 |

---

## 推奨する正本構成

今後の `docs/product` は、以下の順番を中心に読む。

```text
README.md
↓
concierge-first-final-spec.md
↓
concierge-modes.md
↓
consultation-theme-taxonomy.md
↓
history-theme-taxonomy.md
↓
meaning-translation-mapping.md
↓
visit-reflection-flow.md
↓
action_suggestion_v4.md
```

各正本の責務は以下とする。

| 正本 | 責務 |
|---|---|
| `README.md` | `docs/product` の入口と読む順番 |
| `concierge-first-final-spec.md` | Concierge Firstの統合仕様 |
| `concierge-modes.md` | Need Mode / Compat Modeの責務 |
| `consultation-theme-taxonomy.md` | 相談テーマUIの分類 |
| `history-theme-taxonomy.md` | `history_theme` のカテゴリ定義 |
| `meaning-translation-mapping.md` | 相談・ご利益・神社・行動を `history_theme` へ接続する変換正本 |
| `visit-reflection-flow.md` | 参拝から振り返りまでの導線 |
| `action_suggestion_v4.md` | Action Suggestion v4の契約 |

UIワイヤー、補助条件、分析、Explore設計は、正本を補足するReferenceとして扱う。

---

## ファイル別分類

| ファイル | 分類 | 理由 | 依存ファイル | 置き換え先 |
|---|---|---|---|---|
| `README.md` | 正本 | `docs/product` の入口、読む順番、責務、実装判断の優先順位を定義するため。 | `concierge-first-final-spec.md`, `concierge-modes.md`, `history-theme-taxonomy.md`, `meaning-translation-mapping.md`, `visit-reflection-flow.md`, `action_suggestion_v4.md` | なし |
| `concierge-first-final-spec.md` | 正本 | Concierge First MVPの統合仕様として、Home、Concierge、Filter、Need Mode、Compat Modeの責務を横断的に定義するため。 | `concierge-modes.md`, `consultation-theme-taxonomy.md`, `meaning-translation-mapping.md` | なし |
| `concierge-modes.md` | 正本 | Need Mode / Compat Modeの入力責務と、推薦・意味変換への接続点を定義するため。 | `consultation-theme-taxonomy.md`, `history-theme-taxonomy.md`, `meaning-translation-mapping.md` | なし |
| `consultation-theme-taxonomy.md` | 正本 | 相談テーマチップ、表示文言、内部キー、`consultation_axis`、`need_tags`との関係を定義するUI入口の分類正本であるため。 | `meaning-translation-mapping.md` | なし |
| `history-theme-taxonomy.md` | 正本 | `history_theme` のカテゴリ定義を担い、推薦理由、履歴保存、分析、行動設計の基盤となるため。 | `meaning-translation-mapping.md` | なし |
| `meaning-translation-mapping.md` | 正本 | 相談テーマ、相談状態、ご利益、神社情報を `history_theme` へ接続し、Action・Reflectionまでの変換方針を統合して定義するため。 | `consultation-theme-taxonomy.md`, `history-theme-taxonomy.md`, `concierge-modes.md`, `visit-reflection-flow.md`, `action_suggestion_v4.md` | なし |
| `visit-reflection-flow.md` | 正本 | 参拝完了から振り返り保存、状態記録、次回相談への接続を定義するため。 | `history-theme-taxonomy.md`, `meaning-translation-mapping.md`, `reflection-funnel-dashboard.md` | なし |
| `action_suggestion_v4.md` | 正本 | Recommendation v4から受け取るAction SuggestionのInput / Output schema、責務分離、生成ルールを固定するため。 | `meaning-translation-mapping.md`, `visit-reflection-flow.md`, `concierge-modes.md` | なし |
| `home-hero-final-wireframe.md` | Reference | Home Heroの画面構成を確認する資料として有用だが、体験全体の判断は `concierge-first-final-spec.md` が担うため。 | `concierge-first-final-spec.md`, `consultation-theme-taxonomy.md` | `concierge-first-final-spec.md` |
| `concierge-entry-final-wireframe.md` | Reference | Concierge EntryのUI詳細として有用だが、入力責務とMVP方針は正本へ従属するため。 | `concierge-first-final-spec.md`, `concierge-filter-area.md` | `concierge-first-final-spec.md` |
| `concierge-filter-area.md` | Reference | 補助条件エリアのUI詳細として参照価値があるが、Filterの責務は統合仕様に従属するため。 | `concierge-first-final-spec.md`, `compat-mode-ui-flow.md`, `visit-style-taxonomy.md` | `concierge-first-final-spec.md` |
| `need-mode-ui-flow.md` | Reference | Need Modeの画面導線を補足する資料であり、Mode責務は `concierge-modes.md` が正本であるため。 | `concierge-modes.md`, `consultation-theme-taxonomy.md`, `meaning-translation-mapping.md` | `concierge-modes.md` |
| `compat-mode-ui-flow.md` | Reference | Compat Modeの画面導線を補足する資料であり、Mode責務は `concierge-modes.md` が正本であるため。 | `concierge-modes.md`, `concierge-filter-area.md`, `concierge-first-final-spec.md` | `concierge-modes.md` |
| `visit-style-taxonomy.md` | Reference | 参拝スタイル補助条件の分類として有用だが、相談解釈や推薦入力の主軸ではないため。 | `concierge-filter-area.md`, `meaning-translation-mapping.md`, `concierge-first-final-spec.md` | `concierge-filter-area.md` |
| `reflection-funnel-dashboard.md` | Reference | 振り返り導線のKPIとダッシュボード設計を扱う分析資料であり、イベント・保存導線は `visit-reflection-flow.md` が正本であるため。 | `visit-reflection-flow.md`, `history-theme-taxonomy.md` | `visit-reflection-flow.md` |
| `explore-integration-design.md` | Reference | `/shrines` と `/map` のExplore統合設計を扱う。候補探索の詳細資料として残すが、Concierge First全体の正本ではないため。 | `concierge-first-final-spec.md` | `concierge-first-final-spec.md` |
| `product-document-audit.md` | Reference | `docs/product` の分類と整理判断を記録する管理資料であり、プロダクト仕様そのものではないため。 | `README.md`, `concierge-first-final-spec.md`, `meaning-translation-mapping.md` | なし |
| `concierge-first.md` | Archive | Concierge First方針の初期設計として履歴価値はあるが、現行内容は `concierge-first-final-spec.md` へ統合されているため。 | `concierge-first-final-spec.md`, `concierge-modes.md` | `concierge-first-final-spec.md` |
| `concierge-first-wireframe.md` | Archive | Top / Concierge統合前後の検討過程として価値はあるが、現行UI判断には使用しないため。 | `home-hero-final-wireframe.md`, `concierge-entry-final-wireframe.md`, `concierge-first-final-spec.md` | `concierge-first-final-spec.md` |
| `product-doc-consolidation.md` | Archive | Google Docsおよびリポジトリ文書の統合作業メモであり、現行仕様判断には使用しないため。 | `README.md`, `concierge-first-final-spec.md` | `README.md` |
| `action-suggestion-layer.md` | Archive | 過去のAction Suggestion設計として履歴価値はあるが、現行契約は `action_suggestion_v4.md` が担うため。 | `meaning-translation-mapping.md`, `visit-reflection-flow.md`, `action_suggestion_v4.md` | `action_suggestion_v4.md` |

---

## 統合済み文書

以下の5文書は、`meaning-translation-mapping.md` へ内容を統合し、削除した。

```text
theme-to-recommendation-input-mapping.md
state-history-theme-mapping.md
goriyaku-history-theme-mapping.md
shrine-history-theme-mapping.md
history-theme-action-mapping.md
```

各文書が担っていた責務は、現在以下へ統合されている。

| 旧文書の責務 | 現在の正本 |
|---|---|
| 相談テーマから推薦入力への変換 | `meaning-translation-mapping.md` |
| 相談状態から `history_theme` への変換 | `meaning-translation-mapping.md` |
| ご利益から `history_theme` への補助変換 | `meaning-translation-mapping.md` |
| 神社ごとの `history_theme` 分類 | `meaning-translation-mapping.md` |
| `history_theme` からAction・Reflectionへの接続 | `meaning-translation-mapping.md` |

`shrine-classification-policy.md` も神社分類方針へ吸収済みのため削除した。

削除済み文書の変更経緯はGit履歴およびPRで追跡する。

---

## 整理時の注意

- `Archive` は現行仕様判断に使用しない。
- Archive文書を残す場合は、冒頭に現行の置き換え先を明記する。
- 削除対象を決める場合は、先に全文検索で参照元を確認する。
- 削除済み文書は本表のファイル別分類へ残さない。
- 正本を追加・削除する場合は、最初に `README.md` の読む順番を更新する。
- Referenceから正本へ仕様を逆流させない。
- UI詳細、API schema、Migration、テストケース、実装履歴を正本へ過剰に再掲しない。

---

## 更新ルール

本監査文書は、以下の場合に更新する。

- 正本を追加・削除したとき
- 正本とReferenceの責務が変わったとき
- ArchiveまたはDeleteの整理を実施したとき
- 複数文書を統合したとき
- `docs/product` の読む順番を変更したとき

細かな実装変更や完了チェックリストの更新だけでは、本監査文書を更新しない。

---

## ドキュメント監査

`docs/product` 配下の入口は以下とする。

```text
docs/product/README.md
```

プロダクト全体の構造・責務境界は以下を参照する。

```text
docs/core/architecture.md
```

Meaning Layer全体の概念定義は以下を参照する。

```text
docs/core/meaning-layer.md
```

Knowledge Baseおよび実装整合性の監査は以下を参照する。

```text
docs/audit/
```
