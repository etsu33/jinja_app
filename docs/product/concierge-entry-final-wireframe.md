

# ConciergeEntry Final Wireframe

## 目的

`ConciergeEntry` は、HomeHero から始まった相談を受け取り、推薦生成へ進む前の確認・補足画面として扱う。

この画面は「検索フォーム」ではなく、相談テーマを確認し、必要な補助条件だけを追加するための入口である。

---

## ConciergeEntryの役割

ConciergeEntry の役割は以下。

- HomeHero から渡された相談テーマを受け取る
- 直接 `/concierge` に来たユーザーにも相談開始口を提供する
- 相談テーマを確認・微修正できるようにする
- 補助条件Accordionへ誘導する
- 推薦生成CTAへつなぐ

ConciergeEntry は推薦結果を表示しない。

推薦結果の表示責務は `ConciergeSectionsRenderer` 側に寄せる。

---

## HomeHeroから来た時の表示

### URL

```text
/concierge?theme=...
/concierge?theme=...&openFilter=1
```

### 表示方針

HomeHeroから theme が渡された場合、ConciergeEntry は「新しく相談を書かせる画面」ではなく、「相談内容を確認する画面」として表示する。

### 表示構造

```text
相談テーマを確認する

[HomeHeroから渡された相談文]

必要なら少しだけ補足できます。

[＋ 条件を追加する]
[この内容で神社を提案してもらう]
```

### 注意

- HomeHeroで選んだテーマを消さない
- theme がある場合は textarea を空にしない
- `openFilter=1` がある場合は補助条件Accordionを開く
- 相談テーマチップは控えめに表示する

---

## 直接/conciergeに来た時の表示

### URL

```text
/concierge
/concierge?openFilter=1
```

### 表示方針

直接アクセスの場合は、ConciergeEntry が相談開始画面になる。

ただし、検索UIではなく相談体験の入口として表示する。

### 表示構造

```text
今のテーマを選ぶ

[仕事について考えたい]
[人との関係を整えたい]
[お金の流れを整えたい]
[一歩踏み出したい]
[少し休みたい]
[体調を整えたい]
[学びを深めたい]
[これからを考えたい]

必要なら一言だけ補足する
[textarea]

[＋ 条件を追加する]
[この内容で神社を提案してもらう]
```

---

## ConciergeEntryCardに残す要素

### 残す

- 相談テーマ表示
- 相談テーマチップ
- 自由入力 textarea
- 条件追加導線
- 未ログイン時の保存案内
- 相談開始CTA
- クリア

### 控えめにする

- 呼び名入力
- 自由入力 textarea
- 未ログイン案内

### 削除候補

- HomeHeroと重複する強い説明文
- 過度な補足文
- 条件入力本体

---

## ConciergeFilterPanelとの責務境界

### ConciergeEntryCard

担当:

- 相談テーマ
- 相談文の確認
- 相談開始CTA

### ConciergeFilterPanel

担当:

- 誕生日
- ご利益
- 参拝スタイル
- 相性から見た候補
- 補助条件

### 判断

ConciergeEntryCard に条件入力本体を置かない。

条件追加は `ConciergeFilterPanel` に集約する。

---

## 相談テーマチップの扱い

相談テーマチップは、カテゴリ検索ではなく「今の状態を選びやすくする入口」として扱う。

### 最終候補

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

### 対応する内部テーマ

| 表示 | 内部テーマ |
|---|---|
| 仕事について考えたい | work |
| 人との関係を整えたい | relationship |
| お金の流れを整えたい | money |
| 一歩踏み出したい | challenge |
| 少し休みたい | rest |
| 体調を整えたい | health |
| 学びを深めたい | study |
| これからを考えたい | future |

### 注意

- UIでは状態ベースの文言にする
- payloadでは need / axis 判定に使いやすい値へ変換する
- チップ選択を強制しない
- 自由入力で上書き可能にする

---

## 自由入力textareaの扱い

自由入力は主役ではなく補助入力として扱う。

### 役割

- チップだけでは表現できない相談を補足する
- HomeHeroから渡された theme を微修正する
- need推定の補助材料にする

### 表示方針

- Heroより控えめにする
- 「必須入力」感を出しすぎない
- placeholder は短くする

### placeholder候補

```text
例: 気持ちを切り替えたい、これからのことを考えたい
```

---

## CTA文言

### メインCTA

```text
この内容で神社を提案してもらう
```

### 補助条件CTA

```text
＋ 条件を追加する
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

## Home→Concierge→Result Flow

```text
HomeHero
↓
theme / openFilter をURLで渡す
↓
ConciergeEntry
↓
相談テーマを確認
↓
必要ならFilterを追加
↓
filter_apply または send
↓
ConciergeSectionsRenderer
↓
推薦結果表示
```

---

## 次PR候補

### PR1: ConciergeEntry UI整理

```markdown
- [ ] HomeHeroから渡されたtheme表示を確認
- [ ] 直接アクセス時のテーマチップ表示を整理
- [ ] textareaを補助入力として調整
- [ ] 条件追加導線を整理
- [ ] CTA文言を統一
- [ ] typecheck
```

### PR2: 相談テーマ定義の共通化

```markdown
- [ ] 相談テーマ一覧を共通定数化
- [ ] HomeHeroとConciergeEntryで同じテーマ定義を使う
- [ ] 表示文言と内部テーマを分離
- [ ] payload変換を確認
- [ ] typecheck
```

### PR3: ConciergeFilterPanel整理

```markdown
- [ ] 誕生日を補助相性として表示
- [ ] ご利益を神社側特徴条件として表示
- [ ] 参拝スタイルを3レイヤーに整理
- [ ] 相性候補と吉方位候補を混同しない
- [ ] typecheck
```

---

## 完成定義

- HomeHeroから来たユーザーが相談内容を確認できる
- 直接/conciergeに来たユーザーも相談開始できる
- ConciergeEntryとConciergeFilterPanelの責務が重複しない
- 自由入力が主役化しすぎない
- Concierge First方針と整合する

---

## TODO

```markdown
- [x] ConciergeEntryの役割を定義
- [x] HomeHeroから来た時の表示を定義
- [x] 直接/conciergeに来た時の表示を定義
- [x] ConciergeEntryCardに残す要素を確定
- [x] ConciergeFilterPanelとの責務境界を整理
- [x] 相談テーマチップの扱いを確定
- [x] 自由入力textareaの扱いを確定
- [x] CTA文言を確定
- [x] 次PR候補を整理
```
