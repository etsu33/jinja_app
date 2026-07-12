# Explore Integration Design

## 目的

本ドキュメントは、Explore の体験設計と責務を定義する。

Explore は「おすすめされた神社を実際に探し、比較し、訪れるための探索レイヤー」と位置付け、Recommendation・Meaning Layer・神社詳細とは責務を分離する。

---

## 体験フロー

```text
Recommendation
↓
Explore
↓
Detail
↓
Route
↓
Visit
↓
Reflection
```

Explore は「どこへ行くか」を支援する画面であり、「なぜその神社なのか」は Concierge が担当する。

---

## 基本原則

- Explore は候補探索を担当する
- Recommendation Logic を持たない
- Meaning Layer を持たない
- Recommendation Score を持たない
- 検索・比較・位置確認に責務を限定する
- 一覧表示と地図表示を共通体験として提供する

---

## Explore の責務

Explore は以下を担当する。

- 神社候補の一覧表示
- 地図表示
- 神社名検索
- 地域検索
- ご利益タグ検索
- 体験タグによる絞り込み
- 現在地周辺の神社探索
- 神社詳細への導線

---

## 画面構成

```text
Explore
├─ Experience Filter
├─ Detail Search
├─ Nearby
├─ View Mode
│  ├─ List
│  └─ Map
└─ Result Area
```

---

## 入力責務

### 体験フィルター

- 過ごし方
- 歴史テーマ

### 詳細検索

- 神社名
- 地域名
- ご利益タグ

### Nearby

- 現在地
- 周辺神社

Explore は検索条件を保持するが、推薦ロジックは保持しない。

---

## ExploreLayout の責務

ExploreLayout は Explore 全体の共通レイアウトを提供する。

担当するもの

- Explore UI の構成
- 一覧・地図の切り替え
- Filter UI の配置
- Result Area の配置

担当しないもの

- API 呼び出し
- Recommendation Logic
- Meaning Layer
- URL 管理
- Search State
- Nearby State

State は親コンポーネントが保持し、ExploreLayout は Presentational Component として扱う。

---

## View Mode

Explore は 2 つの表示モードを提供する。

| Mode | 役割 |
|------|------|
| List | 神社を比較する |
| Map | 場所を確認する |

初期表示は List とする。

---

## 責務境界

| ドキュメント | 責務 |
|--------------|------|
| `docs/product/explore-integration-design.md` | Explore の体験設計・画面責務 |
| `docs/product/concierge-first.md` | 相談から推薦までの体験導線 |
| `docs/product/concierge-modes.md` | 推薦モード |
| `docs/core/meaning-layer.md` | 意味変換 |
| `docs/core/architecture.md` | システム全体の責務境界 |

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/product/concierge-first.md`
- `docs/product/concierge-modes.md`
- `docs/core/meaning-layer.md`
- `docs/shrine-detail-layer.md`
- `docs/core/roadmap.md`

---

## 更新ルール

- 実装履歴や TODO は本書へ記載しない
- API 仕様・コンポーネント仕様・テスト仕様は専用ドキュメントへ分離する
- Explore の責務または体験設計が変更された場合のみ更新する
- 実装状態の変更だけでは本書を更新しない
- Explore の役割が Recommendation・Detail・Meaning Layer と重複しないよう維持する
