> **Status: Archive**
>
> 本ドキュメントは、Concierge First UI設計初期段階のワイヤーフレーム検討記録である。
>
> 現行のUI・体験設計・実装判断には使用しない。
>
> 最新の仕様は以下を正本とする。
>
> - `docs/product/concierge-first-final-spec.md`
> - `docs/product/home-hero-final-wireframe.md`
> - `docs/product/concierge-entry-final-wireframe.md`

# Concierge First Wireframe

## 目的

Concierge First を設計する初期段階で検討した、Top画面とConcierge画面のワイヤーフレームおよび責務整理を記録する。

本書は設計履歴を保存することを目的とし、現行仕様の判断には利用しない。

---

## 初期コンセプト

KAMI MUSUBI の入口を「神社検索」ではなく、「相談から神社と出会う体験」として設計することを目指した。

```text
Home
↓
相談入力
↓
Concierge
↓
Recommendation
↓
Detail
↓
Route
↓
Visit
↓
Reflection
```

---

## 初期構成

### Home

- Hero
- 相談入力
- 相談テーマチップ
- Conciergeへの導線
- 地図・神社一覧への補助導線

### Concierge

- 相談内容確認
- 補助条件入力
- 推薦結果表示
- 推薦理由表示

---

## 設計方針

- Homeは相談開始を担当する
- Conciergeは推薦生成を担当する
- 補助条件は相談内容を補完する
- 神社検索・地図は補助導線とする
- 推薦ロジックはUIから分離する

---

## 責務整理

| 画面       | 初期の役割 |
| ---------- | ---------- |
| Home       | 相談開始   |
| Concierge  | 推薦生成   |
| Detail     | 神社理解   |
| Route      | 移動支援   |
| Visit      | 参拝記録   |
| Reflection | 振り返り   |

---

## 現在の正本

現在のUI設計は以下の正本で管理する。

- `docs/product/concierge-first-final-spec.md`
- `docs/product/home-hero-final-wireframe.md`
- `docs/product/concierge-entry-final-wireframe.md`
- `docs/product/concierge-filter-area.md`

---

## 関連ドキュメント

- `docs/product/concierge-first-final-spec.md`
- `docs/product/home-hero-final-wireframe.md`
- `docs/product/concierge-entry-final-wireframe.md`
- `docs/product/concierge-filter-area.md`
- `docs/product/concierge-modes.md`
- `docs/core/architecture.md`
