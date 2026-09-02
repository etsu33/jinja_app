# RH3-4 — Mobile Web Geolocation: Cause Audit (no code change)

> **Audit only. No production code was changed.** Per the RH3-4 directive's
> Modification Gate, this phase STOPs before implementation and returns findings to
> Mother Ship, because (a) the failure could not be reproduced with runtime
> evidence in any environment available here, (b) the strongest fixable candidate
> lives in **Compass**, which the RH3-4 directive forbids changing, and (c) a
> proper fix spans multiple independent call sites.
>
> Scope: `apps/web` only. `apps/mobile` (Expo) is out of scope. No MapLibre.

---

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `audit/mobile-web-geolocation` (from `develop`) |
| Base SHA / HEAD | `2ed739dae4047e26f3d9601ae4a34d63fbc86363` |
| `origin/develop` | `2ed739da fix: Shrine Detail Heroのempty-stateを修正 (RH3-3) (#2676)` |
| HEAD == origin/develop | yes |
| Working tree | clean except known untracked `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` (untouched) |
| Duplicate PR / branch for this topic | none (`audit/mobile-web-concierge-ui-quality` and `docs/mobile-web-parity-audit` are unrelated) |

---

## 2. Geolocation production path — every call site

`grep` for `navigator.geolocation` / `getCurrentPosition` / `watchPosition` /
`GeolocationPositionError` / `navigator.permissions` across `apps/web/src`.

| # | File : symbol | Trigger | 3rd-arg options | Error callback | Fallback on failure | Live? |
|---|---|---|---|---|---|---|
| 1 | `src/app/ranking/page.tsx:140` — `PopularTab.enableNear()` | button ("近く") click | **none** (no `timeout`, no `maximumAge`, no `enableHighAccuracy`) | **empty `() => {}`** — silent | implicit: keeps showing global popular list | **live** (secondary; `/ranking` linked from Home) |
| 2 | `src/app/concierge/ConciergeClientFull.tsx:1019` — `useCurrentLocation()` | button ("現在地") click | `{ enableHighAccuracy:false, timeout:8000, maximumAge:300000 }` | `setLocationError("現在地を取得できませんでした。位置情報の許可を確認してください。")` + analytics `direction_origin_result` (`result: code===1 ? "denied" : "failed"`) | manual origin (駅名/住所) input remains | **live** (`/concierge`, `/concierge/full`) |
| 3 | `src/app/navi/[id]/page.tsx:29` — `getLocation()` | mount + retry button | `{ enableHighAccuracy:true, timeout:8000 }` | `setOrigin(null); setLocDenied(true)` | shrine still loads; `locDenied` UI branch | **live** (`/navi/[id]`) |
| 4 | `src/features/map/components/NearbyShrineCardListClient.tsx:75` | `useEffect` on mount | `{ enableHighAccuracy:true, timeout:8000 }` | `clientLog("LOC_FAILED",{code}); setCoords(FALLBACK); setUsedFallback(true); setLoadingLoc(false)` | **explicit `FALLBACK` coordinates + "既定位置" UI** | **live** (map / nearby) |
| 5 | `src/features/compass/CompassClient.tsx:140` — `useDevice()` | button ("現在地") click | **none** (no `timeout`, no `maximumAge`, no `enableHighAccuracy`) | `setDeviceError("現在地を取得できませんでした。駅名・住所から指定してください。")` | manual 駅名/住所 input remains | **live** (Compass; `/compass?ref=home` linked from Home) — **RH3-4 forbids changing Compass** |
| 6 | `src/lib/conciergeChat.ts:35` | (function `conciergeChat`) | `{ timeout:4000 }` | `try/catch` swallow → `location` omitted | request sent without location | **DEAD** — 0 importers (superseded by `src/lib/api/conciergeChat.ts`) |
| 7 | `src/hooks/useGeolocation.ts:47` — `watchPosition` | hook | `{ enableHighAccuracy:true, timeout:10000, maximumAge:30000 }` | `setError(err.message)` | — | **DEAD** — 0 consumers |
| 8 | `src/lib/location.web.ts:9` — `webLocator.current()` | promise util | `{ enableHighAccuracy:true, timeout:8000 }` | `reject(err)` | — | near-dead — used only by `src/app/debug/location/page.tsx` (debug); its other consumer `src/components/UseMyLocationButton.tsx` has **0 consumers** |

### Consumer (what the coordinates feed)

| Call site | Consumer |
|---|---|
| #1 ranking `enableNear` | `usePopularShrines({ near, radiusKm: 30 })` → `/api/populars/` nearby query |
| #2 concierge full `useCurrentLocation` | `userOrigin` → `buildConciergeRequestPayload` → `/api/concierge/chat` (Direction origin) |
| #3 navi | `origin` → route/direction context on `/navi/[id]` |
| #4 nearby | `fetchNearby(lat,lng)` → nearby shrine card list |
| #5 compass `useDevice` | `origin` → `/api/compass/recommendations` (required field; submit is blocked without it) |

### Not a factor

- **No `navigator.permissions` / `permissions.query` anywhere** — every site relies solely on `getCurrentPosition`'s success/error callbacks. (Acceptable per directive; but "previously denied" is only surfaced reactively, and silently at call site #1.)
- **No SSR/hydration access** — every live call site is inside a `useCallback` / `useEffect` / click handler, each guarded by `"geolocation" in navigator` or `!navigator.geolocation`. → **GEO-6 ruled out.**
- **No `isSecureContext` check** in geolocation code, but production is HTTPS (Vercel; `NEXT_PUBLIC_BASE_URL=https://…vercel.app`). No repo evidence of an insecure origin. → GEO-1 not indicated (prod origin itself UNVERIFIED here).
- The **primary Concierge flow** (`/` → `features/home/HomePage`) **does not call `navigator.geolocation` at all**. The geolocation-bearing concierge is the separate `/concierge` "full" variant (call site #2).

---

## 3. Reproduction attempts

| Environment | Available here? | Result |
|---|---|---|
| Desktop Chrome (in-app browser, Chromium) | yes | Not exercised to a failure — the happy path (permission granted) works on call sites #2–#5; no hang observed on desktop. |
| Desktop Chrome + 375px viewport emulation | yes | Same as desktop. Viewport width does not touch any geolocation code path (no width branch anywhere). → **the reported issue is NOT "just a viewport problem".** |
| Chrome DevTools geolocation emulation | not driven this session | — |
| **Production URL** | not exercised | `window.isSecureContext`, prod permission result, prod error codes → **UNVERIFIED** |
| **Preview URL** | not exercised | **UNVERIFIED** |
| localhost | geolocation works under the localhost secure-context exception | not a proxy for prod mobile |
| **iOS Safari (real device)** | **cannot drive** | **NOT_VERIFIED** |
| **Android Chrome (real device)** | **cannot drive** | **NOT_VERIFIED** |

The in-app browser is desktop Chromium. Mobile-viewport emulation does **not**
reproduce iOS Safari / Android Chrome geolocation behaviour: OS Location Services
toggle, Safari per-site permission model, user-gesture timing, and — critically —
a `getCurrentPosition` call that **hangs with no `timeout`** when a fix cannot be
acquired quickly.

**→ The failure was NOT reproduced with runtime evidence in any environment
available here.**

---

## 4. Cause classification

Primary (highest confidence, static evidence):

- **GEO-5 — Timeout / Position unavailable.** Call sites **#1 (`ranking` `enableNear`)** and **#5 (`CompassClient.useDevice`)** invoke `navigator.geolocation.getCurrentPosition(success, error)` **with no third argument** → **no `timeout`**, no `maximumAge`. On mobile browsers (iOS Safari especially, and Android Chrome with weak GPS / power-save), acquisition can stall indefinitely; with no `timeout` the **error callback never fires**. Symptom: user taps "現在地", nothing happens, no error, no result — i.e. "現在地取得ができない". `maximumAge` unset also means a recent cached fix is never accepted.

Contributing:

- **GEO-4 — Error handling.** Call site **#1** has an **empty error callback**: a `PERMISSION_DENIED` / failure is completely silent (falls through to the global popular list). The user gets no feedback that "近く" did nothing.
- **GEO-8 — Browser-specific.** The highest-risk instance (#5 Compass) is a location-first feature and the classic iOS-Safari failure surface. Cannot be confirmed without a real iOS device.

Determination for the reported issue:

- **GEO-10 — Not Reproduced (this environment).** With desktop-Chromium tooling only, the mobile failure is not observable. The GEO-5 / GEO-4 gaps above are code-evident but not yet tied to a captured repro.

Ruled out: GEO-6 (SSR — guarded everywhere), GEO-3 (unsupported — all sites feature-detect + fall back). GEO-1 (secure context) and GEO-9 (environment config) are **UNVERIFIED** (prod origin not exercised) but not indicated by the repo.

---

## 5. Permission / Secure Context / Error handling

| Aspect | State |
|---|---|
| Permissions API (`navigator.permissions.query`) | **not used anywhere** — no proactive `granted` / `prompt` / `denied` detection |
| Secure context guard in code | none; prod is HTTPS (Vercel) — `getCurrentPosition` is a no-op / immediate error on non-secure origins |
| `PERMISSION_DENIED` (code 1) | #2 shows a message + analytics `denied`; #3 `setLocDenied(true)`; #4 `FALLBACK` + log; #5 shows a message; **#1 silent** |
| `POSITION_UNAVAILABLE` (code 2) | #2 message + analytics `failed`; #3 `locDenied`; #4 `FALLBACK`; #5 message; **#1 silent** |
| `TIMEOUT` (code 3) | reachable **only at #2, #3, #4** (they set `timeout`). **Unreachable at #1 and #5** — no `timeout` → the callback that would deliver code 3 never runs. |
| Loading state stuck forever | #4 always clears `setLoadingLoc(false)`. #2/#3/#5 have no dedicated "acquiring…" spinner tied to the call, so a hang shows as an unresponsive button rather than a spinner-forever. #1 has no loading state at all. |

---

## 6. Fail Safe

Location failure does **not** brick the app:

- **Primary Concierge** (`/` → HomePage) — no geolocation dependency at all.
- **`/concierge` full** — manual origin (駅名/住所) input remains; `locationError` shown.
- **Compass** — manual 駅名/住所 input remains; `deviceError` shown (when the callback fires).
- **Map / Nearby** — explicit `FALLBACK` coordinates + a "既定位置" indicator.
- **`/navi/[id]`** — the shrine still loads; `locDenied` branch.
- **Shrine Detail, Google Maps Directions (URL handoff), Save / Visit / Reflection** — none depend on geolocation.

The one place a user can get **stuck with no feedback** is a **no-`timeout`
hang at #1 (ranking "近く") or #5 (Compass "現在地")** — the button appears dead.
At #5 this also blocks Compass submit (origin is required), though manual input is
the documented alternative.

---

## 7. Why this is a STOP (not a fix in this PR)

| STOP condition (RH3-4 directive) | Met? |
|---|---|
| iOS 実機でしか再現できず証拠不足 | **Yes** — cannot drive iOS Safari; failure not reproduced. |
| 複数 component / route に大規模影響 | **Yes** — the fix touches ≥ 2 live call sites (#1, #5) with independent inline implementations; a durable fix is a shared helper (timeout + `maximumAge` + consistent error/fallback) applied across #1/#2/#3/#5. |
| Compass 変更が必要 | **Yes** — the highest-risk instance (#5 `CompassClient.useDevice`) is the missing-`timeout` `getCurrentPosition`, and RH3-4 forbids Compass changes. |
| production / preview origin 設定が原因の可能性 | **UNVERIFIED** — prod `isSecureContext` / permission behaviour not exercised. |

Per "原因確認前に修正しない": the cause is **code-evident but not
runtime-confirmed**, and the most likely instance is out of bounds for this PR.

---

## 8. Recommended follow-up (for Mother Ship)

**Proposed next PR — `fix: web geolocation を共通化して timeout/fallback を統一` (implementation, separate from this audit).** Scope, minimal and additive:

1. Introduce one shared helper (e.g. extend the already-present but unused
   `src/hooks/useGeolocation.ts`, or a `getCurrentPositionSafe()` util) that
   **always** passes `{ enableHighAccuracy:false, timeout:8000, maximumAge:300000 }`
   (matching call site #2, the most considered one), always resolves the loading
   state, and surfaces an error string on every `GeolocationPositionError` code.
2. Route call sites **#1 (`ranking` `enableNear`)**, **#2**, **#3**, **#5
   (`CompassClient.useDevice`)** through it. **#5 requires the Compass-change ban
   to be lifted** — flag explicitly.
3. Give **#1** a visible loading + error state (currently silent).
4. Delete dead code: `src/lib/conciergeChat.ts`, `src/hooks/useGeolocation.ts`
   (if not adopted as the helper), `src/components/UseMyLocationButton.tsx`
   (0 consumers) — or keep as a separate cleanup PR.
5. Tests per the RH3-4 matrix: success / `PERMISSION_DENIED` / `POSITION_UNAVAILABLE`
   / `TIMEOUT` / unsupported / no-duplicate-request. `NearbyShrineCardListClient`
   (#4) already has a geolocation test to model on.
6. No Permissions API, no MapLibre, no backend / schema / Analytics changes, no
   new location UX, no coordinate persistence/logging.

**Real-device verification still required** (Mother Ship → user), regardless of
the fix — see §9.

---

## 9. Real-device verification checklist (hand to a tester)

For **iOS Safari** and **Android Chrome**, on the **production URL**:

1. Open the site. Confirm the address bar shows `https://` (secure context).
2. Go to **Compass** (Home → 方位, or `/compass`). Enter a birthday + purpose.
   Tap **現在地**.
   - Expected: a permission prompt (first time), then an origin is set, or a
     visible error ("現在地を取得できませんでした。駅名・住所から指定してください。").
   - **Bug**: tap does nothing — no prompt, no error, button looks dead — for
     more than ~10s.
3. Repeat on **Ranking → 人気 tab → 近く** toggle.
   - **Bug**: toggling "近く" never changes the list and shows no message.
4. Repeat on **/concierge (full)** → **現在地** button, and on **/navi/<id>**.
5. If a bug occurs, record: URL, browser + OS version, whether a permission
   prompt appeared, iOS Settings → Privacy → Location Services state, Safari
   Settings → Websites → Location state, the exact UI shown, any console error
   (`code` 1/2/3), and whether a **retry** or **manual 駅名/住所 input** works.
6. Also note whether it reproduces on that same device's **Chrome** (Android) or
   a **different network** (weak GPS / indoors).

Do not record captured coordinates anywhere.

---

## 10. Files changed

`docs/audit/mobile-web-geolocation-rh3-4.md` (this file) only. **No production
code, no test, no config.**
