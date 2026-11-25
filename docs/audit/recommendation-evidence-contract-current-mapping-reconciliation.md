# Recommendation Evidence Contract — Current Mapping Reconciliation (P10)

## Metadata

| Field | Value |
|---|---|
| Task | P10 — `DOC_RECONCILIATION`. Reconcile `docs/knowledge/recommendation-evidence-review-contract.md` (§8, §13, §19) with current physical Recommendation mapping truth. **Docs-only.** |
| Type | Documentation reconciliation. No runtime code, no mapping, no taxonomy, no Product decision. |
| Branch | `docs/reconcile-recommendation-evidence-current-mapping` |
| Base | `origin/develop` @ `6e69fefd5ab84b77b00004fcf712897b0e839bc3` (merge of PR #2615). `git fetch origin` this session; `develop` had not advanced beyond the expected merge → `BASE_DRIFT_REQUIRES_REVIEW` not triggered. |
| Date | 2026-08-29 |
| Origin of the finding | `docs/audit/shrine-evidence-integrity-full-audit.md` §15 / P10 (`DOC_DRIFT_CURRENT_MAPPING`). |

## Physical truth (fresh read this session)

`backend/temples/domain/need_to_goriyaku_tag_ids.py`:

```python
"travel_safe": {3, 13, 14},
```

Canonical 39-row `GoriyakuTag` master (contract §5, confirmed `ALIGNED` against
Production in `docs/audit/production-canonical-set-preflight.md`):

| id | name |
|---|---|
| 3 | 交通安全 |
| 13 | 航海安全 |
| 14 | 海上安全 |

Pinned by `backend/temples/tests/test_need_to_goriyaku_tag_ids.py`:
`test_travel_safe_mapping_matches_master_integrity_correction` asserts
`NEED_TO_GORIYAKU_IDS["travel_safe"] == {3, 13, 14}`;
`test_ids_42_to_45_referenced_nowhere` asserts no `NEED_TO_GORIYAKU_IDS` value
references ids 42–45. **19/19 need-mapping tests pass** at this base SHA.

## Chronology (provenance preserved, not rewritten)

1. **PR #2571** — `MISSING_PIPELINE_BRIDGE` established.
2. **PR #2572** (`recommendation-evidence-followup-design.md` §21) — flagged
   `travel_safe = {10, 22, 23}` as an open mapping-quality question; ids 13/14
   were **not** in any `NEED_TO_GORIYAKU_IDS` value at that time.
3. The Recommendation Evidence Review Contract was authored — its §8 / §19
   correctly described the state **as of that moment** (ids 13/14 unwired;
   stale ids 42–45 referenced).
4. **`goriyaku-mapping-master-integrity.md` → `goriyaku-mapping-master-integrity-correction.md`**
   (shipped correction PR) — corrected `travel_safe` to `{3, 13, 14}` and
   removed every stale reference to ids 42–45. The contract text was **not**
   updated then → the drift this note records.
5. **PR #2611 / #2614** — audits re-identified the stale contract text as
   `DOC_DRIFT_CURRENT_MAPPING`, recommended a separate docs-only fix (this PR).

## Stale current/normative claims found — and corrected

| Location | Stale claim | Reconciled to |
|---|---|---|
| §8 (Shrine-level Readiness), RECOMMENDATION_READY note | "`航海安全`/`海上安全` (ids 13/14) … neither ID currently appears in any `NEED_TO_GORIYAKU_IDS` value … a Mapping-layer gap … the `travel_safe` mapping question already flagged as unresolved in PR #2572 §21" | ids 3/13/14 **are** consumed by `travel_safe` in the runtime module (pinned by tests); a Source-backed PASS on one satisfies the Purpose-connectivity half of RECOMMENDATION_READY for `travel_safe` — still needs a valid PASS. The "PASS-but-unwired" illustration now points, generally, to the 10 genuinely-unwired canonical concepts (`shrine-evidence-integrity-full-audit.md`), explicitly deferred to the separate **P7** track. |
| §13 (Batch 17 Pilot Template), 波上宮 row Notes | "even a PASS on 航海安全-adjacent content would not by itself yield RECOMMENDATION_READY under current Mapping" | `航海安全`/`海上安全` are consumed by `travel_safe` now, so a valid PASS on 波上宮's voyage-safety content **would** contribute to RECOMMENDATION_READY for `travel_safe`; the PASS/HOLD decision itself is still not pre-decided by the template. |
| §19 (Limitations), bullet 1 | "does not resolve the `travel_safe` … mapping-quality question ({10, 22, 23}) … referenced again in Section 8 as a live example of a Mapping-layer gap" | Reframed as history: flagged at PR #2572 time (`{10, 22, 23}`), **subsequently corrected** to `{3, 13, 14}`; contract still changes no mapping; ids 13/14 no longer an unwired example. |
| §19 (Limitations), bullet 2 | "several `NEED_TO_GORIYAKU_IDS` values (e.g. ids 42–45 …) do not correspond to any row in the current 39-row `GoriyakuTag` table" | Those stale references were removed in the same correction PR; non-recurrence pinned by `test_ids_42_to_45_referenced_nowhere`. Purpose Mapping stays governed by the runtime module, not a table duplicated in the contract. |
| Status blockquote (top) | *(no stale claim)* | Added a dated "Documentation reconciliation (P10)" note pointing here. |

## Historical claims intentionally left unchanged

- `docs/audit/recommendation-evidence-followup-design.md` §21 and any doc
  describing `travel_safe = {10, 22, 23}` **at PR #2572 time** — correct history.
- `docs/audit/ranking-contract-deep-audit-batch7-source.md` (`travel_safe | {10,22,23}`)
  — historical audit snapshot, pre-correction.
- `docs/audit/goriyaku-mapping-master-integrity*.md`,
  `docs/audit/safe-remaining-need-goriyaku-mapping-correction.md`,
  `docs/audit/semantic-followup-decision-and-pr-split.md` — already state the
  corrected `{3, 13, 14}`; no change.
- `docs/audit/shrine-evidence-integrity-pilot.md` — already says the stale note
  is "not reproduced" and ids 13/14 are wired; no change.
- `docs/audit/shrine-evidence-integrity-full-audit.md` §15 `DOC_DRIFT_CURRENT_MAPPING`
  finding — a point-in-time audit record of the drift that this PR resolves;
  left intact (history), resolution recorded here.
- Contract §19 bullet 3 ("verified against the session's local scratch DB …
  not re-verified against Production directly") — an accurate provenance note
  about the *original contract PR*'s verification method; not a mapping claim,
  left unchanged. (Production `GoriyakuTag` alignment was later independently
  confirmed `ALIGNED` 39/39 in `production-canonical-set-preflight.md`.)

## Consistency statements preserved by the reconciliation

1. Source-backed evidence is required for Recommendation Evidence — **unchanged**.
2. Knowledge Fact correctness does not imply Recommendation eligibility (§3) — **unchanged**.
3. A canonical `GoriyakuTag` being valid does not itself imply Purpose wiring — **unchanged**.
4. Purpose wiring does not itself imply Source-backed eligibility — **unchanged** (made explicit in §8: "wiring is never evidence").
5. `travel_safe` currently consumes ids 3/13/14 — **now stated correctly**.
6. ids 13/14 are no longer an example of an unwired canonical tag — **corrected**.
7. Current Purpose Mapping is governed by the runtime module `need_to_goriyaku_tag_ids.py`, not duplicated in the contract — **stated**; no mapping table copied in.
8. P7 remains the separate Product-decision track for genuinely unwired canonical concepts — **stated**; P10 wires nothing and decides no taxonomy.

## Non-scope / no-write confirmation

No change to `backend/temples/domain/need_to_goriyaku_tag_ids.py`,
`backend/temples/services/`, `backend/temples/models.py`, migrations, fixtures,
seeds, Production data, Knowledge rows, Shrine rows, `Shrine.goriyaku`,
`GoriyakuTag`, Evidence Gate, Recommendation ranking, C1 scoring, Lead, Reason,
interpreter, Compass/Concierge runtime, frontend, or the Google Spreadsheet. No
test file modified. P7 (and P1–P6, P8) not started. The Recommendation Evidence
eligibility contract, and the Knowledge-Fact-correctness ≠ eligibility ≠
Purpose-connectivity separation, are unchanged — only the stale mapping example
was corrected.
