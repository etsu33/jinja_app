# A-5b HOLD Evidence Artifact — 富岡八幡宮

- Position: `candidate_order = 9` of the fixed A-5b input set (Pattern C, historical `BACKFILL_READY` / `DEFERRED_READY`)
- Contract: `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` §6.1, §6.2, §7, §7.1
- Policy: `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §12.1–§12.8
- Base: `develop@0a4491b2505865806af718ac384c5ef8632cb2f3` (includes PR #3061)
- Current authoritative evaluation: `a5b_freeze_status = HOLD`, `reason_code = UNSATISFIED_FREEZE_CONDITIONS`
- Replacement (§6.4) / invalidation (§6.5): **NONE**. One identity at this position
- Seed / Source data / DB / importer / runtime change: **NONE**. HOLD performs zero writes (§6.2)
- Membership / ShrineDeity created: **NONE**
- Historical candidate-freeze document (`docs/audit/collective-deity-backfill-candidate-freeze.md`): **unchanged**
- Fixed-candidate-set closure audit: **not updated by this document**

This is not a Freeze Evidence Artifact. It records why the position cannot reach
`FREEZE` under the current contracts.

## 1. Candidate identity

```text
shrine_ref.name_jp     = 富岡八幡宮
shrine_ref.address     = 東京都江東区富岡1-20-3
source_attested_label  = 応神天皇（誉田別命）外８柱
```

| Field | Value |
|---|---|
| `candidate_order` | `9`: first appearance in the historical freeze doc §5.3 row 1 (after §5.1 ×6 and §5.2 ×2) |
| historical classification | `BACKFILL_READY` (freeze doc §5.3) / `DEFERRED_READY` (freeze doc §10) |
| historical `source_key` | `batch13-tomioka-official` (`batch_13_seed.json`) |

- The label is the historical fixed-input label, recorded verbatim and unchanged.
- It contains full-width `８` (U+FF18).
- No current direct verification confirms that form against the Source (§3).

## 2. Official Source identity

| Field | Value |
|---|---|
| source_type | `shrine_official` |
| publisher | 富岡八幡宮 |
| url | `http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html` |

- **Portable identity:** `shrine_official` + the URL above (A-5b §7.1).
- **Scheme:** `http` and `https` are separate identities under `normalize_source_url`.
- **No `source_key`:** none is issued or reserved by this document.

## 3. Current Source retrieval (2026-10-02 audit)

Fresh attempts during the 2026-10-02 audit, as recorded by Mother Ship:

| Attempt | Result |
|---|---|
| HTTP legacy URL | body not acquired |
| HTTPS equivalent | body not acquired |
| `www` / non-`www` variants | body not acquired |
| official-domain alternative pages | target 御由緒 body not acquired |
| official PDFs / official-domain search | target 御由緒 body not acquired |
| alternate HTTP retrieval path | body not acquired |

```text
fresh direct official body = NOT ACQUIRED
```

- The official domain is still alive. The target 御由緒 body could not be retrieved
  directly in this audit.
- No direct verification event exists for this audit, so no `verified_at` is recorded.

## 4. Historical evidence (discovery / historical audit context only)

| Record | Content | Use in this document |
|---|---|---|
| `docs/audit/knowledge-batch13-seed-preflight.md` §3 (L68–L73) | The official page was checked directly in the Browser pane during Batch13 and contained 「御祭神 応神天皇（誉田別命）外８柱」 | historical only |
| `docs/audit/knowledge-batch13-seed-preflight.md` L17, L97 | the official site lists only 「御祭神 応神天皇（誉田別命）外８柱」 and does not name the other 8 | historical only |
| Source note on `batch13-tomioka-official` (`batch_13_seed.json`) | quotes 「御祭神 応神天皇（誉田別命）外８柱」 | historical only |
| historical freeze doc §5.3 | label, known member 応神天皇, unnamed remainder 8 | historical only |

Constraints applied (Seed 1.1 contract §12.2, §12.3, §12.8):

- The historical verification is **not** promoted to a new direct verification event.
- It cannot provide the new Collective `verified_at`.
- The Source's prior `verified_at` is not inherited.
- The legacy Fact / Deity `verified_at` is not inherited.
- No datetime is reconstructed from audit dates, commits, notes, or metadata.

**Raw snapshot status.** The repository holds none of the following with the official
page body:

- raw HTML
- response body
- WARC
- page snapshot
- screenshot

It holds only historical audit prose, the Source note, the Deity note, and the prior
preflight record. They remain historical evidence only.

## 5. Production read-only observations

All observations are SELECT-only with Production write `0`, as recorded by
Mother Ship. They are Production observation events, not Source verification events.

### 5.1 Observation event 1 — Shrine identity

| Field | Value |
|---|---|
| Observed at | `2026-10-02T14:13:09.000074+09:00` |
| Query identity | `name_jp = 富岡八幡宮`, `address = 東京都江東区富岡1-20-3` |
| Exact identity rows | `1` |
| Row | id `49`, 富岡八幡宮, 東京都江東区富岡1-20-3 |

- Under `resolve_shrine` (`backend/temples/services/knowledge_seed.py`), an exact
  `name_jp` + `address` match on exactly one row returns `OK`, so
  `resolved_shrine_id = 49`.
- The historical row id `104` (`docs/audit/tomioka-hachimangu-identity-resolution.md`,
  `SAME_REAL_SHRINE_DUPLICATE`) does not appear in this result.
- This document draws no conclusion about why id `104` is absent. The fresh
  observation is authoritative for this audit.

### 5.2 Observation event 2 — Existing Collective

| Field | Value |
|---|---|
| Observed at | `2026-10-02T14:16:02.742915+09:00` |
| Query identity | `shrine_id = 49`, `source_attested_label = 応神天皇（誉田別命）外８柱` |
| Matching rows | `0` |

```text
existing Collective preflight = PASS
planned_action                = CREATE if a later FREEZE becomes possible
COLLECTIVE_CONFLICT           = NO
COLLECTIVE_AMBIGUOUS          = NO
```

### 5.3 Observation event 3 — Membership target

| Field | Value |
|---|---|
| Observed at | `2026-10-02T14:31:31.047587+09:00` |
| ShrineDeity id | `188` |
| shrine_id | `49` |
| display_name | 応神天皇 |
| canonical_name | 応神天皇（誉田別命） |
| role | `primary` |
| verification_status | `source_confirmed` |
| confidence | `high` |

- Membership target reference resolution = **PASS**: a same-Shrine ShrineDeity exists.
- Membership Evidence B is **not PASS**.
  - Policy B requires the Membership's own independent Source evidence.
  - No current direct official Source verification event exists to supply it.
- The existing ShrineDeity's `verification_status`, `confidence`, and source relation
  are legacy Facts. They are not inherited (P3).

### 5.4 Non-Source blocker summary

```text
non_source_blocker_count = 0
```

Confirmed by events 1–3:

- Shrine identity resolves
- the existing Collective does not conflict
- the known member ShrineDeity resolves
- no Production ambiguity
- no existing-row mismatch

Remaining blocker: current direct official Source verification only.

## 6. P1–P5 status

| Policy | Status | Reason |
|---|---|---|
| P1 (§12.1) | **NOT ESTABLISHED** | No current direct event confirms that 「応神天皇（誉田別命）外８柱」 is a verbatim contiguous substring of the Source. This includes the numeral form (full-width `８` vs ASCII `8`) |
| P2 (§12.2) | **NOT ESTABLISHED** | Source content not directly confirmed. Historical prose and notes are discovery-only |
| P3 (§12.3) | applied | legacy Facts and notes are used only for discovery and identity matching |
| P4 (§12.4) | not evaluated | no Source content available |
| P5 (§12.5) | **NOT ESTABLISHED** | 「外８柱」 leaves total vs remainder unresolved without the Source. `unspecified` / `null` must not be used to bypass this (§6.2) |

## 7. Values not frozen

The following are **not** frozen by this document. No concrete value is recorded:

- `member_count`
- `member_count_relation`
- `member_list_status`
- `role`
- `verification_status`
- `confidence`
- `verified_at`
- `memberships[]` evidence

The proposed known Membership 応神天皇 (historical freeze doc §5.3, "known Membership
only") resolves to ShrineDeity id `188` (§5.3). It has no current Source evidence entry.

## 8. §6.1 evaluation

| # | Result | Basis |
|---|---|---|
| 1 | PASS | fixed A-5b `candidate_order` 9 |
| 2 | PASS | Production event 1: exact Shrine identity = 1, `resolved_shrine_id = 49` |
| 3 | UNSATISFIED | historical repository text records the label, but no current contract-compliant direct official Source event verifies the verbatim substring for this FREEZE packet |
| 4 | UNSATISFIED | the Source identity is traceable, but the current official Source body could not be directly confirmed |
| 5 | UNSATISFIED | count / relation / `member_list_status` cannot be finalized under P5 without direct Source verification. `null` / `unspecified` is not used to bypass unresolved numeric semantics |
| 6 | PASS | the known member candidate 応神天皇 resolves to same-Shrine ShrineDeity id `188` (event 3) |
| 7 | UNSATISFIED | Membership Evidence B cannot be completed without a current direct official Source event |
| 8 | UNSATISFIED | final count / relation values are not contract-validly established |
| 9 | UNSATISFIED | the new Collective `verified_at` cannot be established under §12.8 |
| 10 | UNSATISFIED | Production conflicts are clear (events 1–3), but Source verification is unresolved |
| 11 | UNSATISFIED | completing the FREEZE packet would require relying on historical notes / prior judgments beyond the current direct verification contract |
| 12 | UNSATISFIED | no contract-compliant Freeze Evidence Artifact can record every required assertion as `SUPPORTED` |

```text
satisfied   = 1, 2, 6
unsatisfied = 3, 4, 5, 7, 8, 9, 10, 11, 12
```

## 9. HOLD basis (A-5b contract §6.2)

| §6.2 HOLD condition | Applies |
|---|---|
| verification metadata cannot be established under the current contract | yes (§3, §4) |
| the Collective assertion is supported only by notes, legacy Facts, or prior judgments, with no direct Source confirmation (P2 / P3) | yes (§4) |
| a numeric expression exists but the Source does not establish its semantics (P5) | yes: unresolved without the Source (§6) |
| member relation is not independently Source-backed | yes (§5.3) |
| no contract-compliant Freeze Evidence Artifact exists, or a required assertion in it is not auditable | yes |

## 10. Final record

```text
candidate_order   = 9
a5b_freeze_status = HOLD
reason_code       = UNSATISFIED_FREEZE_CONDITIONS
review_note       = HOLD: current contract-compliant direct verification against the
                    accepted official Source could not be completed; Production
                    identity, existing Collective, and known Membership target are
                    otherwise resolved.
```

```text
primary_blocker = fresh contract-compliant direct verification against the accepted
                  official Source could not be completed
```

To re-evaluate this position, a new timestamped direct verification event against
the accepted official Source is required (Seed 1.1 contract §12.8). Re-evaluation
then follows P1–P5 and §6.1 fresh, with no judgment inherited from this document.

## 11. Mutation record

```text
Seed 1.1 mutation        0
source_key assigned      0
importer run             0
migration                0
DB / Production write    0
runtime change           0
Membership created       0
ShrineDeity created      0
```
