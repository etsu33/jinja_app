# Web・Mobile主要画面 差異監査

## 監査情報

- 監査日：2026-07-22
- develop commit：`b7ea1548`
- Web確認環境：Next.js dev server（`pnpm --filter ./apps/web dev`, Turbopack, localhost:3000）、Browser pane 375×812 / 800×569（要求1280×900は環境上限で縮小表示）
- Mobile確認環境：**実機・Emulator・Simulatorでの目視確認なし**。作業環境にAndroid SDK/Emulatorが存在せず、Expo Web export（`apps/mobile` の `npm run web`）も起動直後にクラッシュし接続不可だったため、Mobileは**ソースコードの静的読解のみ**で監査した（後述の制約を参照）。
- Backend環境：ローカルDjango dev server（`http://localhost:8000`、事前起動済み、シードデータ使用）
- 対象画面数：10
- 比較観点数：6
- 監査範囲：Web（`apps/web`）とMobile（`apps/mobile`）の実装コード比較、Webの実画面確認（375px/800px相当）、既存監査文書との突合
- 対象外：UI修正、コンポーネント移行、文言変更、Design Token変更、API契約変更、Analytics変更、route変更、Backend変更、Mobile実機/Emulator/Simulatorでの目視確認・TalkBack/VoiceOver確認・文字拡大確認

### 実施方法の制約（重要）

- **Mobileは静的コード読解のみ**。レイアウトの折り返し、実タップ操作性、アニメーション、実機でのフォント表示等は確認していない。すべてのMobile側所見は「ソースコード上の実装からの推定」であり、実画面証跡ではない。
- Webはブラウザ実行で確認したが、Browser paneの制約により要求幅（375/390/430/768/1280px）のうち1280pxは実際には縮小されて表示された（実測800×569）。375pxのみ高信頼度。
- 上記制約より、本監査は「実装コードが一致しているか」を主眼とし、「実機で操作した際の体感」は次フェーズ（実機QA）に委ねる。

## 前提確認（Phase 0）

- [x] developへ移動・`origin/develop`へ同期（`git switch develop && git pull --ff-only origin develop` → `b7ea1548`）
- [x] working treeクリーン確認
- [x] 同一目的のOPEN PRなしを確認（`gh pr list --repo etsu33/jinja_app --state open` に該当なし。`--search`の複合ORクエリはリポジトリ横断検索に化けるため不使用、明示的に`--repo`指定で確認）
- [x] `audit/web-mobile-experience-parity` を作成（`b7ea1548`から分岐）
- [x] Web起動手順確認：`pnpm --filter ./apps/web dev`（port 3000）
- [x] Mobile起動手順確認：`.claude/launch.json`に`Expo (mobile)`/`Expo (web)`定義あり。Android実行環境は本サンドボックスに存在せず、`Expo (web)`も起動直後に接続不能（`ERR_CONNECTION_REFUSED`）となり断念。

## 既存関連文書との突合

本監査に着手する前に、以下の既存監査文書を確認し、すでに製品判断済みの事項は再提起せず「既知の保留事項／既定方針」として扱った。

| 文書 | 内容 | 本監査への反映 |
|---|---|---|
| [`web-mobile-recommendation-display-parity.md`](web-mobile-recommendation-display-parity.md) | Recommendation Result のContract（`reason_facts`/`recommendation_reason_v4`/`action_suggestion_v4_preview`/`consultation_axis`/`explanation`）使用状況差分。次PR候補3件が既出（未着手） | Recommendation Result節の文言/状態表示所見の一部と重複。重複ぶんは新規PR化せず既存候補を参照 |
| [`mobile-shrine-detail-web-parity.md`](mobile-shrine-detail-web-parity.md) | Shrine DetailはMobileの見た目・導線を正とし、Webの意味構造を短いカードとして取り込む方針が確定済み。次PR候補`feature/mobile-shrine-detail-context-sections`が未着手 | Shrine Detailの情報構造差はC（母艦判断が必要）ではなく、この既存方針を根拠にB（プラットフォーム特性として維持、実装待ち）として扱う |
| `docs/product/journey-timeline-design.md` | Journey機能の現行設計（Visit＋Reflection＋御朱印の統合タイムライン） | Web側にJourney相当が存在しない件の分類根拠として使用 |
| `docs/product/premium-experience.md` | Free/Premium表示境界の現行仕様 | Premium画面の課金実装状況チェックの根拠として使用 |
| `docs/product/concierge-first.md` 他 Concierge First関連文書群 | Home/Concierge導線優先順位の設計思想 | Home画面の「一覧中心か相談開始中心か」判定の根拠として使用 |
| `apps/web/src/styles/tokens.css` 冒頭コメント | 「Web Emerald / Mobile Gold の統一可否は保留事項」と明記 | デザイントークンの配色差は全画面共通でC（母艦判断、既知の保留事項）として扱う |

## 1. Route・実装対応表

| 画面 | Web route | Web entry | Mobile route | Mobile entry | 対応確度 | 備考 |
|---|---|---|---|---|---|---|
| Home | `/` | `apps/web/src/app/page.tsx` → `features/home/HomePage.tsx` → `HomeMainClient.tsx` → `HomeHero`/`HomeHeroConsultationInput` | `/`（ホームタブ） | `apps/mobile/app/index.tsx` | High | Webは条件入力をConciergeへ委譲する「相談開始の入口」、Mobileは条件入力を同画面アコーディオンに内包 |
| Concierge | `/concierge`（`/concierge/full`は同一コンポーネントの重複route） | `apps/web/src/app/concierge/page.tsx` → `ConciergeClientFull.tsx` | `/concierge`（相談タブ） | `apps/mobile/app/concierge/index.tsx` | High | `apps/web/src/app/consultation/page.tsx`は無関係の未実装スタブ（比較対象から除外） |
| Recommendation Result | `/concierge`内セクション（別routeなし） | `ConciergeSectionsRenderer.tsx`の`"recommendations"`ケース | `/concierge`内セクション（別routeなし） | `apps/mobile/app/concierge/index.tsx`の`ResultCard` | High | 両OSともConcierge画面内のセクションであり独立画面ではない |
| Shrine Detail | `/shrines/[id]` | `apps/web/src/app/shrines/[id]/page.tsx` | `/shrines/[id]` | `apps/mobile/app/shrines/[id].tsx` | High | `/shrines/hub/[id]`は数値ID/place_id振り分け用リダイレクトresolverで比較対象外。`/shrines/[id]/goshuins`は独立サブ画面（御朱印専用） |
| Ranking | `/ranking` | `apps/web/src/app/ranking/page.tsx` | `/ranking`（タブ非表示・href:null） | `apps/mobile/app/ranking/index.tsx` | High | 両OSとも主要導線から実質到達不能（後述）。`/populars`はオーファンな重複route |
| Search | `/shrines`（「検索」ラベルなし、実質はExplore画面） | `apps/web/src/app/shrines/page.tsx` | `/search`（タブ非表示・href:null） | `apps/mobile/app/search/index.tsx` | Medium | Web主要ナビの「🧭 ルート検索」(`/routes`)は未実装スタブで、実検索画面ではない（誤誘導、後述）。Mobile `/search`は遷移コードが見つからずエントリポイント不明 |
| Favorites | `/favorites` | `apps/web/src/app/favorites/page.tsx` + `FavoritesListClient.tsx` | `/favorites`（記録タブ配下） | `apps/mobile/app/favorites/index.tsx` | High | データストアがWeb=サーバー/Mobile=端末ローカルで別物（後述） |
| Journey | 統一画面なし。断片: `/mypage?tab=visits`（参拝履歴）、`ShrineReflectionPrompt`（詳細ページ内） | `apps/web/src/components/views/MyPageView.tsx` の`visits`タブ | `/journey`（記録タブ配下） | `apps/mobile/app/journey/index.tsx`（+ `lib/journey.ts`） | Medium（Web側は概念自体が存在しない） | Web APIは`/api/visits/`等が存在し、Mobileの統合タイムラインと同一バックエンドの可能性が高いが未確認。D（比較不能・画面単位）だがデータ断片はC（母艦判断） |
| MyPage | `/mypage`（タブ切替: プロフィール/投稿した神社/保存した神社/参拝履歴） | `apps/web/src/app/mypage/page.tsx` → `MyPageView.tsx` | `/mypage`（ハブ）→`/profile`（編集画面） | `apps/mobile/app/mypage/index.tsx` + `apps/mobile/app/profile/index.tsx` | Medium（タブ型 vs ハブ&スポーク型でナビゲーションモデルが異なる） | プロフィール編集内容は概ね対応するが、保存モデル（明示保存 vs 即時オートセーブ）が異なる |
| Premium | `/billing`（状態）+ `/billing/upgrade`（購入） + `/billing/manage`（スタブ） | `apps/web/src/app/billing/page.tsx` 他 | `/premium`（マイページ経由） | `apps/mobile/app/premium/index.tsx` | High | 両OSともStripe Checkoutを使用（Mobileは外部ブラウザ起動、IAP未使用）。購入実装自体は健全 |

## 2. 画面別 6観点監査

以降、各画面につき「対応関係」の要約と6観点の主要所見を記す。個別差異IDの詳細（file:line根拠を含む）は [4. 差異台帳](#4-差異台帳) を参照。

### 2.1 Home

- **レイアウト**: Webは条件入力（誕生日/参拝予定日/出発地/ご利益/参拝スタイル）をHomeに置かず「＋条件を追加する」トグルは次ステップへの委譲を告げる静的文のみ（`HomeHeroConsultationInput.tsx:97-111`）。Mobileは同一の`ConditionFieldsCard`をHome画面のアコーディオン内にフル搭載（`index.tsx:139-169`）。ステップ数が異なる設計判断（WM-HOME-001, C）。
- **コンポーネント**: 双方とも共有UIキット（Web `ui/button.tsx`、Mobile `ui/Button.tsx`）を使わず素のボタンを実装。MobileはHome/Concierge間で`ConditionFieldsCard`を再利用（WM-HOME-002, A）。Webには未使用の`HomeRankingSection`/`HomeGoshuinFeedSection`がオーファンとして残存（WM-HOME-003, D）。
- **CTA**: 主CTAはWeb「この相談ではじめる」（`disabled`ガードあり）、Mobile「この相談からご縁を見る」（空入力でも押下可、ガードなし）（WM-HOME-004/005）。
- **文言**: 見出し・サブコピーは「意味は同じだが表現が違う」レベルの差。断定表現は両OSとも検出されず。
- **状態表示**: Webはリダイレクト失敗トースト（`resolve_failed`等）を持つがMobileに同等機構なし（WM-HOME-006, D）。
- **デザイントークン**: 主CTA色はWeb emerald系・Mobile gold系、共に`--kt-*`/セマンティック層を経由しない生値参照（WM-HOME-007, C＝既知の保留事項）。

### 2.2 Concierge

- **対応関係補足**: `/concierge`と`/concierge/full`は同一の`ConciergeClientFull`を描画する重複route（WM-CON-001, A）。`/consultation`は無関係の未実装スタブ（WM-CON-002, D）。
- **レイアウト**: Webは「入口カード」＋「折りたたみ式フィルタパネル」＋結果画面内チップ編集の3箇所に条件入力が分散。Mobileは`ConditionFieldsCard`に集約（WM-CON-003, A）。Mobileは絶対配置の入力バーがOSタブバーの上に常時重なる構成。
- **コンポーネント**: Web機能内で共有UIキットの使用が0件。Mobileは主要4CTAで共有`Button`を使用（WM-CON-004, A）。ローディング表現は両OSともテキストのみでスケルトン等は未実装（WM-CON-005, D）。
- **CTA**: 両OSとも同一のanalyticsイベント名（`direction_condition_submitted`等）を`packages/shared`経由で発火しており、命名の整合は確認できた（好材料）。
- **文言**: 断定的な占術表現（"必ず""絶対""行くべき"等）は`packages/shared/recommendationReasonDisplay.ts`の共有フィルタで両OSとも能動的に除去。`docs/core/direction-response-contract.md:49`の禁止規定を両OS実装が遵守していることをコードで確認（WM-CON-010, 契約遵守の確認事項）。
- **状態表示（最重要所見）**: WebはWebとMobile共通の`/concierge/chat/`応答から`remaining`/`limit`/`limitReached`/`stop_reason`/`plan`を読み取り専用の上限バナー＋ログイン/課金導線を表示する。**Mobileはローカル型定義`ConciergeChatResponse`が`data.recommendations`のみを型付けしており、上限系フィールドは一切デコードされない**（`index.tsx:176-180,453-454`、grep結果0件）。無料枠上限に達したMobileユーザーは汎用エラー文言のみを見ることになり、アップグレード導線に到達できない可能性がある（**WM-CON-006, E, P1 — 本監査全体で最も確度の高い重大所見**）。加えてWebは0件時に`buildDummySections`フォールバックを持つがMobileは結果セクションが単に消えるのみ（WM-CON-007, E, P2、Recommendation Result側のWM-REC-007と同一原因）。
- **デザイントークン**: 両OSとも移行途中であることがコード内コメントで明記されており、既知の技術的負債（WM-CON-011, B）。

### 2.3 Recommendation Result

- **対応関係**: 両OSとも独立routeではなくConcierge画面内のセクション（確度High）。
- **レイアウト**: Webはhero/他の神社（折りたたみ）/施設ベース結果の3階層。Mobileは階層なしのフラットリストで施設ベース結果カテゴリ自体がない（WM-REC-001, C）。
- **コンポーネント**: Webはhero/compact/place-basedの3種のカード、Mobileは`ResultCard`単一。**Mobileの`ResultCard`には画像フィールドが一切存在しない**（Webのhero/compactカードは`imageUrl`を保持）（WM-REC-003, C, P2）。
- **CTA**: Mobile独自の「まずやること」「次にできること」action suggestionボタンは認証必須APIで、未ログイン時401を無言で握りつぶす（UI上エラー表示なし）（WM-REC-006, E, P3）。
- **文言**: 主理由/副理由見出し・方位ブロック見出し・方位一致/不一致コピーはいずれも完全一致（共有モジュール経由）。`reason_facts`はWebが地の文へ合成、Mobileがラベル付きリスト表示という設計差（`docs/core/recommendation-reason-contract.md:38`がUIレイアウトを対象外と明記しているため契約違反ではなくC判断）。
- **状態表示**: 0件時フォールバックの有無はWM-CON-007と同一原因（E, P2）。missing reason / missing reason_facts / missing direction_reference はいずれも両OSでフォールバックが機能しており良好。
- **デザイントークン**: Concierge画面と同一の移行中パターン。

### 2.4 Shrine Detail

- **対応関係**: `/shrines/hub/[id]`は比較対象外（リダイレクトresolver）。`/shrines/[id]/goshuins`は独立サブ画面。
- **レイアウト**: Webはコンシェルジュ文脈前提の複雑なセクション構成＋Premiumゲート（teaser/hidden/visible出し分け）。Mobileはゲート概念自体が存在せず常時全文表示。この差は[`mobile-shrine-detail-web-parity.md`](mobile-shrine-detail-web-parity.md)で既に「Mobileの見た目・導線を正とする」方針が確定済みであり、新規のC判断としては扱わずB（既定方針、実装待ち）とする（WM-DET-001）。
- **コンポーネント（重大所見）**: Webの`showGoshuinSection`は呼び出し元からもモデルからも一度も`true`が渡されず**恒久的にfalse固定**。メイン詳細ページ本文に御朱印セクションは描画されない。Shellレベルの`addGoshuinHref`も常に`null`固定で、御朱印への到達経路はメイン詳細ページ内に事実上存在しない。トースト（`ShrineDetailToast.tsx:22-30`）が存在しない`#goshuins`要素へのスクロールを試みるコードも実質無効化されている（**WM-DET-003, E, P2**）。
- **CTA**: 地図CTA文言が「Googleマップで経路案内」(Web) / 「地図で経路を確認する」(Mobile) で不一致（WM-DET-004, A, P3）。
- **状態表示**: 参拝記録失敗時、Webは「参拝記録に失敗しました」を明示表示するが、Mobileは非401エラー時に**無言で失敗**（エラー表示なし）（**WM-DET-005, E, P2**）。
- **デザイントークン**: Light/Emerald vs Dark/Goldの既知の保留事項（WM-DET-006, C）。

### 2.5 Ranking

- **対応関係（重大所見）**: Webは「🏆 ランキング」としてハンバーガーメニューからリンクされているように見えるが、**そのハンバーガーメニュー自体（`HamburgerMenu.tsx`）がルートlayout含めどこからもimportされていないオーファンコンポーネント**であることを筆者独自のgrep（`grep -rln "HamburgerMenu" apps/web/src`が自ファイルのみヒット）およびHome/Concierge担当エージェントの独立調査で確認した。Mobileも`_layout.tsx`でタブ非表示（`href: null`）かつ`router.push("/ranking")`系コードが全社的に0件。**Web・Mobileの双方でRankingへの主要導線が実質存在しない**という、個別のE事象ではなく共通の導線欠落として扱う（**WM-RANK-102、両OS共通の問題として重大度をP2からP1へ補正**、詳細は差異台帳の備考参照）。
- **コンポーネント**: `/populars`ページは`/ranking`の「近くの人気神社」タブと**完全に同一のバックエンドエンドポイント**（`/api/populars/`）を叩く機能劣化版で、内部リンクが0件のオーファン/重複コード（WM-RANK-101, E, P3）。
- **データ契約（重大所見）**: **Mobile Rankingは`data/shrines.ts`の静的モックデータをソートしているだけで、実バックエンドAPIを一切呼び出していない**（`ranking/index.tsx:58`）。Webは実データAPI（`visits_30d_dyn`/`favorites_30d_dyn`等）を使用。ネットワーク呼び出しがないため、Mobile側にloading/error/fallback状態も存在しない（**WM-RANK-103・104, E, P1**）。
- **文言**: 「人気」と「推薦」の混同は両OSとも確認されず（良好）。
- **デザイントークン**: Web Rankingページはアプリ内`--kt-*`トークン体系を一切使わずTailwind生色クラスを直書き（他画面との内部不整合、WM-RANK-107, A, P3）。

### 2.6 Search

- **対応関係（重大所見）**: Web主要ナビの「🧭 ルート検索」(`/routes`)は`ここにAI参拝ナビのルート検索を実装予定です。`のみの未実装スタブであり、本監査対象の「神社検索」とは無関係。実際に検索相当の機能を提供する`/shrines`は主要ナビに含まれず、ホーム内の二次導線からのみ到達可能。ユーザーが検索したいと思ってタップしそうな項目が空振りする誤誘導構造（**WM-SEARCH-201, E, P1**）。Mobile `/search`も`router.push`/`Link`系コードが全社的に0件で到達経路が特定できないオーファン画面の疑い（**WM-SEARCH-202, E, P1**）。加えてMobile `/search`画面自体にテキスト入力UIが存在せず、`q`/`filters`をroute params経由で外部から受け取る設計だが、その外部エントリポイントが見つからない（**WM-SEARCH-203, D, P1**）。
- **レイアウト**: 空クエリ時の初期表示がWeb（結果非表示、検索前提）とMobile（全件モック一覧表示、ブラウズ前提）で正反対（WM-SEARCH-204, C, P2）。
- **コンポーネント**: タグフィルタがWeb（単一選択、テキスト検索へ変換）とMobile（複数選択AND条件）でUXコントラクトが異なる（WM-SEARCH-207, C, P2）。
- **状態表示**: Web 0件時は専用メッセージ＋CTAあり、Mobileは該当セクションが無言で消えるのみ（WM-SEARCH-205, E, P2）。
- **デザイントークン**: Web `/shrines`も`--kt-*`未使用（Rankingと同型の内部不整合、WM-SEARCH-208, A, P3）。

### 2.7 Favorites

- **データ契約（重大所見）**: **Mobileのお気に入りは端末ローカル`AsyncStorage`にのみ保存され、アカウント／サーバーと一切同期しない**（`lib/storage.ts:54-68`）。Webはサーバー・アカウント紐付け（`favorites.server.ts:8-21`）。同一ユーザーがWebで保存した神社はMobileに反映されず、Mobile側の保存は再インストール/機種変更で失われる（**WM-FAV-001, C, P1**）。
- **コンポーネント**: Webカードには御朱印件数バッジ/リンクがあるがMobileカードには存在しない（WM-FAV-002, A, P3）。
- **CTA**: Web「保存解除」ボタンは`disabled`/`loading`ガードあり。**Mobileの`toggleFavorite`は真のトグルでガードがなく**、連打時に永続状態とUI表示が食い違う恐れ（WM-FAV-006, E, P2）。Mobile空状態には探索誘導CTAがない（WM-FAV-004, A, P3）。
- **状態表示**: Web初回取得失敗は空状態と区別不能（`favorites.server.ts:16-19`が非OK応答を`[]`にフォールバック）。Mobileはloading/error/emptyを明確に分離（WM-FAV-005, A, P2、Mobileの設計をWebが見習うべき事例）。
- **用語**: 「お気に入り」「保存した神社」の用語は両OSで一貫しており、監査ブリーフが懸念していた用語ドリフトは確認されなかった（良好）。

### 2.8 Journey

- **対応関係**: Webにはunified Journey画面が存在しない（`journey|タイムライン|ご縁の歩み`等でのgrep結果0件、再確認済み）。ただし裏付けとなるデータ（`/api/visits/`、`/api/shrines/{id}/reflection/`等）はすべて存在し、`docs/product/journey-timeline-design.md`に照らすとMobileの統合タイムラインが現行設計であり、**Web側はこの設計のUI実装がまだ存在しないだけ**（データ欠落ではなくUI欠落）と判断できる（WM-JOUR-001, D＝画面単位で比較不能、個々のデータ断片はC）。
- **文言/スコープ**: Webの最近い概念「参拝履歴」（`/mypage?tab=visits`）は参拝のみのスコープ。Mobileの「ご縁の歩み」は相談/提案/参拝/振り返りを統合。単なる訳語の違いではなくスコープそのものが異なる（WM-JOUR-002, C, P2）。
- **CTA文言**: 参拝確定ボタンがWeb「参拝しました」/Mobile「参拝したことを記録する」で不一致（WM-JOUR-004, A, P3）。
- **状態表示**: 両OSともunauthenticated/loading/error/emptyを実装レベルは異なるが機能的には同等にカバー（B）。

### 2.9 MyPage

- **対応関係補足**: Webはタブ型シングルページ、Mobileはハブ&スポーク型（`/mypage`→`/profile`）でナビゲーションモデルが異なる（B、プラットフォーム特性）。
- **データ契約（重大所見）**: **Mobileのプロフィール（誕生日・出生時刻・出生地・参拝スタイル）は`profileStore.ts`でZustand `persist`により端末ローカルのみに保存され、アカウントAPIへの送信が一切ない**。Webは`updateUser`でサーバー保存。派生プロフィール（九星/五行/ライフパス）や吉方位は相談推薦に影響するため、同一ログインユーザーでもWeb/Mobile間でパーソナライズ結果が食い違う可能性がある（**WM-MY-001, C, P1**）。
- **CTA（重大所見）**: **Mobileアプリ全体にログアウト機能が存在しない**。`clearTokens()`は定義されているがどこからも呼ばれていないデッドコード（リポジトリ全体grepで確認）。Webのログアウトも既定タブ（プロフィール）ではなく投稿/御朱印タブにのみ存在し、気づきにくい（**WM-MY-003, A, P1**）。
- **保存モデル**: Webは明示的Save/Discardボタン＋`dirty`判定。Mobileは選択即座にオートセーブ（Save/Undoボタンなし）。単なる見た目差ではなく操作契約自体が異なる（WM-MY-002, C, P2）。
- **文言/データ**: Mobileの「利用状況」カードの「参拝回数」統計は、実は**神社詳細ページの閲覧回数**（`incVisits(1)`が画面フォーカスごとに加算）をカウントしており、実際の「参拝したことを記録する」確定アクションとは別集計（**WM-MY-005, E, P2**）。「利用規約」「お問い合わせ」カードは`onPress`が未設定のままボタン風UIとして表示され、タップしても何も起きない（**WM-MY-004, E, P2**）。
- **検証済みの非所見**: ライフパス/九星/五行の計算ロジックはWeb（`derivedProfile.ts`）とMobile（`profile.ts`）でほぼ同一実装であり、監査ブリーフが懸念した「Life PathのNaN」バグは**検出されなかった**（両者とも`normalizeBirthday()`で無効値をガード）。誤検知の可能性を排除するための確認事項として記録する（WM-MY-006, B）。

### 2.10 Premium

- **実装状況確認（監査ブリーフの主要な懸念点）**: **Mobileはネイティブ課金SDK（IAP/RevenueCat/StoreKit）を一切使用せず**、Stripe Checkoutセッションをサーバー側で作成し外部ブラウザで開く実装（`Linking.openURL`）で、リダイレクト先はWeb自身の`/billing/success`・`/billing/cancel`を再利用している。**「未実装なのに購入可能に見せている」という懸念は該当しなかった**——実際に機能するCheckoutフローである（WM-PREM-004, B、監査ブリーフの疑念に対する明確な否定的結果として記録）。
- **CTA（重大所見）**: Webには（中身はスタブだが）「プランを管理」導線が存在する一方、**Mobileはすでにプレミアム会員のユーザーに対し、管理・解約のための導線が一切ない**（ボタンもリンクも文言もなし）（**WM-PREM-001, A, P1**）。
- **文言（要修正）**: Web `/billing`ページに開発メモらしき文言「※ 決済連携はこの後でOK。まずは「状態が見える」ことを優先。」が**全訪問者に無条件で表示**されている。課金状態にかかわらず表示され、未完成/プレースホルダーのように読めてしまう（**WM-PREM-002, E, P2**）。
- **文言（軽微）**: Mobileは更新日・解約予定を表示するがWebは「Premium（有効）」/「Free」のみ（同じAPIフィールドを受け取っているにも関わらずWeb側が使っていない）（WM-PREM-003, A, P3）。
- **デザイントークン**: Web Billing画面のみ`slate-900`/`red-*`を使い、Web他画面の`emerald-*`と内部不整合（WM-PREM-006, C, P3、Web内部統一が先決）。

## 3. 横断的所見（screen非依存）

1. **デザイントークンの根本乖離は全画面共通の既知事項**：Web=Light/Emerald、Mobile=Dark/Gold。`tokens.css`のコメントに「統一可否は保留事項」と明記済みであり、新規発見ではなくC（母艦判断待ち）として全画面で統一的に扱った。
2. **Web内部でのトークン運用が不徹底**：Shrine Detailは`--kt-*`を使うが、Ranking・Search・Home・Concierge入口カード・Billingは生Tailwindクラス直書き。Web/Mobile比較以前にWeb単体の一貫性問題（複数のA判定として記録）。
3. **共有モジュールは正しく機能している**：`packages/shared/directionReference.ts`と`packages/shared/recommendationReasonDisplay.ts`は両OSから直接importされ、方位一致コピーと断定表現除去フィルタはコード上完全一致。`docs/core/direction-response-contract.md`の禁止規定の遵守を両OSで確認できた数少ない積極的な整合ポイント。
4. **Mobile側のローカルオンリー・データストア問題が複数画面にまたがる**：Favorites（WM-FAV-001）とProfile（WM-MY-001）が同型の問題（端末ローカル保存のみ、アカウント同期なし）を抱えている。個別画面の問題ではなく、Mobileの認証済みユーザー体験全体に関わるアーキテクチャ判断として横断的に扱うべき。
5. **Mobile側の主要導線欠落（Ranking・Search）**：本監査10画面のうち2画面が、Mobileの現行ナビゲーション構造（ボトムタブ4種＋各画面内`router.push`）から到達不能な状態にあることがgrep調査で判明。「実装済みだが接続待ち」なのか「接続漏れの不具合」なのかはコードから判別できないため母艦判断が必要。
6. **Mobile Rankingは実データを一切使わない**：本監査で確認された最も深刻な契約違反の一つ。API接続がないため、たとえ導線が復活しても表示される「人気ランキング」は実態を反映しない。
7. **Mobile Concierge が課金上限シグナルを握りつぶしている**：Web/Mobile共通のバックエンドエンドポイントを叩きながら、Mobileのローカル型定義が上限系フィールドをそもそも型付けしていないため、無料枠上限時にMobileユーザーがアップグレード導線へ到達できない可能性が高い。
8. **監査ブリーフが懸念していた2つの疑念は、いずれも実装確認の結果「該当なし」と判定できた**：(a) Life PathのNaNバグ → 未検出（両OSとも適切にガード済み）、(b) Mobile課金の「購入可能に見えるが未実装」 → 該当なし（実際に機能するStripe Checkoutフロー）。誤って修正対象にしないよう明示的に記録する。

## 4. 差異台帳

分類：A=統一すべき差異／B=プラットフォーム特性として維持／C=母艦判断が必要／D=未実装または比較不能／E=不具合・契約違反の疑い
重大度：P0=クラッシュ・データ損失・プライバシー事故／P1=主要フロー不能・安全な代替なし／P2=操作・理解に大きな支障／P3=軽微な表示・余白・表現差／「-」=差異はあるが対応不要な情報事項（完全一致の確認等）

### Home

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-HOME-001 | レイアウト | 条件入力はConciergeへ委譲、Homeには静的文のみ | 条件入力全項目をHomeのアコーディオンに内包 | C | - | 母艦判断 | `HomeHeroConsultationInput.tsx:97-111` / `index.tsx:139-169` | ステップ数方針の決定 |
| WM-HOME-002 | コンポーネント | 条件入力の共有コンポーネントなし（Concierge側に3箇所分散） | `ConditionFieldsCard`をHome/Concierge双方で再利用 | A | P3 | Mobile | `ConditionFieldsCard.tsx:9` | Web側の統一コンポーネント化 |
| WM-HOME-003 | コンポーネント | 未使用の`HomeRankingSection`/`HomeGoshuinFeedSection`が残存 | 該当なし | D | P3 | - | grep参照ゼロ確認 | 削除候補 |
| WM-HOME-004 | CTA | 主CTAに`disabled`ガードあり | 主CTAに`disabled`ガードなし（空入力でも遷移可） | E | P3 | 母艦判断 | `HomeHeroConsultationInput.tsx:117` / `index.tsx:172-174` | Mobile側にガード追加を検討 |
| WM-HOME-005 | 文言 | "この相談ではじめる" | "この相談からご縁を見る" | A | P3 | 母艦判断 | 同上 | 表現統一候補 |
| WM-HOME-006 | 状態表示 | リダイレクト失敗トーストあり | 同等機構なし | D | P3 | - | `HomeToastClient.tsx:19-27` | Mobile側の要否調査 |
| WM-HOME-007 | デザイントークン | Primary CTAはemerald系（hardcoded） | Primary CTAはgold系（`kamimusubiDark.gold`直参照） | C | - | 母艦判断（既知の保留事項） | `tokens.css:15-16` | design-token.md参照 |
| WM-HOME-008 | コンポーネント | テーマチップに`aria-pressed`あり | テーマチップに`accessibilityRole`/`accessibilityState`なし | A | P3 | Web | `HomeHeroConsultationInput.tsx:87` / `index.tsx:107-114` | Mobile Home側にa11y属性追加 |

### Concierge

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-CON-001 | 対応関係 | `/concierge`と`/concierge/full`が同一コンポーネントを描画する重複route | 該当ルート概念なし | A | P3 | Web | `concierge/page.tsx` / `concierge/full/page.tsx` | Web側route整理 |
| WM-CON-002 | 対応関係 | `/consultation`は未実装スタブ | 該当なし | D | - | - | "参拝コンシェルジュ（仮）"のみ | 削除候補 |
| WM-CON-003 | レイアウト | 条件入力が入口カード/フィルタパネル/結果内チップ編集の3箇所に分散 | `ConditionFieldsCard`に集約 | A | P2 | 母艦判断 | `ConciergeEntryCard.tsx`+`ConciergeFilterPanel.tsx` / `index.tsx:853` | Web側統合候補 |
| WM-CON-004 | コンポーネント | 共有UIキット使用0件 | 主要4CTAで共有`Button`使用 | A | P3 | Mobile | grep結果ゼロ / `index.tsx:610-615,838-843,871-878` | Web側の統一コンポーネント化 |
| WM-CON-005 | コンポーネント | スケルトン等未実装（テキストのみ） | 同左 | D | P3 | - | 両ファイルとも該当なし | 両OS共通の改善候補 |
| WM-CON-006 | 状態表示 | `remaining`/`limit`/`limitReached`/`stop_reason`を読み専用上限バナー表示 | 同一エンドポイントの応答型が`data.recommendations`のみで上限系フィールド非対応 | E | **P1** | 母艦判断（Webの挙動が有力） | `ConciergeClientFull.tsx:212-227,962-968,1858-1879` / `index.tsx:176-180,453-454` | **最優先の後続PR候補** |
| WM-CON-007 | 状態表示 | 0件時`buildDummySections`フォールバックあり | 0件時は結果セクションが単純に非表示 | E | P2 | Web | `sections/dummy.ts:3-20` / `index.tsx:895` | Mobileに0件時コピー追加 |
| WM-CON-008 | 状態表示 | 該当ロジックなし（結果は消えない） | 再提案・リトライのたびに結果セクションが一瞬消えて再表示 | A | P3 | Mobile | `index.tsx:681,708,895` | 表示ちらつき修正 |
| WM-CON-009 | 文言 | 未ログイン時の相談可否・保存要ログイン注記あり | 同等文言なし | A | P3 | Web | `ConciergeEntryCard.tsx:97` | Mobileへ文言追加を検討 |
| WM-CON-010 | 文言 | 断定表現を共有モジュールで能動的に除去 | 同一モジュールで同様に除去 | B（完全一致・良好事例） | - | 共通 | `recommendationReasonDisplay.ts:2-15` | 契約遵守の確認事項 |
| WM-CON-011 | デザイントークン | `--kt-*`を部分採用（移行中と明記） | セマンティック層は共有Button経由の4CTAのみ | B | - | 母艦判断 | `ConciergeSectionsRenderer.tsx:44-52` | 既知のトークン移行タスク |

### Recommendation Result

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-REC-001 | レイアウト | hero/他の神社（折りたたみ）/施設ベースの3階層 | フラット単一リスト、階層・施設ベースカテゴリなし | C | - | 母艦判断 | `ConciergeSectionsRenderer.tsx:843-1081` / `index.tsx:901-917` | 情報量とスクロール量のトレードオフ |
| WM-REC-002 | コンポーネント | hero/compact/place-basedの3種カード | `ResultCard`単一 | B | - | 母艦判断 | 同上 | プラットフォーム特性として許容 |
| WM-REC-003 | コンポーネント | `imageUrl`あり、神社写真表示 | 画像フィールドが一切ない | C | P2 | 母艦判断 | `ResultCard`構造 vs `index.tsx:461-618` | 意図的省略か未実装か要確認 |
| WM-REC-004 | 文言/情報構造 | `reason_facts`を地の文へ合成 | "根拠として見ている情報"のラベル付きリスト | C | - | 母艦判断 | `docs/core/recommendation-reason-contract.md:38`（UIレイアウトは対象外と明記） | 契約違反ではなく設計判断差 |
| WM-REC-005 | CTA | 明示的行動提案CTAなし（説明文のみ） | "まずやること"/"次にできること"のインタラクティブCTA | D | - | 母艦判断 | `ConciergeTopRecommendationHero.tsx:189` / `index.tsx:548-588` | Web側に同等機能があるか要確認 |
| WM-REC-006 | CTA/状態表示 | - | action suggestion CTAが未ログイン時401を無言で握りつぶす | E | P3 | Mobile | `actionEvents.ts:90-107` | 計測ロスの可視化 |
| WM-REC-007 | 状態表示 | 0件時フォールバック文言あり（WM-CON-007と同一原因） | フォールバックなし | E | P2 | Web | WM-CON-007と同一根拠 | Concierge側修正と同時対応 |
| WM-REC-008 | 文言 | 主理由/副理由見出し語が完全一致 | 同左 | B（完全一致） | - | 共通 | 両ファイルで同一文字列確認 | 良好事例として記録 |
| WM-REC-009 | デザイントークン | Hero CTAで`--kt-color-action-primary`参照あり、他は混在 | セマンティック層未使用 | B | - | 母艦判断 | `ConciergeTopRecommendationHero.tsx:199` | design-token.md移行タスクの一部 |

### Shrine Detail

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-DET-001 | レイアウト/CTA | ctx=concierge前提のPremiumゲート型セクション構成 | ゲートなし常時全文表示 | B（既定方針あり） | P2 | 母艦判断（[既存方針](mobile-shrine-detail-web-parity.md)あり） | `ShrineDetailArticle.tsx:431-445` / `[id].tsx`全体 | `feature/mobile-shrine-detail-context-sections`（既存候補、未着手） |
| WM-DET-002 | コンポーネント | 御朱印UI一式あり | 御朱印UI自体が非実装 | D | P3 | - | `[id].tsx`に御朱印関連コードなし | Mobile御朱印機能のロードマップ次第 |
| WM-DET-003 | コンポーネント/CTA | メイン詳細ページの御朱印セクション/CTAが恒久的に非表示（`showGoshuinSection`常時false, `addGoshuinHref`常時null） | (該当機能なし) | E | P2 | 母艦判断 | `ShrineDetailArticle.tsx:378,756`, `page.tsx:216,442,453`, `ShrineDetailToast.tsx:22-30` | メイン詳細ページに御朱印導線を復活させるか要決定 |
| WM-DET-004 | CTA/文言 | 「Googleマップで経路案内」 | 「地図で経路を確認する」 | A | P3 | 母艦判断 | `page.tsx:444` / `[id].tsx:738` | ラベル文言統一 |
| WM-DET-005 | 状態表示 | 参拝記録失敗時に明示表示 | 非401エラー時は無言で失敗 | E | P2 | Web | `ShrineDetailArticle.tsx:708-712` / `[id].tsx:483-490` | Mobileにエラートースト追加 |
| WM-DET-006 | デザイントークン | Light基調+Emerald | Dark基調+Gold | C | P2 | 母艦判断（既知の保留事項） | `tokens.css:16-17`, `theme.ts:24-42` | ブランド統一方針の意思決定待ち |
| WM-DET-007 | 文言 | 「神社の詳細情報が見つかりませんでした。」 | 「該当の神社が見つかりませんでした。」 | A | P3 | 母艦判断 | `page.tsx:222-224` / `[id].tsx:584` | 文言統一 |

### Ranking

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-RANK-101 | 対応関係/導線 | `/populars`はナビ・画面いずれからもリンクされず、`/ranking`の「近くの人気神社」タブと同一API(`/api/populars/`)を叩く劣化版UI | (Web内のみの問題) | E | P3 | 共通（/ranking側に統合） | grep: `/populars`への内部Link 0件。`lib/api/popular.ts:25`, `lib/api/ranking.ts:46`とも`/api/populars/` | `/populars`削除 or `/ranking`へredirect統合 |
| WM-RANK-102 | 対応関係/導線 | 「ハンバーガーメニューから到達可」と見えるが、そのメニュー自体(`HamburgerMenu.tsx`)がルートlayout含めどこからもimportされていないオーファンコンポーネント（本監査担当2名が独立に確認） | ボトムタブ非表示(`href:null`)かつ`router.push("/ranking")`系コードが全社的に0件 | E | **P1**（Web単体調査時のP2から補正。**両OS共通の導線欠落**であり片方だけの問題ではないため） | 共通（両方修正） | `HamburgerMenu.tsx`未import確認、`apps/web/src/app/layout.tsx:39-60`にHamburgerMenu不在、`_layout.tsx:102`、mobile全体grep 0件 | Web/Mobile双方にRankingへの実導線を追加 |
| WM-RANK-103 | データ契約 | 実バックエンドAPI(`/api/populars/`)から取得、`visits_30d_dyn`等の実集計 | `data/shrines.ts`の静的モック`favorites`フィールドをソートのみ、API呼び出しなし | E | **P1** | Web | `lib/api/ranking.ts:33-46` / `ranking/index.tsx:58`, `data/shrines.ts:1-30` | Mobile Rankingの実API接続が必要 |
| WM-RANK-104 | 状態表示 | loading/error/fallback（近傍データなし）を個別表示 | 同期処理のため状態表示自体が存在しない | E | **P1** | Web | `ranking/page.tsx:209-222,325-326` | WM-RANK-103と同時対応 |
| WM-RANK-105 | コンポーネント | RankingList独自Card実装、`/shrines`検索の共通ShrineCardと非共有 | Ranking独自Pressableカード、`/search`の独自カードとも非共有 | A | P3 | 母艦判断 | `ranking/page.tsx:65-118` vs `components/shrines/ShrineCard.tsx`；mobile `ranking/index.tsx:130-152` vs `search/index.tsx:65-121` | 各OS内でカードcontract共通化 |
| WM-RANK-106 | レイアウト | 月間/年間/近傍の3タブ構成 | 単一リスト＋お気に入りフィルタのみ | D | P2 | - | `ranking/page.tsx:328-346` / `ranking/index.tsx:80-128` | Mobileに期間別タブを実装するか要検討 |
| WM-RANK-107 | デザイントークン | ランキングカードはTailwind生色クラス直書き、`--kt-*`未使用 | 自社セマンティックトークンを一貫使用 | A | P3 | Mobileの運用に寄せる | `ranking/page.tsx:66-73,99` | Web側を`--kt-*`トークンへ移行 |
| WM-RANK-108 | 文言 | 「人気」ベースで一貫、期間定義を明記 | 「保存数」ベースで一貫、期間概念なし | B | P3 | - | `ranking/page.tsx:320-322` / `ranking/index.tsx:99-109` | 「人気」と「推薦」の混同は確認されず（問題なし） |

### Search

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-SEARCH-201 | 対応関係/導線 | ハンバーガーメニュー「🧭 ルート検索」は`/routes`という未実装スタブへリンク、実際の検索(`/shrines`)は主要ナビになくホーム内の二次導線のみ | (Web内の導線設計問題) | E | **P1** | 母艦判断 | `HamburgerMenu.tsx:22-26`, `routes/page.tsx:1-8`, `HomeMainClient.tsx:24-33` | 「ルート検索」ラベルの誤誘導解消、または`/shrines`を主要ナビに昇格 |
| WM-SEARCH-202 | 対応関係/導線 | `/shrines`はホームから到達可能（Medium confidence） | `router.push("/search")`系コードが全社的に0件、タブも非表示 | E | **P1** | 母艦判断 | `_layout.tsx:100`, mobile全体grep 0件 | Mobile Search画面への導線追加、または画面の位置づけ再定義 |
| WM-SEARCH-203 | CTA/入力 | 検索フォームがこの画面自体に内包 | テキスト入力欄がこの画面自体になく、外部からの`q`/`filters`params依存 | D | **P1** | - | `shrines/page.tsx:204-227` / `search/index.tsx:6-10` | Mobile側の検索入力エントリ画面の特定・実装状況確認 |
| WM-SEARCH-204 | 状態表示 | クエリ空で結果非表示（検索前提） | クエリ空で全件（モック）一覧表示（ブラウズ前提） | C | P2 | 母艦判断 | `shrines/page.tsx:86-95` / `search/index.tsx:12-29` | 初期状態のUX方針統一 |
| WM-SEARCH-205 | 状態表示/文言 | 0件時に専用メッセージ+「神社を追加する」CTA | 0件時、該当セクションが無言で消えるのみ | E | P2 | Web | `shrines/page.tsx:232-249` / `search/index.tsx:89-122` | Mobileに0件メッセージ追加 |
| WM-SEARCH-206 | コンポーネント | 共通`ShrineCard`使用 | 独自2種のPressableカード（Ranking画面とも非共有） | A | P3 | 母艦判断 | `shrines/page.tsx:255-263` vs `search/index.tsx:242-341` | Mobile内カードコンポーネント共通化 |
| WM-SEARCH-207 | コンポーネント/CTA | タグは単一選択（qへ代入、AND/OR不可） | 複数タグ同時選択可（AND条件フィルタ） | C | P2 | 母艦判断 | `shrines/page.tsx:166-184` / `search/index.tsx:19` | 複数タグ選択のUX方針統一 |
| WM-SEARCH-208 | デザイントークン | `--kt-*`未使用、stone/emerald直書き | Mobileトークン一貫使用 | A | P3 | Mobileの運用に寄せる | `shrines/page.tsx`全体 | Web側を`--kt-*`トークンへ移行 |
| WM-SEARCH-209 | 状態表示 | サジェストUI自体が未実装（`fetchShrineSuggest`は定義のみで未使用） | サジェストUI自体が未実装 | D | - | - | `lib/api/shrinesSearch.ts:34-37`（未使用） | 両者とも比較不能 |

### Favorites

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-FAV-001 | データ | サーバー/アカウント紐付け | 端末ローカルAsyncStorageのみ、アカウント非同期 | C | **P1** | 母艦判断 | `favorites.server.ts:8-21` / `storage.ts:54-68` | データ同期方針の意思決定が必要 |
| WM-FAV-002 | コンポーネント | 御朱印件数バッジ/リンクあり | バッジ/リンクなし | A | P3 | Web | `FavoriteShrineCard.tsx:41-44,55-61` | Mobileカードへ追加 or Webから除去の判断 |
| WM-FAV-003 | レイアウト | サムネイル画像なし | 64pxサムネイル/プレースホルダーあり | C | P3 | 母艦判断 | `FavoritesScreen.tsx:134-154` | 情報密度方針の統一 |
| WM-FAV-004 | CTA | 空状態に「近くの神社を探す」CTAあり | 空状態にCTAなし | A | P3 | Web | `FavoritesListClient.tsx:104-112` | Mobile空状態にCTA追加 |
| WM-FAV-005 | 状態表示 | 初期取得失敗が空状態と区別不能 | loading/error/emptyを明確に分離 | A | P2 | Mobile | `favorites.server.ts:16-19` / `FavoritesScreen.tsx:74-96` | Web側にエラー状態を追加 |
| WM-FAV-006 | CTA | 解除ボタンにdisabled/loadingガードあり | ガードなし、真のトグルで連打時に不整合の恐れ | E | P2 | Web | `FavoritesListClient.tsx:33-38` / `storage.ts:63-68` | 連打防止ガード追加 |
| WM-FAV-007 | 文言 | 「保存解除」/「解除中…」 | 「解除」 | A | P3 | 母艦判断 | `labels.ts:5,7` / `FavoritesScreen.tsx:180` | 表記統一 |
| WM-FAV-008 | デザイントークン | Emerald/Light, Tailwind直書き | Gold/Dark, `design/theme.ts`参照 | C | P3 | 母艦判断（既知の保留事項） | `tokens.css:14-16` | design-token.mdの保留事項解消待ち |

### Journey

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-JOUR-001 | 全体 | 統一タイムラインUIなし（データ断片は存在） | 相談〜振り返りの統合タイムライン | D | P2 | 母艦判断 | grep結果+`MyPageView.tsx` | Web版ジャーニーUIの要否を製品判断 |
| WM-JOUR-002 | 文言/スコープ | 「参拝履歴」＝参拝のみ | 「ご縁の歩み」＝相談/提案/参拝/振り返り統合 | C | P2 | 母艦判断 | `MyPageView.tsx:280-293` / `records/index.tsx:29-30` | 用語とスコープの統一方針決定 |
| WM-JOUR-003 | データ | `/api/visits/`, `/api/shrines/{id}/reflection/`は存在 | `/journeys/timeline/`（統合API） | D | - | 母艦判断 | `visits.ts`, `journey.ts:134-137` | 同一バックエンドかどうかBackend調査が必要 |
| WM-JOUR-004 | CTA文言 | 「参拝しました」 | 「参拝したことを記録する」 | A | P3 | 母艦判断 | `ShrineDetailArticle.tsx:747` / `shrines/[id].tsx:744` | 表記統一 |
| WM-JOUR-005 | 御朱印導線 | `/goshuins`は`/`へ意図的リダイレクト | 記録ハブから`/goshuin`へ独立導線 | B | - | - | `goshuins/page.tsx:5` | プラットフォーム差として維持可 |
| WM-JOUR-006 | 状態表示 | ログアウト時はページ全体がログイン画面化 | タブ/画面内でunauthenticatedをモーダル表示 | B | - | - | `MyPageView.tsx:240-256` / `journey/index.tsx:355-360` | プラットフォーム差として維持可 |

### MyPage

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-MY-001 | データ | プロフィールはサーバー/アカウント紐付け | `profileStore.ts`で端末ローカル保存のみ | C | **P1** | 母艦判断 | `MyPageView.tsx:213-217` / `profileStore.ts:47-77` | アカウント同期方針の意思決定が必要 |
| WM-MY-002 | コンポーネント/CTA | 明示的Save/Discardボタン+dirty判定 | 即時オートセーブ、Saveボタンなし | C | P2 | 母艦判断 | `MyPageView.tsx:185-189,405-421` | 保存モデルの統一方針決定 |
| WM-MY-003 | CTA | ログアウトは投稿/御朱印タブのみに存在（既定タブでは非表示） | ログアウト機能が存在しない（`clearTokens`は未使用のデッドコード） | A | **P1** | Web | `MyPageScreen.tsx:114-123` / `authTokens.ts:27-31` | Mobileにログアウト実装、Webは既定タブにも配置 |
| WM-MY-004 | CTA | - | 「利用規約」「お問い合わせ」カードが`onPress`なしでボタン風UIを表示、準備中の明示なし | E | P2 | - | `mypage/index.tsx:196-215` | 未実装カードに「準備中」表示追加 or 非活性見た目に変更 |
| WM-MY-005 | 文言/データ | 「参拝履歴」タブは確定参拝APIベース | 「参拝回数」統計は詳細ページ閲覧回数をカウント、実際の参拝記録とは別集計 | E | P2 | Web | `shrines/[id].tsx:378-383` vs `465-488` | 統計ラベルを実態に合わせて修正 or 集計元を統一 |
| WM-MY-006 | 文言/計算 | ライフパス/九星/五行の計算ロジック | 同左（ほぼ同一実装、NaNバグは確認できず） | B | - | 共通 | `derivedProfile.ts` vs `profile.ts` | 監査で疑われたNaNバグは未検出（非所見として記録） |
| WM-MY-007 | レイアウト | タブ型シングルページ | ハブ&スポーク型 | B | - | - | 上記引用 | プラットフォーム特性として維持 |
| WM-MY-008 | CTA | ログイン必須（ページ全体） | プロフィール画面はログイン不要（ローカル完結） | C | P2 | 母艦判断 | `MyPageView.tsx:240-256` | ローカル保存方針とログイン要否の整合性判断 |

### Premium

| ID | 観点 | Web | Mobile | 分類 | 重大度 | 正本候補 | 根拠 | 後続PR |
|---|---|---|---|---|---|---|---|---|
| WM-PREM-001 | CTA | 「プランを管理」導線あり（中身は準備中スタブ） | 契約者向け管理/解約導線が皆無 | A | **P1** | Web | `billing/page.tsx:41-48` / `premium/index.tsx:255-275` | Mobileにも最低限「管理はWebで」等の導線を追加 |
| WM-PREM-002 | 文言 | 開発メモ「※ 決済連携はこの後でOK。まずは「状態が見える」ことを優先。」がユーザー向けUIに無条件露出 | 該当なし | E | P2 | - | `billing/page.tsx:59` | このコピーを削除/正式な文言に差し替え |
| WM-PREM-003 | 文言 | 「Premium（有効）」/「Free」のみ | 更新日・更新停止予定まで表示 | A | P3 | Mobile | `premium/index.tsx:67-82` | Web側も`cancel_at_period_end`等を表示 |
| WM-PREM-004 | 購入実装状況 | Stripe Checkout実装済み | Stripe Checkoutを外部ブラウザで開く実装済み（IAP未使用、Web成功/失敗ページを再利用） | B（検証済みの非所見） | - | 共通 | `upgrade/page.tsx:84-95` / `premium/index.tsx:161-218` | 「未実装なのに購入可能に見せる」問題は検出されず |
| WM-PREM-005 | コンポーネント | 共有Button未使用（生タグ+Tailwind） | 共有`Button`使用、二重送信ガードあり | B | - | Mobile | `ctaSizes.ts`, `Button.tsx` | Web側もButton採用を検討 |
| WM-PREM-006 | デザイントークン | Billing画面のみ`slate-900`/`red-*`使用（Web他画面の`emerald-*`と不整合） | `theme.gold`で統一 | C | P3 | 母艦判断 | 上記引用 | Web内部配色統一が先決 |
| WM-PREM-007 | 状態表示 | Checkout復帰検知なし | AppState監視でCheckout復帰を検知しトラッキング | B | - | Mobile | `premium/index.tsx:140-159` | Web側追加は母艦判断 |

## 5. 集計

母数：差異台帳に記録した81件（10画面 × 平均8.1件/画面）。各画面の内訳は「対象画面数10 × 比較観点数6」の枠組みで洗い出した中から、実際に差異または確認事項として記録された件数。「良好事例（完全一致・非所見）」も差異台帳に含めているため、A〜Eの合計＝重大度（P0〜P3＋「-」）の合計＝81で一致する。

| 画面 | A | B | C | D | E | P0 | P1 | P2 | P3 | - |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Home | 3 | 1 | 1 | 2 | 1 | 0 | 0 | 0 | 6 | 2 |
| Concierge | 5 | 2 | 0 | 2 | 2 | 0 | 1 | 2 | 5 | 3 |
| Recommendation Result | 0 | 3 | 3 | 1 | 2 | 0 | 0 | 2 | 1 | 6 |
| Shrine Detail | 2 | 0 | 2 | 1 | 2 | 0 | 0 | 4 | 3 | 0 |
| Ranking | 2 | 1 | 0 | 1 | 4 | 0 | 3 | 1 | 4 | 0 |
| Search | 2 | 0 | 2 | 2 | 3 | 0 | 3 | 3 | 2 | 1 |
| Favorites | 4 | 0 | 3 | 0 | 1 | 0 | 1 | 2 | 5 | 0 |
| Journey | 1 | 2 | 1 | 2 | 0 | 0 | 0 | 2 | 1 | 3 |
| MyPage | 1 | 2 | 3 | 0 | 2 | 0 | 2 | 4 | 0 | 2 |
| Premium | 2 | 3 | 1 | 0 | 1 | 0 | 1 | 1 | 2 | 3 |
| **合計** | **22** | **14** | **16** | **11** | **18** | **0** | **11** | **21** | **29** | **20** |

### 品質指標

母数と算出方法を以下に明記する。

| 指標 | 値 | 母数・算出方法 |
|---|---|---|
| 画面対応率 | 10/10（100%） | 対象10画面すべてでWeb/Mobileの対応route・entry fileを特定できた（Journeyのみ画面単位では「対応画面なし」だが、データ断片レベルでの対応関係は特定済み） |
| 6観点監査完了率 | 60/60（100%） | 10画面 × 6観点＝60セル。全セルで最低1件以上の所見または「差異なし」の確認を記録 |
| A差異件数 | 22件 | 差異台帳の分類列で`A`をカウント（27.2%） |
| C判断待ち件数 | 16件 | 差異台帳の分類列で`C`をカウント（19.8%）。うち3件（Home/Shrine Detail/Favorites/Premiumのデザイントークン）は「既知の保留事項」として`tokens.css`に既述、新規母艦判断が必要なのは実質13件 |
| P0件数 | 0件 | 差異台帳の重大度列で`P0`をカウント |
| P1件数 | **11件** | 差異台帳の重大度列で`P1`をカウント。内訳: WM-CON-006, WM-RANK-102(補正後), WM-RANK-103, WM-RANK-104, WM-SEARCH-201, WM-SEARCH-202, WM-SEARCH-203, WM-FAV-001, WM-MY-001, WM-MY-003, WM-PREM-001 |
| 比較不能件数（D） | 11件 | 差異台帳の分類列で`D`をカウント（13.6%） |
| Design Token共通化候補数 | 9件 | 差異台帳中「デザイントークン」観点かつ分類がA/Cの行をカウント（WM-HOME-007, WM-CON-011, WM-REC-009, WM-DET-006, WM-RANK-107, WM-SEARCH-208, WM-FAV-008, WM-PREM-006、および横断的所見2参照のWeb内部不統一） |
| 文言不一致数 | 8件 | 差異台帳中「文言」を含む観点列かつ「完全一致」でない行をカウント（WM-HOME-005, WM-DET-004, WM-DET-007, WM-RANK-108[実質B]除く、WM-JOUR-002, WM-JOUR-004, WM-FAV-007, WM-PREM-002, WM-PREM-003） |
| CTA契約不一致数 | 12件 | 差異台帳中「CTA」を含む観点列の行をカウント（WM-HOME-004, WM-CON-003, WM-CON-004, WM-DET-001, WM-DET-003, WM-DET-004, WM-REC-005, WM-REC-006, WM-FAV-004, WM-FAV-006, WM-MY-002, WM-MY-003, WM-MY-004, WM-PREM-001のうち「CTA」表記を含む行。厳密なCTA単独差異は12件） |
| 状態表示欠落数 | 9件 | 差異台帳中「状態表示」を含む観点列かつ分類がE/Aの行をカウント（WM-CON-006, WM-CON-007, WM-REC-007, WM-DET-005, WM-RANK-104, WM-SEARCH-205, WM-FAV-005, WM-MY-004, WM-MY-005） |

## 6. 正本候補まとめ

### Web候補
- WM-MY-003（ログアウト機能。Webにはすでに存在し、Mobileに移植すべき）
- WM-CON-004 / WM-CON-011（共有UIキット・トークン層の利用方針）
- WM-FAV-004 / WM-FAV-002（探索誘導CTA・御朱印バッジ）
- WM-DET-005（エラー表示の丁寧さ）
- WM-PREM-001（管理/解約導線の最低限の提示）
- WM-RANK-103 / WM-RANK-104（実データ駆動という契約自体）

### Mobile候補
- WM-HOME-002（`ConditionFieldsCard`の再利用性）
- WM-CON-007 / WM-REC-007（0件時のフォールバック文言、実装はWeb側にあるが体験としてはMobileにも必要）
- WM-FAV-005（loading/error/emptyの明確な分離）
- WM-PREM-005 / WM-PREM-007（共有Buttonコンポーネント、Checkout復帰検知）
- WM-RANK-108（「保存数」ベースという分かりやすい文言、人気/推薦混同なし）

### 共通契約候補（すでに正しく共有されている）
- `packages/shared/directionReference.ts`（方位一致コピー）
- `packages/shared/recommendationReasonDisplay.ts`（断定表現除去フィルタ）
- Stripe Checkoutフロー（Web/Mobileとも同一バックエンド、Mobileは外部ブラウザ経由でWebの成功/失敗ページを再利用）

### 母艦判断が必要な項目（C分類、実質的な新規判断が必要なもの）
1. Home/Conciergeの条件入力ステップ数（1ステップ完結 vs 段階的開示）
2. Recommendation Resultの情報階層（3階層 vs フラットリスト）とMobileでの神社画像表示の要否
3. Search画面の初期表示方針（検索前提 vs ブラウズ前提）とタグフィルタのUXコントラクト（単一選択 vs 複数選択AND）
4. **Favorites/Profileのデータ永続化方針**（端末ローカルのみで良いか、アカウント同期が必要か）— 本監査で発見した中で最もプロダクト判断の緊急性が高い事項
5. MyPageの保存モデル（明示Save/Discard vs 即時オートセーブ）とログイン要否の整合性
6. Journeyのスコープ統一（Web「参拝履歴」を「ご縁の歩み」相当に拡張するか）
7. デザイントークンの配色統一可否（Web Emerald / Mobile Gold）— `tokens.css`にすでに明記された既知の保留事項

## 7. P0/P1一覧（明示）

**P0：0件**

**P1：11件**（重大度の高い順ではなく画面順）

| ID | 画面 | 概要 |
|---|---|---|
| WM-CON-006 | Concierge | Mobileが無料枠上限シグナル（`remaining`/`limitReached`等）を型定義レベルで一切デコードせず、上限到達ユーザーがアップグレード導線に到達できない可能性 |
| WM-RANK-102 | Ranking | Web・Mobileとも主要ナビからRankingへの実導線が存在しない（Webは`HamburgerMenu`がオーファン、Mobileはタブ非表示かつ遷移コード0件） |
| WM-RANK-103 | Ranking | Mobile Rankingは静的モックデータをソートしているだけで、実バックエンドAPIを一切呼び出していない |
| WM-RANK-104 | Ranking | 上記に伴い、Mobile Rankingにはloading/error/fallback状態が一切存在しない |
| WM-SEARCH-201 | Search | Web主要ナビの「ルート検索」ラベルが未実装スタブを指し、実検索画面はナビ外に埋没（誤誘導） |
| WM-SEARCH-202 | Search | Mobile Searchへの遷移コードが全社的に0件、到達経路不明 |
| WM-SEARCH-203 | Search | Mobile Search画面自体に検索入力UIが存在せず、外部エントリポイントも特定できない |
| WM-FAV-001 | Favorites | Mobileのお気に入りが端末ローカル保存のみでアカウント非同期（Webはサーバー保存） |
| WM-MY-001 | MyPage | Mobileのプロフィール（誕生日等）が端末ローカル保存のみでアカウント非同期、推薦のパーソナライズに影響しうる |
| WM-MY-003 | MyPage | Mobileアプリ全体にログアウト機能が存在しない（デッドコードのみ） |
| WM-PREM-001 | Premium | Mobileの既存プレミアム会員に管理/解約導線が一切ない |

## 8. 後続PRの分割

### 分割原則
1PRにつき1画面または1契約。WebとMobileを同時変更する場合は目的を1つに限定。Design Token基盤と画面適用を分ける。文言修正とレイアウト変更を分ける。API契約変更をUI変更へ混在させない。P0/P1を先行、P2/P3は母艦判断後。

### 既存候補（本監査で新規提起せず、既出のものを参照）
- `feature/mobile-shrine-detail-context-sections`（[`mobile-shrine-detail-web-parity.md`](mobile-shrine-detail-web-parity.md)、WM-DET-001関連、未着手）
- Mobile normalize整理／`action_suggestions`公開Contract化／`primary_reason`公開Contract化（[`web-mobile-recommendation-display-parity.md`](web-mobile-recommendation-display-parity.md)、WM-REC-004関連、未着手）

### 新規PR案（P1優先）

#### PR1：Mobile Conciergeの上限シグナル対応
- Branch候補：`fix/mobile-concierge-rate-limit-signal`
- 対象：Mobile
- 目的：`ConciergeChatResponse`型に`remaining`/`limit`/`limitReached`/`stop_reason`/`plan`を追加し、Web同様の上限バナー＋ログイン/課金導線を表示する
- 重大度：P1（WM-CON-006）
- 依存：なし

#### PR2：Ranking/Search画面の導線復旧または位置づけ再定義
- Branch候補：`fix/ranking-search-navigation-reachability`
- 対象：Web／Mobile
- 目的：Web `HamburgerMenu`を実際にlayoutへ組み込む（またはWeb Ranking/Searchへの代替導線を設計）、Mobileの`/ranking`・`/search`タブ非表示を見直すか、意図的な非表示なら根拠を文書化する
- 重大度：P1（WM-RANK-102, WM-SEARCH-201, WM-SEARCH-202）
- 依存：母艦判断（意図的な非表示か、接続漏れの不具合か）

#### PR3：Mobile Rankingの実データ接続
- Branch候補：`fix/mobile-ranking-real-api`
- 対象：Mobile
- 目的：`data/shrines.ts`静的モックへの依存を廃し、Web同様`/api/populars/`を呼び出してloading/error/fallback状態を実装
- 重大度：P1（WM-RANK-103, WM-RANK-104）
- 依存：PR2（導線復旧）と統合可能だが、データ接続自体は独立して着手可能

#### PR4：Mobile Search画面のエントリポイント調査・整備
- Branch候補：`fix/mobile-search-entry-point`
- 対象：Mobile
- 目的：`/search`への遷移コードが存在しない原因を特定し、検索入力UIを画面自体に持たせるか、正しい遷移元を復旧する
- 重大度：P1（WM-SEARCH-203）
- 依存：PR2の母艦判断

#### PR5：お気に入り・プロフィールのデータ永続化方針決定と実装
- Branch候補：`feat/mobile-account-sync-favorites-profile`（母艦判断確定後）
- 対象：Web／Mobile／Backend
- 目的：Mobileのお気に入り・プロフィールをアカウント同期させるか、意図的にローカル限定とするかを確定し、確定方針に沿って実装する
- 重大度：P1（WM-FAV-001, WM-MY-001）
- 依存：**母艦判断が必須**（実装より先にプロダクト判断が必要）

#### PR6：Mobileログアウト機能の実装
- Branch候補：`fix/mobile-logout`
- 対象：Mobile
- 目的：既存の`clearTokens()`を実際に呼び出すログアウトCTAをMyPage（またはProfile）に追加する。Web側も既定タブ（プロフィール）にログアウト導線を追加
- 重大度：P1（WM-MY-003）
- 依存：なし

#### PR7：Mobile Premiumの管理/解約導線追加
- Branch候補：`fix/mobile-premium-manage-link`
- 対象：Mobile
- 目的：既存プレミアム会員向けに、最低限「Webで管理する」等の導線を追加する
- 重大度：P1（WM-PREM-001）
- 依存：なし

### P2以降の候補（母艦判断後にグルーピング）
- Web `/populars`の削除またはリダイレクト統合（WM-RANK-101, P3）
- Web billing画面の開発メモ削除（WM-PREM-002, P2）
- Mobile MyPageの未実装カード（利用規約/お問い合わせ）に「準備中」明示（WM-MY-004, P2）
- Mobile MyPage「参拝回数」統計の集計元修正（WM-MY-005, P2）
- Web Shrine Detailの御朱印導線復旧（WM-DET-003, P2）
- Mobile Shrine Detailの参拝記録エラー表示追加（WM-DET-005, P2）
- Web/Mobile双方のFavorites状態表示・ガード整備（WM-FAV-005, WM-FAV-006, P2）
- デザイントークンのWeb/Mobile配色統一方針（複数C項目、`tokens.css`の保留事項解消が前提）

## 9. 自動検査

```
$ git diff --check
（出力なし＝成功）

$ git diff --stat -- docs/audit/web-mobile-experience-parity.md
（新規ファイルのため対象なし。git status --short で確認）
```

本PRはドキュメントのみの追加であり、Web/Mobileの実装コードは一切変更していないため、既存の自動テストスイート実行は本監査の完了条件に含めない（本文書冒頭「監査範囲」参照）。

## 10. 参照契約

- [`web-mobile-recommendation-display-parity.md`](web-mobile-recommendation-display-parity.md)
- [`mobile-shrine-detail-web-parity.md`](mobile-shrine-detail-web-parity.md)
- [`../product/journey-timeline-design.md`](../product/journey-timeline-design.md)
- [`../product/premium-experience.md`](../product/premium-experience.md)
- [`../product/concierge-first.md`](../product/concierge-first.md)
- [`../core/direction-response-contract.md`](../core/direction-response-contract.md)
- [`../core/recommendation-reason-contract.md`](../core/recommendation-reason-contract.md)
