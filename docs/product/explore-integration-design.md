# Explore Integration Design

## 目的

`/shrines` と `/map` を、将来的に Explore / 神社をたどる体験として統合する。

Top は相談開始、Concierge は推薦理由、Explore は実際に行ける神社を探す体験として分離する。

---

## 基本方針

```text
Top
└─ 相談入力

Concierge
└─ 相談内容に基づく推薦・理由・相性補助

Explore / 神社をたどる
└─ 体験・検索・地図・一覧を統合
```

---

## 統合後の構造

```text
Explore / 神社をたどる
├─ 体験で選ぶ
│  ├─ 過ごし方
│  │  ├─ 静か
│  │  ├─ 自然
│  │  ├─ 駅近
│  │  ├─ ひとり
│  │  └─ 落ち着く
│  │
│  └─ 歴史テーマ
│     ├─ 縁結び
│     ├─ 武運
│     ├─ 商売
│     ├─ 学問
│     ├─ 稲荷
│     └─ 八幡
│
├─ 詳しく探す
│  ├─ 神社名検索
│  ├─ 地域名検索
│  └─ 願いごと検索
│
├─ 近くで探す
│  ├─ 現在地
│  ├─ 近くの神社
│  └─ Google Mapで開く
│
└─ 結果
   ├─ 一覧
   └─ 地図
```

---

将来的には、`/shrines` と `/map` を Explore 画面として統合する。

ただし今回の実装では、まず `/shrines` の上部UIを体験フィルター中心に整理する。

---

## Explore画面の責務

Explore は、相談結果とは別に「実際に行ける神社を探す」ための画面として扱う。

```text
Explore の責務
├─ 体験から神社を探す
├─ 神社名 / 地域 / 願いごとで詳しく探す
├─ 現在地から近くの神社を探す
├─ 一覧で候補を比較する
└─ 地図で場所と移動しやすさを確認する
```

---

## `/shrines` と `/map` の共通要素

```text
共通要素
├─ 神社を探す入口
├─ キーワード入力
├─ 神社候補の表示
├─ 詳細ページへの導線
├─ Google Map / 地図導線
└─ 空状態表示
```

### `/shrines` 固有

```text
/shrines
├─ q検索
├─ ご利益タグ
├─ 体験チップ
├─ 歴史テーマ
└─ 一覧結果
```

### `/map` 固有

```text
/map
├─ 現在地取得
├─ nearby fetch
├─ PlaceSuggestBox
└─ Google Maps検索
```

---


## Explore State 設計

```text
ExploreState
├─ viewMode
│  ├─ list
│  └─ map
│
├─ filters
│  ├─ experienceTags
│  ├─ historyThemes
│  ├─ keyword
│  └─ goriyakuTags
│
├─ nearby
│  ├─ enabled
│  ├─ coords
│  ├─ usedFallback
│  └─ status
│
└─ results
   ├─ listItems
   ├─ nearbyItems
   ├─ selectedPlace
   └─ loadingState
```

---

## ViewMode 定義

```text
viewMode
├─ list: 一覧で候補を比較する
└─ map: 地図で場所と移動しやすさを確認する
```

初期値は `list` とする。

理由:

- 既存 `/shrines` の一覧体験を維持できる
- Map表示は位置情報・外部地図導線の依存がある
- いきなり地図主導にすると実装範囲が広がる

---

## FilterState 定義

```text
FilterState
├─ experienceTags: 過ごし方
├─ historyThemes: 歴史テーマ
├─ keyword: 神社名 / 地域名 / 願いごと
└─ goriyakuTags: ご利益タグ
```

### 配置方針

```text
体験チップ
└─ Explore上部の主導線

詳しく探す
├─ keyword
└─ goriyakuTags
```

神社名検索は残すが、主導線ではなく `詳しく探す` 配下に置く。

---

## NearbyState 定義

```text
NearbyState
├─ enabled: 近くで探すを使うか
├─ coords: 現在地またはfallback座標
├─ usedFallback: 現在地取得失敗時の判定
├─ status: idle / loading / error / empty / ready
└─ items: 近くの神社候補
```

`NearbyState` は Map 固有の処理を直接 Explore 全体へ広げず、近くで探すセクション内に閉じ込める。

---

## ExploreLayout 案

```text
ExploreLayout
├─ ExploreHeader
│  └─ 神社をたどる
│
├─ ExperienceFilterSection
│  ├─ 過ごし方
│  └─ 歴史テーマ
│
├─ DetailSearchAccordion
│  ├─ 神社名検索
│  ├─ 地域名検索
│  └─ 願いごと / ご利益タグ
│
├─ NearbySection
│  ├─ 現在地取得
│  ├─ 近くの神社
│  └─ Google Mapで開く
│
├─ ViewModeTabs
│  ├─ 一覧
│  └─ 地図
│
└─ ResultArea
   ├─ ShrineListResult
   └─ ShrineMapResult
```

---

## TODO

```markdown
- [x] develop最新化
- [x] feature/explore-layout-foundation 作成
- [x] Explore画面の責務を確定
- [x] /shrines と /map の共通要素を洗い出す

# State
- [x] ExploreState設計
- [x] ViewMode定義
- [x] FilterState定義
- [x] NearbyState定義

# Layout
- [x] ExploreLayout設計
- [ ] 一覧/地図切替タブ設計
- [ ] 近くの神社セクション統合設計
- [ ] Search/Map共通Filter設計

# Docs
- [ ] architecture.md更新
- [ ] roadmap.md更新
```
