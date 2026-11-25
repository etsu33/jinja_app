# Cross-Need Semantic Follow-up: Decision & PR Split Audit

## 1. Objective

Use [recommendation-semantic-resolution-cross-need.md](./recommendation-semantic-resolution-cross-need.md)
as the basis for (a) classifying every remaining missing-Reason Need into
work that can proceed without a product decision vs. work that cannot, (b)
building explicit Mother Ship decision packets for `family`, `mental`/
`rest`, `communication`, and `courage`, and (c) designing the next
implementation PRs in technical dependency order — without making any
final product-semantic decision on Mother Ship's behalf.

## 2. Scope

Fresh-read of current code (post-#2594 merge) for: `intent_map`, interpreter
`KEYWORDS`/`REGEX`, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`,
`NEED_TAG_TO_CONSULTATION_AXIS`, Lead/Reason builders, and live DB evidence
(`GoriyakuTag` master, shrine counts). Live runtime simulation via
`extract_need_tags`/`resolve_need_payload`/`resolve_consultation_axis`/
`build_chat_recommendations` against the existing isolated local scratch DB
— read-only, no writes.

## 3. Non-Goals

No implementation of any semantic-decision-gated fix. No final choice among
`family`'s scope options, `mental`/`rest`'s boundary options,
`communication`'s taxonomy options, or `courage`'s evidence-boundary
options. No REGEX modification. No new taxonomy. No DB/model/migration/
seed/frontend changes.

## 4. Base SHA

`origin/develop` @ `ebeb3950828910ab78fe3d4e9023054bbd9cb82e`
(`docs: 全15 Need横断のセマンティック解決度監査 (#2594)`), matching this
task's precondition. Worktree:
`/Users/morietsu/Developer/jinja_app-semantic-followup-decision-split`,
branch `audit/semantic-followup-decision-split`.

**Deliverable A status at the time this audit was written: NOT merged.**
[PR #2596](https://github.com/etsu33/jinja_app/pull/2596) (`fix: complete
Japanese need labels`) is open as a Draft, prepared in parallel under this
same task. Per the Worktree Policy, this worktree was branched from
`origin/develop` before #2596 exists, so the `NEED_LABELS_JA`/
`NEED_TAG_LABELS_JA` completeness defect is **explicitly marked
IMPLEMENTATION_PENDING** throughout this document — this audit does not
treat label completeness as resolved, and none of its findings assume
PR #2596 has landed. Label completeness (`label_ja` display text) and
Reason completeness (`intent_map` free-text sentences) are separate,
independently-landable surfaces — nothing in this audit is blocked by
PR #2596's merge state, and PR #2596 was independently confirmed by its own
regression suite (250 focused + 1769 full-suite tests, 0 failures) before
this document was written.

## 5. Source Audits

- `docs/audit/recommendation-semantic-resolution-cross-need.md` (primary
  input — re-verified against current code, not copied blindly; two
  findings below go beyond what that document reported, see Sections 11
  and 19).
- `docs/audit/marriage-reason-copy-implementation.md` (precedent for
  mechanical `intent_map` additions).
- `docs/audit/remaining-need-goriyaku-semantic-mapping.md` and
  `docs/audit/remaining-product-decision-need-responsibilities.md`
  (communication/mental/courage prior findings).
- `docs/audit/goriyaku-mapping-master-integrity.md` /
  `-correction.md` (39-row canonical master provenance).

## 6. Current Canonical Need Contract

Fresh-read from `backend/temples/domain/need_tags.py` `NEED_TAGS`: **15**,
unchanged since every prior audit this project has produced — love,
relationship, marriage, communication, career, money, study, health,
mental, protection, courage, focus, rest, family, travel_safe.
`NEED_PRIORITY` order (governs which tags survive `extract_need_tags`'s
`max_tags` cutoff) also unchanged: protection, marriage, love, family,
study, career, money, health, mental, relationship, communication, courage,
focus, rest, travel_safe.

## 7. Missing Reason Inventory

Fresh-read `intent_map` inside `_build_need_reason_text`
(`concierge_chat_ranking.py`, line ~2173): **9 entries** present — study,
mental, rest, love, career, money, courage, protection, marriage. **6
canonical Needs absent**, unchanged since the prior audit: `relationship`,
`focus`, `travel_safe`, `health`, `family`, `communication`. All 6 still
fall to the generic `"今の願い"` fallback, live-reconfirmed this session.

## 8. Missing Reason Classification

| Need | Classification | Reason |
|---|---|---|
| relationship | `SEMANTIC_SAFE_WITH_LIMITATION` | Concept (interpersonal-relationship repair/improvement) is stable and unambiguous; a generic Reason is safe to write. Limitation: GID evidence is `{1}` (縁結び), shared verbatim with love/marriage — Lead will often cite "縁結びのご利益" for a relationship-tagged match, the same clause love/marriage also produce, so the Reason sentence carries more of the differentiation burden than for a Need with its own dedicated evidence. |
| focus | `SEMANTIC_SAFE` | Concept (concentration/habit-forming) is stable, unambiguous, and already structurally shares its axis (`study_success`) and GID set (`{9,10}`) with `study` by established precedent (`docs/audit/remaining-need-goriyaku-semantic-mapping.md` SAFE_CORRECTIONS). No open question blocks a generic Reason. |
| travel_safe | `SEMANTIC_SAFE` | Concept (safety while traveling/moving) is stable and unambiguous; GID set `{3,13,14}` (交通安全/航海安全/海上安全) is a clean semantic fit with zero collision risk found anywhere in this or the prior audit. |
| health | `SEMANTIC_SAFE_WITH_LIMITATION` | Concept (general health/illness) is stable and unambiguous on its own terms. Limitation: GID set `{7,8,24,33,38}` includes id=7 (家内安全, household safety — broader than personal health) and id=8 (福徳, general fortune) — a health-tagged Lead may occasionally cite evidence that reads more "household" than "personal health." This is an evidence-fit nuance, not a meaning ambiguity, and does not block writing a Reason keyed on the `health` tag itself. |
| family | `DECISION_REQUIRED` | Family's own meaning is materially unstable across the codebase's own layers (Section 11): the interpreter vocabulary is fertility/childbirth-only, while the current GID mapping (`{2,26,34}` = 厄除け/家庭円満/火防) reads as household-protection/harmony — two different concepts. Writing a Reason now would force a premature choice between them. |
| communication | `BLOCKED_BY_UPSTREAM` | Communication's own meaning (improving communication ability) is not itself ambiguous, but no canonical `GoriyakuTag` in the 39-row master represents it (Section 17) — the current GID set `{30,33,37,39}` is semantically unrelated (強運厄除け/病気平癒/延命長寿/農業守護). A Reason sentence cannot honestly describe evidence the matched shrine doesn't actually have; this must wait for the GID/Taxonomy layer, not for a meaning decision about what "communication" itself means. |

## 9. Semantic-Safe Reason Candidates

| Need | Safe copy candidate (style-matched to existing `intent_map` entries) | Why safe |
|---|---|---|
| relationship | `"人間関係の改善や修復"` | Directly derived from the Need's own KEYWORDS (`人間関係`, `職場`, `家族`, `親子`, `友達`, `対人`) and its axis name (`relationship_repair`); makes no outcome/religious claim; same `"AやB"` sentence pattern as `love`/`courage`/`protection`. |
| focus | `"集中力や習慣づくり"` | Directly derived from KEYWORDS (`集中`, `習慣`, `継続`, `やる気`, `ルーティン`); mirrors `NEED_LABELS_JA["focus"]`'s existing `"集中・継続"` wording. |
| travel_safe | `"移動や旅の安全"` | Directly derived from KEYWORDS (`旅行`, `旅`, `出張`, `移動`, `交通安全`, `安全祈願`) and `NEED_LABELS_JA["travel_safe"]`'s existing `"移動・安全"` wording. |
| health | `"健康や体調の安定"` | Directly derived from KEYWORDS (`健康`, `体調`, `病気`, `不調`, `体力`, `治す`). |

These four are proposed as **candidates only** — Deliverable B does not
implement them (Section 22, Track R1, `READY_TO_IMPLEMENT`, is where
implementation belongs).

## 10. Decision-Gated Reason Candidates

| Need | Blocking classification | Cannot write a safe candidate because |
|---|---|---|
| family | `DECISION_REQUIRED` | Any candidate copy would have to pick a side: a childbirth-flavored sentence (e.g. "子宝や安産") forecloses `FAMILY_SCOPE_BROAD`; a household-harmony-flavored sentence (e.g. "家族円満") forecloses `FAMILY_SCOPE_NARROW` and would currently describe evidence (`家族円満`/id=26) that the interpreter's own vocabulary never actually routes a query toward (Section 11). |
| communication | `BLOCKED_BY_UPSTREAM` | Any candidate copy would be paired by `_build_need_lead` with Lead evidence drawn from `{30,33,37,39}` — 強運厄除け, 病気平癒, 延命長寿, or 農業守護 — none of which a reasonable user would recognize as "communication" evidence, regardless of how well-written the Reason sentence itself is. |

## 11. Family Current Contract

Fresh-read, cross-checked against live DB (not assumed from the prior
audit):

- **KEYWORDS** (`need_tags.py`): `["子宝", "安産", "妊活", "授かり", "出産", "育児"]` — entirely fertility/childbirth-centered. The literal word `"家族"` ("family") is **not present**; it belongs exclusively to `relationship`'s own KEYWORDS.
- **REGEX**: none defined for `family`.
- **GID mapping** (`NEED_TO_GORIYAKU_IDS["family"]`): `{2, 26, 34}` = 厄除け (general warding, 51 shrines, shared with `protection`), 家庭円満 (family harmony, 1 shrine), 火防 (fire prevention, 2 shrines) — this set reads as **household-protection/harmony**, not fertility.
- **New finding this task**: the two canonical `GoriyakuTag` rows that most naturally fit family's own *interpreter* vocabulary — id=16 `安産` (safe childbirth, 5 shrines) and id=35 `子宝` (blessed with children, 1 shrine) — are **not in family's mapping at all**. id=16 is currently assigned to `mental` (`NEED_TO_GORIYAKU_IDS["mental"] = {11,16,26,28,38}`), a semantically unrelated Need. id=35 is **unmapped by any Need** (one of 8 orphaned canonical GoriyakuTag ids in the current master: 17 八方除, 19 八難除, 22 美容, 23 方除け, 25 芸能, 29 芸能運, 31 技芸上達, 35 子宝). This means family's interpreter vocabulary, its GID mapping, and the master's own most-fitting tags for that vocabulary are **three mutually inconsistent signals** — a sharper, more concrete version of the ambiguity the prior audit flagged only qualitatively.
- **Text Evidence**: none (`NEED_TEXT_WEIGHTS` has no `family` entry).
- **Axis**: no `NEED_TAG_TO_CONSULTATION_AXIS` entry — always falls to `other`.
- **Existing product/docs wording**: no product doc found that states an intended scope for `family` beyond the code itself; `docs/audit/remaining-need-goriyaku-semantic-mapping.md` classified family's GID correction as `SAFE_CORRECTIONS` without addressing scope.
- **Existing Reason/Label wording**: no `intent_map` entry (Section 7). `NEED_LABELS_JA` label (pending PR #2596, IMPLEMENTATION_PENDING) was deliberately chosen as the scope-neutral `"家族"` for exactly this reason (`docs/audit/need-labels-ja-completeness-implementation.md` Section 6) — it does not resolve or presuppose this decision.
- **Real DB evidence**: 51 shrines carry id=2 (厄除け, shared with `protection`'s own primary id), 1 carries id=26, 2 carry id=34 — family's *practical* evidence pool is therefore dominated by a generically-protective tag it shares with `protection`, not by anything fertility- or household-specific.
- **Collision with relationship**: fresh live corpus (Section 15's method, applied to family-relevant phrasing): `"家族円満を願いたい"` → `relationship` only (`hits={'relationship': ['家族']}`); `"親子関係を良くしたい"` → `relationship` only; `"家族の健康を願いたい"` → `health`+`relationship` (family absent in both). `family` is **never** extracted for any family-relations-framed query in this corpus — the concept is fully owned by `relationship` in practice, regardless of what the English key `family` might suggest.
- **Collision with health**: `"家族の健康を願いたい"` → `health`+`relationship`, `family` absent (above).
- **`"家庭を整えたい"`** (household-harmony framing, using `家庭` rather than `家族`): matches **neither** `family` nor `relationship` — `relationship`'s KEYWORDS has `家族` but not `家庭`; `family`'s KEYWORDS has neither. It resolves to `mental`+`rest` only, via the unrelated `整えたい` collision (Section 15). A household-harmony query is therefore currently unreachable by *any* of the three Needs one might expect it to reach.

## 12. Family Decision Options

`MOTHER_SHIP_DECISION_REQUIRED`. No option is selected here.

### FAMILY_SCOPE_NARROW
Family remains pregnancy/childbirth/parenting-centered, matching its
current KEYWORDS.

| Impact area | Assessment |
|---|---|
| Interpreter | None required — current KEYWORDS already fit this scope. |
| Mapping | Real correction needed regardless of this option being chosen: reassign id=16 (安産) from `mental` to `family`; add orphaned id=35 (子宝) to `family`; decide whether to keep or drop ids 2/26/34 (household-flavored, a poor fit for a narrow reading) — same shape as the prior `SAFE_CORRECTIONS` pattern (PR #2582). |
| Axis | None of the 9 existing `CONSULTATION_AXES` semantically fits "fertility/childbirth" well; likely stays `other`, or a new axis is a separate, smaller decision. |
| Evidence (Text) | Low-risk mechanical addition possible (`子宝`, `安産`, `妊活`, etc. as Text words), once mapping is corrected. |
| Reason | Becomes `SEMANTIC_SAFE` once mapping is corrected — e.g. `"子宝や安産"`. |
| Likely collisions | Low — fertility-specific vocabulary rarely collides with other Needs' vocabulary in this corpus. |
| Migration/taxonomy | None — ids 16 and 35 already exist in the 39-row master; pure reassignment. |
| PR count | 2 (mapping correction; Reason addition) — plus optionally 1 for Text Evidence. |

### FAMILY_SCOPE_BROAD
Family becomes a broader family/household-relationship intent, absorbing
the "family relations" framing currently owned exclusively by
`relationship`.

| Impact area | Assessment |
|---|---|
| Interpreter | High-impact: would require adding `家族`, `家庭`, `親子関係`, `家族円満`, etc. to `family`'s KEYWORDS — words that directly overlap `relationship`'s own KEYWORDS (`家族`, `親子` already there). Since `family` sits at `NEED_PRIORITY` index 3 and `relationship` at index 9, `family` would begin **winning** the priority-pick step for any query currently resolving to `relationship` via those words — a real, silent behavioral change to `relationship`'s current extraction results, not an additive-only change. |
| Mapping | Moderate: id=26 (家庭円満) is already a good fit; the fertility ids (16, 35) would need a decision on whether they stay within the same, now-broader `family` or are treated as a sub-concept. |
| Axis | `relationship_repair` is a natural reuse (already `relationship`'s own axis). |
| Evidence (Text) | New entries needed (e.g. `家族円満`). |
| Reason | Only safe to write after the above settle. |
| Likely collisions | High and *deliberate* — this option intentionally creates a new priority-order-sensitive overlap with `relationship`, requiring its own collision-handling design and regression corpus, not a simple additive change. |
| Migration/taxonomy | None new needed, but requires an explicit design decision on whether family's fertility-sense is retained alongside or removed. |
| PR count | 3+ (interpreter+priority-collision design; mapping; axis/Reason) — the highest-risk, multi-PR option of the three. |

### FAMILY_SPLIT_REQUIRED
The current single `family` tag cannot safely represent both fertility and
household-relations concepts at once.

| Impact area | Assessment |
|---|---|
| Interpreter | Depends entirely on which sub-option: (a) introduce a 16th canonical Need tag — a major, system-wide taxonomy expansion touching `NEED_TAGS`, `NEED_PRIORITY`, and every Need-keyed dict in the codebase (`KEYWORDS`, `REGEX`, `NEED_TO_GORIYAKU_IDS`, `NEED_TAG_TO_CONSULTATION_AXIS`, `NEED_TEXT_WEIGHTS`, `NEED_LABELS_JA` ×3 copies, `intent_map`) — the single most invasive change of any option surveyed in this document; or (b) a documentation-only decision that `relationship` already fully owns "family relations" and `family` stays narrow — in which case this option collapses into `FAMILY_SCOPE_NARROW` plus a written note, not a distinct technical track. |
| Mapping | High if (a); none if (b). |
| Axis | Reuse `relationship_repair` if (a); none if (b). |
| Evidence (Text) | Only relevant if (a). |
| Reason | Only relevant if (a); closes via `relationship`'s own `SEMANTIC_SAFE_WITH_LIMITATION` Reason addition (Section 9) if (b). |
| Likely collisions | Aims to eliminate the collision by construction, but a poorly-scoped new tag under (a) could recreate it as a 16th collision surface. |
| Migration/taxonomy | High if (a) — the only option in this document that changes the canonical Need *count*, a decision with implications well beyond this audit's scope. None if (b). |
| PR count | 4+ if (a); 0 (docs-only) if (b). |

`TECHNICALLY_LOWEST_RISK`: `FAMILY_SCOPE_NARROW` — it requires no
interpreter change, no new taxonomy, and its mapping correction (reassign
id=16, add id=35) is arguably valid under any of the three options (all
three keep *some* fertility-relevant evidence attached to `family`).
This is a technical-risk observation only, not a product recommendation.

## 13. Mental Current Contract

Fresh-read: KEYWORDS include `"心を整えたい"`, `"心を整える"`,
`"気持ちを整えたい"`, `"気持ちを切り替えたい"`, and the **bare root**
`"整えたい"` itself; also `"疲れ"`, `"疲れて"`, `"疲れている"`, `"疲労"`,
`"癒し"`. REGEX adds `心を整え` (broader than the KEYWORDS exact forms) and
`疲れ(て|が|た)?`. GID: `{11,16,26,28,38}` — includes id=16 (安産), the
family-relevant mapping error noted in Section 11. Axis: `restart_mindset`
(healthy, `DIRECT_FIT`). `intent_map`: present, `"不安や心の安定"`
(`SEMANTIC_SAFE`, already implemented).

## 14. Rest Current Contract

Fresh-read: KEYWORDS include `"休みたい"`, `"休息"`, `"疲れ"`, `"回復"`,
`"睡眠"`, `"眠れない"`, `"リセット"`, `"穏やか"`, `"静か"`,
`"落ち着きたい"`, `"落ち着く"`, `"心を整えたい"`, the bare root
`"整えたい"`, `"自然"`, `"ゆっくり"`, `"過ごしたい"`, `"癒し"`, and more.
REGEX: a single bare-root pattern,
`re.compile(r"(穏やか|静か|落ち着|リセット|休息|癒し|ひと息|一息)")` — the
`落ち着` root has no okurigana, so it matches **any** conjugation
containing it, including `落ち着け` (causative-potential), which is not
itself present in `rest`'s own KEYWORDS list. GID: `{7,8}` (家内安全,
福徳). Axis: `rest_healing` (healthy, `DIRECT_FIT`). No `intent_map`
originally reported missing by the prior audit — **re-confirmed present**:
`"休息や気持ちの切り替え"` (`SEMANTIC_SAFE`, already implemented; Section 7
above lists it among the 9 present entries).

## 15. Mental/Rest Collision Corpus

Fresh-run against current code (not reused from the prior audit), using
this task's own required example variants:

| Query | Interpreter hits | Normalized tags | Axis | GID evidence |
|---|---|---|---|---|
| `気持ちを落ち着けたい` | `{'rest': ['落ち着']}` | `['rest']` | `rest_healing` (need_tags) | `{7,8}` |
| `心を整えたい` | `{'mental': ['心を整えたい','整えたい','心を整え'], 'rest': ['心を整えたい','整えたい']}` | `['mental','rest']` | `restart_mindset` (need_tags) | `{7,8,11,16,26,28,38}` |
| `不安を和らげたい` | `{'mental': ['不安']}` | `['mental']` | `restart_mindset` (need_tags) | `{11,16,26,28,38}` |
| `少し休みたい` | `{'rest': ['休みたい']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |
| `静かに過ごしたい` | `{'rest': ['静か','過ごしたい','静か']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |
| `疲れを癒したい` | `{'mental': ['癒し','疲れ','疲れ'], 'rest': ['疲れ','癒し','癒し']}` | `['mental','rest']` | `rest_healing` (query) | `{7,8,11,16,26,28,38}` |
| `落ち着ける場所に行きたい` | `{'rest': ['落ち着']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |

**Sharpest finding, new this task**: `気持ちを落ち着けたい` — a
straightforwardly mental/emotional-intent query ("I want to calm my
feelings") — extracts **`rest` only**. `mental` is entirely absent, not
merely co-extracted alongside it. Live end-to-end verification
(`build_chat_recommendations`, three synthetic candidates: mental-evidence-
only, rest-evidence-only, both) confirms the real consequence: the
mental-evidence-only candidate scores `score_need=0` and falls to the fully
generic Reason (`"ご利益のご利益で知られる...今の願いを願う参拝先として"`
— note the doubled "ご利益" is a separate, unrelated Lead-fallback
cosmetic artifact of an evidence-less candidate, not part of this finding),
while the rest-evidence-only candidate scores `score_need=1` with a
rest-flavored Reason for a query that was never actually about rest. This
is not merely two Needs sharing evidence — it is a live, concrete
**Need misassignment** with real ranking and Reason consequences, driven
by `rest`'s own bare-root REGEX (`落ち着`) firing on a conjugation
(`落ち着け`) that neither `mental`'s KEYWORDS nor its REGEX cover at all.

Primary Reason wording note (`疲れを癒したい` collision case, both-evidence
candidate): the live Reason text selects `mental`'s copy
(`"不安や心の安定を願う参拝先として"`) even though the candidate matched
both tags with `winner={'rest': 'gid', 'mental': 'gid'}` — the primary-
reason-label selection (a separate, pre-existing mechanism, unmodified by
this audit) appears to prefer `mental` in this tie; not itself a defect
this document scopes further.

## 16. Mental/Rest Decision Options

`MOTHER_SHIP_DECISION_REQUIRED`. Testing (not assuming) the conceptual
distinction "mental = emotional/psychological state, rest = rest/recovery/
low-stimulation intent" against current data:

- **Supported in some cases**: `不安を和らげたい` (clean mental), `少し休みたい`/`静かに過ごしたい` (clean rest) show the distinction working exactly as a clean boundary would predict.
- **Not supported in others**: `心を整えたい`/`疲れを癒したい` co-extract both, and `気持ちを落ち着けたい` — squarely an emotional-state query by that same conceptual test — resolves to `rest` alone. The current code does not implement or consistently honor this distinction; it is a plausible target design, not a description of current behavior.

Decision alternatives (regex/keyword impact stated for information only —
**this audit does not modify REGEX**, per explicit instruction):

| Option | REGEX impact | KEYWORDS impact | Mapping impact | Text-Evidence impact | Regression risk | Control corpus needed |
|---|---|---|---|---|---|---|
| **Keep co-extraction as intentional** (both tags legitimately apply to "整えたい"/"疲れ"/"癒し" queries; document it as by-design) | None | None | None | None | None — status quo | None (no change) |
| **Narrow `rest`'s bare `落ち着` root to require okurigana** (e.g. `落ち着(き|く|いた)`), so `気持ちを落ち着けたい` no longer silently loses `mental` | Would need to change the single `rest` REGEX pattern | None | None | None | Low-medium — must re-verify every other `rest`-REGEX-dependent case (`落ち着ける場所に行きたい` would also stop matching `rest` via REGEX unless `mental` is added there instead) | The 7-query corpus above, plus any existing `rest`-REGEX test coverage |
| **Add mental's own coverage for the causative-potential form** (e.g. `落ち着け` added to `mental`'s KEYWORDS/REGEX alongside, not instead of, rest's) | Would add a new `mental` REGEX entry | Would add to `mental`'s KEYWORDS | None | None | Low — additive, makes `気持ちを落ち着けたい` become `mental`+`rest` (matches the `心を整えたい` pattern) rather than `rest`-only | Same corpus |
| **Deduplicate the shared vocabulary between the two Needs' KEYWORDS entirely** (remove `整えたい`/`疲れ`/`癒し` from one of the two) | Possibly, if REGEX also carries the removed root | Yes, non-trivial — would need per-Need judgment on which Need "owns" each shared word | None | Possibly (if `静か` is deduplicated from one Need's Text weights too) | Medium — a real behavior change for every query currently co-extracting both | Full corpus, both isolated and collision cases |

No option is selected. All four require a Mother Ship decision on whether
co-extraction is desired at all before any code change proceeds.

## 17. Communication Responsibility Matrix

| Layer | Status | Root Cause | Independent Fix Possible? |
|---|---|---|---|
| Interpreter | `BROKEN` (50% coverage in this corpus; 1 `WRONG_NEED`) | KEYWORDS (`会話`,`発信`,`伝える`,`話す`,`営業`,`交渉`,`プレゼン`,`面接`) omits the Need's own literal name (`コミュニケーション`) and common conjugations (`話せる`); `職場` (relationship's own word) can win the query instead | **Yes** — vocabulary is a pure recall improvement, independent of the taxonomy question (Section 22, Track C1). |
| Taxonomy | `BROKEN` | No canonical `GoriyakuTag` among the 39 rows semantically represents "communication skill" | **No** — this is the root blocker; requires new evidence to exist before anything downstream can be fixed for real. |
| GID Mapping | `BROKEN` (`SEMANTICALLY_MISALIGNED`) | Current `{30,33,37,39}` (強運厄除け/病気平癒/延命長寿/農業守護) appear to be placeholder "closest available" assignments; none fit | **No independently** — remapping to other existing tags would not improve the fit; genuinely blocked on Taxonomy. |
| Axis | `BROKEN` (fallback-only) | No `NEED_TAG_TO_CONSULTATION_AXIS` entry and no `CONSULTATION_AXIS_KEYWORDS` entry (fresh-confirmed: zero references to communication anywhere in `consultation_axis.py`) | **Weakly gated** — mechanically addable independent of Taxonomy, but choosing *which* axis (if any) fits presupposes the same open question Taxonomy is asking; treated as gated here. |
| Text Evidence | `ABSENT` | No `NEED_TEXT_WEIGHTS` entry | **No independently** — meaningful only once Taxonomy supplies real evidence words. |
| C1 | `HEALTHY` (mechanism), starved of real evidence | Downstream of GID/Text | N/A |
| Ranking | `HEALTHY` (mechanism) | N/A | N/A |
| Lead | `HEALTHY` (mechanism), reduced to generic fallback for evidence-less candidates | Same starvation | N/A |
| Reason | `BLOCKED` (Section 8) | Even a well-written Reason would be paired with unfit Lead evidence | **No** — blocked by GID Mapping, which is blocked by Taxonomy. |

Real DB evidence for the current mapping: 4 shrines total across the 4
mapped ids (1 each) — fresh-reconfirmed, unchanged from the prior audit.

## 18. Communication Decision Requirements

The "possible shape" the task offered (`Semantic Definition → Interpreter →
Mapping/Taxonomy → Axis → Text Evidence → Reason`) is **not fully
supported** by the evidence gathered: `Interpreter` is not strictly
sequenced after `Semantic Definition`/`Taxonomy` — it operates on a
separate data structure (`need_tags` extraction) from GID/Text evidence
lookup, and vocabulary additions like `コミュニケーション`/`話せる` are
valid under *any* resolution of the taxonomy question, since they extend
an already-established scope (the Need already treats 会話/営業/交渉/
プレゼン/面接 as communication) rather than presupposing a new one. The
dependency structure actually supported by the evidence:

```
Taxonomy/Mapping Decision (Mother Ship — is new canonical evidence
  worth adding for "communication"? if not, is it accepted as
  permanently GID-sparse?)
    |
    +--> Mapping correction (only meaningful after Taxonomy resolves)
    |       |
    |       +--> Text Evidence (only meaningful after Mapping)
    |       |
    |       +--> Axis choice (weakly gated -- could technically
    |       |     precede Mapping, but a real axis choice
    |       |     presupposes the same open question)
    |       |
    |       +--> Reason (blocked until Mapping supplies real evidence)
    |
Interpreter vocabulary expansion (independent -- no product decision
  required, valid under any Taxonomy outcome)
```

Steps requiring a Mother Ship product decision: **Taxonomy/Mapping, Axis,
Reason** (all downstream of the taxonomy question). **Interpreter does
not.**

## 19. Courage Current Evidence

Fresh-read: `NEED_TO_GORIYAKU_IDS["courage"] = {12,15,18,20,24,30,38}`
(仕事運, 武運長長, 夫婦円満, 恋愛成就, 健康長寿, 強運厄除け, 足腰健康 —
note this set is itself semantically heterogeneous, sharing individual ids
with `career` (12,30), `marriage` (18), `love` (20), `health` (24,38) —
courage's evidence footprint touches more other Needs' territory than any
other single Need surveyed). `NEED_TEXT_WEIGHTS["courage"]` includes `勝運`
at weight 3 (its highest tier), alongside `開運`/`開運祈願`/`運を開く`/
`背中を押して`/`一歩踏み出す`/`勇気`/`変わりたい`. Total DB evidence: 20
shrine-references across the 7 ids (`PARTIAL`, unchanged from the prior
audit).

## 20. Career/Courage Shared Evidence

`NEED_TO_GORIYAKU_IDS["career"] = {6,21,30,12,27}`. **Shared ids with
courage: {12, 30}** — both are official members of *both* Needs' mapped
sets, not merely a coincidental Text-word overlap. `NEED_TEXT_WEIGHTS`
also shares `勝運` verbatim (career: weight 2, courage: weight 3).

Fresh DB detail:

| id | Name | Shrines | Notable co-tags observed |
|---|---|---|---|
| 12 | 仕事運 | 11 | None of the 11 shrines carrying id=12 also carry any of courage's *other* unique ids (15,18,20,24,38) — the overlap is purely at the mapping-definition level, never manifested as a single shrine embodying both Needs' distinct evidence simultaneously. |
| 30 | 強運厄除け | 1 | Single shrine (小網神社), tags `[4, 30, 28]` — no courage-unique ids co-present either; evidence base for this id is `DATA_LIMITED` regardless of the collision question. |

**Live C1/Top3 proof** (synthetic candidates: one carrying only the shared
id=12, one carrying a courage-exclusive id=15, one carrying a career-
exclusive id=21; run against both a courage-intent query and a career-
intent query):

- Courage-intent query (`新しいことに挑戦したい`): the id=12 candidate is matched as `['courage']`, `score_need=1`, `winner={'courage':'gid'}`, Reason `"...前進や後押しを願う参拝先として..."` (courage's own copy). The career-exclusive-id candidate scores `score_need=0` and gets the generic fallback — `career`'s evidence was never checked because the interpreter never extracted `career` from this query.
- Career-intent query (`転職を考えている`): symmetric — the id=12 candidate is matched as `['career']` with career's own Reason copy (`"...仕事や転機を願う参拝先として..."`); the courage-exclusive-id candidate scores `0`.

In both directions, the shared-id candidate's Reason/Label correctly and
exclusively reflects whichever Need the query actually expressed —
**zero observed wrong-Need leakage in either direction.**

## 21. Courage Decision Options

Answering B5's eight questions from the evidence above:

1. **Is `勝運` semantically valid for courage?** Yes — "winning fortune" is a defensible fit for courage's "前進・後押し" (moving forward, pushing through) framing; already weighted highest (3) in courage's own Text Evidence.
2. **Is it semantically valid for career?** Also yes — fits career's competitive-advancement framing (promotions, job competition); weighted 2 in career's Text Evidence. Both fits are independently defensible; neither is an error.
3. **Is shared use intentional or leakage?** Repository evidence is insufficient to assert either. Unlike the `love`/`relationship`/`marriage` axis-sharing (explicitly commented in `consultation_axis.py` as deliberate), no comment or doc anywhere marks ids 12/30 as a deliberately shared evidence pool. Per this task's instruction not to select an interpretation the evidence doesn't support, this is left **undetermined**.
4. **Does C1 amplify the collision or merely expose shared evidence?** **Merely exposes it.** Section 20's live test shows the interpreter's own clean separation (already established in the source audit, Section 8) fully gates which Need's GID set gets checked per query — C1 never evaluates courage's evidence for a career query or vice versa, so there is nothing for C1 to amplify.
5. **Is mapping correction sufficient?** Would eliminate the *official* overlap, but since Section 20 shows no real leakage under the current mapping, this would be a precautionary cleanup, not a defect fix.
6. **Is Text Evidence correction sufficient?** Same conclusion — could further differentiate the two Needs' Reason-flavor wording around `勝運`, but is not needed for correctness.
7. **Is data coverage part of the problem?** Partially — id=30 has only 1 shrine (`DATA_LIMITED`); id=12 has 11 (a more representative sample), and both show the same safe pattern, so data sparsity does not appear to be masking a real problem, but the id=30 conclusion specifically rests on a thin sample.
8. **Would removing shared evidence create zero-evidence gaps?** For `career`: removing ids {12,30} leaves `{6,21,27}` (59+1+2 = 62 shrine-references — still comfortably `STRONG`). For `courage`: removing ids {12,30} leaves `{15,18,20,24,38}` (1+1+4+1+1 = 8 shrine-references — drops courage from `PARTIAL` (20) to `SPARSE` (8), a real, quantified evidence-strength cost). **Removing the shared ids is not free for courage.**

**Classification: `MAPPING_OVERLAP_NEEDS_REVIEW`** (primary), with a minor
`TEXT_OVERLAP_NEEDS_REVIEW` note for the shared `勝運` Text weight — **not**
`MULTI_LAYER_EVIDENCE_DECISION`, since Interpreter, C1, Ranking, Lead, and
Reason are all independently confirmed healthy and unaffected; the
question is confined to whether the GID/Text overlap should be reviewed
for cleanliness, not whether it is currently causing harm. `courage` is
**not** part of the missing-Reason set (Section 7) — this packet concerns
evidence boundaries only, unrelated to Reason-copy completeness.

## 22. READY_TO_IMPLEMENT

Items with no unresolved product-semantic decision:

1. **Track R1 — Reason copy for relationship/focus/travel_safe/health**
   (bundled per PR Split Rule 3: mechanical dictionary completeness).
2. **Track C1 — Communication interpreter vocabulary expansion**
   (`コミュニケーション`, conjugations of `話す`/`話せる`) — independently
   justified in Section 18 as not requiring a taxonomy decision.

## 23. READY_AFTER_MECHANICAL_DEPENDENCY

**None.** Every other remaining item's blocker is a product/semantic
decision, not a completed prerequisite PR (Section 24). This bucket is
legitimately empty for this follow-up set.

## 24. MOTHER_SHIP_DECISION_REQUIRED

1. **Family Scope Decision** (Section 12) — `NARROW`/`BROAD`/`SPLIT_REQUIRED`.
2. **Track M1 — Family GID mapping correction** (reassign id=16, add id=35, decide fate of ids 2/26/34) — gated on item 1.
3. **Track E1 — Family interpreter vocabulary expansion** — gated on item 1, and only relevant if `BROAD` or `SPLIT_REQUIRED(a)` is chosen.
4. **Track R2 — Family Reason copy** (Section 10) — gated on item 1.
5. **Communication Taxonomy/Mapping Decision** (Section 18) — is new canonical evidence worth adding, or is `communication` accepted as permanently GID-sparse?
6. **Track C3 — Communication axis choice** — gated on item 5.
7. **Track R3 — Communication Reason copy** (Section 10) — gated on item 5 (via mapping).
8. **Mental/Rest Boundary Decision** (Section 16) — is co-extraction intentional, and is the `気持ちを落ち着けたい` mental-loss behavior acceptable?
9. **Track G1 — Courage/career GID mapping review** (Section 21) — low-urgency; Q8's quantified evidence-strength cost for courage is a real product tradeoff, not a pure cleanup.

## 25. Need-by-Need Technical Tracks

| Track ID | Need(s) | Objective | Preconditions | Layer | Files likely touched | Non-goals | Regression gates | Dependency | Decision required? |
|---|---|---|---|---|---|---|---|---|---|
| R1 | relationship, focus, travel_safe, health | Add `intent_map` entries (Section 9 candidates) | None | Reason | `concierge_chat_ranking.py` | No interpreter/mapping/axis/GID change | 0 failures, existing skips only, Ranking/Lead/Top3 churn=0 (mirrors PR #2593's own gates) | None | No |
| C1 | communication | Add `コミュニケーション`/`話せる`-family vocabulary to KEYWORDS/REGEX | None | Interpreter | `need_tags.py`, `consultation_interpreter.py` (kept synced per established convention) | No GID/Taxonomy/Axis/Reason change | 0 failures; must not change `matched_need_tags` for any other Need's existing test fixtures | None | No |
| M1 | family | Reassign id=16 (mental→family), add orphaned id=35, resolve ids 2/26/34 | Family Scope Decision | Mapping | `need_to_goriyaku_tag_ids.py` | No interpreter/axis/Reason change in the same PR | 0 failures; `mental`'s own test fixtures must not regress from losing id=16 | Family Scope Decision | Yes |
| E1 | family | Expand KEYWORDS to include household/family-relations vocabulary | Family Scope Decision = BROAD or SPLIT(a) | Interpreter | `need_tags.py` | No mapping/axis change in the same PR | 0 failures; explicit `relationship` regression corpus (priority-order change risk, Section 12) | Family Scope Decision, likely after M1 | Yes |
| R2 | family | Add `intent_map` entry | Family Scope Decision (+ M1 if NARROW) | Reason | `concierge_chat_ranking.py` | — | Same gates as R1 | Family Scope Decision, M1 | Yes |
| C2 | communication | Decide + (if yes) add new canonical GID evidence | Mother Ship taxonomy decision | Taxonomy/Mapping | `need_to_goriyaku_tag_ids.py`, possibly new `GoriyakuTag` rows | No Need-count change | New regression corpus specific to communication | None (root decision) | Yes |
| C3 | communication | Add axis entry if one fits | C2 | Axis | `consultation_axis.py` | — | 0 failures | C2 | Yes |
| R3 | communication | Add `intent_map` entry | C2 (real evidence must exist first) | Reason | `concierge_chat_ranking.py` | — | Same gates as R1 | C2 | Yes |
| D1 | mental, rest | Resolve boundary per Section 16's chosen option | Mental/Rest Boundary Decision | Interpreter (KEYWORDS/REGEX per chosen option) | `need_tags.py` | Must not touch Axis/Mapping/Reason | Full 7-query corpus (Section 15) plus existing `mental`/`rest` test suites, 0 failures | Mental/Rest Boundary Decision | Yes |
| G1 | courage, career | Review (not necessarily change) shared ids 12/30 | Mother Ship review of Section 21 | Mapping | `need_to_goriyaku_tag_ids.py` | Must preserve courage's evidence strength (Section 21 Q8) if any id is removed | Full career+courage regression, explicit before/after evidence-count check | None (independent review) | Yes |

## 26. Proposed PR Split

Following the 9 stated rules — one semantic responsibility per PR (Rule 1),
Need-specific decisions never bundled (Rule 2), mechanical completeness may
bundle (Rule 3, applied to R1), Mapping and Interpreter kept separate
(Rule 4, e.g. M1 vs E1), explanation-only fixes never touch Ranking
(Rule 5, all R-tracks), data expansion separate from logic fixes (Rule 6,
Text Evidence tracks are separate from Mapping tracks throughout), taxonomy
isolated (Rule 7, C2 stands alone), each PR has its own regression corpus
(Rule 8, Section 25's rightmost columns), decision-gated PRs stay
`PLANNED_ONLY` (Rule 9):

| Track | Suggested branch | Suggested commit | Draft PR completion definition | Status |
|---|---|---|---|---|
| R1 | `fix/reason-copy-relationship-focus-travel-safe-health` | `fix: add reason copy for relationship, focus, travel_safe, health` | `intent_map` has all 4 entries; completeness/contract test proves no raw-fallback regression; full suite green | `READY_TO_IMPLEMENT` |
| C1 | `fix/communication-interpreter-vocabulary` | `fix: expand communication interpreter vocabulary` | New KEYWORDS/REGEX entries; corpus test proves `コミュニケーション`/`話せる`-family queries now extract `communication`; no other Need's existing fixtures regress | `READY_TO_IMPLEMENT` |
| M1 | `fix/family-gid-mapping-correction` (name illustrative; final scope depends on the decision) | `fix: correct family GID mapping` | — | `PLANNED_ONLY` |
| E1 | `fix/family-interpreter-vocabulary-expansion` | `fix: expand family interpreter vocabulary` | — | `PLANNED_ONLY` |
| R2 | `fix/reason-copy-family` | `fix: add reason copy for family` | — | `PLANNED_ONLY` |
| C2 | `docs/audit-communication-taxonomy-options` → (if approved) `feat/communication-canonical-evidence` | — | — | `PLANNED_ONLY` |
| C3 | `fix/communication-axis` | `fix: add communication consultation axis` | — | `PLANNED_ONLY` |
| R3 | `fix/reason-copy-communication` | `fix: add reason copy for communication` | — | `PLANNED_ONLY` |
| D1 | `fix/mental-rest-boundary` (name illustrative) | — | — | `PLANNED_ONLY` |
| G1 | `docs/audit-courage-career-evidence-review` | — | — | `PLANNED_ONLY` |

No business/product priority is assigned to any row — order within this
table is not a priority ranking.

## 27. Technical Dependency Graph

```
R1 (ready)                         C1 (ready)
   |                                   |
   | (independent, no blockers)        | (independent, no blockers)
   v                                   v
 [implementation]                 [implementation]


Family Scope Decision (Mother Ship)
   |
   +--> M1 (mapping correction)
   |       |
   |       +--> R2 (family reason)
   |
   +--> E1 (interpreter expansion, BROAD/SPLIT(a) only)


Communication Taxonomy Decision (Mother Ship)
   |
   +--> C2 implementation (if approved)
           |
           +--> C3 (axis)
           |
           +--> R3 (reason)


Mental/Rest Boundary Decision (Mother Ship)
   |
   +--> D1 (interpreter boundary fix, per chosen option)


Courage/Career Evidence Review (Mother Ship, independent of all above)
   |
   +--> G1 (optional mapping cleanup)
```

Only `R1` and `C1` have no incoming edges from a Mother Ship decision node.

## 28. Regression Strategy per PR

Every track's Draft PR must independently run:

- Its own focused corpus (Section 25's "Regression gates" column).
- The existing focused suites already established as this project's
  standard set: `test_concierge_explanation*.py`,
  `test_marriage_reason_copy.py`, `test_marriage_interpreter_coverage.py`,
  `test_protection_explanation_coverage.py`, `test_compass_*` (orchestrator,
  runtime, direction_filter, recommendations_api),
  `test_concierge_primary_reason_unification_contract.py`,
  `test_signal_authority_*_contract.py`, `test_recommendation_reason_v4*.py`.
- The full backend suite, with the hard gate: 0 failures, existing-skip
  categories only (currently: GDAL unavailable, PostGIS unavailable,
  `GOOGLE_PLACES_API_KEY` unset, 1 ambiguous-axis-family case — 15 total,
  reconfirmed by PR #2596's own regression run this task).
- Explicit **Ranking/Top3 churn = 0** for every Need *not* targeted by that
  PR — any track touching Interpreter or Mapping (C1, M1, E1, D1, G1) must
  additionally re-run the full 65-case-style cross-Need corpus (or the
  relevant subset) to prove no other Need's extraction/axis/GID result
  changed.

## 29. Mother Ship Decision Matrix

| Topic | Current Behavior | Problem | Option A | Option B | Option C | Technical Consequence | Decision Required |
|---|---|---|---|---|---|---|---|
| Family scope | KEYWORDS=fertility-only; GID={2,26,34}=household-flavored; ids 16/35 (the actual best fertility fits) sit outside family's mapping entirely | Three internally-inconsistent signals for what "family" means (Section 11) | `FAMILY_SCOPE_NARROW` (`TECHNICALLY_LOWEST_RISK`) | `FAMILY_SCOPE_BROAD` | `FAMILY_SPLIT_REQUIRED` | NARROW: 2 PRs, no taxonomy change. BROAD: 3+ PRs, deliberate new `relationship` collision. SPLIT: 0 PRs (docs-only) or 4+ PRs (new 16th Need tag) | Yes |
| Mental/rest boundary | Shared vocabulary (`整えたい`,`疲れ`,`癒し`) plus `rest`'s bare-root REGEX causes both co-extraction and, in one case, complete `mental` loss | Is this intentional multi-Need signaling or a defect? | Keep as-is (documented intentional) | Narrow `rest`'s REGEX root | Add `mental`'s own coverage for the causative form (additive) | Keep: 0 PRs. Narrow: 1 PR + full REGEX-dependent regression. Additive: 1 PR, lower risk than narrowing | Yes |
| Communication semantic definition | No canonical GID fits; current mapping is a placeholder | Is new taxonomy worth investing in, or is communication permanently GID-sparse? | Invest in new canonical evidence | Accept permanent GID-sparsity, interpreter-only improvement | — | Invest: new taxonomy PR + Mapping/Axis/Reason chain. Accept: only Track C1 (interpreter) has real long-term value | Yes |
| Courage/勝運 evidence boundary | ids 12/30 officially shared with career; no leakage observed live; removing them costs courage real evidence strength | Is the overlap intentional, and is a cleanup worth the evidence-strength cost to courage? | Leave as-is (`TECHNICALLY_LOWEST_RISK` — zero observed harm) | Remove courage's claim on 12/30 | Remove career's claim on 12/30 | Leave: 0 PRs. Either removal: 1 PR + courage or career evidence-strength regression check | Yes |
| Missing Reason items (decision-gated) | `family`, `communication` remain on generic fallback Reason text | Blocked by the two decisions above, not by Reason-writing itself | Resolve via Family Scope Decision first | Resolve via Communication Taxonomy Decision first | — | See Tracks R2/R3 | Yes (inherited from the two decisions above) |

## 30. Production Safety

No production code, DB, model, migration, seed, or frontend file was
modified by this deliverable. `git diff --stat` (Section 31) confirms the
committed scope is the single audit document. All findings derive from
fresh code reads and read-only runtime execution (`extract_need_tags`,
`resolve_need_payload`, `resolve_consultation_axis`,
`build_chat_recommendations`, Django ORM `SELECT`/`.count()` queries only)
against the pre-existing isolated local scratch DB — no writes.

## 31. Out of Scope

Implementation of any `MOTHER_SHIP_DECISION_REQUIRED` track (M1, E1, R2,
C2, C3, R3, D1, G1). Selection of a final option for family scope,
mental/rest boundary, communication taxonomy, or courage/career evidence
review. REGEX modification of any kind. New taxonomy or canonical
`GoriyakuTag` rows. Any DB/model/migration/seed/frontend change. Merging
or advancing PR #2596 (Deliverable A) — its state is read-only input to
this document (Section 4).

## 32. STOP

Draft PR only. Two Mother Ship decisions (family scope, communication
taxonomy) plus two lower-urgency reviews (mental/rest boundary,
courage/career evidence) remain open. `Track R1` and `Track C1` are ready
to implement immediately and require no further decision.
