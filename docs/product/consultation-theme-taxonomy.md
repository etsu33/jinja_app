> **Status: Active**
>
> 本ドキュメントは、Home HeroとConcierge Entryで使用する相談テーマの分類・表示文言・内部キー・各レイヤーとの対応関係を管理する正本である。

# Consultation Theme Taxonomy

## 目的

Home HeroとConcierge Entryで使用する相談テーマの分類を定義する。

相談テーマは、神社検索のカテゴリではなく、ユーザーが現在の状態や目的に近い相談の入口を選ぶために使用する。

---

## 基本原則

- UIには状態や目的が伝わる文言を表示する
- 内部では`theme_key`を保持する
- 相談テーマは相談解釈の初期ヒントとして扱う
- 自由入力がある場合は自由入力を優先する
- 推薦入力の正本は`need_tags`と`consultation_axis`とする
- `history_theme`は神社側の意味文脈として扱う
- 相談テーマだけでユーザーの状態を断定しない

---

## 相談テーマ

| 表示文言 | theme_key | 定義 |
|---|---|---|
| 仕事について考えたい | `work` | 仕事、転職、働き方、独立、キャリア判断に関する相談 |
| 人との関係を整えたい | `relationship` | 恋愛、家族、職場、友人、縁、対人関係に関する相談 |
| お金の流れを整えたい | `money` | 収入、売上、金運、経済的不安、生活基盤に関する相談 |
| 一歩踏み出したい | `challenge` | 挑戦、決断、勇気、前進、再出発に関する相談 |
| 少し休みたい | `rest` | 疲労、休息、静けさ、回復、気持ちの整理に関する相談 |
| 体調を整えたい | `health` | 健康、心身の安定、生活リズム、体調不安に関する相談 |
| 学びを深めたい | `study` | 学業、資格、集中、継続、技術習得に関する相談 |
| これからを考えたい | `future` | 将来、人生の方向性、選択肢、自己理解に関する相談 |

---

## レイヤー構成

| レイヤー | 役割 | 例 |
|---|---|---|
| UI表示文言 | ユーザーが選択する相談の入口 | 仕事について考えたい |
| `theme_key` | UI用の内部キー | `work` |
| `consultation_axis` | 相談意図を整理する軸 | `career_change` |
| `need_tags` | 推薦入力の主軸 | `career` / `courage` / `mental` |
| `matched_need_tags` | ユーザー意図と神社情報の一致結果 | `career` / `courage` |
| `history_theme` | 神社側の意味文脈 | 勝負 / 再出発 |

各レイヤーは同一の概念として扱わない。

---

## consultation_axisとの対応

| theme_key | primary consultation_axis | 補助候補 |
|---|---|---|
| `work` | `career_change` | `career` |
| `relationship` | `relationship_repair` | `relationship` |
| `money` | `money_growth` | `money` |
| `challenge` | `restart_mindset` | `career_change` / `other` |
| `rest` | `nature_reset` | `other` |
| `health` | `health` | `other` |
| `study` | `study_success` | `study` |
| `future` | `restart_mindset` | `career_change` / `other` |

### ルール

- `theme_key`を`consultation_axis`として直接確定しない
- `consultation_axis`は相談内容から決定する
- 相談テーマは`consultation_axis`推定の初期ヒントとして利用する
- 自由入力と相談テーマが矛盾する場合は、自由入力由来の解釈を優先する

---

## need_tagsとの対応

| theme_key | primary need_tags | secondary need_tags |
|---|---|---|
| `work` | `career` | `courage` / `mental` |
| `relationship` | `relationship` | `love` / `mental` |
| `money` | `money` | `career` / `courage` |
| `challenge` | `courage` | `career` / `mental` |
| `rest` | `rest` | `mental` |
| `health` | `health` | `protection` / `rest` |
| `study` | `study` | `focus` / `courage` |
| `future` | `mental` | `courage` / `career` |

### ルール

- `theme_key`だけで`need_tags`を確定しない
- 自由入力を`need_tags`抽出の主材料とする
- 相談テーマは`need_tags`抽出の初期ヒントとして利用する
- `matched_need_tags`は神社側情報との一致結果として扱う
- UIへ内部タグ名をそのまま表示しない

---

## history_themeとの対応

| theme_key | 主なhistory_theme | 補助history_theme | 説明方向 |
|---|---|---|---|
| `work` | 勝負 | 再出発 / 学び | 仕事・転機・判断 |
| `relationship` | 縁 | 静寂 | 関係性の整理 |
| `money` | 守り | 勝負 / 再出発 | お金と生活基盤 |
| `challenge` | 勝負 | 再出発 / 学び | 決断・挑戦 |
| `rest` | 静寂 | 復興 | 回復・休息 |
| `health` | 守り | 復興 | 心身の安定 |
| `study` | 学び | 勝負 | 学習・継続 |
| `future` | 再出発 | 静寂 / 学び | 将来・方向性 |

### ルール

- `theme_key`から`history_theme`を直接確定しない
- `history_theme`は神社側の意味文脈として扱う
- 推薦理由やMeaning Layerの説明に利用する
- ユーザーの状態や将来を断定するために利用しない

---

## 自由入力との関係

### 優先順位

```text
自由入力
↓
相談テーマ
↓
補助条件
```

### 判断ルール

- 自由入力がある場合は、その内容を優先する
- 相談テーマのみの場合は、`theme_key`を初期ヒントとして利用する
- 相談テーマと自由入力が矛盾する場合は、自由入力を優先する
- 補助条件は相談内容を上書きしない
- ユーザーの原文を保持する

---

## Home Heroでの利用

Home Heroは相談開始の入口を担当する。

### 表示するもの

- 相談テーマチップ
- 自由入力
- 条件追加導線
- コンシェルジュ開始CTA

### 表示しないもの

- 誕生日入力
- ご利益選択
- 参拝スタイル入力
- 吉方位
- 相性説明

Home Heroの画面構成とUI責務は、`docs/product/home-hero-final-wireframe.md`を参照する。

---

## Concierge Entryでの利用

Concierge Entryは、相談内容の確認・補足を担当する。

### Home Heroから遷移した場合

- 渡された相談内容を初期表示する
- 相談内容を確認・修正できるようにする
- 相談テーマは補助的に表示する

### 直接アクセスした場合

- 相談テーマを選択できるようにする
- 自由入力を受け付ける
- 補助条件入力へ接続する

Concierge Entryの画面構成とUI責務は、`docs/product/concierge-entry-final-wireframe.md`を参照する。

---

## 管理項目

相談テーマは、以下の項目を一体として管理する。

- `theme_key`
- 表示文言
- 定義
- `consultation_axis`
- `need_tags`
- `history_theme`

Home HeroやConcierge Entryで、相談テーマ一覧や内部キー対応を独自に重複管理しない。

---

## 責務境界

### Consultation Theme Taxonomy

- 相談テーマの分類
- UI表示文言
- `theme_key`
- 各レイヤーとの対応関係
- 自由入力との優先順位

### Frontend

- 相談テーマを表示する
- 選択状態を保持する
- 自由入力を受け付ける
- 相談内容をBackendへ渡す

### Backend

- 相談内容を解釈する
- `consultation_axis`を決定する
- `need_tags`を生成する
- 推薦入力へ反映する

Frontendは相談解釈や推薦判定の業務ロジックを重複実装しない。

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/home-hero-final-wireframe.md`
- `docs/product/concierge-entry-final-wireframe.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`

---

## 更新ルール

- 本書は相談テーマの分類・表示文言・内部キー・各レイヤーとの対応関係を管理する。
- Home HeroやConcierge Entryで相談テーマ一覧を重複管理しない。
- 推薦ロジック、UI実装、API仕様は各責務の正本で管理する。
- 相談テーマ、`theme_key`、または各レイヤーとの対応関係が変更された場合のみ更新する。
- TODO、PR計画、実装進捗、作業履歴は本書へ記載しない。
