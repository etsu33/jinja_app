# Visit / Reflection 文書-実装整合性監査

## 目的

`docs/product/visit-reflection-flow.md`（Event/Payload契約・保存責務の正本）と`docs/product/reflection-funnel-dashboard.md`（Funnel KPI設計）が、実際のBackend実装（Model / API / Serializer / Service）およびWeb / Mobileのanalytics送信実装と一致しているかを検証する。

設計変更・実装変更は行わない。文書と実装の差分を記録することのみを目的とする。

---

## 記載区分

- **事実（Fact）**: リポジトリ内のコードから直接確認できる内容。
- **推測（Inference）**: 事実から論理的に導けるが、直接コード上で確認しきれない内容。推測には必ずその根拠を併記する。

---

## 対象ファイル

### 文書

- `docs/product/visit-reflection-flow.md`
- `docs/product/reflection-funnel-dashboard.md`

### 実装（Backend）

- `backend/temples/models.py`（`Visit`, `ShrineReflection`）
- `backend/temples/api/views/visit.py`, `backend/temples/api/views/reflection.py`
- `backend/temples/api/serializers/visit.py`, `backend/temples/api/serializers/reflection.py`
- `backend/temples/services/action_suggestions.py`（`HISTORY_THEME_ACTION_SUGGESTIONS`）
- `backend/temples/management/commands/seed_history_theme.py`

### 実装（Web）

- `apps/web/src/lib/analytics/searchEvents.ts`
- `apps/web/src/lib/analytics/providers.ts`
- `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`
- `apps/web/src/components/shrine/detail/ShrineReflectionPrompt.tsx`
- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`

### 実装（Mobile）

- `apps/mobile` 配下全体（grep結果、該当実装なし）

---

## 1. 保存モデルの比較

### 1.1 ShrineReflection

【事実】docs定義（`visit-reflection-flow.md`）:

```python
class ShrineReflection(models.Model):
    user, shrine
    thread_id: CharField(max_length=64, blank=True, default="")
    result_set_id: CharField(max_length=255, blank=True, default="")
    history_theme: CharField(max_length=32, db_index=True)
    action_theme: CharField(max_length=64, blank=True, default="")
    prompt: TextField(blank=True, default="")
    answer: TextField(blank=True, default="")
    mood_before: PositiveSmallIntegerField(null=True, blank=True)
    mood_after: PositiveSmallIntegerField(null=True, blank=True)
    visited_at: DateTimeField(null=True, blank=True)
    created_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
```

【事実】実装（`backend/temples/models.py:522`）:

```python
class ShrineReflection(models.Model):
    user, shrine
    history_theme: CharField(max_length=32, blank=True, default="")
    prompt: TextField(blank=True, default="")
    answer: TextField()  # blank指定なし = 必須
    mood_before: CharField(max_length=50, blank=True, default="")
    mood_after: CharField(max_length=50, blank=True, default="")
    created_at: DateTimeField(default=timezone.now)
```

【差分（事実）】

| 項目 | docs | 実装 | 一致 |
|---|---|---|---|
| `thread_id` | あり | なし | 不一致 |
| `result_set_id` | あり | なし | 不一致 |
| `action_theme` | あり | なし | 不一致 |
| `visited_at` | あり | なし | 不一致 |
| `updated_at` | あり | なし | 不一致 |
| `mood_before`/`mood_after`の型 | `PositiveSmallIntegerField`（数値） | `CharField`（文字列） | 不一致 |
| `answer`の必須性 | `blank=True`（任意） | 必須 | 不一致 |
| Index構成 | `["user","created_at"]`, `["user","history_theme"]`, `["shrine","history_theme"]` | `["user","-created_at"]`, `["shrine","-created_at"]`, `["history_theme"]` | 不一致 |

### 1.2 Visit

【事実】docs（`visit-reflection-flow.md`）の記述：「Visit 完了時には以下を保持する: `shrineId`, `threadId`, `history_theme`, `actionTheme`, `visitedAt`」

【事実】実装（`backend/temples/models.py:505`）:

```python
class Visit(models.Model):
    STATUS_CHOICES = [("added", "Added"), ("removed", "Removed")]
    user, shrine
    visited_at: DateTimeField(default=timezone.now)
    note: TextField(blank=True)
    status: CharField(max_length=10, choices=STATUS_CHOICES, default="added")
```

【差分（事実）】`threadId`・`history_theme`・`actionTheme`はVisitモデルに一切保存されない。`visitedAt`のみ一致。

---

## 2. API / Serializer

【事実】`VisitCreateView`（`backend/temples/api/views/visit.py`）が受理するフィールドは `shrine_id` と任意の `visited_at` のみ。`historyTheme`, `threadId`, `resultSetId`, `recommendationRank`, `mode`, `accessLevel`, `routeOpenedBefore` はリクエストから読み取られず、保存もされない。

【事実】`ShrineReflectionCreateView`（`backend/temples/api/views/reflection.py`）が受理・保存するフィールドは `history_theme`, `prompt`, `answer`, `mood_before`, `mood_after` のみ。`thread_id`, `result_set_id`, `action_theme` は受理されない。

【推測】Visit・ShrineReflectionいずれも、`docs/product/visit-reflection-flow.md`の「history_theme履歴」節が定義する「推薦時点のhistory_themeはRecommendation Snapshotに保持する」「振り返り時点のhistory_themeはShrineReflectionに保持する」という設計のうち、後者のみ部分的に実装されている（`history_theme`フィールド自体はShrineReflectionに存在するため）。ただし`thread_id`・`result_set_id`が保存されないため、どのRecommendation Snapshot（=どの相談・どの推薦結果セット）に対するVisit・Reflectionかをモデル単体からは復元できない。根拠：1.1・1.2の差分表、2章のAPI受理フィールド。

---

## 3. Event / Payload

### 3.1 イベント名そのものの一致

【事実】`apps/web/src/lib/analytics/searchEvents.ts`の`SearchAnalyticsEventName`型に `"visit_done"`, `"reflection_prompt_view"`, `"reflection_saved"`, `"shrine_detail_view"`, `"route_open"`, `"concierge_result_impression"` が定義されている。イベント名の文字列自体は`docs/product/visit-reflection-flow.md`・`docs/product/reflection-funnel-dashboard.md`の定義と一致する。

### 3.2 visit_done

【事実】送信元は`ShrineDetailArticle.tsx`1箇所のみ。実際に送信されるpayload：

```ts
trackSearchEvent("visit_done", {
  source: "shrine_detail",
  shrineId: cardProps.shrineId,
  threadId: tid != null ? String(tid) : undefined,
  historyTheme: historyTheme ?? undefined,
  ctx,
});
```

【差分（事実）】

| docs定義の項目 | 実装での送信有無 |
|---|---|
| `source`（`"concierge_result" \| "shrine_detail" \| "mypage"`） | 送信されるが常に`"shrine_detail"`固定。他2値の送信箇所はgrep結果になし |
| `shrineId` | 送信あり |
| `historyTheme`（必須） | 送信あり（ただし`historyTheme`がnullの場合は`undefined`となり実際には送信されない） |
| `resultSetId` | 送信なし |
| `recommendationRank` | 送信なし |
| `mode`（`"need" \| "compat"`） | 送信なし |
| `accessLevel` | 送信なし |
| `routeOpenedBefore` | 送信なし |
| `visitedAt` | 送信なし |
| `ctx` | docs未定義の独自パラメータが送信されている |

### 3.3 reflection_prompt_view

【事実】送信元が2箇所存在する。

**送信元1: `ShrineReflectionPrompt.tsx`**（参拝後の振り返り入力UI表示時）

```ts
trackSearchEvent("reflection_prompt_view", {
  source: "shrine_detail",
  shrineId, threadId, historyTheme,
  promptType: "visit_done_reflection",
  ctx,
});
```

**送信元2: `ConciergeTopRecommendationHero.tsx`**（推薦結果画面でAction Suggestionプレビューを表示した時）

```ts
trackSearchEvent("reflection_prompt_view", {
  source: analyticsSource, threadId, resultSetId, shrineId, recommendationRank,
  position: "hero_primary",
  historyTheme,
  actionSuggestionVersion, primaryActionType, secondaryActionType,
  promptType: visibleActionSuggestionV4Preview.reflectionPrompt.promptType,
  actionSource, sourceKeys, summaryLine,
  reflectionPromptSourceSeed,
});
```

【差分（事実）】

- `promptType`の値がdocs定義（`"one_line" | "mood_delta" | "theme_reflection"`）と一致しない。送信元1は`"visit_done_reflection"`という固定値（docs定義のいずれとも異なる）。送信元2は`action_suggestion_v4.md`が定義する`reflection_prompt.prompt_type`（`"before_visit" | "after_visit" | "decision" | "emotion" | "constraint"`）をそのまま転用している。
- 送信元1は「振り返り入力UIが実際に表示された」タイミングで発火する（docsの定義に近い）。
- 送信元2は「Action Suggestionのプレビューカードが表示された」タイミングで発火しており、振り返り入力UI自体は表示されていない。

【推測】同一イベント名`reflection_prompt_view`が意味の異なる2つのタイミング（実際の振り返り入力UI表示 / 推薦結果でのプレビュー表示）で送信されているため、`reflection-funnel-dashboard.md`が定義するFunnel（`visit_done → reflection_prompt_view → reflection_saved`）の集計値には、参拝と無関係な推薦結果閲覧時点のカウントが混入する可能性がある。根拠：送信元2の発火条件（`visibleActionSuggestionV4Preview`の表示、`visit_done`の発生を前提としない）。

### 3.4 reflection_saved

【事実】送信元は`ShrineReflectionPrompt.tsx`1箇所のみ。

```ts
trackSearchEvent("reflection_saved", {
  source: "shrine_detail",
  shrineId, threadId, historyTheme,
  promptType: "visit_done_reflection",
  answerLength,
  moodBefore, moodAfter,
  ctx,
});
```

【差分（事実）】

| docs定義の必須項目 | 実装での送信有無 |
|---|---|
| `source` | 送信あり（常に`"shrine_detail"`固定） |
| `shrineId` | 送信あり |
| `historyTheme`（必須） | 送信あり（null時は送信されない） |
| `promptType`（必須） | 送信あり。ただし値は`"visit_done_reflection"`固定でdocs定義の3値のいずれとも一致しない |
| `answerLength`（必須） | 送信あり |
| `resultSetId` | 送信なし |
| `moodBefore`/`moodAfter`（任意） | 送信あり（型はstring、docsのpayload型定義も`number`ではなく`string \| null`のため一致） |

---

## 4. Analytics送信元（Web / Mobile）

【事実】Web側の送信元は上記の3ファイルに限定される（grep結果で他に該当なし）。

【事実】`apps/mobile`配下には`visit_done` / `reflection_prompt_view` / `reflection_saved`のいずれの実装も存在しない（grep結果0件）。

【推測】モバイルアプリでは参拝・振り返りのAnalytics計測が未実装であるか、Web版とは別の仕組みで計測している可能性がある。今回のgrep範囲（`apps/mobile`）内では確認できなかった。根拠：grep結果0件。

---

## 5. PostHog Event名

【事実】`apps/web/src/lib/analytics/providers.ts`の`PostHogAnalyticsProvider.track()`は、`trackSearchEvent`から渡された`eventName`文字列をそのまま`posthog.capture(eventName, payload)`へ渡す。イベント名の変換・マッピングは行われない。

【事実】したがって、PostHog上に記録されるイベント名は`visit_done` / `reflection_prompt_view` / `reflection_saved`であり、`docs/product/reflection-funnel-dashboard.md`のFunnel定義（`shrine_detail_view → visit_done → reflection_prompt_view → reflection_saved`）とイベント名は一致する。

【差分（事実）】ただしpayload構造・`promptType`の値は3・4章で示した通り文書と一致しない。

---

## 6. history_theme 7カテゴリとの一致

【事実】`backend/temples/services/action_suggestions.py`の`HISTORY_THEME_ACTION_SUGGESTIONS`のキーは以下の7件で、`docs/product/history-theme-taxonomy.md`の7カテゴリ（守り・静寂・再出発・復興・勝負・学び・縁）と完全に一致する。

```text
守り, 静寂, 再出発, 復興, 勝負, 学び, 縁
```

【事実】`ShrineReflection.history_theme`および`Shrine.history_theme`はいずれも`CharField`で自由文字列を受け入れ、DB層でのchoices制約は存在しない。7カテゴリへの制限はアプリケーションコード（`HISTORY_THEME_ACTION_SUGGESTIONS`等の辞書キー）側でのみ担保されている。

---

## PASS / WARNING / FAIL

### PASS

- イベント名（`visit_done` / `reflection_prompt_view` / `reflection_saved` / `shrine_detail_view`等）自体は、docs・Web実装・PostHog送信の3者で一致している。
- `history_theme`の7カテゴリは、`HISTORY_THEME_ACTION_SUGGESTIONS`のキー集合と`history-theme-taxonomy.md`で完全に一致している。

### WARNING

- `visit_done` / `reflection_saved`の`source`は、docsが定義する3値（`concierge_result` / `shrine_detail` / `mypage`）のうち`shrine_detail`のみが実装されている。他2値からの送信経路は現状存在しない。
- `resultSetId` / `recommendationRank` / `mode` / `accessLevel` / `routeOpenedBefore` / `visitedAt`が、docsでは`visit_done`のPayloadに定義されているが、実装では一切送信されていない。
- `apps/mobile`にVisit / Reflection関連のAnalytics実装が存在しない。

### FAIL

- `ShrineReflection`モデルの実装が、docs定義（`thread_id` / `result_set_id` / `action_theme` / `visited_at` / `updated_at`フィールド、`mood_before`/`mood_after`の型、`answer`の必須性、Index構成）と広範囲に一致しない。
- `Visit`モデルの実装に、docsが「Visit完了時に保持する」と定義する`threadId` / `history_theme` / `actionTheme`が一切存在しない。
- `promptType`の値が、docs定義（`one_line` / `mood_delta` / `theme_reflection`）・実装1（`visit_done_reflection`固定）・実装2（Action Suggestion v4の`prompt_type`を転用）の3系統でまったく異なっており、いずれもdocs定義と一致しない。
- `reflection_prompt_view`イベントが、「参拝後の振り返り入力UI表示」と「推薦結果画面でのAction Suggestionプレビュー表示」という意味の異なる2つのタイミングで同一イベント名として送信されており、docsが定義する単一の意味（振り返り入力UIの表示記録）と一致しない。Funnel集計の解釈に影響する可能性がある。

---

## 総括

`docs/product/visit-reflection-flow.md`はEvent名・Payload型・保存モデルの3点セットで契約を定義しているが、実装（Backend Model・API、Web送信コード）を照合した結果、契約として最も重要な「保存モデルのフィールド構成」と「`promptType`の値体系」が、文書と実装の間で大きく乖離していることが確認できた。イベント名自体の一致とhistory_theme 7カテゴリの一致はPASSであり、Funnelの大枠（どのイベントが発火するか）は文書通りに動作していると考えられるが、Payloadの詳細な内容・`reflection_prompt_view`の発火意味論は文書を正として実装を評価すると一致していない。

本監査は事実の記録に留め、`docs/product/visit-reflection-flow.md`・`reflection-funnel-dashboard.md`の修正、および実装側の修正はいずれも行っていない。正本をどちらに寄せるか（文書を実装に合わせるか、実装を文書に合わせるか）は設計判断が必要なため、次工程の判断に委ねる。
