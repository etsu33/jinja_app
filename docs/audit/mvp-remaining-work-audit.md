# MVP Remaining Work Audit / Release Readiness Re-Audit

> Audit-only document. No production code, tests, config, migrations, dependencies,
> or other docs were changed in the PR that introduces this file. Problems recorded
> here were **not fixed** as part of this audit.
>
> Section 18 (Candidate Next Work Packages) is a **candidate list only**. It is
> deliberately unordered and contains no "recommended", "first", or "best next"
> designation. Final prioritisation is returned to Mother Ship.

---

## 0. Audit Conditions and Evidence Limits

| Condition | State at audit time | Effect on findings |
|---|---|---|
| Branch | `audit/mvp-remaining-work-next-feature` off `develop` HEAD `e5b8a6d0` | — |
| Baseline / G4 Merge Gate | **PASS** — `origin/develop` HEAD = `e5b8a6d0` = "fix: finalize responsive web layout for Premium Meaning UI (PR-G4) (#2668)"; G4 class `grid grid-cols-1 gap-2 sm:grid-cols-2` present in `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx` (fallback-state button grid) | Audit authorised to proceed. #2668 already merged; nothing to merge. |
| Backend runtime (`:8000`) | **DOWN** (`ECONNREFUSED` in all prior sessions) | Concierge Result / full Shrine Detail render, live API contracts, and prod DB counts are `UNVERIFIED_RUNTIME_DATA`. |
| Database | Only `backend/db.sqlite3` — a **local dev snapshot** (~8 MB, last modified 2024‑07‑24). Not production. | All row counts labelled `UNVERIFIED_RUNTIME_DATA`. Not treated as current. |
| Web typecheck | `npx tsc -p tsconfig.json --noEmit` → **exit 0** (run during this audit) | Type layer is coherent at `e5b8a6d0`. |
| Web unit tests | 166 `*.test.ts(x)` files present; **not executed in this audit** (no behaviour change to validate; execution deferred to implementation PRs) | Test *presence* verified by path; test *pass state* is `UNVERIFIED` this run. |
| Backend tests | 380 `test_*.py` / `tests.py` files present; **not executed** (need DB) | `UNVERIFIED` this run. |
| Untracked baseline exception | `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` are `next dev`-generated local untracked files. Left untouched, unstaged, excluded from the PR diff. | Confirmed present and untracked at audit start and end. |

Every material judgment below cites a file path, symbol, route, migration, or command.
Where a chain could only be traced statically (no runtime), it is marked
`STATIC-ONLY`.

---

## 1. Executive Summary

KAMI MUSUBI has a **broad, mature implemented surface**. The dominant risk for a
test release is **not missing features** — it is (a) **operational / environmental
readiness** (deployment automation is a stub; legal surface is absent; production
data volume unverifiable from this environment) and (b) **verification gaps**
(backend/runtime could not be exercised).

Structural findings:

1. **Primary journey is code-complete end-to-end** (Concierge → Recommendation →
   Shrine Detail → Route → Visit → Reflection → History). Every layer has a file.
   `STATIC-ONLY` — runtime never exercised this audit.
2. **Recommendation runs on the heuristic (non-LLM) path by default**
   (`CONCIERGE_USE_LLM` default `False`, `backend/shrine_project/settings.py`). The
   LLM path exists but is off; this is a deliberate configuration, not a gap.
3. **Deployment automation is a stub.** `scripts/deploy.sh` contains only
   `echo` lines and commented examples; `.github/workflows/deploy.yml.disabled`
   is disabled. No `render.yaml` / `Dockerfile` / `vercel.json` in the repo.
4. **No legal/commerce surface.** No 利用規約 / プライバシーポリシー /
   特定商取引法 page or string anywhere under `apps/web/src`. This is a paid
   product (Stripe subscription checkout is implemented).
5. **Billing has a real Stripe implementation** gated behind env
   (`BILLING_PROVIDER`, `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`); default runtime
   is the `stub` provider driven by env vars. Whether prod is configured is
   `UNVERIFIED`.
6. **Confirmed dead/disconnected code** persists: the PR‑A→D "Deep Recommendation
   Reason v1" chain (`buildDeepRecommendationReason.ts` + `premiumMeaningContext.ts`
   + `mapConciergeResponseToPremiumMeaningContext.ts` + `computePremiumMeaningValidity`)
   has **zero production importers**; `GoshuinLimitBadge.tsx` has zero importers;
   `aggregateCardCtr` (`cardCtr.ts`) has no live consumer; a stray
   `apps/web/src/app/web/src/lib/server/favorites.server.ts` sits at a bogus route
   path. Classified below as misleading debt, not release risk.
7. **Knowledge data volume unknown.** Models, Django Admin, and ~15 management
   commands for shrine knowledge exist; the local snapshot has 0 deities / 0
   knowledge rows, which is **not evidence about production**.

**Test Release Readiness verdict (Section 17): `NOT_READY`** — driven by
deployment automation, legal surface, and the inability to verify backend runtime
/ data volume from this environment. Feature completeness is not the blocker.

---

## 2. Feature Status Matrix

Classification legend: `COMPLETE` / `COMPLETE_WITH_QA_BACKLOG` / `PARTIAL` /
`BLOCKED` / `NOT_STARTED` / `POST_MVP` / `DEPRECATED_STALE` / `MOTHER_SHIP_DECISION`.

| # | Domain | Feature | Status | Primary evidence |
|---|---|---|---|---|
| A | Concierge | Chat / consultation intake | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/app/api/concierge/chat/route.ts`, `apps/web/src/features/concierge/hooks.ts`, `apps/web/src/lib/api/conciergeChat.ts`; backend `concierge/chat/` in `backend/temples/api/urls.py` |
| A | Concierge | Recommendation result rendering / reading-flow hierarchy | `COMPLETE` | `ConciergeSectionsRenderer.tsx` (PR‑G1/G2/G4 merged: #2661, #2662, #2668) |
| A | Concierge | LLM recommendation path | `PARTIAL` (off by config) | `CONCIERGE_USE_LLM` default `False`, `LLM_*` settings in `backend/shrine_project/settings.py` |
| A | Concierge | Premium/Free/Guest visibility boundary | `COMPLETE` | `apps/web/src/lib/premium/cardVisibility.ts`, `PremiumSeam` in `ConciergeSectionsRenderer.tsx` |
| A | Concierge | Consultation history (list + detail) | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/components/views/ConsultationHistoryListView.tsx` / `ConsultationHistoryDetailView.tsx`; `concierge-threads/` route |
| B | Shrine Detail | Meaning information hierarchy (Direction C hybrid) | `COMPLETE` | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`, PR‑G3 #2663 |
| B | Shrine Detail | `recommendation_meta` Evidence integration | `COMPLETE` | `RecommendationMetaSection.tsx`, wired via `buildShrineDetailModel.ts:1393,1732` → `{...model}` spread, PR‑N3b #2667 |
| B | Shrine Detail | Semantic teaser / analytics alignment | `COMPLETE` | PR‑N3 #2666; `data-testid="shrine-detail-premium-teaser"` per-semantic lines |
| B | Shrine Detail | Deep Reason (production path) | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/lib/concierge/buildDeepReason.ts` consumed by `apps/web/src/app/shrines/[id]/page.tsx` |
| C | Shrine Data / Knowledge | Models + Admin editing | `COMPLETE` | `ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource` in `backend/temples/models.py`; `ShrineDeityAdmin` / `ShrineHistoryAdmin` / `ShrineKnowledgeSourceAdmin` + inlines in `backend/temples/admin.py` |
| C | Shrine Data / Knowledge | Import / seed / coverage tooling | `COMPLETE` | `import_shrine_knowledge.py`, `import_shrines_seed.py`, `seed_deities.py`, `knowledge_coverage_report.py`, `measure_knowledge_recommendation_quality.py`, `bootstrap_production_data.py` in `backend/temples/management/commands/` |
| C | Shrine Data / Knowledge | Production data **volume / coverage** | `UNVERIFIED_RUNTIME_DATA` | Local snapshot only: 103 shrines, 0 deities, 0 goriyaku links (`backend/db.sqlite3`, stale). Not production. |
| D | Map / Route | Explore list / map | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/app/map/page.tsx`; roadmap: "Web: MapLibre GL JS, Mobile: Native地図" (`docs/core/roadmap.md`) |
| D | Map / Route | Route confirmation (Google Maps handoff) | `COMPLETE` | `googleDirHref` / "Googleマップで経路案内" in `apps/web/src/app/shrines/[id]/page.tsx` |
| D | Map / Route | Map API key provisioning | `UNVERIFIED` | `GOOGLE_MAPS_API_KEY` / `GOOGLE_PLACES_API_KEY` blank in `.env.example`, `.env.render.example`, `backend/.env.example` |
| E | Compass | Direction-based recommendation | `COMPLETE` (`STATIC-ONLY`) | `backend/temples/api_views_compass.py` `CompassRecommendationsView` (POST); `apps/web/src/features/compass/*` (CompassClient, PurposeSelector, DirectionVisual, RecommendationsSection); `/compass/page.tsx`; `apps/web/src/app/api/compass/recommendations/route.ts` |
| E | Compass | Runtime contract doc | `COMPLETE` | `docs/product/compass-mvp-runtime-contract.md` |
| F | My Page / Saved Data | My Page screen + tabs | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/features/mypage/components/MyPageScreen.tsx`, `apps/web/src/app/mypage/{page,tabs,history}` |
| F | My Page / Saved Data | Favorite / Visit / Reflection / Journey Timeline | `COMPLETE` (`STATIC-ONLY`) | models `Favorite` (compat "Like"), `Visit`, `ShrineReflection` in `backend/temples/models.py`; routes `favorites`, `visits/`, `shrines/<pk>/reflection/`, `reflections/`, `journeys/timeline/` in `backend/temples/api/urls.py` |
| G | Goshuin | Capture / list / public feed | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/app/goshuin/new/*`, `/goshuins`, `/goshuins/public`, `/shrines/[id]/goshuins`; API `my/goshuins*`, `public/goshuins*`; `backend/temples/api/views/goshuin.py` |
| G | Goshuin | Free vs Premium count limit | `COMPLETE` | `get_my_goshuin_limit` in `backend/temples/api/views/goshuin.py:88,138`; `temples/services/goshuin_limit.py` |
| H | Shrine Registration / Admin | User submission intake | `COMPLETE` (`STATIC-ONLY`) | `apps/web/src/app/shrines/new/page.tsx`, `/api/shrine-submissions/route.ts`; model `ShrineSubmission`; roadmap "Shrine Submissionの受付・審査基盤" |
| H | Shrine Registration / Admin | Candidate fetch / crawl / import pipeline | `COMPLETE` | `fetch_shrine_candidates.py`, `crawl_tiles.py`, `import_approved_candidates.py`, model `ShrineCandidate` |
| I | Ranking | Popular shrines list | `COMPLETE` (`STATIC-ONLY`) | `PopularShrineListView` (`backend/temples/api/urls.py:135` `populars/`), `/api/populars/route.ts`, `/populars/page.tsx`, `/ranking/page.tsx`, `recalc_popular_shrines.py`, model `RankingLog` |
| I | Ranking | `/ranking` vs `/populars` route overlap | `MOTHER_SHIP_DECISION` | Two pages consume popular-shrine data (`apps/web/src/app/ranking/page.tsx` uses `fetchRanking` + `usePopularShrines`; `apps/web/src/app/populars/page.tsx` separate). Which is canonical for MVP is a product call. |
| J | Auth | JWT login / refresh / logout / me | `COMPLETE` (`STATIC-ONLY`) | `api/token/`, `api/token/refresh/`, `api/token/verify/` in `backend/config/urls.py`; `backend/users/urls.py` (`users/me/`, `users/current/`, `users/me/icon/`); BFF `apps/web/src/app/api/auth/{login,logout}/route.ts`; `apps/web/src/lib/auth/AuthProvider.tsx` (cookie access/refresh) |
| J | Auth | Guest mode | `COMPLETE` (`STATIC-ONLY`) | `guestMode` prop threaded in `apps/web/src/app/shrines/[id]/page.tsx`; anonymous column in `cardVisibility.ts` |
| K | Premium / Billing | Billing status window | `COMPLETE` | `backend/temples/services/billing_state.py` `get_billing_status()` / `provider()` |
| K | Premium / Billing | Stripe checkout | `COMPLETE` (`STATIC-ONLY`, env-gated) | `backend/temples/services/billing_checkout.py` `create_checkout_session` (real `stripe.checkout.Session.create`), `backend/temples/api/views/billing.py` `BillingCheckoutView`; route `billings/checkout/` |
| K | Premium / Billing | Stripe webhook + entitlement apply | `COMPLETE` (`STATIC-ONLY`) | `BillingStripeWebhookView` in `billing.py`; `users/services/stripe_webhook.py` (`construct_stripe_event`, `apply_stripe_event`); route `billings/webhook/` |
| K | Premium / Billing | Production billing configuration | `UNVERIFIED` | `BILLING_PROVIDER` defaults to `stub`; `STRIPE_*` blank in every `.env.example`. Whether prod sets `stripe` + keys is unknowable here. |
| L | Analytics | Card event tracking | `COMPLETE` | `apps/web/src/lib/analytics/cardEvents.ts` `trackCardEvent`; `ShrineDetailArticle.tsx` analytics `useEffect` |
| L | Analytics | Cross-surface teaser event naming | `COMPLETE_WITH_QA_BACKLOG` | Shrine Detail uses `card_partial_view` for teaser; Concierge uses `card_teaser_view` — known inconsistency documented in `docs/audit/meaning-analytics-n2-n3-resolution.md` |
| L | Analytics | CTR aggregation consumer | `DEPRECATED_STALE` | `aggregateCardCtr` in `apps/web/src/lib/analytics/cardCtr.ts` has no importer outside its own test |
| M | Responsive Web | 375/390/430 px Premium Meaning polish | `COMPLETE` | PR‑G4 #2668 merged; typecheck clean at `e5b8a6d0` |
| N | Native Mobile | Expo app | `PARTIAL` / separate track | `apps/mobile/` (Expo: `app.config.ts`, `eas.json`, `dist/`); dedicated `docs/audit/mobile-release-readiness-audit.md` |
| O | Deployment / Infra | Deploy automation | `PARTIAL` (stub) | `scripts/deploy.sh` is `echo`-only; `.github/workflows/deploy.yml.disabled` |
| O | Deployment / Infra | Infra-as-code | `NOT_STARTED` in-repo | No `render.yaml` / `Dockerfile` / `vercel.json` / `fly.toml` found |
| O | Deployment / Infra | DB engine / migrations | `COMPLETE` | `dj_database_url` + PostGIS prod / spatialite dev in `backend/shrine_project/settings.py`; 101 migrations, latest `0101_p8b_remove_non_shrine_artifact_id105.py` |
| P | Test Release Readiness | Automated test presence | `COMPLETE` | 166 web + 380 backend test files |
| P | Test Release Readiness | Test execution / green state this audit | `UNVERIFIED` | Only web typecheck run (pass); suites not executed |
| Q | Legal / Operational | Terms / Privacy / 特商法 | `NOT_STARTED` | No matching page or string under `apps/web/src` |
| Q | Documentation | Roadmap + audit corpus | `COMPLETE` | `docs/core/roadmap.md` (Status: Active) + ~40 `docs/audit/*` |

---

## 3. Confirmed Complete (evidence-backed, static)

The following are code-complete and wired across all reachable layers. "Complete"
here means **the code chain is continuous**; runtime behaviour was not exercised
(backend down).

- **Concierge reading-flow result UI** — G1/G2/G4 chain merged; `PremiumSeam`
  single-seam architecture; borderless narrative for meaning layers.
- **Shrine Detail meaning hierarchy** — Direction C hybrid; `DetailSection`
  `primary/secondary/tertiary/plain`; `sectionVariant.ts` card/plain.
- **`recommendation_meta` in Evidence layer** — render-gated identically to its
  already-firing analytics event (`rankTitle && rankBody`), borderless weak
  hierarchy, dark-safe tokens, no premium accent. `RecommendationMetaSection.tsx`.
- **Premium/Free/Guest visibility matrix** — `cardVisibility.ts`
  `getVisibilityForCard(cardId, accessLevel)` with per-CardId
  anonymous/free/premium states.
- **Auth** — SimpleJWT triple (`token` / `token/refresh` / `token/verify`),
  BFF cookie bridge, `AuthProvider`, guest mode.
- **Billing window** — single `get_billing_status()` entry; provider abstraction
  (`stub` / `stripe` / `revenuecat` / `unknown`); real Stripe checkout + webhook
  + entitlement application code present.
- **Goshuin** — capture, list, per-user public page, feed, free/premium count
  limit service.
- **Shrine submission + candidate pipeline** — intake form, BFF, `ShrineSubmission`
  / `ShrineCandidate` models, crawl/fetch/import commands.
- **Ranking** — `PopularShrineListView`, `recalc_popular_shrines`, `RankingLog`.
- **Knowledge model + admin + tooling** — editable via Django Admin; import,
  coverage, and quality-measurement commands exist.
- **DB / migration layer** — 101 migrations; PostGIS prod config via
  `dj_database_url`.

---

## 4. Complete With QA Backlog

| Item | What works | Backlog item | Evidence |
|---|---|---|---|
| Cross-surface teaser analytics | Both surfaces fire an exposure event | Shrine Detail `card_partial_view` vs Concierge `card_teaser_view` naming divergence — analytics consumer must special-case | `docs/audit/meaning-analytics-n2-n3-resolution.md`; `apps/web/src/lib/analytics/cardEvents.ts` |
| Result ↔ Detail join instrumentation | Semantic CardId events emitted per type | Join key `(recommendationInstanceId, shrineId)` with `cardId` as compared dimension needs a live consumer / dashboard to be useful | `docs/audit/recommendation-result-detail-instrumentation-contract.md` §7 |
| Web unit tests | 166 files present; typecheck clean | Full `vitest run` + backend `pytest` green-state not verified this audit (backend needs DB) | test file counts; `apps/web/package.json` `"test": "vitest run"` |
| Responsive polish (G4) | Reading-flow components responsive-safe; fallback-state button grid fixed | Real-device pass at 375/390/430 px was not runnable (backend down → Result/Detail never fully rendered in prior sessions) | prior session notes; PR‑G4 #2668 |

---

## 5. Partial Implementations

| Item | Implemented | Missing / gated | Evidence |
|---|---|---|---|
| LLM recommendation path | `LLM_PROVIDER` / `LLM_MODEL` (openai/gpt-4o-mini) / timeout / retries wiring; `CONCIERGE_USE_LLM` switch | Disabled by default (`default=False`); `OPENAI_API_KEY` blank in all `.env.example`. Whether MVP wants LLM on is a product decision. | `backend/shrine_project/settings.py` |
| Deployment automation | Env-decision + concurrency + environment-name logic in `deploy.yml.disabled`; `.env.render.example` | Workflow **disabled**; `scripts/deploy.sh` has no real steps (only commented `build.sh` / `migrate.sh` / `rsync_or_ssh.sh`); no IaC file in repo | `.github/workflows/deploy.yml.disabled`, `scripts/deploy.sh` |
| Native mobile | Expo project scaffold, `eas.json`, prior `dist/` build, shared design dir | Release-readiness tracked separately; not verified in this audit | `apps/mobile/`, `docs/audit/mobile-release-readiness-audit.md` |
| Map API provisioning | Code paths + env var names | Keys blank in all example envs; MapLibre style/source config not confirmed present in repo (roadmap asserts MapLibre GL JS) | `.env*.example`; `docs/core/roadmap.md` |
| Production billing | Full Stripe code path | `BILLING_PROVIDER` default `stub`; `STRIPE_SECRET_KEY` / `STRIPE_PRICE_ID` / `STRIPE_WEBHOOK_SECRET` blank in examples; prod config unverifiable here | `billing_state.py`, `billing_checkout.py`, `backend/.env.example` |

---

## 6. Confirmed Release Blocker Candidates

> "Blocker candidate" = would plausibly prevent a *paid, publicly reachable* test
> release. Not ranked. Mother Ship confirms which are true blockers for the chosen
> release shape.

| ID | Candidate | Why it may block | Evidence | Confidence |
|---|---|---|---|---|
| RB‑1 | **No legal / commerce surface** | Paid subscription (Stripe checkout) with no 利用規約 / プライバシーポリシー / 特定商取引法に基づく表記 page. Japanese paid-service requirement; app-store / payment-processor requirement. | No page under `apps/web/src/app` (route groups: `auth billing compass concierge consultation goshuin goshuins map mypage navi plan populars ranking routes shrines signup` — none legal); zero matches for legal strings in `*.tsx` | High (absence verified) |
| RB‑2 | **Deployment automation is a stub** | `scripts/deploy.sh` performs no deploy; deploy workflow disabled; no IaC in repo. A repeatable path from `develop` to a running environment is not demonstrable from the repo. | `scripts/deploy.sh` body; `.github/workflows/deploy.yml.disabled` | High (content verified) |
| RB‑3 | **Backend runtime unverifiable** | Could not start `:8000` in any recent session → Concierge Result, full Shrine Detail, Compass, ranking, billing endpoints never exercised. Primary journey is `STATIC-ONLY`. | Prior-session `ECONNREFUSED`; this audit did not attempt a boot (docs-only rule) | High (repeated) |
| RB‑4 | **Production shrine/knowledge data volume unknown** | Recommendation quality and Evidence-gated meaning depend on populated `ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource` / goriyaku links. Local snapshot has 0 of these. | `backend/db.sqlite3` counts (stale, local); `knowledge_coverage_report.py` exists but not run here | Medium (local data is not proof about prod) |
| RB‑5 | **Production billing configuration unverified** | If prod does not set `BILLING_PROVIDER=stripe` + keys, "premium" is env-toggled only and real payment cannot occur; if partially set, `create_checkout_session` raises `RuntimeError("stripe checkout is not configured")`. | `billing_state.provider()` default `stub`; `_stripe_price_id()` / secret-key guard in `billing_checkout.py` | Medium |

---

## 7. Environment / External Blockers

Items outside the codebase that gate release; none are code defects.

- **Stripe account + product/price + webhook endpoint** — `STRIPE_SECRET_KEY`,
  `STRIPE_PREMIUM_PRICE_ID` / `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`.
- **Google Maps / Places API keys** — `GOOGLE_MAPS_API_KEY`,
  `GOOGLE_PLACES_API_KEY` (blank in all examples).
- **OpenAI API key** — only if LLM recommendation is turned on for MVP.
- **Production Postgres + PostGIS** — `DATABASE_URL` (`postgis://…`); prod uses
  PostGIS (`backend/shrine_project/settings.py`).
- **Hosting** — frontend (Vercel implied by `.env.render.example`
  `your-frontend.vercel.app`), backend (`.onrender.com` implied). No provider
  config committed.
- **`ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS`** — must be
  set to real prod domains (examples use placeholders).
- **Object storage** — `STORAGE_BACKEND=local` in examples; goshuin images need
  durable storage in prod.

---

## 8. Mother Ship Decisions Required

| ID | Decision | Context | Not decided here because |
|---|---|---|---|
| MS‑1 | Is **LLM recommendation** in or out for MVP? | Path exists, disabled by default. | Product scope call. |
| MS‑2 | `/ranking` vs `/populars` — **which is canonical**, and is the other removed or kept? | Both pages render popular-shrine data from the same backend. | Product IA call; removal would violate the No-Implementation rule for this audit anyway. |
| MS‑3 | Legal surface: **build in-app pages vs external links vs defer** (and defer implies no public paid release). | RB‑1. | Legal / business call. |
| MS‑4 | Deployment target: **confirm Render + Vercel** (or other) and whether IaC is committed to the repo. | RB‑2. | Infra ownership call. |
| MS‑5 | Dead PR‑A→D chain (N1): **delete / keep-as-scaffold / revive**. | Section 11. | Not touched under No-Implementation rule; needs an explicit disposition task. |
| MS‑6 | Cross-surface teaser analytics naming: **unify names vs document-and-keep**. | Section 4. | Analytics-contract change; gated. |
| MS‑7 | Route sprawl (`/login` vs `/auth/login`, `/signup`, `/g`, `/navi`, `/plan`, `/routes`, `/consultation`, `/web`): **which are MVP-supported, which are compat shims, which are dead**. | Section 11. | Product IA call. |

---

## 9. Post-MVP / Backlog (explicitly deferred, not gaps)

- **Motion / animation** for Premium Meaning UI — deferred by Mother Ship
  decision D‑7 (`docs/design/premium-meaning-ui-direction.md`).
- **Deep Dive expansion PRs** — memory `deep_dive_observation_phase`: no new Deep
  Dive implementation except Critical Bugs until data justifies.
- **Score v3** — shadow observation only (`concierge/score-v3/dashboard/` route;
  `docs/audit/score-v3-shadow-mode-readiness.md`); not the live ranking input.
- **RevenueCat / mobile billing** — provider enum slot exists
  (`billing_state.py` `PROVIDER_CHOICES`), treated as `UserProfile` for now.
- **CTR aggregation dashboards** — `aggregateCardCtr` written, no consumer.
- **Native mobile release** — separate track (`docs/audit/mobile-release-readiness-audit.md`).

---

## 10. Stale TODO / Documentation Notes

- `scripts/deploy.sh` — comment block `# ここに実デプロイ手順を書く（例）` with
  three commented-out script calls; the script is effectively a placeholder.
- `deploy.yml.disabled` — trailing comment discussing an unresolved GitHub
  Actions dynamic-`environment` limitation; workflow parked.
- `backend/users/urls.py` — inline comments `★ ここに MeIconUploadView を入れる`
  / `たぶん既存` indicate uncertainty that was never cleaned up (cosmetic).
- `docs/core/roadmap.md` "基盤実装済み" list asserts MapLibre GL JS for web; the
  repo was not confirmed to contain the MapLibre style/source wiring in this
  audit (grep for `maplibre`/`maptiler` in `apps/web/src` returned no hits) —
  **doc vs code consistency `UNVERIFIED`**, flag for follow-up.
- Large `docs/audit/*readiness*` corpus (~40 files) overlaps in scope; no single
  index ties them to current status. Not a defect; navigability cost.

---

## 11. Dead / Disconnected Architecture

> Classification: **harmless** (inert, no reader confusion) / **misleading debt**
> (looks live, isn't) / **release risk** (could execute wrongly). Nothing deleted.

| Item | Finding | Classification | Evidence |
|---|---|---|---|
| **PR‑A→D "Deep Recommendation Reason v1" chain** | `buildDeepRecommendationReason.ts` imported only by its own test. `premiumMeaningContext.ts` ↔ `mapConciergeResponseToPremiumMeaningContext.ts` ↔ `computePremiumMeaningValidity` import each other only. No production entry point. The **live** deep-reason path is the separate `buildDeepReason.ts` (consumed by `apps/web/src/app/shrines/[id]/page.tsx`). | **Misleading debt** — two similarly-named modules, only one live | `grep` importers: `buildDeepRecommendationReason` → tests only; `buildDeepReason` → `shrines/[id]/page.tsx` |
| Backend `consultation_meaning` API field | Declared in `apps/web/src/lib/api/concierge/types.ts`; consumed only by the three dead files above. API emits it; nothing live reads it. | **Misleading debt** | grep `consultation_meaning` in `apps/web/src` (non-test) → only the dead chain + the type decl |
| `GoshuinLimitBadge.tsx` | `apps/web/src/components/shrine/detail/GoshuinLimitBadge.tsx` has zero importers. | **Misleading debt** (component looks part of Detail; isn't mounted) | grep `GoshuinLimitBadge` → only self |
| `aggregateCardCtr` / `cardCtr.ts` | No importer outside `apps/web/src/lib/analytics/__tests__/cardCtr.test.ts`. | **Harmless** (pure function, no side effects, no exposure) | grep `aggregateCardCtr` → self + own test |
| `apps/web/src/app/web/src/lib/server/favorites.server.ts` | Stray file nested under a bogus `app/web/src/...` path — an accidental copy of `lib/server/favorites.server.ts` sitting inside the App Router tree. Not a valid route segment layout; not imported via `@/`. | **Misleading debt** (pollutes route tree, confuses grep) | `find apps/web/src/app/web -type f` → single file |
| `/ranking` + `/populars` | Two App Router pages for popular-shrine data. | **Misleading debt** → **MS‑2** | `apps/web/src/app/ranking/page.tsx`, `apps/web/src/app/populars/page.tsx` |
| `/login`, `/signup` | Server components that `redirect(...)` (sanitise `next`, strip `_rsc`) — compat shims toward `/auth/*`. | **Harmless** (intentional redirects) | `apps/web/src/app/login/page.tsx`, `apps/web/src/app/signup/page.tsx` |
| `temples/api_urls.py` | Pure compat alias (`from temples.api.urls import urlpatterns`). | **Harmless** (documented alias) | file content |
| Route segments `/g`, `/navi`, `/plan`, `/routes`, `/consultation`, `/media`, `/debug` | Present in App Router; MVP-support status not individually confirmed. | **Unclassified** → **MS‑7** | `ls apps/web/src/app` |

No stale **feature flags** with divergent behaviour were found beyond
`CONCIERGE_USE_LLM` (deliberate) and `BILLING_STUB_*` (test infra).

---

## 12. Critical User Journey (Concierge → Reflection)

Cross-layer trace. `STATIC-ONLY` — no runtime confirmation (backend down).

| Step | Layer chain | State | Evidence |
|---|---|---|---|
| Consult | `ConciergeSectionsRenderer` intake → BFF `api/concierge/chat/route.ts` (JWT cookie bridge, 401→refresh retry) → backend `concierge/chat/` → `ConciergeThread` / `ConciergeMessage` | chain continuous | route files + `backend/temples/api/urls.py` |
| Recommend | heuristic path (`CONCIERGE_USE_LLM=False`) → `recommendation_reason_v4_detail` (backend) → `buildRecommendationReasonViewModel.ts` / `buildMeaningNarrative.ts` / `buildStateNarrative.ts` / `buildReasonNarrative.ts` / `buildDeepReason.ts` → `ConciergeSectionsRenderer` reading-flow sections | chain continuous | `apps/web/src/lib/concierge/*`, `settings.py` |
| Visibility gate | `cardVisibility.ts` `getVisibilityForCard` → `PremiumSeam` | chain continuous | `cardVisibility.ts`, `ConciergeSectionsRenderer.tsx` |
| Shrine Detail | `shrines/[id]/page.tsx` → `buildShrineDetailModel.ts` (1732 LOC: sections, `recommendationMeta` at `:1393`) → `ShrineDetailArticle.tsx` (`{...model}` spread) → `DetailSection` / `RecommendationMetaSection` / `ShrineFactSection` | chain continuous | files cited |
| Analytics | `ShrineDetailArticle` `useEffect` → `trackCardEvent` (`cardEvents.ts`): `context_reason`, `personal_meaning`, `recommendation_meta`, `saved_record`, … | chain continuous | `ShrineDetailArticle.tsx`, `cardEvents.ts` |
| Route | `googleDirHref` → Google Maps handoff | chain continuous | `shrines/[id]/page.tsx` |
| Visit | `shrines/<id>/visit/` route → `Visit` model (linked to recommendation thread) | chain continuous | `backend/temples/api/urls.py`, `models.py` |
| Reflect | `ShrineReflectionPrompt.tsx` → `shrines/<pk>/reflection/` / `reflections/` → `ShrineReflection` model | chain continuous | files cited |
| History | `concierge-threads/` → `ConsultationHistoryListView` / `DetailView` | chain continuous | files cited |

**Break points:** none *statically*. **Unverified:** every runtime hop (API
response shape, DB writes, auth refresh, analytics delivery).

---

## 13. Secondary Journey (Compass, Goshuin, Ranking, Submission)

| Journey | Chain | State | Evidence |
|---|---|---|---|
| Compass | `/compass/page.tsx` → `CompassClient.tsx` (+ PurposeSelector / DirectionVisual / OriginSummary / RecommendationsSection) → `api/compass/recommendations/route.ts` → `CompassRecommendationsView.post` → shrine scoring by element/kyusei | continuous (`STATIC-ONLY`) | `apps/web/src/features/compass/*`, `backend/temples/api_views_compass.py` |
| Goshuin | `goshuin/new/GoshuinNewClient.tsx` → `api/my/goshuins/route.ts` → `backend/temples/api/views/goshuin.py` (limit check `get_my_goshuin_limit`) → `Goshuin` + `GoshuinImage`; public: `goshuins/public` → `public/goshuins/feed` / `[username]` | continuous (`STATIC-ONLY`) | files cited |
| Ranking | `/populars` or `/ranking` → `/api/populars/route.ts` → `PopularShrineListView` → `popular_score` / `recalc_popular_shrines.py` / `RankingLog` | continuous (`STATIC-ONLY`); **route duplication** MS‑2 | files cited |
| Submission | `/shrines/new/page.tsx` → `/api/shrine-submissions/route.ts` → `ShrineSubmission`; admin review → `import_approved_candidates.py` → `Shrine` | continuous (`STATIC-ONLY`) | files cited |
| Ingest variants | `/api/my/shrines/ingest`, `/api/shrines/ingest`, `/api/shrines/suggest` — multiple ingest BFF routes; canonical one for MVP not confirmed | `MOTHER_SHIP_DECISION`-adjacent | `apps/web/src/app/api/**` |

---

## 14. Premium Journey (Free → Upgrade → Premium)

| Step | Chain | State | Evidence |
|---|---|---|---|
| Free sees seam | `cardVisibility.ts` (`shrine_meaning`/`action_meaning`/`personal_meaning` = `teaser` for anonymous/free) → `PremiumSeam` in `ConciergeSectionsRenderer.tsx`; Shrine Detail per-semantic teaser lines (`data-testid="shrine-detail-premium-teaser"`) | continuous | PR‑N3 #2666, PR‑G2 #2662 |
| CTA → upgrade | `buildLoginHref("/billing/upgrade")` → `/auth/login?returnTo=%2Fbilling%2Fupgrade` → `/billing/upgrade/page.tsx` | continuous (`STATIC-ONLY`) | `apps/web/src/app/billing/upgrade/*` |
| Checkout | `billings/checkout/` → `BillingCheckoutView` → `create_checkout_session` → (provider `stripe`) `stripe.checkout.Session.create` → redirect to Stripe | continuous **iff** `BILLING_PROVIDER=stripe` + keys; else `stub_checkout_*` returns success URL directly | `billing_checkout.py` |
| Webhook | Stripe → `billings/webhook/` → `BillingStripeWebhookView` → `construct_stripe_event` → `apply_stripe_event` → `UserProfile` entitlement | continuous (`STATIC-ONLY`) | `billing.py`, `users/services/stripe_webhook.py` |
| Premium unlock | `get_billing_status()` → `plan="premium"` → `cardVisibility` premium column (`visible`) | continuous | `billing_state.py`, `cardVisibility.ts` |

**Risk:** the entire monetisation chain is `STATIC-ONLY` and additionally gated on
env config that this environment cannot inspect (RB‑5). In `stub` mode the
"upgrade" completes with no payment — correct for dev, a release hazard if shipped.

---

## 15. Data Readiness

| Dataset | Local snapshot (`backend/db.sqlite3`, **stale 2024‑07, NOT prod**) | Production | Tooling to populate |
|---|---|---|---|
| Shrines | 103 | `UNVERIFIED_RUNTIME_DATA` | `import_shrines_seed.py`, `bootstrap_production_data.py`, `import_approved_candidates.py` |
| Deities | 0 | `UNVERIFIED_RUNTIME_DATA` | `seed_deities.py` |
| Goriyaku tags / links | 0 / 0 | `UNVERIFIED_RUNTIME_DATA` | `backfill_goriyaku_tags.py` |
| Shrine knowledge (deity/history/source) | 0 | `UNVERIFIED_RUNTIME_DATA` | `import_shrine_knowledge.py`, `export_shrine_knowledge.py`, `knowledge_coverage_report.py` |
| `history_theme` | partial | `UNVERIFIED` | `seed_history_theme.py` |
| `astro_elements` / `location` | partial | `UNVERIFIED` | `backfill_astro_elements.py`, `backfill_location.py` |
| Goshuin | 4 | `UNVERIFIED` (user data) | n/a |
| Visits / Favorites / RankingLog | 0 / 0 / 0 | `UNVERIFIED` (user/behaviour data) | `recalc_popular_shrines.py` |
| PlaceCache / PlaceRef | present | `UNVERIFIED` | `sync_places_nearby.py`, `sync_places_seeds.py` |

**Conclusion:** data-population *tooling* is `COMPLETE`; data-population *state*
for production is entirely `UNVERIFIED_RUNTIME_DATA` from this environment. A
production `knowledge_coverage_report.py` run is the missing evidence.

---

## 16. Deployment Readiness

| Aspect | State | Evidence |
|---|---|---|
| DB engine / migrations | `READY` — PostGIS prod via `dj_database_url`, 101 migrations, spatialite dev fallback | `backend/shrine_project/settings.py`, `backend/temples/migrations/0101_*` |
| Deploy automation | `NOT_READY` — `scripts/deploy.sh` is a stub; `deploy.yml.disabled` disabled | files cited |
| IaC in repo | `NOT_PRESENT` — no `render.yaml` / `Dockerfile` / `vercel.json` / `fly.toml` | `find` |
| Env templates | `PARTIAL` — `.env.example`, `.env.render.example`, `backend/.env.example`, `.env.pytest.local.example` exist; all secrets blank/placeholder | files cited |
| CORS / ALLOWED_HOSTS / CSRF | `NEEDS_PROD_VALUES` — examples use `.onrender.com` / `your-frontend.vercel.app` placeholders | `.env.render.example` |
| Storage | `NEEDS_PROD_VALUES` — `STORAGE_BACKEND=local` in examples; goshuin/user images need durable storage | `.env*.example` |
| CI (non-deploy) | `PRESENT` — `web-tests.yml`, `backend-tests.yml`, `backend-integration.yml`, `backend-pr.yml`, `mobile-ci.yml`, `codeql.yml`, `dependency-review.yml`, `readme-guard.yml` | `.github/workflows/` |
| Health check / smoke | `PARTIAL` — `runner-smoke.yml` present; app-level health endpoint not confirmed | `.github/workflows/` |
| Scheduled jobs | `PRESENT` — `run_scheduled_jobs.py` command | `backend/temples/management/commands/` |

**Overall: `NOT_READY`** — no demonstrable repeatable path from `develop` to a
running production environment; secrets/infra external and unconfigured here.

---

## 17. Test Release Readiness

**Verdict: `NOT_READY`.**

Rationale (each an independent cause):

1. **`NOT_READY` — operational.** Deployment automation is a stub (RB‑2);
   no committed infra config (Section 16).
2. **`NOT_READY` — legal.** No Terms / Privacy / 特商法 surface for a paid
   product (RB‑1).
3. **`NOT_READY_WITHIN_THIS_ENVIRONMENT` — verification.** Backend runtime could
   not be exercised (RB‑3); backend test suite and full web suite not run;
   production data volume unverifiable (RB‑4). Only web `tsc --noEmit` passed.
4. **`READY_WITH_KNOWN_LIMITATIONS` — feature completeness.** The implemented
   surface (Sections 3, 12–14) is code-complete and type-clean; if the above are
   resolved, the feature set itself does not block a test release. Known
   limitations to disclose: heuristic-only recommendation (MS‑1), `stub` billing
   unless prod-configured (RB‑5), analytics naming divergence (Section 4),
   `/ranking`–`/populars` duplication (MS‑2).

To move toward `READY_WITH_KNOWN_LIMITATIONS` overall, the minimum is: a real
deploy path, a legal surface (or a decision that the test release is
closed/non-paid), a green backend suite against a real DB, and a production
`knowledge_coverage_report` snapshot.

---

## 18. Candidate Next Work Packages

> **Unordered. No priority, no "recommended", no "next".** Each is a
> self-contained candidate returned to Mother Ship for selection. Max 5.

### Candidate WP‑A — Legal / Commerce surface for paid release

- **Why:** Stripe subscription checkout is implemented; there is no 利用規約 /
  プライバシーポリシー / 特定商取引法に基づく表記 anywhere. Blocks a public paid
  test release (RB‑1).
- **Evidence:** zero legal route/string under `apps/web/src`; `create_checkout_session`
  (real Stripe) in `backend/temples/services/billing_checkout.py`.
- **Expected files:** new `apps/web/src/app/(legal)/terms/page.tsx`,
  `.../privacy/page.tsx`, `.../commerce-disclosure/page.tsx`; footer/nav link
  component; possibly a `docs/legal/` source-of-truth.
- **Scope:** M (content authoring dominates; wiring is S).
- **Risk:** Low technically; content is a legal/business dependency, not
  engineering.
- **Dependencies:** legal copy provided by Mother Ship / business.
- **Why it might block MVP:** a paid public release without these is
  non-compliant and app-store/processor-rejectable.
- **Suggested AI owner:** web-frontend agent (wiring) + human/business (copy).

### Candidate WP‑B — Deployment path from `develop` to a running environment

- **Why:** `scripts/deploy.sh` does nothing; deploy workflow disabled; no IaC.
  No repeatable release mechanism (RB‑2).
- **Evidence:** `scripts/deploy.sh` body; `.github/workflows/deploy.yml.disabled`;
  absence of `render.yaml` / `Dockerfile` / `vercel.json`.
- **Expected files:** `render.yaml` or `Dockerfile` + host config; real
  `scripts/deploy.sh` (build → migrate → release); re-enabled
  `.github/workflows/deploy.yml`; `docs/infra/` runbook.
- **Scope:** L.
- **Risk:** Medium — touches secrets, migrations-on-deploy, first prod cutover.
- **Dependencies:** MS‑4 (confirm hosting providers); env secrets provisioned.
- **Why it might block MVP:** without it there is no test release to hand testers.
- **Suggested AI owner:** infra/backend agent.

### Candidate WP‑C — Backend runtime + data-readiness verification pass

- **Why:** Primary and monetisation journeys are `STATIC-ONLY`; production
  shrine/knowledge volume is `UNVERIFIED_RUNTIME_DATA` (RB‑3, RB‑4).
- **Evidence:** repeated `ECONNREFUSED` on `:8000`; local `db.sqlite3` has 0
  deities / 0 knowledge rows; `knowledge_coverage_report.py` exists, unrun.
- **Expected files:** likely **none** production — a verification report
  (`docs/audit/…`), plus any *test-only* fixtures if gaps are found. If code
  defects surface, they spawn their own packages.
- **Scope:** M.
- **Risk:** Low (read/verify); may expand if the runtime reveals broken contracts.
- **Dependencies:** a bootable backend + a representative DB (staging or seeded).
- **Why it might block MVP:** ships an unproven primary journey and possibly an
  empty-knowledge recommendation experience.
- **Suggested AI owner:** backend agent with runtime access.

### Candidate WP‑D — Production billing configuration + stub-mode guard

- **Why:** monetisation is env-gated; `stub` mode "completes" upgrade with no
  payment; misconfiguration raises `RuntimeError` at checkout (RB‑5).
- **Evidence:** `billing_state.provider()` default `stub`; `_stripe_price_id()` /
  secret-key guard in `billing_checkout.py`; `BillingStripeWebhookView`.
- **Expected files:** prod env config (external); possibly a guard/log in
  `billing_checkout.py` or `billing.py` so a non-`stripe` provider in a
  production build is loudly surfaced rather than silently stubbed; a billing
  smoke test.
- **Scope:** S–M.
- **Risk:** Medium — payment path; needs Stripe test-mode E2E.
- **Dependencies:** Stripe account, price, webhook endpoint; WP‑B for the webhook
  URL to exist.
- **Why it might block MVP:** if premium is a test-release goal, an unpaid or
  broken checkout defeats it.
- **Suggested AI owner:** backend agent + human (Stripe dashboard).

### Candidate WP‑E — Dead / disconnected code disposition (N1 chain + strays)

- **Why:** `buildDeepRecommendationReason.ts` + `premiumMeaningContext.ts` +
  `mapConciergeResponseToPremiumMeaningContext.ts` + `computePremiumMeaningValidity`
  have zero production consumers but shadow the live `buildDeepReason.ts`;
  `GoshuinLimitBadge.tsx` unmounted; stray
  `apps/web/src/app/web/src/lib/server/favorites.server.ts` pollutes the route
  tree; `/ranking`↔`/populars` duplication. Misleading debt raises the cost of
  every future change in these areas.
- **Evidence:** Section 11 grep results.
- **Expected files:** deletions under `apps/web/src/lib/concierge/`,
  `apps/web/src/components/shrine/detail/GoshuinLimitBadge.tsx`,
  `apps/web/src/app/web/`; possibly `apps/web/src/lib/api/concierge/types.ts`
  (drop unused `consultation_meaning` type) — pending MS‑5 / MS‑2 / MS‑7.
- **Scope:** S (mechanical) once decisions land.
- **Risk:** Low — removal of provably-unimported code; guarded by typecheck + tests.
- **Dependencies:** MS‑5 (revive vs delete the N1 chain), MS‑2, MS‑7.
- **Why it might block MVP:** it does not block function; it is a
  correctness-of-understanding risk during release hardening.
- **Suggested AI owner:** web-frontend agent.

---

## Appendix — Evidence Index (selected)

| Claim | Anchor |
|---|---|
| G4 gate | `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx` (`grid grid-cols-1 gap-2 sm:grid-cols-2`); `develop` HEAD `e5b8a6d0` |
| Heuristic default | `backend/shrine_project/settings.py` `CONCIERGE_USE_LLM = env.bool("CONCIERGE_USE_LLM", default=False)` |
| Deploy stub | `scripts/deploy.sh`; `.github/workflows/deploy.yml.disabled` |
| No legal surface | `ls apps/web/src/app`; `grep -rn "利用規約\|プライバシー\|特定商取引" apps/web/src` → none |
| Stripe real path | `backend/temples/services/billing_checkout.py` `stripe.checkout.Session.create`; `backend/temples/api/views/billing.py` `BillingStripeWebhookView` |
| Billing provider default | `backend/temples/services/billing_state.py` `provider()` → `os.getenv("BILLING_PROVIDER", "stub")` |
| N1 dead chain | `grep -rn buildDeepRecommendationReason apps/web/src` → tests only; live path `buildDeepReason.ts` ← `apps/web/src/app/shrines/[id]/page.tsx` |
| `recommendation_meta` wired | `apps/web/src/lib/shrine/buildShrineDetailModel.ts:1393,1732`; `apps/web/src/components/shrine/detail/RecommendationMetaSection.tsx` |
| Migrations | `backend/temples/migrations/0101_p8b_remove_non_shrine_artifact_id105.py` (101 total) |
| Local DB is stale/non-prod | `backend/db.sqlite3` mtime 2024‑07‑24; 103 shrines / 0 deities / 0 knowledge |
| Web typecheck pass | `cd apps/web && npx tsc -p tsconfig.json --noEmit` → exit 0 (this audit) |
