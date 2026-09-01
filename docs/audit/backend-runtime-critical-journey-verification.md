# Backend Runtime & Critical Journey Verification Audit

> Runtime verification / integration audit. **No production fix was made in this PR.**
> The only file changed is this document. Defects found are recorded, classified,
> and turned into follow-up work-package candidates — not fixed here.
>
> Section 18 (Release Hardening Status) is a **technical finding only**. It is not a
> test-release go/no-go decision. Section 19 candidates are **unordered**.

---

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `audit/backend-runtime-critical-journey` (created from `develop`) |
| Base SHA / HEAD | `1cc02b3b997174e793860d0a7a5ee93d1f98ad32` |
| `origin/develop` at audit time | `1cc02b3b` — `docs: audit MVP remaining work and release readiness (#2669)` |
| Local `develop` | `1cc02b3b` — already in sync with `origin/develop`; no fast-forward needed |
| **#2669 merge evidence** | `git log origin/develop` → top commit is `1cc02b3b docs: audit MVP remaining work and release readiness (#2669)`. **PASS.** |
| Working tree | clean except two known local untracked files (below) |
| Known untracked (left untouched) | `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` — confirmed untracked at audit start and end; not staged, not committed, not in PR diff |

---

## 2. Runtime Environment

Secrets are not reproduced. Values shown are non-secret configuration facts.

| Layer | Finding | Evidence |
|---|---|---|
| Python | 3.11.13 via project venv `/Users/morietsu/Desktop/jinja_app/.venv` (not the stale `~/Developer/...`) | `.venv/bin/python --version` |
| Node | v20.19.5 | `node --version` |
| Django | 5.2.16; DRF 3.17.1; `djangorestframework-simplejwt` 5.5.1; `psycopg` 3.3.4; `dj-database-url` 3.1.2; `django-redis` 7.0.0 (installed, not used at runtime); `gunicorn` 25.1.0 | `.venv/bin/pip list` |
| Django settings module | `shrine_project.settings` | `backend/manage.py:9`, `backend/shrine_project/wsgi.py:14` |
| **ROOT_URLCONF** | **`shrine_project.urls`** (NOT `config.urls`) | `settings.py:299`; runtime `settings.ROOT_URLCONF` |
| Database (this audit) | `postgresql://admin@127.0.0.1:5432/jinja_db` — **LOCAL DEV DB**. Engine resolved to `django.contrib.gis.db.backends.postgis`. `USE_SQLITE=0`, `USE_GIS=1`. | `backend/.env.local`; `django.setup()` → `settings.DATABASES['default']` |
| DB reachability | PostgreSQL listening and accepting connections on `127.0.0.1:5432` | `pg_isready -h 127.0.0.1 -p 5432` → "接続を受け付けています"; `nc -z` OK |
| Redis | **Not required for boot.** Cache backend is `django.core.cache.backends.locmem.LocMemCache`. | runtime `settings.CACHES['default']['BACKEND']` |
| Env file load order | `backend/.env.local` (via `environ.Env.read_env`, `BASE_DIR = backend/`), then `.env.test` only under pytest | `settings.py:26-63` |
| `DEBUG` (local) | `False` (last assignment in `backend/.env.local` wins over an earlier `DEBUG=1`) | runtime `settings.DEBUG` |
| Billing (local) | `BILLING_STUB_PLAN=premium`, `BILLING_STUB_ACTIVE=1` in `backend/.env.local`; `Makefile:dev` also forces these. **Local runtime treats the session as premium.** | `backend/.env.local`; `temples/services/billing_state.py` ("stub運用なら、認証済みでも env を正とする") |
| Frontend → backend | `API_BASE_SERVER=http://127.0.0.1:8000`, `DJANGO_API_BASE_URL=http://127.0.0.1:8000`, `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api` | `apps/web/.env`, `apps/web/.env.local` |
| Frontend flags (local) | `NEXT_PUBLIC_CONCIERGE_RENDERER=new`, `NEXT_PUBLIC_FORCE_BILLING_PLAN=free`, `NEXT_PUBLIC_MAP_PROVIDER=maplibre`, `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS=1` | `apps/web/.env.local` |
| Deploy automation | Out of scope for this audit. (`scripts/deploy.sh` remains a stub; not exercised.) | — |

**Limitations of this environment**

- Local dev Postgres, **not production** — every data figure below is
  `UNVERIFIED_RUNTIME_DATA` for production.
- `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS=1` → map tiles / external media do not load.
- Local billing stub = premium → the Free-tier Premium boundary on Shrine Detail
  could not be observed (see RF findings).
- No physical device; 375px via browser viewport emulation.
- Per task constraint: no Render production shell procedure is proposed anywhere
  in this document.

---

## 3. Backend Boot Result

**Status: PASS.**

| Check | Result | Evidence |
|---|---|---|
| `python manage.py check` | `System check identified no issues (0 silenced).` | command output |
| `django.setup()` + settings import | no exception | audit script |
| Dev server boot | `manage.py runserver 127.0.0.1:8000 --noreload` came up and served requests | server process alive; request log populated |
| `GET /` | 200 | `curl` |
| `GET /api/` | 200 | `curl` |
| `GET /api/shrines/` | 200 (105 shrines, paginated) | `curl` |
| `GET /admin/` | 302 → login (expected) | `curl` |
| Health endpoint | **None** — `GET /healthz` 404, `GET /api/health/` 404 | `curl` (minor: no dedicated health/liveness route) |
| Import errors / startup exceptions | none | `manage.py check`, boot |
| Required env missing | none for boot | boot succeeded with `backend/.env.local` |

Category if it had failed: n/a (it did not fail).

---

## 4. Migration Result

**Status: PARTIAL — 2 of 4 pending migrations applied; 2 blocked (fail-closed by design).**

At audit start `manage.py migrate --check` → exit 1; `--plan` listed 4 pending
`temples` migrations, **all `RunPython` data-cleanup, no schema operations**:

| Migration | Type | Result on this local dev DB |
|---|---|---|
| `0098_remove_stray_test_source_id1` | RunPython (data) | **Applied** by this audit |
| `0099_fix_shrine_49_coordinates` | RunPython (data) | **Applied** by this audit |
| `0100_p8a_duplicate_shrine_shadow_cleanup` | RunPython (data) | **BLOCKED** — `PreconditionViolation: PRESTATE_MISMATCH: shadow pk 101 name_jp is '承認テスト神社', expected '給田六所神社' — P8_A_PRESTATE_POLICY = FAIL_CLOSED` |
| `0101_p8b_remove_non_shrine_artifact_id105` | RunPython (data) | Not reached (0100 aborted the run; transaction rolled back) |

Analysis (per task rule "Do Not Confuse Environment Failure with Product Bug"):

- These are **data-cleanup** migrations, not schema migrations. The DB **schema**
  is fully migrated; the app boots and every endpoint works with 0100/0101
  pending.
- `0100` is **explicitly designed to fail closed**: it asserts a recorded
  pre-state snapshot before touching rows and raises rather than "repair, guess,
  or partially clean" (`temples/migrations/0100_p8a_duplicate_shrine_shadow_cleanup.py:244,483`).
- This particular local dev DB has accumulated QA fixtures — `Shrine` pk 101 =
  `承認テスト神社` ("Approval Test Shrine"), pk 105 = `重複検証神社（別宮）`
  ("Duplication-verification Shrine (branch)") — so the recorded pre-state does
  not match, and the guard fires.
- This is **not a schema error** and is **not, on this evidence, a migration
  code defect**. It is local-DB data divergence meeting an intentional guard.

Classification: **R0 (environment) / DATA_BLOCKED** for this DB. See RF-1.
Not treated as STOP-B because there is no schema error and no broken migration
code — the audit continued and the runtime journey was fully exercised.

---

## 5. Data Readiness Runtime Result

**DB type: local dev PostGIS (`jinja_db` on `127.0.0.1`). NOT production.**

Direct model counts (local dev DB):

| Entity | Count (LOCAL DEV) | Production |
|---|---|---|
| Users | 8 (+1 disposable fixture created by this audit → 9) | `UNVERIFIED_RUNTIME_DATA` |
| Shrines | 105 (100 with goriyaku text, 105 with coordinates) | `UNVERIFIED_RUNTIME_DATA` |
| `Deity` rows | 0 | `UNVERIFIED_RUNTIME_DATA` |
| `ShrineDeity` links | 233 | `UNVERIFIED_RUNTIME_DATA` |
| `ShrineHistory` | 182 | `UNVERIFIED_RUNTIME_DATA` |
| `ShrineKnowledgeSource` | 114 | `UNVERIFIED_RUNTIME_DATA` |
| `GoriyakuTag` | 46 | `UNVERIFIED_RUNTIME_DATA` |
| `ConciergeThread` | 795 at start → ~802 after audit consultations | `UNVERIFIED_RUNTIME_DATA` |
| `Goshuin` | 0 | `UNVERIFIED_RUNTIME_DATA` |
| `Visit` | 7 at start → 8 after audit | `UNVERIFIED_RUNTIME_DATA` |

`knowledge_coverage_report` (existing command, read-only, `scope = qa_filtered_db`,
100 shrines):

| Metric | Value (LOCAL DEV) |
|---|---|
| Total DB shrines | 105 |
| Audit-target shrines (scope) | 100 |
| Excluded test shrines | 5 |
| Knowledge coverage | 86 (86.0%) |
| Zero knowledge | 14 (14.0%) |
| Deity coverage | 86 (86.0%) |
| History coverage | 84 (84.0%) |
| Source coverage | 86 (86.0%) |
| Both deity + history | 84 (84.0%) |
| Verified sources / total | 111 / 111 |
| Confidence distribution | high 396, medium 19 |

This local dev DB is **materially more representative** than the stale SQLite
snapshot cited in audit #2669 (which showed 0 knowledge rows). It is still not
production. **Production knowledge coverage: `UNVERIFIED_RUNTIME_DATA`.**

---

## 6. Authentication Runtime Result

**Guest**

| Check | Result | Evidence |
|---|---|---|
| Landing / concierge intake reachable as guest | PASS — `/` renders the consultation intake; copy: "未ログインでも相談できます。保存にはログインが必要です。" | browser 375px |
| Guest concierge POST | PASS — `POST /api/concierge/chat/` (`permission_classes = [AllowAny]`) → 200; anonymous cookie attached | `curl`; `django.server` log `POST /api/concierge/chat/ ... 200` |
| Login-required actions gated | PASS — `GET /api/users/me/` → 401; `GET /api/concierge-threads/` → 401; Save shows "ログインしてあとで見返す"; Premium CTA → `/auth/login?returnTo=%2Fbilling%2Fupgrade` | `curl`; browser DOM |

**Authenticated (disposable local fixture — no credentials recorded)**

| Check | Result | Evidence |
|---|---|---|
| JWT create | PASS — `POST /api/auth/jwt/create/` → 200, access token (len 232) | `curl` |
| Current user | PASS — `GET /api/users/me/` with `Authorization: Bearer` → 200, profile payload | `curl` |
| **`POST /api/token/`** | **404 Not Found** — this route does not exist on the running server | `curl -i` |

Finding: the JWT endpoints are `api/auth/jwt/create|refresh|verify/` defined in
`shrine_project/urls.py:91-93`. The `api/token/*` triple lives only in
`backend/config/urls.py`, which is **not wired** (`config/` has no `__init__.py`,
no settings/wsgi; `ROOT_URLCONF = shrine_project.urls`). Audit #2669 cited
`backend/config/urls.py` as the root URLconf — that reference is **incorrect at
runtime**. See RF-2. (The web BFF already uses the correct path — e.g.
`apps/web/src/app/api/concierge/chat/route.ts` calls `/api/auth/jwt/refresh/`.)

---

## 7. Concierge Runtime Result

Consultation text used (neutral, no religious assertion):
「仕事について気持ちを整理して、落ち着いて参拝できる神社を探したい」

**Backend, guest, `POST /api/concierge/chat/` — HTTP 200, ~55 KB, ~170 ms.**

| Contract element | Result |
|---|---|
| `ok` | `true` |
| Thread created | yes — `thread_id` returned (795 → increasing across calls); `data.thread_id` echoed |
| Intent extraction | `intent = {"kind": "money_work", "consultation_axis": "other"}` (matched 仕事) |
| Recommendation array | `data.recommendations` — **3 items** |
| Shrine IDs valid | 59 乃木神社, 36 生田神社, 33 椿大神社 — all resolve via `GET /api/shrines/<id>/` |
| Server error | none |
| Serializer / mapping crash | none — frontend rendered the payload without error (Section 9) |
| Perf log | `TOTAL ... total_ms=167.7 status=200 mode=message candidates=100 recs=3 sql_count=0` |

Path in use: **heuristic (non-LLM)** — `CONCIERGE_USE_LLM` default `False`, left
off as required. Not turned on.

---

## 8. Recommendation Runtime Result

Per-recommendation contract (item 0, 乃木神社) — all present and parseable:

| Field | Observed |
|---|---|
| `recommendation_instance_id` | `"8de24335"` (API call); `"30a706bd"` (browser session) — join key present |
| `recommendation_reason_v4` | well-formed prose, knowledge-grounded (deities + goriyaku + visit style + next action) |
| `recommendation_reason_v4_detail` | `{version:"v4", reason_text, fact:{label,name,deity,shrine_history,place_context,history_theme,goriyaku,visit_style_tags,evidence[...]}}` |
| `rank_explanation` | `{primary_axis:"fallback", primary_axis_ja:"近さ", matched_need_tags:["career"], contributors:[need/distance/...] with weights}` |
| `rank_comparison` | `{rank:1, is_top:true, top_name:"乃木神社", gap_from_top:0.0, comparison_summary:"この神社が現在の1位です。"}` |
| `recommendation_reason_quality` | `{knowledge_backing_class:"FULLY_KNOWLEDGE_BACKED", evidence_rate:1.0, deity_knowledge_used:true, history_knowledge_used:true}` |
| `knowledge_deities` | 2 entries with `confidence:"high"` |
| `knowledge_histories` | 3 entries (`founding` / `historical_event`) with `period_text`, `confidence` |
| `action_suggestion_v4_preview` | primary + secondary action + reflection prompt + `action_source` |
| `trust_metadata` | `null` on this item (field present; not populated) |

No `undefined`/`null` fatal path; no missing-contract-field crash; frontend
ViewModel generation succeeded (Section 9).

**Content-quality observations (explicitly out of scope for pass/fail per task
instruction; recorded for Mother Ship):**

- The **legacy top-level `reason`** and the result **`message`** are degenerate on
  the heuristic path — e.g. "ご利益のご利益で知られる乃木神社は、今の願いを願う
  参拝先として適しています。" (unfilled template slots: doubled "ご利益",
  "願いを願う"). The `recommendation_reason_v4*` fields that the reading-flow UI
  actually renders are **not** affected. See RF-3.
- Recommended 生田神社 (Kobe) and 椿大神社 (Mie) are not near the Tokyo coords
  passed (`35.681,139.767`), yet the `message` says candidates were organised
  "近さ" (by proximity). Ranking-quality item, not a runtime failure.
- `consultation_axis` differs between `intent` (`"other"`) and the recommendation
  (`"career_change"` / `"career"`). Minor internal inconsistency.

---

## 9. Concierge Result Browser Result (375px)

**Status: PASS.**

| Criterion | Result |
|---|---|
| URL | `/concierge?tid=802` after submit (guest) |
| Page-level horizontal scroll | none (`scrollWidth == clientWidth == 375`, 0 offending elements) |
| Reading-flow renders | yes — "候補", "今の相談に近い方向の神社 / 乃木神社", "相談内容・ご利益との一致", "参考情報 (乃木希典命、乃木静子命)", "参拝前にできること" + action |
| Free-tier state visible | "あと 2回までは無料で試せます" |
| Fatal error / crash | none |
| Text clipping | none observed |
| Vertical scroll reaches bottom | yes (`atBottom = true`, scrollHeight ~1974) |
| Primary CTA usable | "神社の詳細を見る" → `/shrines/59?ctx=concierge&tid=802` |
| Premium seam readable | "ログインして意味を深掘りする" → `/auth/login?returnTo=%2Fbilling%2Fupgrade` |
| Dark mode | rendered in dark theme, readable |

Console during flow: WebSocket HMR noise + `401` for guest-gated endpoints
(favorites / concierge-threads) — expected. The `500` / `GET_SHRINE_FAILED`
entries seen earlier correlate with the dev server's first cold compile; after
warm-up the backend log shows the same routes returning `200`.

---

## 10. Shrine Detail Runtime Result (375px)

**Status: PASS.** URL `/shrines/59?ctx=concierge&tid=802`.

| Criterion | Result |
|---|---|
| Page loads, no crash | PASS (`crash = false`, no "Application error") |
| Page-level horizontal scroll | none (`scrollWidth 375`, 0 offenders) |
| Vertical scroll reaches bottom | yes (scrollHeight ~2726) |
| Shrine facts | 御祭神 (乃木希典命, 乃木静子命); 由緒・歴史 with `period_text`; 出典 「乃木神社 由緒」 |
| Meaning layers (Direction C hybrid) | "この神社の意味" headline; "神社との意味の接続" → 今のあなたとの接点 / この場所が合う理由 / 今の状態 |
| Consultation connection | "③ 今回の相談との意味" section present |
| Visit perspective | "④ 参拝するときの視点" section present |
| `recommendation_meta` (PR-N3b) | **rendered** — `data-testid="shrine-detail-recommendation-meta"` present; heading "この神社が1位の理由"; body "近さや候補条件を含めた総合順位です。特に 悩みとの一致 が順位を押し上げています。" (matches backend `rank_explanation` / `rank_comparison` verbatim) |
| Evidence / Deep Dive | "参考情報" + "この神社について質問する" render without crash |
| Directions action | "Googleマップで経路案内" button present (Section 11) |
| Save / Visit UI | "ログインしてあとで見返す" (guest save gate), "参拝しました" (visit) — no fatal break |
| Premium teaser (`shrine-detail-premium-teaser`) | **0 found** — session rendered as **premium** (full meaning, no teaser, no upgrade link) because local billing stub = premium/active. Free-tier teaser DOM **not verified** — `BLOCKED_BY_ENVIRONMENT`. |

**Known Responsive QA Backlog (from G4):**

| Item | Verdict |
|---|---|
| Full Concierge Result @ 375px | **PASS** |
| Full Shrine Detail @ 375px | **PASS** (layout); one blank light-coloured box where a map/media container sits — see RF-5 |

---

## 11. Directions Result

**Status: PASS (external handoff contract).**

| Check | Result |
|---|---|
| href generated | `https://www.google.com/maps/dir/?api=1&destination=35.6698%2C139.7268&travelmode=walking` |
| URL format valid | yes — Google Maps Directions API URL scheme |
| Destination identifies shrine | `35.6698,139.7268` ≈ 乃木神社, 東京都港区赤坂 (correct area) |
| Opens externally | `target="_blank"` |
| Link text | "Googleマップで経路案内" |

Live Google Maps routing / billing not exercised (not required this task).

---

## 12. Secondary Journey Result

Authenticated as the disposable local fixture. **API-layer persistence
RUNTIME_VERIFIED:**

| Step | Request | Result |
|---|---|---|
| Save / Favorite | `POST /api/favorites/ {"shrine_id":59}` | 201; body returns favorite `id:21` with embedded shrine; `GET /api/favorites/` then returns it |
| (contract note) | `{"shrine":59}` | 400 `either shrine_id or place_id is required` — field is `shrine_id`, not `shrine` |
| Visit | `POST /api/shrines/59/visit/ {}` | 201 `{"id":11,"created":true}`; `GET /api/visits/` → `count:1`, `status:"added"` |
| Reflection | `POST /api/shrines/59/reflection/ {"answer":"..."}` | 201; body includes `state_change_direction`, `state_change_summary`; `GET /api/reflections/` → `count:1` |
| (contract note) | `{"body":...,"mood":...}` | 400 `answer: この項目は必須です` — field is `answer` |
| History / Journey Timeline | `GET /api/journeys/timeline/` | 200 — returns `reflection_created` ("振り返りを書きました") **and** `visit_completed` ("乃木神社に参拝しました。"), newest first |

**My Page browser render:** not verified this run — the browser session was a
guest (no auth cookie), and form login through the browser pane was unreliable
this session. Data layer that My Page consumes is verified above. Status:
`UNVERIFIED` (browser), `RUNTIME_VERIFIED` (API + persistence + timeline join).

---

## 13. Analytics Runtime Result

**Classification: CLIENT_RUNTIME_VERIFIED (client-side emission).**

`next dev` uses the dev analytics sink (`ConsoleAnalyticsProvider` →
`track()` → `localStorage["app:track:dev-events"]`). PostHog initialises **only**
in a production build with `NEXT_PUBLIC_POSTHOG_KEY`
(`apps/web/src/lib/analytics/providers.ts`), so `window.posthog` is absent here —
by design, not a defect.

Events captured during the Concierge → Shrine Detail navigation (dev sink, 96
buffered):

| Event | Payload highlights |
|---|---|
| `shrine_detail_view` | `source:"concierge_result"`, `shrineId:59`, `recommendationInstanceId:"30a706bd"` |
| `card_view` ×6 per render | `cardId ∈ {context_reason, shrine_meaning, consultation_summary, personal_meaning, saved_record, recommendation_meta}`, `source:"shrine_detail"`, `accessLevel:"premium"`, `visibility:"visible"`, `shrineId:59`, `recommendationInstanceId` (join key per instrumentation contract §7) |

- No analytics runtime exception; no client error attributable to analytics.
- `recommendation_meta` `card_view` fires and corresponds to visible DOM (matches
  the PR-N3b intent).
- **Observation:** the six `card_view` events re-fire on every scroll / re-render
  (repeated identically many times in the buffer). Downstream dedupe may absorb
  this; still worth a check. See RF-6.
- Backend/dashboard delivery E2E: not in scope; status `UNVERIFIED_DELIVERY`.

---

## 14. Critical Journey Matrix

| Step | Static connection | Runtime status | Evidence | Blocker |
|---|---|---|---|---|
| Landing | connected | **RUNTIME_VERIFIED** | `/` renders concierge intake @375px, guest-capable | none |
| Concierge (intake) | connected | **RUNTIME_VERIFIED** | textarea + submit; consultation submitted as guest | none |
| Consultation submit | connected | **RUNTIME_VERIFIED** | `POST /api/concierge/chat/` → 200; thread created | none |
| Backend | connected | **RUNTIME_VERIFIED** | `manage.py check` clean; server serves; request log 200s | none |
| Recommendation | connected | **RUNTIME_VERIFIED** | 3 recs, valid shrine IDs, full v4 + rank + knowledge contract | none (content-quality caveat RF-3) |
| Result render | connected | **RUNTIME_VERIFIED** | `/concierge?tid=…` reading-flow @375px, no h-scroll, reaches bottom | none |
| Shrine Detail | connected | **RUNTIME_VERIFIED** | `/shrines/59` @375px, all sections + `recommendation_meta`, no crash | none (Free-tier teaser BLOCKED_BY_ENVIRONMENT) |
| Directions | connected | **RUNTIME_VERIFIED** | valid Google Maps dir URL, `target=_blank` | none |
| Save / Favorite | connected | **RUNTIME_VERIFIED** (API) | `POST /api/favorites/` → 201, persisted | none |
| Visit | connected | **RUNTIME_VERIFIED** (API) | `POST /api/shrines/59/visit/` → 201; `GET /api/visits/` count 1 | none |
| Reflection | connected | **RUNTIME_VERIFIED** (API) | `POST /api/shrines/59/reflection/` → 201 with state-change | none |
| My Page / History | connected | **RUNTIME_VERIFIED** (API) / `UNVERIFIED` (browser) | `GET /api/journeys/timeline/` shows visit + reflection | none |

---

## 15. Runtime Failures

No `R1` (release-blocker) runtime failure was found. No `5xx` on the critical
journey after warm-up, no UI crash, no contract mismatch that broke rendering.

### Runtime Finding RF-1 — Data-cleanup migrations 0100/0101 fail closed on the local dev DB

- **Classification:** R0 (environment) / DATA_BLOCKED — not a schema error; not, on this evidence, a migration code defect.
- **Severity:** R0 locally. Potential R2 *iff* the same pre-state mismatch exists on the target production DB (unknown from here).
- **Reproduction:** `cd backend && ../.venv/bin/python manage.py migrate temples` against `jinja_db` on `127.0.0.1`.
- **Expected:** all pending `temples` migrations apply.
- **Actual:** `0098`, `0099` apply; `0100_p8a_duplicate_shrine_shadow_cleanup` raises `PreconditionViolation: PRESTATE_MISMATCH: shadow pk 101 name_jp is '承認テスト神社', expected '給田六所神社' — P8_A_PRESTATE_POLICY = FAIL_CLOSED`; transaction rolls back; `0101` not reached.
- **Error summary:** intentional fail-closed guard in the migration; local DB `Shrine` pk 101 / 105 hold QA fixtures (`承認テスト神社`, `重複検証神社（別宮）`) instead of the recorded snapshot.
- **Evidence:** `temples/migrations/0100_p8a_duplicate_shrine_shadow_cleanup.py:244,483`; `manage.py showmigrations temples` (0100/0101 `[ ]`); `Shrine.objects.get(pk=101).name_jp == '承認テスト神社'`.
- **Suspected layer:** DB data state (local), not code.
- **Release impact:** none for app runtime (schema is current; endpoints work). Migration-on-deploy would abort **if** production data does not match the recorded pre-state — needs verification against a clean / prod-representative DB.
- **Follow-up PR candidate:** WP-A.

### Runtime Finding RF-2 — `backend/config/urls.py` is dead; `api/token/*` routes 404

- **Classification:** dead / misleading code.
- **Severity:** R3 (no functional break — the correct routes exist and are used).
- **Reproduction:** `curl -i -X POST http://127.0.0.1:8000/api/token/` → `404`.
- **Expected (per audit #2669 evidence index):** `api/token/`, `api/token/refresh/`, `api/token/verify/` served from the root URLconf.
- **Actual:** `ROOT_URLCONF = shrine_project.urls`; JWT routes are `api/auth/jwt/create|refresh|verify/` (`shrine_project/urls.py:91-93`). `backend/config/` has only `urls.py` + `__pycache__` — no `__init__.py`, not a package, imported by nothing; last touched years ago (#166).
- **Error summary:** stale URL module never wired; a prior audit cited it as authoritative.
- **Evidence:** `settings.ROOT_URLCONF`; `ls backend/config/`; `grep -r "config.urls" backend` → no hits; `curl` 404.
- **Suspected layer:** routing / repo hygiene + audit documentation.
- **Release impact:** none functional. Risk is future confusion (as already happened in #2669).
- **Follow-up PR candidate:** WP-B.

### Runtime Finding RF-3 — Heuristic concierge `reason` / result `message` text is degenerate

- **Classification:** content generation defect (heuristic path).
- **Severity:** R3 — recommendations still render; the reading-flow UI uses the well-formed `recommendation_reason_v4*` fields, not this text.
- **Reproduction:** `POST /api/concierge/chat/ {"message":"仕事について…","lat":35.681,"lng":139.767}`; inspect `data.recommendations[*].reason` and top-level `message`.
- **Expected:** natural sentence with filled slots.
- **Actual:** "ご利益のご利益で知られる乃木神社は、今の願いを願う参拝先として適しています。" — doubled "ご利益", "願いを願う"; slots not substituted.
- **Evidence:** captured response body (`cc1_body.json` in audit scratch); `recommendation_reason_v4` on the same item is well-formed.
- **Suspected layer:** heuristic reason template in the recommendation builder (non-LLM path).
- **Release impact:** if any surface shows the legacy `reason` / `message` verbatim to users, copy quality is poor. The verified reading-flow surfaces do not.
- **Follow-up PR candidate:** WP-C.

### Runtime Finding RF-4 — Ranking surfaces QA-fixture shrines at the top on the local DB

- **Classification:** R0 (environment) / DATA_BLOCKED — same root cause as RF-1 (unapplied `0100`/`0101`).
- **Severity:** R0 locally; would be R2 if present in production data.
- **Reproduction:** `GET /api/populars/?limit=3` → results `[105 "重複検証神社（別宮）", 104 "重複検証神社", …]`.
- **Expected:** real shrines ranked by `popular_score`.
- **Actual:** duplicate-verification test shrines rank #1/#2.
- **Evidence:** `curl` response.
- **Suspected layer:** DB data state (local).
- **Release impact:** none if production data is clean; the `0100`/`0101` cleanup is meant to remove exactly these artifacts.
- **Follow-up PR candidate:** WP-A (shared with RF-1).

### Runtime Finding RF-5 — Shrine Detail @375px shows a large blank light-coloured box

- **Classification:** R0 (environment) / BLOCKED_BY_ENVIRONMENT — likely a MapLibre tile container with tiles disabled (`NEXT_PUBLIC_DISABLE_EXTERNAL_APIS=1`); no `<img>` element present.
- **Severity:** R3/R4 pending confirmation (bright empty block on a dark page).
- **Reproduction:** load `/shrines/59` at 375px in this local env; a ~200px light box sits above "神社について".
- **Expected:** a map, an image, or a graceful placeholder consistent with the dark theme.
- **Actual:** empty near-white block.
- **Evidence:** screenshot; `document.querySelectorAll('img').length === 0`.
- **Suspected layer:** map/media component empty-state, or env (tiles off).
- **Release impact:** cosmetic in production if tiles/media load; needs a run with external APIs enabled to classify properly.
- **Follow-up PR candidate:** WP-E.

### Runtime Finding RF-6 — Analytics `card_view` re-fires on every scroll / re-render

- **Classification:** analytics instrumentation observation.
- **Severity:** R3/R4.
- **Reproduction:** load `/shrines/59`, scroll up/down; read `localStorage["app:track:dev-events"]` — the same 6 `card_view` payloads repeat many times.
- **Expected:** one exposure event per card per view (or an intentional, documented re-entry model).
- **Actual:** repeated identical emissions within a single page view.
- **Evidence:** dev sink buffer (96 events, mostly repeats of the same 6).
- **Suspected layer:** `ShrineDetailArticle` analytics `useEffect` dependency / viewport guard.
- **Release impact:** inflated exposure counts / CTR denominators unless deduped downstream.
- **Follow-up PR candidate:** WP-E (shared with RF-5) or standalone.

*(No fix code is included for any finding, by task rule.)*

---

## 16. Runtime Verified Items (STATIC_ONLY → RUNTIME_VERIFIED)

- Backend boot under the supported local config (`manage.py check` clean; server serves).
- Guest access to Concierge intake and `POST /api/concierge/chat/`.
- Recommendation payload contract (`recommendation_reason_v4_detail`, `rank_explanation`, `rank_comparison`, `recommendation_instance_id`, `knowledge_deities`, `knowledge_histories`, `action_suggestion_v4_preview`).
- Concierge Result reading-flow render at 375px (new renderer).
- Shrine Detail render at 375px: meaning layers, knowledge/deity/history/source, "③ 今回の相談との意味", "④ 参拝するときの視点".
- `recommendation_meta` Evidence integration (PR-N3b) — DOM present, text matches backend, `card_view` fires.
- Directions external handoff URL.
- Favorite / Visit / Reflection persistence and Journey Timeline join (API layer).
- Client-side analytics emission for `shrine_detail_view` and the six `card_view` cardIds with the Result↔Detail join key.
- JWT issuance via `api/auth/jwt/create/` and authenticated `users/me`.
- `knowledge_coverage_report` runs read-only and returns coverage figures (local scope).

---

## 17. Still Unverified

| Item | Reason |
|---|---|
| Production DB volume / knowledge coverage | No access to production DB from this environment. |
| Migrations `0100`/`0101` against a clean / prod-representative DB | Blocked locally by QA-fixture pre-state (RF-1); a clean DB was not available. |
| Free-tier Premium boundary on Shrine Detail (per-semantic teaser DOM, N3) | Local billing stub = premium/active → session rendered as premium. `BLOCKED_BY_ENVIRONMENT`. |
| LLM recommendation path | `CONCIERGE_USE_LLM` default `False`; left off per Mother Ship decision. Not a gap. |
| My Page rendered in the browser | Browser session was guest; form login through the pane was unreliable this session. API layer verified. |
| Map tiles / shrine media rendering | `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS=1` in local env. |
| Analytics backend/dashboard delivery E2E | Out of scope; dev sink only. |
| Deployment path | Out of scope for this task. |

---

## 18. Release Hardening Status

**`CRITICAL_JOURNEY_RUNTIME_VERIFIED`.**

The primary journey — Web → Backend → Database → Authentication/Guest → Concierge
Consultation → Recommendation → Concierge Result → Shrine Detail → Directions —
was exercised end-to-end against a real local backend and a representative
(non-production) database at 375px, with no release-blocker (`R1`) runtime
failure. The secondary journey (Save → Visit → Reflection → History) is
runtime-verified at the API/persistence layer.

This is a technical finding only. It is **not** a test-release go/no-go decision,
and it carries these explicit caveats:

- Verified against a **local dev DB**, not production; production data readiness
  remains `UNVERIFIED_RUNTIME_DATA`.
- The **Free-tier** Premium boundary on Shrine Detail was not observable in this
  environment (local billing stub forces premium).
- Two data-cleanup migrations are blocked on the local DB (RF-1); their behaviour
  against production data is unverified.

---

## 19. Follow-up Work Packages

> Unordered. No priority. Returned to Mother Ship.

### WP-A — Verify `0100`/`0101` data-cleanup migrations against a clean / prod-representative DB
- **Findings:** RF-1, RF-4.
- **Scope:** S–M (verification; no product code unless a real defect surfaces).
- **Affected layers/files:** `backend/temples/migrations/0100_p8a_duplicate_shrine_shadow_cleanup.py`, `0101_p8b_remove_non_shrine_artifact_id105.py`; `GET /api/populars/`.
- **Suggested AI owner:** backend agent with access to a clean/staging DB.
- **Release impact:** migrate-on-deploy could abort if production pre-state mismatches; ranking could surface artifact shrines if `105`/`104` exist in prod.

### WP-B — Remove dead `backend/config/urls.py` and correct the URLconf reference in audit #2669
- **Finding:** RF-2.
- **Scope:** S.
- **Affected layers/files:** `backend/config/` (delete), `docs/audit/mvp-remaining-work-audit.md` (correct `api/token/*` → `api/auth/jwt/*`, root URLconf `shrine_project.urls`).
- **Suggested AI owner:** backend agent.
- **Release impact:** none functional; removes a documented source of confusion.

### WP-C — Fix degenerate heuristic recommendation `reason` / result `message` text
- **Finding:** RF-3.
- **Scope:** S–M.
- **Affected layers/files:** heuristic reason/message template in the recommendation builder (non-LLM path) under `backend/temples/` (e.g. `concierge_chat_ranking` / reason-text assembly); `data.message` assembly in `temples/api_views_concierge.py` / `temples/api/views/compat.py`.
- **Suggested AI owner:** backend agent.
- **Release impact:** user-facing copy quality on any surface that shows the legacy `reason`/`message`; the verified reading-flow surfaces are unaffected.

### WP-D — Runtime-verify the Free-tier Premium boundary on Shrine Detail
- **Blocked item** (Section 17); relates to PR-N3 / N3b.
- **Scope:** S (env + verification), no product code expected.
- **Affected layers/files:** local/staging billing env (`BILLING_STUB_PLAN=free` or `NEXT_PUBLIC_FORCE_BILLING_PLAN` alignment); `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx` teaser DOM (`data-testid="shrine-detail-premium-teaser"`).
- **Suggested AI owner:** web-frontend agent with a free-plan runtime.
- **Release impact:** the paid boundary is currently unverified at runtime for the Free tier.

### WP-E — Shrine Detail media/map empty-state and analytics re-fire check (external APIs enabled)
- **Findings:** RF-5, RF-6.
- **Scope:** S–M.
- **Affected layers/files:** map/media component on `/shrines/[id]` (MapLibre container / `next/image` fallback); `ShrineDetailArticle` analytics `useEffect` (viewport/dedupe guard).
- **Suggested AI owner:** web-frontend agent with a runtime where `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS` is not set.
- **Release impact:** cosmetic empty block on mobile; possible inflated analytics exposure counts.

---

## Appendix — Commands executed (validation only)

| Command | Result |
|---|---|
| `git fetch origin` / `git log origin/develop` | #2669 confirmed at `origin/develop` HEAD `1cc02b3b` |
| `.venv/bin/python manage.py check` | no issues |
| `.venv/bin/python manage.py migrate --check` | exit 1 (4 pending) → applied `0098`/`0099`; `0100` fail-closed |
| `.venv/bin/python manage.py knowledge_coverage_report` | ran read-only; coverage 86% (local `qa_filtered_db` scope) |
| `manage.py runserver 127.0.0.1:8000 --noreload` | booted; served the journey; stopped at end of audit |
| `curl` — `/`, `/api/`, `/api/shrines/`, `/api/shrines/49/`, `/api/populars/`, `/api/users/me/`, `/api/concierge/chat/`, `/api/auth/jwt/create/`, `/api/favorites/`, `/api/shrines/59/visit/`, `/api/shrines/59/reflection/`, `/api/visits/`, `/api/reflections/`, `/api/journeys/timeline/` | statuses recorded in §3–§12 |
| `pytest -q -k "concierge_chat or jwt or token_obtain"` (backend) | **156 passed**, 1974 deselected |
| `npx tsc -p tsconfig.json --noEmit` (`apps/web`) | exit 0 |
| `npx vitest run` — `ShrineDetailArticle`, `buildShrineDetailModel` | **73 passed** (2 files) |
| Browser (viewport 375×812) | Concierge Result + Shrine Detail rendered; no page-level horizontal scroll; bottom reachable; screenshots captured |

**Local dev DB mutations made by this audit** (local `jinja_db` only): applied
migrations `0098`/`0099`; created disposable user `rt_audit_tmp` (pk 17, local
fixture — no credential recorded here); created favorite id 21, visit id 11,
reflection id 10 (all shrine 59); created concierge threads (~796–802) via guest +
fixture consultations. No production system was touched. Pre-push hooks, if they
run test suites, are reported separately by the tooling.
