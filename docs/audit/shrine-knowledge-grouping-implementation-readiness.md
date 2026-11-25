> **Status: Implementation-readiness audit only.** No production code, UI, Backend, Serializer,
> Knowledge Model, DB, migration, Ranking, or Recommendation Authority was changed to produce this
> document (`git diff` on application code = 0). This document does not reopen whether Presentation
> Grouping is allowed in principle — that is settled by
> [`shrine-knowledge-contract.md`](../knowledge/shrine-knowledge-contract.md)'s "Presentation
> Groupingの契約" section (PR #2466, merged). This document also does not authorize starting the
> implementation it scopes.

# Shrine Knowledge Presentation Grouping — Implementation Readiness Audit

Each finding is labeled **FACT** (read directly from code, with citation), **INFERENCE** (a
conclusion drawn from FACTs, stated as such), or **PROPOSAL** (a design idea for the future PR, not
implemented, not authorized here).

## 1. Purpose and Scope

The prior contract clarification (PR #2466) decided *that* Presentation Grouping — rendering
independent Facts sharing an exact, already-canonical `history_type` under one shared UI heading,
without merging content or inferring new categories — is allowed, subject to constraints. This audit
answers a narrower, implementation-facing question: **can that be built today as a frontend-only,
additive presentation change, with Fact identity and per-Fact provenance genuinely preserved**, or
does something about the current data/component boundary make that harder than the contract
discussion assumed. It produces enough file:line detail for a future PR-B to be scoped as one
self-contained task, without starting that work here.

## 2. Governing Contract

**FACT**: [`docs/knowledge/shrine-knowledge-contract.md`](../knowledge/shrine-knowledge-contract.md)
"Presentation Groupingの契約" section states the decision `PRESENTATION GROUPING ALLOWED WITH
CONSTRAINTS`, with the operative distinction:

- **A. Data Merge** (prohibited) — multiple Facts become one Fact.
- **B. Semantic Auto-Grouping** (prohibited) — the system infers thematic relatedness from Fact text.
- **C. Presentation Grouping** (conditionally allowed) — independent Facts sharing an already-exact
  canonical field, rendered under a shared visual heading, with identity/text/type/source/evidence
  unchanged, `disputed` Facts excluded.

This audit takes that decision as settled and does not re-derive it.

## 3. Current Data-Flow Map

**FACT** — traced end to end, file:line:

```
Backend Model
  ShrineHistory (backend/temples/models.py:523-572), ShrineDeity (models.py:480-521)
  Meta.ordering = ["sort_order", "id"] on both (models.py:509-513, 561-565)
        ↓
Serializer
  ShrineDetailSerializer.get_histories()/get_deities()
  (backend/temples/api/serializers/shrine.py:214-241)
  — filters via evidence_gate.decide_detail_display_state(), does NOT re-sort
  ShrineHistorySerializer (shrine.py:85-108): fields = id, history_type, title, content,
    period_text, event_date, sort_order, verification_status, confidence, sources
  ShrineDeitySerializer (shrine.py:59-82): fields = id, display_name, canonical_name, role,
    sort_order, verification_status, confidence, sources
        ↓
Frontend raw API type
  apps/web/src/lib/api/types.ts:34-58
  ShrineDeity { id, display_name, canonical_name, role, sort_order, verification_status,
    confidence, sources: ShrineKnowledgeSource[] }
  ShrineHistory { id, history_type, title, content, period_text, event_date, sort_order,
    verification_status, confidence, sources: ShrineKnowledgeSource[] }
  ShrineKnowledgeSource (types.ts:22-30): { id, source_type, title, publisher, url,
    verification_status, confidence }
        ↓
Shrine object fetch
  apps/web/src/app/shrines/[id]/page.tsx:204 (getShrineDetailServer) → `s`/`shrine`
        ↓
ViewModel construction  ***id and sources are dropped here — see §6/§7***
  buildShrineDetailModel.ts:1683: factSection = buildShrineFactSection(shrine)
  apps/web/src/lib/shrine/buildShrineFactSection.ts:41-74
        ↓
Shrine Detail model
  buildShrineDetailModel.ts return value, `factSection: DetailFactSection | null` (line 1717)
        ↓
Rendering
  ShrineDetailArticle.tsx:689: {factSection ? <ShrineFactSection section={factSection} /> : null}
  apps/web/src/components/shrine/detail/ShrineFactSection.tsx:75-91 (outer section) →
    DeityList (22-39) / HistoryList (41-73)
```

## 4. Knowledge Renderer Map

**FACT**:

| Layer | File | Role |
|---|---|---|
| Page/container | `apps/web/src/app/shrines/[id]/page.tsx` | Fetches `shrine` (with `.deities`/`.histories`), calls `buildShrineDetailModel()`, renders `<ShrineDetailArticle {...model} .../>` (`page.tsx:482-503`, from the prior audit's trace) |
| ViewModel builder | `apps/web/src/lib/shrine/buildShrineDetailModel.ts:1683` | Calls `buildShrineFactSection(shrine)`, attaches result as `factSection` |
| Fact ViewModel function | `apps/web/src/lib/shrine/buildShrineFactSection.ts` | API shape → `DetailFactSection` |
| Types | `apps/web/src/components/shrine/detail/types.ts:55-78` | `FactDisplayState`, `DetailFactDeity`, `DetailFactHistoryItem`, `DetailFactSection` |
| Section component | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx:689` | Conditionally renders `<ShrineFactSection>` |
| Fact section component | `apps/web/src/components/shrine/detail/ShrineFactSection.tsx` | Renders heading + `DeityList` + `HistoryList` |
| Individual Fact card | `ShrineFactSection.tsx:41-73` (`HistoryList`), `22-39` (`DeityList`) | 1 array item → 1 pill (deity) or 1 bordered card (history) |

## 5. Fact List Source

**FACT**: The displayed Facts come from `shrine.deities`/`shrine.histories` — two plain arrays on the
`Shrine` API object, typed `ShrineDeity[]`/`ShrineHistory[]` (`api/types.ts:83-84`). Each array item
is independent (no nesting, no shared parent object beyond the array itself).

| Item | API field | Frontend type | Normalization layer | Identity present in raw type? |
|---|---|---|---|---|
| Deity | `deities` | `ShrineDeity` (`api/types.ts:34-43`) | `buildShrineFactSection.ts:52-56` | Yes — `id: number` (`types.ts:35`) |
| History | `histories` | `ShrineHistory` (`api/types.ts:47-58`) | `buildShrineFactSection.ts:58-66` | Yes — `id: number` (`types.ts:48`) |

**FACT**: the UI **already receives** enough metadata (`id`, `history_type`, `sources`) at the
`shrine` object fetch layer to group without any re-fetch — the gap (§6/§7) is that the ViewModel
mapping (`buildShrineFactSection.ts`) does not currently carry `id`/`sources` through to the
component boundary, not that the data isn't available.

## 6. `history_type` Propagation Trace

**FACT**, layer by layer:

1. Model: `ShrineHistory.history_type` (`models.py:536`, `CharField(max_length=32,
   choices=HISTORY_TYPE_CHOICES)`, required, no default).
2. Serializer: `ShrineHistorySerializer.Meta.fields` includes `"history_type"` (`shrine.py:92-103`).
3. Frontend API type: `ShrineHistory.history_type: string` (`api/types.ts:49`).
4. ViewModel: `buildShrineFactSection.ts:59` — `history_type: history.history_type` (passed through
   unchanged) and `60` — `history_type_label: resolveHistoryTypeLabel(history.history_type)` (a
   **label lookup**, not a transformation of the value itself; `HISTORY_TYPE_LABELS`,
   `buildShrineFactSection.ts:10-17`).
5. Type: `DetailFactHistoryItem.history_type: string` (`types.ts:64`) — present at the ViewModel
   type boundary.
6. Render boundary: `ShrineFactSection.tsx:52-54` reads `history.history_type_label` (the label, not
   the raw value) and displays it as a small text span per card. The raw `history_type` value itself
   reaches the component's props (`history.history_type`, part of the object passed in) but is not
   currently read by the render function for anything beyond the label lookup already done upstream.

**Explicit answers**:

1. Present in the API response? **Yes** (`shrine.py:92-103`).
2. Preserved in frontend state/ViewModel? **Yes**, unchanged (`buildShrineFactSection.ts:59`).
3. Available at the exact rendering boundary? **Yes** — it is a field on every object in
   `section.histories`, which `ShrineFactSection`/`HistoryList` receives as props
   (`ShrineFactSection.tsx:41`).
4. Normalized or transformed? **No** — the value itself is copied verbatim; only a **display label**
   is derived from it via a fixed lookup table, the value is not altered.
5. Can exact-value equality be used safely? **Yes** — `HISTORY_TYPE_LABELS` (`buildShrineFactSection.ts:10-17`)
   already keys off `history_type` by exact string equality for the existing label lookup; grouping
   by the same exact-match key is the same operation already performed today, just used for a
   `Record`/`groupBy` instead of a single lookup.

## 7. Current `1 Fact = 1 Card` Rendering Behavior

**FACT** (`ShrineFactSection.tsx:41-73`, `HistoryList`):

```tsx
{histories.map((history, index) => (
  <div key={`${history.title}:${index}`} className="...">
    <span>{history.history_type_label}</span>
    {history.title ? <h4>{history.title}</h4> : null}
    {history.period_text ? <span>{history.period_text}</span> : null}
    {history.displayState === "disputed" ? <DisputedBadge /> : null}
    {history.content ? <p>{history.content}</p> : null}
  </div>
))}
```

This is exactly `facts.map((fact) => <FactCard ... />)` — a flat, unconditional 1:1 map, no grouping,
no aggregation, no cap.

- **Grouping level**: none (flat list).
- **Sort order**: `buildShrineFactSection.ts:58` — `sortBySortOrder(histories)` (`sort_order`
  ascending, `buildShrineFactSection.ts:32-34`) before the array reaches the component. Same for
  deities (`buildShrineFactSection.ts:52`).
- **React key / identity**: `${history.title}:${index}` (`ShrineFactSection.tsx:48`) and
  `${deity.display_name}:${index}` (`ShrineFactSection.tsx:29`) — **positional, not database-id
  based**. The raw API `id` (present on `ShrineHistory`/`ShrineDeity`, §5) is not used here because
  it is not present on `DetailFactHistoryItem`/`DetailFactDeity` at all (§6/§9 below).
- **Section headings**: fixed strings "御祭神" (`ShrineFactSection.tsx:25`) and "由緒・歴史"
  (`ShrineFactSection.tsx:44`) — not derived from data, not per-type.
- **Source/evidence relationship**: **FACT — sources are not rendered anywhere in the current UI**,
  at either the per-Fact or per-section level. `HistoryList`/`DeityList` never read `.sources`
  because `DetailFactHistoryItem`/`DetailFactDeity` don't carry that field at all (§9). This is the
  central finding for §10.

## 8. Frontend-Only Feasibility for the Grouping Transform Itself

**Evaluated transform**: `[{history_type: X}, {history_type: X}, {history_type: Y}]` →
`{X: [...], Y: [...]}` (or an equivalent ordered grouping structure), for display purposes only.

**FACT**: `history_type` is already present, unmodified, at every layer including the ViewModel type
(§6). No new API field, no Backend change, no Serializer change, no DB change, and no Knowledge Model
change is needed to perform this specific transform — it operates entirely on data the frontend
already has in hand by the time `buildShrineFactSection()` runs.

**Decision: FRONTEND-ONLY WITH SMALL CONTRACT GAP** (not `FRONTEND-ONLY CONFIRMED` outright).

**Reason**: the grouping transform itself needs nothing new. But the contract (§2) requires more than
"the transform is safe" — it requires **Fact identity** and **per-Fact provenance** to remain
independently traceable in the *shipped* UI. §9/§10 below find that the current `DetailFactHistoryItem`/
`DetailFactDeity` ViewModel types do not carry `id` or `sources` at all — both are dropped between the
raw API type (§5, which has them) and the ViewModel (§6). This is itself a frontend-only,
additive gap (the data already crosses the API boundary — nothing needs to newly reach the frontend
from the Backend), but it is a real gap in the *current* code that a literal implementation of
grouping-only, without also closing it, would leave unresolved: a grouped UI could satisfy "don't
merge Facts" while still having no stable way to prove per-Fact source attribution to a reader,
because nothing shows sources today, grouped or not.

## 9. Fact Identity Preservation

**FACT**: `ShrineHistory.id`/`ShrineDeity.id` are present at the raw API type (`api/types.ts:35,48`)
but are **not** copied into `DetailFactHistoryItem`/`DetailFactDeity` by
`buildShrineFactSection.ts:52-66` (compare the object literals there against `api/types.ts:34-58` —
`id` is the one field present on every raw type and absent from every ViewModel type,
`types.ts:57-71`).

**FACT**: Today's identity mechanism is the React key `${title}:${index}` /
`${display_name}:${index}` (`ShrineFactSection.tsx:29,48`) — positional plus display text, not a
database identifier.

**Can grouping preserve the individual Fact object untouched?** **Yes** — grouping (Operation C) only
reorders/partitions the existing array into sections; it does not require creating, merging, or
mutating any Fact object. The structure

```
group container
  ├─ original Fact A
  └─ original Fact B
```

is achievable by `Object.groupBy`/`reduce`-style partitioning of the existing `histories` array,
retaining each `DetailFactHistoryItem` object by reference — no new synthetic "merged Fact" object is
required or proposed.

**Gap, not a blocker**: without `id` wired through, the *implementation* of a grouped list would need
to keep using a positional/title-based key inside each group, which is workable (title remains
associated with its own Fact regardless of which group it renders in) but is less robust than an
id-based key, particularly if a future PR wants list-reordering or animation stability across
re-renders. **PROPOSAL**: add `id: number` to `DetailFactHistoryItem`/`DetailFactDeity`
(`types.ts:57-71`) and thread it through `buildShrineFactSection.ts:52-66` (the raw value is already
in scope there — `deity.id`/`history.id` — simply not copied into the returned object literal),
using `id` as the React key post-grouping. This is additive, frontend-only, no Backend/API change.

## 10. Provenance Preservation

**FACT**: `ShrineKnowledgeSource[]` (`sources`) is present on the raw API types
(`ShrineDeity.sources`, `ShrineHistory.sources`, `api/types.ts:42,57`) — confirmed sent by the
Backend (`ShrineDeitySerializer`/`ShrineHistorySerializer.Meta.fields` both include `"sources"`,
`shrine.py:75,103`, resolved per-Fact via `get_sources()`/`_fact_ready_sources()`,
`shrine.py:44-52,79-82,107-110` — each Fact's sources are its own querySet, never shared or unioned
across Facts at the Backend layer).

**FACT**: `buildShrineFactSection.ts:52-66` does **not** copy `sources` into
`DetailFactDeity`/`DetailFactHistoryItem`. `types.ts:57-71` confirms neither ViewModel type has a
`sources` field. `ShrineFactSection.tsx` (both `DeityList` and `HistoryList`) never reads or renders
any source/evidence information — **sources are not displayed anywhere in the current Shrine Detail
Knowledge UI, independent of grouping.**

**Can every displayed Fact remain independently attributable after grouping?** At the **data** level:
yes, unconditionally — since sources are never merged or shared per-Fact at the Backend or in the raw
API type, and grouping doesn't touch that structure, there is no mechanism by which grouping could
create a "Group X → shared ambiguous sources" situation. At the **currently-shipped UI** level: the
question is not yet answerable by observing the app, because no source is shown for any Fact today,
grouped or ungrouped — there is nothing to check against. This is the same gap identified in §8/§9:
closing it (wiring `sources` through, analogous to the `id` proposal) is what would let a future PR
*demonstrate* per-Fact provenance rather than merely not-violate it structurally.

**PROPOSAL**: add `sources: ShrineKnowledgeSource[]` (or a minimal display-safe subset of it, e.g.
`{title, url, source_type}[]`) to `DetailFactHistoryItem`/`DetailFactDeity`, threaded through
`buildShrineFactSection.ts` the same way as `id`. Frontend-only, additive, no Backend/API change
(the data is already sent).

## 11. `disputed` Handling

**FACT**: `verification_status` → `FactDisplayState` (`"full" | "disputed"`) is already computed
per-Fact in the ViewModel — `resolveFactDisplayState()` (`buildShrineFactSection.ts:28-30`), applied
individually to every deity (`buildShrineFactSection.ts:55`) and every history
(`buildShrineFactSection.ts:65`). The result, `displayState`, is present on both
`DetailFactDeity`/`DetailFactHistoryItem` (`types.ts:60,70`) — i.e. **already at the exact render
boundary**.

**Can the frontend reliably exclude `disputed` Facts from ordinary Presentation Grouping?** **Yes** —
`history.displayState === "disputed"` (or `!== "disputed"`) is already the exact check
`ShrineFactSection.tsx:61` uses today to decide whether to render `<DisputedBadge />`. A future
grouping implementation can partition on `displayState` first (disputed vs. not), applying grouping
only to the non-disputed subset and rendering `disputed` items exactly as today (ungrouped,
individually) — no new metadata, no heuristic, no inference required.

**Intended behavior, confirmed achievable with existing data**: ordinary Facts group by exact
`history_type`; `disputed` Facts remain individually rendered per the existing "Shrine Detail
Multi-View Contract" (unaffected by this audit).

## 12. Current Fact Ordering Source of Truth

**FACT** (re-verified by direct read of the serializer, not inferred): `ShrineDetailSerializer.get_histories()`/
`get_deities()` (`shrine.py:214-241`) iterate `obj.histories.all()`/`obj.deities.all()` in a plain
list comprehension that only **filters** (via `evidence_gate.decide_detail_display_state()`) — there
is no `.order_by(...)` call in either method. Django's default queryset ordering for an unordered
`.all()` call is the related Model's `Meta.ordering`. `ShrineHistory.Meta.ordering = ["sort_order",
"id"]` (`models.py:561-565`) and `ShrineDeity.Meta.ordering = ["sort_order", "id"]`
(`models.py:509-513`).

**Source of truth: the `ShrineHistory`/`ShrineDeity` Model's `Meta.ordering` (`sort_order` ascending,
then `id` ascending as a tiebreaker)** — not queryset-default insertion order, not serializer
reordering, not frontend-invented sorting. The frontend's `sortBySortOrder()`
(`buildShrineFactSection.ts:32-34`) re-sorts by `sort_order` again defensively, redundant with but
consistent with the Backend order (it does not add an `id`-tiebreaker, a minor inconsistency with the
Backend's compound sort key, not relevant to grouping safety since `sort_order` collisions are
expected to be rare and are already Backend-tiebroken).

## 13. Proposed Grouped Ordering Rule (Design Only)

**PROPOSAL — group order**: preserve the existing canonical `history_type` enum declaration order
from `HISTORY_TYPE_CHOICES` (`models.py:526-533`: `official_origin, founding, historical_event,
tradition, regional_context, editorial_summary`) as the section order, rather than inventing a new
ordering (e.g. by first-occurrence in the array, or alphabetically). This is the one ordering already
codified as canonical (it is the enum's own declared order, used consistently for
`HISTORY_TYPE_LABELS`'s key order in `buildShrineFactSection.ts:10-17` today), so it requires no new
judgment call.

**PROPOSAL — Fact order inside a group**: preserve the existing `sort_order` (then `id`) order (§12)
within each group — i.e., grouping should **partition**, not **re-sort**, the already-ordered array.
This directly satisfies the task's instruction to prefer existing canonical order over inventing a
new one.

**No safe canonical group order needs to be invented** — `HISTORY_TYPE_CHOICES`'s declaration order
already exists and is already used as a canonical key order elsewhere in the same file
(`buildShrineFactSection.ts:10-17`). Do not derive group or item order from `title`/`content` text,
consistent with the task's constraint.

## 14. Backend / Serializer / Model / Migration Impact

**11. Backend code change required?** **NO.** All data needed for grouping (`history_type`) and for
closing the identity/provenance gaps (`id`, `sources`) is already computed and returned by
`ShrineDetailSerializer` (§3, §6, §9, §10). No new Backend logic, endpoint, or field is needed.

**12. Serializer change required?** **NO.** `ShrineHistorySerializer`/`ShrineDeitySerializer`
(`shrine.py:59-108`) already include every field a frontend-only implementation would need
(`id`, `history_type`, `sources`, plus the fields already flowing through). Nothing needs to be
added to the API response.

**13. Knowledge Model change required?** **NO.** `history_type` (the proposed grouping key) already
exists as a Model field with a fixed, canonical enum (`models.py:526-533`). No new Fact field,
relation, grouping entity, or category Model is required — this audit's evidence supports the
expected `NO Knowledge Model change` conclusion; nothing found contradicts it.

**14. Migration required?** **NO.** No Model field is being added, removed, or altered — §11-§13
above establish that every value needed already exists in the DB/Model as-is.

## 15. Existing Tests

**FACT** — files and what they protect:

| File | Protects | Modification needed for PR-B? |
|---|---|---|
| `apps/web/src/lib/shrine/__tests__/buildShrineFactSection.test.ts` | ViewModel conversion: `displayState` derivation (lines 56-133), `sort_order`/content preservation (135-163), **"複数disputed Factを自動統合・自動グルーピングせず個別に保持する"** (165-184) — direct precedent for the disputed-non-grouping guarantee at the ViewModel layer | Extend — add cases for `id`/`sources` propagation (once §9/§10's gap is closed) and for grouping-key extraction from same-type Facts |
| `apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.test.tsx` | UI rendering: full vs. `disputed` display (24-166), **"複数disputed Historyは自動統合・自動グルーピングされず個別表示される"** (98-134, asserts no auto-generated "複数の説"/"複数説" text and exactly 2 independent disputed badges), Design Token references (168-183) | Extend — add grouped-rendering assertions (shared heading present, each Fact's own card still independently present under it) |
| `apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.integration.test.tsx` | API-response-shaped fixture → ViewModel → UI, end to end (PR-D1). **Its fixture already contains two `history_type: "tradition"` Facts** (ids 21/22, lines 89-110) — though both are `disputed` in this fixture, it is the closest existing same-type-multi-Fact precedent, and already proves "複数disputed Factが別々のViewModel itemとして保持される（自動統合されない）" (148-154) and the render-layer equivalent (166-177, 179-190) | Extend — add a **non-disputed** same-`history_type` multi-Fact case (the scenario grouping actually targets) alongside the existing disputed one |
| `apps/web/src/components/shrine/detail/__tests__/ShrineDetailArticle.test.tsx` — `"神社について(Fact) Section"` describe block (line 736) | `factSection=null` → no render (757-761); basic deity+history render (763-798); **"複数Historyをすべて表示する（品川神社相当）"** (800-846) — **this is the exact same-canonical-type multi-Fact case**: two Facts both with `history_type: "historical_event"` (lines 818-826, 827-835), both `displayState: "full"` (non-disputed), asserting all three history titles render | **This is the primary test to extend for PR-B** — after grouping, assert the two `"historical_event"`/"歴史" Facts render under one shared heading while the "founding"/"創始" Fact renders under its own, and all three original titles/contents remain present unchanged |

## 16. Required Future Test Cases (Design Only, Not Implemented)

| # | Case | Required? | Note |
|---|---|---|---|
| 1 | One Fact in one canonical type | Yes | Baseline — a single-item group must still render sensibly (with or without a group heading for a group of one — a PR-B design choice, not decided here) |
| 2 | Two Facts, same exact `history_type` | Yes | Core case — extends the existing "品川神社相当" test (§15) |
| 3 | Facts with different `history_type` | Yes | Confirms groups don't merge across types — already partially covered by "品川神社相当" (founding vs. historical_event) |
| 4 | History and Tradition kept separate | Yes | Specific instance of #3, matches the task's original example |
| 5 | Each Fact retains its own Source | Yes, **conditional on §10's gap being closed first** — cannot be asserted meaningfully until `sources` reaches the ViewModel | Add once the PROPOSAL in §10 ships |
| 6 | Each Fact retains its own identity/key | Yes, **conditional on §9's gap being closed first** for an `id`-based assertion; a positional/title-based version is possible today | Add id-based version once §9's PROPOSAL ships |
| 7 | `disputed` Fact is not folded into normal group | Yes | Extends `ShrineFactSection.integration.test.tsx`'s existing disputed-pair fixture (§15) with a mixed disputed+non-disputed-same-type case |
| 8 | Original Fact order remains stable | Yes | Assert group-internal order matches `sort_order` (§13's PROPOSAL), not re-derived |
| 9 | Missing/unknown `history_type` | Yes | `resolveHistoryTypeLabel()` already has a fallback (`buildShrineFactSection.ts:20`: `HISTORY_TYPE_LABELS[historyType] ?? historyType`) — confirm grouping handles an unrecognized value gracefully (e.g., its own group keyed on the raw string, not dropped/crashed) |
| 10 | No Fact content is merged or rewritten | Yes | Direct regression guard against Operation A, mirrors existing `"sort_orderを維持し、Fact本文...を変更しない"` (`buildShrineFactSection.test.ts:135`) |
| 11 | Mobile rendering with multiple Facts in one section | **Not applicable** | **FACT**, confirmed in the prior audit (`shrine-detail-explanation-knowledge-responsibility.md` §2, citing `shrine-knowledge-contract.md`'s "Mobile Current State" section): Mobile's `ShrineApiResponse` type does not define `deities`/`histories`/`verification_status` at all, and Mobile does not render Knowledge Facts in any form today. There is no Mobile Fact rendering to add a grouped-rendering test for; this case is out of scope until Mobile Knowledge Fact support (母艦判断項目 #23, unrelated to this audit) is separately decided |

## 17. Exact PR-B File Scope

**FACT-based, not guessed** — every file below is one already touched by the existing Fact
data-flow (§3/§4) or its existing tests (§15).

**Required (production code)**:

- `apps/web/src/components/shrine/detail/types.ts` — extend `DetailFactHistoryItem`/
  `DetailFactDeity` with `id`/`sources` (§9/§10 PROPOSALs); add whatever grouped-section shape
  `DetailFactSection` needs (e.g. `historyGroups: { historyType: string; label: string; items:
  DetailFactHistoryItem[] }[]` alongside or instead of the flat `histories` array — exact shape is a
  PR-B design decision, not made here).
- `apps/web/src/lib/shrine/buildShrineFactSection.ts` — thread `id`/`sources` through; add the
  grouping/partitioning logic (by `history_type`, excluding `disputed`, per §11/§13).
- `apps/web/src/components/shrine/detail/ShrineFactSection.tsx` — render grouped headings instead
  of (or in addition to) the flat `HistoryList`; keep `DisputedBadge`/individual-card structure
  otherwise unchanged; render source/evidence per Fact if §10's PROPOSAL ships in the same PR.

**Test-only**:

- `apps/web/src/lib/shrine/__tests__/buildShrineFactSection.test.ts`
- `apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.test.tsx`
- `apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.integration.test.tsx`
- `apps/web/src/components/shrine/detail/__tests__/ShrineDetailArticle.test.tsx` (extend the
  "神社について(Fact) Section" describe block, §15/§16)

**Explicitly untouched** (confirmed by §3's full data-flow trace and this audit's investigation
scope):

- Backend (`backend/temples/**`) — confirmed no change needed, §14.
- Serializers (`backend/temples/api/serializers/shrine.py`) — confirmed no change needed, §14.
- Models / migrations — confirmed no change needed, §14.
- Ranking / Recommendation Authority (`concierge_chat_ranking.py`, `recommendation-signal-authority.md`
  scope) — not part of the Fact data-flow traced in §3 at all; Knowledge Facts are Explanation-only
  per that doc's existing Decision A (unchanged, out of scope here).
- Result Hero / Compact (`ConciergeSectionsRenderer.tsx`, `ConciergeTopRecommendationHero.tsx`) —
  confirmed in the prior audit (`shrine-detail-explanation-knowledge-responsibility.md` §14) to have
  zero reference to `deities`/`histories`/Fact rendering; this PR's scope (§ Fact section only)
  cannot reach those files.
- Deep Dive — unrelated feature, no shared files with the traced data-flow.

## 18. Decision Matrix

| Requirement | Decision | Evidence |
|---|---|---|
| Frontend-only | **YES** | §8, §14 — `history_type`, `id`, `sources` all already cross the API boundary (`shrine.py:59-108`, `api/types.ts:34-58`); no Backend/Serializer/Model call needed for the transform |
| Additive presentation change | **YES** | §7/§8 — the change adds a grouping/partition step and (optionally) new ViewModel fields; nothing existing is removed; `sort_order`, `title`, `content`, `history_type_label`, `displayState` all remain as-is |
| Fact identity preserved | **YES** (with an implementation-quality gap, not a contract violation) | §9 — no Operation A anywhere in the traced or proposed code; `id` exists on the raw type but isn't yet wired into the ViewModel — PROPOSAL closes this additively |
| Per-Fact provenance preserved | **YES at the data level; not yet demonstrable in the shipped UI** | §10 — sources are never merged/shared at the Backend or raw-type layer; but `sources` isn't wired into the ViewModel or rendered anywhere today, grouped or not — PROPOSAL closes this additively |
| Exact canonical grouping possible | **YES** | §6 — `history_type` present, unmodified, at every layer through the render boundary; `HISTORY_TYPE_LABELS` already keys off it by exact match |
| Disputed exclusion possible | **YES** | §11 — `displayState` (`"full"`/`"disputed"`) already computed per-Fact and present at the render boundary; the same check `ShrineFactSection.tsx:61` already uses today can gate grouping |
| Backend change unnecessary | **YES** | §14 |
| Serializer change unnecessary | **YES** | §14 |
| Knowledge Model change unnecessary | **YES** | §14 |
| Migration unnecessary | **YES** | §14 |

## 19. Final Decision

# PARTIAL READY

**Basis**: Every structural question — whether grouping is Frontend-only, whether it requires
Backend/Serializer/Model/migration changes, whether the canonical grouping key
(`history_type`) is safely available, and whether `disputed` Facts can be reliably excluded — resolves
cleanly to **YES**, with direct file:line evidence (§8, §11, §14, §18). This is not `BLOCKED`: nothing
found requires a schema change, and no data needed for grouping is missing from the API response.

It is not the unconditional `READY FOR PR-B IMPLEMENTATION`, because two of the Decision Matrix's YES
answers (Fact identity, per-Fact provenance) are YES **at the data/structural level** but rely on a
concrete, small, currently-real gap being closed first: `id` and `sources` are computed by the
Backend and present in the raw API type (§5), but are dropped by
`buildShrineFactSection.ts`'s ViewModel mapping (§9, §10) and never reach
`DetailFactHistoryItem`/`DetailFactDeity` or the rendering component. Until that's wired through, a
grouped UI could satisfy "don't merge Facts" and "don't infer categories" while still having no way
to *show* a reader that each grouped Fact retains its own identity and its own source — the contract's
provenance constraint would be true but unverifiable from the shipped page.

**This is the "small contract/data gap" `PARTIAL READY` exists for.** It does not require its own
separate PR or any Backend/Serializer/Model work (§14) — §17 already folds closing it into PR-B's own
required file scope (`types.ts` + `buildShrineFactSection.ts`, items 1-2 of the "Required" list), so
PR-B remains assignable as one self-contained task: wire `id`/`sources` through, then implement the
`history_type`-keyed grouping with `disputed` excluded, per §13's ordering rule and §16's test matrix.

**This decision does not authorize starting that work.** PR-B still requires its own scoping,
ViewModel-shape decision (§17's "exact shape is a PR-B design decision, not made here"), and explicit
approval before implementation begins.

---

Production code changes = 0
UI changes = 0
Backend changes = 0
Serializer changes = 0
Knowledge Model changes = 0
Migrations = 0
Ranking changes = 0
Recommendation Authority changes = 0
