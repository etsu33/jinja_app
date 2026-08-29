# Source Backfill + Local/Production Reproducibility — id 10 / id 22 (P4)

## 1. Metadata

| Field | Value |
|---|---|
| Task | P4 — audit + safely remediate Source coverage for shrine id 10 (鶴岡八幡宮) and id 22 (給田六所神社), and establish a deterministic artifact that produces the same expected state Local **and** Production. |
| Type | Scoped, reversible **data migration** + audit doc. No model / schema / serializer / Evidence Gate / mapping / taxonomy / frontend / Spreadsheet change. |
| Branch | `audit/source-backfill-id10-id22-reproducibility` |
| Base | `origin/develop` @ `75d1986975f62be640bb6070eea49f71df5a9f9e` (PR #2618 / migration 0095). `git fetch origin` this session. Intervening merges since P3-plan: PR #2617 (`docs/audit/test-release-premium-boundary-audit.md`, docs-only) + PR #2618 (P3 migration 0095 + test + doc). Neither materially alters Shrine / Knowledge models, Evidence Gate, Knowledge selector, GoriyakuTag, the Recommendation Evidence contract, migration conventions, or the Shrine Detail serializer → **no `BASE_DRIFT_REQUIRES_REVIEW`**. |
| Worktree | `~/Developer/jinja_app-p4` (isolated; control repo untouched). |
| Date | 2026-08-29 |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`). Every query passed `guard.py check-readonly-sql`. Credential value never printed / logged / in argv. **No Production write path is available in this session.** |

## 2. Repository architecture map (fresh read)

| Component | Current path / behavior |
|---|---|
| Shrine | `backend/temples/models.py:222` — `goriyaku` `TextField` (blank/null), `goriyaku_tags` M2M → `GoriyakuTag`, `place_ref` `OneToOne` (map-resolve duplicate rows carry `place_ref`; the catalog row does not — see migration 0091). |
| `ShrineKnowledgeSource` | `models.py:432` — `source_type` ∈ {`shrine_official`, `government`, `cultural_property`, `academic`, `museum_or_archive`, `local_history`, `tourism_official`, `secondary_editorial`, `user_observation`, `internal_research`}; `title` (not-blank), `url` `URLField`, `publisher`, `verification_status` (default `draft`), `confidence`, `verified_at`, `language`. `clean()` → `source_confirmed`/`reviewed` **require** `verified_at`. No uniqueness constraint on `url`. |
| `ShrineDeity` / `ShrineHistory` | `models.py:480` / `:523` — `sources` M2M → `ShrineKnowledgeSource`; `verification_status`, `confidence`, `verified_at`, `sort_order`. `ShrineHistory.history_type` ∈ {`official_origin`, `founding`, `historical_event`, `tradition`, `regional_context`, `editorial_summary`}. |
| Evidence Gate | `backend/temples/services/evidence_gate.py` — `FACT_READY_VERIFICATION_STATUSES = ("source_confirmed", "reviewed")`. `decide_fact_usability(*, verification_status, confidence, source_verification_statuses)` → `usable = fact_ready AND ≥1 fact-ready Source`. `decide_detail_display_state(...)` → `"full"` / `"disputed"` / `"hidden"` (Shrine Detail path). |
| Knowledge selector | `backend/temples/services/shrine_knowledge_selector.py` — `fetch_fact_ready_knowledge_{deities,histories}` prefetch only fact-ready Sources, then `decide_fact_usability`. |
| Coverage tooling | `backend/temples/services/knowledge_coverage_report.py` (+ command) — read-only; scope-injectable (P9). |
| Shrine Detail API | `backend/temples/api/serializers/shrine.py` `ShrineDetailSerializer` — `deities` / `histories` are `SerializerMethodField`s filtered by `decide_detail_display_state ∈ ("full","disputed")`. **Docstring: "Knowledge未登録時は `[]` を返し、Legacy Field（sajin/description）へのfallbackは行わない。"** Each Fact's `sources` = `_fact_ready_sources` (verification_status ∈ FACT_READY). |
| `goriyaku` → tag | `backend/temples/management/commands/backfill_goriyaku_tags.py` `parse_goriyaku()` (split `[、,／/・\|\n\r\t]+`), `GoriyakuTag.objects.get_or_create(name=…)` — name-based, **can create tags**, no id scoping. |
| Data-migration precedent | `0090` (add tag M2M to named shrines), `0091` (fill LEGACY reason facts — **this is the migration that gave id 22 its prose `goriyaku` + `家内安全` tag**; documents the catalog-vs-`place_ref`-duplicate row problem for 給田六所神社 / 長太稲荷神社), `0094` (`.only()` legacy-`text`-`location` guard + name/address identity guard + reverse), `0095` (P3 — scoped, idempotent, reversible, `filter(name=…).first()` never `get_or_create`). |
| Contracts | `docs/knowledge/shrine-knowledge-contract.md` (Source契約, verified_at rule); `docs/knowledge/recommendation-evidence-review-contract.md` (incl. P10 reconciliation — `travel_safe = {3,13,14}`, no benefit from name/deity/anecdote/tradition); `docs/audit/shrine-evidence-integrity-full-audit.md` (id 10 / id 22 both `PROVENANCE_GAP` / `SOURCE_GAP` — knowledge present, no official/primary Source); `docs/audit/batch17-recommendation-evidence-activation.md` (P3 template). |

## 3. Production before-state [prod]

### id 10 鶴岡八幡宮

| Field | Value |
|---|---|
| name_jp / address | 鶴岡八幡宮 / 神奈川県鎌倉市雪ノ下2-1-31 |
| lat / lng / place_ref | 35.3256 / 139.5566 / **NULL** (catalog row) |
| `goriyaku` | `勝運・仕事運・厄除け` (LEGACY seed; `updated_at` 2026-06-11) |
| `goriyaku_tags` | 2 厄除け · 11 勝運 · 12 仕事運 |
| ShrineDeity ×3 | 22 応神天皇, 23 比売神, 24 神功皇后 (role `unknown`, `source_confirmed` / `high`, sources 13+14) |
| ShrineHistory ×5 | 13 `founding` 「由比若宮の勧請」 (康平6年1063 源頼義…由比若宮); 14 `historical_event` 「現在地への遷座」 (治承4年1180 源頼朝); 15 「源義家による修復」; 16 「源平池の造営」; 17 「神宮寺の創建」 — all `source_confirmed` / `high`, sources 13/14 |
| Sources | **13 `tourism_official`** `source_confirmed`/`high` (鎌倉市観光協会, `trip-kamakura.com/place/japanheritage/209.html`); **14 `secondary_editorial`** `source_confirmed`/`high` (Wikipedia). **No `shrine_official` / `government` / `cultural_property`.** |
| Disputed Facts | 0 |

### id 22 給田六所神社

| Field | Value |
|---|---|
| name_jp / address | 給田六所神社 / `日本、〒157-0064 東京都世田谷区給田１丁目３−７` |
| lat / lng / place_ref | 35.662443 / 139.5920237 / **NULL** (catalog row; shadow row is id 101, `place_ref` set — excluded per PR #2612/#2614) |
| `goriyaku` | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` (**prose**, written by migration 0091; `updated_at` 2026-08-10) |
| `goriyaku_tags` | 7 家内安全 (hand-set by 0091; 0091 also tried `地域安泰` which is not in the 39-row master → silently skipped) |
| ShrineDeity ×2 | 39 大国魂大神 (`primary`), 40 天照皇大神 (`secondary`) — `source_confirmed` / **`medium`**, sources 24+25 |
| ShrineHistory ×4 | 27 `founding` 「武蔵総社六所宮よりの分霊勧請」; 28 「村社列格」; 29 「社殿改築」; 30 「神明社の合祀」 (千歳村給田八五〇番地の無格社・神明社を合祀) — `source_confirmed` / **`medium`**, sources 24/25 |
| Sources | **24 `secondary_editorial`** `source_confirmed`/`medium` (Wikipedia 六所神社(世田谷区給田)); **25 `local_history`** `source_confirmed`/`medium` (`tesshow.jp`). **No `shrine_official` / `government` / `cultural_property`.** |
| Disputed Facts | 0 |

## 4. Spreadsheet identity reconciliation

Spreadsheet used as **identity / location reference only** (not modified; row-id equality not used as proof). Task-supplied observations vs Production [prod]:

| | Spreadsheet | Production [prod] | Match |
|---|---|---|---|
| id 10 | 鶴岡八幡宮 / 神奈川県鎌倉市雪ノ下2-1-31 | 鶴岡八幡宮 / 神奈川県鎌倉市雪ノ下2-1-31 | **name EXACT · address EXACT** · coords 35.3256/139.5566 = Tsurugaoka Hachimangu, Kamakura |
| id 22 | 給田六所神社 / 東京都世田谷区給田1丁目3-7 | 給田六所神社 / `…東京都世田谷区給田１丁目３−７` | **name EXACT · address NORMALIZED_MATCH** (`給田1丁目3-7` == `給田１丁目３−７`) · coords 35.662443/139.5920237 |

Neither spreadsheet row carries an `official_source_url`. **No material identity conflict → `IDENTITY_RECONCILIATION_REQUIRED` not triggered.** (Direct Codex spreadsheet read remains blocked; the task-supplied observations + `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ = VERIFIED` [project] are sufficient for identity reconciliation, and both match Production.)

## 5–7. Source candidates + classification + identity evidence

`PASS_SOURCE` = trustworthy authority + unambiguous shrine identity + stable URL + factual content about this shrine.

### id 10 鶴岡八幡宮

| Candidate | Type | This-session result | Class | Identity evidence |
|---|---|---|---|---|
| 鶴岡八幡宮 official — `www.hachimangu.or.jp/knowledge/` | shrine_official | **could not be first-hand fetched** — TLS certificate verification failure (`unable to verify the first certificate`); `web.archive.org` blocked for this tool. Content (御祭神 応神天皇/神功皇后/比売神; 康平6年1063 源頼義; 建久2年1191) confirmed **only via search-engine index snippets**, which match Production's existing Facts. | **HOLD_SOURCE** | Genuine official domain, but not first-hand reviewable this session → cannot be recorded `source_confirmed`. |
| 文化庁 文化遺産オンライン — `online.bunka.go.jp/heritages/detail/160978` "鶴岡八幡宮境内（史跡）" | cultural_property | **fetched & reviewed this session.** 史跡, designated 1967-04-24. States: 源頼義 の若宮 (Wakamiya) を 源頼朝 が現在地へ遷し 八幡神を勧請; 「鎌倉の中心」; 本宮ほか多数 重要文化財. Location 鎌倉市雪ノ下・小町・材木座. **No ご利益 statement** (cultural-property record). | **PASS_SOURCE** | Exact identity (鶴岡八幡宮境内, Kamakura); government cultural authority; stable URL; directly supports the founding + 1180-relocation histories. |
| 鎌倉市観光協会 — `trip-kamakura.com/place/japanheritage/209.html` | tourism_official | already recorded [prod] as Source 13 (`source_confirmed`). | *(pre-existing)* | — |
| Wikipedia 鶴岡八幡宮 | secondary_editorial | already recorded [prod] as Source 14. | *(pre-existing)* | — |
| tourism aggregators (JR東海ツアーズ, timesclub, park.tachikawaonline, amahashi, sampai-goshuin …) | — | tourism/blog copy; not primary. | **REJECT_SOURCE** | discovery leads only |

### id 22 給田六所神社

| Candidate | Type | This-session result | Class | Identity evidence |
|---|---|---|---|---|
| 文化庁「地域伝統行事・民俗芸能等 情報発信サイト」 — `dentou-hasshin.bunka.go.jp/search/158.html` "給田六所神社例大祭" | government | **fetched & reviewed this session.** States: 「給田六所神社は、武蔵国 大國魂神社の御分霊を招請して建立された氏神様」; 所在 「世田谷区給田1丁目3番7号」; 例大祭 = 毎年10月第4日曜日, 都内有数の大太鼓(径5尺), 子ども神輿, 囃子. **No ご利益 statement** (festival page; the festival prays for 五穀豊穣・無病息災 = a prayer intention, not a stated shrine benefit). | **PASS_SOURCE** | Exact name + address; government cultural authority (文化庁, same authority as 建部大社's P3 government source); stable URL; directly supports the founding history. |
| 東京都神社庁 六所神社(世田谷区給田) — `tokyo-jinjacho.or.jp/setagaya/2048` | government / religious-body | **could not be first-hand fetched** — served plain HTTP on 443 (`WRONG_VERSION_NUMBER` after HTTPS upgrade). Content (御祭神 大國魂大神 + 天照皇大神; 天文年間1532–54 六所宮 御分霊; 明治42年1909 神明社 合祀) confirmed **only via search-engine index snippets**, which match Production's existing Facts. | **HOLD_SOURCE** | Genuine official religious-body listing, but not first-hand reviewable this session. |
| tesshow.jp `setagaya/shrine_kyuden_roksho.html` | local_history | already recorded [prod] as Source 25 (`source_confirmed`). | *(pre-existing)* | — |
| Wikipedia 六所神社(世田谷区給田) | secondary_editorial | already recorded [prod] as Source 24. | *(pre-existing)* | — |
| hotokami / yaokami / setagayajin / okumiya / sanpo-nikki / local-media blogs | — | third-party summaries / blogs. | **REJECT_SOURCE** | discovery leads only |

**Two official-source domains were unreachable to the fetch tool this session (TLS cert / HTTP-only)** — the same class of blocker P3 hit with `hokkaidojingu.or.jp`. Recorded as `HOLD_SOURCE`, deferred (Section 18), not written.

## 8. Supported Knowledge Facts (from the `PASS_SOURCE`s)

Both `PASS_SOURCE`s are **government / cultural-property** records that **corroborate Facts already stored in Production**. They add no new factual claim that is not already a Fact, and contain **no explicit ご利益/御神徳**.

| `PASS_SOURCE` | Directly supports existing Fact | Action |
|---|---|---|
| id 10 · `online.bunka.go.jp/heritages/detail/160978` | `ShrineHistory` `founding` 「由比若宮の勧請」 (源頼義の若宮); `ShrineHistory` `historical_event` 「現在地への遷座」 (治承4年1180 源頼朝) | add Source, relate to **these 2 existing histories** |
| id 22 · `dentou-hasshin.bunka.go.jp/search/158.html` | `ShrineHistory` `founding` 「武蔵総社六所宮よりの分霊勧請」 (武蔵国 大國魂神社の御分霊) | add Source, relate to **this 1 existing history** |

## 9. Unsupported / inferred claims explicitly rejected

- **id 10 official `shrine_official` Source** — not added: could not be first-hand fetched/verified this session. Not recorded from a search snippet.
- **id 22 東京都神社庁 Source** — not added: could not be first-hand fetched/verified this session.
- **id 22 例大祭 as a new `ShrineHistory` Fact** — not added: the two sources **materially disagree on the festival date** (文化庁: 10月第4日曜日; 東京都神社庁 via search: 10月2日); and a festival schedule is marginal, non-Recommendation-facing. No Fact written.
- **Any deity relation for the new Sources** — the two `PASS_SOURCE`s do not enumerate the enshrined deities in the fetched text (id 10 record speaks of 八幡神 generically; id 22 festival page names 大國魂神社 as the 分霊 origin, not the local deity roster). The Sources are related **only to the `founding` / relocation histories they explicitly support**, not to `ShrineDeity` rows.
- **No benefit inference** — neither Source states a ご利益; no `goriyaku` / `GoriyakuTag` change; no deity→benefit / history→benefit / tradition→benefit derivation.

## 10. Explicit Recommendation Evidence candidates

**None.** Neither `PASS_SOURCE` contains an explicit blessing / prayer-benefit statement. id 10's `goriyaku` (`勝運・仕事運・厄除け`) remains **`LEGACY_EXISTING`, untouched** by P4; id 22 has no canonical `goriyaku` labels (prose + a hand-set `家内安全` tag), also **untouched**. **Recommendation Evidence activation is not part of this Source Backfill** and no follow-up activation is triggered by it. (A Recommendation-Evidence review of id 10's LEGACY `goriyaku` against its official Source is P2 territory — Section 18.)

## 11. id 22 sparse-data result

`SOURCE_BACKFILL_RESULT` for id 22 = **`GOVERNMENT_SOURCE_ADDED` (provenance upgrade only)** — one `government` (文化庁) Source added and related to the existing founding history. **Not** `INSUFFICIENT_OFFICIAL_EVIDENCE`: a sufficient first-hand-reviewed government Source was found. Consistent with the sparse-data policy: **identity/location preserved, no manufactured Facts, no `goriyaku`, no `GoriyakuTag`.** The detailed deity/history detail already present remains at its stored `medium` confidence (unchanged). The primary religious-body listing (東京都神社庁) is deferred (unreachable this session) — this does **not** mean "the shrine has no history/benefit", only that the system's official-source coverage for id 22 is still improving.

## 12. Missing-detail backend / API / UI behavior

| Layer | Behavior when a shrine has no deity / no history / no usable Source / no `goriyaku` / no tag |
|---|---|
| DB | fields simply absent (no `ShrineDeity`/`ShrineHistory` rows; `goriyaku` `""`/NULL; empty M2M) |
| Serializer / API (`ShrineDetailSerializer`) | `deities: []`, `histories: []` (empty arrays, never `null`/`undefined`); **no fallback to `sajin` / `description`**; `goriyaku` = the raw field (`""` when unset). Covered by `test_shrine_detail_api_returns_empty_arrays_when_no_knowledge` and 3 more assertions in `temples/tests/api/test_shrine_detail_knowledge_api.py`. |
| Crash / regression | none — `SerializerMethodField` returns `[]` deterministically; query count unchanged (`test_shrine_detail_api_source_filtering_does_not_increase_query_count`). |
| Product semantics | matches the preferred reading — **"verified detail is not currently registered"**, not "this shrine has no history / no benefit". No misleading "no benefit" wording is emitted by the backend. |

**No frontend/UI change required in P4** — existing behavior is safe. id 10 and id 22 both already have deity + history Knowledge, so their Detail views render normally; the P4 Source relation only makes the (already fact-ready) Facts cite an additional, higher-authority Source.

## 13. Local / Production reproducibility mechanism

**`backend/temples/migrations/0096_source_backfill_id10_id22.py`** — a scoped, reversible `RunPython` data migration (0090 / 0091 / 0094 / 0095 pattern; `makemigrations --check` = no model changes).

**Reproducibility keystone:** the local dev DB (`jinja_db`) and Production assign **different `ShrineHistory` pks to the same seed Facts** (verified this session: 鶴岡八幡宮's 「由比若宮の勧請」 founding history is pk **19** locally vs pk **13** in Production; 給田六所神社's founding history is pk **12** locally vs pk **27** in Production). A pk-keyed guard would therefore write different rows in each environment — a reproducibility failure. So the migration matches target Facts by **environment-stable identity only**: `shrine_id` (pk 10 / 22 — stable) + `history_type` + `title` (seed-defined). The same artifact then relates the reviewed Source to the same *semantic* Fact everywhere.

Safety behavior:

- shrine matched by `pk` + `name_jp` + `place_ref_id IS NULL` (the catalog row, not the map-resolve `place_ref` duplicate — 0091); mismatch ⇒ that shrine is a no-op;
- `ShrineKnowledgeSource` looked up by exact `url` + `source_type` first ⇒ re-run reuses it (no duplicate Source row); created with `verification_status = "source_confirmed"`, `verified_at = 2026-08-29`, `confidence = "high"`, `publisher = "文化庁"`;
- `history.sources.add(src)` ⇒ no-op if the relation already exists (idempotent);
- `.only()` on the `Shrine` `SELECT` excludes `location` (the 0091/0094 legacy-`text`-column GEOSException guard);
- reverse (`revert_source_backfill`): removes exactly the relations this migration added, then deletes the Source row **only if** it has no remaining `deities` / `histories` relations (a later Fact citing it survives).

## 14. Write scope

Allowed and used: **`ShrineKnowledgeSource` inserts + `ShrineHistory.sources` M2M relations, for shrine ids 10 and 22 only.**

| Shrine | New `ShrineKnowledgeSource` | Related to existing `ShrineHistory` |
|---|---|---|
| 10 | `cultural_property` · 「鶴岡八幡宮境内（史跡）｜文化遺産オンライン（文化庁）」 · `https://online.bunka.go.jp/heritages/detail/160978` · `source_confirmed` / `high` / `verified_at 2026-08-29` | `founding` 「由比若宮の勧請」 + `historical_event` 「現在地への遷座」 |
| 22 | `government` · 「給田六所神社（給田六所神社例大祭）｜地域伝統行事・民俗芸能等 情報発信サイト（文化庁）」 · `https://www.dentou-hasshin.bunka.go.jp/search/158.html` · `source_confirmed` / `high` / `verified_at 2026-08-29` | `founding` 「武蔵総社六所宮よりの分霊勧請」 |

**Not written:** any `ShrineDeity` / `ShrineHistory` Fact (none created; none modified); any `verification_status` / `confidence` / `verified_at` / `content` of an existing Fact; `Shrine.goriyaku`; `goriyaku_tags`; `GoriyakuTag` master; `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS`; Evidence Gate; interpreter / scoring / ranking / C1 / Lead / Reason; frontend; Google Spreadsheet. No shrine other than 10 and 22.

## 15. Local verification

- `python manage.py makemigrations temples --check --dry-run` → **"No changes detected"** (data-only).
- `python manage.py migrate temples` → `Applying temples.0096_source_backfill_id10_id22... OK`.
- Applied state on the **local dev DB** (`jinja_db`, whose `ShrineHistory` pks differ from Production): the migration created source `online.bunka.go.jp/heritages/detail/160978` related to shrine 10's 「由比若宮の勧請」 + 「現在地への遷座」, and `dentou-hasshin.bunka.go.jp/search/158.html` related to shrine 22's 「武蔵総社六所宮よりの分霊勧請」 — i.e. the **expected state**, reached via title/type matching despite the pk drift.
- `python manage.py migrate temples 0095` → `Unapplying … OK`; 0 leftover P4 Source rows. `migrate temples` again → re-applies cleanly (idempotent forward + reverse cycle on the real local DB).
- Tests: `test_migration_0096_source_backfill_id10_id22.py` — **11 passed** (list in Section 23). Focused Knowledge/Evidence-Gate/selector/coverage/need-mapping/0091/0094/0095 regression — **127 passed**. Shrine-detail knowledge API — **64 passed**. Full `backend/temples` suite — **1929 passed, 13 skipped, 0 failed**.
- `git diff --check` → clean. `markdownlint` (`.markdownlint.json` rules) → 0 issues.

## 16. Production apply status

**`PRODUCTION_ACTIVATION = PENDING_AUTHORIZED_APPLY`** — only a read-only Production credential is available this session; not bypassed, no ad-hoc SQL, no disabled guards. Migration `0096` is committed and applies on the next authorized `migrate` / deploy. Production `ShrineHistory` pks (13 / 14 / 27) are matched by the same `shrine_id` + `history_type` + `title` identity the local run used → same expected result.

Pre-apply gate (re-verified [prod] this session):

| Check | Result |
|---|---|
| id 10 / id 22 shrine identity (name + address + `place_ref IS NULL`) | matches the migration guard |
| target histories present [prod] | id 10 pk 13 「由比若宮の勧請」 `founding`, pk 14 「現在地への遷座」 `historical_event`; id 22 pk 27 「武蔵総社六所宮よりの分霊勧請」 `founding` — all present, `source_confirmed`, fact-ready |
| new Source `url`s not already present [prod] | neither `online.bunka.go.jp/heritages/detail/160978` nor `dentou-hasshin.bunka.go.jp/search/158.html` is currently a `ShrineKnowledgeSource` for id 10 / id 22 |
| scope | exactly ids 10 and 22 |
| get_or_create risk | none — `ShrineKnowledgeSource` looked up by `url`+`source_type`, `ShrineHistory` never created |

## 17. Inconsistencies found

- **Local dev DB `ShrineHistory` pk drift vs Production** (Section 13) — the reproducibility issue this task exists to catch; handled by identity-based matching.
- **Two official-source domains unreachable to the fetch tool** — `www.hachimangu.or.jp` (TLS cert verification failure) and `www.tokyo-jinjacho.or.jp` (HTTP-only, `WRONG_VERSION_NUMBER` after HTTPS upgrade). Same class as P3's `hokkaidojingu.or.jp`. Deferred, not written.
- **id 22 `goriyaku` provenance** — the prose `goriyaku` and the `家内安全` tag were written by migration **0091** as a LEGACY reason-fact fill, **not** from a reviewed Source. P4 does not touch it; a Recommendation-Evidence review of it is out of P4 scope.
- **id 22 tag `地域安泰`** — migration 0091 intended to add `地域安泰` to id 22 but that label is not in the canonical 39-row master, so `GoriyakuTag.objects.get(...)` silently no-op'd; only `家内安全` is attached. Recorded, not changed.
- **例大祭 date conflict** between 文化庁 and 東京都神社庁 sources for id 22 — reason the festival was not written as a Fact.

## 18. Follow-up PR packets

| # | Packet | Trigger |
|---|---|---|
| F1 | **id 10 `shrine_official` Source** — add `www.hachimangu.or.jp/knowledge/` (`shrine_official`, `source_confirmed`) related to the deities + histories, in a session where the site is fetchable (or via an authorized offline capture). Same identity-based migration pattern as 0096. | `www.hachimangu.or.jp` TLS reachable |
| F2 | **id 22 東京都神社庁 Source** — add `tokyo-jinjacho.or.jp/setagaya/2048` (official religious-body listing; type `government`) related to deities 39/40 + histories 27/30, in a session where the HTTP-only site is fetchable. | `tokyo-jinjacho.or.jp` fetchable |
| F3 | **id 10 Recommendation-Evidence review of the LEGACY `goriyaku`** (`勝運・仕事運・厄除け`) against its official Source once F1 lands — P2-class work; P-C flagged all three labels HOLD on the non-primary Source reviewed there. | F1 done; P2 track |
| F4 | **id 22 confidence review** — with F2's religious-body Source, a reviewer may raise the deity/history `confidence` from `medium`. Fact-field change ⇒ its own reviewed PR. | F2 done |

No frontend PR packet — missing-detail behavior is already safe (Section 12).

## 19. STOP confirmation

No STOP-without-write condition triggered: Spreadsheet ↔ Production identity match; Production targets unambiguous; the two written Sources have unambiguous identity and were first-hand retrieved; no Fact write requires inference; the migration reproduces Local ↔ Production deterministically (identity-based matching); no safety control bypassed; missing-detail behavior needs no Product/UI decision. The two unreachable official domains were classified `HOLD_SOURCE` and deferred — they do not block the government/cultural-property backfill that P4 does perform. PR created. **Not merged.** P4 not broadened. P1 / P2 / P5 / P6 / P7 / P8 not started.

## 20. F5 — migration 0096 reverse-safety fix (post-P5-preflight)

`docs/audit/p5-id21-id22-current-state-evidence.md` §14 confirmed a
reverse-safety edge case in this migration, and the Mother Ship approved
fixing it **before** 0096 is authorized for Production.

- **`0096_REVERSE_EDGE_CASE_BEFORE = CONFIRMED`.** Original `revert_source_backfill`
  called `history.sources.remove(source)` for every target history and deleted
  the Source if it became unreferenced — **unconditionally**. If, before 0096
  forward, a `ShrineKnowledgeSource` with the same `url` + `source_type`
  already existed and a target history already cited it, forward was an
  effective no-op (reuse + idempotent `.add()`), but reverse would still strip
  that pre-existing relation and could delete a pre-existing Source row —
  removing state 0096 never created.
- **`0096_REVERSE_EDGE_CASE_AFTER = FIXED`.** Forward now writes a sentinel
  (`MIGRATION_TAG = "[temples.0096:auto-created]"`) into `ShrineKnowledgeSource.note`
  **only on a row it creates itself**; a reused pre-existing Source is never
  modified. Reverse acts **only** on a Source whose `note` contains that exact
  sentinel — so a pre-existing (reused) Source, and any relation it already
  had, is left exactly as found. This mirrors 0095's "reverse only undoes the
  exact state forward wrote". Forward's provenance semantics (which Source,
  which target histories, identity guards, `.only()` `location` guard,
  Local/Production title-based matching) are otherwise **unchanged**; the only
  forward change is the rollback-tracking `note` stamp.
- **`PRODUCTION_0096_STATUS = PENDING_AUTHORIZED_APPLY`** — verified this
  session against the Production `django_migrations` ledger (read-only): the
  latest applied `temples` migration is `0094_fix_shrine_70_coordinates`;
  **0095 and 0096 are both `<NOT APPLIED>`**. So 0096 is edited in place (the
  repository-approved path for an unapplied migration); no already-applied
  migration contract is rewritten. On the first authorized Production apply,
  forward creates the two Sources fresh and stamps them, so the fix is fully
  effective there. `PRODUCTION_IMPACT` of the original edge case remains
  `NONE_CURRENTLY` — neither P4 Source URL exists in Production today.
- Tests: `test_migration_0096_source_backfill_id10_id22.py` gains
  `test_f5_preexisting_source_and_relation_survive_reverse` (the required
  scenario), `test_f5_forward_stamps_marker_only_on_rows_it_creates`,
  `test_f5_reverse_ignores_a_source_it_did_not_stamp`,
  `test_f5_reapply_after_reverse_recreates_and_re_marks`; all prior coverage
  (new-Source creation, relation creation, normal reverse, Source shared by
  another Fact, idempotent forward, repeated apply, wrong-identity no-op,
  Local/Production PK drift, unrelated shrines unchanged) is retained.
- **Local-DB note:** the local `jinja_db` may still hold the two P4 Source
  rows from an earlier *pre-F5* apply of 0096 with an empty `note`; the F5
  reverse conservatively leaves such unmarked rows alone. This is a dev-DB
  artifact only — Production has never applied 0096, so it starts clean.
- Delivered as its own PR (`fix/migration-0096-reverse-guard`), **not** bundled
  with the P5-DATA tag reconciliation.
