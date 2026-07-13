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
  /** Concierge結果画面など、resultSetIdを取得できる経路からのみ送信する */
  resultSetId?: string | null;
  historyTheme?: string | null;
  /** Concierge結果画面など、recommendationRankを取得できる経路からのみ送信する */
  recommendationRank?: number | null;
  /** 遷移元の`ctx`クエリパラメータから導出する。`ctx`自体はpayloadへ含めない */
  mode?: "need" | "compat";
  accessLevel?: "anonymous" | "free" | "premium";
  routeOpenedBefore?: boolean;
  visitedAt?: string | null;
};
```

### 必須項目

- `source`
- `shrineId`

`historyTheme` は参拝後の分析と振り返り接続に使用するが、値が取得できない場合はキー自体を省略してよい（空文字を送らない）。イベント自体は`historyTheme`の有無にかかわらず必ず送信する。詳細は「Analytics Contract」節の「historyTheme欠損時の扱い」を参照する。

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
  /** 画面ソース。visit_done等の「表示文脈」は`reflectionContext`が担うため、sourceはここでは混在させない */
  source: "concierge_result" | "shrine_detail" | "map" | "shrines";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme?: string | null;
  actionTheme?: string | null;
  /** どのフォーム構造でReflectionを入力させたか */
  reflectionFormType: "one_line" | "mood_delta" | "theme_reflection";
  /** Reflectionがどの文脈で表示されたか */
  reflectionContext: "visit_done" | "mypage" | "night_reflection";
  accessLevel?: "anonymous" | "free" | "premium";
};
```

`reflectionFormType` と `reflectionContext` は、Action Suggestion v4の `reflection_prompt.prompt_type`（`before_visit` / `after_visit` / `decision` / `emotion` / `constraint`）とは異なる語彙である。両者を混在させない。

`source` は「どの画面から送信されたか」を表す全Event共通の語彙とし、`visit_done`/`mypage`/`night_reflection`のような「表示文脈」は`reflectionContext`が単独で担う。両者を混在させない。

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
  source: "concierge_result" | "shrine_detail" | "map" | "shrines";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme?: string | null;
  actionTheme?: string | null;
  reflectionFormType: "one_line" | "mood_delta" | "theme_reflection";
  reflectionContext: "visit_done" | "mypage" | "night_reflection";
  answerLength: number;
  moodBefore?: string | null;
  moodAfter?: string | null;
  accessLevel?: "anonymous" | "free" | "premium";
};
```

`moodBefore`/`moodAfter` はUI入力値をそのまま送信する文字列とする（`ShrineReflection.mood_before`/`mood_after`と同じ`CharField`型に合わせる）。

### 必須項目

- `source`
- `shrineId`
- `reflectionFormType`
- `reflectionContext`
- `answerLength`

`historyTheme`は`visit_done`と同様、値が取得できない場合はキーを省略してよい。

---

## Reflection保存責務

振り返りデータは`ShrineReflection`を正本として保存する。

```python
class ShrineReflection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shrine_reflections",
    )
    shrine = models.ForeignKey(
        "temples.Shrine",
        on_delete=models.CASCADE,
        related_name="reflections",
    )
    thread = models.ForeignKey(
        "temples.ConciergeThread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reflections",
    )
    history_theme = models.CharField(
        max_length=32,
        blank=True,
        default="",
    )
    prompt = models.TextField(
        blank=True,
        default="",
    )
    answer = models.TextField()
    mood_before = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )
    mood_after = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
    )
```

### Index

```python
models.Index(fields=["user", "-created_at"])
models.Index(fields=["shrine", "-created_at"])
models.Index(fields=["history_theme"])
```

### 必須保存項目

- `user`
- `shrine`
- `answer`
- `created_at`

`answer`は空文字を許容しない。UI側も回答が空の間は保存操作をできなくする（「あとで書く」の保存は提供しない）。

### 任意保存項目

- `thread`（`thread_id`としてAPIで送受信する。振り返り対象の参拝のきっかけとなった相談スレッドへの接続キー）
- `history_theme`
- `prompt`
- `mood_before`
- `mood_after`

`history_theme`は値が取得できない場合、空文字ではなくフィールド省略（デフォルト空文字）で扱う。

### 採用しないフィールド

以下は過去検討したが採用しない。理由を明記する。

| フィールド | 採用しない理由 |
|---|---|
| `result_set_id` | Backend側に「推薦結果セット」を一意識別する概念・モデルが存在しない。`thread`（Recommendation Snapshotへの接続キー）を正本とし、`result_set_id`は追加しない |
| `action_theme` | Action Suggestionの実行・完了は`ActionEvent`モデルが別途管理しており、`ShrineReflection`への重複保存にあたる |
| `visited_at` | 「いつ参拝したか」は`Visit.visited_at`の責務であり、Reflection側に重複保存しない |
| `updated_at` | Reflection編集（Update API）が存在しないため、更新日時を持つ意味がない。編集機能を追加する際に再検討する |

### mood_before / mood_after の型

`CharField`（自由記述の文字列）とする。UIは数値スケールではなく自由記述テキストとして`moodBefore`/`moodAfter`を入力させており、Model・Serializer・API・Frontend UI・Analytics Payloadのすべてでこの型に統一済みである。

### 保存しないもの

- 医療的な状態評価
- 宗教的な達成判定
- AIによる断定的な心理分析
- 成功・失敗の自動判定

---

## Visit保存責務

`Visit`は参拝・訪問の完了事実を保存する。

```python
class Visit(models.Model):
    STATUS_CHOICES = [("added", "Added"), ("removed", "Removed")]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visits",
    )
    shrine = models.ForeignKey(
        "temples.Shrine",
        on_delete=models.CASCADE,
        related_name="visits",
    )
    thread = models.ForeignKey(
        "temples.ConciergeThread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits",
    )
    visited_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="added")
```

`thread`は`ShrineReflection`と同様、参拝のきっかけとなった相談スレッドへの接続キーとして任意で保存する。`history_theme`はVisitへ重複保存しない（Analytics Eventのpayloadで扱えば十分であり、DB保存の必要性がない）。

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

- 推薦時点の`history_theme`はRecommendation Snapshot（`ConciergeThread.recommendations_v2`）に保持する
- 振り返り時点の`history_theme`は`ShrineReflection`に保持する
- 過去のRecommendation Snapshotは再計算しない
- 現在のReflection状態はDBから取得する

この分離により、推薦時点の文脈と行動後の記録を混在させない。

推薦時点のSnapshotと、Visit/Reflectionを接続する正本キーは`thread`（`ConciergeThread`への外部キー、API上は`thread_id`）である。`result_set_id`という概念はBackendに存在しないため、接続キーとして採用しない。

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
  mode?: "need" | "compat";
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
| `visit_done` | `source`, `shrineId` |
| `reflection_prompt_view` | `source`, `shrineId`, `reflectionFormType`, `reflectionContext` |
| `reflection_saved` | `source`, `shrineId`, `reflectionFormType`, `reflectionContext`, `answerLength` |

`historyTheme`はいずれのEventでも必須項目に含めない。値が取得できる場合のみpayloadへ含める任意項目として扱う（詳細は次項）。

### historyTheme欠損時の扱い

`Shrine.history_theme`は`blank=True, default=""`であり、本番推薦対象の神社でも値が未設定（空文字）のケースが存在しうる。また神社詳細画面へConcierge経由でなく直接アクセスした場合は、Meaning Layerの意味変換結果（`shrineMeaningPayloadV2`）自体が存在せず、`historyTheme`を取得できない。

以下の方針とする。

- `historyTheme`が取得できない場合でも、`visit_done` / `reflection_prompt_view` / `reflection_saved` のEvent送信自体は行う（Eventを破棄しない）。Funnelの母数（`shrine_detail_view → visit_done → ...`）を`historyTheme`の有無で歪めないことを優先する。
- `historyTheme`の値が取得できない場合は、空文字（`""`）を送らず、payloadから`historyTheme`キー自体を省略する。
- `historyTheme: null`を明示的に送る運用は採用しない（Analytics送信の共通シリアライズ処理が`null`/`undefined`のキーを一律で除外する実装のため、値なし状態はキー省略で統一する）。
- `historyTheme`別の集計では、キーが存在しないレコードを「欠損」として扱う。

### ctxパラメータの扱い

`ctx`（`"map" | "concierge" | null`、遷移元を示すURLクエリパラメータ）は、`visit_done` / `reflection_prompt_view` / `reflection_saved` のpayloadへ直接含めない。`ctx === "concierge"`の場合のみ`mode: "need"`へ変換して送信する（他の`trackCardEvent`系イベントと同じ変換規則）。`ctx`という生のパラメータ名はAnalytics Payload契約に含めない。

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
