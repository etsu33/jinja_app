# Shrine Identity — Compass / Concierge Shared Identity Contract

## Status

- Status: `AUDITED_CONTRACT_RECORDED`
- Recorded at: `2026-09-23`
- Type: architecture / contract audit. **Read-only.**
- Runtime behavior change: `NONE`
- Related: `docs/audit/canonical-shrine-anchor-gate-c-decision-record.md` (Gate C — Split Anchor)
- Classification (as audited): **`PARTIALLY_SHARED`** (§7)
- Updated at: `2026-09-23` — `F-1` 実装により Compass 側の状態が変化（§9）
- `F-3` design record: `docs/audit/shared-shrine-identity-resolver-design.md`
  （設計のみ。runtime 未変更）

本書の §1–§8 は監査時点の記録であり、書き換えていない。Compass `id` fallback は
この監査の時点では残存していたが、**`F-1` で除去済み**。現在状態は §9 を参照。

## 1. Mother Ship Architectural Principle

```text
Compass and Concierge MUST share the same Shrine identity.
Selection logic MAY differ.
```

```text
Compass    : direction-first, geographic direction has high importance
Concierge  : meaning / goriyaku / consultation-fit first, geography secondary
```

After selection, both must resolve to the same canonical Shrine entity.

```text
SHRINE_IDENTITY_AUTHORITY = Shrine.id
PUBLIC_IDENTITY_KEY       = shrine_id
```

A generic recommendation `id` is **not** identity authority.

### 1.1 Three separate questions

```text
Shrine Identity   -> "Which Shrine is this?"      -> Shrine.id / shrine_id
Canonical Anchor  -> "Where is this Shrine represented geographically?"
Navigation Anchor -> "Where should navigation take the user?"
```

Changing an anchor must not change Shrine identity. Under Gate C
(`SPLIT_CANONICAL_AND_NAVIGATION_ANCHORS`) two anchors will exist per Shrine; this
contract fixes that **both belong to one `Shrine.id`**, and that neither anchor is ever
an identity input.

## 2. Current Identity Flow

### 2.1 Diagram

```text
                        ┌──────────────────────────────┐
                        │   temples_shrine  (Shrine)   │
                        │   PRIMARY KEY = Shrine.id    │  <- SHRINE_IDENTITY_AUTHORITY
                        └───────────────┬──────────────┘
                                        │
             backend/temples/services/concierge_chat_candidates.py
             build_chat_candidates_with_eligibility()      L203
             qs = Shrine.objects.all()                     L213
             QA-fixture exclusion + eligibility gate       L226-259
                                        │
                        candidate dict emission            L284-286
                        ┌───────────────┴───────────────┐
                        │  "id":        s.id            │
                        │  "shrine_id": s.id            │   <- SAME VALUE, one source
                        │  "place_id":  place_ref.place_id (nullable)
                        └───────────────┬───────────────┘
                                        │
              backend/temples/services/concierge_chat.py
              build_chat_recommendations()                 L639
              _normalize_candidate_fields() per candidate   L676
              recommendation dict: "shrine_id" = shrine_id or id   L441
                                        │
                   ┌────────────────────┴────────────────────┐
                   │                                         │
        CONCIERGE path                            COMPASS path
        (api/views/concierge.py)      compass_recommendation_orchestrator.py
                                       imports build_chat_candidates_with_eligibility  L50
                                       imports build_chat_recommendations              L49
                                       direction filter + 15/30/60km rings   L162-183
                                       recs = build_chat_recommendations(...)  L328
                                       "untouched ... does not reshape"        L103-104
                   │                                         │
                   │                        api/compass_public_projection.py
                   │                        ITEM_FIELDS allowlist includes
                   │                        BOTH "shrine_id" AND "id"     L32-33
                   │                                         │
        features/concierge/detailHref.ts        features/compass/components/
        pickShrineId()                          CompassRecommendationsSection.tsx
          shrine_id ?? shrineId ?? shrine.id      L35  shrine_id ?? id   (analytics)
          *** `id` DELIBERATELY EXCLUDED ***      L58  shrine_id ?? id   (navigation)
                   │                                         │
                   └────────────────┬────────────────────────┘
                                    │
                    lib/nav/buildShrineHref.ts  L55
                    /shrines/{id}?ctx=&tid=&recommendation_*
                                    │
                        app/shrines/[id]/page.tsx
                        numericId -> Shrine detail
```

### 2.2 Audit items 1–10

| # | Question | Finding | Evidence |
| ---: | --- | --- | --- |
| 1 | Concierge candidate creation → Shrine DB | `build_chat_candidates_with_eligibility()` queries `Shrine.objects.all()` | `concierge_chat_candidates.py` L203, L213 |
| 2 | Compass candidate creation → Shrine DB | identical — Compass imports the same function | `compass_recommendation_orchestrator.py` L50 |
| 3 | Both use `concierge_chat_candidates.py`? | **YES.** Single shared candidate source. Compass additionally reuses `build_chat_recommendations` and does not reshape results | orchestrator L49–50, L103–104, L328 |
| 4 | How `Shrine.id` becomes `id` / `shrine_id` | one emission site sets both from the same attribute: `"id": s.id`, `"shrine_id": s.id` | `concierge_chat_candidates.py` L284–285 |
| 5 | Concierge result → detail navigation | `detailHref.ts` → `pickShrineId()` → `buildShrineHref()`. `id` is explicitly refused | `detailHref.ts` L12–14, L26–29, L38–44 |
| 6 | Compass result → detail navigation | `CompassRecommendationsSection.tsx` L58 `rec.shrine_id ?? rec.id` → `buildShrineHref()` | L58, L77–90 |
| 7 | Where `id` is accepted as fallback | 16 backend sites / 8 files + 12 frontend sites — enumerated in §4 | §4 |
| 8 | Compass-only / Concierge-only identity namespace | **NONE.** Neither surface creates Shrine rows; both read the same table through one function | §3 |
| 9 | Can `place_id` substitute for a registered Shrine identity | **YES, currently possible** — see §5 | `places.py` L44–60 |
| 10 | favorite / detail / analytics identity | same `shrine_id` key; favorites additionally accept `place_id` for unregistered targets | §2.3 |

### 2.3 Favorite / detail / analytics

```text
favorites  backend/temples/api/serializers/favorites.py L62-94
             shrine_id = PrimaryKeyRelatedField   -> FK-validated against Shrine
             place_id  accepted for UNREGISTERED targets only
             L94: "either shrine_id or place_id is required"

detail     app/shrines/[id]/page.tsx  -> numericId -> Shrine PK lookup

analytics  trackShrineInteraction({ shrineId })  GoogleMapRouteLink.tsx L92,
                                                 ShrineDetailViewTracker.tsx L46
           trackRecommendationQuality({ shrineId })  concierge/hooks.ts L154
```

Favorites are the strongest link in the chain: `PrimaryKeyRelatedField` means an
invalid `shrine_id` is rejected at the serializer, not silently stored.

## 3. Current Shared Behavior

```text
SHARED_CANDIDATE_SOURCE        = YES   concierge_chat_candidates.py
SHARED_RECOMMENDATION_BUILDER  = YES   concierge_chat.build_chat_recommendations
SHARED_IDENTITY_ORIGIN         = YES   Shrine.id, single emission site
SEPARATE_IDENTITY_NAMESPACE    = NONE
IDENTITY_FROM_NAME             = NOT_OBSERVED
IDENTITY_FROM_COORDINATES      = NOT_OBSERVED
IDENTITY_FROM_ANCHOR           = NOT_OBSERVED (no anchor field feeds identity)
SHARED_DETAIL_ROUTE            = YES   buildShrineHref -> /shrines/{id}
```

The architectural principle is **already satisfied at the data layer**. Compass does
not select from a different pool, does not re-key candidates, and does not mint Shrine
rows. Its difference from Concierge is confined to a direction filter and distance
rings applied *after* the shared candidate build.

The `id` field is therefore not currently a divergent identity — at the producer it is
by construction equal to `shrine_id`. The problem recorded below is contractual, not a
present-tense data defect.

## 4. Inconsistencies / Fallbacks

### 4.1 Backend `shrine_id or id` sites

```text
concierge_chat_candidates.py   L66     _candidate_shrine_id: ("shrine_id", "id")
concierge_chat.py              L441    shrine_id or id or source.shrineId
                               L521, L606, L616
concierge_chat_ranking.py      L1144
concierge_chat_pool.py         L44, L56, L91, L108
concierge_chat_observation.py  L94, L139, L224
concierge_candidate_utils.py   L137-138
recommendation_score_components.py     L114
recommendation_quality_measurement.py  L125
```

```text
BACKEND_FALLBACK_SITES = 16   across 8 files
```

All read `shrine_id` first and fall back to `id`. Because §2.1 shows both keys come
from `Shrine.id`, every one of these currently resolves to the same value.

### 4.2 Frontend `id` fallback — the Compass / Concierge asymmetry

This is the material finding.

```text
CONCIERGE navigation   features/concierge/detailHref.ts  L26-29
  pickShrineId = shrine_id ?? shrineId ?? shrine.id
  `id` is EXCLUDED, with an explicit in-code rule (L12-14):
    "recommendation の `id` は shrine_id ではない可能性があるため使わない。
     実在 shrine への導線は shrine_id / shrineId / shrine.id のみを採用する。"

COMPASS navigation     features/compass/components/CompassRecommendationsSection.tsx
  L58  const shrineId = rec.shrine_id ?? rec.id;
  L77-90  -> buildShrineHref(shrineId, { ctx: "compass", ... })
  `id` is ACCEPTED as a navigation identity.
```

```text
CONCIERGE : id-fallback present in ANALYTICS ONLY   (hooks.ts L145, L154)
COMPASS   : id-fallback present in ANALYTICS AND NAVIGATION (L35 and L58)
```

Concierge already encodes the Mother Ship rule; Compass does not. The two surfaces
disagree about whether `id` is identity-bearing.

### 4.3 `id` is a published Compass contract field

```text
backend/temples/api/compass_public_projection.py L32-33
COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS = ("shrine_id", "id", "name", "address", ...)

backend/temples/api/serializers/compass.py L121-122
shrine_id = IntegerField(required=False, allow_null=True)
id        = IntegerField(required=False, allow_null=True)
```

`id` is not merely tolerated by the Compass client — it is in the Compass Monthly
Public Contract v1 allowlist. Removing the client fallback and removing the field are
therefore two separate decisions.

### 4.4 Other frontend identity readers

```text
ConsultationHistoryDetailView.tsx     L41   shrine_id ?? id
PlaceCardClientActions.tsx            L29   shrine_id ?? id
app/shrines/resolve/page.tsx          L38   shrine_id ?? id
app/shrines/[id]/page.tsx             L370  shrine_id ?? id   (thread rec matching)
lib/api/places.ts                     L47   shrine_id ?? id
lib/concierge/pickReasonFromThread.ts L20   shrine.id ?? shrine_id ?? shrineId ?? id
lib/concierge/buildPreviousConsultationSummary.ts L16  shrine_id ?? id
components/shrine/detail/ShrineDetailArticle.tsx  L368  shrine?.id ?? shrine?.shrine_id
```

`ShrineDetailArticle.tsx` L368 reverses the precedence (`id` before `shrine_id`). On a
Shrine detail payload `id` *is* the Shrine PK, so it is correct today, but it is the one
site whose ordering does not match the contract's stated precedence.

### 4.5 Severity

```text
PRESENT_TENSE_DATA_DEFECT = NONE OBSERVED
CONTRACT_DEFECT           = PRESENT
```

No divergence can occur while `concierge_chat_candidates.py` L284–285 is the only
emission site. The exposure is that **nothing enforces that invariant**: any future
producer that sets `id` to a ranking index, a list position, a result-set offset, or a
Places-derived value would silently repoint Compass navigation while Concierge stayed
correct.

## 5. Can `place_id` Substitute for a Registered Shrine Identity?

```text
ANSWER = YES, under a currently-common condition.
```

```text
backend/temples/services/places.py  L44-60
def get_or_create_shrine_by_place_id(place_id):
    pr = get_or_sync_place(place_id)
    shrine = getattr(pr, "shrine", None)   # reverse OneToOne
    if shrine and shrine.id:
        return shrine                       # dedupe ONLY via PlaceRef.shrine
    ...
    return Shrine.objects.create(...)       # otherwise: NEW Shrine row
```

Deduplication depends entirely on an existing `PlaceRef → Shrine` link. A registered
Shrine whose `place_ref` is **unlinked** is invisible to this check, so resolving that
shrine's Google `place_id` creates a second Shrine row for the same real shrine.

The unlinked state is the norm, not the exception:

```text
docs/audit/position-audit-v2/legacy-position-provenance-batch01.md §1
  place_ref_id = null for all 10 Batch 01 shrines
```

And the failure has already occurred in Production:

```text
docs/audit/tomioka-hachimangu-identity-resolution.md
  富岡八幡宮  {id 49, id 104}   — "zero-data place_ref shadow pattern"
  confirmed duplicate pairs:  101 = 給田六所神社,  103 = 長太稲荷神社
backend/temples/migrations/0099_fix_shrine_49_coordinates.py
  "the same value stored on the duplicate shadow row id 104"
```

This is an identity-creation path that predates and is independent of Compass /
Concierge. It does not break their *shared* identity — both would see the same shadow
row — but it breaks the guarantee that one real shrine maps to one `Shrine.id`.

```text
PLACE_ID_CAN_SHADOW_REGISTERED_IDENTITY = YES
SCOPE                                   = Shrine rows with place_ref = NULL
OBSERVED_OCCURRENCES                    = 3 documented pairs
AFFECTS_COMPASS_VS_CONCIERGE_PARITY     = NO (both resolve identically)
```

## 6. Proposed Authoritative Identity Contract

```text
SHRINE_IDENTITY_AUTHORITY = Shrine.id
PUBLIC_IDENTITY_KEY       = shrine_id
```

### 6.1 Rules

```text
R-1  Compass and Concierge MAY use different recommendation logic.
R-2  Compass and Concierge MUST NOT create separate Shrine identities.
R-3  Registered Shrines MUST be resolved by shrine_id.
R-4  The same real Shrine MUST map to the same Shrine record on both surfaces.
R-5  Shrine identity MUST NOT be derived from name.
R-6  Shrine identity MUST NOT be derived from coordinates.
R-7  Shrine identity MUST NOT be derived from the Canonical Anchor.
R-8  Shrine identity MUST NOT be derived from the Navigation Anchor.
R-9  A generic recommendation `id` MUST NOT be used as identity authority.
```

### 6.2 Anchor separation (binding under Gate C)

```text
Shrine.id            answers  "which Shrine"
Canonical Anchor     answers  "where is it represented"
Navigation Anchor    answers  "where should navigation go"

An anchor change MUST NOT change, invalidate, or re-key Shrine identity.
Adding the Canonical anchor field MUST NOT introduce a second identity key.
```

Recorded because Gate C introduces a second coordinate per Shrine. Neither anchor is
an identity input under R-6 / R-7 / R-8.

### 6.3 Compliance status per rule

```text
R-1  SATISFIED   direction filter / rings applied after the shared candidate build
R-2  SATISFIED   neither surface writes Shrine rows
R-3  PARTIAL     Compass navigation accepts `id` (§4.2)
R-4  SATISFIED   single emission site, single table
R-5  SATISFIED   no name-based identity resolution observed
R-6  SATISFIED   no coordinate-based identity resolution observed
R-7  SATISFIED   Canonical Anchor does not exist yet; no path would feed identity
R-8  SATISFIED   Navigation Anchor is read-only downstream of identity
R-9  VIOLATED    16 backend + 12 frontend fallback sites (§4.1, §4.2, §4.4)
```

## 7. Classification

```text
COMPASS_CONCIERGE_SHRINE_IDENTITY = PARTIALLY_SHARED
```

Not `ALREADY_SHARED`, because two surfaces disagree in code about whether `id` is
identity-bearing, and `id` is a published Compass contract field (§4.2, §4.3).

Not `NOT_SHARED`, because the candidate source, the recommendation builder, the
identity origin and the detail route are literally the same code paths, and no
divergent value can currently be produced (§3).

```text
data layer      = SHARED
contract layer  = NOT YET ENFORCED
```

> この分類は監査時点（`2026-09-23`, PR #2948）のもの。`R-3` / `R-4` / `R-5` / `F-1`
> 完了後の Compass 側の現在状態は §9 を参照。歴史的記録として本節は書き換えない。

## 8. Future Implementation Follow-ups

None of these are performed by this document.

```text
F-1  Compass navigation: drop the `id` fallback at
     CompassRecommendationsSection.tsx L58, matching detailHref.ts.
     Blocked on F-2 — removing the client fallback before the field is
     guaranteed present would break navigation for any item lacking shrine_id.

F-2  Verify shrine_id is present on every Compass recommendation item, then
     decide the fate of `id` in the Compass Monthly Public Contract v1 allowlist
     (compass_public_projection.py L32-33, serializers/compass.py L122).
     Contract-visible change — requires its own gate.

F-3  Introduce one shared identity resolver used by both surfaces
     (a frontend analogue of detailHref.pickShrineId) so the rule lives in one
     place rather than per component.
     -> DESIGNED. See docs/audit/shared-shrine-identity-resolver-design.md
        (resolver contract, public_strict / registered_compat policies,
        prohibited fields, normalization, fail-closed conflict rule,
        implementation location, consumer classification).
        Design only — not implemented, no consumer migrated. F-4 implements.

F-4  Normalize ShrineDetailArticle.tsx L368 precedence to shrine_id-first.

F-5  Collapse the 16 backend `shrine_id or id` sites onto
     _candidate_shrine_id() once F-2 settles whether `id` may be dropped.

F-6  place_id shadow-identity hardening: make get_or_create_shrine_by_place_id
     dedupe against registered Shrines whose place_ref is NULL, and backfill
     place_ref links. Separate from Compass / Concierge parity (§5).

F-7  Add a regression test asserting id == shrine_id == Shrine.id at the
     concierge_chat_candidates.py emission site, so the invariant §4.5 relies on
     is enforced rather than assumed.
```

Suggested order: `F-7` → `F-2` → `F-1` → `F-3` / `F-4` → `F-5`. `F-6` is independent.

## 9. Required Statements

```text
1. No runtime behavior was changed.
2. The Shrine model was not modified.
3. Compass runtime was not modified.
4. Concierge runtime was not modified.
5. The Compass `id` fallback was NOT removed.
6. No API response shape was changed.
7. No database, schema, or migration change.
8. Recommendation / Ranking were not changed.
9. Canonical / Navigation coordinates were not changed.
10. The only committed change is this document.
```

## 10. STOP

```text
IDENTITY_AUTHORITY   = Shrine.id
PUBLIC_IDENTITY_KEY  = shrine_id
CLASSIFICATION       = PARTIALLY_SHARED
RUNTIME_CHANGE       = NONE
FOLLOW_UPS_RECORDED  = F-1 .. F-7
FOLLOW_UPS_STARTED   = NONE
```

Next action requires a Mother Ship instruction naming a follow-up.

---

## 9. Current State Update — F-1 (Compass `id` fallback removed)

Recorded at: `2026-09-23`. 本節は §1–§8 の監査記録を置き換えるものではなく、
その後の実装によって変化した **現在状態** を追記するもの。

### 9.1 What changed

```text
§2.1 / §4.2 / §6.3 が記録した Compass 側の状態:

  BEFORE (audited state, PR #2948 時点)
    CompassRecommendationsSection.tsx
      L35  const shrineId = rec.shrine_id ?? rec.id;   (analytics)
      L58  const shrineId = rec.shrine_id ?? rec.id;   (navigation)

  AFTER (current, F-1)
      const shrineId = rec.shrine_id;                  (both sites)
```

```text
COMPASS_NAVIGATION_USES_SHRINE_ID_ONLY = YES
COMPASS_ANALYTICS_USES_SHRINE_ID_ONLY  = YES
COMPASS_ID_FALLBACK                    = REMOVED
```

### 9.2 R-9 compliance updated

§6.3 は `R-3`（「登録済み Shrine は shrine_id で解決する」）を `PARTIAL`、
`R-9`（「generic recommendation `id` を identity authority にしない」）を
`VIOLATED` と記録していた。その根拠は Compass 側の fallback だった。

```text
Compass Monthly について:
  R-3 = SATISFIED
  R-9 = SATISFIED
```

Concierge 側および §4.1 / §4.4 が列挙したその他の fallback 箇所は **未変更**。
`F-1` は Compass Monthly のみを対象とし、Concierge / Consultation History /
Places / Favorites の identity 挙動には触れていない。したがって §7 の
`PARTIALLY_SHARED` という全体分類は、Compass 以外の箇所が残る限り変わらない。

### 9.3 Scope note

```text
F-1 changed   : apps/web/src/features/compass/components/CompassRecommendationsSection.tsx
F-1 preserved : `id` in CompassRecommendation / Public Projection / OpenAPI / API payload
                id = COMPATIBILITY_FIELD
                id = NOT_IDENTITY_AUTHORITY
                id = STILL_PRESENT_IN_PUBLIC_CONTRACT
F-1 untouched : Concierge fallbacks, Consultation History, Places / Favorites,
                F-3 / F-4 / F-5 / F-6
```

実装の詳細と回帰の証跡は
`docs/audit/compass-shrine-id-presence-audit.md` §14。

## 10. Current State Update — F-4 (shared Web resolver implemented)

> 追記。§1–§9 の歴史的記録は書き換えない。

```text
SHARED_WEB_RESOLVER = apps/web/src/lib/identity/resolveShrineId.ts
F4_STATUS           = PARTIAL_SAFE_MIGRATION
```

`F-3`（#2957）が設計した resolver を `F-3.1` で `ShrineIdentityResolution`
（`resolved` / `absent` / `invalid` / `conflict`）へ拡張したうえで実装し、
Web の**現行 live 経路**のみを移行した。

### 10.1 §4.4 "Other frontend identity readers" の現在地

§4.4 の一覧は `F-1` 時点のものであり、行番号ごとそのまま保持する。現在の状態:

```text
移行済み（generic `id` を identity に使わない）
  features/compass/components/CompassRecommendationsSection.tsx   （F-1 → F-4 で共有化）
  features/concierge/detailHref.ts                                （pickShrineId 削除）
  features/concierge/hooks.ts                                     （analytics 2箇所）
  lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts    （local resolveShrineId 削除）

未変更 — 履歴 snapshot 互換のため意図的に保留
  ConsultationHistoryDetailView.tsx      L41
  lib/concierge/buildPreviousConsultationSummary.ts  L16
  lib/concierge/pickReasonFromThread.ts  L20
  app/shrines/[id]/page.tsx              L370

未変更 — F-6（place_id shadow identity）経路
  lib/api/places.ts                      L47
  components/PlaceCardClientActions.tsx  L29
  app/shrines/resolve/page.tsx           L38

未変更 — 違反ではない
  components/shrine/detail/ShrineDetailArticle.tsx  L368
```

```text
F4_HISTORICAL_SNAPSHOT_MIGRATION = DEFERRED
REASON = PRE_CUTOVER_ID_ONLY_SNAPSHOT_COMPATIBILITY_NOT_PROVEN
```

### 10.2 §7 分類への影響

```text
分類は PARTIALLY_SHARED のまま変わらない。
```

`F-4` は Web の live 経路のみを共有実装へ寄せた。§4.1 の backend 16 sites
（`F-5`）、place_id shadow identity（`F-6`）、履歴 snapshot consumer は未変更で
あり、Compass と Concierge が**完全に同一の identity 実装を共有している**
状態にはまだ到達していない。

実装の詳細と回帰の証跡は
`docs/audit/shared-shrine-identity-resolver-design.md` §13（F-3.1）/ §14（F-4）。

## 11. Current State Update — F-5B (backend shared resolver implemented)

> 追記。§1–§10 の歴史的記録は書き換えない。

```text
BACKEND_SHARED_RESOLVER = backend/temples/domain/shrine_identity.py
CANONICAL_RESOLVER_MODE = STRICT_FAIL_CLOSED
VALID_SHRINE_ID         = POSITIVE_INTEGER_ONLY
F5B_STATUS              = IMPLEMENTED
```

### 11.1 §4.1 "Backend `shrine_id or id` sites" の現在地

§4.1 は `BACKEND_FALLBACK_SITES = 16 / 8 files` と記録していた。`F-5A`（#2960）
はそれが**不足**であり実数が 22 / 13 であることを確定した。§4.1 の一覧は
当時の記録としてそのまま保持する。現在の状態:

```text
移行済み（共有 resolver へ集約）   16 site
  concierge_chat_candidates.py / concierge_chat_pool.py（4）
  concierge_candidate_utils.py / concierge_chat_ranking.py
  concierge_chat.py（2: #8 #9）/ domain/weekly_presentation.py
  concierge_chat_observation.py（3）
  recommendation_quality_measurement.py / recommendation_score_components.py
  management/commands/export_recommendation_output_snapshot.py

未変更 — 突合 key（identity resolver ではない）   2 site
  concierge_chat.py:636, 646

未変更 — 履歴 snapshot 互換                      2 site
  api/views/concierge.py:140 / journey_timeline.py:130

未変更 — dead code（importer 0 件）              2 site
  concierge_candidate_normalize.py:28, 31
```

### 11.2 §4.5 の警告が test fixture で現実化していた

§4.5 は次の露出を記録していた。

```text
「将来の producer が `id` に ranking index / list position を入れたら、
  Compass navigation が静かに別 Shrine を指す」
```

`F-5B` の移行中に、`test_concierge_chat_observation` の fixture が
まさにその形（`{"id": 1, "shrine_id": 101}` — `id` が rank）であることが
露見した。旧 `or` 実装が `shrine_id` を黙って採用していたため観測されて
いなかった。

```text
PRODUCTION_DATA_AFFECTED = NOT OBSERVED
  F-7 invariant 下の live candidate では id と shrine_id は一致する。
  影響したのは invariant に違反していた test fixture のみ。
```

### 11.3 §7 分類への影響

```text
分類は PARTIALLY_SHARED のまま変わらない。
```

Web（`F-4`）と backend（`F-5B`）はそれぞれ共有 resolver を持つが、履歴
snapshot consumer（Web 4 件 / backend 2 件）、突合 key 2 件、place_id
shadow identity（`F-6`）が未統合のまま残る。

実装の詳細と回帰の証跡は
`docs/audit/backend-shrine-identity-fallback-consolidation.md` §10–§19。

## 12. Current State Update — F-6A (place_id shadow identity audited)

> 追記。§5 / §8 を含む §1–§11 の歴史的記録は書き換えない。

```text
F6A_STATUS                  = AUDITED
PLACE_ID_IDENTITY_AUTHORITY = NO
RUNTIME_CHANGE              = NONE
```

### 12.1 §5「place_id は登録済み Shrine identity の代わりになるか」の現在地

§5 の結論（place_id は identity authority ではない）は変わらない。`F-6A` は
その**再発防止がまだ実装されていない**ことを確定した。

```text
CURRENT_WRITER = backend/temples/services/places.py::get_or_create_shrine_by_place_id
COLLISION_DETECTION_PRESENT = NO
POST_0100_SHADOW_RECREATION_POSSIBLE = YES
```

migration 0100 は shadow Shrine 101/103/104 を削除したが、docstring の
`DROP_SHADOW_ONLY` の通り **place_ref を primary へ転送していない**。3 つの
PlaceRef 行は孤立したまま残っており、同じ place_id を再 resolve すると
新しい shadow 行が作られる。呼び出し列は
`docs/audit/place-id-shadow-identity-hardening.md` §2.2。

構造的な理由として、`Shrine` の部分 unique 制約 2 つ
（`uq_shrine_name_loc` / `uq_shrine_name_addr_when_loc_null`）はどちらも
`place_ref__isnull=True` を条件に持つため、**place_ref を持つ行は
name/address の一意性から除外される**（同 §1.6）。

### 12.2 §8「Future Implementation Follow-ups」の現在地

```text
F-1  完了（#2956）
F-3  完了（#2957）
F-4  完了（#2959）
F-5A 完了（#2960）
F-5B 完了（#2961）
F-6A 完了（本 PR。監査・設計のみ）
F-6B 未着手（実装）
```

### 12.3 新たに観測した writer（§4 の一覧に無い）

```text
api/views/shrines_nearby.py:40
  Shrine.objects.update_or_create(place_ref=pref)
  -> get_or_create_shrine_by_place_id と同じ shadow 形状

  ただし到達不能:
    ルーティング参照 0 件
    search_nearby_places が未定義（呼び出し 1 箇所のみ、import も定義も無い）

  SHRINES_NEARBY_REACHABLE = NO
  -> F-6B の対象外。削除可否は別決定
```

### 12.4 §7 分類への影響

```text
分類は PARTIALLY_SHARED のまま変わらない。
```

`F-6A` は docs のみであり、runtime の identity 挙動を一切変えていない。

詳細は `docs/audit/place-id-shadow-identity-hardening.md`。
