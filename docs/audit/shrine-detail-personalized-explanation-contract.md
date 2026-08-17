> **Status: Audit only.** No production code, UI, Backend, Ranking, Serializer, Model, or migration
> was changed to produce this document (`git diff` on application code = 0). This audit does not add
> astrology/九星/goriyaku vocabulary to the UI, does not invent a new Recommendation reason, and does
> not reimplement Ranking Authority in the Frontend. It exists to determine — with code and real
> persisted-data evidence, not inference — which signals genuinely contributed to a given
> Recommendation, and to define the responsibility boundary for translating only those into a
> Personalized Explanation.

# Shrine Detail Personalized Explanation Authority & Translation Contract Audit

Each finding is labeled **FACT** (read directly from code or real DB data, with citation),
**INFERENCE** (a conclusion drawn from FACTs, stated as such), or **PROPOSAL** (a design idea for a
future PR, not implemented, not authorized here). Any cell that cannot be confirmed from code is
marked `UNCONFIRMED` rather than guessed.

## 0. Headline Findings (read this first)

Traced end-to-end using a **real persisted recommendation** (`ConciergeThread.id=800`, shrine
妙義神社/id=88, `consultation_axis="restart_mindset"`, matched `history_theme="勝負"`,
`matched_need_tags=["courage"]`) — both the raw persisted JSON (§9) and the actual rendered Shrine
Detail page at `/shrines/88?ctx=concierge&tid=800` (§9) — three concrete problems were found, none
of which are hypothetical:

1. **The signal that actually contributed to Ranking never appears in the displayed text.**
   `consultation_axis="restart_mindset"` mediated a real, non-zero Ranking contribution
   (`history_theme_candidate_boost.contribution = 0.24`, §9.3) for this exact shrine, but
   `consultation_axis` has **zero references** anywhere in
   `backend/temples/services/shrine_meaning_composer.py` — the exact Backend service that generates
   "今のあなたとの接点"/"この場所が合う理由"/"今の状態" (§4.1, confirmed by direct grep, zero
   matches). The rendered page never states what about the user's consultation caused the match.
2. **A Backend logic gap makes the summary understate a real Primary reason.** When
   `primary_reason_source == "history_theme"` (the *highest*-priority reason per
   `PRIMARY_REASON_PRIORITY`, `recommendation-signal-authority.md` §4), `_to_rank_explanation()`
   (`concierge_chat_ranking.py:1863-1972`) computes `primary_axis` from a fixed set —
   `{"user_selected_tag", "need_tag", "goriyaku_tag", "text_hint"}` → `"need"`, `"element"` →
   `"element"`, **everything else → `"fallback"`** — and `"history_theme"` is not a member of that
   set. For thread 800, this produced `primary_axis: "fallback"`, `primary_axis_ja: "近さ"`, and a
   summary sentence "近さや候補条件を含めた総合順位です" (§9.3, real persisted data) — describing a
   genuinely strong, non-fallback match as if it were a weak proximity-only one. **Not fixed here**
   (production code unchanged) — recorded as a finding for PR-A/母艦判断.
3. **"今のあなたとの接点" and "この場所が合う理由" are near-duplicates**, and **"今の状態" is
   frequently generic boilerplate regardless of the actual consultation.** In the real trace (§9),
   both of the first two blocks resolve to the same shrine-side phrase ("決断や挑戦の前に向き合い
   [やすい神社/うための候補です]") via the identical `HISTORY_THEME_DISPLAY_COPY` lookup
   (`shrine_meaning_composer.py:179`); "今の状態" produced **the same generic sentence** on two
   entirely different shrines under entirely different consultations (real consultation vs. Direct
   Navigation with no consultation at all, §9.1/§9.2) — confirming its own fallback branch
   (`_build_consultation_summary()`, `shrine_meaning_composer.py:571-579`) is reached far more often
   than the code comment ("ユーザーの相談状態だけを整理する") implies.

These findings ground the rest of this document.

## 1. Current "この場所が合う理由" Display Blocks

**FACT**, confirmed by rendering the real trace (§9) and matching against source:

| Displayed block | Heading text (verbatim, from real render) | Backend generator |
|---|---|---|
| 今のあなたとの接点 | "今のあなたとの接点" | `_build_hero_meaning`-equivalent path — see §4.1 |
| **この場所が合う理由** | "この場所が合う理由" | `_build_shrine_meaning()` (`shrine_meaning_composer.py:589-608`) |
| 今の状態 | "今の状態" | `_build_consultation_summary()` (`shrine_meaning_composer.py:571-579`) |
| で見ること / ここで試したいこと / あとで見直したいこと | (Premium/gated) | `shrine_meaning_composer.py` action-block generators (not the audit's focus; no signal-authority concern found) |

Note the task's exact phrase "この場所が合う理由" **is** a literal, currently-rendered heading
(confirmed at `/shrines/88?ctx=concierge&tid=800`) — unlike the prior audit
([`shrine-detail-explanation-knowledge-responsibility.md`](shrine-detail-explanation-knowledge-responsibility.md))
which could not find that exact string; it is produced when `shrineMeaningPayloadV2`'s block
`shrine_meaning` (id, `payloadV2.ts:77-90`) is active and its title happens to read "この場所が合う
理由" for this data — the underlying generator is `_build_shrine_meaning()`.

## 2. Recommendation Authority — Canonical Source

**FACT**: [`docs/product/recommendation-signal-authority.md`](../product/recommendation-signal-authority.md)
is the canonical source (re-confirmed, not re-derived) for signal responsibility classification
(Eligibility / Primary / Secondary / Personalization / Context / Explanation-only). This audit adds
no new classification — it verifies *reachability and per-instance traceability* of the signals that
doc already classifies, and re-confirms nothing in that doc's Current Implementation table has
changed since [`shrine-detail-explanation-knowledge-responsibility.md`](shrine-detail-explanation-knowledge-responsibility.md)'s
prior read.

**FACT** (re-verified, `concierge_chat_ranking.py`):

- **Candidate generation**: `build_chat_candidates()` (`concierge_chat_candidates.py`) — only
  `goriyaku_tag_ids` is a DB-level hard filter (signal-authority.md §4/§6, unchanged).
- **Ranking/scoring**: the `_attach_breakdown`-equivalent function in `concierge_chat_ranking.py`
  (~line 1015 onward) computes `score_total = score_element*w1 + score_need*w2 + score_popular*w3 +
  astro_bonus` (line 1225) and the internal sort key `score_need_rank_weighted` (includes
  `history_theme_candidate_boost`, line 1160).
- **Reason generation only**: `recommendation_reason_v4.py` (Knowledge `deity`/`shrine_history`,
  Explanation-only per signal-authority.md §8) and `shrine_meaning_composer.py` (the Personalized
  Explanation text generator this audit is about).
- **Analytics/debug/metadata only**: `_debug.user_state_profile` (`concierge_chat.py:129-172`),
  `score_v3`/`score_v3_detail` (explicitly `"mode": "shadow"` in the real trace, §9.3 —
  shadow-only, does not affect real ranking, matches `recommendation_score_components.py`'s own
  docstring "Score candidate profile completeness for shadow observation only" found in the prior
  audit).

## 3. Consultation Axis

| Question | Answer | Evidence |
|---|---|---|
| 生成元 | `resolve_consultation_axis()` (`backend/temples/domain/consultation_axis.py:207`), once per request | FACT, re-confirmed unchanged from prior audit |
| Candidateへ作用するか | **No** | Not part of `build_chat_candidates()`'s filter set |
| Rankingへ作用するか | **Yes, as a Mediator** | Gates `history_theme_candidate_boost` (`concierge_chat_ranking.py:610,618`); real trace: contribution `0.24` for thread 800 (§9.3) |
| Reasonへ作用するか | **Partially** — reaches `breakdown_detail.features.history_theme_candidate_boost.consultation_axis` (raw provenance) but **not** used by `shrine_meaning_composer.py` (zero grep matches, §0/§4.1) | FACT |
| Shrine Detailまで保持されているか | **Yes, at the Backend/persisted-snapshot layer** (`rec.consultation_axis`, confirmed in real thread-800 JSON, §9.3) — **No, at the Frontend ViewModel layer**: `pickBreakdownFromThread.ts`/`pickExplanationPayloadFromThread.ts` do not extract it (re-confirmed, zero matches), `buildShrineDetailModel.ts` never references it (re-confirmed, zero matches) | FACT |
| Personalized Explanationに使用可能か | **Conditionally yes** — it is a real Primary(Mediator) signal with a verified non-zero real-instance contribution, and the finer-grained provenance (`breakdown_detail.features.history_theme_candidate_boost`) already exists Backend-side; using it safely requires (a) a new Frontend picker for `breakdown_detail` (Detail-side gap, additive) and (b) using it only when `history_theme_candidate_boost.contribution > 0` for that specific recommendation, never unconditionally | INFERENCE from FACTs above |

## 4. Goriyaku

### 4.1 Role in Recommendation

**FACT** (re-confirmed): three distinct things share the name "goriyaku" —

1. `goriyaku_tag_ids` (numeric) — Eligibility filter, contributes to `score_need` via
   `matched_by_gid` (`concierge_chat_ranking.py:1093-1121`).
2. `goriyaku` (free text) — Secondary, via `matched_by_text`.
3. `goriyaku_tags` (name strings, `Shrine.goriyaku_tags`, the shrine's **full static** catalog) —
   explanation/debug metadata in the ranking function itself; separately, this is what
   `getBenefitLabels()` (`apps/web/src/lib/shrine/getBenefitLabels.ts:8-9`) reads for Detail's "③"
   text — **unfiltered by what actually matched this consultation** (prior audit's §5 finding,
   unchanged, re-confirmed no code touched this path since).

### 4.2 ユーザー入力goriyaku vs. shrine generic goriyaku — 分離可能か

**FACT, real trace (§9.3)**: `rec.breakdown.matched_need_tags = ["courage"]` — the actual matched
tag(s) for this specific recommendation — is a **top-level field on `breakdown`**, distinct from
`shrine.goriyaku_tags` (the shrine's full, generic tag list, confirmed separately via
`getBenefitLabels()`'s source, §4.1).

**FACT**: `breakdown.matched_need_tags` **already reaches Shrine Detail's frontend ViewModel today**
— `pickBreakdownFromThread.ts:20-25` picks `rec.breakdown` wholesale (includes `matched_need_tags`
at the top level, confirmed by real data, §9.3), and `buildShrineDetailModel.ts:324`
(`getMatchedNeedTags(breakdown)`) already reads it — used internally for
`buildProposalFromBreakdown()`/`getPrimaryNeedTag()`, just not currently surfaced as an explicit,
labeled "what matched" UI element.

**Answer to "推薦に寄与したgoriyakuだけを説明根拠として取得可能か"**: **Yes, already, no gap.** This
is the one signal in this audit that needs no new wiring — `matched_need_tags` is exactly the
"recommendation-driving" set, already at the Detail render boundary, already distinguishable from
the shrine's generic tag catalog.

## 5. Astrology (Western Zodiac / 4-Element)

**FACT** (re-confirmed): `backend/temples/domain/astrology.py` — `sun_sign_and_element()`/
`element_priority()` compute a Western tropical zodiac sign + one of 火/土/風/水 from birthdate;
feeds `astro_bonus`, an additive term of `score_total` (`concierge_chat_ranking.py:1225`), **only
when `astro_bonus_enabled`** (gated by `public_mode == "compat"`, signal-authority.md §6 —
i.e. conditional on mode, not always active).

**New finding (this audit)**: `astro_bonus`'s **per-instance contribution is already traceable** —
`_to_rank_explanation()` conditionally appends an `astro_bonus` entry to `contributors`/
`top_contributors` **only if `astro_bonus > 0` for that specific candidate**
(`concierge_chat_ranking.py:1918-1926`: `if astro_bonus > 0: contributors.append({"axis":
"astro_bonus", ...})`). This is a real, already-implemented, contribution-gated (not merely
existence-gated) provenance mechanism — exactly the kind of "signal existed vs. signal contributed"
distinction the task's 3-condition test requires.

**Reaches Detail?** `rank_explanation` (containing `contributors`/`top_contributors`) is already
picked by `page.tsx:324` (`recommendation?.rank_explanation`) and passed into
`buildShrineDetailModel()` — **but** the frontend `RankExplanation` type
(`buildShrineDetailModel.ts:208-215`) declares only `version`/`summary`/`primary_axis`/
`primary_axis_ja`/`primary_label`/`primary_label_ja` — **`contributors`/`top_contributors` are not
declared on the type and are not read anywhere in `buildShrineDetailModel.ts`** (confirmed by
re-grep). The only current use of `rank_explanation` is (a) `.summary` as `recommendationMeta.rankBody`
(§1's "この神社が1位の理由", gated to `isTop`) and (b) `.primary_axis`/`.primary_label_ja` as a
fallback key into a canned-phrase lookup (`buildHeroMeaningCopy`, `buildShrineDetailModel.ts:1254-1297`)
— **not** the actual `contributors` list.

**Can Ranking contribution be identified per-instance?** **Yes** — via `top_contributors` (already
contribution-filtered) or `contributors[i].contribution > 0`.

**Usable for Personalized Explanation only when contributed?** **Yes, and the mechanism to enforce
that already exists Backend-side** (`if astro_bonus > 0`) — the Frontend gap is purely additive
(type + read), not a new Backend capability.

## 6. 九星気学 (Nine Star Ki)

**FACT** (re-confirmed by direct grep of `concierge_chat_ranking.py`, this audit): `kyusei` has
**zero references** in the scoring/ranking function. `Shrine.kyusei` (`models.py:262-267`) and
`backend/temples/domain/kyusei.py` exist and are wired into
`backend/temples/services/direction_reference.py:8` (`CALCULATION_METHOD =
"annual_monthly_kyusei_v1"`) — the Direction/参拝タイミング feature, classified **Context** by
signal-authority.md, not a shrine-selection Ranking signal.

**Authority check**: **No Authority currently exists for using 九星気学 in Personalized
Explanation.** It is not in the Ranking pipeline at all for shrine selection; using it to describe
"why this shrine" would be describing something that had zero influence on the recommendation.

**禁止事項の明文化**: Per the task's explicit constraint and this finding, the following is recorded
as a standing prohibition for any future PR touching Personalized Explanation:

> 九星気学 (`kyusei`) must not appear in Personalized Explanation text unless and until it is wired
> into the shrine-selection Ranking pipeline (`concierge_chat_ranking.py`) with a
> contribution-gated provenance mechanism equivalent to `astro_bonus`'s (§5). Its current presence
> in `Shrine.kyusei`/the Direction feature does not constitute Ranking Authority for shrine
> selection. Displaying it "because it exists" or "because it sounds personalized" is exactly the
> failure mode this audit's 3-condition test (§8) exists to prevent.

## 7. `history_theme`, Shrine Meaning, Place Context

**FACT** (re-confirmed): `history_theme` (`Shrine.history_theme` static field) is **Primary
(conditional)** per signal-authority.md — contributes Rank only when `consultation_axis` mediates a
match (§3), `reason_facts` priority 0 (highest). Real trace confirms non-zero contribution for a
genuine case (§9.3).

**Knowledge Fact vs. Recommendation Evidence — already separated**: confirmed unchanged from the
prior audit — `ShrineDeity`/`ShrineHistory` (Knowledge Model, "神社について") are Explanation-only,
never Rank-connected (signal-authority.md §8, Decision A), and rendering (`ShrineFactSection.tsx`,
now grouped per PR #2468) remains structurally independent from the Personalized Explanation blocks
audited here (§1's table — different generator functions entirely). **No generic Knowledge Fact is
automatically promoted to Recommendation reason** — re-confirmed, no code path found connecting
`ShrineHistory` rows to `shrine_meaning_composer.py`'s output.

**Shrine meaning / place context role**: `shrine_meaning_composer.py`'s `_build_shrine_meaning()`
uses, in priority order: `get_shrine_culture_translation()` → `SHRINE_HISTORY_STORY_OVERRIDES` (a
per-shrine hardcoded override table) → `history_theme` (via `HISTORY_THEME_DISPLAY_COPY`) →
`description` → `goriyaku` (free text) → `sajin`. **`consultation_axis` is absent from this entire
priority chain** (§0/§4.1) — the "shrine side" of the Primary(Mediator) pairing is present;
the "consultation side" is not.

## 8. Signal Existence vs. Contribution — Traceability

**FACT**: current fields that let the Frontend distinguish "signal exists" from "signal contributed
to this specific recommendation":

| Field | Where | Per-instance contribution gate? |
|---|---|---|
| `breakdown.matched_need_tags` | `rec.breakdown` (reaches Detail today) | Implicit — non-empty means it mattered for `score_need` |
| `rank_explanation.top_contributors` | `rec.rank_explanation` (reaches `page.tsx`, unused beyond `.summary`) | **Yes, explicit** — pre-filtered to `contribution > 0`, capped at top 2 |
| `rank_explanation.contributors` | same | **Yes, explicit** — each entry has its own `.contribution` value, `0` for non-contributing axes |
| `breakdown_detail.features.history_theme_candidate_boost` | `rec.breakdown_detail` (persisted, **not** picked by any Detail-side frontend function) | **Yes, explicit** — `.raw`/`.contribution` are `0` when it didn't fire; includes the `.consultation_axis`/`.history_theme` values that produced it |
| `breakdown_detail.features.astro_bonus` | same (`breakdown_detail`, not picked) | Flat float, `0` = did not contribute |

**Signals with no current per-instance contribution field at all**: `kyusei` (§6 — not in the
Ranking pipeline, so the question doesn't apply), `deity`/`shrine_history` (Explanation-only by
design, never meant to have a Rank contribution field, per signal-authority.md §8).

**Provenance genuinely missing from the API that would be needed**: none found — every signal this
audit could confirm as Ranking-relevant (`need`, `element`, `astro_bonus`,
`history_theme_candidate_boost`/`consultation_axis`) already has a contribution-gated field in the
persisted response. The gap is **entirely Frontend-side wiring** (§8's rightmost column showing
"not picked"/"unused"), not missing Backend provenance. This mirrors the exact pattern found in the
Shrine Knowledge Presentation Grouping work (#2467/#2468): Backend already computes and sends what's
needed; Frontend ViewModels drop or never read it.

## 9. Real-Data Trace

### 9.1 Direct Navigation (no consultation) — baseline for comparison

**FACT**: `/shrines/10` (鶴岡八幡宮, no `ctx=concierge`/`tid`) rendered "今の状態":
*"今は、迷いを整理し続けるより、次に動かす方向を一つ決める方が流れを作りやすい時期です。気になって
いることを一つに絞ると、次の判断が見えやすくなります。"*

### 9.2 Real Consultation-Linked Recommendation

**FACT**: `ConciergeThread.id=800` (queried directly from the local database, aggregate/single-row
read only), recommendation for 妙義神社 (shrine_id=88):

- `consultation_axis: "restart_mindset"`
- `breakdown.matched_need_tags: ["courage"]`
- `breakdown_detail.features.history_theme_candidate_boost: {raw: 0.8, weight: 0.3, contribution:
  0.24, history_theme: "勝負", consultation_axis: "restart_mindset"}`
- `rank_explanation.primary_reason_source: "history_theme"`
- `rank_explanation.primary_axis: "fallback"` ← **the bug in §0.2**
- `rank_explanation.top_contributors: [{axis: "need", axis_ja: "悩みとの一致", contribution: 3.0}]`
  (the blended "need" axis — already includes the 0.24 boost, but the label doesn't reveal the
  history_theme/consultation_axis mechanism specifically)

Rendered at `/shrines/88?ctx=concierge&tid=800`:

- 今のあなたとの接点: *"妙義神社は、決断や挑戦の前に向き合いやすい神社です。"*
- **この場所が合う理由**: *"妙義神社は、決断や挑戦の前に向き合うための候補です。詳しい背景は、
  歴史文脈とあわせて補足します。"*
- 今の状態: **identical text to §9.1**, despite a completely different shrine and a real,
  measurably-contributing consultation signal.

No console errors beyond expected anonymous-session 401s.

### 9.3 What Is Lost Between Real Signal and Displayed Text

- `consultation_axis="restart_mindset"` never appears, in any translated form, anywhere in the
  rendered text.
- `history_theme="勝負"` (the word itself, or any direct reference to "勝負"/victory/decision theme)
  never appears — only its pre-mapped generic phrase "決断や挑戦の前" (`HISTORY_TYPE_LABELS`-style
  lookup, `shrine_meaning_composer.py:179`).
- The two "why" blocks (接点/合う理由) say the same thing twice.
- "今の状態" contributes nothing consultation-specific in this trace.
- The one number that would prove genuine contribution (`0.24`) is never surfaced, nor is it
  expected to be shown raw — but nothing derived from it (e.g. "あなたの相談内容と特に一致した
  テーマがあります") is shown either.

## 10. Displayable vs. Internal-Only Classification

| Category | Signals |
|---|---|
| **表示可能（今回寄与が確認できた場合）** | `matched_need_tags`（既にDetail到達済み）, `history_theme`＋`consultation_axis`のペア（`breakdown_detail`経由、追加wiring必要）, `astro_bonus`（`rank_explanation.top_contributors`経由、追加wiring必要） |
| **ユーザー向け翻訳が必要** | すべての上記 — 内部key（`"need"`, `"restart_mindset"`, `"勝負"`等）をそのまま出さない。`history_theme`は既に`HISTORY_THEME_DISPLAY_COPY`という翻訳層を持つ（再利用可能）。`consultation_axis`には現状翻訳層が存在しない（新規作成が必要、ただしFrontendでの意味の再解釈ではなく、既存の`_axis_label_ja`/`HISTORY_THEME_DISPLAY_COPY`と同型の固定lookup） |
| **内部専用、表示禁止** | `kyusei`（§6, Ranking未接続）, `score_v3`/`score_v3_detail`（shadow-only）, `_debug.*`, `primary_axis`の内部値そのもの（`"fallback"`等の英語key） |

## 11. Personalized Explanation Layer — Responsibility (Design Only)

**1文定義**: Personalized Explanation Layerは、今回のRecommendationへ実際に寄与したSignal（Primary/
Secondary/Personalization/Context、寄与量>0で確認済みのもの）だけを、ユーザーの相談内容と神社側
Evidenceの両方が分かる1つの接続文へ翻訳する責務を持つ。

**Knowledge Layerとの境界**: Knowledge Layer（`ShrineDeity`/`ShrineHistory`、Explanation-only）は
Personalized Explanation Layerの入力にしない（signal-authority.md §8 Decision Aを維持）。神社の
事実は「神社について」が担当し続ける。

**Result Heroとの境界**: 変更提案なし（Result Freeze対象外にこの監査は踏み込まない）。ただし
`recommendation-result-detail-density-change-readiness.md`で既出のとおり、Hero/Detail双方が同じ
Reason V4 adapterを共有している事実は変わらない — 本監査が定義するcontribution-gated signalの
使用先をHero側にも適用するかはFuture判断（Result Freeze解除後）。

**Shrine Detailとの責務分担**: Shrine Detailは、Personalized Explanation Layerが翻訳した接続文
（今回版）と、Knowledge Layerの事実（恒常版）を、別々のsection（現状どおり）として並べる。1つの
sectionへ統合しない。

## 12. Connection Model

```
User Consultation (query, need_tags, consultation_axis)
        ↓ resolve_consultation_axis() / need_tags extraction
Recommendation Signal (matched_need_tags, history_theme match, astro sun_sign/element, birthdate)
        ↓ concierge_chat_ranking.py scoring
Recommendation Authority (score_need, score_element, astro_bonus, history_theme_candidate_boost
        — each with a contribution value, §8)
        ↓ persisted per recommendation item (breakdown, breakdown_detail, rank_explanation)
Shrine-side Evidence / Meaning (history_theme's shrine-side phrase via HISTORY_THEME_DISPLAY_COPY,
        matched goriyaku tags, culture_translation)
        ↓ MISSING LINK (§9.3): consultation-side half of the connection is dropped here
Personalized Explanation (今のあなたとの接点 / この場所が合う理由 / 今の状態)
```

Traced with real data (§9): the pipeline works correctly through "Shrine-side Evidence" — the break
is specifically between the contribution-gated signal data (`breakdown_detail`,
`rank_explanation.contributors`) and the text-generation step (`shrine_meaning_composer.py`), which
never reads the consultation-side half of what it's explaining.

## 13. Answers to the 10 Required Questions

1. **現在の「この場所が合う理由」は、本当に今回のRecommendation理由を説明しているか？** —
   **部分的にのみ。** 神社側の意味（history_theme由来）は反映されるが、なぜ*今回のあなたの相談*に
   対してその神社側の意味が選ばれたのか（consultation_axisとの一致）は一切説明されない（§9.3）。
2. **相談内容と神社側Evidenceの間で、現在どのsignalが失われているか？** —
   `consultation_axis`そのもの（§0.1, §4.1, §7）。神社側の意味は残るが、ユーザー側の起点が消える。
3. **consultation_axisはPersonalized Explanationの軸として利用できるか？** —
   **条件付きで可能。** 実データでcontribution>0が確認できる場合に限り（§3, §8）、かつ現状は
   Backend側に既に必要なprovenance（`breakdown_detail.features.history_theme_candidate_boost`）が
   存在するため、追加のBackend実装なしでFrontend wiringのみで到達可能。
4. **「今回一致したご利益」をgenericな神社ご利益と区別して取得できるか？** —
   **Yes、既に可能、ギャップなし。** `breakdown.matched_need_tags`が既にDetailへ到達済み（§4.2）。
5. **astrology signalは「今回の推薦に寄与した」と判定できるか？** —
   **Yes。** `rank_explanation.top_contributors`が`astro_bonus > 0`の場合のみ含む、既にBackend側で
   実装済みのcontribution-gated機構（§5）。Frontend側の型・利用が未実装なだけ。
6. **九星気学をPersonalized Explanationに使用するAuthorityは現在存在するか？** —
   **存在しない。** Rankingパイプラインに一切接続されていないことをコードで再確認済み（§6）。
7. **history_themeはRecommendation理由なのか、Explanation補助なのか？** —
   **両方、条件付き。** `consultation_axis`と一致した場合はPrimary（Rank寄与あり、§3）。一致しない
   場合はExplanation補助（`reason_facts`のみ、Rank非寄与）。現在の表示はこの区別をしていない。
8. **Frontendだけで正しいPersonalized Explanationを構築できるか？** —
   **ほぼYes、一部Backend provenanceの新規picker実装が必要（Backend変更ではない）。** §8のとおり
   必要なcontribution-gated値はすべて既にAPIレスポンス内に存在する。Frontendの役割は「新しい理由を
   生成する」ことではなく「既にBackendが確定させたcontributionを、既存の翻訳層（`HISTORY_THEME_
   DISPLAY_COPY`相当）へ通すだけ」であるべき。
9. **Backendから追加provenanceが必要か？** —
   **No、確認された範囲では不要。** 唯一の例外は§0.2のバグ（`primary_axis`が`history_theme`を
   認識しない）——これはprovenance不足ではなくロジックの不整合であり、本監査では修正しない。
10. **Result HeroとShrine Detailで、Personalized Explanationをどこまで重複させるべきか？** —
    **本監査の範囲外（Result Freeze対象）。** 事実として、両者は現状同じReason V4 adapterを
    共有している（`recommendation-result-detail-density-change-readiness.md`で既出）。本監査が
    定義するcontribution-gated contract自体はDetail専用ではなく共有可能な設計だが、Hero側への
    適用可否の判断はResult Freeze解除後に委ねる。

## 14. Frontend Field / Backend Requirement Determination

**実装に必要なFrontend field**（すべて既存APIレスポンスから取得可能、新規Backend field不要）:

- `rank_explanation.contributors` / `.top_contributors`（型`RankExplanation`への追加のみ）
- `breakdown_detail.features.history_theme_candidate_boost`（新規picker、`pickBreakdownFromThread.ts`
  相当の`breakdown_detail`版が必要）
- `breakdown_detail.features.astro_bonus`（同上）
- `consultation_axis`のユーザー向け翻訳lookup（新規、`HISTORY_THEME_DISPLAY_COPY`と同型・同じ
  Frontend側の固定辞書パターン。Backendの`_axis_label_ja`とは別に、consultation_axisの値
  （`restart_mindset`等）専用の翻訳表が必要 — Backend側にこの値のための日本語ラベルが存在するか
  未確認、§15参照）

**Backend/API変更の必要性**: **不要。** 必要な値はすべて既に`rank_explanation`/`breakdown_detail`
に存在し、既に`ConciergeThread.recommendations`へ永続化されている（§8/§9で実データ確認済み）。

**Serializer変更の必要性**: **不要。** これらの値はSerializerを経由しない経路
（`ConciergeThread.recommendations`のJSONField、Concierge Chat API応答）に既に含まれる。

**Recommendation Authority変更の必要性**: **不要、かつ変更してはならない。** 本監査はcontribution
判定ロジック自体を一切変更しない。既存の`contribution > 0`判定をFrontendが読むだけ。

## 15. Risks / Unknowns

- **§0.2のバグ**（`primary_axis`が`"history_theme"`を認識しない）は、修正すればFrontend側の
  fallbackキー選択（`resolveHeroMeaningFallbackKey`）の挙動にも影響する可能性がある。本監査は
  この修正を提案しない（Ranking/Reason生成ロジックの変更に該当するため、母艦判断が必要）。
  ただし、この監査が提案するFrontend実装（PR-A/B）は、このバグの有無に関わらず動作する
  （`rank_explanation.contributors`/`breakdown_detail`から直接読むため、`primary_axis`の
  誤判定に依存しない設計とする）。
- **consultation_axisの値（`"restart_mindset"`等）専用の日本語翻訳表がBackend/Frontendどちらにも
  存在するか未確認。** `_axis_label_ja()`（Backend）は`need`/`element`/`direction`/`distance`/
  `popular`/`astro_bonus`/`fallback`のみを扱い、`consultation_axis`の個別値（`restart_mindset`
  等）は扱わない。新規翻訳表が必要になる可能性が高いが、既存パターン（固定dictionary、
  テキストヒューリスティックなし）を踏襲すれば済む規模かは、`consultation_axis`が取りうる値の
  全体像（enum）を別途確認する必要がある — **UNCONFIRMED**（本監査のスコープでは`domain/
  consultation_axis.py`の値一覧までは確認していない）。
- **実データ1件（thread 800）のみでのトレース。** 他のconsultation_axis値・他のprimary_reason_
  source値での挙動は個別に確認していない。

## 16. Implementation PR Split (Design Only, Not Authorized)

**PR-A — Data / Provenance Wiring**
- 目的: 既にBackendが計算・永続化しているcontribution-gated provenance（`rank_explanation.
  contributors`/`top_contributors`、`breakdown_detail.features.history_theme_candidate_boost`/
  `astro_bonus`）をFrontendのViewModel層まで届ける。
- 対象ファイル: `apps/web/src/lib/shrine/buildShrineDetailModel.ts`（`RankExplanation`型へ
  `contributors`/`top_contributors`追加）、新規または既存picker拡張（`breakdown_detail`を
  thread snapshotから取得する経路）。
- Backend/Serializer/Model変更: **不要**（§14）。
- Recommendation Authority変更: **禁止、かつ不要**。
- テスト: 各fieldの伝播テスト（`buildShrineFactSection.test.ts`/Chapter 5と同型のパターン）。

**PR-B — Personalized Explanation ViewModel**
- 目的: PR-Aで届いたcontribution-gated dataを、「寄与が確認できたsignalだけ」翻訳する専用
  ViewModel関数を新設する（Frontendで新しい推薦理由を生成するのではなく、既に確定した
  contributionを固定翻訳表へ通すのみ）。
- 対象ファイル: 新規`apps/web/src/lib/shrine/buildPersonalizedExplanation.ts`相当（設計のみ、
  ファイル名は実装PRで決定）。`consultation_axis`翻訳表の新設が必要な場合はここに追加。
- 制約: `contribution > 0`が確認できないsignalは一切使用しない（§8の判定基準をそのままコードへ
  反映する）。`kyusei`はAuthority不在のため対象外のまま。
- Backend/Serializer/Model/Authority変更: **不要**。

**PR-C — Shrine Detail Presentation**
- 目的: PR-Bの出力を、既存の「今のあなたとの接点」/「この場所が合う理由」的section構造の中で
  重複なく表示する（§0.3の重複解消を含むかは、この監査の範囲外のPersonalized Explanation
  Redesignに踏み込まない限りにおいて最小限に留める）。
- 対象ファイル: `ShrineFactSection.tsx`とは別の、既存Meaning section系コンポーネント
  （実装PRで特定）。
- 制約: UI redesignを目的にしない。専門用語（占星術・九星・ご利益キーワード）を追加する目的の
  変更は行わない。

**PR-D — Analytics / Regression Verification**
- 目的: 表示されたPersonalized Explanationが実際にcontribution>0のsignalのみに基づくことを
  保証する回帰テストを追加する。§0.2のバグを踏まえ、`primary_axis`の値に依存しないテスト設計に
  する。
- 対象ファイル: 上記PR-B/PR-Cのテストファイル。新規Analytics eventの追加は本監査では提案しない
  （スコープ外、必要性が確認できていない）。

## 17. Final Decision

# PARTIAL READY

**実装可能なもの**:

- goriyaku（matched_need_tags）: 既に完全にReady（§4.2）。
- astro_bonus: contribution-gated provenanceがBackendに既に存在し、Frontend wiringのみで到達可能
  （§5, §14）。
- consultation_axis / history_theme_candidate_boost: 同様にBackend provenance既存、Frontend
  wiringのみ（§3, §14）。ただし専用翻訳表の新設が必要（§15）。

**未確定のもの**:

- consultation_axisの全値に対する日本語翻訳表の設計（§15、`domain/consultation_axis.py`の値
  一覧を別途確認する必要がある）。
- §0.2のBackendロジックの不整合（`primary_axis`が`history_theme`を認識しない）への対応方針
  （修正するか、Frontend側で`primary_axis`に依存しない設計に倒すか）は母艦判断。
- Result HeroとDetailの重複範囲（質問10、Result Freeze解除待ち、本監査のスコープ外）。

`kyusei`はAuthority不在のため、いかなるPRにおいてもPersonalized Explanationへ使用しない
（§6の禁止事項を維持）。

---

Production code changes = 0
UI changes = 0
Backend changes = 0
Ranking changes = 0
Serializer changes = 0
Model changes = 0
Migrations = 0
Recommendation Authority changes = 0
