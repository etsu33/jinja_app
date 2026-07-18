> **Status: Reference**
>
> 本ドキュメントは、Reflectionから次回推薦への接続に関する設計背景を記録した参照資料である。
>
> 現行の体験フローは`docs/product/visit-reflection-flow.md`、正確な実装は関連するBackend実装コードおよびテストを最終的な正本とする。

# Reflection → Next Recommendation Design

## 目的

`visit_done → reflection_saved → history → next_recommendation` の流れを整理し、振り返りデータを次回推薦にどう利用するかを設計する。

KAMI MUSUBI の体験は、単なる神社検索ではなく、以下の循環を作ることを目指す。

```text
悩み・状態
↓
意味解釈
↓
神社
↓
参拝
↓
振り返り
↓
再訪・次回推薦
```

このドキュメントでは、既存実装で接続済みの部分と、今後追加すべき設計を分離する。

---

## 1. 現在の既存接続

### 1.1 Model

対象モデルは以下。

```text
backend/temples/models.py
```

| model | 役割 |
|---|---|
| `Visit` | 参拝済み状態を保存する |
| `ShrineReflection` | 参拝後の振り返りを保存する |
| `ShrineInteractionLog` | detail_view / route_open / shrine_card_click などの行動ログを保存する |

`Visit` は `status="added"` を参拝済みとして扱う。

`ShrineReflection` は以下を保持する。

```text
user
shrine
history_theme
prompt
answer
mood_before
mood_after
created_at
```

現時点では、振り返り本文そのものから状態変化を構造化する処理はまだない。

---

## 2. visit_done / reflection_saved API

### visit_done 相当

```text
backend/temples/api/views/visit.py
```

`VisitCreateView` が `Visit` を作成する。

```text
POST /api/...visit...
```

保存内容:

```text
user
shrine
visited_at
status=added
```

### reflection_saved 相当

```text
backend/temples/api/views/reflection.py
```

`ShrineReflectionCreateView` が `ShrineReflection` を作成する。

保存内容:

```text
user
shrine
history_theme
prompt
answer
mood_before
mood_after
```

---

## 3. action_state 更新ロジック

対象:

```text
backend/temples/services/concierge_history.py
```

`classify_shrine_action_state` は以下の優先順位で状態を返す。

```text
reflected
visited
saved
route_opened
detail_viewed
none
```

つまり、すでに以下の状態遷移は表現できる。

```text
detail_viewed
↓
route_opened
↓
saved
↓
visited
↓
reflected
```

この状態は recommendation item の `action_state` に付与される。

---

## 4. behavior_signal の既存接続

対象:

```text
backend/temples/services/concierge_history.py
backend/temples/services/concierge_chat_ranking.py
```

`calculate_shrine_behavior_signal_v2` は以下の重みで行動をスコア化する。

| action | score |
|---|---:|
| detail_view | count × 0.2 × recency |
| route_open | count × 0.6 × recency |
| save | 1.5 × recency |
| visit | 3.0 × recency |
| reflection | 4.0 × recency |

この値は `concierge_chat_ranking.py` で `score_v2` に接続される。

```text
behavior_signal
behavior_contribution
capped_behavior_contribution
behavior_ratio
```

行動シグナルの影響は、相談内容ベースの ranking score に対して最大30%までに制限されている。

つまり現時点でも、以下はすでに成立している。

```text
振り返り済みの神社
↓
behavior_signal が上がる
↓
次回推薦でやや上がりやすくなる
```

---

## 5. behavior_funnel CVR

対象:

```text
backend/temples/services/behavior_funnel.py
```

既存で以下を計測できる。

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
save_to_visit_cvr
visit_to_reflection_cvr
```

重要KPI:

| KPI | 意味 |
|---|---|
| `save_to_visit_cvr` | 保存が実際の参拝につながったか |
| `visit_to_reflection_cvr` | 参拝が振り返りにつながったか |

今後の改善では、単に推薦精度を見るのではなく、以下を優先して見る。

```text
推薦 → 保存 → 参拝 → 振り返り
```

---

## 6. 現時点で足りないもの

現在は「振り返りをした事実」は次回推薦に使えている。

しかし、以下はまだ使えていない。

```text
振り返りの内容
mood_before / mood_after の変化
answer から読み取れる状態変化
history_theme ごとの変化傾向
```

つまり現状は以下。

```text
reflection_saved
↓
行動シグナルとして加点
```

今後目指す形は以下。

```text
reflection_saved
↓
状態変化を抽出
↓
次回推薦の need / history_theme / action_suggestions に反映
```

---

## 7. reflection内容から状態変化を抽出する設計

### 7.1 最小構造

まずは `ShrineReflection` の既存フィールドを使う。

```text
mood_before
mood_after
answer
history_theme
created_at
```

初期設計では、新規モデルを増やさず、service 層で以下を算出する。

```text
state_change_direction
state_change_summary
next_need_hint
next_history_theme_hint
```

### 7.2 state_change_direction

候補:

```text
improved
unchanged
worsened
unknown
```

判定材料:

```text
mood_before
mood_after
answer
```

初期PRでは、LLM判定ではなくルールベースでよい。

例:

| before | after | direction |
|---|---|---|
| 不安 | 落ち着いた | improved |
| 疲れた | 少し軽い | improved |
| 変わらない | 変わらない | unchanged |
| まだ不安 | もっと不安 | worsened |

### 7.3 next_need_hint

振り返り内容から、次回相談に使える need tag 候補を抽出する。

例:

| answer の内容 | next_need_hint |
|---|---|
| 少し落ち着いたが、次は動きたい | courage |
| まだ不安が強い | mental |
| 仕事の方向性を考えたい | career |
| 人とのつながりを見直したい | relationship / love |

### 7.4 next_history_theme_hint

振り返り内容と前回 history_theme から、次のテーマ候補を出す。

例:

| 前回 history_theme | reflection | 次の候補 |
|---|---|---|
| 静寂 | 落ち着いたので次は動きたい | 勝負 / 再出発 |
| 守り | 不安は少し減った | 再出発 |
| 勝負 | 決めきれなかった | 静寂 / 守り |
| 縁 | 連絡してみたい | 縁 / 勝負 |

---

## 8. 状態変化を次回推薦へ利用する設計

### 8.1 短期

まずは ranking に直接入れすぎない。

理由:

```text
reflection本文の解釈は誤判定リスクがある
推薦の主軸は query / need_tags / history_theme のまま維持したい
```

初期利用は以下に限定する。

```text
explanation
next action suggestion
history card
```


### 8.2 中期

`next_need_hint` と `next_history_theme_hint` を次回推薦の補助シグナルにする。

使い方:

```text
query need_tags
+ 
reflection next_need_hint
+ 
recent history_theme
```

ただし、補助シグナルとして扱い、query 由来の need_tags を上書きしない。

### reflection_hint ranking policy

- reflection_hint は現時点では ranking に直接加点しない
- next_need_hint / next_history_theme_hint は次回推薦補助候補として扱う
- 次回相談の need_tags と next_need_hint の一致率を観測する
- 一致率が高ければ weak boost として別PRで設計する

### 8.3 長期

Recommendation Score v3 では、以下を追加する。

```text
reflection_state_change_match
recent_reflection_theme_match
user_preferred_history_theme
```

ただし、最初から v3 に入れない。

まずは記録と監査を優先する。

---

## 9. PR分解

### PR1: 現状設計docs

ブランチ:

```text
feature/reflection-next-recommendation-design
```

目的:

```text
visit_done / reflection_saved / behavior_signal / next_recommendation の現状と次設計を整理する
```

対象:

```text
docs/analytics/reflection-next-recommendation-design.md
```

---

### PR2: reflection state change service

ブランチ:

```text
feature/reflection-state-change-service
```

目的:

```text
ShrineReflection から state_change_direction / next_need_hint / next_history_theme_hint を算出する service を追加する
```

対象候補:

```text
backend/temples/services/reflection_state_change.py
backend/temples/tests/services/test_reflection_state_change.py
```

---

### PR3: reflection history card

ブランチ:

```text
feature/reflection-history-card-contract
```

目的:

```text
振り返り履歴に mood_before / mood_after / history_theme / state_change_summary を出せる contract を定義する
```

対象候補:

```text
backend/temples/api/serializers/reflection.py
backend/temples/api/views/reflection.py
frontend reflection history UI
```

---

### PR4: next recommendation reflection hint

ブランチ:

```text
feature/recommendation-reflection-hint
```

目的:

```text
次回推薦時に recent reflection の next_need_hint / next_history_theme_hint を補助情報として使う
```

対象候補:

```text
backend/temples/services/concierge_history.py
backend/temples/services/concierge_chat.py
backend/temples/services/concierge_chat_ranking.py
```

---

## 10. 優先順位

今は以下の順で進める。

```text
1. reflection-next-recommendation-design docs を確定
2. reflection_state_change service を追加
3. reflection history card contract を定義
4. recommendation に reflection hint を補助接続
```

理由:

```text
既存 behavior_signal はすでにある
まず足りないのは reflection の中身を構造化する層
ranking へ直接入れるのは最後でよい
```

---

## TODO

```markdown
- [x] develop 最新化
- [x] feature/reflection-next-recommendation-design 作成
- [x] Visit / ShrineReflection / ShrineInteractionLog の存在確認
- [x] visit_done / reflection_saved API確認
- [x] action_state更新ロジック確認
- [x] behavior_funnel CVR確認
- [x] score_v2 の behavior_signal 接続確認
- [x] reflection → next_recommendation の既存接続を整理
- [x] reflection内容から状態変化を抽出する設計
- [x] 状態変化を次回推薦へ利用する設計
- [x] docs/analytics/reflection-next-recommendation-design.md 作成
```
