# Recommendation Terminology Contract Audit

## 目的

Recommendation関連用語について、概念名・物理フィールド名・表示名・責務境界を整理し、
Backend・Frontend・Knowledge・Analyticsで共通利用できる正式契約を定義する。

本書は**名称変更を目的としない**。

目的は、

- 概念の統一
- 用語の責務固定
- 将来のリファクタリング指針
- Codex実装時の判断基準

を明文化することである。

---

# 基本原則

- 概念名（Concept）と物理フィールド名（Physical Name）を分離する
- 既存Payload・Snapshot・Analyticsとの互換性を維持する
- snake_case / camelCase はレイヤー差として扱う
- UI表示名と内部名を混同しない
- User Input と User × Shrine Match を分離する
- Recommendation と Recommendation Reason を混同しない
- Recommendation Readiness は品質概念であり推薦ロジックではない

---

# レイヤー定義

| Layer | 内容 |
|------|------|
| Concept | ビジネス上の正式概念 |
| Backend | Python・DB・API契約 |
| Frontend | ViewModel・UI |
| Knowledge | ドキュメント・Meaning Layer |
| Analytics | 行動分析・イベント |

---

# 用語監査表

| 用語 | レイヤー | 正式な意味 | 正本 | 互換性 | 判定 |
|------|----------|------------|------|---------|------|
| need_tags | Backend | ユーザー相談から抽出したNeed候補一覧 | Backend | 維持 | Active |
| matched_need_tags | Backend | 神社とのマッチ判定に使用したNeed一覧 | Backend | 維持 | Active |
| primary_need_tag | Backend | Need候補の代表値 | Backend | 維持 | Active |
| consultation_axis | Backend / Knowledge | 相談カテゴリの代表軸 | Meaning Translation | 維持 | Active |
| history_theme | Meaning Layer | 神社文脈と相談文脈を接続する意味タグ | Meaning Translation | 維持 | Active |
| Recommendation | Product | 推薦候補・順位付け全体 | Product | 維持 | Active |
| Recommendation Reason | Product | 推薦理由全体 | Recommendation Reason | 維持 | Active |
| Recommendation Readiness | Knowledge | 推薦利用可能性を示す品質概念 | Knowledge | 維持 | Active |
| Fact | Recommendation Reason | 神社固有事実 | Recommendation Reason | 維持 | Active |
| Meaning | Knowledge | history_themeを中心とした意味付け | Meaning Translation | 維持 | Active |
| Interpretation | Recommendation Reason | Meaning＋相談解釈 | Recommendation Reason | 維持 | Active |
| User Connection | Knowledge | ユーザー状態との接続概念 | Knowledge | 維持 | Active |
| Action | Recommendation Reason | 次の小さな行動提案 | Action Suggestion | 維持 | Active |

---

# Recommendation Reason 構造

Recommendation Reason は以下3層で構成される。

```text
Recommendation Reason

├── Fact
│
├── Interpretation
│
└── Action
```

Interpretation は内部的に

```text
Meaning
+
User Connection
```

を統合して生成する。

したがって

```text
Meaning
```

と

```text
Interpretation
```

は同義ではない。

---

# 概念名と物理名の対応表

| 正式概念 | Backend | Frontend | 備考 |
|-----------|----------|-----------|------|
| Need Tags | need_tags | needTags | User Need候補 |
| Matched Need Tags | matched_need_tags | matchedNeedTags | Shrine Match |
| Primary Need | primary_need_tag | primaryNeedTag | 代表Need |
| Consultation Axis | consultation_axis | consultationAxis | User分類 |
| History Theme | history_theme | historyTheme | Meaning Layer |
| Recommendation | recommendations | recommendations | 推薦候補 |
| Recommendation Reason | reason_text | recommendationReason | 推薦理由 |
| Fact | fact | fact | 神社固有情報 |
| Interpretation | interpretation | interpretation | Meaning＋User Connection |
| Action | action | action | 行動提案 |

---

# Knowledge と実装の対応

Knowledgeでは以下の概念を利用する。

```text
Fact

↓

Meaning

↓

User Connection

↓

Recommendation
```

実装では以下へ統合される。

```text
Fact

↓

Interpretation

↓

Action
```

対応関係は次の通り。

| Knowledge | Backend |
|------------|----------|
| Fact | fact |
| Meaning | interpretationの一部 |
| User Connection | interpretationの一部 |
| Recommendation | reason_text |
| Action | action |

---

# Recommendation と Recommendation Reason の責務

Recommendation は

```text
どの神社を推薦するか
```

を決定する。

Recommendation Reason は

```text
なぜその神社なのか
```

を説明する。

Recommendation Readiness は

```text
推薦に利用可能な品質を満たしているか
```

を判断する。

三者は責務が異なるため混同しない。

---

# history_theme の責務

history_theme は

User State を保存するものではない。

history_theme は

```text
相談文脈

↓

Meaning Translation

↓

神社文脈
```

を接続するための意味タグである。

利用箇所

- Meaning Translation
- Recommendation
- Recommendation Reason
- Shrine Meaning
- Action Suggestion
- Reflection
- Analytics
- Runtime Snapshot

---

# need_tags の責務

need_tags

```text
ユーザー相談から抽出されたNeed候補
```

matched_need_tags

```text
神社候補と一致したNeed
```

primary_need_tag

```text
代表Need
```

これらは用途が異なるため混同しない。

---

# consultation_axis の責務

consultation_axis は

相談分類を示す代表軸である。

Recommendation Score

Meaning Translation

Recommendation Reason

で利用される。

UI表示用コピーではない。

---

# Fact の責務

Fact は

神社固有情報のみを扱う。

扱える情報

- deity
- shrine_history
- goriyaku
- place_context
- visit_style
- history_theme（意味タグとして）

Fact は

ユーザー状態を解釈しない。

行動提案もしない。

---

# Interpretation の責務

Interpretation は

相談内容を意味付けする。

入力

- consultation_axis
- need_profile
- state_profile
- meaning_translation
- historical_interpretation

Interpretation は

神社固有事実を書かない。

Actionを書かない。

---

# Action の責務

Action は

ユーザーが次に取りやすい一歩を提示する。

Action は

Recommendationの説明を書かない。

Factを書かない。

相談解釈を繰り返さない。

---

# User Connection の責務

Knowledge上の概念である。

Backendでは

Interpretationへ統合される。

独立Payloadは持たない。

---

# 互換維持方針

現段階では物理フィールド名を変更しない。

維持対象

- need_tags
- matched_need_tags
- primary_need_tag
- consultation_axis
- history_theme
- fact
- interpretation
- action
- reason_text
- historyTheme
- consultationAxis

理由

- Snapshot互換
- API契約互換
- Analytics互換
- Frontend互換
- テスト互換

---

# 廃止・整理候補

| 用語 | 問題 | 方針 |
|------|------|------|
| Recommendation Ready | Recommendation Readinessと表記揺れ | Recommendation Readinessへ統一 |
| actionMeaning | ActionなのにMeaningという名称 | 将来的にActionへ寄せる候補 |
| consultationSummary | Interpretationと責務が重なる | UI専用名称として維持 |
| shrineMeaning | FactとMeaningが混在 | UI名称として維持 |
| heroMeaningCopy | Recommendation表示専用 | UI名称として維持 |
| interpretation（Frontend） | Backend Interpretationと粒度差 | ViewModelとして維持 |

---

# 判断保留

以下は監査対象だが、今回変更しない。

- actionMeaning の正式名称変更
- consultationSummary のBackend移行
- shrineMeaning のBackend生成
- heroMeaningCopy の命名整理
- need系の命名統一
- history_theme の概念名変更

---

# Codex実装候補

優先順位1

- Web内部の needTags 系名称整理

優先順位2

- primary_need_tag の責務整理

優先順位3

- Recommendation Reason ViewModel の命名整理

優先順位4

- actionMeaning の命名改善

---

# 完了条件

- [x] 正式用語表を記載
- [x] 概念名と物理名の対応表を記載
- [x] 互換維持方針を記載
- [x] 廃止・整理候補を記載
- [x] Recommendation Reason の3層構造を定義
- [x] Knowledgeと実装の責務対応を整理
- [x] Codex実装候補を整理

---

# 監査結果

Recommendation関連の主要用語について、

- 概念
- Backend
- Frontend
- Knowledge
- Analytics

の責務境界を整理し、現時点では**物理フィールド名は変更せず、概念定義を正本として固定する**方針とする。
