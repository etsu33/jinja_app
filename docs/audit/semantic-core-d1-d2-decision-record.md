# Semantic Core — D1 / D2 Mother Ship Decision Record

> **Status: Decided** (Mother Ship, 2026-08-30). Canonical semantic
> *direction* is fixed; no schema, adapter, or runtime change is made or
> authorised by this record. It canonicalises the Mother Ship decisions on
> **D1 `SEMANTIC_CORE_STRATEGY`** and **D2 `NEED_TAG_ROLE`** that were
> prepared by the merged audits below. **No runtime, interpreter,
> `consultation_axis`, `need_tags`, `NEED_TO_GORIYAKU_IDS`, GoriyakuTag,
> Knowledge, Evidence, candidate-generation, `score_need`, scoring, ranking,
> Lead, Reason, Compass, `PremiumMeaningContext`, API-contract, test, or
> migration change is performed. No field is renamed. `NORMALIZE_MODEL` is
> not implemented. The routing adapter is not implemented. D3–D6 are not
> decided.** Follows the `docs/audit/*-decision-record.md` convention
> (cf. `docs/audit/ranking-contract-decision-record.md`).

---

## 1. Status

`DECIDED` — for D1 and D2 only. D3 (`CONSULTATION_AXIS_ROLE`) and D4–D6
remain open (§20, §21). This record is a *direction* and *responsibility*
fix, not an implementation authorisation.

```text
D1_SEMANTIC_CORE_STRATEGY = NORMALIZE_MODEL
D2_NEED_TAG_ROLE          = EVIDENCE_ROUTING_LAYER
MVP_ROLLOUT_POLICY        = ADAPTER_GATED
RANKING_REWRITE           = NOT_REQUIRED
COMPASS_REWRITE           = NOT_REQUIRED
PRIMARY_SEMANTIC_MODEL_FOR_NEED_TAG = NO
SEMANTIC_CORE_SOURCE      = NORMALIZED_MODEL
COMPATIBILITY_FUNCTION    = YES
COMPASS_SHARED_ROUTING_KEY = YES
SEMANTIC_CORE_MEMBERSHIP_EQUALS_ROUTING_ELIGIBILITY = NO
D3_CONSULTATION_AXIS_ROLE = UNDECIDED
```

## 2. Decision date

2026-08-30.

## 3. Decision authority

**Mother Ship.** This record documents decisions already taken; it does not
re-evaluate them. The audits in §22 are supporting evidence, not the
deciding authority — an audit conclusion becomes product policy only where
this record explicitly adopts it.

## 4. Context

`develop` base at recording time:
`518b67995a85df0315bad0c13e0ca67ebed80387`
(`docs: audit InterpretationProfile field redesign candidates (#2651)`).

Prior audits established:

- The current semantic core is `need_tag` (a 15-value flat list) plus a
  single-valued `consultation_axis`; `interpret_consultation`'s
  `InterpretationProfile` is shadow / display-only for ranking. The flat
  `need_tag` list is semantically overloaded (topic + state + intention in
  one axis), cannot represent polarity / negation, multi-state, or
  primary-vs-secondary-with-reason, and depends on three drifted
  keyword tables (`recommendation-nuance-quality-audit.md`,
  `consultation-understanding-architecture-audit.md`).
- Of the three D1 strategies compared over 34 canonical consultation cases,
  `NORMALIZE_MODEL` is the only one that can preserve every semantic
  dimension for every applicable case (representational capacity), with
  schema adoption and ranking activation kept independent
  (`semantic-core-strategy-decision-audit.md`).
- All five audited `InterpretationProfile` fields (`state_profile`,
  `emotion_profile`, `direction_profile`, `action_intent`,
  `constraint_profile`) are `DO_NOT_ROUTE`; none is a credible `need_tag`
  producer (`interpretation-profile-field-redesign-audit.md`).

This record fixes the resulting direction so downstream design and the D3
decision can proceed from a stable base.

---

## 5. D1 Decision

```text
D1_SEMANTIC_CORE_STRATEGY = NORMALIZE_MODEL
```

The canonical representation of a user's consultation meaning **must not** be
only `need_tag` or `consultation_axis`. The future canonical **Semantic
Core** is a dedicated normalized representation that can preserve multiple
semantic dimensions without destructive flattening.

## 6. D1 adopted meaning

- The Semantic Core should be able to hold, without collapsing them into one
  another, the dimensions identified by the prior audits:
  **topic**, **state**, **intention**, **polarity**, **primary / secondary
  emphasis**, **contrast**, and **explicit constraints** where appropriate.
- `need_tag` and `consultation_axis` become **derived projections / views**
  of the Semantic Core, produced by adapters, not the source of truth.
- `SEMANTIC_CORE_SOURCE = NORMALIZED_MODEL`.
- **Representational capacity ≠ interpretation accuracy.** The model having a
  place to preserve a signal does not mean the extractor can reliably
  populate it from free text. Parser / extraction quality is a separate,
  still-unresolved problem (§19).

## 7. D1 non-goals

`NORMALIZE_MODEL` as decided here does **not** mean, and does not authorise:

- an immediate Recommendation rewrite;
- an immediate ranking rewrite; `RANKING_REWRITE = NOT_REQUIRED` (§8);
- an immediate Score v3 activation (`SCORE_V3_MODE` stays `shadow` unless a
  separate decision changes it);
- an immediate Compass rewrite; `COMPASS_REWRITE = NOT_REQUIRED` (§13);
- an immediate replacement of the current `need_tag` routing;
- copying the current `InterpretationProfile` schema into the canonical
  model unchanged (§17);
- defining the final production Semantic Core schema in this task — the
  dimension list in §6 is the *scope of what must be representable*, not a
  schema.

## 8. D1 MVP rollout boundary

```text
MVP_ROLLOUT_POLICY = ADAPTER_GATED
RANKING_REWRITE    = NOT_REQUIRED
```

Initial adoption path:

```text
consultation input
  → normalized Semantic Core
    → compatibility / routing adapter
      → current need_tag routing
        → current NEED_TO_GORIYAKU_IDS mapping
          → reviewed GoriyakuTag / Evidence
            → current candidate generation / ranking (unchanged)
```

- The first adoption of `NORMALIZE_MODEL` **must be compatible with keeping
  current ranking behaviour unchanged**: the adapter emits the same
  `need_tags` the current pipeline already consumes.
- `RANKING_REWRITE = NOT_REQUIRED` states that **D1 adoption does not require
  immediate ranking replacement**. It does **not** state that ranking will
  never change; any future ranking change is a separate decision (D-series
  or a Score decision), gated by its own evidence and observation.

---

## 9. D2 Decision

```text
D2_NEED_TAG_ROLE = EVIDENCE_ROUTING_LAYER
```

## 10. D2 adopted meaning

- `need_tag` is **not** the canonical representation of the user's full
  consultation meaning. `PRIMARY_SEMANTIC_MODEL_FOR_NEED_TAG = NO`.
- `need_tag` is a **routing representation**: it connects approved semantic
  intent / signals to Recommendation Evidence.

  ```text
  Canonical Semantic Core
    → routing projection
      → need_tag
        → NEED_TO_GORIYAKU_IDS mapping
          → reviewed GoriyakuTag / Evidence
  ```

- **Semantic meaning may exist in the Semantic Core without a corresponding
  `need_tag`.** Semantic Core membership does not automatically grant
  routing eligibility:

  ```text
  SEMANTIC_CORE_MEMBERSHIP != ROUTING_ELIGIBILITY
  ```

## 11. D2 non-goals

- No `need_tag` is added; the `NEED_TAGS` set is unchanged.
- No `NEED_TO_GORIYAKU_IDS` entry is added, removed, or altered.
- No Evidence mapping is created.
- No GoriyakuTag mapping is inferred from any semantic signal.
- **No deprecation decision is made.** `need_tag` is **not** declared a
  temporary shim; current evidence does not support that (§12).
- The concrete rules of the *routing projection* (which Semantic Core
  signals project to which `need_tag`, and under what governance) are **not**
  defined here.

---

## 12. Evidence routing boundary (D2 evidence integrity)

The existing evidence-integrity contract is preserved verbatim:

- **Semantic plausibility ≠ approved Recommendation Evidence.** A signal
  being semantically related to a need does **not** make it an approved
  routing input.
- Routing eligibility remains **separately governed** by the reviewed
  mapping / evidence rules. The audits' `SEMANTIC_ROUTING_PLAUSIBLE` label is
  explicitly **not** the same as `EVIDENCE_ROUTING_APPROVED`.
- GoriyakuTag is never inferred from deity / history / tradition / raw
  `goriyaku` prose; the reviewed `goriyaku_tags` contract is unchanged.
- `NEED_TO_GORIYAKU_IDS` is unchanged. No tags created.

## 13. Concierge / Compass responsibility boundary

```text
COMPASS_SHARED_ROUTING_KEY = YES
COMPASS_REWRITE            = NOT_REQUIRED
```

```text
Concierge:  consultation input
              → normalized Semantic Core
                → routing projection
                  → need_tag ─┐
                              │  shared downstream
Compass:    preselected purpose / current compatible input
              → need_tag-compatible routing ─┘
                              │
                              ▼
                    need_tag → GoriyakuTag / Evidence → Recommendation pipeline
```

- **`need_tag` is the shared routing key** between Concierge and Compass; the
  Need → GoriyakuTag → Evidence → Recommendation pipeline downstream of
  `need_tag` is shared and unchanged.
- The five audited `InterpretationProfile` fields are **Concierge-only in
  practice**: Compass calls `interpret_consultation(query="")` and receives
  empty values for `state_profile` / `emotion_profile` /
  `direction_profile` / `action_intent` / `constraint_profile`.
- **The Concierge `direction_profile` is NOT reused for Compass.** It is
  *derived motivational framing* over `state_profile`, not the geographic
  Compass direction (九星 / `houi`); the two only share a colliding name.
- A richer Concierge Semantic Core does **not** require any Compass
  behaviour change. `COMPASS_REWRITE = NOT_REQUIRED`.

## 14. InterpretationProfile audit implications

From `interpretation-profile-field-redesign-audit.md` (PR #2651), recorded
here at principle level only — **not** turned into field-schema decisions,
and **no field is renamed** in runtime or any canonical contract:

| field | implication |
|---|---|
| `state_profile` | not stable as-is (a keyword signal presented as a psychological state; negation- and clause-sensitive; arbitrary `primary_state`; coverage gaps). **Candidate only after redesign** (`expressed_state` + polarity, wording-grounded). **Do not route directly.** |
| `emotion_profile` | 100 % derived from `state_profile` (the `query` argument is unused). Not suitable as a canonical "emotion" field as-is. **Do not route.** |
| `direction_profile` | derived motivational framing from `state_profile`; **not** the geographic Compass direction; name collides with the frontend `direction_profile`. **Do not route.** |
| `action_intent` | mixed responsibility — product / visit actions plus a semantic-intention leak (`整理` → `reflect`; `神社` → `visit`). **Requires separation** before any part is canonical. **Do not route as-is.** |
| `constraint_profile` | domain / state conflation (`energy` ← fatigue tokens; `relationship` ← relationship-topic tokens); genuine explicit constraints missed. **Explicit-only redesign required.** **Do not route.** |

**Key principle:** *do not copy the current `InterpretationProfile` directly
into `NORMALIZE_MODEL`.* Two of its five fields are derivations, two mix
layers, one needs a safety-grounded redefinition.

## 15. Evidence integrity boundary

(Consolidated with §12.) The Semantic Core and its routing projection must
not weaken the reviewed-Evidence contract:

- routing inputs are governed by reviewed mapping rules, not by semantic
  plausibility;
- `NEED_TO_GORIYAKU_IDS` and the `goriyaku_tags` review process are the sole
  gate for Recommendation Evidence eligibility;
- adding a dimension to the Semantic Core creates **no** new Evidence path
  by itself.

## 16. Safety boundary

Architectural / non-diagnostic. The Semantic Core should **preserve what the
user expressed** without escalating heuristic keyword matches into
unsupported psychological assertions.

- Prefer explicit grounding distinctions:
  `USER_EXPLICIT` / `LINGUISTICALLY_INFERRED` / `SYSTEM_INFERRED` /
  `UNSUPPORTED`.
- A `SYSTEM_INFERRED` value (e.g. "the user is anxious" from one keyword,
  possibly on a negated span) must not be presented to the user as an
  assertion about their mental or emotional condition.
- **No medical or psychological diagnosis fields.** The Semantic Core does
  not classify users' conditions.
- Do not state that a shrine is spiritually necessary for a user, or that a
  particular divine benefit is certain. Recommendation and meaning copy
  describe *expression* and *evidence*, not certainty.

## 17. FREE / Premium non-goal

**No FREE / Premium entitlement decision is made in this record.**

- The Semantic Core and Recommendation understanding are **upstream shared
  infrastructure**.
- `PremiumMeaningContext` is a **downstream consumer** (its
  `consultation.interpretedContext` is an opaque `Record<string, unknown> |
  null`, currently `null`).
- Semantic Core interpretation quality is **not** tier-dependent: FREE and
  Premium consume the *same* interpretation; Premium may *present* more of
  it, but does not get a "better" interpretation.
- `PremiumMeaningContext` is not changed here. Premium field availability is
  not defined here. Any entitlement decision belongs to a separate task.

---

## 18. Consequences

### Benefits

- **One canonical place for consultation meaning** — `NORMALIZE_MODEL` gives
  a single source of truth instead of the current three drifted keyword
  tables plus a shadow profile plus `consultation_axis`.
- **Semantic dimensions are no longer forced into `need_tag`** — topic,
  state, intention, polarity, primary/secondary, contrast, and explicit
  constraints each get a place to live instead of collapsing into one
  15-value list.
- **Evidence routing remains stable** — `need_tag` → `NEED_TO_GORIYAKU_IDS`
  → reviewed Evidence is untouched; the adapter emits the same `need_tags`
  the pipeline already consumes.
- **Current Recommendation can remain operational during migration** —
  `ADAPTER_GATED` rollout, `RANKING_REWRITE = NOT_REQUIRED`.
- **Compass can remain operational** — `need_tag` stays the shared routing
  key; `COMPASS_REWRITE = NOT_REQUIRED`.
- **Improved future observability** — a normalized core makes it possible to
  attribute a failure to the right layer: interpretation vs routing / need
  mapping vs Evidence vs ranking, instead of the current entanglement.

### Tradeoffs / costs

- The normalized Semantic Core **still needs actual schema design** — this
  record fixes the direction and the dimension scope, not the schema.
- **Parser / extraction quality remains unresolved** — representational
  capacity does not fix negation, clause segmentation, or open-ended
  state/intention detection.
- **Adapters must be owned and tested** — Semantic Core → `need_tag`,
  Semantic Core → `consultation_axis` view, Semantic Core → reason-v4, etc.,
  each with a parity guard so current outputs are preserved.
- **The current `InterpretationProfile` cannot simply be promoted** — its
  fields are derivations / layer-mixes / a psychological over-claim (§14).
- **D3–D6 remain open** — `consultation_axis` role, negation model,
  multi-signal policy, and interpretation-profile role are still to be
  decided.
- **Future runtime implementation must avoid duplicate semantic sources of
  truth** — once the Semantic Core exists, `need_tag`, `consultation_axis`,
  and any retained profile must be *derived*, never independently
  authoritative.

## 19. Known limitations

- This record does not define: the Semantic Core schema; the dimension
  value sets / taxonomy (a D2-adjacent design task); the routing-projection
  rules; the negation representation; the adapter contracts; any test plan.
- `NORMALIZE_MODEL` is a *capacity* decision. It does not by itself improve
  the interpreter's accuracy on the 34 canonical cases; the PR #2646 /
  #2647 nuance-loss findings persist until extraction work is done
  separately.
- `RANKING_REWRITE = NOT_REQUIRED` and `COMPASS_REWRITE = NOT_REQUIRED`
  describe D1-adoption obligations, not permanent commitments.

## 20. Deferred decisions

| decision | status |
|---|---|
| D3 `CONSULTATION_AXIS_ROLE` | **UNDECIDED** — next Mother Ship decision (§21) |
| D4 `INTERPRETATION_PROFILE_ROLE` | UNDECIDED (`SHADOW` / `PROMOTE` / `NORMALIZE_FIRST` / `DEPRECATE_CANDIDATE`) |
| D5 `NEGATION_MODEL` | UNDECIDED (`NO_CHANGE` / `PREPROCESS_GUARD` / `POLARITY_SIGNAL` / `CLAUSE_LEVEL_MODEL`) |
| D6 `MULTI_SIGNAL_POLICY` | UNDECIDED (`KEEP_MAX3_PRIORITY` / `EXPAND_LIST` / `PRIMARY_SECONDARY` / `STRUCTURED_MULTI_DIMENSION`) |
| Semantic Core schema / taxonomy | not started |
| Routing-projection rules | not started |
| Adapter contracts + parity test plan | not started |
| FREE / Premium field availability | separate task |
| Score v3 activation | separate decision (`SCORE_V3_MODE` stays `shadow`) |

## 21. D3 handoff

`D3 CONSULTATION_AXIS_ROLE` remains **UNDECIDED**. This record selects
**none** of `KEEP_CURRENT` / `DERIVED_ONLY` / `MULTI_VALUE_FUTURE` /
`DEPRECATE_CANDIDATE`. Evidence carried forward for the D3 decision:

- `consultation_axis` is a **single-value bottleneck** — one of 9 values;
  it drops every secondary axis and flips on secondary co-fired tokens
  (`consultation-understanding-architecture-audit.md` §12, L6/L7;
  `semantic-core-strategy-decision-audit.md`).
- Its runtime effect is **framing plus a ranking router** via
  `resolve_history_theme_candidate_boost(consultation_axis,
  shrine.history_theme)` added to `score_need_rank_weighted` and the
  prefilter score — it is the axis's only ranking contribution.
- It is **not** the canonical full consultation meaning; it is
  keyword-then-`need_tag`-fallback-derived and partially duplicates
  `need_tag`.
- The D1 / D2 decisions **reduce the pressure** to treat `consultation_axis`
  as a semantic source of truth: the Semantic Core now owns meaning, and
  `need_tag` owns routing, so `consultation_axis` can be reconsidered as a
  derived view and/or a ranking-routing concern without carrying semantic
  authority.

The D3 decision (its final role, single- vs multi-value, and whether the
`history_theme` boost is re-sourced) is the next Mother Ship step.

## 22. Evidence / audit references

| document | role |
|---|---|
| `docs/audit/semantic-core-strategy-decision-audit.md` (PR #2649) | D1 three-strategy comparison over 34 canonical cases; schema-vs-ranking separation; Decision Packet |
| `docs/audit/interpretation-profile-field-redesign-audit.md` (PR #2651) | five `InterpretationProfile` fields audited; all `DO_NOT_ROUTE`; `D2_EVIDENCE_IMPACT = SUPPORTS` |
| `docs/audit/consultation-understanding-architecture-audit.md` (PR #2647) | AS-IS semantic model; L1–L16 information-loss points; D1–D6 decision packet |
| `docs/audit/recommendation-nuance-quality-audit.md` (PR #2646) | 34 canonical consultation cases; first-loss-point / failure model; `need_tag` semantic overload |
| `docs/audit/ranking-contract-decision-record.md` | precedent for this decision-record convention (not a semantic input) |

---

## Repository Changes

- `docs/audit/semantic-core-d1-d2-decision-record.md`: this file (new).
- No other change. No runtime, test, contract, `PremiumMeaningContext`,
  interpreter, `consultation_axis` / `need_tags` / `NEED_TO_GORIYAKU_IDS`,
  scoring, ranking, Lead, Reason, Compass, Evidence, GoriyakuTag, Knowledge,
  migration, Production, or Spreadsheet change. No field renamed.
  `NORMALIZE_MODEL` and the routing adapter are **not** implemented. D3–D6
  are **not** decided.

## Stop

`D1_SEMANTIC_CORE_STRATEGY = NORMALIZE_MODEL` and
`D2_NEED_TAG_ROLE = EVIDENCE_ROUTING_LAYER` are recorded as final for this
task. Next step: **D3 `CONSULTATION_AXIS_ROLE`** Mother Ship decision.
