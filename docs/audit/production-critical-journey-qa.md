# Production Critical Journey QA

> **QA only. No production code was changed.** Defects (if any) become independent
> PRs. No credential, token, cookie, personal data, or precise user location is
> recorded in this document.
>
> The Anonymous end-to-end journey and the 375px responsive checks were executed
> on production and **passed**. Two journey segments could **not** be executed by
> the QA agent — the Authenticated Free flow (requires a production login /
> account, which the agent may not create or authenticate) and the Mobile Web
> device Geolocation check (requires a real smartphone). No release-blocking
> defect was found in any executable segment.

---

## 1. Scope

Production URL: **`https://jinja-app-web.vercel.app`** (frontend) → Vercel BFF →
**`https://jinja-backend.onrender.com`** (backend).

Journeys per the QA directive:

- **A — Anonymous:** Landing → Concierge → Recommendation Result → Shrine Detail → Google Maps Directions
- **B — Authenticated Free:** Login → Concierge → Result → Detail → Save → Visit → Reflection → Timeline → Premium CTA
- **C — Responsive Web (375px):** Concierge Result, Shrine Detail, Premium CTA
- **D — Mobile Web (real device):** Production URL → current-location action → permission → geolocation → location-dependent UI
- Cross-cutting: Analytics `card_view` dedupe (RH3-1), Browser Console / Network.

---

## 2. Base SHA

| Item | Value |
|---|---|
| Branch | `qa/production-critical-journey` (from `develop`) |
| Base SHA / HEAD | `65575715c928215f38c4af90da1144b1156ebf89` |
| `origin/develop` | `65575715 audit: Goriyaku Evidence Foundation差分監査 (#2678)` |
| HEAD == origin/develop | yes |
| Working tree | clean except known untracked `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` (untouched) |
| Note | PR #2679 (Production Environment Configuration Verification) is not yet merged; it is docs-only and does not affect the deployed production runtime under test. |

---

## 3. Production URLs

| Surface | URL | Reachable |
|---|---|---|
| Frontend (Vercel `jinja-app-web`) | `https://jinja-app-web.vercel.app` | YES (HTTP/2, TLS, HSTS) |
| Backend (Render) | `https://jinja-backend.onrender.com` | YES (via BFF only; browser makes 0 direct calls) |

---

## 4. Anonymous Journey (Journey A) — EXECUTED

Session: fresh, `localStorage` / `sessionStorage` / cookies cleared, no auth cookie
(`GET /api/users/me/` → 401 throughout). Viewport 1265×900 (desktop) for A; 375px for C.

| Phase | Result | Evidence |
|---|---|---|
| **A — Landing** | **PASS** | `GET /` 200; title "KAMI MUSUBI"; concierge intake renders ("今の相談から、向かう神社を見つける" + textarea + theme chips + "この相談ではじめる"); `isSecureContext: true`; no page-level horizontal scroll; dark UI readable; secondary paths (参拝コンパス / 地図 / 神社一覧) present |
| **B — Anonymous Concierge** | **PASS** | Consultation text「仕事について気持ちを整理して、落ち着いて参拝できる神社を探したい」→ input + submit OK; loading resolved; navigated to `/concierge?tid=48` (thread created); not blocked by an auth requirement |
| **C — Recommendation Result** | **PASS** | ≥1 recommendation (**乃木神社**); shrine name shown; reason shown ("仕事や働き方を見直したい相談として受け取れます。／内容との一致が強い"); free info shown (参考情報 / 参拝前にできること / 今回の相談の整理 / 今回の相談との接点 / この神社が持つ文脈); **Premium seam per anonymous contract** — CTA "ログインして意味を深掘りする" → `/auth/login?returnTo=%2Fbilling%2Fupgrade`; detail CTA "神社の詳細を見る" → `/shrines/59?ctx=concierge&tid=48`; no horizontal scroll; reaches bottom (scrollH 1630) |
| **D — Shrine Detail** | **PASS** | `/shrines/59?ctx=concierge&tid=48` → 200; h1 "乃木神社"; no crash; **`bg-slate-100` count = 0, empty `h-32` media slot count = 0** (RH3-3 empty-hero fix LIVE in production); public facts (神社について / 御祭神 乃木希典命・乃木静子命 / 由緒・歴史 with period text); consultation connection (神社との意味の接続 / 今のあなたとの接点 / この場所が合う理由 / 今の状態); **`recommendation_meta` visible** (`data-testid="shrine-detail-recommendation-meta"`: "この神社が1位の理由 ／ 相談内容との一致は「転機・仕事」が主因です。特に 悩みとの一致 が順位を押し上げています。"); **Free/Premium boundary correct** — no "③ 今回の相談との意味" / "④ 参拝するときの視点" full-body sections; **Premium teaser (anonymous)** present, CTA "ログインして意味を深掘りする" → `/auth/login?returnTo=%2Fbilling%2Fupgrade`; Save/Visit region ("質問する" / "ログインしてあとで見返す" / "参拝しました"); no horizontal scroll; reaches bottom (scrollH 2079) |
| **E — Google Maps Directions** | **PASS** | CTA "Googleマップで経路案内" href = `https://www.google.com/maps/dir/?api=1&destination=35.6698%2C139.7268&travelmode=walking` — well-formed Google Maps Directions URL (`api=1`, destination ≈ 乃木神社 area, `travelmode=walking`); not malformed; external handoff; the production app does not crash. (Google Maps routing quality itself is out of scope.) |

---

## 5. Authenticated Free Journey (Journey B) — NOT EXECUTED

**`USER_VERIFICATION_REQUIRED`.** Phases F–L require a production **login / account**.
The QA agent operates under a policy that prohibits creating accounts and entering
passwords to authenticate, so it cannot establish an authenticated production
session. No production login was attempted.

| Phase | Status | Note |
|---|---|---|
| **F — Login (Free)** | NOT EXECUTED | agent cannot create/authenticate a production account |
| **G — Authenticated Free Concierge** | NOT EXECUTED | requires F |
| **H — Save persistence** | NOT EXECUTED | requires F; needs an authenticated write + reload |
| **I — Visit persistence** | NOT EXECUTED | requires F |
| **J — Reflection persistence** | NOT EXECUTED | requires F |
| **K — Timeline** | NOT EXECUTED | requires H/I/J |
| **L — Authenticated Free Premium CTA (RH3-2 prod regression)** | NOT EXECUTED | requires F |

Available indirect evidence for L (RH3-2): the fix was verified in RH3-2 via local
runtime (anonymous / authenticated-free / premium) + 6 unit tests, and the
deployed production bundle contains the authenticated-free CTA copy
("この神社を選ぶ意味を深掘りする") and the `/billing/upgrade` target. The
**production** authenticated-free path itself is unverified.

**Recommended:** a human (or the user, with their own credentials and explicit
authorization) runs Phases F–L on production and records the result. See §13.

---

## 6. Persistence (Phases H / I / J / K)

**NOT EXECUTED** — see §5. Persistence was verified against a real backend + DB at
the **API layer** in a prior audit (PR #2670, local runtime: Save → 201, Visit →
201, Reflection → 201 with state-change, Timeline join shows both events). The
**production** authenticated persistence round-trip (write → reload → still there →
appears in Timeline / My Page) is unverified in this QA.

---

## 7. Premium CTA

| Tier | Where | Result |
|---|---|---|
| **Anonymous** | production Concierge Result + Shrine Detail (desktop + 375px) | **PASS** — CTA "ログインして意味を深掘りする" → `/auth/login?returnTo=%2Fbilling%2Fupgrade` (correct anonymous contract; login flow with `returnTo` preserved) |
| **Authenticated Free** | production Shrine Detail | **NOT EXECUTED** (§5). Expected per RH3-2: "この神社を選ぶ意味を深掘りする" → `/billing/upgrade` direct (no `/auth/login` hop). |
| **Premium** | production Shrine Detail | NOT EXECUTED (no premium session). |

No real payment was executed. No checkout was initiated.

---

## 8. Responsive 375px (Journey C) — EXECUTED (anonymous)

Viewport 375×812 on production.

| Phase | Result | Evidence |
|---|---|---|
| **M — 375px Concierge Result** | **PASS** | `/concierge?tid=48`; no page-level horizontal scroll (0 offending elements); candidate (乃木神社) + meaning hierarchy + Premium seam readable; "神社の詳細を見る" CTA present and tappable; reaches bottom (scrollH 1974); no crash |
| **M — 375px Shrine Detail** | **PASS** | `/shrines/59?ctx=concierge&tid=48`; no horizontal scroll (0 offenders); no crash; **`bg-slate-100` = 0, `h-32` = 0** (RH3-3 fix live at 375px — screenshot confirms the hero shows only "乃木神社" in a token card, no bright empty box); facts (御祭神 / 由緒・歴史) readable; meaning hierarchy readable; `recommendation_meta` (1) readable; Directions CTA clickable (valid URL); Save/Visit buttons present; reaches bottom (scrollH 2355) |
| **M — 375px Premium CTA (anonymous)** | **PASS** | teaser CTA renders without clipping, tappable, copy readable, routes to `/auth/login?returnTo=%2Fbilling%2Fupgrade` |
| **M — 375px Premium CTA (authenticated Free)** | NOT EXECUTED | requires login (§5) |

Screenshot (375px, anonymous Shrine Detail): hero card = "乃木神社" text only, no
empty light box; "操作 / Googleマップで経路案内"; "神社について / 御祭神
乃木希典命・乃木静子命 / 由緒・歴史 / 創始 / 中央乃木会の発足と神社設立許可…";
clean dark layout.

---

## 9. Mobile Web Geolocation (Journey D / Phase N) — NOT EXECUTED

**`USER_DEVICE_VERIFICATION_REQUIRED`.** The QA agent cannot operate a real iPhone
(Safari) or Android (Chrome). 375px viewport emulation is **not** accepted as a
mobile-geolocation pass per the directive.

Production-side preconditions that **were** verified (this session + PR #2679):

| Precondition | Result |
|---|---|
| Production URL is HTTPS | `location.protocol === "https:"` |
| Secure context | `window.isSecureContext === true` |
| Geolocation API present | `'geolocation' in navigator === true` |
| Origin type | normal secure web origin — `getCurrentPosition` / `watchPosition` available |

→ GEO-R environment causes (secure context / origin config) are **not** a factor
on the production origin. This aligns with RH3-4 (#2677), which classified the
mobile geolocation issue as a **code** concern (missing `timeout` at
`ranking/page.tsx` `enableNear()` and `CompassClient.useDevice()`), not an
environment one.

**Hand to a tester** (iPhone Safari and Android Chrome, on
`https://jinja-app-web.vercel.app`):

1. Open the site; confirm the address bar shows `https://`.
2. Go to **参拝コンパス** (Home → 方向から探す, or `/compass`). Enter a birthday +
   purpose. Tap **現在地**.
3. Also try **神社一覧 → 人気 → 近く** and, if visible, the `/concierge` (full)
   **現在地** button.
4. Record, per device: device category (iPhone / Android), browser
   (Safari / Chrome), permission state (Allow / Deny / Ask), whether a permission
   prompt appeared, current-location result (success / failure), the UI shown,
   any error code (1/2/3) if safely visible, retry result, and whether manual
   駅名/住所 input works as a fallback.
5. If it fails, classify against RH3-4's `GEO-R1…GEO-R8`. Do **not** record
   captured coordinates.

---

## 10. Analytics — `card_view` dedupe (RH3-1) — PARTIAL

| Check | Result |
|---|---|
| PostHog live in production | **YES** — client loads `us-assets.i.posthog.com` and transmits to `us.i.posthog.com` (5 analytics resources on a Shrine Detail page view) |
| RH3-1 dedupe code deployed | **YES** — production deploy is from `develop 65575715`, which includes PR #2672 (`ebec8002`, the `firedCardViewKeysRef` firing-layer dedupe in `ShrineDetailArticle.tsx`) |
| Per-event `card_view` count in production | **NOT INDEPENDENTLY VERIFIED** — PostHog batches events into encoded POST bodies and the QA agent has no PostHog project access; `window.posthog` is not exposed on this build for interception |
| Prior verification (RH3-1) | 3 unit tests (same page view re-render → 1 per cardId; `getVisits` async settle → 1; unmount→remount → fires again) + local dev-sink runtime (3× in dev → 1× after the fix) |

**Interpretation:** the dedupe fix is deployed and was proven at the unit + local
runtime level; a direct production event-stream count needs PostHog project
access (a separate check for whoever owns the PostHog project).

---

## 11. Console / Network (Phase P) — PASS

Across the Anonymous Journey (Landing, Concierge, Result, Detail) and the 375px
checks:

| Check | Result |
|---|---|
| Fatal console error | **none** |
| Console errors present | only `401` for guest-gated BFF routes (`/api/users/me/`, `/api/visits/`, `/api/favorites/`, `/api/concierge-threads/`) — expected for an anonymous session; noisy (several retries) but harmless |
| Repeated `5xx` | **none** observed on any journey route |
| CORS error | **none** — all API calls are BFF-relative |
| Mixed-content error | **none** — every request is `https:` |
| BFF requests | succeed — client API calls go to `jinja-app-web.vercel.app/api/*` only; **0** direct calls to `jinja-backend.onrender.com`; BFF proxy returns backend data |
| Google Maps API calls | **0** (Directions is a URL handoff) |

---

## 12. Defects

**Release blockers: none.** No Critical Journey segment that could be executed was
broken.

Non-blocking observations (not defects that gate Test Release; recorded for
awareness — do not fix during QA):

| ID | Observation | Journey | Severity | Note |
|---|---|---|---|---|
| OBS-1 | Anonymous free consultation quota shows "あと **998** 回までは無料で試せます" | A / C (Result) | NON_BLOCKING_DEFECT (product config) | Production anonymous quota appears near-unlimited. Not a journey blocker; a product/config decision (is a low anonymous cap intended for Test Release?). No code change proposed here. |
| OBS-2 | Multiple `401` console errors per page for an anonymous visitor (each guarded BFF endpoint retried) | A / C | NON_BLOCKING (cosmetic/log noise) | Expected guest behaviour; consider quieter handling later. Not a blocker. |

---

## 13. External / User-Device Verification Required

| ID | Item | Who | Why the QA agent could not do it |
|---|---|---|---|
| UV-1 | **Authenticated Free journey on production** — Phases F–L: Login, authenticated Concierge, **Save / Visit / Reflection persistence** (write → reload → Timeline / My Page), authenticated-Free **Premium CTA** (expect "この神社を選ぶ意味を深掘りする" → `/billing/upgrade` direct, no `/auth/login` hop — RH3-2 production regression) | Mother Ship / user (with their own credentials + explicit authorization) | agent policy prohibits creating accounts / entering passwords to authenticate |
| UV-2 | **Mobile Web Geolocation on a real device** — iPhone Safari and/or Android Chrome, per §9 procedure; classify any failure against RH3-4 `GEO-R1…GEO-R8` | Mother Ship / user | agent cannot operate a physical smartphone; viewport emulation is not accepted |
| UV-3 | **Production PostHog `card_view` event count** — confirm one `card_view` per `(event :: cardId :: visibility :: accessLevel :: shrineId :: recommendationInstanceId)` per Shrine Detail page view; scroll / harmless re-render add none; a genuine re-visit is a new page view (new events expected) | whoever owns the PostHog project | agent has no PostHog project access; events are batched/encoded |

---

## 14. Final Verdict

### `USER_DEVICE_VERIFICATION_REQUIRED` (intermediate)

- **Anonymous Journey (A): PASS** end-to-end on production — Landing, Concierge,
  Recommendation Result, Shrine Detail, Directions.
- **Responsive 375px (C): PASS** for the anonymous Concierge Result, Shrine
  Detail, and Premium CTA.
- **RH3-3** (empty Hero) and **`recommendation_meta`** (PR-N3b) are **confirmed
  live in production** (DOM: 0 `bg-slate-100`, 0 empty `h-32`; recommendation_meta
  testid renders with backend text).
- **Console / Network: PASS** — no fatal errors, no `5xx`, no CORS / mixed
  content; Browser → Vercel BFF → Render Backend confirmed (0 direct Render
  calls); PostHog transmitting.
- **No release-blocking defect** was found in any executable segment.

**Not a final `PRODUCTION_CRITICAL_JOURNEY_PASS`** because two segments require
verification the QA agent cannot perform:

1. **UV-2 — Mobile Web device Geolocation** (real iPhone / Android). This is a
   Test Release requirement per the directive; 375px emulation does not satisfy
   it.
2. **UV-1 — Authenticated Free journey on production** (Login → Concierge → Save
   → Visit → Reflection → Timeline → Premium CTA), because the agent may not
   create or authenticate a production account.

**Not `PRODUCTION_CRITICAL_JOURNEY_BLOCKED`** — nothing in any tested segment is
broken.

Mother Ship / user to execute UV-1 and UV-2 (and optionally UV-3) and then issue
the final verdict.

---

## 15. Production write actions performed (normal user operations only)

- Created anonymous Concierge threads via the normal intake flow (production
  `tid=48` and any prior anonymous threads from retries). No authenticated writes.
  No Save / Visit / Reflection. No admin / DB operations. No account created. No
  payment. No personal data or precise location submitted.
- QA cleanup: anonymous consultation threads have no user-facing delete in this
  flow; they are left as-is (no PII, low-value QA records).

---

## 16. Files changed

`docs/audit/production-critical-journey-qa.md` (this file) only. **No production
code, no test, no config.**
