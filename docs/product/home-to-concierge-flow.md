

# Home to Concierge Flow

## 目的

HomeHero から Concierge へ遷移する仕様を定義する。

このドキュメントでは、HomeHero で入力・選択された相談テーマを `/concierge` にどう渡すか、`openFilter` をどう扱うか、`theme_key` を渡すかどうか、空入力時の挙動を整理する。

HomeHero は相談体験の入口であり、Concierge は相談内容の確認・補助条件追加・推薦生成を担う。

---

## 結論

MVPでは、HomeHero から Concierge へ渡す query parameter は以下に限定する。

```text
theme
openFilter
```

`theme_key` は現時点では URL に渡さない。

理由は、現行実装では `theme` の自然文を正本として扱っており、`theme_key` を追加すると UI状態・分析・推薦入力の責務が増えるため。

`theme_key` は将来の共通定数化・analytics設計で追加を検討する。

---

## HomeHeroから渡すquery parameter

### 採用するもの

| parameter | 型 | 役割 | 例 |
|---|---|---|---|
| theme | string | 相談テーマ・自由入力の本文 | `気持ちを切り替えたい` |
| openFilter | `1` | Concierge到達時に補助条件Accordionを開く | `openFilter=1` |

### 採用しないもの

| parameter | 理由 |
|---|---|
| theme_key | 初期MVPでは渡さない。自然文 `theme` を正本にする |
| birthdate | HomeHeroには置かない。Filter側で扱う |
| goriyaku_tag_ids | HomeHeroには置かない。Filter側で扱う |
| visit_style | HomeHeroには置かない。Filter側で扱う |
| direction | Direction Audit完了まで前面化しない |

---

## themeの扱い

`theme` は、HomeHero から Concierge へ渡す相談本文として扱う。

### 役割

```markdown
- HomeHeroの自由入力内容を渡す
- チップ選択時はチップに対応する自然文を渡す
- ConciergeEntryのtextarea初期値になる
- Need Modeの query 入力になる
```

### 遷移例

```text
/concierge?theme=仕事の流れを整えて、次に進むきっかけがほしいです
```

### 注意

- `theme` は URL encode する
- 空文字の場合は渡さない
- `theme` は `theme_key` ではなく自然文として扱う
- Concierge側では `theme` を textarea に反映する

---

## openFilterの扱い

`openFilter=1` は、Concierge到達時に補助条件Accordionを開くためのフラグとして扱う。

### 役割

```markdown
- HomeHeroの「＋ 条件を追加する」から来た場合に使う
- ConciergeClientFullで `setIsFilterOpen(true)` する
- 誕生日・ご利益・参拝スタイルなどの補助条件入力へ誘導する
```

### 遷移例

```text
/concierge?theme=少し休みたい&openFilter=1
```

```text
/concierge?openFilter=1
```

### 注意

- `openFilter` は推薦条件そのものではない
- UIの初期表示制御だけに使う
- `openFilter=1` がない場合は通常のConciergeEntry表示にする

---

## theme_keyを渡すか判断

### 結論

MVPでは `theme_key` をURLに渡さない。

### 理由

現時点では、以下の設計で十分成立する。

```text
HomeHero
↓
theme自然文
↓
ConciergeEntry textarea
↓
query
↓
need_tags抽出
```

`theme_key` を追加すると、以下の責務が増える。

```markdown
- theme_keyのURL設計
- theme_keyとtheme自然文の同期
- theme_keyのanalytics設計
- theme_keyのpayload設計
- theme_keyと自由入力が矛盾した時の優先順位
```

すでに `consultation-theme-taxonomy.md` と `meaning-translation-mapping.md` で、`theme_key` はUI用の中間キーとして整理済みである。

そのため、初期MVPではURLに出さず、将来の共通定数化PRで扱う。

---

## 空入力時の遷移仕様

### 通常開始CTA

HomeHero の「この相談ではじめる」は、theme が空の場合は disabled にする。

```text
themeあり → /concierge?theme=...
themeなし → disabled
```

### 条件追加CTA

HomeHero の「＋ 条件を追加する」は、theme が空でも遷移できる。

```text
themeあり → /concierge?theme=...&openFilter=1
themeなし → /concierge?openFilter=1
```

### 理由

補助条件だけ先に入れたいユーザーを拒否しないため。

ただし、推薦生成には最終的に相談テーマまたは自由入力が必要である。

---

## HomeHero / ConciergeEntry / Filterの責務接続

### HomeHero

担当:

```markdown
- 相談テーマチップを選ぶ
- 自由入力を書く
- Conciergeへ遷移する
- 条件追加導線を出す
```

担当しない:

```markdown
- 誕生日入力
- ご利益選択
- 参拝スタイル詳細
- 相性説明
- 吉方位説明
```

---

### ConciergeEntry

担当:

```markdown
- HomeHeroから渡されたthemeを受け取る
- themeをtextarea初期値として表示する
- 相談内容を確認・編集できるようにする
- 推薦生成CTAを表示する
- Filterへの導線を表示する
```

担当しない:

```markdown
- 条件入力本体を持つ
- 誕生日や相性を主入力にする
- 吉方位を前面化する
```

---

### ConciergeFilterPanel

担当:

```markdown
- 誕生日
- ご利益
- 参拝スタイル
- 相性から見た候補
- extraCondition
```

担当しない:

```markdown
- 相談テーマの正本化
- Need Modeの主入力
- 推薦理由の主表示
```

---

## URLパターン一覧

| 状態 | URL | Concierge側の挙動 |
|---|---|---|
| テーマありで開始 | `/concierge?theme=...` | textareaにthemeを反映、Filterは閉じる |
| テーマありで条件追加 | `/concierge?theme=...&openFilter=1` | textareaにthemeを反映、Filterを開く |
| テーマなしで直接開始 | `/concierge` | 空のConciergeEntryを表示 |
| テーマなしで条件追加 | `/concierge?openFilter=1` | 空のConciergeEntryを表示、Filterを開く |

---

## 実装方針

### HomeHeroConsultationInput

現行の `buildConciergeHref(theme, options?)` を維持する。

```ts
buildConciergeHref(theme)
buildConciergeHref(theme, { openFilter: true })
```

### ConciergeClientFull

現行の `openFilter` 受け取りを維持する。

```ts
const openFilter = (sp.get("openFilter") ?? "").trim();
if (openFilter === "1") setIsFilterOpen(true);
```

### theme受け取り

`theme` は、ConciergeEntryの `needText` 初期値として使う。

---

## analytics方針

初期MVPでは、Home→Concierge遷移時の `theme_key` analytics は追加しない。

ただし、将来的には以下を検討する。

```markdown
- home_theme_chip_click
- home_to_concierge_start
- home_to_concierge_filter_open
- themeKey property
- hasTheme property
- openFilter property
```

### 判断

今はUI責務と推薦入力を固める段階なので、analytics拡張は次フェーズに回す。

---

## 次PR候補

### PR1: Home→Concierge遷移仕様の実装確認

```markdown
- [ ] buildConciergeHrefの現行仕様をテストで固定
- [ ] themeあり通常遷移を確認
- [ ] themeありopenFilter遷移を確認
- [ ] themeなしopenFilter遷移を確認
- [ ] typecheck
```

### PR2: HomeHero / ConciergeEntry UI整合

```markdown
- [ ] HomeHeroのチップ文言をTaxonomyに寄せる
- [ ] ConciergeEntryのチップ文言をTaxonomyに寄せる
- [ ] 自由入力の表示優先度を整理
- [ ] 条件追加導線を補助扱いに調整
- [ ] typecheck
```

### PR3: theme_key共通定数化

```markdown
- [ ] CONSULTATION_THEMESを共通定数化
- [ ] theme_key / label / defaultText を分離
- [ ] HomeHero / ConciergeEntryで共通利用
- [ ] theme_keyをanalyticsに入れるか判断
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/home-to-concierge-flow作成
- [x] HomeHeroから渡すquery parameterを確定
- [x] themeの扱いを定義
- [x] openFilterの扱いを定義
- [x] theme_keyを渡すか判断
- [x] 空入力時の遷移仕様を定義
- [x] HomeHero / ConciergeEntry / Filterの責務を接続
- [x] docsへHome→Concierge遷移仕様を追記
```
