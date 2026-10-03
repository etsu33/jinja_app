# Web Worldview Real-data Visual QA Gate

## 1. Purpose

PR #2968 / #2974 で確立した KAMI MUSUBI Web Worldview
（Deep Ink Navy + restrained shrine-gold）が、実データ・認証済み状態・各種ステータス表示でも
破綻せず成立していることを確認する。

本監査は **実装ではなく観測と分類を先に行う Gate** とする。

Mother Ship decision:

> Semantic State Polish より先に Real-data Visual QA を行う。
> 状態色・Premium・selection・saved・disabled 等の再設計は、
> 実データ表示で問題が再現された箇所だけを根拠付きで後続 PR に切り出す。

理由:
- #2974 は Worldview 基盤を全 user-facing route へ展開したが、実データ表示を確認できない route / state が残った。
- 状態色には semantic responsibility があり、見た目だけで一括置換すると意味境界を壊す。
- 先に実データ状態を観測すれば、Worldview regression と既存 semantic-state 問題を分離できる。

## 2. Baseline

- Base branch: `develop`
- Baseline merge: PR #2974
- Baseline commit: `c2ed75e22d768b7916a410b5524b42b839b5f3a5`
- Web Worldview Foundation: PR #2968
- App-wide rollout: PR #2974

この監査中は Worldview Token / Backdrop / Frame の設計を変更しない。

## 3. Scope

### Primary real-data targets

1. Concierge
   - 相談入力後
   - 推薦結果
   - Top Recommendation Hero
   - Other Recommendations
   - Premium preview / Premium state
   - disabled / selection / notice states

2. Shrine Detail
   - 実在神社の詳細
   - Hero
   - Fact / Meaning
   - Judge / Proposal / Reflection
   - Deep Dive
   - Save / Favorite
   - Goshuin section

3. Goshuin
   - 一覧あり
   - 空状態
   - 新規登録
   - 公開プロフィール表示

4. MyPage / Favorites
   - 認証済み通常状態
   - 空状態
   - データあり
   - 履歴詳細
   - settings

5. Map
   - map tile loaded
   - shrine marker / panel
   - current-location related UI
   - sheet / overlay / sticky UI

6. Ranking / Populars
   - データあり
   - top-ranked state
   - card states

7. Billing / Premium
   - current plan
   - upgrade
   - manage
   - success / cancel
   - CTA hierarchy

### Secondary targets

- Auth
- Shrine submission
- Consultation history
- Public user pages
- Terms / Privacy
- 404 / error boundaries

Secondary target は regression が見つかった場合だけ深掘りする。

## 4. Viewport Matrix

最低限:

- 375 px
- 390 px
- 430 px
- 1280 px

実データ確認では 390 px を主観測幅とし、
問題が見つかった画面だけ 375 / 430 / 1280 へ横展開して確認する。

## 5. Visual QA Contract

各対象 state で以下を確認する。

- Header / page / Footer に色の継ぎ目がない
- page ground が Deep Ink Navy のまま
- WorldviewBackdrop が 1 画面 1 個
- Gold Path が本文の可読性を邪魔しない
- 文字コントラストが崩れていない
- white / light neutral の accidental surface が残っていない
- Forest green の neutral surface が再出現していない
- semantic color が意味を維持している
- disabled が disabled と認識できる
- selected / saved が neutral card と区別できる
- success / warning / error が相互に区別できる
- Premium が通常 UI と区別できる
- focus ring が確認できる
- sticky / fixed UI が backdrop より前面
- dialog / sheet / modal / overlay が正常
- 画像・地図・御朱印画像が Worldview 装飾に負けない
- 横スクロールが発生しない
- 実データの長文で overflow / clipping が起きない

## 6. Finding Classification

発見事項は必ず次のいずれかに分類する。

### A. WORLDVIEW_REGRESSION

#2974 によって発生した回帰。

例:
- Navy 化による文字不可視
- Backdrop の重複
- Header / Footer seam
- token migration による contrast regression

対応:
- 本監査 PR では記録のみ。
- 修正は follow-up fix PR。

### B. PRE_EXISTING_SEMANTIC_STATE

#2974 より前から存在した状態色 / semantic UI の問題。

例:
- light emerald surface + ivory text
- Forest 由来 disabled / saved / selection color
- semantic state の contrast 不足

対応:
- Semantic State Polish 候補へ送る。

### C. CONTENT_DATA_STRESS

実データの長さ・件数・画像比率で露呈した問題。

例:
- 長い神社名
- 長文 explanation
- 多数 tag
- 画像欠損

対応:
- 内容に応じて専用 UI fix へ分離。

### D. FUNCTIONAL_NON_VISUAL

見た目ではなく挙動の問題。

例:
- 認証 redirect
- API error
- map loading failure
- CTA navigation

対応:
- 本監査から分離し、該当機能 track へ送る。

### E. PASS

実データ state でも問題なし。

## 7. Evidence Record

各対象ごとに以下を記録する。

| Route / State | Auth | Data | 390px | Other widths | Finding | Classification | Follow-up |
|---|---|---|---|---|---|---|---|
| /concierge result | no | real | PASS (390x844) | 455px provisional PASS | Navy ground / header continuity / card hierarchy / long-form text / gold CTA remain readable; no horizontal overflow observed | PASS | none |
| /shrines/[id] | no | real | PASS (390x844) | 455px provisional PASS | Concierge→Shrine Detail continuity preserved; cards, history text, meaning sections remain readable | PASS | semantic-state follow-up only |
| /shrines/[id]/goshuins | no | real | TODO | TODO if needed | TBD | TBD | TBD |
| /mypage | yes | real | PASS (390x844) | not required | Logged-out gate, auth login, and authenticated profile/data state remain readable; saved shrine cards and recent consultation fit without overflow | PASS | none |
| /favorites | yes | real | PASS (390x844) | not required | Two saved shrines, addresses, detail links and remove buttons fit without overflow; Navy surface hierarchy and footer continuity hold | PASS | none |
| /goshuin/new | yes | n/a | NOT VERIFIED | not required | Current repo keeps /goshuin/new, but /goshuins and /goshuins/public redirect to /; feature is treated as mostly closed for this audit | NOT VERIFIED | defer unless Goshuin flow is reopened |
| /map | yes | real | PARTIAL (390x844) | not required | Worldview/list cards render correctly, but current MapPageClient does not render a map when viewMode=map; the toggle changes state only | FUNCTIONAL_NON_VISUAL | separate map-view implementation task |
| /populars | no | real | COVERED via /ranking popular tab (390x844) | not required | Popular ranking data renders; same rank-highlight contrast issue applies to #1/#3 cards | PRE_EXISTING_SEMANTIC_STATE | shared RankingList fix |
| /ranking | no | real | FAIL visual state (390x844) | responsive expansion not needed before fix | Rank #1/#3 use hard-coded light yellow/amber surfaces while text inherits near-white dark-theme foreground, causing severe contrast loss | PRE_EXISTING_SEMANTIC_STATE | dedicated Ranking semantic-surface fix PR |
| /billing | yes | real | PASS with CTA note (390x844) | not required | Current Free plan card and gold upgrade CTA are readable; upgrade page primary CTA remains neutral surface-emphasis and is visually weaker than the gold action CTA | PRE_EXISTING_SEMANTIC_STATE | CTA hierarchy decision for later polish |
| /billing/manage | yes | local stub/free | PASS shell / Stripe portal NOT VERIFIED (390x807) | production check required separately | Free-plan management shell is readable; Stripe Customer Portal is intentionally not invoked for Free accounts and was not exercised in local stub mode | PASS + NOT VERIFIED external portal | verify production Stripe configuration and Premium customer flow separately |

Screenshot 自体は repository へ commit しない。
PR 本文または GitHub attachment / QA note で evidence を参照する。


### 7.1 Concierge / Shrine Detail — 390px formal observation (2026-09-24)

Input used:

> 最近、仕事について少し迷っています。今後の方向性を整理したくて、落ち着いて考えられる神社に行きたいです。人が多すぎず、静かに参拝できる場所が希望です。

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 844**
- flow: Home input → `/concierge?tid=9` → `/shrines/59?ctx=concierge&tid=9`
- earlier 455px screenshots are treated as provisional corroborating evidence only

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| Home input at 390px | Header controls fit, input surface remains within viewport, Gold Path stays subordinate, no visible horizontal overflow | PASS | none |
| Concierge result / top recommendation | Deep Ink Navy ground, surface hierarchy, title, reference info and recommendation copy remain readable at 390px | PASS | none |
| Concierge emerald semantic labels | Emerald labels remain readable but visually sit outside the Navy + shrine-gold neutral language | PRE_EXISTING_SEMANTIC_STATE | Semantic State Polish candidate |
| Long-form concierge copy | Line length and wrapping remain readable; no clipping or overflow observed in supplied evidence | PASS | none |
| Shrine Detail / real shrine data | Shrine title, address, deity chips, history cards and meaning sections remain readable at 390px; route continuity is preserved | PASS | none |
| Premium / login deeper-meaning block | Dark green surface and gold text remain readable but visually stand apart from the canonical Navy neutral system | PRE_EXISTING_SEMANTIC_STATE | Semantic State Polish candidate |
| Header / page continuity | No Forest / white seam observed in supplied 390px evidence | PASS | none |
| Gold Path readability | Decorative line remains low-contrast and does not visibly cross text at a disruptive intensity | PASS | none |
| Horizontal layout | No visible horizontal scrolling or viewport escape in supplied evidence | PASS | none |

Formal classification for this pass:

```text
WORLDVIEW_REGRESSION            = 0 observed
PRE_EXISTING_SEMANTIC_STATE     = 2 observed patterns
CONTENT_DATA_STRESS             = 0 observed
FUNCTIONAL_NON_VISUAL           = 0 observed in this pass
PASS                            = Concierge / Shrine Detail core Worldview
```

The two semantic-state patterns are **not blockers for PR #2974's Worldview rollout**.
They are candidates for a later Semantic State Polish PR and must not be changed inside this audit PR.

Not covered by this evidence:
- Concierge loading state
- explicit disabled state
- selected/saved state
- authenticated Premium state
- Footer end-of-page seam
- 375 / 430 / 1280 expansion for these real-data states

Per the viewport policy, extra widths are required only where a problem is found.
The semantic-state findings are color-language issues rather than 390px layout failures, so no responsive expansion is required for the core Concierge/Shrine layout at this point.


### 7.2 MyPage / Auth — 390px formal observation (2026-09-24)

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 844**
- states:
  - `/mypage?tab=profile` while logged out
  - `/auth/login?returnTo=%2Fmypage`
  - `/mypage` after successful authentication
- authenticated MyPage contained:
  - account name / plan badge / email
  - recent consultation
  - two saved shrines with addresses
  - settings entry

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| MyPage logged-out gate | Navy ground, card surface, gold login CTA and footer remain visually continuous; no white/Forest seam | PASS | none |
| Auth login form | Labels, inputs, gold primary CTA and registration link remain readable; Gold Path stays decorative and does not disrupt form readability | PASS | none |
| Login → MyPage return flow | The supplied evidence shows the authenticated MyPage state after login; no visual discontinuity was observed across the transition | PASS | none |
| MyPage authenticated account card | Account name, FREE badge and email retain hierarchy on Navy surfaces | PASS | none |
| Recent consultation card | Real text truncation and date fit inside the card at 390px; no visible horizontal overflow | PASS | none |
| Saved shrines list | Two real shrine names and addresses fit within card bounds; nested cards preserve surface hierarchy | PASS | none |
| Footer / short-page ground | Logged-out MyPage and Login both show the footer above remaining viewport ground without a color seam; the ground stays Deep Ink Navy below it | PASS | none |
| Header authenticated state | MyPage / Logout controls fit at 390px and remain visually subordinate to page content | PASS | none |

Formal classification for this pass:

```text
WORLDVIEW_REGRESSION            = 0 observed
PRE_EXISTING_SEMANTIC_STATE     = 0 newly observed
CONTENT_DATA_STRESS             = 0 observed
FUNCTIONAL_NON_VISUAL           = 0 observed in supplied flow
PASS                            = MyPage / Auth core Worldview
```

This evidence also closes the previously open **Footer end-of-page seam** check for the supplied short-page states.

Not covered by this evidence:
- `/mypage/history`
- `/mypage/history/[tid]`
- `/mypage/settings`
- Favorites
- authenticated empty-state variants
- Premium account state

Per the viewport policy, no 375 / 430 / 1280 expansion is required for these states because no 390px layout or Worldview regression was observed.


### 7.3 History / Favorites / Billing / additional Shrine evidence — 390px formal observation (2026-09-24)

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 844**
- states:
  - `/mypage/history`
  - `/favorites`
  - `/shrines/10`
  - `/billing/upgrade`
  - `/billing`
  - `/billing/success?checkout_session_id=stub_checkout_1`
  - external Google Maps route opened from shrine detail

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| MyPage history list | Real consultation title, summary, date and reflection count fit inside a single card at 390px; footer seam remains absent | PASS | none |
| Favorites list | Two saved shrines with real names/addresses fit without horizontal overflow; remove controls remain visible and subordinate | PASS | none |
| Additional Shrine Detail data | Multiple deity chips and several historical event cards remain readable; long historical copy wraps without clipping | PASS | none |
| Billing current plan | Free plan state is readable and the gold `プレミアムにする` action is visually clear | PASS | none |
| Billing upgrade content | Premium benefits, beta price, legal text and page hierarchy fit cleanly at 390px | PASS | none |
| Billing upgrade primary CTA | `Premiumを始める` uses the neutral `surface-emphasis` treatment, so it reads weaker than the gold action-primary CTA used on the current-plan page | PRE_EXISTING_SEMANTIC_STATE | Mother Ship CTA hierarchy decision / later Semantic State Polish |
| Billing success waiting state | Notice, refresh action and retry action remain readable; no Worldview seam or light-surface regression observed | PASS | none |
| Google Maps handoff | External Google Maps opens and renders route guidance; external provider UI is outside KAMI MUSUBI Worldview scope | PASS | internal `/map` remains separately unverified |

Formal classification for this pass:

```text
WORLDVIEW_REGRESSION            = 0 observed
PRE_EXISTING_SEMANTIC_STATE     = 1 observed pattern (Billing CTA hierarchy)
CONTENT_DATA_STRESS             = 0 observed
FUNCTIONAL_NON_VISUAL           = 0 observed in supplied flow
PASS                            = History / Favorites / Shrine data / Billing shell
```

Not covered by this evidence:
- `/mypage/history/[tid]`
- `/mypage/settings`
- `/billing/manage`
- Premium-active account state
- Billing error state
- internal `/map` UI

Per the viewport policy, no extra width expansion is required for the PASS states because no 390px layout regression was observed.

### 7.4 Goshuin scope verification (repository state, 2026-09-24)

Repository verification:
- `/goshuins` exists only as a redirect to `/`.
- `/goshuins/public` exists only as a redirect to `/`.
- `/goshuin/new` still exists as a user-facing route.

Mother Ship interpretation for this audit:
- The list/public Goshuin experience is effectively closed in the current Web product.
- `/goshuin/new` is still present technically, but no active end-to-end Goshuin flow was supplied for real-data QA.
- Do **not** reopen or redesign Goshuin inside this audit.
- Record the Goshuin primary target as **NOT VERIFIED / DEFERRED** unless the feature is explicitly returned to active MVP scope.

This satisfies the audit Done Criteria requirement to either verify a primary target or explicitly mark it NOT VERIFIED with a reason.


### 7.5 Explore Map / Ranking — 390px formal observation (2026-09-24)

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 844**
- states:
  - `/shrines` Explore entry
  - `/map`
  - `/ranking` popular tab, before and after geolocation filtering
- repository verification against current `develop`

#### Map implementation finding

Repository evidence:
- `MapPageClient` owns `viewMode` and initializes it to `"map"`.
- `viewMode` is passed into `ExploreLayout`.
- The rendered body does **not** branch on `viewMode`.
- `mode === "nearby"` always renders `NearbyShrineCardListClient`.
- `mode === "search"` renders only the selected-place card.
- No map component / map canvas is rendered from `MapPageClient`.

Therefore the current “一覧 / 地図” control exposes a **map mode label without a map implementation**.
This is not a Worldview failure and is classified as `FUNCTIONAL_NON_VISUAL`.

The current list presentation itself passes Worldview QA:
- Deep Ink Navy ground is continuous.
- cards remain within the 390px viewport.
- shrine names / addresses are readable.
- no visible horizontal overflow was observed.

#### Ranking contrast finding

Observed:
- rank #1 uses `bg-yellow-50`
- rank #3 uses `bg-amber-50`
- ranking card text inherits the dark-theme `text-card-foreground` / Worldview text hierarchy.
- address / metrics also use `--kt-color-text-secondary`, which is near-white in the current dark theme.
- supplied screenshots show the #1 / #3 card content becoming extremely low-contrast on the light ranking surfaces.

Historical verification:
- the hard-coded `bg-yellow-50` / `bg-amber-50` rank surfaces already existed before PR #2974.
- before PR #2974, dark `--card-foreground` was already a near-white ivory value.
- PR #2974 changed dark neutral text from Dark Forest ivory to Worldview ivory, but did not introduce the light ranking surfaces.

Therefore this is classified as **PRE_EXISTING_SEMANTIC_STATE**, not `WORLDVIEW_REGRESSION`.

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| /shrines Explore entry | List/explore shell remains readable and visually consistent at 390px | PASS | none |
| /map list state | Nearby shrine list renders correctly on Navy surfaces | PASS | none |
| /map map-mode control | “地図” can be selected but no map canvas/component is rendered; list content remains | FUNCTIONAL_NON_VISUAL | separate map implementation task |
| /ranking normal Navy cards | rank #2 and standard cards remain readable | PASS | none |
| /ranking rank #1 / #3 highlight cards | hard-coded yellow/amber light surfaces combine with near-white dark-theme text, causing severe contrast failure | PRE_EXISTING_SEMANTIC_STATE | Ranking semantic-surface fix |
| /ranking geolocation state | location filtering changes list content but does not alter the contrast failure pattern | PRE_EXISTING_SEMANTIC_STATE | same shared fix |

Formal classification for this pass:

```text
WORLDVIEW_REGRESSION            = 0 observed
PRE_EXISTING_SEMANTIC_STATE     = 1 confirmed pattern (ranking light rank surfaces)
CONTENT_DATA_STRESS             = 0 observed
FUNCTIONAL_NON_VISUAL           = 1 confirmed gap (map mode has no map renderer)
PASS                            = Explore shell / Map list state / normal ranking cards
```

Mother Ship follow-up split:
1. **Ranking Semantic Surface Fix**
   - keep rank hierarchy
   - remove unreadable light-surface + ivory-text combination
   - prefer semantic dark ranking surfaces / border / badge treatment
   - do not change ranking data, order, counts, favorite behavior, or API
2. **Map View Implementation**
   - separate product feature task
   - current audit only records the missing implementation
   - do not implement it inside PR #2977


### 7.6 History detail / Billing manage — 390px observation (2026-09-24)

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 807**
- states:
  - `/mypage/history/3`
  - `/billing/manage` while the authenticated account is Free
  - `/billing/success?checkout_session_id=stub_checkout_1`

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| /mypage/history/[tid] | Recommendation cards, metadata and long consultation title remain within viewport; no Worldview seam or horizontal overflow observed | PASS | none |
| /billing/manage — Free state | Current plan card, explanatory copy and navigation controls remain readable and continuous with the Navy shell | PASS | none |
| Stripe Customer Portal | Not exercised. The Free state intentionally does not call the portal endpoint. The supplied success URL contains `stub_checkout_1`, confirming this local flow is using the billing stub rather than a real Stripe checkout session | NOT VERIFIED | production Stripe configuration + Premium customer flow must be verified separately |
| /billing/success — stub pending state | Pending-status notice and actions remain readable; this proves the local stub/success shell only, not Stripe production behavior | PASS shell / NOT VERIFIED Stripe behavior | production verification |

Implementation contract verified from current repository:
- `/billing/manage` only renders the **プランを管理** button when `plan === "premium" && is_active === true`.
- In that Premium-active state, clicking the button calls `POST /api/billings/portal`.
- Backend `create_portal_session()` requires:
  - `BILLING_PROVIDER=stripe`
  - `STRIPE_SECRET_KEY`
  - a linked `UserProfile.stripe_customer_id`
- When those conditions are satisfied, the backend creates a Stripe Billing Portal session and returns `portal_url`; the browser then redirects to Stripe.
- When the provider is not Stripe, the portal endpoint is intentionally unavailable.
- Checkout behaves differently in stub mode: a fake `stub_checkout_* ` session redirects back to the local success URL instead of opening Stripe Checkout.

Therefore the local Free/stub screenshot **does not imply that production Stripe is missing or broken**.
It only proves that the local environment is not exercising a Stripe Premium customer portal flow.


### 7.7 Production billing provider direct dashboard confirmation (2026-09-24)

Evidence:
- user-provided Render Dashboard screenshot
- workspace: `エツ's workspace`
- service: `jinja-backend`
- Environment page
- visible environment row: `BILLING_PROVIDER = stripe`

Result:
- Production backend billing provider is **directly confirmed as `stripe`** in Render.
- This closes the provider-mode uncertainty for production.
- Secret values were not exposed or recorded.
- Stripe secret / price / webhook-secret presence remains a separate configuration check.
- This evidence is configuration QA only and does not prove an end-to-end live Checkout / Customer Portal transaction.

Classification:
- Production billing mode: **CONFIRMED_STRIPE**
- Local `stub_checkout_*` behavior remains expected and environment-specific.


### 7.8 Production Stripe credential presence / mode confirmation (2026-09-24)

Evidence:
- user-confirmed Render Environment presence for production backend `jinja-backend`
- secret values are not recorded
- only the Stripe secret-key mode prefix was reported

Confirmed:
- `STRIPE_SECRET_KEY`: **SET**
- secret key prefix indicates **Stripe test mode** (`sk_test_...`)
- `STRIPE_PRICE_ID`: **SET**
- `STRIPE_WEBHOOK_SECRET`: **SET**
- `BILLING_PROVIDER=stripe`: previously directly confirmed in Render

Interpretation:
- Production backend is configured to use the Stripe integration, but the current Stripe secret key is a **test-mode key**.
- Therefore this configuration must not be treated as live-charge ready.
- A Price ID uses the same `price_...` prefix in test and live mode, so presence alone does not prove its mode. It must belong to the same Stripe mode/account as the active secret key.
- A webhook signing secret (`whsec_...`) also does not reveal test/live mode from its prefix alone. Its endpoint mode must be confirmed in the Stripe Dashboard.

Release boundary:
- Keep test-mode credentials during development / QA.
- Switching to live billing must be a dedicated release gate.
- That gate must confirm a live secret key, live Price ID, live webhook endpoint/signing secret, and one controlled end-to-end Checkout → Webhook → entitlement → Customer Portal verification.
- No live credential change is part of PR #2977.


### 7.9 Stripe Dashboard Sandbox confirmation (2026-09-24)

Evidence:
- user-provided Stripe Dashboard screenshot
- Stripe Dashboard banner explicitly shows Sandbox / test mode
- visible API key prefixes:
  - secret key: `sk_test_...`
  - publishable key: `pk_test_...`
- no full secret value is recorded

Result:
- Stripe account context currently used for verification is **Sandbox / Test Mode**.
- This independently confirms the Render-side `STRIPE_SECRET_KEY` test-mode prefix.
- The current production backend may use the real Stripe integration path while still pointing at Stripe test-mode credentials.
- This is suitable for development / pre-release QA and does **not** represent live-charge readiness.

Still to verify before live release:
- `STRIPE_PRICE_ID` belongs to the same Stripe Sandbox/Test environment for current QA.
- `STRIPE_WEBHOOK_SECRET` belongs to the corresponding Sandbox/Test webhook endpoint.
- Before live billing, switch as one controlled release gate to:
  - live secret key (`sk_live_...`)
  - live publishable context where required
  - live Price ID
  - live webhook endpoint/signing secret
  - one controlled end-to-end live Checkout → Webhook → entitlement → Customer Portal verification.

No live credential change is part of PR #2977.


### 7.10 Stripe Sandbox product catalog pricing check (2026-09-24)

Evidence:
- user-provided Stripe Dashboard screenshot
- Stripe Dashboard is explicitly in Sandbox mode
- product catalog contains a product named `Premium`
- visible recurring price for that product: **¥500 JPY / month**
- current Web billing UI and Terms state **¥780 / month** for the β Early User price

Result:
- Sandbox/Test mode itself is confirmed.
- `STRIPE_PRICE_ID` alignment is **confirmed**: the Stripe Sandbox Premium recurring Price ID matches the Render `STRIPE_PRICE_ID`.
- The currently configured Stripe Sandbox Premium price is **¥500 / month**.
- The current Web billing UI and Terms state **¥780 / month**.
- Therefore the pricing configuration mismatch is **confirmed**.
- Do not change either side inside this audit PR. Mother Ship must first confirm the canonical release price, then a dedicated billing-config follow-up should align Stripe and the product copy.

Classification:
- `CONFIGURATION_MISMATCH_CONFIRMED`
- release-significant and must be resolved before paid release.


### 7.11 Mother Ship decision — β Early User canonical price (2026-09-24)

Decision:

> **β Early User price = ¥780 / month**

Product rationale:
- KAMI MUSUBI Premium is not positioned as a one-shot shrine search unlock.
- The paid value is the recurring guidance loop:
  - Concierge consultation
  - deeper explanation of why the shrine fits the current state
  - reflection on changes since prior consultations
  - Compass as a recurring-use surface
  - weekly Compass output as a reason to return between consultations
- The weekly Compass is part of the product-value hypothesis supporting a monthly subscription rather than a one-time purchase.
- Therefore Mother Ship keeps **¥780 / month** as the canonical β Early User price and treats the current Stripe Sandbox ¥500 recurring Price as configuration drift.

Follow-up boundary:
- Do not change Stripe configuration inside PR #2977.
- Create a dedicated billing configuration follow-up after this audit.
- The follow-up must align Stripe Sandbox to the canonical ¥780 / month price, update Render `STRIPE_PRICE_ID` to the matching Sandbox Price, and re-run Checkout display / webhook / entitlement QA.
- Live-mode pricing remains a separate pre-release gate.

## 8. No-change Areas

本監査 PR では変更しない。

- Worldview Token 実値
- WorldviewBackdrop geometry
- WorldviewFrame architecture
- Recommendation / ranking logic
- Concierge interpretation logic
- Backend
- Django / DB / migration
- API contract
- Analytics
- Authentication behavior
- Billing behavior
- Map provider behavior
- Mobile app
- semantic-state color values
- CTA hierarchy
- 404 copy

問題を見つけても、この PR に修正を混ぜない。

## 9. STOP Rules

以下の場合は推測で進めず STOP して記録する。

- 認証済み state を安全に作れない
- Production data の再現に write が必要
- 課金操作が実決済を発生させる
- 本番アカウント / secret の追加が必要
- Production DB を直接編集する必要がある
- 外部 provider の有料 action が必要
- observed issue が visual か functional か判定不能

## 10. Done Criteria

- Primary target をすべて確認または NOT VERIFIED と明記
- 各 finding を A〜E に分類
- Worldview regression と pre-existing semantic issue を分離
- Semantic State Polish に送る対象を確定
- 実装修正を混ぜない
- Mother Ship 向けの次 PR 分割案を作る
- 本 PR は audit 記録のみで close / merge 可能な状態にする

## 11. Next Gate

本監査完了後、Mother Ship が以下を確定する。

1. WORLDVIEW_REGRESSION fix PR の要否
2. Semantic State Polish の対象 Token / Component
3. CTA hierarchy の要否
4. 実データ content-stress fix の分割
5. 追加 QA が必要な route

Semantic State Polish は、この監査の evidence を正本として開始する。
