# MapLibre用本番タイル提供元の比較監査

## 1. 目的

KAMI MUSUBIのWeb版神社検索地図に、Web地図ライブラリとしてMapLibre GL JSを採用する暫定方針([docs/audit/web-search-map-library-selection.md](./web-search-map-library-selection.md)参照)を前提に、本番用タイル提供方式を比較する。比較対象は以下の3系統に限定する。

1. MapTiler Cloud
2. Stadia Maps
3. Protomaps + Cloudflare R2 / Workers

このPRでは契約・APIキー発行・依存追加・Web地図実装のいずれも行わない。採用判断に必要な費用・運用・認証・地図品質・障害対応を文書化するのみに留め、最終採用判断は行わない。第一候補・第二候補と、母艦が別途判断すべき事項を差し戻す。

## 2. 対象範囲

- 対象: Web版神社検索地図(`ShrineSearchMap.web.tsx`)が将来利用する本番タイル提供元の比較
- 対象外: Web地図ライブラリそのものの選定(前回監査で完了、MapLibre GL JSを暫定第一候補として扱う)、Mobile(`react-native-maps`)、Backend API
- 比較候補: MapTiler Cloud、Stadia Maps、Protomaps + Cloudflare R2/Workersの3系統のみ。それ以外(自前サーバーでのOSMタイル生成等)は対象に加えない

## 3. 前提

- Web地図ライブラリはMapLibre GL JSを暫定第一候補とする(最終決定は別途)
- Mobileは`react-native-maps`を維持する(本監査の対象外)
- WebとMobileでは地図タイルの完全一致より操作契約(`ShrineSearchMapProps`)の一致を優先する
- Webには現在、地図タイルを描画しない一覧fallback(`ShrineSearchMap.web.tsx`)が存在する
- `selectedShrineId`・`ShrineMapPoint`・座標欠損時の一覧残存契約(`hasValidCoordinates`)は実装済みであり、タイル提供元選定はこれらに影響しない
- public OpenStreetMap tile server(`tile.openstreetmap.org`)は本番基盤として採用しない(前回監査で確認済み。[Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/)により本番常用は想定外)

## 4. 現行実装

以下を実際に読み、確認した(コミット`a5e9579e`時点、developの`docs/audit/web-search-map-library-selection.md`マージ直後)。

### 4.1 Web fallbackの現行仕様(`apps/mobile/components/search/ShrineSearchMap.web.tsx`)

`react-native-maps`をimportせず、`View`/`Pressable`/`Text`のみで構成。`points`配列を受け取り一覧をPressableとして描画し、選択中項目には「選択中」ラベル+border色の両方で選択状態を示す。地図タイルは一切描画していない(前回監査から変更なし)。

### 4.2 MapLibre導入予定箇所・style URLを注入する場所

`ShrineSearchMap.web.tsx`はコンポーネント内で完結しており、`points`/`selectedId`/`onSelect`という`ShrineSearchMapProps`(`apps/mobile/lib/shrineMap.ts`で定義)以外の外部依存を持たない。MapLibre導入時は、この関数コンポーネント内で`maplibre-gl`の`Map`インスタンスを生成し、`style`オプションへタイル提供元のstyle URLを渡す構成になる想定。style URLの値自体は環境変数(`EXPO_PUBLIC_*`)経由で注入する設計が、既存の`EXPO_PUBLIC_API_BASE_URL`等の命名規則(`apps/mobile/lib/http.ts`)と一貫する。

### 4.3 公開クライアントキーの扱い

`apps/mobile/app.json`の`expo.extra`にはAPIキー相当の値は含まれていない。既存のクライアント公開値は全て`process.env.EXPO_PUBLIC_*`経由(`apps/mobile/lib/http.ts`, `apps/mobile/lib/posthogAnalyticsProvider.ts`)。Web版はExpo Routerの静的書き出し(`expo export -p web`)によるビルドのため、`EXPO_PUBLIC_*`はビルド時にクライアントバンドルへ埋め込まれる。**タイル提供元のキー(APIキーまたはstyle URLに含まれるトークン)も同様にバンドルへ露出する前提で、キー漏洩リスクを設計する必要がある**(認証方式の比較は10節)。

### 4.4 provider障害時のfallback

現状、`ShrineSearchMap.web.tsx`自体が地図タイル未実装のfallback UIであるため、「provider障害時にfallbackへ切り替える」ロジックは実装されていない(実装するものが何もない)。MapLibre導入時は、地図初期化失敗時に既存の一覧UIへ切り替えるロジックを新たに実装する必要がある(13節で共通方針を整理)。

### 4.5 selectedShrineIdとの責務境界

`selectedShrineId`はSearch画面(`apps/mobile/app/search/index.tsx`)の`useState`が正本であり、`ShrineSearchMap`コンポーネントは`selectedId`/`onSelect` propを介して読み書きするのみ。タイル提供元の選定は、この選択状態の管理方式に一切影響しない(どのプロバイダを選んでも`ShrineSearchMapProps`契約は変わらない)。

### 4.6 CI / EAS / Vercel設定

- `.github/workflows/mobile-ci.yml`: `apps/mobile/**`変更時に`pnpm install --frozen-lockfile --ignore-workspace` → `pnpm test` → `pnpm typecheck`を実行。タイル提供元選定はこのCI構成に影響しない
- `apps/mobile/eas.json`: `development`/`preview`/`production`の3ビルドプロファイルが存在する。各プロファイルに`environment`指定があり、EAS側で環境ごとに異なる環境変数値を設定できる仕組みが既にある(開発・Preview・本番でタイル提供元のキーを分離できる土台は存在する)
- Web版のデプロイは`apps/mobile/package.json`の`"deploy": "npx expo export -p web && npx eas-cli@latest deploy"`によるEAS Hostingであり、**Vercelではない**。Vercelは別アプリ(`apps/web`、Next.js)のホスティングに使われている。EAS Hostingにおけるプレビューデプロイ(コミット/ブランチ単位のプレビューURL)の詳細な挙動は、今回のリポジトリ調査だけでは確認できず**未確認**とする
- 上記2点(EAS Web deployのプレビューURL体系、各タイル提供元がEAS Hostingのプレビュードメインをドメイン制限に登録できるか)は、契約前に各社ドキュメントで個別確認が必要

### 4.7 EXPO_PUBLIC_*環境変数の既存命名規則

`EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_POSTHOG_KEY`, `EXPO_PUBLIC_POSTHOG_HOST`の3例が既存。命名は`EXPO_PUBLIC_<サービス名>_<用途>`のパターン。タイル提供元導入時は`EXPO_PUBLIC_MAPTILER_KEY`や`EXPO_PUBLIC_STADIA_MAPS_API_KEY`のような命名が既存規則と一貫する(本PRでは追加しない)。

## 5. 必須要件

- 3系統(MapTiler Cloud / Stadia Maps / Protomaps + Cloudflare)を公式資料に基づき比較する
- public OSM tile serverを比較対象・採用候補に含めない
- MapLibre GL JS本体とタイル提供元を混同しない(前回監査の区分を維持する)
- map sessionとAPI requestを混同しない(6節・8節で定義を明示)
- 商用利用可否を各社の料金ページで確認する
- 料金は公式資料で確認できた範囲のみ記載し、推測は「未確認」とする
- 最終採用は断定しない

## 6. MapTiler Cloud

出典: [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/)(2026年7月時点、直接取得)、[Map usage: Sessions vs requests](https://docs.maptiler.com/guides/maps-apis/maps-platform/what-is-map-session-in-maptiler-cloud/)、[How to protect your map key](https://docs.maptiler.com/guides/maps-apis/maps-platform/how-to-protect-your-map-key/)、[Japan maps in MapTiler](https://docs.maptiler.com/guides/map-tiling-hosting/data-hosting/japan-maps-in-maptiler-cloud/)、[MapTiler support](https://www.maptiler.com/support/)。

| 項目 | 内容 |
| --- | --- |
| Free | $0/月。**5,000 map sessions/月**、100,000 API requests/月、5GBストレージ(1ファイル) |
| Freeの商用利用可否 | **不可**。公式に "testing, personal or non-commercial use" 向けと明記 |
| 月間sessions(Free) | 5,000 |
| 月間API requests(Free) | 100,000 |
| Flex基本料金 | $30/月 |
| Flex included | 25,000 map sessions/月、500,000 API requests/月、10GBストレージ、商用利用可 |
| 超過料金(Flex) | $2.50/1,000 sessions、$0.15/1,000 requests、追加ストレージ$20/月/100GB |
| APIキーの必要性 | 必須 |
| style JSON URL | あり(MapTiler Cloud経由でstyle JSONを発行、MapLibre GL JSから直接参照可能) |
| MapLibre互換性 | 公式にMapLibre GL JSベースの`maptiler-sdk-js`を提供しており互換性あり |
| custom styles | あり(スタイルエディタ経由でカスタム可能) |
| 日本語ラベル | 日本向けストリートマップスタイル(Streets/Gray/Dark)がMIERUNE監修でGSIオープンデータ+OSMを統合して提供されている旨を確認。ラベル言語切替の仕組み(`language`オプション)も公式ドキュメントに存在 |
| attribution | 必須(MapTiler/OSM双方の帰属表示、具体的な文言は契約プラン確認時に個別確認) |
| domain / referrer制限 | "Allowed HTTP origins"(ホワイトリスト方式)で制限可能。Origin/Refererヘッダーを送らないリクエストはOriginが指定されている場合拒否される |
| usage limit | Free/Flexともプラン記載の月間枠あり(表内) |
| hard limit / overage設定 | **Free**: 枠超過でサービス一時停止(アップグレードまで)。**Flex**: hard limitなし、月末に自動で超過分が請求される |
| SLA | Customプランで99.9%稼働率SLA提供。Free/Flexには明記なし |
| support | Basic support(年$10,000、ステータスページ・ドキュメント・Web/メール問い合わせ、1-3営業日目安)、Priority support(24/7ホットライン)、Custom SLA(個別契約) |
| status page | [status.maptiler.com](https://status.maptiler.com/)あり |
| cache条件 | 未確認(公式資料でキャッシュ可否・条件を明記したページを本監査では特定できず) |
| provider障害時の挙動 | 未確認(自動フェイルオーバー・代替エンドポイントの明記なし) |

## 7. Stadia Maps

出典: [Stadia Maps pricing](https://stadiamaps.com/pricing/)(2026年7月時点、直接取得)、[Authentication](https://docs.stadiamaps.com/authentication/)、[Quickstart: MapLibre GL JS](https://docs.stadiamaps.com/tutorials/vector-maps-with-maplibre-gl-js/)、[Map Style Library](https://docs.stadiamaps.com/themes/)、[Legally Required Attribution](https://docs.stadiamaps.com/attribution/)、[Stadia Maps Status](https://status.stadiamaps.com/)。

| 項目 | 内容 |
| --- | --- |
| Free | $0/月。**200,000クレジット/月** |
| Freeの商用利用可否 | **不可** |
| Starter | $20/月、1,000,000クレジット/月、商用利用可 |
| Standard | $80/月、7,500,000クレジット/月、商用利用可 |
| Professional | $250/月、25,000,000クレジット/月、商用利用可 |
| 商用プラン最低料金 | $20/月(Starter) |
| credits / overage | Starter: 超過+$0.03/1,000クレジット。Standard: +$0.02/1,000。Professional: +$0.015/1,000。Freeは超過利用不可("No additional usage") |
| hard limitの既定挙動 | Freeは枠到達で利用不可(hard limit)。有償プランは超過課金で継続利用可能(公式資料に80%通知の明記は確認できず、**未確認**) |
| 80%通知 | 未確認(公式資料で明記箇所を特定できず) |
| domain-based authentication | あり。Web公開アプリ向けに推奨される方式で、コード変更不要・キー露出リスクなしと説明されている |
| API key認証 | あり(サーバーサイド/モバイル向け、クエリパラメータまたは`Authorization: Stadia-Auth`ヘッダー)。「エンドユーザーに漏洩しにくい用途向け」と明記されており、Web公開アプリでの単純なクライアントキー埋め込みは推奨されていない |
| MapLibre JSON style URL | あり(例: `https://tiles.stadiamaps.com/styles/alidade_smooth.json`) |
| MapLibre推奨の有無 | 明示的に推奨。Stadia MapsはMapLibreプロジェクトの創設メンバーの1社と説明されている |
| 日本語地名 | カスタムスタイルでラベル言語切替が可能な旨を確認。ラテン文字と日本語フォントを1つの"bold"にまとめる設定例あり。個別の「日本語ラベル品質」評価は未確認(9節でPoC確認へ送る) |
| dark style | あり(Alidade Smooth Dark等) |
| attribution | 必須。スタイルごとに文言が異なり(Stamen系はさらに追加クレジットが必要)、正確な文言はプラン・スタイル確定後に公式ドキュメントで個別確認が必要 |
| global CDN | 未確認(公式pricing/authenticationページでは明記を特定できず) |
| SLA | 標準プランには明記なし。Enterprise相当で個別SLA契約が可能と説明されている |
| support | `support@stadiamaps.com`での人的サポートを確認。SLA付きサポートはEnterprise相当で個別契約 |
| cache条件 | 未確認 |
| provider障害時の挙動 | [status.stadiamaps.com](https://status.stadiamaps.com/)でインシデント履歴を公開。自動フェイルオーバーの明記はなし |

## 8. Protomaps + Cloudflare

出典: [PMTiles Concepts](https://docs.protomaps.com/pmtiles/)、[protomaps/basemaps LICENSE_DATA.md](https://github.com/protomaps/basemaps/blob/main/LICENSE_DATA.md)、[Basemap Localization](https://docs.protomaps.com/basemaps/localization)、[Basemaps for MapLibre](https://docs.protomaps.com/basemaps/maplibre)、[Cloudflare R2 Pricing(公式製品ページ)](https://www.cloudflare.com/products/r2/)、[Cloudflare Workers Pricing(公式ドキュメント、直接取得)](https://developers.cloudflare.com/workers/platform/pricing/)。

「map sessionとAPI requestを混同しない」注記: この系統には「map session」という課金単位自体が存在しない。R2は保存(storage)・操作(Class A/B operations)・転送(egress)、Workersはリクエスト数・CPU時間で課金される、MapTiler/Stadiaとは全く異なる従量課金モデルである。

| 項目 | 内容 |
| --- | --- |
| PMTilesのライセンス | BSD(フォーマット・実装ライブラリ) |
| OSM basemapのライセンス | ODbL(Open Database License)。[protomaps/basemaps](https://github.com/protomaps/basemaps)が生成する完成物(Produced Work)は「© OpenStreetMap」の可視的な帰属表示が必須(Map Stylesのみ使いOSM由来タイルセットを使わない場合は不要という例外あり) |
| MapLibre GL JSとの接続方式 | `pmtiles`というJavaScriptライブラリでprotocolハンドラを登録し、MapLibre GL JSのstyle定義内で`pmtiles://`スキームのURLとしてPMTilesアーカイブを参照する方式。MapLibre GL JSが「スムーズな体験とカスタムスタイリングに推奨されるライブラリ」と公式に説明されている |
| PMTiles archive更新方法 | 公式ドキュメントに明確な更新頻度・自動更新の記載を本監査では特定できず。**未確認**(自前でOSMデータから再ビルドし、更新後のファイルをR2に再アップロードする運用が必要と推測されるが、確定情報ではない) |
| Cloudflare R2費用 | Standardストレージ$0.015/GB-月、Infrequent Access $0.01/GB-月。**egressは無料**($0.00/GB、公式に明記) |
| Workers費用 | Freeプラン: 1日100,000リクエストまで無料、1リクエストあたりCPU時間10ms上限、超過時は同種の操作がエラーになる(ハードストップ、公式ドキュメント直接取得で確認)。Paidプラン: $5/月〜、月1,000万リクエスト込み、超過$0.30/100万リクエスト |
| 月10M requests枠 | R2のFree tierには「月10GB-月ストレージ、Class A操作100万回、Class B操作1,000万回、egress無料」が含まれる(Class B=読み取り系操作が1,000万回/月が該当。「月10M requests」はR2 Free tierのClass B操作上限に相当すると考えられるが、地図タイル配信の1リクエスト=Class B操作1回に一致するかは実装依存のため**PoC確認待ち**とする) |
| 追加requests料金 | R2: Class A $4.50/100万、Class B $0.36/100万。Workers: $0.30/100万リクエスト(Paidプラン超過分) |
| storage費用 | R2 $0.015/GB-月(Standard) |
| egress費用 | **無料**(R2の主要な差別化ポイント) |
| CORS | R2バケットはCORS設定に対応(バケット単位でオリジンを許可するポリシーを設定可能という一般的なCloudflare R2の機能。本監査ではKAMI MUSUBI向けの具体的な設定例までは検証しておらず、実装時のPoC確認項目とする) |
| HTTP Range Requests | PMTilesの中核機構。R2はRangeリクエストに対応するオブジェクトストレージであり、PMTilesアーカイブの一部だけを都度取得する方式と技術的に整合する |
| cache設定 | Cloudflareのエッジキャッシュ(CDN)を介した配信が可能な構成が一般的だが、KAMI MUSUBI向けの具体的なキャッシュルール設定は本監査では未検証。**PoC確認待ち** |
| cache invalidation | 未確認(PMTilesファイルの差し替え時にCDNキャッシュをどう無効化するかは実装方針次第で、公式の単一手順は本監査では特定できず) |
| データ更新頻度 | 未確認(自前運用のため、更新頻度自体もKAMI MUSUBI側の運用方針次第) |
| 日本語ラベル対応 | protomaps/basemapsは言語別のlocalized style.jsonを配布しており、`lang: "ja"`指定で日本語ラベル表示に対応する旨をドキュメントで確認。国名ラベルは対象言語のみ、地名・通り名は複数言語表示に対応 |
| attribution | OSM由来タイルセットを使う場合「© OpenStreetMap」の可視的表示が必須(ODbLの要求。上記「OSM basemapのライセンス」参照) |
| 運用担当の必要性 | **高い**。タイルのビルド・R2へのアップロード・Workersでの配信設定・CORS/キャッシュ設定・PMTilesの更新運用を全て自チームで担う |
| 障害対応 | Cloudflareインフラ(R2/Workers)自体の障害はCloudflare側の責任範囲だが、PMTilesアーカイブの破損・更新ミス等はチーム側の責任範囲。フェイルオーバー・監視は自前で設計する必要がある |
| ロックイン | ソフトウェア(PMTiles/MapLibre)自体はベンダーロックインなし(BSD)。ただし現在の構成(R2+Workers)からの移行にはPMTilesファイルの移設作業が発生する(ファイル自体は標準フォーマットのため、別のオブジェクトストレージへの移設は技術的には可能) |
| CDN遅延 | 未確認(CloudflareのグローバルCDN網を通常利用できると推測されるが、日本国内からのレイテンシ実測値は本監査の対象外) |
| 推奨構成 | 未確認(公式に「推奨アーキテクチャ」として明記された単一の構成は本監査では特定できず。R2 + Workers + PMTilesの組み合わせは複数のブログ記事・コミュニティ事例で紹介されている一般的なパターンとして記録するに留める) |
| バックアップ方針 | 未確認(自前運用のため、バックアップ方針自体もKAMI MUSUBI側で新たに定義する必要がある) |

## 9. 日本国内地図品質

実際の画面表示(日本語地名・都道府県名・市区町村名・駅名・高速道路・一般道路・神社周辺の細街路・山間部・離島・dark style・375px幅での可読性)は、いずれのプロバイダも契約・APIキー発行を行わないと実地図で比較できない。本監査では契約を行っていないため、以下はすべて**契約前のPoC確認待ち**とする。

- MapTiler Cloud: 日本向けにMIERUNE監修のStreets/Gray/Darkスタイルが提供されている旨はドキュメントで確認したが、実際の描画品質(神社周辺の細街路・離島の詳細度等)は未検証
- Stadia Maps: 日本語ラベル切替の仕組み自体は確認したが、実際の日本国内データの詳細度・dark styleでの可読性は未検証
- Protomaps + Cloudflare: OSMベースのため、データそのものの日本国内カバレッジはOSMコミュニティの編集状況に依存する。日本語ローカライズの仕組みは確認したが、実際の描画品質は未検証

いずれのプロバイダも基盤データはOSM系(MapTiler/Stadia/Protomapsとも、各社の独自クロールではなくOSMを主要ソースの一つとして利用していると各社ドキュメントから読み取れる)であるため、神社のような細かい地物の反映状況はOSMコミュニティの編集密度に左右される点は3系統に共通するリスクとして記録する。

## 10. 認証・キー管理

| 項目 | MapTiler Cloud | Stadia Maps | Protomaps + Cloudflare |
| --- | --- | --- | --- |
| 公開APIキーの有無 | あり(必須) | あり(API key方式)、またはdomain-based認証(キーレス) | Workers経由配信の場合、R2バケット自体は非公開のままWorkers側で認可可能。公開APIキー必須ではない構成にできる |
| domain制限 | Allowed HTTP origins(ホワイトリスト) | domain-based authenticationあり(Web公開アプリに推奨) | Cloudflare Workers側でOriginヘッダー検証等を自前実装すれば可能。標準機能としては未確認 |
| referrer制限 | Origin/Refererヘッダー未送信のリクエストは拒否対象になり得る | 未確認(domain-based authenticationの内部実装詳細は非公開) | 自前実装次第(Workers内で任意のロジックを書ける) |
| API制限 | ユーザーエージェント制限も選択可能 | API key方式は「サーバーサイド/モバイル向け」と明記 | 自前実装次第 |
| secretをクライアントへ置く必要があるか | 静的書き出しの性質上、キーはビルド時にクライアントバンドルへ埋め込まれる(4.3節)。domain制限で悪用を軽減する設計になる | 同上。ただしdomain-based認証を選べばキー自体をクライアントへ置かずに済む | Workers経由配信を選べば、R2の認証情報自体をクライアントへ露出させない構成にできる(Workersがサーバー側の代理として動く) |
| キー漏洩時のローテーション | キー再発行機能はダッシュボードにあると推測されるが、具体的な手順は未確認 | 同上、未確認 | Workers/R2のアクセストークンはCloudflareダッシュボードから再発行可能という一般的な機能はあるが、KAMI MUSUBI向けの具体手順は未確認 |
| 開発・Preview・本番の分離 | プランごとにキーを分けて運用する一般的なSaaSパターンが可能と推測されるが、公式に「環境別キー管理」を明記したページは未確認 | 「Property」単位でキーを分離管理できる仕組みが確認できた(Webサイト用・モバイルアプリ用等) | `apps/mobile/eas.json`のビルドプロファイル(development/preview/production)に対応する形で、Cloudflare側もWorkers環境(Environments)を分ければ分離可能(Cloudflare Workersの一般機能。KAMI MUSUBI向けの具体設定は未検証) |
| Vercel Preview domain対応 | 未確認(本アプリのWeb版はVercelを使わずEAS Hostingを使うため、この論点自体の該当性は低い。4.6節参照) | 同上 | 同上 |
| EAS Web deploy対応 | 未確認(EAS Hostingのプレビューデプロイのドメイン体系自体を本監査では特定できず) | 未確認 | 未確認 |
| 使用量アラート | 未確認 | 未確認 | Cloudflareダッシュボードの一般的な使用量表示はあるが、KAMI MUSUBI向けのアラート設定は未検証 |
| hard limit | Freeは枠到達で停止(6節)、Flexはhard limitなし | Freeは枠到達で停止(7節) | Workers Freeは1日100,000リクエストでハードストップ(公式確認済み)。R2自体には明示的なhard limitの記載はなし(従量課金) |
| budget cap | 未確認(MapTiler Custom/Stadia Enterpriseで個別契約時に設定可能な可能性はあるが、標準プランでの明記は特定できず) | 未確認 | Cloudflareの請求アラート機能で近い運用は可能と推測されるが、確定情報ではないため未確認とする |

## 11. 料金比較

3ケース(月間1万 / 5万 / 10万 map sessions)を比較する。**session(地図を1回表示する単位)とAPI request(タイル1枚ごとのHTTPリクエスト)は異なる単位であり、1回のsessionで複数のtile requestが発生する**。以下はいずれも公式料金表に基づく概算であり、実際のタイルリクエスト数(ズームレベル・パン操作の頻度)によって変動するため、確定値ではなくレンジまたは「要見積もり」として扱う。

### 11.1 MapTiler Cloud(sessionベースで課金)

| 月間sessions | 想定プラン | 概算費用 |
| --- | --- | --- |
| 1万 | Free枠(5,000)を超えるためFlexが必要 | Flex基本 $30/月(25,000 sessions枠内に収まるため追加費用なし) |
| 5万 | Flexの25,000 sessions枠を超過 | $30/月 + 超過25,000 sessions × $2.50/1,000 = $30 + $62.50 = **$92.50/月** |
| 10万 | Flexの25,000 sessions枠を超過 | $30/月 + 超過75,000 sessions × $2.50/1,000 = $30 + $187.50 = **$217.50/月** |

(API requests枠も別途消費するが、1 sessionあたりのtile request数は画面設計・ズーム操作依存のため、requests側の超過有無は「要見積もり」とする)

### 11.2 Stadia Maps(creditsベースで課金、session/requestとは別のクレジット単位)

Stadia Mapsは「map session」や「API request」ではなく独自の「credits」で課金するため、KAMI MUSUBIの月間map session数をそのままcredits数に換算することはできない。1 map load(=1 session相当)が何creditsに相当するかは、使用するAPI(vector tile/static/geocoding等)の組み合わせによって変わるため、**公式料金だけで正確な月間費用を算出できない**。

| 月間sessions(参考) | 概算費用 |
| --- | --- |
| 1万 | 商用利用が前提であればFree(非商用専用)は使えないため、最低でもStarter $20/月からのレンジ。実際のcredits消費量は要見積もり |
| 5万 | Starter〜Standardのレンジ($20〜$80/月)。要見積もり |
| 10万 | Standard相当が目安だが要見積もり |

### 11.3 Protomaps + Cloudflare(storage/operations/requestsベースで課金、sessionという単位が存在しない)

PMTiles方式では「1 session」に対して発生するR2への実際のリクエスト数(Class B操作)とWorkersのリクエスト数はほぼ比例すると考えられるが、正確な比率は画面設計(初期表示ズームレベル・タイル分割数)に依存するため確定できない。以下は「1 session ≒ 数件〜十数件のタイルrequest」という一般的な傾向を踏まえた粗い試算であり、**要見積もり**の前提付きで記載する。

| 月間sessions(参考) | Workersリクエスト概算 | 概算費用 |
| --- | --- | --- |
| 1万 | 数万〜十数万requests/月 | Workers Free枠(1日10万requests=月300万requests相当)に収まる可能性が高い。R2ストレージ・Class B操作もFree tier(月1,000万Class B操作)に収まる可能性が高く、**$0〜数ドル/月のレンジ**(ストレージ数GB分の$0.015/GB-月が主要な実費) |
| 5万 | 数十万〜百万requests台/月 | 同様にWorkers/R2いずれもFree tier内に収まる可能性があるが、境界に近づくため**要見積もり** |
| 10万 | 百万requests台/月 | Workers Freeの日次上限(10万/日=月300万相当)には収まる可能性が高いが、R2のClass B操作(月1,000万)との比較含め**要見積もり** |

無料枠を商用利用できないMapTiler/Stadia Mapsとは異なり、Cloudflare R2/Workersの無料枠自体には「商用利用不可」の制限は本監査で確認した範囲では見当たらない(Cloudflareの利用規約全体の遵守は別途必要)。ただし、Protomaps側のOSM basemapデータ自体はODbLの帰属表示義務があり、「無料だから制約なし」ではない点に注意(8節)。

### 11.4 注記

- 上記はいずれも米ドル建ての公式料金そのままの記載であり、税・為替換算、日本円換算は行っていない
- 「無料枠を商用利用できない場合は0円として扱わない」の原則に基づき、MapTiler Free・Stadia Free単体は商用のKAMI MUSUBI本番運用の選択肢から除外し、上表では有償プランを起点に算出した

## 12. 運用比較

| 項目 | MapTiler Cloud | Stadia Maps | Protomaps + Cloudflare |
| --- | --- | --- | --- |
| self-host要否 | 不要(フルマネージド) | 不要(フルマネージド) | **必要**(タイルビルド・R2アップロード・Workers配信を自チームで運用) |
| 運用工数 | 低い(APIキー発行・style URL参照のみ) | 低い(同上) | **高い**(初期構築+継続的なデータ更新運用が必要) |
| 障害対応 | プロバイダ側の責任範囲が大きい。ステータスページで状況確認可能 | プロバイダ側の責任範囲が大きい。ステータスページで状況確認可能 | インフラ(Cloudflare)障害とデータ運用ミス(自チーム責任)が分離しており、後者の切り分け・対応は自チームの負荷になる |
| 長期費用の傾向 | セッション数に比例して増加(11.1節) | クレジット消費に比例して増加(11.2節、正確な予測が難しい) | ストレージ+リクエスト課金のため、Free tier内であれば長期的に大幅に安く抑えられる可能性がある(11.3節)が、運用工数とのトレードオフ |

## 13. 障害時fallback

タイル提供元を問わず、以下を共通方針として整理する(実装は本PRの対象外)。

- provider(タイル提供元)の読込に失敗した場合、既存のWeb一覧fallback UI(`ShrineSearchMap.web.tsx`の現行表示)へ切り替える
- 切り替え時も`selectedShrineId`は維持し、選択状態を失わない
- 神社詳細CTA(`SelectedShrineMapCard`の「詳細を見る」)は地図の状態に関わらず維持する
- provider障害時もAPI検索結果(`mapPoints`)は消さない。地図タイルの表示・非表示のみを切り替える
- provider障害(タイル読込失敗)と検索API障害(`fetchShrineMapPoints`失敗)を混同しない。それぞれ独立したエラー状態として扱う(既存の`mapStatus`とは別の状態管理が必要になる想定)
- 地図の再読み込みをユーザーが再試行できるようにする(既存の「もう一度試す」ボタンと同様のUXパターンを踏襲する想定)
- Analytics送信に失敗しても地図操作・選択操作を止めない(既存の`lib/analytics.ts`が例外を握りつぶす設計と一貫させる)
- 障害ログに座標・住所・検索語といった個人の行動が推測できる情報を残さない(エラー種別・タイムスタンプ等の非個人情報のみをログに残す方針)

## 14. 比較表

| 比較項目 | MapTiler Cloud | Stadia Maps | Protomaps + Cloudflare |
| --- | --- | --- | --- |
| サービス種別 | フルマネージドSaaS | フルマネージドSaaS | 自前ホスティング(データ配信基盤のみクラウド利用) |
| MapLibre互換 | 対応(`maptiler-sdk-js`) | 対応(公式推奨、創設メンバー) | 対応(`pmtiles`ライブラリ経由) |
| style URL | あり | あり | あり(自前生成・R2ホスティング) |
| 日本語地名 | 対応スタイルあり(MIERUNE監修) | 言語切替の仕組みあり | localized style.json(`lang: "ja"`)あり |
| dark style | あり | あり(Alidade Smooth Dark等) | 自前スタイルとして作成可能(標準提供の確認は未了) |
| APIキー | 必須 | 必須(またはdomain-based認証) | 必須ではない構成にできる(Workers経由なら非公開のまま配信可能) |
| domain制限 | Allowed HTTP origins | domain-based authentication | 自前実装(Workers) |
| Free商用利用 | 不可 | 不可 | 商用利用不可の明記は本監査では確認できず(ただしOSMデータのODbL帰属表示義務は別途必須) |
| 最低月額(商用) | $30(Flex) | $20(Starter) | 実費(11.3節、Free tier内なら数ドル未満の可能性) |
| 無料枠 | 5,000 sessions/月・100,000 requests/月 | 200,000 credits/月(非商用) | Workers: 1日10万requests。R2: 10GB-月ストレージ、Class A100万/月、Class B1,000万/月、egress無料 |
| 超過料金 | $2.50/1,000 sessions、$0.15/1,000 requests | $0.015〜$0.03/1,000クレジット(プラン依存) | R2: Class A $4.50/100万、Class B $0.36/100万、ストレージ$0.015/GB-月。Workers: $0.30/100万リクエスト(Paid) |
| hard limit | Free: あり。Flex: なし | Free: あり。有償: 超過課金で継続 | Workers Free: あり(1日10万requestsで停止)。R2: 従量課金、明示的なhard limit記載なし |
| 使用量通知 | 未確認 | 未確認 | 未確認 |
| SLA | Customプランで99.9% | Enterprise相当で個別契約 | Cloudflare本体の一般的なSLA(製品ごとに個別、本監査では未確認) |
| support | Basic(年$10k)〜Priority〜Custom SLA | メールサポート、Enterpriseで拡張 | Cloudflareサポート(インフラ側)+自チーム(データ運用側) |
| CDN | あり(自社) | あり(global CDNと紹介されるが詳細未確認) | あり(CloudflareのグローバルCDN網) |
| cache | 未確認 | 未確認 | 未確認(エッジキャッシュの一般的な仕組みはあるが具体設定は未検証) |
| attribution | 必須(MapTiler/OSM) | 必須(スタイルごとに文言が異なる) | 必須(OSM由来タイルセット使用時、ODbL) |
| 日本国内品質 | 契約前PoC確認待ち(9節) | 契約前PoC確認待ち(9節) | 契約前PoC確認待ち(9節、OSM編集密度に依存) |
| provider変更容易性 | style URL差し替えで比較的容易(MapLibre互換のため) | 同上 | PMTilesファイルの移設が必要だが、フォーマット自体はオープンなため技術的難易度は中程度 |
| self-host要否 | 不要 | 不要 | 必要 |
| 運用工数 | 低 | 低 | 高 |
| 障害対応 | プロバイダ主体 | プロバイダ主体 | インフラはCloudflare、データはチーム主体で分離 |
| 月1万概算 | $30/月(Flex基本料金内) | $20/月〜(要見積もり) | $0〜数ドル/月(Free tier内の可能性、要見積もり) |
| 月5万概算 | $92.50/月 | $20〜$80/月(要見積もり) | Free tier境界、要見積もり |
| 月10万概算 | $217.50/月 | Standard相当が目安、要見積もり | 要見積もり(Workers日次上限との比較が必要) |
| KAMI MUSUBI適合性 | 15節・16節で詳述 | 15節・16節で詳述 | 15節・16節で詳述 |

## 15. 第一候補

現時点では、**運用を外部サービスへ委ねつつMapLibreとの接続を簡潔に保つことを優先する場合、MapTiler Cloudが第一候補になり得る**。理由:

- style URLをそのままMapLibre GL JSへ渡すだけで動作し、`maptiler-sdk-js`という公式SDKも用意されている
- 日本向けにMIERUNE監修のスタイルが公式に用意されており、9節のPoC確認をスムーズに進めやすい
- Flexプランはhard limitがなく(サービス停止しない)、月末精算のため、検索画面という「使われるたびに課金が発生する」機能の運用上安全側に倒せる
- ただし、月10万sessions規模になると月$200超のレンジになり(11.1節)、KAMI MUSUBIの想定トラフィックが不明な現時点では費用の予見可能性を運用チームと事前にすり合わせる必要がある

## 16. 第二候補

一方、**商用最低料金とhard limitの制御を重視する場合、Stadia Mapsも有力である**。理由:

- 商用プラン最低料金がMapTilerより低い($20/月〜)
- domain-based authenticationにより、クライアントバンドルへAPIキーを露出させない構成を選べる(4.3節のリスクを軽減できる)
- MapLibreプロジェクトの創設メンバーの1社であり、MapLibre GL JSとの親和性が高い

ただし、courses/credits単位の課金でありKAMI MUSUBIの月間session数から正確な費用を事前算出できない(11.2節)ため、契約前に見積もり相談または試用が必要になる。

**Protomaps + Cloudflareは長期費用を抑えられる可能性があるが、データ更新・CDN・障害対応を自分たちで担うため、MVP初期には運用負荷が高い。** トラフィックが十分に伸び、運用チームにインフラ運用の余力ができた段階で再評価する候補として位置づける(第一候補・第二候補には含めない)。

## 17. 不採用または保留理由

- public OpenStreetMap tile server: 前提(3節)により最初から比較対象外。本番常用がポリシー違反のリスクを伴うため
- Protomaps + Cloudflare: 不採用ではなく「保留」。費用面のポテンシャルは高いが、MVP初期(運用体制が薄い段階)では自前運用のオーバーヘッドがリスクに見合わない可能性がある。トラフィックが伸びた後の再評価候補として17節ではなく15-16節末尾に位置づけた

## 18. 母艦判断事項

以下は本監査の範囲外であり、母艦(プロジェクトオーナー/意思決定者)が別途判断する必要がある:

1. **最終タイル提供元の意思決定**(MapTiler Cloud / Stadia Maps / Protomaps + Cloudflareのいずれか、または他候補の再検討)
2. 想定月間map sessions数の見積もり(11節の3ケースのどのレンジに近いか)
3. MapTiler Flex($30/月〜)またはStadia Starter($20/月〜)の商用契約を締結する予算・決裁権限
4. Protomaps + Cloudflareを選ぶ場合、タイルビルド・更新運用を担当するチーム/担当者のアサイン
5. APIキー/style URLの環境変数命名確定(`EXPO_PUBLIC_MAPTILER_KEY`案など、既存命名規則との整合)
6. EAS Hostingのプレビューデプロイのドメイン体系の確認(4.6節、10節で未確認とした項目)と、各プロバイダのドメイン制限設定への反映方法
7. attribution文言の最終確認(選定プロバイダ・選定スタイル確定後、各社公式ドキュメントで正確な文言を取得する)
8. SLA・サポート水準の要否(無償プランのまま運用するか、有償プランの99.9%SLA等を必要とするか)

## 19. PoC確認項目

契約・実装着手前に、実際のアカウント作成・style URL発行を伴う形で確認すべき項目(本PRでは未実施):

- 9節の日本国内地図品質(日本語地名・都道府県名・市区町村名・駅名・高速道路・一般道路・神社周辺の細街路・山間部・離島・dark style・375px幅での可読性)を、各プロバイダの実際のstyle URLをMapLibre GL JSに読み込んで目視確認する
- MapTiler/Stadiaのキャッシュ挙動(cache条件、6節・7節で未確認とした項目)
- Protomaps + CloudflareのR2 CORS設定の具体的な動作確認、Class B操作とタイルrequest数の実測比率
- EAS Hostingのプレビューデプロイのドメイン体系と、各プロバイダのdomain制限設定への登録可否
- 実際のユーザー操作パターン(検索→地図表示→ズーム/パン)における1 session あたりの平均tile request数の実測(11節の概算精度向上のため)
- 選定候補の利用規約・attribution文言の最新版を、契約直前に再度公式ページで確認する

## 20. 実装PR分割案

タイル提供元の最終決定後に着手する想定の分割案(判断確定後、選んだプロバイダに応じて詳細化する)。

- **PR-A(基盤)**: 選定プロバイダのAPIキー/style URL発行、環境変数追加(`EXPO_PUBLIC_*`)、`ShrineSearchMap.web.tsx`への最小限のMapLibre GL JS導入(Marker表示は既存`ShrineSearchMapProps`契約を維持)
- **PR-B(fallback統合)**: 13節の共通方針に基づくprovider障害時fallback実装(既存Web一覧UIへの切替、`selectedShrineId`維持、詳細CTA維持)
- **PR-C(品質確認・attribution)**: PoC確認項目(19節)の結果を踏まえたスタイル調整、attribution表示の実装、日本語ラベル・375px幅での可読性の最終確認
- **PR-D(該当する場合のみ)**: Protomaps + Cloudflareを選んだ場合のタイルビルド・更新パイプライン構築(本監査の制約により今回は含めない)

## 21. 残存リスク

- 本監査は各社公式ページ・公式ドキュメントの2026年7月時点の内容に基づく。料金・無料枠・利用規約はいずれのプロバイダも改定され得るため、契約直前に必ず最新情報を再確認する
- Stadia Maps・MapTiler Cloudの正確な月間費用は、session/credits消費量の実測なしには算出できない(11節)。想定より早く有償プラン超過に達するリスクがある
- Protomaps + Cloudflareは自チームでの運用が前提であり、担当者の異動・退職等でタイル更新運用が滞るとデータが陳腐化するリスクがある(バックアップ方針・引き継ぎ手順が未確認、8節)
- OSM系データを基盤とする3系統いずれも、神社のような細かい地物の反映度はOSMコミュニティの編集密度に依存する。地域によっては期待する精度が得られない可能性がある(9節)
- 「cache条件」「provider障害時の自動フェイルオーバー」「使用量アラート」「hard limit通知」など、複数の項目が公式資料だけでは確認できず「未確認」のまま残っている。契約前のPoC・営業問い合わせで埋める必要がある
- Vercel Preview domain対応・EAS Web deploy対応は、そもそも本アプリのWeb版の実際のホスティング方式(EAS Hosting)の詳細を本監査では十分に検証できておらず、この点も別途確認が必要

## 22. 公式参照資料

- [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/)
- [Map usage: Sessions vs requests | MapTiler](https://docs.maptiler.com/guides/maps-apis/maps-platform/what-is-map-session-in-maptiler-cloud/)
- [How to protect your map key | MapTiler](https://docs.maptiler.com/guides/maps-apis/maps-platform/how-to-protect-your-map-key/)
- [API key | MapTiler](https://docs.maptiler.com/cloud/api/authentication-key/)
- [Japan maps in MapTiler Cloud](https://docs.maptiler.com/guides/map-tiling-hosting/data-hosting/japan-maps-in-maptiler-cloud/)
- [MapTiler SDK JS (GitHub)](https://github.com/maptiler/maptiler-sdk-js)
- [How to change the default map labels language | MapTiler SDK JS](https://docs.maptiler.com/sdk-js/examples/language-map/)
- [MapTiler support](https://www.maptiler.com/support/)
- [MapTiler security](https://www.maptiler.com/security/)
- [Stadia Maps pricing](https://stadiamaps.com/pricing/)
- [Authentication | Stadia Maps](https://docs.stadiamaps.com/authentication/)
- [Quickstart: MapLibre GL JS | Stadia Maps](https://docs.stadiamaps.com/tutorials/vector-maps-with-maplibre-gl-js/)
- [Map Style Library | Stadia Maps](https://docs.stadiamaps.com/themes/)
- [Legally Required Attribution | Stadia Maps](https://docs.stadiamaps.com/attribution/)
- [Map Attribution Requirements | Stadia Maps](https://stadiamaps.com/attribution/)
- [Stadia Maps Status](https://status.stadiamaps.com/)
- [PMTiles Concepts | Protomaps Docs](https://docs.protomaps.com/pmtiles/)
- [Basemaps for MapLibre | Protomaps Docs](https://docs.protomaps.com/basemaps/maplibre)
- [Basemap Localization | Protomaps Docs](https://docs.protomaps.com/basemaps/localization)
- [protomaps/basemaps LICENSE_DATA.md](https://github.com/protomaps/basemaps/blob/main/LICENSE_DATA.md)
- [protomaps/basemaps (GitHub)](https://github.com/protomaps/basemaps)
- [Protomaps](https://protomaps.com/)
- [Cloudflare R2 — Egress-Free Object Storage](https://www.cloudflare.com/products/r2/)
- [Pricing | Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)
- [Tile Usage Policy | OSMF Operations Working Group](https://operations.osmfoundation.org/policies/tiles/)
- [docs/audit/web-search-map-library-selection.md(前回監査)](./web-search-map-library-selection.md)

## 23. 監査日と確認コミット

- 監査日: 2026-07-25
- ブランチ: `audit/web-map-tile-provider-selection`
- 現行実装の確認基準コミット: `a5e9579e`(develop、前回監査PR #2171マージ直後)
- 外部情報の取得日: 2026-07-25(WebSearch/WebFetch実施日。料金・仕様は変更され得るため、契約前に再確認すること)
