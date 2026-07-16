# Product Documents

## 目的

`docs/product`配下のプロダクト仕様書の入口。

プロダクトの体験設計、画面責務、分類体系、意味変換、参拝後体験およびPremium体験に関する正本を一覧化し、読む順番を定義する。

---

## 読む順番

### 1. 基本体験と推薦契約

```text
README.md
↓
kami-musubi-experience-design.md
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
recommendation-v4-interpreter-contract.md
↓
action_suggestion_v4.md
```

### 2. 神社詳細・参拝・記録

```text
shrine-detail-layer.md
↓
shrine-detail-v3-design.md
↓
shrine-submission-flow.md
↓
visit-reflection-flow.md
↓
reflection-timeline-design.md
```

### 3. Premium・課金

```text
pricing.md
↓
premium-experience.md
↓
billing-paywall.md
```

---

## 正本

### 全体体験

| ファイル | 役割 |
|---|---|
| `kami-musubi-experience-design.md` | 相談・推薦・参拝・振り返りを一本の体験として接続する最上位体験設計 |

### Concierge・Recommendation

| ファイル | 役割 |
|---|---|
| `concierge-first-final-spec.md` | Concierge First全体仕様 |
| `concierge-modes.md` | Need Mode / Compat Mode等のMode責務 |
| `consultation-theme-taxonomy.md` | 相談テーマの分類体系 |
| `history-theme-taxonomy.md` | `history_theme`の分類定義 |
| `meaning-translation-mapping.md` | 相談・ご利益・神社・行動を`history_theme`へ接続する変換仕様 |
| `recommendation-v4-interpreter-contract.md` | Consultation InterpreterのInput / Output契約 |
| `action_suggestion_v4.md` | Action Suggestion v4の契約・Schema |

### 神社詳細・参拝・記録

| ファイル | 役割 |
|---|---|
| `shrine-detail-layer.md` | Shrine DetailのPublic / Context / Personal Layer契約 |
| `shrine-detail-v3-design.md` | Shrine Detail v3のUX・Analytics・Premium接続設計 |
| `shrine-submission-flow.md` | 神社追加、重複候補および投稿後導線の現行仕様 |
| `visit-reflection-flow.md` | 参拝から振り返りまでの体験・保存・イベント契約 |
| `reflection-timeline-design.md` | 相談・参拝・Reflectionを時系列で接続する体験設計 |

### Premium・Billing

| ファイル | 役割 |
|---|---|
| `pricing.md` | Free / Premiumの提供価値境界と価格表現 |
| `premium-experience.md` | Free / Premiumの画面別体験差と保存・履歴・比較の原則 |
| `billing-paywall.md` | 課金状態、Free制限、利用可否およびPaywall判定の契約 |

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
| `card-visibility-renderer-split.md` | Card表示可否とRenderer責務の設計補足 |
| `concierge-card-architecture.md` | Concierge Card Treeと表示構造の設計補足 |
| `direction-ranking-design.md` | 方角を推薦補助軸として扱う設計補足 |
| `journey-timeline-design.md` | Journey Timelineの体験・情報設計 |
| `mobile-bottom-navigation.md` | Mobile下部ナビゲーションの設計補足 |
| `monetization-flow-design.md` | Premium提示、購入復帰および継続計測の設計 |
| `shrine-detail-meaning-layer.md` | Shrine DetailにおけるMeaning Layerの設計補足 |

---

## Archive

| ファイル | 役割 |
|---|---|
| `concierge-first.md` | Concierge First初期設計 |
| `concierge-first-wireframe.md` | 初期ワイヤーフレーム |

---

## 役割境界

- **README.md**は`docs/product`の入口として、読む順番と各文書の役割のみを管理する。
- **正本**は、現行の体験・機能・画面・契約に関する仕様判断の基準とする。
- **Reference**は、正本を補足するUI設計、分析設計または設計背景として扱う。
- **Archive**は履歴保存を目的とし、現行仕様判断には使用しない。
- システム構造、技術レイヤーおよび依存関係は`docs/core/`を参照する。
- 神社知識、用語、コピーおよび生成原則は`docs/knowledge/`を参照する。
- Analyticsのイベント、PayloadおよびKPI契約は`docs/analytics/`を参照する。
- 文書の分類・監査結果は`product-document-audit.md`を参照する。

---

## 更新ルール

- 正本を追加・削除した場合は、本書の「読む順番」と「正本」を同じPRで更新する。
- 文書の分類が変更された場合は、`product-document-audit.md`と内容を一致させる。
- 詳細仕様、TODO、実装履歴、監査結果およびPR情報は本書へ記載しない。
- 同一文書を複数カテゴリへ重複掲載しない。
- 本書はProduct文書の入口としての役割のみを維持する。
