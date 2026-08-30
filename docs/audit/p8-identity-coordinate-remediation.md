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

**Runtime — scoring:** the **canonical primaries** carry Recommendation
scoring evidence — id 21 = `SCORING_USED` (`goriyaku_tags` 4, 5), id 22 =
`SCORING_USED` (tag 7), id 49 = `SCORING_USED` (tags 4, 11). The **P8 removal
targets** carry none — id 101 / 103 / 104 / 105 = `SCORING_NOT_USED` (0
`goriyaku_tags`; scoring is `goriyaku_tag`-GID intersection only). Therefore
**removing the three shadows + the non-shrine artefact has
`RECOMMENDATION_IMPACT = NONE`** — the removal targets hold no scoring
evidence, and the primaries (21/22/49) are untouched.

**Runtime — display:** the removal targets **do** leak into **display**
surfaces — `PopularShrineListView`, `RankingAPIView`, `NearestShrinesAPIView`,
`ShrineViewSet`, `PublicShrineDetailView` all query `Shrine.objects.all()`
with **no `exclude_qa_fixture_shrines` call**, so `広島市` and the three
shadows are served as list cards / map pins / detail pages (sorted last,
`popular_score = 0`).

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
`place_ref`. Deleting id 104 alone would strip the good position, so id 49's
coordinate must be corrected **before or atomically with** the id-104
removal — via §16 **Design A** (a standalone P8-C applied first, after which
P8-A only **reads** id 49's coordinate for PRE validation and never mutates
it) **or** **Design B** (the coordinate update is P8-A's atomic step 1). The
two designs are **mutually exclusive**;
`NO_CHANGE_REQUIRED` (accept ~306 m) is also valid and leaves id 49's
coordinate as-is.

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
| **101** | only via non-goriyaku query; scores 0 → never recommended | **`SCORING_NOT_USED`** (0 tags → C1 NONE, `score_need`=0) | `NOT_USED` | `DISPLAY_USED` — `/shrines/101` renders (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 給田六所神社 pin/card (last) | 0 | **`USER_DATA_REFERENCED`** — 1 operator `detail_view` row; also read by `concierge_history` (per-user "already seen" check for user 1) & `behavior_funnel` counts | `ANALYTICS_USED` (1 row in funnel totals) | `ADMIN_ONLY` visible | **counted in the coverage-tool default (107)** as a 0-knowledge shrine | `SCORING_NOT_USED, DISPLAY_USED, MAP_USED, USER_DATA_REFERENCED, ANALYTICS_USED, ADMIN_ONLY` |
| **103** | as 101 | **`SCORING_NOT_USED`** | `NOT_USED` | `DISPLAY_USED` (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 長太稲荷神社 pin/card | 0 | **`USER_DATA_REFERENCED`** — 1 operator `detail_view` row | `ANALYTICS_USED` | `ADMIN_ONLY` | counted in default 107 | `SCORING_NOT_USED, DISPLAY_USED, MAP_USED, USER_DATA_REFERENCED, ANALYTICS_USED, ADMIN_ONLY` |
| **104** | as 101 | **`SCORING_NOT_USED`** | `NOT_USED` | `DISPLAY_USED` (empty) | `MAP_USED` / `DISPLAY_USED` — duplicate 富岡八幡宮 pin/card **at the correct coordinate** | 0 | 0 | — | `ADMIN_ONLY` | counted in default 107 | `SCORING_NOT_USED, DISPLAY_USED, MAP_USED, ADMIN_ONLY` |
| **105** | only via non-goriyaku query; scores 0 | **`SCORING_NOT_USED`** | `NOT_USED` | `DISPLAY_USED` — `/shrines/105` renders an empty "shrine" for a city | `MAP_USED` / `DISPLAY_USED` — `広島市` pin/card | 0 | 0 | — | `ADMIN_ONLY` | counted in default 107 | `SCORING_NOT_USED, DISPLAY_USED, MAP_USED, ADMIN_ONLY` |

**Not inferred from field presence** — every "DISPLAY_USED / MAP_USED" above
was traced to a view whose queryset is `Shrine.objects.all()` **without**
`exclude_qa_fixture_shrines` (only `build_chat_candidates` and
`knowledge_coverage_report` call that helper, and it filters by *name* — the
shadows' real names and `広島市` slip through).

**`RECOMMENDATION_IMPACT = NONE` for the P8 removal (shadows 101/103/104 +
artefact 105).** Those four rows are `SCORING_NOT_USED` — they carry 0
`goriyaku_tags`, and scoring reads only `goriyaku_tags`-GID intersection.
Removing them changes no candidate-eligibility, `score_need`, C1, ranking,
Need-match, Lead, or Reason output for any real shrine. The canonical
primaries **21 / 22 / 49 are `SCORING_USED`** (they carry the shrine's tags)
and are **not** touched by P8-A / P8-B.

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

### `P8_A_PRESTATE_POLICY = FAIL_CLOSED`

P8-A is a scoped remediation of a **specific audited Production state**. For
every Mother-Ship-approved pair, the migration must verify that the pair
matches its **exact approved PRE state** before any mutation. **Unexpected
state aborts the migration (`RAISE`) before any write** — it is **not**
treated as a "safe successful no-op", it is **not** described as
"idempotent after deletion", and forward must **not** be recordable as
applied when a mismatch is seen. Do not repair or guess.

The single exception is the **applicability boundary** (below): a fresh /
empty migration lineage where the audited Production subject *cannot* exist
(no row at the pk, no row with the audited identity anywhere) may be a
**narrowly documented clean no-op**. Absence produced *by a prior successful
P8-A run* is **not** the same state and must not reuse that no-op path.

### Preconditions (exact PRE dimensions — all must match, else `RAISE` / `ABORT`)

For each approved shadow pair:

1. **primary identity matches** — pk + exact `name_jp` + exact `address`
   (+ for id 49: 1 deity + 2 histories present).
2. **shadow identity matches** — pk + exact `name_jp` + exact `address`.
3. **expected `place_ref` matches** — shadow `place_ref_id` == the audited
   Google `place_id` (101 `ChIJl-MEepfxGGAR1Eo44p__GaE`, 103
   `ChIJX19mq8nxGGARsA2kP4gX90M`, 104 `ChIJK11I4BGJGGAR5mZswigcu58`).
4. **expected zero-data state matches** — shadow has 0 `ShrineDeity` / 0
   `ShrineHistory` / 0 Source / 0 `goriyaku_tags` / empty `goriyaku` /
   `updated_at == created_at`.
5. **expected relation counts match** — shadow: 0 `Favorite` / 0 `Visit` /
   0 `ShrineReflection` / 0 `Goshuin` / 0 `ActionEvent` / 0
   `ConciergeThread.main_shrine`.
6. **expected `ShrineInteractionLog` state matches** — **exactly 1** row on
   id 101 and **exactly 1** on id 103 (`action_type='detail_view'`,
   `user_id=1`), **0** on id 104. A count / attribute mismatch → `ABORT`.
7. **expected user-owned reference state matches** — no user-owned row
   (favourite / visit / reflection / goshuin) on any shadow. Any such row →
   `ABORT` (do not auto-move it without an explicit Mother Ship decision).
8. **coordinate-coupling requirement for id 104 matches** — id 104's
   coordinate == its audited value `35.6717809, 139.799519`, **and** id 49's
   coordinate matches what the chosen delivery design (§16) expects:
   - **Design A** (independent P8-C ran first): P8-A **reads** id 49's
     coordinate here and requires `35.6717809, 139.799519`; if it is still
     `35.6733, 139.7967` → `ABORT` (run P8-C first). P8-A performs **no**
     coordinate write in forward or reverse.
   - **Design B** (folded): id 49 == the audited drifted value `35.6733,
     139.7967`; P8-A step 1 updates it, fail-closed on that exact value.
   - **`NO_CHANGE_REQUIRED`**: id 49 == `35.6733, 139.7967`; P8-A reads and
     leaves it (no write).
   Any id 49 coordinate not matching the design's expected value → `ABORT`.

If an approved subject exists but **any** field/relation above differs:
`RAISE` / `ABORT`. Do not repair, do not guess, do not proceed with the
other pairs from a partially-mutated transaction (the whole `atomic()`
block rolls back).

### Applicability boundary (the only clean no-op)

If, at apply time, **no row exists at the approved pk and no row with the
approved shadow identity (`name_jp` + `address` + `place_ref_id`) exists
anywhere**, and the migration lineage shows P8-A has **never** been applied
in this environment (fresh DB / test DB seeded without the shadows), the pair
is a **documented clean no-op** — recorded explicitly as
`APPLICABILITY_BOUNDARY_FRESH_LINEAGE`, distinct from a mismatch. This path
exists so the migration runs on a fresh local/CI DB that never had the
Production shadows; it is **not** reachable after a real P8-A run deleted the
rows (that history makes reverse — not a re-forward — the correct operation).

### Migration number / sequencing

Confirmed against `develop` at implementation time — as of this audit the
highest is `0098_remove_stray_test_source_id1` (PR #2628), so P8 migrations
would start at **`0099`**. `0095`–`0098` are merged to `develop` but
**unapplied to Production** (ledger latest = `0094`) — sequencing decision
for the Mother Ship, §19.

### Relation-migration order (per pair, inside one `atomic()` block)

1. (104 only) copy `latitude` / `longitude` (and optionally `place_ref_id`)
   from id 104 → id 49 **iff** id 49's coordinate is still the drifted A and
   the Mother Ship chose `UPDATE` (P8-C).
2. `ShrineInteractionLog`: `UPDATE … SET shrine_id = <primary> WHERE
   shrine_id = <shadow>` — after Precondition 6 confirmed exactly 1 row on
   id 101 and 1 on id 103 (0 on id 104, so this UPDATE legitimately affects
   0 rows for that pair — an audited zero, not a mismatch).
3. `Favorite` / `Visit` / `ShrineReflection` / `Goshuin` / `ActionEvent` /
   `ConciergeThread.main_shrine`: Preconditions 5 & 7 already confirmed these
   are 0 on every shadow — so this step legitimately does nothing. (The §12
   `MOVE` + `Favorite` de-dupe contract is retained for the case a future
   Mother-Ship-approved PRE state *includes* such rows.)
4. Clear the shadow's `place_ref_id` (O2O) — either re-point to the primary
   (104 → 49, if chosen) or set NULL (101/103).
5. Delete the shadow row **only if** a final guard passes: shadow still
   zero-data, no remaining `ShrineDeity` / `ShrineHistory` / `Favorite` /
   `Visit` / `ShrineReflection` / `Goshuin` / `ShrineInteractionLog` /
   `goriyaku_tags` rows, `name_jp`/`address` unchanged from the audited value.

### Canonical identity guards (never act by pk alone)

- Guards are the PRE dimensions above. On a mismatch the migration **raises**
  (aborts the `atomic()` block) — it does **not** silently no-op a
  mismatched-but-present subject. This is stricter than, and the same
  contract class as, the P6 / `0098` and `0097` (PR #2629) fail-closed
  precondition corrections.

### Reverse-state strategy — deterministic static audited data (no ephemeral forward state)

A `RunPython` forward function's local variables **do not survive** until
reverse. Reverse must reconstruct the PRE state from data that is actually
available:

- **Strategy A (preferred, sufficient here): static audited snapshot baked
  into the migration module.** The shadow rows' full field values are known
  and fixed from this audit — bake a constant per pair:
  `{pk_hint, name_jp, address, latitude, longitude, place_ref_id,
  created_at, kind='shrine'}` for 101 / 103 / 104, plus the corrected id 49
  coordinate. Reverse re-creates each shadow from its constant (a **new pk** —
  pk is not identity; document this) and re-establishes its `place_ref`.
- **The 2 `ShrineInteractionLog` rows are identified by stable audited
  semantics, not by forward-run memory:** `shrine_id ∈ {21, 22}` (post-move)
  **AND** `user_id = 1` **AND** `action_type = 'detail_view'` **AND**
  `metadata->>'ctx' = 'map'` **AND** `created_at` == the audited value
  (`2026-06-11 07:18:05` for the id-101 row, `2026-06-11 08:00:22` for the
  id-103 row). Reverse moves exactly those back to the re-created shadows.
  Forward's `MOVE` is `UPDATE … SET shrine_id = <primary> WHERE` that same
  audited predicate (before the move it selects on the shadow's `shrine_id`).
- **Strategy B (only if A is judged insufficient): an explicitly persisted
  migration-owned marker** — e.g. a `note`/audit row the migration writes and
  reverse reads. Do **not** rely on anything that is not persisted.
- Reverse is exact for identity + relations; pk is best-effort (new pk) and
  documented — same contract as `0095` / `0096`.

### Reverse precondition

Reverse may assume the **exact approved PRE contract held** only because
forward `RAISE`s on any mismatch (it is never recorded as applied otherwise).
Reverse restores **only** the state this migration owns (the 3 shadow rows it
deleted, the 2 interaction-log rows it moved, and — if bundled — id 49's
coordinate). It must **not** re-create a shadow when a row with that shadow
identity already exists (guard reverse too), and it must **not** run on a
lineage that only ever hit the `APPLICABILITY_BOUNDARY_FRESH_LINEAGE` no-op.

### Exact deletion conditions (unchanged intent, restated under FAIL_CLOSED)

Delete shadow `S` (pair primary `P`) only after **all** PRE dimensions
(§Preconditions 1–8) have passed for that pair and steps 1–4 completed in the
same transaction. Any deviation detected at any step → `RAISE` → whole
`atomic()` block rolls back, nothing deleted.

### Rollback behaviour

After a **successfully recorded** P8-A, `migrate temples <prev>` re-creates
all three shadows from the static audited snapshots (new pks) and moves the 2
audited interaction-log rows back. Coordinate / `place_ref` changes to id 49
(if bundled) reverse to A / NULL. Reverse is a **no-op** for a pair whose
shadow identity already exists, and for a lineage that only ever hit the
fresh-lineage applicability boundary.

### Tests (a P8-A PR must add) — under `FAIL_CLOSED`

Valid path:

1. **valid forward** — each shadow removed; each primary's `ShrineDeity` /
   `ShrineHistory` / `goriyaku` / `goriyaku_tags` **unchanged**; the 2
   `ShrineInteractionLog` rows now point at id 22 / id 21 with `user_id` /
   `action_type` / `metadata` / `created_at` preserved.
2. **valid forward → reverse restores the exact audited PRE state** — 3
   shadow rows back (audited `name_jp` / `address` / coordinate /
   `place_ref_id`; new pks allowed), 2 interaction-log rows back on the
   shadows, id 49 coordinate back to A (if bundled).
3. **valid forward → reverse → forward is deterministic** (same end state as
   after test 1).
4. `Favorite` collision path: seed a favourite on both shadow and primary
   for one user ⇒ after migrate, exactly one row, older `created_at` kept.
5. other shrines untouched (spot-check a real shrine + id 105).
6. Recommendation snapshot for 給田六所神社 / 長太稲荷神社 / 富岡八幡宮
   byte-identical before/after (`SCORING_NOT_USED` targets removed;
   `SCORING_USED` primaries untouched).
7. Knowledge-coverage default denominator: 107 → 104 (before P8-B) exactly.

Abort path (each must `raise` and leave the DB **byte-unchanged**):

1. **wrong primary identity** (primary renamed / address changed / id 49
   missing its deity+histories) → raises / aborts.
2. **wrong shadow identity** (shadow renamed / address changed / different
   `place_ref_id`) → raises / aborts.
3. **unexpected shadow data** (shadow has a `ShrineDeity` / `ShrineHistory`
   / `goriyaku_tags` / non-empty `goriyaku` / `updated_at != created_at`) →
   raises / aborts.
4. **`ShrineInteractionLog` count / attribute mismatch** (0 or 2 rows on a
   shadow, or a row with a different `user_id` / `action_type` / `ctx`) →
   raises / aborts.
5. **unexpected user-owned reference** (a favourite / visit / reflection /
   goshuin on a shadow) → raises / aborts.
6. **id 104 coordinate-coupling not satisfied** (id 49 coordinate is neither
   A nor B) → raises / aborts.
7. **failed forward leaves the DB unchanged** — after any abort test, every
   row count and every target row is identical to before the migration ran
   (the whole `atomic()` block rolled back).

Applicability boundary:

1. **fresh / empty lineage** — on a DB where no row exists at the approved
   pks and no row with the approved shadow identity exists anywhere, and
   P8-A has never been recorded applied, forward is a documented clean
   no-op (`APPLICABILITY_BOUNDARY_FRESH_LINEAGE`); reverse on that lineage
   is also a no-op (does **not** create shadows).
2. **absence-after-cleanup is NOT the boundary** — after a valid forward
   deleted the shadows, re-running forward is **not** a "successful no-op":
   it either detects the recorded-applied state and is inert, or (if
   re-invoked) raises rather than silently re-passing; the correct operation
   on that lineage is reverse.

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
P8-B (artefact) as two independent reversible migrations. The coordinate
change is handled by **exactly one** of §16's mutually exclusive designs:
**Design A** (a standalone P8-C migration, applied before P8-A; P8-C is the
only migration that mutates id 49's coordinate, and P8-A only reads it for
fail-closed PRE validation — never writes it, in forward or reverse) **or**
**Design B** (no standalone P8-C; the coordinate update is P8-A's atomic
step 1). **Both mechanisms must never coexist in one migration lineage.**
**Not selected — Mother Ship decision.**

## 15. P8-B Remediation Design — Non-shrine Artefact (id 105 `広島市`)

**Design only. Not implemented.**

### `P8_B_PRESTATE_POLICY = FAIL_CLOSED`

Same principle as P8-A. When the audited subject **exists**, the migration
requires its **exact approved PRE state** and **raises / aborts** on any
mismatch — a present-but-different id 105 is **not** a "safe successful
no-op". Forward is not recordable as applied on a mismatch. The only clean
no-op is the **applicability boundary**: a fresh / empty lineage where no row
exists at pk 105 and no row with the audited artefact identity
(`name_jp='広島市'` + `address` + `place_ref_id`) exists anywhere, and P8-B
has never been recorded applied. Absence produced by a prior successful P8-B
run is **not** that state (reverse is the correct operation there).

### Exact PRE dimensions (all must match, else `RAISE` / `ABORT`)

- pk 105 **and** `name_jp == '広島市'` **and** `address == '日本、広島県広島市'`
  **and** `place_ref_id == 'ChIJu0_z7giZWjURcvfBz1DO5Ac'` **and** the
  `place_ref` snapshot `types` contain `locality` (and not
  `place_of_worship`).
- 0 `ShrineDeity` / 0 `ShrineHistory` / 0 Source / 0 `goriyaku_tags` / empty
  `goriyaku`.
- **0 rows** in every user-owned / analytics table (`Favorite`, `Visit`,
  `ShrineReflection`, `Goshuin`, `ShrineInteractionLog`, `ActionEvent`,
  `ConciergeThread.main_shrine`). Any non-zero → `ABORT` (do **not** auto-move
  a real user row — there is no primary to move it to; escalate to the
  Mother Ship).

### Deletion + reverse

- All PRE dimensions pass ⇒ delete pk 105 inside `atomic()`; orphan its
  `place_ref` cache row (harmless). Any deviation → `RAISE` → rollback,
  nothing deleted.
- **Reverse-state strategy:** a static audited snapshot baked into the
  migration module (`kind='shrine'`, `name_jp='広島市'`, `address`,
  `latitude 34.3852894`, `longitude 132.4553055`,
  `place_ref_id='ChIJu0_z7giZWjURcvfBz1DO5Ac'`) — no ephemeral forward state.
- **Reverse precondition:** runs only after a forward whose exact PRE
  contract passed and was recorded applied. Reverse is a **no-op** if a row
  with the artefact identity already exists, and on a lineage that only hit
  the fresh-lineage boundary.

### Coverage / count effects

Raw `Shrine` 108 → 107 (with P8-A: → 104); coverage-tool default denominator
107 → 106 (with P8-A: → 103); `source_type` / knowledge metrics unchanged
(105 had none); one spurious Hiroshima map point removed. Canonical identity
count **unchanged (103)**.

### Tests — under `FAIL_CLOSED`

Valid: valid forward removes the artefact; valid forward → reverse restores
the exact audited snapshot; forward → reverse → forward deterministic; a
real shrine and the P8-A primaries untouched; coverage default denominator
delta exactly −1.
Abort (each must `raise`, DB byte-unchanged): wrong id-105 identity
(`name_jp` / `address` / `place_ref_id` differ); `place_ref` type is
`place_of_worship` not `locality`; any `ShrineDeity` / `ShrineHistory` /
`goriyaku_tags` present; **any user-owned / analytics row present** (seed a
favourite → migration raises, does **not** silently `HOLD`-skip); failed
forward leaves the DB unchanged.
Applicability boundary: fresh / empty lineage (no pk 105, no artefact
identity anywhere, never recorded applied) → documented clean no-op;
absence-after-cleanup is **not** that path.

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
- **Expected old coordinate:** `35.6733, 139.7967`.
- **Expected new coordinate:** `35.6717809, 139.799519`.
- **Distance delta:** ≈ **305.6 m** (Δlat +0.0015191, Δlng −0.0028190).
- **`P8_C_PRESTATE_POLICY = FAIL_CLOSED` (no "already-corrected" no-op).**
  For an intended database where Shrine id 49 **exists**, forward may run
  **only if all**: pk == 49 **and** `name_jp == '富岡八幡宮'` **and**
  `address` normalizes to `東京都江東区富岡1-20-3` **and** the current
  coordinate is **exactly** the audited old value `35.6733, 139.7967`. If
  id 49 already holds `35.6717809, 139.799519` (or any third value), forward
  **`RAISE`s / `ABORT`s** — it is **not** treated as a successful no-op and
  is **not** recorded as applied. (Reason: a recorded-applied forward must
  imply id 49 held the exact old coordinate, so that reverse can restore it
  from the exact new coordinate without creating drift that never existed.)
  This mirrors `0094_fix_shrine_70_coordinates` and the P6 / `0097` (PR
  #2629) / `0098` fail-closed corrections.
- **Applicability boundary — `PENDING_IMPLEMENTATION_REVIEW`.** Coordinate
  state is a single scalar pair; reverse **cannot** distinguish
  "old→new by this migration" from "already-new, untouched" purely from the
  observable value. Therefore:
  - The **only** candidate clean no-op is **subject genuinely absent** (no
    row at pk 49 and no row whose identity matches 富岡八幡宮 anywhere) on a
    fresh migration lineage that never recorded P8-C applied — and even that
    is offered **only if** a fresh-schema / test DB needs it. "id 49 exists
    with the corrected coordinate" is **explicitly not** a boundary.
  - If subject-absent reverse still cannot be made symmetric from observable
    DB state, P8-C **must** use a persisted migration-owned marker (Strategy
    B of §14) or **omit the clean-no-op path entirely** and rely on Django's
    migration ledger (a recorded-applied P8-C is the only state from which
    reverse runs). Prefer the ledger-only contract.
- **Reverse contract.** A successfully applied forward implies id 49 held the
  exact audited old coordinate. Reverse restores `35.6733, 139.7967` **only
  from the exact new coordinate `35.6717809, 139.799519`**. If reverse sees
  any other value it **`RAISE`s / `ABORT`s** (or uses the repository's
  documented reverse fail-closed behaviour) — it does **not** silently
  overwrite an unexpected value.
- **Map / recommendation regression tests:** id 49 still appears in
  `NearestShrinesAPIView` / map for a Monzen-nakacho query (now at the
  correct spot); `build_chat_candidates` distance for a nearby `lat`/`lng`
  shifts by ~306 m (assert the new distance); scoring / Reason / Knowledge
  unchanged (coordinate is not a scoring input); `PopularShrineListView`
  ordering unchanged.

### Two mutually exclusive delivery designs (never both in one lineage)

Exactly one of the following is chosen. **A single migration lineage must
never contain both an independent P8-C migration and a P8-A that also mutates
id 49's coordinate.**

#### Design A — independent P8-C migration

Coordinate responsibility split:

- **P8-C is the ONLY migration that MUTATES `Shrine.latitude` / `longitude`
  for id 49** (`35.6733, 139.7967` → `35.6717809, 139.799519`), fail-closed
  on the exact old value per above.
- **P8-A MAY and MUST READ id 49's `latitude` / `longitude` — but ONLY for
  fail-closed PRE validation** (its Precondition 8). P8-A **MUST NOT**
  `UPDATE`, copy, restore, or otherwise mutate id 49's coordinate in forward
  **or** reverse.

Steps:

1. P8-C updates id 49's coordinate, fail-closed on the exact old value.
2. P8-A runs **later**.
3. P8-A **reads** id 49's coordinate for its Precondition 8 check and
   performs **zero** coordinate writes.
4. P8-A handles **only** the shadow relations / `place_ref` cleanup /
   deletion per the Mother Ship decision (for id 104, `place_ref` is
   `DROP_SHADOW_ONLY` or moved to id 49 — but the *coordinate* is already
   correct from P8-C).
5. P8-A's Precondition 8 (§14) requires the **exact corrected value**
   `35.6717809, 139.799519` **before** shadow id 104 deletion (P8-C already
   applied). If id 49 is still at the old / drifted coordinate → P8-A
   `RAISE`s / `ABORT`s (P8-C was skipped — run it first).
6. **P8-A reverse MUST NOT change id 49's coordinates** in Design A — reverse
   re-creates the shadow rows / moves the interaction-log rows only; the
   corrected coordinate stays as P8-C left it (P8-C's own reverse is the only
   thing that restores the old coordinate).

#### Design B — coordinate folded into P8-A

1. **No independent P8-C migration exists.**
2. P8-A validates id 49's exact old coordinate `35.6733, 139.7967` **and**
   id 104's trusted coordinate `35.6717809, 139.799519`.
3. P8-A updates id 49 to the trusted coordinate as part of the same
   `atomic()` remediation (its step 1).
4. P8-A then deletes id 104 after every guard (§14 Preconditions 1–8) passes.
5. Reverse restores **both** — id 104 (from its static audited snapshot) and
   id 49's old coordinate `35.6733, 139.7967` (from the exact new value,
   fail-closed).

**If the Mother Ship judges ~306 m acceptable for this app's map
granularity:** `P8_C_ACTION = NO_CHANGE_REQUIRED` — no coordinate migration
in either design; P8-A then treats id 104's `place_ref` per the Mother Ship
decision and leaves id 49's coordinate as the audited drifted value (its
Precondition 8 checks for `35.6733, 139.7967`).

### Tests (a P8-C PR — or the folded P8-A coordinate step — must add)

1. **exact old PRE → forward updates to new** — id 49 at `35.6733, 139.7967`
   ⇒ after forward, `35.6717809, 139.799519`.
2. **already-corrected PRE → forward raises** — id 49 at `35.6717809,
   139.799519` ⇒ forward `raise`s; DB unchanged.
3. **wrong identity → forward raises** — pk 49 renamed / address changed ⇒
   `raise`; DB unchanged.
4. **unexpected third coordinate → forward raises** — id 49 at any value
   other than the exact old pair ⇒ `raise`; DB unchanged.
5. **failed forward leaves the DB unchanged** — after tests 2–4, id 49's row
   is byte-identical to before.
6. **valid forward → reverse restores the exact old coordinate** —
   `35.6717809, 139.799519` → `35.6733, 139.7967`.
7. **valid forward → reverse → forward is deterministic** (ends at the new
   coordinate).
8. **reverse from an unexpected coordinate does not overwrite it** — seed
   id 49 with a third value, run reverse ⇒ `raise` / documented reverse
   fail-closed; the third value is **not** overwritten.
9. **independent-P8-C + P8-A sequencing does not apply the coordinate update
   twice** — after Design A's P8-C, P8-A **reads** id 49's coordinate for
   PRE validation but performs **zero** coordinate writes; both P8-A forward
   and P8-A reverse leave id 49 at the corrected `35.6717809, 139.799519`.
10. **folded (Design B) has no independent P8-C migration** — the migration
    lineage contains no standalone P8-C; the coordinate change is P8-A's
    step 1 and its reverse restores the old coordinate together with id 104.

## 17. Risks / Blockers

| # | Risk / blocker | Mitigation |
|---|---|---|
| 1 | **id 104 holds the only accurate 富岡八幡宮 coordinate + `place_of_worship` `place_ref`.** Deleting it without first correcting id 49's coordinate loses the good position. | §16 **Design A** (standalone P8-C is the only migration that mutates id 49's coordinate; P8-A only reads it for PRE validation, never writes it in forward or reverse) **XOR** **Design B** (coordinate update = P8-A atomic step 1). Never both in one lineage. `NO_CHANGE_REQUIRED` also valid. Hard precondition — §14 Precondition 8, §16. |
| 2 | `0095`–`0098` are **merged to `develop` but unapplied to Production** (ledger latest = `0094`). A new P8 migration's number (`0099`+), `dependencies`, and deploy order interact with them. | Mother Ship decides sequencing (§19). Each P8 migration is **`FAIL_CLOSED`**: when the audited Production subject is present it must match its exact approved PRE state or `RAISE` (never a silent successful no-op / "idempotent after deletion"). For P8-A / P8-B the only clean no-op is the narrowly documented fresh/empty **subject-absent** boundary (§14, §15). **P8-C has no "already-corrected" no-op** — an id 49 already at the corrected coordinate `RAISE`s; P8-C prefers a ledger-only contract (§16). Same contract class as the P6 / `0097` (PR #2629) / `0098` corrections. |
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
| T8 | id 21 / 22 / 49 are `SCORING_USED` (carry `goriyaku_tags`); id 101 / 103 / 104 / 105 are `SCORING_NOT_USED` (0 `goriyaku_tags`). Removing the four `SCORING_NOT_USED` targets (shadows 101/103/104 + artefact 105) has `RECOMMENDATION_IMPACT = NONE` and **zero** Knowledge-content impact; the `SCORING_USED` primaries 21/22/49 are not touched by P8-A / P8-B | **FINAL** (traced code paths §11) |
| T9 | `UNIQUE_REAL_SHRINE_IDENTITIES = 103`; coverage-tool **default** denominator is currently **107** and would become **103** after P8-A + P8-B **without a policy change** | **FINAL** |
| T10 | `temples_like` / `temples_rankinglog` / `temples_conciergehistory` do not exist in Production; `temples_shrine_deities` is an empty legacy table | **FINAL** |
| T11 | Only `build_chat_candidates` and `knowledge_coverage_report` apply `exclude_qa_fixture_shrines`; all Shrine display APIs do not | **FINAL** |

## 19. Mother Ship Decision Packet

### Remediation safety contract (fixed by this audit — **not** a Mother Ship choice)

```text
P8_A_PRESTATE_POLICY = FAIL_CLOSED   # §14 — audited subject present ⇒ exact PRE match or RAISE; only clean no-op = fresh/empty applicability boundary
P8_B_PRESTATE_POLICY = FAIL_CLOSED   # §15 — same, for id 105
P8_C_PRESTATE_POLICY = FAIL_CLOSED   # §16 — id 49 present ⇒ current coord must be EXACTLY 35.6733,139.7967 or RAISE/ABORT; "already-corrected" is NOT a no-op; reverse restores old only from the exact new value or RAISE; no both-mechanisms lineage (Design A xor Design B)
```

- No P8 migration may treat an unexpected present state as a "safe
  successful no-op" or as "idempotent after deletion".
- Reverse-state is reconstructed from **static audited snapshots baked into
  the migration** (Strategy A) or an **explicitly persisted migration-owned
  marker** (Strategy B) — never from `RunPython` in-memory forward state,
  which does not survive to reverse.
- The 2 `ShrineInteractionLog` rows are addressed by a **stable audited
  predicate** (`user_id=1` + `action_type='detail_view'` + `ctx='map'` +
  audited `created_at`), not by ephemeral forward-run ids.
- Reverse may assume the exact approved PRE contract held **because** forward
  `RAISE`s on any mismatch; reverse restores only migration-owned state and
  is itself guarded (no re-create when the identity already exists; no-op on
  a fresh-lineage-only history).

### Mother Ship actions

Technical findings (§18) are evidence-final. **Product / governance actions
below are `PENDING_MOTHER_SHIP` — not inferred here.**

```text
P8_101_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (KEEP_PRIMARY_REMOVE_SHADOW → 22)
P8_103_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (→ 21)
P8_104_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_SHADOW (→ 49), coordinate-coupled to P8_49_COORDINATE_ACTION
P8_105_ACTION            = PENDING_MOTHER_SHIP   # audit recommends REMOVE_ARTIFACT
P8_49_COORDINATE_ACTION  = PENDING_MOTHER_SHIP   # audit recommends UPDATE → 35.6717809, 139.799519 (Δ ≈ 305.6 m); NO_CHANGE_REQUIRED is valid if ~306 m is within map tolerance
P8_DELIVERY              = PENDING_MOTHER_SHIP   # audit recommends SPLIT_MIGRATIONS: P8-A shadows + P8-B artefact as independent reversible RunPython migrations; the id 49 coordinate via §16 Design A (standalone P8-C, before P8-A) XOR Design B (folded into P8-A step 1) — never both
P8_C_DELIVERY_DESIGN     = PENDING_MOTHER_SHIP   # DESIGN_A_INDEPENDENT_P8C / DESIGN_B_FOLDED_INTO_P8A / NO_CHANGE_REQUIRED
P8_USER_DATA_POLICY      = PENDING_MOTHER_SHIP   # audit recommends MOVE_TO_PRIMARY (the 2 ShrineInteractionLog rows → 22 / 21). NO_USER_DATA is factually true for 104/105 but NOT for 101/103.
P8_COUNTER_POLICY        = PENDING_MOTHER_SHIP   # moot for current data (all counters 0 / RankingLog table absent); audit recommends PRIMARY_ONLY, with SUM reserved for any future raw tally column
```

Additional pending items:

1. **Sequencing** of the P8 migrations relative to the unapplied `0095`–`0098`
   (P8 starts at `0099`; `dependencies` + deploy order).
2. Whether id 104's `place_ref` (Google Place link) should be **moved to
   id 49** on removal (gives id 49 a `place_of_worship` provider record) or
   dropped.
3. Whether the id 49 coordinate is changed at all (`UPDATE` vs
   `NO_CHANGE_REQUIRED`) and, if changed, via §16 **Design A** (standalone
   P8-C) or **Design B** (folded into P8-A) — the two are mutually exclusive
   and must never both appear in one migration lineage.
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
