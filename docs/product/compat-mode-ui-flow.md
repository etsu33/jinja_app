# Compat Mode UI Flow

## 目的

Concierge First における Compat Mode のUI導線を定義する。

Compat Mode は、誕生日・element4・相性候補・占術補助・方位補助などを扱う補助モードである。

このドキュメントでは、Compat Mode の役割、Need Mode との境界、HomeHero / ConciergeEntry / Meaning Card での表示方針を整理する。

---

## 結論

MVPでは、Compat Mode を推薦の主導線にはしない。

主導線は Need Mode とし、Compat Mode は補助条件Accordion内に置く。

```text
Need Mode
相談テーマ / 自由入力 / need_tags / matched_need_tags
↓
推薦理由の中心

Compat Mode
誕生日 / element4 / 相性候補 / 方位補助
↓
補足理由・補助条件
```

誕生日や相性は残す。

ただし、UI前面には出さない。

吉方位は、現在地・方角計算・九星気学ロジックの根拠が確認できるまで前面化しない。

---

## Compat Modeの役割

Compat Mode は、相談テーマに対する神社推薦を補助するための相性・文脈補助レイヤーである。

### 担当するもの

```markdown
- 誕生日入力
- element4算出
- 相性から見た候補
- 占術補助シグナル
- 方位補助シグナル
- 吉方位候補の将来設計
```

### 担当しないもの

```markdown
- 相談テーマの正本化
- need_tags の主判定
- 推薦理由の主語
- ユーザー状態の断定
- 参拝すべき方向の断定
```

---

## 誕生日入力の責務

誕生日入力は、相性補助のための任意入力として扱う。

### UI上の扱い

```markdown
- HomeHeroには置かない
- ConciergeEntryにも主入力として置かない
- ConciergeFilterPanel内の補助条件として置く
- 必須入力にしない
- 「提案の補助として使います」と明記する
```

### 役割

```markdown
- element4算出の入力
- 相性候補の初期ヒント
- analytics上の hasBirthdate 判定
- Compat Mode の補助シグナル
```

### 表示文言候補

```text
誕生日（任意）
提案の補助として使います
```

### 注意

誕生日からユーザーの性格や運命を断定しない。

「あなたは〇〇だから、この神社が正しい」とは表示しない。

---

## element4の責務

`element4` は、誕生日から算出される相性補助ラベルとして扱う。

### 現在の位置付け

現行UIでは、`ConciergeFilterPanel` 内で以下のように表示される。

```text
あなたの傾向: {element4}
```

### 役割

```markdown
- suggestedTags の補助条件
- 相性から見た候補の表示補助
- Compat Modeの説明材料
```

### 表示方針

`element4` は、ユーザーの本質や人格を断定する表現にしない。

#### NG

```markdown
- あなたは火タイプなので、この神社に行くべきです
- あなたの性格は〇〇です
- この属性の人はこの神社と相性が良いです
```

#### OK

```markdown
- 誕生日から見た補助傾向です
- 相性候補を出すための参考情報です
- 相談テーマを補助する材料として使います
```

---

## 相性表示の責務

相性表示は、Need Modeで抽出した相談テーマに対して、神社候補を補助的に並べる材料として扱う。

### UI上の扱い

```markdown
- ConciergeFilterPanel内に置く
- 「相性から見た候補」として表示する
- 推薦結果の主理由にはしない
- Meaning Cardでは補足欄に置く
```

### 役割

```markdown
- 誕生日由来の補助シグナル
- suggestedTags の表示
- ご利益タグ選択の補助
```

### 表示文言候補

```text
相性から見た候補
誕生日情報をもとに、補助的に近いテーマを表示しています。
```

### 注意

相性表示は、Need Modeの相談テーマより上位に置かない。

ユーザーが選んだ相談内容と矛盾する相性候補を強制しない。

---

## 吉方位表示の責務

吉方位は現時点では前面化しない。

### 理由

現時点で未確認の論点がある。

```markdown
- 現在地を推薦計算に使っているか
- 神社との方角計算をしているか
- 九星気学ロジックがあるか
- 吉方位表示のデータソースは何か
- 相性候補と吉方位候補が混同されていないか
```

### MVP方針

```markdown
- 吉方位は補足表示にもまだ強く出さない
- Direction Audit が完了するまで前面化しない
- 使う場合は「方位の参考情報」として弱く扱う
- 参拝を促す断定表現は使わない
```

### NG

```markdown
- 今日はこの方角が吉です
- 吉方位なのでこの神社に行くべきです
- この方角なら運気が上がります
```

### OK

```markdown
- 方位情報は補助的な参考として扱います
- 現在地や方角計算の根拠が確認できた場合のみ表示します
- 相性候補とは分けて扱います
```

---

## Need Modeとの境界

Need Mode と Compat Mode は明確に分離する。

| 項目 | Need Mode | Compat Mode |
|---|---|---|
| 主入力 | 相談テーマ / 自由入力 | 誕生日 |
| 主データ | need_tags / consultation_axis | element4 / suggestedTags |
| 推薦理由 | 主理由 | 補足理由 |
| UI位置 | HomeHero / ConciergeEntryの主導線 | ConciergeFilterPanel内の補助条件 |
| スコア影響 | 主軸 | 補助シグナル |
| 表示トーン | 今の相談から見る | 補助的に見る |

### 境界ルール

```markdown
- Need Modeを主導線にする
- Compat Modeは補助条件に閉じる
- Compat Modeは相談テーマを上書きしない
- Compat ModeはRecommendation Score v2で強い重みにしない
- Compat Mode由来の情報はMeaning Cardの補足欄に置く
```

---

## HomeHeroでの表示方針

HomeHeroでは Compat Mode を表示しない。

### 表示するもの

```markdown
- 相談テーマチップ
- 自由入力
- 条件追加導線
- この相談ではじめるCTA
```

### 表示しないもの

```markdown
- 誕生日入力
- element4
- 相性表示
- 吉方位表示
- 占術説明
```

### 理由

HomeHeroは相談体験の入口であり、相性診断の入口ではない。

ここで誕生日や占術を前面化すると、神社検索 / 占い診断アプリに見える。

---

## ConciergeEntryでの表示方針

ConciergeEntryでも Compat Mode を主入力として扱わない。

### 表示するもの

```markdown
- 相談テーマの確認
- 自由入力の編集
- 補助条件Accordionへの導線
```

### Compat Modeへの導線

```text
＋ 条件を追加する
```

Accordionを開いた先に、誕生日・相性候補を表示する。

### 注意

ConciergeEntryの主CTAは、Need Mode由来の相談開始である。

誕生日を入れないと進めない構造にしない。

---

## Meaning Cardでの表示方針

Meaning Cardでは、Need Mode由来の推薦理由を主表示にする。

Compat Mode由来の情報は補足欄に置く。

### 表示順

```text
1. 相談テーマとの一致
2. 神社側の意味文脈
3. 参拝前に意識すること
4. 補足情報
   - 誕生日由来の相性補助
   - 参拝スタイルとの一致
   - 方位情報がある場合の参考表示
```

### 表示文言候補

```text
補足として、誕生日情報から見た相性候補とも一部重なっています。
```

```text
方位情報は、現在地と計算根拠が確認できる場合のみ参考として表示します。
```

---

## Recommendation Score v2での扱い

Compat Mode は補助シグナルとして扱う。

### 主軸にしないもの

```markdown
- birthdate
- element4
- suggestedTags
- direction_bonus
- zodiac / astrology /九星気学系の補助情報
```

### 補助として使う可能性があるもの

```markdown
- hasBirthdate
- element4
- selected_goriyaku_tag_ids
- suggestedTags
- direction_bonus
```

### 判断

`need_tags` / `matched_need_tags` / `consultation_axis` を主軸にする。

Compat Modeは、同程度の候補間で補助的に効く程度に留める。

---

## UI文言方針

### NG

```markdown
- あなたは〇〇タイプです
- この神社が運命的に合っています
- 吉方位なので行くべきです
- 誕生日から見るとこれが正解です
```

### OK

```markdown
- 誕生日情報は、相性を見る補助として使います
- 相談テーマとの一致を優先して提案しています
- 相性情報は補足として参考にできます
- 方位情報は計算根拠が確認できる場合のみ表示します
```

---

## 次PR候補

### PR1: Compat Mode 表示整理

```markdown
- [ ] ConciergeFilterPanelの誕生日説明を補助表現へ調整
- [ ] element4表示文言を弱める
- [ ] 相性候補の説明を追加
- [ ] 吉方位表示を前面化しない方針を反映
- [ ] typecheck
```

### PR2: Meaning Card補足欄整理

```markdown
- [ ] Need Mode由来の推薦理由を主表示にする
- [ ] Compat Mode由来の情報を補足欄へ移動する
- [ ] 誕生日・相性・方位の表示順を整理する
- [ ] 説明文の断定表現を避ける
```

### PR3: Direction Audit

```markdown
- [ ] 現在地を推薦計算に使っているか確認
- [ ] 神社との方角計算をしているか確認
- [ ] 九星気学ロジックがあるか確認
- [ ] 吉方位表示のデータソース確認
- [ ] 相性候補と吉方位候補を分離する
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/compat-mode-ui-flow作成
- [x] Compat Modeの役割を定義
- [x] 誕生日入力の責務を整理
- [x] element4の責務を整理
- [x] 相性表示の責務を整理
- [x] 吉方位表示の責務を整理
- [x] Need Modeとの境界を整理
- [x] HomeHeroでの表示方針を整理
- [x] ConciergeEntryでの表示方針を整理
- [x] Meaning Cardでの表示方針を整理
- [x] docsへCompat Mode UI Flowを追記
```
