> **Status: Audit / design investigation only.** No production code, UI, Ranking, Recommendation
> Authority, Backend scoring, or Analytics instrumentation was changed to produce this document
> (`git diff` on application code = 0). The Recommendation Result observation freeze
> ([`recommendation-result-observation-policy.md`](../product/recommendation-result-observation-policy.md))
> remains active and is **not** touched or reopened by this audit — this document is scoped to
> Shrine Detail only. This document uses `READY FOR DETAIL INFORMATION RESTRUCTURE` /
> `PARTIAL READY` / `HOLD` as its own, separate decision states — it never uses
> `PRODUCT CHANGE READY`, which belongs exclusively to the Result observation policy.

# Shrine Detail Explanation / Knowledge Responsibility Audit

Each finding is labeled **FACT** (read directly from code/docs, with citation), **INFERENCE**
(a conclusion drawn from FACTs, stated as such), or **PROPOSAL** (a design idea for a future PR,
not implemented, not authorized here).

## 1. Purpose

Two UX concerns were observed on Shrine Detail:

- **(A)** The Personalized Explanation ("why this shrine fits your consultation") feels abstract
  and doesn't visibly connect to the actual recommendation signals (consultation axis, goriyaku,
  astrology/九星, shrine meaning/history theme).
- **(B)** The "神社について" (Shrine Knowledge) section shows what reads as duplicate History and
  Tradition blocks.

This audit traces the current implementation to determine whether these are caused by data
structure, rendering structure, information-responsibility design, or intentional content
modeling — without assuming the answer in advance.

## 2. Current Data-Flow Map

**FACT**: Shrine Detail's content is assembled by
[`buildShrineDetailModel.ts`](../../apps/web/src/lib/shrine/buildShrineDetailModel.ts), called from
[`apps/web/src/app/shrines/[id]/page.tsx`](../../apps/web/src/app/shrines/%5Bid%5D/page.tsx). There
are **four independent content-generation systems** feeding it, not one:

### A. Reason V4 pathway (consultation-specific, wins when present)

- Backend: `recommendation_reason_v4_detail`, persisted per-recommendation-item on
  `ConciergeThread.recommendations`/`recommendations_v2` (see §3 for the persistence mechanism,
  confirmed identical to how `consultation_axis`/`astro_elements` persist).
- `page.tsx:321-322`: `selectedRecommendation` is found by matching `shrine_id` inside the
  re-fetched thread (`getConciergeThreadServer(String(tid))`, `page.tsx:314`).
- `page.tsx:419-421`: `recommendationReasonV4Detail = normalizeRecommendationReasonV4Detail(selectedRecommendation?.recommendation_reason_v4_detail ?? null)`.
- `buildShrineDetailModel.ts:1625-1627`: `reasonV4 = isConciergeContext ? buildShrineDetailReasonV4Sections(recommendationReasonV4Detail) : {..., hasStructured: false}` — **Direct Navigation (no `ctx=concierge`) never receives this**, by design (comment at `buildShrineDetailModel.ts:63-64`: "相談文脈からFact/Interpretation/Actionを推測しない").
- When `reasonV4.hasStructured` is true, `buildShrineDetailModel.ts:1629-1674` renders it as three
  numbered sections: **"② 選ばれた背景"** (fact), **"③ 今回の相談との意味"** (interpretation),
  **"④ 参拝するときの視点"** (action) — and, critically, **filters out** any PayloadV2-sourced
  `kind: "meaning"` section first (line 1631-1633: `.filter((item) => item.section.kind !== "reason" && item.section.kind !== "meaning" && item.section.kind !== "action")`).

### B. Legacy `recommendationReasonDetail` / `buildRecommendationReasonViewModel` pathway

- `page.tsx:112-172` (`buildRecommendationReasonDetailInput`): calls
  `buildRecommendationReasonViewModel()` (`page.tsx:132-149`) with `breakdown`, `astro_elements`,
  `astro_priority`, `reason_facts`, `needTags` — **the same shared reason ViewModel builder used
  for the Result Hero** (confirmed: `apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts`
  is imported by both `page.tsx` and, via `conciergeToShrineList.ts`, the Result pathway).
- Produces `recommendationReasonDetail.consultationSummary`/`shrineMeaning`/`actionMeaning`
  (`page.tsx:162-167`), which feed:
  - **"① 今回の相談の整理"** (`buildProposalSection`, `buildShrineDetailModel.ts:538-544`, `lead`
    resolved by `resolveDetailLead()`, `buildShrineDetailModel.ts:592-613`, priority:
    `recommendationReasonDetail.consultationSummary` → `conciergeDeepReason.interpretation` →
    `conciergeReason` (raw) → PayloadV2 `generatedLead`).
  - **"③ この神社で受け取る意味"** (`buildMeaningSection`, `buildShrineDetailModel.ts:998-1035`,
    title fixed as **"この神社と今の状態の重なり"** — this is the literal heading closest to the
    task's paraphrase "この場所が合う理由"/"今のあなたとの接点"; no component in the codebase uses
    those exact strings).
  - **"④ 参拝するときの視点"** (`buildActionSection`, similar priority chain).
- When Reason V4 (A) is structured, these get superseded (§A above), but they remain the operative
  path when it is not (older threads, Direct Navigation with a synthetic payload, or any turn where
  the backend did not attach structured detail).

### C. `ShrineMeaningPayloadV2` pathway (shrine-scoped, **not consultation-specific**)

- `page.tsx:236`: `shrineMeaningPayloadV2 = await fetchShrineMeaningPayloadV2Server(numericId)` —
  called with **only the shrine id**, independent of `tid`/consultation.
- [`apps/web/src/lib/api/shrineMeaning.ts:19`](../../apps/web/src/lib/api/shrineMeaning.ts): fetches
  `/api/shrines/:id/meaning/`.
- [`apps/web/src/lib/shrineMeaning/payloadV2.ts:20-95`](../../apps/web/src/lib/shrineMeaning/payloadV2.ts):
  the `source` fields it's generated from are `goriyaku`/`goriyakuTags`/`sajin`/`description`/
  `historyTheme`/`element`/`placeTags`/`directionBonus` — **all static per-shrine attributes**, none
  of them the specific consultation's `breakdown`/`reason_facts`/`matched_need_tags`. Its
  `generated.consultationSummary` field is therefore a per-shrine generic summary, not a real
  per-consultation one, despite the field name.
- `buildShrineDetailModel.ts:84-173` (`buildMeaningSectionsFromPayloadV2`) turns
  `payload.display.blocks` into sections, including a premium "補足：神社の背景とご利益" block
  (`buildShrineDetailModel.ts:152-164`) built from block ids `history_context`/`deity_symbol`/
  `benefit_action` (`payloadV2.ts:77-90`).
- `buildShrineDetailModel.ts:1602-1619`: this is used as the **base** `freeDisplaySections`/
  `premiumDisplaySections` whenever `shrineMeaningPayloadV2` exists, **before** Reason V4 (A) is
  layered on top and (conditionally) filters it out.
- **This audit did not trace the Backend "meaning composer" that generates the actual `title`/`body`
  text for `history_context`/`deity_symbol` blocks** — only the frontend type contract and assembly
  logic. Flagged as an unknown in §8.

### D. Shrine Knowledge Fact pathway (static, always independent)

- `buildShrineDetailModel.ts:1683`: `factSection = buildShrineFactSection(shrine)` — reads
  `shrine.deities`/`shrine.histories` directly off the `Shrine` API object (not from the thread, not
  from the recommendation, not consultation-scoped at all).
- [`buildShrineFactSection.ts`](../../apps/web/src/lib/shrine/buildShrineFactSection.ts): returns
  `null` if both arrays are empty; otherwise sorts by `sort_order` and maps 1:1 into
  `DetailFactSection.deities`/`.histories`.
- Rendered by [`ShrineFactSection.tsx`](../../apps/web/src/components/shrine/detail/ShrineFactSection.tsx)
  under the heading **"神社について"**, entirely separate from sections A/B/C — always shown
  alongside them when Knowledge data exists, regardless of which of A/B/C is active.

**INFERENCE**: Systems A/B/C answer "why this shrine, for this consultation" (Personalized
Explanation); system D answers "what is this shrine, factually" (Shrine Knowledge). That split
matches the intended responsibility boundary in principle (§7), but A/B/C themselves are three
overlapping implementations of the same responsibility rather than one, which is itself a
data-structure/rendering-structure finding, addressed in §11.

## 3. Signal Availability Matrix

**FACT** (backend persistence mechanism, confirmed for `consultation_axis`/`astro_elements`/
`astro_priority`/`goriyaku_tags`/`history_theme`/`matched_need_tags`, and by the same code path used
for `recommendation_reason_v4_detail`): `backend/temples/api_views_concierge.py:906-939` captures the
full per-item `recs.get("recommendations")` list (which has these fields set on every item) as
`thread_recommendations`/`thread_recommendations_v2`, and passes it to `append_chat(...)`
(`backend/temples/services/concierge_history.py:356-411`), which writes it onto
`ConciergeThread.recommendations`/`.recommendations_v2` (`JSONField`, `models.py:635-636`). A later
Detail-page fetch of the thread by `tid` sees exactly what was persisted at that chat turn — no
re-computation on read. **This is the mechanism by which anything "reaches Detail" indirectly at
all** (system A/B in §2); anything not extracted from that persisted dict by
`pickBreakdownFromThread.ts`/`pickExplanationPayloadFromThread.ts`/`pickReasonFromThread.ts`/
`page.tsx` simply never becomes available to the Detail ViewModel, even though it is sitting in the
persisted JSON.

| Signal | Canonical source | Recommendation Authority (per [`recommendation-signal-authority.md`](../product/recommendation-signal-authority.md) §6, unless noted) | Reaches Detail? | Safe to expose directly? | Needs translation? | Should stay internal? |
|---|---|---|---|---|---|---|
| `need_tags` | Client input, structured | **Primary** | Yes, indirectly — `breakdown.matched_need_tags` extracted by `pickBreakdownFromThread.ts` and used by `buildProposalFromBreakdown()` (`buildShrineDetailModel.ts:546-578`) | Partially — already translated into copy sentences, not raw tag values | Already handled | No |
| `consultation_axis` | Resolved once per request (`resolve_consultation_axis`, `backend/temples/domain/consultation_axis.py:207`), broadcast to every recommendation item and persisted (see above) | **Primary (Mediator)** — gates `history_theme_candidate_boost` | **No** — FACT: `pickBreakdownFromThread.ts` and `pickExplanationPayloadFromThread.ts` (checked directly, zero matches) do not extract it; `buildShrineDetailModel.ts` never references it (checked, zero matches) | Would need translation (raw axis values are categorical/internal, e.g. not user-facing copy as-is) | Yes | No — it is a real Primary-Mediator signal, not noise |
| `goriyaku_tag_ids` (numeric) | `Shrine` M2M / candidate filter | **Eligibility + Explanation** (no Rank contribution by design; `_attach_breakdown`-equivalent in `concierge_chat_ranking.py:1093-1121` — `matched_by_gid` is one input unioned into `matched_all`, which becomes `score_need` at line 1124, so it **does** contribute to `score_need`/ranking via that union, contrary to a naive "explanation-only" read) | Not directly (ids); only via `matched_need_tags` derived from `breakdown` | N/A (internal ids) | N/A | Yes |
| `goriyaku` (free text) | `Shrine.goriyaku` | **Secondary** (`matched_by_text`) | Indirectly, folded into `buildBenefitText()` prose | Already handled | Already handled | No |
| `goriyaku_tags` (name strings, per-shrine full list) | `Shrine.goriyaku_tags` M2M | Explanation/display metadata in the ranking function (`concierge_chat_ranking.py:938-941`, debug profile only) | **Yes, but as generic shrine metadata, not filtered to this consultation** — see §5 | Risk: see §5 | N/A | Flag risk, not internal |
| `history_theme` | `Shrine.history_theme` static field | **Primary (conditional)** — contributes Rank only when `consultation_axis` matches (§4/§6 of signal-authority doc) | Yes — via `ShrineMeaningPayloadV2.source.historyTheme` → `generated.historyContext` (system C, §2), and via Reason V4 fact text (system A) when structured | Already handled via generated prose | Already handled | No |
| `deity` / `shrine_history` (legacy `sajin`/`description`-derived) | `Shrine.sajin`/`Shrine.description` via `_build_score_v3_candidate_profile()` | **Explanation-only (Decision A, current)** per signal-authority doc §8 | Yes, via `recommendation_reason_v4` text (system A's `factText`) | Already handled (prose) | Already handled | No |
| `knowledge_deities` / `knowledge_histories` (i.e. `ShrineDeity`/`ShrineHistory`) | New Knowledge Model, `backend/temples/models.py:480-572` | **Explanation-only (Decision A, current)** per signal-authority doc §8 — explicitly **not** connected to Score/Ranking | Yes — directly, via `ShrineDetailSerializer.get_deities`/`get_histories` (`backend/temples/api/serializers/shrine.py:218-241`) → `buildShrineFactSection.ts` (system D) | Yes — already gated by `verification_status`/`FactDisplayState` per Evidence Gate | Field-name translation already handled (`HISTORY_TYPE_LABELS`) | No |
| `astro_elements`/`astro_priority` (Western 4-element/zodiac) | `backend/temples/domain/astrology.py` (`sun_sign_and_element`, `element_priority`) | Contributes to `score_total` via `astro_bonus` (`concierge_chat_ranking.py:1054-1063,1225`) — **not listed as a named Signal in `recommendation-signal-authority.md`'s 17-signal table**; implicitly folded under `birthdate` (Personalization) | Yes, indirectly — passed into `buildRecommendationReasonViewModel()` (`page.tsx:140-141`), which turns `astro_priority>0` into a `"sign_support"` secondary reason type (frontend, `buildRecommendationReasonViewModel.ts:452`) — not shown as a distinct labeled block | Not currently exposed as a distinct element | Would need translation/labeling if exposed distinctly | Currently folded into prose; classification gap noted in §6 |
| `kyusei` (九星, Nine Star Ki) | `Shrine.kyusei` field (`models.py:262-267`) + `backend/temples/domain/kyusei.py` (user-side, from birthdate) | **FACT, confirmed by direct grep**: zero references in `concierge_chat_ranking.py` (the scoring function) — not a Ranking input for shrine selection. Used by `backend/temples/services/direction_reference.py:8` (`CALCULATION_METHOD = "annual_monthly_kyusei_v1"`) — a **Direction/Context** feature, not core Recommendation Ranking | `Shrine.kyusei` **is** included in `ShrineDetailSerializer.Meta.fields` (reaches the Detail API response) but **FACT, confirmed by direct grep**: zero references anywhere in `buildShrineDetailModel.ts`/`ShrineDetailArticle.tsx`/`ShrineFactSection.tsx` — unused at the frontend Detail rendering layer today | Reaches API, unused in UI | N/A (unused) | Not currently promoted as a Recommendation reason — correctly stays out of Personalized Explanation per the task's instruction not to promote UI-only astrology as Authority |
| `recommendationInstanceId` | Backend `rid`, per-generation | N/A (identity, not a ranking/explanation signal) | Yes — re-derived server-side in `page.tsx:432-434` from the persisted thread snapshot | N/A (internal id) | N/A | Internal (join key only, per [`recommendation-result-detail-instrumentation-contract.md`](recommendation-result-detail-instrumentation-contract.md)) |
| Thread context (`tid`, `ctx`) | URL query | N/A | Yes, directly (`page.tsx:178-179`) | N/A | N/A | Internal (routing/identity only) |

## 4. `consultation_axis` Displayability — Factual Assessment

- **Exists in the current Detail data flow?** Not at the frontend ViewModel layer. It is persisted
  per-recommendation-item on the thread snapshot (§3), but no current frontend picker
  (`pickBreakdownFromThread.ts`, `pickExplanationPayloadFromThread.ts`, `pickReasonFromThread.ts`,
  `pickModeFromThread.ts`) extracts it, and `buildShrineDetailModel.ts` never references it (checked
  directly — zero matches for `consultation_axis`/`consultationAxis` in that file).
- **Already used indirectly in displayed copy?** No. The closest displayed value,
  `conciergeExplanationPayload.primary_need_label_ja` (used in `buildProposalLead()`,
  `buildShrineDetailModel.ts:580-590`), comes from `_explanation_payload.primary_reason`, a
  different field than `consultation_axis`.
- **Could it be safely displayed as explanatory context?** Structurally yes — the value already
  exists on the persisted thread snapshot the Detail page already re-fetches; adding an extraction
  step is additive, not a new Backend capability. It is a genuine Primary(Mediator) signal per the
  Signal Authority doc, not internal noise, so displaying it (translated to user-facing copy) would
  not misrepresent it as more authoritative than it is.
- **Would it duplicate an existing visible reason?** Not literally (no current text is derived from
  it), but it is conceptually adjacent to `primary_need_label_ja` (both describe "what kind of
  consultation this is") — a future PR would need to decide whether it supplements or replaces that
  existing lead sentence rather than stacking a second, overlapping one.

## 5. Goriyaku / Benefit Signal Role

Three distinct things share the "goriyaku" name and must not be conflated:

1. **`goriyaku_tag_ids`** (numeric) — recommendation-driving: Eligibility filter, and via
   `matched_by_gid` a real contributor to `score_need`/ranking (§3 table). Not itself displayed.
2. **`goriyaku`** (free text on `Shrine`) — recommendation-driving: Secondary signal via
   `matched_by_text`. Folded into prose already (`buildBenefitText`).
3. **`goriyaku_tags`** (name strings, `Shrine.goriyaku_tags`, the shrine's **full, static** tag list)
   — this is what actually reaches Shrine Detail's "③ この神社と今の状態の重なり" text, via
   `getBenefitLabels(shrine)` (`apps/web/src/lib/shrine/getBenefitLabels.ts:8-9`: reads
   `shrine.goriyaku_tags` directly, falling back to legacy `shrine.goriyaku` free text) →
   `page.tsx:260` (`shrineBenefitLabels = getBenefitLabels(s)`) → `buildBenefitText()`
   (`buildShrineDetailModel.ts:615-698`), which takes `labels.filter(Boolean).slice(0, 3)` — the
   **first three of the shrine's entire tag list**, not filtered to only the tags that actually
   matched this consultation's `need_tags`.

**FACT, risk (not a proposed fix)**: `buildBenefitText`'s `primary` argument (which tag family
decides the sentence's tone: courage/money/mental/career/rest/love/study) **is**
recommendation-driving (`getPrimaryNeedTag(breakdown)`, sourced from `matched_need_tags`), but the
`joined` label list embedded in the same sentence (up to 3 shown) is the shrine's generic tag
catalog, unrelated to which tags actually matched. It is structurally possible for the sentence to
name a goriyaku tag the shrine has that had nothing to do with why it was recommended — this is a
factual mechanism, not a confirmed production instance (no DB query was run to find a live example).

**Do not treat every goriyaku tag as a recommendation reason** (per task instruction) — confirmed:
only `goriyaku_tag_ids`/`goriyaku` (free text) are recommendation-driving; `goriyaku_tags` (name
strings) as consumed by `getBenefitLabels()` is generic shrine metadata.

## 6. Astrology / 九星気学 Signal Role

Two **separate, unrelated** systems exist — do not merge them:

- **Western 4-element/zodiac** (`backend/temples/domain/astrology.py`): `sun_sign_and_element()`
  computes a zodiac sign + one of 火/土/風/水 from birthdate; `element_priority()` scores
  compatibility. **Affects Ranking** — `concierge_chat_ranking.py:1054-1063` feeds `astro_bonus`,
  which is an additive term of `score_total` (`concierge_chat_ranking.py:1225`). Reaches Detail
  indirectly (astro_priority/astro_elements → `buildRecommendationReasonViewModel()` → folded into a
  `"sign_support"` secondary reason sentence, `buildRecommendationReasonViewModel.ts:452`) but is
  **not shown as a distinct, labeled element** anywhere in Detail's UI today.
- **九星 / Nine Star Ki** (`Shrine.kyusei`, `backend/temples/domain/kyusei.py`): extensively
  implemented, but **FACT (direct grep, this audit)**: zero references in
  `concierge_chat_ranking.py` — it does **not** affect Recommendation Ranking for which shrine gets
  selected. It feeds `direction_reference.py`'s `CALCULATION_METHOD = "annual_monthly_kyusei_v1"` —
  the Direction/参拝タイミング feature, which the Signal Authority doc classifies as **Context**, not
  a shrine-selection signal. `Shrine.kyusei` is present in `ShrineDetailSerializer`'s response
  (reaches the Detail API) but **FACT (direct grep, this audit)**: unused anywhere in
  `buildShrineDetailModel.ts`/`ShrineDetailArticle.tsx`/`ShrineFactSection.tsx` — dead data at the
  Detail frontend layer.

**Do not promote UI-only astrology logic as Recommendation Authority** (per task instruction) —
confirmed neither system is currently a UI-invented signal; both are real Backend-computed values.
The gap is that neither `astro_elements`/`astro_priority` nor `kyusei` appears as a named, classified
row in `recommendation-signal-authority.md`'s 17-signal table — a documentation gap, not a behavior
gap. Any future PR that surfaces astrology in the Personalized Explanation should first close that
classification gap (a docs-only addition to the signal-authority doc) rather than inventing a new
UI-side authority.

## 7. Signal Classification Table

(Consolidates §3–§6 into the exact format requested.)

| Signal | Canonical source | Used by Recommendation Authority? | Reaches Detail? | Safe to expose directly? | Needs translation? | Should remain internal? |
|---|---|---|---|---|---|---|
| `need_tags` | Client input | Yes (Primary) | Indirectly (breakdown) | Partially (translated) | No (done) | No |
| `consultation_axis` | Backend, per-request | Yes (Primary/Mediator) | No (persisted, not extracted) | Structurally yes | Yes | No |
| `goriyaku_tag_ids` | Shrine M2M | Yes (Eligibility + score_need via matched_by_gid) | No (ids only) | N/A | N/A | Yes |
| `goriyaku` (text) | Shrine field | Yes (Secondary) | Indirectly (prose) | Already handled | Already handled | No |
| `goriyaku_tags` (names) | Shrine M2M | Explanation/debug only in ranking; not a score input | Yes, as generic metadata | Risk (§5) | N/A | Flag, not internal |
| `history_theme` | Shrine field | Yes (Primary, conditional) | Yes (systems A & C) | Already handled | Already handled | No |
| `deity`/`shrine_history` (legacy) | `sajin`/`description` | No (Explanation-only, Decision A) | Yes (system A prose) | Already handled | Already handled | No |
| `ShrineDeity`/`ShrineHistory` (Knowledge Model) | New Model | No (Explanation-only, Decision A) | Yes, directly (system D) | Yes (Evidence-gated) | Handled | No |
| `astro_elements`/`astro_priority` | `domain/astrology.py` | Yes (astro_bonus → score_total) | Indirectly (prose only) | Not currently distinct | Yes, if exposed distinctly | Classification gap (§6) |
| `kyusei` | `Shrine.kyusei`/`domain/kyusei.py` | No (Direction/Context only, confirmed) | Reaches API, unused in UI | N/A (unused) | N/A | Not Ranking-relevant to Detail explanation |
| `recommendationInstanceId` | Backend `rid` | N/A (identity) | Yes | N/A | N/A | Internal join key |
| Thread context (`tid`/`ctx`) | URL | N/A | Yes | N/A | N/A | Internal routing |

## 8. Personalized Explanation Layer Responsibility (Design Only)

Target: *"Why does this shrine make sense for this consultation?"*

**Should contain** (combinations of):

- Consultation axis framing, if/when exposed (§4) — translated, not raw.
- The recommendation-driving benefit signal actually matched for this consultation
  (`matched_need_tags`-filtered goriyaku, not the shrine's full generic tag list — §5's risk should
  be closed here, not worked around).
- Astrology/九星 signal **only if it genuinely contributed to Ranking for this candidate** (i.e.
  Western 4-element `astro_bonus`, confirmed real; **not** `kyusei`, confirmed not a Ranking input —
  §6) and explicitly labeled as such rather than folded anonymously into prose.
- Shrine meaning / `history_theme` connection (already present, systems A/C).
- One final human-readable connecting sentence (already the intent of "③ この神社と今の状態の重なり"
  / Reason V4's interpretation text).

**Must NOT contain**:

- The shrine's unfiltered generic `goriyaku_tags` list presented as if it explains this specific
  recommendation (§5 risk).
- Knowledge Facts (`deity`/`shrine_history`/`ShrineDeity`/`ShrineHistory`) presented in a way that
  reads as a Ranking reason — this would violate the Explanation Contract already fixed in
  `recommendation-signal-authority.md` §10 ("祭神が○○だから1位です" is an explicit anti-pattern
  example there). System D ("神社について") already keeps this separate; a future PR must not merge
  D into A/B/C.
- `kyusei` framed as if it influenced which shrine was recommended (§6 — it did not).
- Two independently-generated "why this shrine" sentences shown simultaneously — i.e. system C's
  generic `consultationSummary`/`shrineMeaning` must not render alongside system A/B's real,
  consultation-specific versions; today this is already prevented when `reasonV4.hasStructured` is
  true (§2), but is not prevented for the legacy B-only path if a future PR adds more PayloadV2
  content.

## 9. Shrine Knowledge Fact Taxonomy

**FACT** (`backend/temples/models.py`, confirmed by direct backend trace):

| Fact type | Model | Field | Canonical values |
|---|---|---|---|
| Deity (祭神) | `ShrineDeity` (`models.py:480-521`) | `role` | `primary`/`enshrined`/`secondary`/`unknown` |
| History/Origin/Tradition/etc. | `ShrineHistory` (`models.py:523-572`) | `history_type` | `official_origin`（由緒）/`founding`（創始）/`historical_event`（歴史）/`tradition`（伝承）/`regional_context`（地域史）/`editorial_summary`（要約） — labels from `HISTORY_TYPE_LABELS`, `buildShrineFactSection.ts:10-17` |

There is **no separate "shrine_history" Fact type distinct from `ShrineHistory`** in the current
Knowledge Model — `shrine_history` (lowercase, legacy) refers to the pre-Knowledge-Model
`Shrine.description`-derived Recommendation Fact (system A/B's `factText`), a different, older
concept than the `ShrineHistory` rows rendered in "神社について" (system D). The task's requested
categories `deity`/`shrine_history`/`history`/`tradition`/`place_context`/`meaning`/`evidence` map
onto the current model as follows:

- `deity` → `ShrineDeity.display_name` (rendered as pills, `ShrineFactSection.tsx:22-39`).
- `shrine_history` (legacy Recommendation Fact) → **not** part of system D at all; it is system A/B's
  `factText`/`shrineMeaning`, a generated sentence, not a Knowledge record.
- `history`/`tradition`/`official_origin`/`founding`/`regional_context`/`editorial_summary` → all six
  are `ShrineHistory.history_type` values, each independent rows, each rendered as its own card
  (`ShrineFactSection.tsx:41-73`).
- `place_context` → not a current `history_type` value; `regional_context`（地域史）is the closest
  existing category. `place_context`/`placeTags` do appear as a *different*, unrelated field in
  system C's `ShrineMeaningSourceFieldsV2.placeTags` (`payloadV2.ts:46`) — a third, separate concept
  from Knowledge Model `regional_context`.
- `meaning` → ambiguous across systems: system B/C both use the word "meaning" (`buildMeaningSection`,
  `ShrineMeaningPayloadV2`) for *interpretation* text, not a Knowledge Fact category at all.
- `evidence`/source metadata → `ShrineKnowledgeSource` (`models.py:432-471`), surfaced per-Fact via
  `ShrineDeitySerializer`/`ShrineHistorySerializer`'s `sources` field (`shrine.py:66-82`), but **not
  currently rendered** in `ShrineFactSection.tsx` (confirmed: the component reads `deities`/
  `histories` only, no `sources` field is destructured or displayed).

**Rendering cardinality (FACT, `ShrineFactSection.tsx:22-73`)**: 1 `ShrineDeity` row → 1 pill; 1
`ShrineHistory` row → 1 independent bordered card, labeled with `history_type_label`. No aggregation,
no grouping, no cap on count.

## 10. History / Tradition / Deity / `shrine_history` Boundary

Using [`docs/knowledge/shrine-knowledge-contract.md`](../knowledge/shrine-knowledge-contract.md) (the
existing canonical doc for this) as source of truth, not inventing new categories:

| Type | Intended meaning (contract) | Current data source | Current UI treatment | Overlap risk |
|---|---|---|---|---|
| `official_origin`（由緒） | Shrine's own official origin account | `ShrineHistory.history_type="official_origin"` | Independent card | Low — distinct type |
| `founding`（創始） | Founding/enshrinement facts, date certainty tracked separately (`event_date` vs `period_text`) | `ShrineHistory.history_type="founding"` | Independent card | Low |
| `historical_event`（歴史） | Post-founding events (rebuilding, relocation, etc.) | `ShrineHistory.history_type="historical_event"` | Independent card | Medium — could read as generic "History" to a user unfamiliar with the 6-way split |
| `tradition`（伝承） | Legend/oral tradition, explicitly **not** confirmed historical fact — contract mandates hedged language (`docs/core/recommendation-reason-contract.md` "TRADITION_ALWAYS_HEDGED", cited in the contract doc) | `ShrineHistory.history_type="tradition"` | Independent card, same visual treatment as the other 5 types | **High** — nothing in `ShrineFactSection.tsx` visually distinguishes `tradition`'s epistemic weakness from `official_origin`'s; both render in an identical bordered card, differing only in the small `history_type_label` text |
| `regional_context`（地域史） | Local/regional historical context | `ShrineHistory.history_type="regional_context"` | Independent card | Low |
| `editorial_summary`（要約） | App-authored summary of a Source, not the Source itself | `ShrineHistory.history_type="editorial_summary"` | Independent card | Low |
| `deity`（祭神） | `ShrineDeity` | Independent Model | Pill list | Low, separate section |

**FACT**: the Model layer already keeps these 6 types cleanly separated and independently
constrained (`docs/knowledge/shrine-knowledge-contract.md` "history_type / verification_status /
confidenceの3軸分離" — `tradition ≠ disputed`, `official_origin ≠ source_confirmed`). The overlap
risk is **presentation-only**: the UI does not visually reflect the semantic distance between, say,
`tradition` (hedged, unconfirmed) and `official_origin` (the shrine's own account).

## 11. Duplicate-Looking History / Tradition Blocks — Cause Investigation

Two distinct, **both real**, mechanisms can each independently produce what an observer would
describe as "2 History blocks" or "2 Tradition blocks." Neither is a bug; both are documented/coded
behavior.

### Mechanism (a): Multiple `ShrineHistory` rows sharing one `history_type` (system D only)

**FACT**: `ShrineHistory` has **no `unique_together`/`UniqueConstraint`** tying `shrine` + any other
field together (`models.py:561-565`, confirmed by direct backend trace). The Knowledge contract
explicitly documents this as the intended "Multiple Fact保持方針" — multiple independent
`ShrineHistory` rows per shrine, each with its own `title`/`content`/`sources`, are expected, and
`shrine-knowledge-contract.md` explicitly **prohibits** automatically merging or grouping them
("複数のFactを自動グルーピングすること" is listed among forbidden AI/system behaviors, in both the
Disputed Evidence Contract section and the Multiple Fact保持方針 section). If a shrine has, e.g., two
`ShrineHistory` rows both with `history_type="tradition"`, `ShrineFactSection.tsx` renders two
separate cards, each labeled "伝承" — this is exactly what would visually read as "2 Tradition
blocks." The existing test `ShrineDetailArticle.test.tsx`'s "複数Historyをすべて表示する（品川神社相当）"
confirms this is a known, intentionally-supported real-shrine scenario, not a hypothetical edge case.

### Mechanism (b): System C (PayloadV2) and System D (Fact) both rendering when Reason V4 is not structured

**FACT** (`buildShrineDetailModel.ts:1611-1674`, traced in §2): when `reasonV4.hasStructured` is
**false** (older thread, Direct Navigation, or any turn where the backend didn't attach structured
Reason V4 detail), `premiumDisplaySectionsBeforeReasonV4` — which includes system C's
"補足：神社の背景とご利益" block (containing `history_context`/`deity_symbol` content, entirely
independent of the Knowledge Model) — is used **as-is**, alongside system D's "神社について" Fact
section (which renders unconditionally whenever `shrine.deities`/`shrine.histories` are non-empty,
`buildShrineDetailModel.ts:1683`, independent of `reasonV4.hasStructured`). A user could then see
both a `history_context`-derived sentence (system C, generic per-shrine) and independent
`ShrineHistory` cards (system D, Knowledge Model) on the same page — two content blocks that both
read as "history," from two unrelated data sources. **This mechanism is conditional**: when
`reasonV4.hasStructured` is true, the filter at `buildShrineDetailModel.ts:1631-1633` removes
system C's `kind: "meaning"` block first, so this overlap does not occur on that (more common,
better-instrumented) path.

**Classification** (per the task's options): the cause is **"same Fact type rendered
independently"** (mechanism a, the primary and unconditional cause) **and, conditionally,
"modeling ambiguity / independent content-generation systems"** (mechanism b, only when Reason V4 is
unstructured). It is explicitly **not**: duplicated database records (no evidence found; the Model
itself intentionally allows multiple legitimate rows), improper source duplication (each
`ShrineHistory` row has its own independent `sources` relation per the Source contract), or a
grouping bug (grouping is contractually prohibited, not merely unimplemented — see §12).

**Unknown, not resolved by this audit**: which mechanism actually produced the specific "2 History /
2 Tradition" instance the task describes was not verified against production data (no DB query was
run; this audit is frontend/backend code tracing only).

## 12. Same-Category Multi-Card Rendering Rule Audit

**FACT**: Yes, the current UI intentionally renders "1 Fact = 1 card" for `ShrineHistory`
(`ShrineFactSection.tsx:41-73`, direct 1:1 `.map()`, no grouping logic).

**FACT**: No grouping rule exists anywhere in the codebase (`buildShrineFactSection.ts` and
`ShrineFactSection.tsx` both checked directly — no `groupBy`/aggregation of any kind).

This is **not** merely an unaddressed information-density gap — it is an explicit contract.
`docs/knowledge/shrine-knowledge-contract.md`'s Disputed Evidence Contract section states, for
`disputed` Facts specifically but as a general principle the doc repeats in its Multiple Fact
section: *"複数のFactを自動グルーピングすること"* is a **prohibited** behavior, "将来実装する場合も"
(even in future implementations). Any grouped-rendering design (§13) must be evaluated against
whether it counts as the kind of automatic grouping this contract forbids, or whether grouping by an
already-explicit, human-assigned categorical field (`history_type`) is a different, permitted thing
("displaying existing metadata" vs. "the system judging that Facts belong together"). **This
audit does not resolve that interpretation question — flagged as a risk requiring Product/母艦
confirmation in §14.**

## 13. Grouped-Rendering Feasibility (Design Only, Not Implemented)

**PROPOSAL — safe, metadata-backed option**: group `ShrineHistory` cards by exact `history_type`
value equality (the 6 existing canonical categories), under one heading per type, e.g.:

```
由緒 (official_origin)
  [card] [card]
歴史 (historical_event)
  [card]
伝承 (tradition)
  [card] [card]
```

This uses only already-existing, explicitly human/reviewer-assigned metadata
(`history.history_type`) — it does not invent new categories, does not infer relationships between
Facts, and does not require the system to judge semantic similarity. It is display-layer
re-organization of a field that already exists on every row.

**PROPOSAL, explicitly flagged as NOT currently supported by metadata**: the task's example grouping
(創建/江戸期/近代 — by era/period) is **not** achievable safely today:

- `period_text` (`models.py:539-544`) is a free-text display field ("推定年代等、幅を持つ期間表現") —
  not a structured, comparable value.
- `event_date` (`models.py:545`) is a nullable `DateField`, only populated "確定している場合のみ" —
  not reliably present across rows, and even where present, deriving an "era" bucket from a raw date
  would be a new categorization the Model does not currently define.
- Per the task's own instruction, heuristically parsing `period_text` copy to infer an era would be
  "inventing categories from copy text heuristics," which is out of scope unless explicitly marked
  Future-only.

**Conclusion for §12/§13**: value-based grouping by the existing `history_type` field is
metadata-supported and feasible as a design; era-based subgrouping is not supported by current
metadata and would require either a new structured field (Backend Model change, out of scope for a
Detail-only audit) or explicitly-flagged Future heuristic work.

## 14. Result Overlap Assessment

**Reminder**: this section classifies overlap only; it does not recommend changing Result UI, and the
Result observation freeze is unaffected.

| Field/content | Shown on Result (Hero/Compact) | Shown on Detail | Classification |
|---|---|---|---|
| Reason V4 fact/interpretation/action text (`shrine_meaning`/`action_meaning`/`consultation_summary`) | Yes — `ConciergeTopRecommendationHero`, same adapter (`buildHeroReasonV4Sections`) | Yes — system A, same underlying `recommendation_reason_v4_detail` and (per `recommendation-result-information-architecture.md` §5) the same `reasonV4FactPriority.ts` adapter logic | **Potentially redundant** — already identified independently in `recommendation-result-detail-density-change-readiness.md` and confirmed at the Analytics-event level (identical `cardId`s on both surfaces) in `recommendation-result-detail-instrumentation-contract.md` §5 |
| `history_theme` content | Yes — Result's ungated `historyThemeDisplay` section (`recommendation-result-information-architecture.md` §3.1, item 6) | Yes — system C's `historyContext`, only on the path where PayloadV2 is the active source (§2) | Potentially redundant, but only when system C (not Reason V4) is active |
| `trustMetadata` (`rank_class`/`cultural_status`/`lineage`/`origin_summary`) | Yes — Result-only section (`ConciergeSectionsRenderer.tsx`, per earlier chapter of this audit trail) | **No** — confirmed by direct grep, zero references in any Detail component | **Result-only** |
| `ShrineDeity`/`ShrineHistory` Knowledge Facts ("神社について") | **No** — confirmed, no reference to `deities`/`histories`/Fact rendering anywhere in `ConciergeSectionsRenderer.tsx`/`ConciergeTopRecommendationHero.tsx` | Yes — system D | **Detail-only** — matches the intended Hero=summary/Detail=complete responsibility split already defined in `recommendation-result-information-architecture.md` §5 |
| `consultation_axis`/`recommendationInstanceId` | Analytics/join-key only, not user-facing content on Result either | Not user-facing on Detail (§4) | Not applicable — plumbing, not explanation content, on both sides |

## 15. Risks / Unknowns

- **§12's grouping-prohibition interpretation is unresolved.** Whether grouping-by-existing-value
  (§13's safe proposal) is compatible with `shrine-knowledge-contract.md`'s "no automatic grouping"
  language, or whether that contract's authors intended to forbid *any* multi-Fact aggregation
  including value-equality grouping, was not decided by this audit and needs explicit Product/母艦
  confirmation before PR-B (§16) is scoped further.
- **System C's Backend "meaning composer" internals were not traced.** This audit only examined the
  frontend type contract (`payloadV2.ts`) and assembly logic; the actual backend service that
  generates `history_context`/`deity_symbol` block titles/bodies (and thus whether they'd read to a
  user as literally "History"/"Deity" content, reinforcing mechanism (b) in §11) was out of scope for
  this Detail-focused audit.
- **The specific production instance behind the task's "2 History / 2 Tradition" observation was not
  identified.** No database query was run to determine whether mechanism (a), mechanism (b), or both
  produced that specific observed page. Root-causing the exact instance would need one, before
  deciding whether §16's PR-C is actually necessary or whether §16's PR-B (grouping) alone would
  resolve it.
- **The §5 goriyaku-label mismatch risk is a structural possibility, not a confirmed production
  occurrence.** No example of a displayed, non-matching goriyaku tag was found or looked for in
  production data.
- **`astro_elements`/`astro_priority`/`kyusei` are not named rows in `recommendation-signal-
  authority.md`'s Decision Table** (§6) — this audit infers their classification from where they're
  used in code, not from an existing Product decision recorded in that doc. A future PR touching
  Personalized Explanation's astrology content should treat this as a prerequisite documentation gap,
  not assume this audit's classification is itself an authorized Product decision.

## 16. Future PR Split (Design Only, Not Authorized)

**PR-A — Personalized Explanation Data Contract Clarification**
- Purpose: decide (Product) whether `consultation_axis` should be surfaced in "① 今回の相談の整理",
  and if so, extract it from the already-persisted thread snapshot.
- Files likely affected: `pickBreakdownFromThread.ts` or a new `pickConsultationAxisFromThread.ts`,
  `buildShrineDetailModel.ts` (`buildProposalSection`/`buildProposalLead`).
- Backend changes required: **No** — the value is already persisted (§3).
- Recommendation Authority changes: **Prohibited and unnecessary** — this only reads an existing,
  already-classified Primary(Mediator) signal; no scoring/ranking logic is touched.
- Test scope: extend `pickBreakdownFromThread`-style picker tests; extend
  `buildShrineDetailModel.ts` snapshot/unit tests for the proposal section's lead text.

**PR-B — Shrine Knowledge Grouped Rendering**
- Purpose: group `ShrineHistory` cards by existing `history_type` value under one heading per type
  (§13's safe proposal only — not era-based grouping).
- Files likely affected: `buildShrineFactSection.ts`, `ShrineFactSection.tsx`,
  `apps/web/src/components/shrine/detail/types.ts` (`DetailFactSection` shape).
- Backend changes required: **No** — `history_type` already exists on every row.
- Recommendation Authority changes: **Prohibited and unnecessary** — purely a Detail-side rendering
  change to already-Explanation-only data.
- **Blocked on**: §15's grouping-prohibition interpretation question — must be resolved by Product
  before this PR can be scoped with confidence.
- Test scope: extend `ShrineFactSection.integration.test.tsx` (already exists, per
  `shrine-knowledge-contract.md`'s PR-D1 reference) for multi-row-same-type fixtures (the existing
  "品川神社相当" test is the natural base case to extend).

**PR-C — History / Tradition Density Polish**
- Purpose: visually distinguish `tradition`（伝承, hedged/unconfirmed） from the other 5
  `history_type` values (§10's overlap-risk finding), independent of whether PR-B ships.
- Files likely affected: `ShrineFactSection.tsx` only (styling/labeling, no data changes).
- Backend changes required: **No.**
- Recommendation Authority changes: **Prohibited and unnecessary.**
- Test scope: `ShrineFactSection.tsx` unit/snapshot tests for the `tradition` visual treatment.

**PR-D (new candidate identified by this audit) — System C / System D Overlap on the Unstructured
Reason V4 Path**
- Purpose: decide (Product) whether system C's "補足：神社の背景とご利益" block should still render
  when `reasonV4.hasStructured` is false and Knowledge Facts (system D) are also present for the same
  shrine (§11 mechanism (b)) — currently no code prevents both from rendering on that path.
- Files likely affected: `buildShrineDetailModel.ts` (the `premiumDisplaySectionsBeforeReasonV4`
  branch).
- Backend changes required: **No.**
- Recommendation Authority changes: **Prohibited and unnecessary.**
- Test scope: a `buildShrineDetailModel.ts` test with `reasonV4.hasStructured=false` +
  non-empty `shrine.histories`, asserting the (currently undecided) desired behavior once Product
  decides it.

## 17. Final Decision

# PARTIAL READY

**Basis**: The audit successfully traced and cited, with FACT-level confidence, the full data-flow
map (§2), the signal availability matrix (§3/§7), the Fact taxonomy (§9/§10), the duplication
mechanisms (§11, both confirmed with code citations), the current (contractually intentional)
non-grouping rule (§12), and the Result/Detail overlap classification (§14). These are sufficient to
scope PR-A, PR-C, and PR-D with confidence.

It is not `READY FOR DETAIL INFORMATION RESTRUCTURE` because PR-B — the change most directly
responsive to the task's concern (B), duplicate-looking History/Tradition blocks — is blocked on an
unresolved contract-interpretation question (§15) that only Product/母艦 can answer: whether grouping
`ShrineHistory` cards by their existing `history_type` value counts as the "automatic grouping"
`shrine-knowledge-contract.md` prohibits. Proceeding to implement PR-B without that answer risks
either violating a documented Knowledge contract or building the wrong thing.

It is not `HOLD` because most of the audit's findings are conclusive, well-cited, and immediately
actionable for PR-A/PR-C/PR-D — there is no reason to block all Detail information-responsibility
work pending the one open question.

**This decision does not authorize any implementation.** Each PR candidate in §16 requires its own
scoping and explicit approval before work begins. It also does not authorize, and is entirely
independent of, any Result Hero/Compact UI change — the Result observation freeze in
`recommendation-result-observation-policy.md` remains fully in effect and untouched by this document.

---

Production code changes = 0
UI changes = 0
Ranking changes = 0
Recommendation Authority changes = 0
Backend scoring changes = 0
Migrations = 0
Analytics instrumentation changes = 0
