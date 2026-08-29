# P8 — Identity / Coordinate Remediation Audit

## 1. Executive Summary

Fresh read-only Production inspection (2026-08-30) **revalidates every historical
P8 finding** and adds the exact relation / user-data / runtime blast radius
needed to design remediation.

| Target | Fresh classification | Evidence (this audit, all `[prod]`) |
|---|---|---|
| **id 101 → id 22** (給田六所神社) | **`SAME_REAL_SHRINE_DUPLICATE`** — 101 is the shadow | identical `name_jp`; identical `address`; coordinates **byte-identical** (Δlat 0, Δlng 0); 101 has a `place_of_worship` `place_ref`, 22 has none; 101 created 2026-06-11 07:18 (~1.5 h after 22); 101 has 0 deity / 0 history / 0 Source / 0 `goriyaku` / 0 tags; 22 carries 2 deities + 4 histories (all `source_confirmed`) + `goriyaku` prose + tag `家内安全` |
| **id 103 → id 21** (長太稲荷神社) | **`SAME_REAL_SHRINE_DUPLICATE`** — 103 is the shadow | identical `name_jp` / `address`; coordinates **byte-identical**; 103 has a `place_of_worship` `place_ref`, 21 has none; 103 created 2026-06-11 08:00 (~2.2 h after 21); 103 zero-data; 21 carries `goriyaku` prose + tags `商売繁盛` / `五穀豊穣` (0 Knowledge) |
| **id 104 → id 49** (富岡八幡宮) | **`SAME_REAL_SHRINE_DUPLICATE`** — 104 is the shadow (re-confirms merged `docs/audit/tomioka-hachimangu-identity-resolution.md` §12) | identical `name_jp`; `address` `NORMALIZED_MATCH` (both → `東京都江東区富岡1-20-3`, = 江東区 `MUNICIPAL_OFFICIAL`); 104 has a `place_of_worship` + `tourist_attraction` `place_ref` whose coordinate **equals** 104's; 104 zero-data; 49 carries 1 deity + 2 histories (`shrine_official` Source) + `goriyaku` + tags. **Coordinate caveat:** 49's stored coordinate is ~**305.6 m** from 104 / the Google Place / the shrine's real location — a position-quality defect on the primary (see §10). |
| **id 105 `広島市`** | **`CONFIRMED_NON_SHRINE_ARTIFACT`** | `kind='shrine'` (mislabel); its `place_ref` Google types are **`["locality","political"]`** (a municipality, not `place_of_worship`); `address` `日本、広島県広島市`; 0 Knowledge / 0 tags / 0 `goriyaku` / 0 user data |
| **id 49 identity** | **`IDENTITY_MATCH`** | merged `tomioka-hachimangu-identity-resolution.md` §12 + this audit's fresh re-read |
| **id 49 coordinate** | **`COORDINATE_DRIFT`** | current `35.6733, 139.7967`; trusted reference `35.6717809, 139.799519` (id 104 Google `place_of_worship` PlaceRef; 6.6 m from the published Wikipedia coordinate; matches the `MUNICIPAL_OFFICIAL` address). Δlat **+0.0015191**, Δlng **−0.0028190**, ≈ **305.6 m** (haversine). |

**Blast radius (all targets):** user-owned rows exist on **only two** shadows —
`ShrineInteractionLog`: **1 row on id 101, 1 row on id 103**, both
`action_type='detail_view'`, both `user_id = 1` (username `test`,
`is_superuser=t` — the operator account), both `metadata={"ctx":"map",…}`,
each created **~4 s after** its shadow row — i.e. artefacts of the same
map-resolve workflow that created the shadows, not genuine end-user
engagement. **id 22 / 49 / 104 / 105 have zero rows** across every
Shrine-referencing table. No favourites, visits, reflections, goshuin,
concierge threads, or action events reference any target.

**Runtime:** none of the seven rows participate in scoring (`goriyaku_tag`
GID intersection only; shadows/artifact have 0 tags). They **do** leak into
**display** surfaces — `PopularShrineListView`, `RankingAPIView`,
`NearestShrinesAPIView`, `ShrineViewSet`, `PublicShrineDetailView` all query
`Shrine.objects.all()` with **no `exclude_qa_fixture_shrines` call**, so
`広島市` and the three shadows are served as list cards / map pins / detail
pages (sorted last, `popular_score = 0`).

**Canonical denominator:** `UNIQUE_REAL_SHRINE_IDENTITIES = 103` is
**re-confirmed** (raw 108 − 1 QA fixture `id 102` − 1 non-shrine artefact
`id 105` − 3 duplicate shadows `101/103/104`). No fresh evidence contradicts
103 → **`P8_CANONICAL_DENOMINATOR_STATUS = CONFIRMED_103`**.

**This task changes nothing.** It is an audit + remediation design. Three
independent implementation packets (**P8-A** shadows, **P8-B** artefact,
**P8-C** id 49 coordinate) are designed but **not** built. All action fields
in the Mother Ship Decision Packet (§19) are `PENDING_MOTHER_SHIP`.

## 2. Scope / Baseline

| Field | Value |
|---|---|
| Task | P8 — audit + remediation **design** for known identity / coordinate targets. Audit-only. No Production write, no Spreadsheet write, no migration, no app-code change. Does not start P1. |
| Repository | `~/Developer/jinja_app` (control); isolated worktree `~/Developer/jinja_app-p8`. |
| Branch | `audit/p8-identity-coordinate-remediation` |
| Base | `origin/develop` @ `9e39bba024f2a4ca1044f05f96634a76d4fb77fe` — verified fresh (PR #2626 / #2627 / #2628 / #2629 all merged). Working tree clean; no unrelated files touched. |
| Date | 2026-08-30 |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`); every statement passed `guard.py` `is_readonly_sql`; credential value never printed / logged / in argv. **No Production write.** |
| Spreadsheet | `CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED` (no authenticated snapshot this session). Spreadsheet facts below are taken **only** from `[MS]`-verified statements already merged in `docs/audit/production-canonical-set-preflight.md`, `#2612`, `#2613`, `tomioka-hachimangu-identity-resolution.md`. **Not** a blocker — every identity was resolvable from Production + merged audits. **No Spreadsheet cell value is written or invented.** |
| Targets | Production ids **21, 22, 49, 101, 103, 104, 105** |

## 3. Production Fresh Read

### 3.1 Shrine identity

| id | kind | `name_jp` | `address` | `latitude` | `longitude` | `place_ref_id` | `created_at` | `updated_at` |
|---|---|---|---|---|---|---|---|---|
| 21 | shrine | 長太稲荷神社 | 日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | 35.660614 | 139.6017688 | **NULL** | 2026-06-11 05:49:02 | 2026-08-10 01:18:53 (= migration 0091) |
| 22 | shrine | 給田六所神社 | 日本、〒157-0064 東京都世田谷区給田１丁目３−７ | 35.662443 | 139.5920237 | **NULL** | 2026-06-11 05:49:02 | 2026-08-10 01:18:53 |
| 49 | shrine | 富岡八幡宮 | 東京都江東区富岡1-20-3 | **35.6733** | **139.7967** | **NULL** | 2026-06-11 05:49:02 | 2026-06-11 05:49:02 (never touched) |
| 101 | shrine | 給田六所神社 | 日本、〒157-0064 東京都世田谷区給田１丁目３−７ | 35.662443 | 139.5920237 | ChIJl-MEepfxGGAR1Eo44p__GaE | 2026-06-11 07:18:01 | 2026-06-11 07:18:01 |
| 103 | shrine | 長太稲荷神社 | 日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | 35.660614 | 139.6017688 | ChIJX19mq8nxGGARsA2kP4gX90M | 2026-06-11 08:00:18 | 2026-06-11 08:00:18 |
| 104 | shrine | 富岡八幡宮 | 日本、〒135-0047 東京都江東区富岡１丁目２０−３ | 35.6717809 | 139.799519 | ChIJK11I4BGJGGAR5mZswigcu58 | 2026-06-12 01:31:31 | 2026-06-12 01:31:31 |
| 105 | shrine | 広島市 | 日本、広島県広島市 | 34.3852894 | 132.4553055 | ChIJu0_z7giZWjURcvfBz1DO5Ac | 2026-06-19 16:04:10 | 2026-06-19 16:04:10 |

No `official_name` / `official_address` / `canonical_status` columns exist on
`temples_shrine` (those live only in the Spreadsheet). `name_romaji`, `element`,
`kyusei` are empty for all targets. `views_30d = favorites_30d = popular_score = 0`
for all seven.

### 3.2 `place_ref` (table `place_ref`, pk = Google `place_id`)

| `place_id` | `name` | `snapshot types` | `lat` / `lng` |
|---|---|---|---|
| ChIJl-MEepfxGGAR1Eo44p__GaE (id 101) | 給田六所神社 | `establishment, place_of_worship, point_of_interest` | 35.662443 / 139.5920237 |
| ChIJX19mq8nxGGARsA2kP4gX90M (id 103) | 長太稲荷神社 | `establishment, place_of_worship, point_of_interest` | 35.660614 / 139.6017688 |
| ChIJK11I4BGJGGAR5mZswigcu58 (id 104) | 富岡八幡宮 | `establishment, place_of_worship, point_of_interest, tourist_attraction` | 35.6717809 / 139.799519 |
| ChIJu0_z7giZWjURcvfBz1DO5Ac (id 105) | 広島市 | **`locality, political`** | 34.3852894 / 132.4553055 |

ids 21 / 22 / 49 have **no** `place_ref`.

### 3.3 Recommendation / semantic state

| id | `goriyaku` (raw) | `goriyaku_tags` | `history_theme` |
|---|---|---|---|
| 21 | `地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。` | `4 商売繁盛`, `5 五穀豊穣` | `守り` |
| 22 | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` | `7 家内安全` | `守り` |
| 49 | `勝運・商売繁盛` | `4 商売繁盛`, `11 勝運` | (empty) |
| 101 / 103 / 104 / 105 | **empty** | **none** | (empty) |

> Note: `goriyaku_tags` on ids 21 / 22 reflect state **before** migration
> `0097` (P5-DATA) and the `0096` Source backfill — both are **merged to
> `develop` but NOT applied to Production** (Production `django_migrations`
> latest `temples` = `0094`). P8 does not touch `goriyaku` or tags.

### 3.4 Knowledge state

| id | deities | deity fact-ready | histories | history fact-ready | Sources (distinct, on this shrine's Facts) |
|---|---|---|---|---|---|
| 21 | 0 | 0 | 0 | 0 | 0 |
| 22 | 2 (`大国魂大神` primary, `天照皇大神` secondary) | 2 | 4 (`founding` + 3 `historical_event`) | 4 | 2 — `六所神社 (世田谷区給田) - Wikipedia` (`secondary_editorial`), `tesshow.jp …roksho` (`local_history`), both `source_confirmed` |
| 49 | 1 (`応神天皇` primary, `high`) | 1 | 2 (`寛永4年(1627)の創建` + `明治維新…徳川将軍家の崇敬`, `high`) | 2 | 1 — `富岡八幡宮 御由緒` (`shrine_official`, `source_confirmed`) |
| 101 / 103 / 104 / 105 | 0 | 0 | 0 | 0 | 0 |

### 3.5 User / relational state — every Shrine-referencing table present in Production

| id | favorites | visits | reflections | goshuin | interaction_logs | action_events | concierge_threads (`main_shrine`) | `temples_shrine_deities` (legacy M2M) | goriyaku_tag links |
|---|---|---|---|---|---|---|---|---|---|
| 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| 49 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| **101** | 0 | 0 | 0 | 0 | **1** | 0 | 0 | 0 | 0 |
| **103** | 0 | 0 | 0 | 0 | **1** | 0 | 0 | 0 | 0 |
| 104 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 105 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Production-wide totals for context: favourites 3, visits 2, reflections 1,
goshuin 0, interaction_logs 9, action_events 0, concierge threads 45,
`temples_shrine_deities` **0** (legacy table, empty).

The two interaction-log rows:

| row | shrine_id | user_id | `action_type` | `metadata` | `created_at` | shadow `created_at` |
|---|---|---|---|---|---|---|
| il #2 | 101 | 1 (`test`, superuser) | `detail_view` | `{"ctx":"map","event":"shrine_detail_view"}` | 2026-06-11 07:18:05 | 2026-06-11 07:18:01 (**+4 s**) |
| il #4 | 103 | 1 (`test`, superuser) | `detail_view` | `{"ctx":"map",…}` | 2026-06-11 08:00:22 | 2026-06-11 08:00:18 (**+4 s**) |

#### "What would break if this row disappeared today?"

| id | Answer |
|---|---|
| 22, 49 | These are **canonical primaries** — do **not** remove. Removing would drop real Knowledge (22: 2 deities + 4 histories; 49: 1 deity + 2 histories + the only `shrine_official` Source), `goriyaku`, tags, and every Recommendation surface for the shrine. |
| 21 | Canonical primary. Removing would drop its `goriyaku` prose + 2 tags (its only content; 0 Knowledge). |
| 101 | Nothing user-facing except: the `/shrines/101` detail page 404s; one duplicate 給田六所神社 card/pin disappears from list/map/ranking; **1 operator `detail_view` interaction-log row is CASCADE-deleted** (analytics only, `user_id=1`). No favourite / visit / reflection / goshuin / thread. |
| 103 | Same as 101 (its own 1 operator interaction-log row CASCADE-deleted). |
| 104 | Nothing — 0 relations of any kind. The duplicate 富岡八幡宮 card/pin disappears. **Caveat:** 104 holds the *correct* coordinate + the `place_of_worship` `place_ref`; if 104 is deleted without first fixing id 49's coordinate (P8-C), the accurate position is lost. |
| 105 | Nothing — 0 relations. A `広島市` "shrine" card/pin/detail-page stops being served. Coverage-tool default denominator drops by 1 (see §13). |

## 4. Shrine Reference / Relation Schema

Every model that references `Shrine` (directly or transitively). `on_delete`
from `temples/models.py`; "in Prod?" from `information_schema`
(`temples_like`, `temples_rankinglog`, `temples_conciergehistory` **do not
exist** in Production — their migrations are unapplied — so they can hold no
reference to any target).

| Relation / Model | FK / M2M | field | `on_delete` | in Prod? | user-owned? | rows on any P8 target | must migrate before delete? | class |
|---|---|---|---|---|---|---|---|---|
| `ShrineDeity` | FK | `shrine` | CASCADE | yes | no (Knowledge) | 22, 49 only (primaries) | n/a (primaries kept) | `KEEP_PRIMARY` |
| `ShrineHistory` | FK | `shrine` | CASCADE | yes | no (Knowledge) | 22, 49 only | n/a | `KEEP_PRIMARY` |
| `Shrine.goriyaku_tags` | M2M | through `temples_shrine_goriyaku_tags` | — | yes | no | 21, 22, 49 only | n/a (shadows have 0) | `KEEP_PRIMARY` |
| `Shrine.place_ref` | O2O | `place_ref` (Shrine side) | SET_NULL | yes | no | 101, 103, 104, 105 | on shadow delete, `PlaceRef` row is simply orphaned (harmless; `place_ref` is a cache table) | `DROP_SHADOW_ONLY` |
| `Favorite` | FK | `shrine` (null=True; alt `place_id`) | CASCADE | yes | **yes** | **0** on all targets | n/a (no rows) — if any appeared: `MOVE` + de-dupe on `UniqueConstraint(user, shrine)` | `MOVE` (contract only) |
| `Visit` | FK | `shrine` | CASCADE | yes | **yes** | **0** | n/a — else `MOVE` | `MOVE` (contract only) |
| `ShrineReflection` | FK | `shrine` | CASCADE | yes | **yes** | **0** | n/a — else `MOVE` | `MOVE` (contract only) |
| `Goshuin` (+ `GoshuinImage` via `Goshuin`) | FK | `shrine` (null=False) | CASCADE | yes | **yes** | **0** | n/a — else `MOVE` | `MOVE` (contract only) |
| `ShrineInteractionLog` | FK | `shrine` | CASCADE | yes | **yes** (analytics) | **1 on id 101, 1 on id 103** (`user_id=1`) | **YES** — `MOVE` to primary, or Mother Ship explicitly accepts CASCADE loss | `MOVE` / `HOLD_FOR_REVIEW` |
| `ActionEvent` | FK | `shrine` (null=True) | SET_NULL | yes | **yes** (analytics) | **0** | n/a (SET_NULL anyway) | `N_A` |
| `ConciergeThread` | FK | `main_shrine` (null=True) | SET_NULL | yes | **yes** | **0** | n/a (SET_NULL; thread survives) | `N_A` |
| `temples_shrine_deities` | legacy M2M table | `shrine_id` | — | yes (table) | no | 0 (table empty, no ORM model) | no | `N_A` |
| `Like` | FK | `shrine` | CASCADE | **NO** | yes | 0 (table absent) | no | `N_A` |
| `RankingLog` | FK | `shrine` | CASCADE | **NO** | no | 0 (table absent) | no | `N_A` |
| `ConciergeHistory` | FK | `shrine` (null=True) | SET_NULL | **NO** | yes | 0 (table absent) | no | `N_A` |

**Only `ShrineInteractionLog` requires a pre-delete relation migration**, and
only for ids 101 and 103 (1 row each). Every other user-owned relation has
**0 rows** on all P8 targets today; their migration rules are specified as a
**contract** (§12) in case rows appear before P8-A ships.

## 5. Spreadsheet Reconciliation (READ-ONLY; `[MS]`-sourced)

`CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED`. The following are
`[MS]`-verified facts already merged in prior audits — **no fresh
Spreadsheet read, no cell value invented, nothing written.**

Identity-match hierarchy applied: (1) id + verified identity → (2)
`official_name` / `name_jp` → (3) `official_address` / `address` → (4)
coordinate proximity → (5) Google Place / `place_ref` → (6) human review.

| Production target | Spreadsheet relationship | Evidence |
|---|---|---|
| id 22 給田六所神社 | **`MATCH`** | Spreadsheet has a 給田六所神社 row (identity `[MS]` via #2612); name + address align; the confirmed primary of the 22/101 pair. |
| id 101 給田六所神社 | **`SHADOW_DUPLICATE`** (no distinct Spreadsheet row) | #2612 `[MS]`: the confirmed duplicate pairs are 給田六所 {22 primary, 101 shadow} / 長太稲荷 {21 primary, 103 shadow}; **no Spreadsheet-side row corresponds to a Production shadow**. Join by name+address+coord, never id. |
| id 21 長太稲荷神社 | **`MATCH`** | Spreadsheet 長太稲荷神社 row `[MS]`; confirmed primary of the 21/103 pair. |
| id 103 長太稲荷神社 | **`SHADOW_DUPLICATE`** (no distinct Spreadsheet row) | as id 101. |
| id 49 富岡八幡宮 | **`MATCH`** | **Spreadsheet row id 49 = 富岡八幡宮** `[MS]` (#2612, tomioka §12). Spreadsheet id 49 has **no** `reference_latitude` / `reference_longitude` / `coordinate_delta_m` / `coordinate_status` populated `[MS]`. |
| id 104 富岡八幡宮 | **`SHADOW_DUPLICATE`** of the *shrine*; **NOT joinable to Spreadsheet id 104** | **Spreadsheet row id 104 = a QA fixture named `重複検証神社`** `[MS]` (`production-canonical-set-preflight.md` §11, tomioka §11) — an unrelated entity. |
| id 105 広島市 | **`NO_MATCH`** (`QA_FIXTURE_ONLY` / artefact) | Spreadsheet ids 101–105 are historical QA fixture rows `[MS]`; no Spreadsheet row identifies 広島市 as a shrine. |

**`PRODUCTION_ID ↔ SPREADSHEET_ID` MUST NOT be joined by id alone** — proven
by id 104: Production id 104 = a 富岡八幡宮 shadow; Spreadsheet id 104 = the
QA fixture `重複検証神社`. Different namespaces.

## 6. Duplicate Review — 101 ↔ 22 (給田六所神社)

| Signal | id 22 (primary) | id 101 (shadow) |
|---|---|---|
| `name_jp` | 給田六所神社 | 給田六所神社 (identical) |
| `address` | 日本、〒157-0064 …給田１丁目３−７ | identical |
| coordinate | 35.662443 / 139.5920237 | **byte-identical** (Δ 0 / 0) |
| `place_ref` | none | `ChIJl-MEepfxGGAR1Eo44p__GaE` — Google `place_of_worship` named 給田六所神社 at the same address, `synced_at` −0.5 s before 101's `created_at` |
| `created_at` | 2026-06-11 05:49:02 | 2026-06-11 07:18:01 (**+1.5 h**) |
| `updated_at` == `created_at` | no (0091 touched it) | **yes** (never touched) |
| `goriyaku` / tags | prose + `家内安全` | empty / none |
| Knowledge | 2 deity + 4 history (`source_confirmed`) + 2 Sources | 0 / 0 / 0 |
| user data | 0 | **1 `ShrineInteractionLog`** (`user_id=1`, `detail_view`, `ctx=map`, +4 s) |
| Spreadsheet | `MATCH` | `SHADOW_DUPLICATE` (no distinct row) |
| prior audit | primary `[MS]` #2612 §10 | confirmed shadow `[MS]` #2612 §10 |

**Classification: `SAME_REAL_SHRINE_DUPLICATE`.** Technically preferred
canonical row: **id 22** (data-bearing, earlier, Spreadsheet `MATCH`; §13).
**Technical recommendation: `KEEP_PRIMARY_REMOVE_SHADOW`** (drop id 101 after
moving its 1 interaction-log row to id 22).

## 7. Duplicate Review — 103 ↔ 21 (長太稲荷神社)

| Signal | id 21 (primary) | id 103 (shadow) |
|---|---|---|
| `name_jp` / `address` | 長太稲荷神社 / …上祖師谷１丁目３−１０ | identical / identical |
| coordinate | 35.660614 / 139.6017688 | **byte-identical** (Δ 0 / 0) |
| `place_ref` | none | `ChIJX19mq8nxGGARsA2kP4gX90M` — Google `place_of_worship` named 長太稲荷神社, `synced_at` −0.5 s before 103's `created_at` |
| `created_at` | 2026-06-11 05:49:02 | 2026-06-11 08:00:18 (**+2.2 h**) |
| `updated_at` == `created_at` | no (0091) | **yes** |
| `goriyaku` / tags | prose + `商売繁盛` / `五穀豊穣` | empty / none |
| Knowledge | 0 / 0 / 0 | 0 / 0 / 0 |
| user data | 0 | **1 `ShrineInteractionLog`** (`user_id=1`, `detail_view`, `ctx=map`, +4 s) |
| Spreadsheet | `MATCH` | `SHADOW_DUPLICATE` |
| prior audit | primary `[MS]` #2612 §10 | confirmed shadow `[MS]` #2612 §10 |

**Classification: `SAME_REAL_SHRINE_DUPLICATE`.** Preferred canonical row:
**id 21** (data-bearing — its `goriyaku` + tags are the shrine's only
content; earlier; Spreadsheet `MATCH`). **Technical recommendation:
`KEEP_PRIMARY_REMOVE_SHADOW`** (drop id 103 after moving its 1 interaction-log
row to id 21).

## 8. Duplicate Review — 104 ↔ 49 (富岡八幡宮)

**Why id-equality is invalid here:** **Production id 104** = a 富岡八幡宮
shadow row (this audit). **Spreadsheet id 104** = a QA fixture named
`重複検証神社` `[MS]` — a different entity. **Spreadsheet id 49** = 富岡八幡宮
`[MS]`, which corresponds to **Production id 49**. There is no id join
between the namespaces.

| Row | Identity | Evidence |
|---|---|---|
| Spreadsheet row id 104 | QA fixture `重複検証神社` | `[MS]` `production-canonical-set-preflight.md` §11 |
| Production id 104 | 富岡八幡宮 shadow (`place_ref`-only, zero-data) | this audit §3; merged `tomioka-hachimangu-identity-resolution.md` §11–§12 |
| Production id 49 | 富岡八幡宮 canonical primary (data-bearing) | this audit §3–§4; tomioka §5, §12; Spreadsheet id 49 = 富岡八幡宮 `[MS]` |

| Signal | id 49 (primary) | id 104 (shadow) |
|---|---|---|
| `name_jp` | 富岡八幡宮 | 富岡八幡宮 |
| `address` normalized | `東京都江東区富岡1-20-3` | `東京都江東区富岡1-20-3` (`NORMALIZED_MATCH`; = 江東区 `MUNICIPAL_OFFICIAL`) |
| coordinate | 35.6733 / 139.7967 | 35.6717809 / 139.799519 |
| coordinate Δ (49 − 104) | — | Δlat **+0.0015191**, Δlng **−0.0028190**, **≈ 305.6 m** (haversine) |
| `place_ref` | none | `ChIJK11I4BGJGGAR5mZswigcu58` — Google `place_of_worship` + `tourist_attraction`, name 富岡八幡宮, coordinate **equals** id 104's, 6.6 m from the published Wikipedia coordinate |
| `created_at` | 2026-06-11 05:49:02 | 2026-06-12 01:31:31 (**+~19.7 h**, next day) |
| `updated_at` == `created_at` | yes (never touched) | yes |
| `goriyaku` / tags | `勝運・商売繁盛` + `商売繁盛` / `勝運` | empty / none |
| Knowledge | 1 deity + 2 history (`high`, `source_confirmed`) + `shrine_official` Source | 0 / 0 / 0 |
| user data | 0 | 0 |
| Spreadsheet | `MATCH` (row id 49) | `SHADOW_DUPLICATE` of the shrine; **not** joinable to Spreadsheet id 104 |
| prior audit | primary; merged tomioka §12 | confirmed shadow; merged tomioka §11–§12 |

**Classification: `SAME_REAL_SHRINE_DUPLICATE`** (re-confirms the merged
`tomioka-hachimangu-identity-resolution.md` §12; the two structural
differences — 104 created next-day, 104's coordinate from its own geocode —
are explained there and do not indicate a second shrine). Preferred canonical
row: **id 49** (data-bearing, earliest, Spreadsheet `MATCH`).

**Technical recommendation: `KEEP_PRIMARY_REMOVE_SHADOW` — but coordinate-coupled.**
id 104 holds the **only accurate** coordinate + the `place_of_worship`
`place_ref`. P8-A's id-104 step **must** first copy 104's coordinate (and,
optionally, `place_ref`) onto id 49 — i.e. **P8-C is a precondition of the
id-104 removal**, or the two are done in one migration. Deleting 104 alone
would strip the good position.

## 9. Artifact Review — id 105 `広島市`

| Attribute | Value |
|---|---|
| `name_jp` | 広島市 ("Hiroshima City") |
| `kind` | `shrine` (**mislabel** — it is a municipality) |
| `address` | `日本、広島県広島市` (prefecture + city only; no street) |
| coordinate | 34.3852894 / 132.4553055 (Hiroshima city centroid) |
| `place_ref` | `ChIJu0_z7giZWjURcvfBz1DO5Ac`, Google types **`["locality","political"]`** — an administrative area, **not** `place_of_worship` |
| `goriyaku` / tags / `history_theme` | empty / none / empty |
| Knowledge | 0 deity / 0 history / 0 Source |
| candidate eligibility | in `build_chat_candidates` pool for a **non-goriyaku** query (has coords + address, name not `テスト…`); scores 0 (0 tags) → never actually recommended |
| map / list / ranking / nearest | **served** — `PopularShrineListView`, `RankingAPIView`, `NearestShrinesAPIView`, `ShrineViewSet` query `Shrine.objects.all()` filtered only by `kind='shrine'`; `広島市` passes → appears as a card / map pin, sorted last (`popular_score=0`) |
| detail page | `/shrines/105` and `PublicShrineDetailView` render an empty "shrine" page for a city |
| admin | visible in the Shrine admin list |
| analytics / ranking participation | `views_30d = 0`, `popular_score = 0`, 0 `ShrineInteractionLog` / `ActionEvent` |
| user-owned relations | **0** across every table |

**Classification: `CONFIRMED_NON_SHRINE_ARTIFACT`.** A municipality row
accidentally created as a Shrine (`place_ref` type `locality/political`,
prefecture-only address, zero shrine data). **Technical recommendation:
`REMOVE_ARTIFACT`** (P8-B). No user data, no Knowledge, no runtime scoring
role; removal only stops it being served on display surfaces and aligns the
coverage-tool default denominator (§13).

## 10. id 49 富岡八幡宮 Identity / Coordinate Review

### Identity — **`IDENTITY_MATCH`**

Merged `tomioka-hachimangu-identity-resolution.md` §10–§12 established, and
this audit re-confirms: id 49's `name_jp` = 富岡八幡宮; its `address`
normalizes to `東京都江東区富岡1-20-3` = the 江東区 `MUNICIPAL_OFFICIAL`
address; Spreadsheet id 49 = 富岡八幡宮 `[MS]`; id 104's `place_of_worship`
`place_ref` independently identifies 富岡八幡宮 at that lot.

### Coordinate — **`COORDINATE_DRIFT`**

| Point | Coordinate | Source | Precision |
|---|---|---|---|
| **A** = id 49 stored | 35.6733, 139.7967 | manual seed on the pre-existing row | 4 dp (coarse) |
| **B** = id 104 stored | 35.6717809, 139.799519 | Google Place `ChIJK11I4BGJGGAR5mZswigcu58` (`place_of_worship`) geocode | 7 dp |
| **C** = id 104 `place_ref` coord | 35.6717809, 139.799519 | same Google Place record | 7 dp |
| **D** = published supplementary | 35.6717528, 139.7995833 | Wikipedia (EN) — corroboration only | — |

| Pair | Distance (haversine, WGS-84) |
|---|---|
| **A ↔ B** (id 49 vs id 104 / Google Place) | **305.6 m** |
| B ↔ C | 0.0 m |
| B ↔ D | 6.6 m (corroborates B/C) |
| A ↔ D | ~312 m |

**Deltas (A − B):** Δlat = **+0.0015191°**, Δlng = **−0.0028190°**,
≈ 305.6 m NW.

**Strongest reference: B / C** — id 104's coordinate. It (a) is a Google
`place_of_worship` geocode for 富岡八幡宮 at the confirmed municipal address,
(b) is 6.6 m from the independent published coordinate D, and (c) sits on the
real shrine grounds. id 49's coordinate A is a coarse manual seed ~306 m off
— the same defect class as `docs/audit/shrine-70-coordinate-correction.md`
(id 70 pointed ~250 m off). It is a **position-quality defect on the
primary**, not evidence of a second shrine.

**`P8_49_COORDINATE_ACTION` recommendation: UPDATE** id 49 to
`35.6717809, 139.799519` (adopt B/C). See P8-C (§16).

## 11. Runtime Blast Radius

Traced against actual code paths (`concierge_chat_candidates.build_chat_candidates`,
`shrine_qa_fixture_exclusion`, `shrine_knowledge_selector`, `evidence_gate`,
`concierge_chat` Reason builders, `temples/api/views/shrine.py`,
`behavior_funnel`, `concierge_history`, `knowledge_coverage_report`).

| Row | Recommendation candidate pool | Scoring / C1 / Need / Lead / Reason | Concierge / Compass | Shrine Detail API | Map / list / ranking / nearest | Favourites / Visits / Reflections / Goshuin | `ShrineInteractionLog` | Analytics (`behavior_funnel`) | Admin | Knowledge coverage | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **21** | yes (2 tags) | `SCORING_USED` | used | `DISPLAY_USED` | `MAP_USED` / `DISPLAY_USED` | 0 rows | 0 | — | visible | counted (0-knowledge shrine) | `SCORING_USED, DISPLAY_USED, MAP_USED` |
| **22** | yes (1 tag) | `SCORING_USED` | used | `DISPLAY_USED` (2 deities + 4 histories) | `MAP_USED` | 0 | 0 | — | visible | counted (has knowledge) | `SCORING_USED, DISPLAY_USED, MAP_USED` |
| **49** | yes (2 tags) | `SCORING_USED` | used | `DISPLAY_USED` (1 deity + 2 histories) | `MAP_USED` (**at the drifted coordinate**) | 0 | 0 | — | visible | counted (has knowledge) | `SCORING_USED, DISPLAY_USED, MAP_USED` |
| **101** | only via non-goriyaku query; scores 0 → never recommended | `NOT_USED` (0 tags → C1 NONE, `score_need`=0) | `NOT_USED` | `DISPLAY_USED` — `/shrines/101` renders (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 給田六所神社 pin/card (last) | 0 | **`USER_DATA_REFERENCED`** — 1 operator `detail_view` row; also read by `concierge_history` (per-user "already seen" check for user 1) & `behavior_funnel` counts | `ANALYTICS_USED` (1 row in funnel totals) | `ADMIN_ONLY` visible | **counted in the coverage-tool default (107)** as a 0-knowledge shrine | `DISPLAY_USED, MAP_USED, USER_DATA_REFERENCED, ANALYTICS_USED, ADMIN_ONLY` |
| **103** | as 101 | `NOT_USED` | `NOT_USED` | `DISPLAY_USED` (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 長太稲荷神社 pin/card | 0 | **`USER_DATA_REFERENCED`** — 1 operator `detail_view` row | `ANALYTICS_USED` | `ADMIN_ONLY` | counted in default 107 | `DISPLAY_USED, MAP_USED, USER_DATA_REFERENCED, ANALYTICS_USED, ADMIN_ONLY` |
| **104** | as 101 | `NOT_USED` | `NOT_USED` | `DISPLAY_USED` (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 富岡八幡宮 pin/card **at the correct coordinate** | 0 | 0 | — | `ADMIN_ONLY` | counted in default 107 | `DISPLAY_USED, MAP_USED, ADMIN_ONLY` |
| **105** | only via non-goriyaku query; scores 0 | `NOT_USED` | `NOT_USED` | `DISPLAY_USED` — `/shrines/105` renders an empty "shrine" for a city | `MAP_USED` / `DISPLAY_USED` — `広島市` pin/card | 0 | 0 | — | `ADMIN_ONLY` | counted in default 107 | `DISPLAY_USED, MAP_USED, ADMIN_ONLY` |

**Not inferred from field presence** — every "DISPLAY_USED / MAP_USED" above
was traced to a view whose queryset is `Shrine.objects.all()` **without**
`exclude_qa_fixture_shrines` (only `build_chat_candidates` and
`knowledge_coverage_report` call that helper, and it filters by *name* — the
shadows' real names and `広島市` slip through).

**Net scoring impact of the full P8 remediation: NONE.** The shadows /
artefact carry 0 `goriyaku_tags`, and scoring reads only
`goriyaku_tags`-GID intersection. Removing them changes no
candidate-eligibility, `score_need`, C1, ranking, Need-match, Lead, or Reason
output for any real shrine.

## 12. User Data / Relation Migration Matrix

For the confirmed shadows **101, 103, 104**. "Primary" = 22, 21, 49
respectively.

| Relation | Primary state | Shadow state | Action | Conflict policy | User impact |
|---|---|---|---|---|---|
| `ShrineDeity` | 22: 2 · 21: 0 · 49: 1 | all 0 | `KEEP_PRIMARY` | n/a — **do not merge Facts**; shadows have none | none |
| `ShrineHistory` | 22: 4 · 21: 0 · 49: 2 | all 0 | `KEEP_PRIMARY` | n/a | none |
| `Shrine.goriyaku_tags` | 22: 1 · 21: 2 · 49: 2 | all 0 | `KEEP_PRIMARY` | n/a | none |
| `Shrine.goriyaku` (text) | populated on 21/22/49 | empty on shadows | `KEEP_PRIMARY` | n/a | none |
| `Shrine.place_ref` (O2O) | none on 21/22/49 | set on 101/103/104 | 101/103: `DROP_SHADOW_ONLY` (orphan the `place_ref` cache row — harmless). **104: `MOVE` to id 49** (attach 104's `place_ref` to id 49) **iff** the Mother Ship wants id 49 to gain the Google Place link; else `DROP_SHADOW_ONLY` | O2O uniqueness: clear the shadow's `place_ref_id` before/at delete | none (cache only) |
| `ShrineInteractionLog` | 0 on all primaries | **1 on 101, 1 on 103**, 0 on 104 | **`MOVE`** the 2 rows to id 22 / id 21 (`UPDATE … SET shrine_id = <primary> WHERE id IN (…)`), preserving `user_id`, `action_type`, `metadata`, `created_at` | no `UniqueConstraint` on this table → no conflict; if the Mother Ship deems operator `ctx=map` rows disposable, `DROP_SHADOW_ONLY` is an accepted alternative (explicit decision) | negligible — 2 operator (`user_id=1`) `detail_view` rows; end users unaffected |
| `ActionEvent` | 0 | 0 | `N_A` (SET_NULL anyway) | — | none |
| `ConciergeThread.main_shrine` | 0 | 0 | `N_A` (SET_NULL; thread survives) | — | none |
| `Favorite` / `Visit` / `ShrineReflection` / `Goshuin` | 0 | **0** | **`MOVE` (contract)** — if any row appears before P8-A ships: `UPDATE … SET shrine_id = <primary>`; then de-duplicate against `UniqueConstraint(user, shrine)` (`Favorite`) — on collision, keep the **older** `created_at`, drop the newer duplicate; preserve `user_id` + timestamps | `Favorite`: `uniq_favorite_user_shrine`; `Goshuin`/`Visit`/`Reflection`: none | none today; contract protects future rows |
| `Like` / `RankingLog` / `ConciergeHistory` | tables absent in Prod | absent | `N_A` | — | none |
| `temples_shrine_deities` (legacy M2M) | 0 | 0 | `DROP_SHADOW_ONLY` (table-level; empty everywhere) | — | none |

**Counters.** The only counter-like fields are `Shrine.views_30d`,
`favorites_30d`, `popular_score`, `last_popular_calc_at` — **all 0 / NULL on
every target**, and `RankingLog` (per-day view/like counts) **does not exist
in Production**. So **counter policy is moot for the current data**
(`PRIMARY_ONLY` trivially — the primary's 0 is kept; nothing to sum or
merge). If the Mother Ship wants a rule recorded for future counter columns:
`PRIMARY_ONLY` for `popular_score` / `last_popular_calc_at` (recomputed by
`recalc_popular_shrines`), `SUM` for raw view/favourite tallies — **flagged
as a product-semantics decision, not chosen here.**

**Knowledge.** Not merged. Shadows have 0 Facts / 0 Sources; primaries keep
theirs untouched. No Fact-content or Source-provenance rewrite anywhere in
P8.

## 13. Canonical Denominator Impact

`P8_CANONICAL_DENOMINATOR_STATUS = CONFIRMED_103` — fresh evidence matches
the merged value; not redefined here.

| Term | CURRENT `[prod]` | PROPOSED (P8-A + P8-B applied) | Note |
|---|---|---|---|
| raw Production `Shrine` rows | **108** | **104** (−3 shadows −1 artefact) | 106/107/108 are real (Batch 17, 2026-08-23) |
| QA fixture rows (name convention) | 1 — id 102 `テスト確認神社 20260611` | 1 (unchanged — id 102 out of P8 scope) | excluded by `exclude_qa_fixture_shrines` (name) |
| non-shrine artefact rows | 1 — id 105 `広島市` | **0** | P8-B removes it |
| duplicate-shadow rows | 3 — id 101, 103, 104 | **0** | P8-A removes them |
| **canonical real-shrine identities** | **103** | **103** (unchanged) | identity count is invariant — the removed rows were never canonical |
| Recommendation candidate denominator (effective) | 103 real + leakage of 101/103/104/105 into non-goriyaku queries | 103, no leakage | shadows/artefact currently enter the pool but score 0 |
| Knowledge coverage tool — **default** `audit_target_shrines` (`scope = qa_filtered_db`) | **107** (108 − id 102 only; 101/103/104/105 **not** name-excluded) | **103** (108 − id 102 − id 105 − 3 shadows) | P8 removal makes the default denominator equal the canonical 103 **without a policy change** |
| Knowledge coverage tool — **explicit canonical scope** | 103 (already) | 103 | unchanged; P9 (`#2615`) made scope injectable |
| geographic coverage denominator | tracks the same Shrine population; 广島市 currently adds a spurious Hiroshima point | −1 spurious point; −3 duplicate points | display-map only |

**Why the canonical denominator stays 103:** the four rows P8 removes
(101, 103, 104, 105) were **already excluded** from
`UNIQUE_REAL_SHRINE_IDENTITIES` by #2612 / #2613 / tomioka. Deleting them
makes the raw table and the coverage-tool *default* converge on 103; it does
not move the canonical identity count. No fresh evidence contradicts 103, so
no `REVIEW_REQUIRED`.

## 14. P8-A Remediation Design — Duplicate Shadows (101, 103, 104)

**Design only. Not implemented.**

### Preconditions

1. Fresh state gate at implementation time: re-assert (a) each shadow still
   `name_jp` + `address` + coordinate match its primary (101/103 byte-identical;
   104 within ~306 m and `NORMALIZED_MATCH` address), (b) each shadow still
   has 0 deity / 0 history / 0 Source / 0 tag / 0 `goriyaku`, (c)
   `ShrineInteractionLog` rows on 101/103 are still exactly the 2 known
   operator rows (else `HOLD`), (d) 22 / 21 / 49 still carry their data.
2. **id 104 is coordinate-coupled to P8-C** — do not delete id 104 until
   id 49 holds an accurate coordinate (either P8-C ran first, or the same
   migration copies 104's coordinate to 49 as step 0).
3. Migration number confirmed against `develop` at implementation time — as
   of this audit the highest is `0098_remove_stray_test_source_id1` (PR
   #2628), so P8 migrations would start at **`0099`**. Note `0095`–`0098`
   are all merged to `develop` but **unapplied to Production** (ledger latest
   = `0094`) — sequencing decision for the Mother Ship, §19.

### Relation-migration order (per pair, inside one `atomic()` block)

1. (104 only) copy `latitude` / `longitude` (and optionally `place_ref_id`)
   from id 104 → id 49 **iff** id 49's coordinate is still the drifted A and
   the Mother Ship chose `UPDATE` (P8-C).
2. `ShrineInteractionLog`: `UPDATE … SET shrine_id = <primary> WHERE
   shrine_id = <shadow>` (moves the 1 row for 101/103; no-op for 104).
3. `Favorite` / `Visit` / `ShrineReflection` / `Goshuin` / `ActionEvent` /
   `ConciergeThread.main_shrine`: apply the §12 contract (today all 0 rows →
   no-ops; `Favorite` de-dupe on collision).
4. Clear the shadow's `place_ref_id` (O2O) — either re-point to the primary
   (104 → 49, if chosen) or set NULL (101/103).
5. Delete the shadow row **only if** a final guard passes: shadow still
   zero-data, no remaining `ShrineDeity` / `ShrineHistory` / `Favorite` /
   `Visit` / `ShrineReflection` / `Goshuin` / `ShrineInteractionLog` /
   `goriyaku_tags` rows, `name_jp`/`address` unchanged from the audited value.

### Canonical identity guards (never delete by pk alone)

- Primary matched by **pk + exact `name_jp` + exact `address`** (and, for 49,
  assert 1 deity + 2 histories present).
- Shadow matched by **pk + exact `name_jp` + exact `address` + `place_ref_id`
  = the audited Google `place_id` + `updated_at == created_at` + zero-data**.
- Any mismatch ⇒ that pair is a **no-op** (fail-closed, mirroring `0097`'s
  precondition guard, PR #2629).

### Reversible strategy

- Forward stores, in the migration's own `RunPython` (or a companion audit
  row / `note`), the deleted shadow's full field snapshot (`name_jp`,
  `address`, `latitude`, `longitude`, `place_ref_id`, `created_at`) and the
  moved `ShrineInteractionLog` ids.
- Reverse re-creates the shadow row (new pk — pk is not identity) with the
  snapshot values and moves the recorded `ShrineInteractionLog` rows back.
- Reverse is best-effort for pk (documented), exact for identity + relations
  — same contract as `0095` / `0096`.

### Exact deletion conditions

Delete shadow `S` (pair primary `P`) **iff all**: `S.name_jp == audited`,
`S.address == audited`, `S.place_ref_id == audited place_id`,
`S.updated_at == S.created_at`, `S` has 0 `ShrineDeity` + 0 `ShrineHistory` +
0 `goriyaku_tags` + 0 `Favorite` + 0 `Visit` + 0 `ShrineReflection` + 0
`Goshuin` + 0 `ShrineInteractionLog` (after step 2), and `P` exists with its
audited data.

### Rollback behaviour

`migrate temples <prev>` re-creates all three shadows (new pks) and restores
the 2 interaction-log rows to them. Coordinate/`place_ref` changes to id 49
(if bundled) reverse to A / NULL.

### Tests (a P8-A PR must add)

1. each shadow removed; each primary's `ShrineDeity` / `ShrineHistory` /
   `goriyaku` / `goriyaku_tags` **unchanged**.
2. the 2 `ShrineInteractionLog` rows now point at id 22 / id 21, with
   `user_id` / `action_type` / `metadata` / `created_at` preserved.
3. wrong-identity shadow (renamed, or non-zero data, or different
   `place_ref_id`) ⇒ **no-op**.
4. other shrines untouched (spot-check a real shrine + id 105).
5. `Favorite` collision path: seed a favourite on both shadow and primary
   for one user ⇒ after migrate, exactly one row, older `created_at` kept.
6. reverse re-creates 3 shadows + moves interaction logs back.
7. idempotent forward (run ×2).
8. Recommendation snapshot for 給田六所神社 / 長太稲荷神社 / 富岡八幡宮
   byte-identical before/after (0 scoring impact).
9. Knowledge-coverage default denominator: 107 → 104 (before P8-B) exactly.

### Production deployment gate

Read-only ledger check that `temples` is at the expected migration; a dry-run
plan; post-deploy verification that raw `Shrine` count dropped by exactly 3,
canonical identity count still 103, and `SELECT count(*) FROM
temples_shrineinteractionlog` unchanged (moved, not deleted).

### Delivery mechanism comparison

| Mechanism | Assessment |
|---|---|
| **reversible data migration** (`RunPython`, scoped, identity-guarded) | Matches repo convention (0090–0098 are all scoped data migrations). Version-pinned, CI-tested, atomic, reversible, ledgered, single authorized `migrate` path. Handles the `ShrineInteractionLog` move + guarded delete in one transaction. **Recommended.** |
| management command | one-off, no ledger, no automatic reverse, easy to misrun; repo commands are for repeatable ingestion, not one-shot cleanup. Rejected. |
| manual Production edit | no guard, no test, no reverse, no audit trail; contradicts `migration_safety` posture. Rejected. |

**`P8_DELIVERY` recommendation:** `SPLIT_MIGRATIONS` — P8-A (shadows) and
P8-B (artefact) as two independent reversible migrations, with P8-C
(coordinate) either its own migration ordered **before** P8-A's id-104 step
or folded into P8-A step 1. (One combined migration is acceptable but couples
three unrelated rollbacks.) **Not selected — Mother Ship decision.**

## 15. P8-B Remediation Design — Non-shrine Artefact (id 105 `広島市`)

**Design only. Not implemented.**

- **Identity guard:** act only if pk 105 **and** `name_jp == '広島市'`
  **and** `address == '日本、広島県広島市'` **and** `place_ref_id ==
  'ChIJu0_z7giZWjURcvfBz1DO5Ac'` **and** the `place_ref` snapshot `types`
  contain `locality` **and** 0 `ShrineDeity` / 0 `ShrineHistory` / 0
  `goriyaku_tags` / empty `goriyaku`. Any mismatch ⇒ no-op.
- **Reference guard:** assert 0 rows in every user-owned / analytics table
  (`Favorite`, `Visit`, `ShrineReflection`, `Goshuin`,
  `ShrineInteractionLog`, `ActionEvent`, `ConciergeThread.main_shrine`)
  before delete; if any is non-zero ⇒ `HOLD`.
- **User-data guard:** none expected; contract = if a row appears, `HOLD` for
  Mother Ship (do **not** auto-move a real user favourite onto "nothing" —
  there is no primary to move to).
- **Deletion condition:** all guards pass ⇒ delete pk 105; orphan its
  `place_ref` cache row (harmless).
- **Reverse:** re-create a `Shrine` (new pk) with the exact snapshot
  (`kind='shrine'`, `name_jp='広島市'`, `address`, `latitude`, `longitude`,
  `place_ref_id`).
- **Coverage / count effects:** raw `Shrine` 108 → 107 (with P8-A: → 104);
  coverage-tool default denominator 107 → 106 (with P8-A: → 103);
  `source_type` / knowledge metrics unchanged (105 had none); one spurious
  Hiroshima map point removed. Canonical identity count **unchanged (103)**.
- **Tests:** artefact removed; identity-mismatch no-op; reference-guard
  `HOLD` path (seed a favourite → migration refuses); reverse re-creates;
  idempotent; a real shrine and the P8-A primaries untouched; coverage
  default denominator delta exactly −1.

## 16. P8-C Remediation Design — id 49 Coordinate

**Coordinate remediation IS required** (`COORDINATE_DRIFT`, §10) — **but it
is a low-severity position-quality defect and its necessity is a Mother Ship
call**, so this is a design, not an obligation.

- **Trusted source:** id 104's Google `place_of_worship` PlaceRef
  (`ChIJK11I4BGJGGAR5mZswigcu58`) coordinate = **`35.6717809, 139.799519`**
  (= its own stored coordinate; 6.6 m from the published Wikipedia
  coordinate; on the shrine grounds at the `MUNICIPAL_OFFICIAL` address).
  No paid API call — the value already exists in Production (`place_ref`
  table + id 104 row).
- **Expected old coordinate:** `35.6733, 139.7967` (guard: refuse if id 49's
  current coordinate is not this — fail-closed).
- **Expected new coordinate:** `35.6717809, 139.799519`.
- **Distance delta:** ≈ **305.6 m** (Δlat +0.0015191, Δlng −0.0028190).
- **Identity guard:** pk 49 **and** `name_jp == '富岡八幡宮'` **and**
  `address` normalizes to `東京都江東区富岡1-20-3`. Any mismatch ⇒ no-op.
  (Same shape as migration `0094_fix_shrine_70_coordinates`.)
- **Reversible update:** forward sets the new pair; reverse restores
  `35.6733, 139.7967`; guard on both directions checks the "from" value
  matches before writing.
- **Map / recommendation regression tests:** id 49 still appears in
  `NearestShrinesAPIView` / map for a Monzen-nakacho query (now at the
  correct spot); `build_chat_candidates` distance for a nearby `lat`/`lng`
  shifts by ~306 m (assert the new distance); scoring / Reason / Knowledge
  unchanged (coordinate is not a scoring input); `PopularShrineListView`
  ordering unchanged.
- **Sequencing:** if P8-A will also copy id 104's coordinate onto id 49,
  P8-C is redundant with that step — pick one. If P8-A uses
  `DROP_SHADOW_ONLY` for id 104's `place_ref`, run P8-C **before** P8-A so the
  good coordinate is captured onto id 49 before id 104 is deleted.

**If the Mother Ship judges ~306 m acceptable for this app's map
granularity:** `P8_C_ACTION = NO_CHANGE_REQUIRED` is a valid outcome — do not
create migration work solely because the P8-C label exists.

## 17. Risks / Blockers

| # | Risk / blocker | Mitigation |
|---|---|---|
| 1 | **id 104 holds the only accurate 富岡八幡宮 coordinate + `place_of_worship` `place_ref`.** Deleting it via P8-A without P8-C first loses the good position. | P8-A step 1 copies 104 → 49, **or** P8-C runs first. Documented as a hard precondition (§14, §16). |
| 2 | `0095`–`0098` are **merged to `develop` but unapplied to Production** (ledger latest = `0094`). A new P8 migration's number (`0099`+), `dependencies`, and deploy order interact with them. | Mother Ship decides sequencing (§19). The P8 migrations must be written so forward is a no-op if the target state is already clean (fail-closed guards, per `#2629`). |
| 3 | 2 `ShrineInteractionLog` rows on 101/103 are **user-owned** (`user_id=1`). CASCADE would delete them silently. | P8-A explicitly `MOVE`s them (§12). Mother Ship may instead accept the loss (operator `ctx=map` rows) — an explicit decision, not a default. |
| 4 | Display endpoints (`Popular`, `Ranking`, `Nearest`, `ShrineViewSet`, `PublicShrineDetailView`) **do not** call `exclude_qa_fixture_shrines`. Even after P8, a *future* mis-created row would leak again. | Out of P8 scope, but recorded: consider centralising the canonical filter in a manager/queryset. **Not** a P8 change. |
| 5 | `CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED`. | All Spreadsheet facts are `[MS]`-verified & merged; every identity was resolvable without a fresh read. No blocker. |
| 6 | Local dev DB PK drift (`DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`). | All P8 migrations match by identity fields, never pk. |
| 7 | id 21 / id 22 tags shown here predate `0097` (P5-DATA). | P8 does not touch `goriyaku` / tags; the two migrations are independent. |

## 18. Technical Findings (evidence-final)

| # | Finding | Status |
|---|---|---|
| T1 | 101 ↔ 22 = `SAME_REAL_SHRINE_DUPLICATE`; 101 shadow, 22 canonical primary | **FINAL** (byte-identical coord + address + name; `place_of_worship` `place_ref`; zero-data; #2612 `[MS]`) |
| T2 | 103 ↔ 21 = `SAME_REAL_SHRINE_DUPLICATE`; 103 shadow, 21 canonical primary | **FINAL** (same basis) |
| T3 | 104 ↔ 49 = `SAME_REAL_SHRINE_DUPLICATE`; 104 shadow, 49 canonical primary | **FINAL** (re-confirms merged tomioka §12; `NORMALIZED_MATCH` address + `place_of_worship` `place_ref` + `SHADOW_PATTERN_MATCH=STRONG`) |
| T4 | id 105 `広島市` = `CONFIRMED_NON_SHRINE_ARTEFACT` | **FINAL** (`place_ref` types `locality/political`; prefecture-only address; zero data) |
| T5 | id 49 identity = `IDENTITY_MATCH` | **FINAL** |
| T6 | id 49 coordinate = `COORDINATE_DRIFT` ≈ 305.6 m from the trusted reference `35.6717809, 139.799519` | **FINAL** (measurement); remediation necessity = Mother Ship |
| T7 | User-owned rows on any P8 target = **2** `ShrineInteractionLog` (id 101, id 103; `user_id=1`, operator `ctx=map`). Everything else = 0. | **FINAL** |
| T8 | Removing 101/103/104/105 has **zero** Recommendation scoring impact and **zero** Knowledge-content impact | **FINAL** (traced code paths §11) |
| T9 | `UNIQUE_REAL_SHRINE_IDENTITIES = 103`; coverage-tool **default** denominator is currently **107** and would become **103** after P8-A + P8-B **without a policy change** | **FINAL** |
| T10 | `temples_like` / `temples_rankinglog` / `temples_conciergehistory` do not exist in Production; `temples_shrine_deities` is an empty legacy table | **FINAL** |
| T11 | Only `build_chat_candidates` and `knowledge_coverage_report` apply `exclude_qa_fixture_shrines`; all Shrine display APIs do not | **FINAL** |

## 19. Mother Ship Decision Packet

Technical findings (§18) are evidence-final. **Product / governance actions
below are `PENDING_MOTHER_SHIP` — not inferred here.**

```text
P8_101_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (KEEP_PRIMARY_REMOVE_SHADOW → 22)
P8_103_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (→ 21)
P8_104_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (→ 49), coordinate-coupled to P8_49_COORDINATE_ACTION
P8_105_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_ARTIFACT
P8_49_COORDINATE_ACTION  = PENDING_MOTHER_SHIP   # audit recommends UPDATE → 35.6717809, 139.799519 (Δ ≈ 305.6 m); NO_CHANGE_REQUIRED is valid if ~306 m is within map tolerance
P8_DELIVERY              = PENDING_MOTHER_SHIP   # audit recommends SPLIT_MIGRATIONS (P8-A shadows / P8-B artefact / P8-C coordinate as independent reversible RunPython migrations)
P8_USER_DATA_POLICY      = PENDING_MOTHER_SHIP   # audit recommends MOVE_TO_PRIMARY (the 2 ShrineInteractionLog rows → 22 / 21). NO_USER_DATA is factually true for 104/105 but NOT for 101/103.
P8_COUNTER_POLICY        = PENDING_MOTHER_SHIP   # moot for current data (all counters 0 / RankingLog table absent); audit recommends PRIMARY_ONLY, with SUM reserved for any future raw tally column
```

Additional pending items:

1. **Sequencing** of the P8 migrations relative to the unapplied `0095`–`0098`
   (P8 starts at `0099`; `dependencies` + deploy order).
2. Whether id 104's `place_ref` (Google Place link) should be **moved to
   id 49** on removal (gives id 49 a `place_of_worship` provider record) or
   dropped.
3. Whether P8-C is executed at all (`UPDATE` vs `NO_CHANGE_REQUIRED`).
4. Whether the 2 operator `ShrineInteractionLog` rows are moved or accepted
   as CASCADE loss.

## 20. STOP

- Every P8 target freshly inspected `[prod]`; every historical finding
  revalidated (all confirmed).
- All `Shrine` relations enumerated (§4); user-data blast radius known
  (§3.5, §12) — **2 rows**, both `ShrineInteractionLog`, both operator.
- id 49 identity + coordinate reconciled (§10); denominator effect known
  (§13) — canonical stays **103**.
- P8-A / P8-B / P8-C designed (§14–§16); Mother Ship Decision Packet prepared
  (§19), all action fields `PENDING_MOTHER_SHIP`.
- **No Production write. No Spreadsheet write. No migration created. No seed
  changed. No application code changed. No `Shrine` row deleted or merged.**
- This branch adds exactly one file:
  `docs/audit/p8-identity-coordinate-remediation.md`.
- Does **not** start P1. Does **not** implement P8-A / P8-B / P8-C.

Next step: Mother Ship decisions on §19, then independent P8-A / P8-B / P8-C
implementation PRs.
