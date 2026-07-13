> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおける参拝完了から振り返り保存までの体験・イベント・保存責務を定義する正本である。

# Visit Reflection Flow

## 目的

本ドキュメントは、KAMI MUSUBIにおける参拝完了から振り返り保存までの体験、イベント、保存責務を定義する。

参拝完了を体験の終点ではなく、ユーザーが行動後の気づきを整理し、次回相談へ接続する入口として扱う。

```text
route_open
↓
visit_done
↓
reflection_prompt_view
↓
reflection_saved
↓
history_theme履歴
↓
next_consultation
```

---

## 基本原則

- 参拝完了は振り返りの入口として扱う
- 振り返りは短い変化記録として扱う
- 長文日記を前提にしない
- 心理状態を診断しない
- 宗教的な効果や達成を判定しない
- 参拝しなかった場合も、日常行動の振り返りを許容する
- 保存行為と履歴分析の価値を分離する
- `history_theme` を変化記録の共通軸として扱う

---

## 体験フロー

```text
concierge_result_impression
↓
shrine_detail_transition
↓
route_open
↓
visit_done
↓
reflection_prompt_view
↓
reflection_saved
↓
next_consultation_started
```

各段階の責務は以下とする。

| 段階 | 責務 |
|---|---|
| `route_open` | 現地への移動検討を記録する |
| `visit_done` | 参拝・訪問完了を記録する |
| `reflection_prompt_view` | 実際のReflection入力UIが表示されたことだけを記録する |
| `reflection_saved` | 振り返り保存を記録する |
| `next_consultation_started` | 次回相談への再接続を記録する |

`reflection_prompt_view` は、ユーザーが回答できるReflection入力UIの表示のみを対象とする。Concierge結果画面でAction Suggestionの振り返り質問プレビューを表示した場合は、`reflection_prompt_view` ではなく `docs/product/action_suggestion_v4.md` が定義する別イベントを使用する（詳細は本書「reflection_prompt_view」節を参照）。

---

## visit_done

### 責務

ユーザーが参拝・訪問を完了した事実を記録し、振り返り導線を開始する。

`visit_done` は神社へ行った事実を表し、心理的変化や効果を判定しない。

### 発火条件

- 神社詳細で参拝完了を明示したとき
- 経路確認後に訪問完了を明示したとき
- 保存済み神社を参拝済みに変更したとき

### Event名

```text
visit_done
```

### Payload

```ts
type VisitDonePayload = {
  source: "concierge_result" | "shrine_detail" | "mypage";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme: string;
  recommendationRank?: number | null;
  mode?: "need" | "compat";
  accessLevel?: "anonymous" | "free" | "premium";
  routeOpenedBefore?: boolean;
  visitedAt?: string | null;
};
```

### 必須項目

- `source`
- `shrineId`
- `historyTheme`

`historyTheme` は参拝後の分析と振り返り接続に使用する。

---

## reflection_prompt_view

### 責務

ユーザーが回答できるReflection入力UIが実際に表示された事実を記録する。

表示されたことだけを扱い、回答や保存完了は扱わない。

`reflection_prompt_view` は、ユーザーが実際に回答可能なReflection入力フォームの表示にのみ使用する。Action Suggestionの振り返り質問プレビュー（Concierge結果画面で表示される、回答不可のプレビューテキスト）はこのイベントに含めない。プレビュー表示の計測は `docs/product/action_suggestion_v4.md` が定義する `action_suggestion_reflection_preview_view` を使用する。

### 発火条件

- `visit_done` 後に振り返りUIを表示したとき
- マイページから振り返り導線を表示したとき
- 振り返り通知から入力画面を表示したとき

### Event名

```text
reflection_prompt_view
```

### Payload

```ts
type ReflectionPromptViewPayload = {
  source: "visit_done" | "mypage" | "night_reflection";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme: string;
  actionTheme?: string | null;
  /** どのフォーム構造でReflectionを入力させたか */
  reflectionFormType: "one_line" | "mood_delta" | "theme_reflection";
  /** Reflectionがどの文脈で表示されたか */
  reflectionContext: "visit_done" | "mypage" | "night_reflection";
  accessLevel?: "anonymous" | "free" | "premium";
};
```

`reflectionFormType` と `reflectionContext` は、Action Suggestion v4の `reflection_prompt.prompt_type`（`before_visit` / `after_visit` / `decision` / `emotion` / `constraint`）とは異なる語彙である。両者を混在させない。

### 質問生成

振り返り質問は`history_theme`を参照できる。

| history_theme | 質問例 |
|---|---|
| 守り | 今日、自分の土台を少し守れたことは何か |
| 静寂 | 今日、静かになれた瞬間はあったか |
| 再出発 | 今日、区切りをつけられたことは何か |
| 復興 | 今日、自分を立て直すためにできたことは何か |
| 勝負 | 今日、前に進むために決めたことは何か |
| 学び | 今日、積み上げたことは何か |
| 縁 | 今日、大切にしたい縁に対して何ができたか |

質問は答えを誘導せず、状態整理を補助する表現にする。

---

## reflection_saved

### 責務

ユーザーが振り返りを保存した事実を記録する。

`reflection_saved` は保存完了を表し、内容の正しさや心理的改善を判定しない。

### Event名

```text
reflection_saved
```

### Payload

```ts
type ReflectionSavedPayload = {
  source: "visit_done" | "mypage" | "night_reflection";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme: string;
  actionTheme?: string | null;
  reflectionFormType: "one_line" | "mood_delta" | "theme_reflection";
  reflectionContext: "visit_done" | "mypage" | "night_reflection";
  answerLength: number;
  moodBefore?: number | null;
  moodAfter?: number | null;
  accessLevel?: "anonymous" | "free" | "premium";
};
```

### 必須項目

- `source`
- `shrineId`
- `historyTheme`
- `reflectionFormType`
- `reflectionContext`
- `answerLength`

---

## Reflection保存責務

振り返りデータは`ShrineReflection`を正本として保存する。

```python
class ShrineReflection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    shrine = models.ForeignKey(
        "temples.Shrine",
        on_delete=models.CASCADE,
    )
    thread_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )
    result_set_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    history_theme = models.CharField(
        max_length=32,
        db_index=True,
    )
    action_theme = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )
    prompt = models.TextField(
        blank=True,
        default="",
    )
    answer = models.TextField(
        blank=True,
        default="",
    )
    mood_before = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    mood_after = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    visited_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
```

### Index

```python
models.Index(fields=["user", "created_at"])
models.Index(fields=["user", "history_theme"])
models.Index(fields=["shrine", "history_theme"])
```

### 必須保存項目

- `user`
- `shrine`
- `history_theme`
- `prompt`
- `answer`
- `created_at`

### 任意保存項目

- `mood_before`
- `mood_after`
- `thread_id`
- `result_set_id`
- `action_theme`
- `visited_at`

### 保存しないもの

- 医療的な状態評価
- 宗教的な達成判定
- AIによる断定的な心理分析
- 成功・失敗の自動判定

---

## history_theme履歴

`history_theme` は、推薦理由だけでなく、行動後の変化を整理する軸として保存する。

```text
consultation
↓
history_theme
↓
visit / action
↓
reflection
↓
history_theme履歴
```

### 保存責務

- 推薦時点の`history_theme`はRecommendation Snapshotに保持する
- 振り返り時点の`history_theme`は`ShrineReflection`に保持する
- 過去のRecommendation Snapshotは再計算しない
- 現在のReflection状態はDBから取得する

この分離により、推薦時点の文脈と行動後の記録を混在させない。

---

## Analytics Contract

### 共通Payload

```ts
type ReflectionAnalyticsBasePayload = {
  source: string;
  shrineId?: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme?: string | null;
  accessLevel?: "anonymous" | "free" | "premium";
};
```

### Events

- `visit_done`
- `reflection_prompt_view`
- `reflection_saved`

### 必須Payload

| Event | 必須項目 |
|---|---|
| `visit_done` | `source`, `shrineId`, `historyTheme` |
| `reflection_prompt_view` | `source`, `shrineId`, `historyTheme`, `reflectionFormType`, `reflectionContext` |
| `reflection_saved` | `source`, `shrineId`, `historyTheme`, `reflectionFormType`, `reflectionContext`, `answerLength` |

### 集計指標

- `route_open → visit_done` CVR
- `visit_done → reflection_prompt_view` CVR
- `reflection_prompt_view → reflection_saved` CVR
- `historyTheme`別`visit_done`率
- `historyTheme`別`reflection_saved`率
- `reflection_saved → next_consultation_started`率

Analyticsは体験改善の観測に利用し、個別ユーザーの心理状態判定には利用しない。

---

## Free / Premium境界

### Free

Freeでは、参拝記録と短い振り返り保存を提供する。

- 参拝完了の記録
- ひとこと振り返り
- 直近履歴の表示

### Premium

Premiumでは、保存された記録の比較・整理・継続分析を提供する。

- 前回Reflectionとの比較
- `history_theme`の月次推移
- 繰り返し現れるテーマの表示
- 過去記録をもとにした振り返り支援

Premium価値は保存機能そのものではなく、蓄積した変化を比較・整理できることに置く。

---

## 責務境界

### Visit

担当するもの:

- 参拝・訪問完了の事実
- `visited_at`
- 訪問対象の神社
- 振り返り導線の開始

担当しないもの:

- 心理状態の判定
- Reflection回答の保存
- 推薦理由の再生成

### Reflection

担当するもの:

- 振り返り質問
- 回答保存
- moodの任意記録
- `history_theme`との接続

担当しないもの:

- Visit完了判定
- 神社推薦順位
- 医療・心理診断
- 宗教的効果判定

### Analytics

担当するもの:

- 表示・遷移・保存イベントの計測
- Funnel集計
- `historyTheme`別の傾向確認

担当しないもの:

- ユーザー状態の断定
- 推薦理由の生成
- UIの表示判断

---

## 関連ドキュメント

- `docs/product/action_suggestion_v4.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/reflection-funnel-dashboard.md`
- `docs/core/architecture.md`
- `docs/core/narrative-guideline.md`

---

## 更新ルール

本ドキュメントは以下の場合のみ更新する。

- Visit / Reflectionの責務が変更された場合
- Event名またはPayload契約が変更された場合
- `ShrineReflection`の保存責務が変更された場合
- Free / Premium境界が変更された場合
- `history_theme`の保存方針が変更された場合

実装進捗、作業手順、PR計画、TODO、テスト実行履歴は本書へ記載しない。
