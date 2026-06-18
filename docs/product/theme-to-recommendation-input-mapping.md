

# Theme to Recommendation Input Mapping

## 目的

`consultation-theme-taxonomy` で定義した相談テーマを、推薦ロジックで扱う入力へ接続する。

このドキュメントでは、以下の対応を整理する。

- `theme_key` と `need_tags`
- `theme_key` と `consultation_axis`
- `theme_key` と `history_theme`
- Recommendation Score v2 入力との接続
- User State Profile への反映方針

相談テーマはUI上の入口であり、推薦の正本ではない。

推薦の正本は、既存の `need_tags` / `consultation_axis` / `matched_need_tags` を中心に扱う。

---

## 結論

MVPでは、相談テーマを以下のように扱う。

```text
相談テーマチップ
↓
theme_key
↓
consultation_axis 初期ヒント
↓
need_tags 初期ヒント
↓
User State Profile
↓
Recommendation Score v2
```

ただし、自由入力がある場合は自由入力を優先する。

`theme_key` は、ユーザーの状態を断定するものではなく、相談解釈の初期ヒントとして扱う。

---

## 前提

既存の主要レイヤーは以下。

| レイヤー | 正本性 | 役割 |
|---|---:|---|
| theme_key | 低 | UI選択の入口 |
| query / 自由入力 | 高 | ユーザー相談内容の正本 |
| consultation_axis | 中 | 相談意図の分類 |
| need_tags | 高 | 推薦入力の主軸 |
| matched_need_tags | 高 | ユーザー意図と神社側情報の一致結果 |
| history_theme | 中 | 神社側の意味文脈 |

---

## 変換表

| theme_key | 表示文言 | primary consultation_axis | primary need_tags | secondary need_tags | 主な history_theme | 補助 history_theme |
|---|---|---|---|---|---|---|
| work | 仕事について考えたい | career_change | career | courage / mental | 勝負 | 再出発 / 学び |
| relationship | 人との関係を整えたい | relationship_repair | relationship | love / mental | 縁 | 静寂 |
| money | お金の流れを整えたい | money_growth | money | career / courage | 守り | 勝負 / 再出発 |
| challenge | 一歩踏み出したい | restart_mindset | courage | career / mental | 勝負 | 再出発 / 学び |
| rest | 少し休みたい | nature_reset | rest | mental | 静寂 | 復興 |
| health | 体調を整えたい | health | health | protection / rest | 守り | 復興 |
| study | 学びを深めたい | study_success | study | focus / courage | 学び | 勝負 |
| future | これからを考えたい | restart_mindset | mental | courage / career | 再出発 | 静寂 / 学び |

---

## consultation-theme-taxonomy と need_tags の対応

### 方針

`theme_key` は `need_tags` を直接確定しない。

あくまで初期ヒントとして扱う。

### 理由

同じテーマでも、自由入力によって意味が変わるため。

例:

| theme_key | 自由入力 | 優先する need_tags |
|---|---|---|
| rest | 転職するか迷って眠れない | career / mental / rest |
| work | 疲れて何も考えられない | rest / mental |
| money | 起業の売上を伸ばしたい | money / career / courage |
| future | 資格を取って方向性を変えたい | study / career / courage |

---

## consultation_axis との対応

`consultation_axis` は、相談の意図を分類するレイヤーとして扱う。

### MVP方針

- `theme_key` は `consultation_axis` の候補を与える
- 自由入力がある場合は、LLM / 既存ルールの推定を優先する
- `theme_key` と推定 `consultation_axis` がズレた場合は、自由入力由来を優先する

### 対応

| theme_key | axis候補 | 備考 |
|---|---|---|
| work | career_change / career | 転職・仕事運・働き方を含む |
| relationship | relationship_repair / relationship | 恋愛より広い対人関係を含む |
| money | money_growth / money | 金運祈願ではなく経済活動の相談として扱う |
| challenge | restart_mindset / career_change | 挑戦・決断・再出発を含む |
| rest | nature_reset / other | 休息・回復・静けさを含む |
| health | health | 心身・生活基盤の安定を含む |
| study | study_success / study | 学業・資格・継続・集中を含む |
| future | restart_mindset / other | 将来不安・方向性の見直しを含む |

---

## history_theme との対応

`history_theme` は神社側の意味文脈である。

ユーザー側の相談テーマそのものではない。

### 方針

- `theme_key` から `history_theme` を直接確定しない
- 神社側の `history_theme` と `need_tags` の一致を推薦理由に使う
- Meaning Card では、`history_theme` を神社側の文脈として表示する

### 対応候補

| theme_key | つながりやすい history_theme | 解釈 |
|---|---|---|
| work | 勝負 / 再出発 / 学び | 仕事の判断、転機、積み上げ |
| relationship | 縁 / 静寂 | 関係性の整理、距離感の見直し |
| money | 守り / 勝負 / 再出発 | お金の不安、収入行動、生活基盤 |
| challenge | 勝負 / 再出発 / 学び | 挑戦、決断、前進 |
| rest | 静寂 / 復興 | 休息、回復、落ち着き |
| health | 守り / 復興 | 心身と生活の土台を守る |
| study | 学び / 勝負 | 継続、集中、試験、成果 |
| future | 再出発 / 静寂 / 学び | 方向性の再整理、内省、理解 |

---

## Recommendation Score v2入力との接続

### 接続するもの

Recommendation Score v2 では、以下を入力候補として扱う。

```markdown
- query
- need_tags
- consultation_axis
- selected_goriyaku_tag_ids
- extra_condition
- behavior_signal
- context_profile
```

### theme_keyの扱い

`theme_key` は Recommendation Score v2 の直接重みにはしない。

初期段階では、以下の補助情報として扱う。

```markdown
- need_tags抽出の補助
- consultation_axis推定の補助
- analytics property
- UI状態復元
```

### 理由

`theme_key` はUI選択であり、ユーザーの本当の相談意図とは限らない。

推薦スコアで直接強く使うと、自由入力よりチップが優先される危険がある。

---

## User State Profileへの反映

User State Profileでは、以下の優先順位で扱う。

```text
query / 自由入力
↓
need_tags
↓
consultation_axis
↓
theme_key
↓
補助条件
```

### 役割

| 項目 | User State Profileでの役割 |
|---|---|
| query | ユーザー相談内容の正本 |
| need_tags | 推薦入力の主軸 |
| consultation_axis | 相談意図の整理 |
| theme_key | UI上の初期ヒント |
| extra_condition | 参拝体験・条件の補助 |
| birthdate | 相性補助 |
| goriyaku_tag_ids | 神社側特徴との一致補助 |

### 反映方針

- User State Profile の正本は `query` と `need_tags`
- `theme_key` は状態断定には使わない
- `theme_key` は「ユーザーが選んだ入口」として保持する
- 推薦理由では、`matched_need_tags` と神社側情報を優先する

---

## 実装方針

### 初期実装ではやらないこと

```markdown
- theme_keyを直接score加点に使う
- theme_keyだけでhistory_themeを決める
- theme_keyだけでユーザー状態を断定する
- 吉方位や相性とtheme_keyを混ぜる
```

### 初期実装でやる候補

```markdown
- theme_keyをanalytics payloadへ追加する
- theme_keyをUI復元用に保持する
- theme_keyからquery初期文を作る
- theme_keyからneed_tags補助ヒントを渡すか検討する
```

---

## 触る可能性が高いファイル

```text
apps/web/src/features/home/components/HomeHeroConsultationInput.tsx
apps/web/src/features/concierge/components/ConciergeEntryCard.tsx
apps/web/src/features/concierge/buildPayloadFromUnified.ts
apps/web/src/features/concierge/hooks.ts
apps/web/src/features/concierge/types/chatRequest.ts
backend/temples/domain/consultation_axis.py
backend/temples/domain/need_tags.py
backend/temples/services/concierge_chat_ranking.py
docs/analytics/user-state-profile.md
docs/analytics/recommendation-score-v2-current-design.md
```

---

## 次PR候補

### PR1: theme_key共通定数化

```markdown
- [ ] CONSULTATION_THEMES を共通定数として作成
- [ ] HomeHeroConsultationInput を共通定数へ接続
- [ ] ConciergeEntryCard を共通定数へ接続
- [ ] theme_key / label / defaultText を分離
- [ ] typecheck
```

### PR2: theme_key analytics追加

```markdown
- [ ] HomeHeroから theme_key を渡すか検討
- [ ] ConciergeEntryで theme_key を保持するか検討
- [ ] analytics payload に themeKey を追加するか検討
- [ ] PostHogでテーマ別CVRを見られる状態にする
```

### PR3: User State Profile反映

```markdown
- [ ] User State Profileに theme_key の位置付けを追記
- [ ] theme_key は正本ではなく初期ヒントと明記
- [ ] query / need_tags / consultation_axis との優先順位を明記
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/theme-to-recommendation-input-mapping作成
- [x] consultation-theme-taxonomy と need_tags を対応付ける
- [x] consultation_axis を対応付ける
- [x] history_theme を対応付ける
- [x] 変換表を作る
- [x] Recommendation Score v2入力との接続を整理する
- [x] User State Profileへ反映する
```
