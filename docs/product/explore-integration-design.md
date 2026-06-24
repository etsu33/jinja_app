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

## ExploreLayout 利用方針

ExploreLayout は Container として扱う。

責務:

- Explore UIを並べる
- childrenを描画する

責務外:

- API呼び出し
- Recommendation Logic
- Meaning Layer
- URL管理
- Search State管理

---

## Props Boundary

```text
ExploreLayout
├─ activeTag
├─ inputValue
├─ viewMode
├─ goriyakuTags
├─ callbacks
└─ children
```

方針:

- State は親が保持する
- ExploreLayout は Presentational Component として扱う
- ExploreLayout は結果表示の中身を解釈しない
- ExploreLayout は `children` を ResultArea として描画する

---

## Integration Strategy

```text
Phase 1
└─ ExploreLayout 作成

Phase 2
└─ /shrines 接続

Phase 3
└─ /map 接続

Phase 4
└─ Explore Route 統合
```

### 接続方針

- `/shrines` は list mode の親として State を保持する
- `/map` は map / nearby mode の親として State を保持する
- ExploreLayout は `/shrines` と `/map` の共通UIとして段階的に接続する
- 既存URLは維持し、統合Routeは後続フェーズで検討する

---

## Story / Test Strategy

```text
ExploreLayout.story.tsx
├─ list mode
├─ map mode
├─ active tag
└─ empty result

ExploreLayout.test.tsx
├─ children render
├─ viewMode render
├─ tag callback
└─ search callback
```

方針:

- 本番ページ接続前に props 構造を固定する
- Story では UI状態を確認する
- Test では callback と children 描画を確認する
- API呼び出しは ExploreLayout のテスト対象にしない

---

## Search / Map 共通Filter設計

Search / Map 共通Filter は、Explore 上で使う検索条件の意味を揃えるための設計レイヤーとして扱う。

### 目的

```text
共通Filterの目的
├─ /shrines と /map の入力条件を揃える
├─ ExploreLayout 接続時の props 境界を明確にする
├─ Search State と Nearby State を混ぜない
└─ 将来の Explore Route 統合に備える
```

---

## Common Filter State

```text
CommonFilterState
├─ keyword
│  └─ 神社名 / 地域名 / 願いごと
│
├─ experienceTag
│  └─ 過ごし方
│
├─ historyTheme
│  └─ 歴史テーマ
│
└─ goriyakuTag
   └─ ご利益タグ
```

### 方針

- keyword は `/shrines` の q 検索を正本とする
- experienceTag / historyTheme は体験チップ由来の条件として扱う
- goriyakuTag は DetailSearchAccordion 配下の補助条件として扱う
- 1つの tag 文字列に寄せる現状実装は維持しつつ、将来的に filter object へ拡張できる形にする

---

## `/shrines` 側 Filter 入力

```text
/shrines
├─ keyword
│  └─ inputValue / q
│
├─ experienceTag
│  └─ ExperienceFilterSection
│
├─ historyTheme
│  └─ ExperienceFilterSection
│
└─ goriyakuTag
   └─ DetailSearchAccordion
```

責務:

- `/shrines` は list mode の検索状態を保持する
- URL の `q` は当面維持する
- fetchShrines() の呼び出しは `/shrines` 側に残す
- ExploreLayout は検索結果を解釈しない

---

## `/map` 側 Filter 入力

```text
/map
├─ keyword
│  └─ PlaceSuggestBox
│
├─ nearby
│  └─ NearbyShrineCardListClient
│
└─ viewMode
   └─ map / nearby
```

責務:

- `/map` は map / nearby mode の状態を保持する
- 現在地取得・fallback・nearby fetch は NearbyShrineCardListClient 側に閉じ込める
- PlaceSuggestBox は map 側の keyword 入力として扱う
- ExploreLayout 接続時も nearby 処理を ExploreLayout に持ち込まない

---

## ExploreLayout 接続前の制約

```text
接続前の制約
├─ ExploreLayout は API を呼ばない
├─ ExploreLayout は URL を更新しない
├─ ExploreLayout は Search State を持たない
├─ ExploreLayout は Nearby State を持たない
└─ ExploreLayout は children を ResultArea として描画するだけにする
```

### 段階的接続

```text
Phase 1
└─ /shrines の上部UIだけ ExploreLayout に接続

Phase 2
└─ list result を children として渡す

Phase 3
└─ /map の上部UIを ExploreLayout に接続

Phase 4
└─ NearbySection / Map result の統合範囲を再判断する
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
- [x] 一覧/地図切替タブ設計
- [x] 近くの神社セクション統合設計
- [x] Search/Map共通Filter設計

# ExploreLayout Usage
- [x] ExploreLayout利用方針を追加
- [x] Props Boundaryを追加
- [x] Integration Strategyを追加
- [x] Story/Test Strategyを追加

# Docs
- [ ] architecture.md更新
- [ ] roadmap.md更新
```
