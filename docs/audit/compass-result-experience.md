> **Status: Active**
>
> This is a **docs-only UX audit**. It does not modify Backend production
> code, Frontend production code, Runtime, Recommendation Ranking,
> Concierge, Analytics instrumentation, Product/Runtime Contract, or the
> DB. **Live browser interaction (clicking/typing) failed consistently in
> this session** — screenshots rendered but click actions timed out with
> "pane is currently hidden" regardless of retry, an environment/tooling
> issue, not a Compass defect. Evidence for this audit therefore comes
> from three sources, each labeled where used: (1) direct code trace
> against current `develop`, (2) this repository's own existing component
> tests (`CompassClient.test.tsx`, `CompassClient.analytics.test.tsx`,
> which render the real component tree via Testing Library, not a mock of
> the UI itself), and (3) real screenshots captured earlier in this same
> session (the Monthly Fallback UI/Copy Alignment task), against the exact
> same, unmodified UI code — confirmed via `git log` that no commit has
> touched any Compass UI file since that capture.

# Compass Result Experience Audit

## 1. Purpose

After Compass resolves a direction and returns shrine recommendations, can
a user immediately understand the result and know what to do next? This
audit answers that for COMMON, MONTHLY_FALLBACK, and `no_common_direction`,
inventories the shrine recommendation card, traces the CTA/route path,
checks responsive behavior, and confirms what current Analytics can and
cannot observe about the next user action.

## 2. Scope

In scope: `CompassClient.tsx` and everything it renders (direction
visualization, result-state messaging, recommendation cards), the detail
CTA, the route path as far as the existing, unmodified
`GoogleMapRouteLink`/`ShrineDetailShell`, responsive behavior at
375/390/430px, and Analytics event readiness for the next action after a
Compass result. Out of scope (Section 27): any implementation, Ranking,
Concierge, shrine data, the Product/Runtime Contract, and DB/migrations.

## 3. Canonical Sources

Read: `compass-product-contract.md`, `compass-mvp-runtime-contract.md`,
`compass-monthly-fallback-ui-analytics-boundary.md`,
`compass-recommendation-availability.md` (+ its two production-measurement
follow-ups), `compass-calculation-method-measurement-valid-from.md`,
`compass-analytics-contract.md`, `compass-posthog-query-contract.md`.
Current implementation re-traced directly: `CompassClient.tsx`,
`CompassDirectionVisual.tsx`, `CompassRecommendationsSection.tsx`,
`CompassOriginSummary.tsx`, `ShrineCardCompact.tsx`,
`GoogleMapRouteLink.tsx`, `ShrineDetailShell.tsx`, `searchEvents.ts`,
`cardEvents.ts`.

---

## 4. Production Evidence

```
COMMON:            code trace + existing tests + real screenshot from this
                    session's prior UI Copy Alignment task (desktop width;
                    responsive widths not independently captured for COMMON
                    specifically -- see Section 16-18 caveat)
MONTHLY_FALLBACK:   code trace + existing tests + real screenshots from this
                    session's prior task at 375px/390px/430px (with live
                    recommendation cards, real local backend, unmodified code)
no_common_direction: code/test evidence only -- no birthdate exists for
                    today's date (2026-08-22) that reproduces this state
                    (verified by scanning kyusei.py across a wide birthdate
                    range locally; none returned a residual/empty-both
                    case for today), and this session's live browser tooling
                    failed for new interaction this turn (Section 0). Marked
                    PRODUCTION OBSERVATION UNAVAILABLE per this task's own
                    Section 5 contingency.
```

No screenshot containing QA personal input (birthdate) is committed to
this repository — only textual descriptions of what was observed.

---

## 5. Current Result Architecture

Traced from `CompassClient.tsx` (unchanged structure since #2512):

```
1. Header: "今月の参拝コンパス" + target month + one-line Product Promise text
2. Input section: purpose chips (CompassPurposeSelector) + origin summary
   (CompassOriginSummary) + birthdate date input + submit button
3. [conditional, directionContext != null] Direction card:
   CompassDirectionVisual (8-sector wheel + "今月意識したい方向: X" text)
   + calculationMethod-derived note (COMMON vs MONTHLY_FALLBACK copy)
4. [conditional, uiState-exclusive] One of: direction_filter_unavailable /
   no_common_direction / direction_zero_candidates / evidence_zero_candidates
   / backend_error messaging (DetailSection, title + one body sentence)
5. [conditional, recommendation_success] CompassRecommendationsSection:
   list of ShrineCardCompact cards under "この方向の参拝候補"
```

Sections 3-5 are mutually exclusive per current `uiState`/`directionContext`
logic — never rendered simultaneously in a contradictory combination.

---

## 6. COMMON UX

**Evidence**: real screenshot (this session, prior task, desktop width) +
code trace.

```
Result heading:        "今月、意識したい方向" (DetailSection title)
Direction visualization: 8-sector wheel, highlighted sector(s) filled +
                        bold text, "今月意識したい方向: 東" label below
Explanatory copy:      "年盤と月盤の両方で重なる、今月の参考方位です。
                        日盤は使用していません。（参考情報です）"
Recommendation cards:  3 (observed), "この方向の参拝候補" heading
Primary CTA:           per-card "詳細だけ見る" (Section 13)
Secondary CTA:         none
Route affordance:      none directly on result (Section 14)
```

**Does it make clear that annual and monthly directions overlap?** Yes —
the copy explicitly states "年盤と月盤の両方で重なる" ("both the annual
and monthly charts overlap").

**Classification: CLEAR.**

---

## 7. MONTHLY_FALLBACK UX

**Evidence**: real screenshots (this session, prior task, 375/390/430px,
with live recommendation cards) + code trace.

```
Explanatory copy: "年盤と月盤で重なる方位がないため、今月の月盤を参考に
                   した方位です。日盤は使用していません。（参考情報です）"
```

Checked against the four sub-questions:

- Does it communicate annual/monthly did not overlap? **Yes** — "重なる
  方位がないため" ("because there is no overlapping direction").
- Does it communicate the direction is monthly-reference-based? **Yes** —
  "今月の月盤を参考にした方位です" ("a direction based on this month's
  monthly chart").
- Does it communicate the result is still usable reference information?
  **Yes** — "（参考情報です）" suffix, identical framing to COMMON.
  Does it imply annual/monthly agreement? **No** — confirmed by the exact
  copy-fix audited and tested in the prior UI Copy Alignment task
  (`CompassClient.test.tsx`'s dedicated MONTHLY_FALLBACK test asserts the
  old misleading "重なる、今月の参考方位です" phrasing is absent).

**Visual comparison with COMMON**: structurally **identical** — same
direction wheel component, same note position, same font size (`text-xs`),
same muted color (`text-[var(--kt-color-text-muted)]`). The **only**
distinguishing signal between COMMON and MONTHLY_FALLBACK is the note's
prose content; there is no separate visual weight, icon, badge, or color
treatment marking a fallback result as structurally different from a
COMMON one.

**Does the user understand this is a fallback without reading it as an
error or the same-strength result?** The text is unambiguous if read in
full — but nothing about the surrounding visual treatment prompts a user
to read it carefully rather than skim past it as "the same kind of note
COMMON also has."

**Classification: B — SEMANTICALLY CORRECT BUT TOO SUBTLE.**

Not **C (Misleading)** — the text itself is accurate and was already
audited/tested for this in the prior UI Copy Alignment task. Not **A
(Clear enough)** — nothing differentiates the *visual* presentation from
COMMON, so comprehension depends entirely on the user actually reading a
small, muted, two-sentence note. Not **D (Over-emphasized / feels like
error)** — if anything, the opposite risk exists.

---

## 8. `no_common_direction` UX

**Evidence**: code + `CompassClient.test.tsx` (renders the real component
tree via Testing Library) — production observation unavailable this turn
(Section 4).

```
Title: "今月は方位の参考情報がありません"
Body:  "生年月日・出発地点はどちらも問題ありません。年盤と月盤の共通方位も、
        今月の月盤単独の参考方位も、今月はいずれもありませんでした。"
```

Checked against the narrowed residual meaning (#2508/#2517): the copy
explicitly states both the common direction *and* the monthly fallback
were checked ("年盤と月盤の共通方位も、今月の月盤単独の参考方位も") — this
matches the actual, narrowed trigger condition, not the pre-#2508 wording.
It does not imply an input mistake ("どちらも問題ありません" — "both are
fine"), and does not suggest retrying will help (no retry language at
all).

**Does this become a dead end?** The input form (purpose/origin/birthdate)
remains rendered above this message (it is never unmounted), so a user
*can* scroll up and change any input and resubmit — but **no explicit CTA,
link, or suggestion points them to do so**, to Concierge, or to browsing
shrines directly. The message stops at "here's what happened," with no
"here's what you could try" follow-up.

**Classification: PARTIAL CONTINUATION** — a path exists (the form is
still there), but it is not surfaced as a next action; a user reading only
this message has no explicit guidance.

---

## 9. Information Hierarchy

Actual observed sequence (Section 5): Header/Promise → Input form →
[Direction card] → [state message] → [Recommendations]. This matches the
"expected concepts" order the task named. No duplicated information was
found (the direction wheel's text label and the note serve different,
non-redundant purposes — "what direction" vs. "why"). No competing CTAs
were found anywhere in the flow — exactly one primary action exists at
each stage (submit button, then per-card detail link). The input form
itself is moderately long (purpose chips + origin summary + date input +
button) before any result appears, which is inherent to a single-scroll
page design, not a hierarchy defect.

---

## 10. Cognitive Load

To answer "what direction / why / which shrine / what to tap," a user
must parse, in sequence: (1) the wheel's highlighted sector + text label,
(2) the one- or two-sentence note explaining the direction's source, (3)
each card's single-line reason text, (4) each card's address line, (5)
the small "詳細だけ見る" link. That is 4-5 short, distinct text elements
across two structurally separate sections (direction card, recommendation
list) per result.

**Classification: MODERATE.**

Cause: not any single piece of copy is heavy, but the MONTHLY_FALLBACK
distinction (Section 7) adds a comprehension burden with no structural
cue to slow the user down and actually read it, and each recommendation
card asks the user to read a full sentence-length reason rather than a
scannable label.

---

## 11. Shrine Card Inventory

Traced directly from `ShrineCardCompact.tsx` and its caller
`CompassRecommendationsSection.tsx` (which supplies only `name`, `address`,
`distanceM`, `reason`, `href`, `onDetailClick` — **not**
`imageUrl`, `trustMetadata`, `explanationOnlyFactText`, or `tags`, even
though the shared component supports all of them):

| Element | Shown for Compass? |
|---|---|
| Shrine name | YES (`<h3>`, truncated to 1 line) |
| Image / placeholder | **NO** — `imageUrl` is never passed; the image slot renders as an empty gray box (`bg-slate-100`) with no icon or "no photo" text |
| Match label / trust badges | **NO** — `trustMetadata` never passed |
| Reason / description | YES — one line, `line-clamp-1`, prefixed by the static label "相談内容・ご利益との一致" |
| Address | YES — one line, truncated |
| Distance | **Effectively never** — `ShrineCardCompact`'s own logic only shows `distanceM` when `address` is absent (`!address && distText`); Compass's candidate query always requires a non-empty address (`concierge_chat_candidates.py:84`), so `distance_m` — which the API does return — is suppressed in practice on every Compass card |
| Direction-related info | NO (shown once, above, for the whole result — not per-card) |
| Benefit / purpose match | YES (via the reason text) |
| Detail CTA | YES — "詳細だけ見る" |
| Route CTA | NO (only reachable via Shrine Detail, Section 14) |
| Save / favorite | NO |

Evaluated against the four questions:

```
1. Why this shrine?              PARTIAL -- one truncated, templated
                                  sentence ("Xのご利益で知られるYは、今の
                                  願いを願う参拝先として適しています。"
                                  observed verbatim in this session's
                                  earlier screenshots for two different
                                  shrines, differing only by name/goriyaku
                                  keyword)
2. Where is it?                  YES -- address shown
3. Why this one over the others? NO  -- no distance, no rank indicator, no
                                  trust label; the templated reason
                                  sentence shape is identical across cards
4. What can I do next?           PARTIAL -- one detail link, no route/save
                                  shortcut from the card itself
```

---

## 12. Card Differentiation

Two real reason strings observed in this session's earlier screenshots
(different shrines, same purpose selection):

```
"商売繁盛のご利益で知られる穴守稲荷神社は、今の願いを願う参拝先として適しています。"
"開運のご利益で知られる品川神社は、今の願いを願う参拝先として適しています。"
```

Both follow the identical template shape (`{goriyaku}のご利益で知られる
{name}は、今の願いを願う参拝先として適しています。`), differing only in
the substituted goriyaku keyword and shrine name. Combined with the
absence of distance (Section 11) and any rank/trust indicator, the UI
currently exposes **thin, template-shaped differentiation** — a user can
tell the shrines apart by name/address/goriyaku-keyword, but the card
content does not surface *why Ranking placed one above another*. This is
recorded as a UI-exposure finding only; **Recommendation Ranking itself
was not inspected beyond this boundary and was not changed.**

---

## 13. Detail CTA

```
Copy:          "詳細だけ見る" ("Just look at the details")
Visual weight: 11px, slate-400 (muted gray), positioned at the end of the
               address row via ml-auto
Tap target:    enlarged via -m-3 p-3 (negative margin + padding), giving an
               effective target well beyond the visible text -- consistent
               with this app's other 44px (min-h-11) tap-target convention
Association:   each link is generated per-card via buildShrineHref with
               that card's own shrineId/rank -- unambiguous
Competing actions: none -- exactly one CTA per card
```

**Classification: WEAK.** The copy is semantically clear and the tap
target is adequately sized, but the visual salience (small size, muted
color, right-aligned after other text) makes it easy to overlook on a
first pass — it reads more like fine print than a primary action.

---

## 14. Route / Visit Path

Traced: Compass result → (tap "詳細だけ見る") → Shrine Detail page →
(`GoogleMapRouteLink`, rendered by `ShrineDetailShell.tsx`) → external
Google Maps.

```
Direct route CTA on Compass result: NO
Taps required to start a route:     2 (detail link, then the route link
                                     on the Detail page)
Route action discoverable:          only after opening Detail; nothing on
                                     the Compass result screen hints a
                                     route action exists downstream
Matches existing app-wide pattern:  YES -- GoogleMapRouteLink hardcodes
                                     source="shrine_detail" universally;
                                     this is not a Compass-specific gap,
                                     every entry point (Concierge included)
                                     requires opening Detail first
```

**Classification: DISCOVERABLE** (not OBVIOUS — no on-result affordance
hints at it; not a dead end either — a user familiar with the app's
existing Detail-first pattern will find it in one additional tap).

---

## 15. Next-Action Clarity

```
COMMON:              OBVIOUS -- one CTA per card, nothing competes, no
                      ambiguity about what a tap does
MONTHLY_FALLBACK:     OBVIOUS for "what to tap next" (identical structure
                      to COMMON) -- the Section 7 subtlety is about
                      understanding the direction's *source*, not about
                      knowing what action to take
no_common_direction:  UNCLEAR -- matches Section 8's PARTIAL CONTINUATION
                      finding; no explicit next step is offered
```

---

## 16. Responsive — 375px

**Evidence**: real screenshot, this session's prior task, MONTHLY_FALLBACK
case with live recommendation cards.

```
Horizontal overflow:        none observed
Direction wheel:             not captured at this exact scroll position in
                              this session's screenshot (recommendation
                              cards were in view); the wheel component
                              itself is unchanged from the desktop capture
Note text wrapping:          wraps naturally to 3 lines, no truncation, no
                              clipping
Recommendation card width:   fits viewport width with appropriate margins
CTA clipping:                none -- "詳細だけ見る" fully visible
Address truncation:          one line, ellipsis where needed (by design,
                              `truncate` class)
Touch target density:        cards have adequate vertical spacing
                              (`space-y-3`)
```

## 17. Responsive — 390px

Same screenshot session, same case. Findings identical to 375px: no
overflow, note wraps to 2 lines instead of 3 (more horizontal room), cards
and CTA render cleanly.

## 18. Responsive — 430px

Same screenshot session. Note wraps to 2 lines; direction wheel visible in
this capture, rendered at full size, centered, no clipping of the 8
direction labels (including the wider two-character labels 北東/北西/南東/
南西). No horizontal scrolling at any of the three widths.

**Caveat**: all three responsive captures are from the MONTHLY_FALLBACK
case specifically (captured in the prior session's task). COMMON's
responsive rendering was not independently re-captured — it shares the
exact same `CompassDirectionVisual`/note-rendering structure and differs
only in note text length (COMMON's note is shorter, so no additional
wrapping risk is expected), so this is inferred, not independently
observed, for COMMON specifically.

---

## 19. Accessibility Quick Check

```
Button/link labels:      all interactive elements carry descriptive text
                          (confirmed via accessibility-tree reads earlier
                          this session -- "転機・仕事", "変更する", "今月
                          の方向を確認する", etc., all real button/radio
                          labels, not icon-only controls)
Direction wheel encoding: highlighted sectors are distinguished by BOTH
                          fill color AND bold/larger text
                          (fontWeight 700 vs 400, fontSize 15 vs 13,
                          CompassDirectionVisual.tsx) -- not color-only
Tap target sizing:       purpose chips, origin/birthdate inputs, and the
                          submit button all use the app's min-h-11 (44px)
                          convention; the Detail CTA's effective tap area
                          is enlarged via -m-3 p-3
Small/low-contrast text: the Detail CTA ("詳細だけ見る") is 11px,
                          slate-400 on a light background -- the smallest,
                          lowest-contrast text element in the flow
Color-only information:  none found -- every color-coded signal observed
                          (direction wheel, goriyaku labels where present)
                          is paired with text
```

**Finding**: the Detail CTA's small size/contrast (also noted in Section
13) is the only concrete, observed accessibility-adjacent concern; no
other obvious issue was found. This is not a full WCAG audit and no
contrast ratios were measured.

---

## 20. Analytics Event Trace

Traced directly (`searchEvents.ts`, `cardEvents.ts`, `CompassClient.tsx`,
`CompassRecommendationsSection.tsx`, `GoogleMapRouteLink.tsx`,
`ShrineDetailShell.tsx`):

```
compass_entry             -- fires once per mount
compass_result             -- fires once per resolved submit; carries
                              result_state, calculationMethod, purpose,
                              origin_mode, has_birthdate,
                              recommendation_count, recommendationInstanceId
card_view                  -- fires per rendered recommendation card
                              (recommendation_success only), source=compass,
                              shrineId, recommendationRank, recommendationInstanceId
shrine_detail_transition    -- fires on Detail CTA click, source=compass,
                              shrineId, recommendationRank,
                              recommendationInstanceId, position=compact
shrine_detail_view          -- fires on Shrine Detail mount when the URL
                              carries ctx=compass (built by buildShrineHref)
route_open                  -- fires on the Detail page's Google Maps link
                              click; source is hardcoded "shrine_detail"
                              (never "compass"), but ctx and
                              recommendationInstanceId ARE threaded through
                              from the URL and passed to this event
                              (ShrineDetailShell.tsx confirmed)
favorite_click / shrine_decision / visit_done / reflection_prompt_view --
                              same-page-render-only Compass attribution,
                              already documented as a limitation in
                              compass-posthog-query-contract.md
```

```
A. Compass result shown:               MEASURABLE (compass_result)
B. Shrine detail opened from Compass:  MEASURABLE (shrine_detail_transition
                                        source=compass + shrine_detail_view
                                        ctx=compass, joined by
                                        recommendationInstanceId/shrineId)
C. Route opened after Compass:         PARTIAL -- see Section 20-1
D. Save/favorite after Compass:        PARTIAL -- same-page-render-only
                                        attribution (pre-existing, documented
                                        limitation, not new)
E. Eventual visit/reflection:          PARTIAL -- same reason as D
```

### 20-1. A specific, previously-undocumented measurement nuance

`route_open`'s `source` property is **hardcoded to `"shrine_detail"`**
universally (`GoogleMapRouteLink.tsx:65-73`) — it is never `"compass"`,
even when the Shrine Detail page was reached via a Compass
recommendation. Compass attribution for `route_open` is only recoverable
via its separately-passed `ctx`/`recommendationInstanceId` properties, not
via `source`. A future analyst filtering `route_open` by `source =
"compass"` (the pattern that works for `card_view` and
`shrine_detail_transition`) would get **zero rows**, even though
Compass-attributed route opens do exist and are queryable via
`ctx`/`recommendationInstanceId`. This is not a Compass-specific defect —
it is the app-wide, pre-existing `route_open` contract (Section 14) — but
it was not called out explicitly in `compass-posthog-query-contract.md`'s
existing event table, which is why it is recorded as a finding here.

---

## 21. Compass → Detail Measurement Readiness

**YES**, a clean funnel already exists and is already documented in
`compass-posthog-query-contract.md` Section 3 ("Canonical Compass
Funnel"): `compass_result` → `card_view{source=compass}` →
`shrine_detail_transition{source=compass}` → `shrine_detail_view{ctx=compass}`,
joined by `recommendationInstanceId` + `shrineId`. No missing property
was found.

---

## 22. Compass → Route Measurement Readiness

**Classification: PARTIAL** (not full MEASURABLE, not NOT MEASURABLE).

The join is possible (`ctx`/`recommendationInstanceId` survive into
`route_open`, Section 20-1), but it requires knowing to join on those
properties instead of the `source` field that works for every other
event in the funnel — an easy, silent mistake. This audit does not
calculate any funnel rate (per this task's own instruction) — it only
assesses readiness.

---

## 23. Findings by Severity

**P1 — HIGH**

```
Issue:            MONTHLY_FALLBACK is semantically correct but visually
                   indistinguishable from COMMON (Section 7)
Evidence:          identical DetailSection/CompassDirectionVisual/note
                   styling; only the note's prose differs
User impact:       a skimming user may not register that this direction
                   carries less corroboration than a COMMON result
State affected:    MONTHLY_FALLBACK
Width affected:    all (375/390/430, structural, not width-dependent)
Likely owner:      CompassClient.tsx / CompassDirectionVisual.tsx (Frontend)
```

**P2 — MEDIUM**

```
Issue:            no_common_direction offers no explicit next action
Evidence:          Section 8 -- title+body only, no CTA/link, input form
                   remains present but unreferenced
User impact:       user is told what happened but not what to try next
State affected:    no_common_direction
Width affected:    all
Likely owner:      CompassClient.tsx (Frontend)
```

```
Issue:            Shrine card differentiation is thin/templated
Evidence:          Section 11-12 -- identical sentence template, no
                   distance, no rank/trust indicator surfaced
User impact:       hard to judge why one recommended shrine outranks
                   another
State affected:    recommendation_success (COMMON and MONTHLY_FALLBACK alike)
Width affected:    all
Likely owner:      ShrineCardCompact.tsx / CompassRecommendationsSection.tsx
                   (Frontend); underlying Reason content is Recommendation
                   Authority's domain, not changed or judged here
```

```
Issue:            route_open Compass attribution requires ctx/
                   recommendationInstanceId, not source (Section 20-1)
Evidence:          GoogleMapRouteLink.tsx:65-73
User impact:       none directly (this is an analytics/measurement risk,
                   not a user-facing issue)
State affected:    N/A (analytics documentation gap)
Width affected:    N/A
Likely owner:      compass-posthog-query-contract.md (docs), no code owner
```

**P3 — LOW**

```
Issue:            Detail CTA is small/low-contrast (11px, slate-400)
Evidence:          Section 13, 19
User impact:       minor discoverability friction
State affected:    recommendation_success
Width affected:    all
Likely owner:      ShrineCardCompact.tsx (Frontend, shared with other
                   surfaces -- not Compass-exclusive)
```

```
Issue:            Empty image slot (gray box, no icon/placeholder text)
Evidence:          Section 11 -- imageUrl never passed for Compass
User impact:       could visually read as a broken image rather than an
                   intentional no-photo state
State affected:    recommendation_success
Width affected:    all
Likely owner:      CompassRecommendationsSection.tsx (Frontend)
```

No **P0 — BLOCKING** finding exists: at no observed or traced state does a
user become unable to complete the intended flow.

---

## 24. UX Change Decision

```
F — MULTIPLE NARROW UX FIXES REQUIRED
```

Not **B** alone (copy/hierarchy) — Section 11/12's card-content finding
and Section 20-1's analytics-documentation finding are independent of
copy. Not **C** alone (card content) — Section 7/8's findings are
copy/hierarchy, not card-content. Not **H** (major redesign) — nothing
found rises above P1, and the overall architecture (Section 5, 9) was
found sound with no dead ends, no P0s, and a working, documented funnel to
Detail (Section 21). Not **G** (Analytics gap prevents evaluation) — this
audit *was* able to evaluate the funnel; only one narrow, PARTIAL nuance
was found (Section 22), not a blocking gap.

---

## 25. Recommended Follow-up

Narrow, independent future PRs (not implemented here; sequencing example
only, per this task's own instruction not to combine unrelated fixes):

```
PR1 -- no_common_direction next-action affordance (copy/hierarchy only):
       add an explicit suggested next step (change purpose/origin, or a
       pointer to Concierge) without implying retry-with-same-inputs will help.

PR2 -- MONTHLY_FALLBACK visual reinforcement: a UX-polish pass (icon,
       tone, or label) making the fallback distinction easier to notice at
       a glance, on top of the already-contract-compliant copy (#2512).
       This is additive polish, not a correction -- the existing UI/
       Analytics Boundary audit (compass-monthly-fallback-ui-analytics-
       boundary.md Section 10) already concluded copy alone satisfies the
       Signal-to-Explanation Rule; this PR would be about clarity, not
       compliance.

PR3 -- Shrine card differentiation review: owned by whoever holds
       Recommendation Reason/card-content decisions, not Compass-specific;
       out of this audit's authority to prescribe further than "the UI
       currently under-exposes distinguishing information."

PR4 -- Documentation-only: add the route_open source="shrine_detail"
       Compass-attribution caveat (Section 20-1) to
       compass-posthog-query-contract.md, so a future query author does
       not silently get zero rows filtering by source="compass".
```

---

## 26. Implementation Follow-up Definitions

> Canonical follow-up definitions for this audit, as directed by the
> repository owner. These are **definitions only** — no follow-up is
> implemented by this document, and none is prioritized over another
> beyond the dependency notes given per item. The audit's existing
> findings (Sections 6-23) and UX Change Decision (Section 24: **F —
> MULTIPLE NARROW UX FIXES REQUIRED**) are unchanged by this section — no
> severity classification is revised here, because no new evidence was
> gathered; this section only structures the four findings already on
> record into actionable future-PR shape.

### 26-1. Follow-up 1 — COMMON / MONTHLY_FALLBACK Visual Distinction

```
Problem:  Copy already distinguishes COMMON from MONTHLY_FALLBACK
          correctly (#2512), but the visual treatment is structurally
          identical -- a user who does not read the note carefully cannot
          tell the two apart at a glance.
Goal:     A user can identify COMMON vs. MONTHLY_FALLBACK without reading
          the explanatory note closely.
```

**Evidence from this audit**: Section 7 (Classification B — SEMANTICALLY
CORRECT BUT TOO SUBTLE); Section 23's P1 finding (highest severity in this
audit).

```
Scope:    CompassClient.tsx's direction-card rendering and/or
          CompassDirectionVisual.tsx -- a visual/structural treatment
          (e.g. tone, icon, or label) layered on top of the existing,
          already-correct copy. Frontend UX only.
Constraints / Non-goals:
  - Runtime unchanged -- calculationMethod remains the sole source of
    truth for which branch renders; no new runtime field required.
  - Recommendation Ranking unchanged.
  - Analytics instrumentation unchanged.
  - Must NOT introduce error framing -- MONTHLY_FALLBACK is a legitimate
    result (compass-product-contract.md Section 2.2-3), not a degraded or
    failed one; visual treatment must not read as a warning/error state.
  - Must not weaken or contradict the existing, contract-compliant copy
    (Section 2.2-7's Signal-to-Explanation Rule requirement) -- this is
    additive polish, not a copy rewrite.
Done Definition:
  - COMMON and MONTHLY_FALLBACK are visually distinguishable without
    reading the note text closely.
  - No layout regression at 375px / 390px / 430px (Sections 16-18's
    baseline must still hold).
  - Existing semantics (both the copy and the underlying calculationMethod
    contract) preserved exactly.
Likely affected component/docs:
  apps/web/src/features/compass/CompassClient.tsx,
  apps/web/src/features/compass/components/CompassDirectionVisual.tsx
Proposed future PR boundary:
  PR1 -- Frontend UX only, per the repository owner's directive. Does not
  touch Runtime, Ranking, Analytics, Concierge, DB, or the Product/Runtime
  Contract.
```

### 26-2. Follow-up 2 — `no_common_direction` Continuation

```
Problem:  The result itself is already explained correctly and honestly,
          but offers no explicit next action -- the message stops at
          "here's what happened" without "here's what you could try."
Goal:     no_common_direction stops being a dead end.
```

**Evidence from this audit**: Section 8 (Classification: PARTIAL
CONTINUATION); Section 15 (Next-Action Clarity: UNCLEAR for this state);
Section 23's P2 finding.

```
Scope:    CompassClient.tsx's no_common_direction messaging block --
          adding an explicit next-action affordance (e.g. a prompt to
          change purpose/origin, or a pointer to Concierge). Frontend
          navigation/CTA only.
Constraints / Non-goals:
  - Retry must NOT be framed as the primary CTA -- Product Contract
    Section 2.1-2 already establishes retry is not a meaningful solution
    (the calculation is deterministic for the same inputs/month).
  - Must not reframe this state as an input error -- birthdate/origin
    validity is unrelated to this state (Section 2.1-1's definition,
    unchanged).
  - Runtime unchanged -- no new state, no new trigger condition.
  - Must preserve the existing, narrowed residual semantics (#2508/#2517)
    -- do not reintroduce pre-#2508 framing.
Done Definition:
  - An explicit next action exists and is visible without scrolling logic
    changes elsewhere.
  - No error-style language or visual treatment is introduced.
  - Existing Compass semantics (Section 2.1, 2.2-4) remain intact.
Likely affected component/docs:
  apps/web/src/features/compass/CompassClient.tsx
Proposed future PR boundary:
  PR2 -- Frontend navigation/CTA only, per the repository owner's
  directive. Does not touch Runtime, Ranking, Analytics, Concierge, DB, or
  the Product/Runtime Contract.
```

### 26-3. Follow-up 3 — Shrine Card Differentiation

```
Problem:  Multiple recommended shrines are not sufficiently distinguished
          on their cards -- reason text follows an identical template
          shape, distance is computed but suppressed, and no rank/trust
          indicator is shown.
Goal:     A user can compare candidates and choose one.
```

**Evidence from this audit**: Section 11 (card question-by-question
evaluation: "why this one over others" = NO); Section 12 (two real
templated reason strings observed, differing only by substituted
name/goriyaku keyword); Section 23's P2 finding.

```
Scope:    Presentation of already-available recommendation data on the
          existing card (ShrineCardCompact.tsx /
          CompassRecommendationsSection.tsx) -- e.g. surfacing distance
          (already computed, currently suppressed), or varying which
          already-passed fields are shown. Frontend presentation only,
          using existing recommendation data only.
Constraints / Non-goals:
  - No Ranking change -- candidate order, scoring, and Recommendation
    Reason generation are Recommendation Authority's domain
    (compass-product-contract.md Section 6), untouched here.
  - No new score, weight, or ranking signal introduced.
  - No DB schema change -- only fields already returned by the API
    (e.g. distance_m, already present but suppressed by
    ShrineCardCompact's own display logic) may be surfaced differently.
Done Definition:
  Each card sufficiently answers:
  - Why this shrine?
  - Where is it?
  - What's different about it from the other candidates?
  - What can I do next?
Likely affected component/docs:
  apps/web/src/components/shrines/ShrineCardCompact.tsx,
  apps/web/src/features/compass/components/CompassRecommendationsSection.tsx
Proposed future PR boundary:
  PR3 -- Frontend presentation only, using existing recommendation data
  only, per the repository owner's directive. No Ranking or DB changes.
  Underlying Recommendation Reason *content* generation remains outside
  this PR's authority (Section 12's own boundary note).
```

### 26-4. Follow-up 4 — Compass Route Attribution Contract

```
Problem:  route_open's source property alone cannot identify a
          Compass-originated route action -- it is hardcoded
          "shrine_detail" universally, regardless of entry point.
Goal:     Clarify the Compass -> Detail -> Route measurement contract.
```

**Evidence from this audit**: Section 20-1 (`GoogleMapRouteLink.tsx:65-73`
hardcodes `source: "shrine_detail"`; Compass attribution survives only via
`ctx`/`recommendationInstanceId`, confirmed threaded through by
`ShrineDetailShell.tsx`); Section 22 (Classification: PARTIAL, not NOT
MEASURABLE — the properties already exist, the gap is that they are
undocumented as the correct join key).

```
Scope:    Docs-only investigation first, per the repository owner's
          directive -- determine whether the existing ctx/
          recommendationInstanceId properties on route_open are
          sufficient to answer "was this route opened after a Compass
          recommendation," and if so, document that query contract
          explicitly. Do not add instrumentation until that
          investigation concludes it is actually insufficient.
Constraints / Non-goals:
  - No new Analytics event.
  - Must verify existing properties are proven insufficient before
    proposing any instrumentation change -- this audit's own trace
    (Section 20-1) found the properties already survive the join; the
    gap identified is documentation, not missing data.
  - Any future instrumentation PR (only if genuinely needed) remains
    out of this follow-up's initial scope.
Done Definition (either of):
  - compass-posthog-query-contract.md is updated to explicitly define the
    Compass -> Route query (joining route_open on ctx=compass AND/OR
    recommendationInstanceId, not source), closing the gap with existing
    properties; OR
  - if that investigation instead finds the existing properties
    insufficient, a single, minimal Instrumentation Gap is defined (not
    implemented) naming exactly what property is missing and why
    ctx/recommendationInstanceId do not already cover it.
Likely affected component/docs:
  docs/analytics/compass-posthog-query-contract.md (primary);
  apps/web/src/components/shrine/GoogleMapRouteLink.tsx (reference only,
  not necessarily changed)
Proposed future PR boundary:
  PR4 -- Docs/Analytics contract investigation first, per the repository
  owner's directive. An instrumentation PR is only defined as a *future*
  possibility, contingent on that investigation's outcome -- not assumed
  necessary by this document.
```

### 26-5. Dependency Notes (not a priority decision)

```
Follow-ups 1, 2, and 3 are independent of each other and of Follow-up 4 --
none blocks another. Follow-up 4 is independent of the other three (it
concerns Detail->Route measurement, not the result screen itself). No
follow-up depends on another completing first. This section records
independence only; it does not rank or sequence the four beyond what
Sections 26-1 through 26-4 already state as their own proposed PR
boundary.
```

---

## 27. Non-goals

This audit does not:

- Change Compass direction logic, Monthly Fallback runtime, Recommendation
  Ranking, candidate filtering, shrine DB data, Concierge, Analytics
  instrumentation, the Product/Runtime Contract, or the DB.
- Implement any of Section 25's recommended follow-ups, or Section 26's
  finalized follow-up definitions.
- Calculate any Compass → Route or Compass → Detail funnel rate.
- Perform a full WCAG accessibility audit (Section 19 is a quick check
  only).
- Reproduce `no_common_direction` in a live browser this session (Section
  4's stated limitation).
- Make a final implementation priority decision beyond Section 26-5's
  independence notes.
- Add any new Analytics event (Section 26-4 explicitly rules this out for
  its own follow-up).

---

## 28. Impact

```
Production code changed:          NO
Frontend production code changed: NO
Backend production code changed:  NO
Analytics instrumentation changed: NO
Runtime changed:                  NO
Recommendation Ranking changed:   NO
Concierge changed:                NO
DB changed:                       NONE
Migration:                        NONE
```

---

## 29. Verification

```
git status --short   -> only this document (+ known untracked
                         apps/web/AGENTS.md, apps/web/CLAUDE.md, excluded)
git diff --stat       -> only this document
git diff --check      -> clean
```

Every code citation in this document was re-read directly from current
`develop` in this session. No screenshot containing QA personal input
(birthdate) is committed. `no_common_direction` production observation
is explicitly marked unavailable (Section 4), not fabricated. Live
interactive browser evidence for this turn specifically was not obtainable
(Section 0) — this is disclosed, not concealed, and existing automated
tests plus this session's own prior real screenshots were used as the
next-best evidence tier instead of guessing.
