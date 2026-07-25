# Web地図ライブラリ比較監査(Google Maps JavaScript API / MapLibre GL JS)

## 1. 目的

KAMI MUSUBIのWeb版神社検索画面(`apps/mobile`のExpo Router Web出力、`ShrineSearchMap.web.tsx`)へ実際の地図表示を実装する前に、候補となる2つのWeb地図ライブラリ

- Google Maps JavaScript API
- MapLibre GL JS

を、現在のリポジトリ構成・既存Mobile地図実装・費用・運用負荷・アクセシビリティ・将来拡張の観点で比較し、採用判断に必要な事実と条件を文書化する。

このPRでは地図ライブラリを導入しない。最終採用判断も行わない。推奨の方向性と、判断のために母艦(プロジェクトオーナー/意思決定者)が別途決める必要がある事項を整理して差し戻す。

## 2. 対象範囲

- 対象: Web版(`apps/mobile`のExpo Router Web出力)の神社検索地図表示
- 対象外: Mobile(iOS/Android)の`react-native-maps`実装、Backend API、`apps/web`(Next.js)の他機能
- 比較候補: Google Maps JavaScript APIとMapLibre GL JSの2つのみ。他候補(Leaflet単体、Mapbox GL JS等)は本監査の対象に加えない

## 3. 現行実装

以下のファイルを実際に読み、現状を確認した(コミット`cb8bdf4d`時点)。

### 3.1 Web fallbackの構造(`apps/mobile/components/search/ShrineSearchMap.web.tsx`)

- 地図タイルは描画していない。`react-native-maps`をimportせず、`View`/`Pressable`/`Text`のみで構成された「位置情報のある神社を一覧から選択できる」旨のfallback UIになっている
- `points`配列を受け取り、`Pressable`のリストとして描画。選択中の項目には「選択中」ラベルとborder色(`theme.borderGold`)の両方を付与し、色だけに依存しない選択表現になっている
- `accessibilityRole="button"` / `accessibilityLabel`(選択時は「〜を選択、選択中」) / `accessibilityState={{ selected }}` を設定済み

### 3.2 Native実装(`apps/mobile/components/search/ShrineSearchMap.native.tsx`)

- `react-native-maps`の`MapView`/`Marker`を使用。有効座標(`hasValidCoordinates`)を持つ点のみMarker化し、座標欠損点は地図下の別リスト(「位置情報のない神社」)として選択可能にしている
- `MapView`に`key`を設定しておらず、`initialRegion`は`points`にのみ依存する`useMemo`で計算している。選択変更のたびにMapViewがremountされたりviewportが初期化されたりしない
- `zoomEnabled`/`scrollEnabled`/`pitchEnabled`/`rotateEnabled`は明示指定なし(react-native-maps既定値=true)。ピンチ拡大縮小・ドラッグは制限していない

### 3.3 Search画面(`apps/mobile/app/search/index.tsx`)

- `selectedShrineId: string | null`のみをSearch画面の状態として保持し(`useState`)、選択中の神社オブジェクトは`mapPoints.find(...)`で導出している。選択状態を二重管理していない
- `ShrineSearchMap`に`points={mapPoints} selectedId={selectedShrineId} onSelect={setSelectedShrineId}`を渡し、選択カード(`SelectedShrineMapCard`)は`selectedShrineId`から導出した神社を表示
- 神社一覧(`visibleShrines`)の各カードに、`mapPoints`に同一idが存在する場合のみ有効化される「地図で選択」ボタンを追加済み(カード本体の詳細遷移とは独立)

### 3.4 selectedShrineIdの正本

`apps/mobile/app/search/index.tsx`の`useState<string | null>`が唯一の正本。Native/Web/一覧のいずれの操作もこの状態を更新するだけで、他のコンポーネントは全て導出値を参照する。

### 3.5 `ShrineSearchMapProps`(`apps/mobile/lib/shrineMap.ts`)

```ts
export type ShrineSearchMapProps = {
  points: ShrineMapPoint[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};
```

NativeとWebの両コンポーネントがこの共有型をそのまま使用しており、Props契約の一致は`pnpm typecheck`で構造的に保証されている。

### 3.6 有効座標判定と座標欠損時の挙動(`apps/mobile/lib/shrineMap.ts`)

```ts
export type ShrineMapPoint = {
  id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  address?: string;
  imageUrl?: string;
};

export function hasValidCoordinates(
  point: ShrineMapPoint,
): point is ShrineMapPoint & { latitude: number; longitude: number } {
  return point.latitude !== null && point.longitude !== null;
}
```

`toShrineMapPoints`は、id・nameが欠けている項目のみ除外する。座標が欠損・不正(NaN/Infinity/範囲外/片方のみ有効)な項目は除外せず、`latitude`/`longitude`を`null`にしたうえで一覧・選択・詳細遷移の対象に残す。Marker表示可否だけを`hasValidCoordinates`で別途判定する構造になっている。将来Web側に実地図を導入する場合も、この関数と型をそのまま再利用できる。

### 3.7 Webビルド方式・SSR/CSR境界

- `apps/mobile/package.json`の`"deploy": "npx expo export -p web && npx eas-cli@latest deploy"`から、Web版はExpo Routerの静的書き出し(`expo export -p web`)によって生成され、EAS経由でデプロイされている
- Next.jsのようなサーバーサイドレンダリング(リクエストごとのSSR)は行っていない。事実上クライアントサイドレンダリング(静的書き出し+ブラウザ実行)であり、Next.js特有の「サーバー環境で`window`が存在しない」制約は本アプリのWeb版には直接あてはまらない
- 別途`apps/web`(Next.js、Vercelでホスティングされている: `docs/infra/env_policy.md`等に記載あり)が存在するが、これは神社検索地図とは別画面群であり、本監査のWeb版はこのNext.jsアプリではない。将来Next.js側にも同種の地図が必要になった場合は、SSR環境での読込方式(`next/dynamic`によるクライアント限定読込など)を別途検討する必要がある

### 3.8 環境変数の既存命名規則

- Mobile(クライアントに露出する値): `EXPO_PUBLIC_*`(例: `EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_POSTHOG_KEY`, `EXPO_PUBLIC_POSTHOG_HOST`)
- Backend(サーバー専用値): プレフィックスなし。ルートの`.env.example`に既に`GOOGLE_PLACES_API_KEY=`と`GOOGLE_MAPS_API_KEY=`が空値のプレースホルダーとして存在する(`backend/temples/signals.py`, `backend/temples/views.py`で使用されており、神社の住所・写真等をサーバー側でGoogle Places APIから取得する用途)
- **重要な注意点**: 既存の`GOOGLE_MAPS_API_KEY`/`GOOGLE_PLACES_API_KEY`はBackendのサーバーサイド専用キーであり、ブラウザに露出させるWeb地図表示用のクライアントキーとは権限・制限方法(HTTP referrer制限 vs サーバーIP制限)が異なるべきものである。Web地図を導入する場合、既存のBackendキーを転用せず、`EXPO_PUBLIC_GOOGLE_MAPS_WEB_API_KEY`のような別名・別キーを新設する前提で設計する必要がある(本PRでは環境変数を追加しない)

### 3.9 CI/ビルド設定

- `.github/workflows/mobile-ci.yml`: `apps/mobile/**`または`packages/shared/**`変更時にPR/push契機で実行。`pnpm install --frozen-lockfile --ignore-workspace` → `pnpm test` → `pnpm typecheck`
- `pnpm-workspace.yaml`(ルート)は`apps/mobile`を明示的に除外(`"!apps/mobile"`)しており、`apps/mobile`は独自の`pnpm-lock.yaml`を持つ独立したワークスペースである。ルートの`package.json`/`pnpm-lock.yaml`を変更せずとも、`apps/mobile`側の依存関係だけで地図ライブラリ選定を進められる
- `.github/workflows/deploy.yml.disabled`は無効化されており、現状Web版の自動デプロイはCIに組み込まれていない(手動`pnpm deploy`相当と推測されるが、本監査では深追いしない)

## 4. 必須要件(前提の再確認)

- WebとMobileで地図タイルの完全一致ではなく、**操作契約の一致**(`ShrineSearchMapProps` = `points`/`selectedId`/`onSelect`)を優先する
- `selectedShrineId`正本・座標欠損神社の一覧残存・詳細遷移の維持は、地図ライブラリ選定に関わらず変更しない前提とする
- Backend API契約・Mobile地図・`ShrineSearchMap.web.tsx`の現行挙動は本PRでは変更しない

## 5. Google Maps JavaScript API調査

公式資料(developers.google.com)およびGoogleがWeb検索結果に提供する一次情報を確認した。料金は2026年7月時点の記載。

### 5.1 料金(Dynamic Maps)

[Maps JavaScript API Usage and Billing](https://developers.google.com/maps/documentation/javascript/usage-and-billing) / [Google Maps Platform core services pricing list](https://developers.google.com/maps/billing-and-pricing/pricing)によれば、Dynamic Maps(地図の読み込み=マップロード単位で課金)の料金は以下(Essentialsティア、1,000ロードあたり):

| ロード数(月間) | 単価 |
| --- | --- |
| 0〜10,000 | 無料 |
| 10,001〜100,000 | $7.00 |
| 100,001〜500,000 | $5.60 |
| 500,001〜1,000,000 | $4.20 |
| 1,000,001〜5,000,000 | $2.10 |
| 5,000,000超 | $0.53 |

### 5.2 月間無料利用枠と2025年3月の制度変更

[Changes to Google Maps Platform automatic volume discounts, monthly credit, and services transitioning to Legacy status](https://developers.google.com/maps/billing-and-pricing/faq)によれば、2025年3月1日付で以下の変更が行われている:

- 全SKU共通だった月額$200クレジットは廃止され、SKUごとの個別無料枠(Essentialsティアで月10,000イベント)に置き換わった
- 無料枠はSKUごとに独立しており、プールされない(例: Dynamic Mapsの無料枠を使い切ってもGeocodingの無料枠には影響しない、が合算での相殺もできない)
- 自動ボリューム割引の適用範囲が月間100,000イベント超から500万イベント超まで拡大された
- 実務上の影響として、単一SKUで月10,000ロードを超えた時点で他のSKUが未使用でも課金が発生するようになった(旧$200クレジットのプール共有時とは挙動が異なる)

KAMI MUSUBIの検索画面はユーザーが検索するたびに地図を1回ロードする設計が想定されるため、月間ユーザー数×平均検索回数がおおよそ10,000ロードを超えるかどうかが無料/有料の分岐点になる。

### 5.3 APIキー・Billing有効化の必要性

[How to Get a Google Maps API Key](https://scrap.io/guide-google-maps-api-key)等の解説記事および[Google Maps Platform FAQ](https://developers.google.com/maps/faq)の記載を踏まえると:

- 標準のAPIキーを発行するには、Google Cloudの課金アカウント(有効な支払い方法=クレジットカード等)の登録が必須。無料枠内であっても、支払い方法未登録の状態ではAPIキーが機能を停止する
- 例外として、課金アカウント不要の「[Maps Demo Key](https://mapsplatform.google.com/maps-demo-key/)」が用意されているが、日次上限があり検証・プロトタイプ用途に限られ、本番運用には使えない

→ Google Maps採用は、本番運用の時点で**運用チームがGoogle Cloudの請求管理(支払い方法登録・予算アラート設定)を許容できるか**が前提条件になる。

### 5.4 HTTP referrer制限

[Adding restrictions to API keys](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys)によれば、Webアプリ向けにはHTTPリファラー制限でキーの利用ドメインを絞り込める(ワイルドカード対応、`https://`/`http://`のみサポート)。ただし、プライバシー保護のためモダンブラウザがクロスオリジンリクエストでReferrerヘッダーを削減・省略するケースがあり、サイトの`referrer-policy`設定によって制限の効き方が変わる点に注意が必要。

### 5.5 Marker / Advanced Marker

[Migrate to advanced markers](https://developers.google.com/maps/documentation/javascript/advanced-markers/migration)によれば:

- `google.maps.Marker`は2024年2月21日(v3.56)付で非推奨(deprecated)。廃止時期は未定だが、新規の不具合は今後修正されない方針
- 後継の`google.maps.marker.AdvancedMarkerElement`が推奨。ただし利用には`marker`ライブラリの追加読み込みと、地図初期化時の`mapId`指定が必須
- 現時点でGoogle Maps採用を選ぶ場合、最初から`AdvancedMarkerElement`で実装するのが妥当(レガシーMarkerでの新規実装は推奨されない)

### 5.6 Popup / InfoWindow

`InfoWindow`クラスが標準搭載されており、Marker押下時の吹き出し表示に利用できる(本アプリでは既に選択カード=`SelectedShrineMapCard`がその役割を担っているため、InfoWindowを使わずMarker押下→既存の選択カード更新、という構成も可能)。

### 5.7 Marker clustering

Google本体には含まれておらず、別ライブラリ[`@googlemaps/markerclusterer`](https://www.npmjs.com/package/@googlemaps/markerclusterer)(npm別パッケージ)が必要。今回の要件(Markerクラスタリングを追加しない)には該当しないが、将来拡張の論点として記録する。

### 5.8 ホイールズーム・ドラッグ操作

標準の`MapOptions`でホイールズーム(`scrollwheel`)・ドラッグ(`draggable`/`gestureHandling`)を制御可能。デフォルトで両方とも有効。

### 5.9 キーボード操作・スクリーンリーダー対応

Google Maps JavaScript API自体はMarker/ズームコントロール等にキーボード操作(Tab/矢印キー)とARIA属性を組み込んでいるが、詳細な適合レベル(WCAG準拠度)を明記した単一の公式ページは今回の調査では特定できなかった。Advanced Markerは独自のHTML/CSS要素として実装するため、`aria-label`等をアプリ側で明示的に付与する必要がある(レガシーMarkerより開発者側の実装負荷がやや高い)。

### 5.10 Routes / Places連携

同一プラットフォーム(Google Maps Platform)内のAPIとして、Routes API(経路案内)・Places API(場所検索・詳細情報)がある。[Places Details (Advanced)は1,000リクエストあたり$32](https://www.mapsi.dev/google-maps-api-pricing)、Route Matrix APIは要素(origin-destinationペア)あたり課金など、Maps JavaScript APIとは別建てのSKU・料金体系。既にBackendが`GOOGLE_PLACES_API_KEY`でPlaces APIを利用しているため(3.8節)、同一ベンダー内で将来Routes/Places連携する場合の統合コストはMapLibre側より低いと考えられる。

### 5.11 SSR環境での読込方式

[Load the Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/load-maps-js-api)および[@googlemaps/js-api-loader](https://www.npmjs.com/package/@googlemaps/js-api-loader)によれば、`loading=async`パラメータ付きスクリプトタグ、または`@googlemaps/js-api-loader`パッケージによる動的import(Promiseベース)が推奨されている。KAMI MUSUBIのWeb版はSSRではなく静的書き出し+CSRのため(3.7節)、この論点は他社のNext.js SSR環境ほど重要ではないが、`window`が存在しないビルド時評価を避けるためコンポーネントのマウント後に読み込む設計は引き続き必要。

### 5.12 ロード失敗時の扱い

`window.gm_authFailure`というグローバルコールバックが用意されており、APIキー不正・課金未設定等の認証エラー発生時に呼び出される([Error Messages](https://developers.google.com/maps/documentation/javascript/error-messages))。ネットワーク起因の読込失敗は、`@googlemaps/js-api-loader`のPromiseがreject/timeoutすることで検知できる。いずれもアプリ側でcatchし、既存のWeb fallback一覧UIへ切り替える設計が必要(完全な地図表示保証はできない)。

## 6. MapLibre GL JS調査

### 6.1 OSSライセンス

[MapLibre GL JS LICENSE.txt](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt)により3条項BSDライセンス。Mapbox GL JSが2020年12月に非OSSライセンスへ移行する直前のBSDライセンス版(v1.13)をLinux Foundation傘下でハードフォークしたもの。クローズドソースSaaSへの組み込みやモバイルWebView内での利用に法的制約がない(著作権表示の保持のみが条件)。

### 6.2 MapLibre本体とタイル提供元の責務分離

MapLibre GL JSは「地図タイルを描画するクライアントライブラリ」であり、タイルデータそのものは提供しない。地図を表示するには、別途ベクタータイルを配信する`style URL`(styleスペック準拠のJSON、タイルソースを指す)が必須。つまりMapLibre GL JS単体を導入しても地図は表示できず、**タイル提供元の選定が別途不可欠**(7節で詳述)。

### 6.3 Marker

`Marker`クラスが標準搭載。HTML要素ベースで、カスタムアイコン・DOM要素を自由に指定できる。

### 6.4 Popup

`Popup`クラスが標準搭載。Marker/クリックイベントに紐づけて吹き出し表示が可能([accessibility issue #360](https://github.com/maplibre/maplibre-gl-js/issues/360)によれば、閉じるボタンの`×`文字をスクリーンリーダーから隠す等の改善が進行中で、細部のアクセシビリティ課題がIssueとして継続的に報告されている)。

### 6.5 Clustering

`GeoJSONSource`に`cluster: true`を指定するだけでクラスタリングが有効化される([Create and style clusters](https://maplibre.org/maplibre-gl-js/docs/examples/create-and-style-clusters/))。内部で[supercluster](https://github.com/mapbox/supercluster)ライブラリを使用しており、追加パッケージのインストールなしにMapLibre本体機能として使える(Google Mapsは別パッケージが必要、6.3節との対比で7節比較表に反映)。

### 6.6 zoom / drag

標準の`MapOptions`で`scrollZoom`/`dragPan`等を制御可能。デフォルトで両方有効。

### 6.7 WebGL要件

[Browser support | MapLibre GL JS | Esri Developer](https://developers.arcgis.com/maplibre-gl-js/browser-support/)等によれば、現行バージョンはWebGL2が必須(WebGL1のみのブラウザは非対応)。[Fallback for disabled webgl (Discussion #4473)](https://github.com/maplibre/maplibre-gl-js/discussions/4473)によれば、**MapLibre GL JS自体には自動フォールバック機構がない**。WebGL非対応環境向けのフォールバックはアプリ側で`maplibregl.supported()`等を使って検知し、実装する必要がある。KAMI MUSUBIは既にWeb fallback UI(一覧表示)を持つため、WebGL非対応時にこの既存fallbackへ切り替える設計は比較的自然に組み込める。

### 6.8 モバイル幅対応

タッチ操作(ピンチズーム・パン)に標準対応しており、レスポンシブなコンテナサイズに追従する。モバイル幅特有の追加設定は不要。

### 6.9 キーボード操作

[KeyboardHandler](https://maplibre.org/maplibre-gl-js/docs/API/classes/KeyboardHandler/)が標準搭載。矢印キーでパン(100px単位)、Shift+矢印でズーム/回転/傾斜操作に対応。

### 6.10 スクリーンリーダー対応

検索結果の要約によれば、組み込みのスクリーンリーダー向けアナウンス・ハイコントラストモード検知・双方向テキストシェーピング(自前のharfbuzz-jsフォーク)を備え、Marker間をTabで移動して読み上げに対応する旨が紹介されている。一方で[WCAG 2.1 Accessibility Evaluation (Issue #53)](https://github.com/maplibre/maplibre-gl-js/issues/53)や[Issue #362](https://github.com/maplibre/maplibre-gl-js/issues/362)のように、`aria-label`と`title`の二重読み上げなど個別の改善Issueが継続的に報告されており、完全なWCAG準拠が保証されているわけではない。

### 6.11 MapLibre Nativeとの関係

[MapLibre Native](https://maplibre.org/projects/native/)はC++で書かれたモバイル向けGPU描画ライブラリで、MapLibre GL JS(Web/JavaScript)とは別プロジェクト。React Native向けには[`@maplibre/maplibre-react-native`](https://github.com/maplibre/maplibre-react-native)(rnmapboxのフォーク、MIT license)があり、これを使えばMobile側もMapLibre Nativeベースに統一できる可能性がある。ただし、現在Mobile側は`react-native-maps`(Apple Maps/Google Mapsのネイティブラッパー)を使用しており、この監査の制約(react-native-mapsの依存を変更しない)によりMobile側の変更は対象外。**「WebをMapLibre GL JSにした場合、将来Mobileも`@maplibre/maplibre-react-native`へ統一できる可能性がある」という将来性の論点としてのみ記録する**(今回は採用・実装しない)。

### 6.12 経路表示に別サービスが必要か

MapLibre GL JS本体にRoutes/Directions相当の機能はない。経路探索が必要な場合はOSRM、Valhalla、GraphHopper等の外部ルーティングサービス(自前ホスティングまたはOpenRouteService等のホスティングサービス)を別途統合する必要がある。

### 6.13 タイル提供元障害時の扱い

MapLibre GL JS自体にタイル提供元の冗長化・自動フェイルオーバー機構は組み込まれていない。単一のタイル提供元がダウンした場合、style URLを切り替えるロジックをアプリ側で実装しない限り地図タイルは表示されない(7節で詳述)。

## 7. タイル提供元の追加論点

MapLibre GL JS採用を選ぶ場合、**タイル提供元の選定が別途・必ず必要**である。本監査では最終選定は行わず、必須条件のみ整理する。

- **public OpenStreetMap tile server(`tile.openstreetmap.org`)を本番の安定基盤として扱わない**: [Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/)により、汎用デフォルト設定・リファラー削除・偽装トラフィック等は予告なくブロックされ得ると明記されている。一括ダウンロードやオフライン用途のプリフェッチも禁止されている。本番のユーザー向けアプリでの常用は同ポリシーの想定外であり、**採用不可**として扱う
- **attribution表示**: OSMベースのタイルは"© OpenStreetMap contributors"等の帰属表示が利用規約上ほぼ必須(提供元ごとに文言・表示要件が異なるため、選定時に個別確認が必要)
- **キャッシュ要件**: 商用タイル提供元の多くはCDN経由でのタイル配信を前提としており、自前キャッシュプロキシを禁止または制限する場合がある(OSMFは自前キャッシュプロキシを推奨していない)
- **referer要件**: Google Maps同様、多くの商用タイル提供元がAPIキー+リファラー制限で利用を制御する
- **SLAの有無**: 無料/低価格ティアでは明示的なSLAがないことが一般的。可用性を契約で担保したい場合は有償プランの契約内容を個別確認する必要がある
- **商用利用条件**: 提供元によって「非商用は無料、商用は要契約」(例: Stadia Maps)、「リクエスト数ベースで無料枠あり、商用も可」(例: MapTiler)、「自前ホスティングなら実質無料」(例: Protomaps/PMTiles)など、モデルが大きく異なる
- **月間料金・使用量上限・APIキー**: 提供元ごとに個別。今回調査した範囲では:
  - MapTilerはクレジットカード登録不要の無料枠(月10万リクエスト程度)があり、Cloudプランは月$29から([MapTiler pricing](https://www.maptiler.com/cloud/pricing/))
  - Stadia Mapsは非商用は無料ティア、商用利用は有償プラン契約が必要([Stadia Maps pricing](https://stadiamaps.com/pricing/))
  - Protomaps/PMTilesは自前のオブジェクトストレージ(S3等)にタイルファイルを置いて配信する方式で、ソフトウェア自体は無料。ホスティングAPIを使う場合は非商用は月100万リクエストまで無料、商用利用はGitHub Sponsors経由で月$14から([Protomaps](https://protomaps.com/))
  - いずれも今回のWebSearch結果に基づく概算であり、正式な料金・利用規約は契約前に各社の最新公式ページで再確認が必要(本監査では確定情報として扱わない)
- **プロバイダ切替可能な構造**: MapLibre GL JSはstyle URLを差し替えるだけでタイル提供元を切り替えられるため、特定ベンダーへの技術的ロックインは小さい。ただし、切替時のスタイル(配色・注記言語等)の見た目差異は提供元ごとに発生する

**具体的なタイル提供元の最終選定は本PRの対象外とする。MapLibre GL JS採用を進める場合、タイル提供元の選定・契約・料金確認を別タスクとして必ず実施する必要がある。**

## 8. 比較表

| 比較項目 | Google Maps JavaScript API | MapLibre GL JS |
| --- | --- | --- |
| 導入速度 | 比較的速い(単一ベンダーでMarker/Popup/UIが完結) | 本体は速いが、タイル提供元選定が別途必要なため実質的な導入速度はタイル提供元契約に依存 |
| 追加依存 | `@googlemaps/js-api-loader`(推奨)、クラスタリングには`@googlemaps/markerclusterer`が別途必要 | `maplibre-gl`本体のみでMarker/Popup/クラスタリングが完結。タイル提供元のSDK/契約が別途必要な場合あり |
| SSR/Next.js互換 | `@googlemaps/js-api-loader`の動的import推奨。本アプリはCSR静的書き出しのため制約は小さい | クライアント限定読込が前提(WebGL/`window`依存)。本アプリはCSR静的書き出しのため制約は小さい |
| APIキー | 必須(Google Cloud発行) | MapLibre本体は不要。タイル提供元によっては必要 |
| Billing設定 | 必須(無料枠内でも支払い方法の登録が必要) | MapLibre本体は不要。タイル提供元によっては必要 |
| 無料利用枠 | Dynamic Maps: 月10,000ロードまで無料(SKUごと個別、2025年3月以降) | MapLibre本体は無料(OSS)。タイル提供元ごとに個別(7節) |
| 従量課金 | 10,001ロード以降$7/1,000〜(規模で逓減、5.1節) | MapLibre本体は無課金。タイル提供元の従量課金に依存 |
| 料金監視 | Google Cloud Billingの予算アラート等で監視可能(運用チームの請求管理体制が前提) | タイル提供元ごとのダッシュボード/APIキー単位で個別に監視が必要 |
| Marker | 標準搭載。ただし`Marker`は非推奨、`AdvancedMarkerElement`への移行が推奨(要`mapId`+`marker`ライブラリ) | 標準搭載(`Marker`クラス、非推奨なし) |
| Popup | 標準搭載(`InfoWindow`) | 標準搭載(`Popup`)。細部のa11y改善が進行中(Issueあり) |
| clustering | 別パッケージ`@googlemaps/markerclusterer`が必要 | 本体機能(`GeoJSONSource`の`cluster: true`)で完結 |
| zoom | 標準対応(`scrollwheel`等で制御可) | 標準対応(`scrollZoom`等で制御可) |
| drag | 標準対応(`draggable`/`gestureHandling`) | 標準対応(`dragPan`) |
| キーボード操作 | Marker/コントロールにTab・矢印キー対応(詳細な公式適合表は未特定) | `KeyboardHandler`で矢印キーパン・Shift+矢印でズーム/回転/傾斜に対応(公式ドキュメントあり) |
| スクリーンリーダー | ARIA属性を組み込み済みだが、単一の公式適合表は今回特定できず | 組み込みのスクリーンリーダー対応ありと紹介されるが、個別のa11y Issueも継続報告あり。WCAG完全準拠の明言はなし |
| モバイル幅 | 標準でレスポンシブ対応 | 標準でレスポンシブ対応(タッチジェスチャー含む) |
| 独自デザイン | Advanced Markerで柔軟なHTML/CSSカスタムが可能。地図タイル自体のスタイルカスタムはCloud Console経由 | style JSON(vector tile style spec)でタイルの配色・注記まで自由にカスタム可能。デザイン自由度は高い |
| attribution | Googleロゴ/利用規約リンクの表示が必須(標準UIに組み込み済み) | タイル提供元ごとに個別のattribution文言が必要(7節) |
| タイル管理 | Google側が一元管理。アプリ側での管理不要 | タイル提供元の選定・契約・キー管理・障害対応をアプリ側/運用チームが担う |
| 障害時fallback | `gm_authFailure`等でエラー検知可能。既存Web fallback一覧へ切替える設計が必要 | `maplibregl.supported()`等でWebGL非対応を検知、既存Web fallback一覧へ切替える設計が必要。タイル提供元障害はstyle URL切替をアプリ側で実装しない限り対応不可 |
| Places連携 | 同一プラットフォーム内で連携しやすい(BackendのGoogle Places API利用実績あり、3.8節) | 別途外部サービスとの統合が必要 |
| Routes連携 | 同一プラットフォーム内のRoutes APIで連携可能(SKU別課金) | 別途OSRM/Valhalla等の外部ルーティングサービスが必要 |
| ベンダーロックイン | Google Cloudプラットフォームへの依存度が高い(APIキー・課金・利用規約が単一ベンダー) | MapLibre本体はロックインなし(BSD、style URL差し替え可)。ただし選んだタイル提供元への依存は残る |
| 将来のNative統一可能性 | react-native-mapsのAndroid実装は内部的にGoogle Maps SDKを使用しており親和性はあるが、Web/Native間のコード共有は基本的にない | `@maplibre/maplibre-react-native`によりMobile側もMapLibre Nativeへ将来統一できる可能性がある(今回は未着手・将来論点、6.11節) |
| 保守工数 | APIキー・課金設定・Advanced Marker移行など、Google Cloud側の運用知識が必要 | タイル提供元の契約管理・style更新・a11y Issue追随など、MapLibreエコシステム側の運用知識が必要 |
| KAMI MUSUBIとの適合性 | 9節で詳述 | 9節で詳述 |

## 9. KAMI MUSUBIへの適合評価

- 現状の`ShrineSearchMapProps`(`points`/`selectedId`/`onSelect`)と座標欠損時の一覧残存ロジック(`hasValidCoordinates`)は、どちらのライブラリを採用してもそのまま再利用できる設計になっている。ライブラリ選定はこの契約に影響しない
- Backendは既に`GOOGLE_PLACES_API_KEY`でGoogle Places APIを利用しており(神社の住所・写真取得)、Google Maps Platformとのベンダー関係が既に存在する。この点はGoogle Maps採用側にわずかな優位性がある(契約・請求の一本化)が、Web地図表示用クライアントキーは既存のBackend用キーと権限・制限方式が異なるため、そのまま転用はできない(3.8節)
- KAMI MUSUBIは費用構造が未確定な立ち上げ期のプロダクトであり、月間検索回数(=マップロード数)の見通しが立っていない。Google Maps採用は、月10,000ロードを超えた瞬間に運用チームがGoogle Cloud課金管理を担う体制が前提になる
- Web版は既に「地図が使えなくても一覧で選択・詳細遷移できる」fallback設計になっており(3.1節)、どちらのライブラリを採用しても「地図はあくまで補助UI、一覧が主契約」という現在の設計思想と両立できる
- デザインの自由度(KAMI MUSUBIの世界観に合わせた配色のカスタム地図)を重視する場合はMapLibre GL JSが有利だが、タイル提供元の契約・料金・SLAという追加の意思決定が必要になる

## 10. 推奨案

現時点では、**費用制御とデザイン自由度を優先する場合はMapLibre GL JSが有力である。ただし、本番タイル提供元の契約・料金・SLAが未確定であるため、採用確定には追加判断が必要である。**

Google Maps JavaScript APIを不採用と断定するものではない。以下のいずれかに該当する場合は、Google Maps側を再評価対象とする:

- Places連携(場所検索・詳細情報表示)を早期に導入する場合
- Routes連携(経路案内)を早期に導入する場合
- アクセシブルなMarker実装(公式ドキュメントが明示的に存在する範囲)の実装速度を最優先する場合
- 運用チームがGoogle Cloudの請求管理(支払い方法登録・予算アラート運用)を許容する場合

## 11. 不採用案の理由

本監査ではGoogle Maps JavaScript API・MapLibre GL JSのいずれも「不採用」とは断定していない。参考として、比較対象に含めなかった候補とその理由のみ記録する:

- Leaflet単体: ベクタータイル・WebGL描画を前提としたKAMI MUSUBIの将来的なデザインカスタム要件と比較して機能面で劣後する可能性があり、かつ本監査のスコープ(Google Maps/MapLibreの2択比較)外のため対象外とした
- Mapbox GL JS: 2020年12月にBSDから非OSSライセンスへ移行しており、費用構造がGoogle Mapsに近くなる一方でOSSの利点(MapLibreの主な採用理由)が失われるため、本監査のスコープ外とした

## 12. 母艦判断事項

以下は本監査の範囲外であり、母艦(プロジェクトオーナー/意思決定者)が別途判断する必要がある:

1. **最終ライブラリ採用の意思決定**(Google Maps JavaScript API / MapLibre GL JSのいずれか)
2. MapLibre採用の場合: **タイル提供元の最終選定**(MapTiler / Stadia Maps / Protomaps等、料金・SLA・商用利用条件を契約前に公式ページで最新確認したうえで選ぶ)
3. Google Maps採用の場合: **運用チームがGoogle Cloud課金管理体制(支払い方法登録・予算アラート・月次コスト監視)を持てるか**
4. 想定月間検索回数(マップロード数)の見積もり — Google Maps採用時に無料枠(月10,000ロード)を超える見込みかどうかの判断材料
5. Places連携・Routes連携の導入時期(早期導入する場合はGoogle Maps再評価の理由になる、10節)
6. Web版クライアント向けAPIキーの命名規則確定(`EXPO_PUBLIC_GOOGLE_MAPS_WEB_API_KEY`案など、Backendの既存`GOOGLE_MAPS_API_KEY`と混同しない命名)
7. アクセシビリティ(キーボード操作・スクリーンリーダー)の目標適合レベル(WCAG準拠を必須要件にするか、努力目標にするか)

## 13. 実装PR分割案

最終判断がどちらになっても共通する分割の考え方を提示する(判断確定後、選んだライブラリに応じて詳細化する)。

- **PR-A(基盤)**: 選定ライブラリの依存追加、APIキー/style URLの環境変数追加、`ShrineSearchMap.web.tsx`への最小限のMarker表示実装(既存`ShrineSearchMapProps`契約を維持し、fallback一覧は地図読込失敗時のフォールバックとして残す)
- **PR-B(選択同期)**: 既存の`selectedShrineId`/`onSelect`とMarker選択状態の同期、座標欠損神社の非Marker表示・一覧残存の実装(`hasValidCoordinates`をそのまま流用)
- **PR-C(アクセシビリティ・仕上げ)**: キーボード操作・スクリーンリーダー対応の検証と調整、attribution表示の適合確認、エラー時fallback(認証失敗/WebGL非対応/タイル提供元障害)の実装
- **PR-D(該当する場合のみ)**: Marker clustering、Places/Routes連携等の将来拡張(本監査の制約により今回は含めない)

## 14. 残存リスク

- Google Maps Platformの料金体系は2025年3月に一度大きく変更されており、再変更されるリスクがある。採用確定時点で必ず最新の公式価格ページを再確認する必要がある
- MapLibre採用時のタイル提供元は、無料/低価格ティアでSLAが明示されないことが多く、可用性リスクをアプリ側でどう吸収するか(fallback UIへの切替タイミング等)の設計が別途必要
- OSM public tile serverを開発中に安易に使うと、本番相当のトラフィックパターンで予告なくブロックされるリスクがある(7節)。開発環境でも早期に商用/自前ホスティングのタイル提供元へ切り替える運用が望ましい
- MapLibre GL JSはWebGL2必須であり、WebGL非対応の古いブラウザ・一部の組み込みWebViewでは動作しない。実際のユーザー環境(特にモバイルWebViewからのアクセスがあるか)の分布を確認する必要がある
- Advanced Marker(Google Maps)・MapLibre双方とも、スクリーンリーダー対応の細部は継続的に改善中であり、WCAG準拠を厳密に要求する場合は実装時に個別の受け入れテストが必要
- 本監査はWebSearch/WebFetchによる2026年7月時点の一次情報・要約記事に基づく。契約・実装着手前に、各社公式ページで再度最新情報を確認すること

## 15. 参照した公式資料

- [Maps JavaScript API Usage and Billing](https://developers.google.com/maps/documentation/javascript/usage-and-billing)
- [Google Maps Platform core services pricing list](https://developers.google.com/maps/billing-and-pricing/pricing)
- [Changes to Google Maps Platform automatic volume discounts, monthly credit, and services transitioning to Legacy status](https://developers.google.com/maps/billing-and-pricing/faq)
- [Google Maps Platform pricing overview](https://developers.google.com/maps/billing-and-pricing/overview)
- [Migrate to advanced markers](https://developers.google.com/maps/documentation/javascript/advanced-markers/migration)
- [Marker (deprecated)](https://developers.google.com/maps/documentation/javascript/reference/marker)
- [Adding restrictions to API keys](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys)
- [Google Maps Platform FAQ](https://developers.google.com/maps/faq)
- [Google Maps Platform security guidance](https://developers.google.com/maps/api-security-best-practices)
- [Load the Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/load-maps-js-api)
- [@googlemaps/js-api-loader (npm)](https://www.npmjs.com/package/@googlemaps/js-api-loader)
- [Error Messages | Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/error-messages)
- [Marker Clustering | Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/marker-clustering)
- [@googlemaps/markerclusterer (npm)](https://www.npmjs.com/package/@googlemaps/markerclusterer)
- [Maps Demo Key](https://mapsplatform.google.com/maps-demo-key/)
- [MapLibre GL JS LICENSE.txt](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt)
- [MapLibre GL JS (公式サイト)](https://maplibre.org/projects/gl-js/)
- [Create and style clusters | MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/examples/create-and-style-clusters/)
- [GeoJSONSource | MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/)
- [KeyboardHandler | MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/API/classes/KeyboardHandler/)
- [WCAG 2.1 Accessibility Evaluation (Issue #53)](https://github.com/maplibre/maplibre-gl-js/issues/53)
- [accessibility issue #360(Popup閉じるボタン)](https://github.com/maplibre/maplibre-gl-js/issues/360)
- [accessibility issue #362(aria-label/title重複)](https://github.com/maplibre/maplibre-gl-js/issues/362)
- [Fallback for disabled webgl (Discussion #4473)](https://github.com/maplibre/maplibre-gl-js/discussions/4473)
- [Browser support | MapLibre GL JS | Esri Developer](https://developers.arcgis.com/maplibre-gl-js/browser-support/)
- [Check if WebGL is supported | MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/examples/check-if-webgl-is-supported/)
- [MapLibre Native (公式サイト)](https://maplibre.org/projects/native/)
- [MapLibre React Native (GitHub)](https://github.com/maplibre/maplibre-react-native)
- [Tile Usage Policy | OSMF Operations Working Group](https://operations.osmfoundation.org/policies/tiles/)
- [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/)
- [Stadia Maps pricing](https://stadiamaps.com/pricing/)
- [Protomaps](https://protomaps.com/)
- [PMTiles Concepts | Protomaps Docs](https://docs.protomaps.com/pmtiles/)

## 16. 監査日と確認コミット

- 監査日: 2026-07-25
- ブランチ: `audit/web-search-map-library-selection`
- 現行実装の確認基準コミット: `cb8bdf4d2b68aa6832c4b64deed143b440ae91b9`(develop、PR #2170マージ直後)
- 外部情報の取得日: 2026-07-25(WebSearch/WebFetch実施日。料金・仕様は変更され得るため、実装着手前に再確認すること)
