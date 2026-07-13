# Product Documents

## 目的

`docs/product` 配下のプロダクト仕様書の入口。

プロダクトの体験設計・責務・分類体系・意味変換・参拝後体験に関する正本を一覧化し、読む順番を定義する。

---

## 読む順番

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

---

## 正本

| ファイル | 役割 |
|---|---|
| `concierge-first-final-spec.md` | Concierge First 全体仕様 |
| `concierge-modes.md` | Need Mode / Compat Mode の責務 |
| `consultation-theme-taxonomy.md` | 相談テーマの分類体系 |
| `history-theme-taxonomy.md` | `history_theme` の分類定義 |
| `meaning-translation-mapping.md` | 相談・ご利益・神社・行動を `history_theme` へ接続する変換仕様 |
| `visit-reflection-flow.md` | 参拝から振り返りまでの体験設計 |
| `action_suggestion_v4.md` | Action Suggestion v4 の契約・Schema |

---

## Reference

| ファイル | 役割 |
|---|---|
| `home-hero-final-wireframe.md` | Home Hero UI設計 |
| `concierge-entry-final-wireframe.md` | Concierge Entry UI設計 |
| `concierge-filter-area.md` | Filter UI設計 |
| `need-mode-ui-flow.md` | Need Mode UI導線 |
| `compat-mode-ui-flow.md` | Compat Mode UI導線 |
| `visit-style-taxonomy.md` | 参拝スタイル分類 |
| `reflection-funnel-dashboard.md` | Reflection KPI・分析設計 |
| `explore-integration-design.md` | Explore体験設計 |
| `product-document-audit.md` | Product文書の監査・分類管理 |

---

## Archive

| ファイル | 役割 |
|---|---|
| `concierge-first.md` | Concierge First 初期設計 |
| `concierge-first-wireframe.md` | 初期ワイヤーフレーム |
| `action-suggestion-layer.md` | Action Suggestion 初期設計 |
| `product-doc-consolidation.md` | Google Docs統合作業履歴 |

---

## 役割境界

- **README.md** は `docs/product` の入口として、読む順番と各文書の役割のみを管理する。
- **正本** は実装・仕様判断の基準とする。
- **Reference** は正本を補足する資料として扱う。
- **Archive** は履歴保存を目的とし、現行仕様判断には使用しない。
- 文書の分類・監査結果は `product-document-audit.md` を参照する。

---

## 更新ルール

- 正本を追加・削除した場合は、本書を最初に更新する。
- 文書の分類が変更された場合は、`product-document-audit.md` と内容を一致させる。
- 詳細仕様・TODO・実装履歴・PR情報は本書へ記載しない。
- 本書は入口としての役割のみを維持する。
