> **Status: Audit / Historical（Shrine Detail Premium Information Architecture Audit、時点記録）**
>
> 本ドキュメントは、KAMI MUSUBI Web版のShrine Detailページが、確定済みProduct Decision A（`HYBRID`）が要求するPremium体験を収容できる構造なのかを、現行実装のEvidenceに基づいて監査した記録である。`docs/audit/test-release-premium-boundary-audit.md`（PR #2617）・`docs/audit/premium-personalization-deep-search-audit.md`（PR #2619）の続編であり、既存Auditを上書きしない。
>
> 対象コミット: `origin/develop` HEAD `607de72b`（PR #2619・#2620マージ後）。作業branch: `claude/kami-musubi-premium-audit-8roagp`（`origin/develop`から再起動）。
>
> **本監査はProduct Decisionを行わない。** Mother Ship Decision Input（Phase 12）の3案（SAME_PAGE / RESTRUCTURED_DETAIL / SEPARATE_PREMIUM_EXPERIENCE）はいずれも選択せず、`Codex Recommendation: NONE`と明記する。
>
> **分類ルール**: FACT（コード/テスト/契約から直接確認）・INFERENCE（複数FACTからの推論）・UNRESOLVED（追加調査またはMother Ship判断が必要）。既存Auditの記述が現行コードと乖離している場合は`AUDIT_STALE`として明記する（コピーではなく、必要範囲を現行コードと照合済み）。
>
> Web版のみを対象とする（Mobile対象外）。UI/Component/Route/Ranking/Score/Free Text処理/Signal Extraction/InterpretationProfile/Recommendation Reason/Premium Gate/Billing/Subscription/Quota/Authentication/Favorite/Reflection/Record/Analytics/Backend API/Serializer/DB/Schema/Migration/Test/Copy/Mobileのいずれも変更していない。発見した既存バグ（`context_reason`のmislabel等）も修正していない。

# KAMI MUSUBI — Shrine Detail Premium Information Architecture Audit

## Executive Summary

1. **Decision A（`HYBRID`）は前提として確定済み**——FreeでRecommendation Engineを十分体験でき、PremiumはDeep Interpretation/Personalized Recommendation/Deep Recommendation Reason/Personal Meaning/Personal Recordを通じて深化する。本監査はこの前提の下で、現行Shrine Detailの構造的な収容力のみを評価する。
2. **既存Auditに対する最重要の訂正（AUDIT_STALE）**: `premium-personalization-deep-search-audit.md`は「Direct Navigation/`ctx=map`経由のユーザーは、Premiumであっても①〜④ブロックを一切受け取らない」と記述していたが、これは現行コードと一致しない。実際には、①〜④ブロック（`personal_meaning`カード）は**payloadV2経路（多数派のケース）ではctx非依存で表示される**——`buildMeaningSectionsFromPayloadV2()`はctx引数を一切取らず、`GET /api/shrines/{id}/meaning/`はctxに関わらず常時取得される（`page.tsx:255`、`ctx==="concierge"`分岐の外）。**真に個人化された内容（`recommendation_reason_v4_detail`由来）が表示されるのは`ctx==="concierge"`かつ構造化スレッドが解決した場合のみ**であり、それ以外の経路（Direct Navigation・`ctx=map`・`ctx=compass`）でPremiumユーザーが見るのは、神社固有の一般的なコピー（ユーザー・相談情報を一切受け取らない`compose_shrine_meaning_payload()`由来）である。**「Premium個人化コンテンツ」というラベルの実体の大半が、実は個人化されていない神社一般コピーである**、という発見は、HYBRID要件の収容力評価において極めて重要である。
3. **Backend側のentitlement強制は依然として皆無**（既存2Audit・本監査すべてで再確認済みFACT）。`GET /api/shrines/{id}/meaning/`・`GET /api/shrines/{id}/`・`POST /api/deep-dive/ask/`はすべて`AllowAny`であり、"premium"ラベル付きコンテンツを含む全文を無条件返却する。
4. **`context_reason`カードは依然としてDEAD_POLICY（死んだ設定）**——Free層配列には`kind==="reason"`のセクションが構造的に一度も入らないため、"partial"というポリシー値は実効性を持たない。
5. **新たに発見した2件の死んだコード（前回Auditには存在しなかった、または見落とされていた）**: `PublicGoshuinSection`（御朱印公開ギャラリー、`showGoshuinSection`が本番経路で常に`false`）と`GoshuinLimitBadge`（御朱印上限バッジ、import元0件）。前回Audit（`premium-personalization-deep-search-audit.md`）は御朱印ギャラリーを「完全表示、差なし」と記録していたが、これは`AUDIT_STALE`——実際は到達不能なdead codeである。
6. **Compassは`tid`を一切運ばない**（FACT、新規確認）——`downstreamCtx`が`"compass"`を`null`へ正規化するため（`page.tsx:196`）、Compass経由の到達はコンテンツ個人化の観点でDirect Navigationと完全に同一になる（Analytics上のsourceラベルのみが異なる）。
7. **Architecture Option評価（Phase 7-9）では、SEPARATE_PREMIUM_EXPERIENCE（Option C）に対する強い既存実装Precedentが発見された**——`apps/web/src/app/mypage/history/[tid]/page.tsx`が、まさにOption Cが必要とする形（`shrine_id`不要、`tid`のみでThread全体をServer-sideで再取得する独立Route）を本番で既に実装している。一方、`shrines/[id]/goshuins`は「同一Shrineのsub-route」というOption Cのもう半分（shrine-scoped separate route）の先例である。両パターンの組み合わせ自体はrepo内に前例がない。
8. 本監査はSAME_PAGE/RESTRUCTURED_DETAIL/SEPARATE_PREMIUM_EXPERIENCEの3案を技術的Evidenceのみで比較し（Phase 10）、Test Release実装規模（Phase 11）とMother Ship Decision Input（Phase 12）を整理した。**いずれのOptionも選択していない。**

---

## Phase 0 — Baseline

| 確認項目 | 結果 | Evidence |
| --- | --- | --- |
| 最新developをbase | Y（`607de72b`、PR #2619・#2620マージ後から分岐） | `git log --oneline -5 origin/develop` |
| PR #2619マージ済み | Y（`3b4b3734`としてsquash merge） | 同上 |
| working tree | clean | `git status` |
| unrelated changes | なし | 同上 |
| 現在branch | `claude/kami-musubi-premium-audit-8roagp`（タスク記載の`audit/shrine-detail-premium-information-architecture`ではなく、セッション指定branchをdevelopから再起動して使用。git運用要件によるものであり調査内容には影響しない） | `git branch --show-current` |
| 対象commit SHA | `607de72b` | 上記 |
| 既存の未関連作業の変更・削除なし | Y | `git status`（他ファイル変更なし） |

---

## Phase 1 — Route / Entry Path Audit

**`ctx`/`tid`契約の構造（`page.tsx`→`buildShrineDetailModel.ts`を直接追跡、FACT）**:

- 受理される`ctx`値: `"map" | "concierge" | "compass"`（それ以外は`null`に正規化）——`page.tsx:55-57`
- **`downstreamCtx = ctx === "compass" ? null : ctx`**（`page.tsx:196`）——`buildShrineDetailModel`・`ShrineDetailShell`のclose-link等、コンテンツ個人化ロジック全体へはこの正規化後の値が渡る。**Compass由来のトラフィックは、コンテンツ個人化の観点でDirect Navigationと事実上区別されない**。元の`ctx`（`"compass"`含む）はAnalytics/source-labelingのためだけに一部コンポーネント（`ShrineDetailViewTracker`, `ShrineSaveButton`, `ShrineReflectionPrompt`, `GoogleMapRouteLink`）へ個別に渡る。
- Concierge thread取得（`getConciergeThreadServer`）は`ctx==="concierge" && tid`が真の場合のみ発火（`page.tsx:331`）。Compassは`tid`を一切持たないため（Part 1.3参照）、この分岐は常に素通り。
- `buildShrineDetailModel.ts`内で`ctx`を直接条件分岐しているのは2箇所のみ: `buildProposalSection`（`ctx==="concierge"`限定、`:531`）と`resolveDetailLead`（同上、`:601`）。**`ctx==="map"`はこのファイル内で一切特別扱いされない**——Direct Navigationと完全に同一の描画になる（close-link遷移先とAnalyticsのsourceラベルのみ異なる）。

**Entry Path一覧（FACT、推測での経路追加なし）**:

| Entry Path | Source Route | Destination | Query/State/Context | Login依存 | Premium依存 | 表示差 | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Concierge推薦結果 | `conciergeToShrineList.ts` | `/shrines/:id?ctx=concierge&tid=<threadId>` | `ctx=concierge`, `tid` | N（Concierge chat自体は匿名可） | N | **完全な個人化が可能**（proposal①、consultation-summary/state-delta lead、`recommendationReasonDetail`/`recommendationReasonV4Detail`がすべて populate） | `conciergeToShrineList.ts:198-207`; `page.tsx:331-380,412-433` |
| Concierge（thread未確定/compat fallback） | 同上、`tid`なし | `/shrines/:id?ctx=concierge` | `ctx=concierge`のみ | N | N | Partial——合成された「compat」explanation payloadのみ（実データではなく静的プレースホルダー） | `page.tsx:385-407` |
| Compass推薦結果 | `CompassRecommendationsSection.tsx` | `/shrines/:id?ctx=compass&recommendation_instance_id=...&recommendation_rank=N` | `ctx=compass`, `recommendation_instance_id`, `recommendation_rank`。**`tid`は一切運ばれない** | N | N | **個人化なし**（`downstreamCtx`が`null`化、Direct Navigationと同一描画。Analytics source labelのみ異なる） | `CompassRecommendationsSection.tsx:81-89`; `page.tsx:187-196,331` |
| Map（近隣一覧） | `NearbyShrineCardListClient.tsx`（`buildMapDetailHref`経由） | `/shrines/:id?ctx=map[&tid=...]` | `ctx=map`、任意で`tid`（Map側から素通し） | N | N | **個人化なし**（`ctx==="map"`は`buildShrineDetailModel`で未チェック） | `NearbyShrineCardListClient.tsx:137-142`; `buildMapDetailHref.ts:1-19` |
| Direct Navigation/URL | 任意 | `/shrines/:id` | なし（`ctx=null`） | N | N | ベースライン（proposal①なし、consultation-summary leadなし） | `page.tsx:181-220` |
| Favorite page | `FavoriteShrineCard.tsx` | `/shrines/:id` | なし | N（`/favorites`はmiddleware非対象） | N | Direct Navigationと同一 | `FavoriteShrineCard.tsx:33`; `middleware.ts:7-19` |
| MyPage（御朱印保存フロー） | `MyPageScreen.tsx`/`MyGoshuinList.tsx` | `/shrines/:id?toast=goshuin_saved#goshuins` | なし | **Y**（`/mypage/:path*`はlogin必須） | N | Direct Navigationと同一（`#goshuins`アンカーは実際には存在しない、Phase 2参照） | `MyPageScreen.tsx:233`; `middleware.ts:7-19` |
| Ranking/Top page | `RankingCard.tsx`/`RankingList.tsx` | `/shrines/:id` | なし | N | N | Direct Navigationと同一 | `app/ranking/page.tsx:110`; `RankingCard.tsx:10` |
| 御朱印投稿完了（`/goshuin/new`） | `GoshuinNewClient.tsx` | `/shrines/:id#goshuins` | ハッシュのみ | UNRESOLVED | N | Direct Navigationと同一（ハッシュ先は存在しない） | `GoshuinNewClient.tsx:85` |
| Shrine hub redirect | `app/shrines/hub/[id]/page.tsx` | `/shrines/:id?ctx&tid`へredirect | 素通し | 呼び出し元次第 | 呼び出し元次第 | 純粋なredirect | `app/shrines/hub/[id]/page.tsx:1-32` |
| Place resolve redirect | `app/shrines/resolve/page.tsx` | 同上 | 素通し | Y（resolve API自体は401→login誘導） | N | 純粋なredirect | `app/shrines/resolve/page.tsx:1-49` |
| PlaceCardClientActions（検索結果からのfavorite） | `PlaceCardClientActions.tsx` | `/shrines/:id`（ctx/tidなし） | なし | Y（favorite作成コールが401） | N | Direct Navigationと同一 | `PlaceCardClientActions.tsx:34,38-40` |

存在しない経路は追加していない（`buildShrineHref`/`buildMapDetailHref`/`detailHrefFromRecommendation`等のgrepで確認済みの呼び出し元のみを列挙）。

**Part 1.3 — 構造的発見: Compassは`tid`を一切運ばない（FACT、新規）**: `CompassRecommendationsSection.tsx:83-87`が構築するhrefは`ctx:"compass"`, `recommendationInstanceId`, `recommendationRank`のみで、`tid`フィールドは`CompassRecommendation`/`buildShrineHref`のオプションに存在しない。`downstreamCtx`の`null`化と合わせ、**Compass由来のトラフィックはコンテンツ個人化のあらゆる観点でDirect Navigationと区別不能**である。

---

## Phase 2 — Component Tree

**実際のRender Tree（`page.tsx`の実装から直接構築、概念図ではない）**:

```text
ShrineDetailPage (apps/web/src/app/shrines/[id]/page.tsx)
├─ ScrollToTopOnMount
├─ ShrineDetailViewTracker
├─ ShrineDetailToast
└─ ShrineDetailShell
   ├─ ShrineCloseLink
   ├─ [条件付き「操作」DetailSection]
   │  └─ GoogleMapRouteLink（googleDirHref存在時のみ）
   └─ children → ShrineDetailArticle
      ├─ ShrineDetailHeroHeader（local fn）
      ├─ ShrineDetailHeroCard
      ├─ [方位補足コピー box]（inline）
      ├─ ShrineDetailStateDeltaSection（actionStateがvisited/reflected時のみ）
      ├─ [参拝後お礼コピー box]（inline）
      ├─ ShrineDetailSections（contextReasonSections）
      │  ├─ ShrineReasonSection（kind:"reason"）
      │  ├─ ShrineProposalSection（kind:"proposal"）
      │  ├─ ShrineJudgeSection（kind:"meaning"）
      │  ├─ ShrineActionSection（kind:"action"）
      │  └─ ShrineSupplementSection（kind:"supplement"）
      ├─ ShrineDetailSections（premiumSections、personalMeaningVisibility==="visible"時のみ）
      ├─ PremiumUpgradePrompt（personalMeaningVisibility==="teaser"時のみ）
      ├─ ShrineFactSection（factSection非null時のみ）
      │  ├─ DeityList
      │  └─ HistoryList → HistoryCard, SourceList
      ├─ ShrineDeepDivePrompt（常時レンダリング）
      ├─ [Save/Visit/Reflectionパネル]（resolvedSaveActionNode存在時のみ）
      │  ├─ ShrineSaveButton
      │  └─ ShrineReflectionPrompt（hasVisitHistory時のみ）
      ├─ PublicGoshuinSection（★DEAD——showGoshuinSectionが本番経路で常にfalse）
      └─ DetailDisclosureBlock（「ご利益」、!hasSections時のみ）
```

**Component表**:

| Component | Responsibility | Data Source | Personalized | Login | Premium | Entry Path依存 | Evidence |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `ShrineDetailPage` | Server Component、全データ取得・model組み立て | `getShrineDetailServer`, `getBillingStatusServer`, `getConciergeThreadServer`, `fetchShrineMeaningPayloadV2Server`等 | Y（ctx=concierge&tid時） | N | N（取得のみ、遮断しない） | Y | `page.tsx:181-549` |
| `ShrineDetailViewTracker` | `shrine_detail_view`発火（マウント時1回） | props | N（tracking用途） | N | N | Y（sourceラベル） | `ShrineDetailViewTracker.tsx:20-62` |
| `ShrineDetailToast` | `?toast=goshuin_saved`時に`alert()`+`#goshuins`へscroll | URLクエリ | N | N | N | N | `ShrineDetailToast.tsx:9-34`（**scroll先の`#goshuins`要素は本番描画で存在しない**、Part 2.3参照） |
| `ShrineDetailShell` | レイアウトシェル、close button、「操作」block | props | N | N | N | Y（close遷移先） | `ShrineDetailShell.tsx:45-123` |
| `ShrineDetailArticle` | メインコンテンツ組み立て | `buildShrineDetailModel`出力全体+`isPremiumActive`+`ctx`+`stateDelta` | Y | N（内部の`useAuth()`はCTA文言のみ） | **Y——ただしFrontend表示制御のみ** | Y | `ShrineDetailArticle.tsx:379-841` |
| Hero意味コピー（local fn） | title+hero-meaningコピー描画（非Premiumは汎用文へ差し替え） | `heroMeaningCopy`, `isPremiumActive` | Y（concierge経由時のみ真の個人化、それ以外は汎用fallback） | N | Y（`isPremiumActive`直接三項演算） | Y | `ShrineDetailArticle.tsx:222-238,650-654` |
| `ShrineDetailStateDeltaSection` | 「前回との違い」、非Premiumはteaser CTA | `stateDelta`, `isPremiumActive` | Y | Y（訪問記録の前提としてlogin必須） | **Y——実際に機能する真のteaser gate** | Y（`stateDelta`は`ctx==="concierge"`時のみ非null） | `ShrineDetailArticle.tsx:288-375,459-461,602-616,661-663` |
| ①〜④ブロック（`personal_meaning`カード） | 「選ばれた理由/状態整理/意味/視点」 | **分岐**: payloadV2経路（`buildMeaningSectionsFromPayloadV2`、ctx非依存）or 真の個人化経路（`buildShrineDetailReasonV4Sections`、ctx=concierge+構造化thread限定）or fallback（`buildPremiumDisplaySections`、ctx依存） | **条件付き**（Phase 4-STALE参照——多数派経路では非個人化） | N | Y（`personalMeaningVisibility`、teaser/visible二値） | **payloadV2経路では非依存（多数派）、個人化経路のみctx=concierge限定** | `ShrineDetailArticle.tsx:456,677-683`; `buildShrineDetailModel.ts:84-173,1125-1171,1602-1694` |
| ⑤補足（ご利益・象徴・相性） | タグ群chip描画 | `buildSupplementSection()` | HYBRID（ご利益/象徴はFACT、相性タグは相談由来） | N | N（`contextReasonVisibility`は参照されず常時全文） | 相性タグのみ相談依存 | `ShrineDetailArticle.tsx:463-467,675`; `buildShrineDetailModel.ts:1072-1101` |
| `PremiumUpgradePrompt` | Premium CTAカード（ゲスト/ログイン済みFreeを`useAuth()`で区別） | `useAuth()` | Y（文言） | **Y——ゲスト/Free正しく区別** | Y（CTA gate自体） | N | `ShrineDetailArticle.tsx:172-220` |
| `ShrineFactSection` | 御祭神/由緒・歴史 | `buildShrineFactSection(shrine)` | N | N | **N（明示的にPremium対象外とコメントで宣言）** | N | `ShrineDetailArticle.tsx:687-689`; `buildShrineFactSection.ts:49-84`; `evidence_gate.py:53-80` |
| `ShrineDeepDivePrompt` | 自由記述Q&A | `POST /api/deep-dive/ask/` | N | UNRESOLVED | UNRESOLVED（Backend側は`AllowAny`確認済み、Part 2で再確認） | N | `ShrineDetailArticle.tsx:691-695`; `deep_dive.py:76-108` |
| `ShrineSaveButton` | Favorite toggle | `useFavorite()`, `useAuth()` | N | **Y（401→login redirect）** | N | Y（sourceラベル） | `ShrineSaveButton.tsx:31-141`; `backend/favorites/views.py:16` |
| `ShrineReflectionPrompt` | 参拝後振り返り | `createShrineReflection()` | Y | **Y（Backend `IsAuthenticated`確認済み）** | N（`accessLevel`propはAnalytics専用） | Y | `ShrineReflectionPrompt.tsx:1-158`; `reflection.py:11,48` |
| `PublicGoshuinSection` | 公開御朱印ギャラリー | `publicGoshuinsPreview` | N | N | N | **N/A——本番描画で到達不能（DEAD CODE、Part 2.3参照）** | `ShrineDetailArticle.tsx:388,414,795-806` |
| `DetailDisclosureBlock`（ご利益fallback） | `!hasSections`時のみのfallback | 同上タグデータ | N | N | N | N | `ShrineDetailArticle.tsx:808-838` |
| `RecommendationMetaSection` | 「1位の理由」等 | `recommendationMeta` | Y（もし描画されれば） | N/A | N/A | N/A | **確認済みdead code**（import元0件） `RecommendationMetaSection.tsx:14`; tracking-onlyの参照`ShrineDetailArticle.tsx:586-600` |
| `GoshuinLimitBadge` | 「御朱印 N/limit」バッジ+upgrade link | `fetchMyGoshuinCount()` | N/A | N/A | N/A | N/A | **新規確認済みdead code**（import元0件、前回Auditでは未言及） `GoshuinLimitBadge.tsx:11` |

**Part 2.3 — 新規発見: `PublicGoshuinSection`は本番描画で到達不能（`AUDIT_STALE`）**:

- **旧記述**（`premium-personalization-deep-search-audit.md` Section 5行174）: 「御朱印（公開ギャラリー+投稿） | 完全表示 | 差なし | なし | なし | N（公開UGC）」——**完全表示されると記録していた**。
- **新発見（現行コード）**: `ShrineDetailArticle.tsx:388,414,795-806`が`showGoshuinSection`（既定`false`）で全体をゲートしている。`buildShrineDetailModel.ts`の戻り値（`:1705-1738`）にはこのフラグが一切含まれず（`[Gg]oshuin`の全文grepで`publicGoshuinsPreview`/`publicGoshuinsViewAllHref`のみ確認、フラグ自体なし）、`page.tsx`のJSX（`:518-544`）も明示的にセットしていない。**結果として本番経路で`showGoshuinSection`は常に`false`であり、`PublicGoshuinSection`は一度もレンダリングされない。** このフラグが`true`になる唯一の箇所は、コンポーネント自身の単体テスト（`ShrineDetailArticle.test.tsx:169`）のみ。
- **副次的影響**: `ShrineDetailToast`が御朱印保存後に`document.getElementById("goshuins")?.scrollIntoView(...)`を試みるが（`ShrineDetailToast.tsx:20-30`）、`#goshuins`アンカー自体が存在しないため無言でno-opする。
- **判定: `AUDIT_STALE`**。

**Part 2.4 — 前回Audit主張の再確認結果（Backend enforcement/context_reason/personal_meaning/previous_comparison/isAuthenticated hardcode）**: すべて現行コードと一致（変化なし）。詳細はPhase 4参照。

---

## Phase 3 — Section Inventory

| Section | Runtime表示 | Responsibility Class | Data Source | Personalized | Login | Premium | Entry Path | Evidence |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| Hero title/address | Y | SHRINE_FACT | shrine素フィールド | N | N | N | N | `ShrineDetailArticle.tsx:651,653` |
| Hero意味コピー | Y | HYBRID | `buildHeroMeaningCopy()`（concierge優先→汎用fallback） | 条件付き | N | Y（生boolean三項） | Y（真の個人化はconcierge限定） | `buildShrineDetailModel.ts:1254-1297` |
| Hero画像カード | Y | SHRINE_FACT | 静的 | N | N | N | N | `ShrineDetailArticle.tsx:655` |
| 方位補足コピー | Y（存在時） | SHRINE_FACT | `shrineMeaningPayloadV2.generated.directionSupportCopy` | N | N | N | N（ctx非依存で常時取得） | `buildShrineDetailModel.ts:1701`; composer`shrine_meaning_composer.py:757-770` |
| 参拝後state-delta | Y（visited/reflected時） | PERSONAL_MEANING | `page.tsx:352-364 compareState()` | Y | Y | **Y（真のgate、生boolean判定）** | Y（`ctx==="concierge"`限定でのみ非null） | `ShrineDetailArticle.tsx:288-375,459-461` |
| 参拝後お礼コピー | Y | RECORD隣接（静的） | 静的文字列 | N | Y | N | N | `ShrineDetailArticle.tsx:664-672` |
| **①〜④ブロック（`personal_meaning`）** | Y（`personalMeaningVisibility==="visible"`時） | **分岐**（`ctx==="concierge"`+構造化thread時のみPERSONAL_MEANING、それ以外はSHRINE_FACT相当の一般コピー） | `buildMeaningSectionsFromPayloadV2()`（ctx非依存、多数派）or `buildShrineDetailReasonV4Sections()`（concierge+構造化限定） | **条件付き（Phase 4-STALE参照）** | N | Y（visible/teaser） | **多数派経路は非依存** | `buildShrineDetailModel.ts:84-173,1625-1694` |
| ⑤補足（ご利益・象徴・相性） | Y（常時、free配列） | HYBRID | `buildSupplementSection()` | 相性タグのみY | N | **N（`contextReasonVisibility`は無視され常時全文）** | 相性タグのみ相談依存 | `buildShrineDetailModel.ts:1072-1101,1429-1432` |
| Recommendation meta | **N（dead code）** | N/A（本来RECOMMENDATION） | 計算はされる、tracking専用 | Y（もし描画されれば） | N/A | N/A | N/A | `RecommendationMetaSection.tsx:14`（import元0件） |
| 御祭神/由緒・歴史 | Y（Knowledge存在時） | SHRINE_FACT | `buildShrineFactSection(shrine)` | N | N | **N（明示的にPremium対象外）** | N | `ShrineDetailArticle.tsx:687-689`; `evidence_gate.py:53-80` |
| Deep Dive Q&A | Y（常時） | SHRINE_FACT | `deep_dive_answer.py`経由 | N | N | N | N | `deep_dive.py:76-108`（`AllowAny`） |
| Save/お気に入り | Y | RECORD | `useFavorite`→Favorites API | N | **Y** | N | N | `ShrineSaveButton.tsx:44-48,92-98`; `backend/favorites/views.py:16` |
| 参拝記録 | Y | RECORD | `addVisit()` | N | **Y** | N | N | `ShrineDetailArticle.tsx:748-788`; `visit.py:13,60` |
| 参拝後の振り返り | Y（訪問記録後） | RECORD | `createShrineReflection()` | Y | **Y** | N | N | `ShrineReflectionPrompt.tsx:19,54-67`; `reflection.py:11,48` |
| 御朱印（公開ギャラリー+投稿） | **N（dead code、AUDIT_STALE）** | RECORD（本来） | `PublicGoshuinSection` | N | N | N | N/A | `ShrineDetailArticle.tsx:388,414,795-806`（Phase 2.3参照） |
| 経路案内 | Y（lat/lng存在時） | VISIT | `gmapsDirUrl()` | N | N | N | N | `page.tsx:268` |
| ご利益フォールバック（`!hasSections`のみ） | Y（セクション皆無時のみ） | SHRINE_FACT | 同上タグデータ | N | N | N | N | `ShrineDetailArticle.tsx:808-838` |

---

## Phase 4 — Current Gate Audit

**宣言ポリシー（`cardVisibility.ts:41-180`）と実Runtime挙動の対比、`ShrineDetailArticle.tsx`が実際に`getVisibilityForCard`を呼ぶ4カードのみ**:

| CardId | 宣言（匿名/Free/Premium） | 実Runtime挙動 | 分類 |
| --- | --- | --- | --- |
| `context_reason` | hidden/**partial**/visible | Free配列に`kind==="reason"`のセクションが構造的に一度も入らない（payloadV2経路は`kind:"meaning"`のみ、fallback経路は`kind:"supplement"`のみをfree tierへ）。`"partial"`の値は実描画に影響を与えない。全文は`ShrineDetailArticle.tsx:675`で`contextReasonVisibility`を直接参照せず無条件レンダリング | **DEAD_POLICY**（Concierge`ConciergeSectionsRenderer.tsx:1065-1096`と同種のバグクラス、変化なし再確認） |
| `personal_meaning` | hidden/**teaser**/visible | `"visible"`→完全表示、`"teaser"`→`PremiumUpgradePrompt`へ完全差し替え（部分リークなし）。**gate機構自体は正しく機能する** | **TEASER/FULL（機構は正常）——ただしPhase 4-STALEの通り"visible"の中身が信頼できる個人化コンテンツとは限らない** |
| `recommendation_meta` | hidden/visible/visible | 計算はAnalyticsイベント名選択（`card_view`/`card_partial_view`）にのみ使用、対応する`RecommendationMetaSection`は未レンダリング | **DEAD_POLICY**（ポリシー値が描画へ一切影響しない） |
| `previous_comparison` | hidden/**hidden**/visible | `ShrineDetailArticle.tsx:459-461`が非Premiumを強制的に`"teaser"`へ上書き（宣言上の`"hidden"`とは異なる）。実際の描画gateは`previousComparisonVisibility`ではなく`isPremiumActive`の生boolean判定（`:300`）——`previousComparisonVisibility`はAnalytics送信にのみ使用 | **CTA/TEASER（エンドユーザー挙動としては正常機能）——ただしAnalyticsが記録する値（teaser）と宣言ポリシー（hidden）が食い違う** |

`ShrineDetailArticle.tsx`から一度も`getVisibilityForCard`で参照されないが`CardId`共用体には存在するID（Concierge側専用またはShrine Detail未使用）: `shrine_hero`, `shrine_compact`, `other_shrines`, `save_prompt`, `login_prompt`, `premium_preview`（コンポーネントとして直接レンダリング、policy lookup経由ではない）, `consultation_summary`, `state_teaser`, `filter_panel`, `shrine_meaning`, `action_meaning`, `comparison_hint`, `history_shift`, `deep_reflection`, `shrine_public_info`, `shrine_access`, `shrine_goriyaku`, `shrine_goshuin_preview`, `saved_record`（`ShrineDetailArticle.tsx:457`で常に`"visible"`ハードコード）。

**Backend側enforcement確認（再検証、FACT・変化なし）**:

| Endpoint | File | Permission | Plan/entitlementチェック |
| --- | --- | --- | --- |
| `GET /api/shrines/{id}/meaning/` | `shrine_meaning.py:10-29` | `AllowAny` | **なし。** `compose_shrine_meaning_payload(shrine)`はshrine行のみを引数に取り、request/user/planを一切参照しない |
| `GET /api/shrines/{id}/`（`ShrineViewSet.retrieve`） | `shrine.py:260-263` | `AllowAny` | なし（データ品質フィルタ`verification_status`のみ、planゲートではない） |
| `POST /api/deep-dive/ask/` | `deep_dive.py:76-80` | `AllowAny` | なし |
| Favorites | `backend/favorites/views.py:16` | `IsAuthenticated` | ログインgateのみ |
| Visit | `visit.py:13,60` | `IsAuthenticated` | ログインgateのみ |
| Reflection | `reflection.py:11,48` | `IsAuthenticated` | ログインgateのみ |
| 御朱印feed | `goshuin_feed.py:9`, `goshuin.py:28` | `AllowAny` | なし |

**Backend enforcement結論: 変化なし、再確認済み。** Shrine Detailのデータ経路にBackend側entitlement/planチェックは一切存在しない。匿名/curlによる直接呼び出しで、現在"Premium限定"とラベル付けされた全文を取得できる。

**`accessLevel`のisAuthenticatedハードコード再確認（FACT・変化なし）**: `ShrineDetailArticle.tsx:447-453`が`resolveAccessLevel({plan,is_active}, true)`と`true`を固定引数で渡しており、`accessLevel`は`"anonymous"`に絶対にならない。現状これを悪用した実害（コンテンツ漏洩）はない（現在使用中の全CardIdの`anonymous`/`free`ポリシー値がたまたま同じ扱いになるため）が、潜在バグとして継続する。

### Phase 4-STALE — `personal_meaning`カードの内容実態に関する訂正（最重要）

**旧記述**（`premium-personalization-deep-search-audit.md` Executive Summary #6 / Phase 8）: 「Direct Navigation・`ctx=map`経由のユーザーは、Premiumであっても②③④ブロックを一切受け取らない（`buildShrineDetailModel.ts:1136`: `if (!args.isConciergeContext) return sections;`）」

**新発見（現行コード）**: `buildShrineDetailModel.ts:1136`の`isConciergeContext`ゲートは、`buildPremiumDisplaySections()`という**フォールバック関数の内部にのみ**存在する。この関数は`payloadV2DisplaySections`が`null`の場合にのみ呼ばれる（`:1611-1613`、`payloadV2DisplaySections?.premiumDisplaySections ?? buildPremiumDisplaySections(...)`）。

実際の多数派経路である`buildMeaningSectionsFromPayloadV2()`（`:84-173`）は**ctx引数を一切取らない**。この関数は`GET /api/shrines/{id}/meaning/`のレスポンス（`shrineMeaningPayloadV2`）から`access:"premium"`ブロックすべてを無条件で`premiumDisplaySections`へ分類する（`:108-119,138-165`）。そして`shrineMeaningPayloadV2`自体は**ctxに関わらず常時取得される**（`page.tsx:255`、`ctx==="concierge"`分岐より前で実行）。Backend側の`compose_shrine_meaning_payload(shrine)`（`shrine_meaning_composer.py:858-868`）はshrine行のみを引数に取り、request/user/相談情報を一切受け取らない——`_build_action_meaning()`には無条件の最終fallback文字列が存在する（`:640`）ため、`action_meaning`ブロック（`access:"premium"`）はほぼすべてのshrineに対して常に存在する（テストで裏付け: `test_shrine_meaning_composer.py:45-46`が`blocks`が常にtruthyであることを確認）。

`ShrineDetailArticle.tsx:677-683`の実際の描画条件は`personalMeaningVisibility==="visible"`（純粋なplan判定）と`hasPremiumSections`のみであり、**`ctx`チェックはこの描画分岐に一切存在しない**。

**結論（新FACT）**: Premiumユーザーは、Direct Navigation・`ctx=map`・`ctx=compass`のいずれの経路でも①〜④ブロックの「表示」自体は受け取る。ただし、その中身は**神社一般の生成コピー**（ユーザー・相談情報を一切反映しない）であり、**真に個人化された内容（`recommendation_reason_v4_detail`由来の相談連動narrative）が表示されるのは`ctx==="concierge"`かつ構造化スレッドが解決した場合のみ**である（`:1625-1694`、`hasStructured`チェック`:1630`）。

**この訂正がHYBRID要件評価に与える影響**: 「Personal Meaning」というPremiumカードの名前と、実際に多数派の到達経路で表示される内容（神社一般コピー）との間に、実態としての乖離がある。これは`context_reason`のような「描画されない」DEAD_POLICYとは異なる種類の問題——**「描画はされるが、個人化されていないものが個人化ラベルで提示される」**という、Content Depth戦略にとってより本質的な課題である。

**UNRESOLVED**: この①〜④のctx非依存挙動が意図的な設計（「個人化データがない場合のgraceful な一般プレビュー」）なのか、payloadV2移行時に旧来のctxゲート付きfallbackを上書きした意図しない副産物なのかは、コードのコメントからは判別できない（`buildMeaningSectionsFromPayloadV2()`にctxに関する言及は一切ない）。

---

## Phase 5 — 現行Shrine Detailの責務

「理想的な責務」ではなく、**現在の実装が実際に何を担っているか**のみを分類する。

| 責務 | 分類 | 根拠 |
| --- | --- | --- |
| 神社を知る | **PRIMARY** | 常時レンダリング・無ゲートのFact section、Deep Dive Q&A（`AllowAny`）、Hero、⑤ご利益/象徴。ページ上で唯一login/plan摩擦が皆無な責務 |
| Recommendationを理解する | **SECONDARY** | `reasonSection`（`:423-518`）は実際に`conciergeBreakdown`/rank dataから構築されるが、`ctx==="concierge"`限定または`reasonV4.factText`（`:1635-1647`）に上書きされる。専用UIである`RecommendationMetaSection`はdead codeのため、専用サーフェスとしては機能していない |
| 自分との意味を理解する | **SECONDARY（重大な留保付き）** | 真に個人化されたコンテンツは存在するが、`ctx==="concierge"`+構造化thread限定でのみ到達（Phase 4-STALE）。それ以外の経路では同一UI枠に非個人化の一般コピーが表示される——機能は実在するが、到達率・忠実度はUIの見た目が示唆するより狭い |
| 参拝へ進む | **PRIMARY** | 無ゲートのGoogle Maps route link、参拝記録ボタン。plan/ctx依存なし |
| 記録する | **PRIMARY** | Favorite/参拝記録/振り返りいずれも完全に機能する、login-gated（planではない）実装 |
| 再訪する | **NOT_IMPLEMENTED** | 「また来てください」的な仕組みは、state-delta比較（それ自体が既にmid-flowであることを前提とする）以外に存在しない。スケジューリング/リマインダー/再訪促進コードは未発見 |
| Premium conversion | **PRIMARY** | `PremiumUpgradePrompt`・state-deltaインラインCTA・Hero差し替えという複数の実際に機能するCTA経路が存在する、ページ上で唯一PRIMARY級のPremium機構（ただしゲートする中身がPhase 4-STALEの通り常に信頼できる個人化コンテンツとは限らない） |

---

## Phase 6 — HYBRID Requirement Mapping

| HYBRID Requirement | 現行Surface | 現行Section | Current Capability | Missing Capability | Detail内収容可能性 | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Deep Interpretation | Concierge Backend（Shrine Detailではない） | ①ブロック（`ShrineProposalSection`）は`ctx==="concierge"`限定で相談要約を表示 | `interpret_consultation()`の8次元`InterpretationProfile`が計算済みだがdebug専用で破棄（`premium-personalization-deep-search-audit.md`既存FACT、本監査で再確認せず） | Shrine Detail側でこの深い解釈を受け取り表示する経路が存在しない（そもそもConcierge Backend側で未接続） | **CROSS_PAGE_CONCERN**（Deep Interpretation自体はConcierge/Recommendation Engine側の責務であり、Shrine Detailはその結果を表示するだけの下流） | `consultation_interpreter.py:260-297`（既存Audit引用） |
| Personalized Recommendation | Concierge Backend | ①〜④ブロック（真の個人化経路のみ） | `recommendation_reason_v4_detail`が`ctx==="concierge"`+構造化thread時に個人化narrativeを提供 | 他の到達経路（Direct/Map/Compass）向けの個人化データ供給経路が存在しない | **FITS_WITH_RESTRUCTURE**（現行の枠組み自体は個人化コンテンツを表示できるが、`ctx`非依存の経路がこれを薄めている——ctx依存を全経路で一貫させる、または経路によらず個人化データを供給する設計変更が必要） | `buildShrineDetailModel.ts:1625-1694` |
| Deep Recommendation Reason | Shrine Detail（②ブロック）+ Concierge Backend | `ShrineReasonSection`（kind:"reason"） | `reasonSection`/`reasonV4.factText`が実データを持つが、専用UI（`RecommendationMetaSection`）はdead code、`context_reason`カードのgateもDEAD_POLICY | 専用の「Deep Reason」表示面が機能していない（既存gate機構が両方とも死んでいる） | **ALREADY_FITS（構造としては）——ただし既存2つのgate機構（`RecommendationMetaSection`のdead code、`context_reason`のDEAD_POLICY）を機能させる、または置き換える必要がある** | `RecommendationMetaSection.tsx:14`; Phase 4 |
| Personal Meaning | Shrine Detail（①〜④ブロック、`personal_meaning`カード） | 同上 | 機構（teaser/visible二値gate）は正常動作。ただしPhase 4-STALEの通り、中身が経路依存で個人化されたりされなかったりする | 全経路で一貫した個人化データ供給 | **FITS_WITH_RESTRUCTURE**（gate機構自体はALREADY_FITSだが、コンテンツ供給ロジックの再設計が必要） | `buildShrineDetailModel.ts:84-173` |
| Personal Record | Shrine Detail（Save/参拝記録/振り返り） | 既存RECORD sections | Favorite/Visit/Reflectionはすべて機能する（ただしいずれもPremium非依存、login依存のみ） | Premium限定の「記録の深さ拡張」（既存監査`test-release-premium-boundary-audit.md`が言及したGoshuin上限のPremium非対応等）は未接続。`GoshuinLimitBadge`は存在するが未使用（dead code） | **ALREADY_FITS（構造は存在する）——PremiumとRecordを接続する具体的な差分ロジックが未実装** | `ShrineSaveButton.tsx`; `GoshuinLimitBadge.tsx:11`（dead） |

---

## Phase 7 — Architecture Option A: SAME_PAGE

前提: 現行Shrine Detailの基本構造を維持し、その中にPremium Personalized Section/Gateを置く。

| 確認項目 | 内容 |
| --- | --- |
| 既存Component再利用 | 高——`ShrineDetailSections`/`ShrineJudgeSection`/`ShrineActionSection`等の既存section描画基盤をそのまま拡張できる |
| Route変更 | なし |
| State変更 | 小——既存の`ctx`/`tid`クエリパラメータの枠内で対応可能（Phase 1のInfra調査: `buildShrineHref()`は新規named optionを追加する程度の小さな変更で拡張可能） |
| Recommendation Context保持 | 既存の`tid`→`getConciergeThreadServer()`再取得パターンをそのまま利用可能 |
| Direct Navigation | Phase 4-STALEの発見により、Direct Navigation時の①〜④の扱い（個人化データなしでどう表示するか）を明示的に設計し直す必要がある——現状は「たまたま非個人化コピーが出る」という状態 |
| Backend entitlement | 現状皆無（Phase 4）。SAME_PAGEを選んでも、Backend enforcementの欠如という技術的負債は独立して残る |
| Analytics | 既存の`ctx`/`tid`/`recommendationInstanceId`ベースのAnalytics契約をそのまま拡張可能 |
| Login | 既存の`useAuth()`パターンをそのまま再利用可能 |
| Premium CTA | 既存の`PremiumUpgradePrompt`パターンを拡張可能 |
| Record | 既存のFavorite/Visit/Reflection機構をそのまま拡張可能 |
| Test | 既存の`ShrineDetailArticle.test.tsx`（25 cases）・`buildShrineDetailModel.test.ts`（32 cases）が最も密結合——新Section追加のたびにこの2ファイルへのテスト追加が必要になる |
| Page complexity | 増加——既に`ShrineDetailArticle.tsx`は800行超、`buildShrineDetailModel.ts`も1700行超の大きなファイルであり、新規Premium sectionの追加はこれらをさらに肥大化させる |
| conditional rendering増加 | 増加——`personalMeaningVisibility`/`contextReasonVisibility`/`previousComparisonVisibility`に加えて新たな条件分岐が積み重なる |
| entry path依存 | 既存の`ctx`分岐ロジックにさらに条件が積み重なる |

**評価結果**:

| 項目 | 評価 |
| --- | --- |
| Existing Capability | HIGH（既存section描画基盤・gate機構・Analytics契約をそのまま拡張） |
| Required Change | MEDIUM（新規Section追加、Backend entitlement配線は別途必要） |
| Technical Risk | MEDIUM（単一の巨大ファイル群がさらに肥大化、条件分岐の複雑化） |
| State Risk | LOW（既存の`ctx`/`tid`パターンの延長） |
| Routing Risk | NONE（Route変更なし） |
| Test Impact | MEDIUM〜HIGH（最密結合ファイル2つへの追加テストが継続的に必要） |
| Backend Impact | LOW〜MEDIUM（新規Premium差分ロジックの追加は必要だが、既存`resolve_plan_context()`等を再利用可能） |
| Frontend Impact | MEDIUM（既存ファイルの拡張） |
| Analytics Impact | LOW（既存の`ctx`/`tid`/`recommendationInstanceId`契約をそのまま利用） |
| Known Limitation | Phase 4-STALEの「個人化データなしの経路でどう振る舞うか」という設計上の空白が、SAME_PAGEを選んでも自動的には解決しない |

---

## Phase 8 — Architecture Option B: RESTRUCTURED_DETAIL

前提: Shrine Detail自体を再構成し、神社FACTとPersonalized Experienceを同一Page内で明確に分離する。この構造の採用を決定するものではない。

| 確認項目 | 内容 |
| --- | --- |
| 既存Component再利用 | 中〜高——`ShrineFactSection`（FACT）と`ShrineJudgeSection`/`ShrineActionSection`等（Personal）は既にコード上責務が分かれているため、Component自体の再利用性は高い。ただし現在1つのフラットなスクロールに統合されている構造の組み替えが必要 |
| Route変更 | なし（同一Route内の再構成） |
| State変更 | 小〜中（既存の`ctx`/`tid`をそのまま利用可能だが、tab/anchor等の新しいUI状態管理が必要になる可能性） |
| Recommendation Context保持 | SAME_PAGEと同様、既存パターンで対応可能 |
| Direct Navigation | 明確な分離により、「FACTセクションは常に見せる」「Personalizedセクションは個人化データの有無に応じて明示的に空状態を示す」という設計がしやすくなる（現状のような曖昧な非個人化コピーの混入を避けやすい） |
| Backend entitlement | SAME_PAGEと同じく、現状皆無という技術的負債は独立 |
| Analytics | 既存契約の拡張で対応可能だが、section再編に伴うcardId/イベント名の見直しが必要になる可能性 |
| Component responsibility再編 | 必要——`buildShrineDetailModel.ts`（1700行超）の出力構造自体を「FACT群」「Personalized群」に明確に分離する再設計が必要 |
| existing builder再利用性 | 高——`buildShrineFactSection.ts`・`buildMeaningSectionsFromPayloadV2()`等、個々のbuilder関数自体は責務が既に分かれているため、それらの「呼び出し方・組み合わせ方」を変えるだけで対応できる可能性がある |
| section ordering | 変更が必要（現状はFACTとPersonalizedが交互に近い順序で並ぶ） |
| navigation anchor/tab等の必要性 | 検討対象になり得る——Phase 1のInfra調査で、`mypage`/`plan`に既存のquery-param tabパターンの前例があることを確認済み（`mypage/tabs.ts`, `plan/PlanView.tsx`のtab query param） |
| current testsへの影響 | 大——`ShrineDetailArticle.test.tsx`（25 cases）・`buildShrineDetailModel.test.ts`（32 cases）はいずれも現行の「単一フラット構造」を前提にしたテストが多く、構造再編に伴い広範な書き直しが必要になる可能性が高い |
| direct entry時のPersonalized section behavior | RESTRUCTURED_DETAILを機に、Phase 4-STALEで発見した「非個人化コピーが個人化ラベルで出る」問題を明示的に解消する設計機会になり得る（ただし本監査はこれを推奨しない） |

**評価結果**:

| 項目 | 評価 |
| --- | --- |
| Existing Capability | MEDIUM（個々のbuilder/componentは再利用可能だが、組み合わせ方の再設計が必要） |
| Required Change | HIGH（`buildShrineDetailModel.ts`の出力構造自体の再設計、tab/anchor UIの新設検討） |
| Technical Risk | MEDIUM〜HIGH（大規模な内部リファクタ、既存Analyticsイベントとの整合維持） |
| State Risk | LOW〜MEDIUM（tab状態管理を追加する場合はやや増加） |
| Routing Risk | NONE（Route変更なし） |
| Test Impact | HIGH（最も密結合な2ファイルの広範な書き直し） |
| Backend Impact | LOW〜MEDIUM（SAME_PAGEと同水準） |
| Frontend Impact | HIGH（構造再設計） |
| Analytics Impact | MEDIUM（section再編に伴うイベント/プロパティの見直し） |
| Known Limitation | Route自体は変わらないため、SEPARATE_PREMIUM_EXPERIENCEが持つ「Backend側で明確にPremium専用エンドポイントを新設する」という強制力は生まれない |

---

## Phase 9 — Architecture Option C: SEPARATE_PREMIUM_EXPERIENCE

前提: Shrine Detailは「神社そのものを知るSurface」として維持し、「ユーザー×神社」のPersonalized Premium Experienceを別Route/別Surfaceへ分離する。概念例であり実装指示ではない。

| 確認項目 | 内容 |
| --- | --- |
| 新Routeの必要性 | Y（新設が前提） |
| Recommendation Context受け渡し | **強い既存Precedentあり**——`apps/web/src/app/mypage/history/[tid]/page.tsx`が、`tid`のみをURLパラメータとして受け取り、`getConciergeThreadServer(tid)`でServer-side再取得する、まさにOption Cが必要とする形を本番で既に実装している（Infra Agent確認、FACT） |
| shrine id | 既存の`buildShrineHref()`が`subpath`オプションを既にサポートしており（`shrines/[id]/goshuins`が実例）、`shrines/[id]/premium`のような新規sub-routeへの拡張は技術的に小さな変更で可能（INFERENCE、`buildShrineHref.ts:47,71-72`のsubpath機構から） |
| consultation/recommendation state | `tid`（thread id）のURL round-tripのみで再取得可能（既存パターンの延長、上記Precedent参照）。ただし`recommendation_instance_id`/`recommendation_rank`（Compass経由）は現状threadから再導出できないフィールドのため、これらを必要とする場合は別途URL経由で運ぶ必要がある（UNRESOLVED、Infra Agent報告） |
| reload耐性 | 高——Server-side再取得ベースのため、ページreloadでも`tid`さえURLにあれば状態は再構築される（既存`mypage/history/[tid]`と同じ耐性） |
| Direct URL | 対応可能（Server Componentとして`tid`必須のURLを設計すれば良い） |
| authentication | 既存の`ConciergeThreadDetailView`（`AllowAny`、`anonymous_id`cookieでスコープ）がそのまま再利用可能——新規認可ロジックは不要（Infra Agent確認） |
| entitlement | 新設が必要（SAME_PAGE/RESTRUCTURED_DETAILと同じくBackend側は現状皆無）。ただし新規独立Routeを作ることで、「Premium専用エンドポイント」として最初からentitlement checkを組み込む設計がしやすい（既存の`resolve_plan_context()`/`is_premium_for_user()`を新規Viewへ組み込むだけで対応可能、Infra Agent確認） |
| Backend API | 新規エンドポイントが必要。ただし`concierge_explanation_payload.py`・`recommendation_reason_v4.py`・`shrine_meaning_composer.py`という既存の3つのサービスが「Deep Recommendation Reason」「Personal Meaning」相当のデータを既に生成しており、これらを新規Viewで合成するだけで多くを賄える可能性がある（Infra Agent確認、新規ロジックは「組み合わせるView」自体のみ） |
| Personal Recordとの統合 | UNRESOLVED（既存のReflection/Visit機構との接続方法は本監査では特定できず） |
| Route/Visitとの関係 | 既存のRoute機能（`GoogleMapRouteLink`）はShrine Detail側に残すか、新Route側にも複製するかは未決定（Product Decision） |
| Analytics funnel | 既存の`ctx`/`tid`/`recommendationInstanceId`のURL-param連鎖を新Routeへも継承する必要がある（既存の「Result⇔Detail duplicate-exposure join」契約の拡張として、新Routeでも同じプロパティを引き継ぐ設計が必要、Infra Agent確認） |
| Browser back | UNRESOLVED（新Routeからの戻り先設計は本監査では評価していない） |
| Deep Link | Direct URL対応と同様、`tid`ベースの設計であれば対応可能 |
| existing components再利用 | 中——`ShrineJudgeSection`/`ShrineActionSection`等のPersonalized系Componentはそのまま新Routeへ移植可能な可能性が高いが、`ShrineFactSection`等のFACT系は残す/複製しないという判断が必要 |
| Test impact | 新規Route用のテストスイートが必要（既存の`ShrineDetailArticle.test.tsx`等への直接的な破壊的変更は最小限で済む可能性——既存Testを壊さずに新規追加できる） |

**評価結果**:

| 項目 | 評価 |
| --- | --- |
| Existing Capability | MEDIUM（`mypage/history/[tid]`という強いPrecedent、既存Backend service群の再利用可能性） |
| Required Change | HIGH（新規Route、新規Backend View、Analytics funnel拡張が必要） |
| Technical Risk | MEDIUM（新規構築だが、確立されたPrecedentパターンをなぞれるため予測可能性は高い） |
| State Risk | LOW（既存の`tid`ベースServer再取得パターンをそのまま踏襲可能） |
| Routing Risk | MEDIUM（新Route設計、Browser back/Deep Link動作の検証が必要） |
| Test Impact | MEDIUM（既存テストへの破壊は少ないが、新規テストスイート一式が必要） |
| Backend Impact | HIGH（新規エンドポイント・新規entitlement配線が必要、ただし既存service再利用可） |
| Frontend Impact | HIGH（新規ページ一式） |
| Analytics Impact | MEDIUM〜HIGH（既存funnel契約の新Routeへの拡張設計が必要） |
| Known Limitation | 「shrine-scoped」（`shrines/[id]/goshuins`的）と「personalized/premium separate」（`mypage/history/[tid]`的）という2つの既存パターンの組み合わせ自体には、repo内に直接の前例がない（両者は個別には存在するが、統合されたことはない） |

---

## Phase 10 — Architecture Comparison Matrix

Product Decisionは行わない。総合点・Winnerは付けない。

| Dimension | SAME_PAGE | RESTRUCTURED_DETAIL | SEPARATE_PREMIUM_EXPERIENCE |
| --- | --- | --- | --- |
| Existing Component Reuse | HIGH | MEDIUM | MEDIUM |
| New Component Need | LOW | MEDIUM | HIGH |
| Route Change | NONE | NONE | HIGH |
| State Complexity | LOW | MEDIUM | LOW |
| Entry Path Complexity | MEDIUM（既存`ctx`分岐がさらに増加） | MEDIUM | LOW（新Routeは`tid`のみに単純化できる可能性） |
| Backend Change | LOW〜MEDIUM | LOW〜MEDIUM | HIGH |
| Entitlement Enforcement | UNRESOLVED（現状皆無、どのOptionでも新設が必要な点は共通） | UNRESOLVED（同左） | UNRESOLVED（同左だが新規Route新設が「最初からentitlementを組み込む」機会にはなり得る） |
| Analytics Change | LOW | MEDIUM | MEDIUM〜HIGH |
| Test Impact | MEDIUM〜HIGH（既存最密結合ファイルへの継続的追加） | HIGH（既存最密結合ファイルの広範な書き直し） | MEDIUM（新規スイート一式、既存への影響は最小） |
| Mobile Impact | OUT_OF_SCOPE | OUT_OF_SCOPE | OUT_OF_SCOPE |
| Test Release Scope | MEDIUM | HIGH | HIGH |
| Known Technical Risk | MEDIUM（既存巨大ファイルのさらなる肥大化） | MEDIUM〜HIGH（大規模内部リファクタ） | MEDIUM（新規構築だが強いPrecedentあり、予測可能性は比較的高い） |

---

## Phase 11 — Test Release Implementation Size

3案それぞれについて、Web Test Releaseまでに必要となる変更を実装せず洗い出す。

### SAME_PAGE

| 分類 | 変更内容 | 分類（REQUIRED/OPTIONAL/FUTURE/UNKNOWN） | 対象候補ファイル |
| --- | --- | --- | --- |
| Frontend | 新規Premium sectionの`ShrineDetailArticle.tsx`/`buildShrineDetailModel.ts`への追加 | REQUIRED | `ShrineDetailArticle.tsx`, `buildShrineDetailModel.ts` |
| Frontend | `personal_meaning`カードのctx非依存問題（Phase 4-STALE）への対処 | REQUIRED（HYBRID要件の「個人化」を実質的に満たすため） | `buildShrineDetailModel.ts:84-173` |
| Frontend | `context_reason`のDEAD_POLICY是正 | OPTIONAL（本監査は修正しないが、Test Release前に認識共有は必要） | `ShrineDetailArticle.tsx:104-120` |
| Backend | `ShrineMeaningView`等へのentitlement enforcement追加 | REQUIRED（Backend enforcementなしのままPremium訴求を強化するのはリスク） | `shrine_meaning.py` |
| Backend | 新規Premiumデータ用の追加フィールド | REQUIRED（拡張内容次第） | `shrine_meaning_composer.py` |
| Routing | なし | — | — |
| State | `ctx`/`tid`拡張が必要な場合の`buildShrineHref()`更新 | OPTIONAL | `buildShrineHref.ts` |
| Authentication | 変更なし | — | — |
| Premium Entitlement | `resolve_plan_context()`の新規View/箇所への配線 | REQUIRED | `plan_service.py`, `shrine_meaning.py` |
| Analytics | 新規Premium section用イベント/プロパティ追加 | OPTIONAL〜REQUIRED（KPI次第） | `cardVisibility.ts`, 各種analytics lib |
| Tests | `ShrineDetailArticle.test.tsx`/`buildShrineDetailModel.test.ts`への追加 | REQUIRED | 同上テストファイル |
| Documentation | Product文書更新 | REQUIRED | `docs/product/premium-experience.md`等 |

### RESTRUCTURED_DETAIL

| 分類 | 変更内容 | 分類 | 対象候補ファイル |
| --- | --- | --- | --- |
| Frontend | `buildShrineDetailModel.ts`出力構造の再設計（FACT/Personalized分離） | REQUIRED | `buildShrineDetailModel.ts` |
| Frontend | Section再編・順序変更・tab/anchor UI検討 | REQUIRED | `ShrineDetailArticle.tsx` |
| Backend | SAME_PAGEと同水準のentitlement追加 | REQUIRED | `shrine_meaning.py` |
| Routing | なし（同一Route内） | — | — |
| State | tab状態管理を採用する場合の新規実装 | OPTIONAL | 新規（既存`mypage/tabs.ts`パターン参考） |
| Authentication | 変更なし | — | — |
| Premium Entitlement | SAME_PAGEと同水準 | REQUIRED | `plan_service.py` |
| Analytics | Section再編に伴うイベント/プロパティの見直し | REQUIRED | 各種analytics lib |
| Tests | `ShrineDetailArticle.test.tsx`（25 cases）・`buildShrineDetailModel.test.ts`（32 cases）の広範な書き直し | REQUIRED | 同上 |
| Documentation | Product文書更新+設計文書の新規作成 | REQUIRED | 同上 |

### SEPARATE_PREMIUM_EXPERIENCE

| 分類 | 変更内容 | 分類 | 対象候補ファイル |
| --- | --- | --- | --- |
| Frontend | 新規Route/Page一式（`mypage/history/[tid]`パターンを踏襲） | REQUIRED | 新規（例: `app/shrines/[id]/premium/`等、未定） |
| Frontend | 既存Personalized Componentの新Routeへの移植/複製判断 | REQUIRED | `ShrineJudgeSection.tsx`, `ShrineActionSection.tsx`等 |
| Backend | 新規Premium専用エンドポイント | REQUIRED | 新規View（`concierge_explanation_payload.py`/`recommendation_reason_v4.py`/`shrine_meaning_composer.py`の再利用を検討） |
| Routing | `buildShrineHref()`への`subpath`拡張、または独立Route設計 | REQUIRED | `buildShrineHref.ts` |
| State | 新Routeでの`tid`再取得ロジック（`getConciergeThreadServer`再利用） | REQUIRED（ただし既存パターン踏襲のため実装コストは低め） | 新規page.tsx |
| Authentication | 既存`ConciergeThreadDetailView`（`AllowAny`+anonymous_id scoping）を再利用 | OPTIONAL（新規ロジック不要の可能性） | `concierge.py:88-128` |
| Premium Entitlement | 新規View新設時に最初から組み込み | REQUIRED | 新規View |
| Analytics | 既存funnel契約（`ctx`/`tid`/`recommendationInstanceId`）の新Routeへの拡張 | REQUIRED | 各種analytics lib |
| Tests | 新規テストスイート一式 | REQUIRED | 新規テストファイル |
| Documentation | 新規Surfaceの設計文書、既存Shrine Detail文書との責務分離の明文化 | REQUIRED | 新規+既存文書更新 |

---

## Phase 12 — Mother Ship Decision Input

選択肢は固定。各Optionについて以下のみ記載する。Winner/推奨案/順位/スコアリングは付けない。

### Option A: `SAME_PAGE`

- **Current FACT**: 現行Shrine Detailは既に`personal_meaning`/`previous_comparison`という機能するteaser gateと、`context_reason`という機能しないDEAD_POLICYを併せ持つ（Phase 4）。①〜④ブロックの中身は経路依存で個人化されたりされなかったりする（Phase 4-STALE）。
- **Existing Capability**: 既存section描画基盤・gate機構・Analytics契約・既存3つのBackend service（explanation payload/reason v4/meaning composer）をそのまま拡張利用できる（Phase 6-7）。
- **Required Change**: 新規Premium section追加、Backend entitlement配線、ctx非依存問題への対処（Phase 11）。
- **Missing Capability**: Backend entitlement enforcement（全Option共通で皆無）、全経路一貫した個人化データ供給。
- **Technical Risk**: 既に800〜1700行規模の巨大ファイル（`ShrineDetailArticle.tsx`, `buildShrineDetailModel.ts`）がさらに肥大化する（Phase 7）。
- **Test Release Impact**: MEDIUM（既存最密結合テストファイルへの継続的追加、Phase 10）。
- **Unresolved Questions**: ctx非依存の①〜④コンテンツが意図的設計か副産物か（Phase 4-STALE）が未解決のまま拡張すると、同じ曖昧さを新機能にも継承するリスクがある。

**Codex Recommendation: NONE**

### Option B: `RESTRUCTURED_DETAIL`

- **Current FACT**: `buildShrineFactSection.ts`（FACT）と`buildMeaningSectionsFromPayloadV2()`等（Personalized）は既にコードレベルで責務が分かれているが、`buildShrineDetailModel.ts`の出力・`ShrineDetailArticle.tsx`の描画順序では明確に分離されていない（Phase 2, 8）。`mypage`/`plan`に既存のquery-param tabパターンの前例がある（Phase 9 Infra確認）。
- **Existing Capability**: 個々のbuilder/componentの再利用性は高い（Phase 8）。
- **Required Change**: `buildShrineDetailModel.ts`の出力構造自体の再設計、Section再編、既存Analyticsイベントとの整合維持（Phase 11）。
- **Missing Capability**: Backend entitlement enforcement（Option A同様）。
- **Technical Risk**: 大規模内部リファクタ、既存テスト（合計57 cases）の広範な書き直しリスク（Phase 8, 10）。
- **Test Release Impact**: HIGH（Phase 10-11）。
- **Unresolved Questions**: tab/anchor UIを採用するか、単純な垂直分離に留めるかは未検討（本監査スコープ外）。

**Codex Recommendation: NONE**

### Option C: `SEPARATE_PREMIUM_EXPERIENCE`

- **Current FACT**: `apps/web/src/app/mypage/history/[tid]/page.tsx`が、Option Cの核となる技術形状（`tid`のみでServer-side全再取得、状態管理プラミング不要）を本番で既に実装している（Phase 9 Infra確認、強いPrecedent）。`shrines/[id]/goshuins`が「shrine-scoped separate route」のもう半分の前例。両パターンの組み合わせ自体はrepo内に前例がない。
- **Existing Capability**: `ConciergeThreadDetailView`（`AllowAny`+anonymous_id scoping）、および`concierge_explanation_payload.py`/`recommendation_reason_v4.py`/`shrine_meaning_composer.py`という3つの既存Backend serviceの再利用可能性（Phase 9）。
- **Required Change**: 新規Route、新規Backend Premium専用View、Analytics funnel拡張（Phase 11）。
- **Missing Capability**: 新規Viewでのentitlement組み込み自体は未実装（ただし「新規だからこそ最初から組み込みやすい」という性質がある）。Personal Recordとの統合方法（UNRESOLVED、Phase 9）。
- **Technical Risk**: 新規構築のためHIGHの変更量だが、確立されたPrecedentパターンをなぞれるため予測可能性は比較的高い（Phase 9-10）。
- **Test Release Impact**: HIGH（新規Route一式が必要、Phase 10-11）だが、既存Shrine Detailテストへの破壊的影響は他の2Optionより小さい可能性がある。
- **Unresolved Questions**: `recommendation_instance_id`/`recommendation_rank`（Compass経由）をthreadから再導出できない問題（Phase 9）、Route/Visit機能をどちらのSurfaceに残すか（Phase 9）、Browser back/Deep Link挙動（Phase 9）。

**Codex Recommendation: NONE**

---

## Unresolved（Decision外の補足、Phase横断で再掲）

1. ①〜④ブロックのctx非依存挙動が意図的設計か副産物か（Phase 4-STALE）。
2. `askDeepDive()`/`createShrineReflection()`のBackend側認証要件の一部細部（`ShrineReflectionPrompt`は`reflection.py`で`IsAuthenticated`確認済みだが、Deep Diveの認証要件はPart 2で`AllowAny`確認済み——両者とも本監査で解決済み。ただし御朱印**投稿**（読み取りではなく書き込み）エンドポイントの正確な権限クラスは未追跡）。
3. `previous_comparison`のFree層向け合成`"teaser"`上書き（宣言ポリシー`"hidden"`との不一致）が意図的なProduct判断か、実装上の見落としか。
4. Option Cにおける`recommendation_instance_id`/`recommendation_rank`（Compass経由）の新Routeへの受け渡し方法。
5. Option Cにおける既存Route/Visit機能をどちらのSurfaceに残すかの判断。
6. `HomeGoshuinFeedSection.tsx`/`MyGoshuinTopSection.tsx`がどのトップレベルRouteに組み込まれているか（未追跡）。

---

## Evidence / Files 参照一覧

### Frontend（Web）

- `apps/web/src/app/shrines/[id]/page.tsx`
- `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`, `ShrineDetailHeroCard.tsx`, `ShrineFactSection.tsx`, `ShrineReflectionPrompt.tsx`, `ShrineReasonSection.tsx`, `ShrineProposalSection.tsx`, `ShrineJudgeSection.tsx`, `ShrineActionSection.tsx`, `ShrineSupplementSection.tsx`, `RecommendationMetaSection.tsx`, `GoshuinLimitBadge.tsx`
- `apps/web/src/components/shrine/ShrineDetailShell.tsx`, `ShrineCloseLink.tsx`, `ShrineDetailViewTracker.tsx`, `ShrineDetailToast.tsx`, `ShrineSaveButton.tsx`, `GoogleMapRouteLink.tsx`, `ConciergeShrineCard.tsx`, `PublicGoshuinSection.tsx`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`, `buildShrineFactSection.ts`
- `apps/web/src/lib/nav/buildShrineHref.ts`
- `apps/web/src/lib/premium/cardVisibility.ts`, `accessLevel.ts`
- `apps/web/src/lib/api/billing.server.ts`, `shrineMeaning.server.ts`, `concierge.server.ts`
- `apps/web/src/app/mypage/history/[tid]/page.tsx`, `apps/web/src/app/shrines/[id]/goshuins/page.tsx`
- `apps/web/src/app/plan/page.tsx`, `PlanView.tsx`, `apps/web/src/app/mypage/tabs.ts`
- `apps/web/src/features/compass/components/CompassRecommendationsSection.tsx`
- `apps/web/middleware.ts`
- テスト: `apps/web/src/lib/shrine/__tests__/buildShrineDetailModel.test.ts`, `apps/web/src/components/shrine/detail/__tests__/ShrineDetailArticle.test.tsx`, `apps/web/src/app/shrines/[id]/__tests__/page.test.tsx`

### Backend

- `backend/temples/api/views/shrine_meaning.py`, `shrine.py`, `deep_dive.py`
- `backend/temples/services/shrine_meaning_composer.py`, `evidence_gate.py`, `plan_service.py`, `billing_state.py`
- `backend/temples/api/views/concierge.py`（`ConciergeThreadDetailView`）
- `backend/favorites/views.py`, `backend/temples/api/views/visit.py`, `reflection.py`, `goshuin_feed.py`, `goshuin.py`
- テスト: `backend/temples/tests/test_shrine_meaning_endpoint.py`, `test_shrine_meaning_composer.py`, `backend/temples/tests/api/test_shrine_detail_knowledge_api.py`

### 参照した既存文書（重複作成を避けるため確認済み、上書きしない）

- `docs/audit/test-release-premium-boundary-audit.md`（PR #2617）
- `docs/audit/premium-personalization-deep-search-audit.md`（PR #2619、本監査が`AUDIT_STALE`として訂正した箇所を含む）

---

## 責務境界

本書は「現行Shrine DetailのHYBRID Premium体験に対する構造的収容力を、Evidenceに基づいて整理すること」のみを責務とする。以下は対象外であり、実施していない。

- Shrine Detail UI・Component・Route・Recommendation Ranking・Score・Free Text処理・Signal Extraction・InterpretationProfile・Recommendation Reason・Premium Gate・Billing・Subscription・Quota・Authentication・Favorite・Reflection・Record・Analytics・Backend API・Serializer・DB・Schema・Migration・Test・Copy・Mobileの変更
- 新しいPremium Pageの実装、新しいRouteの実装、Gate修正、Backend enforcement修正、`context_reason`修正、既存bugの修正、unrelated refactor
- Product Decision（Decision A-1・Decision B以降の代理決定を含む）
- Compass Premium設計

発見した問題（`context_reason`のDEAD_POLICY、`PublicGoshuinSection`/`GoshuinLimitBadge`のdead code、①〜④のctx非依存挙動、`accessLevel`のisAuthenticatedハードコード等）はすべて修正せずAuditへ記録するに留めた。

## 更新ルール

- 本書は時点記録（Historical）であり、以降の実装変更によって内容は陳腐化しうる。継続的な更新は行わない。
- Decision A-1が確定した場合、その決定は別途Product文書で記録し、本書へ遡及反映はしない。
