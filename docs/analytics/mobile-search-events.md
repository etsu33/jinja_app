> **Status: Active / Contract**

# Mobile Search導線のイベント契約

Mobile／Expo WebのHome→Search入口、Search画面、神社一覧・人気の神社・地図(Marker/選択カード)からの神社詳細遷移、および神社詳細の外部経路CTAを対象とするEvent契約を管理する。実装は`apps/mobile/lib/searchAnalytics.ts`を正本とし、送信はMobile既存の`track()`パイプライン(`apps/mobile/lib/analytics.ts`)へ委譲する。

`shrine_card_click`・`route_open`はWeb版(`apps/web/src/lib/analytics/searchEvents.ts`)と同一のEvent名を再利用する。Web側にこれらのEvent専用のActive契約文書は存在しないため(実装コードのみが正本)、本書はMobile側の発火条件・Payloadのみを規定し、Web側の実装・契約は変更しない。

| Event | 発火条件 | Payload | 重複の単位 |
| --- | --- | --- | --- |
| `search_entry_click` | Homeの「神社を地図・一覧から探す」CTAを押した操作 | `source: "home"`, `platform: "mobile"` | クリックごと |
| `search_screen_view` | Search画面(`/search`)がマウントされたとき | `source: "mobile_search"`, `platform: "mobile"` | 画面マウント中に1回(`React.useEffect`の空配列依存で再レンダーでの重複を防ぐ) |
| `shrine_card_click` | 神社一覧・人気の神社・地図選択カードのいずれかから、神社詳細への遷移操作を行ったとき(カードの単なる表示では発火しない) | `source`(`"mobile_search"` \| `"map"`), `shrineId`, `position`(`"list"` \| `"popular"` \| `"map"`), `platform: "mobile"` | 遷移操作ごと |
| `map_marker_select` | Marker(Native/Web)、Native座標欠損リスト、Web fallback一覧のいずれかで神社を選択した操作(神社詳細への遷移ではない) | `source: "map"`, `shrineId`, `position: "map"`, `platform: "mobile"` | 選択操作ごと(同じ神社の再選択も1回として送る) |
| `route_open` | 神社詳細画面の外部経路CTA(Googleマップ起動)を押した操作 | `source: "shrine_detail"`, `shrineId`, `routeTarget: "google_maps"`, `platform: "mobile"` | クリックごと |

## `position`の扱い(Webとの差分)

Web版`SearchAnalyticsPayload`の`position`型は`"hero_primary" | "compact" | "map" | "list"`であり、`"popular"`を含まない。Mobile側のSearch画面には「人気の神社」という、Web側に存在しない独立セクションがあるため、Mobile専用の`position: "popular"`を追加する。

- `shrine_card_click`のEvent名自体はWebと共通のまま再利用する
- `position`の値は、Webの既存3値(`hero_primary`/`compact`/`map`/`list`のうちMobileで使うのは`map`/`list`)に`popular`を追加した形で送信する
- Web側の型定義・実装は変更しない(`SearchAnalyticsPayload`は`[key: string]: SearchAnalyticsPrimitive`という索引シグネチャを持ち、追加のprimitive値を許容する構造のため、Mobileからの`position: "popular"`送信はWeb側の契約を破壊しない)

## `map_marker_select`と`shrine_card_click`の分離

地図上でMarker(または座標欠損リスト、Web fallback一覧)を選択する行動と、選択後に神社詳細へ進む行動は別行動として扱う。

- Markerや地図内一覧を選んだだけでは`map_marker_select`のみを送信し、`shrine_card_click`は送らない
- 選択カードの「詳細を見る」を押した時点で`shrine_card_click`(`position: "map"`)を送信する
- 両者が同時に発火することはない(選択操作と遷移操作は別のUI操作である)

## `route_open`のWeb契約との一致

`apps/web/src/components/shrine/GoogleMapRouteLink.tsx`の`route_open`は`{source: "shrine_detail", routeTarget: "google_maps", shrineId, threadId, historyTheme, ctx}`を送信する。Mobileは`threadId`・`historyTheme`・`ctx`をWeb固有Payloadとして送信せず、`source`・`shrineId`・`routeTarget`のみをWebと同じ意味・同じ値で送信する。

`apps/mobile/lib/shrineInteractions.ts`の`trackShrineRouteOpen`(Backend `/shrine-interactions/`へのPOST)は本契約と別系統であり、本書の対象外とする。両者は同じユーザー操作から呼ばれるが、送信先(PostHog系 / Backend保存系)が異なるため重複計測とはみなさない。

## 神社詳細への入口source

`apps/mobile/app/shrines/[id].tsx`の`trackShrineDetailView`は、入口(神社一覧/人気の神社/地図/コンシェルジュ等)によらず`source: "mobile_shrine_detail"`固定のままとする(変更しない)。入口の識別は、Search側で発火する`shrine_card_click`・`map_marker_select`の`position`で行う。神社詳細画面表示イベント自体の入口別source識別は、今回のスコープに含めない(`docs/audit/mobile-user-flow-inventory.md` 9節・14節、`docs/product/mobile-user-flow.md` 9節を参照)。

## 禁止属性

次の値はEvent名を問わず送信しない。

- 相談文、検索語、自由入力条件
- 住所、駅名、都道府県名、緯度・経度
- 誕生日、参拝予定日
- style URL、APIキー、MapTilerキー
- Google MapsのURL全文
- ユーザー名、メールアドレス、トークン、Cookie
- APIレスポンス全文、Recommendation本文、`reasonFacts`全文

`shrineId`・`source`・`position`・`routeTarget`・`platform`のみを許可する。

## Payload型

- primitive型(string/number/boolean)のみを許可する
- nested object・配列を送らない
- `null`/`undefined`は送信前に除外する(`apps/mobile/lib/analytics.ts`の`serializeAnalyticsPayload`が構造的に担う)

## 重複防止

- `search_screen_view`は画面マウント時の`useEffect`(空配列依存)でのみ発火し、再レンダーでは発火しない
- `map_marker_select`と`shrine_card_click`(`position: "map"`)は別Event・別UI操作であり、同じ操作で二重発火しない
- `shrine_card_click`は「一覧」「人気の神社」「選択カード」のいずれか1つのUI要素からのみ発火し、同一クリックで複数箇所から発火しない
- `route_open`(本契約、PostHog系)と`trackShrineRouteOpen`(Backend `/shrine-interactions/`POST系)は送信先が異なる別系統として扱い、本書では重複とみなさない

## 変更ルール

- Event名またはPayloadを変更する場合は、`apps/mobile/lib/searchAnalytics.ts`と本書を同じPRで更新する
- `position`に新しい値を追加する場合は、Web側の`SearchAnalyticsPayload`型と意味が衝突しないことを確認したうえで本書へ追記する
- 本書はMobile Search導線のEvent契約のみを管理する。Web側の実装・契約(`apps/web/src/lib/analytics/searchEvents.ts`)は変更しない
