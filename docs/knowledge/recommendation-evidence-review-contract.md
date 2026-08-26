# Recommendation Evidence Review Contract

> **Status**: Contract definition only. No Recommendation Engine, C1 Max, Purpose Mapping, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`, Model, Migration, frontend/UI, Production DB, Production Shrine Seed, or Production Knowledge Seed change is included in this PR. This document does not perform Batch 17 Recommendation Evidence Review and does not start Batch 18 Fact Generation.

## Background

[`docs/audit/shrine-knowledge-recommendation-evidence-bridge.md`](../audit/shrine-knowledge-recommendation-evidence-bridge.md) (PR #2571) established that imported Shrine Knowledge (`ShrineDeity`/`ShrineHistory`) never automatically becomes Recommendation Evidence — the `MISSING_PIPELINE_BRIDGE` finding. [`docs/audit/recommendation-evidence-followup-design.md`](../audit/recommendation-evidence-followup-design.md) (PR #2572) evaluated candidate designs for closing that gap and concluded: reuse `Shrine.goriyaku`/`GoriyakuTag` as-is (no new schema), add a separate Recommendation Evidence Review document distinct from Knowledge Fact Human Review, and record provenance in that document rather than in the database.

This document is the normative contract those conclusions pointed to. It defines, precisely, what a reviewer may and may not do when converting reviewed Shrine Knowledge into Recommendation Evidence.

## 1. Contract Scope

**IN SCOPE**:

- Determining whether Source text contains an explicit blessing/benefit statement
- Reviewed `goriyaku` text (free-text, written by a human reviewer)
- Selecting a canonical existing `GoriyakuTag` candidate for that text
- Recording Source traceability for the decision
- The PASS / HOLD / NO_EVIDENCE / REVISE decision itself
- Shrine-level recommendation-readiness status derived from those decisions

**OUT OF SCOPE** (governed elsewhere, unaffected by this contract):

- Ranking weight (C1 Max, `score_need_rank_weighted`, `history_theme_candidate_boost`)
- Purpose Mapping (`NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`)
- C1 scoring itself
- User consultation interpretation (Concierge's `interpret_consultation`)
- Reason copy / Lead copy generation
- New taxonomy or new `GoriyakuTag` labels
- Religious truth claims of any kind — this contract never asserts that a blessing is real, only that a Source states it

## 2. Evidence Eligibility Rules

| Class | Definition | Disposition |
|---|---|---|
| **ELIGIBLE_EXPLICIT** | An official or approved Source explicitly states a blessing / prayer benefit / benefit category (e.g. a Source sentence naming 学業成就, 縁結び, 厄除け, or an equivalent explicit benefit phrase) | May proceed to PASS if it also maps cleanly to an existing canonical `GoriyakuTag` (Section 6) |
| **REVIEW_REQUIRED** | Source contains semantically related material — a historical anecdote, a deity association, a tradition that could imply a modern benefit — but does not explicitly state a blessing | Must NOT be automatically converted to `goriyaku`. Requires a documented human judgment call; typically resolves to HOLD unless a reviewer can point to an explicit statement elsewhere in the same Source |
| **INELIGIBLE** | Model/assistant background knowledge, shrine-name inference, deity-name inference, popularity or reputation, tourism copy with no blessing meaning, unsupported editorial interpretation | Must not be converted under any circumstance, regardless of how well-known the association is culturally |
| **UNKNOWN** | Source text is unavailable, inaccessible, or insufficient to make any determination | Held pending more Source material; never defaults to ELIGIBLE or INELIGIBLE by assumption |

This directly operationalizes constraints #14–#16 of the governing task: no Purpose may be derived from a deity name, a shrine name, or a historical anecdote unless the Source itself explicitly states the blessing.

## 3. Fact vs Recommendation Evidence Boundary

**`Knowledge Fact correctness ≠ Recommendation eligibility.`** A Fact can be 100% correctly transcribed from its Source and still carry zero Recommendation Evidence, because "is this a faithful record of what the Source says" and "does the Source explicitly state a benefit" are different questions.

| Source statement type | Knowledge Fact? | Recommendation Evidence? | Human Review required? |
|---|---|---|---|
| Explicit official blessing statement (e.g. Source states "学業成就のご利益で知られる") | Yes (as `shrine_history`/`editorial_summary` or supporting `deity` context) | Yes — ELIGIBLE_EXPLICIT | Yes, for both Fact correctness and Recommendation Evidence |
| Deity identity (name, `role`) | Yes (`deity`) | No, by itself (constraint #14 — no Purpose derivation from deity name alone) | Yes, for Fact correctness only |
| Historical event (dated, source_confirmed) | Yes (`shrine_history`, `historical_event`) | Only if the event text itself states a benefit outcome (e.g. 波上宮's "祈ったところ豊漁となり"); otherwise No | Yes, for Fact correctness; separately for Recommendation Evidence if benefit language is present |
| Founding story | Yes (`shrine_history`, `founding`) | Rarely — founding narratives are typically administrative/institutional, not benefit statements (cf. 北海道神宮) | Yes, for Fact correctness only, unless benefit language is present |
| Tradition (`tradition`, unconfirmed lineage) | Yes, but explicitly marked as non-factual lineage per Contract | REVIEW_REQUIRED at best — traditions describe belief/practice, not a Source's explicit assertion of a benefit category, unless the tradition text itself states one | Yes, for Fact correctness; Recommendation Evidence only with explicit reviewer judgment, never automatic |
| Historical anecdote (e.g. 建部大社's Yoritomo prayer-then-restoration narrative) | Yes (`historical_event`) | REVIEW_REQUIRED (constraint #16 — anecdote implies but does not explicitly state a benefit) | Yes, for both, with Recommendation Evidence requiring explicit HOLD/PASS judgment, not automatic conversion |
| Tourism description | No (not a Knowledge Fact category) | INELIGIBLE — tourism copy is not Source-backed benefit language | N/A for Fact; Recommendation Evidence review must reject it outright |
| Editorial summary | Yes, but only as a summary of a Source-backed Fact (`editorial_summary`) | Only if the underlying Source it summarizes contains explicit benefit language — the summary itself is never sufficient grounds | Yes, for both, and the reviewer must trace back to the underlying Source, not just the summary |
| AI-generated interpretation | No — `shrine-knowledge-contract.md`'s AI-generation constraints (§AI生成値の制約) prohibit AI-generated content from being saved as confirmed Fact | INELIGIBLE outright | N/A — never enters either pipeline as human-reviewed content |

## 4. Reviewed Goriyaku Contract

`Shrine.goriyaku` (`backend/temples/models.py:241`, free-text `TextField`, `help_text="ご利益（自由メモ）"`) stores human-reviewed, Source-backed labels once this contract governs a write to it. Specifically:

- **Delimiter convention**: reuse the existing split pattern already implemented in `backfill_goriyaku_tags.parse_goriyaku()` (`re.compile(r"[、,／/・\|\n\r\t]+")`). House style is `・` between labels (matches existing seed style, e.g. 太宰府天満宮's `"学業成就・合格祈願・厄除け"`), for consistency with legacy data, though the split regex accepts any of the listed delimiters.
- **Order convention**: no functional requirement (the field feeds an unordered M2M). For reviewer legibility, list labels in Source-evidence-strength order (strongest explicit statement first). This is a documentation convention only, not enforced by code.
- **Only existing canonical labels may be used.** Every label written into `goriyaku` under this contract must be an exact string match (or an explicitly-approved normalization, below) to an existing `GoriyakuTag.name`. This is not optional — constraint #13 ("do not add new GoriyakuTag labels") combined with `backfill_goriyaku_tags`'s `GoriyakuTag.objects.get_or_create(name=name)` behavior means any non-matching string silently creates a new, uncontrolled tag the moment the backfill command runs. Preventing that is this contract's single most important mechanical safeguard.
- **Normalization is allowed only for surface-form variation of the same stated concept** — e.g. a Source phrase "受験合格を祈願" normalizing to the existing canonical label `合格祈願` (same concept, different word order/particle) is allowed. Normalization is **not** allowed when it requires inferring the specific benefit category from a vague or generic statement (e.g. "様々なご利益がある" — "various benefits" — states no specific category and must not be normalized to any one label), and is not allowed when it could plausibly map to more than one existing canonical label with comparable plausibility.
- **Normalization must HOLD** whenever: (a) the Source phrase is generic/non-specific, (b) two or more canonical labels are similarly plausible, or (c) the reviewer cannot point to a specific existing `GoriyakuTag.name` that the Source phrase clearly and singularly supports.

## 5. Canonical GoriyakuTag Resolution

Fresh-read of the current `GoriyakuTag` table (local scratch DB, 39 rows; expected to match Production, which shares the same seed source) and `backfill_goriyaku_tags.py`:

- **Exact-match behavior**: `parse_goriyaku()` splits `goriyaku` on delimiters into discrete strings; `get_or_create(name=name)` links to (or creates) a `GoriyakuTag` by exact string equality. There is no fuzzy matching, stemming, or synonym table in the command.
- **Normalization behavior**: none exists in code today. Any normalization (Section 4) must happen at review time, in the reviewer's head and in the review document — not in the command, which is unmodified by this contract.
- **Ambiguity handling**: the command itself has no ambiguity handling — it will happily create two unrelated tags from two unrelated substrings. Ambiguity must be resolved by the reviewer before text is written, per Section 4's HOLD rule. This contract does not add ambiguity-handling code; it prevents ambiguous text from reaching the field in the first place.
- **New-label prohibition**: absolute. A reviewer must check the proposed label string against the current `GoriyakuTag.name` list (39 rows as of this writing: 縁結び, 厄除け, 交通安全, 商売繁盛, 五穀豊穣, 開運, 家内安全, 福徳, 学業成就, 合格祈願, 勝運, 仕事運, 航海安全, 海上安全, 武運長久, 安産, 八方除, 夫婦円満, 八難除, 恋愛成就, 導き, 美容, 方除け, 健康長寿, 芸能, 家庭円満, 出世運, 金運, 芸能運, 強運厄除け, 技芸上達, 八方除け, 病気平癒, 火防, 子宝, 心願成就, 延命長寿, 足腰健康, 農業守護) **before** marking a candidate PASS. If no existing label matches, the correct decision is HOLD (Section 7), never inventing new wording that resembles an existing label but isn't one.
- **HOLD rule when Source wording does not map cleanly**: if the Source states a benefit but no current `GoriyakuTag.name` represents that specific benefit category (e.g. a hypothetical Source explicitly naming a benefit outside the current 39-label vocabulary), the correct decision is HOLD, with a note describing the gap — **not** REVISE into a nearby label that changes the meaning, and not a request to create a new tag (out of scope for this contract; would require a separate, explicit Mother Ship decision to expand taxonomy, which constraint #12 places outside this task).

This structurally prevents `Source phrase → reviewer invents new semantic category`: the reviewer's only two write-eligible actions are (1) exact match to an existing label, or (2) narrow, single-candidate normalization to an existing label. Every other case is HOLD.

## 6. Provenance Contract

No DB schema change. Provenance is recorded entirely in a Markdown review document, per the pattern already proven for Knowledge Fact Human Review (`docs/audit/shrine-expansion-batch1-human-review.md`). Minimum fields per accepted or rejected Recommendation Evidence item:

| Field | Purpose |
|---|---|
| `shrine` | Which shrine this item applies to |
| Source key / reference | Which `ShrineKnowledgeSource` (or equivalent citation) supports this item |
| Source phrase (quoted or closely paraphrased) | The exact evidentiary text a reviewer is judging |
| Proposed canonical `goriyaku` text | What would be written into `Shrine.goriyaku` if PASS |
| Resulting existing `GoriyakuTag` | Which existing tag(s) this text is expected to resolve to via `backfill_goriyaku_tags` |
| Review decision | PASS / HOLD / NO_EVIDENCE / REVISE (Section 7) |
| Reviewer note | Free text — reasoning, especially for HOLD/REVISE |
| HOLD reason | Required when decision is HOLD |

## 7. Review Decision States

Four states, kept fully separate from Knowledge `verification_status` (which governs Fact correctness, not Recommendation eligibility — Section 3):

- **PASS**: Explicit Source-backed evidence (ELIGIBLE_EXPLICIT, Section 2) maps safely — exact match or narrow normalization (Section 4) — to an existing canonical `GoriyakuTag`. Ready to be written into `Shrine.goriyaku`.
- **HOLD**: Potential evidence exists (REVIEW_REQUIRED, Section 2) but the mapping or the underlying meaning is ambiguous, generic, or unsupported by a specific existing label. Not written; remains open for future re-review (e.g. if more Source material becomes available).
- **NO_EVIDENCE**: The Source has been reviewed in full and contains no explicit Recommendation Evidence of any kind (e.g. 北海道神宮's Batch 17 Facts). This is a confirmed, terminal state for the reviewed Source set — not an omission.
- **REVISE**: The underlying evidence is sound (would otherwise be ELIGIBLE_EXPLICIT) but the candidate wording or label selection needs correction before it can be marked PASS — e.g. wrong canonical label chosen, delimiter formatting error. This is a workflow/editorial state, distinct from HOLD's evidentiary ambiguity.

All four are needed: PASS/NO_EVIDENCE are terminal outcomes, HOLD is an evidentiary-ambiguity hold, REVISE is a technical-correction hold. Collapsing HOLD and REVISE would conflate "we don't know if this is true" with "we know what this should say, it's just written wrong" — different follow-up actions.

## 8. Shrine-level Readiness

Current engine reality (per PR #2571's fresh read of `_attach_breakdown`, `matched_all`, `_prefilter_candidates_for_need`, re-confirmed unchanged this session): a single matching `GoriyakuTag`/text-weight hit is sufficient to register a real Purpose match for a given `NEED_TAG` — `matched_all` is a set, and any one member makes the candidate eligible for that need's ranking and Lead/Reason generation. There is no minimum-evidence-count threshold in the engine today, so this contract does not invent one.

- **RECOMMENDATION_READY** (per Purpose): at least one PASS evidence item exists whose resulting `GoriyakuTag` is actually wired into `NEED_TO_GORIYAKU_IDS` or matched by `NEED_TEXT_WEIGHTS` for that Purpose. **Note**: PASS alone does not guarantee this — e.g. `航海安全`/`海上安全` (ids 13/14) are valid existing canonical tags a reviewer could correctly PASS against explicit Source text (波上宮's voyage-safety prayer content is a real example), but neither ID currently appears in any `NEED_TO_GORIYAKU_IDS` value, so a PASS there would not by itself make the shrine RECOMMENDATION_READY for any current Purpose. This is a Mapping-layer gap (out of scope for this contract, and out of scope for the `travel_safe` mapping question already flagged as unresolved in PR #2572 §21) — the review contract can only confirm Source-backing and correct canonical-tag selection; it cannot guarantee Purpose routing, which depends on `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS`, both frozen under this task's constraints #4–#5.
- **PARTIALLY_READY**: at least one PASS evidence item exists (and is Purpose-wired), but review of the shrine's full Source set is not yet complete — more items remain HOLD or unreviewed.
- **NO_RECOMMENDATION_EVIDENCE**: review is complete; all items resolved to NO_EVIDENCE.
- **HOLD**: review is complete or in progress; no PASS exists yet, and at least one item remains HOLD.

## 9. Compass / Concierge Shared Use

Confirmed unchanged this session (zero backend/frontend diff between the last fresh-read baseline and current `develop`): both Compass and Concierge read the same `Shrine.goriyaku`/`goriyaku_tags` fields and the same `_prefilter_candidates_for_need`/`_attach_breakdown` functions in `concierge_chat_ranking.py`. Reviewed Recommendation Evidence written under this contract flows through the existing, unmodified chain:

```
Reviewed Recommendation Evidence (this contract)
  → Shrine.goriyaku
  → backfill_goriyaku_tags (unmodified)
  → GoriyakuTag
  → existing NEED_TO_GORIYAKU_IDS / NEED_TEXT_WEIGHTS (unmodified)
  → Compass and Concierge (both, simultaneously)
```

No engine-specific duplicate review is required. Result: **`SHARED_RECOMMENDATION_EVIDENCE_CONTRACT`**.

## 10. Human Review Workflow — Pipeline Position

```
Discovery → Source Confirmation → Fact Generation → Knowledge Human Review
  → Recommendation Evidence Review (this contract)
  → Post-review Validation (Section 11) → Production Import
```

**Production Import sequencing — Option B recommended (Knowledge can import first, Recommendation Evidence follows separately)**, not Option A (import only after both reviews complete):

- Option A couples two independently valuable outputs. Knowledge Facts have standalone value (Shrine Detail display, per `shrine-knowledge-contract.md`'s Detail Multi-View Contract) regardless of whether any Recommendation Evidence is ever found for that shrine. Blocking Knowledge Import on Recommendation Evidence Review completion would delay a Fact-correct, Source-verified shrine from Production for a reason (Purpose-matchability) that a shrine like 北海道神宮 may never satisfy (NO_RECOMMENDATION_EVIDENCE, Section 8) — Option A would hold a perfectly good Knowledge entry hostage to a search that may legitimately end in "no evidence found."
- Option B also matches existing precedent exactly: Batch 17 was already imported to Production via Knowledge Import alone, with Recommendation Evidence deliberately deferred (that deferral is the entire reason this contract exists). Adopting B formalizes what already happened rather than introducing new process friction.
- Recommendation: **Option B**. Recommendation Evidence Review, once it produces PASS items, is imported as a follow-up `Shrine.goriyaku` update + `backfill_goriyaku_tags` re-run — a separate, smaller, independently-timed operation.

## 11. Validation Contract (pre-import, no tooling implemented)

- Source reference exists for every PASS item
- Every PASS item's proposed `goriyaku` text is present and non-empty
- The resulting canonical `GoriyakuTag` name exists in the current `GoriyakuTag` table (Section 5) — checked before import, not assumed
- No new tag would be created by running `backfill_goriyaku_tags` against the proposed text (i.e., every split token exact-matches an existing `GoriyakuTag.name`)
- No unsupported semantic interpretation: the review document's Source phrase, read on its own, must support the proposed label without requiring outside (model/cultural) knowledge to bridge the gap
- No duplicate/contradictory mapping: the same Source phrase is not mapped to two different canonical labels across review entries for the same shrine
- HOLD and NO_EVIDENCE items never become active recommendation data — only PASS items are eligible to be written into `Shrine.goriyaku`

## 12. Existing Shrine Compatibility

- **LEGACY_EXISTING**: shrines whose `goriyaku` was populated by the original seed data (predating this Knowledge Fact / Review architecture) remain valid as-is. This contract governs future writes; it does not retroactively invalidate, re-review, or flag existing `goriyaku` values. 太宰府天満宮's `"学業成就・合格祈願・厄除け"` remains valid Recommendation Evidence under LEGACY_EXISTING status without requiring a review document.
- **REVIEWED_NEW**: `goriyaku` text (or additions to existing `goriyaku` text) written under this contract's process, with a corresponding review-document entry.
- No existing contract (Knowledge Contract or otherwise) requires immediate review of all current shrines, and this contract does not introduce that requirement. A future backfill/re-review of LEGACY_EXISTING shrines against this contract's stricter provenance standard is a possible later initiative, not adopted here.

## 13. Batch 17 Pilot Template (reusable, not executed in this task)

| Shrine | Source | Evidence | Proposed canonical Goriyaku | Existing Tag | Decision | Notes |
|---|---|---|---|---|---|---|
| 北海道神宮 | *(Batch 17 sources)* | Per `recommendation-evidence-followup-design.md` §6: no Source-backed prayer/benefit language found in any of the 3 committed histories | — | — | *(TBD — prior audit's finding: NO_EXPLICIT_EVIDENCE)* | Starting point only; not a final review decision under this contract |
| 建部大社 | *(Batch 17 sources)* | Per `recommendation-evidence-followup-design.md` §6: Yoritomo prayer-then-restoration anecdote, `source_confirmed`, implies but does not explicitly state a benefit category | — | — | *(TBD — prior audit's finding: SOURCE_TEXT_REQUIRED / IMPLICIT_ONLY, i.e. REVIEW_REQUIRED under Section 2 of this contract)* | Requires an explicit reviewer HOLD/PASS judgment; this contract does not pre-decide it |
| 波上宮 | *(Batch 17 sources)* | Per `recommendation-evidence-followup-design.md` §6: multiple `source_confirmed` histories with explicit prayer/outcome language (豊漁・豊穣・平穏・航海の平安) | — | — | *(TBD — prior audit's finding: READY_FOR_RECOMMENDATION_EVIDENCE_REVIEW)* | Section 8 caveat applies: even a PASS on 航海安全-adjacent content would not by itself yield RECOMMENDATION_READY under current Mapping |

The empty "Proposed canonical Goriyaku" / "Existing Tag" / "Decision" columns are intentional — this task defines the template and carries forward only conclusions already established in merged audits (PR #2572); it does not perform the Batch 17 review itself (constraint #21).

## 14. Batch 18 Workflow

For 多賀大社・日吉大社・普天満宮・沖縄県護国神社, if this contract is adopted, the expected sequence (not started by this task, constraint #20):

```
Fact Generation → Knowledge Human Review
  → Production Import (Knowledge only, per Section 10 Option B)
  → Recommendation Evidence Review (this contract)
  → Post-review Validation (Section 11)
  → Production Import (Recommendation Evidence follow-up)
```

This decouples Batch 18's Knowledge timeline from its Recommendation Evidence timeline, consistent with Section 10's recommendation and with how Batch 17 already happened in practice.

## 15. Contract Placement

Placed at `docs/knowledge/recommendation-evidence-review-contract.md` (Option A: standalone document), not merged into `docs/knowledge/shrine-knowledge-contract.md` (Option B) or a product/recommendation architecture doc (Option C):

- Option B is rejected because Section 3 of this very contract states `Knowledge Fact correctness ≠ Recommendation eligibility` — folding this contract into the Knowledge Contract would blur the exact boundary it exists to enforce, and `shrine-knowledge-contract.md` is already large (1200+ lines); adding a second, distinct responsibility to it contradicts constraint #19 ("prefer a dedicated contract document over rewriting unrelated contracts").
- Option C is rejected because this is a human-reviewer workflow contract, not an engine/architecture document — its audience (reviewers producing review documents) matches `docs/knowledge/`'s existing audience (readers of `shrine-knowledge-contract.md`) more closely than `docs/core/recommendation-architecture.md`'s audience (engine design).
- Option A keeps this contract adjacent to, but structurally separate from, the Knowledge Contract — mirroring the same "separate document, not merged into an existing one" pattern that PR #2572 already recommended for the Review workflow itself (Option B there, of four options considered).

No second "decision record" document is created — the background/rationale this contract would otherwise restate already lives in the two merged audit documents (PR #2571, PR #2572), linked in the Background section above.

## 16. Review Checklist (reusable, per item)

- [ ] Source explicit? (Section 2 — is this ELIGIBLE_EXPLICIT, not REVIEW_REQUIRED or INELIGIBLE?)
- [ ] Blessing language explicit, not implied by anecdote/deity/tradition alone? (Section 3)
- [ ] Maps to a canonical existing `GoriyakuTag.name`, exact match or narrow normalization only? (Section 4)
- [ ] Tag actually exists in the current `GoriyakuTag` table? (Section 5 — checked, not assumed)
- [ ] No inference from deity identity or shrine name alone? (constraints #14–#15)
- [ ] No inference from historical anecdote unless the Source explicitly states the blessing? (constraint #16)
- [ ] Provenance recorded per Section 6 (shrine, Source reference, phrase, proposed text, resulting tag, decision, note)?
- [ ] Decision is one of PASS / HOLD / NO_EVIDENCE / REVISE, not left ambiguous? (Section 7)
- [ ] If PASS: does the resulting tag actually route into `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS` for a Purpose, or is this a Section 8 Mapping-gap case worth noting separately?
- [ ] Ready for Validation (Section 11)?

## 17. KPI Contract (measurement only, no thresholds)

**Geographic KPI** (existing, unaffected by this contract): total shrines, covered prefectures.

**Recommendation Evidence KPI** (new dimension this contract enables measuring): Recommendation-ready shrine count (Section 8), `goriyaku` coverage (% of reviewed shrines reaching PASS), `GoriyakuTag` coverage (distinct tags actually attached via reviewed evidence vs legacy), Purpose-matchable shrine count (shrines whose reviewed evidence is also Mapping-wired, per Section 8's caveat), Purpose geographic coverage (prefectures with at least one Purpose-matchable shrine, per Purpose), NO_EVIDENCE count, HOLD count.

## 18. Mother Ship Decision Inputs

1. Recommended contract location: `docs/knowledge/recommendation-evidence-review-contract.md` (this document; Section 15)
2. Recommended pipeline position: Knowledge Human Review → Recommendation Evidence Review → Validation, with Production Import split per Section 10 Option B
3. Recommended review states: PASS / HOLD / NO_EVIDENCE / REVISE (Section 7)
4. Recommended provenance format: Markdown review document, no DB schema change (Section 6)
5. `Shrine.goriyaku` reuse: Yes, as-is (Section 4)
6. `GoriyakuTag` reuse: Yes, as-is, exact-match/narrow-normalization only (Section 5)
7. New schema needed: No
8. Engine change needed: No
9. Whether Batch 17 pilot should happen next: this document only prepares the template (Section 13); the decision to run it is Mother Ship's, informed by PR #2572 §19's `DEFINE_EVIDENCE_REVIEW_CONTRACT_FIRST` recommendation now being satisfied by this contract's existence
10. Whether Batch 18 should wait: not blocked by this contract — Section 10/14 decouple Knowledge Import from Recommendation Evidence Review, so Batch 18 Fact Generation could proceed independently of when/whether a Batch 17 Evidence Review pilot runs

## 19. Limitations

- This contract does not resolve the `travel_safe` `NEED_TO_GORIYAKU_IDS` mapping-quality question ({10, 22, 23}, none of which read as "travel safety" at the tag-name level) flagged in PR #2572 §21 — it is referenced again in Section 8 as a live example of a Mapping-layer gap this contract cannot fix, since Mapping changes are outside this task's constraints.
- A brief cross-check found that several `NEED_TO_GORIYAKU_IDS` values (e.g. ids 42–45, referenced under `family`/`mental`/`health`/`rest`/`relationship`) do not correspond to any row in the current 39-row `GoriyakuTag` table — an existing Mapping/data-integrity gap, unrelated to and unresolved by this contract, noted here only because a reviewer following Section 5's "tag actually exists" check could otherwise be confused by a Purpose that appears wired in code but has no live tag.
- GoriyakuTag vocabulary (39 rows) and `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS` were verified against the session's local scratch DB (`shrine_dataset_audit_local`) and `develop`'s tracked code, not re-verified against Production directly.
- This contract does not itself decide whether 建部大社's Yoritomo anecdote (Section 13) should resolve to PASS or HOLD — that remains a live, unresolved judgment call for whoever runs the actual Batch 17 pilot review.

## 20. Out of Scope

Recommendation Engine code, C1 Max, Purpose Mapping, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`, frontend/UI, Production DB, Production Shrine Seed, Production Knowledge Seed, new Model, new Migration, new taxonomy / new `GoriyakuTag` labels, Batch 17 Recommendation Evidence Review execution, Batch 18 Fact Generation.
