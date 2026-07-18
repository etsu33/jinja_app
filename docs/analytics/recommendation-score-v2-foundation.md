> **Status: Reference**
>
> 本ドキュメントは、Recommendation Score v2の設計思想・4レイヤー構成の背景を記録した参照資料である。
>
> 現行のスコア式・重みは`docs/analytics/recommendation-score-v2-current-design.md`を正本とする。

# Recommendation Score v2 Foundation

## 目的

Recommendation Score v2 は、Kamimusubi の商品価値である「今の相談に対して、納得して行動したくなる神社提案」を再現性ある形で高めるための推薦スコア設計である。

この設計では、単に相談文と神社タグを一致させるだけではなく、以下の4レイヤーを組み合わせる。

```text
User State Profile
+
Shrine Meaning Profile
+
Context Profile
+
Behavior Profile
=
Recommendation Score v2
```

MVPでは、まず説明可能で壊れにくいスコアを優先し、将来的に実測CVRで重みを調整する。

---

## 結論

初期版の Recommendation Score v2 は、以下の方針で設計する。

```markdown
- User State を主軸にする
- Shrine Meaning は神社側の意味文脈として扱う
- Context は補助スコアとして扱う
- Behavior は最初から強く効かせず、実測後に重みを上げる
- Compat / 誕生日 / 方位系は補助情報に留める
- 吉方位はDirection Audit完了までスコア本体に入れない
```

初期計算式は以下を仮置きする。

```text
score_v2 =
  user_state_match * 0.40
+ shrine_meaning_match * 0.25
+ context_match * 0.15
+ behavior_match * 0.20
```

ただし、この重みは仮説であり、保存率・詳細閲覧率・ルート閲覧率・参拝完了率・振り返り保存率を見て調整する。

---

## 1. User State Profile定義

### ゴール

ユーザーが今どの状態・目的から相談しているかを、推薦計算の主入力として扱う。

### 現在地

現在の主要入力は以下。

```markdown
- query
- need_tags
- matched_need_tags
- consultation_axis
- theme_key
- selected_goriyaku_tag_ids
- extra_condition
```

### 定義

User State Profile は、以下の情報を持つ。

```ts
UserStateProfile = {
  query: string;
  need_tags: string[];
  consultation_axis?: string | null;
  theme_key?: string | null;
  primary_need_tag?: string | null;
  secondary_need_tags: string[];
  emotional_tone?: "anxious" | "tired" | "stuck" | "hopeful" | "neutral" | null;
  urgency?: "low" | "mid" | "high" | null;
}
```

### 優先順位

```text
query
↓
need_tags
↓
consultation_axis
↓
theme_key
↓
selected_goriyaku_tag_ids
```

### 注意

`matched_need_tags` は User State Profile の正本ではない。

`matched_need_tags` は、ユーザー側の `need_tags` と神社側の情報が一致した結果として扱う。

### 次の一手

```markdown
- [ ] need_tagsをUser Stateの正本として固定
- [ ] consultation_axisを補助分類として扱う
- [ ] theme_keyはUI由来の初期ヒントとして扱う
- [ ] emotional_toneは将来拡張として保持
```

---

## 2. Shrine Meaning Profile定義

### ゴール

神社が持つ意味・文脈・ご利益・歴史テーマを、推薦理由の説明可能性に接続する。

### 現在地

現在の主要入力は以下。

```markdown
- goriyaku
- goriyaku_tags
- history_theme
- culture_translation
- reason_facts
- visit_style_tags
- description
- shrine_meaning
```

### 定義

Shrine Meaning Profile は、以下の情報を持つ。

```ts
ShrineMeaningProfile = {
  shrine_id: number | string;
  name: string;
  goriyaku_tags: string[];
  history_theme?: string | null;
  meaning_keywords: string[];
  visit_style_tags: string[];
  cultural_context?: string | null;
  action_role?: string | null;
}
```

### 役割

```markdown
- need_tagsとの一致を見る
- history_themeで神社側の意味文脈を説明する
- visit_style_tagsで過ごし方の一致を見る
- culture_translationで神社固有性を補強する
```

### 注意

`history_theme` はユーザー状態を断定するために使わない。

神社側が持つ文脈として扱い、Meaning Cardでは「この神社が持つ文脈」として表示する。

### 次の一手

```markdown
- [ ] history_themeとneed_tagsの対応表を固定
- [ ] goriyaku_tagsとneed_tagsの接続を整理
- [ ] visit_style_tagsはContext寄りの補助として扱う
- [ ] culture_translationの使いすぎを避ける
```

---

## 3. Context Profile定義

### ゴール

ユーザーが実際に行きやすいか、体験として合いやすいかを補助的に評価する。

### 現在地

現在の主要入力は以下。

```markdown
- extra_condition
- visit_style_tags
- requested_visit_style_tags
- matched_visit_style_tags
- distance_m
- duration_max_min
- crowd
- location
```

### 定義

Context Profile は、以下の情報を持つ。

```ts
ContextProfile = {
  requested_visit_style_tags: string[];
  shrine_visit_style_tags: string[];
  matched_visit_style_tags: string[];
  distance_m?: number | null;
  duration_max_min?: number | null;
  crowd_preference?: "quiet" | "normal" | "crowded" | null;
  location_available: boolean;
}
```

### 役割

```markdown
- 近場優先
- 静かな場所
- 自然を感じたい
- 有名で安心
- アクセスしやすい
- 境内をゆっくり歩きたい
```

これらを主推薦ではなく、補助条件として反映する。

### 注意

現在地・方角・吉方位は Direction Audit 完了まで Recommendation Score v2 本体に入れない。

### 次の一手

```markdown
- [ ] visit_style_tagsの一致をcontext_matchとして扱う
- [ ] distance_mの扱いを決める
- [ ] location_available=false時のfallbackを定義
- [ ] 吉方位はMVP外として維持
```

---

## 4. Behavior Profile定義

### ゴール

ユーザーの行動から、推薦の納得度・行動意欲・実際の価値を推定する。

### 現在地

現在または近い将来扱う行動シグナルは以下。

```markdown
- save
- detail_view
- route_open
- visit_done
- reflection_saved
```

### 定義

Behavior Profile は、以下の情報を持つ。

```ts
BehaviorProfile = {
  shrine_id: number | string;
  user_id?: number | string | null;
  anonymous_id?: string | null;
  action_counts: {
    save: number;
    detail_view: number;
    route_open: number;
    visit_done: number;
    reflection_saved: number;
  };
  recent_actions: string[];
  last_action_at?: string | null;
}
```

### 役割

```markdown
- 保存した神社は興味が強い
- 詳細閲覧は興味の確認
- ルート閲覧は行動意欲
- 参拝完了は実行完了
- 振り返り保存は体験価値
```

### 注意

Behavior は初期段階で強く効かせすぎない。

理由は、初期ユーザー数が少ない状態では、行動履歴が偏りやすいため。

### 次の一手

```markdown
- [ ] 行動イベントの保存場所を確認
- [ ] 同一user / anonymous_idで集計できるか確認
- [ ] shrine_id単位とtheme単位の集計を分ける
- [ ] 短期行動と長期行動を分ける
```

---

# 行動シグナル重み設計

## save重み設計

### 意味

保存は「あとで見返したい」「候補として残したい」という中程度の興味を表す。

### 仮重み

```text
save_weight = 0.20
```

### 加点方針

```markdown
- 同じ神社を保存済み: +0.20
- 同じtheme_keyで保存傾向あり: +0.10
- 保存後に詳細閲覧あり: detail_view側で評価
```

### 注意

保存だけでは参拝意欲とは限らない。

「気になる」段階として扱う。

---

## detail_view重み設計

### 意味

詳細閲覧は、推薦結果に対して説明や情報を確認しに行った行動である。

### 仮重み

```text
detail_view_weight = 0.15
```

### 加点方針

```markdown
- 推薦後に詳細閲覧: +0.15
- 同じhistory_themeの詳細閲覧が多い: +0.05
- 詳細閲覧のみで離脱: 強加点しない
```

### 注意

詳細閲覧は興味だが、行動意欲としては中程度。

---

## route_open重み設計

### 意味

ルート閲覧は「実際に行く可能性」が高い行動である。

### 仮重み

```text
route_open_weight = 0.30
```

### 加点方針

```markdown
- 推薦後にルート閲覧: +0.30
- detail_view後にroute_open: +0.35
- route_open後にvisit_done: visit_done側で評価
```

### 注意

route_openは行動意欲として強めに扱う。

ただし誤タップや地図確認だけの可能性もあるため、visit_doneほど強くしない。

---

## visit_done重み設計

### 意味

参拝完了は、推薦が実際の行動につながったことを表す。

### 仮重み

```text
visit_done_weight = 0.45
```

### 加点方針

```markdown
- 推薦神社へのvisit_done: +0.45
- route_open後のvisit_done: +0.50
- 同じtheme_keyでvisit_done傾向あり: +0.20
```

### 注意

visit_doneは強いシグナル。

ただし自己申告のため、過度に絶対視しない。

---

## reflection_saved重み設計

### 意味

振り返り保存は、神社体験がユーザーの内省・変化・記録につながったことを表す。

### 仮重み

```text
reflection_saved_weight = 0.55
```

### 加点方針

```markdown
- visit_done後のreflection_saved: +0.55
- reflection内容に次回テーマが含まれる: +0.15
- 同じhistory_themeでreflection_saved傾向あり: +0.20
```

### 注意

reflection_savedは商品価値に最も近い行動シグナル。

「推薦が当たった」ではなく「体験が意味になった」ことを示すため、将来的には最重要KPI候補にする。

---

# Recommendation Score v2計算式設計

## 初期計算式

```text
score_v2 =
  user_state_match * 0.40
+ shrine_meaning_match * 0.25
+ context_match * 0.15
+ behavior_match * 0.20
```

## 各スコア

### user_state_match

```text
user_state_match =
  need_tag_match
+ consultation_axis_match
+ theme_key_hint
```

初期上限は `1.0` とする。

### shrine_meaning_match

```text
shrine_meaning_match =
  need_tags_to_goriyaku_match
+ need_tags_to_history_theme_match
+ culture_context_match
```

初期上限は `1.0` とする。

### context_match

```text
context_match =
  visit_style_match
+ distance_fit
+ access_fit
```

初期上限は `1.0` とする。

### behavior_match

```text
behavior_match =
  save_signal
+ detail_view_signal
+ route_open_signal
+ visit_done_signal
+ reflection_saved_signal
```

初期上限は `1.0` とする。

---

## 初期weight

```ts
const SCORE_V2_WEIGHTS = {
  user_state: 0.40,
  shrine_meaning: 0.25,
  context: 0.15,
  behavior: 0.20,
};

const BEHAVIOR_SIGNAL_WEIGHTS = {
  save: 0.20,
  detail_view: 0.15,
  route_open: 0.30,
  visit_done: 0.45,
  reflection_saved: 0.55,
};
```

---

## KPI

Recommendation Score v2 の改善は、以下のKPIで見る。

```markdown
- save_rate
- detail_view_rate
- route_open_rate
- visit_done_rate
- reflection_saved_rate
- save_to_route_open_rate
- route_open_to_visit_done_rate
- visit_done_to_reflection_saved_rate
```

---

## 実装順

### PR1: Profile定義

```markdown
- [ ] User State Profile型を定義
- [ ] Shrine Meaning Profile型を定義
- [ ] Context Profile型を定義
- [ ] Behavior Profile型を定義
```

### PR2: Score v2計算器

```markdown
- [ ] score_v2 weightsを定義
- [ ] 各profileからpartial scoreを計算
- [ ] breakdownを返す
- [ ] 既存scoreと並行運用する
```

### PR3: 行動シグナル接続

```markdown
- [ ] save signalを接続
- [ ] detail_view signalを接続
- [ ] route_open signalを接続
- [ ] visit_done signalを接続
- [ ] reflection_saved signalを接続
```

### PR4: 分析ダッシュボード接続

```markdown
- [ ] score_v2別save_rateを見る
- [ ] score_v2別route_open_rateを見る
- [ ] score_v2別visit_done_rateを見る
- [ ] score_v2別reflection_saved_rateを見る
```

---

## 今回やらないこと

```markdown
- 吉方位ロジック本実装
- 九星気学ロジック本実装
- 方角計算のscore本体投入
- behaviorだけで推薦を上書きする
- 誕生日だけで推薦順位を決める
- LLMだけでscoreを決める
```

---

## TODO

```markdown
- [x] develop最新化
- [x] docs/recommendation-score-v2-foundation作成
- [x] User State Profile定義
- [x] Shrine Meaning Profile定義
- [x] Context Profile定義
- [x] Behavior Profile定義
- [x] save重み設計
- [x] detail_view重み設計
- [x] route_open重み設計
- [x] visit_done重み設計
- [x] reflection_saved重み設計
- [x] Recommendation Score v2計算式設計
```
