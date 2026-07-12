# Meaning Translation Mapping

## 目的

本ドキュメントは、KAMI MUSUBI における相談テーマ・相談状態・ご利益・神社文脈・行動提案の対応関係を一つに統合する正本である。

対象範囲は以下とする。

- `theme_key` から相談解釈への接続
- 相談状態から `history_theme` への変換
- ご利益から `history_theme` への補助変換
- 神社ごとの `history_theme` 付与方針
- `history_theme` から Action / Reflection への接続
- Recommendation / Runtime Snapshot / Analytics との接続

本書は「一つの入力から一つの答えを機械的に決める表」ではない。

自由入力を正本とし、UI選択・ご利益・誕生日・占術情報は補助シグナルとして扱う。

---

# 全体フロー

```text
相談テーマ / 自由入力
        │
        ▼
Consultation Interpretation
        │
        ▼
state_profile
need_profile
consultation_axis
emotion_profile
        │
        ▼
Meaning Translation
        │
        ▼
history_theme
action_context
reflection_question_seed
        │
        ▼
Shrine Fact / Shrine Meaning
        │
        ▼
Recommendation Match
        │
        ▼
Recommendation Reason
Action Suggestion
        │
        ▼
Visit
        │
        ▼
Reflection
```

Meaning Translation は Recommendation の補助レイヤーであり、順位決定レイヤーではない。

---

# 正本性と優先順位

## 正本レイヤー

| 項目 | 正本性 | 役割 |
|------|--------|------|
| query / 自由入力 | 高 | ユーザー相談内容の正本 |
| need_tags | 高 | 推薦入力の主軸 |
| consultation_axis | 中 | 相談意図の分類 |
| state_profile | 中 | 現在状態の構造化 |
| theme_key | 低 | UI選択の入口 |
| goriyaku_tag_ids | 低〜中 | 明示された願い |
| history_theme | 中 | 神社側の意味文脈 |
| matched_need_tags | 高 | User × Shrine の一致結果 |

優先順位は以下とする。

```text
query / 自由入力
        │
        ▼
need_tags
        │
        ▼
consultation_axis
state_profile
        │
        ▼
theme_key
        │
        ▼
補助条件
```

theme_key・ご利益・誕生日・占術・吉方位だけで推薦結果を決定しない。

---

# 相談テーマから推薦入力への接続

## 基本方針

相談テーマ（theme_key）は推薦理由を決定するものではない。

theme_key は

- consultation_axis の初期候補
- need_tags の初期ヒント
- Analytics
- UI復元

に利用する。

自由入力が存在する場合は自由入力を優先する。

```text
相談テーマチップ
        │
        ▼
theme_key
        │
        ▼
consultation_axis（初期候補）
        │
        ▼
need_tags（初期候補）
        │
        ▼
Consultation Interpretation
```

---

## 対応表

| theme_key | 表示文言 | consultation_axis候補 | primary need_tags | secondary need_tags | history_theme候補 |
|-----------|----------|----------------------|------------------|--------------------|-------------------|
| work | 仕事について考えたい | career_change | career | courage / mental | 勝負・再出発・学び |
| relationship | 人との関係を整えたい | relationship_repair | relationship | love / mental | 縁・静寂 |
| money | お金の流れを整えたい | money_growth | money | career / courage | 守り・勝負・再出発 |
| challenge | 一歩踏み出したい | restart_mindset | courage | career / mental | 勝負・再出発・学び |
| rest | 少し休みたい | nature_reset | rest | mental | 静寂・復興 |
| health | 体調を整えたい | health | health | protection | 守り・復興 |
| study | 学びを深めたい | study_success | study | focus | 学び・勝負 |
| future | これからを考えたい | restart_mindset | mental | courage / career | 再出発・静寂・学び |

---

## 自由入力を優先する例

| theme_key | 自由入力 | 優先される need_tags |
|-----------|---------|----------------------|
| rest | 転職するか迷って眠れない | career / mental / rest |
| work | 疲れて何も考えられない | rest / mental |
| money | 起業の売上を伸ばしたい | money / career / courage |
| future | 資格を取って方向性を変えたい | study / career / courage |

theme_key は「入口」であり、状態を断定するものではない。

---

# 相談状態から history_theme への変換

## 基本方針

相談状態を直接ご利益へ変換しない。

まず状態を整理し、その状態を人生テーマ（history_theme）へ翻訳する。

```text
相談状態
      │
      ▼
history_theme
      │
      ▼
神社
```

これにより、同じご利益でも異なる推薦理由を生成できる。

---

## 対応表

| 相談状態 | primary history_theme | secondary history_theme | 解釈 |
|-----------|----------------------|------------------------|------|
| 不安が強い | 守り | 静寂 | まず土台を整える |
| 将来が見えない | 再出発 | 静寂 | 一度立ち止まり方向を見直す |
| 疲れている | 静寂 | 復興 | 回復を優先する |
| 落ち込んでいる | 復興 | 静寂 | エネルギーを取り戻す |
| やり直したい | 再出発 | 復興 | 区切りを作る |
| 転職を考えている | 再出発 | 勝負 | 環境変化と挑戦 |
| 独立したい | 勝負 | 再出発 | 挑戦と決断 |
| 挑戦したい | 勝負 | 学び | 前へ進む準備 |
| 決断したい | 勝負 | 守り | 覚悟と選択 |
| 自信がない | 復興 | 学び | 自己効力感の回復 |
| 勉強したい | 学び | 勝負 | 積み上げと成長 |
| 人間関係で悩む | 縁 | 静寂 | 関係性の整理 |
| 健康が不安 | 守り | 復興 | 生活基盤を守る |
| お金が不安 | 守り | 再出発 | 不安を減らし生活を整える |
| 商売を伸ばしたい | 勝負 | 再出発 | 攻めと変化 |
| 自分を見つめ直したい | 静寂 | 学び | 内省と理解 |

---
# ご利益 → history_theme

## 基本方針

ご利益は推薦結果を決めるものではなく、ユーザーが入力しやすい「願いの入口」として扱う。

Meaning Translation では、ご利益を直接推薦理由へ変換せず、`history_theme` を経由して神社の意味文脈へ接続する。

```text
ご利益
    │
    ▼
history_theme
    │
    ▼
Shrine Meaning
    │
    ▼
Recommendation Reason
```

同じご利益でも、相談状態によって異なる `history_theme` が選ばれる。

---

## 対応例

| ご利益 | primary history_theme | secondary history_theme | 解釈 |
|---------|----------------------|-------------------------|------|
| 金運 | 守り | 勝負・再出発 | 生活基盤・収入・働き方 |
| 商売繁盛 | 勝負 | 再出発 | 商い・挑戦・成長 |
| 仕事運 | 勝負 | 学び | 決断・努力・成果 |
| 開運 | 再出発 | 勝負 | 区切り・流れの変化 |
| 厄除け | 守り | 復興 | 不安やリスクから距離を置く |
| 縁結び | 縁 | 守り | 人・機会とのつながり |
| 学業成就 | 学び | 勝負 | 積み上げ・継続 |
| 病気平癒 | 復興 | 守り | 回復・生活基盤 |
| 家内安全 | 守り | 縁 | 暮らしと家族 |
| 交通安全 | 守り | 再出発 | 安全な移動 |

---

## ご利益の扱い

悪い例

> 「この神社は金運が上がります。」

良い例

> 「金運という願いを、今は生活基盤を整えるテーマとして受け止めています。」

効果保証・運勢保証・宗教的断定は行わない。

---

# history_theme 定義

## 基本方針

`history_theme` は、ユーザーではなく「神社が持つ意味文脈」を表す。

相談状態・ご利益・神社情報を一度このレイヤーへ翻訳し、

- Recommendation
- Action Suggestion
- Reflection
- Analytics

で共通利用する。

---

## MVPカテゴリ

| history_theme | 意味 |
|---------------|------|
| 守り | 土台・安心・生活基盤 |
| 静寂 | 内省・休息・整理 |
| 再出発 | 区切り・新しい一歩 |
| 復興 | 回復・立て直し |
| 勝負 | 決断・挑戦 |
| 学び | 継続・成長 |
| 縁 | 人・機会とのつながり |

---

## 神社への付与方針

`history_theme` は以下を総合して決定する。

- 神社の由緒
- 御祭神
- 歴史
- ご利益
- 土地性
- コンシェルジュで伝えたい意味

ご利益だけで決定しない。

---

## 分析への利用

`history_theme` は Recommendation だけでなく、Behavior Funnel の分析軸として利用する。

```text
Consultation
      │
      ▼
history_theme
      │
      ▼
Recommendation
      │
      ▼
Visit
      │
      ▼
Reflection
```

主な分析対象

- Recommendation CTR
- Detail View
- Route Open
- Visit
- Reflection
- 継続利用率

---

## 将来拡張

MVPでは以下の7カテゴリに限定する。

将来的に必要性が確認できた場合のみ、

- 導き
- 巡り
- 浄化

などの追加を検討する。

カテゴリ追加は、Recommendation・Meaning Layer・Analytics すべてへの影響を確認したうえで実施する。

# history_theme → Action / Reflection

## 基本方針

`history_theme` は推薦理由で終わらず、

- Action Suggestion
- Visit
- Reflection
- Behavior Analytics

まで一貫して利用する。

```text
history_theme
        │
        ▼
Action Theme
        │
        ▼
Action Suggestion
        │
        ▼
Visit
        │
        ▼
Reflection
        │
        ▼
Behavior Analytics
```

AIは行動を強制しない。

「今日できる小さな一歩」を提示する補助レイヤーとして扱う。

---

# history_theme ごとの行動テーマ

| history_theme | 行動テーマ | 参拝時の例 | 日常行動例 | Reflection例 |
|---------------|-----------|-----------|------------|--------------|
| 守り | 土台を整える | 今守りたいものを一つ思い浮かべる | 生活基盤を一つ整える | 今日守れたことは何か |
| 静寂 | 情報から距離を置く | 静かな時間を過ごす | 通知を切る・休む | 静かになれた瞬間はあったか |
| 再出発 | 区切りを作る | 手放したいことを言葉にする | 明日の一歩を決める | 今日区切りを付けられたことは何か |
| 復興 | 回復を優先する | 疲れを認める | 睡眠・食事・休息 | 回復のためにできたことは何か |
| 勝負 | 次の一歩を決める | 決めたいことを書き出す | 応募・相談・予約などを行う | 今日決断したことは何か |
| 学び | 積み上げる | 学びたいことを確認する | 15分だけ学習する | 今日積み上げたことは何か |
| 縁 | 関係を育てる | 大切な人を思い浮かべる | 感謝・連絡・距離調整 | 今日大切にした縁は何か |

---

# Visit との接続

Visit は「参拝した事実」を保存するレイヤーである。

```text
Route
    │
    ▼
Visit
    │
    ▼
Reflection
```

Visit 完了時には以下を保持する。

- shrineId
- threadId
- history_theme
- actionTheme
- visitedAt

---

# Reflection との接続

Reflection は正解を評価するものではない。

参拝後の状態変化を記録する。

保存対象の例

- history_theme
- actionTheme
- prompt
- answer
- moodBefore
- moodAfter
- createdAt

保存しないもの

- 心理診断
- 医療判断
- 宗教的達成判定
- AIによる人生評価

---

# Runtime Snapshot との関係

Meaning Translation の結果は Runtime Snapshot に保持される。

保持対象例

- history_theme
- action_context
- reflection_question_seed
- matched_need_tags
- recommendation_reason
- action_suggestion

Runtime Snapshot は推薦生成時点の状態を保存する。

保存後に再計算しない。

---

# Analytics との接続

Meaning Translation は Behavior Funnel の分析にも利用する。

```text
Consultation
        │
        ▼
Recommendation
        │
        ▼
Detail
        │
        ▼
Route
        │
        ▼
Visit
        │
        ▼
Reflection
```

主な分析対象

- Recommendation CTR
- Detail View
- Route Open
- Visit Rate
- Reflection Rate
- 継続利用率
- history_theme 別CVR
- history_theme 別継続率

---

# Responsibility

Meaning Translation の責務

- Recommendation の補助
- Action Theme の生成
- Reflection Prompt の生成
- Runtime Snapshot への保持
- Analytics 軸の提供

責務外

- 推薦順位の決定
- UI表示
- 神社マスター更新
- 行動の強制
- 効果保証
- 心理診断
- 宗教的判断

# 神社ごとの history_theme 付与方針

## 基本方針

`history_theme` は神社ごとの意味文脈を表す。

分類はご利益だけで決定せず、神社そのものが持つ背景を総合して判断する。

```text
神社
    │
    ▼
history_theme
    │
    ▼
Recommendation
Action
Reflection
Analytics
```

---

## 判定要素

神社の `history_theme` は以下を総合して決定する。

- 御祭神
- 神社の由緒
- 歴史的背景
- ご利益
- 土地性
- コンシェルジュで伝えたい意味

ご利益だけで分類しない。

---

## MVPカテゴリ

MVPでは以下の7カテゴリに限定する。

| history_theme | 意味 |
|---------------|------|
| 守り | 土台・安心・生活基盤 |
| 静寂 | 内省・休息・整理 |
| 再出発 | 区切り・新しい一歩 |
| 復興 | 回復・立て直し |
| 勝負 | 決断・挑戦 |
| 学び | 継続・成長 |
| 縁 | 人・機会とのつながり |

---

## 神社分類例

| 神社の特徴 | history_theme |
|------------|---------------|
| 商売繁盛・勝運 | 勝負 |
| 縁結び・良縁 | 縁 |
| 厄除け・家内安全 | 守り |
| 学業・知恵 | 学び |
| 病気平癒・回復 | 復興 |
| 静かな山・自然・内省 | 静寂 |
| 再建・再生・転機 | 再出発 |

---

## 管理方針

本番推薦対象の神社は、原則 `history_theme` を持つ。

```text
Shrine
    │
    ▼
history_theme 必須
```

テスト神社は分析対象外とする。

情報不足の場合のみ一時的に未設定を許容する。

---

## 運用方針

新規神社登録時は

```text
ShrineSubmission
        │
        ▼
Admin Review
        │
        ▼
history_theme 決定
        │
        ▼
公開
```

承認時に `history_theme` を確定する。

---

# Recommendation との接続

Meaning Translation は Recommendation を補助する。

```text
Consultation Interpretation
            │
            ▼
Meaning Translation
            │
            ▼
history_theme
            │
            ▼
Recommendation Match
            │
            ▼
Recommendation Reason
```

Recommendation が利用する情報

- need_tags
- consultation_axis
- history_theme
- Shrine Fact
- Shrine Meaning

---

# Runtime Snapshot

Recommendation 生成時には Runtime Snapshot を保存する。

保持対象例

- history_theme
- matched_need_tags
- recommendation_reason
- action_context
- action_suggestion
- score components

保存後は再計算しない。

現在の Favorite や Visit が変化しても、生成時点の Recommendation を維持する。

---

# Analytics

Meaning Translation は分析軸として利用する。

```text
Consultation
        │
        ▼
Recommendation
        │
        ▼
Detail
        │
        ▼
Route
        │
        ▼
Visit
        │
        ▼
Reflection
```

分析対象

- Recommendation CTR
- Detail View
- Route Open
- Visit Rate
- Reflection Rate
- 継続利用率
- history_theme 別CVR
- history_theme 別継続率

---

# 責務境界

Meaning Translation が担当すること

- consultation の意味整理
- history_theme の生成
- Action Theme の生成
- Reflection Prompt の生成
- Recommendation 補助
- Runtime Snapshot への情報提供
- Analytics 軸の提供

担当しないこと

- 推薦順位の決定
- Recommendation Score の計算
- UI表示
- 神社マスター更新
- 行動の強制
- 効果保証
- 心理診断
- 宗教的判断

---

# 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/product/concierge-first.md`
- `docs/product/concierge-modes.md`
- `docs/product/explore-integration-design.md`

---

# 更新ルール

本書は **Meaning Translation の対応関係** の正本とする。

更新対象は以下に限定する。

- 新しい `history_theme` の追加
- consultation → history_theme の対応変更
- ご利益 → history_theme の対応変更
- Action / Reflection への接続変更
- Recommendation / Runtime Snapshot / Analytics との接続変更

実装履歴、TODO、テスト手順、PRメモは本書へ記載しない。
