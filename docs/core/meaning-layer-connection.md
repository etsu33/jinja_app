# Meaning Layer Connection

## 目的

本ドキュメントは、Meaning Layer が Consultation Interpretation、Recommendation、Composer とどのように接続されるかを定義する。

詳細な実装、API契約、テスト方針は各正本ドキュメントへ委譲し、本書では接続責務のみを扱う。

---

# 全体フロー

```text
User Input
↓
Consultation Interpretation
↓
interpretation_profile
↓
Meaning Translation
↓
translation_result
↓
ShrineMeaningComposer
↓
generated
↓
Recommendation / Detail
```

Meaning Layer は、相談解釈と神社固有情報を接続し、Recommendation および Detail が利用する意味情報を生成する。

---

# 入力

Meaning Layer は以下を入力として受け取る。

```text
interpretation_profile
Shrine Fact
Shrine Meaning
```

主な入力項目

- state_profile
- need_profile
- direction_profile
- emotion_profile
- action_intent
- Shrine.history_theme
- Shrine 固有情報

---

# 出力

Meaning Layer は `translation_result` を生成する。

主な出力

```text
history_theme
historicalContext
action_context
actionMeaning
reflection_question_seed
```

Composer は `translation_result` を利用し、表示用データを生成する。

---

# Composer との接続

Meaning Layer は `ShrineMeaningComposer` を通して表示データへ接続する。

```text
translation_result.history_theme
→ generated.historyContext

translation_result.action_context
→ generated.actionMeaning

translation_result.reflection_question_seed
→ generated.afterVisitReflection
```

表示文言の最終決定は Composer が担当する。

Meaning Layer は表示コピーを直接生成しない。

---

# Recommendation との接続

Meaning Layer は Recommendation の意味入力として利用される。

```text
Shrine Fact
+
translation_result
+
interpretation_profile
↓
Recommendation Match
↓
Recommendation Reason
```

Meaning Layer は推薦順位を直接決定しない。

Recommendation が候補選定と Runtime Snapshot の生成を担当する。

---

# Fallback

Meaning Layer は意味情報が不足する場合、既存データへ安全にフォールバックする。

```text
history_theme
→ Shrine.history_theme

action_context
→ HISTORY_THEME_ACTION_CONTEXT

reflection_question_seed
→ afterVisitReflection
```

Meaning Layer は fallback を提供するが、表示文言の生成は Composer の責務とする。

---

# 責務境界

Meaning Layer が担当するもの

- 意味情報の構造化
- 神社文脈との接続
- Action / Reflection の材料生成
- Composer への意味入力提供

Meaning Layer が担当しないもの

- 推薦順位の決定
- 表示コピーの最終生成
- UI描画
- 心理診断
- 宗教的保証

---

# 保存方針

Meaning Layer 自体は永続データを保持しない。

Recommendation 生成時に利用された意味情報は Runtime Snapshot として保存する。

保存対象の例

- recommendation reason
- action suggestion
- score_v2
- score components
- evidence

Meaning Layer 自体は Snapshot の保存責務を持たない。

---

# 関連ドキュメント

本レイヤーの詳細仕様は以下を正本とする。

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/shrine-detail-layer.md`
- `docs/premium-experience.md`

本ドキュメントは接続仕様のみを定義する。

API契約、実装詳細、テストケースは各正本ドキュメントで管理する。
