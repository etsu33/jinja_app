# 座標未取得神社の経路案内・横断監査（2026-11-20）

## 範囲・正本

- 正本：`develop` の実装（監査時点）および本PRの差分
- 対象：Web Nearby / 神社詳細 / Compass、モバイル検索地図
- 非対象：ランキング、座標の捏造、DB更新、Compass Public Projectionの契約変更
- 実データ上の契機：徳島県の正八幡神社（阿南市）・天村雲神社・建布都神社・坂本八幡神社は座標未取得として登録管理。共有シートのIDを本番DBのShrine.idと同一視しない。

## 現行動作の証拠と判定

| 経路 | 現行の実装 | 判定 |
| --- | --- | --- |
| モバイル検索地図（Native/Web） | `apps/mobile/lib/shrineMap.ts` が座標欠損をnullに正規化し、`ShrineSearchMap.native.tsx` / `ShrineSearchMap.web.tsx` が `hasValidCoordinates` でMarkerを絞る。座標なし神社はリストに残す。 | マーカー欠損は防止（既存テストあり） |
| Web神社詳細 | `apps/web/src/app/shrines/[id]/page.tsx` は `toValidDestinationCoords` に失敗すれば `googleDirHref = null`。住所や名前へfallbackしない。 | 座標欠損による誤経路を防止（既存テストあり） |
| Web Nearby | `NearbyShrineCardListClient.tsx` は従来、座標欠損でも `buildGoogleMapsDirUrl` が住所/名前にfallbackしていた。 | **今回修正**：DB-backed（`shrine_id` 有）で座標不正・欠損なら経路CTAを抑止。Google Places-only候補は既存のfallbackを維持。 |
| Compass候補カード | `CompassRecommendationsSection.tsx` が住所→名前で経路生成。 `backend/temples/api/compass_public_projection.py` のallowlistは座標、経路可否を公開していない。 | **未解決**：座標欠損かどうか区別不能。仕様決定待ち。 |
| GoogleMapRouteLink | 渡されたHTTPS URLを開く汎用アクション。自前でShrineの座標・認証済みアンカーを判定しない。 | 呼び出し元での制御が必要。 |

## 本PRの狙いと検証ケース

Web Nearbyの`shrine_id`を持つ登録済み神社について、欠損・片側欠損・WGS84範囲外の場合は経路CTAを作成しない。既存の正常な座標の経路と、`shrine_id`を持たないGoogle Places検索候補のaddress/name fallbackは変更しない。

回帰テスト追加：
- `shrine_id`あり・両方null・住所あり → 経路ボタンなし
- `shrine_id`あり・片側null / 範囲外 → 経路ボタンなし
- `shrine_id`あり・有効緯度経度 → 座標destinationの経路ボタンあり
- `shrine_id`なしのGoogle Places候補 → 既存の住所/名前fallbackテストを維持

テスト完了判定はCIの実行結果を確認後に行う。ファイル編集だけではPASSとしない。

## Mother Shipへ差し戻す仕様判断

### Compassの経路許可条件（未決定）

Compass Monthly Public Projectionは、あえて`latitude` / `longitude`を公開しない契約。現状では、住所や名前を持つが参拝アンカー未確定の登録神社を、UIから識別できない。

選択肢：
- **A**：Backendで公的・現行Sourceに裏付けられた`route_eligible`と参拝先アンカーを公開し、Compass側はtrueの場合のみ経路CTAを表示する。
- **B**：Compassから直接経路CTAを外し、座標を検証する神社詳細の導線に一本化する。
- **C**：現状の住所・名称fallbackを維持し、座標未取得神社への誤案内リスクを明示的に受け入れる。

本PRはA/B/Cの最終判断をしない。Compass Public Projection / OpenAPI / Backend推薦ロジックを無断変更しない。A/Bの判断が確定するまで、**全導線の経路安全性を保証したとは記録しない**。

## Source/Contract注意

`docs/knowledge/shrine-position-contract.md` では `Shrine.latitude/longitude` をVisitor / Navigation Anchorと定義し、行政地番・法人住所・単なる山域中心などは自動で採用しない。座標が形式上有効でも、位置QAや参拝経路QAのPASSを自動的に意味しない。

## 次の実装PR

1. Mother ShipがCompass A/B/Cを確定。
2. Codexが対象API/フロント/テストをPR単位で実装。
3. 正常座標、座標欠損、同名別社、位置QA保留、GPS値域エラーを横断テスト。
4. CIと人手の経路リンクQAを通過したら完了。
