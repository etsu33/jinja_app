# Recommendation Nuance / Quality Audit

> **Status: AUDIT ONLY — READ-ONLY. No interpreter, mapping, scoring, ranking,
> evidence, data, or copy change is made or proposed for implementation here.**
> Audit base `origin/develop` = `4d7685f02d25dd21a639fa313d10e2df1640d66a`
> (after PR #2645). Branch `audit/recommendation-nuance-quality`.
>
> This document establishes the current truth of how a user's consultation
> wording travels through the recommendation pipeline. Section 19 lists
> improvement *candidates* for Mother Ship; nothing in it is selected,
> ranked as product priority, or implemented.

---

## 1. Executive Summary

The current recommendation pipeline turns free text into a **need_tag list**
(max 3, keyword/regex, priority-ranked), a **consultation_axis** (one of 9),
and a **GoriyakuTag-id set** (`NEED_TO_GORIYAKU_IDS`). Ranking rewards a
candidate shrine when its reviewed `goriyaku_tags` (GID evidence) or its
`goriyaku`/`description` prose (Text evidence) or its `astro_tags` intersect
those signals; otherwise `score_need = 0` and ordering falls to popularity /
distance / axis-history-theme boost.

Principal findings (evidence in later sections):

1. **The interpreter recognises Topic well, State weakly, Intention barely.**
   It is a flat keyword/substring matcher over 15 need_tags. "疲れている",
   "自信がなくなってきた", "落ち着かない" partially land (via `mental`/`rest`
   roots). "引きずっている", "気持ちを整理したい", "子どものことが心配",
   "環境を変えたい", "一歩踏み出すのが怖い→怖い" as a *state* do not.
2. **Negation is not handled at all.** `恋愛の相談ではない` → `need_tags=['love']`,
   GID `[縁結び, 恋愛成就]`. `結婚より今は仕事を優先したい` →
   `['marriage','career']`, axis `relationship_repair`. Every negated /
   de-emphasised keyword is matched as if asserted.
3. **Two `NEED_TO_GORIYAKU_IDS` entries are semantically mismatched to their
   Need.** `mental → {勝運, 家庭円満, 金運, 足腰健康}` and
   `rest → {家内安全, 福徳}` — none of those 6 GoriyakuTags denotes
   calm / healing / rest / emotional steadying. `communication → {}` (empty
   by deliberate Mother Ship decision). `courage`, `focus`, `relationship`,
   `health` mappings are broad or borrowed.
4. **`score_need` frequently stays 0 for emotional-state consultations even
   when the interpreter fired**, because the mapped GoriyakuTags either don't
   exist on many shrines (`夫婦円満` = 1 shrine, `福徳` = 1, `心願成就` = 3)
   or don't semantically match the Need. Ranking then reverts to popularity /
   distance.
5. **The `interpretation_profile` (STATE / DIRECTION / OUTCOME / DECISION /
   CONSTRAINT signals) is computed on every request but is shadow-only** — it
   never reaches candidate generation, `score_need`, ranking, Lead, or Reason.
   Only `need_tags` + `consultation_axis` + user-selected `goriyaku_tag_ids`
   are load-bearing.
6. **Reason/Lead copy is bounded by the same evidence.** When `score_need = 0`
   the Reason is the generic "今の悩みや願いに合わせて参拝先の候補に入れて
   います"; when a mismatched GID matched, the Lead can cite a
   Purpose-unrelated label (a known, documented limitation for `health`).

**First-loss-point distribution** across the 34 natural-language audit cases
(Section 15/17): INTERPRETER 8, NEED→GORIYAKU mapping 7, EVIDENCE 4,
NEGATION 5, MULTI-SIGNAL/AXIS 4, none-lost 6. No CANDIDATE_GAP was observed
(the canonical pool is only 103 shrines and every free-text request scores
the whole pool). No blocker to safe operation was found; the gaps degrade
*nuance fidelity*, not availability.

`RECOMMENDATION_NUANCE_AUDIT_STATUS = COMPLETE`. Full verdict in Section 20.

---

## 2. Scope

Audited path (logical): user consultation input → free_text (`query`) →
interpreter → Purpose / Need signals → Need → GoriyakuTag mapping → eligible
Recommendation Evidence → candidate generation → C1 / `score_need` → final
ordering → Lead / Reason.

- **In scope:** the concierge chat pipeline (`POST` `…/concierge/chat`), its
  interpreter modules, `NEED_TO_GORIYAKU_IDS`, `_attach_breakdown` scoring,
  `_sort_chat_recommendations`, `build_recommendation_reason`. Read-only
  Production measurement of GoriyakuTag evidence coverage.
- **Referenced, not re-audited:** the Compass path
  (`api_views_compass.py`, `purpose` input) — noted where it diverges.
- **Out of scope / untouched:** any change. LLM path (`CONCIERGE_USE_LLM`
  default `False`; heuristic path is the runtime default and the subject
  here). Astrology/element, direction/`houi`, visit-style, behaviour signals
  — described only where they dominate `score_need = 0` cases.

---

## 3. Current Pipeline (as built)

```text
HTTP POST concierge/chat  (api_views_concierge.ConciergeChatView.post)
  │
  ├─ normalize_concierge_request(data)               concierge_input_contract.py
  │     query (raw free text; `message` folded in)
  │     goriyaku_tag_ids  (Level 3-B explicit constraint — user-picked tags)
  │     extra_condition   (Level 2 visit-preference, legacy free-text parse)
  │     visit_preferences (Level 2 visit-preference, structured)
  │     birthdate
  │     ── NO structured "consultation theme" field exists in this contract ──
  │
  ├─ interpret_consultation(query, need_tags=[])     consultation_interpreter.py
  │     → interpretation_profile  { state_profile, need_profile,
  │        direction_profile, emotion_profile, action_intent,
  │        decision_context, constraint_profile, outcome_hint }
  │     SHADOW: used only for (a) translate_meaning() shrine meaning payload
  │     inside build_chat_candidates, (b) _debug, (c) Score v3 shadow
  │     components. NOT used for need_tags, score_need, ranking, Lead, Reason.
  │
  ├─ _build_chat_candidates_pipeline → build_chat_candidates(              concierge_chat_candidates.py
  │        goriyaku_tag_ids = data.get("goriyaku_tag_ids"),  ← user-picked only
  │        area, lat, lng)
  │     qs = Shrine.objects.all()
  │       .filter(goriyaku_tags__id__in=goriyaku_tag_ids)  IFF user picked tags
  │       exclude_qa_fixture_shrines()          (name-convention QA exclusion)
  │       .filter(latitude/longitude not null).exclude(address="")
  │       order_by(-popular_score, id)[: max(limit*5, 50) = 100]
  │     → candidate dicts incl. goriyaku_tag_ids, goriyaku, description,
  │        astro_tags, history_theme, popular_score, distance_m
  │     ── Need→GoriyakuTag mapping is NOT applied at candidate generation ──
  │
  └─ build_chat_recommendations(query, candidates, …)                     concierge_chat.py
       ├─ resolve_need_payload(query, need_tags=[])          concierge_chat_need.py
       │    need_tags == [] → extract_need_tags(query)       domain/need_tags.py
       │    → need_tags  (max 3, NEED_PRIORITY order)
       ├─ resolve_consultation_axis(query, need_tags, llm_axis=None)  domain/consultation_axis.py
       │    llm_axis(none) → query keyword hits → need_tag fallback → "other"
       ├─ resolve_llm_route(…)   CONCIERGE_USE_LLM=False (default)
       │    → _prefilter_candidates_for_need(candidates, need_tags, axis)   concierge_chat_ranking.py
       │        per candidate: +2 astro_tag hit, +2 GID hit, +1 text hit,
       │        +2 study text bonus, + history_theme_candidate_boost
       │    → _seed_recs_from_candidates(prefiltered, size=12)
       ├─ _ensure_pool_size(size=20) / _merge_candidate_fields
       ├─ _attach_chat_rec_enrichment → per rec:
       │    _attach_breakdown(rec, need_tags, weights, requested_goriyaku_tag_ids, axis)
       │        matched_by_tag  = need_tags ∩ rec.astro_tags
       │        matched_by_text = need_tags whose NEED_TEXT_WEIGHTS hint ∈ (goriyaku+description)
       │        matched_by_gid  = need_tags whose need_tags_to_goriyaku_ids ∩ rec.goriyaku_tag_ids
       │        matched_by_user_selected_gid = rec.goriyaku_tag_ids ∩ requested_goriyaku_tag_ids
       │        score_need       = len(union of the first three)          ← public contract score
       │        score_need_rank_weighted = astro*2 + C1Max(gid,text) + study_bonus
       │                                    + history_theme_candidate_boost ← ranking-effective
       │        reason_facts + _primary_reason_label  (_resolve_primary_reason)
       │    build_recommendation_reason(rec, need_tags, need_gid_label_by_id)
       ├─ attach_explanation_payload
       ├─ _sort_chat_recommendations
       │    default: sort by -resolve_score_sort_key (score_v3 mode) then distance then name
       │             then _diversify_by_need(limit=3)
       │    distance_mode ("sort_distance" in extra tags): primary-tier-reason
       │             candidates first, then distance
       └─ _attach_rank_comparison → recommendations[]
```

---

## 4. Source-of-Truth Files

| Concern | File | Key symbols |
|---|---|---|
| Free-text interpretation (shadow profile) | `backend/temples/services/consultation_interpreter.py` | `NEED_KEYWORDS`, `STATE_KEYWORDS`, `DIRECTION_BY_STATE`, `ACTION_KEYWORDS`, `DECISION_KEYWORDS`, `CONSTRAINT_KEYWORDS`, `OUTCOME_KEYWORDS`, `interpret_consultation()` |
| Need extraction (runtime) | `backend/temples/domain/need_tags.py` | `NEED_TAGS` (15), `NEED_PRIORITY`, `KEYWORDS`, `REGEX`, `NEED_TEXT_HINTS`, `extract_need_tags()` |
| Need normalisation / fallback | `backend/temples/services/concierge_chat_need.py` | `NEED_TAG_ALIASES`, `NEED_SYNONYMS`, `resolve_need_payload()`, `extract_need_fallback()` |
| Consultation axis | `backend/temples/domain/consultation_axis.py` | `CONSULTATION_AXES` (9), `CONSULTATION_AXIS_ALIASES`, `CONSULTATION_AXIS_KEYWORDS`, `NEED_TAG_TO_CONSULTATION_AXIS`, `resolve_consultation_axis()` |
| Need → GoriyakuTag mapping | `backend/temples/domain/need_to_goriyaku_tag_ids.py` | `NEED_TO_GORIYAKU_IDS`, `need_tags_to_goriyaku_ids()` |
| Candidate generation | `backend/temples/services/concierge_chat_candidates.py` | `build_chat_candidates()` |
| QA-fixture exclusion | `backend/temples/services/shrine_qa_fixture_exclusion.py` | `exclude_qa_fixture_shrines()` |
| Recommendation facade | `backend/temples/services/concierge_chat.py` | `build_chat_recommendations()`, `_attach_chat_rec_enrichment()`, `_sort_chat_recommendations()` |
| LLM vs heuristic route | `backend/temples/services/concierge_chat_llm_route.py` | `resolve_llm_route()` |
| Prefilter + C1 + score_need + reason | `backend/temples/services/concierge_chat_ranking.py` | `_prefilter_candidates_for_need()`, `_attach_breakdown()`, `NEED_TEXT_WEIGHTS`, `STUDY_SHRINE_HINTS`, `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`, `_build_reason_facts()`, `_resolve_primary_reason()`, `build_recommendation_reason()`, `_build_need_lead()`, `_resolve_matched_lead_evidence()`, `_build_need_reason_text()`, `_diversify_by_need()`, `PRIMARY_REASON_PRIORITY` |
| Score v2 (legacy contract) | `backend/temples/services/recommendation_score_v2.py` | `calculate_recommendation_score_v2()` |
| Score v3 components (shadow) | `backend/temples/services/recommendation_score_components.py` | `calculate_state_match_score()` … (shadow only) |
| Reason v4 (structured explanation) | `backend/temples/services/recommendation_reason_v4.py` | `build_recommendation_reason_v4()` — used for a preview payload / action-suggestion, not the primary `rec["reason"]` string |
| API orchestration | `backend/temples/api_views_concierge.py` | `ConciergeChatView.post`, `_build_chat_candidates_pipeline()` |
| Compass path (referenced) | `backend/temples/api_views_compass.py` | `purpose` input |

**CODE/DOC discrepancies recorded** (Section 10, 16 `DOC_CODE_DRIFT`):

- `backend/temples/fixtures/goriyaku_tags.json` contains **15** rows with
  *different names* (`縁結び`, `子宝・安産`, `学業成就`, …). The **runtime
  master in Production is 39 rows** with different labels (`厄除け`, `商売繁盛`,
  `恋愛成就`, `夫婦円満`, `福徳`, …). `NEED_TO_GORIYAKU_IDS` is keyed to the
  39-row master (it references ids up to 39). The fixture is stale and must
  not be used to interpret the mapping. (Verified read-only, Section 12.)
- `consultation_interpreter.NEED_KEYWORDS` and `domain/need_tags.KEYWORDS`
  are **near-duplicates that have drifted**: the interpreter copy adds
  `悩み・迷い・考えすぎ` (mental), `前に進` (courage), `生活費` (money),
  `一人・ひとり` (rest), `学び・スキル` (study) that the runtime copy lacks.
  Only the runtime copy (`domain/need_tags`) affects ranking.

---

## 5. Purpose Inventory

**"Purpose" is not a single canonical runtime object in the concierge chat
path.** There are three overlapping representations:

### 5.1 `need_tag` (the load-bearing "purpose/need" axis) — 15 canonical keys

`backend/temples/domain/need_tags.NEED_TAGS`, priority order
`backend/temples/domain/need_tags.NEED_PRIORITY`:

| # (priority) | need_tag | structured entry | free-text entry | in `score_need`? | in Lead/Reason? | coexists? |
|---|---|---|---|---|---|---|
| 1 | `protection` | via `goriyaku_tag_ids` pick | `KEYWORDS`+`REGEX` | yes | yes | yes (max 3) |
| 2 | `marriage` | " | `KEYWORDS`+`REGEX` | yes | yes | yes |
| 3 | `love` | " | `KEYWORDS`+`REGEX` | yes | yes | yes |
| 4 | `family` | " | `KEYWORDS` | yes | yes | yes |
| 5 | `study` | " | `KEYWORDS`+`REGEX`(+study text bonus) | yes | yes | yes |
| 6 | `career` | " | `KEYWORDS` | yes | yes | yes |
| 7 | `money` | " | `KEYWORDS` | yes | yes | yes |
| 8 | `health` | " | `KEYWORDS` | yes | yes | yes |
| 9 | `mental` | " | `KEYWORDS`+`REGEX` | yes | yes | yes |
| 10 | `relationship` | " | `KEYWORDS` | yes | yes | yes |
| 11 | `communication` | " | `KEYWORDS` | **GID contributes 0** (empty map) | yes (text only) | yes |
| 12 | `courage` | " | `KEYWORDS`+`REGEX` | yes | yes | yes |
| 13 | `focus` | " | `KEYWORDS` | yes | yes | yes |
| 14 | `rest` | " | `KEYWORDS`+`REGEX` | yes | yes | yes |
| 15 | `travel_safe` | " | `KEYWORDS` | yes | yes | yes |

Aliases feeding `need_tag` (two independent copies:
`concierge_chat_need.NEED_TAG_ALIASES` and
`concierge_chat_ranking.NEED_TAG_ALIASES`, kept in sync by hand):
`romance→love`, `anxiety→mental`, `healing→rest`, `career_change→career`,
`work→career`, `fortune→money`, `challenge/ambition/success→courage`.
`relationship` and `marriage` were **deliberately removed** from the alias
table (they are first-class need_tags — see
`docs/audit/marriage-love-alias-boundary.md`,
`docs/audit/concierge-l1-freetext-readiness.md`).

### 5.2 `consultation_axis` — 9 canonical keys

`backend/temples/domain/consultation_axis.CONSULTATION_AXES`:
`money_growth`, `career_change`, `independence`, `relationship_repair`,
`rest_healing`, `restart_mindset`, `nature_reset`, `study_success`, `other`.

- Resolution precedence (`resolve_consultation_axis`): normalised `llm_axis`
  (never set on the heuristic path) → **query keyword hits**
  (`CONSULTATION_AXIS_KEYWORDS`, most-hits then `CONSULTATION_AXIS_PRIORITY`)
  → **`need_tags` fallback** (`NEED_TAG_TO_CONSULTATION_AXIS`, first tag that
  maps) → `"other"`.
- Participates in scoring **only** via
  `resolve_history_theme_candidate_boost(axis, shrine.history_theme)` added to
  `score_need_rank_weighted` and to the prefilter score
  (`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`). It does **not** change
  `need_tags`, the GID set, `score_need` (public), or `matched_need_tags`.
- Affects Reason indirectly: a `history_theme` reason_fact is only emitted
  when `history_theme_candidate_boost > 0` (i.e. axis-aligned). `independence`
  and `nature_reset` and `other` have **no** `NEED_TAG_TO_CONSULTATION_AXIS`
  producer — they are only reachable from query keywords.
- `restart_mindset` collapses several distinct intentions (`courage`,
  `mental`) onto one axis.

### 5.3 Compass `purpose` (separate API, referenced only)

`api_views_compass.py` takes a plain `purpose` string; mapped elsewhere
(`docs/audit/compass-purpose-goriyaku-mapping*.md`). Not part of the chat
runtime path audited here.

---

## 6. Need Inventory

All 15 need_tags, produced by `extract_need_tags()` (substring `KEYWORDS`
match ∪ `REGEX` search, then `NEED_PRIORITY` pick, `max_tags=3`).
GoriyakuTag ids resolved against the **39-row Production master** (Section 12).

| need_tag | main producing tokens (runtime `KEYWORDS`/`REGEX`) | `NEED_TO_GORIYAKU_IDS` | GID names | mapping empty? | shared GID with | reaches `score_need`? | Lead/Reason? |
|---|---|---|---|---|---|---|---|
| `love` | 恋愛, 恋, 復縁, 片思い, 両思い, 出会い, 告白 | `{1,20}` | 縁結び, 恋愛成就 | no | marriage, relationship (id 1) | yes | yes |
| `relationship` | 人間関係, 職場, 上司, 同僚, 家族, 親子, 友達, 対人 | `{1}` | 縁結び | no | love, marriage | yes | yes |
| `marriage` | 縁結び, 良縁, 結婚, 婚活, 結縁, ご縁, 夫婦円満, 夫婦関係, 夫婦仲 | `{1,18}` | 縁結び, 夫婦円満 | no | love, relationship (id 1) | yes | yes |
| `communication` | 会話, 発信, 伝える, 話す, 営業, 交渉, プレゼン, 面接, コミュニケーション, 話せる/話せない, 伝えられない/伝わらない | `set()` | — | **YES (deliberate)** | — | **GID part = 0**; text-only via `NEED_TEXT_WEIGHTS` (none defined for `communication` either) | yes (may be generic) |
| `career` | 転職, 仕事, 就職, 昇進, 独立, 起業, キャリア, 天職, 副業, 働き方, 好きな仕事, 仕事を辞めたい, 会社を作りたい, 道を開く | `{6,21,30,12,27}` | 開運, 導き, 強運厄除け, 仕事運, 出世運 | no | courage (12,30), money(—) | yes | yes |
| `money` | 金運, 収入, 給料, 年収, 貯金, 商売, 繁盛, 売上, お金, 事業, 経営, 安定, 資金, 利益, 収益, 業績, 稼ぐ/稼ぎ, もっと稼ぎたい | `{5,36,4,28}` | 五穀豊穣, 心願成就, 商売繁盛, 金運 | no | — | yes | yes |
| `study` | 学業, 合格, 試験, 受験, 資格, 勉強, 成績, 学び直し | `{9,10}` | 学業成就, 合格祈願 | no | focus (identical) | yes (+study text bonus) | yes |
| `health` | 健康, 体調, 病気, 不調, 体力, 治す | `{7,8,24,33,38}` | 家内安全, 福徳, 健康長寿, 病気平癒, 足腰健康 | no | rest (7,8) | yes | yes (known: Lead may cite 家内安全) |
| `mental` | 不安, 落ち込み, ストレス, メンタル, 自信, 焦り, しんどい, つらい/辛い/苦しい, 心を整えたい, 気持ちを切り替えたい, 整えたい, 癒し, 疲れ(て/ている), 疲労, 流れが悪い, 最近うまくいかない | `{11,26,28,38}` | 勝運, 家庭円満, 金運, 足腰健康 | no | protection (11), money (28), courage (38), rest(—) | yes | yes |
| `protection` | 厄, 厄除, 厄払い, 浄化, 邪気, お祓い, 清めたい, 災難, 守護, 流れが悪い, 守って, 守られたい | `{11,32,2}` | 勝運, 八方除け, 厄除け | no | mental (11) | yes | yes |
| `courage` | 決断, 挑戦, 一歩, 背中押して, 勇気, 変わりたい, 踏み出す, 開運(祈願), 運を開きたい, 流れを変えたい/良くしたい, 行動, きっかけ, 動き出したい, 前向きになりたい, 後押ししてほしい | `{12,15,18,20,24,30,38}` | 仕事運, 武運長久, 夫婦円満, 恋愛成就, 健康長寿, 強運厄除け, 足腰健康 | no | career (12,30), love (20), marriage (18) | yes | yes |
| `focus` | 集中, 習慣, 継続, 怠け, 先延ばし, やる気, ルーティン | `{9,10}` | 学業成就, 合格祈願 | no | study (identical) | yes | yes |
| `rest` | 休みたい, 休息, 疲れ, 回復, 睡眠, 眠れない, リセット, 穏やか, 静か, 落ち着きたい/落ち着く, 心を整えたい, 整えたい, 自然, ゆっくり, 過ごしたい, 癒し, ひと息, 日常から離れたい, 離れて, 慌ただしい | `{7,8}` | 家内安全, 福徳 | no | health (7,8) | yes | yes |
| `family` | 子宝, 安産, 妊活, 授かり, 出産, 育児 | `{16,35}` | 安産, 子宝 | no | — | yes | yes |
| `travel_safe` | 旅行, 旅, 出張, 移動, 交通安全, 安全祈願 | `{3,13,14}` | 交通安全, 航海安全, 海上安全 | no | — | yes | yes |

**Layer-by-layer status for the 15 explicitly-required Needs** (Section 12
expands): interpreter-produces / has-GID-mapping / mapped-tag-has-evidence /
reaches-scoring are separate columns and must not be collapsed.

| Need | interpreter produces | GID mapping non-empty | mapped tag has ≥1 canonical shrine | semantically aligned mapping |
|---|---|---|---|---|
| love | yes | yes | yes (縁結び 33) | yes |
| relationship | yes | yes | yes (縁結び 33) | **partial** — 縁結び is romantic; workplace/family relations borrow it |
| marriage | yes | yes | yes (縁結び 33; 夫婦円満 1) | yes |
| communication | yes | **no (empty)** | n/a | n/a (Mother Ship: `DISABLE_GID_EVIDENCE`) |
| career | yes | yes | yes (開運 60, 仕事運 11) | **partial** — 開運/強運厄除け are generic luck |
| money | yes | yes | yes (商売繁盛 18, 金運 2) | **partial** — 五穀豊穣/心願成就 loose |
| study | yes | yes | yes (学業成就 8, 合格祈願 4) | yes |
| health | yes | yes | yes (家内安全 28; 病気平癒 2) | **partial** — 家内安全 = household safety, not personal health |
| mental | yes | yes | yes by count (勝運 20) | **NO** — 勝運/家庭円満/金運/足腰健康 unrelated to anxiety/steadying |
| protection | yes | yes | yes (厄除け 53) | yes |
| courage | yes | yes | yes by count (仕事運 11) | **partial** — 夫婦円満/恋愛成就/健康長寿/足腰健康 scattered |
| focus | yes | yes | yes (学業成就 8) | **partial** — reuses study; no habit/concentration tag exists |
| rest | yes | yes | yes by count (家内安全 28) | **NO** — 家内安全/福徳 not calm/healing; no 癒し/静寂 tag exists |
| family | yes | yes | yes (安産 6, 子宝 1) | yes (narrow reading, Mother Ship: `NARROW`) |
| travel_safe | yes | yes | yes (交通安全 7) | yes |

---

## 7. Interpreter Vocabulary Inventory

### 7.1 Mechanics (runtime — `extract_need_tags`)

- **Normalisation:** `query.strip()` only. No case-folding for JA (n/a),
  **no width normalisation** (`　`→` ` is done only later in `_attach_breakdown`
  material, not in the interpreter), no kana↔kanji folding, no lemmatisation.
- **Matching:** plain Python `substring in query` for every `KEYWORDS` entry;
  `re.Pattern.search` for every `REGEX` entry. Hits accumulate into
  `hits[tag]`.
- **Conjunction / multi-signal:** any number of tags may hit; final list is
  `NEED_PRIORITY`-ordered and truncated to `max_tags=3`. There is **no**
  clause splitting on `が`, `けど`, `より`, `。`, `、`, `し`, etc. — the whole
  query string is one match surface.
- **Punctuation / whitespace:** ignored (substring match is position-agnostic).
- **Negation:** **none.** No `ない`, `じゃない`, `わけではない`, `より`,
  `というより` handling anywhere in `domain/need_tags.py`,
  `consultation_interpreter.py`, or `consultation_axis.py`.
- **Ambiguity:** resolved only by `NEED_PRIORITY` (fixed global order) and
  `max_tags` truncation; no confidence gating on the runtime path.
- **Regex set (runtime):** `protection` (厄(除\|払), 厄を落としたい, 流れが悪い,
  悪い流れ, 清めたい, お祓い, 守って, 守られたい); `study` ((合格\|必勝\|試験),
  受験); `marriage` ((縁結び\|良縁\|結婚)); `love` ((恋愛\|復縁\|片思い));
  `mental` (つらい, 辛い, 苦しい, 心を整え, 落ち着け(たい\|たく),
  疲れ(て\|が\|た)?, 流れが悪い, 最近うまくいかない); `rest`
  ((穏やか\|静か\|落ち着\|リセット\|休息\|癒し\|ひと息\|一息)); `courage`
  (背中を押して, 運を開きたい, 流れを良くしたい, 流れを変えたい, 開運(祈願)?,
  (行動\|動き出\|踏み出), きっかけ(が)?ほしい).

### 7.2 Text-evidence vocabulary (ranking side — `NEED_TEXT_WEIGHTS`)

Only 7 need_tags have `NEED_TEXT_WEIGHTS` (matched against a shrine's
`goriyaku`+`description`, **not** the user query): `study`, `career`,
`courage`, `mental`, `love`, `money`, `rest`. `relationship`, `marriage`,
`communication`, `health`, `protection`, `focus`, `family`, `travel_safe`
have **no** Text-evidence weights → those Needs score only via GID or astro.

### 7.3 Shadow interpreter vocabulary (`consultation_interpreter.py`)

`STATE_KEYWORDS`: `tired`(疲れ, しんど, 休み, 癒), `anxious`(不安, 怖, 心配,
焦り), `uncertain`(迷, わから, 決められ, 悩), `stuck`(停滞, 動け, 進ま, 詰ま),
`ready_to_change`(変えたい, 切り替え, やり直, 始めたい).
`OUTCOME_KEYWORDS`: `decide`, `calm`, `move_forward`, `clarify`.
`DECISION_KEYWORDS`: `career_decision`, `relationship_decision`,
`money_decision`, `rest_or_action`. `CONSTRAINT_KEYWORDS`: `time`, `money`,
`energy`, `relationship`. `ACTION_KEYWORDS`: `visit`, `reflect`, `save`.
**All of these are shadow — none reaches ranking, Lead, or Reason.**

---

## 8. Topic / State / Intention Coverage (audit lens only)

Classifications: `SUPPORTED` (reliably produces a load-bearing need_tag),
`PARTIAL` (only via a borrowed/loose token, or only shadow), `NOT_REPRESENTED`
(no load-bearing signal), `AMBIGUOUS` (produces a signal that mis-frames the
input).

### 8.1 Topic

| Topic | status | evidence |
|---|---|---|
| career / work | `SUPPORTED` | 転職/仕事/キャリア… → `career` |
| money | `SUPPORTED` | 金運/収入/稼ぎたい… → `money` |
| love (romance) | `SUPPORTED` | 恋愛/出会い/復縁 → `love` |
| marriage | `SUPPORTED` | 結婚/婚活/夫婦 → `marriage` |
| study / exam | `SUPPORTED` | 合格/試験/資格 → `study` |
| health | `PARTIAL` | 健康/体調/病気 → `health`, but axis = `other` and GID = household-flavoured |
| family (as topic) | `PARTIAL` | 家族 → `relationship` (not a `family` tag; `family` = fertility only). 子ども/育児/子育て except 育児 → nothing |
| interpersonal / workplace relations | `SUPPORTED` (tag) / `PARTIAL` (evidence) | 人間関係/職場/対人 → `relationship`, GID `{縁結び}` |
| travel / safety | `SUPPORTED` | 旅行/出張/交通安全 → `travel_safe` |
| spiritual cleansing / luck | `SUPPORTED` | 厄/お祓い/開運 → `protection` / `courage` |
| bereavement / loss | `NOT_REPRESENTED` | 「別れた人を引きずっている」→ `need_tags=[]` |
| parenting worry | `NOT_REPRESENTED` | 「子どものことが心配」→ `need_tags=[]` |

### 8.2 State

| State | status | evidence |
|---|---|---|
| fatigue (tired) | `PARTIAL` | 疲れ/疲れている → `mental`+`rest` (load-bearing); also shadow `state=tired` |
| anxiety | `PARTIAL` | 不安/焦り → `mental`; 心配/怖い → shadow `state=anxious` only, **no need_tag** |
| hesitation / indecision | `NOT_REPRESENTED` (load-bearing) | 迷っている/決められない → shadow `state=uncertain` only; no need_tag (`迷い` is in the *shadow* NEED_KEYWORDS for `mental` but not the runtime one) |
| loss of confidence | `PARTIAL` | 自信 (bare) → `mental`; 「自信がなくなってきた」lands only because 自信 substring matches |
| stagnation | `PARTIAL` | 流れが悪い/最近うまくいかない → `mental`+`protection` (runtime); 停滞/詰まっている → shadow `stuck` only |
| restlessness / not calm | `PARTIAL` | 落ち着かない → `rest` (via 落ち着 regex) but frames as "wants rest" |
| conflict (with a person) | `NOT_REPRESENTED` | 「関係がうまくいかない」→ `relationship` only if 人間関係/職場/家族 token present; 「うまくいかない」alone → `mental` |
| fear (of acting) | `NOT_REPRESENTED` | 「踏み出すのが怖い」→ `courage` (from 踏み出す), the *fear* is dropped; shadow `state=anxious` |
| lingering / can't let go | `NOT_REPRESENTED` | 引きずっている → nothing |

### 8.3 Intention

| Intention | status | evidence |
|---|---|---|
| move forward | `PARTIAL` | 前に進みたい → shadow `outcome=move_forward`; runtime: `前に進` is in *shadow* courage KEYWORDS, not runtime → often no need_tag unless 一歩/踏み出す/挑戦 present |
| decide | `NOT_REPRESENTED` (load-bearing) | 決めたい/決断 → shadow `outcome=decide`; no need_tag |
| calm down | `PARTIAL` | 落ち着きたい → `rest`; 整えたい → `mental`+`rest` |
| challenge something | `SUPPORTED` | 挑戦/一歩/踏み出す → `courage` |
| protect something | `SUPPORTED` | 守って/守られたい/厄除け → `protection` |
| repair a relationship | `PARTIAL` | 仲直り/関係を修復 → `consultation_axis=relationship_repair` (keyword), but `need_tag` only if 人間関係/家族/職場 token present |
| leave something (quit/change env) | `NOT_REPRESENTED` | 「環境を変えたい」「会社を辞めたい」→ 仕事を辞めたい is a `career` KEYWORD; 「環境を変えたい」alone → nothing |
| focus | `PARTIAL` | 集中/継続 → `focus` (maps to study evidence) |
| rest | `SUPPORTED` | 休みたい/休息/ひと息 → `rest` |

---

## 9. Structured Theme vs Free Text

**There is no structured "consultation theme" selector in the concierge chat
input contract** (`concierge_input_contract.py`). The structured signal that
exists is `goriyaku_tag_ids` (Level 3-B explicit constraint, user-picked
GoriyakuTag ids). Behaviour of `goriyaku_tag_ids` (structured) vs `query`
(free text), from code:

| # | situation | current behaviour |
|---|---|---|
| 1 | agree (picked tag ≈ query need) | `goriyaku_tag_ids` becomes a **hard candidate filter** (`build_chat_candidates` `.filter(goriyaku_tags__id__in=…)`) AND scores as `matched_by_user_selected_gid` (reason_fact `user_selected_tag`, score 3.0, priority tier 4). `query` need_tags score in parallel. Effects add. |
| 2 | complement (different but compatible) | Union: pool filtered to shrines having ≥1 picked tag; within that pool, `query` need_tags still drive `score_need`. |
| 3 | conflict (picked tag vs query need) | **No conflict resolution.** Pool is filtered to the picked tag's shrines; if none of those match the query need, `score_need` is 0 for all and ordering is popularity/distance. The picked tag still yields a `user_selected_tag` reason_fact, so the Reason can foreground the *picked* tag while the query nuance is silently unused. |
| 4 | free_text contains a second Need | Up to 3 need_tags extracted; all score. e.g. `転職したいけど一歩踏み出すのが怖い` → `['career','courage']`, GID union of both (10 tags). |
| 5 | free_text stronger nuance than a (picked) tag | The picked tag is a hard filter and a tier-4 reason; free-text nuance only affects `score_need` **within** that filtered pool and only if a mapped GID/text/astro hit lands. Nuance can be diluted. |
| 6 | free_text has no recognised signal | `need_tags=[]`; `_prefilter_candidates_for_need` gives every candidate score 0; `_seed_recs_from_candidates` takes popularity order; `_attach_breakdown` `score_need=0`; Reason = generic fallback string. axis falls to `other` (unless a `CONSULTATION_AXIS_KEYWORDS` hit). |

Observed (offline run, Section 15):

- `theme≈career` + `新しい仕事に挑戦したい` → `['career','courage']`, axis
  `career_change`. Agree.
- `theme≈career` + `最近疲れていて少し休みたい` → `['mental','rest']`, axis
  `rest_healing`. Free text **overrides** the notional theme entirely; there
  is no theme field to hold "career", so the fatigue wins.
- `theme≈love` + `恋愛より仕事のことで悩んでいます` → `['love','career']`
  (both matched; `恋愛` matched despite `より`), axis `relationship_repair`
  (need_tag fallback picks `love` before `career`). The stated pivot to work
  is not honoured.

---

## 10. Negation / Context Behaviour

**The interpreter performs no negation or context analysis.** Every result
below is the actual offline output of `extract_need_tags` /
`resolve_consultation_axis` on the branch base.

| input | need_tags (runtime) | GID | axis | interpreter behaviour |
|---|---|---|---|---|
| `恋愛の相談ではない` | `['love']` | `{縁結び, 恋愛成就}` | `relationship_repair` | **matches keyword inside negated text**; produces `love` |
| `転職したいわけではない` | `['career']` | `{開運, 仕事運, 導き, 出世運, 強運厄除け}` | `career_change` | negation ignored; produces `career` |
| `不安ではないけど迷っている` | `['mental']` | `{勝運, 家庭円満, 金運, 足腰健康}` | `restart_mindset` | matches the *negated* 不安 → `mental`; the asserted 迷っている produces **no** need_tag (shadow `state=uncertain` only) → **unintended Need** |
| `結婚より今は仕事を優先したい` | `['marriage','career']` | `{縁結び, 開運, 仕事運, 夫婦円満, 導き, 出世運, 強運厄除け}` | `relationship_repair` | `結婚` matched despite `より`; axis fallback picks `marriage` → **mis-framed as a marriage consultation** |
| `休みたいというより環境を変えたい` | `['rest']` | `{家内安全, 福徳}` | `rest_healing` | matches the de-emphasised 休みたい → `rest`; the asserted 環境を変えたい produces **no** signal (`ready_to_change` shadow only) |

Summary: understands negation — **no**; ignores negation — **yes (silently)**;
matches keywords inside negated text — **yes**; produces multiple signals —
**yes (unfiltered)**; produces an unintended Need — **yes (3 of 5 cases)**;
produces no signal — only when the asserted clause also has no keyword.

---

## 11. Need → GoriyakuTag Mapping

`NEED_TO_GORIYAKU_IDS` (`backend/temples/domain/need_to_goriyaku_tag_ids.py`),
resolved against the 39-row Production master. Layer columns are independent.

| Need | GID ids | GID names | shared with | mapping-empty | interpreter-can-produce | mapped-tag-has-evidence (canonical shrines) | evidence-reaches-scoring |
|---|---|---|---|---|---|---|---|
| love | 1, 20 | 縁結び, 恋愛成就 | marriage, relationship (1) | no | yes | 縁結び 33 / 恋愛成就 4 | yes |
| relationship | 1 | 縁結び | love, marriage | no | yes | 縁結び 33 | yes (but semantic borrow) |
| marriage | 1, 18 | 縁結び, 夫婦円満 | love, relationship (1) | no | yes | 縁結び 33 / 夫婦円満 1 | yes |
| communication | — | — | — | **yes** | yes | n/a | **no (GID part contributes 0; no Text weights either)** |
| career | 6, 21, 30, 12, 27 | 開運, 導き, 強運厄除け, 仕事運, 出世運 | courage (12,30) | no | yes | 開運 60 / 仕事運 11 / 出世運 3 / 導き 1 / 強運厄除け 1 | yes |
| money | 5, 36, 4, 28 | 五穀豊穣, 心願成就, 商売繁盛, 金運 | — | no | yes | 商売繁盛 18 / 金運 2 / 五穀豊穣 3 / 心願成就 3 | yes |
| study | 9, 10 | 学業成就, 合格祈願 | focus (identical) | no | yes | 学業成就 8 / 合格祈願 4 | yes (+ study text bonus) |
| health | 7, 8, 24, 33, 38 | 家内安全, 福徳, 健康長寿, 病気平癒, 足腰健康 | rest (7,8), mental (38) | no | yes | 家内安全 28 / 病気平癒 2 / 健康長寿 1 / 福徳 1 / 足腰健康 1 | yes (dominated by 家内安全) |
| mental | 11, 26, 28, 38 | 勝運, 家庭円満, 金運, 足腰健康 | protection (11), money (28), courage (38) | no | yes | 勝運 20 / 金運 2 / 家庭円満 1 / 足腰健康 1 | yes by count, **semantically off** |
| protection | 11, 32, 2 | 勝運, 八方除け, 厄除け | mental (11) | no | yes | 厄除け 53 / 勝運 20 / 八方除け 1 | yes |
| courage | 12, 15, 18, 20, 24, 30, 38 | 仕事運, 武運長久, 夫婦円満, 恋愛成就, 健康長寿, 強運厄除け, 足腰健康 | career (12,30), love (20), marriage (18), health (24,38) | no | yes | 仕事運 11 / 恋愛成就 4 / (others 1) | yes by count, scattered |
| focus | 9, 10 | 学業成就, 合格祈願 | study (identical) | no | yes | 学業成就 8 / 合格祈願 4 | yes (borrowed from study) |
| rest | 7, 8 | 家内安全, 福徳 | health (7,8) | no | yes | 家内安全 28 / 福徳 1 | yes by count, **semantically off** |
| family | 16, 35 | 安産, 子宝 | — | no | yes | 安産 6 / 子宝 1 | yes |
| travel_safe | 3, 13, 14 | 交通安全, 航海安全, 海上安全 | — | no | yes | 交通安全 7 / 海上安全 5 / 航海安全 2 | yes |

**Layer distinctions that must not be collapsed:**

- *interpreter-can-produce* is `yes` for all 15.
- *mapping-non-empty* is `yes` for 14; `communication` is empty **by
  design** (Mother Ship `DISABLE_GID_EVIDENCE`,
  `docs/audit/remaining-need-semantic-decision-packets.md`).
- *mapped-tag-has-evidence* is `yes` for all 14 non-empty maps **by row
  count**, but for `mental` and `rest` the rows are the wrong meaning, and
  for `relationship`/`focus` the rows are borrowed from another Need.
- *evidence-reaches-scoring* is `yes` for the 14 — but `score_need` is `0`
  unless a *specific candidate in the pool* carries one of the mapped ids or a
  Text hint. See Section 13/14.

---

## 12. Evidence Coverage (read-only Production measurement)

Measured via the sanctioned read-only bridge
(`scripts/migration_safety/readonly_query.sh`) against Production on
2026-08-30, **after** the P8 chain (`temples` head `0101`). No write.

- GoriyakuTag master: **39 rows.**
- Canonical shrines (QA fixtures excluded by name convention): **103.**
- Candidate-pool eligible (lat/lng present, address non-empty): **103** (all).
- Canonical shrines with ≥1 `goriyaku_tags` link: **100 / 103.** (The 3
  without: consistent with `0097`/P5-DATA having stripped `21`/`22`'s tags
  and one further shrine.)
- Total `temples_shrine_goriyaku_tags` rows: **296.**

Per-GoriyakuTag canonical-shrine coverage (all also candidate-eligible):

| id | name | shrines | id | name | shrines | id | name | shrines |
|---|---|---|---|---|---|---|---|---|
| 6 | 開運 | 60 | 1 | 縁結び | 33 | 27 | 出世運 | 3 |
| 2 | 厄除け | 53 | 11 | 勝運 | 20 | 29 | 芸能運 | 3 |
| 7 | 家内安全 | 28 | 4 | 商売繁盛 | 18 | 36 | 心願成就 | 3 |
| 12 | 仕事運 | 11 | 9 | 学業成就 | 8 | 13 | 航海安全 | 2 |
| 3 | 交通安全 | 7 | 16 | 安産 | 6 | 22 | 美容 | 2 |
| 14 | 海上安全 | 5 | 10 | 合格祈願 | 4 | 28 | 金運 | 2 |
| 20 | 恋愛成就 | 4 | 5 | 五穀豊穣 | 3 | 33 | 病気平癒 | 2 |
| 13 | 航海安全 | 2 | 22 | 美容 | 2 | 34 | 火防 | 2 |

On **exactly 1 canonical shrine each** (16 tags): 8 福徳, 15 武運長久,
17 八方除, 18 夫婦円満, 19 八難除, 21 導き, 23 方除け, 24 健康長寿, 25 芸能,
26 家庭円満, 30 強運厄除け, 31 技芸上達, 32 八方除け, 35 子宝, 37 延命長寿,
38 足腰健康, 39 農業守護.

Usable GID evidence by Need (union of mapped ids' canonical shrine counts —
upper bound; a single request only benefits from candidates actually in the
scored pool):

| Need | mapped GID names (shrines) | practical evidence reach |
|---|---|---|
| protection | 厄除け(53), 勝運(20), 八方除け(1) | **HIGH** |
| career | 開運(60), 仕事運(11), 出世運(3), 導き(1), 強運厄除け(1) | **HIGH** (but 開運 is generic) |
| courage | 仕事運(11), 恋愛成就(4), 武運長久/夫婦円満/健康長寿/強運厄除け/足腰健康(1 ea) | **MODERATE** (11) |
| love | 縁結び(33), 恋愛成就(4) | **HIGH** |
| marriage | 縁結び(33), 夫婦円満(1) | **HIGH** (via 縁結び) |
| relationship | 縁結び(33) | **HIGH count / LOW precision** |
| money | 商売繁盛(18), 金運(2), 五穀豊穣(3), 心願成就(3) | **MODERATE** (≈18–24) |
| mental | 勝運(20), 金運(2), 家庭円満(1), 足腰健康(1) | **count MODERATE / semantics WRONG** |
| health | 家内安全(28), 病気平癒(2), 健康長寿(1), 福徳(1), 足腰健康(1) | **count MODERATE / precision LOW** (家内安全) |
| study | 学業成就(8), 合格祈願(4) | **MODERATE**, clean |
| focus | 学業成就(8), 合格祈願(4) | **MODERATE**, borrowed |
| rest | 家内安全(28), 福徳(1) | **count MODERATE / semantics WRONG** |
| travel_safe | 交通安全(7), 海上安全(5), 航海安全(2) | **MODERATE**, clean |
| family | 安産(6), 子宝(1) | **LOW**, clean |
| communication | — | **NONE (by design)** |

Text evidence: only 7 Needs have `NEED_TEXT_WEIGHTS`; it matches a shrine's
own `goriyaku`/`description` prose, not the query. It is a fallback channel
for `study/career/courage/mental/love/money/rest` and absent for the other 8.

No new Production data was created. Evidence eligibility follows the existing
reviewed `goriyaku_tags` contract only — no inference from shrine name,
deity, history, tradition, or raw `goriyaku` prose (that prose is used *only*
by the separately-scoped `NEED_TEXT_WEIGHTS` channel, which is the existing
contract, not a new inference).

---

## 13. C1 / `score_need` / Ranking Trace

### 13.1 How the interpreted Need reaches the score (`_attach_breakdown`)

```text
need_tags (≤3)  ×  candidate
  matched_by_tag  = need_tags ∩ candidate.astro_tags                → each +2 (flat, unconditional)
  matched_by_gid  = need_tags whose NEED_TO_GORIYAKU_IDS ∩ candidate.goriyaku_tag_ids
  matched_by_text = need_tags whose NEED_TEXT_WEIGHTS hint ∈ (candidate.goriyaku + description)
  C1 Max per tag  = for tag in gid∪text:  max(gid_weighted=2.0 , text_raw×1.2)   (tie → gid)
  study_bonus     = +1 (rank) if "study" in need_tags and a STUDY_SHRINE_HINT ∈ material
  history boost   = HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS[axis][candidate.history_theme]

  score_need                 = len(matched_by_tag ∪ matched_by_text ∪ matched_by_gid)   ← PUBLIC contract field
  score_need_rank            = len(matched_by_tag)*2 + gid_text_contribution + study_bonus
  score_need_rank_weighted   = len(matched_by_tag)*2.0 + gid_text_contribution_weighted + study_bonus + history_boost
  score_total (public)       = score_element*w1 + score_need*w2 + score_popular*w3 + astro_bonus
```

Final ordering (`_sort_chat_recommendations`, default mode) uses
`resolve_score_sort_key` (Score v3 mode), then `distance_m`, then name, then
`_diversify_by_need(limit=3)`.

### 13.2 Failure cases observed / derivable

| case | interpreter | mapping | evidence in pool | outcome |
|---|---|---|---|---|
| `communication` only (e.g. `プレゼンで話すのが苦手`) | detects `communication` | empty GID, no text weights | n/a | `score_need = 0` from the communication signal — C1 NONE branch, contract-correct per Mother Ship. Ordering = popularity/distance. **SCORING_GAP by design.** |
| `mental` / `rest` emotional-state query with no 厄/浄化/縁 token | detects `mental`/`rest` | maps to 勝運/家内安全/福徳/… | those tags exist on 1–28 shrines, but a *calm/anxiety* consultation rarely surfaces those shrines high in the popularity pool, and when it does the match is the wrong meaning | `score_need` often 0–1; ranking driven by popularity. **EVIDENCE_GAP + NEED_GORIYAKU_MAPPING_GAP.** |
| Need detected, GID mapping fine, but the mapped tag is rare (`夫婦円満` 1, `福徳` 1, `導き` 1) | ok | ok | ≤1 shrine, likely not in the scored pool for a given area | `score_need = 0` for most requests. **EVIDENCE_GAP.** |
| Need detected, a mapped GID *does* hit a pooled shrine | ok | ok | yes | `score_need ≥ 1`; C1 Max adds +2 (gid) or `text×1.2` to `score_need_rank_weighted`; may still be outweighed by `score_popular`/`distance` for a far or unpopular shrine. **RANKING_GAP (soft).** |
| `astro_tags` match | — | — | — | flat +2 per tag, **unconditional**, can dominate a weak-evidence need match. |
| axis-aligned `history_theme` | — | — | — | `history_theme_candidate_boost` (0.0–~small) added to weighted rank + prefilter; the only place `consultation_axis` touches ranking. |

`score_need` (public) is an **integer count of matched channels**, not a
graded semantic-fit score. Two candidates each matching one tag by GID tie at
`score_need = 1` regardless of how well `勝運` vs `縁結び` fits the query.

---

## 14. Candidate / C1 / Ranking findings (enumerated per Section 14 of the brief)

- **Interpreter detects the Need but C1 receives no usable signal:**
  `communication` (empty map, no text weights) — *always*. `mental`/`rest`
  when the query is purely emotional-state wording — *frequently*.
- **Mapping exists but no eligible Evidence in the pool:** any Need whose only
  well-populated mapped tag is generic (`career`→開運; `relationship`→縁結び)
  will "match" but on a semantically loose basis; any Need mapped to a
  1-shrine tag (`marriage`→夫婦円満, `courage`→武運長久, etc.) gets nothing
  from that id.
- **Evidence exists but `score_need` stays 0:** occurs whenever none of the
  ≤100 pooled (popularity-ordered) shrines carries a mapped GID / text hint /
  astro tag for the detected Need — the pool is not Need-filtered on the
  free-text path.
- **`score_need` positive but rank barely moves:** `w2` (need weight) is one
  term among `score_element*w1 + score_need*w2 + score_popular*w3 +
  astro_bonus`; a single-channel `score_need = 1` on a low-popularity distant
  shrine loses to a high-popularity near shrine with `score_need = 0`.
- **Another dimension dominates:** `score_popular` (0–1 from
  `popular_score/10`), `distance` decay, `astro` flat +2/tag, and (compat
  mode) `astro_bonus` up to 0.6 routinely outweigh a thin need match.
- **No CANDIDATE_GAP:** the canonical pool is 103 and the free-text path
  scores essentially all of it, so "the right shrine wasn't a candidate" was
  not observed. The gap is that the right shrine isn't *scored up*.

---

## 15. Natural-Language Case Matrix

34 cases. `need_tags` / `axis` / `GID` are **actual** offline output of
`extract_need_tags` + `resolve_consultation_axis` + `need_tags_to_goriyaku_ids`
on base `4d7685f0`. `state/outcome` from `interpret_consultation` (shadow).
"Expected (audit)" is an audit expectation only — **not** a product
requirement. Score/rank/Lead columns are reasoned from Section 13 (offline;
per-request ranking depends on area/pool and was not run against a live DB).

| id | input | expected (audit) | actual need_tags | actual axis | actual GID (names) | shadow state/outcome | first loss point |
|---|---|---|---|---|---|---|---|
| Career-A | 転職して新しい環境に進みたい | career + forward intent | `['career']` | career_change (query) | 開運, 仕事運, 導き, 出世運, 強運厄除け | –/– | none (topic ok; "新環境へ進みたい" intent dropped, acceptable) |
| Career-B | 転職したいけど一歩踏み出すのが怖い | career + fear/hesitation | `['career','courage']` | career_change (query) | 開運,仕事運,武運長久,夫婦円満,恋愛成就,導き,健康長寿,出世運,強運厄除け,足腰健康 | anxious/– | INTERPRETER_MISS (fear not modelled; courage from 踏み出す masks it) + MULTI_SIGNAL_LOSS (GID union to 10, incl. 夫婦円満/恋愛成就) |
| Career-C | 今の仕事を続ける自信がなくなってきた | career + loss of confidence | `['career','mental']` | career_change (need_tags) | 開運,勝運,仕事運,導き,家庭円満,出世運,金運,強運厄除け,足腰健康 | –/– | NEED_GORIYAKU_MAPPING_GAP (mental→勝運/金運/…; confidence not served) |
| Career-D | 仕事が忙しくて気持ちが落ち着かない | overwhelm / wants calm | `['career','rest']` | career_change (need_tags) | 開運,家内安全,福徳,仕事運,導き,出世運,強運厄除け | –/calm | NEED_GORIYAKU_MAPPING_GAP (rest→家内安全/福徳) |
| Career-E | 仕事に集中できない | focus at work | `['career','focus']` | **study_success** (query) | 開運,学業成就,合格祈願,仕事運,導き,出世運,強運厄除け | –/– | THEME_FREE_TEXT_CONFLICT / axis overmatch (集中→study axis overrides career) |
| Career-F | 職場の人間関係がうまくいかない | workplace relationship strain | `['relationship']` | relationship_repair (query) | 縁結び | –/– | NEED_GORIYAKU_MAPPING_GAP (relationship→縁結び, romantic) |
| Love-A | 新しい出会いがほしい | new romantic connection | `['love']` | relationship_repair | 縁結び, 恋愛成就 | –/– | none |
| Love-B | 今の恋人との関係を大切にしたい | nurture existing relationship | `['love']` | relationship_repair | 縁結び, 恋愛成就 | –/– | PARTIAL — "維持/大切に" vs "出会い" not distinguished |
| Love-C | 結婚について迷っている | marriage + indecision | `['marriage']` | relationship_repair | 縁結び, 夫婦円満 | uncertain/– | none (topic ok; indecision shadow-only) |
| Love-D | 好きな人に気持ちを伝える勇気がほしい | courage to confess | `['communication','courage']` | **restart_mindset** (need_tags) | 仕事運,武運長久,夫婦円満,恋愛成就,健康長寿,強運厄除け,足腰健康 | –/– | NEED_GORIYAKU_MAPPING_GAP (communication empty; courage→仕事運/武運…); axis restart_mindset odd |
| Love-E | 別れた人のことを引きずっていて気持ちを整理したい | grief / closure | `[]` | other (fallback) | — | –/clarify | INTERPRETER_MISS (no signal at all) |
| Family-A | 家族が穏やかに過ごせたらいい | family peace | `['relationship','rest']` | rest_healing (query) | 縁結び, 家内安全, 福徳 | –/– | PARTIAL — 家族→relationship(縁結び); "family harmony" not `family` tag |
| Family-B | 子どものことが心配 | worry about child | `[]` | other (fallback) | — | anxious/– | INTERPRETER_MISS (no signal) |
| Family-C | 出産を控えていて不安 | prenatal anxiety | `['family','mental']` | restart_mindset (need_tags) | 勝運,安産,家庭円満,金運,子宝,足腰健康 | anxious/– | PARTIAL — `family`→安産/子宝 good; `mental`→勝運/金運 off; axis restart_mindset off |
| Family-D | 家族との関係で悩んでいる | family relationship strain | `['relationship']` | relationship_repair (query) | 縁結び | uncertain/– | NEED_GORIYAKU_MAPPING_GAP (縁結び) |
| MR-A | 最近ずっと気持ちが落ち着かない | restlessness / unsettled | `['rest']` | rest_healing (need_tags) | 家内安全, 福徳 | –/calm | NEED_GORIYAKU_MAPPING_GAP (rest→家内安全/福徳) |
| MR-B | 何もしたくないくらい疲れている | exhaustion | `['mental','rest']` | rest_healing (query) | 家内安全,福徳,勝運,家庭円満,金運,足腰健康 | tired/– | EVIDENCE_GAP + NEED_GORIYAKU_MAPPING_GAP (no calm/healing tag in master) |
| MR-C | 少し立ち止まって休みたい | pause / rest | `['rest']` | rest_healing (query) | 家内安全, 福徳 | tired/– | NEED_GORIYAKU_MAPPING_GAP |
| MR-D | 不安はあるけど前に進みたい | anxious but wants to move | `['mental']` | restart_mindset (need_tags) | 勝運, 家庭円満, 金運, 足腰健康 | anxious/move_forward | MULTI_SIGNAL_LOSS (前に進みたい dropped — `前に進` runtime-absent) + mapping gap |
| Neg-1 | 恋愛の相談ではない | NOT love | `['love']` | relationship_repair | 縁結び, 恋愛成就 | –/– | NEGATION_FAILURE |
| Neg-2 | 転職したいわけではない | NOT career | `['career']` | career_change | 開運,仕事運,導き,出世運,強運厄除け | –/– | NEGATION_FAILURE |
| Neg-3 | 不安ではないけど迷っている | indecision, NOT anxiety | `['mental']` | restart_mindset | 勝運,家庭円満,金運,足腰健康 | anxious/– | NEGATION_FAILURE (matched 不安) + INTERPRETER_MISS (迷い runtime-absent) |
| Neg-4 | 結婚より今は仕事を優先したい | career priority, NOT marriage | `['marriage','career']` | **relationship_repair** | 縁結び,開運,仕事運,夫婦円満,導き,出世運,強運厄除け | –/– | NEGATION_FAILURE + THEME_FREE_TEXT_CONFLICT (axis→relationship_repair) |
| Neg-5 | 休みたいというより環境を変えたい | wants change, NOT rest | `['rest']` | rest_healing | 家内安全, 福徳 | tired/ready_to_change | NEGATION_FAILURE (matched 休みたい) + INTERPRETER_MISS (環境を変えたい absent) |
| Theme-1 | 新しい仕事に挑戦したい | career + challenge | `['career','courage']` | career_change (need_tags) | 開運,仕事運,武運長久,夫婦円満,恋愛成就,導き,健康長寿,出世運,強運厄除け,足腰健康 | –/– | MULTI_SIGNAL_LOSS (GID union to 10) — otherwise ok |
| Theme-2 | 最近疲れていて少し休みたい | fatigue + rest | `['mental','rest']` | rest_healing (query) | 家内安全,福徳,勝運,家庭円満,金運,足腰健康 | tired/– | NEED_GORIYAKU_MAPPING_GAP |
| Theme-3 | 恋愛より仕事のことで悩んでいます | work worry, not romance | `['love','career']` | **relationship_repair** | 縁結び,開運,仕事運,恋愛成就,導き,出世運,強運厄除け | uncertain/– | NEGATION_FAILURE (恋愛 matched despite より) + axis mis-pick |
| Money-A | もっと稼ぎたい | money | `['money']` | money_growth (query) | 商売繁盛, 五穀豊穣, 金運, 心願成就 | –/– | none (五穀豊穣/心願成就 loose but 商売繁盛/金運 carry it) |
| Study-A | 資格試験に合格したい | study/exam | `['study']` | study_success (query) | 学業成就, 合格祈願 | –/– | none |
| Travel-A | 家族旅行の安全を祈願したい | travel safety | `['relationship','travel_safe']` | **relationship_repair** | 縁結び, 交通安全, 航海安全, 海上安全 | –/– | MULTI_SIGNAL_LOSS (家族→relationship added; axis→relationship_repair not travel) |
| Health-A | 健康で長生きしたい | health/longevity | `['health']` | **other** (fallback) | 家内安全, 福徳, 健康長寿, 病気平癒, 足腰健康 | –/– | PURPOSE_NEED_MAPPING_GAP (health has no axis) + precision (家内安全 dominates) |
| Protect-A | 最近流れが悪いのでお祓いしたい | cleansing / protection | `['protection','mental']` | restart_mindset (need_tags) | 厄除け,勝運,家庭円満,金運,八方除け,足腰健康 | –/– | none for protection (厄除け 53 strong); `mental` co-fires from 流れが悪い (MULTI_SIGNAL_LOSS minor) |
| Courage-A | 背中を押してほしい | encouragement | `['courage']` | restart_mindset (need_tags) | 仕事運,武運長久,夫婦円満,恋愛成就,健康長寿,強運厄除け,足腰健康 | –/move_forward | NEED_GORIYAKU_MAPPING_GAP (scattered; 開運 — the natural fit — is NOT in courage's map) |
| Focus-A | 集中力を高めて勉強を継続したい | focus + study | `['study','focus']` | study_success (query) | 学業成就, 合格祈願 | –/– | none (focus borrows study evidence; acceptable) |

---

## 16. Failure Classification

Counts across the 34 cases (a case may carry more than one; `BOTH` used only
where two layers are clearly jointly responsible). "Root cause" (first loss
point) counts are in Section 17 and are the authoritative single-attribution.

| category | count (any-layer) | representative cases |
|---|---|---|
| `INTERPRETER_MISS` | 8 | Love-E, Family-B (total miss); Career-B (fear), MR-D & Neg-3 & Neg-5 (asserted clause missed), Career-C (confidence only via bare 自信), Family-A ("family harmony") |
| `INTERPRETER_OVERMATCH` | 3 | Career-E (集中→study axis), Protect-A (`mental` co-fires on 流れが悪い), Travel-A (`relationship` co-fires on 家族) |
| `NEGATION_FAILURE` | 5 | Neg-1, Neg-2, Neg-3, Neg-4, Neg-5 (+ Theme-3 via より) |
| `MULTI_SIGNAL_LOSS` | 4 | Career-B, Theme-1 (GID union to 10 incl. off-topic ids), MR-D, Travel-A |
| `THEME_FREE_TEXT_CONFLICT` | 4 | Career-E, Neg-4, Theme-2 (fatigue overrides notional theme), Theme-3 |
| `PURPOSE_NEED_MAPPING_GAP` | 2 | Health-A (`health` → axis `other`), `independence`/`nature_reset` axes unreachable from need_tags |
| `NEED_GORIYAKU_MAPPING_GAP` | 7 | Career-C/D, Career-F, Family-D, MR-A/C, Courage-A, Love-D (communication empty) |
| `EVIDENCE_GAP` | 4 | MR-B, Theme-2, marriage→夫婦円満(1), family→子宝(1) |
| `CANDIDATE_GAP` | 0 | — (pool = whole canonical set) |
| `SCORING_GAP` | 3 | communication (C1 NONE by design), `score_need` = flat channel count (no graded fit), astro flat +2 can dominate |
| `RANKING_GAP` | 2 | thin `score_need` outweighed by `score_popular`/`distance`; `_diversify_by_need` can reorder near-ties |
| `LEAD_GAP` | 2 | `health` Lead may cite 家内安全 (documented limitation); generic fallback Lead when `score_need=0` |
| `REASON_GAP` | 3 | generic "今の悩みや願いに合わせて…" when no match; Reason foregrounds user-picked tag over free-text nuance on conflict; `communication` Reason has no evidence to cite |
| `DATA_GAP` | 3 | no `癒し`/`静寂`/`rest` GoriyakuTag in the 39-row master; `夫婦円満`/`福徳`/`導き`/… on only 1 shrine each; 3/103 canonical shrines have 0 `goriyaku_tags` |
| `DOC_CODE_DRIFT` | 3 | 15-row stale `fixtures/goriyaku_tags.json` vs 39-row runtime master; `consultation_interpreter.NEED_KEYWORDS` vs `domain/need_tags.KEYWORDS` drift; `interpretation_profile` computed-but-shadow (docstring says "prepares structured input for … future Score v3" — matches code, but product surface implies it is used) |

---

## 17. First-Loss-Point Analysis (mandatory)

For each case, the **first** layer at which the audit-expected meaning is lost:

| first-loss layer | cases | count |
|---|---|---|
| **INTERPRETER** (miss or overmatch before Need is formed) | Love-E, Family-B, Career-B, Career-E, Neg-3, Neg-5, MR-D, Career-C | 8 |
| **NEGATION** (interpreter fired on negated text) | Neg-1, Neg-2, Neg-4, Theme-3, (Neg-3 counted at interpreter) | 4 |
| **NEED→GORIYAKU mapping** (Need correct, mapped ids wrong/loose) | Career-D, Career-F, Family-D, MR-A, MR-C, Courage-A, Love-D | 7 |
| **EVIDENCE** (Need + mapping fine, no eligible shrine in pool) | MR-B, Theme-2, (marriage/夫婦円満 & family/子宝 as structural) | 4 |
| **AXIS / MULTI-SIGNAL** (Need list ok, axis mis-pick or GID dilution changes framing) | Neg-4→axis, Travel-A, Theme-1, Protect-A | 4 |
| **none lost** (topic + evidence adequate) | Career-A, Love-A, Love-C, Money-A, Study-A, Focus-A | 6 |

Rule applied: e.g. Career-F — interpreter *correctly* yields `relationship`,
Need is right, so the loss is at **mapping** (`relationship → {縁結び}`), not
`INTERPRETER_MISS`. e.g. Love-E — interpreter yields nothing, so the loss is
at **INTERPRETER**, regardless of downstream.

---

## 18. Known Gaps (audit facts, not proposals)

1. **No negation / de-emphasis handling** at any layer (`ない`, `わけではない`,
   `より`, `というより`). 5–6 of 34 cases mis-fire.
2. **No clause segmentation** — the whole query is one match surface, so
   `A けど B` and `A より B` both contribute A and B equally.
3. **State and Intention are not first-class runtime signals.** They exist
   only in the shadow `interpretation_profile` (STATE/OUTCOME/DECISION/
   CONSTRAINT/DIRECTION) and in Score v3 shadow components — neither reaches
   `need_tags`, `score_need`, ranking, Lead, or Reason.
4. **`mental` and `rest` GID mappings do not denote their concept.**
   `mental → {勝運, 家庭円満, 金運, 足腰健康}`, `rest → {家内安全, 福徳}`.
   There is **no** `癒し` / `静寂` / `心の平安` GoriyakuTag in the 39-row
   master to map to (DATA_GAP).
5. **`communication` has no GID evidence and no Text weights** — a
   communication-only consultation contributes `score_need = 0` from that
   signal (Mother Ship `DISABLE_GID_EVIDENCE`, intended).
6. **`relationship → {縁結び}`** conflates workplace/family relations with
   romantic bonds; **`focus → {学業成就, 合格祈願}`** borrows study evidence;
   **`career`/`courage`** lean on generic `開運`/`強運厄除け`.
7. **`courage` map omits `開運` (id 6)** even though 開運 is `courage`'s
   strongest `NEED_TEXT_WEIGHTS` hint and 開運 covers 60 shrines; `career`
   holds id 6 instead.
8. **`consultation_axis` is need-tag-fallback-driven for several inputs**, so
   a secondary co-fired tag (`家族`→`relationship`, `結婚`→`marriage`) can
   flip the axis away from the user's stated focus (Neg-4, Travel-A, Theme-3).
   `independence`, `nature_reset`, `health` have no `need_tag` producer.
9. **`score_need` (public) is a channel *count*, not a graded fit.** All
   single-channel matches tie at 1; `astro_tags` contributes a flat
   unconditional +2/tag that can outrank a real (but thin) need match.
10. **Popularity / distance routinely dominate** a 1-channel `score_need` on
    the free-text path (the pool is not Need-filtered).
11. **Reason/Lead degrade to generic copy** whenever `score_need = 0`, and can
    foreground a user-picked `goriyaku_tag_id` over unmatched free-text
    nuance; `health` Lead may cite `家内安全` (documented in
    `docs/audit/compass-need-lead-purpose-alignment.md`).
12. **DOC_CODE_DRIFT:** stale 15-row `fixtures/goriyaku_tags.json`; two
    drifted copies of the need-keyword list (`domain/need_tags` runtime vs
    `consultation_interpreter` shadow — the shadow copy has richer vocab that
    never takes effect).
13. **3 / 103 canonical shrines carry zero `goriyaku_tags`** (post-P5/P8);
    16 GoriyakuTags are on exactly 1 shrine each — thin evidence tail.

---

## 19. Mother Ship Decision Candidates

**None selected. None implemented. Not ranked as product priority.** Each is
one direction that *could* address an observed gap; all carry risk and all
require an explicit decision.

| # | observed problem (section) | candidate direction | affected layer | affected audit cases | risk | work type |
|---|---|---|---|---|---|---|
| C1 | Negation mis-fires (§10, §17: 5–6 cases) | add a negation/de-emphasis guard (`…ない`, `わけではない`, `より`, `というより`) that suppresses hits in the negated span | interpreter (`domain/need_tags`, `consultation_axis`) | Neg-1…5, Theme-3 | over-suppression of legit hits; JA parsing is heuristic; needs its own test corpus | code + tests |
| C2 | Whole-query match surface (§7.1, §9) | clause-split on `けど/が/より/。/、` and weight/section the segments | interpreter | Career-B, Neg-4, Theme-2/3 | changes which tag is "primary"; ranking sensitivity | code + tests |
| C3 | State not load-bearing (§8.2, §18.3) | promote selected `state_profile` signals (tired/anxious/uncertain) into a runtime signal that biases ranking or Reason | interpreter → scoring/Reason | Career-C, Family-B/C, MR-*, Neg-3 | Score v3 is still shadow; wiring it in is a scoring-behaviour change; needs A/B | code + taxonomy + tests |
| C4 | Intention not load-bearing (§8.3) | represent "decide / move-forward / repair / leave / rest" as an Intention signal feeding axis or Reason | interpreter → axis/Reason | Career-A/B, MR-D, Neg-5, Love-E | new taxonomy dimension; product-defining | taxonomy + code + tests |
| C5 | `mental`/`rest` GID mapping wrong concept; no calm/healing tag exists (§11, §18.4, §18 DATA_GAP) | add a `癒し`/`心の平安`/`静穏` GoriyakuTag to the master + reviewed shrine evidence, then remap `mental`/`rest` | GoriyakuTag master + Evidence + `NEED_TO_GORIYAKU_IDS` | MR-A/B/C, Theme-2, Career-D | new taxonomy row is a data + review project (P8-class); every shrine needs re-review; ranking shifts for all rest/mental queries | data + evidence + taxonomy + code |
| C6 | `communication` has no evidence (§11, §12) | define a communication-specific GoriyakuTag + evidence, or an approved Text-evidence set; then populate `NEED_TO_GORIYAKU_IDS["communication"]` | taxonomy + Evidence + mapping | Love-D and any 話す/伝える/プレゼン query | Mother Ship already set `DISABLE_GID_EVIDENCE` — reversing needs a taxonomy decision first | data + taxonomy + code |
| C7 | `relationship → {縁結び}` romantic borrow (§11) | add a non-romantic-relations GoriyakuTag (e.g. `人間関係円満`/`和合`) + evidence, remap | taxonomy + Evidence + mapping | Career-F, Family-A/D | same as C5 (data project); `縁結び` fallback removal changes 33-shrine reach | data + taxonomy + code |
| C8 | `courage` map omits `開運` (id 6) though it's the strongest text hint & 60-shrine tag (§18.7) | move / add id 6 to `courage`'s GID set | `NEED_TO_GORIYAKU_IDS` only | Courage-A, Career-B, Theme-1 | 開運 is generic — could over-broaden `courage` matches; interacts with `career`'s existing id-6 hold | code + tests |
| C9 | GID union balloons with ≥2 need_tags (§10, §15 Career-B/Theme-1) | cap or de-duplicate the per-request GID set, or weight by need_tag priority | scoring (`_attach_breakdown` gid path) | Career-B, Theme-1, Travel-A | reduces recall for genuinely multi-need queries | code + tests |
| C10 | `score_need` is a flat channel count; astro flat +2 can dominate (§13, §18.9) | grade `score_need` by semantic-fit (e.g. GID exact-concept > generic > borrowed) and/or gate the astro +2 | scoring | most thin-match cases | re-tunes ranking globally; needs offline snapshot + A/B | code + measurement |
| C11 | axis flips on secondary co-fired tag; `health`/`independence`/`nature_reset` unreachable from need_tags (§8, §18.8) | add `health`→(new axis or `rest_healing`), make axis prefer the *highest-priority* need_tag not the first mapped one | `consultation_axis` | Health-A, Neg-4, Travel-A, Theme-3 | axis feeds `history_theme_candidate_boost` — real ranking effect | code + tests |
| C12 | Reason generic when `score_need = 0` (§15, §16 REASON_GAP) | a nuance-aware fallback Reason that reflects the detected (even unscored) Need/State | Reason (`build_recommendation_reason`) | communication-only, MR-*, Love-E | risk of claiming a fit the ranking didn't find — must stay honest per `recommendation-signal-authority.md` | code + copy + tests |
| C13 | vocabulary misses (§8, §17 INTERPRETER) | targeted `KEYWORDS`/`REGEX` additions: 心配, 迷い/迷って, 引きずる, 環境を変えたい, 前に進みたい (align runtime with the richer shadow list) | interpreter | Family-B, Love-E, Neg-3, Neg-5, MR-D | over-match; each addition needs a negative-case check; do **not** just merge the shadow list wholesale | code + tests |
| C14 | DOC_CODE_DRIFT (§4, §16) | delete/regenerate `fixtures/goriyaku_tags.json` to the 39-row master; converge or clearly separate the two need-keyword lists | fixtures / interpreter modules | n/a (hygiene) | low behaviour risk; fixture may be referenced by other tests | code + tests |
| C15 | `score_need = 0` because pool isn't Need-filtered on free-text path (§13, §14) | apply `need_tags_to_goriyaku_ids` as a soft candidate-pool boost (not a hard filter) in `build_chat_candidates` | candidate generation | all thin-evidence emotional queries | changes the pool for every free-text request; interacts with distance mode | code + measurement |

---

## 20. Final Audit Verdict

```text
RECOMMENDATION_NUANCE_AUDIT_STATUS = COMPLETE

INTERPRETER_COVERAGE   = TOPIC_SUPPORTED / STATE_PARTIAL / INTENTION_MINIMAL
                         (15 need_tags, flat keyword+regex, no negation,
                          no clause segmentation; State/Intention exist only
                          in a shadow profile that does not reach ranking)

NEED_MAPPING_STATUS    = PRESENT_BUT_UNEVEN
                         (14/15 non-empty; communication empty by design;
                          mental & rest semantically mismatched; relationship
                          & focus borrowed; career & courage lean on generic
                          luck tags; courage omits 開運)

EVIDENCE_COVERAGE_STATUS = MEASURED / ADEQUATE_FOR_COMMON_TOPICS_THIN_ELSEWHERE
                         (39-tag master; 100/103 canonical shrines carry ≥1
                          tag; strong for protection/love/marriage/career;
                          moderate for money/study/travel_safe; weak or
                          wrong-concept for mental/rest/family/communication;
                          16 tags on 1 shrine each; no calm/healing tag)

SCORING_TRACE_STATUS   = TRACED / KNOWN_LIMITATIONS
                         (score_need = flat channel count; astro flat +2;
                          popularity & distance dominate thin need matches;
                          consultation_axis touches rank only via
                          history_theme_candidate_boost; communication → C1
                          NONE by design)

EXPLANATION_TRACE_STATUS = TRACED / EVIDENCE_BOUNDED
                         (Lead/Reason cite the C1-winning evidence; degrade to
                          generic copy at score_need = 0; can foreground a
                          user-picked tag over unmatched free-text nuance;
                          health Lead may cite 家内安全 — documented)

BLOCKERS = 0
```

No blocker to safe operation or to a Mother Ship decision was found. The 15
findings in Section 19 are decision candidates only. Nothing in this audit was
implemented; no interpreter, mapping, taxonomy, scoring, ranking, evidence,
shrine, Knowledge, Source, copy, migration, Production, Spreadsheet, or
frontend artefact was changed.

---

## Appendix A — Method / Reproducibility

- **Code read** at `origin/develop` `4d7685f0` (post PR #2645), files in §4.
- **Interpreter executed offline** (no DB, no behaviour change) via
  `extract_need_tags`, `resolve_consultation_axis`, `need_tags_to_goriyaku_ids`,
  `interpret_consultation` on the 34 §15 cases —
  `USE_GIS=0 USE_SQLITE=1` pure-function invocation with the repo's venv
  (`/Users/morietsu/Developer/jinja_app/.venv`, Django 5.2.16).
- **Evidence coverage** measured read-only against Production 2026-08-30 via
  `scripts/migration_safety/readonly_query.sh` (SELECT-only, allow-listed,
  credential never in argv/log). Queries: GoriyakuTag master, canonical
  shrine population with the `exclude_qa_fixture_shrines` name filter,
  per-tag shrine link counts. **No write.**
- **Focused test run:** `NOT_RUN` — the local `test_jinja_db` is in a broken
  state (`must be owner of database test_jinja_db` on recreate; a closed
  cursor on `--reuse-db`). Repairing a shared local Postgres DB is out of
  scope for a read-only audit. CI (`unit` + `integration`) on the branch PR
  exercises the interpreter/need/reason suites
  (`test_need_to_goriyaku_tag_ids.py`,
  `test_communication_interpreter_coverage.py`,
  `test_marriage_interpreter_coverage.py`,
  `test_mental_rest_interpreter_coverage.py`,
  `test_concierge_need_contract.py`, `test_concierge_need_variation.py`,
  `test_need_lead_purpose_alignment.py`, `test_reason_*.py`).
- `git diff --check`: clean. Only this file added.
