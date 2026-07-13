> **Status: Reference**
>
> 本ドキュメントは Home Hero の画面構成を補足する Reference 文書である。
>
> 体験全体の責務は `docs/product/concierge-first-final-spec.md`、
> 相談テーマの分類は `docs/product/consultation-theme-taxonomy.md` を正本とする。

# Home Hero Final Wireframe

## 目的

Home Hero の画面構成とUI責務を定義する。

Home Hero は「神社を探す画面」ではなく、「相談を始める入口」として扱い、相談内容を Concierge へ渡す役割を担う。

---

## Home Heroの役割

- 相談を始める
- 相談テーマを選ぶ
- 自由入力を受け付ける
- Conciergeへ遷移する

Home Hero では推薦を行わない。

---

## 画面構成

### 表示する要素

- Heroタイトル
- Heroサブコピー
- 相談テーマチップ
- 自由入力
- 条件追加導線
- コンシェルジュ開始CTA

### 表示しない要素

- 誕生日入力
- ご利益選択
- 参拝スタイル入力
- 詳細条件入力
- 神社検索UI

補助条件は Concierge Filter が担当する。

---

## 相談テーマ

相談テーマは入力補助として表示する。

自由入力を制限せず、ユーザーが自分の言葉で相談内容を書けることを優先する。

相談テーマの分類・表示文言・内部キーは、`docs/product/consultation-theme-taxonomy.md` を正本とする。

---

## 条件追加導線

### 表示文言

```text
＋ 条件を追加する
```

### 補足文

```text
誕生日・ご利益・参拝スタイルなどの条件を追加できます
```

補助条件は相談テーマより目立たせない。

---

## Home HeroとConciergeの責務

| Home Hero | Concierge |
|------------|------------|
| 相談開始 | 相談内容の解釈 |
| 相談テーマ入力 | 条件入力 |
| 自由入力 | 推薦生成 |
| Conciergeへの遷移 | 推薦理由の表示 |

Home Hero は入口、Concierge は推薦体験を担当する。

---

## 役割境界

- Home Hero は推薦ロジックを持たない。
- Home Hero は意味変換を行わない。
- Home Hero は相談内容を Concierge へ渡すことだけを担当する。
- 補助条件は Concierge Filter が担当する。

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/concierge-filter-area.md`

---

## 更新ルール

- 本書は Home Hero の画面構成とUI責務のみを管理する。
- 推薦ロジック・相談テーマ分類・実装仕様は各正本ドキュメントで管理する。
- Home Hero の画面構成または責務が変更された場合のみ更新する。
