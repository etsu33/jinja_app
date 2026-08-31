# Premium Meaning UI Direction & Implementation PR Plan

Branch: `design/premium-meaning-ui-direction`
Type: **design decision + implementation planning.** No production UI, business logic,
generation, entitlement, analytics, or routing changes in this task.
Baseline: `origin/develop` @ `d46ab4ff` (`docs: audit Deep Reason and Premium UI connection (#2656)`).
Inputs: `docs/audit/deep-reason-premium-ui-connection.md` (#2656), current production
components, `apps/web/src/styles/tokens.css`, existing tests.

---

## 1. Audit Findings Used

From #2656, the findings that materially drive this decision. Split per instruction into
**Confirmed** (repo/audit evidence), **Interpretation** (design conclusion from that
evidence), **Open Decision** (needs Mother Ship).

### 1.1 Confirmed

| Ref | Finding |
|---|---|
| A-C1 | Concierge Result stacks **5 near-identical `conciergeSoftCardClass` surfaces** (runtime match, trust, history, shrine meaning, action meaning) + a 6th near-identical surface (consultation summary). `ConciergeSectionsRenderer.tsx:53`, blocks `:1003 :1029 :1051 :1065 :1076 :1091`. |
| A-C2 | Reading order is wrong for the target flow: `consultation_summary` (FREE context) renders **after** `shrine_meaning` + `action_meaning` (PREMIUM teasers). `ConciergeSectionsRenderer.tsx:1065→1076→1091`. |
| A-C3 | Guest/Free: `shrine_meaning` and `action_meaning` each render a **full bordered card whose entire body is one "Premiumで読めます" sentence** + a caption. `:1073-1078 :1082-1087`. |
| A-C4 | **No heading scale.** Section identity is only `text-xs font-semibold tracking-[0.12em] text-[--kt-color-text-muted]`; body uniformly `text-sm leading-7 text-secondary`. Primary/Secondary/Tertiary use identical type. |
| A-C5 | Only two surfaces in active use on the result screen: `bg-background-subtle` and `bg-surface-default`; `shadow-medium` applied uniformly so elevation conveys nothing. |
| A-C6 | Premium is expressed as **amber border + amber fill + "Premium" wording**, repeated in `ConciergePremiumEntryCard`, `PremiumUpgradePrompt`, `ShrineDetailStateDeltaSection` (non-premium branch), `PremiumStateDeltaCard` (non-premium branch) — up to **4 amber upsell boxes across the two screens**, same visual treatment for CTA-A and CTA-B. |
| A-C7 | CTA competition: for a logged-in free user at quota, `ConciergePremiumEntryCard` (CTA-A) + `save_prompt` + `isUiPaywall` box (CTA-C) can stack consecutively. `ConciergeClientFull.tsx:1944-1987`. |
| A-C8 | Presentation duplication: `runtimeMatchLines` ("今回の相談との接点") vs `shrine_meaning` ("相談から見た意味") answer the same question; `historyThemeDisplay` and `shrine_meaning` both framed "（KAMI MUSUBIの解釈）"; the two teaser one-liners are the same sentence pattern. |
| A-C9 | `recommendation_meta` ("Recommendation Evidence" / rank reason) is generated + fires a `card_view` event but **has no JSX**. `RecommendationMetaSection.tsx` imported nowhere. |
| A-C10 | **Deep Recommendation Reason v1 (`buildDeepRecommendationReason`) reaches no production surface.** Production "deep" meaning is the older heuristic `buildMeaningNarrative` / `buildStateNarrative` / `buildDeepReason` + backend `recommendation_reason_v4_detail`. |
| A-C11 | Mobile @375px (static): CTA `<a>` links are `text-xs px-3 py-2` (~30–34px, under 44px); `ConciergeConsultationSummary` 3-pill header wraps; `grid-cols-2` fallback buttons wrap to uneven heights. |
| A-C12 | `cardVisibility.ts` contract is internally consistent, matches the fixed boundary, and shows **no body-content leak** post-#2654. |

### 1.2 Interpretation

| Ref | Conclusion | From |
|---|---|---|
| A-I1 | The screens need **hierarchy (type + surface tier + spacing)**, not more containers. The audit's own lean ("B now → A target, reject C") endorses reducing card stacking. | A-C1, A-C4, A-C5 |
| A-I2 | The teaser must become a **faded continuation inside its section**, not a separate empty card; that removes A-C3 and one instance of A-C6 at once. | A-C3, A-C6 |
| A-I3 | Premium should be **one transition point per screen**, not a treatment repeated per gated block. | A-C6, A-C7 |
| A-I4 | `consultation_summary` belongs **above** the deep-meaning layers, as the "why it connects to this consultation" step. | A-C2 |
| A-I5 | `runtimeMatchLines` + `historyThemeDisplay` + `shrine_meaning` should be **merged into one "meaning" narrative**, not three adjacent surfaces asking overlapping questions. | A-C8 |
| A-I6 | Any restructure can proceed on the **current heuristic meaning text**; it must not claim to render "Deep Recommendation Reason v1". | A-C10 |

### 1.3 Open Decision (carried to §13)

* D-1 UI direction (A / B / C).
* D-2 `recommendation_meta`: render into FREE, or delete component + its `card_view` event.
* D-3 Whether the restructure may add **one** additive variant to the shared `DetailSection`
  component (`plain`/`bare`, borderless) — needed by Directions A and C.
* D-4 Whether `docs/audit` non-UI follow-ups N1–N4 (Deep Reason connection, name
  collision, double-CardId, dead code) are sequenced before/after PR-G work.
* D-5 Collapsible evidence: are `<details>`/disclosure acceptable for Layer 6, or must
  hierarchy+spacing alone carry it (audit Phase-D caution).

---

## 2. Current UI Architecture

Actual production component tree at `d46ab4ff`.

### 2.1 Concierge Result

```
ConciergeClientFull
└ ConciergeLayout                         mx-auto max-w-4xl px-4  (no bottom chat bar in normal mode)
  └ <div class="p-4 space-y-5">
     ├ (isFiltering banner)               rounded-3xl border bg-background-subtle
     ├ ConciergeSectionsRenderer          mx-auto max-w-md lg:max-w-2xl space-y-4
     │   payload.sections.map():
     │   ├ "filter"  → DetailSection(variant=secondary) | ConciergeFilterPanel (+ preset chips)
     │   └ "recommendations" → DetailSection(variant=secondary, title)
     │       ├ ModeBadge
     │       ├ "あと N回まで無料で試せます"                        ← quota copy (CTA-C family)
     │       ├ bannerText                                          conciergeNoticeCardClass (amber)
     │       ├ fallback: grid-cols-2 buttons
     │       ├ appliedLabel chip                                   conciergeSoftCardClass
     │       ├ HERO block (space-y-2):
     │       │   ├ ConciergeTopRecommendationHero
     │       │   │     name · eyebrowLabel · conclusionLines · actionReason
     │       │   │     PRIMARY CTA  "神社の詳細を見る"  bg-[--kt-color-action-primary]   ← the one strong CTA
     │       │   ├ DirectionReferenceCard
     │       │   ├ runtimeMatchLines      section  conciergeSoftCardClass   "今回の相談との接点"
     │       │   ├ trustMetadata          section  conciergeSoftCardClass
     │       │   ├ historyThemeDisplay    section  conciergeSoftCardClass   "…（KAMI MUSUBIの解釈）" / "この神社が持つ文脈"
     │       │   ├ shrine_meaning         section  conciergeSoftCardClass   "相談から見た意味（KAMI MUSUBIの解釈）"   [teaser: guest/free]
     │       │   ├ action_meaning         section  conciergeSoftCardClass   "今の自分への問い"                        [teaser: guest/free]
     │       │   ├ ConciergeConsultationSummary     rounded-2xl border bg-surface-default shadow-sm   "今回の相談の整理"
     │       │   ├ ShrineSaveButton (variant=subtle)
     │       │   └ ConciergePremiumEntryCard        conciergePremiumCardClass (amber)                 ← CTA-A
     │       ├ "迷った時だけ、ほかの神社を見る" toggle → ShrineCardCompact[]
     │       ├ placeItems → PlaceShrineCard[]
     │       └ save_prompt button   "あとで見返すために保存" / "ログインしてあとで見返す"
     ├ PremiumStateDeltaCard          rendered only when previous_comparison !== "hidden" (premium)   ← CTA-B
     ├ ConciergeDebugPanel
     └ isUiPaywall box                "無料回数を使い切りました。" + "有料プランを見る"                ← CTA-C
```

Meaning data for the hero block is built inline:
`buildRecommendationReasonViewModel({rec, reasonFacts, mode, needTags})` → `reason` /
`state` / `meaning` narrative builders → `reasonVm.detail.{consultationSummary,
shrineMeaning, actionMeaning}` + `conclusionLines` (Hero). **Heuristic, need-tag driven.**

### 2.2 Shrine Detail

```
shrines/[id]/page.tsx  →  ShrineDetailShell  →  ShrineDetailArticle  (<article class="space-y-4">)
├ <section class="space-y-5">
│   ├ ShrineDetailHeroHeader            rounded border bg-surface-default shadow-medium   title + "この神社の意味" + copy
│   ├ ShrineDetailHeroCard              image
│   ├ directionSupportCopy              rounded border bg-background-subtle               (optional)
│   ├ ShrineDetailStateDeltaSection     amber CTA-B branch when !premium; only if actionState ∈ {visited, reflected}
│   └ after-visit copy                  rounded border emerald                           (optional)
├ ShrineDetailSections(contextReasonSections)     → ShrineReasonSection | ShrineProposalSection | ShrineSupplementSection   (each: rounded border bg-surface-default p-4)     ← context_reason (FREE)
├ personalMeaningVisibility === "visible" → ShrineDetailSections(premiumSections)
│      → ShrineJudgeSection (<details> rounded border)  |  ShrineActionSection (per-item bg-premium-surface border-premium-border shadow-medium)
├ personalMeaningVisibility === "teaser"  → PremiumUpgradePrompt   rounded border-amber-100 bg-amber-50/70   ← CTA-A
├ ShrineFactSection                     rounded border                                   (shrine-public facts)
├ ShrineDeepDivePrompt                  rounded border
├ save / visit / reflection block       rounded border emerald  →  nested inner rounded border  →  nested ShrineReflectionPrompt (rounded border emerald)
├ PublicGoshuinSection                  DetailSection
└ fallback benefit                      DetailDisclosureBlock
```

`recommendation_meta` — **not in the tree** (generated + tracked, never rendered; A-C9).

### 2.3 Shared building blocks already available

| Component | Capability | Current use |
|---|---|---|
| `DetailSection` (`components/shrine/DetailSection.tsx`) | **3-tier `variant` (`primary` / `secondary` / `tertiary`)** — each with its own surface, padding, shadow, and title class; renders the title as `<h2>`. | Compass (`CompassClient.tsx`) uses all 3 variants deliberately. Concierge Result uses **only** the default `secondary` as the outer wrapper; the 6 stacked meaning cards do **not** use it. Shrine Detail uses it only for `PublicGoshuinSection` / shell. |
| `DetailDisclosureBlock` | Collapsible titled block. | Shrine Detail fallback benefit; StateDelta breakdown. |
| `conciergeSoftCardClass` / `conciergeNoticeCardClass` / `conciergePremiumCardClass` | Local const class strings in `ConciergeSectionsRenderer.tsx:53-60`. | The 6-card stack + notices + premium box. |

**Key architecture fact:** the hierarchy primitive the audit asks for (`DetailSection`
variants, `<h2>` titles, distinct surface tiers) **already exists and is already used
this exact way on the Compass screen.** The Concierge Result / Shrine Detail meaning
content simply does not use it.

---

## 3. Current Design-System Constraints

From `apps/web/src/styles/tokens.css` (Design Token v1, 3-layer: Tailwind primitive →
`--kt-*` semantic → light/`.dark` theme). Components reference the semantic layer only.

### 3.1 Reusable tokens

| Role | Light | Dark | Note for this work |
|---|---|---|---|
| `--kt-color-background-base` | white | `#07101f` | page ground |
| `--kt-color-background-subtle` | slate-50 | `#0b1424` | the **recessed** surface (tertiary) |
| `--kt-color-surface-default` | white | `#101827` | the **raised** surface (primary/secondary content) |
| `--kt-color-surface-elevated` | white | `#0b1424` | **light-mode: identical to `surface-default`** — no elevation step available |
| `--kt-color-text-primary / -secondary / -muted / -inverse` | slate-900 / -700 / -500 / white | `#f7f0e3` / `#a99b80` / `#c4b89a` / white | the only text ramp |
| `--kt-color-border-default / -strong / -focus` | slate-200 / -300 / emerald-300 | `#384154` / slate-500 / emerald-400 | |
| `--kt-color-action-primary (+ -hover, -text)` | emerald-600 / -700 / white | emerald-500 / -400 / white | brand / Primary CTA |
| `--kt-color-premium-accent / -surface / -border` | amber-700 / amber-50 / amber-200 | amber-500 / amber-950 / amber-800 | **the only Premium tokens** |
| `--kt-color-status-success-*` | emerald 600/800/50/200 | emerald 300/200/950/800 | after-visit / saved states |
| `--kt-radius-{control,card,panel,image,pill}` | md / 2xl / xl / xl / full | — | card = `rounded-2xl` |
| `--kt-shadow-{none,low,medium,high,brand}` | none / xs / sm / lg / emerald-tint | — | **the elevation lever in light mode** |
| `--kt-space-{page-x,section-y,card,control-x,control-y,inline-gap,stack-gap}` | 16 / 24 / 16 / 16 / 8 / 8 / 12 px | — | `section-y` (24) is the only "between-section" step defined; the screens currently use `space-y-4` (16) everywhere |

### 3.2 Constraints / limitations

1. **No typography scale tokens.** No `--kt-font-*` / size / line-height / weight
   tokens. Heading hierarchy must be built from Tailwind utilities directly. The
   de-facto scale is `DetailSection`'s title classes:
   * primary `text-base font-semibold text-primary`
   * secondary `text-sm font-semibold text-primary`
   * tertiary `text-xs font-semibold text-muted`
   Any new heading level (e.g. an in-section `<h3>` for Layer 3–5) must be defined as a
   documented utility combo, reused verbatim, **not** a new token system.
2. **No light-mode elevation step.** `surface-default` == `surface-elevated` == white.
   The two usable light surfaces are **white** (raised) and **slate-50** (recessed).
   Elevation differences in light mode come from **shadow** (`--kt-shadow-low/medium/high`)
   and **padding**, not colour. Directions must not invent a third surface colour.
3. **`section-y` (24px) exists but is unused** — the screens hard-code `space-y-4`
   (16px). Adopting `space-y-6` at section boundaries is a token-aligned change (matches
   `--kt-space-section-y`), not a new value.
4. **Premium = amber only.** No "premium gradient", no second premium colour. A restrained
   Premium transition must be built from `premium-surface` (amber-50) + `premium-border`
   (amber-200) + whitespace + type, used **once** per screen.
5. **`DetailSection` has no borderless variant.** Directions A and C need one; adding a
   `plain` variant (no border, no shadow, transparent bg, `<h2>` title kept) is a single
   additive change to a shared component with existing tests — **D-3**.
6. Dark mode is fully defined for every token above; any class the plan introduces must
   use `--kt-*` (never raw `amber-*` / `slate-*` literals) so dark mode stays correct.
   The current code already violates this in places (`bg-amber-50/70`,
   `border-amber-100`, `text-amber-950`, `bg-emerald-50` literals) — the restructure PRs
   should replace those with tokens **only where they touch the markup anyway** (no
   opportunistic sweep).

### 3.3 What can be achieved with the existing system

* A real 3-level hierarchy — **yes**, via `DetailSection` variants (already proven on Compass).
* Distinct Primary surface — **yes**, via `shadow-high` + `border-strong` + `p-6` (the `primary` variant), no new colour.
* Recessed Tertiary — **yes**, via `background-subtle` + no shadow (the `tertiary` variant).
* Borderless editorial sections — **needs D-3** (one additive `DetailSection` variant).
* Teaser fade — **yes**, CSS `mask-image` / gradient over `background-base`→transparent; no new token.
* Restrained Premium transition — **yes**, `premium-surface` + single `premium-border` hairline + whitespace; used once.
* Typographic hierarchy — **yes**, but hand-rolled utility combos, documented in the PR.

---

## 4. Three Visual Directions

Three genuinely different models. All keep `cardVisibility.ts`, generation, ranking,
entitlement, analytics, and routing unchanged.

### Direction A — "Editorial Journey"

**Concept.** The recommendation result reads as a single written piece. One column, a
page-level title (shrine name + one-line meaning), then labelled passages separated by
**whitespace and a hairline**, not boxes. The recommendation is the opening; each
Meaning layer is the next paragraph of the same story; Premium is where the story
continues deeper, in the same column.

**Layout model.** Vertical, borderless. `<h2>` per layer (Layers 1–6), optional `<h3>`
for sub-points. `space-y-6` between layers, `space-y-3` within. Full-bleed text at the
`max-w-md` measure. The only boxed elements: the shrine hero image, and the
save/visit/reflection block (genuine interaction).

**Information hierarchy.**
* Primary = the shrine name `<h1>` + one-line meaning + the "神社の詳細を見る" CTA (kept as the single filled button).
* Secondary = Layers 2–5 body text, `text-[15px] leading-7 text-primary`, `<h2>` `text-base font-semibold`.
* Tertiary = Layer 6 evidence (trust, history detail, rank reason, "other shrines"), `text-sm leading-6 text-secondary` under a muted `<h3>`, or in a `DetailDisclosureBlock` (D-5).

**Premium treatment.** At the Free→Premium boundary the column gets: `space-y-6` gap →
a thin `premium-border` hairline → the deep content on a **subtle `premium-surface`
(amber-50) tint that bleeds to page edge** (no rounded box) → for Free/Guest the first
~2 lines render then fade (`mask-image` to transparent) into **one** CTA-A line
("この神社を選ぶ意味を深掘りする"). Premium users just see the tint + full text, no CTA.

**Component impact.**
* `ConciergeSectionsRenderer` recommendations branch: rewrite the hero block; drop `conciergeSoftCardClass` from runtime-match / trust / history / shrine-meaning / action-meaning; merge runtime-match + history into the shrine-meaning narrative (A-I5).
* `ConciergeConsultationSummary`: strip the box + pills → `<h2>` + paragraph; move above the deep layers (A-I4).
* `ShrineDetailArticle` sections 6–10: same borderless treatment; `ShrineReasonSection` / `ShrineJudgeSection` / `ShrineActionSection` lose outer `border`/`bg`/`shadow` (keep for `saveActionNode`).
* `DetailSection`: add `plain` variant (D-3).
* `PremiumUpgradePrompt` / `ConciergePremiumEntryCard`: replace the amber box with the fade+hairline+one-line CTA.

**Design-token impact.** Existing tokens sufficient **except D-3** (one `DetailSection`
variant). `space-y-6` = `--kt-space-section-y`. Fade uses a gradient over
`--kt-color-background-base`. No new colours.

**Mobile @375px.** Best outcome: shortest page, fewest tap targets, clearest
transitions, no repeated chrome. Risk: the fade's last visible line must stay legible at
375px (test); borderless sections rely on spacing discipline that must survive dynamic
content lengths.

**Strengths.** Removes A-C1, A-C3, A-C5, A-C6 (mostly), A-C8, and most of the scroll
inflation. Premium reads as depth (A-I2/I3). Matches the target reading flow literally.
Aligns with the "contemporary first, restraint over decoration" principle.

**Risks.** Largest DOM diff. Needs a firm type-scale decision applied consistently or it
degrades into unstyled text. Borderless + variable content can look unstructured if
spacing is sloppy. Under-selling Premium if the fade is too subtle (needs design QA at 3
viewports × 3 access states).

**Implementation cost — Medium.** ~2 structural PRs (one per screen) + the shared
`DetailSection` variant. No token architecture work.

---

### Direction B — "Layered Native Surfaces"

**Concept.** Keep an app-like surface model, but make surfaces **mean** something: one
tier per hierarchy level, and far fewer of them. Use `DetailSection` variants exactly as
Compass already does.

**Layout model.** 3 surfaces on Concierge Result instead of 8:
1. **Hero** — `DetailSection variant="primary"` (or the existing Hero component) — shrine + core reason + CTA.
2. **意味** — `DetailSection variant="secondary"` — one surface containing Layers 2–5 as `<h3>` sub-sections with internal dividers (`border-t --kt-color-border-default`), not per-item cards. Premium content sits inside this surface with one CTA-A row at its foot.
3. **根拠・詳細** — `DetailSection variant="tertiary"` (recessed, `background-subtle`, no shadow), optionally `DetailDisclosureBlock` — trust, history detail, rank reason, "other shrines".

**Information hierarchy.** Carried by the variant: `primary` (border-strong, shadow-high,
p-6, `text-base` title) > `secondary` (border-default, shadow-medium, p-5, `text-sm`
title) > `tertiary` (background-subtle, no shadow, p-4, `text-xs` muted title). This is
already the shipped Compass hierarchy.

**Premium treatment.** One `premium-surface` (amber-50) block **inside** the 意味
surface (a nested region, `border-t --kt-color-premium-border`), with the teaser fade
for Free/Guest and exactly one CTA-A. No amber box anywhere else; `PremiumStateDeltaCard`
and `ShrineDetailStateDeltaSection` (CTA-B) keep their own surface but adopt the same
restrained styling so CTA-A and CTA-B stop looking identical (A-C6).

**Component impact.**
* `ConciergeSectionsRenderer`: wrap Layers 2–5 in one `DetailSection secondary`; wrap Layer 6 in one `DetailSection tertiary`; delete the 5 `conciergeSoftCardClass` usages; internal `<h3>` + `border-t` dividers.
* `ConciergeConsultationSummary`: becomes the first `<h3>` sub-section of the 意味 surface (or a slim `secondary`), reordered above deep layers.
* `ShrineDetailArticle`: group sections 6–10 into `secondary` (meaning) + `tertiary` (facts/evidence/deep-dive).
* `DetailSection`: **no change** (variants already exist).
* Premium components: restyle to the shared restrained treatment, one CTA each.

**Design-token impact.** **None.** Everything is existing `DetailSection` variants +
existing tokens. `space-y-6` between the 3 surfaces = `--kt-space-section-y`.

**Mobile @375px.** Fewer borders/shadows, ~2 card-heights saved, collapsible Tertiary
removes evidence from the default viewport. Still visibly "boxed" — less calm than A.
Two large surfaces can feel monolithic if internal dividers are weak.

**Strengths.** Lowest risk and cost; **zero new primitives**; proven on Compass;
directly kills A-C1, A-C3 (teaser inside a surface, not its own card), A-C6 (one Premium
region), A-C7 (one CTA in the meaning area). Fully reversible.

**Risks.** Doesn't deliver the "editorial / one narrative" feel the product brief asks
for — it's a tidy-up, not a reframe. `<h3>` + divider hierarchy inside one surface can
still read as "mini cards". Consultation summary as a sub-section may under-weight it.

**Implementation cost — Low.** ~2 small PRs + premium restyle. Mostly deleting wrappers
and swapping in `DetailSection variant=`.

---

### Direction C — "Hybrid: Editorial Meaning, Native Objects" (audit-aligned)

**Concept.** Editorial reading flow for the **Meaning narrative** (Layers 2–5), native
surfaces retained **only** for things that are genuinely an object, a state, or an
interaction: the shrine entity/hero, the action area (save / visit / reflection), the
evidence/details block, and the single Free→Premium transition.

**Layout model.**
* **Object** — shrine hero (name, image, one-line meaning, Primary CTA): a `primary` surface / the existing Hero component. Boxed — it's the entity.
* **Narrative** — Layers 2–5 (`core reason → connection to consultation → shrine meaning → personal meaning → action meaning`): **borderless editorial** column, `<h2>` per layer, `space-y-6`, one measure. This is Direction A's treatment, scoped to the meaning story only.
* **Premium transition** — one hairline + `premium-surface` tint + fade + one CTA-A, at the Layer 3→4 boundary (where the user has just understood the shrine's meaning and the next layer is "what it means for *you*").
* **Evidence** — Layer 6: `tertiary` recessed surface or `DetailDisclosureBlock` (D-5). Boxed and de-emphasised — it's reference material, not narrative.
* **Actions** — save / visit / reflection: keep as a surface (genuine interaction + state), but flatten the 3-deep nested borders to one.

**Information hierarchy.**
* Primary = shrine hero object (boxed, `shadow-high`) + Primary CTA.
* Secondary = the borderless meaning narrative (type-driven: `<h2>` `text-base font-semibold`, body `text-[15px] leading-7 text-primary`).
* Tertiary = evidence surface (recessed) + action surface (functional, not narrative).

**Premium treatment.** Identical to A's transition, but there is exactly **one** in the
whole page and it sits at a single, deliberate narrative seam. CTA-B (continuity) stays
on its own surface, restyled to not mimic CTA-A. CTA-C (quota) stays as the paywall box,
visually distinct (neutral, not amber).

**Component impact.** Union of A (for the narrative section) and B (for hero/evidence/
actions), but **narrower than A**: `ShrineReasonSection` etc. only lose their box when
they're part of the narrative; `ShrineFactSection`, `PublicGoshuinSection`,
save/visit/reflection keep surfaces. Needs the `DetailSection plain` variant (D-3) for
the narrative section only.

**Design-token impact.** Existing tokens + **D-3** (one `DetailSection` variant), same
as A.

**Mobile @375px.** Narrative reads cleanly and short; objects/actions stay recognisably
tappable; evidence is collapsed out of the first viewport. Best balance of "calm
reading" and "app affordances". Risk: the boundary between "narrative" and "object" must
be drawn consistently or the page looks half-migrated.

**Strengths.** Matches the product brief's target flow **and** the design principle
"cards only for a genuinely separate object, state, or interaction" — literally. Keeps
the shrine entity and actions as solid, confident UI. One Premium moment. Reuses
`DetailSection` (+1 variant). Evidence stays available without interrupting (A-I1, A-I5).

**Risks.** Requires a clear, documented rule for "narrative vs object" so future work
doesn't drift. Slightly more design judgement per section than B. Two visual languages on
one page can feel inconsistent if the transition between them isn't handled (spacing +
the hero acting as the anchor).

**Implementation cost — Medium** (between B and A; closer to B because the boxed parts
are largely unchanged). ~3 PRs.

---

## 5. Comparison Matrix

Scale: ●●● strong · ●●○ adequate · ●○○ weak.

| Criterion (weight) | A — Editorial | B — Layered Surfaces | C — Hybrid |
|---|---|---|---|
| Mobile readability (High) | ●●● shortest, calmest, fewest targets | ●●○ tidier but still boxed | ●●● short narrative + clear affordances |
| Meaning hierarchy (High) | ●●● pure type/space hierarchy | ●●○ variant tiers, can read as mini-cards | ●●● type-driven narrative, boxed objects |
| Premium differentiation (High) | ●●● depth via fade/tint/one CTA | ●●○ one region, still amber block | ●●● one deliberate seam, depth cue |
| Existing architecture compat (High) | ●●○ needs D-3, larger diff | ●●● zero new primitives, Compass precedent | ●●○ needs D-3, medium diff |
| Design-system reuse (High) | ●●○ tokens ok, +1 variant, hand-rolled type scale | ●●● `DetailSection` variants as-is | ●●○ `DetailSection` + 1 variant |
| Maintainability (High) | ●●○ spacing discipline critical; less "guard-railed" | ●●● variant API constrains drift | ●●○ needs a documented narrative/object rule |
| Visual trend alignment (Med) | ●●● contemporary editorial | ●●○ generic app cards | ●●● editorial + restraint |
| Implementation effort (Med) | ●○○ Medium (largest) | ●●● Low | ●●○ Medium |
| Motion readiness (Low) | ●●● borderless sections reveal cleanly | ●●○ surface reveal ok | ●●● narrative reveal + object anchor |
| Decorative novelty (Low) | ●●○ intentionally plain | ●○○ none | ●●○ intentionally plain |

**Reading of the matrix:** B wins on cost / compatibility / maintainability; A wins on
readability / hierarchy / Premium / trend; C matches A on the High-weight *experience*
criteria while giving back most of B's compatibility and guard-rails, at Medium cost.

---

## 6. Recommended Direction

### RECOMMENDATION — Mother Ship approval required

**Direction C — "Hybrid: Editorial Meaning, Native Objects".**

Why C is best supported by the current architecture and product intent:

1. **It matches the stated design principle exactly.** The brief says "use cards only
   when they represent a genuinely separate object, state, or interaction." C draws that
   line explicitly: shrine entity, actions, evidence, and the Premium seam are objects/
   states → surfaces; the Meaning story is one narrative → borderless. A over-applies
   borderless to things that *are* objects (the hero, the save block); B keeps
   everything boxed.
2. **It delivers the target reading flow** (Recommended Shrine → Why this shrine → Why it
   connects → What it may mean for you → What to keep in mind → Evidence) as a literal
   vertical narrative, which the audit (A-I1, A-I4, A-I5) and the product context both
   ask for. B produces the right *order* but still in six containers.
3. **It reuses the shipped hierarchy primitive.** `DetailSection` variants + `<h2>`
   titles are already used this way on Compass (`CompassClient.tsx`). C keeps that for
   the boxed parts and adds exactly one additive variant (`plain`, D-3) for the
   narrative — no parallel design system, no token architecture, no new colours.
4. **It confines Premium to one moment** (A-I3), at a real narrative seam (Layer 3→4),
   using only existing `premium-*` tokens + whitespace + a fade. This removes 3 of the 4
   repeated amber boxes (A-C6) and the CTA stacking (A-C7) without touching entitlement
   or analytics.
5. **It is reversible and shippable in slices.** The boxed parts (hero, facts, goshuin,
   actions) are largely unchanged, so PR-G1/G3 are low-blast-radius; only the narrative
   section and the Premium seam are genuinely new.
6. **Effort is Medium, not High.** Because objects stay boxed, C's diff is closer to B's
   than A's.

**Fallback:** if Mother Ship rejects D-3 (no new `DetailSection` variant), the plan
degrades gracefully to **Direction B** with no other change — same PR sequence, the
narrative section uses `DetailSection variant="secondary"` with internal `<h3>` +
dividers instead of borderless. Recommend approving D-3.

**Not recommended:** Direction A alone (over-applies borderless, largest risk for the
readability gain over C). Motion (PR-G5) is out of MVP scope regardless.

---

## 7. Target Concierge Result Architecture

Derived from the current production content (§2.1). Section-level hierarchy under
Direction C.

| # | Layer | Content (existing source) | Treatment | Access behaviour |
|---|---|---|---|---|
| 1 | **Consultation context** | `reasonVm.detail.consultationSummary` (`buildStateNarrative`) | Opening paragraph. `<h2>` "今回の相談の整理" + body. Borderless. **Moved above deep layers** (A-I4). | Guest/Free/Premium: full (FREE). |
| 2 | **Recommended shrine (object)** | `ConciergeTopRecommendationHero` (name, eyebrow, `conclusionLines`, action) | **Boxed** — `primary` surface. Contains the **one** Primary CTA `神社の詳細を見る`. | all: full. |
| 3 | **Why this shrine** (core / basic reason) | `conclusionLines` + `runtimeMatchLines` merged in (A-I5) | Borderless narrative, `<h2>` "この神社が選ばれた理由". | all: full (FREE). |
| 4 | **Why it connects to this consultation** | `runtimeMatchLines` ("今回の相談との接点") folded here; `historyThemeDisplay` context folded here | Borderless, continues the column. | all: full (FREE). |
| — | **Premium seam** | one hairline + `premium-surface` tint begins + (Free/Guest) fade → **one** CTA-A "この神社を選ぶ意味を深掘りする" | single transition, tokens only | Premium: no CTA, tint + full content. Free/Guest: fade + CTA-A. |
| 5 | **Shrine meaning** | `reasonVm.detail.shrineMeaning` (`buildMeaningNarrative`) | Borderless, on `premium-surface` tint. `<h2>` "相談から見たこの神社の意味". | Premium: full. Free/Guest: teaser = first lines faded (A-I2). |
| 6 | **Personal meaning** | (Concierge currently has no dedicated field — `heroMeaningCopy` / `shrineMeaning` secondary framing) | Borderless. Only render if content exists; otherwise omit (no empty card). | Premium: full. Free/Guest: covered by the one seam above — **no second teaser card** (A-C3). |
| 7 | **Action meaning** | `reasonVm.detail.actionMeaning` (`buildReflectionQuestion`) | Borderless, `<h2>` "参拝するときに意識すること". | Premium: full. Free/Guest: within the faded region — no separate teaser card. |
| 8 | **Evidence / details** (tertiary) | `trustMetadata`, `historyThemeDisplay` detail, rank reason (if D-2 = render), "迷った時だけ、ほかの神社を見る" → compact list | **Recessed** `tertiary` surface or `DetailDisclosureBlock` (D-5). De-emphasised. | all. |
| 9 | **Secondary actions** | `ShrineSaveButton` (subtle) + `save_prompt` button — **consolidated to one** | Text/subtle button, below evidence. | Guest: "ログインして保存". |
| 10 | **Continuity** (CTA-B) | `PremiumStateDeltaCard` | Own surface, restrained styling, distinct from CTA-A. | Premium only (unchanged: `previous_comparison` gate). |
| 11 | **Quota** (CTA-C) | `isUiPaywall` box | Neutral surface (not amber), visually distinct from CTA-A. | Free at limit. |

Notes: quota copy "あと N回まで無料" stays where it is (near the top of the
recommendations section) — it is informational, not a CTA, and must not move into the
Premium seam.

---

## 8. Target Shrine Detail Architecture

**Responsibility split (must be explicit):**

| | Concierge Result | Shrine Detail |
|---|---|---|
| Primary job | "Here is the shrine for *this consultation*, and why." | "Here is *this shrine* — what it is, and (if you came from a consultation) what it meant for you." |
| Consultation meaning | the main event | **one clearly-bounded section**, secondary to shrine facts |
| Shrine public facts | minimal (trust chips only) | the spine of the page |
| Deep/Personal/Action meaning | teased inline | the Premium section, one seam |
| Duplication rule | — | **must not restate** the Concierge narrative; links back to it instead |

Section-level hierarchy under Direction C:

| # | Layer | Content (existing source) | Treatment | Access |
|---|---|---|---|---|
| 1 | **Shrine identity (object)** | `ShrineDetailHeroHeader` + `ShrineDetailHeroCard` | `primary` surface: `<h1>` name, one-line meaning, image. | all. |
| 2 | **Shrine public facts** | `ShrineFactSection` (祭神・由緒・歴史), benefit labels | Borderless narrative OR `secondary` surface — this is the page spine. Never Premium-gated. | all (FREE). |
| 3 | **Why this shrine was recommended** (only if `ctx=concierge`/`tid`) | `context_reason` sections (`buildContextReasonSections`) + `recommendation_meta` **if D-2 = render** | Borderless, `<h2>` "今回の相談でこの神社が選ばれた理由". Short; links to the Concierge Result for the full narrative (no restatement). | all (FREE). |
| — | **Premium seam** | one hairline + `premium-surface` tint + (Free/Guest) fade → one CTA-A | single transition | Premium: full. Free/Guest: fade + CTA-A. Replaces `PremiumUpgradePrompt`. |
| 4 | **This shrine's meaning for you** | `premiumSections` → `ShrineJudgeSection` content (deep/personal) | Borderless on tint. | Premium: full. Free/Guest: faded. |
| 5 | **What to keep in mind when visiting** | `premiumSections` → `ShrineActionSection` content | Borderless on tint; drop per-item gold sub-cards (A-C6 / V23). | Premium: full. Free/Guest: faded. |
| 6 | **Continuity** (CTA-B) | `ShrineDetailStateDeltaSection` | Own surface, restrained, distinct from CTA-A; only after visit. | Free: teaser branch. Premium: full. |
| 7 | **Actions & records (object/state)** | save / visit / `ShrineReflectionPrompt` | **One** surface (flatten the 3-deep nesting), functional styling. | Guest: login-gated per current rules. |
| 8 | **Goshuin** | `PublicGoshuinSection` (`DetailSection`) | unchanged. | all. |
| 9 | **Deep-dive Q&A** | `ShrineDeepDivePrompt` | `tertiary` / recessed. | unchanged. |

---

## 9. Card / Surface Classification

Every current container. **No component is deleted in the implementation PRs unless
explicitly noted; this is a classification.**

### Concierge Result

| Current container | Class | Action |
|---|---|---|
| `ConciergeTopRecommendationHero` | **KEEP AS CARD** | It's the shrine entity + the Primary CTA. Promote to `primary` surface. |
| `DirectionReferenceCard` | KEEP AS CARD | Distinct object (direction/route reference). |
| `runtimeMatchLines` section (`conciergeSoftCardClass`) | **MERGE** | Fold into Layers 3–4 narrative (A-I5). Container removed. |
| `trustMetadata` section | **DEEMPHASIZE** | Move to Layer 8 evidence (tertiary/recessed). |
| `historyThemeDisplay` section | **MERGE** + **DEEMPHASIZE** | Context line → Layer 4 narrative; extended framing → Layer 8. |
| `shrine_meaning` section | **CONVERT TO SECTION** | Borderless Layer 5. Teaser = fade, not a card (A-C3). |
| `action_meaning` section | **CONVERT TO SECTION** | Borderless Layer 7. |
| `ConciergeConsultationSummary` (box + pills) | **CONVERT TO SECTION** | Borderless Layer 1, moved above deep layers (A-I4). Pills → inline meta or dropped. |
| `ConciergePremiumEntryCard` (amber box) | **MERGE** into the Premium seam | One transition (fade + hairline + one CTA-A). Amber box removed. |
| `ShrineSaveButton` (subtle) + `save_prompt` button | **MERGE** | One secondary action (Layer 9). |
| "ほかの神社" toggle + `ShrineCardCompact[]` | **REMOVE FROM PRIMARY FLOW** | Into Layer 8 evidence / disclosure. |
| `PlaceShrineCard[]` | KEEP AS CARD | Distinct objects (unregistered shrines). |
| `bannerText` / fallback grid buttons | KEEP AS CARD | Genuine state (fallback / dummy results). |
| `PremiumStateDeltaCard` (CTA-B) | KEEP AS CARD, **restyle** | State object; restrained styling, must not mimic CTA-A. |
| `isUiPaywall` box (CTA-C) | KEEP AS CARD, **restyle neutral** | Quota state; visually distinct from Premium. |

### Shrine Detail

| Current container | Class | Action |
|---|---|---|
| `ShrineDetailHeroHeader` + `ShrineDetailHeroCard` | **KEEP AS CARD** | Shrine identity object → `primary`. |
| `directionSupportCopy` | DEEMPHASIZE | Inline caption under hero, not its own box. |
| `ShrineDetailStateDeltaSection` (CTA-B) | KEEP AS CARD, **restyle** | State; distinct from CTA-A; flatten. |
| after-visit copy | KEEP AS CARD | Genuine state. |
| `ShrineReasonSection` / `ShrineProposalSection` (context_reason) | **CONVERT TO SECTION** | Borderless Layer 3. |
| `ShrineSupplementSection` | MERGE into Layer 2 (facts) or DEEMPHASIZE | Benefit/symbol labels are shrine facts. |
| `ShrineJudgeSection` (`<details>`, premium) | **CONVERT TO SECTION** | Borderless Layer 4 on tint; keep disclosure only if D-5 says so. |
| `ShrineActionSection` (per-item gold sub-cards) | **CONVERT TO SECTION** | Borderless Layer 5; drop per-item `premium-surface` sub-cards. |
| `PremiumUpgradePrompt` (amber box) | **MERGE** into the Premium seam | One transition. |
| `ShrineFactSection` | KEEP AS CARD or CONVERT | Page spine (Layer 2); keep as `secondary` surface or borderless — design call in PR-G3. |
| `ShrineDeepDivePrompt` | DEEMPHASIZE | `tertiary` / recessed (Layer 9). |
| save / visit / `ShrineReflectionPrompt` block | KEEP AS CARD, **flatten** | Interaction + state; collapse 3-deep nested borders to one surface. |
| `PublicGoshuinSection` (`DetailSection`) | KEEP AS CARD | Unchanged. |
| fallback benefit `DetailDisclosureBlock` | KEEP AS CARD | Unchanged. |
| `RecommendationMetaSection` (unused) | **D-2** | Render into Layer 3, or delete component + its `card_view` event. |
| `GoshuinLimitBadge` (unused) | REMOVE FROM PRIMARY FLOW | Dead code; leave for the audit's N4 cleanup, not a PR-G task. |

---

## 10. CTA Architecture

| Tier | Element | Where | Visual | Rule |
|---|---|---|---|---|
| **Primary** | `神社の詳細を見る` (Concierge) / in-page nav (Detail) | Inside the shrine hero (Layer 2 / Layer 1) | The **only** filled `--kt-color-action-primary` button on the screen | Exactly one. Never competes with Premium. |
| **Secondary** | **CTA-A — Meaning Depth** `この神社を選ぶ意味を深掘りする` | The **single** Premium seam (Layer 3→4 / 3→4) | `--kt-color-premium-accent` text or a single outlined button on the `premium-surface` tint; **not** a filled box | Exactly one per screen. Appears only *after* the user has read enough to know what "deeper" means (Principle 4). |
| **Secondary** | **CTA-B — Continuity** `前回との違いを見る` | `PremiumStateDeltaCard` / `ShrineDetailStateDeltaSection` | Own restrained surface; **must not** reuse CTA-A's amber-box styling | Only when `stateDelta` exists. Distinct copy + distinct surface from CTA-A. |
| **Tertiary** | **CTA-C — Quota** `有料プランを見る` | `isUiPaywall` box | **Neutral** surface (border-default / surface-default), not amber | Only at limit. Informational quota line ("あと N回") stays separate near the results top. |
| **Tertiary** | Save / login-to-save | Layer 9 | Text / subtle button | One consolidated control. |

**Non-competition guarantees:**
* Meaning Depth (A), Continuity (B), Quota (C) each have a **different surface colour
  role**: A = `premium-surface` (amber tint), B = restrained neutral/own, C = neutral
  paywall. No two look alike.
* Only one filled primary button per screen (the shrine CTA).
* CTA-A appears **once**, at a narrative seam — never repeated per gated section (fixes A-C6/A-C7).
* CTA-B and CTA-C are gated by state (`stateDelta`, quota) and do not appear in the
  default Guest/Free result view.

---

## 11. Implementation PR Plan

3 core PRs + 1 conditional + 1 out-of-MVP. Each: one visual responsibility, business
logic / Premium visibility rules / analytics untouched, independently reviewable, no
unrelated refactor.

### PR-G0 (prerequisite, tiny) — `DetailSection` `plain` variant

* **Purpose:** add the borderless variant Directions A/C need. Additive only.
* **Branch:** `feat/detail-section-plain-variant`
* **Scope:** `components/shrine/DetailSection.tsx` — add `variant: "plain"` →
  `SECTION_CLASS.plain = ""` (no border/bg/shadow, keep `<h2>` title class =
  `text-base font-semibold text-[--kt-color-text-primary]`), `TITLE_CLASS.plain`,
  `RIGHT_CLASS.plain`. No caller changes.
* **Likely files:** `DetailSection.tsx`, `components/shrine/__tests__/` (new variant test).
* **Tests:** unit — `variant="plain"` renders `<h2>` + children, no `border`/`shadow`
  class. Snapshot of the 4 variants.
* **Screenshots:** none (primitive).
* **Exclusions:** no caller migration; no other variant changes.
* **DoD:** variant exists, typechecks, `tokens.test.ts` + `DetailSection` tests green.
* **Skip this PR if** Mother Ship rejects D-3 → the plan falls back to Direction B (use
  `secondary` + `<h3>` dividers) and PR-G1/G3 adjust accordingly.

### PR-G1 — Concierge Result information hierarchy

* **Purpose:** restructure the Concierge Result into the §7 layer order with typographic
  hierarchy and merged/borderless sections. **No Premium behaviour change**, **no Shrine
  Detail change**, **no meaning-generation change**.
* **Branch:** `feat/concierge-result-hierarchy`
* **Scope:**
  * Reorder to §7: consultation context (Layer 1) above the deep layers.
  * Merge `runtimeMatchLines` + `historyThemeDisplay` context into Layers 3–4 narrative; drop their `conciergeSoftCardClass`.
  * `shrine_meaning` / `action_meaning` / `ConciergeConsultationSummary` → borderless sections (Direction C) or `DetailSection secondary` (fallback B).
  * `trustMetadata` + "ほかの神社" → Layer 8 recessed / disclosure.
  * Consolidate `ShrineSaveButton` + `save_prompt` into one Layer 9 control.
  * Introduce `space-y-6` (= `--kt-space-section-y`) between layers; document the `<h2>`/`<h3>`/body utility combos in a top-of-file comment.
  * Replace raw `amber-*`/`slate-*` literals **only in the blocks being edited** with `--kt-*`.
* **Likely files:** `features/concierge/components/ConciergeSectionsRenderer.tsx`,
  `ConciergeConsultationSummary.tsx`, `ConciergeTopRecommendationHero.tsx` (promote to
  `primary` surface only), `features/concierge/components/__tests__/*`.
* **Tests:**
  * Update `ConciergeSectionsRenderer.coverage.test.tsx`, `*.ctaHierarchyTrustPlacement.test.tsx`, `*.recommendationInstanceId.test.tsx` for new DOM/order.
  * Keep asserting: exactly one `bg-[--kt-color-action-primary]` CTA (`神社の詳細を見る`); `recommendation-premium-preview` present for guest/free, absent for premium; all `trackCardEvent` / `trackSearchEvent` calls unchanged (cardId, event, visibility, analytics props).
  * New: section order (consultation context precedes `shrine_meaning`); no `conciergeSoftCardClass` on the merged blocks.
* **Screenshots:** Concierge Result @ 375 / 390 / 430, access = guest / free / premium (6 min; 9 with fallback state).
* **Behaviour that must not change:** `cardVisibility` outcomes; every analytics event
  name/prop; `onAction` dispatch; Hero CTA target; teaser text presence for guest/free
  (may move into the fade but must still be reachable copy).
* **Rollback boundary:** revert `ConciergeSectionsRenderer.tsx` + the 2 helper
  components + their tests. No shared-component or token revert needed (PR-G0 stands
  alone).
* **Exclusions:** Premium seam styling (PR-G2), Shrine Detail (PR-G3), `PremiumStateDeltaCard` (PR-G2), quota box (PR-G2), motion (PR-G5).

### PR-G2 — Premium Meaning presentation & CTA architecture

* **Purpose:** replace the repeated amber upsell boxes with **one** Free→Premium seam per
  screen (fade + hairline + `premium-surface` tint + one CTA-A), and make CTA-A / CTA-B /
  CTA-C visually non-competing (§10). **No entitlement / payment / generation change.**
* **Branch:** `feat/premium-meaning-seam`
* **Scope:**
  * New shared `PremiumSeam` presentational component (fade mask + hairline + tint + single CTA-A slot); tokens only (`--kt-color-premium-surface/-border/-accent`, gradient over `--kt-color-background-base`).
  * Concierge: `ConciergePremiumEntryCard` → `PremiumSeam` at the Layer 4→5 boundary; teaser fade replaces the one-line teaser cards.
  * Shrine Detail: `PremiumUpgradePrompt` → `PremiumSeam` at the Layer 3→4 boundary.
  * `PremiumStateDeltaCard` + `ShrineDetailStateDeltaSection` (CTA-B): restyle to a restrained neutral/own surface, drop amber-box look, keep copy + link + analytics.
  * `isUiPaywall` box (CTA-C): restyle to neutral (`border-default` / `surface-default`), keep copy + links + logic.
  * `ShrineActionSection`: drop per-item `premium-surface` sub-cards (V23).
* **Likely files:** new `features/premium/PremiumSeam.tsx` (or `components/premium/`),
  `ConciergeSectionsRenderer.tsx` (seam slot), `components/shrine/detail/ShrineDetailArticle.tsx`,
  `PremiumStateDeltaCard.tsx`, `components/shrine/detail/ShrineActionSection.tsx`, tests.
* **Tests:**
  * `PremiumSeam` unit: renders exactly one CTA; CTA `href` = `/billing/upgrade` (guest → `buildLoginHref`); fires `premium_preview_click` / `cardId: premium_preview` / `visibility: teaser` / `ctaType: continue_with_premium` **unchanged**.
  * Guest/Free: gated body content not present in DOM (contract from #2654 — no leak).
  * Premium: full content present, no CTA-A.
  * Only one element with the Premium accent per screen; CTA-B surface ≠ CTA-A surface class.
  * `PremiumStateDeltaCard` / `isUiPaywall` analytics + links unchanged.
* **Screenshots:** Concierge Result + Shrine Detail, @ 375 / 390 / 430, access = guest /
  free / premium (18). Plus: Shrine Detail with `stateDelta` (CTA-B visible) and
  Concierge at quota limit (CTA-C visible) to prove non-competition.
* **Behaviour that must not change:** `cardVisibility` resolution; all Premium analytics
  events + props; upgrade/login hrefs; `isPremiumActive` source; teaser = no body leak.
* **Rollback boundary:** delete `PremiumSeam`, revert the ~4 touched components + tests.
  Independent of PR-G1/G3 (seam slot is additive; if PR-G1 not merged, seam still drops
  into the current layout).
* **Exclusions:** layer reordering (PR-G1/G3); Deep Reason connection (audit N1); any
  `cardVisibility.ts` change.

### PR-G3 — Shrine Detail Meaning integration & shrine/consultation split

* **Purpose:** apply the §8 hierarchy; make Shrine Detail clearly *shrine-first* with a
  bounded consultation-meaning section that **does not duplicate** the Concierge Result;
  resolve D-2 (`recommendation_meta`).
* **Branch:** `feat/shrine-detail-meaning-layout`
* **Scope:**
  * Reorder to §8: identity (Layer 1) → public facts spine (Layer 2) → "why recommended" short section w/ link back to Concierge (Layer 3) → Premium seam → meaning/action (Layers 4–5) → CTA-B → actions → goshuin → deep-dive.
  * `context_reason` / `ShrineJudgeSection` / `ShrineActionSection` → borderless (Direction C) within the narrative; `ShrineFactSection` stays a surface (spine).
  * Flatten the save/visit/reflection nested borders (3 → 1 surface).
  * `directionSupportCopy` → inline caption.
  * **D-2:** either wire `RecommendationMetaSection` into Layer 3 (FREE) **or** delete `RecommendationMetaSection.tsx` + remove the `recommendation_meta` `card_view` block in `ShrineDetailArticle.tsx` (`:586-600` + deps). Analytics-contract-adjacent → needs the D-2 decision before this PR starts.
* **Likely files:** `components/shrine/detail/ShrineDetailArticle.tsx`,
  `ShrineDetailSections` + `ShrineReasonSection` / `ShrineJudgeSection` / `ShrineActionSection` /
  `ShrineProposalSection` / `ShrineSupplementSection`, `RecommendationMetaSection.tsx`
  (render or delete), `shrines/[id]/page.tsx` (only if D-2 = delete → drop the unused prop),
  `components/shrine/detail/__tests__/*`.
* **Tests:**
  * Update `ShrineDetailArticle.test.tsx` for new DOM/order.
  * Keep asserting: premium sections hidden for free (`personalMeaningVisibility` teaser → seam, not content); `card_view` events for `context_reason` / `personal_meaning` / `shrine_meaning` / `action_meaning` unchanged in cardId/accessLevel/visibility.
  * D-2 = render: new assertion `recommendation_meta` content visible for free/premium + its `card_view` now matches a real surface. D-2 = delete: assert no `recommendation_meta` event fires and `RecommendationMetaSection` removed.
  * Shrine Detail meaning copy is **not** a verbatim copy of Concierge `shrineMeaning` in the same render (spot-check for the known fallback-dup, V13).
* **Screenshots:** Shrine Detail @ 375 / 390 / 430, access = guest / free / premium,
  ctx ∈ {direct, concierge} (12–18); plus visited/reflected state (CTA-B).
* **Behaviour that must not change:** `buildShrineDetailModel` output; `cardVisibility`;
  Favorite / Visit / Reflection action boundaries + their analytics; premium gating;
  routing / `ctx` handling.
* **Rollback boundary:** revert `ShrineDetailArticle.tsx` + the section components +
  tests (+ `RecommendationMetaSection`/`page.tsx` if D-2 = delete). Independent of G1;
  depends on G2 only for the shared `PremiumSeam` (soft dep — can ship with a local seam
  and adopt `PremiumSeam` on merge).
* **Exclusions:** Concierge Result (PR-G1); Premium seam *styling* (owned by PR-G2);
  Deep Reason connection (audit N1); Compass.

### PR-G4 — Mobile polish (CONDITIONAL)

* **Create only if** PR-G1–G3 QA at 375px surfaces issues not already fixed by the
  restructure. Candidates from the audit: CTA `<a>` min-height 44px (A-C11 / V16),
  preset chip height, `grid-cols-2` fallback → stacked ≤390px (V18),
  `ConciergeConsultationSummary` header wrap (V17), global bottom-nav / safe-area overlap
  on the last section (audit M9, unverified).
* **Branch:** `fix/premium-meaning-mobile-polish`
* **Scope:** spacing / tap-target / wrap / safe-area only. No hierarchy or Premium change.
* **Tests:** RTL where meaningful (button min-height class); mostly screenshot diffs.
* **Screenshots:** 375 / 390 / 430 for both screens, before/after.
* **DoD:** no horizontal overflow; all interactive targets ≥ 44px; no clipped labels;
  last section clears any fixed bottom nav.
* **Do not create** if G1–G3 already covered these (prefer folding in).

### PR-G5 — Motion / microinteraction (OUT OF MVP)

* **Not implemented now.** Only propose after G1–G3 ship. The borderless-section +
  single-seam structure from Direction C supports section reveal, Premium-unlock
  transition, and meaning expansion without further structural change (audit Phase F).
* **Branch (future):** `feat/premium-meaning-motion`
* **Gate:** explicit Mother Ship request; must respect `prefers-reduced-motion`; no
  analytics/logic change.

---

## 12. Risks

Concrete only.

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Borderless sections look unstructured** if content lengths vary or spacing is applied inconsistently. | Direction C limits borderless to the meaning narrative; `space-y-6` between `<h2>` layers is mandated and asserted in tests; the hero + evidence stay boxed as anchors. |
| R2 | **Teaser fade regresses the "no body leak" contract** (#2654) if the faded text is present in the DOM. | `PremiumSeam` must render **only** the allowed teaser lines for guest/free (same strings as today), not the full body with a CSS mask over it. Test asserts gated body strings absent from DOM. |
| R3 | **Analytics drift** — reordering / unwrapping changes which `trackCardEvent` fires or its `visibility` value. | Each PR keeps the existing `getVisibilityForCard` calls and event payloads verbatim; tests assert event name + `cardId` + `visibility` + analytics props unchanged. D-2 is the only intentional analytics change and is called out explicitly. |
| R4 | **Dark mode breakage** from replacing token refs with literals (or vice-versa) mid-edit. | Only touch literals in blocks already being edited; use `--kt-*`; screenshot QA includes `.dark`. |
| R5 | **`DetailSection` `plain` variant** used incorrectly elsewhere later, eroding the hierarchy. | Document intent in the component + a lint-style comment; variant is additive and covered by a snapshot test. If D-3 rejected → fall back to Direction B, no new variant. |
| R6 | **Shrine Detail ↔ Concierge Result duplication** creeps back when both render `shrineMeaning`. | §8 rule: Detail Layer 3 is a *short* "why recommended" + link back, not the full narrative; PR-G3 test spot-checks for verbatim duplication (V13). |
| R7 | **CTA-B / CTA-C restyle** unintentionally changes copy or link and affects funnel analytics. | PR-G2 restyles surface classes only; copy, `href`, and `trackRetentionEvent` / paywall logic asserted unchanged. |
| R8 | **Scope creep** into `buildMeaningNarrative` / `buildDeepRecommendationReason` because the meaning text reads thin once the chrome is gone. | Hard constraint: generation is out of scope. If the restructured layout exposes weak copy, that is a **separate** finding for Mother Ship (audit N1), not a PR-G change. |
| R9 | **Compass parity** — Compass uses `DetailSection` variants; if PR-G0 changes shared title classes it could shift Compass. | PR-G0 is **additive** (`plain` only); no change to `primary`/`secondary`/`tertiary`. Compass screenshot in PR-G0 QA. |
| R10 | Merge order: PR-G2's `PremiumSeam` vs PR-G1/G3 layout. | G2 designed to drop into either the old or new layout; G1/G3 use a seam *slot*. Recommended merge order G0 → G1 → G2 → G3, but G2 can precede G1. |

---

## 13. Mother Ship Decisions Required

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D-1 | **Visual direction** | A (Editorial) / B (Layered Surfaces) / **C (Hybrid)** | **C** — best matches the target reading flow and the "cards only for objects/states/actions" principle, reuses `DetailSection`, Medium cost. Fallback: **B** if D-3 is rejected. |
| D-2 | **`recommendation_meta`** | (a) render `RecommendationMetaSection` into Shrine Detail Layer 3 (FREE) / (b) delete the component + its `card_view` event | Lean **(a) render** — the fixed boundary lists "Recommendation Evidence" as FREE, and it is already generated + tracked; rendering it closes A-C9 without an analytics-contract removal. Decide before PR-G3. |
| D-3 | **Add `plain` variant to shared `DetailSection`** | yes / no | **Yes** — one additive variant, additive-only, test-covered; unlocks C (and A). No → plan degrades to B automatically. |
| D-4 | **Sequence vs audit non-UI follow-ups (N1–N4)** | before / after / parallel to PR-G | **Parallel is fine.** PR-G work runs on the current heuristic meaning text and does not depend on N1 (Deep Reason connection). N2/N3 (naming / double-CardId) should land before any analytics-touching part of PR-G3 (D-2). |
| D-5 | **Collapsible evidence (Layer 6 / Layer 9)** | `<details>` / `DetailDisclosureBlock` allowed / hierarchy + spacing only | Lean **allowed for Layer 6 evidence + deep-dive only** (reference material), not for meaning layers. Audit Phase-D caution applies to *meaning*, not to trust/rank/"other shrines". |
| D-6 | **PR-G4 (mobile polish)** | standalone / fold into G1–G3 | Decide after G1–G3 QA; default **fold in** unless a cross-cutting issue (bottom-nav/safe-area) needs its own PR. |
| D-7 | **PR-G5 (motion)** | schedule / defer | **Defer** — not MVP; revisit after G1–G3 ship. |

---

## 14. STOP

No implementation performed. No production UI, business logic, generation, entitlement,
analytics, or routing changed. This document is the deliverable.

Awaiting Mother Ship decisions D-1 … D-7 before any PR-G* branch is opened.
