

# Access Tier Copy Audit

> **Status: Archive**
>
> 本ドキュメントは、Access Tier Copy接続時点の判断とTODOを記録したArchive文書である。
>
> 現行のAccess Tier判定・Paywall責務は `docs/product/billing-paywall.md` を正本とする。

## ConciergeResult Premium card 接続方針

### ゴール
ConciergeResult の Premium 系カードが `reasonVm.hero.*` を使い回さず、意味整理用の `reasonVm.detail.*` を参照する状態にする。

### 現在地
`ConciergeTopRecommendationHero` は Hero 表示専用として `reasonVm.hero.*` を参照する。
一方で、状態整理・神社意味・行動意味のカードは `reasonVm.detail.*` を正本として扱う。

### 接続方針

```txt
ConciergeTopRecommendationHero
→ reasonVm.hero.*

ConsultationSummaryCard
→ reasonVm.detail.consultationSummary

ShrineMeaningCard
→ reasonVm.detail.shrineMeaning

ActionMeaningCard
→ reasonVm.detail.actionMeaning
```

### legacy fields
`reasonVm.why` と `reasonVm.interpretation` は legacy compatibility field として残す。
このPRでは削除しない。

### 判断
`hero.*` は presentation 用、`detail.*` は meaning / interpretation 用として扱う。
Premium 差分は hero copy の再利用ではなく、detail payload の接続で表現する。

### TODO

```markdown
- [x] ConciergeTopRecommendationHero は reasonVm.hero.* のまま維持する
- [x] ConsultationSummaryCard は reasonVm.detail.consultationSummary を参照する
- [x] ShrineMeaningCard は reasonVm.detail.shrineMeaning を参照する
- [x] ActionMeaningCard は reasonVm.detail.actionMeaning を参照する
- [x] why / interpretation は legacy として即削除しない
- [x] docs/access-tier-copy-audit.md に接続方針を追記
- [x] typecheck
```
