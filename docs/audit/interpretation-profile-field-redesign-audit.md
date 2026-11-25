# InterpretationProfile Field Redesign Audit

> **Status: AUDIT ONLY — READ-ONLY.** Provides evidence for the Mother Ship's
> future **D2 `NEED_TAG_ROLE`** decision and the normalized Semantic Core
> design under the already-selected **D1 `SEMANTIC_CORE_STRATEGY =
> NORMALIZE_MODEL`**. **No redesign is implemented. No runtime behaviour
> changes. D1 is not reopened. D2 is not selected. No field is renamed,
> promoted, or moved.**
>
> Base `origin/develop` = `a6543ec3d27cc4d33402779aa43b9cc694b052b4`
> (PR #2649 merge). Branch `audit/interpretation-profile-field-redesign`.
>
> Canonical inputs: `docs/audit/recommendation-nuance-quality-audit.md`
> (PR #2646), `docs/audit/consultation-understanding-architecture-audit.md`
> (PR #2647), `docs/audit/semantic-core-strategy-decision-audit.md`
> (PR #2649). **Runtime code is authoritative where it disagrees with those
> documents** — every claim below is re-derived from
> `a6543ec3` source + a pure-function probe (Appendix A).

---

## 1. Scope

Audit exactly these five current `InterpretationProfile` fields, produced by
`temples.services.consultation_interpreter.interpret_consultation()`:

1. `state_profile`
2. `emotion_profile`
3. `direction_profile`
4. `action_intent`
5. `constraint_profile`

| # | documented name | actual runtime field | status |
|---|---|---|---|
| 1 | `state_profile` | `state_profile` | **MATCH** |
| 2 | `emotion_profile` | `emotion_profile` | **MATCH** |
| 3 | `direction_profile` | `direction_profile` | **MATCH** (but collides with an unrelated frontend `direction_profile` — see §9) |
| 4 | `action_intent` | `action_intent` | **MATCH** |
| 5 | `constraint_profile` | `constraint_profile` | **MATCH** |

For each field: trace producer → transformation → consumers → behavioural
effect; evaluate on the §6 framework; classify Semantic Core disposition,
Need-routing eligibility, Concierge/Compass boundary, explanation/action
value, safety risk, and Stable-Contract readiness; and end with a neutral
Mother Ship Decision Packet.

The other three `interpret_consultation` blocks (`need_profile`,
`decision_context`, `outcome_hint`) are traced only where they interact with
the five targets; they are not the subject of this audit.

---

## 2. Non-goals

- Not implementing or designing the redesign; not writing a new taxonomy.
- Not selecting D2 `NEED_TAG_ROLE`; not reopening D1.
- Not renaming, moving, promoting, deprecating, or re-scoping any runtime
  field.
- Not modifying `NEED_TO_GORIYAKU_IDS`, `GoriyakuTag`, Knowledge Facts,
  Evidence, candidate generation, scoring, ranking, Lead, Reason, Compass,
  entitlement, analytics, the interpreter, tests, `PremiumMeaningContext`,
  API contracts, migrations, Production, or the Spreadsheet.
- Not treating semantic plausibility as Evidence approval (§18).
- Not asserting medical/psychological facts about users (§19).

---

## 3. Current Runtime Architecture

```text
POST concierge/chat  →  ConciergeChatView.post                       api_views_concierge.py:614
  interpretation_profile = interpret_consultation(query, need_tags=[])   consultation_interpreter.py
  │   raw_query = query.strip()
  │   state_profile      = build_state_profile(raw_query)            # STATE_KEYWORDS (5 buckets)
  │   need_profile       = build_need_profile(raw_query, need_tags)   # NEED_KEYWORDS (not audited here)
  │   direction_profile  = build_direction_profile(state_profile)     # DERIVED from state_profile
  │   emotion_profile    = build_emotion_profile(raw_query, state_profile)  # DERIVED from state_profile
  │   action_intent      = build_action_intent(raw_query)            # ACTION_KEYWORDS (visit/reflect/save)
  │   decision_context   = build_decision_context(raw_query)         # DECISION_KEYWORDS (not audited)
  │   constraint_profile = build_constraint_profile(raw_query)       # CONSTRAINT_KEYWORDS (time/money/energy/relationship)
  │   outcome_hint       = build_outcome_hint(raw_query)             # OUTCOME_KEYWORDS (not audited)
  │
  ├─ concierge_chat_candidates.build_chat_candidates(interpretation_profile)
  │     translate_meaning(interpretation_profile)                    meaning_translation.py:219
  │       reads: need_profile, direction_profile, action_intent, decision_context,
  │              constraint_profile, outcome_hint   (NOT state_profile / emotion_profile directly)
  │       → translation_result → candidate["history_context"]  (display field)
  │
  ├─ concierge_chat.build_chat_recommendations(interpretation_profile)
  │     _debug["interpretation_profile"] = profile                   concierge_chat.py:897   (STRIPPED at response)
  │     _build_score_v3_debug_payload(interpretation_profile)        # Score v3 SHADOW (SCORE_V3_MODE default "shadow")
  │     _attach_recommendation_reason_quality(interpretation_profile) concierge_chat.py:905
  │       recommendation_reason_v4._build_interpretation(profile)    recommendation_reason_v4.py:281
  │         reads: state_profile.primary_state, emotion_profile.intensity,
  │                need_profile, decision_context, constraint_profile, outcome_hint
  │         → rec["recommendation_reason_v4_detail"].interpretation  ← REACHES PUBLIC RESPONSE
  │       recommendation_reason_v4._build_action(profile)            recommendation_reason_v4.py:411
  │         reads: action_intent.intent, outcome_hint
  │         → rec["recommendation_reason_v4_detail"].action          ← REACHES PUBLIC RESPONSE
  │     attach_action_suggestion_v4_preview(recs)                    concierge_chat.py:1035
  │       action_suggestion_builder.build_action_suggestion(interpretation_profile)
  │         reads: decision_context, constraint_profile, outcome_hint  (NOT state/emotion/direction/action_intent directly)
  │         → rec["action_suggestion_v4_preview"]                    ← REACHES PUBLIC RESPONSE
  │
  └─ _build_chat_response(recs)                                      api_views_concierge.py:320
        data.pop("_debug", None)                                    api_views_concierge.py:340
        (raw state_profile / emotion_profile / direction_profile / action_intent /
         constraint_profile are inside _debug → STRIPPED; never reach the client
         as raw fields)
        (rec["recommendation_reason_v4_detail"], rec["action_suggestion_v4_preview"]
         survive on the rec object → the ONLY user-facing surface of these 5 fields)

Compass:  compass_recommendation_orchestrator.get_compass_recommendations       :221
        interpret_consultation(query="", need_tags=[purpose])       → all 5 target fields EMPTY
        (STATE/EMOTION/DIRECTION/ACTION/CONSTRAINT all None/[] for every Compass request)
```

**Producer:** the single producer of `InterpretationProfile` is
`interpret_consultation()` in `backend/temples/services/consultation_interpreter.py`.
It is called from exactly two sites:
`api_views_concierge.ConciergeChatView.post` (Concierge, real free text) and
`compass_recommendation_orchestrator.get_compass_recommendations` (Compass,
`query=""`).

**Consumers of the profile as a whole:** `translate_meaning`
(`meaning_translation.py`), `recommendation_reason_v4`
(`_build_interpretation` / `_build_used_interpretation` / `_build_action`),
`recommendation_score_components.calculate_state_match_score` (Score v3
**shadow**), `recommendation_input_profile.build_recommendation_input_profile`,
`shrine_meaning_composer` (carries it into `meaning_payload.source`),
`action_suggestion_builder.build_action_suggestion`, and the `_debug`
envelope in `concierge_chat.py` (stripped at the response boundary).

**No frontend file reads any of the five raw fields.** `apps/web/src/lib/api/concierge/types.ts`
does not declare `state_profile` / `emotion_profile` / `direction_profile` /
`action_intent` / `constraint_profile`. The frontend only sees their
*transformed* output via `rec.recommendation_reason_v4_detail`
(`buildHeroReasonV4Sections.ts`, `buildShrineDetailReasonV4Sections.ts`,
`ConsultationHistoryDetailView.tsx`, `shrines/[id]/page.tsx`) and
`rec.action_suggestion_v4_preview` (`conciergeToShrineList.ts`,
`actionSuggestionV4Preview.ts`, `journey_timeline.py`,
`features/concierge/hooks.ts`). `constraint_profile` appears in
`conciergeResultItem.ts` / `actionSuggestionV4Preview.ts` **only as a
provenance-key string**, never as a value.

**`PremiumMeaningContext` (PR #2648/#2650):**
`consultation.interpretedContext` is `Record<string, unknown> | null`,
**fixed to `null`** by the PR-B mapper ("the only candidate source
(`interpret_consultation()` / InterpretationProfile) is debug-only, not a
stable Contract field … does not read `_debug`"). None of the five fields
flows into `PremiumMeaningContext` today.

**Analytics / observability:** `_build_user_state_profile`
(`concierge_chat.py:124`, despite its name) is built from
`need_tags` / `consultation_axis` / ranked recommendations — **not** from
`state_profile`; it is `_debug`-only. `observe_direction_signal` /
`observe_profile_signal` (`concierge_chat_observation.py`) observe the
birthdate-derived *geographic* direction and worship-style profile — **not**
`direction_profile` — and are `_debug`-only.

**Tests:** `backend/temples/tests/services/test_consultation_interpreter.py`
(6 tests: stable-schema, `state_need_direction_and_action` extraction,
`v4_fields`, explicit-need-tag merge, `selected_goriyaku_tag_ids`,
empty-query safety); `test_meaning_translation.py`;
`test_recommendation_reason_v4.py`; `test_recommendation_score_components.py`;
`test_action_suggestion_builder.py`. **None** asserts negation behaviour,
clause behaviour, false-positive suppression, or `primary_state` ordering.

---

## 4. Actual Field Schema (`a6543ec3`)

### 4.1 `state_profile` — `build_state_profile(query)`

```python
STATE_KEYWORDS = {
  "tired":           ("疲れ", "しんど", "休み", "癒"),
  "anxious":         ("不安", "怖", "心配", "焦り"),
  "uncertain":       ("迷", "わから", "決められ", "悩"),
  "stuck":           ("停滞", "動け", "進ま", "詰ま"),
  "ready_to_change": ("変えたい", "切り替え", "やり直", "始めたい"),
}
# output:
{ "primary_state": states[0] | None,      # states = list(hits.keys()) → STATE_KEYWORDS DECLARATION order, NOT hit count / salience
  "secondary_states": states[1:],
  "state_hits": {bucket: [matched substrings]},
  "confidence": min(0.95, 0.45 + total_substring_hits * 0.12) }   # 0 hits → 0.0
```

- Pure substring `in` match (`_collect_hits`). No normalization, no width
  folding, no clause segmentation, **no negation handling**.
- `primary_state` = first key inserted into `hits` = the first STATE_KEYWORDS
  bucket (by declaration) that matched — **not** the most-hit or
  most-central. `tired` outranks `anxious` outranks `uncertain` … regardless
  of the query.
- `confidence` is a linear function of *substring hit count*, not of
  certainty.

### 4.2 `emotion_profile` — `build_emotion_profile(query, state_profile)`

```python
{ "tone": state_profile["primary_state"] or "unknown",                 # verbatim relabel of state
  "intensity": "high" if confidence>=0.75 else "medium" if confidence>=0.45 else "low" if signals else "unknown",
  "signals": sorted(set(all state_hits substrings)) }
```

- **The `query` argument is never used.** `emotion_profile` is a 100 %
  deterministic re-view of `state_profile`: `tone` is `primary_state`
  verbatim; `intensity` is a bucketed `state_profile.confidence`; `signals`
  is the flattened `state_hits`.

### 4.3 `direction_profile` — `build_direction_profile(state_profile)`

```python
DIRECTION_BY_STATE = {
  "tired":           ("rest",      ("静寂", "復興")),
  "anxious":         ("stabilize", ("守り", "静寂")),
  "uncertain":       ("review",    ("静寂", "再出発")),
  "stuck":           ("reset",     ("再出発", "静寂")),
  "ready_to_change": ("challenge", ("再出発", "勝負")),
}
{ "direction": DIRECTION_BY_STATE[primary_state][0] | None,     # rest|stabilize|review|reset|challenge  (motivational stance)
  "themes":    list(DIRECTION_BY_STATE[primary_state][1]),      # history_theme-namespace values
  "source_state": primary_state }                              # names its own dependency
```

- **100 % derived from `state_profile.primary_state`.** No query input.
- `direction` values are a *motivational framing / stance* vocabulary
  (`rest` / `stabilize` / `review` / `reset` / `challenge`) — **not**
  geographic direction, **not** Compass `houi`, **not** consultation
  intention, **not** recommendation direction.
- `themes` are drawn from the `history_theme` namespace (`静寂` `守り`
  `再出発` `勝負` `復興`) shared with `SCORE_V3_HISTORY_THEME_BY_AXIS` and the
  shrine `history_theme` column.

### 4.4 `action_intent` — `build_action_intent(query)`

```python
ACTION_KEYWORDS = {
  "visit":   ("行きたい", "参拝", "神社", "場所", "向かう"),
  "reflect": ("考えたい", "整理", "見つめ", "振り返"),
  "save":    ("残したい", "保存", "記録"),
}
{ "intent": intents[0] | None,           # ACTION_KEYWORDS declaration order
  "strength": "soft" if any hit else "unknown",
  "candidates": intents,
  "intent_hits": {bucket: [matched]} }
```

- `visit` fires on the bare topic word **`神社`** (any query naming a shrine).
- `reflect` fires on **`整理`** — which is also a *consultation* verb
  ("気持ちを整理したい" = want to sort out my feelings), i.e. a
  semantic-intention token mislabelled as a product action.
- `save` fires on 記録 / 保存 / 残したい (genuine product actions).

### 4.5 `constraint_profile` — `build_constraint_profile(query)`

```python
CONSTRAINT_KEYWORDS = {
  "time":         ("時間がない", "忙しい", "余裕がない"),
  "money":        ("お金が不安", "生活費", "収入", "金銭"),
  "energy":       ("疲れ", "しんど", "体力", "休みたい"),
  "relationship": ("人間関係", "家族", "職場", "相手"),
}
{ "primary_constraint": constraints[0] | None,   # CONSTRAINT_KEYWORDS declaration order
  "constraints": constraints,
  "constraint_hits": {bucket: [matched]} }
```

- `time` = the only genuinely *explicit practical constraint* vocabulary —
  and it is exact-substring only (`時間がない`, not `時間があまりない`).
- `energy` fires on **`疲れ` / `休みたい`** — which are *state / topic*
  tokens (`mental` / `rest`).
- `relationship` fires on **`人間関係` / `家族` / `職場`** — which are
  *relationship topic* tokens.
- `money` fires on `収入` (also a `money` topic token).

---

## 5. Producer / Consumer Dependency Graph

```text
                         query (raw free text; Compass: "")
                           │
                 ┌─────────┴──────────────────────────────────────────────┐
                 ▼                                                        ▼
      build_state_profile(query)                             build_action_intent(query)     build_constraint_profile(query)
      STATE_KEYWORDS ×5                                       ACTION_KEYWORDS ×3             CONSTRAINT_KEYWORDS ×4
                 │                                                        │                              │
     ┌───────────┼───────────────┐                                       │                              │
     ▼           ▼               ▼                                       │                              │
 state_profile   build_emotion_profile(_, state_profile)   build_direction_profile(state_profile)       │
     │           = emotion_profile (100% derived)          = direction_profile (100% derived)           │
     │           tone=primary_state, intensity=conf-bucket  direction∈{rest..challenge}, themes         │
     │                     │                                          │                                 │
     ▼                     ▼                                          ▼                                 ▼
 recommendation_reason_v4._build_interpretation ──────────────────────┴───────────── translate_meaning ─┤
   reads state_profile.primary_state + emotion_profile.intensity        reads direction_profile,       reads constraint_profile.primary_constraint
   → JA copy ("不安や心配を中心に、要素があります")                        action_intent, decision_context,  → SHRINE_CONTEXT_NEED_BY_CONSTRAINT text
   → rec.recommendation_reason_v4_detail.interpretation                  constraint_profile, outcome_hint  → translation_result.shrine_context_need
   → PUBLIC RESPONSE (display)                                           → history_theme / history_theme_secondary / shrine_context_need / action_context
                                                                        → candidate.history_context (display)
 recommendation_score_components.calculate_state_match_score            → Score v3 shadow (history_score, meaning_match_score)
   reads state_profile → Score v3 SHADOW (weight 0.45)                  → recommendation_reason_v4._build_action
   (SCORE_V3_MODE default "shadow" → NOT in sort order)                     reads action_intent.intent + outcome_hint
                                                                           → rec.recommendation_reason_v4_detail.action → PUBLIC RESPONSE (display)
 recommendation_reason_v4._build_interpretation also reads               action_suggestion_builder.build_action_suggestion
   constraint_profile.primary_constraint (theme fallback)                 reads decision_context + constraint_profile + outcome_hint
                                                                          → rec.action_suggestion_v4_preview → PUBLIC RESPONSE (display)
 _debug["interpretation_profile"] = whole profile  →  _build_chat_response pops "_debug"  →  STRIPPED
```

### 5.1 Per-field INPUT → PRODUCER → TRANSFORMATION → FIELD → CONSUMERS → BEHAVIOURAL EFFECT

| field | INPUT | PRODUCER | TRANSFORMATION | CONSUMERS | BEHAVIOURAL EFFECT |
|---|---|---|---|---|---|
| `state_profile` | raw query | `build_state_profile` | substring hits vs `STATE_KEYWORDS`; `primary_state` = first bucket by declaration; `confidence` = 0.45 + 0.12·hits | `recommendation_reason_v4._build_interpretation` (→ `_v4_detail.interpretation` copy, **response**); `recommendation_score_components` (Score v3 **shadow**); `emotion_profile` (derived); `direction_profile` (derived); `_debug` (stripped) | **MIXED** — `SHADOW_ONLY` for sort order; `DISPLAY_ONLY` and *load-bearing for the user-visible reason-v4 interpretation text* |
| `emotion_profile` | `state_profile` only | `build_emotion_profile` | `tone` = `primary_state`; `intensity` = confidence bucket; `signals` = flattened hits | `recommendation_reason_v4._build_interpretation` (`intensity` → "要素が強めに出ています" vs "要素があります", **response**); `_debug` | **DISPLAY_ONLY** (one adjective in reason-v4 copy) + **DERIVED_ONLY** (no independent signal) |
| `direction_profile` | `state_profile.primary_state` | `build_direction_profile` | `DIRECTION_BY_STATE` lookup | `translate_meaning` (`direction` → `HISTORY_THEME_BY_DIRECTION` → `history_theme`; `themes[1]` → `history_theme_secondary`) → candidate `history_context` (display), Score v3 **shadow**, reason-v4; `_debug` | **DERIVED_ONLY** + `SHADOW_ONLY` (ranking) + `DISPLAY_ONLY` (history_context text) |
| `action_intent` | raw query | `build_action_intent` | substring hits vs `ACTION_KEYWORDS` | `recommendation_reason_v4._build_action` (→ `_v4_detail.action`, **response**); `translate_meaning._resolve_action_context` (`ACTION_CONTEXT_BY_INTENT`, but `outcome_hint` is checked first); `_debug` | **DISPLAY_ONLY** (action-context text; fires in ~3/34 cases) |
| `constraint_profile` | raw query | `build_constraint_profile` | substring hits vs `CONSTRAINT_KEYWORDS` | `recommendation_reason_v4._build_interpretation` (theme fallback); `translate_meaning._resolve_shrine_context_need` (`SHRINE_CONTEXT_NEED_BY_CONSTRAINT`); `action_suggestion_builder` (`primary_constraint`); frontend provenance keys; `_debug` | **DISPLAY_ONLY** (shrine-context-need + action-suggestion text) |

**None of the five is `LOAD_BEARING` for candidate generation, `score_need`,
the C1 winner, or the default sort order.** All ranking influence is gated
behind `SCORE_V3_MODE = active` (default `shadow`), and even then flows only
through the `state_profile`→Score-v3 and `direction_profile`→`history_theme`
paths. Their real current effect is on **user-visible explanation text**
(reason-v4 detail + action-suggestion preview), which is where the §16 safety
risk lands.

---

## 6. Evaluation Framework Results

Legend: A OBSERVABILITY (`DIRECT` groundable in wording / `INDIRECT` / `NOT`),
B INFERENCE_DEPTH, C PSYCHOLOGICAL_ASSERTION_RISK, D FALSE_POSITIVE_RISK,
E NEGATION_SENSITIVITY, F CLAUSE_SENSITIVITY, G SEMANTIC_CORE_VALUE,
H EVIDENCE_ROUTING_VALUE, I EXPLANATION_VALUE, J ACTION_UX_VALUE,
K COMPASS_VALUE, L STABLE_CONTRACT_READINESS.

| field | A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `state_profile` | INDIRECT (a keyword is groundable; the *label* "state" is not) | STRONG_INFERENCE | **HIGH** | **HIGH** | **YES** | **YES** | MEDIUM | LOW | MEDIUM | LOW | NONE | `REQUIRES_REDESIGN` |
| `emotion_profile` | NOT (no independent input) | UNSUPPORTED_INFERENCE (re-labels state) | **HIGH** | **HIGH** (inherits state's) | YES (inherits) | YES (inherits) | LOW | NONE | LOW | LOW | NONE | `NOT_SUITABLE` (as "emotion") |
| `direction_profile` | NOT (derived) | STRONG_INFERENCE (state → stance) | MEDIUM | MEDIUM (inherits state's) | YES (inherits) | YES (inherits) | LOW (no new meaning) | LOW | MEDIUM (feeds history_theme) | MEDIUM | NONE (name collides; Compass never populates) | `REQUIRES_REDESIGN` (+ rename) |
| `action_intent` | DIRECT for `visit`/`save`; INDIRECT for `reflect` | LIGHT_INFERENCE (visit/save) / STRONG (reflect≈closure) | LOW | MEDIUM (`神社` topic → `visit`) | CONDITIONAL | CONDITIONAL | LOW (as consultation semantics) | NONE | MEDIUM | **HIGH** (product/visit action) | LOW | `REQUIRES_REDESIGN` (split) |
| `constraint_profile` | DIRECT for `time`; INDIRECT/NOT for `energy`/`relationship`/`money` | LIGHT (`time`) / STRONG (`energy`,`relationship` from topic) | LOW | **HIGH** (`energy`←疲れ topic; `relationship`←人間関係/家族 topic) | CONDITIONAL | **YES** (which clause owns the token) | LOW | NONE (do not infer GID) | MEDIUM (practical framing) | **HIGH** (practical filter) | LOW | `REQUIRES_REDESIGN` (restrict to explicit) |

Evidence for every cell is in §7–§11 and the Appendix A probe.

---

## 7. `state_profile` Audit

### 7.1 What it currently represents — a mixture

`state_profile` is produced from a **linguistic signal** (5 fixed keyword
buckets, substring match) but is **named, structured, and consumed as a
psychological state**: the field is `primary_state`; `emotion_profile.tone`
copies it verbatim; `recommendation_reason_v4._build_interpretation` maps it
to first-person-facing copy —
`{"uncertain":"判断に迷う様子","tired":"無理なく休みたい様子","anxious":"不安や心配","stuck":"停滞を見直したい様子","ready_to_change":"流れを切り替えたい様子"}`
— which reaches `rec.recommendation_reason_v4_detail.interpretation` and the
Hero Reason sections. It is simultaneously: a **linguistic signal** (what it
measures), a **psychological-state assertion** (how it is labelled and
rendered), a **consultation-framing hint** (feeds `direction_profile` →
`history_theme`), and a **recommendation hint** (Score v3 shadow, weight
0.45). → **MIXTURE**, dominated by "linguistic signal presented as
psychological state".

### 7.2 Producer rules that can fire it

`tired` ← 疲れ / しんど / 休み / 癒 · `anxious` ← 不安 / 怖 / 心配 / 焦り ·
`uncertain` ← 迷 / わから / 決められ / 悩 · `stuck` ← 停滞 / 動け / 進ま / 詰ま ·
`ready_to_change` ← 変えたい / 切り替え / やり直 / 始めたい. Substring only; no
alias table; no fallback; `primary_state` = first matching bucket by
declaration order (`tired > anxious > uncertain > stuck > ready_to_change`).

### 7.3 Concrete false-positive / over-reach / negation examples (probe, §Appendix A)

| input | `primary_state` | why it is a problem |
|---|---|---|
| `子どものことが心配` (Family-B) | **anxious** (`心配`) | ordinary caregiving language → the system asserts "the user is anxious" (`emotion.tone=anxious`, copy "不安や心配を中心に") |
| `不安ではないけど迷っている` (Neg-3) | **anxious** (`不安`) + secondary `uncertain` | matched the **explicitly negated** word; `primary_state` is the opposite of what the user said → **NEGATION_SENSITIVITY = YES** |
| `休みたいというより環境を変えたい` (Neg-5) | **tired** (`休み`) + `ready_to_change` | matched the **de-emphasised** clause; frames a change-of-environment consultation as fatigue |
| `転職したいけど一歩踏み出すのが怖い` (Career-B) | **anxious** (`怖`) | "踏み出すのが怖い" = normal hesitation about a decision → asserted as anxiety; drives `direction=stabilize`, `themes=[守り,静寂]` |
| `最近ずっと気持ちが落ち着かない` (MR-A) | **None** | the flagship "restlessness" state has **no** `STATE_KEYWORDS` bucket (`落ち着` is absent) → the one case most about state produces no state |
| `仕事が忙しくて気持ちが落ち着かない` (Career-D) | **None** | same gap |
| `疲れていて決められない` (latent, not in 34) | **tired** (declaration order) | `uncertain` also hits (`決められ`) but `tired` wins by declaration, not salience → `primary_state` can misrepresent the central concern |

### 7.4 Verdict

```text
STATE_PROFILE_STABLE_AS_IS            = NO
   (name asserts a psychological state it cannot observe; negation- and
    clause-sensitive; primary_state ordering is arbitrary; the central
    "unsettled" state has no bucket; C = HIGH, D = HIGH, E = YES, F = YES)

STATE_PROFILE_REDEFINITION_REQUIRED   = YES
   Minimum conditions for a Stable Contract concept (illustrative name only —
   e.g. `expressed_state` / `user_expressed_signal`, NOT selected here):
     1. definition = "a signal grounded in the user's own wording", never
        "the user's mental/emotional condition";
     2. every value carries a `polarity` (asserted / negated / de-emphasised)
        and an explicit source span, so a negated token cannot set it;
     3. `primary` selection is salience- or count-based, not declaration
        order, or the field is multi-valued with no forced primary;
     4. coverage gap closed or documented (unsettled / restless / loss-of-
        confidence / grief have no bucket today);
     5. downstream copy templates reworded to describe *expression*
        ("落ち着かない気持ちについて書かれています"), not diagnosis;
     6. deterministic output shape + false-positive/negation test corpus;
     7. named producer owner + versioning if externally exposed.

STATE_PROFILE_NEED_ROUTING_ELIGIBILITY = DO_NOT_ROUTE
   Semantically plausible for `mental` / `rest` need_tags, but: (a) no
   approved `NEED_TO_GORIYAKU_IDS` mapping exists for a "state" input
   (§18 SEMANTIC_ROUTING_PLAUSIBLE / EVIDENCE_ROUTING_NOT_APPROVED); (b) E =
   YES means a negated token could route evidence; (c) mapping "the user is
   anxious" → a GoriyakuTag would be a psychological assertion feeding
   recommendation (§16). Useful only for EXPLANATION and (post-redesign,
   with polarity) OBSERVABILITY.
```

---

## 8. `emotion_profile` Audit

### 8.1 Source

`build_emotion_profile(query, state_profile)` — **`query` is unused.**
`tone` = `state_profile["primary_state"]` verbatim (or `"unknown"`);
`intensity` = a 3-way bucket of `state_profile["confidence"]` (which is
itself `0.45 + 0.12 · substring_hit_count`); `signals` = the flattened
`state_hits`.

### 8.2 Is it measuring emotion?

**No.** It is a **relabel of another heuristic.** `tone` is the state bucket
under a different name; `intensity` is *how many state keywords matched*
("high" needs `confidence ≥ 0.75` ⇒ ≥ 3 substring hits — reached by **0** of
the 34 cases; every non-empty case is "medium"). There is no affect
lexicon, no valence/arousal model, no independent signal.

### 8.3 Propagation chain (state error → emotion error)

`state_profile.primary_state` wrong ⇒ `emotion_profile.tone` wrong (1:1).
Probe: Neg-3 `state=anxious` (from negated 不安) ⇒ `emotion.tone=anxious`,
`signals=['不安','迷']`, `intensity=medium` ⇒ reason-v4 copy renders "不安や
心配を中心に、要素があります" for a user who said they are **not** anxious.
Family-B: `心配` ⇒ `state=anxious` ⇒ `emotion.tone=anxious` for a parent's
ordinary worry. Every `state_profile` false positive in §7.3 is also an
`emotion_profile` false positive.

### 8.4 Verdict

```text
EMOTION_PROFILE_INDEPENDENT_SIGNAL     = NO   (query unused; 100% derived from state_profile)
EMOTION_PROFILE_STATE_DEPENDENCY       = TOTAL (tone = primary_state; intensity = f(confidence); signals = state_hits)
EMOTION_PROFILE_STABLE_AS_IS           = NO
   (as an "emotion" field it over-claims; L = NOT_SUITABLE under that name)
EMOTION_PROFILE_REDEFINITION_REQUIRED  = YES  (either DEPRECATE as a redundant view of state_profile, or
   redefine as a non-diagnostic `expressed_intensity` / `affective_language_signal` that is honestly
   "count/strength of affect-language tokens", not "emotional intensity"; requires its own token
   evidence, not a state_profile re-view, to become independent)
EMOTION_PROFILE_NEED_ROUTING_ELIGIBILITY = DO_NOT_ROUTE  (adds nothing state_profile does not; routing a
   derived relabel is strictly worse than routing its source, which is itself DO_NOT_ROUTE)
```

---

## 9. `direction_profile` Audit

### 9.1 What it actually means

`build_direction_profile(state_profile)` → `DIRECTION_BY_STATE[primary_state]`.
`direction ∈ {rest, stabilize, review, reset, challenge}` is a **motivational
framing / recommended stance** ("given this state, lean toward rest /
stabilising / reviewing / resetting / challenging"). `themes` are
`history_theme`-namespace labels. `source_state` names the dependency
explicitly.

- It is **not** semantic direction (topic), **not** intention (the user's
  goal), **not** geographic direction, **not** Compass `houi`, **not**
  "recommendation direction". It is derived motivational framing.
- **Name collision (already flagged in code):**
  `apps/web/src/features/concierge/types/chatRequest.ts:73-75` comments that
  the client `direction_profile` is the *kyusei (九星) lucky-direction
  geographic calculation* (`MyPageView.tsx` `buildDirectionProfile(form)` →
  `targetYear`, `luckyDirections`), a completely unrelated concept; the
  comment explicitly distinguishes it from
  `consultation_interpreter.build_direction_profile()`.
  `observe_direction_signal` (`concierge_chat_observation.py`) likewise
  observes the *geographic* direction, not this field.

### 9.2 Producers / consumers

Producer: `build_direction_profile` (state-derived only). Consumers:
`translate_meaning._resolve_history_theme` (`direction` →
`HISTORY_THEME_BY_DIRECTION` → `history_theme`) and
`_resolve_history_theme_secondary` (`themes[1]`) →
`translation_result` → candidate `history_context` (display), Score v3
`history_score` / `meaning_match_score` (**shadow**), reason-v4. `_debug`.
The **live** ranking's `resolve_history_theme_candidate_boost` uses
`consultation_axis` + the *shrine's* `history_theme` column, **not** this
field.

### 9.3 Concierge / Compass boundary

- **Concierge:** it is *derived framing* over `state_profile`, not new
  consultation meaning. It duplicates information already in
  `state_profile` / `emotion_profile` and re-projects it into the
  `history_theme` namespace.
- **Compass:** `get_compass_recommendations` calls
  `interpret_consultation(query="")` → `state_profile` empty →
  `direction_profile` empty for **every** Compass request. Compass derives
  its own (geographic) direction from birthdate elsewhere. There is **no**
  current Compass use and **no** reusable value without a *different
  producer* (geographic direction needs birthdate + target date, not a
  consultation state).

### 9.4 Verdict

```text
DIRECTION_PROFILE_CONCIERGE_ROLE          = DERIVED_MOTIVATIONAL_FRAMING (over state_profile) — not consultation meaning
DIRECTION_PROFILE_COMPASS_ROLE            = NONE (never populated for Compass; not the geographic concept; name collides)
DIRECTION_PROFILE_SEMANTIC_CORE_ELIGIBILITY = DERIVED_VIEW  (a projection of the state/intention dimensions;
   its only unique artefact is the history_theme routing, which is a translation concern, not core meaning)
DIRECTION_PROFILE_NEED_ROUTING_ELIGIBILITY = DO_NOT_ROUTE  (state-derived; inherits E/F sensitivity; no Evidence mapping)
DIRECTION_PROFILE_GENERATION_STATUS        = STATE_DERIVED_ONLY, NO_INDEPENDENT_EVIDENCE, RENAME_REQUIRED
   (the name must not be shared with the geographic frontend `direction_profile`)
```

---

## 10. `action_intent` Audit

### 10.1 Runtime values and activators

`visit` ← 行きたい / 参拝 / **神社** / 場所 / 向かう · `reflect` ← 考えたい /
**整理** / 見つめ / 振り返 · `save` ← 残したい / 保存 / 記録.
`intent` = first bucket by declaration order; `strength` = "soft" if any hit
else "unknown". Fired in the probe by **only 3 of 34** canonical cases
(Love-E → `reflect` via 整理; plus `PROBE-A1` → `visit`, `PROBE-A2` → `save`).

### 10.2 Three concepts being conflated

| concept | question | belongs to `action_intent` today? |
|---|---|---|
| A. consultation intention | "what does the user want to change / protect / resolve / pursue?" | leaks in via **`reflect` ← 整理** (Love-E "気持ちを整理したい" = closure, a consultation intention) |
| B. product action intent | "what does the user want to do *inside KAMI MUSUBI*?" | yes — 保存 / 記録 → `save` |
| C. visit behaviour | "does the user intend to visit / save / reflect?" | yes — 行きたい / 参拝 / 向かう → `visit` |

Topic keywords mistaken for action intent: **`神社`** (any shrine mention) →
`visit`; **`整理`** (sort out feelings) → `reflect`.

### 10.3 Classification

`action_intent` is **MIXED** — predominantly `PRODUCT_ACTION` /
`VISIT_ACTION` vocabulary, with a `SEMANTIC_INTENTION` leak through
`reflect ← 整理`. Only the semantic-intention slice ("reflect / clarify /
organise-my-thinking") is a candidate for the future Semantic Core
`intention` dimension; `visit` and `save` are UX/action-layer concerns and
should not sit in consultation semantics.

### 10.4 Verdict

```text
ACTION_INTENT_CURRENT_ROLE                 = MIXED (PRODUCT_ACTION + VISIT_ACTION, with a SEMANTIC_INTENTION leak via `reflect`←整理)
ACTION_INTENT_TOPIC_COUPLING               = YES (`神社` → `visit`; `整理` → `reflect`)
ACTION_INTENT_SEMANTIC_CORE_ELIGIBILITY    = PARTIAL — only the "reflect/organise/clarify" sense maps to a future
   `intention` dimension; needs to be separated from visit/save first (INSUFFICIENT_EVIDENCE for visit/save as semantics)
ACTION_INTENT_ACTION_LAYER_ELIGIBILITY     = HIGH (visit/save are product/visit actions → ACTION_LAYER)
ACTION_INTENT_NEED_ROUTING_ELIGIBILITY     = DO_NOT_ROUTE (product/visit actions have no Evidence-routing meaning;
   the `reflect` sense is an explanation/action concern, not a GID selector)
```

---

## 11. `constraint_profile` Audit

### 11.1 Category-by-category classification

| bucket | tokens | what it actually is |
|---|---|---|
| `time` | 時間がない / 忙しい / 余裕がない | **CONSTRAINT** (explicit practical limit) — but exact-substring only; `PROBE-C1 "時間があまりない"` does **not** match |
| `money` | お金が不安 / 生活費 / 収入 / 金銭 | **MIXED** — "お金が不安" is a state; 生活費 / 収入 are money-topic tokens; genuine-constraint only if the user names a budget limit (`PROBE-C3 "予算をかけたくない"` does **not** match) |
| `energy` | 疲れ / しんど / 体力 / 休みたい | **STATE / TOPIC**, not a constraint — 疲れ / 休みたい are `mental` / `rest` tokens; fires on MR-B, MR-C, Neg-5, Theme-2 purely because those are fatigue *expressions* |
| `relationship` | 人間関係 / 家族 / 職場 / 相手 | **DOMAIN / TOPIC**, not a constraint — fires on Career-F ("職場の人間関係" = the topic), Family-A / Family-D ("家族" = the topic), **Travel-A** ("家族旅行" = 家族 is a trip modifier) |

### 11.2 Domain / topic → constraint conflation (probe)

| input | `primary_constraint` | correct reading |
|---|---|---|
| `職場の人間関係がうまくいかない` (Career-F) | **relationship** | relationship is the *topic*, not a limiting constraint |
| `家族旅行の安全を祈願したい` (Travel-A) | **relationship** | 家族 modifies the trip; there is no constraint |
| `何もしたくないくらい疲れている` (MR-B) | **energy** | fatigue is the *state / topic*, not a practical "energy budget" |
| `お金について相談したい` (`PROBE-M1`) | **None** (does not match) | correct here — but only because `お金` alone is not in the table; `収入` would have conflated |
| `体力的に長時間は難しい` (`PROBE-C4`) | **energy** | *this* is a genuine explicit constraint — and it matches only via `体力` |
| `時間があまりない` / `遠くまでは行けない` / `予算をかけたくない` (`PROBE-C1/C2/C3`) | **None** | genuine explicit constraints that the current vocabulary **misses** |

Net: of 5 `constraint_profile` firings across the 34 canonical cases, **all 5
are topic/state conflations** (Career-F, Family-A, Family-D, Travel-A ×
relationship; MR-B/MR-C/Neg-5/Theme-2 × energy — several cases). The genuine
explicit-constraint probes (`時間があまりない`, `遠くまでは行けない`,
`予算をかけたくない`) are **not detected**.

### 11.3 Verdict

```text
CONSTRAINT_PROFILE_DOMAIN_CONFLATION   = HIGH  (`energy` ← fatigue state/topic; `relationship` ← relationship topic;
   every canonical-case firing is a conflation; `time` is the only clean category and it under-matches)
CONSTRAINT_PROFILE_EXPLICITNESS        = LOW   (only `time` targets explicit constraints; even it is exact-substring;
   real explicit constraints — distance, budget, time-availability phrased naturally — are missed)
CONSTRAINT_PROFILE_STABLE_AS_IS        = NO
CONSTRAINT_PROFILE_REDEFINITION_REQUIRED = YES
   Minimum conditions: (1) restrict to *explicitly stated* practical limits (time / distance / budget /
   physical-availability), with a wording-grounded producer; (2) exclude any token that is also a topic or
   state token; (3) clause-scope the match (which clause owns "疲れ"?); (4) target role is a PRACTICAL_FILTER /
   ACTION_MEANING signal, NOT consultation semantics and NOT Evidence routing.
CONSTRAINT_PROFILE_NEED_ROUTING_ELIGIBILITY = DO_NOT_ROUTE (a constraint limits *how* to act, not *what* the
   consultation is about; no Evidence meaning; conflation would route topics as constraints)
```

---

## 12. Cross-Field Collision Matrix

Pairs classified `INDEPENDENT` / `DERIVED` (one is computed from the other) /
`OVERLAPPING` (share inputs / meaning partially) / `DUPLICATED` (carry the
same information) / `CONFLATED` (one wrongly activates from the other's
domain) / `UNKNOWN`.

| ↓ from \ → to | `state_profile` | `emotion_profile` | `direction_profile` | `action_intent` | `constraint_profile` |
|---|---|---|---|---|---|
| **`state_profile`** | — | **DERIVED** (`emotion` is 100% computed from `state`) | **DERIVED** (`direction` is 100% computed from `state.primary_state`) | INDEPENDENT (different keyword table) | **CONFLATED** (`state` "疲れ"/"しんど" ⇒ `constraint.energy` from the same tokens) |
| **`emotion_profile`** | **DUPLICATED** (`tone` = `state.primary_state`; `signals` = `state_hits`) | — | **OVERLAPPING** (both are pure functions of `state.primary_state`) | INDEPENDENT | OVERLAPPING (shares the fatigue tokens transitively via `state`) |
| **`direction_profile`** | **DERIVED** (via `source_state`) | **OVERLAPPING** (sibling derivations of `state`) | — | INDEPENDENT | INDEPENDENT |
| **`action_intent`** | INDEPENDENT | INDEPENDENT | INDEPENDENT | — | INDEPENDENT (but `visit`←`神社` and `constraint.relationship`←`職場`/`家族` are both topic→field conflations of the *same* class) |
| **`constraint_profile`** | **CONFLATED** (`energy`←"疲れ"/"休みたい" = state/`rest` tokens) | OVERLAPPING (transitive) | INDEPENDENT | INDEPENDENT | — |

### 12.1 Cascade failures (actual runtime paths)

1. **`state` → `emotion` → `direction` → `history_theme` → Reason copy.**
   One negated/topic keyword sets `state.primary_state`, which
   *deterministically* sets `emotion.tone`, `emotion.intensity`,
   `direction.direction`, `direction.themes`, then
   `translate_meaning.history_theme` / `history_theme_secondary`, then
   `recommendation_reason_v4_detail.interpretation` copy.
   Probe — **Neg-3 `不安ではないけど迷っている`**: `不安` (negated) ⇒
   `state=anxious` ⇒ `emotion.tone=anxious`, `signals=['不安','迷']` ⇒
   `direction=stabilize`, `themes=['守り','静寂']` ⇒ `history_theme=守り`,
   `history_theme_secondary=静寂`, `shrine_context_need="気持ちを落ち着け、今の状態を整理したい"` ⇒
   user-facing copy asserting anxiety the user denied. **5-layer cascade
   from one keyword on a negated span.**
2. **`state` declaration-order primary → wrong emotion/direction.** A query
   hitting `uncertain` + `tired` yields `primary_state=tired` (declaration
   order) ⇒ `direction=rest` even when indecision is the point.
3. **topic → `constraint`.** Career-F / Family-A / Family-D / Travel-A: a
   relationship *topic* ⇒ `constraint.relationship` ⇒
   `shrine_context_need="人との関係や距離感を整理したい"` inserted into the
   explanation even for a travel-safety prayer (Travel-A).
4. **`emotion` adds nothing but a failure surface.** Because `emotion` is a
   pure re-view of `state`, it cannot correct a `state` error and cannot
   add signal — it only widens the blast radius of a `state` false positive
   into a second field name consumed by reason-v4.

---

## 13. Relevant Canonical 34-Case Traces

The 34 cases are the PR #2646/#2649 canonical set — **not recomputed here**;
the columns below are the actual `interpret_consultation` output for the five
target fields (Appendix A probe). Cases where **all five fields are empty**
(the field simply does not activate) are summarised, not tabled.

**All five fields empty** (13 cases): Career-A, Career-C, Career-E, Love-A,
Love-B, Love-D (state/emotion/direction/action/constraint all `None`/`[]`;
`outcome_hint`/`need_profile` may still fire), Money-A, Study-A, Health-A,
Protect-A, Focus-A, Neg-2, Theme-1.

**Cases that activate ≥1 target field:**

| case | `state.primary` | `emotion.tone/intensity` | `direction.dir` | `action.intent` | `constraint.primary` | note |
|---|---|---|---|---|---|---|
| Career-B | anxious (`怖`) | anxious / medium | stabilize | – | – | hesitation → asserted anxiety |
| Career-D | – | unknown | – | – | – | (only `outcome=calm`) — "落ち着かない" state uncaptured |
| Career-F | – | unknown | – | – | **relationship** (`人間関係`,`職場`) | topic → constraint |
| Love-C | uncertain (`迷`) | uncertain / medium | review | – | – | indecision = fair |
| Love-E | – | unknown | – | **reflect** (`整理`) | – | consultation "closure" mislabelled as product action |
| Family-A | – | unknown | – | – | **relationship** (`家族`) | topic → constraint |
| Family-B | anxious (`心配`) | anxious / medium | stabilize | – | – | caregiver worry → asserted anxiety |
| Family-C | anxious (`不安`) | anxious / medium | stabilize | – | – | prenatal anxiety — arguably fair, still an assertion |
| Family-D | uncertain (`悩`) | uncertain / medium | review | – | **relationship** (`家族`) | topic → constraint; `悩` → "uncertain" (distress≈indecision) |
| MR-A | – | unknown | – | – | – | flagship "restless" → **no state**; only `outcome=calm` |
| MR-B | tired (`疲れ`) | tired / medium | rest | – | **energy** (`疲れ`) | state token double-counted as constraint |
| MR-C | tired (`休み`) | tired / medium | rest | – | **energy** (`休みたい`) | intention token → state + constraint |
| MR-D | anxious (`不安`) | anxious / medium | stabilize | – | – | anxiety asserted; forward-intent (`前に進`) unseen by these 5 |
| Neg-1 | – | unknown | – | – | – | negation invisible to all 5 |
| Neg-3 | **anxious (negated 不安)** + sec `uncertain` | anxious / medium | stabilize | – | – | **negation false positive + cascade** |
| Neg-4 | – | unknown | – | – | – | de-emphasis invisible to all 5 |
| Neg-5 | **tired (de-emphasised 休み)** + sec `ready_to_change` | tired / medium | rest | – | **energy** (`休みたい`) | contrast false positive |
| Theme-2 | tired (`疲れ`,`休み`) | tired / medium | rest | – | **energy** (`疲れ`,`休みたい`) | double-count |
| Theme-3 | uncertain (`悩`) | uncertain / medium | review | – | – | `悩んでいます` → "uncertain" |
| Travel-A | – | unknown | – | – | **relationship** (`家族`) | trip modifier → constraint |
| Courage-A | – | unknown | – | – | – | (only `outcome=move_forward`) |

Observations: `state_profile` fires on 9/34; of those, **3 are outright
false framings** (Career-B hesitation, Family-B caregiver worry, and the
negation/contrast cases Neg-3, Neg-5). `emotion_profile` adds nothing beyond
`state`. `direction_profile` fires iff `state` fires (9/34) and always as a
`state` derivation. `action_intent` fires on 1/34 (Love-E, and as a
mislabel). `constraint_profile` fires on ~8/34 and **every canonical-case
firing is a topic/state conflation**.

---

## 14. Field-Specific Probes

The 34 canonical cases barely exercise `action_intent` (1 hit) and never
exercise a *genuine explicit* `constraint`. **8 `FIELD_SPECIFIC_PROBE`
inputs** were added (Appendix A) and are **kept out of the 34-case
denominator**:

| probe | input | result | what it demonstrates |
|---|---|---|---|
| `PROBE-C1` | 時間があまりない | `constraint = None` | genuine time constraint **missed** (exact-substring gap) |
| `PROBE-C2` | 遠くまでは行けない | `constraint = None` | distance constraint has **no category** |
| `PROBE-C3` | 予算をかけたくない | `constraint = None` | budget constraint **missed** |
| `PROBE-C4` | 体力的に長時間は難しい | `constraint = energy` (`体力`) | a genuine physical-availability constraint — the one that lands, via `体力` |
| `PROBE-A1` | 近くの神社に行きたい | `action_intent = visit` | `visit` — but any query naming `神社` triggers it |
| `PROBE-A2` | この相談を記録しておきたい | `action_intent = save` | genuine product action `save` |
| `PROBE-D1` | 停滞していて動けない | `state = stuck`; `direction = reset`; `themes=[再出発,静寂]` | the `stuck` bucket + its state→direction derivation |
| `PROBE-M1` | お金について相談したい | `constraint = None`; `translate.shrine_context_need = 生活や収入の土台を整えたい` | a money *topic* does not (here) fire `constraint`, but `translate_meaning` still injects a money "shrine_context_need" from `need_profile` |

---

## 15. Semantic Core Disposition Matrix

Under D1 = `NORMALIZE_MODEL`, for each field's **future disposition** (not
implemented here). `CANONICAL` / `CANONICAL_AFTER_REDESIGN` / `DERIVED_VIEW` /
`ACTION_LAYER` / `COMPASS_LAYER` / `EXPLANATION_ONLY` / `SHADOW_ONLY` /
`DEPRECATE_CANDIDATE` / `INSUFFICIENT_EVIDENCE`.

| field | disposition | maps to D1 dimension(s) | evidence |
|---|---|---|---|
| `state_profile` | **`CANONICAL_AFTER_REDESIGN`** | `STATE` (+ `POLARITY`) | §7 — the *concept* (a wording-grounded "expressed state") belongs in the core; the current field's naming, negation-sensitivity, arbitrary primary, and coverage gaps disqualify it as-is |
| `emotion_profile` | **`DERIVED_VIEW`** or **`DEPRECATE_CANDIDATE`** | (view of `STATE`) | §8 — 100 % derived from `state_profile`; independent value = none; keep only as a computed `expressed_intensity` view, or drop |
| `direction_profile` | **`DERIVED_VIEW`** (Concierge) / **`EXPLANATION_ONLY`** | (projection of `STATE`/`INTENTION` into `history_theme`) | §9 — no new meaning; its one artefact (history_theme) is a translation concern; **rename required** (collides with the geographic frontend `direction_profile`) |
| `action_intent` | **split:** `INSUFFICIENT_EVIDENCE` for the semantic slice → possibly `CANONICAL_AFTER_REDESIGN` as `INTENTION`; **`ACTION_LAYER`** for `visit`/`save` | `INTENTION` (only the `reflect`/organise sense) ; `OTHER` (visit/save) | §10 — mostly product/visit actions; the `整理`→`reflect` leak is the only consultation-semantic content |
| `constraint_profile` | **`CANONICAL_AFTER_REDESIGN`** as an explicit-only `CONSTRAINT` dimension, consumed by **`ACTION_LAYER`** / practical filtering, **not** by routing | `CONSTRAINT` | §11 — a real dimension exists (explicit practical limits), but the current field is HIGH domain-conflated and under-covers genuine constraints |

**Do not copy the current `InterpretationProfile` into the normalized
model.** Two of the five fields (`emotion_profile`, `direction_profile`) are
derivations, not signals; two (`action_intent`, `constraint_profile`) mix
layers; one (`state_profile`) needs a safety-grounded redefinition before it
can be canonical.

---

## 16. Need Routing Eligibility Matrix (D2 input)

**Semantic Core membership does NOT imply Need routing** (§14 of the task,
§18 of the PR #2647 packet). A signal may be valid core meaning and still be
`DO_NOT_ROUTE` because it is useful only for explanation / action /
personalization / Compass / observability.

| field | routing status | why |
|---|---|---|
| `state_profile` | **`DO_NOT_ROUTE`** | negation-sensitive (E = YES); no approved `NEED_TO_GORIYAKU_IDS` mapping for a "state" input; routing "the user is anxious" → a GoriyakuTag is a psychological assertion feeding recommendation (§17). `SEMANTIC_ROUTING_PLAUSIBLE` for `mental`/`rest`, `EVIDENCE_ROUTING_NOT_APPROVED`. |
| `emotion_profile` | **`DO_NOT_ROUTE`** | a derived relabel of `state_profile`; routing it is strictly worse than routing the source, which is itself `DO_NOT_ROUTE`. |
| `direction_profile` | **`DO_NOT_ROUTE`** | state-derived; inherits E/F sensitivity; its `history_theme` output is a ranking-*boost* routing key via `consultation_axis`, not a need_tag / GID selector, and even that path is shrine-column-driven today. |
| `action_intent` | **`DO_NOT_ROUTE`** | `visit`/`save` are UX actions with no Evidence meaning; the `reflect`/organise sense is an explanation/action concern. |
| `constraint_profile` | **`DO_NOT_ROUTE`** | a constraint limits *how* to act, not *what* the consultation is about; HIGH domain-conflation means routing would treat topics/states as constraints. Post-redesign it is a `PRACTICAL_FILTER`, applied *after* routing, never a routing input. |

**D2 evidence impact.** None of the five audited fields is a credible
`need_tag` / Evidence routing input; each is `DO_NOT_ROUTE`. This is
**consistent with — and reinforces —** the Mother Ship working direction
`D2 NEED_TAG_ROLE = EVIDENCE_ROUTING_LAYER` (need_tag as a validated routing
key fed by a *separate, deliberately chosen* signal set, with Semantic Core
membership decoupled from routing). No audited evidence argues that
`need_tag` should carry state / emotion / direction / action / constraint
meaning, and none argues these fields should become routing producers.

```text
D2_EVIDENCE_IMPACT = SUPPORTS
   (evidence supports keeping need_tag as a routing layer and keeping these five signals out of routing;
    it does not weaken or contradict the working direction; D2 is NOT finalized here)
```

---

## 17. Concierge / Compass Boundary

| concern | finding |
|---|---|
| Do the five fields exist for Compass? | **No.** `get_compass_recommendations` calls `interpret_consultation(query="")` → `state_profile` / `emotion_profile` / `direction_profile` / `action_intent` / `constraint_profile` are **all empty** for every Compass request. |
| Is there reusable Compass value in `direction_profile`? | **No.** The Compass concept is *geographic* lucky-direction from birthdate + target date; the Concierge `direction_profile` is a *state-derived motivational stance*. Reuse would require a different producer and a different input; the two only share a (colliding) name. |
| Would redesigning these Concierge fields change Compass behaviour? | **No**, provided the shared surfaces are respected: `interpret_consultation`'s **schema keys** are shared (Compass passes the result into `build_chat_candidates` / `build_chat_recommendations`), so **key renames** would touch Compass's reason-v4 path; **values** do not (Compass's are empty). `NEED_TAGS` / `NEED_TO_GORIYAKU_IDS` / ranking / candidate generation are untouched by any of these five fields. |
| Boundary statement | These five fields are **Concierge-only** in practice. A richer Concierge state/intention/constraint model does **not** require any Compass change; Compass and Concierge product responsibilities are not merged. |

---

## 18. Evidence Boundary

Preserved principle: **semantic meaning ≠ recommendation-evidence
eligibility.** This audit:

- proposes **no** new `GoriyakuTag` mapping from state / emotion / direction /
  action / constraint;
- creates **no** tags; alters **no** `NEED_TO_GORIYAKU_IDS` entry;
- treats semantic plausibility as *not* Evidence approval.

For each field, the two are kept explicitly separate:

| field | `SEMANTIC_ROUTING_PLAUSIBLE` | `EVIDENCE_ROUTING_NOT_APPROVED` |
|---|---|---|
| `state_profile` | plausible for `mental` / `rest` | **not approved** — no reviewed mapping; negation risk |
| `emotion_profile` | (same as state, derived) | **not approved** |
| `direction_profile` | plausible via `history_theme` framing | **not approved** as a GID selector (only an axis-gated ranking boost exists, shrine-column-driven) |
| `action_intent` | not plausible (product/visit actions) | **not approved** |
| `constraint_profile` | not plausible (limits action, not meaning) | **not approved** |

GoriyakuTag is never inferred from deity / history / tradition; the reviewed
`goriyaku_tags` contract is unchanged.

---

## 19. Psychological / Religious Safety Boundary

Classification of what each field's current output *claims* vs what the user
*expressed*: `USER_EXPLICIT` / `LINGUISTICALLY_INFERRED` / `SYSTEM_INFERRED` /
`UNSUPPORTED`.

| field / value | current claim | grounding | risk |
|---|---|---|---|
| `state_profile.primary_state = "anxious"` | "the user is anxious" | `SYSTEM_INFERRED` from one substring; `UNSUPPORTED` when the span is negated (Neg-3) or ordinary (Family-B `心配`) | **HIGH** — asserts a mental condition |
| `emotion_profile.tone = "anxious"` | "the user's emotional tone is anxious" | `SYSTEM_INFERRED` (re-label of state) / `UNSUPPORTED` | **HIGH** — asserts emotion |
| `emotion_profile.intensity = "medium"` | "emotional intensity is medium" | `SYSTEM_INFERRED` — actually "2 state keywords matched" | **MEDIUM** — overstates precision |
| `direction_profile.direction = "stabilize"` | "the user should stabilise" | `SYSTEM_INFERRED` from state | **MEDIUM** — prescriptive stance from a shaky state read |
| `action_intent.intent = "visit"` | "the user intends to visit" | `LINGUISTICALLY_INFERRED` (usually a wording match) | **LOW** |
| `constraint_profile.primary_constraint = "energy"` | "energy is a practical constraint" | `SYSTEM_INFERRED` from a fatigue/topic token | **MEDIUM** |
| downstream reason-v4 copy ("不安や心配を中心に、要素があります") | states the user's condition to the user | inherits the above | **HIGH** when derived from negated/ordinary wording |

**Safety requirements for any future Stable Contract in this area** (not
implemented): describe *expression*, never *condition*
("『落ち着かない』という言葉が使われています", not "あなたは不安定な状態です");
carry `polarity` so negated spans cannot assert; never claim a shrine is
"spiritually necessary" or a divine benefit is "certain"; keep
`SYSTEM_INFERRED` values out of user-facing assertions unless
`USER_EXPLICIT` or clearly hedged. This is architecture/safety
classification, not medical diagnosis.

---

## 20. Stable Contract Readiness

| field | READY? | what must be true first |
|---|---|---|
| `state_profile` | **`REQUIRES_REDESIGN`** | precise "expressed-state" definition (not "psychological state"); `polarity` per value + source span; salience-based (not declaration-order) or no forced primary; coverage gaps closed (unsettled / restless / loss-of-confidence / grief); negation + clause behaviour specified and tested (false-positive corpus); deterministic shape; named producer owner; safety-reworded downstream copy; versioning if exposed; downstream consumer ownership (reason-v4, Score v3) documented |
| `emotion_profile` | **`NOT_SUITABLE` as "emotion"** | either deprecate (redundant view of `state`), or redefine as `expressed_intensity` = honest token count/strength with its own affect-language evidence, its own tests, and non-diagnostic wording |
| `direction_profile` | **`REQUIRES_REDESIGN` + rename** | rename to avoid the geographic `direction_profile` collision; define as a *derived view* (explicit `source` provenance) or fold into the `history_theme` translation layer; do not present it as independent meaning; if kept, negation/clause behaviour inherited from `state` must be bounded |
| `action_intent` | **`REQUIRES_REDESIGN` (split)** | separate `PRODUCT_ACTION` / `VISIT_ACTION` (owned by the action/UX layer) from any `SEMANTIC_INTENTION` sense; remove topic tokens (`神社`) from the action vocabulary; the visit/save half needs a stable action contract, the semantic half needs to join the `intention` dimension design |
| `constraint_profile` | **`REQUIRES_REDESIGN`** | restrict to explicitly stated practical limits (time / distance / budget / physical availability); exclude every token that is also a topic or state token; clause-scope the match; define the target role as `PRACTICAL_FILTER` / `ACTION_MEANING`, applied after routing; add coverage for the currently-missed explicit constraints; false-positive tests against topic/state inputs |

**Nothing is promoted in this PR.**

---

## 21. Summary Matrices

### 21.1 Field overview

| field | current role | inference risk | semantic-core disposition | need-routing status | Compass | Stable Contract |
|---|---|---|---|---|---|---|
| `state_profile` | linguistic signal presented as psychological state; MIXED (shadow-rank + display) | STRONG / **HIGH** psych-assertion; E = YES; D = HIGH | `CANONICAL_AFTER_REDESIGN` (`STATE` + `POLARITY`) | `DO_NOT_ROUTE` | none (empty for Compass) | `REQUIRES_REDESIGN` |
| `emotion_profile` | 100 % derived re-view of `state_profile`; display only | UNSUPPORTED (relabel); HIGH (inherited) | `DERIVED_VIEW` / `DEPRECATE_CANDIDATE` | `DO_NOT_ROUTE` | none | `NOT_SUITABLE` (as "emotion") |
| `direction_profile` | state-derived motivational stance → `history_theme`; display + shadow | STRONG (state→stance); MEDIUM | `DERIVED_VIEW` / `EXPLANATION_ONLY` | `DO_NOT_ROUTE` | none (name collides w/ geographic) | `REQUIRES_REDESIGN` + rename |
| `action_intent` | MIXED product/visit action + a semantic-intention leak; display | LIGHT (visit/save) / STRONG (`整理`→reflect); LOW psych | split: `INTENTION` slice / `ACTION_LAYER` (visit/save) | `DO_NOT_ROUTE` | low | `REQUIRES_REDESIGN` (split) |
| `constraint_profile` | mostly topic/state conflation; a real "explicit constraint" dimension underneath; display | STRONG (topic→constraint); D = HIGH | `CANONICAL_AFTER_REDESIGN` (`CONSTRAINT`, explicit-only) → `ACTION_LAYER` consumer | `DO_NOT_ROUTE` | low | `REQUIRES_REDESIGN` |

### 21.2 Value-by-consumer

| field | semantic meaning | evidence routing | explanation | action / UX | Compass |
|---|---|---|---|---|---|
| `state_profile` | MEDIUM (after redesign) | NONE | MEDIUM (needs safety rewording) | LOW | NONE |
| `emotion_profile` | LOW | NONE | LOW | LOW | NONE |
| `direction_profile` | LOW | LOW (axis-gated boost only) | MEDIUM (history_theme) | MEDIUM | NONE |
| `action_intent` | LOW (only the reflect sense) | NONE | MEDIUM | **HIGH** | LOW |
| `constraint_profile` | LOW | NONE | MEDIUM | **HIGH** (practical filter) | LOW |

### 21.3 Cross-field collision (condensed)

`emotion_profile` = **DUPLICATED/DERIVED** from `state_profile`.
`direction_profile` = **DERIVED** from `state_profile`.
`constraint_profile.energy` = **CONFLATED** with `state_profile` fatigue
tokens. `constraint_profile.relationship` / `action_intent.visit` = topic →
field conflation (same class). `action_intent` is otherwise `INDEPENDENT`.
Cascade: `state → emotion → direction → history_theme → user-facing Reason
copy` (5 layers from one keyword; fires on negated spans — Neg-3, Neg-5).

---

## 22. Unresolved Questions (for Mother Ship / future design)

1. Should `emotion_profile` be **deprecated outright** (it is a pure view of
   `state_profile`) or kept as an explicitly-derived `expressed_intensity`?
2. Should `state_profile`'s value set stay at the current 5 buckets, or does
   the redesign need coverage for *unsettled / restless / loss-of-confidence
   / grief / hesitation* (all currently uncaptured)?
3. Where does the "expressed-state, with polarity" signal get **produced** —
   inside the normalized Semantic Core producer, or as a separate
   linguistic pre-pass feeding it? (Interacts with D5 `NEGATION_MODEL`.)
4. `direction_profile`: fold into the `history_theme` **translation layer**
   entirely, or keep a named derived core view? And what is its new name?
5. `action_intent`: is the `visit` / `save` half owned by an Action/UX
   contract that is out of Semantic Core scope, and does the `reflect` half
   merge into the `intention` dimension or stay separate as an
   "explanation-question seed"?
6. `constraint_profile`: is "explicit practical constraint" a Semantic Core
   dimension at all, or purely an **Action/Personal-Meaning** concern
   (D1's `constraints[]` slot vs an action-layer filter)?
7. Do any of these five ever need to appear in `PremiumMeaningContext.interpretedContext`
   once a Source of Truth is confirmed, and if so which — with what safety
   wording?
8. Does the Score v3 `state_match_score` weight (0.45) presuppose a
   `state_profile` quality bar that the redesign must meet **before** any
   `SCORE_V3_MODE=active` decision?

---

## 23. Mother Ship Decision Packet

Neutral. **No value is chosen.** Candidates per field, with evidence /
benefits / costs / risks / affected consumers / D2 implication.

### `STATE_PROFILE_ROLE` candidates

| candidate | evidence | benefits | costs | risks | affected consumers | D2 implication |
|---|---|---|---|---|---|---|
| `CANONICAL_AFTER_REDESIGN` (as `expressed_state` + polarity) | §7, §12, §19 | a real core dimension; safety-grounded; fixes negation cascade | redesign effort; new producer + tests; downstream copy rework | if under-scoped, still asserts states | reason-v4, Score v3, translate_meaning | none (still `DO_NOT_ROUTE`) |
| `EXPLANATION_ONLY` | §5, §7.1 | smallest change; keeps it out of the core | leaves the psych-assertion risk in the explanation surface | negated-span copy persists | reason-v4 detail | none |
| `SHADOW_ONLY` (revert to purely observational, no user-facing copy) | §5, §16 | removes the safety surface immediately (by policy, not code, in this audit) | loses the "state" explanation value | — | reason-v4 detail | none |
| `DEPRECATE_CANDIDATE` | §7.3 gaps | removes a low-quality signal | loses potential future value | — | reason-v4, Score v3 | none |

### `EMOTION_PROFILE_ROLE` candidates

| candidate | evidence | benefits | costs | risks | affected consumers | D2 |
|---|---|---|---|---|---|---|
| `DEPRECATE_CANDIDATE` | §8 (100 % derived; `query` unused) | removes a redundant failure surface | reason-v4 loses the intensity adjective | none | reason-v4 `_build_interpretation` | none |
| `DERIVED_VIEW` (rename → `expressed_intensity`, honest token-count) | §8, §21 | keeps the one useful bit without the "emotion" over-claim | still needs non-diagnostic wording | mislabelled precision if not reworded | reason-v4 | none |
| `CANONICAL_AFTER_REDESIGN` (independent affective-language signal) | §8.2 | genuine independent value | needs a real affect lexicon + evidence + tests (large) | scope creep into diagnosis | reason-v4, Score v3 | none |

### `DIRECTION_PROFILE_ROLE` candidates

| candidate | evidence | benefits | costs | risks | affected consumers | D2 |
|---|---|---|---|---|---|---|
| `DERIVED_VIEW` (rename; explicit `source` provenance) | §9 | keeps history_theme routing without claiming new meaning | rename touches shared schema keys (Compass reason-v4 path) | inherits `state` E/F sensitivity | translate_meaning, reason-v4, Score v3 | none |
| `EXPLANATION_ONLY` / fold into translation layer | §9.2 | one fewer top-level field; clearer boundary | migration of `translate_meaning` inputs | — | translate_meaning | none |
| `DEPRECATE_CANDIDATE` | §9 (no independent value) | simplifies | `history_theme` must be sourced from `state`/`need`/`decision` directly | — | translate_meaning | none |
| `COMPASS_LAYER` | §9.3, §17 | — | **not supported** — different concept, different producer, empty for Compass | would merge unrelated concepts | — | none |

### `ACTION_INTENT_ROLE` candidates

| candidate | evidence | benefits | costs | risks | affected consumers | D2 |
|---|---|---|---|---|---|---|
| split: `ACTION_LAYER` (visit/save) + `INTENTION` slice (reflect/organise) | §10 | correct layering; removes topic coupling (`神社`) | two contracts instead of one; wiring | boundary disputes with the `intention` dimension design | reason-v4 `_build_action`, action_suggestion_v4, translate_meaning | none |
| `ACTION_LAYER` only (drop the semantic leak) | §10.2 | simplest clean split | loses the `整理`→closure signal from this field (may exist elsewhere via `outcome_hint`) | — | as above | none |
| `EXPLANATION_ONLY` | §5 | minimal | keeps the mislabel | — | reason-v4 detail | none |
| `DEPRECATE_CANDIDATE` | §13 (1/34 hit rate) | removes a barely-used field | loses visit/save UX signal | — | action_suggestion_v4 | none |

### `CONSTRAINT_PROFILE_ROLE` candidates

| candidate | evidence | benefits | costs | risks | affected consumers | D2 |
|---|---|---|---|---|---|---|
| `CANONICAL_AFTER_REDESIGN` — explicit-only `CONSTRAINT`, consumed by `ACTION_LAYER` / practical filter | §11 | a genuine dimension; supports Personal/Action Meaning | redesign; new vocabulary; clause scoping; tests | if not strict, topic→constraint conflation returns | translate_meaning `shrine_context_need`, action_suggestion_v4, reason-v4 | none (applied after routing, never as a routing input) |
| `ACTION_MEANING` / `PRACTICAL_FILTER` only (not in Semantic Core) | §11.3 | keeps the core small; puts constraints where they act | needs an action-layer home | — | action_suggestion_v4 | none |
| `EXPLANATION_CONTEXT` only | §5 | minimal | leaves the conflation in the explanation | Travel-A-type text bleed persists | reason-v4, translate_meaning | none |
| `DEPRECATE_CANDIDATE` | §11.2 (every canonical firing is a conflation) | removes a mostly-wrong signal | loses the genuine explicit-constraint capability entirely | — | translate_meaning, action_suggestion_v4 | none |

### D2 evidence impact

```text
D2_EVIDENCE_IMPACT = SUPPORTS
```

The audit finds **all five fields `DO_NOT_ROUTE`** and finds **no evidence**
that `need_tag` should carry state / emotion / direction / action /
constraint meaning. This is consistent with, and reinforces, the working
direction `D2 NEED_TAG_ROLE = EVIDENCE_ROUTING_LAYER` (need_tag as a
validated routing key; Semantic Core membership decoupled from routing
eligibility). **D2 `NEED_TAG_ROLE` is not set by this audit** — it remains a
Mother Ship decision.

---

## Appendix A — Method / Reproducibility

- Code read at `origin/develop` `a6543ec3d27cc4d33402779aa43b9cc694b052b4`
  (PR #2649 merge). Consumers traced by `grep` across `backend/temples/**`
  and `apps/web/src/**` (non-test); `_debug` strip confirmed at
  `api_views_concierge.py:340` (`data.pop("_debug", None)`); `SCORE_V3_MODE`
  default `"shadow"` confirmed in `concierge_chat_ranking.resolve_score_v3_mode_detail`.
- **Pure-function probe** (no DB, no behaviour change; repo venv
  `/Users/morietsu/Developer/jinja_app/.venv`, Django 5.2.16,
  `USE_GIS=0 USE_SQLITE=1`): `interpret_consultation()` +
  `translate_meaning()` run on the 34 canonical cases (from
  `docs/audit/recommendation-nuance-quality-audit.md` §15) plus **8
  `FIELD_SPECIFIC_PROBE`** inputs (`PROBE-C1..C4`, `PROBE-A1/A2`, `PROBE-D1`,
  `PROBE-M1`), recording `state_profile`, `emotion_profile`,
  `direction_profile`, `action_intent`, `constraint_profile`, `outcome_hint`
  and the `translate_meaning` output for each. All §7–§14 examples are
  actual probe output. Probes are **excluded** from the 34-case denominator.
- Existing tests inspected (not run against a DB — the local `test_jinja_db`
  is in a broken state, `must be owner of database test_jinja_db`; per the
  task's docs-only rule shared infra was not repaired; CI covers the
  suites): `test_consultation_interpreter.py` (6 tests, none for negation /
  clause / false-positive / primary ordering), `test_meaning_translation.py`,
  `test_recommendation_reason_v4.py`, `test_recommendation_score_components.py`,
  `test_action_suggestion_builder.py`.
- `git diff --check`: clean. Exactly one repository file changed
  (`docs/audit/interpretation-profile-field-redesign-audit.md`). The
  #2646 / #2647 / #2649 canonical audits are untouched.
- No runtime / test / frontend / contract change; no Production or
  Spreadsheet access; no migration.
