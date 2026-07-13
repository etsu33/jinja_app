> **Status: Reference**
>
> 本ドキュメントは Need Mode のUI導線と表示責務を補足する Reference 文書である。
>
> Mode全体の責務は `docs/product/concierge-modes.md`、
> 相談テーマの分類は `docs/product/consultation-theme-taxonomy.md`、
> Meaning変換は `docs/product/meaning-translation-mapping.md` を正本とする。

# Need Mode UI Flow

## 目的

Concierge FirstにおけるNeed ModeのUI導線と表示責務を定義する。

Need Modeは、ユーザーの相談テーマや自由入力を起点に、相談内容を整理し、`need_tags`を中心とした推薦へ接続する主導線として扱う。

---

## 基本方針

```text
相談テーマ
↓
自由入力
↓
need_tags
↓
matched_need_tags
↓
推薦理由
↓
Meaning Card
```

- Need ModeをConcierge Firstの主導線とする
- 自由入力を相談解釈の正本入力として扱う
- 相談テーマは入力補助として扱う
- `need_tags`を推薦入力の中心に置く
- Compat Modeは補助情報として扱い、Need Modeを上書きしない
- 神社検索や条件検索として見せない

---

## Need Modeの責務

### 担当するもの

- 相談テーマ
- 自由入力
- `need_tags`
- `consultation_axis`
- `matched_need_tags`
- 推薦理由の主文脈
- Meaning Cardの中心文脈

### 担当しないもの

- 誕生日による相性補助
- 占術補助
- 吉方位
- 方角計算
- 経路最適化
- 神社名・地域名による通常検索

---

## 相談テーマ

相談テーマは、ユーザーが相談を始めやすくする入力補助として扱う。

### 役割

- 相談開始の負担を下げる
- 自分の状態に近い入口を選びやすくする
- `need_tags`抽出の初期ヒントになる
- `consultation_axis`推定の初期ヒントになる

相談テーマの表示文言、内部キー、各レイヤーとの対応関係は、`docs/product/consultation-theme-taxonomy.md` を正本とする。

本書では相談テーマ一覧を重複管理しない。

---

## 自由入力

自由入力はNeed Modeの正本入力として扱う。

### 役割

- 相談テーマだけでは表現できない内容を受け取る
- `need_tags`抽出の主材料になる
- `consultation_axis`推定の主材料になる
- 推薦理由の主文脈になる

### 優先順位

```text
自由入力
↓
相談テーマ
↓
補助条件
```

### ルール

- 自由入力がある場合は、その内容を優先する
- 相談テーマと自由入力が矛盾する場合は、自由入力を優先する
- 補助条件は相談内容を上書きしない
- ユーザーの原文を保持する
- UI側で心理状態を断定しない

---

## need_tagsとの接続

`need_tags`はNeed Modeの中心データとして扱う。

### 責務

- 相談意図を推薦可能な単位へ整理する
- 神社側の情報と接続する
- `matched_need_tags`の母体になる
- Recommendationの主要入力になる

### UIからの接続

```text
Home Hero / Concierge Entry
↓
相談テーマ / 自由入力
↓
query
↓
need_tags抽出
↓
Recommendation
```

`need_tags`は内部情報として扱い、UIへそのまま表示しない。

表示時は、ユーザー向けの意味表現へ変換する。

---

## matched_need_tagsとの関係

`matched_need_tags`は、ユーザー側の相談意図と神社側の情報が一致した結果を表す。

### ルール

- `need_tags`と同一視しない
- 相談テーマと同一視しない
- 推薦理由の根拠として利用する
- UIでは技術的なタグ名を直接表示しない

---

## Compat Modeとの責務境界

Need Modeは相談内容を中心に扱い、Compat Modeは誕生日・相性・占術・方位などの補助情報を扱う。

| Need Mode | Compat Mode |
|---|---|
| 相談テーマ | 誕生日 |
| 自由入力 | element4 |
| `need_tags` | 相性候補 |
| `consultation_axis` | 占術補助 |
| `matched_need_tags` | 方位補助 |
| 推薦理由の中心 | 推薦理由の補足 |

### 境界ルール

- Need Modeを主導線とする
- Compat Modeは補助条件として扱う
- Compat Modeは推薦理由の主語にしない
- 占術や相性だけで推薦を決定しない
- 吉方位は補助情報として扱う
- Compat ModeはNeed Modeの相談解釈を上書きしない

---

## Home Heroでの表示

Home HeroではNeed Modeの入口を前面に出す。

### 表示するもの

- 相談テーマ
- 自由入力
- コンシェルジュ開始CTA
- 条件追加導線

### 表示しないもの

- 誕生日入力
- 相性説明
- 吉方位説明
- ご利益選択本体
- 参拝スタイル詳細

Home Heroの画面責務は `docs/product/home-hero-final-wireframe.md` を参照する。

---

## Concierge Entryでの表示

Concierge Entryでは、相談内容の確認と補足を行う。

### 役割

- Home Heroから渡された相談内容を表示する
- 自由入力を確認・修正できるようにする
- 相談テーマを補助的に表示する
- 補助条件入力へ接続する
- 推薦生成へ進める

Concierge Entryの画面責務は `docs/product/concierge-entry-final-wireframe.md` を参照する。

---

## Concierge Filterとの接続

補助条件はConcierge Filterが担当する。

```text
Need Mode
↓
相談テーマ / 自由入力
↓
必要に応じてConcierge Filter
↓
推薦生成
```

Concierge Filterは、誕生日・ご利益・参拝スタイル・自由補足を扱う。

補助条件の画面責務は `docs/product/concierge-filter-area.md` を参照する。

---

## 推薦結果での表示

推薦結果では、Need Mode由来の文脈を中心に表示する。

```text
相談内容
↓
今必要な意味
↓
神社と重なる理由
↓
次に取りやすい行動
```

Compat Mode由来の情報は補足として扱う。

### 表示原則

- 相談内容を推薦理由の中心にする
- `matched_need_tags`を説明根拠として利用する
- `history_theme`は神社側の意味文脈として扱う
- 相性・占術・方位は補足表示に留める
- 行動や結果を断定しない

---

## UI文言

### 使用しない表現

- あなたはこのタイプです
- この神社が正解です
- この神社へ行くべきです
- 吉方位なので必ず良い結果になります
- 金運が上がります

### 使用する表現

- 相談内容から、今の状態と重なる文脈を整理します
- この神社の背景には、相談内容と重なる要素があります
- 誕生日情報は、相性を見る補助として利用します
- 方位情報は、参考情報として扱います

---

## Recommendationとの接続

Need ModeはRecommendationの主要入力を提供する。

### 主入力

- `query`
- `need_tags`
- `consultation_axis`
- `matched_need_tags`

### 補助入力

- `selected_goriyaku_tag_ids`
- `extra_condition`
- `visit_style_tags`
- `birthdate`
- `element4`

### ルール

- `need_tags`と`matched_need_tags`を主軸にする
- 補助入力は主入力を上書きしない
- 推薦順位の判定はBackendを正本とする
- Frontendは推薦ロジックを重複実装しない

---

## 責務境界

### Frontend

- 相談テーマを表示する
- 自由入力を受け取る
- 補助条件への導線を提供する
- 推薦結果を表示する

### Backend

- 相談内容を解釈する
- `need_tags`を生成する
- `consultation_axis`を決定する
- `matched_need_tags`を算出する
- 推薦順位と推薦理由を生成する

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/home-hero-final-wireframe.md`
- `docs/product/concierge-entry-final-wireframe.md`
- `docs/product/concierge-filter-area.md`

---

## 更新ルール

- 本書はNeed ModeのUI導線と表示責務のみを管理する。
- 相談テーマ一覧は本書で重複管理しない。
- `need_tags`や`consultation_axis`の生成ロジックはBackend側の正本で管理する。
- 推薦ロジック、API契約、Meaning変換の詳細は各正本ドキュメントで管理する。
- Need ModeのUI導線または責務が変更された場合のみ更新する。
- TODO、PR計画、実装進捗、作業履歴は本書へ記載しない。
