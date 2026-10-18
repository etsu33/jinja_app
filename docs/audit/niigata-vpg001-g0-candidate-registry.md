# NIIGATA-001-VPG001 — G0 Candidate Registry Admission

## 1. Status

```text
VPG001 MEMBERSHIP            = FROZEN
G0                           = PASS
G1                           = NOT STARTED
G2                           = NOT STARTED
Product Surface              = NOT DECIDED
Production write             = NONE
Recommendation eligibility   = NOT EVALUATED
CORE_READY                   = NO
```

- Recorded at: 2026-10-18
- Base: `develop@230e1a3`（PR #3260 merge, VPG001 freeze）
- Branch: `feature/niigata-vpg001-g0-candidate-registry`

## 2. Authority

- `docs/audit/niigata-001-vpg001-freeze.md`（frozen VPG001 membership; not modified）
- `docs/audit/niigata-batch001-ready-set-freeze.md`（frozen Source rows and handoff membership; not modified）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（Nationwide G0 initial state,
  admission_provenance, build_batch responsibility boundary, G0 / G1 boundary）
- Precedent: NIIGATA-001-H004 G0 registration（`docs/audit/niigata-h004-g0-candidate-registry.md`）

## 3. Three roles that stay separate

```text
Source handoff    = provenance unit       （frozen Ready Set; where a row came from）
VPG001            = processing selection  （audit-level; which rows to process next）
Candidate Master  = lifecycle authority   （registry rows and their gate state）
```

A member is admitted while the other four members of its Source handoff stay unregistered. This does
**not** mutate or partially redefine the frozen Source handoff. The handoff keeps its five members in
Source order. Only Candidate Master registration is partial.

## 4. Registered candidates

Exactly five rows were appended to `backend/temples/data/shrine_expansion_candidate_master.json`, in
VPG001 order. `candidate_name` and `source_position` are byte-identical to the frozen Ready Set and the
VPG001 freeze record（checked by test）:

| candidate_id | candidate_name | source_position | admission_provenance.handoff_id（original Source handoff） | frozen raw_address（not stored, see §6） |
|---|---|---|---|---|
| nsrc-000021 | 荒川神社 | page008-row003 | NIIGATA-001-H015 | 胎内市桃崎浜187番地 |
| nsrc-000022 | 五十嵐神社 | page010-row004 | NIIGATA-001-H019 | 三条市大字飯田2283番地 |
| nsrc-000023 | 熱串彦神社 | page006-row010 | NIIGATA-001-H012 | 佐渡市長江854番地 |
| nsrc-000024 | 秋葉神社 | page003-row007 | NIIGATA-001-H006 | 新潟市秋葉区秋葉3丁目8番19号 |
| nsrc-000025 | 天津神社 | page007-row006 | NIIGATA-001-H014 | 糸魚川市一の宮1丁目3番34号 |

IDs continue the global serial after nsrc-000020（H004）. No ID is reused or renumbered.
`NIIGATA-001-VPG001` appears in no Candidate Master field.

## 5. Initial Nationwide G0 state（all five）

```text
candidate_status        = DISCOVERED
status_reason_code      = REGISTRY_ADMISSION_COMPLETE
identity_status         = UNREVIEWED
duplicate_status        = UNREVIEWED
official_source_status  = AVAILABLE
knowledge_status        = UNREVIEWED
build_batch             = null
wave_id                 = null
candidate_reason        = official_source_full_enumeration_candidate
```

admission_provenance（immutable after G0）:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
handoff_id             = each member's ORIGINAL frozen Source handoff（§4）
source_position        = exact frozen position（§4）
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

`handoff_id` is never `NIIGATA-001-VPG001`. `build_batch` is not inferred from the processing group, the
Source batch or the Source handoff.

## 6. What is deliberately not done

```text
identity decision（identity_status = CONFIRMED）    NOT DONE（G1）
duplicate decision                                 NOT DONE（G1）
official_name / official_address / reading          NOT HYDRATED
official source / screening evidence                NOT HYDRATED
latitude / longitude / location                     NOT ASSIGNED（G2）
Google Maps coordinates（天津神社 screenshots）      NOT ADOPTED
shrine_id / Base Shrine Seed row                    NOT CREATED
goriyaku / goriyaku_tags / Knowledge                NOT CREATED
build_batch                                         null
product_surface                                     NOT ADDED（no such field）
Recommendation ranking                              UNCHANGED
Production                                          NOT CONNECTED
```

The frozen `raw_address` stays in the Ready Set and is not copied into Candidate Master as
`official_address`.

天津神社: the screening audit records deity evidence as primary-source verified by Mother Ship, with the
deity name and source reference `NOT_SUPPLIED_IN_REPO`. None of that screening evidence enters Candidate
Master at G0. The row has the same G0 state as the other four. The two-honden（天津神社・奴奈川神社）
structure remains a G1 / G3 MODEL_RISK question.

No identity or duplicate conclusion is drawn from names. 秋葉神社 is a common shrine name. Whether
nsrc-000024 duplicates an existing Shrine is a G1 question, not a G0 fact.

## 7. Partial Source handoff representation

```text
shrine_expansion_handoffs.json（handoff manifest）   UNCHANGED（H001–H004 only）
H006 / H012 / H014 / H015 / H019                     NOT added, not even partially
```

The handoff manifest describes whole registered handoffs. A partially registered Source handoff is not
written into it, and the original handoffs are not rewritten around the selected member. Instead, a
separate **test-only** fixture describes the processing group:

```text
backend/temples/tests/fixtures/shrine_expansion_value_selected_groups.json
  processing_group_id = NIIGATA-001-VPG001
  members: candidate_id, candidate_name, source_position, source_handoff（original）,
           identity_status, duplicate_status, expected G0 lifecycle
```

It is not runtime input and not Candidate Master authority. Every Nationwide Candidate Master row is
covered by exactly one of the two fixtures.

| Source handoff | frozen members（unchanged） | registered at G0 | unregistered |
|---|---|---|---|
| NIIGATA-001-H006 | page003-row006 … page003-row010 | page003-row007（nsrc-000024） | 4 |
| NIIGATA-001-H012 | page006-row006 … page006-row010 | page006-row010（nsrc-000023） | 4 |
| NIIGATA-001-H014 | page007-row006 … page007-row010 | page007-row006（nsrc-000025） | 4 |
| NIIGATA-001-H015 | page008-row001 … page008-row005 | page008-row003（nsrc-000021） | 4 |
| NIIGATA-001-H019 | page010-row001 … page010-row005 | page010-row004（nsrc-000022） | 4 |

A later admission of one of the 20 unregistered rows gets the next free `nsrc-*` ID and the same original
Source handoff as `handoff_id`. That is a separate decision.

## 8. Changed files

| File | Change |
|---|---|
| `backend/temples/data/shrine_expansion_candidate_master.json` | 5 rows appended（64 → 69）. Existing rows and top-level keys unchanged. The nsrc-000020 line differs only by the added trailing comma |
| `backend/temples/tests/fixtures/shrine_expansion_value_selected_groups.json` | new test-only VPG001 fixture（§7） |
| `backend/temples/tests/test_shrine_expansion_candidate_master.py` | VPG001 G0 tests + 30 mutation rejections; coverage test accepts VPG-covered rows（§9）; `_h002_extra_member` moved to the unregistered `nsrc-000026` |
| `backend/temples/tests/test_g6_nationwide_handoff_identity.py` | VPG001 members are absent from the identity manifest and every lookup fails closed |
| this file | — |

Not changed: frozen Ready Set, VPG001 freeze record, handoff manifest（`shrine_expansion_handoffs.json`）,
identity manifest, Base / Knowledge Seed, H001–H004 rows（H004 stays G0 ×5; PR #3258 is still evidence
only）, Priority Policy, gate and Candidate Master contracts.

## 9. Tests

One existing test needed an update, and the handoff manifest was **not** changed for it.
`test_every_registered_handoff_is_in_the_manifest` asserted that every Candidate Master `handoff_id` is a
whole handoff in the handoff manifest. It now skips rows covered by the value-selected group fixture, and
additionally asserts that every Nationwide row is covered by exactly one of the two fixtures. Its purpose
is kept: an unregistered handoff or an uncovered row still fails.

`_h002_extra_member`（the H002 "member added" mutation）used `nsrc-000021`, now a real ID. It moves to
the unregistered `nsrc-000026`, so the mutation still fails for the intended reason.

New tests（literals independent of the fixture）:

| # | Requirement | Test |
|---|---|---|
| 1 | exact membership = five rows only | `test_niigata_vpg001_is_registered_at_g0_only`, `test_vpg001_fixture_matches_freeze_record_and_frozen_ready_set` |
| 2 | candidate_id nsrc-000021 … nsrc-000025 | `test_niigata_vpg001_is_registered_at_g0_only`（serial is nsrc-000001 … 000025） |
| 3 | name / position / original source_handoff | fixture vs literal vs VPG001 freeze §3 vs frozen Ready Set（incl. raw_address, RUNNER_READY） |
| 4–7 | G0 lifecycle exact; identity / duplicate UNREVIEWED; build_batch null | `test_niigata_vpg001_is_registered_at_g0_only`（exact row equality） |
| 8 | no product_surface field | same, plus forbidden-field set |
| 9 | no VPG ID in admission_provenance.handoff_id | same, over all Nationwide rows |
| 10 | original H006 / H012 / H014 / H015 / H019 unchanged | `test_vpg001_source_handoff_membership_is_unchanged`（5 each in Source order, absent from the handoff manifest, the 20 others unregistered） |
| 11 | H001–H004 unchanged | handoff contracts pass + literal state snapshot of nsrc-000001 … 000020 |
| 12 | no Base Seed / Knowledge hydration | `test_vpg001_has_no_base_seed_or_knowledge_hydration` |
| 13 | 天津神社 screening evidence does not hydrate Candidate Master | `test_vpg001_amatsu_screening_evidence_does_not_hydrate_candidate_master` |
| 14 | absent from the reviewed identity manifest | `test_vpg001_g0_members_are_not_reviewed_identities`（G6） |
| 15 | G6 identity lookup fails closed | same: each original Source handoff and `NIIGATA-001-VPG001` raise `unknown handoff` |

`test_niigata_vpg001_contract_rejects_mutations`（30 cases）:

- handoff_id = VPG001 / wrong Source handoff; source_position / snapshot changed
- premature identity CONFIRMED; duplicate NEW / SAME_NAME_DIFFERENT_SHRINE
- BUILD_READY / IMPORTED / CORE_READY; reason beyond G0; official source / knowledge advancement
- build_batch = VPG001 / Source handoff; wave_id = W0; product_surface field
- processing_group_id / priority_class field; 天津神社 deity_evidence hydrated
- official name / address, reading, coordinate, shrine_id, goriyaku hydration
- name changed; member removed; a sibling of the Source handoff registered; reused nsrc ID

## 10. Validation

Local disposable PostgreSQL 16, Python 3.11:

```text
test_shrine_expansion_candidate_master.py + test_g6_nationwide_handoff_identity.py   717 passed
backend full suite（-n auto）                                                         6248 passed, 8 skipped
ruff check（changed tests）                                                          clean
ruff format（added blocks）                                                          clean
git diff --check                                                                    clean
handoff manifest / identity manifest vs origin/develop                              unchanged
Base Seed / Knowledge Seeds vs origin/develop                                       unchanged
frozen Ready Set / VPG001 freeze record vs origin/develop                           unchanged
```

`test_shrine_expansion_candidate_master.py` was already not `ruff format`-clean on develop. Only the added
blocks were formatted, to keep the diff scoped.

## 11. Next

```text
NEXT_GATE = G1（identity / duplicate review, separate PR）
天津神社 G1 prerequisite = record deity name / primary source reference（NOT_SUPPLIED_IN_REPO）
```
