> **Status: Archive**
>
> 本ドキュメントは、Concierge First の初期設計を記録するArchive文書である。
>
> 現行の仕様判断には使用しない。
>
> 最新の仕様は `docs/product/concierge-first-final-spec.md` を正本とする。

# Concierge First

## 目的

KAMI MUSUBI における Concierge First の設計思想と、体験全体の方向性を記録する。

本書は初期設計の保存を目的とし、現行の仕様・実装判断には使用しない。

---

## 初期コンセプト

KAMI MUSUBI の体験は、「神社を探す」ことではなく、「相談から神社と出会い、現実の行動へつなげる」ことを目的として設計された。

```text
相談
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

検索を起点とするのではなく、相談を起点とすることを基本思想としている。

---

## 基本原則

- 相談をプロダクトの入口とする
- 神社検索・地図は補助導線とする
- 補助条件（参拝スタイル・誕生日・ご利益）は推薦を補完する
- 占術・相性・吉方位は補助シグナルとして扱う
- AIは心理・宗教・人生を断定しない

---

## 初期の責務整理

| 画面 | 役割 |
|------|------|
| Top | 相談開始 |
| Concierge | 推薦生成 |
| Explore | 候補探索 |
| Detail | 神社理解 |
| Route | 移動支援 |
| Visit | 参拝記録 |
| Reflection | 振り返り |

---

## 現行仕様

現在の Concierge First の正式仕様は、以下の正本で管理する。

- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`

---

## 関連ドキュメント

- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
