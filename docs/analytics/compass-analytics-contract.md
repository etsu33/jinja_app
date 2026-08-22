# Compass Analytics Contract

> Status: Active

Compass の発見から Recommendation 経由の Shrine Detail 表示、および
Favorite / Visit / Reflection への source 伝播までを計測する契約。

## Lifecycle

| event | 用途 | 主なproperty |
|---|---|---|
| `home_compass_entry_click` | HomeからCompassを開く | `source=home` |
| `compass_entry` | Compass表示 | `referrer_source=home\|direct` |
| `compass_result` | Compass request完了 | `result_state`, `purpose`, `origin_mode`, `has_birthdate`, `recommendation_count`, `recommendationInstanceId`, `calculationMethod`（新規、任意。COMMON/MONTHLY FALLBACKの識別用segmentation dimension。詳細は`docs/analytics/compass-posthog-query-contract.md` §1.2） |

## Recommendation attribution

成功したCompass APIレスポンスは、リクエストごとにステートレスな
`recommendation_instance_id`を1つ生成する。DBへ保存しない。同一レスポンスの
全Recommendation itemにも同じ値を複製し、frontendでは既存の
`recommendationInstanceId` propertyとして扱う。

| 段階 | event | 必須attribution |
|---|---|---|
| Recommendation表示 | `card_view` | `source=compass`, `recommendationInstanceId`, `shrineId`, `recommendationRank` |
| Recommendationクリック | `shrine_detail_transition` | 同上 |
| Shrine Detail表示 | `shrine_detail_view` | 同上 |

CompassからShrine DetailへのURLは `ctx=compass`、
`recommendation_instance_id`、`recommendation_rank`を運ぶ。直接訪問ではこれらを
合成しない。`ctx=compass`以外の既存経路、特にConciergeのthread snapshotからの
Recommendation Instance復元は変更しない。

## Action source propagation（PR-C）

Compass経由でShrine Detailに到達した**同一ページrender**の範囲でのみ、
Favorite / Visit / Reflectionの既存イベントが`source=compass`を伝播する。新規
イベントは追加しない（既存event + `source`のみ）。

| Action | event（既存、変更なし） | 変更内容 |
|---|---|---|
| Favorite | `favorite_click`, `shrine_decision` | `source`を`ctx===compass`のときのみ`"compass"`、それ以外は既存どおり`"shrine_detail"`のまま |
| Visit | `visit_done` | 同上 |
| Reflection | `reflection_prompt_view`, `reflection_saved` | 同上 |

Concierge/map/直接訪問の`source`値は変更しない（既存contractのまま）。

`recommendationInstanceId`も同じ範囲で伝播する
（`compassRecommendationInstanceId ?? conciergeRecommendationInstanceId`）。
`recommendationRank`はFavorite/Visit/Reflectionへ伝播しない
— Concierge経由でも現状これらのactionへrankは渡っておらず、PR-Cはその
既存アーキテクチャに新しい配線を追加しない。

### Attribution strength（帰属の強さ）

| Action | 分類 | 理由 |
|---|---|---|
| Favorite | SESSION / NAVIGATION ATTRIBUTION | 同一Shrine Detail page renderの`ctx`クエリパラメータに限定。DB永続化なし |
| Visit | SESSION / NAVIGATION ATTRIBUTION | 同上 |
| Reflection（prompt/saved） | SESSION / NAVIGATION ATTRIBUTION（同一page render時のみ） | 同上。**別セッション・別日にShrine Detailへ再訪問してReflectionを書いた場合はMEASUREMENT GAP** — URLに`ctx=compass`が残らないため`source`は正しく`"shrine_detail"`にfallbackする。これは既知の制約であり、永続化で解消しない（PR-Cのスコープ外） |

Compass runtimeは引き続きephemeral。DB change・migration・Compass History・
Personal Continuityは本PRで一切実装しない。

## Privacy

上記イベントへ生年月日、緯度・経度、住所・駅名等のraw origin、相談文・自由入力を
送信してはならない。許可するCompass入力由来propertyはcanonical purpose slug、
coarseな`origin_mode`、`has_birthdate`のみである。

## Persistence boundary

DB change、migration、Compass Historyは作成しない。Recommendation InstanceはAPI
レスポンスと遷移URLに限定したanalytics contextである。
