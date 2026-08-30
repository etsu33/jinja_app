# Consultation Understanding Architecture Audit

> **Status: ARCHITECTURE AUDIT — READ-ONLY. No runtime, interpreter, mapping,
> taxonomy, scoring, ranking, Reason, Lead, schema, migration, Production,
> frontend, or test change is made or proposed for implementation.** Section 20
> lists the decisions Mother Ship must make; no value is selected.
>
> Audit base `origin/develop` = `334bd87650881207345b983c826dde43d8867bd3`
> (PR #2646 merge commit). Branch `audit/consultation-understanding-architecture`.
>
> Builds on the merged findings of `docs/audit/recommendation-nuance-quality-audit.md`
> (PR #2646). Where that audit measured *nuance loss*, this audit answers the
> *architecture* question: can the existing semantic structures be reused and
> promoted, or does the semantic model need restructuring first.

---

## 1. Executive Summary

**Primary question.** Can richer consultation understanding be built by
promoting/reconnecting the structures that already exist, or are their
responsibilities too fragmented / lossy / inconsistent to safely extend?

**Evidence-based answer: reuse is feasible for the *carriers*, but the
*semantic model* needs a normalization step first.** Specifically:

1. **The plumbing to make richer signals load-bearing already exists** and is
   partly connected. `interpret_consultation()` produces a stable 9-key
   `interpretation_profile` (STATE / DIRECTION / EMOTION / ACTION / DECISION /
   CONSTRAINT / OUTCOME / NEED). It flows into `translate_meaning()` →
   `recommendation_reason_v4` → `rec["recommendation_reason_v4_detail"]`,
   which **is returned on the public API response** (display-only), and into
   the Score v3 shadow components. `recommendation_reason_v4._build_interpretation`
   **already turns `state_profile` / `decision_context` / `constraint_profile`
   / `outcome_hint` into user-facing explanation copy.** So "no consumer
   exists" is false.

2. **But the profile is not load-bearing for what decides the recommendation.**
   It does **not** touch candidate generation, `score_need`, the sort order
   (`_sort_chat_recommendations`), the legacy `rec["reason"]` string, or the
   Lead. Those run entirely on `need_tags` (from `extract_need_tags`) +
   `consultation_axis` + user-selected `goriyaku_tag_ids`. Score v3 (the one
   scorer that consumes the profile) is **shadow by default**
   (`SCORE_V3_MODE` unset → `"shadow"`); a single env var flips it to
   `"active"` and makes the profile drive ranking with pre-tuned weights
   (`state 0.45`, `history 0.10`, …).

3. **Three parallel need-extractors exist with drifted vocabularies.**
   `domain/need_tags.KEYWORDS`+`REGEX` (runtime, feeds ranking),
   `consultation_interpreter.NEED_KEYWORDS` (feeds `interpretation_profile.need_profile`
   — has extra tokens the runtime lacks: `前に進`, `悩み`, `迷い`, `考えすぎ`,
   `生活費`, `一人`, `学び`, `スキル`), and `concierge_chat_need.NEED_SYNONYMS`
   (6-need fallback). A promoted profile would carry a *different* need list
   than the ranker uses.

4. **`need_tag` is semantically overloaded.** The same 15-value list is asked
   to carry Topic (`career`, `money`), Intention (`courage`, `rest`, `focus`),
   and State (`mental`). It has no slot for polarity (negation), decision
   conflict, or "primary vs secondary with a reason". These are
   **model-capacity limits**, not vocabulary or mapping bugs.

5. **Negation / polarity has nowhere to live.** No field in
   `interpretation_profile`, no `reason_fact` type, no `need_tag` convention
   represents "asserted vs negated vs de-emphasised vs contrasted". This is
   `NOT_REPRESENTABLE` without a new field.

6. **`consultation_axis` is a derived single-value framing + ranking-routing
   layer** that partially duplicates `need_tag` (both derive from the same
   tokens) and adds exactly one thing `need_tag` cannot: the
   `history_theme_candidate_boost` routing key. It is a
   `SINGLE_VALUE_BOTTLENECK` for inputs that legitimately span two axes.

7. **Concierge / Compass share the semantic *core*** (`need_tag` →
   `NEED_TO_GORIYAKU_IDS` → `_attach_breakdown` → `_sort` →
   `build_recommendation_reason` → `recommendation_reason_v4`). The
   **free-text interpreter is Concierge-only** (Compass has no query;
   `purpose` is a single `need_tag`). So free-text / negation / clause work is
   Compass-safe; changes to `NEED_TAGS`, `NEED_TO_GORIYAKU_IDS`, ranking,
   Reason, `NEED_TAG_TO_CONSULTATION_AXIS`, or the `interpret_consultation`
   schema are **not** Compass-safe.

**Verdict shape (Section 21):** `EXISTING_MODEL_REUSE_STATUS =
REUSE_WITH_NORMALIZATION`; `INTERPRETATION_PROFILE_STATUS =
PROMOTABLE_AFTER_NORMALIZATION`;
`NEED_TAG_CAPACITY_STATUS = SEMANTIC_OVERLOAD, MODEL_CAPACITY_LIMIT`;
`NEGATION_CAPACITY_STATUS = NOT_REPRESENTABLE`; `BLOCKERS = 0` (nothing
blocks a Mother Ship decision; the work required is scoped, not open-ended).

---

## 2. Scope

Audited: the semantic-understanding path from consultation input to
recommendation and explanation — `query`/`free_text`, `extract_need_tags`,
`NEED_PRIORITY`, `KEYWORDS`, `REGEX`, `resolve_need_payload`,
`consultation_axis`, `interpretation_profile` and all eight sub-profiles,
`NEED_TO_GORIYAKU_IDS`, `build_chat_candidates`, `_attach_breakdown` /
`score_need` / C1, `_sort_chat_recommendations`, `build_recommendation_reason`
/ `_build_need_lead` / `reason_facts` / `_resolve_primary_reason`,
`recommendation_reason_v4`, `translate_meaning`, Score v2 / Score v3, and the
Compass orchestrator.

Not in scope: any change; the LLM route (`CONCIERGE_USE_LLM` default `False`);
frontend rendering choices between `rec["reason"]` and
`recommendation_reason_v4_detail`; astrology/direction/visit-style except
where they gate a `score_need = 0` result.

---

## 3. Current Runtime Path (load-bearing)

```text
POST concierge/chat  →  ConciergeChatView.post                       api_views_concierge.py
  normalize_concierge_request(data)                                  concierge_input_contract.py
    → query (raw free text; `message` folded), goriyaku_tag_ids,
      extra_condition, visit_preferences, birthdate
      ── NO structured "consultation theme" field ──
  interpret_consultation(query, need_tags=[])                        consultation_interpreter.py
    → interpretation_profile   ── NOT used by candidate gen / score_need /
       sort order / rec["reason"] / Lead. Used by: translate_meaning (below),
       reason_v4 detail (below), Score v3 shadow (below), _debug.
  _build_chat_candidates_pipeline → build_chat_candidates(           concierge_chat_candidates.py
       goriyaku_tag_ids = data.get("goriyaku_tag_ids")  ← USER-PICKED ONLY
       , interpretation_profile)
     Shrine.objects.all()
       .filter(goriyaku_tags__id__in=goriyaku_tag_ids)  IFF user picked tags
       exclude_qa_fixture_shrines()
       .filter(lat/lng not null).exclude(address="")
       order_by(-popular_score, id)[: max(limit*5, 50)]
     per candidate: translate_meaning(interpretation_profile)
       → translation_result → compose_shrine_meaning_payload
       → candidate["history_context"]        (display field; not ranked)
     ── Need→GoriyakuTag mapping NOT applied at candidate generation ──
  build_chat_recommendations(query, candidates, need_tags=None, …)   concierge_chat.py
    resolve_need_payload(query, need_tags or [])                     concierge_chat_need.py
      need_tags == [] → extract_need_tags(query)                     domain/need_tags.py
        KEYWORDS substring ∪ REGEX search → hits
        NEED_PRIORITY pick, max_tags=3          →  need_tags  (≤3)
    resolve_consultation_axis(query, need_tags, llm_axis=None)       domain/consultation_axis.py
      normalize(llm_axis) → query keyword hits → need_tag fallback → "other"
        → consultation_axis  (single value)
    resolve_llm_route(…)   CONCIERGE_USE_LLM=False (default)         concierge_chat_llm_route.py
      → _prefilter_candidates_for_need(candidates, need_tags, axis)  concierge_chat_ranking.py
          per candidate: +2 astro-tag, +2 GID (need_tags_to_goriyaku_ids ∩
          candidate.goriyaku_tag_ids), +1 text hint (NEED_TEXT_WEIGHTS ∈
          goriyaku+description), +2 study bonus,
          + resolve_history_theme_candidate_boost(axis, candidate.history_theme)
      → _seed_recs_from_candidates(size=12) → _ensure_pool_size(20)
    _attach_chat_rec_enrichment → per rec:
      _attach_breakdown(rec, need_tags, weights, requested_goriyaku_tag_ids, axis)
        matched_by_tag / matched_by_text / matched_by_gid / matched_by_user_selected_gid
        score_need = len(union of the first three)               ← public contract
        score_need_rank_weighted = astro*2 + C1Max(gid=2.0, text×1.2)
                                    + study_bonus + history_theme_candidate_boost
        reason_facts + _primary_reason_label  (_resolve_primary_reason,
          PRIMARY_REASON_PRIORITY)
      rec["reason"] = build_recommendation_reason(rec, need_tags, need_gid_label_by_id)
        → _resolve_matched_lead_evidence → _build_need_reason_text / _build_need_lead
      _attach_reason_source(rec)
    attach_explanation_payload(recs)
    _sort_chat_recommendations(recs, sort_tags, score_v3_mode)
      score_v3_mode == "shadow" (default) → sort by rec["_score_total"]  (v2)
        then distance, then name, then _diversify_by_need(limit=3)
      score_v3_mode == "active" (env) → sort by breakdown.score_v3        (v3)
    _attach_rank_comparison → recommendations[]
    _attach_recommendation_reason_quality(recs, interpretation_profile)   ← reaches response
      per rec: build_recommendation_input_profile(interpretation_profile,
        translation_result, candidate_profile, score_v2_fields)
        → build_recommendation_reason_v4(...)
        → rec["recommendation_reason_v4"]         (string; on rec, NOT _debug)
        → rec["recommendation_reason_v4_detail"]  { reason_text, fact,
             interpretation, action }             (on rec, NOT _debug)
        → rec["recommendation_reason_quality"]
  _build_chat_response(recs …)                                       api_views_concierge.py
    data.pop("_debug", None)     ← strips interpretation_profile, reason_v4_preview,
                                    score_v3_shadow_observation, user_state_profile
    (rec["reason"], rec["recommendation_reason_v4"],
     rec["recommendation_reason_v4_detail"] survive → public body)
```

## 4. Current Shadow / Non-Ranking Path

```text
interpret_consultation(query)  →  interpretation_profile
  │
  ├─ translate_meaning(interpretation_profile)                       meaning_translation.py
  │   direction_profile.direction → HISTORY_THEME_BY_DIRECTION → history_theme
  │   direction_profile.themes[1] → history_theme_secondary
  │   need_profile.primary_need_tag / constraint_profile → shrine_context_need
  │   action_intent.intent / outcome_hint.primary_outcome → action_context
  │   history_theme → REFLECTION_QUESTION_BY_HISTORY_THEME → reflection_question_seed
  │   → translation_result
  │       ├─ candidate["history_context"] (display; via compose_shrine_meaning_payload)
  │       ├─ Score v3 components: calculate_meaning_match_score / calculate_history_score
  │       │    (recommendation_score_components.py — SHADOW unless SCORE_V3_MODE=active)
  │       └─ recommendation_reason_v4 (below)
  │
  ├─ build_recommendation_input_profile(interpretation_profile, translation_result,
  │     candidate_profile, score_v2_fields)                          recommendation_input_profile.py
  │   ├─ run_recommendation_algorithm_v3_shadow(...)                 recommendation_algorithm_v3.py
  │   │    → recs["_debug"]["score_v3"]  (stripped at response boundary)
  │   └─ build_recommendation_reason_v4(recommendation_input_profile, authority_context)
  │        recommendation_reason_v4._build_interpretation(interpretation_profile, meaning_translation)
  │          consumes: state_profile.primary_state, emotion_profile.intensity,
  │            decision_context.primary_decision, constraint_profile.primary_constraint,
  │            outcome_hint.primary_outcome, consultation_axis
  │          → interpretation.text ("判断に迷う様子を中心に、要素があります" …)
  │        → rec["recommendation_reason_v4_detail"].interpretation   ← REACHES RESPONSE
  │
  └─ recs["_debug"]["interpretation_profile"] / ["reason_v4_preview"] / …  ← stripped
```

**So `interpretation_profile` has three consumer tiers:**

| tier | consumers | reaches user? | affects ranking? |
|---|---|---|---|
| stripped debug | `_debug.interpretation_profile`, `_debug.reason_v4_preview`, `_debug.score_v3*`, `_debug.user_state_profile` | no (`_build_chat_response` pops `_debug`) | no |
| shadow scoring | `calculate_recommendation_score_components` via `translate_meaning` | no | **only if `SCORE_V3_MODE=active`** |
| display | `rec["recommendation_reason_v4_detail"].interpretation` / `.action`; `candidate["history_context"]` | **yes** | no |

---

## 5. AS-IS Semantic Model

```text
query (free text, Concierge only; Compass sends purpose = one need_tag)
  │
  ├─ extract_need_tags(query)                     domain/need_tags.py     [RUNTIME]
  │    KEYWORDS (15) substring  ∪  REGEX (8 families) search
  │    → hits{tag:[...]}  → NEED_PRIORITY pick  → max_tags=3
  │    → need_tags[]  (≤3, ordered)
  │        ├─ need_tags_to_goriyaku_ids(need_tags)  = ∪ NEED_TO_GORIYAKU_IDS[tag]
  │        │    → matched_by_gid  → score_need (+ C1 Max +2.0)          [RANKING]
  │        ├─ NEED_TEXT_WEIGHTS[tag] ∈ shrine(goriyaku+description)
  │        │    → matched_by_text → score_need (+ C1 Max text×1.2)      [RANKING]
  │        ├─ need_tags ∩ shrine.astro_tags → matched_by_tag (+2 flat)  [RANKING]
  │        ├─ _resolve_primary_reason → _primary_reason_label
  │        │    → build_recommendation_reason → rec["reason"], Lead     [EXPLAIN]
  │        └─ NEED_LABELS_JA[tag] → reason_fact.label_ja                 [EXPLAIN]
  │
  ├─ resolve_consultation_axis(query, need_tags)  domain/consultation_axis.py  [RUNTIME]
  │    query keyword hits (CONSULTATION_AXIS_KEYWORDS)
  │      else need_tag fallback (NEED_TAG_TO_CONSULTATION_AXIS)  else "other"
  │    → consultation_axis  (1 of 9, single value)
  │        └─ resolve_history_theme_candidate_boost(axis, shrine.history_theme)
  │             → + score_need_rank_weighted, + _prefilter score               [RANKING]
  │        └─ history_theme reason_fact emitted only when boost > 0            [EXPLAIN]
  │
  └─ interpret_consultation(query, need_tags=[])  consultation_interpreter.py  [SHADOW/DISPLAY]
       ├─ state_profile   (STATE_KEYWORDS: tired/anxious/uncertain/stuck/ready_to_change)
       │     primary_state + secondary_states[] + state_hits + confidence
       ├─ need_profile    (NEED_KEYWORDS — a SECOND, drifted 15-need table)
       │     need_tags[] (≠ extract_need_tags for shadow-only tokens) + primary_need_tag
       ├─ direction_profile  (DIRECTION_BY_STATE: primary_state → direction + themes[])
       │     themes ∈ {静寂, 守り, 再出発, 勝負, 縁, 学び, 復興}  ← history_theme namespace
       ├─ emotion_profile   (tone = primary_state; intensity from confidence)
       ├─ action_intent    (ACTION_KEYWORDS: visit/reflect/save)
       ├─ decision_context (DECISION_KEYWORDS: career/relationship/money/rest_or_action)
       ├─ constraint_profile (CONSTRAINT_KEYWORDS: time/money/energy/relationship)
       └─ outcome_hint     (OUTCOME_KEYWORDS: decide/calm/move_forward/clarify)
             │
             └─ translate_meaning() → history_theme / history_theme_secondary /
                  shrine_context_need / action_context / reflection_question_seed
                    ├─ Score v3 components (SHADOW unless SCORE_V3_MODE=active)
                    └─ recommendation_reason_v4_detail.{interpretation,action}   [EXPLAIN, reaches response]
```

---

## 6. Semantic Responsibility Matrix

Ownership classes: `SINGLE_OWNER`, `DUPLICATED`, `PARTIAL_DUPLICATION`,
`UNOWNED`, `SHADOW_ONLY` (owned but only shadow/display consumers),
`AMBIGUOUS_OWNERSHIP`.

| concept | need_tag? | consultation_axis? | interpretation_profile? | regex/keyword owner | load-bearing consumer | class |
|---|---|---|---|---|---|---|
| Topic — career | `career` | `career_change` | `need_profile`, `decision_context=career_decision` | `KEYWORDS.career` (×3 tables) | GID map, score_need, axis boost, Reason | `PARTIAL_DUPLICATION` (need_tag + axis both from same tokens) |
| Topic — money | `money` | `money_growth` | `need_profile`, `decision_context=money_decision` | `KEYWORDS.money` | GID map, score_need, axis boost, Reason | `PARTIAL_DUPLICATION` |
| Topic — love / marriage | `love` / `marriage` | `relationship_repair` | `need_profile`, `decision_context=relationship_decision` | `KEYWORDS.love/marriage` | GID map, score_need, Reason | `PARTIAL_DUPLICATION` |
| Topic — family | `relationship` (家族→relationship) / `family` (fertility only) | `relationship_repair` (or none) | `need_profile` | `KEYWORDS.relationship/family` | GID map, score_need, Reason | `AMBIGUOUS_OWNERSHIP` (家族 → relationship, not family) |
| Topic — health | `health` | none (`other`) | `need_profile` | `KEYWORDS.health` | GID map, score_need, Reason | `SINGLE_OWNER` (need_tag) |
| Topic — travel / safety | `travel_safe` | none | `need_profile` | `KEYWORDS.travel_safe` | GID map, score_need, Reason | `SINGLE_OWNER` |
| Topic — study / focus | `study` / `focus` (same GID) | `study_success` | `need_profile` | `KEYWORDS.study/focus` | GID map, score_need, axis boost, Reason | `PARTIAL_DUPLICATION` |
| Intention — challenge / act | `courage` | `restart_mindset` | `outcome_hint=move_forward`, `state=ready_to_change` | `KEYWORDS.courage` + `REGEX.courage` | GID map, score_need, Reason | `DUPLICATED` (need_tag *and* outcome_hint carry it, only need_tag load-bearing) |
| Intention — rest / pause | `rest` | `rest_healing` | `state=tired`, `direction=rest`, `outcome`(—) | `KEYWORDS.rest` + `REGEX.rest` | GID map, score_need, axis boost, Reason | `DUPLICATED` |
| Intention — focus / continue | `focus` | `study_success` | (none direct) | `KEYWORDS.focus` | GID map (=study), score_need | `SINGLE_OWNER` |
| Intention — decide | (none) | (none) | `outcome_hint=decide`, `decision_context.*` | `OUTCOME_KEYWORDS.decide` | reason_v4 detail only | `SHADOW_ONLY` |
| Intention — move forward | (partial: `courage` if 一歩/踏み出す/挑戦) | `restart_mindset` | `outcome_hint=move_forward` | `OUTCOME_KEYWORDS` + `KEYWORDS.courage` | reason_v4 detail; need_tag only if courage vocab hit | `PARTIAL_DUPLICATION` |
| Intention — calm down | (partial: `rest`/`mental`) | `rest_healing` / `restart_mindset` | `outcome_hint=calm` | `OUTCOME_KEYWORDS.calm` + `REGEX` | reason_v4 detail; need_tag partial | `PARTIAL_DUPLICATION` |
| Intention — repair relationship | `relationship` (if 人間関係/家族 token) | `relationship_repair` | (none) | `CONSULTATION_AXIS_KEYWORDS.relationship_repair` | axis boost; need_tag partial | `PARTIAL_DUPLICATION` |
| Intention — leave / change env | (none) | (none) | `state=ready_to_change` | `STATE_KEYWORDS.ready_to_change` | reason_v4 detail only | `SHADOW_ONLY` |
| State — fatigue | `mental` + `rest` (疲れ) | `rest_healing` | `state=tired`, `emotion.tone=tired` | `KEYWORDS.mental/rest` + `STATE_KEYWORDS.tired` | GID map (wrong-concept), score_need, reason_v4 | `DUPLICATED` (need_tag + state_profile) |
| State — anxiety | `mental` (不安/焦り) | `restart_mindset` | `state=anxious` | `KEYWORDS.mental` + `STATE_KEYWORDS.anxious` | GID map (wrong-concept), score_need, reason_v4 | `DUPLICATED` |
| State — indecision / uncertainty | (none load-bearing; shadow `迷い` in NEED_KEYWORDS.mental) | (none) | `state=uncertain`, `decision_context` | `STATE_KEYWORDS.uncertain` | reason_v4 detail only | `SHADOW_ONLY` |
| State — loss of confidence | `mental` (bare 自信) | `restart_mindset` | `state`(—) | `KEYWORDS.mental` (自信) | GID map, score_need | `SINGLE_OWNER` (weak) |
| State — stagnation | `mental` + `protection` (流れが悪い) | `restart_mindset` | `state=stuck` (停滞/動け/詰ま) | `REGEX.mental/protection` + `STATE_KEYWORDS.stuck` | GID map, score_need, reason_v4 | `DUPLICATED` |
| State — restlessness / not calm | `rest` (落ち着 regex) | `rest_healing` | `state`(—) | `REGEX.rest` | GID map, score_need | `SINGLE_OWNER` |
| Emotion — intensity | (none) | (none) | `emotion_profile.intensity` (from state confidence) | derived | reason_v4 detail only | `SHADOW_ONLY` |
| Decision context / conflict | (none) | (none) | `decision_context.primary_decision` + `decision_candidates[]` | `DECISION_KEYWORDS` | reason_v4 detail only | `SHADOW_ONLY` |
| Constraint (time/money/energy/relationship) | (none) | (none) | `constraint_profile` | `CONSTRAINT_KEYWORDS` | `translate_meaning.shrine_context_need`, reason_v4 detail | `SHADOW_ONLY` |
| Action intent (visit/reflect/save) | (none) | (none) | `action_intent` | `ACTION_KEYWORDS` | `translate_meaning.action_context`, reason_v4 detail | `SHADOW_ONLY` |
| Outcome (decide/calm/forward/clarify) | (none) | (none) | `outcome_hint` | `OUTCOME_KEYWORDS` | `translate_meaning.action_context`, reason_v4 detail | `SHADOW_ONLY` |
| Direction / history_theme framing | (none) | (drives `history_theme_candidate_boost` via *shrine* theme) | `direction_profile.direction/themes` (∈ history_theme namespace) | `DIRECTION_BY_STATE` + `HISTORY_THEME_BY_DIRECTION` | ranking uses *axis + shrine.history_theme*, NOT the profile theme; profile theme → reason_v4 + Score v3 shadow | `AMBIGUOUS_OWNERSHIP` (same namespace, two producers, only one wired to rank) |
| Negation / polarity | **(none)** | **(none)** | **(none — no field)** | **(none)** | **(none)** | `UNOWNED` |
| Confidence per signal | (none) | (none) | `state_profile.confidence` only (one scalar for the whole state block) | derived | reason_v4 intensity | `SHADOW_ONLY` (partial) |
| Multi-topic / mixed intent | `need_tags[]` (≤3, priority) | single value (last-writer / fallback) | `state.secondary_states[]`, `decision.decision_candidates[]` | — | ranking: GID union of all; axis: one | `PARTIAL_DUPLICATION` (list on need side, single on axis side) |

---

## 7. Runtime vs Shadow Matrix

| signal | computed | returned (public) | logged | stored (thread) | candidate gen | C1 / score_need | sort order | legacy Reason / Lead | reason_v4 detail | Score v3 shadow |
|---|---|---|---|---|---|---|---|---|---|---|
| `need_tags` (`extract_need_tags`) | ✅ | via `_need`/breakdown | ✅ | ✅ (recs) | filter only if user GIDs | ✅ | ✅ (via `_score_total`) | ✅ | ✅ (via input profile) | ✅ |
| `consultation_axis` | ✅ | ✅ (`recs["consultation_axis"]`, per rec) | ✅ | ✅ | ❌ | via `history_theme_candidate_boost` | ✅ (that term) | history_theme fact gating | ✅ | ✅ |
| `interpretation_profile` (whole) | ✅ (every request) | ❌ (`_debug` popped) | ✅ (`_debug`) | ❌ | ❌ | ❌ | ❌ (default) / ✅ (`SCORE_V3_MODE=active`) | ❌ | ✅ (`.interpretation`, `.action`) | ✅ |
| `state_profile` | ✅ | ❌ raw | ✅ | ❌ | ❌ | ❌ | ❌ / ✅(active) | ❌ | ✅ (state copy) | ✅ (`state_match_score` 0.45 wt) |
| `emotion_profile` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (intensity) | ❌ |
| `direction_profile` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ / ✅(active via history_score) | ❌ | ✅ (theme label) | ✅ |
| `action_intent` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (`action_context`) | ❌ |
| `decision_context` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (`_build_interpretation`) | ❌ |
| `constraint_profile` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (`shrine_context_need`) | ❌ |
| `outcome_hint` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (`action_context`) | ✅ (`meaning_match_score`) |
| `need_profile` (inside profile) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (`primary_need`) | ✅ |
| `translation_result` | ✅ (per candidate) | via `meaning_payload.source.translationResult` | ✅ | ✅ | ❌ | ❌ | ❌ / ✅(active) | ❌ | ✅ | ✅ (`history_score`, `meaning_match_score`) |

**"Computed ≠ load-bearing":** every `interpretation_profile` sub-block is
computed on every request; **zero of them** influence which shrines are
candidates, `score_need`, or the default sort order. Their only user-visible
effect today is the `recommendation_reason_v4_detail` text.

---

## 8. Information-Loss Points

Loss classes: `LOSS_BY_TRUNCATION`, `LOSS_BY_COLLAPSE`, `LOSS_BY_PRIORITY`,
`LOSS_BY_SINGLE_VALUE`, `LOSS_BY_MAPPING`, `LOSS_BY_UNUSED_SIGNAL`,
`LOSS_BY_FALLBACK`, `LOSS_BY_CONFLICT`.

| # | location | INPUT | TRANSFORM | OUTPUT | LOST | reversible | downstream impact | class |
|---|---|---|---|---|---|---|---|---|
| L1 | `KEYWORDS`/`REGEX` substring match | full sentence, clause structure, particles | `token in query` / `pattern.search` | `hits{tag:[token]}` | word order, clause boundaries, `けど`/`より`/`。` scope, which clause a token was in | no | negation & contrast invisible; `A より B` and `A けど B` treated identically | `LOSS_BY_COLLAPSE` |
| L2 | `max_tags=3` in `extract_need_tags` | all matched need_tags | slice `NEED_PRIORITY`-ordered list to 3 | ≤3 tags | 4th+ need entirely | no | a 4-topic consultation loses its lowest-priority topic silently | `LOSS_BY_TRUNCATION` |
| L3 | `NEED_PRIORITY` fixed global order | co-equal needs | pick top-N by a static rank (`protection > marriage > love > … > rest > travel_safe`) | ordered subset | user's *own* emphasis; "primary is what I mentioned first/loudest" | no | `結婚より仕事` → `[marriage, career]` (marriage wins by priority though career is the point) | `LOSS_BY_PRIORITY` |
| L4 | `NEED_TAG_ALIASES` (×2 copies) | `romance`/`anxiety`/`challenge`/… | map to canonical (`romance→love`, `anxiety→mental`, `challenge→courage`) | canonical tag | the distinction the alias erased (`anxiety` vs generic `mental`) | no | English-ish inbound tags lose granularity | `LOSS_BY_MAPPING` |
| L5 | `resolve_need_payload` when `need_tags` passed | free text (Compass: none) | if `need_tags` truthy, skip `extract_need_tags` entirely | normalized passed tags | any free-text nuance (n/a for Compass; relevant if a caller passes tags AND text) | no | free text ignored when explicit tags present | `LOSS_BY_FALLBACK` |
| L6 | `resolve_consultation_axis` single-value | multiple axis-keyword hits | `sorted(hits, key=(-count, priority))[0]` | one axis | every secondary axis | no | `仕事に集中できない` → `study_success` (集中) beats `career`; boost routed to the wrong theme family | `LOSS_BY_SINGLE_VALUE` + `LOSS_BY_CONFLICT` |
| L7 | axis need_tag fallback | ordered `need_tags` | first tag with a `NEED_TAG_TO_CONSULTATION_AXIS` entry | one axis | the intended focus when a secondary co-fired tag maps first (`家族`→`relationship`→`relationship_repair` for a travel query) | no | axis-driven `history_theme` boost misdirected | `LOSS_BY_PRIORITY` |
| L8 | `need_tags_to_goriyaku_ids` union | per-tag GID sets | `set().union(*[NEED_TO_GORIYAKU_IDS[t] for t in tags])` | one flat GID set | which tag contributed which id; per-tag weighting | no | 2 needs → up to 10 GIDs incl. off-topic (`courage` pulls `夫婦円満`,`恋愛成就`); precision diluted | `LOSS_BY_COLLAPSE` |
| L9 | candidate pool: no Need filter on free-text path | intent (`need_tags`) | pool = top ~100 by `popular_score` (Need not applied) | popularity-ordered pool | Need-relevance of the pool | no | `score_need = 0` whenever no pooled shrine carries a mapped tag; rank = popularity/distance | `LOSS_BY_UNUSED_SIGNAL` |
| L10 | `score_need = len(matched_all)` | graded semantic fit | count of matched *channels* (astro ∪ text ∪ gid) | small integer | how *well* a tag fits (勝運 vs 縁結び both = 1) | no | ties everywhere; `astro` flat +2 can outrank a real thin need match | `LOSS_BY_COLLAPSE` |
| L11 | `_resolve_primary_reason` | all `reason_facts` | `sorted(facts, key=(PRIMARY_REASON_PRIORITY, -score, label))[0]` | one primary fact | every other reason; the fact that a *state* or *intention* was present (no such fact type) | no | Reason foregrounds `user_selected_tag` / `history_theme` over the user's free-text nuance | `LOSS_BY_PRIORITY` |
| L12 | `_build_need_lead` fallback chain | matched evidence | gid label → text hint → hard-coded per-tag label → `"ご利益"` | one short label | the consultation nuance when `score_need = 0` | no | generic Lead ("ご利益") on an emotional-state consultation | `LOSS_BY_FALLBACK` |
| L13 | `build_recommendation_reason` fallback | rec + need_tags | if no `_primary_reason_label` and no `matched_tags` → `"{name}は、今の悩みや願いに合わせて…"` | generic string | everything the user said | no | no-match consultation gets a content-free Reason | `LOSS_BY_FALLBACK` |
| L14 | `interpretation_profile` → `_debug` pop | full profile | `data.pop("_debug")` at response boundary | (nothing survives except reason_v4 detail) | the structured profile itself | reversible (recomputable) | clients can't see or use the profile; only the pre-rendered v4 copy | `LOSS_BY_UNUSED_SIGNAL` |
| L15 | `need_profile` (in profile) vs `extract_need_tags` | same query | two different keyword tables (`NEED_KEYWORDS` vs `KEYWORDS`+`REGEX`) | two need lists that can disagree | consistency | no (by construction) | a promoted profile would route on a *different* need list than the ranker | `LOSS_BY_CONFLICT` |
| L16 | `state_profile.confidence` single scalar | per-signal certainty | one float for the whole state block (`0.45 + n*0.12`, capped 0.95) | one number | which state is certain vs guessed | no | reason_v4 `intensity` is coarse; no per-need confidence anywhere | `LOSS_BY_COLLAPSE` |

**Irreversible-loss points** (cannot be reconstructed from the output alone,
only by re-running on the raw query): L1, L2, L3, L4, L6, L7, L8, L10, L11,
L15, L16. **Recoverable** (raw query retained; recompute possible): L5, L9,
L12, L13, L14 (`raw_query` is kept in `interpretation_profile` and in the
thread's saved query, so a richer pass could re-derive).

---

## 9. Existing Vessel Reuse Assessment

Classes: `REUSE_AS_IS`, `REUSE_WITH_EXTENSION`, `REUSE_AS_INPUT_ONLY`,
`PROMOTE_FROM_SHADOW`, `DEPRECATE_CANDIDATE`, `REQUIRES_STRUCTURAL_CHANGE`,
`UNKNOWN`.

| structure | class | evidence | strengths | limits | coupling risk | migration risk | back-compat risk | testability | Compass effect | Concierge effect |
|---|---|---|---|---|---|---|---|---|---|---|
| `need_tags` (list) | `REUSE_AS_INPUT_ONLY` (as the *routing* key) / `REQUIRES_STRUCTURAL_CHANGE` (as the *semantic model*) | 15-value flat list carries topic+intention+state; `max_tags=3`; no polarity slot (§6, §11) | tested, stable, drives GID routing + Reason; shared, predictable | cannot separate topic/state/intention; no negation; priority truncation | HIGH — `NEED_TO_GORIYAKU_IDS`, `_attach_breakdown`, `build_recommendation_reason`, `NEED_TAG_TO_CONSULTATION_AXIS`, Compass `purpose` validation all key off it | HIGH if the *set* changes (Compass `purpose` must be a `NEED_TAG`); LOW if kept as an internal routing layer fed by a richer model | HIGH (API `purpose`, thread payloads, `_need` debug) | HIGH (pure functions, many existing tests) | shared — any set/mapping change hits Compass | primary routing key |
| `consultation_axis` | `REUSE_WITH_EXTENSION` or `DERIVED_ONLY` | single value, produced by keyword-then-fallback, only rank effect is `history_theme_candidate_boost` (§13) | cheap, tested, isolates a ranking-routing concern | single-valued; flips on secondary tokens; partial duplicate of `need_tag` | MEDIUM — `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`, reason_fact gating | LOW (add multi-value alongside) to MEDIUM (change semantics) | MEDIUM (`recs["consultation_axis"]` is in the response, per rec) | HIGH | shared (Compass derives it from `purpose`) | framing + boost routing |
| `interpretation_profile` | `PROMOTE_FROM_SHADOW` — but **after normalization** (§10) | stable 9-key schema, deterministic, already wired to `translate_meaning`/reason_v4/Score-v3; `SCORE_V3_MODE=active` already consumes it | rich (state/emotion/action/decision/constraint/outcome); `raw_query` retained; existing tests assert the schema | dual need extraction (L15); no negation/polarity/per-signal confidence; single-`primary` + list-`secondary` shape inconsistency; naming overlaps (`direction_profile` ≠ compass direction; `need_profile` ≠ `need_tags`) | MEDIUM — reason_v4 and Score v3 already depend on the exact keys | MEDIUM — schema keys are asserted by tests; adding fields is safe, renaming is not | LOW (currently `_debug`-only + display) | MEDIUM (`test_consultation_interpreter.py` covers schema + a few extractions; no negation/determinism-corpus tests) | Compass passes `query=""` → profile near-empty; promoting it changes reason_v4 for Compass too | main promotion candidate |
| `NEED_TO_GORIYAKU_IDS` | `REUSE_AS_IS` (structurally) — semantic corrections are a separate data project (see PR #2646 §19) | `dict[str, set[int]]`, 14/15 non-empty, keyed to 39-row master | simple, shared, testable | `mental`/`rest` wrong-concept; no calm/healing tag exists; borrowed maps | HIGH — the join key between semantics and evidence | LOW (dict edit) but each edit shifts ranking for all queries of that need | LOW | HIGH (`test_need_to_goriyaku_tag_ids.py`) | shared | shared |
| `reason_facts` | `REUSE_WITH_EXTENSION` | typed list `{type,label,label_ja,evidence,score,is_primary}`; 8 types, none for state/intention/negation (§17) | extensible by design; `PRIMARY_REASON_PRIORITY` is a single ordered dict | no polarity; `PRIMARY_TIER` boundary is hard-coded at `element` | MEDIUM — `_resolve_primary_reason`, `has_primary_tier_reason`, distance-mode tiering, reason_v4 `authority_context` | LOW (add a type + a priority slot) | MEDIUM (fact `type` values appear in responses / analytics) | HIGH | shared | shared |
| `primary_reason` / `PRIMARY_REASON_PRIORITY` | `REUSE_WITH_EXTENSION` | ordered dict, `culture_translation` excluded from primary selection | deterministic, one code path | adding a tier reshuffles selection globally | MEDIUM | LOW | MEDIUM | HIGH | shared | shared |
| `Lead` (`_build_need_lead`) | `REUSE_WITH_EXTENSION` | gid-label → text-hint → per-tag fallback → `"ご利益"` | short, evidence-cited when a match exists | no state/intention input; generic on `score_need = 0` | LOW | LOW | LOW | HIGH | shared | shared |
| `Reason` legacy (`build_recommendation_reason`) | `REUSE_WITH_EXTENSION` | need_tag / primary_reason driven | consistent with ranking evidence | generic fallback; ignores profile | MEDIUM | LOW | MEDIUM (string in response) | HIGH | shared | shared |
| `recommendation_reason_v4` | `PROMOTE_FROM_SHADOW` (already half-promoted) | `_build_interpretation` consumes state/decision/constraint/outcome; `_v4_detail` is on the rec, not `_debug` → reaches response | proves richer signals are consumable *today* with no schema change | parallel to legacy `reason`; which the UI shows is a frontend decision; no negation input | MEDIUM (depends on `interpretation_profile` keys + `translate_meaning`) | LOW | LOW–MEDIUM (`_v4_detail` shape is in the response) | MEDIUM (`test_recommendation_reason_v4.py`) | affects Compass reason_v4 | affects Concierge reason_v4 |

---

## 10. interpretation_profile Promotion Assessment

Verdict: **`PROMOTABLE_AFTER_NORMALIZATION`.**

| criterion | finding |
|---|---|
| semantic completeness | Topic + State + Emotion + Action + Decision + Constraint + Outcome present. **Missing: polarity/negation, per-signal confidence, clause/segment provenance, hypothetical/contrast marking.** |
| naming consistency | **Inconsistent.** `direction_profile` is not the Compass compass-direction; `need_profile.need_tags` is a *second* need list (not `extract_need_tags`); `themes` collides with the `history_theme` namespace; `emotion_profile.tone` = `primary_state` (redundant). |
| deterministic behavior | **Yes** — verified: identical output across 3 runs for the same input; pure functions, no clock/RNG/DB. |
| test coverage | Schema keys asserted (`test_consultation_interpreter.py::test_..._returns_stable_schema`), a handful of extraction assertions, empty-input safety, explicit-need-tag merge. **No negation cases, no determinism corpus, no cross-check vs `extract_need_tags`.** |
| overlap with `need_tags` | **High and divergent** (L15): `need_profile` uses `consultation_interpreter.NEED_KEYWORDS` which has tokens the runtime `KEYWORDS` lacks (`前に進`, `悩み`, `迷い`, `考えすぎ`, `生活費`, `一人`, `学び`, `スキル`). Promoting `need_profile` as-is would route recommendations on a different need list than `NEED_TO_GORIYAKU_IDS` expects. |
| overlap with `consultation_axis` | Partial: `decision_context.primary_decision` (`career_decision` …) mirrors the axis families; `direction_profile` mirrors the `history_theme` boost namespace. |
| negation representation | **None.** No field. |
| polarity | **None.** |
| confidence | One scalar for the whole `state_profile`; nothing per need/topic/intention. |
| clause segmentation | **None** — `_collect_hits` matches against the whole string. |
| multi-value support | Mixed: `state_profile.secondary_states[]` and `decision_context.decision_candidates[]` are lists; `direction_profile.direction`, `outcome_hint.primary_outcome`, `action_intent.intent` are single. Inconsistent shape. |
| downstream schema compatibility | `translate_meaning`, `recommendation_reason_v4`, `recommendation_input_profile`, Score v3 all already read specific keys — **additive changes are safe; key renames are breaking.** |
| scoring compatibility | `SCORE_V3_MODE=active` already routes `state_match_score` (0.45 weight), `meaning_match_score`, `history_score` from the profile. Promotion for ranking = flip the env var + accept the pre-tuned weights (no new code path), *after* fixing L15. |
| Reason compatibility | reason_v4 already consumes it; legacy `reason`/Lead/`reason_facts` do not (needs an extension, §17). |

**What "normalization" means here (illustrative, not a schema proposal):**
unify the need list to one extractor; give every signal block the same
`{primary, candidates[], confidence}` shape; add an explicit polarity marker
per signal; rename `direction_profile`/`themes` to avoid the `history_theme`
and Compass-direction collisions.

---

## 11. need_tag Capacity Assessment

Can the 15-value list remain the dominant semantic representation?

| must express | can `need_tag` express it? | evidence |
|---|---|---|
| topic | **yes** | `career`, `money`, `love`, `health`, `study`, `travel_safe` are topics |
| state | **partially, by overloading** | `mental` is a state, not a topic; fatigue lands as `mental`+`rest`; anxiety-only text (`心配`) lands nowhere load-bearing |
| intention | **partially, by overloading** | `courage`, `rest`, `focus` are intentions competing for slots with topics |
| uncertainty | **no** | no `need_tag` for "I don't know / I'm undecided"; only shadow `state=uncertain` |
| negation | **no** | flat string list has no polarity position |
| decision conflict (`A より B`) | **no** | both A and B become tags; priority picks one; the *contrast* is gone |
| mixed intent (topic + intention) | **only within 3 slots, priority-ordered** | `転職したいけど怖い` → `[career, courage]`; the "but" relationship is not represented |
| relationship subtype (romantic vs family vs workplace) | **coarsely** | `love` vs `relationship` vs `marriage`; 家族→`relationship` (not `family`); no workplace-specific value |
| change direction (toward / away / pause) | **no** | `courage`≈toward, `rest`≈pause exist as *tags* but "away from X" has no representation |

Deficiency classification: **`SEMANTIC_OVERLOAD`** (one axis carries three
kinds of meaning) **+ `MODEL_CAPACITY_LIMIT`** (a flat unordered-except-by-static-priority
string list structurally cannot hold polarity, per-signal confidence, or a
primary/secondary relationship *with its reason*). It is **not**
`VOCABULARY_ONLY` (adding words to `mental` won't create a polarity slot) and
**not** `MAPPING_ONLY` (fixing `NEED_TO_GORIYAKU_IDS["mental"]` won't let the
model represent "not anxious, just undecided").

`need_tag` **can** remain the **evidence-routing layer** (it is good at that:
tested, shared, deterministic). It **cannot** remain the place where topic,
state, intention, and polarity are *distinguished*.

---

## 12. consultation_axis Assessment

| question | finding |
|---|---|
| a real semantic dimension? | **Weakly.** It is a *framing label* ("this is a career-change consultation") derived from the same tokens as `need_tag`. |
| a ranking helper? | **Yes** — its only ranking effect is `resolve_history_theme_candidate_boost(axis, shrine.history_theme)` added to `score_need_rank_weighted` and the prefilter score. |
| a derived framing layer? | **Yes** — `resolve_consultation_axis` is keyword-then-`need_tag`-fallback; never independent of `need_tag` on the heuristic path. |
| duplicated topic classification? | **Partially** — `money_growth`/`career_change`/`study_success`/`relationship_repair` shadow `money`/`career`/`study`/`relationship` need_tags. |
| legacy compatibility structure? | **Partly** — several axes (`independence`, `nature_reset`) have **no** `NEED_TAG_TO_CONSULTATION_AXIS` producer and are reachable only from query keywords; `health` has no producer at all. |
| how produced | `normalize(llm_axis)` (never set) → `CONSULTATION_AXIS_KEYWORDS` hit (most-hits, then `CONSULTATION_AXIS_PRIORITY`) → first `need_tag` with a mapping → `"other"`. |
| would real inputs need multiple axes? | **Yes** — e.g. `仕事に集中できない` legitimately spans `career_change` + `study_success`; the single value drops one. |
| what happens on secondary-token flip | The axis can change entirely (`家族` in a travel query routes the axis to `relationship_repair`), misdirecting the `history_theme` boost. |
| should it stay single-valued? | **Open** — it is a `SINGLE_VALUE_BOTTLENECK` for ~4/34 audited cases (PR #2646 §17 AXIS/MULTI-SIGNAL). |
| does it duplicate `need_tag`? | **Partially** (framing vs routing). |
| does it carry info `need_tag` cannot? | **One thing:** the `history_theme` boost routing key (axis × shrine theme → magnitude). Nothing else. |

Reuse class: **`DERIVED_ONLY`** (keep as a computed view over the semantic
core) **or `REUSE_WITH_EXTENSION`** (allow multi-value). Not
`DEPRECATE_CANDIDATE` unless the `history_theme` boost is redesigned.

---

## 13. Negation / Polarity Capacity

| construct | asserted | negated | de-emphasised | contrasted | uncertain | hypothetical |
|---|---|---|---|---|---|---|
| `need_tag` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `consultation_axis` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `interpretation_profile` (any sub-block) | ✅ | ❌ | ❌ | ❌ | `state=uncertain` (a *state*, not a polarity) | ❌ |
| `reason_facts` | ✅ (`is_primary` bool only) | ❌ | ❌ | ❌ | ❌ | ❌ |

Examples and where they currently land (from PR #2646 §10, re-verified):

| input | current output | polarity actually meant |
|---|---|---|
| `恋愛の相談ではない` | `need_tags=['love']`, GID `{縁結び, 恋愛成就}` | love = **negated** |
| `転職したいわけではない` | `need_tags=['career']` | career = **negated** |
| `不安ではないけど迷っている` | `need_tags=['mental']` (from 不安), `state=uncertain` | 不安 = **negated**, 迷い = **asserted** (and unrepresented) |
| `結婚より仕事を優先したい` | `need_tags=['marriage','career']`, axis `relationship_repair` | marriage = **de-emphasised**, 仕事 = **asserted primary** |
| `休みたいというより環境を変えたい` | `need_tags=['rest']`, `state=ready_to_change` (shadow) | 休みたい = **contrasted-away**, 環境を変えたい = **asserted** (unrepresented) |

Classification: **`NOT_REPRESENTABLE`** without a new field. There is no
object today whose shape can carry a polarity value, and no consumer that
would read one. `REPRESENTABLE_BUT_UNUSED` does **not** apply — even
`state=uncertain` is a coincidental state label, not a polarity slot.

### 13.1 Two candidate mitigations, precisely defined

These two Decision 5 values are distinct **by what they preserve
downstream**, not by how they are implemented. A parser / preprocess step
may be the *producer* in either case — that alone does not decide the
classification.

**`PREPROCESS_GUARD`** — a Concierge-side pre-interpretation protection
mechanism that detects negated / excluded / contrasted phrases and
**suppresses or adjusts keyword / regex matching before semantic output is
produced**. Properties:

- **no** first-class polarity field is added to the semantic model;
- **no** polarity object is carried downstream;
- **no** new semantic schema is introduced;
- **no** downstream consumer receives `"negated"` as structured semantic
  data — consumers see only the post-guard semantic result;
- its effect is behavioural filtering / suppression before normal
  extraction;
- it is a bounded, compatibility-oriented mitigation;
- it is Concierge-side and does not change Compass `purpose` input directly.

  *Example:* on `恋愛の相談ではない` a `PREPROCESS_GUARD` may stop `恋愛` from
  producing `need_tag=love`. Downstream structures do **not** receive
  `polarity = negated`; they receive only the (now love-free) semantic
  result.

**`POLARITY_SIGNAL`** — polarity is **preserved explicitly as part of the
consultation semantic representation and remains available to downstream
consumers**. Properties:

- introduces a first-class polarity field (or equivalent structured signal),
  conceptually able to represent at least `asserted` / `negated` /
  `de-emphasised` / `contrasted`, and `uncertain` / `hypothetical` if a
  later design supports them;
- polarity survives interpretation;
- downstream consumers (Reason / explanation / future ranking) can inspect
  it;
- it is **not** merely suppression before extraction.

  *Clarification:* a `POLARITY_SIGNAL` **may** be populated by a lightweight
  parser or preprocess step. "Implemented by a preprocess parser" does
  **not** make it a `PREPROCESS_GUARD`. The classification depends solely on
  whether polarity is preserved as structured semantic data downstream.

### 13.2 Contrast table

| property | `PREPROCESS_GUARD` | `POLARITY_SIGNAL` |
|---|---|---|
| blocks a false keyword match | yes | yes (can) |
| adds a semantic field | no | yes |
| polarity survives downstream | no | yes |
| schema change | no | yes |
| Reason can inspect negation directly | no | yes |
| ranking can inspect negation directly | no | yes, if wired |
| compatibility risk | lower | higher |
| semantic fidelity | limited (suppression only) | higher (structured) |
| Compass `purpose` input affected | no (Concierge-side) | no directly; shared profile schema changes |
| producer | parser / preprocess step | parser / preprocess step **or** later a clause model — but the signal is retained |

---

## 14. Multi-Signal Capacity

| combination | representation today | destructive point |
|---|---|---|
| multiple Topics | `need_tags[]` (≤3), `NEED_PRIORITY` order | `max_tags=3` (L2); 4th topic dropped |
| multiple States | `state_profile.secondary_states[]` (list) | not load-bearing; `primary_state` alone feeds `direction_profile`/reason_v4 |
| Topic + State | `need_tags` mixes them (`[career, mental]`); `state_profile` separately | GID union (L8) blends them; `score_need` can't say "topic matched, state didn't" |
| Topic + Intention | `need_tags` mixes them (`[career, courage]`) | priority + `max_tags`; the *relationship* ("career, but scared") is gone |
| State + Intention | `state_profile` + (`need_tag` if intention has vocab) + `outcome_hint` | three places, none authoritative |
| contradictory signals | both become `need_tags` / axis-keyword hits | axis single-value picks one (L6); no "conflict" marker |
| primary vs secondary intent | `need_tags[0]` / `primary_need_tag` / `_primary_reason_label` | *positional* only; no "secondary because X" and no way to keep >3 |

Prioritization becomes destructive at: **L2** (`max_tags=3` — hard drop),
**L3/L7** (`NEED_PRIORITY` / axis fallback — user's own emphasis overridden by
a static table), **L6** (axis single-value — a legitimate second axis is
discarded), **L8** (GID union — per-tag identity lost), **L11**
(`_resolve_primary_reason` — one fact wins, and there is no fact type for
"state" or "intention" so those can never be the primary reason).

`primary vs secondary` is **representable positionally** (list order,
`primary_need_tag`) but **not with capacity or rationale** (can't keep the
4th, can't say why one is primary, can't mark one as "contrasted away").

---

## 15. Concierge / Compass Boundary

| structure | classification | evidence |
|---|---|---|
| free-text interpreter (`query`, `extract_need_tags`, `KEYWORDS`, `REGEX`, `resolve_need_payload` free-text branch, `interpret_consultation` state/outcome/etc.) | **`CONCIERGE_ONLY`** | Compass sends `query=""` and `purpose = one need_tag`; `resolve_need_payload(query="", need_tags=[purpose])` short-circuits before `extract_need_tags`; `interpret_consultation("")` yields an empty profile |
| `NEED_TAGS` set (15) | **`SHARED`** | Compass validates `purpose in NEED_TAGS` (`STATE_INVALID_PURPOSE` otherwise) |
| `NEED_TO_GORIYAKU_IDS` + `need_tags_to_goriyaku_ids` | **`SHARED`** | both call `build_chat_recommendations` → `_attach_breakdown` |
| `_prefilter_candidates_for_need` / `_attach_breakdown` / `score_need` / C1 | **`SHARED`** | `compass_recommendation_orchestrator.get_compass_recommendations` → `build_chat_recommendations(query="", need_tags=[purpose])` |
| `_sort_chat_recommendations` / ranking | **`SHARED`** | same facade; Compass adds its own direction + distance-stage filters *before* the facade |
| `consultation_axis` | **`SHARED_BUT_DIFFERENT_ENTRYPOINT`** | Concierge: query keywords → need_tag fallback. Compass: query empty → always the `need_tag` fallback for `purpose` |
| `build_recommendation_reason` / Lead / `reason_facts` | **`SHARED`** | produced inside `build_chat_recommendations` for both |
| `interpret_consultation` / `interpretation_profile` / `translate_meaning` / `recommendation_reason_v4` | **`SHARED`** (Compass passes a near-empty profile) | `compass_recommendation_orchestrator` calls `interpret_consultation` and passes the profile into `build_chat_candidates` and `build_chat_recommendations` |
| HTTP orchestration (quota, thread, request-shape, LLM route, compat mode) | **`SHOULD_REMAIN_SEPARATE`** | `CompassRecommendationsView` docstring: "既存 ConciergeChatView を実装の簡便さのために流用しない"; own view, no import from `api_views_concierge` |
| Evidence contract (`goriyaku_tags` reviewed links) | **`SHARED`** | same `Shrine.goriyaku_tags` |

**Risk register for a Concierge-driven semantic redesign:**

| change | Compass impact | severity |
|---|---|---|
| add/adjust `KEYWORDS`/`REGEX`; add a `PREPROCESS_GUARD` (suppression) or a Concierge-side polarity-signal producer; clause segmentation | **none** (Compass has no free text) | LOW |
| change the `NEED_TAGS` *set* (add/remove/rename) | **breaks** Compass `purpose` validation + API contract | HIGH |
| change `NEED_TO_GORIYAKU_IDS` | shifts Compass ranking for that `purpose` | MEDIUM |
| change `_attach_breakdown` / `score_need` / `_sort` | changes Compass ordering | MEDIUM–HIGH |
| change `NEED_TAG_TO_CONSULTATION_AXIS` or make axis multi-value | changes Compass axis + `history_theme` boost | MEDIUM |
| rename `interpretation_profile` keys | breaks Compass reason_v4 (shared `translate_meaning`/reason_v4) | MEDIUM |
| add fields to `interpretation_profile`, add `reason_fact` types, promote profile for Concierge ranking only (env/flag scoped) | Compass unaffected if gated | LOW |

---

## 16. Explanation Compatibility

Per signal, can the current explanation architecture consume it without
structural change? Classes: `ALREADY_SUPPORTED`, `ADAPTER_SUFFICIENT`,
`REASON_SCHEMA_EXTENSION_REQUIRED`, `ARCHITECTURE_CHANGE_REQUIRED`.

| signal | legacy `reason` / Lead | `reason_facts` / `primary_reason` | `recommendation_reason_v4` | overall |
|---|---|---|---|---|
| **State** (tired/anxious/uncertain/…) | not read → would need a fallback branch | no `state` fact type → `REASON_SCHEMA_EXTENSION_REQUIRED` | **`ALREADY_SUPPORTED`** — `_build_interpretation` maps `primary_state` to copy today | `ADAPTER_SUFFICIENT` for v4; `REASON_SCHEMA_EXTENSION_REQUIRED` for legacy/facts |
| **Intention** (decide/forward/calm/challenge) | Lead has hard-coded per-tag labels; no intention input | no `intention` fact type | v4 reads `outcome_hint` / `action_intent` via `translate_meaning.action_context` | `ADAPTER_SUFFICIENT` (v4); `REASON_SCHEMA_EXTENSION_REQUIRED` (facts) |
| **Decision context / conflict** | not read | no fact type | v4 reads `decision_context.primary_decision` | `ADAPTER_SUFFICIENT` (v4); `REASON_SCHEMA_EXTENSION_REQUIRED` (facts) |
| **Constraint** (time/money/energy) | not read | no fact type | v4 reads `constraint_profile` via `translate_meaning.shrine_context_need` | `ADAPTER_SUFFICIENT` (v4); `REASON_SCHEMA_EXTENSION_REQUIRED` (facts) |
| **Negation / polarity** | not representable | no polarity on facts; `is_primary` bool only | not representable (no input field) | **`ARCHITECTURE_CHANGE_REQUIRED`** — needs a new field upstream *and* a consumer |
| **history_theme framing** (from profile) | not read | `history_theme` fact exists but gated on axis boost (uses *shrine* theme) | v4 reads `translate_meaning.history_theme` (from profile) | `ALREADY_SUPPORTED` (v4); `ADAPTER_SUFFICIENT` (facts, if de-gated) |

**Net:** `recommendation_reason_v4` is a working proof that state / intention /
decision / constraint are consumable **today** with no schema change (it
already renders them). The gaps are: (a) the **legacy `reason`/Lead** and
**`reason_facts`/`primary_reason`** paths ignore all of it, and (b)
**negation** has no representation anywhere and would need an upstream field
plus a consumer — the only `ARCHITECTURE_CHANGE_REQUIRED` item.

---

## 17. Architecture Smells

| smell | evidence / location | impact | severity |
|---|---|---|---|
| `DUPLICATE_INTERPRETER` | **three** need-keyword tables: `domain/need_tags.KEYWORDS`+`REGEX` (runtime), `consultation_interpreter.NEED_KEYWORDS` (profile), `concierge_chat_need.NEED_SYNONYMS` (6-need fallback) — verified to disagree (`前に進`, `悩み`, `迷い`, `生活費`, `一人`, `学び`, `スキル` are shadow-only) | a promoted profile routes on a different need list than the ranker; every vocab fix must be applied in ≥2 places | **HIGH** |
| `UNUSED_PROFILE` / `DEAD_SIGNAL` | `state_profile`, `emotion_profile`, `action_intent`, `decision_context`, `constraint_profile`, `outcome_hint` computed every request; **zero** effect on candidates, `score_need`, or default sort order | compute cost + false impression that consultation state is "handled" | **MEDIUM** |
| `SHADOW_LOGIC` with a live switch | Score v3 (`recommendation_score_components`, weights `state 0.45` …) consumes the profile and is one env var (`SCORE_V3_MODE=active`) from driving the sort order | latent behavior change; the "shadow" is production-adjacent | **MEDIUM** |
| `SEMANTIC_OVERLOAD` | `need_tag` list carries Topic + State + Intention (§6, §11) | cannot extend to negation / multi-state / decision-conflict without a new layer | **MEDIUM** |
| `SINGLE_VALUE_BOTTLENECK` | `consultation_axis` (1 of 9); `direction_profile.direction` (1); `outcome_hint.primary_outcome` (1) | secondary axes / outcomes silently dropped (L6, L7) | **MEDIUM** |
| `MAGIC_PRIORITY` | `NEED_PRIORITY` (static 15-order), `CONSULTATION_AXIS_PRIORITY`, `PRIMARY_REASON_PRIORITY`, `NEED_PRIORITY` in `concierge_chat_need` (a **fourth**, 6-key, different order) | user emphasis overridden by hidden tables; four priority orders to keep coherent | **MEDIUM** |
| `REGEX_COUPLING` | ranking correctness depends on `REGEX`/`KEYWORDS` literal token lists in `domain/need_tags.py`; `NEED_TEXT_WEIGHTS` (7 needs) separately couples ranking to shrine-prose tokens | vocabulary edits are ranking changes; hard to test in isolation | **MEDIUM** |
| `MAPPING_COUPLING` | `NEED_TO_GORIYAKU_IDS` is the sole semantic↔evidence join; `mental`/`rest` map to wrong-concept ids; no calm/healing tag exists | semantic model quality is capped by the 39-row master (structural — PR #2646 denominator C) | **MEDIUM** |
| `EXPLANATION_COUPLING` | two parallel reason systems (`build_recommendation_reason` → `rec["reason"]`; `_attach_recommendation_reason_quality` → `rec["recommendation_reason_v4_detail"]`), both in the response; `PRIMARY_TIER_REASON_TYPES` hard-cut at `element` | which one is authoritative is undefined at the API layer; a redesign must pick | **MEDIUM** |
| `DOC_CODE_DRIFT` | stale 15-row `backend/temples/fixtures/goriyaku_tags.json` (different names) vs 39-row runtime master; `interpret_consultation` docstring says "does not change recommendation ranking … prepares structured input for … future Score v3 shadow observation" (accurate, but reason_v4 detail now ships to the response) | onboarding hazard; the fixture actively misleads mapping analysis | **LOW–MEDIUM** |
| `NAMING_COLLISION` | `direction_profile` (state-derived) vs Compass compass-direction (`houi`); `direction_profile.themes` vs `history_theme`; `need_profile` vs `need_tags`; `emotion_profile.tone` == `state_profile.primary_state` | promotion-time confusion; key renames are breaking | **LOW** |
| `UNREACHABLE_STATE` | `consultation_axis` values `independence`, `nature_reset` have no `NEED_TAG_TO_CONSULTATION_AXIS` producer; `health` has none | those axes only fire on query keywords; `health` never gets a `history_theme` boost | **LOW** |
| `BACKWARD_COMPATIBILITY_RISK` | `NEED_TAGS` set is an API contract (Compass `purpose`); `recs["consultation_axis"]`, `rec["reason"]`, `rec["recommendation_reason_v4_detail"]` are in the response body; thread payloads persist `recommendations` | any semantic-core change is also an API/persistence change | **MEDIUM** |
| `NO BLOCKER` | nothing prevents a Mother Ship decision or a scoped implementation; the required work is bounded | — | — |

No `BLOCKER`-severity smell found.

---

## 18. Reuse-vs-Redesign Options

### Option A — Preserve Current Model (adapters/consumers only)

Keep `need_tags`, `consultation_axis`, `interpretation_profile` exactly.
Only add adapters/consumers: e.g. wire `state_profile`/`outcome_hint` into the
**legacy** `reason`/Lead the way reason_v4 already does; de-gate the
`history_theme` fact; add a schema-free negation mitigation — a
`PREPROCESS_GUARD` (§13.1) that suppresses `extract_need_tags` hits inside a
negated span (a string transform before the existing matcher; **no polarity
field, nothing carried downstream**).

- **Decision 5 alignment:** Option A uses `NEGATION_MODEL = PREPROCESS_GUARD`
  (suppression only; no structured polarity).
- **effort:** LOW–MEDIUM. **semantic fidelity gain:** LOW–MEDIUM (the guard
  fixes ~6/34 cases by *suppression*; state reaches the legacy Reason).
- **risk:** LOW (no schema, no set change). **back-compat:** HIGH-safe.
- **complexity:** adds a preprocess step + Reason branches; the three-table
  `DUPLICATE_INTERPRETER` and `SEMANTIC_OVERLOAD` smells **remain**.
- **migration:** none. **test:** extend interpreter + reason tests.
- **Compass:** the negation guard is Concierge-only (LOW); Reason changes are
  shared (MEDIUM).
- **ceiling:** cannot represent multi-state, decision-conflict, or
  primary/secondary-with-reason — those need a richer container.

### Option B — Promote the Existing Rich Profile

Make `interpretation_profile` a first-class semantic input for Concierge;
keep `need_tags` as the evidence-routing / compatibility layer. Flip
`SCORE_V3_MODE` to `active` (scoped) so `state_match_score` etc. drive
ranking; wire `interpretation_profile.*` into `reason_facts` (new types) and
the legacy Reason.

- **prerequisite:** fix `DUPLICATE_INTERPRETER` (unify `need_profile` with
  `extract_need_tags`) and the shape/naming inconsistencies (§10) — i.e. the
  "normalization" step. Without it, ranking would run on a different need
  list than evidence routing.
- **effort:** MEDIUM. **semantic fidelity gain:** MEDIUM–HIGH (state /
  outcome / decision become load-bearing; Score v3 weights already tuned).
- **risk:** MEDIUM — Score v3 activation is a real ranking change; needs the
  existing A/B observation (`score_v3_ab_observation`) as the guard; reason_v4
  and Compass already depend on the exact profile keys.
- **complexity:** MEDIUM (mostly wiring + one env/flag + a need-list unify).
  **migration:** none (no DB). **test:** Score v3 activation tests, reason
  extension tests, need-list-parity test.
- **back-compat:** MEDIUM (`reason_facts` type values, `_v4_detail` shape,
  ranking order all shift). **Compass:** shares the profile + ranking →
  MEDIUM; gate activation per entrypoint to isolate.
- **still missing:** negation — Option B does not add polarity by itself.
- **Decision 5 alignment:** Option B may pair with either
  `NEGATION_MODEL = PREPROCESS_GUARD` (schema-free suppression, if the
  profile schema is left unextended) **or** `NEGATION_MODEL = POLARITY_SIGNAL`
  (if the profile schema gains a polarity field as part of the promotion).

### Option C — Normalize the Semantic Model (canonical layer)

Introduce one canonical representation between interpretation and
recommendation, e.g. (illustrative only, **not a schema proposal**):

```text
consultation_semantics
  topic[]        {value, confidence, polarity}
  state[]        {value, confidence, polarity}
  intention[]    {value, confidence, polarity}
  decision       {frame, options[], conflict?}
  constraints[]  {value}
  raw_query
```

`need_tags` / `consultation_axis` / `interpretation_profile` become **derived
views** over it (adapters preserve every current output).

- **effort:** HIGH. **semantic fidelity:** HIGH (topic/state/intention
  separated; polarity first-class; multi-value native; primary/secondary
  carries a reason).
- **risk:** MEDIUM–HIGH — every current consumer must be re-expressed as an
  adapter; the `DUPLICATE_INTERPRETER` / `MAGIC_PRIORITY` / `SEMANTIC_OVERLOAD`
  / `SINGLE_VALUE_BOTTLENECK` smells are resolved by construction.
- **complexity:** HIGH (new layer + N adapters + parity tests).
  **migration:** none for data; API can stay identical behind adapters.
  **test burden:** HIGH initially, LOWER long-term (one place to reason
  about meaning).
- **back-compat:** HIGH-safe *if* adapters are exact (needs a golden-output
  parity suite against current behavior). **Compass:** isolated *if* the
  `purpose`→`need_tag` adapter is preserved verbatim.
- **maintainability:** best long-term; single source of semantic truth; kills
  the three-table drift.
- **Decision 5 alignment:** the canonical layer carries `{value, confidence,
  polarity}` per signal, so it naturally supports
  `NEGATION_MODEL = POLARITY_SIGNAL`, and is the option in which
  `NEGATION_MODEL = CLAUSE_LEVEL_MODEL` (polarity/scope attached at the
  clause level) becomes feasible.

### Option D — Hybrid: normalize the *container*, defer the *model*

Do the minimal normalization from Option B's prerequisite (one need
extractor; consistent `{primary, candidates[], confidence, polarity}` block
shape; rename the colliding keys) **and add a first-class polarity field to
the normalized interpretation profile, populated by a lightweight
Concierge-side parser / preprocess step** — but do **not** promote the
profile to ranking yet. Keep Score v3 shadow. Wire the normalized profile
(polarity included) into reason_v4 and a new `reason_fact` type only.

- **Decision 5 alignment:** Option D uses `NEGATION_MODEL = POLARITY_SIGNAL`.
  The polarity field is **first-class and retained downstream** (reason_v4
  and the new `reason_fact` type can inspect it). The parser / preprocess
  step is **only the producer** of that signal — it is not a
  `PREPROCESS_GUARD`, because polarity is preserved as structured semantic
  data rather than consumed as pre-extraction suppression.
- **effort:** MEDIUM. **fidelity:** MEDIUM (negation + state visible in the
  explanation as structured data; ranking unchanged → low ranking risk).
- **risk:** LOW–MEDIUM (no ranking change; additive schema). **migration:**
  none. **back-compat:** HIGH-safe (additive). **Compass:** reason_v4 shared
  → MEDIUM; ranking untouched → LOW.
- **positions for later:** leaves Option B (flip Score v3) or Option C
  (full canonical layer) as a clean next step on a consistent base — and the
  polarity signal is already in place for either.

*No option is selected. No option is ranked as product priority.*

---

## 19. Decision Criteria Comparison

Scale: ✅ strong / �observed-neutral / ⚠ weak-or-risky (evidence-based, not scored).

| criterion | A Preserve | B Promote | C Normalize | D Hybrid |
|---|---|---|---|---|
| 1. semantic fidelity | ⚠ ceiling at single-container; negation via `PREPROCESS_GUARD` suppression only (no structured polarity) | ✅ state/outcome load-bearing; negation only if schema extended (`PREPROCESS_GUARD` or `POLARITY_SIGNAL`) | ✅ topic/state/intention/polarity separated (`POLARITY_SIGNAL`/`CLAUSE_LEVEL_MODEL`) | ○ explanation-only fidelity now; negation as structured `POLARITY_SIGNAL` (retained downstream), ranking unchanged |
| 2. reuse of tested behavior | ✅ maximal | ✅ high (Score v3 weights, reason_v4 exist) | ⚠ re-expressed via adapters | ✅ high |
| 3. backward compatibility | ✅ | ⚠ ranking + fact types shift | ✅ if adapters exact (needs parity suite) | ✅ additive |
| 4. complexity | ✅ low | ○ medium | ⚠ high | ○ medium |
| 5. hidden coupling risk | ⚠ 3-table drift & overload remain | ○ need-list unify required first | ✅ resolved by construction | ○ partially resolved |
| 6. testability | ✅ | ○ (needs Score v3 activation + parity tests) | ⚠ large parity suite upfront | ○ |
| 7. incremental rollout safety | ✅ | ○ (env/flag + A/B observation exists) | ⚠ big-bang unless adapter-gated | ✅ |
| 8. Compass isolation | ✅ (guard is Concierge-only) | ⚠ shared ranking + profile | ○ isolated if `purpose` adapter preserved | ○ ranking untouched |
| 9. Reason compatibility | ○ (legacy branch to add) | ○ (fact-type extension) | ✅ (adapter) | ✅ (v4 + one fact type) |
| 10. data/mapping migration | ✅ none | ✅ none | ✅ none (adapters) | ✅ none |
| 11. rollback safety | ✅ | ○ (env flip back; fact types linger in analytics) | ○ (feature-flag the layer) | ✅ |
| 12. maintainability | ⚠ smells persist | ○ fewer, some remain | ✅ single source of truth | ○ improved base |

---

## 20. Mother Ship Decision Packet

Evidence for each decision is in the cited sections. **No value is selected.**

**Decision 1 — `SEMANTIC_CORE_STRATEGY`** ∈ {`PRESERVE_CURRENT`,
`PROMOTE_PROFILE`, `NORMALIZE_MODEL`, `OTHER`}.
Evidence: §1, §9, §11, §18, §19. The carriers are reusable; the model is
overloaded (§11). Negation is unrepresentable in every option except a new
field (§13). Option D (§18) is the low-risk base that keeps B and C open.

**Decision 2 — `NEED_TAG_ROLE`** ∈ {`PRIMARY_SEMANTIC_MODEL`,
`EVIDENCE_ROUTING_LAYER`, `COMPATIBILITY_LAYER`, `OTHER`}.
Evidence: §6, §9, §11, §15. `need_tag` is a good routing key (tested, shared,
deterministic) and a poor semantic model (topic + state + intention in one
list, no polarity). Compass `purpose` pins it to an API contract (§15).

**Decision 3 — `CONSULTATION_AXIS_ROLE`** ∈ {`KEEP_CURRENT`, `DERIVED_ONLY`,
`MULTI_VALUE_FUTURE`, `DEPRECATE_CANDIDATE`}.
Evidence: §12, L6, L7. It adds exactly one thing `need_tag` cannot (the
`history_theme` boost key), is single-valued, and flips on secondary tokens.
`DEPRECATE_CANDIDATE` only viable if the `history_theme` boost is re-sourced.

**Decision 4 — `INTERPRETATION_PROFILE_ROLE`** ∈ {`SHADOW`, `PROMOTE`,
`NORMALIZE_FIRST`, `DEPRECATE_CANDIDATE`}.
Evidence: §4, §7, §10, §17. It is already half-promoted (reason_v4 detail
ships to the response; Score v3 consumes it) and deterministic, but has a
divergent second need extractor (L15), inconsistent block shapes, and
colliding names. `PROMOTE` as-is would route ranking on the wrong need list.

**Decision 5 — `NEGATION_MODEL`** ∈ {`NO_CHANGE`, `PREPROCESS_GUARD`,
`POLARITY_SIGNAL`, `CLAUSE_LEVEL_MODEL`}.
Evidence: §13 / §13.1 / §13.2, L1, PR #2646 §10/§17 (6/34 cases). Nothing
today can carry polarity (§13). Value definitions:

- `NO_CHANGE` — leave the current negation limitation unresolved; the 6/34
  mis-fire cases persist.
- `PREPROCESS_GUARD` — schema-free suppression / correction of keyword /
  regex matches **before** semantic extraction; no polarity field, nothing
  carried downstream (§13.1). Concierge-side; blunt but low-risk.
- `POLARITY_SIGNAL` — a first-class structured polarity signal that is
  **retained downstream** and inspectable by Reason / explanation / future
  ranking (§13.1); needs one field plus at least one consumer. May be
  produced by a lightweight parser without becoming a `PREPROCESS_GUARD`.
- `CLAUSE_LEVEL_MODEL` — clause-aware semantic interpretation where polarity
  and scope are attached at the clause or per-signal level; a larger
  architecture change (Option C-scale).

**Decision 6 — `MULTI_SIGNAL_POLICY`** ∈ {`KEEP_MAX3_PRIORITY`,
`EXPAND_LIST`, `PRIMARY_SECONDARY`, `STRUCTURED_MULTI_DIMENSION`}.
Evidence: §14, L2, L3, L6, L8, L11. `max_tags=3`, `NEED_PRIORITY`, the single
axis, and the GID union are four independent destructive reducers.
`PRIMARY_SECONDARY` needs a rationale field; `STRUCTURED_MULTI_DIMENSION` is
Option C.

**Cross-decision dependencies:**

- D1=`PRESERVE_CURRENT` (Option A) ⇒ D4=`SHADOW`, D6∈{`KEEP_MAX3_PRIORITY`};
  D5 pairs with `PREPROCESS_GUARD` (schema-free suppression — Option A adds
  no polarity field).
- D1=`PROMOTE_PROFILE` (Option B) ⇒ D4∈{`PROMOTE`, `NORMALIZE_FIRST`} and
  requires L15 fixed; D5 may be `PREPROCESS_GUARD` **or** `POLARITY_SIGNAL`
  depending on whether the profile schema is extended with a polarity field.
- D1=`NORMALIZE_MODEL` (Option C) ⇒ D2=`EVIDENCE_ROUTING_LAYER`,
  D3∈{`DERIVED_ONLY`,`MULTI_VALUE_FUTURE`},
  D5∈{`POLARITY_SIGNAL`,`CLAUSE_LEVEL_MODEL`}, D6=`STRUCTURED_MULTI_DIMENSION`.
- **Option D (Hybrid) ⇒ D5=`POLARITY_SIGNAL`** — a first-class polarity field
  is added to the normalized profile and retained downstream; the
  parser / preprocess step is only its producer, not a `PREPROCESS_GUARD`.
  D4=`NORMALIZE_FIRST`, ranking unchanged, D6 unconstrained.
- D5=`NO_CHANGE` leaves the 6/34 negation cases unaddressed regardless of D1.

---

## 21. Final Audit Verdict

```text
CONSULTATION_ARCHITECTURE_AUDIT_STATUS = COMPLETE

EXISTING_MODEL_REUSE_STATUS      = REUSE_WITH_NORMALIZATION
   (carriers — need_tag as routing key, consultation_axis as derived view,
    interpretation_profile as input, reason_facts as extensible — are
    reusable; the semantic MODEL needs a normalization step: one need
    extractor, consistent block shape, a polarity field, de-collided names)

INTERPRETATION_PROFILE_STATUS    = PROMOTABLE_AFTER_NORMALIZATION
   (deterministic, stable schema, already wired to translate_meaning /
    reason_v4 / Score v3; blockers to as-is promotion: dual need extraction
    L15, no negation/polarity, inconsistent primary-vs-list shape, name
    collisions)

NEED_TAG_CAPACITY_STATUS         = SEMANTIC_OVERLOAD + MODEL_CAPACITY_LIMIT
   (one 15-value list carries topic + state + intention; structurally cannot
    hold polarity, multi-state, or primary/secondary-with-reason;
    NOT vocabulary-only, NOT mapping-only)

CONSULTATION_AXIS_STATUS         = DERIVED_FRAMING_PLUS_RANKING_ROUTER / SINGLE_VALUE_BOTTLENECK
   (partial duplicate of need_tag; sole unique contribution is the
    history_theme_candidate_boost key; single-valued, flips on secondary tokens)

NEGATION_CAPACITY_STATUS         = NOT_REPRESENTABLE
   (no field in any current object; no consumer; not REPRESENTABLE_BUT_UNUSED)

MULTI_SIGNAL_CAPACITY_STATUS     = LIST_WITH_DESTRUCTIVE_REDUCERS
   (need_tags[] up to 3 + NEED_PRIORITY + single axis + GID union;
    primary/secondary is positional only, no capacity beyond 3, no rationale)

EXPLANATION_COMPATIBILITY_STATUS = ADAPTER_SUFFICIENT_FOR_STATE_INTENTION /
                                   REASON_SCHEMA_EXTENSION_REQUIRED_FOR_FACTS /
                                   ARCHITECTURE_CHANGE_REQUIRED_FOR_NEGATION
   (recommendation_reason_v4 already renders state/decision/constraint/outcome;
    legacy reason/Lead and reason_facts/primary_reason ignore them and have no
    polarity slot)

BLOCKERS = 0
   (no code evidence of a blocker to a Mother Ship decision or to a scoped
    implementation; the required work is bounded, not open-ended)
```

**Reuse sufficient?** For the *routing and explanation carriers* — yes,
with extension. **Redesign required?** For the *semantic model* — a
normalization step is required before `interpretation_profile` can be
promoted to ranking or before negation/multi-dimension can be represented;
a full canonical layer (Option C) is *optional*, not forced by the evidence.

---

## Appendix A — Method / Reproducibility

- Code read at `origin/develop` `334bd876` (PR #2646 merge). Semantic files
  confirmed unchanged since the PR #2646 audits (last-touch commits all
  pre-#2643).
- **Pure-function diagnostics** (no DB, no behavior change, repo venv
  `/Users/morietsu/Developer/jinja_app/.venv`, Django 5.2.16,
  `USE_GIS=0 USE_SQLITE=1`): confirmed the three keyword tables and their
  drift; `interpret_consultation` determinism (identical output ×3) and
  9-key schema; `translate_meaning` output; `need_profile` vs
  `extract_need_tags` divergence.
- **Focused tests:** `NOT_RUN` — the local `test_jinja_db` / `jinja_db` is in
  a broken state (`must be owner of database test_jinja_db` on recreate;
  closed cursor on `--reuse-db`; 69 setup errors). Per task §24, shared
  infrastructure was not repaired. Branch-PR CI (`unit` + `integration`)
  exercises `test_consultation_interpreter.py`, `test_meaning_translation.py`,
  `test_need_to_goriyaku_tag_ids.py`, `test_concierge_input_contract.py`,
  `test_recommendation_reason_v4.py`, `test_recommendation_score_components.py`,
  `test_recommendation_input_profile.py`, `test_recommendation_algorithm_v3.py`.
- `git diff --check`: clean. Only this file added.
- No DB write, no Production access, no Spreadsheet access, no migration.
