

# ShrineDetail policy 接続監査

> **Status: Archive**
>
> 本ドキュメントは、Shrine Detailのカード接続候補と優先順位を整理した時点監査である。
>
> Context Reason・Personal Meaning・Saved Recordの責務は `docs/product/shrine-detail-layer.md` を正本とする。

最終更新: 2026-05-18  
対象: ShrineDetail / ContextReason / PersonalMeaning / SavedRecord

---

## 目的

神社詳細ページに存在する表示ブロックを棚卸しし、今後 `CardVisibilityPolicy` に接続する候補を整理する。

このPRでは実装を増やさず、既存表示の責務確認だけを行う。

---

## 対象ファイル

```txt
apps/web/src/app/shrines/[id]/page.tsx
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
apps/web/src/lib/shrine/buildShrineDetailModel.ts
```

---

## 現在の ShrineDetail 表示構造

神社詳細ページは、以下の3層に近い構造をすでに持っている。

```markdown
- ContextReason: コンシェルジュ起点の推薦理由
- PersonalMeaning: ユーザー文脈に対する意味づけ
- SavedRecord: お気に入り・御朱印・保存済み記録
```

ただし、現時点では cardId 単位ではなく、既存 section / props / 導線に分散している。

---

## ContextReasonCard 相当

### 既存表示

```markdown
- `reasonSection`
- `ShrineReasonSection`
- `recommendationMeta`
- `ShrineComparisonDisclosure`
- `recommendationRankExplanation`
- `recommendationRankComparison`
```

### 主な関連ファイル

```txt
apps/web/src/app/shrines/[id]/page.tsx
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
apps/web/src/lib/shrine/buildShrineDetailModel.ts
```

### 責務

コンシェルジュ起点で「なぜこの神社が候補に入ったのか」を説明する。

主に以下を扱う。

```markdown
- 今回の相談との一致
- 推薦候補内での位置づけ
- 上位候補との違い
- rank explanation / rank comparison
```

### 表示してよいもの

```markdown
- 推薦判断の主理由
- 補助理由
- 1位理由
- 他候補との差
```

### 表示しないもの

```markdown
- ユーザーの長期記録
- 御朱印やお気に入りの履歴
- 状態変化の深掘り
- 行動の断定
```

### policy 接続候補

```markdown
- cardId: context_reason
- anonymous: hidden
- free: partial
- premium: visible
```

### 現時点の判断

`ContextReasonCard` 相当は既存構造がある。

ただし `reasonSection` と `recommendationMeta` が分かれているため、最初のpolicy接続では両方をまとめて制御するか、別cardIdに分けるかを決める必要がある。

---

## PersonalMeaningCard 相当

### 既存表示

```markdown
- `meaningSection`
- `ShrineJudgeSection`
- `heroMeaningCopy`
- `recommendationReasonDetail`
- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
```

### 主な関連ファイル

```txt
apps/web/src/app/shrines/[id]/page.tsx
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
apps/web/src/lib/shrine/buildShrineDetailModel.ts
```

### 責務

ユーザーの相談文脈に対して、この神社をどう受け取るかを説明する。

主に以下を扱う。

```markdown
- 今の状態整理
- 神社の意味
- 行動意味
- コンシェルジュ起点の個人向け補足理由
```

### 表示してよいもの

```markdown
- recommendationReasonDetail.consultationSummary
- recommendationReasonDetail.shrineMeaning
- recommendationReasonDetail.actionMeaning
- heroMeaningCopy
```

### 表示しないもの

```markdown
- 公開神社情報そのもの
- 御朱印記録
- お気に入り保存状態
- 他ユーザー情報
```

### policy 接続候補

```markdown
- cardId: personal_meaning
- anonymous: hidden
- free: teaser
- premium: visible
```

### 現時点の判断

`PersonalMeaningCard` 相当は既存構造がある。

ただし、`heroMeaningCopy` はヘッダーにも使われており、単純に hidden にすると詳細ページ全体の見出し体験まで崩れる可能性がある。

最初のpolicy接続では、本文section側を対象にし、hero copy は別扱いにするのが安全。

---

## SavedRecordCard 相当

### 既存表示

```markdown
- `saveActionNode`
- `favoriteNoticeState`
- `PublicGoshuinSection`
- `addGoshuinHref`
- `showGoshuinSection`
- `publicGoshuinsPreview`
- `publicGoshuinsViewAllHref`
```

### 主な関連ファイル

```txt
apps/web/src/app/shrines/[id]/page.tsx
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
apps/web/src/components/shrine/detail/PublicGoshuinSection.tsx
apps/web/src/components/shrine/ShrineSaveButton.tsx
```

### 責務

お気に入り、御朱印、保存済み記録など、ユーザー個人の記録導線を扱う。

主に以下を扱う。

```markdown
- お気に入り保存
- お気に入り解除
- 自分の記録への導線
- 御朱印追加導線
- 公開御朱印表示
```

### 表示してよいもの

```markdown
- お気に入り保存CTA
- 保存完了メッセージ
- マイページのお気に入り導線
- 御朱印追加導線
- 公開御朱印preview
```

### 表示しないもの

```markdown
- コンシェルジュ推薦理由
- 個人向け意味づけ本文
- Premium専用の深い比較
```

### policy 接続候補

```markdown
- cardId: saved_record
- anonymous: teaser
- free: visible
- premium: visible
```

### 現時点の判断

`SavedRecordCard` 相当は、単一cardではなく複数導線に分散している。

そのため、最初から1つの `SavedRecordCard` としてUI統合するのではなく、以下のように段階的に扱う。

```markdown
1. saveActionNode / favoriteNoticeState を保存導線として整理
2. PublicGoshuinSection を公開記録導線として整理
3. addGoshuinHref を個人記録追加導線として整理
4. 必要なら後続PRで SavedRecordCard として統合
```

---

## ConciergeResult 側との分離

この監査は ShrineDetail 側のみを対象とする。

ConciergeResult 側の以下とは別PRで扱う。

```markdown
- consultation_summary
- shrine_meaning
- action_meaning
- previous_comparison
- history_shift
- deep_reflection
```

理由:

```markdown
- ConciergeResult は相談結果の提示が主目的
- ShrineDetail は神社情報と個人文脈の接続が主目的
- 同じ cardId 名でも表示位置と責務が異なる
- 同時に変更すると表示境界が崩れやすい
```

---

## policy 接続優先順位

### 優先度A: ContextReasonCard

最初に接続する候補。

理由:

```markdown
- 既存の reasonSection がある
- context_reason の責務と対応しやすい
- Concierge起点の文脈に限定しやすい
- Free partial / Premium visible の差分を作りやすい
```

### 優先度B: PersonalMeaningCard

次に接続する候補。

理由:

```markdown
- recommendationReasonDetail が既にある
- consultationSummary / shrineMeaning / actionMeaning の整理単位がある
- Premium価値と接続しやすい
```

注意:

```markdown
- heroMeaningCopy は別扱いにする
- 詳細ページの主見出しを壊さない
```

### 優先度C: SavedRecordCard

最後に接続する候補。

理由:

```markdown
- 保存 / 御朱印 / お気に入りが分散している
- Public情報とPersonal情報が混ざりやすい
- UI統合前に責務整理が必要
```

---

## 実装を増やさない制約

この監査PRでは以下を行わない。

```markdown
- [ ] CardVisibilityPolicy を変更しない
- [ ] ShrineDetailArticle の JSX を変更しない
- [ ] buildShrineDetailModel の返却構造を変更しない
- [ ] 新規コンポーネントを作らない
- [ ] analytics event を追加しない
- [ ] Free / Premium の表示差分を変更しない
```

---

## 次PR候補

### 候補A: context_reason policy 接続

```markdown
- [ ] CardVisibilityPolicy に context_reason を追加
- [ ] ShrineDetailArticle で contextReasonVisibility を使う
- [ ] reasonSection を hidden / partial / visible に分岐
- [ ] card_view / card_partial_view analytics を送る
- [ ] typecheck
```

### 候補B: personal_meaning policy 接続

```markdown
- [ ] CardVisibilityPolicy に personal_meaning を追加
- [ ] meaningSection を hidden / teaser / visible に分岐
- [ ] heroMeaningCopy は表示維持する
- [ ] card_teaser_view / card_view analytics を送る
- [ ] typecheck
```

### 候補C: saved_record policy 接続

```markdown
- [ ] CardVisibilityPolicy に saved_record を追加
- [ ] saveActionNode / favoriteNoticeState の扱いを整理
- [ ] PublicGoshuinSection との境界を決める
- [ ] anonymous は保存導線 teaser にする
- [ ] typecheck
```

---

## TODO

```markdown
- [x] ShrineDetail page の表示構造を確認
- [x] ContextReasonCard 相当の既存表示を整理
- [x] PersonalMeaningCard 相当の既存表示を整理
- [x] SavedRecordCard 相当の既存表示を整理
- [x] policy 接続候補を整理
- [x] ConciergeResult 側とは別PRにする
- [x] 実装はまだ増やさない
```
