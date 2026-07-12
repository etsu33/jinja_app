

# Concierge First Final Spec

## 目的

Concierge First 実装前に、HomeHero / ConciergeEntry / Filter / Need Mode / Compat Mode / Recommendation Score v2 / User State Profile の責務を1枚に統合する。

このドキュメントは、これまで分割して整理した設計ドキュメント群を実装前仕様として束ねるための正本である。

実装時はこの仕様を基準にし、迷った場合は個別ドキュメントへ戻る。

---

## MVP結論

Kamimusubi のMVP主導線は、神社検索ではなく「相談テーマから神社と出会う体験」とする。

```text
HomeHero
↓
相談テーマ / 自由入力
↓
ConciergeEntry
↓
補助条件Filter
↓
Need Mode中心の推薦
↓
Meaning Card
```

MVPでは以下を守る。

```markdown
- Need Modeを主導線にする
- Compat Modeは補助条件に留める
- 誕生日は残すが前面化しない
- 相性は補足理由に留める
- 吉方位はDirection Audit完了まで前面化しない
- 神社一覧 / 地図はサブ導線にする
- 自由入力は補助入力として見せつつ、解釈上は正本として扱う
- 参拝スタイルは推薦補助として扱う
```

---

## HomeHero責務

HomeHero は相談体験の入口である。

### 担当するもの

```markdown
- 相談テーマチップ表示
- 自由入力textarea
- 「この相談ではじめる」CTA
- 「＋ 条件を追加する」導線
- /concierge への遷移
```

### 担当しないもの

```markdown
- 誕生日入力
- ご利益選択本体
- 参拝スタイル詳細
- 相性表示
- 吉方位表示
- 神社一覧の主導線化
- 地図の主導線化
```

### UI方針

```markdown
- 相談テーマを主役にする
- textareaは補助入力として見せる
- 条件追加は補助導線として扱う
- 検索フォーム感を弱める
- Quiet Luxuryトーンへ寄せる
```

---

## ConciergeEntry責務

ConciergeEntry は、HomeHeroから渡された相談テーマを確認・補足し、推薦生成へ進める画面である。

### 担当するもの

```markdown
- URL query `theme` の受け取り
- textarea初期値への反映
- 相談内容の確認・編集
- 相談テーマチップの表示
- 推薦生成CTA
- Filterへの導線
- 未ログイン時の保存案内
```

### 担当しないもの

```markdown
- 条件入力本体
- 誕生日や相性の主入力化
- 吉方位表示の前面化
- 推薦結果表示
```

### 表示方針

HomeHeroから `theme` が渡された場合は、相談内容の確認画面として扱う。

直接 `/concierge` に来た場合は、相談開始画面として扱う。

---

## Filter責務

Filter は、Need Modeを補助する条件入力レイヤーである。

### 担当するもの

```markdown
- 誕生日
- ご利益タグ
- 参拝スタイル
- 相性から見た候補
- extraCondition
```

### 担当しないもの

```markdown
- 相談テーマの正本化
- Need Modeの主入力
- 推薦理由の主表示
- 吉方位の前面化
```

### 表示方針

Filter は `ConciergeFilterPanel` に集約する。

HomeHero / ConciergeEntry に条件入力本体を重複させない。

---

## Need Mode / Compat Mode境界

### Need Mode

Need Mode は、ユーザーの相談テーマ・自由入力から必要性を読み取り、推薦理由の主文脈を作る。

```markdown
- 相談テーマ
- 自由入力
- query
- need_tags
- consultation_axis
- matched_need_tags
- 推薦理由の主文脈
- Meaning Cardの中心文脈
```

### Compat Mode

Compat Mode は、誕生日・相性・占術補助・方位補助を扱う補助レイヤーである。

```markdown
- 誕生日
- element4
- suggestedTags
- 相性候補
- 方位補助
- 吉方位候補
```

### 境界ルール

```markdown
- Need Modeを主導線にする
- Compat ModeはFilter内に置く
- Compat Modeは相談テーマを上書きしない
- Compat Modeは推薦理由の主語にしない
- Compat Mode由来の情報はMeaning Cardの補足欄に置く
```

---

## Recommendation Score v2入力一覧

Recommendation Score v2では、以下を入力候補として扱う。

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
- hasBirthdate
- behavior_signal
- context_profile
```

### MVP判断

```markdown
- need_tags / matched_need_tags を主軸にする
- consultation_axis は相談意図の整理に使う
- visit_style_tags は補助加点として扱う
- birthdate / element4 はCompat Mode補助として扱う
- theme_key は初期MVPではscoreへ直接入れない
```

---

## User State Profile入力一覧

User State Profileでは、以下を優先順位で扱う。

```text
query / 自由入力
↓
need_tags
↓
consultation_axis
↓
theme_key
↓
extra_condition
↓
Compat Mode補助情報
```

### 正本入力

```markdown
- query
- need_tags
```

### 整理用入力

```markdown
- consultation_axis
- theme_key
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

User State Profileでは、ユーザー状態を断定しない。

`need_tags` は相談意図の正本として扱い、`matched_need_tags` は神社側との一致結果として扱う。

---

## Home→Concierge遷移仕様

MVPで渡すquery parameterは以下。

```text
theme
openFilter
```

### theme

`theme` は相談本文の自然文として扱う。

```text
/concierge?theme=...
```

### openFilter

`openFilter=1` は、Concierge到達時にFilterを開くためのUI制御フラグとして扱う。

```text
/concierge?theme=...&openFilter=1
/concierge?openFilter=1
```

### theme_key

MVPではURLに渡さない。

`theme_key` は将来の共通定数化・analytics設計で検討する。

---

## Concierge First実装順

実装順は以下を推奨する。

### PR1: HomeHero / ConciergeEntry UI整合

```markdown
- [ ] HomeHeroのチップ文言をTaxonomyに寄せる
- [ ] ConciergeEntryのチップ文言をTaxonomyに寄せる
- [ ] textareaを補助入力として表示調整
- [ ] 条件追加導線を補助扱いに調整
- [ ] typecheck
```

### PR2: Filter UI整理

```markdown
- [ ] ConciergeFilterPanelを3レイヤー表示へ整理
- [ ] 誕生日説明を補助表現へ調整
- [ ] 相性候補の説明を弱める
- [ ] 参拝スタイルを体験 / 実用 / 神社好き向けに整理
- [ ] typecheck
```

### PR3: Home→Concierge遷移テスト固定

```markdown
- [ ] buildConciergeHrefの仕様をテストで固定
- [ ] themeあり通常遷移を確認
- [ ] themeありopenFilter遷移を確認
- [ ] themeなしopenFilter遷移を確認
- [ ] typecheck
```

### PR4: Meaning Card設計接続

```markdown
- [ ] Need Mode由来の推薦理由を主表示にする
- [ ] Compat Mode由来の情報を補足欄へ移動する
- [ ] history_themeを神社側文脈として表示する
- [ ] action_suggestionとの重複を避ける
- [ ] typecheck
```

---

## MVP実装対象

### 実装対象

```markdown
- HomeHero相談テーマチップ整理
- ConciergeEntry相談確認UI整理
- Filter内の誕生日 / ご利益 / 参拝スタイル集約
- Need Mode / Compat Mode表示分離
- Home→Concierge遷移仕様固定
- Meaning Cardの主文脈整理
```

### 実装しないもの

```markdown
- theme_keyのURL渡し
- theme_keyのscore直接加点
- 吉方位の前面表示
- 九星気学ロジックの本実装
- 方角計算の本実装
- 神社一覧の主導線化
- 地図の主導線化
- visitStyle専用stateの新設
- photo / goshuin / mythology / special などのvisit_style_tags追加
```

---

## 次PR候補

### 最優先

```markdown
- [ ] HomeHero / ConciergeEntry UI整合
```

### 次点

```markdown
- [ ] Filter UI整理
- [ ] Home→Concierge遷移テスト固定
- [ ] Meaning Card設計接続
```

---

## 参照ドキュメント

```markdown
- docs/product/home-hero-final-wireframe.md
- docs/product/concierge-entry-final-wireframe.md
- docs/product/consultation-theme-taxonomy.md
- docs/product/meaning-translation-mapping.md
- docs/product/visit-style-taxonomy.md
- docs/product/need-mode-ui-flow.md
- docs/product/compat-mode-ui-flow.md
- docs/product/home-to-concierge-flow.md
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/concierge-first-final-spec作成
- [x] HomeHero責務を最終固定
- [x] ConciergeEntry責務を最終固定
- [x] Filter責務を最終固定
- [x] Need Mode / Compat Mode接続整理
- [x] Recommendation Score v2入力一覧確定
- [x] User State Profile入力一覧確定
- [x] Concierge First実装順を確定
- [x] MVP実装対象を確定
```
