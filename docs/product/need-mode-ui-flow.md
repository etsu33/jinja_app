# Need Mode UI Flow

## 目的

Concierge First における Need Mode のUI導線を定義する。

Need Mode は、ユーザーの相談テーマや自由入力から「今どのような願い・状態・必要性があるか」を読み取り、`need_tags` を中心に神社推薦へ接続する主導線である。

このドキュメントでは、相談テーマチップ、自由入力、`need_tags`、Compat Mode との責務境界を整理し、UI上で何を前面に出すかを固定する。

---

## 結論

MVPでは、Kamimusubi の主導線を Need Mode とする。

```text
相談テーマチップ
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

誕生日・相性・占術・吉方位は Compat Mode として扱い、Need Mode を上書きしない。

---

## Need Modeの役割

Need Mode は、ユーザーの相談内容をもとに、神社推薦の中心軸を作るモードである。

### 担当するもの

```markdown
- 相談テーマ
- 自由入力
- need_tags
- consultation_axis
- matched_need_tags
- 推薦理由の主文脈
- Meaning Card の中心文脈
```

### 担当しないもの

```markdown
- 誕生日による相性補助
- 占術補助
- 吉方位
- 方角計算
- 現在地からの経路最適化
- 神社検索そのもの
```

Need Mode は「神社を条件検索するモード」ではない。

ユーザーの相談から、今必要な意味を抽出し、その意味に合う神社へ接続するためのモードである。

---

## 相談テーマチップとの関係

相談テーマチップは、Need Mode の入口として扱う。

### 役割

```markdown
- 相談の開始ハードルを下げる
- ユーザーが自分の状態を選びやすくする
- need_tags抽出の初期ヒントになる
- consultation_axis推定の初期ヒントになる
```

### 採用テーマ

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

### 注意

相談テーマチップは、相談内容を確定するものではない。

自由入力がある場合は、自由入力の意味を優先する。

---

## 自由入力との関係

自由入力は Need Mode の正本入力として扱う。

### 役割

```markdown
- チップでは表現しきれない相談を受け取る
- need_tags抽出の主材料になる
- consultation_axis推定の主材料になる
- 推薦理由の主文脈になる
```

### 優先順位

```text
自由入力
↓
相談テーマチップ
↓
補助条件
```

### 判断例

| 相談テーマチップ | 自由入力 | 優先する解釈 |
|---|---|---|
| 少し休みたい | 転職するか迷って眠れない | career / mental / rest |
| 仕事について考えたい | 疲れて何も考えられない | rest / mental |
| お金の流れを整えたい | 起業の売上を伸ばしたい | money / career / courage |
| これからを考えたい | 資格を取って方向性を変えたい | study / career / courage |

---

## need_tagsとの接続

`need_tags` は Need Mode の中心データである。

### 現在の役割

```markdown
- ユーザーの相談意図をタグ化する
- 神社側のご利益・説明・history_themeと接続する
- matched_need_tags の母体になる
- Recommendation Score v2 の主入力になる
```

### UIからの接続

```text
HomeHero / ConciergeEntry
↓
相談テーマチップ / 自由入力
↓
query
↓
need_tags抽出
↓
Recommendation Score v2
```

### 注意

`need_tags` はUIでそのまま見せない。

ユーザー向けには、以下のような意味表現に変換する。

| need_tag | UI上の説明方向 |
|---|---|
| career | 仕事や転機に向き合う |
| money | お金や生活の流れを整える |
| relationship / love | 人との関係やご縁を見直す |
| courage | 一歩踏み出す |
| rest / mental | 気持ちを落ち着ける、休む |
| health | 心身や生活の土台を整える |
| study / focus | 学びや積み重ねに向き合う |

---

## Compat Modeとの責務境界

Compat Mode は、誕生日・相性・占術補助・方位補助などを扱う補助モードである。

### Need Mode

```markdown
- 相談テーマ
- 自由入力
- need_tags
- consultation_axis
- matched_need_tags
- 推薦理由の中心
```

### Compat Mode

```markdown
- 誕生日
- element4
- 相性候補
- 占術補助
- 方位補助
- 吉方位候補
```

### 境界ルール

```markdown
- Need Modeを主導線にする
- Compat Modeは補助条件Accordion内に置く
- Compat Modeは推薦理由の主語にならない
- 相性や占術は、相談テーマとの一致を補足する時だけ表示する
- 吉方位は現在地・方角計算の根拠が確認できるまで前面化しない
```

---

## UI表示方針

### HomeHero

HomeHero では Need Mode を前面に出す。

```markdown
- 相談テーマチップ
- 自由入力
- この相談ではじめるCTA
- 条件追加導線
```

表示しないもの:

```markdown
- 誕生日入力
- 相性説明
- 吉方位説明
- ご利益選択本体
- 参拝スタイル詳細
```

---

### ConciergeEntry

ConciergeEntry では、相談テーマの確認と微修正を行う。

```markdown
- HomeHeroから渡されたthemeを表示する
- 自由入力を編集できる
- 必要なら相談テーマチップを選び直せる
- 補助条件Accordionへ進める
```

---

### Result / Meaning Card

推薦結果では、Need Mode由来の文脈を中心に表示する。

```text
あなたの相談テーマ
↓
今必要な意味
↓
この神社と重なる理由
↓
参拝前に意識すること
```

Compat Mode由来の情報は、補足として扱う。

---

## UI文言方針

### NG

```markdown
- あなたは〇〇タイプなので、この神社が正しいです
- 誕生日から見ると、この神社に行くべきです
- 吉方位なので必ず良いです
- 金運アップできます
```

### OK

```markdown
- 相談内容から見ると、今は仕事や転機に向き合う文脈が強く出ています
- この神社は、決断や前進の意味と重なります
- 誕生日情報は、相性を見る補助として使っています
- 方位情報は補助的な参考情報として扱います
```

---

## Recommendation Score v2との接続

Need Mode は Recommendation Score v2 の主入力になる。

### 主入力

```markdown
- query
- need_tags
- consultation_axis
- matched_need_tags
```

### 補助入力

```markdown
- selected_goriyaku_tag_ids
- extra_condition
- visit_style_tags
- birthdate
- element4
```

### 判断

`need_tags` と `matched_need_tags` を主軸にする。

`birthdate` / `element4` / `visit_style_tags` は補助シグナルとして扱う。

---

## 次PR候補

### PR1: Need Mode UI反映

```markdown
- [ ] HomeHero / ConciergeEntry の文言をNeed Mode中心に整理
- [ ] 相談テーマチップを主導線として表示
- [ ] 自由入力を補助入力として見せつつ、解釈上は正本として扱う
- [ ] 条件追加導線を補助扱いにする
- [ ] typecheck
```

### PR2: Need Mode / Compat Mode表示分離

```markdown
- [ ] ConciergeFilterPanel内で誕生日・相性を補助表示にする
- [ ] Need Mode由来の推薦理由を主表示にする
- [ ] Compat Mode由来の情報を補足表示へ移動する
- [ ] 吉方位表示はDirection Audit完了まで前面化しない
```

### PR3: Meaning Card接続

```markdown
- [ ] Meaning Cardの主文脈をneed_tags / matched_need_tagsに寄せる
- [ ] history_themeは神社側の意味文脈として表示する
- [ ] Compat Modeは補足欄に分離する
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/need-mode-ui-flow作成
- [x] Need Modeの役割を定義
- [x] 相談テーマチップとの関係を整理
- [x] 自由入力との関係を整理
- [x] need_tagsとの接続を整理
- [x] Compat Modeとの責務境界を整理
- [x] docsへNeed Mode UI導線を追記
```
