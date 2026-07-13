> **Status: Reference**
>
> 本ドキュメントは Concierge Entry の画面構成とUI責務を補足する Reference 文書である。
>
> 体験全体の責務は `docs/product/concierge-first-final-spec.md`、
> 相談テーマの分類は `docs/product/consultation-theme-taxonomy.md` を正本とする。

# Concierge Entry Final Wireframe

## 目的

`ConciergeEntry` の画面構成とUI責務を定義する。

`ConciergeEntry` は、Home Heroから始まった相談を受け取り、推薦生成前に相談内容を確認・補足する画面として扱う。

検索フォームではなく、相談内容を整え、必要な補助条件を追加して推薦へ進む入口とする。

---

## Concierge Entryの役割

- Home Heroから渡された相談内容を受け取る
- 相談内容を確認・修正できるようにする
- 直接アクセスしたユーザーへ相談開始口を提供する
- 補助条件入力へ誘導する
- 推薦生成CTAへ接続する

`ConciergeEntry` は推薦結果を表示しない。

推薦結果の表示は `ConciergeSectionsRenderer` が担当する。

---

## Home Heroから遷移した場合

### URL

```text
/concierge?theme=...
/concierge?theme=...&openFilter=1
```

### 表示方針

theme が渡された場合は、新しく相談を書かせる画面ではなく、相談内容を確認・補足する画面として表示する。

### 表示構造

```text
相談内容を確認する

[Home Heroから渡された相談内容]

必要な場合のみ内容を補足する

[＋ 条件を追加する]
[この内容で神社を提案してもらう]
```

### ルール

- Home Heroから渡された相談内容を初期表示する
- theme がある場合は入力欄を空にしない
- openFilter=1 の場合は補助条件エリアを開く
- 相談テーマチップは補助的に表示する

---

## 直接アクセスした場合

### URL

```text
/concierge
/concierge?openFilter=1
```

### 表示方針

直接アクセスの場合は、ConciergeEntry を相談開始画面として表示する。

### 表示構造

```text
今の相談テーマを選ぶ

[相談テーマチップ]

必要なら一言補足する
[textarea]

[＋ 条件を追加する]
[この内容で神社を提案してもらう]
```

相談テーマの表示文言・内部キー・対応関係は、`docs/product/consultation-theme-taxonomy.md` を正本とする。

---

## 画面構成

### 表示する要素

- 相談内容
- 相談テーマチップ
- 自由入力
- 条件追加導線
- 推薦生成CTA
- クリア操作
- 未ログイン時の保存案内

### 控えめに表示する要素

- 呼び名入力
- 自由入力
- 未ログイン案内

### 表示しない要素

- 推薦結果
- 推薦順位
- 条件入力本体
- 長い説明文
- Meaning Layerの内部情報

---

## 相談テーマ

相談テーマは、カテゴリ検索ではなく、相談を始めやすくする入力補助として扱う。

### ルール

- 相談テーマの選択を強制しない
- 自由入力による補足・修正を許可する
- 表示文言と内部キーをUI内で独自管理しない
- 正式な分類は `docs/product/consultation-theme-taxonomy.md` を参照する

---

## 自由入力

自由入力は、相談テーマだけでは表現しきれない内容を補足するために使用する。

### 役割

- Home Heroから渡された相談内容を修正する
- 相談テーマを自分の言葉で補足する
- 相談解釈の入力としてBackendへ渡す

### 表示方針

- 必須入力であるように見せすぎない
- 長文入力を前提にしない
- 相談テーマより強く見せない
- ユーザーの原文を維持する

### Placeholder

```text
例: 気持ちを切り替えたい、これからのことを考えたい
```

---

## 条件追加導線

### 表示文言

```text
＋ 条件を追加する
```

補助条件入力は `ConciergeFilterPanel` が担当する。

`ConciergeEntry` 内に条件入力本体を重複して配置しない。

---

## CTA

### メインCTA

```text
この内容で神社を提案してもらう
```

### クリア

```text
クリア
```

### 未ログイン案内

```text
未ログインでも相談できます。保存にはログインが必要です。
```

---

## Concierge Filterとの責務境界

| Concierge Entry | Concierge Filter |
|---|---|
| 相談テーマ | 誕生日 |
| 相談内容の確認・修正 | ご利益 |
| 自由入力 | 参拝スタイル |
| 推薦生成CTA | 相性に関する補助情報 |
| 条件追加導線 | その他の補助条件 |

`ConciergeEntry` は相談の主入力を扱い、`ConciergeFilterPanel` は推薦を補完する条件を扱う。

---

## 推薦結果との責務境界

| Concierge Entry | ConciergeSectionsRenderer |
|---|---|
| 相談入力 | 推薦結果 |
| 入力確認 | 推薦理由 |
| 条件追加への導線 | Action Suggestion |
| 推薦生成CTA | 神社候補の表示 |

`ConciergeEntry` は推薦生成前までを担当する。

---

## 画面フロー

```text
Home Hero
↓
theme / openFilter
↓
Concierge Entry
↓
相談内容の確認・補足
↓
必要に応じてConcierge Filter
↓
推薦生成
↓
ConciergeSectionsRenderer
```

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/concierge-filter-area.md`

---

## 更新ルール

- 本書は Concierge Entry の画面構成とUI責務のみを管理する。
- 相談テーマの分類・表示文言・内部キーは本書で重複管理しない。
- 推薦ロジック・Meaning Layer・API契約は各正本ドキュメントで管理する。
- Concierge Entryの画面構成またはUI責務が変更された場合のみ更新する。
- TODO・PR計画・実装進捗・作業履歴は本書へ記載しない。
