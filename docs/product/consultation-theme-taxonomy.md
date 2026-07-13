# Consultation Theme Taxonomy

## 目的

Home Hero と Concierge Entry で使用する相談テーマの分類を定義する。

本書は、相談テーマの表示文言・内部キー・各レイヤーとの対応関係を管理する正本とする。

---

## 基本方針

相談テーマは、神社検索カテゴリではなく、「ユーザーが今どの状態から相談を始めるか」を選びやすくする入口として扱う。

- UIには状態ベースの文言を表示する
- 内部では `theme_key` を保持する
- 推薦の正本は `need_tags` と `consultation_axis` とする
- `history_theme` は神社側の意味文脈として扱う

---

## 採用する相談テーマ

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

## レイヤー構成

| レイヤー | 役割 | 例 |
|---|---|---|
| UI表示文言 | ユーザーが選択する相談テーマ | 仕事について考えたい |
| theme_key | UI用内部キー | work |
| consultation_axis | 相談意図 | career_change |
| need_tags | 推薦ロジックの正本 | career / courage / mental |
| history_theme | 神社側の意味文脈 | 勝負 / 再出発 |
| matched_need_tags | ユーザー意図と神社情報の一致結果 | career / courage |

---

## consultation_axis対応

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

### 方針

- `theme_key` は `consultation_axis` ではない
- `consultation_axis` は相談内容から最終決定する
- UIテーマは初期入力のヒントとして扱う

---

## need_tags対応

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

### 方針

- 自由入力を優先する
- チップは初期ヒントとして利用する
- `matched_need_tags` は神社側との一致結果として扱う

---

## history_theme対応

| theme_key | 主な history_theme | 補助 history_theme | 説明方向 |
|---|---|---|---|
| work | 勝負 | 再出発 / 学び | 仕事・転機・判断 |
| relationship | 縁 | 静寂 | 関係性の整理 |
| money | 守り | 勝負 / 再出発 | お金と生活基盤 |
| challenge | 勝負 | 再出発 / 学び | 決断・挑戦 |
| rest | 静寂 | 復興 | 回復・休息 |
| health | 守り | 復興 | 心身の安定 |
| study | 学び | 勝負 | 学習・継続 |
| future | 再出発 | 静寂 / 学び | 将来・方向性 |

### 方針

`history_theme` はユーザー状態を断定するためではなく、推薦理由や Meaning Layer の文脈として利用する。

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

- 自由入力がある場合は自由入力を優先する
- チップのみの場合は `theme_key` を初期ヒントとして利用する
- チップと自由入力が矛盾する場合は自由入力を優先する
- 補助条件は相談テーマを上書きしない

---

## Home Heroでの利用

### 表示するもの

- 相談テーマチップ
- 自由入力
- 条件追加導線
- コンシェルジュ開始CTA

### 表示しないもの

- 誕生日
- ご利益
- 参拝スタイル
- 吉方位
- 相性説明

Home Hero は相談開始の入口を担当する。

---

## Concierge Entryでの利用

Home Hero から相談内容が渡された場合は、その内容を確認・補足する画面として扱う。

直接アクセス時は相談開始画面として扱う。

---

## 共通定数

将来的には相談テーマを共通定数として管理する。

保持する情報は以下とする。

- theme_key
- 表示文言
- consultation_axis
- need_tags
- history_theme

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`

---

## 更新ルール

- 本書は相談テーマの分類と対応関係のみを管理する。
- 推薦ロジック・UI実装・API仕様は他の正本ドキュメントで管理する。
- 相談テーマ・theme_key・各レイヤーとの対応が変更された場合のみ更新する。
