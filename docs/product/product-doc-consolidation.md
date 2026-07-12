# Product Doc Consolidation

## 目的

Google Docs の `product` ドキュメントを、現行の Concierge First 最新仕様へ統合する。

このドキュメントは、Google Docs 側を直接更新する前に、Git上で統合方針を固定するための作業メモである。

正本は `docs/product/concierge-first-final-spec.md` とし、Google Docs の `product`
は最新仕様を読むための1枚のハブドキュメントとして再構成する。

---

## 結論

Google Docs `product` は、以下の役割へ整理する。

```text
KAMI MUSUBI Product
= 事業・UX・MVP仕様の最新ハブ
```

古い Concierge First Wireframe は、`concierge-first-final-spec.md` ベースの最新版へ置き換える。

Explore案は削除せず、将来構想として下部へ移動する。

---

## Source of Truth

現時点の正本は以下。

```text
docs/product/concierge-first-final-spec.md
```

補助参照は以下。

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

Google Docs `product` は、これらをすべて並列に載せるのではなく、`concierge-first-final-spec.md` を中心に再構成する。

---

## Google Docs product 再構成方針

### 残すもの

```markdown
- Product Vision
- Concierge First MVP結論
- HomeHero / ConciergeEntry / Filter責務
- Need Mode / Compat Mode境界
- Recommendation Score v2との接続
- User State Profileとの接続
- Concierge First実装順
- MVP実装対象
- 将来構想としてのExplore
```

### 置き換えるもの

```markdown
- 古い Concierge First Wireframe
- 古いHomeHero案
- 古い条件追加エリア案
- 古い実装Phase
- theme_key / openFilter整理前の遷移仕様
```

### 下部へ移動するもの

```markdown
- Explore Integration Design
- /shrines と /map の将来統合案
- 神社検索・地図・一覧の拡張構想
```

### 削除してよいもの

```markdown
- 重複している古いワイヤー
- HomeConciergeInlineClient前提の記述
- 誕生日・相性・吉方位を主導線に見せる記述
- 現行仕様と矛盾するCTA文言
```

---

## Google Docs product 新構成案

```markdown
# KAMI MUSUBI Product

## 1. Product Vision

KAMI MUSUBI は、神社検索アプリではなく、今の相談テーマから神社と出会うAIコンシェルジュ体験である。

## 2. Source of Truth

現時点の正本は `docs/product/concierge-first-final-spec.md` とする。

## 3. Concierge First MVP

- Need Modeを主導線にする
- Compat Modeは補助条件に留める
- 誕生日は残すが前面化しない
- 吉方位はDirection Audit完了まで前面化しない
- 神社一覧・地図はサブ導線にする

## 4. UI責務

### HomeHero

相談テーマ / 自由入力 / 開始CTA / 条件追加導線

### ConciergeEntry

相談内容の確認・編集 / 推薦生成CTA / Filter導線

### Filter

誕生日 / ご利益 / 参拝スタイル / 相性候補 / extraCondition

## 5. Need Mode / Compat Mode

Need Modeを推薦理由の中心にする。Compat Modeは補足理由として扱う。

## 6. Recommendation Score v2接続

主入力は query / need_tags / consultation_axis / matched_need_tags。補助入力は visit_style_tags / birthdate / element4 /
selected_goriyaku_tag_ids。

## 7. User State Profile

query と need_tags を正本として扱う。theme_key や誕生日は補助情報として扱う。

## 8. 実装順

1. HomeHero / ConciergeEntry UI整合
2. Filter UI整理
3. Home→Concierge遷移テスト固定
4. Meaning Card設計接続

## 9. MVP実装対象

- HomeHero相談テーマチップ整理
- ConciergeEntry相談確認UI整理
- Filter内の補助条件集約
- Need Mode / Compat Mode表示分離
- Home→Concierge遷移仕様固定
- Meaning Cardの主文脈整理

## 10. 実装しないもの

- theme_keyのURL渡し
- 吉方位の前面表示
- 九星気学ロジック本実装
- 方角計算本実装
- 神社一覧・地図の主導線化

## 11. Future: Explore

Exploreは将来構想として保持する。Topは相談開始、Conciergeは推薦理由、Exploreは実際に行ける神社を探す体験として分離する。
```

---

## README / roadmap への反映要否

### README

反映候補あり。

```markdown
- Concierge Firstの正本リンクを追加
- Product Visionを「神社検索」から「相談体験」へ更新
```

### roadmap

反映候補あり。

```markdown
- Concierge First設計完了を反映
- 次フェーズをUI実装へ移動
- Recommendation Score v2 / Meaning Card接続を次タスクへ整理
```

### architecture

現時点では必須ではない。

ただし、Need Mode / Compat Modeの責務分離をArchitectureへ反映する余地はある。

---

## 次PR候補

### PR1: Google Docs product 更新

```markdown
- [ ] Google Docs product を concierge-first-final-spec ベースに再構成
- [ ] 古い Concierge First Wireframe を最新版へ置換
- [ ] Explore案は将来構想として下部へ移動
- [ ] Source of Truth を明記
- [ ] 実装順を最新化
```

### PR2: README / roadmap 反映

```markdown
- [ ] READMEにConcierge First正本リンクを追加
- [ ] roadmapに設計完了と実装フェーズを反映
- [ ] 必要に応じてarchitectureへNeed / Compat境界を追記
```

---

## TODO

```markdown
- [x] develop最新化
- [x] docs/product-doc-consolidation作成
- [x] Google Docs product を concierge-first-final-spec ベースに再構成
- [x] 古い Concierge First Wireframe を最新版へ置換
- [x] Explore案は将来構想として下部へ移動
- [x] Source of Truth を明記
- [x] 実装順を最新化
- [x] README / roadmap への反映要否を確認
```
