# Analytics Event Storage Audit

## 目的

- event が適切に送れているか、payload が足りているかを監査する
- 今後の改善のための課題を洗い出す
- 次PR候補

---

## 関連ドキュメント

- `docs/analytics/save-premium-correlation.md`
  - favorite / detail / route / premium_preview / checkout / premium_active の相関定義
  - save_rate / detail_to_route_rate / save_to_route_rate の分析定義
  - 「保存されるが課金されない」「詳細は見られるが参拝行動に進まない」「Premium preview は押されるが checkout に行かない」落下判定

# save / premium correlation との接続

`analytics-card-events.md` は event payload / provider / 保存先の監査を扱う。

一方で、`docs/analytics/save-premium-correlation.md` は、取得済み event をどう組み合わせて落下地点を判定するかを扱う。

責務分離:

```txt
analytics-card-events.md
  → event が正しく送れるか / payload が足りているか

analytics/save-premium-correlation.md
  → event を使って save / premium / checkout の相関をどう読むか
```

このため、相関分析の定義は `save-premium-correlation.md` を正本とする。

# 欠損リスク
