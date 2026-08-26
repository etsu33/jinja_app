# Recommendation Evidence Follow-up Design Audit

> **Status**: AUDIT / DESIGN ONLY. No Recommendation Engine, Mapping, Model, Migration, Seed, Knowledge Seed, Production DB, or UI/frontend change is included in this PR. This document defines candidate designs for Mother Ship decision; it does not implement any of them.

## 1. Scope

This document answers one question:

> After Human Review confirms a shrine's Deity / History / Source Facts, what additional human-reviewed artifact or field should be produced so Compass and Concierge can actually use that shrine for Purpose matching?

It builds directly on [`docs/audit/shrine-knowledge-recommendation-evidence-bridge.md`](shrine-knowledge-recommendation-evidence-bridge.md) (PR #2571, merged), which established that a `MISSING_PIPELINE_BRIDGE` exists between the Knowledge layer (`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`) and the Recommendation Evidence layer (`Shrine.goriyaku` → `GoriyakuTag` → `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS`). This audit does not re-derive that finding; it takes it as the starting point and designs the smallest safe next stage.

Out of scope is listed in full in Section 22.

## 2. Base SHA

- Worktree: `/Users/morietsu/Developer/jinja_app-recommendation-evidence-followup`
- Branch: `audit/recommendation-evidence-followup-design`
- Created from `origin/develop` at `2daf404f0038c30c042550d83819bd7801f7b593` (`docs: Shrine Knowledge to Recommendation Evidence Bridge Audit (#2571)`), immediately after that PR was merged with explicit Mother Ship authorization in the preceding session turn.
- Confirmed via `git log --oneline -3`: `2daf404f` → `5169d05b` (`Web共通コンポーネントをDark UIトークンへ統一 (#2570)`, unrelated concurrent work, untouched by this audit).

## 3. Current Pipeline

Fresh-read confirms the pipeline described in PR #2571 is unchanged (no commits touched `temples/services/concierge_chat_ranking.py`, `temples/domain/need_to_goriyaku_tag_ids.py`, `temples/models.py` Shrine/GoriyakuTag definitions, or `import_shrine_knowledge.py` between `2daf404f` and the fresh read performed for this document):

```
Discovery → Source → Knowledge Fact (ShrineDeity / ShrineHistory)
   → Human Review (Fact correctness) → Production Import
   → [NO BRIDGE] →  Shrine.goriyaku (free text, independently populated)
                        → backfill_goriyaku_tags → GoriyakuTag (M2M)
                        → NEED_TO_GORIYAKU_IDS (GID evidence)
                        → NEED_TEXT_WEIGHTS (Text evidence, matched against goriyaku/description text)
                        → _prefilter_candidates_for_need / _attach_breakdown
                        → C1 Max Scoring → Lead → Reason
```

`Shrine.goriyaku` (`backend/temples/models.py:241`, `TextField`, `help_text="ご利益（自由メモ）"`) and `Shrine.goriyaku_tags` (`models.py:246`, M2M to `GoriyakuTag`) are the only fields Compass/Concierge's evidence-matching code reads. `ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource` are never referenced by `concierge_chat_ranking.py`, `need_to_goriyaku_tag_ids.py`, or `import_shrine_knowledge.py` (confirmed via grep, 0 matches for `goriyaku`/`history_theme` in the importer, re-confirmed this session).

`docs/knowledge/shrine-knowledge-contract.md` (line 33) independently documents the same gap from the Knowledge-contract side, citing `docs/audit/concierge-end-to-end-consistency-audit.md` **Blocker #1**: `deity`/`shrine_history` are empty in 105/105 shrines in that audit's snapshot, and `recommendation_reason_v4.py`'s `QUALITY_FACT_KEYS = ("deity", "shrine_history", "goriyaku", "history_theme")` (contract doc line 156) treats Knowledge Facts and `goriyaku`/`history_theme` as interchangeable for reason-quality purposes even though only the latter two are ever populated. This is independent, pre-existing confirmation (not authored by this audit) that the bridge gap is a recognized, named architectural fact, not a novel finding.

## 4. Human Review Responsibility

| Review Responsibility | Current? | Source |
|---|---|---|
| Fact correctness | Yes | `shrine-expansion-batch1-human-review.md` — per-Fact PASS/REVISE decisions for all 25 Batch 17 Facts |
| Source correspondence | Yes | Same document; explicit "禁止事項8: 意味的に近いという理由でPASSさせない" rule applied (波上宮 H5-B revision, rejected "境内整備" because only the near-synonym "全整備事業" was found) |
| `history_type` | Yes | Same document; 北海道神宮 H1 revised tradition→founding, citing Contract "history_type一覧" |
| `verification_status` | Yes | Same document; 建部大社 H2 split into disputed H2-A/H2-B (675 vs 676 conflicting dates) |
| `confidence` | Yes | Same document; assigned per-Fact alongside `verification_status` |
| deity role | Yes | Same document; `role: unknown` used where official sources show no explicit hierarchy, per Contract §deity契約/役割候補 |
| Goriyaku | **No** | Not mentioned anywhere in `shrine-expansion-batch1-human-review.md`. `Shrine.goriyaku` for all 3 Batch 17 shrines remains `""` (confirmed via `shrines_seed_clean.json`, commit `af0a1ec3`) |
| Recommendation Purpose | **No** | Not mentioned anywhere in the Human Review document or in `shrine-knowledge-contract.md`'s deity/shrine_history sections |
| Recommendation eligibility | **No** | No review artifact in the current pipeline determines whether a shrine becomes Purpose-matchable |

Human Review, as currently practiced, is exclusively a **Fact-correctness** review: does this Fact accurately represent what the Source says, and is it classified correctly (`history_type`, `verification_status`, `confidence`, deity `role`)? It never asks "what Purpose does this support" or "should this shrine be recommendation-eligible for X". This is consistent with `shrine-knowledge-contract.md`'s own architecture: the contract's `Fact利用条件` sections (deity §246-263, shrine_history §364-380) define when a Fact may be *displayed or cited*, never when a shrine becomes *recommendation-eligible* for a Purpose. The two concerns are currently, cleanly separated — but separated to the point that nothing connects them.

## 5. Recommendation Evidence Candidate Types

| Candidate | Already production-active? | Recommendation-connected? | Human-reviewable? | New schema required? |
|---|---|---|---|---|
| `Shrine.goriyaku` (free text) | Yes | Yes (feeds `backfill_goriyaku_tags` + `NEED_TEXT_WEIGHTS` substring match) | Yes (already an Admin-editable TextField) | No |
| `GoriyakuTag` (canonical M2M) | Yes | Yes (feeds `NEED_TO_GORIYAKU_IDS` directly) | Yes (Admin can attach/detach existing tags) | No |
| `Shrine.description` | Yes | No (not read by any Compass/Concierge scoring code path found via grep) | Yes, but contract doc (line 125, 287-298) confirms this field's responsibility is already muddled ("神社紹介文"/"由緒"/"ご利益説明" mixed with no `help_text`) | N/A (exists, but not Recommendation-connected and already flagged as a mixed-responsibility field to avoid extending further) |
| `history_theme` | Yes | Yes, but ranking-magnitude-only (per PR #2571's finding: added only to `score_need_rank_weighted`, never to `matched_all`; cannot create a new Purpose match) | Currently written only via `admin.py`/`seed_history_theme.py`/migrations — no Human Review workflow touches it | No, but contract doc line 380 explicitly classifies `history_theme` as "Meaning Layerの解釈情報" (an interpretation generated from `shrine_history`, not a primary fact) — relevant to Phase 5 |
| Knowledge Fact metadata (`ShrineDeity.role`, `ShrineHistory.history_type`) | Yes (as Knowledge data) | No (never read by Recommendation code) | Yes (this is exactly what current Human Review already reviews) | No |
| "existing need tags" (i.e. `GoriyakuTag` rows already in the DB) | Yes | Yes | Yes | No — 41 `GoriyakuTag` rows already exist locally, including the exact study-purpose tags (`id=9` 学業成就, `id=10` 合格祈願) |

**Conclusion**: `Shrine.goriyaku` and `GoriyakuTag` are the only two candidates that are simultaneously production-active, Recommendation-connected, and Human-reviewable under the existing contract, with zero new schema. Every other candidate either isn't Recommendation-connected (`description`), can't independently create a Purpose match (`history_theme`), or isn't Recommendation-connected at all (Knowledge Fact metadata). This satisfies the task's "prefer reuse over new schema" instruction directly — reuse is not just preferable, it's the only option that requires no new schema.

## 6. Source-backed Goriyaku Feasibility

Fresh-read of `backend/temples/data/knowledge_seeds/batch_17_seed.json` (the actual committed, real Fact content for the 3 Batch 17 shrines), classified strictly against explicit Source text — no inference from deity identity or shrine name:

**北海道神宮** (4 deities, 3 histories, all `source_confirmed`): All history content is institutional/administrative — enshrinement date, renaming (札幌神社→北海道神宮), imperial visit dates. No sentence anywhere states what worshippers pray for or what benefit is associated with the shrine. → **NO_GORIYAKU_EVIDENCE**.

**建部大社** (2 deities, 4 histories after Human Review's disputed-split): One history explicitly narrates: "源頼朝が平家に捕らわれた際に当社で前途を祈願し、後に源氏再興を果たして再び参拝し、神宝と神領を寄進した" (`verification_status: source_confirmed`, not disputed). This is an explicit Source-backed account of a specific historical figure praying for his future here and subsequently restoring his clan's fortunes — a concrete anecdote, not a generic blessing statement (e.g. it does not say "当社は開運・出世のご利益で知られる"). → **IMPLICIT_ONLY** (the anecdote implies a career/fortune-restoration association; asserting that association as a `goriyaku` label would require one interpretive step beyond what the Source states verbatim, per Section 7 below).

**波上宮** (6 deities, 5 histories, all `source_confirmed`): Multiple histories explicitly state what people prayed for and, once, an explicit causal outcome: "海の彼方のニライカナイの神々に豊漁・豊穣と平穏を祈り"（prayed for bountiful catch/harvest and peace）, "海浜で霊石を得て祈ったところ豊漁となり"（prayed and the catch became bountiful — an explicit prayer→outcome statement）, "航海の平安を祈り"（prayed for safe voyage）. These are the closest thing to explicit blessing language found in Batch 17. → **EXPLICIT_GORIYAKU_SOURCE** for the underlying content (bountiful catch/harvest, safe voyage, peace), with the caveat noted in Section 11 that none of these cleanly maps to a currently-defined `NEED_TAG`.

No Batch 17 Fact anywhere states or implies **study/scholarship** content, confirming the prior finding in PR #2571 that Batch 17 cannot explain the `study` Purpose gap regardless of any bridge design.

## 7. Fact vs Interpretation Boundary

Per the task's own definitions and `shrine-knowledge-contract.md`'s "Evidence Gate要件 / fallback" section (lines 998–1012, which independently defines the same boundary for a different purpose — Reason-text fallback safety):

**FACT** (safe to carry into Recommendation Evidence as-is): deity identity with role, an explicit official blessing/prayer statement quoted or closely paraphrased from a Source (e.g. 波上宮's "豊漁・豊穣と平穏を祈り").

**INTERPRETATION** (requires a human judgment call, not a mechanical transcription): "this history means career change" (建部大社's Yoritomo anecdote → career), "this deity implies love", "this shrine is suitable for study". Contract doc line 1008 gives the exact same example in its own forbidden-list: 「この神社は決断を後押しする歴史を持っています」 is flagged as illegitimate because it asserts a historical property (決断を後押しする) that the Source does not state.

The contract's own resolution for this exact tension (line 1005) is instructive and directly reusable here: an **Interpretation fallback is conditionally permitted, but only when it is legible to the reader as interpretation, not fact** — its example wording is "登録されているテーマ上、今回の相談と接点がある候補として選ばれています". Applied to Recommendation Evidence: a reviewer may record 建部大社's Yoritomo anecdote as supporting a `career`-adjacent `GoriyakuTag`, but only as a **human interpretive judgment made explicit and attributable to a reviewer**, never as an automatically-derived Fact. This is exactly why Phase 9's options (below) center on a *Human Review* stage rather than any automatic derivation — automatic Deity→Purpose or History→Purpose derivation is explicitly prohibited by this task's constraints #6–#8, and the Contract's own fallback rules independently support treating any non-explicit association as Interpretation requiring a human reviewer, not a script.

## 8. Existing Goriyaku Contract

Fresh-read of `backend/temples/models.py:241` and `backend/temples/management/commands/backfill_goriyaku_tags.py`:

1. **Is `goriyaku` expected to be Source-backed?** No. The field's own `help_text` is "ご利益（自由メモ）" — "free memo". There is no `source_reference`, `verification_status`, or `confidence` field on `Shrine.goriyaku` itself (unlike `ShrineDeity`/`ShrineHistory`, which have all three).
2. **Is it free text?** Yes — `models.TextField`, delimiter-split by `backfill_goriyaku_tags.parse_goriyaku()` on `、,／/・|` and newlines/tabs.
3. **Is it canonical or editorial?** Editorial. The seed data (`shrines_seed_clean.json`) populates it per-shrine as free-form Japanese phrases (e.g. 太宰府天満宮's `"学業成就・合格祈願・厄除け"`); there is no enum or fixed vocabulary enforced at the field level.
4. **Is Admin/manual editing supported?** Yes — it is a plain Django Admin-editable `TextField` with no custom widget or validation found.
5. **Is provenance retained?** No. Nothing on `Shrine` records who wrote a given `goriyaku` string, when, or from what evidence. This is a materially weaker provenance guarantee than `ShrineDeity`/`ShrineHistory`, which carry `source_reference`/`verification_status`/`confidence`/`verified_at` by contract.
6. **Can Human Review safely produce it under the existing contract?** Partially. Human Review can *write into* the field mechanically (it's just a TextField), but the existing contract for `goriyaku` carries no provenance requirement, so a naive reuse would silently downgrade the provenance guarantee Human Review has been building for Knowledge Facts (Source-backed, `verification_status`-gated) back down to unaudited free text.
7. **Would doing so require a contract change?** Not a *code* contract change (no Model/migration needed), but it would require a *process* contract addition: a documented rule that Recommendation-Evidence-originated `goriyaku` writes must retain an audit trail external to the field itself (e.g. in a Review document, as Batch-17-style Human Review already does for Facts).

**Classification: REUSE_WITH_REVIEW_RULE.** The field and its downstream pipeline (`backfill_goriyaku_tags`, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`) can be reused exactly as-is with no schema change, provided the *process* — not the field — carries the provenance and Source-backing discipline that the field itself does not enforce.

## 9. GoriyakuTag Responsibility

Evaluated against `backfill_goriyaku_tags.py`, read in full this session:

- The command's tag-creation step is `GoriyakuTag.objects.get_or_create(name=name)` for every delimiter-split token of `goriyaku` — this is deterministic in the sense that identical text always produces identical tags, but it performs **zero canonicalization or existing-taxonomy matching**. A reviewer writing `"学業成就"` (matches existing `GoriyakuTag id=9`) produces a correct link; a reviewer writing a near-synonym like `"学問成就"` would silently create a **new, uncontrolled tag** rather than linking to the existing canonical one. This directly interacts with constraint #10 ("Do not create new taxonomy") — the mechanical safety of that constraint currently depends entirely on reviewer discipline, not on any code-level guard.
- **Recommendation: A (free-text `goriyaku` only), constrained by review process, not B.** Human Review should write free-text `goriyaku` using **only vocabulary that already exists as a `GoriyakuTag.name`** (41 such rows exist locally, including the exact study-purpose tags `学業成就`/`合格祈願`), then rely on the existing, unmodified `backfill_goriyaku_tags` command to perform the mechanical link. This avoids requiring reviewers to interact with `GoriyakuTag` IDs directly (error-prone, requires DB lookup) while structurally preventing new-taxonomy creation (reviewers select from a fixed vocabulary list, not free invention) — an operational safeguard, not a code change, so it satisfies constraint #10 without touching the command.
- Option C ("both") is rejected as unnecessary: since `backfill_goriyaku_tags` deterministically derives `GoriyakuTag` from `goriyaku` text when the vocabulary is constrained to existing tag names, having reviewers additionally hand-pick the canonical tag would be redundant duplicate entry with no additional safety, unless the constrained-vocabulary discipline above is not adopted (see Section 13 validation).

## 10. Provenance

| Option | Provenance | Implementation cost | Contract impact | Auditability | Semantic-drift risk |
|---|---|---|---|---|---|
| A — `goriyaku` text, no Source relation | None | Zero | None | None (indistinguishable from any other seed-time `goriyaku` edit) | High — no way to later verify why a given phrase was added |
| B — `goriyaku` text + audit reference to Source (in a Review document, not in the DB) | Document-level | Zero (reuses the same Markdown-review pattern `shrine-expansion-batch1-human-review.md` already established) | None (no Model/migration) | Full — same pattern already proven for Fact review | Low — every addition traceable to a specific Source citation in a reviewed document |
| C — explicit Recommendation Evidence artifact with a DB-level Source relation | DB-level, formal | High — requires new Model + migration | Violates constraints #11/#12 directly | Highest (structured) | Lowest, but not achievable without violating this task's own constraints |
| D — reuse Knowledge Fact relation indirectly (e.g. link `goriyaku` to the `ShrineHistory`/`ShrineDeity` row it was derived from) | DB-level, formal | High — requires new FK/M2M + migration | Violates constraints #11/#12 | High | Low, but not achievable without a schema change |

**Recommendation: Option B.** It is the only option that adds real provenance without violating constraints #11 ("Do not create Model") or #12 ("Do not create migration"), and it directly reuses a pattern (a dedicated, per-batch Markdown Human Review document citing exact Source text) that this repo has already run successfully for Batch 17 Fact review.

## 11. Review Stage Options

| Option | Safety | Reviewer cognitive load | Provenance | Scalability | Batch workflow complexity | Rollback | Auditability |
|---|---|---|---|---|---|---|---|
| A — Extend existing Human Review table with Recommendation Evidence columns | Medium — mixes two distinct review questions ("is this Fact correct" vs "does this shrine support Purpose X") in one pass, risking reviewer conflation | Higher per-row (two judgments at once) | Same document, so provenance is retained, but harder to isolate/re-review independently | Same as current | Low (no new stage) | Must re-open the same document to roll back either Fact or Evidence decisions | Mixed — a single doc audits both concerns, less separable |
| B — Separate Recommendation Evidence Review document, Knowledge review unchanged | High — keeps "Fact correctness" and "Recommendation interpretation" as textually distinct artifacts | Lower per-document (one judgment per pass) | Strong — new document cites Source text explicitly | Good — new document type, reusable per batch | Low — additive, not a new pipeline stage | Can roll back Evidence Review independently of Knowledge Review | High — mirrors the clean separation the task's own constraint #20 asks for |
| C — Separate pipeline stage after Human Review (Source → Facts → Human Review → Recommendation Evidence Review → Validation → Import) | Highest — formalizes ordering, prevents Evidence Review from starting before Fact Review is settled | Same as B, plus explicit gating | Strongest — stage boundary is enforced by workflow, not just convention | Best long-term, but adds a formal stage to every future batch | Highest now (new stage to define/document/run each batch) | Cleanest — each stage is independently re-runnable | Highest |
| D — Keep tracks fully separate (Knowledge expansion and Recommendation Evidence expansion never interact) | Avoids the coupling risk entirely | None | N/A | Does not scale — the original problem (rich Knowledge, zero Purpose matches) persists indefinitely | None | N/A | N/A but doesn't solve anything |

D is rejected outright — it is the status quo that motivated this audit and leaves the `MISSING_PIPELINE_BRIDGE` permanently unresolved. A is rejected as higher-risk for no real benefit over B. **Recommendation: Option B now, with an explicit note that it is structurally compatible with graduating to Option C later** (B's separate document already has the right boundary; C only adds formal workflow sequencing on top of the same document type, so no rework is needed if C is adopted later).

## 12. Minimal Evidence Contract

Per Section 8's REUSE_WITH_REVIEW_RULE classification and Section 10's Option B, the minimal Recommendation Evidence Review record needs exactly:

- **shrine** (which Shrine this applies to)
- **explicit Source reference** (which Source text supports this — reused from the same Source citation already required by `shrine-knowledge-contract.md`'s `Fact利用条件`, not a new Source model)
- **reviewed `goriyaku` text** (the exact free-text string a reviewer proposes to write, drawn only from existing `GoriyakuTag.name` vocabulary per Section 9)
- **canonical `GoriyakuTag` candidate** (which existing tag(s) this text is expected to resolve to via `backfill_goriyaku_tags`, recorded for reviewer self-check, not as a separate DB write)
- **verification state** (PASS / HOLD / NO_EVIDENCE — reusing the same tri-state vocabulary Batch 17's Human Review already uses for Facts, not inventing a new one)
- **reviewer decision** (who decided, when — same convention as the existing Human Review document)
- **HOLD reason** (free text, required when verification state is HOLD or NO_EVIDENCE)

No more fields than this are needed: everything downstream (`GoriyakuTag` linkage, `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS` matching, Compass/Concierge scoring) is already handled by existing, unmodified code once `Shrine.goriyaku` is written correctly.

## 13. Batch 17 Reconstruction

Using only the Section 6 classification (repo-preserved, Source-backed information only, no values written):

| Shrine | Classification |
|---|---|
| 北海道神宮 | **NO_EXPLICIT_EVIDENCE** — no Source-backed content states or implies any prayer/benefit; a Recommendation Evidence Review would correctly HOLD this shrine, not fabricate a `goriyaku` value |
| 建部大社 | **SOURCE_TEXT_REQUIRED** — the Yoritomo anecdote is a real, source_confirmed Fact, but per Section 7 it is IMPLICIT_ONLY; whether it is strong enough to support a `career`-adjacent `goriyaku` phrase is exactly the kind of judgment call the proposed Review stage exists to make, and cannot be resolved by this audit alone |
| 波上宮 | **READY_FOR_RECOMMENDATION_EVIDENCE_REVIEW** — multiple `source_confirmed` histories contain explicit prayer/outcome language (豊漁・豊穣・平穏・航海の平安); a reviewer has real Source text to evaluate against existing `GoriyakuTag` vocabulary, even though (per Section 6) none of it maps cleanly to a current `NEED_TAG` — that mapping-fit question is itself part of what Review should determine, not an audit pre-judgment |

## 14. Batch 18 Workflow Impact

For 多賀大社・日吉大社・普天満宮・沖縄県護国神社 (the 4 SOURCE_CONFIRMED candidates identified in `docs/audit/shrine-expansion-next-batch-planning.md`, PR #2569), if this task's Option B (Section 11) is adopted, the intended future sequence becomes:

```
Source Discovery → Fact Generation → Human Review (Fact correctness, unchanged)
  → Recommendation Evidence Review (new document, per Section 12's minimal contract)
  → Post-review Validation (per Section 15) → Production Import
```

This is additive to the existing Batch 17/planned Batch 18 sequence, not a replacement — Fact Generation and Fact-correctness Human Review remain exactly as-is. This sequence is **not** assumed final; it depends on Mother Ship's Phase 17 decision (Section 19 below), since Batch 18 could equally proceed with Fact Generation now and have Recommendation Evidence Review run as a distinct follow-up pass rather than an inline sequential step (this is exactly the RUN_BATCH_18_FACTS_IN_PARALLEL_WITH_CONTRACT option in Section 19).

## 15. Validation Responsibility

Conceptual checks only (no tooling implemented):

- Reviewed `goriyaku` text is non-empty for any shrine marked READY (as opposed to HOLD/NO_EVIDENCE)
- `GoriyakuTag` resolution succeeds after running the unmodified `backfill_goriyaku_tags` command — i.e., the reviewed text actually produces the intended canonical tag link, not an unintended new tag (directly checks the Section 9 risk)
- Source-backed review evidence exists for every non-HOLD shrine (the Review document itself, per Section 10 Option B, is this check's evidence)
- Purpose coverage becomes measurable (i.e., can be computed post-import — not a pass/fail gate itself, see Section 16)
- No unsupported semantic claim: the reviewed `goriyaku` text must trace to an explicit Source quotation, not a paraphrase that adds meaning the Source doesn't contain (this reuses Section 7's Fact/Interpretation boundary as the actual check)
- No ambiguous label mapping: the reviewed text must resolve to exactly the intended `GoriyakuTag` id(s), not an unrelated existing tag with coincidentally similar wording

## 16. Compass / Concierge Shared Contract

Both Compass and Concierge read the same `Shrine.goriyaku`/`goriyaku_tags` fields and the same `_prefilter_candidates_for_need`/`_attach_breakdown` functions in `concierge_chat_ranking.py` (confirmed in PR #2571's fresh read, re-confirmed unchanged this session). Since the proposed Evidence Review stage writes into exactly these shared fields via the existing, unmodified pipeline, and does not touch anything Compass-specific (Direction/Distance filtering) or Concierge-specific (nationwide candidate pool, LLM interpretation) —

**Classification: SHARED_STAGE_SUFFICIENT.** No Compass-specific or Concierge-specific review variant is needed; a single Recommendation Evidence Review, writing to the shared `goriyaku` field, benefits both surfaces identically and simultaneously, exactly as `太宰府天満宮`'s existing `goriyaku` already does today.

## 17. KPI Boundary

**Geographic Data KPI** (existing, from `shrine-expansion-next-batch-planning.md`): shrine count, covered prefectures, regional density. Unaffected by this design — it measures whether shrines physically exist in under-covered areas, independent of whether they carry Recommendation Evidence.

**Recommendation Evidence KPI** (new dimension this design introduces, measurement only, no thresholds set): recommendation-ready shrine count (shrines with non-empty `goriyaku`/`goriyaku_tags` after Review), goriyaku coverage (% of imported shrines that reach READY vs HOLD/NO_EVIDENCE per Section 13's tri-state), purpose-matchable shrine count (shrines whose `goriyaku_tags` resolve to at least one `NEED_TO_GORIYAKU_IDS` value for some Purpose), purpose geographic coverage (prefectures where at least one purpose-matchable shrine exists, per Purpose — the metric that would, if computed today, explain why `study` specifically underperforms per the earlier session's geographic-sparsity finding).

These two KPIs are kept deliberately separate: a shrine can be Geographic-KPI-positive (physically added, fixes a coverage gap) while being Recommendation-Evidence-KPI-negative (NO_EXPLICIT_EVIDENCE, like 北海道神宮) — the two tracks answer different questions and neither should be used to infer the other.

## 18. Minimal Follow-up PR

No existing document defines a Recommendation Evidence Review Contract (confirmed: `docs/knowledge/shrine-knowledge-contract.md` defines the Fact/Source contract only; no `docs/knowledge/` or `docs/audit/` file defines Recommendation Evidence Review). Therefore the smallest next PR is:

**`docs/review: define Recommendation Evidence Review Contract`** — a docs-only PR that formalizes Section 12's minimal contract (fields, tri-state verification, HOLD-reason requirement, "text must be drawn from existing `GoriyakuTag` vocabulary" rule) as a standalone contract document, mirroring how `docs/knowledge/shrine-knowledge-contract.md` formalized the Fact contract before any Fact review was run. Only after that contract exists should a **`data: Batch 17 Recommendation Evidence Human Review`** PR (applying Section 12's contract to the 3 Section 13 classifications) follow, since Batch 17 is the one batch with committed Source text already available for a full pilot.

## 19. Batch 18 Decision Input

**DEFINE_EVIDENCE_REVIEW_CONTRACT_FIRST.**

Reasoning: Section 13 shows Batch 17 already contains one READY shrine (波上宮) and one SOURCE_TEXT_REQUIRED judgment call (建部大社) that a contract-less, ad-hoc review would handle inconsistently. Defining the contract first (Section 18's first PR) costs nothing against Batch 18's timeline — it is docs-only and does not block Fact Generation, which has no dependency on it. Running a Batch 17 pilot against a real, already-available contract before Batch 18 Facts exist would validate the contract cheaply (3 shrines, already-committed Source text, no new Discovery/Source work needed) before investing reviewer effort in 4 more shrines. This is offered as the audit's assessment, not a final decision — Mother Ship's actual choice is recorded in Section 20.

## 20. Mother Ship Decision

*(Pending — this section intentionally left for Mother Ship input at PR review time, per the task's own instruction that Phase 17's decision is "Mother Ship input only".)*

## 21. Limitations

- This audit evaluated only Batch 17's 3 shrines' committed Source text; it did not re-verify the 4 candidate Batch 18 shrines (多賀大社・日吉大社・普天満宮・沖縄県護国神社) since their Facts have not yet been generated (Batch 18 Fact Generation is explicitly out of scope, constraint #16).
- The `travel_safe` NEED_TAG's `NEED_TO_GORIYAKU_IDS` mapping ({10, 22, 23} → 合格祈願/美容/方除け) does not semantically match "travel safety" at the GoriyakuTag-name level; this is a pre-existing, out-of-scope data-quality question (the code comment at `need_to_goriyaku_tag_ids.py` itself references a separate `docs/audit/compass-purpose-goriyaku-mapping.md` VALID/QUESTIONABLE/INVALID/MISSING classification) and is noted here only because it affects how cleanly 波上宮's 航海安全 content could map to an existing Purpose — it is not evaluated or resolved by this audit.
- This audit's Fact/Interpretation classification (Section 6, 13) is a human (assistant) reading of Source text, not itself a Human Review decision under the proposed contract — it demonstrates the kind of judgment the proposed Review stage would need to make, but does not substitute for that Review.
- Local DB verification (GoriyakuTag ids 9/10/22/23, 41 total rows) was performed against the session's local scratch DB (`shrine_dataset_audit_local`), not Production; Production's `GoriyakuTag` table is expected to match since both are seeded from the same tracked fixtures, but this was not independently re-verified against Production in this audit.

## 22. Out of Scope

- UI / frontend changes
- Automatic semantic inference (Deity→Purpose, History→Purpose, Tradition→Purpose)
- Production DB mutation
- Batch 18 Fact Generation implementation
- Recommendation Engine, C1 Max, Mapping, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS` code changes
- New Model or migration definition
- Final resolution of the `travel_safe` GID-mapping quality question noted in Section 21
