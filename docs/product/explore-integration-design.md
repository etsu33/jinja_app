# Explore Integration Design

## 目的

本ドキュメントは、Explore の責務と役割を定義する。

Explore は「おすすめされた神社を探し、比較し、訪問先を選ぶための探索レイヤー」とし、Recommendation・Meaning Layer・神社詳細とは責務を分離する。

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
```

Explore は「どこへ行くか」を支援し、「なぜその神社なのか」は Concierge が担当する。

---

## 基本原則

- Explore は探索体験のみを担当する
- Recommendation Logic を持たない
- Meaning Layer を持たない
- Recommendation Score を持たない
- 検索・比較・位置確認に責務を限定する

---

## Explore の責務

- 神社候補の一覧表示
- 地図表示
- 神社検索
- 条件による絞り込み
- 現在地周辺の探索
- 神社詳細への導線

---

## 画面責務

| 画面 | 役割 |
|------|------|
| Explore | 神社候補を探す・比較する |
| Detail | 神社情報を理解する |
| Route | 現地まで移動する |

### 設計原則

- Explore は探索のみを担当する
- Detail は神社情報を正確に伝える
- Route は移動支援のみを担当する

---

## 責務境界

| ドキュメント | 責務 |
|--------------|------|
| `docs/product/explore-integration-design.md` | Explore の役割・画面責務 |
| `docs/product/concierge-first.md` | 体験導線 |
| `docs/product/concierge-modes.md` | 推薦モード |
| `docs/core/meaning-layer.md` | 意味変換 |
| `docs/core/architecture.md` | システム全体の責務 |

---

## 関連ドキュメント

- `docs/product/concierge-first.md`
- `docs/product/concierge-modes.md`
- `docs/core/meaning-layer.md`
- `docs/core/architecture.md`

---

## 更新ルール

- 本書には実装手順・API仕様・TODOを記載しない
- Explore の責務または役割が変更された場合のみ更新する
- 詳細仕様は各正本ドキュメントで管理する
