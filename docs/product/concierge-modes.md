

# Concierge Modes

## 目的

KAMI MUSUBIにおけるコンシェルジュ推薦の入口を定義する。

本ドキュメントは、ユーザーがどの入口から相談・推薦に入るのかを整理し、`history_theme`、神社推薦、理由生成へ接続するための正本である。

```text
ユーザー入力
↓
mode判定
↓
状態整理 / 相性補助
↓
history_theme
↓
神社推薦
↓
理由生成
↓
行動
```

---

## 基本方針

MVPでは、推薦モードを以下の2つに限定する。

```markdown
- Need Mode: 悩み・状態・願いごとから探す
- Compat Mode: 生年月日・相性から探す
```

将来モードは候補として保持するが、MVPでは実装主軸にしない。

---

## Mode一覧

| Mode | 内部名 | 主入力 | 主な役割 | history_themeとの関係 |
|---|---|---|---|---|
| Need Mode | `need` | query / ご利益 / 状態 | 今の悩みや願いから神社を提案する | 主軸として使う |
| Compat Mode | `compat` | birthdate | 生年月日から相性を補助する | 補助的に使う |
| Route Mode | `route` | location | 現在地や行きやすさから候補を出す | 将来候補 |
| Theme Mode | `theme` | history_theme | 人生テーマから神社を探す | 将来候補 |
| Shrine Search Mode | `search` | shrine name / area | 神社名・地域から探す | 補助導線 |

---

# 1. Need Mode

## 定義

ユーザーの今の悩み・状態・願いごとから神社を提案するモード。

KAMI MUSUBIの中心モードであり、MVPの主軸とする。

## 主入力

```markdown
- query
- goriyaku_tag_ids
- extra_condition
- area
- lat / lng
- birthdate（任意・補助）
```

## 入力例

```text
最近疲れている
転職で迷っている
金運を上げたい
人間関係を整えたい
静かに過ごしたい
```

## 処理の流れ

```text
query
↓
相談状態を抽出
↓
必要に応じてご利益を補助情報として扱う
↓
history_themeを決める
↓
神社候補を出す
↓
相談状態と神社文脈を接続して説明する
```

## history_themeとの接続

Need Modeでは、`history_theme` を推薦理由の中心に置く。

例:

```text
入力:
金運が気になる。将来のお金が不安。

↓

状態:
お金への不安

↓

history_theme:
守り

↓

推薦理由:
お金そのものを増やす約束ではなく、今は生活の土台や判断を整える文脈として受け取る。
```

## 出力方針

- 「今の状態に合う」を主語にする
- ご利益だけで推薦理由を完結させない
- 結果保証をしない
- 神社の歴史・由緒・場所性を補助材料として扱う

## 禁止表現

```markdown
- 金運が上がります
- 恋愛が成就します
- 必ず成功します
- この神社が正解です
```

---

# 2. Compat Mode

## 定義

生年月日から見た傾向や相性を補助情報として使い、神社を提案するモード。

ただし、KAMI MUSUBIでは生年月日を絶対的な判定軸にはしない。

## 主入力

```markdown
- birthdate
- area
- lat / lng
```

## 補助情報

```markdown
- 九星気学
- 五行
- 占星術的な要素
```

## 入力例

```text
生年月日から相性の良い神社を知りたい
今の自分に合う神社を見たい
相性ベースで探したい
```

## 処理の流れ

```text
birthdate
↓
九星 / 五行 / 星座などの傾向を取得
↓
神社側の要素と照合
↓
必要に応じてhistory_themeを補助する
↓
神社候補を出す
```

## history_themeとの接続

Compat Modeでは、`history_theme` は主軸ではなく補助的に扱う。

例:

```text
生年月日から見た傾向
↓
火の要素が強い
↓
行動・切り替えと相性が良い
↓
history_theme候補: 勝負 / 再出発
```

## 出力方針

- 生年月日から見た傾向として表現する
- 性格や運命を断定しない
- 状態相談がある場合はNeed Modeの情報を優先する
- 相性は補助材料として扱う

## 禁止表現

```markdown
- あなたはこういう人です
- この運命です
- この方角しかありません
- 生年月日上、これが正解です
```

---

# 3. Need Mode と Compat Mode の優先順位

## 原則

状態相談がある場合は Need Mode を優先する。

```text
相談状態 > ご利益 > 生年月日補助
```

## 判定例

| 入力 | 優先Mode | 理由 |
|---|---|---|
| 最近疲れている | need | 状態相談が明確 |
| 金運が気になる | need | 願いごとが明確 |
| 生年月日から相性を知りたい | compat | birthdate主軸 |
| 転職で迷っている。生年月日も入れたい | need | 状態相談が主軸、birthdateは補助 |
| 近くの神社を見たい | search / route | 相談ではなく探索導線 |

---

# 4. history_themeへの接続

推薦エンジンでは、最終的に以下の形へ変換する。

```text
mode
↓
入力解釈
↓
history_theme
↓
神社候補
```

## Need Mode

```text
query / ご利益 / 状態
↓
state-history-theme-mapping
↓
history_theme
```

## Compat Mode

```text
birthdate
↓
五行 / 九星 / 要素
↓
history_theme補助
```

---

# 5. 推薦エンジン全体図

```text
User Input
├─ query
├─ goriyaku
├─ birthdate
├─ location
└─ extra condition

↓

Mode Resolver
├─ need
└─ compat

↓

Meaning Layer
├─ state-history-theme-mapping.md
├─ goriyaku-history-theme-mapping.md
└─ history-theme-taxonomy.md

↓

Shrine Matching
├─ history_theme
├─ goriyaku_tags
├─ astro_elements
├─ distance
└─ popular_score

↓

Explanation Layer
├─ consultationSummary
├─ shrineMeaning
├─ actionMeaning
└─ historyContext

↓

User Action
├─ shrine_detail_transition
├─ route_open
├─ save_prompt
└─ premium_preview
```

---

# 6. 将来Mode候補

## Route Mode

### 目的

現在地や移動しやすさから神社を提案する。

### 注意

Route Modeは主価値にしない。

```text
現在地
↓
近い神社
```

だけでは、KAMI MUSUBIの価値である状態整理が弱くなる。

将来的には、以下のように補助として扱う。

```text
history_theme
↓
今日行きやすい神社
```

---

## Theme Mode

### 目的

ユーザーが人生テーマから直接探せる導線。

例:

```markdown
- 再出発の神社
- 勝負の神社
- 静寂の神社
```

### 注意

MVPではまだ主導線にしない。

先にNeed Modeから自然にhistory_themeが出る状態を作る。

---

## Shrine Search Mode

### 目的

神社名や地域名で探す通常検索。

### 位置づけ

検索は補助導線であり、コンシェルジュ体験の主導線ではない。

---

# 7. 運用ルール

## やること

```markdown
- modeは内部名として `need` / `compat` を使う
- UI文言は「悩みベース」「相性ベース」とする
- 状態相談がある場合はNeed Modeを優先する
- birthdateは任意入力として扱う
- history_themeは説明・分析・履歴保存の軸として使う
```

## やらないこと

```markdown
- mode名に feel / filter を使わない
- 生年月日だけでユーザーの状態を断定しない
- ご利益だけで推薦理由を完結させない
- 近いだけで推薦理由を完結させない
- 吉方位を主役にしない
```

---

# 8. 関連ドキュメント

```markdown
- docs/product/history-theme-taxonomy.md
- docs/product/state-history-theme-mapping.md
- docs/product/goriyaku-history-theme-mapping.md
- docs/core/narrative-guideline.md
```

---

# 9. TODO

```markdown
- [x] concierge-modes.md 作成
- [x] Need Mode定義
- [x] Compat Mode定義
- [x] 将来Mode候補整理
- [x] history_themeとの接続を記載
- [x] 推薦エンジン全体図を記載
```
