# D1 — Semantic Core Strategy Decision Audit

> **Status: DECISION-COMPARISON AUDIT — READ-ONLY.** Produces evidence-backed
> comparison material for **D1 `SEMANTIC_CORE_STRATEGY`** ∈
> {`PRESERVE_CURRENT`, `PROMOTE_PROFILE`, `NORMALIZE_MODEL`, `OTHER`}.
> **No D1 value is selected. No D2–D6 value is selected. No option is
> ranked or marked "recommended". No FREE/Premium decision is made. No
> runtime / interpreter / taxonomy / mapping / evidence / scoring / ranking
> / Lead / Reason / API / frontend / Compass / entitlement / migration
> change is made or proposed for implementation.**
>
> Base `origin/develop` = `5b273f7fcdb0e98e373f0f0c1d4590300d374785`
> (PR #2647 merge commit). Branch `audit/semantic-core-strategy-decision`.
>
> Primary inputs: `docs/audit/recommendation-nuance-quality-audit.md`
> (PR #2646, canonical 34-case matrix + failure model) and
> `docs/audit/consultation-understanding-architecture-audit.md` (PR #2647,
> canonical architecture audit, L1–L16, Decision Packet). Topic / State /
> Intention are **audit / candidate semantic dimensions**, not adopted
> production taxonomy.

---

## 1. Executive Summary

The current semantic core is `need_tag` (a 15-value flat list) plus a
single-valued `consultation_axis`; `interpretation_profile` is computed on
every request but is shadow / display-only (it reaches the response only as
pre-rendered `recommendation_reason_v4_detail` text and feeds Score v3 which
is shadow by default). This was re-confirmed against `develop` `5b273f7f` —
**no `temples/` code changed since PR #2647's audit base**; every finding
below is a fresh read.

Three strategies were evaluated across the **34 canonical consultation
cases**, six semantic dimensions (Topic / State / Intention / Polarity /
Primary-Secondary / Contrast), and nine downstream concerns.

- **`PRESERVE_CURRENT`** — semantic core stays `need_tag` + current
  `consultation_axis`; `interpretation_profile` stays shadow; no new
  first-class dimension, no polarity. It **cannot** represent Polarity (0/6)
  or Contrast (0/6) at all, represents State only by overloading `mental`
  (0 FULL / 10 PARTIAL / 11 LOST of 21), and represents Primary/Secondary
  only positionally (0 FULL / 6 PARTIAL / 8 LOST of 14). Cost LOW, risk LOW,
  Compass impact LOW, ranking change NONE_REQUIRED — and **no semantic
  fidelity is gained by leaving ranking unchanged**.
- **`PROMOTE_PROFILE`** — reuse the existing `interpretation_profile` as the
  semantic carrier **after the normalization PR #2647 requires** (one need
  extractor, consistent block shape, de-collided names). With the **current**
  profile fields it lifts State to 8 FULL / 4 PARTIAL / 9 LOST and Intention
  to 5 FULL / 19 PARTIAL / 8 LOST, and makes Primary/Secondary mostly
  explicit (0 FULL / 11 PARTIAL / 3 LOST). Polarity and Contrast remain
  **LOST unless the profile schema is extended** (`NORMALIZED_PROFILE_EXTENSION`).
  Cost MEDIUM, schema change MEDIUM, interpreter change MEDIUM, ranking change
  NONE_REQUIRED for schema adoption — **Score v3 activation is optional, not
  required**.
- **`NORMALIZE_MODEL`** — a canonical `consultation_semantics` representation
  (`topic[]` / `state[]` / `intention[]` / `polarity` / `decision` /
  `constraints`) sits before Need/Evidence routing, with adapters preserving
  every current output. It **can** preserve every dimension for every
  applicable case (representational capacity: Topic 26/26, State 21/21,
  Intention 32/32, Polarity 6/6, Primary/Secondary 14/14, Contrast 6/6) —
  with the explicit caveat that this measures **representational capacity,
  not parser accuracy**. Cost HIGH, schema change HIGH (mitigated to MEDIUM
  if adapter-gated with a parity suite), ranking change NONE_REQUIRED for
  adoption — **NORMALIZE_MODEL does not require immediate ranking
  replacement**.

**Semantic schema and ranking are independent axes** and are evaluated
separately throughout (§21). `PROMOTE_PROFILE` ≠ Score v3 activation;
`NORMALIZE_MODEL` ≠ ranking rewrite; `PREPROCESS_GUARD` ≠ `POLARITY_SIGNAL`
(§9, §22, reconciled with PR #2647 §13).

`SEMANTIC_CORE_STRATEGY_AUDIT_STATUS = COMPLETE`. `BLOCKERS = 0`.
`MOTHER_SHIP_D1_STATUS = DECISION_REQUIRED`. Full verdict in §16.

---

## 2. Scope and Method

- **In scope:** comparison material for D1 only. Re-confirmation of the
  runtime semantic path; a 34-case × 3-strategy × 6-dimension retention
  matrix; L1–L16 impact per strategy; schema vs interpreter vs ranking vs
  evidence vs explanation vs Compass impact per strategy; cost and risk
  evidence; a neutral Mother Ship D1 Decision Packet; D1→D2–D6 dependency
  reconciliation.
- **Not in scope / prohibited:** selecting D1 or any D2–D6 value; ranking
  A/B/C; "recommended" language; FREE/Premium design; any implementation;
  any runtime, schema, taxonomy, mapping, evidence, scoring, ranking, Lead,
  Reason, API, frontend, Compass, or entitlement change; migrations;
  Production or Spreadsheet writes.
- **Retention classification** (per case × strategy × dimension):
  `FULL` = the strategy's semantic representation preserves the distinction
  explicitly and deterministically enough for downstream use;
  `PARTIAL` = some meaning survives but one or more distinctions are
  collapsed, inferred indirectly, or depend on an overloaded field;
  `LOST` = the distinction is not represented after the strategy's semantic
  reduction; `NOT_APPLICABLE` = the case does not contain that dimension.
  A dimension is **not** `FULL` merely because `raw_query` is retained.
- **Runtime re-confirmed** at `develop` `5b273f7f`: `git log 334bd876..HEAD
  -- temples/` is empty — only docs PRs #2646/#2647 merged since the PR #2647
  audit base. The PR #2647 AS-IS model, L1–L16, and Decision Packet stand
  unchanged; file-by-file last-touch commits are all pre-#2643.

---

## 3. Re-Confirmed Current Runtime Semantic Path (source of truth)

| stage | symbol / file | load-bearing? | carries |
|---|---|---|---|
| free text in | `query` via `normalize_concierge_request` (`concierge_input_contract.py`) | yes | raw string; `goriyaku_tag_ids`, `extra_condition`, `visit_preferences`, `birthdate`. **No structured "consultation theme" field.** |
| need extraction (runtime) | `extract_need_tags` (`domain/need_tags.py`) via `resolve_need_payload` (`concierge_chat_need.py`) | **yes** | `need_tags` ≤3, `KEYWORDS` ∪ `REGEX`, `NEED_PRIORITY` order, `max_tags=3` |
| need extraction (shadow) | `build_need_profile` → `NEED_KEYWORDS` (`consultation_interpreter.py`) | no | `interpretation_profile.need_profile.need_tags` — **a second, drifted table** (`前に進`, `悩み`, `迷い`, `考えすぎ`, `生活費`, `一人`, `学び`, `スキル` are shadow-only — re-verified) |
| need extraction (fallback) | `extract_need_fallback` → `NEED_SYNONYMS` (6 needs) | no (except try/except path) | third keyword table |
| axis | `resolve_consultation_axis` (`domain/consultation_axis.py`) | **yes** (ranking, via boost only) | `consultation_axis` — 1 of 9; keyword-then-need_tag-fallback |
| rich profile | `interpret_consultation` (`consultation_interpreter.py`) | **shadow / display** | `state_profile`, `need_profile`, `direction_profile`, `emotion_profile`, `action_intent`, `decision_context`, `constraint_profile`, `outcome_hint` |
| meaning translation | `translate_meaning` (`meaning_translation.py`) | shadow / display | `history_theme`, `history_theme_secondary`, `shrine_context_need`, `action_context`, `reflection_question_seed` |
| evidence routing | `need_tags_to_goriyaku_ids` → `NEED_TO_GORIYAKU_IDS` (`domain/need_to_goriyaku_tag_ids.py`) | **yes** | per-need GID set → union |
| candidate gen | `build_chat_candidates` (`concierge_chat_candidates.py`) | **yes** | filters by **user-picked** `goriyaku_tag_ids` only; else popularity pool |
| scoring | `_attach_breakdown` / `_prefilter_candidates_for_need` (`concierge_chat_ranking.py`); `recommendation_score_v2.py` | **yes** | `score_need` = channel count; C1 Max; `score_need_rank_weighted` |
| Score v3 | `recommendation_score_components.py` via `build_recommendation_input_profile` | **shadow** (`SCORE_V3_MODE` unset → `"shadow"`; re-verified) | `state_match_score` (wt 0.45), `meaning_match_score`, `history_score` — consumes `interpretation_profile` |
| sort | `_sort_chat_recommendations` (`concierge_chat.py`) | **yes** | `resolve_score_sort_key` → `_score_total` (v2) unless `SCORE_V3_MODE=active` |
| Reason / Lead (legacy) | `build_recommendation_reason` / `_build_need_lead` / `reason_facts` / `_resolve_primary_reason` (`concierge_chat_ranking.py`) | **yes** | `need_tag`-driven; generic fallback |
| Reason v4 | `recommendation_reason_v4.py` via `_attach_recommendation_reason_quality` (`concierge_chat.py`) | **display (reaches response)** | `rec["recommendation_reason_v4_detail"]` — `_build_interpretation` consumes `state_profile` / `decision_context` / `constraint_profile` / `outcome_hint` (re-verified, file unchanged since 2026-08-13) |
| response boundary | `_build_chat_response` (`api_views_concierge.py`) | — | `data.pop("_debug")` — strips `interpretation_profile`; keeps `rec["reason"]` + `rec["recommendation_reason_v4_detail"]` |
| Compass | `api_views_compass.py` → `compass_recommendation_orchestrator.get_compass_recommendations` (both unchanged since 2026-08-23) | — | own HTTP view; **calls `interpret_consultation`, `build_chat_candidates`, `build_chat_recommendations`** with `query=""`, `need_tags=[purpose]`; `purpose` must be one of `NEED_TAGS` |

---

## 4. The Canonical 34 Consultation Cases

Reconstructed verbatim from `docs/audit/recommendation-nuance-quality-audit.md`
§15. Group counts verified: **Career 6, Love 5, Family 4, Mental/Rest 4,
Negation 5, Theme 3, Other 7 → 34.** No case invented; each appears exactly
once in every strategy matrix (§7–§9). No discrepancy found vs the merged
source.

| id | input | audit-expected meaning | current `need_tags` |
|---|---|---|---|
| Career-A | 転職して新しい環境に進みたい | career + forward intent | `['career']` |
| Career-B | 転職したいけど一歩踏み出すのが怖い | career + fear/hesitation (contrast) | `['career','courage']` |
| Career-C | 今の仕事を続ける自信がなくなってきた | career + loss of confidence | `['career','mental']` |
| Career-D | 仕事が忙しくて気持ちが落ち着かない | career context + wants calm | `['career','rest']` |
| Career-E | 仕事に集中できない | career + focus problem | `['career','focus']` |
| Career-F | 職場の人間関係がうまくいかない | workplace-relationship strain | `['relationship']` |
| Love-A | 新しい出会いがほしい | love + seek-new | `['love']` |
| Love-B | 今の恋人との関係を大切にしたい | love + nurture-existing | `['love']` |
| Love-C | 結婚について迷っている | marriage + indecision | `['marriage']` |
| Love-D | 好きな人に気持ちを伝える勇気がほしい | love/communication + courage-to-act | `['communication','courage']` |
| Love-E | 別れた人のことを引きずっていて気持ちを整理したい | grief + closure | `[]` |
| Family-A | 家族が穏やかに過ごせたらいい | family wellbeing / harmony | `['relationship','rest']` |
| Family-B | 子どものことが心配 | family (child) + worry | `[]` |
| Family-C | 出産を控えていて不安 | family (childbirth) + anxiety | `['family','mental']` |
| Family-D | 家族との関係で悩んでいる | family-relationship strain | `['relationship']` |
| MR-A | 最近ずっと気持ちが落ち着かない | restlessness / unsettled | `['rest']` |
| MR-B | 何もしたくないくらい疲れている | exhaustion | `['mental','rest']` |
| MR-C | 少し立ち止まって休みたい | pause / rest | `['rest']` |
| MR-D | 不安はあるけど前に進みたい | anxiety (contrast) + move-forward | `['mental']` |
| Neg-1 | 恋愛の相談ではない | love **negated** | `['love']` |
| Neg-2 | 転職したいわけではない | career **negated** | `['career']` |
| Neg-3 | 不安ではないけど迷っている | anxiety **negated**, indecision asserted (contrast) | `['mental']` |
| Neg-4 | 結婚より今は仕事を優先したい | career primary, marriage **de-emphasised** (contrast) | `['marriage','career']` |
| Neg-5 | 休みたいというより環境を変えたい | change-env asserted, rest **contrasted-away** | `['rest']` |
| Theme-1 | 新しい仕事に挑戦したい | career + challenge | `['career','courage']` |
| Theme-2 | 最近疲れていて少し休みたい | fatigue + rest | `['mental','rest']` |
| Theme-3 | 恋愛より仕事のことで悩んでいます | career primary, love **de-emphasised** (contrast) | `['love','career']` |
| Money-A | もっと稼ぎたい | money + increase | `['money']` |
| Study-A | 資格試験に合格したい | study/exam | `['study']` |
| Travel-A | 家族旅行の安全を祈願したい | travel safety (+ family modifier) | `['relationship','travel_safe']` |
| Health-A | 健康で長生きしたい | health / longevity | `['health']` |
| Protect-A | 最近流れが悪いのでお祓いしたい | protection + bad-flow state | `['protection','mental']` |
| Courage-A | 背中を押してほしい | encouragement / push | `['courage']` |
| Focus-A | 集中力を高めて勉強を継続したい | focus + persist + study | `['study','focus']` |

**Dimension applicability (denominators).** A dimension counts only when the
case genuinely contains it (§8 `NOT_APPLICABLE` rule):

| dimension | applicable cases | count |
|---|---|---|
| **Topic** | all except MR-A/B/C/D, Neg-3, Neg-5, Theme-2, Courage-A | **26** |
| **State** | Career-B/C/D/E/F, Love-C/D/E, Family-B/C/D, MR-A/B/C/D, Neg-3/5, Theme-2/3, Protect-A, Courage-A | **21** |
| **Intention** | all except Neg-1, Neg-2 (pure negations with no positive intent stated) | **32** |
| **Polarity** (signal negation / de-emphasis) | Neg-1, Neg-2, Neg-3, Neg-4, Neg-5, Theme-3 | **6** |
| **Primary / Secondary** | Career-B/C/D/E, Love-D/E, Family-C, MR-D, Neg-3/4/5, Theme-3, Travel-A, Protect-A | **14** |
| **Contrast / de-emphasis** (`けど` / `より` / `というより`) | Career-B, MR-D, Neg-3, Neg-4, Neg-5, Theme-3 | **6** |

Percentages in §15 always show numerator / denominator against these, never
against 34.

---

## 5. Strategy Definitions Used (evidence-locked)

### 5.1 `PRESERVE_CURRENT` (§9)

- Load-bearing semantic model stays centred on `need_tag(s)`.
- `consultation_axis` stays in its current single-value framing +
  `history_theme_candidate_boost` role.
- `max_tags=3` / `NEED_PRIORITY` behaviour unchanged.
- `interpretation_profile` stays shadow / explanatory-only (it is already
  connected to `recommendation_reason_v4_detail` on the response — that
  connection is not removed, but nothing new is wired).
- **No new first-class semantic dimension. No polarity field.** Ranking and
  evidence-routing contracts intact.
- `PREPROCESS_GUARD` is **not** automatically part of this strategy; it is a
  separate, optional, schema-free compatibility mitigation (§9, PR #2647
  §13.1) and is not credited to `PRESERVE_CURRENT` here.
- Not credited with any capability it does not currently have.

### 5.2 `PROMOTE_PROFILE` (§10) — evaluate `PROMOTABLE_AFTER_NORMALIZATION`

- The existing `interpretation_profile` becomes the semantic carrier **after**
  the normalization PR #2647 identifies as a prerequisite: one need
  extractor (fix L15), consistent `{primary, candidates[], confidence}` block
  shape, de-collided names (`direction_profile`, `themes`, `need_profile`).
- The already-present richer blocks (`state_profile`, `outcome_hint`,
  `decision_context`, `constraint_profile`, `action_intent`) may become
  load-bearing.
- **Polarity is not present today** and is not assumed. Where a result needs
  it, the audit distinguishes `CURRENT_PROFILE` (base strategy) from
  `NORMALIZED_PROFILE_EXTENSION` (an explicit profile-schema extension adding
  a polarity field + producer).
- Existing Need / GID / ranking architecture is **adapted**, not replaced.
- This is **not** "promote the current profile unchanged" and **not**
  `NORMALIZE_MODEL`.

### 5.3 `NORMALIZE_MODEL` (§11)

- A dedicated canonical consultation semantic representation is introduced
  **before** Need / Evidence routing. Candidate architectural dimensions
  (not adopted taxonomy): `topic[]`, `state[]`, `intention[]`, `polarity`,
  `decision`, `constraints`; per-signal `{value, confidence, polarity,
  emphasis}`.
- Adapters project it into the existing `need_tag` / `GoriyakuTag` / ranking
  contracts; every current output is preserved behind the adapter.
- It does **not** automatically mean: replace ranking, replace `need_tag`,
  activate every dimension in scoring, change Compass behaviour, or perform
  an LLM rewrite. **Semantic representation is separated from downstream
  activation** throughout.
- Evaluated for **representational capacity** (per §8 / §14): can a
  normalized representation preserve the distinction. Parser detection
  accuracy for open-ended vocabulary is a **separate** question and is
  flagged wherever a `FULL` rests on it.

---

## 6. How Each Dimension Fares Per Strategy (mechanism, before the case matrix)

| dimension | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` (CURRENT_PROFILE) | `NORMALIZE_MODEL` (capacity) |
|---|---|---|---|
| **Topic** | `need_tag` topic-flavoured tags; collapses (家族→relationship, workplace→relationship, focus↔study); `FULL` on clean topic, `PARTIAL` on collapse, `LOST` when no tag fires | same `need_tag` granularity via `need_profile`; marginal gains from shadow vocab; **same classification as PRESERVE** at base (a `NORMALIZED_PROFILE_EXTENSION` topic-subtype could lift `PARTIAL`s) | `topic[]` with per-item polarity + emphasis; workplace/family/romantic distinguishable by value or qualifier → `FULL` representationally for all applicable (taxonomy enum = D2, out of scope) |
| **State** | one overloaded tag (`mental`); no distinct state field load-bearing → never `FULL`; `PARTIAL` when it lands as `mental`/`rest`, else `LOST` | `state_profile.primary_state` ∈ {tired, anxious, uncertain, stuck, ready_to_change} + `secondary_states[]` + `confidence`, made load-bearing → `FULL` when a `STATE_KEYWORDS` bucket fires, `LOST` where no bucket exists (自信 / 落ち着かない / 引きずる / 流れが悪い have no bucket) | `state[]`, multiple explicit states with confidence → `FULL` representationally for all applicable; bucket gaps become a parser-vocabulary question, not a representational one |
| **Intention** | intention-flavoured tags (`courage`/`rest`/`focus`) + topic-implied goals → never `FULL`; `PARTIAL` when one of those fires, `LOST` otherwise (decide / move-forward w/o 一歩 / change-env / nurture-vs-seek / closure) | `outcome_hint` {decide, calm, move_forward, clarify} + `action_intent` + `decision_context`, made load-bearing → `FULL` where `OUTCOME_KEYWORDS` fires (catches MR-D 前に進, Courage-A 背中, Love-E 整理, MR-A/Career-D 落ち着), else `PARTIAL`/`LOST` | `intention[]`, multiple explicit → `FULL` representationally for all applicable |
| **Polarity** | no field, no consumer; `PREPROCESS_GUARD` excluded from this strategy → **`LOST` for all 6** | no polarity field in `CURRENT_PROFILE` → **`LOST` for all 6**; `NORMALIZED_PROFILE_EXTENSION` (field + producer) → `PARTIAL`–`FULL` | `polarity` per signal (asserted / negated / de-emphasised / contrasted) → `FULL` for all 6 |
| **Primary / Secondary** | positional `need_tags[0]` / static `NEED_PRIORITY`, capped at 3, no rationale; `PARTIAL` when priority order matches user emphasis, `LOST` when inverted or when the primary signal is a state (dropped) | `primary_state` + `secondary_states[]` explicit for state; `primary_need_tag` + list positional for topic/intention; after normalization consistent `{primary, candidates[]}` → mostly `PARTIAL` (both signals visible, cross-block emphasis implicit); `LOST` for topic-vs-topic (Neg-4, Theme-3) | per-signal `emphasis` role, cross-block → `FULL` for all 14 |
| **Contrast / de-emphasis** | no representation → **`LOST` for all 6** | no contrast field in `CURRENT_PROFILE`; `decision_candidates[]` lists options but not the relation → **`LOST` for all 6**; `NORMALIZED_PROFILE_EXTENSION` → `PARTIAL`–`FULL` | contrast/relation link between signals (or `decision.conflict`) → `FULL` for all 6 |

---

## 7. 34-Case Evaluation — `PRESERVE_CURRENT`

`Ev` = evidence-routing usability, `Ex` = explanation usability, `IL` =
information-loss posture. `–` = `NOT_APPLICABLE`.

| case | Topic | State | Inten | Polar | Pri/Sec | Contr | Ev | Ex | IL | rationale (evidence) |
|---|---|---|---|---|---|---|---|---|---|---|
| Career-A | FULL | – | LOST | – | – | – | PARTIAL | PARTIAL | unchanged | `['career']` clean; "進みたい" forward-intent has no runtime vocab (`courage` REGEX = 踏み出す/動き出, not 進みたい) so the intent is dropped |
| Career-B | FULL | LOST | PARTIAL | – | PARTIAL | LOST | PARTIAL | PARTIAL | unchanged | career fires; fear "怖い" not in any table → state LOST; `courage` from 踏み出す carries the challenge-intent but is priority-mixed and blows the GID union to 10; "けど" contrast unrepresented |
| Career-C | FULL | PARTIAL | LOST | – | LOST | – | PARTIAL | PARTIAL | unchanged | `mental` fires on bare 自信 → valence survives as generic mental (wrong-concept GIDs); the state is the point but `need_tags[0]=career` inverts primacy |
| Career-D | FULL | PARTIAL | PARTIAL | – | LOST | – | PARTIAL | PARTIAL | unchanged | "落ち着かない" lands as `rest` (an intention tag), not a state; calm-need survives as a rest tag; career-first order inverts the real primary (the state) |
| Career-E | FULL | LOST | PARTIAL | – | PARTIAL | – | PARTIAL | PARTIAL | unchanged | `focus` fires; "集中できない" negated-capability not modelled; axis flips to `study_success` (L6); both signals present, order acceptable |
| Career-F | PARTIAL | LOST | LOST | – | – | – | PARTIAL | LOST | unchanged | workplace-relationship collapsed to `relationship`→`{縁結び}`; "うまくいかない" (no 最近) does not fire `mental`; repair-intent unrepresented |
| Love-A | FULL | – | LOST | – | – | – | PARTIAL | PARTIAL | unchanged | `love` topic clean; "seek-new" vs generic love not distinguished (no intention field) |
| Love-B | FULL | – | LOST | – | – | – | PARTIAL | PARTIAL | unchanged | identical `['love']` to Love-A; "nurture-existing" nuance collapsed |
| Love-C | FULL | LOST | LOST | – | – | – | PARTIAL | PARTIAL | unchanged | `marriage` topic clean; "迷っている" indecision has no runtime vocab (`迷` is shadow-only) → state + decide-intent both LOST |
| Love-D | LOST | LOST | PARTIAL | – | PARTIAL | – | LOST | PARTIAL | unchanged | topic `love` not surfaced (tags `communication`+`courage`); `communication` GID empty; courage carries the act-intent loosely; axis `restart_mindset` |
| Love-E | LOST | LOST | LOST | – | LOST | – | LOST | LOST | unchanged | `need_tags=[]` — total miss; grief + closure both unrepresented; axis `other` |
| Family-A | PARTIAL | – | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | 家族→`relationship`; "family harmony" has no home; "穏やか"→`rest` carries a wish-for-peace proxy |
| Family-B | LOST | LOST | LOST | – | – | – | LOST | LOST | unchanged | `need_tags=[]`; 心配 not in runtime `KEYWORDS` → worry + protect-intent both LOST |
| Family-C | FULL | PARTIAL | PARTIAL | – | PARTIAL | – | PARTIAL | PARTIAL | unchanged | `family`→`{安産,子宝}` serves safe-birth (primary); `mental` from 不安 carries the anxiety layer (secondary), wrong-concept GIDs |
| Family-D | PARTIAL | LOST | LOST | – | – | – | PARTIAL | LOST | unchanged | family-relationship collapsed to `relationship`→`{縁結び}`; "悩んでいる" not in runtime `mental` → state + resolve-intent LOST |
| MR-A | – | PARTIAL | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | no life-domain topic; "落ち着かない" lands as `rest` (intention), the unsettled state and the calm-want both carried loosely by one tag |
| MR-B | – | PARTIAL | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `mental`+`rest` fire on 疲れ; exhaustion valence survives, mapped to wrong-concept GIDs |
| MR-C | – | PARTIAL | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `rest` fires on 休みたい; pause-intent carried, state weak |
| MR-D | – | PARTIAL | LOST | – | LOST | LOST | PARTIAL | PARTIAL | unchanged | only `['mental']` (from 不安); "前に進みたい" is shadow-only → the **primary** signal (move-forward) is entirely lost; the "けど" contrast unrepresented |
| Neg-1 | PARTIAL | – | – | LOST | – | – | PARTIAL | LOST | unchanged | 恋愛 matched inside "…ではない" → `['love']` asserted; the domain is identified but framed as positive; **negation unrepresentable** |
| Neg-2 | PARTIAL | – | – | LOST | – | – | PARTIAL | LOST | unchanged | 転職 matched inside "…わけではない" → `['career']`; negation LOST |
| Neg-3 | – | LOST | LOST | LOST | LOST | LOST | PARTIAL | LOST | unchanged | matched the **negated** 不安 → `['mental']`; asserted 迷い has no runtime vocab; polarity, contrast, indecision, primary all LOST |
| Neg-4 | PARTIAL | – | PARTIAL | LOST | LOST | LOST | PARTIAL | LOST | unchanged | 結婚 matched despite "より" → `['marriage','career']`; `NEED_PRIORITY` puts marriage first, **inverting** the stated primary; de-emphasis + contrast LOST; axis → `relationship_repair` |
| Neg-5 | – | PARTIAL | LOST | LOST | LOST | LOST | PARTIAL | LOST | unchanged | matched the de-emphasised 休みたい → `['rest']`; asserted "環境を変えたい" absent; contrast + change-intent LOST |
| Theme-1 | FULL | – | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `career`+`courage`; challenge-intent carried by `courage`, GID union to 10 |
| Theme-2 | – | PARTIAL | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `mental`+`rest` on 疲れ; fatigue + rest carried loosely |
| Theme-3 | PARTIAL | LOST | LOST | LOST | LOST | LOST | PARTIAL | LOST | unchanged | 恋愛 matched despite "より" → `['love','career']`, love first → primary inverted; "悩んでいます" not in runtime `mental`; de-emphasis + contrast LOST |
| Money-A | FULL | – | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `money` clean; "もっと"/increase not represented but domain routes well (商売繁盛/金運) |
| Study-A | FULL | – | PARTIAL | – | – | – | FULL | PARTIAL | unchanged | `study` + study text bonus; intention ≈ topic here and well-routed (学業成就/合格祈願) |
| Travel-A | PARTIAL | – | PARTIAL | – | PARTIAL | – | PARTIAL | PARTIAL | unchanged | `travel_safe` present but `relationship` co-fires on 家族 and takes axis; travel-primary vs family-modifier positionally inverted |
| Health-A | FULL | – | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `health` topic clean; axis `other` (no producer); 家内安全 dominates the GID reach |
| Protect-A | FULL | PARTIAL | PARTIAL | – | PARTIAL | – | PARTIAL | PARTIAL | unchanged | `protection`→`{厄除け}` strong; `mental` co-fires on 流れが悪い; protection-primary matches order |
| Courage-A | – | LOST | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `courage` fires on 背中を押して; scattered GID map; underlying hesitation state unrepresented |
| Focus-A | FULL | – | PARTIAL | – | – | – | PARTIAL | PARTIAL | unchanged | `study`+`focus`; focus + persist collapsed to the study evidence path |

**`PRESERVE_CURRENT` aggregate** (see §15 for the reconciled table):
Topic 15 FULL / 8 PARTIAL / 3 LOST (26); State 0 / 10 / 11 (21); Intention
0 / 19 / 13 (32); Polarity 0 / 0 / 6 (6); Primary/Secondary 0 / 6 / 8 (14);
Contrast 0 / 0 / 6 (6). No L1–L16 point is mitigated or resolved.

---

## 8. 34-Case Evaluation — `PROMOTE_PROFILE`

Carrier field named for every non-`LOST` cell. `CP` = the capability rests
on a **current** `interpretation_profile` field; `EXT` = it needs a
`NORMALIZED_PROFILE_EXTENSION` (new field/vocab) — credited only with the
dependency stated.

| case | Topic | State | Inten | Polar | Pri/Sec | Contr | carrier / dependency |
|---|---|---|---|---|---|---|---|
| Career-A | FULL | – | LOST | – | – | – | `need_profile` topic; forward-intent not in `OUTCOME_KEYWORDS` ("進みたい"≠"前に進") → LOST `CP` (EXT: add 進みたい → FULL) |
| Career-B | FULL | **FULL** | PARTIAL | – | PARTIAL | LOST `CP` | `state_profile.primary_state=anxious` (STATE_KEYWORDS 怖) `CP`; challenge via `courage` need_tag; contrast has no field `CP` |
| Career-C | FULL | LOST `CP` | LOST | – | LOST | – | 自信 in no `STATE_KEYWORDS` bucket → `primary_state=None` (EXT: add 自信 → FULL state + PARTIAL P/S) |
| Career-D | FULL | LOST `CP` | **FULL** | – | PARTIAL `CP` | – | 落ち着 in no state bucket, but `outcome_hint.primary_outcome=calm` (OUTCOME_KEYWORDS 落ち着) `CP` carries the intention; calm-intent primary + career secondary both visible, cross-block emphasis implicit |
| Career-E | FULL | LOST `CP` | PARTIAL | – | PARTIAL | – | no state bucket; `focus` need_tag; axis flip (L6) unchanged |
| Career-F | PARTIAL | LOST `CP` | LOST | – | – | – | workplace-relationship still collapsed; うまくいかない in no bucket (EXT for state) |
| Love-A | FULL | – | LOST | – | – | – | seek-new not in `OUTCOME_KEYWORDS` (EXT) |
| Love-B | FULL | – | LOST | – | – | – | nurture-existing not representable `CP` (EXT) |
| Love-C | FULL | **FULL** | PARTIAL | – | – | – | `state_profile.primary_state=uncertain` (STATE_KEYWORDS 迷) `CP`; `decision_context` carries decide-intent `CP` |
| Love-D | LOST | LOST `CP` | PARTIAL | – | PARTIAL | – | topic `love` still not surfaced; 勇気 in no bucket; `courage`+`communication` need_tags carry the act loosely |
| Love-E | LOST | LOST `CP` | **FULL** | – | PARTIAL | – | `outcome_hint.primary_outcome=clarify` (OUTCOME_KEYWORDS 整理) `CP` — closure captured; grief itself has no bucket (EXT) |
| Family-A | PARTIAL | – | PARTIAL | – | – | – | 家族→relationship unchanged; 穏やか→`rest` need_tag |
| Family-B | LOST | **FULL** | LOST | – | – | – | `state_profile.primary_state=anxious` (STATE_KEYWORDS **心配**) `CP` — the state now lands even though `need_tags` is still `[]` |
| Family-C | FULL | **FULL** | PARTIAL | – | PARTIAL | – | `family` need_tag + `state_profile=anxious` (不安) `CP`; safe-birth primary via need_tag, anxiety as explicit secondary state |
| Family-D | PARTIAL | PARTIAL `CP` | LOST | – | – | – | family-relationship collapsed; `state_profile=uncertain` (STATE_KEYWORDS 悩) approximates the distress |
| MR-A | – | LOST `CP` | **FULL** | – | – | – | 落ち着 in no state bucket; `outcome_hint=calm` `CP` carries the want (EXT for the unsettled state) |
| MR-B | – | **FULL** | PARTIAL | – | – | – | `state_profile=tired` (STATE_KEYWORDS 疲れ) `CP`; `rest` need_tag for the intention |
| MR-C | – | PARTIAL `CP` | PARTIAL | – | – | – | `state_profile=tired` via 休み `CP` (weak — 休み is an intention token in that bucket); `rest` need_tag |
| MR-D | – | **FULL** | **FULL** | – | PARTIAL | LOST `CP` | `state_profile=anxious` (不安) **and** `outcome_hint=move_forward` (前に進) both `CP` — the case `PRESERVE_CURRENT` loses entirely is now two explicit signals; their contrast has no field `CP` |
| Neg-1 | PARTIAL | – | – | LOST `CP` | – | – | domain via `need_profile`; **no polarity field** `CP` (EXT + producer → PARTIAL) |
| Neg-2 | PARTIAL | – | – | LOST `CP` | – | – | as Neg-1 |
| Neg-3 | – | **FULL** | PARTIAL | LOST `CP` | PARTIAL | LOST `CP` | `state_profile=uncertain` (迷) `CP` captures the **asserted** indecision as the primary signal; the negated 不安 and the contrast still need EXT |
| Neg-4 | PARTIAL | – | PARTIAL | LOST `CP` | LOST `CP` | LOST `CP` | `need_profile` still positional → marriage-first; de-emphasis / contrast / cross-topic primacy all need EXT |
| Neg-5 | – | PARTIAL `CP` | PARTIAL `CP` | LOST `CP` | PARTIAL `CP` | LOST `CP` | `state_profile.secondary=ready_to_change` (STATE_KEYWORDS 変えたい) `CP` surfaces the change-intent; rest is de-emphasised (needs EXT) |
| Theme-1 | FULL | – | PARTIAL | – | – | – | `courage` need_tag; challenge not in `OUTCOME_KEYWORDS` |
| Theme-2 | – | **FULL** | PARTIAL | – | – | – | `state_profile=tired` (疲れ) `CP`; `rest` need_tag |
| Theme-3 | PARTIAL | PARTIAL `CP` | LOST | LOST `CP` | LOST `CP` | LOST `CP` | `state_profile=uncertain` (悩) `CP`; love-first positional; de-emphasis + contrast need EXT |
| Money-A | FULL | – | PARTIAL | – | – | – | `money` need_tag; "もっと" not represented |
| Study-A | FULL | – | PARTIAL | – | – | – | `study` need_tag + text bonus |
| Travel-A | PARTIAL | – | PARTIAL | – | PARTIAL | – | `relationship` co-fire unchanged; both topics in `need_profile` list |
| Health-A | FULL | – | PARTIAL | – | – | – | `health` need_tag; axis `other` unchanged |
| Protect-A | FULL | LOST `CP` | PARTIAL | – | PARTIAL | – | 流れが悪い in no `STATE_KEYWORDS` bucket → state LOST `CP` (EXT); `protection` need_tag primary |
| Courage-A | – | LOST `CP` | **FULL** | – | – | – | `outcome_hint=move_forward` (OUTCOME_KEYWORDS 背中) `CP`; hesitation state has no bucket (EXT) |
| Focus-A | FULL | – | PARTIAL | – | – | – | `study`+`focus` need_tags |

**`PROMOTE_PROFILE` aggregate (CURRENT_PROFILE baseline):**
Topic 15 / 8 / 3 (26); State **8 FULL** / 4 PARTIAL / 9 LOST (21);
Intention **5 FULL** / 19 PARTIAL / 8 LOST (32); Polarity 0 / 0 / 6 (6) —
`NORMALIZED_PROFILE_EXTENSION` moves this to `PARTIAL`–`FULL`;
Primary/Secondary 0 / **11 PARTIAL** / 3 LOST (14); Contrast 0 / 0 / 6 (6) —
`NORMALIZED_PROFILE_EXTENSION` moves this to `PARTIAL`–`FULL`.
`EXT` notes mark 9 State and several Intention `LOST` cells that a
state/intention-vocabulary extension would lift.

---

## 9. 34-Case Evaluation — `NORMALIZE_MODEL`

Per §8 / §14 this measures **representational capacity** of a canonical
`consultation_semantics` layer, not parser accuracy. `FULL` = the layer can
hold the distinction explicitly; the caveat is repeated in §15.

| case | Topic | State | Inten | Polar | Pri/Sec | Contr | note (what the representation holds) |
|---|---|---|---|---|---|---|---|
| Career-A | FULL | – | FULL | – | – | – | `topic=[career]`, `intention=[advance]` |
| Career-B | FULL | FULL | FULL | – | FULL | FULL | `topic=[career:primary]`, `state=[fear]`, `intention=[step_forward]`, contrast(fear ⟂ step_forward) |
| Career-C | FULL | FULL | FULL | – | FULL | – | `state=[confidence_low:primary]`, `topic=[career:context]` |
| Career-D | FULL | FULL | FULL | – | FULL | – | `state=[unsettled:primary]`, `intention=[calm]`, `topic=[career:context]` |
| Career-E | FULL | FULL | FULL | – | FULL | – | `topic=[career]`, `intention=[focus:primary]`, `state=[scattered]` |
| Career-F | FULL | FULL | FULL | – | – | – | `topic=[relationship{workplace}]`, `state=[strained]`, `intention=[repair]` |
| Love-A | FULL | – | FULL | – | – | – | `intention=[seek_new]` distinct from Love-B |
| Love-B | FULL | – | FULL | – | – | – | `intention=[nurture_existing]` distinct from Love-A |
| Love-C | FULL | FULL | FULL | – | – | – | `topic=[marriage]`, `state=[undecided]`, `intention=[decide]` |
| Love-D | FULL | FULL | FULL | – | FULL | – | `topic=[love/communication]`, `state=[courage_low]`, `intention=[confess:primary]` |
| Love-E | FULL | FULL | FULL | – | FULL | – | `topic=[love{past}]`, `state=[grief:primary]`, `intention=[closure]` |
| Family-A | FULL | – | FULL | – | – | – | `topic=[family{wellbeing}]`, `intention=[wish_peace]` |
| Family-B | FULL | FULL | FULL | – | – | – | `topic=[family{child}]`, `state=[worry]`, `intention=[protect]` |
| Family-C | FULL | FULL | FULL | – | FULL | – | `topic=[family{childbirth}:primary]`, `state=[anxiety:secondary]` |
| Family-D | FULL | FULL | FULL | – | – | – | `topic=[relationship{family}]`, `state=[distress]`, `intention=[resolve]` |
| MR-A | – | FULL | FULL | – | – | – | `state=[restless:primary]`, `intention=[calm]` |
| MR-B | – | FULL | FULL | – | – | – | `state=[exhaustion:primary]`, `intention=[rest]` |
| MR-C | – | FULL | FULL | – | – | – | `state=[depleted]`, `intention=[pause]` |
| MR-D | – | FULL | FULL | – | FULL | FULL | `state=[anxiety:secondary]`, `intention=[move_forward:primary]`, contrast link |
| Neg-1 | FULL | – | – | FULL | – | – | `topic=[love: polarity=negated]` |
| Neg-2 | FULL | – | – | FULL | – | – | `topic=[career: polarity=negated]` |
| Neg-3 | – | FULL | FULL | FULL | FULL | FULL | `state=[anxiety: polarity=negated]`, `state=[indecision: asserted, primary]`, contrast |
| Neg-4 | FULL | – | FULL | FULL | FULL | FULL | `topic=[career: asserted, primary]`, `topic=[marriage: polarity=de-emphasised]`, contrast |
| Neg-5 | – | FULL | FULL | FULL | FULL | FULL | `intention=[change_env: primary]`, `intention=[rest: polarity=contrasted-away]`, contrast |
| Theme-1 | FULL | – | FULL | – | – | – | `topic=[career]`, `intention=[challenge]` |
| Theme-2 | – | FULL | FULL | – | – | – | `state=[fatigue]`, `intention=[rest]` |
| Theme-3 | FULL | FULL | FULL | FULL | FULL | FULL | `topic=[career: primary]`, `topic=[love: de-emphasised]`, `state=[distress]`, `intention=[resolve]`, contrast |
| Money-A | FULL | – | FULL | – | – | – | `topic=[money]`, `intention=[increase]` |
| Study-A | FULL | – | FULL | – | – | – | `topic=[study]`, `intention=[pass_exam]` |
| Travel-A | FULL | – | FULL | – | FULL | – | `topic=[travel_safe: primary]`, `topic=[family: modifier]` |
| Health-A | FULL | – | FULL | – | – | – | `topic=[health]`, `intention=[longevity]` |
| Protect-A | FULL | FULL | FULL | – | FULL | – | `topic=[protection: primary]`, `state=[bad_flow]`, `intention=[purify]` |
| Courage-A | – | FULL | FULL | – | – | – | `state=[hesitation]`, `intention=[encouragement]` |
| Focus-A | FULL | – | FULL | – | – | – | `topic=[study]`, `intention=[focus, persist]` |

**`NORMALIZE_MODEL` aggregate (representational capacity):**
Topic 26 FULL / 0 / 0 (26); State 21 / 0 / 0 (21); Intention 32 / 0 / 0 (32);
Polarity 6 / 0 / 0 (6); Primary/Secondary 14 / 0 / 0 (14); Contrast 6 / 0 / 0
(6). **Caveat (mandatory):** these are `FULL` for *representational
capacity*. Whether a lightweight producer can reliably *populate* every
`state[]` / `intention[]` value from free text is a separate parser-quality
question; the six `polarity` / `contrast` cases rest on lexically detectable
markers (`ない` / `ではない` / `わけではない` / `より` / `というより` / `けど`)
and are the most defensible; open-ended state/intention detection accuracy
is **not** claimed here.

---

## 10. Dimension Retention Summary (aggregate, per strategy)

Numerator / denominator shown against §4 applicability, never against 34. No
single headline "meaning-retention %".

### Topic — denominator 26

| | FULL | PARTIAL | LOST | FULL rate |
|---|---|---|---|---|
| `PRESERVE_CURRENT` | 15 | 8 | 3 | 15/26 = 58% |
| `PROMOTE_PROFILE` (CP) | 15 | 8 | 3 | 15/26 = 58% (EXT topic-subtype could lift the 8 PARTIAL) |
| `NORMALIZE_MODEL` (capacity) | 26 | 0 | 0 | 26/26 = 100% (representational) |

### State — denominator 21

| | FULL | PARTIAL | LOST | FULL rate |
|---|---|---|---|---|
| `PRESERVE_CURRENT` | 0 | 10 | 11 | 0/21 = 0% |
| `PROMOTE_PROFILE` (CP) | 8 | 4 | 9 | 8/21 = 38% (EXT state-vocab lifts most of the 9 LOST) |
| `NORMALIZE_MODEL` (capacity) | 21 | 0 | 0 | 21/21 = 100% (representational) |

### Intention — denominator 32

| | FULL | PARTIAL | LOST | FULL rate |
|---|---|---|---|---|
| `PRESERVE_CURRENT` | 0 | 19 | 13 | 0/32 = 0% |
| `PROMOTE_PROFILE` (CP) | 5 | 19 | 8 | 5/32 = 16% (EXT lifts several LOST) |
| `NORMALIZE_MODEL` (capacity) | 32 | 0 | 0 | 32/32 = 100% (representational) |

### Polarity — denominator 6

| | FULL | PARTIAL | LOST |
|---|---|---|---|
| `PRESERVE_CURRENT` | 0 | 0 | 6 |
| `PROMOTE_PROFILE` — `CURRENT_PROFILE` | 0 | 0 | 6 |
| `PROMOTE_PROFILE` — `NORMALIZED_PROFILE_EXTENSION` | (0–6) | (variable) | (0–6) — depends on the added field + producer |
| `NORMALIZE_MODEL` (capacity) | 6 | 0 | 0 |

### Primary / Secondary — denominator 14

| | FULL | PARTIAL | LOST |
|---|---|---|---|
| `PRESERVE_CURRENT` | 0 | 6 | 8 |
| `PROMOTE_PROFILE` (CP) | 0 | 11 | 3 |
| `NORMALIZE_MODEL` (capacity) | 14 | 0 | 0 |

### Contrast / de-emphasis — denominator 6

| | FULL | PARTIAL | LOST |
|---|---|---|---|
| `PRESERVE_CURRENT` | 0 | 0 | 6 |
| `PROMOTE_PROFILE` — `CURRENT_PROFILE` | 0 | 0 | 6 |
| `PROMOTE_PROFILE` — `NORMALIZED_PROFILE_EXTENSION` | (0–6) | (variable) | (0–6) |
| `NORMALIZE_MODEL` (capacity) | 6 | 0 | 0 |

---

## 11. Information-Loss L1–L16 Comparison

L1–L16 definitions are quoted verbatim from `docs/audit/consultation-understanding-architecture-audit.md`
§8 and are **not** redefined. Legend: `unchanged` / `mitigated` (behaviour
improved, not eliminated) / `structurally resolved` (the mechanism no longer
exists) / `still unresolved`.

| loss point | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| L1 `KEYWORDS`/`REGEX` substring, clause structure lost | unchanged | unchanged (clause parsing not required by the base strategy) | mitigated **iff** a clause-aware producer is adopted; else unchanged (the representation can hold clause-scoped polarity, the parser is separate) |
| L2 `max_tags=3` truncation | unchanged | mitigated (`secondary_states[]` / `candidates[]` uncapped for state/decision; `need_tags` still ≤3 for GID routing) | structurally resolved (`topic[]`/`state[]`/`intention[]` uncapped; the adapter down-projects to ≤3 need_tags only at the routing boundary) |
| L3 `NEED_PRIORITY` fixed order | unchanged | mitigated (profile records primary vs secondary explicitly for state/decision; need_tag list still priority-ordered for routing) | structurally resolved (emphasis explicit per signal; static priority, if used, lives inside the adapter) |
| L4 `NEED_TAG_ALIASES` ×2 collapse | unchanged | mitigated (normalization unifies the alias tables) | structurally resolved (aliases confined to one adapter) |
| L5 `resolve_need_payload` skips free text when tags passed | unchanged | unchanged | unchanged (same Concierge-free-text / Compass-tags boundary) |
| L6 `consultation_axis` single-value | unchanged | unchanged unless axis is made multi-value (a D3 choice, not required) | structurally resolved **iff** axis becomes a derived multi-value view; else unchanged |
| L7 axis need_tag fallback order | unchanged | unchanged | resolved iff axis is derived; else unchanged |
| L8 `need_tags_to_goriyaku_ids` union (per-tag identity lost) | unchanged | mitigated (adapter can weight/scope per detected topic-intention) | mitigated (adapter maps per canonical signal; union still at the GID-set boundary but provenance retained upstream) |
| L9 candidate pool: no Need filter on free-text path | unchanged | unchanged (candidate gen not required to change) | unchanged (optional soft-boost is a separate ranking decision) |
| L10 `score_need` = channel count | unchanged | unchanged unless Score v3 is activated (optional) | unchanged unless ranking integration is chosen (separate decision) |
| L11 `_resolve_primary_reason` single winner; no state/intention fact type | unchanged | mitigated (state/intention citable via reason_v4; a `reason_fact` type extension needed for the legacy primary-reason path) | mitigated (canonical signals + new fact types; primary reason can be a state / intention / polarity — needs the fact-type extension) |
| L12 `_build_need_lead` fallback chain | unchanged | mitigated (Lead can read state/intention) | mitigated (Lead adapter can cite a canonical signal) |
| L13 `build_recommendation_reason` generic fallback | unchanged | mitigated | mitigated |
| L14 `interpretation_profile` → `_debug` pop | unchanged (profile stays `_debug`) | structurally resolved (the profile *is* the semantic carrier and is exposed) | structurally resolved (canonical semantics is the carrier, exposed by design) |
| L15 `need_profile` vs `extract_need_tags` divergence | unchanged (both still exist) | structurally resolved (one need extractor — the explicit normalization prerequisite) | structurally resolved (one canonical producer) |
| L16 `state_profile.confidence` single scalar | unchanged | mitigated (per-signal confidence is a normalization/EXT step) | structurally resolved (per-signal `{value, confidence}`) |

Count summary — points **structurally resolved**: `PRESERVE` 0, `PROMOTE`
2 (L14, L15), `NORMALIZE` 6 (L2, L3, L4, L14, L15, L16). Points **mitigated**:
`PRESERVE` 0, `PROMOTE` ~7 (L2, L3, L4, L11, L12, L13, L16), `NORMALIZE` ~7
(L1‑cond, L6‑cond, L7‑cond, L8, L11, L12, L13). Points **still unresolved**
under every strategy: **L5, L9, L10** (all three depend on separate
candidate-generation / ranking decisions, not on D1).

---

## 12. Primary / Secondary / Contrast Capacity (four probe inputs)

Per §17, evaluated on the six sub-abilities. `Y` / `partial` / `N`.

### `結婚より今は仕事を優先したい` (Neg-4)

| sub-ability | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` (CP) | `NORMALIZE_MODEL` |
|---|---|---|---|
| multiple signals detected | Y (`['marriage','career']`) | Y (`need_profile`) | Y |
| primary signal identified | N (`NEED_PRIORITY` picks **marriage**, inverting the stated primary) | N (still positional) | Y (`emphasis=primary` on career) |
| secondary signal retained | partial (marriage present but as co-equal tag) | partial | Y (`emphasis=secondary` on marriage) |
| negated signal retained | – (this is de-emphasis, not negation) | – | – |
| de-emphasised signal retained | N | N (needs EXT) | Y (`polarity=de-emphasised` on marriage) |
| contrast relation retained | N | N (needs EXT) | Y (contrast link) |

### `転職したいけど一歩踏み出すのが怖い` (Career-B)

| sub-ability | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` (CP) | `NORMALIZE_MODEL` |
|---|---|---|---|
| multiple signals detected | Y (`['career','courage']`) | Y (+ `state_profile=anxious`) | Y |
| primary signal identified | partial (career first — matches, but by static priority) | partial | Y |
| secondary signal retained | partial (fear as `courage` tag, not a state) | Y (fear as explicit `state=anxious`) | Y (`state=[fear]`) |
| negated signal retained | – | – | – |
| de-emphasised signal retained | – | – | – |
| contrast relation retained | N | N (no contrast field CP) | Y |

### `不安ではないけど迷っている` (Neg-3)

| sub-ability | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` (CP) | `NORMALIZE_MODEL` |
|---|---|---|---|
| multiple signals detected | N (only `['mental']`, from the **negated** word) | partial (`state=uncertain` from 迷 **and** `mental` need_tag) | Y |
| primary signal identified | N (indecision absent) | Y (`primary_state=uncertain`) | Y |
| secondary signal retained | N | partial (the negated 不安 → `mental` need_tag, wrong sign) | Y |
| negated signal retained | N | N (needs EXT) | Y (`polarity=negated` on anxiety) |
| de-emphasised signal retained | – | – | – |
| contrast relation retained | N | N (needs EXT) | Y |

### `休みたいというより環境を変えたい` (Neg-5)

| sub-ability | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` (CP) | `NORMALIZE_MODEL` |
|---|---|---|---|
| multiple signals detected | N (only `['rest']`, the de-emphasised want) | partial (`rest` need_tag + `state.secondary=ready_to_change` from 変えたい) | Y |
| primary signal identified | N (change-env absent) | partial (`ready_to_change` surfaces it) | Y (`intention=[change_env: primary]`) |
| secondary signal retained | N | partial (rest present but not marked de-emphasised) | Y |
| negated signal retained | – | – | – |
| de-emphasised signal retained | N | N (needs EXT) | Y (`polarity=contrasted-away` on rest) |
| contrast relation retained | N | N (needs EXT) | Y |

A flat list of multiple `need_tags` is **not** equivalent to structured
multi-signal representation: it lacks emphasis roles, polarity, and any
contrast relation, and it is capped at 3 (§6, L2, L3).

---

## 13. Change-Size Classifications

### 13.1 Semantic Schema Change (§18)

| factor | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| new fields / structures | none | reshape `interpretation_profile` to consistent `{primary, candidates[], confidence}` blocks; polarity field only under EXT | new `consultation_semantics` object + per-signal `{value, confidence, polarity, emphasis}` |
| adapter needs | none (optional: de-gate one reason_fact) | thin: `need_profile.need_tags` → existing `need_tag` map; reason_v4 already wired | many: `consultation_semantics` → `need_tag(s)` → GID; → axis view; → reason_v4; → Score v3 input |
| duplicate extractor cleanup | none | **required** (3 keyword tables → 1; L15) | required (one canonical producer) |
| schema compatibility | full | additive-safe for consumers; **key renames break** `test_consultation_interpreter.py` + reason_v4 + Score v3 | full behind exact adapters; needs a golden-output parity suite |
| API compatibility | unchanged | `interpretation_profile` is `_debug`-only today; exposing it as the carrier adds a response field; `rec` reason fields unchanged | unchanged behind adapters (API can stay identical) |
| migration need | none | **none** (in-memory object + response payload; thread payloads persist `recommendations`, not the profile) | **none** (in-memory representation; no persisted schema) |
| serialization impact | none | new/renamed profile keys in the response and observability logs | new object in observability / `_debug`; adapters keep the public body stable |
| **classification** | **LOW** | **MEDIUM** (HIGH only if a polarity extension + response exposure are bundled in) | **HIGH** (MEDIUM if adapter-gated with a parity suite) |

### 13.2 Runtime Interpreter Change (§19) — independent of schema

| factor | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| keyword extractor consolidation | none | **3 → 1** (`KEYWORDS`+`REGEX` vs `NEED_KEYWORDS` vs `NEED_SYNONYMS`) | 1 canonical producer |
| regex ownership | unchanged | decide single owner during consolidation | single owner |
| normalization | none | block-shape + naming normalization | inherent to the model |
| clause parsing | none | **not required** by the base strategy | enabled by the representation, **not forced** (a lightweight marker producer suffices for the §12 inputs) |
| polarity parsing | none | none at base; a producer only under EXT | a lightweight producer populates `polarity` from `ない/ではない/より/けど/というより`; deep clause polarity is optional |
| priority / `max_tags` behaviour | unchanged | unchanged for routing (still ≤3 need_tags out) | moves into the adapter; the model itself is uncapped |
| raw-query preservation | unchanged (`raw_query` kept) | unchanged | unchanged |
| `interpret_consultation` producer | unchanged | becomes the single producer | replaced by / wraps the canonical producer |
| **classification** | **LOW** | **MEDIUM** | **MEDIUM–HIGH** (representation change is large; parser change can stay lightweight) |

### 13.3 Implementation Cost Breakdown (§25) — decision evidence only, no choice implied

| sub-area | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| semantic model | LOW | MEDIUM | HIGH |
| interpreter | LOW | MEDIUM | MEDIUM–HIGH |
| adapters | LOW | LOW–MEDIUM | HIGH |
| evidence routing | LOW | LOW | LOW–MEDIUM |
| ranking (schema-adoption mode) | LOW | LOW | LOW |
| explanation | LOW–MEDIUM (optional legacy branch) | MEDIUM (fact-type ext + wiring) | MEDIUM (fact-type ext + adapter) |
| tests | LOW | MEDIUM (extractor parity, reason ext, optional Score v3 activation) | HIGH (golden-output parity across every consumer) |
| Compass regression surface | LOW | MEDIUM (shared schema + reason_v4) | MEDIUM (adapter discipline) |
| documentation | LOW | MEDIUM | HIGH |
| **overall** | **LOW** | **MEDIUM** | **HIGH** |

---

## 14. Evidence Routing, Ranking Separation, Explanation, Compass

### 14.1 Evidence Routing (§20)

`need_tag → NEED_TO_GORIYAKU_IDS → reviewed goriyaku_tags` (Recommendation
Evidence). Knowledge-Fact correctness stays separate from Recommendation
eligibility; **no strategy weakens the evidence contract or infers GID from
deity / history / tradition.**

| strategy | routing contract | note |
|---|---|---|
| `PRESERVE_CURRENT` | **unchanged** | capped by current mapping quality (`mental`/`rest` wrong-concept, `communication` empty, borrowed maps — #2646); no strategy here fixes that (it is #2646 denominator C, a data project) |
| `PROMOTE_PROFILE` | **adapter required** (trivial) | `need_profile.need_tags` → same map after unification; L15 ambiguity removed; mapping quality unchanged |
| `NORMALIZE_MODEL` | **adapter required** | `consultation_semantics → need_tag(s) → GID`; the adapter *can* choose a better need_tag per topic/intention, but the 39-tag master's gaps still cap the ceiling |

### 14.2 Ranking Separation (§21) — mandatory

Two independent modes evaluated for every strategy.

| strategy | Mode A: schema adopted, ranking unchanged | Mode B: richer signals progressively integrated into ranking |
|---|---|---|
| `PRESERVE_CURRENT` | `NONE_REQUIRED` | not applicable — there are no richer load-bearing signals to integrate without *becoming* `PROMOTE_PROFILE`; **`PRESERVE_CURRENT` gains no semantic fidelity by leaving ranking unchanged** |
| `PROMOTE_PROFILE` | `NONE_REQUIRED` — the profile can be load-bearing for explanation/observability while `_score_total` / `_sort_chat_recommendations` stay on Score v2 | `OPTIONAL` → `ADAPTER_REQUIRED`: flip `SCORE_V3_MODE=active` (already consumes the profile, weights pre-tuned, guarded by the existing `score_v3_ab_observation`); **not** a structural rewrite; **`PROMOTE_PROFILE` does not require Score v3 activation** |
| `NORMALIZE_MODEL` | `NONE_REQUIRED` — the adapter emits the same `need_tags` the ranker already consumes | `OPTIONAL` → `ADAPTER_REQUIRED`: feed canonical signals into a scoring adapter; Score v2 and any v3 coexist behind the mode switch; **`NORMALIZE_MODEL` does not require immediate ranking replacement** |

`SEMANTIC_RANKING_SEPARATION_STATUS = CONFIRMED`.

### 14.3 Explanation / Reason (§22) — re-checked on `develop` `5b273f7f`

`recommendation_reason_v4._build_interpretation` still consumes
`state_profile` / `decision_context` / `constraint_profile` / `outcome_hint`
(file unchanged since 2026-08-13). PR #2647's finding stands: **state /
intention → adapter-sufficient for reason_v4; facts → reason-schema
extension required; negation → architecture change required.**

| consumer | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| legacy Lead (`_build_need_lead`) | schema-ext or a new branch to read state | adapter (profile load-bearing) | adapter |
| legacy Reason (`build_recommendation_reason`) | same | adapter | adapter |
| `reason_facts` / `_resolve_primary_reason` | **reason-schema extension** for a state/intention/polarity fact type | reason-schema extension | reason-schema extension |
| `recommendation_reason_v4` | **adapter-sufficient** for state/intention (already renders them); polarity needs the signal upstream → **architecture change** | adapter-sufficient for state/intention; polarity only under EXT | adapter-sufficient; polarity native (then a fact-type ext for the legacy path) |
| `recommendation_reason_v4_detail` (in response) | unchanged | carries richer state/intention once the profile is load-bearing | carries canonical signals via adapter |

### 14.4 Compass Shared-Contract Impact (§23)

Concierge-only vs shared, re-verified at `5b273f7f`:

| element | classification |
|---|---|
| free-text interpretation (`query`, `extract_need_tags`, `KEYWORDS`/`REGEX`, non-empty `interpret_consultation`) | **Concierge-only** (Compass sends `query=""`, `purpose = one need_tag`) |
| `NEED_TAGS` set | **shared** (Compass validates `purpose in NEED_TAGS`) |
| `NEED_TO_GORIYAKU_IDS` | **shared** |
| candidate generation (`build_chat_candidates`) | **shared** |
| ranking (`_attach_breakdown` / `_sort_chat_recommendations`) | **shared** |
| Reason / Lead / `reason_facts` | **shared** |
| `interpretation_profile` / `translate_meaning` / `recommendation_reason_v4` | **shared** (Compass passes a near-empty profile) |
| `consultation_axis` | **shared, different entrypoint** (Compass derives from `purpose`) |
| Compass `purpose` input | **Compass-only**; must remain one of `NEED_TAGS` |

| strategy | semantic-model risk | runtime-behavior risk | overall Compass impact |
|---|---|---|---|
| `PRESERVE_CURRENT` | LOW (nothing shared changes) | LOW (an empty-state legacy Reason branch is a no-op for Compass) | **LOW** |
| `PROMOTE_PROFILE` | MEDIUM (`interpret_consultation` schema is shared; key renames break Compass reason_v4; `NEED_TAGS` set unchanged) | LOW (Compass ranking untouched while Score v3 stays shadow) | **MEDIUM** |
| `NORMALIZE_MODEL` | MEDIUM (the `purpose → need_tag` adapter must be preserved verbatim; `interpret_consultation` can stay a derived view (LOW) or be replaced (MEDIUM)) | LOW (candidate gen / ranking unchanged in Mode A) | **MEDIUM** |

**A richer Concierge semantic model does not require changing Compass
free-text behaviour** — Compass has no free-text entry path. Concierge and
Compass product responsibilities are not merged by any strategy.

### 14.5 FREE / Premium Boundary (§24)

Recorded boundary only: **semantic-understanding quality is evaluated
independently of entitlement.** `PREPROCESS_GUARD`, `POLARITY_SIGNAL`, and
normalized semantics are **not** classified as Premium-only capabilities.
Any FREE / Premium product decision belongs to a separate entitlement task
and is **not** made here.

---

## 15. Migration / Rollout Risk (§26) and 100-User Observability (§28)

### 15.1 Migration / Rollout Risk — schema-adoption vs ranking-activation split

| strategy | schema-adoption risk | ranking-activation risk | drivers |
|---|---|---|---|
| `PRESERVE_CURRENT` | **LOW** | n/a | no schema; rollback trivial; regression scope ≈ the optional Reason branch only |
| `PROMOTE_PROFILE` | **MEDIUM** | **MEDIUM** (separate, env-reversible, `score_v3_ab_observation` guard) | profile reshape touches reason_v4 + Score v3 + response payload + `test_consultation_interpreter.py` schema assertions; `need_profile` unification can shift which tags fire (behaviour drift); Reason dual-system persists |
| `NORMALIZE_MODEL` | **MEDIUM–HIGH** (MEDIUM if adapter-gated behind a flag with a golden-output parity suite; HIGH if adopted big-bang) | **MEDIUM** (same separate, gated decision) | broad consumer surface; back-compat is HIGH-safe *only* if every adapter output is bit-for-bit the current output; Score v2 / v3 coexist; a canonical layer is the most observable / rollback-inspectable |

`schema adoption risk` and `ranking activation risk` are **separate** for
`PROMOTE_PROFILE` and `NORMALIZE_MODEL`; `PRESERVE_CURRENT` has no ranking
activation path.

### 15.2 100-User Test Observability (diagnostic capacity only — no analytics designed)

Can post-test feedback attribute a failure to a layer?

| diagnostic question | `PRESERVE_CURRENT` | `PROMOTE_PROFILE` | `NORMALIZE_MODEL` |
|---|---|---|---|
| understood the **topic**? | partial (`need_tags` logged, but topic is entangled with state/intention) | partial–good (`need_profile` explicit; still tag-granular) | good (`topic[]` explicit) |
| understood the **state**? | poor (only visible if it became `mental`) | good (`state_profile.primary_state` explicit and load-bearing) | good (`state[]` explicit) |
| understood **what the user wanted to do**? | poor (intention entangled in `need_tags`) | good (`outcome_hint` explicit) | good (`intention[]` explicit) |
| misread a **negated** phrase? | not distinguishable (no polarity anywhere) | not distinguishable at base (EXT needed) | distinguishable (`polarity` field) |
| chose the **wrong primary** signal? | hard (positional only) | partial (`primary_state` vs `primary_need_tag` visible) | clear (`emphasis` roles) |
| semantics right but **mapping / evidence** wrong? | partly (compare `need_tags` to GID hits) | partly | clearer (canonical signal vs adapter output vs GID) |
| semantics right but **ranking** poor? | hard (semantics and score conflated) | clearer (profile vs `_score_total` vs Score v3 shadow) | clearest (canonical layer vs adapter vs score) |
| recommendation right but **explanation** weak? | partly (legacy `reason` vs `reason_v4_detail`) | partly | partly (same two-system issue persists until unified) |
| **overall observability** | **LOW–MEDIUM** | **MEDIUM–HIGH** | **HIGH** |

---

## 16. Final Audit Verdict

```text
SEMANTIC_CORE_STRATEGY_AUDIT_STATUS = COMPLETE

PRESERVE_CURRENT_STATUS   = EVALUATED
   (Topic 15/26 FULL; State 0/21 FULL, 10 PARTIAL, 11 LOST;
    Intention 0/32 FULL, 19 PARTIAL, 13 LOST; Polarity 0/6; Contrast 0/6;
    Primary/Secondary 0/14 FULL, 6 PARTIAL, 8 LOST; L1–L16 all unchanged;
    schema LOW / interpreter LOW / cost LOW / risk LOW / Compass LOW;
    ranking Mode A NONE_REQUIRED, no Mode B without becoming PROMOTE_PROFILE)

PROMOTE_PROFILE_STATUS    = EVALUATED
   (PROMOTABLE_AFTER_NORMALIZATION; CURRENT_PROFILE: Topic 15/26 FULL,
    State 8/21 FULL, Intention 5/32 FULL, Primary/Secondary 11/14 PARTIAL;
    Polarity & Contrast LOST unless NORMALIZED_PROFILE_EXTENSION;
    L14 + L15 structurally resolved, ~7 mitigated; schema MEDIUM /
    interpreter MEDIUM / cost MEDIUM / schema-risk MEDIUM /
    ranking-activation-risk MEDIUM / Compass MEDIUM;
    ranking Mode A NONE_REQUIRED — Score v3 activation is OPTIONAL, not required)

NORMALIZE_MODEL_STATUS    = EVALUATED
   (representational capacity: every dimension FULL for every applicable
    case — Topic 26/26, State 21/21, Intention 32/32, Polarity 6/6,
    Primary/Secondary 14/14, Contrast 6/6 — CAVEAT: capacity, not parser
    accuracy; L2/L3/L4/L14/L15/L16 structurally resolved, ~7 mitigated,
    L5/L9/L10 unresolved [separate ranking decisions];
    schema HIGH [MEDIUM if adapter-gated + parity suite] /
    interpreter MEDIUM–HIGH / cost HIGH / schema-risk MEDIUM–HIGH /
    ranking-activation-risk MEDIUM / Compass MEDIUM;
    ranking Mode A NONE_REQUIRED — does NOT require ranking replacement)

SEMANTIC_RANKING_SEPARATION_STATUS = CONFIRMED
   (schema adoption and ranking activation are independent for all three;
    PROMOTE_PROFILE ≠ Score v3 activation; NORMALIZE_MODEL ≠ ranking rewrite)

COMPASS_IMPACT_STATUS     = EVALUATED
   (free-text interpretation is Concierge-only; NEED_TAGS set /
    NEED_TO_GORIYAKU_IDS / ranking / Reason / interpret_consultation schema /
    consultation_axis are shared; PRESERVE LOW, PROMOTE MEDIUM,
    NORMALIZE MEDIUM; semantic-model risk separated from runtime-behavior risk)

MOTHER_SHIP_D1_STATUS     = DECISION_REQUIRED

BLOCKERS = 0
```

**Comparison readiness:** the three strategies are evaluated on the same
34 cases, the same six dimensions with explicit denominators, the same
L1–L16, and schema-vs-ranking kept separate. No blocker prevents a Mother
Ship D1 decision. The undefined canonical taxonomy under `NORMALIZE_MODEL`
(topic/state/intention enums) is a **downstream D2 dependency**, explicitly
out of scope here (§11, §14), **not** a blocker.

---

## 17. Mother Ship D1 Decision Packet

**D1 `SEMANTIC_CORE_STRATEGY`** — neutral summary. **No value selected. No
ranking. No "recommended". No inferred preference.**

### Option A — `PRESERVE_CURRENT`

- **What changes:** nothing structural; at most an optional wiring of an
  already-computed shadow field into the legacy Reason, and/or de-gating one
  `reason_fact`.
- **What stays unchanged:** `need_tag` as the semantic core; single-value
  `consultation_axis`; `max_tags=3` / `NEED_PRIORITY`; `interpretation_profile`
  shadow; evidence routing; ranking; API; Compass.
- **Semantic fidelity:** Topic 15/26 FULL; State 0 FULL; Intention 0 FULL;
  Polarity 0/6; Primary/Secondary 0 FULL; Contrast 0/6. No L-point resolved.
- **Implementation cost:** LOW. **Rollout risk:** LOW (schema) / n/a (ranking).
- **Compass impact:** LOW.
- **Ranking requirement:** `NONE_REQUIRED`; no path to Mode B without
  becoming Option B.
- **Known unresolved gaps:** negation, contrast, distinct state, distinct
  intention, structured primary/secondary, the three-extractor drift (L15),
  the shadow profile (L14) — all remain.

### Option B — `PROMOTE_PROFILE`

- **What changes:** consolidate the 3 need-keyword tables to 1 (L15);
  normalize `interpretation_profile` block shape and names; make
  `state_profile` / `outcome_hint` / `decision_context` load-bearing; wire
  them into reason_v4 (adapter, already partly present) and — with a
  `reason_fact` extension — into the legacy Reason. Polarity/contrast only
  if a `NORMALIZED_PROFILE_EXTENSION` (new field + producer) is included.
- **What stays unchanged:** `need_tag` → GID routing (via adapter); candidate
  generation; ranking (Mode A); Score v2 as the default scorer; `NEED_TAGS`
  set; Compass `purpose` contract.
- **Semantic fidelity (CURRENT_PROFILE):** Topic 15/26 FULL; State 8/21 FULL
  (+4 PARTIAL); Intention 5/32 FULL (+19 PARTIAL); Primary/Secondary 11/14
  PARTIAL; Polarity & Contrast LOST unless EXT. L14, L15 structurally
  resolved; ~7 mitigated.
- **Implementation cost:** MEDIUM. **Rollout risk:** schema MEDIUM,
  ranking-activation MEDIUM (separate, env-reversible, guarded).
- **Compass impact:** MEDIUM (shared `interpret_consultation` schema; renames
  break Compass reason_v4).
- **Ranking requirement:** `NONE_REQUIRED` for adoption; Score v3 activation
  is `OPTIONAL` (Mode B).
- **Known unresolved gaps:** polarity and contrast without an explicit
  profile-schema extension; cross-block primary/secondary emphasis;
  state/intention vocabulary buckets that don't exist (自信, 落ち着かない,
  引きずる, 流れが悪い, seek-vs-nurture, change-env).

### Option C — `NORMALIZE_MODEL`

- **What changes:** a canonical `consultation_semantics` layer
  (`topic[]` / `state[]` / `intention[]` / `polarity` / `decision` /
  `constraints`, per-signal `{value, confidence, polarity, emphasis}`) is
  introduced before Need/Evidence routing; `need_tag` / `consultation_axis` /
  `interpretation_profile` become derived views via adapters; a golden-output
  parity suite guards every current output.
- **What stays unchanged (Mode A):** the public API body; candidate
  generation; ranking; Score v2 default; the evidence contract; Compass
  behaviour (behind a preserved `purpose → need_tag` adapter).
- **Semantic fidelity (representational capacity):** every dimension FULL for
  every applicable case — with the explicit caveat that this is capacity,
  not parser accuracy; the 6 polarity/contrast cases rest on lexically
  detectable markers. L2/L3/L4/L14/L15/L16 structurally resolved; ~7
  mitigated; L5/L9/L10 unresolved (separate ranking/candidate decisions).
- **Implementation cost:** HIGH. **Rollout risk:** schema MEDIUM–HIGH
  (MEDIUM if adapter-gated + parity suite), ranking-activation MEDIUM
  (separate, gated).
- **Compass impact:** MEDIUM (adapter discipline: `purpose → need_tag` must
  be preserved verbatim).
- **Ranking requirement:** `NONE_REQUIRED` for adoption; integration is
  `OPTIONAL` (Mode B).
- **Known unresolved gaps:** the canonical taxonomy enums (D2 dependency,
  out of scope); parser detection accuracy for open-ended state/intention
  vocabulary; the two-Reason-system ambiguity (persists until a separate
  unification); L5/L9/L10 (candidate/ranking decisions independent of D1).

### Option D — `OTHER`

No additional architecture option is surfaced by the code evidence beyond
A / B / C and the PR #2647 "Option D (Hybrid)" (minimal normalization + a
first-class polarity field on the profile, populated by a lightweight
producer, ranking untouched) — which is a **staging path between B and C**
(`NEGATION_MODEL = POLARITY_SIGNAL`), not a distinct semantic-core strategy.
Recorded for completeness; not evaluated as a fourth core strategy.

---

## 18. D1 → D2–D6 Decision Dependencies (reconciled with PR #2647 §20)

**No D2–D6 value is selected.** Which values stay *compatible* with each D1
option:

| downstream decision | if D1 = `PRESERVE_CURRENT` | if D1 = `PROMOTE_PROFILE` | if D1 = `NORMALIZE_MODEL` |
|---|---|---|---|
| **D2 `NEED_TAG_ROLE`** | `PRIMARY_SEMANTIC_MODEL` (unchanged); `EVIDENCE_ROUTING_LAYER` only if a shadow signal is later wired | `EVIDENCE_ROUTING_LAYER` or `COMPATIBILITY_LAYER` (the profile carries meaning; need_tag routes evidence) | `EVIDENCE_ROUTING_LAYER` (the canonical layer carries meaning; need_tag is a derived routing key) |
| **D3 `CONSULTATION_AXIS_ROLE`** | `KEEP_CURRENT` | `KEEP_CURRENT` or `DERIVED_ONLY` | `DERIVED_ONLY` or `MULTI_VALUE_FUTURE` |
| **D4 `INTERPRETATION_PROFILE_ROLE`** | `SHADOW` | `PROMOTE` or `NORMALIZE_FIRST` (requires L15 fixed) | `NORMALIZE_FIRST` or `DEPRECATE_CANDIDATE` (profile becomes a derived view of the canonical layer) |
| **D5 `NEGATION_MODEL`** | `NO_CHANGE` or `PREPROCESS_GUARD` (schema-free suppression; not credited to A's fidelity above) | `PREPROCESS_GUARD` (no profile-schema change) **or** `POLARITY_SIGNAL` (with a `NORMALIZED_PROFILE_EXTENSION`) | `POLARITY_SIGNAL` or `CLAUSE_LEVEL_MODEL` (the canonical layer carries per-signal polarity natively) |
| **D6 `MULTI_SIGNAL_POLICY`** | `KEEP_MAX3_PRIORITY` | `PRIMARY_SECONDARY` or `EXPAND_LIST` feasible (profile has `secondary_states[]`); `KEEP_MAX3_PRIORITY` still possible for the routing boundary | `STRUCTURED_MULTI_DIMENSION` (native); `PRIMARY_SECONDARY` as the adapter's projection |

This matches PR #2647 §20's cross-dependency notes; it does not extend or
decide them.

---

## Appendix A — Method / Reproducibility

- Code re-read at `origin/develop` `5b273f7fcdb0e98e373f0f0c1d4590300d374785`
  (PR #2647 merge). `git log 334bd876..HEAD -- temples/` is **empty** — only
  docs PRs #2646 / #2647 merged since the PR #2647 audit base; every
  semantic file's last-touch commit is pre-#2643. PR #2647's AS-IS model,
  L1–L16, and Decision Packet are therefore restated, not re-derived.
- 34 canonical cases extracted verbatim from
  `docs/audit/recommendation-nuance-quality-audit.md` §15; group counts
  (6/5/4/4/5/3/7 = 34) verified; each case appears exactly once in §7, §8,
  §9. No case invented; no discrepancy vs the merged source.
- Pure-function diagnostics (no DB, no behaviour change, repo venv
  `/Users/morietsu/Developer/jinja_app/.venv`, Django 5.2.16,
  `USE_GIS=0 USE_SQLITE=1`): re-confirmed the three drifted keyword tables
  (`前に進`, `悩み`, `迷い`, `考えすぎ`, `生活費`, `一人`, `学び`, `スキル`
  shadow-only), `interpret_consultation` determinism (identical output ×3)
  and 9-key schema, `translate_meaning` output, `need_profile` vs
  `extract_need_tags` divergence. `SCORE_V3_MODE` default `"shadow"`
  re-confirmed from `resolve_score_v3_mode_detail`. `recommendation_reason_v4`
  `_build_interpretation` state/decision/constraint/outcome consumption
  re-confirmed (file unchanged since 2026-08-13).
- Focused pytest suites (`test_consultation_interpreter.py`,
  `test_meaning_translation.py`, `test_need_to_goriyaku_tag_ids.py`,
  `test_concierge_input_contract.py`, `test_recommendation_reason_v4.py`,
  `test_recommendation_score_components.py`): **NOT_RUN** — the local
  `jinja_db` / `test_jinja_db` is in a broken state (`must be owner of
  database test_jinja_db` on recreate; 69 setup errors on `--reuse-db`).
  Per the task's audit-only validation rule, shared infrastructure was not
  repaired; CI (`unit` + `integration`) exercises these suites on the PR.
- `git diff --check`: clean. Exactly one repository file changed
  (`docs/audit/semantic-core-strategy-decision-audit.md`). The #2646 and
  #2647 canonical audits are untouched.
- No Production access, no Spreadsheet access, no migration, no runtime
  change.
