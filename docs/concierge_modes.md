# Concierge Modes

最終更新: 2026-03-19

## 目的

コンシェルジュの推薦を、以下の2モードに分離して説明可能にする。

- 悩みベース: 今の悩み・気分・願いごとから神社を探す
- 相性ベース: 生年月日から見た「今の巡り」や受け取りやすさから神社を探す

本ドキュメントは、入力 / 判定軸 / 出力 / 詳細ページの説明責任を整理するためのもの。

---

## 1. モード一覧

| モード | 内部名 | ユーザー向け説明 | 主入力 |
|---|---|---|---|
| 悩みベース | `need` | 今の気持ちや願いごとから探す | `query` |
| 相性ベース | `compat` | 生年月日との相性や巡りから探す | `birthdate` |

---

## 2. 悩みベース (`need`)

### 目的
ユーザーの現在の状態や悩みに合う神社を返す。

### 主入力
- `query`
- `goriyaku_tag_ids`（任意）
- `extra_condition`（任意）
- `area` / `lat` / `lng`（任意）
- `birthdate`（任意・補助）

### 主判定軸
- `need_tags`
- `matched_need_tags`
- `astro_tags`
- `goriyaku_tag_ids`
- 距離
- 人気度

### 補助判定
- `birthdate` があれば補助的に相性情報を参照する場合はある
- ただし主軸は `query`

### 出力の原則
- 「今の状態に合う」ことを結論にする
- 理由文は `need_tags` と神社の特徴を接続する
- 足りない情報を先に言い訳しない

### 詳細ページの理由文
例:
- 不安を整えながら次の一歩を踏み出したい今の状態に合っています
- 落ち着きたい気持ちと、この神社の厄除け・浄化の特徴が重なっています

---

## 3. 相性ベース (`compat`)

### 目的
ユーザーの生年月日から見た「今の巡り」や受け取りやすい傾向と、
神社の持つ文脈・雰囲気との相性を返す。

### 主入力
- `birthdate`
- `area` / `lat` / `lng`（任意）

### 主判定軸
- `fortune_profile(birthdate)`
- `gogyou`
- `history_theme`
- 神社の空気感
- 距離
- 人気度

### 補助判定
- `astro_elements` は補助一致として扱う
- 西洋占星術は ranking の微調整に限定する
- `query` は任意
- `goriyaku_tag_ids` / `extra_condition` は基本的に主軸ではない

### 東洋 / 西洋の役割分離

| レイヤー | 役割 | 主従 |
|---|---|---|
| 五行 | 今の巡り・受け取りやすさ | 主 |
| history_theme | 神社文脈 | 主 |
| 西洋占星術 | 軽い相性補助 | 従 |

### 出力の原則
- 「今の自分が受け取りやすい神社」であることを結論にする
- 五行や神社文脈を優先して説明する
- 西洋占星術は補助理由としてのみ使う
- query がなくても成立する

### 詳細ページの理由文
例:
- 今は「水」の傾向が強く、静かに整え直せる神社との相性が出ています
- 切り替えや再出発に関わる歴史文脈が、今の巡りと重なっています
- 落ち着いて受け取りやすい空気感を持つ神社として上位に入っています

---

## 4. モード判定ルール

### 原則
- request payload に `mode` を明示で持たせる
- frontend / backend で同じモード名を使う
- `feel / filter` は UI表現であり、内部ロジック名には使わない

### 判定

#### `mode == "need"`
- query ベース推薦を実行する

#### `mode == "compat"`
- birthdate ベース推薦を実行する
- query が空でも成立させる

### フォールバック
- `mode` 未指定で `birthdate` のみある場合:
  - `compat` 扱い
- `mode` 未指定で `query` がある場合:
  - `need` 扱い

---

## 5. frontend の扱い

### 現状
- `entryMode = "feel" | "filter"`
- `birthdateToElement4()` が frontend 側に存在
- request payload では `need / compat` に寄せ始めている

### 方針
- UI文言:
  - 「今の気持ちから探す」
  - 「生年月日との相性や巡りから探す」
- 内部名:
  - `need`
  - `compat`

### 注意
`birthdateToElement4()` は UI補助用に限定し、推薦根拠の正本にしない。  
正本は backend 側の `fortune_profile()` と ranking ロジックとする。

---

## 6. backend の扱い

### 悩みベース
- `need_tags`
- `matched_need_tags`
- `astro_tags`
- 距離 / 人気

### 相性ベース
- `fortune_profile(birthdate)`
- `gogyou`
- `history_theme`
- `astro_elements`（補助）
- 距離 / 人気

### 必須修正
- `birthdate` 単独で `compat` モードに入れる
- `flow` と `mode` の意味を docs 上でも一致させる
- explanation は東洋主軸に寄せる
- ranking の西洋依存は段階的に縮小する

---

## 7. 詳細ページの扱い

### 原則
詳細ページの「なぜこの神社か」は、推薦モードに依存して出し分ける。

### 悩みベース
- `need_tags` と神社特徴の接続

### 相性ベース
- 五行
- history_theme
- 神社の空気感
- 必要に応じて西洋相性補助

### 禁止
- モードが違うのに同じ抽象文を出すこと
- 情報不足の言い訳を冒頭に置くこと
- 西洋 explanation を主語に戻すこと

---

## 8. テストユーザー募集の再開条件

以下が揃うまで再開しない。

- `need / compat` の仕様が固定されている
- `birthdate` 単独で `compat` が成立する
- 詳細ページで mode 別の理由文が出る
- 運営側が「なぜこの神社か」を説明できる
- 東洋主軸 / 西洋補助の責務分離が崩れていない

---

## 9. 直近の実装順

1. backend で `birthdate` 単独 compat 分岐を確定
2. `fortune_profile()` を explanation payload に接続
3. `history_theme` を Shrine に追加
4. frontend entry 導線を `悩み / 相性` にリネーム
5. frontend の `birthdateToElement4()` を UI補助へ縮小
6. 詳細ページの理由文を mode 別に出し分け
7. ranking の西洋依存を段階的に縮小
8. テストユーザー募集を再開
