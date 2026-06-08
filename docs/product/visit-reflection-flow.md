

# Visit Reflection Flow

## 目的

KAMI MUSUBIにおける、参拝完了から振り返り保存までの導線を定義する。

このドキュメントは、`visit_done` event、`reflection_prompt_view` event、`reflection_saved` event、reflection保存テーブル、PostHog分析、history_theme履歴保存の正本として扱う。

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
変化記録
```

---

## 基本方針

- 参拝完了はゴールではなく、振り返りの入口として扱う
- 振り返りは長文日記ではなく、短い変化記録として扱う
- 宗教的・心理的な断定をしない
- 参拝しなかったユーザーにも、日常行動の振り返りを許容する
- Premium価値は、履歴比較・テーマ推移・変化記録に置く

---

## 全体フロー

```text
1. concierge_result_impression
   ↓
2. shrine_detail_transition
   ↓
3. route_open
   ↓
4. visit_done
   ↓
5. reflection_prompt_view
   ↓
6. reflection_saved
   ↓
7. next_consultation_started
```

---

# 1. visit_done event設計

## 目的

ユーザーが参拝・訪問・または推薦後の行動を完了したことを記録する。

`visit_done` は「神社に行ったこと」だけでなく、KAMI MUSUBI上では次の振り返り導線へ進むトリガーとして扱う。

## 発火タイミング

```markdown
- 神社詳細画面で「参拝しました」ボタンを押した時
- route_open後に、一定時間後または後日「行ってきた」を押した時
- 保存済み神社から「参拝済みにする」を押した時
```

## event name

```text
visit_done
```

## payload

```ts
type VisitDonePayload = {
  source: "concierge_result" | "shrine_detail" | "mypage";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme?: string | null;
  recommendationRank?: number | null;
  mode?: "need" | "compat";
  accessLevel?: "anonymous" | "free" | "premium";
  routeOpenedBefore?: boolean;
  visitedAt?: string;
};
```

## 最低限必要なpayload

```markdown
- source
- shrineId
- historyTheme
```

## 注意

`historyTheme` が欠損すると、参拝後の分析ができなくなる。

```text
historyTheme
↓
visit_done率
↓
reflection_saved率
↓
再相談率
```

の比較が崩れるため、本番推薦対象の神社では `historyTheme` を原則必須とする。

---

# 2. reflection_prompt_view event設計

## 目的

参拝完了後、ユーザーに短い振り返り入力を促す表示を記録する。

## 発火タイミング

```markdown
- visit_done後に振り返りカードが表示された時
- マイページの保存済み神社から振り返り導線が表示された時
- 夜の振り返り通知・導線が表示された時
```

## event name

```text
reflection_prompt_view
```

## payload

```ts
type ReflectionPromptViewPayload = {
  source: "visit_done" | "mypage" | "night_reflection";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme?: string | null;
  actionTheme?: string | null;
  promptType: "one_line" | "mood_delta" | "theme_reflection";
  accessLevel?: "anonymous" | "free" | "premium";
};
```

## 表示する質問

質問は `history_theme` に応じて切り替える。

| history_theme | 質問例 |
|---|---|
| 守り | 今日、自分の土台を少し守れたことは何か |
| 静寂 | 今日、静かになれた瞬間はあったか |
| 再出発 | 今日、区切りをつけられたことは何か |
| 復興 | 今日、自分を立て直すためにできたことは何か |
| 勝負 | 今日、前に進むために決めたことは何か |
| 学び | 今日、積み上げたことは何か |
| 縁 | 今日、大切にしたい縁に対して何ができたか |

---

# 3. reflection_saved event設計

## 目的

ユーザーが振り返りを保存したことを記録する。

KAMI MUSUBIの継続価値は、この `reflection_saved` から始まる。

## event name

```text
reflection_saved
```

## payload

```ts
type ReflectionSavedPayload = {
  source: "visit_done" | "mypage" | "night_reflection";
  shrineId: number | string;
  threadId?: string | null;
  resultSetId?: string | null;
  historyTheme: string;
  actionTheme?: string | null;
  promptType: "one_line" | "mood_delta" | "theme_reflection";
  answerLength: number;
  moodBefore?: number | null;
  moodAfter?: number | null;
  accessLevel?: "anonymous" | "free" | "premium";
};
```

## 分析で見ること

```markdown
- visit_done → reflection_saved CVR
- historyTheme別 reflection_saved率
- reflection_saved後の再相談率
- reflection_saved後のpremium_preview_click率
```

---

# 4. reflection保存テーブル設計

## 目的

参拝後・行動後の短い振り返りを保存し、後続の前回比較・月次推移・Premium変化記録に利用する。

## 最小テーブル案

```python
class ShrineReflection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shrine = models.ForeignKey("temples.Shrine", on_delete=models.CASCADE)
    thread_id = models.CharField(max_length=64, blank=True, default="")
    result_set_id = models.CharField(max_length=255, blank=True, default="")
    history_theme = models.CharField(max_length=32, db_index=True)
    action_theme = models.CharField(max_length=64, blank=True, default="")
    prompt = models.TextField(blank=True, default="")
    answer = models.TextField(blank=True, default="")
    mood_before = models.PositiveSmallIntegerField(null=True, blank=True)
    mood_after = models.PositiveSmallIntegerField(null=True, blank=True)
    visited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## index候補

```python
models.Index(fields=["user", "created_at"])
models.Index(fields=["user", "history_theme"])
models.Index(fields=["shrine", "history_theme"])
```

## MVPで保存するもの

```markdown
- user
- shrine
- history_theme
- prompt
- answer
- created_at
```

## MVPで任意にするもの

```markdown
- mood_before
- mood_after
- thread_id
- result_set_id
- action_theme
- visited_at
```

## 保存しないもの

```markdown
- 医療的な状態評価
- 宗教的な達成判定
- AIによる断定的な心理分析
- 長文日記を前提にした本文
```

---

# 5. history_theme履歴保存方針

## 目的

`history_theme` を、単なる推薦理由ではなく、ユーザーの変化記録の軸として保存する。

```text
相談
↓
history_theme
↓
参拝 / 行動
↓
reflection
↓
history_theme履歴
```

## 保存タイミング

```markdown
- consultation saved
- visit_done
- reflection_saved
```

## 保存先候補

```markdown
- ConciergeThread / ConsultationHistory 側に保存
- ShrineReflection 側に保存
- 将来、ThemeHistory集計テーブルを追加
```

## MVP方針

MVPでは、まず `ShrineReflection.history_theme` に保存する。

理由:

```markdown
- 参拝後・行動後の変化と直接接続できる
- historyTheme別 reflection_saved率を集計できる
- Premium変化記録に転用しやすい
```

---

# 6. PostHog event payload定義

## 共通payload

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

## events

```markdown
- visit_done
- reflection_prompt_view
- reflection_saved
```

## event別必須項目

| event | 必須payload |
|---|---|
| visit_done | source / shrineId / historyTheme |
| reflection_prompt_view | source / shrineId / historyTheme / promptType |
| reflection_saved | source / shrineId / historyTheme / answerLength |

## 集計KPI

```markdown
- route_open → visit_done CVR
- visit_done → reflection_prompt_view CVR
- reflection_prompt_view → reflection_saved CVR
- historyTheme別 visit_done率
- historyTheme別 reflection_saved率
- reflection_saved → next_consultation_started率
```

---

# 7. Free / Premium 境界

## Free

Freeでは、短い振り返り保存まで許可する。

```markdown
- 参拝しました
- ひとこと振り返り
- 最新数件の表示
```

## Premium

Premiumでは、履歴比較・月次推移・テーマ変化を表示する。

```markdown
- 前回reflectionとの比較
- history_theme月次推移
- よく出る人生テーマ
- 次の参拝提案
```

## 方針

Premiumは、保存行為そのものではなく、保存された変化を整理して見返す価値に置く。

---

# 8. 今後の実装順

```markdown
- [ ] analytics event typeに visit_done / reflection_prompt_view / reflection_saved を追加
- [ ] ShrineReflection modelを追加
- [ ] migration作成
- [ ] reflection保存APIを追加
- [ ] 神社詳細に visit_done CTA を追加
- [ ] visit_done後に reflection prompt を表示
- [ ] reflection_saved をPostHogへ送信
- [ ] マイページでreflection履歴を表示
- [ ] Premiumで月次推移を表示
```

---

# TODO

```markdown
- [x] visit_done event設計
- [x] reflection_prompt_view event設計
- [x] reflection_saved event設計
- [x] reflection保存テーブル設計
- [x] history_theme履歴保存方針を整理
- [x] PostHog event payload を定義
- [x] docs/product/visit-reflection-flow.md 作成
```
