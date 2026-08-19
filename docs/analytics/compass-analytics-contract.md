# Compass Analytics Contract

> Status: Active

Compass の発見から Recommendation 経由の Shrine Detail 表示までを計測する契約。
Favorite / Visit / Reflection の source 伝播は本契約の対象外（PR-C）である。

## Lifecycle

| event | 用途 | 主なproperty |
|---|---|---|
| `home_compass_entry_click` | HomeからCompassを開く | `source=home` |
| `compass_entry` | Compass表示 | `referrer_source=home\|direct` |
| `compass_result` | Compass request完了 | `result_state`, `purpose`, `origin_mode`, `has_birthdate`, `recommendation_count`, `recommendationInstanceId` |

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

## Privacy

上記イベントへ生年月日、緯度・経度、住所・駅名等のraw origin、相談文・自由入力を
送信してはならない。許可するCompass入力由来propertyはcanonical purpose slug、
coarseな`origin_mode`、`has_birthdate`のみである。

## Persistence boundary

DB change、migration、Compass Historyは作成しない。Recommendation InstanceはAPI
レスポンスと遷移URLに限定したanalytics contextである。
