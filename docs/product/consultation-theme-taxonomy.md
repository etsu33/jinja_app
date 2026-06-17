

# Consultation Theme Taxonomy

## 目的

HomeHero / ConciergeEntry で使う相談テーマを正本化する。

このドキュメントでは、UI表示文言・内部キー・`consultation_axis`・`need_tags`・`history_theme` の対応を整理し、Concierge First の入力導線がぶれないようにする。

相談テーマは、神社検索カテゴリではなく「ユーザーが今どの状態から相談を始めるか」を選びやすくする入口として扱う。

---

## 結論

MVPでは、HomeHero / ConciergeEntry の相談テーマを以下の8テーマに固定する。

```markdown
- 仕事について考えたい
- 人との関係を整えたい
- お金の流れを整えたい
- 一歩踏み出したい
- 少し休みたい
- 体調を整えたい
- 学びを深めたい
- これからを考えたい
```

UIでは状態ベースの文言を出し、内部では `theme_key` として保持する。

`theme_key` は表示専用の中間キーであり、推薦の正本は既存の `need_tags` と `consultation_axis` を使う。

---

## 前提

既存実装・既存ドキュメントでは、相談に関わる概念が複数存在する。

```markdown
- HomeHero チップ
- ConciergeEntry チップ
- consultation_axis
- need_tags
- matched_need_tags
- history_theme
```

これらを同じ意味として扱わない。

### 各レイヤーの責務

| レイヤー | 役割 | 例 |
|---|---|---|
| UI表示文言 | ユーザーが選びやすい入口 | 仕事について考えたい |
| theme_key | UI用の内部キー | work |
| consultation_axis | 相談意図の軸 | career_change |
| need_tags | 推薦ロジックの正本 | career / courage / mental |
| history_theme | 神社側の意味文脈 | 勝負 / 再出発 / 学び |
| matched_need_tags | ユーザー意図と神社側情報の一致結果 | career / courage |

---

## 採用する相談テーマ一覧

| 表示文言 | theme_key | 定義 |
|---|---|---|
| 仕事について考えたい | work | 仕事、転職、働き方、独立、次のキャリア判断に関する相談 |
| 人との関係を整えたい | relationship | 恋愛、家族、職場、友人、縁、対人関係を整理したい相談 |
| お金の流れを整えたい | money | 収入、売上、金運、不安、経済活動、生活基盤に関する相談 |
| 一歩踏み出したい | challenge | 挑戦、決断、勇気、前進、再出発のきっかけがほしい相談 |
| 少し休みたい | rest | 疲労、休息、静けさ、回復、気持ちを落ち着けたい相談 |
| 体調を整えたい | health | 健康、心身の安定、生活リズム、体調不安に関する相談 |
| 学びを深めたい | study | 学業、資格、集中、継続、技術習得、積み上げに関する相談 |
| これからを考えたい | future | 将来、人生の方向性、選択肢、自分を見つめ直す相談 |

---

## 表示文言と内部キー

UI上は短いカテゴリ名ではなく、状態ベースの文言を使う。

### 採用しない表示

```markdown
- 仕事
- 人間関係
- お金
- 挑戦
- 休息
- 健康
- 学び
- 将来
```

これらは短く分かりやすいが、カテゴリ検索感が強い。

### 採用する表示

```markdown
- 仕事について考えたい
- 人との関係を整えたい
- お金の流れを整えたい
- 一歩踏み出したい
- 少し休みたい
- 体調を整えたい
- 学びを深めたい
- これからを考えたい
```

Kamimusubi は神社検索ではなく相談体験なので、状態や目的が伝わる文言に寄せる。

---

## consultation_axis対応

`consultation_axis` は、ユーザーがなぜその相談をしているかを表す相談意図レイヤーとして扱う。

既存実装では、`career`, `money`, `relationship`, `study`, `health`, `protection`, `travel_safe`, `other` が存在する。

ただし、`docs/analytics/consultation-axis-discovery.md` では、より細かい候補として以下が整理されている。

```markdown
- money_growth
- career_change
- relationship_repair
- restart_mindset
- nature_reset
- study_success
```

MVPでは、UIの `theme_key` から最も近い `consultation_axis` に寄せる。

| theme_key | primary consultation_axis | 補助候補 |
|---|---|---|
| work | career_change | career |
| relationship | relationship_repair | relationship |
| money | money_growth | money |
| challenge | restart_mindset | career_change / other |
| rest | nature_reset | other |
| health | health | other |
| study | study_success | study |
| future | restart_mindset | career_change / other |

### 注意

- `theme_key` は `consultation_axis` そのものではない
- `consultation_axis` は自然文・LLM・ルール抽出で最終判断する
- UIチップは初期ヒントとして扱う

---

## need_tags対応

`need_tags` は推薦ロジック上の正本として扱う。

UIテーマは `need_tags` を固定的に決めるものではなく、初期ヒントとして扱う。

| theme_key | primary need_tags | secondary need_tags |
|---|---|---|
| work | career | courage / mental |
| relationship | relationship | love / mental |
| money | money | career / courage |
| challenge | courage | career / mental |
| rest | rest | mental |
| health | health | protection / rest |
| study | study | focus / courage |
| future | mental | courage / career |

### 判断

- 自由入力がある場合は自由入力を優先する
- チップだけの場合は対応する `need_tags` を初期ヒントとして使う
- `matched_need_tags` は神社側との一致結果であり、UIテーマとは別物として扱う

---

## history_theme対応

`history_theme` は神社側の意味文脈であり、ユーザー側の相談テーマとは分離する。

ただし、UIテーマから推薦結果の説明文を組み立てる際の接続候補として使う。

| theme_key | 主な history_theme | 補助 history_theme | 説明方向 |
|---|---|---|---|
| work | 勝負 | 再出発 / 学び | 仕事・転機・判断・積み上げ |
| relationship | 縁 | 静寂 | 関係性の整理 |
| money | 守り | 勝負 / 再出発 | お金の不安と行動の整理 |
| challenge | 勝負 | 再出発 / 学び | 決断・挑戦・前進 |
| rest | 静寂 | 復興 | 回復・休息・静けさ |
| health | 守り | 復興 | 心身と生活基盤を守る |
| study | 学び | 勝負 | 集中・継続・積み上げ |
| future | 再出発 | 静寂 / 学び | 方向性の見直し |

### 注意

`history_theme` はユーザー状態を断定するために使わない。

神社側の文脈として、推薦理由や Meaning Card の説明に使う。

---

## 自由入力との関係

自由入力は、チップで表現しきれない相談内容を補足するために使う。

### 優先順位

```text
自由入力
↓
相談テーマチップ
↓
補助条件
```

### 判断ルール

- チップのみの場合は、theme_key を相談の初期ヒントとして扱う
- 自由入力がある場合は、自由入力の内容を優先する
- チップと自由入力が矛盾する場合は、自由入力を優先する
- 補助条件は推薦の補正に使うが、相談テーマを上書きしない

### 例

| チップ | 自由入力 | 優先する解釈 |
|---|---|---|
| 少し休みたい | 転職するか迷っている | career / mental |
| 仕事について考えたい | 疲れて何もしたくない | rest / mental |
| お金の流れを整えたい | 起業の売上を伸ばしたい | money / career / courage |

---

## HomeHeroでの扱い

HomeHero は相談開始の入口として扱う。

### 表示するもの

```markdown
- 相談テーマチップ
- 自由入力 textarea
- 条件追加導線
- この相談ではじめる CTA
```

### 表示しないもの

```markdown
- 誕生日入力
- ご利益選択
- 参拝スタイル詳細
- 吉方位
- 相性判定の説明
```

### HomeHeroの役割

- ユーザーが今のテーマを選ぶ
- 必要なら一言補足する
- `/concierge` へ遷移する

---

## ConciergeEntryでの扱い

ConciergeEntry は、HomeHero から渡された相談テーマを確認・補足する場所として扱う。

### HomeHeroから来た場合

```text
/concierge?theme=...
```

- 渡された theme を textarea に反映する
- 相談内容の確認画面として扱う
- チップは控えめに表示する

### 直接アクセスの場合

```text
/concierge
```

- 相談テーマチップを表示する
- 自由入力を表示する
- 検索UIではなく相談体験の入口として扱う

---

## 実装方針

### 共通定数化候補

将来的に、以下のような共通定数として切り出す。

```ts
export const CONSULTATION_THEMES = [
  {
    key: "work",
    label: "仕事について考えたい",
    primaryAxis: "career_change",
    needTags: ["career", "courage", "mental"],
    historyThemes: ["勝負", "再出発", "学び"],
  },
  {
    key: "relationship",
    label: "人との関係を整えたい",
    primaryAxis: "relationship_repair",
    needTags: ["relationship", "love", "mental"],
    historyThemes: ["縁", "静寂"],
  },
]
```

### 触る可能性が高いファイル

```text
apps/web/src/features/home/components/HomeHeroConsultationInput.tsx
apps/web/src/features/concierge/components/ConciergeEntryCard.tsx
apps/web/src/features/concierge/buildPayloadFromUnified.ts
apps/web/src/features/concierge/hooks.ts
backend/temples/domain/consultation_axis.py
backend/temples/domain/need_tags.py
```

---

## 次PR候補

### PR1: 相談テーマ定義の共通化

```markdown
- [ ] `CONSULTATION_THEMES` を定義
- [ ] HomeHero のチップを共通定数へ接続
- [ ] ConciergeEntry のチップを共通定数へ接続
- [ ] 表示文言と内部キーを分離
- [ ] typecheck
```

### PR2: consultation_axis連携整理

```markdown
- [ ] theme_key と consultation_axis の対応を実装に反映するか判断
- [ ] 既存 `consultation_axis` と詳細axis候補の整合を確認
- [ ] analytics payload に theme_key を持たせるか判断
```

### PR3: need_tags補助連携

```markdown
- [ ] theme_key から need_tags 初期ヒントを渡すか判断
- [ ] 自由入力がある場合の優先順位を確認
- [ ] payload上で theme_key と query を分離するか判断
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/consultation-theme-taxonomy作成
- [x] HomeHero / ConciergeEntryで使う相談テーマを確定
- [x] 表示文言と内部キーを分離
- [x] need tag / consultation axis との対応を整理
- [x] 自由入力との関係を定義
- [x] docsへ相談テーマ一覧を追記
```
