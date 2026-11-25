# NIIGATA-001-H004 — G0 Candidate Registry Admission

## 1. Status

```text
G0                           = PASS
G1                           = NOT STARTED
G2                           = NOT STARTED
Product Surface              = NOT DECIDED
Production write             = NONE
Recommendation eligibility   = NOT EVALUATED
CORE_READY                   = NO
```

- Recorded at: 2026-10-18
- Base: `develop@0ef8c22`（PR #3256 merge）
- Branch: `feature/niigata-h004-g0-candidate-registry`

## 2. Authority

- `docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H004（frozen; not modified）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`
  （Nationwide Source Track Boundary: Namespace, Nationwide G0 initial state, admission_provenance,
  build_batch responsibility boundary, G0 / G1 boundary）
- Precedent: NIIGATA-001-H003 G0 registration（PR #3247）

## 3. Registered candidates

Exactly five rows were added to `backend/temples/data/shrine_expansion_candidate_master.json`, in frozen
source order. `candidate_name` and `source_position` are byte-identical to the frozen Ready Set
（including `赤鏥` = U+8D64 U+93E5, checked by test）:

| candidate_id | candidate_name | source_position | frozen raw_address（not stored, see §5） |
|---|---|---|---|
| nsrc-000016 | 赤坂神社 | page002-row006 | 燕市笈ケ島2103番地 |
| nsrc-000017 | 赤坂諏訪神社 | page002-row007 | 燕市下粟生津515番地 |
| nsrc-000018 | 赤崎神社 | page002-row008 | 燕市吉田宮小路874番地 |
| nsrc-000019 | 赤鏥神社 | page002-row009 | 新潟市西蒲区赤鏥538番地 |
| nsrc-000020 | 赤澤神社 | page002-row010 | 上越市吉川区赤沢313番地 |

IDs continue the global serial after nsrc-000015（H003）. No ID is reused or renumbered.

## 4. Initial Nationwide G0 state（all five）

```text
candidate_status        = DISCOVERED
status_reason_code      = REGISTRY_ADMISSION_COMPLETE
build_batch             = null
duplicate_status        = UNREVIEWED
wave_id                 = null
identity_status         = UNREVIEWED
official_source_status  = AVAILABLE
knowledge_status        = UNREVIEWED
candidate_reason        = official_source_full_enumeration_candidate
```

admission_provenance（immutable after G0）:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
handoff_id             = NIIGATA-001-H004
source_position        = exact frozen position（§3）
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

`build_batch` is not inferred from `source_batch_id` or `handoff_id`（contract: build_batch
responsibility boundary）.

## 5. What is deliberately not done

```text
identity decision（identity_status = CONFIRMED）    NOT DONE（G1）
duplicate decision                                 NOT DONE（G1）
official_name / official_address / reading          NOT HYDRATED
latitude / longitude / location                     NOT ASSIGNED（G2）
shrine_id / Base Shrine Seed row                    NOT CREATED
goriyaku / goriyaku_tags / Knowledge                NOT CREATED
build_batch                                         null
product_surface                                     NOT ADDED（no such field）
Production                                          NOT CONNECTED
```

No duplicate or identity conclusion is drawn from name similarity. 赤坂神社 / 赤坂諏訪神社 share a
prefix and are both in 燕市, and 赤澤神社 is at 赤沢. These are G1 questions, not G0 facts. The frozen
`raw_address` stays in the Ready Set and is not copied into Candidate Master as `official_address`.

## 6. Changed files

| File | Change |
|---|---|
| `backend/temples/data/shrine_expansion_candidate_master.json` | 5 rows appended（59 → 64）. Existing rows and top-level keys unchanged. The nsrc-000015 line differs only by the added trailing comma |
| `backend/temples/tests/fixtures/shrine_expansion_handoffs.json` | test-only NIIGATA-001-H004 handoff spec appended. H001–H003 unchanged |
| `backend/temples/tests/test_shrine_expansion_candidate_master.py` | H004 G0 test + 26 mutation rejections. `_h002_extra_member` moved to the unregistered `nsrc-000021` / `page003-row001` |
| `backend/temples/tests/test_g6_nationwide_handoff_identity.py` | H004 is G0-only: absent from the identity manifest, and `load_handoff_shrine_identities` fails closed |
| this file | — |

Not changed: frozen Ready Set, identity manifest, Base / Knowledge Seed, H001 / H002 / H003 rows
（H003 stays IMPORTED ×4 + nsrc-000014 DISCOVERED）, gate and Candidate Master contracts.

## 7. Tests

`test_niigata_h004_is_registered_at_g0_only`（manifest-independent literals）:

- exact five IDs in order, exact name / source_position mapping
- exact G0 lifecycle and immutable provenance per row
- name / position equal to the frozen Ready Set §NIIGATA-001-H004（parsed from the document）
- no identity / duplicate conclusion, no BUILD_READY / IMPORTED / CORE_READY, `build_batch = null`
- no hydration, `reading` or `product_surface` field
- H001 / H002 / H003 / H004 handoff contracts pass. H003 states pinned. Wave0 accounting unchanged.

`test_niigata_h004_contract_rejects_mutations`（26 cases）:

- premature identity CONFIRMED; duplicate NEW / SAME_NAME_DIFFERENT_SHRINE / ALIAS / DUPLICATE
- BUILD_READY / IMPORTED / CORE_READY; reason beyond G0; official source / knowledge advancement
- build_batch = handoff id / source batch id; wave_id = W0; product_surface field
- official name / address, reading, coordinate, shrine_id, goriyaku hydration
- provenance position / snapshot changed; member moved to H003
- 赤坂神社 / 赤坂諏訪神社 merged; 赤澤神社 renamed to 赤沢神社

`test_g0_only_handoff_is_not_a_reviewed_identity_handoff`（G6）: H004 UNREVIEWED ×5, absent from
`shrine_expansion_nationwide_identity_manifest.json`, and the loader raises `unknown handoff`.

Validation（local disposable PostgreSQL 16, Python 3.11）:

```text
test_shrine_expansion_candidate_master.py + test_g6_nationwide_handoff_identity.py   680 passed
backend full suite（-n auto）                                                         6211 passed, 8 skipped
ruff check（changed tests）                                                          clean
ruff format（added H004 block）                                                      clean
git diff --check                                                                    clean
```

One of three full runs had a single failure in
`test_migration_0105_w0b02t02_remove_qa_artifact_id102.py`（parallel-run only）. It passes alone（41
passed）, and the other two full runs were all green. That file does not read the Candidate Master
or the handoff fixture. `test_shrine_expansion_candidate_master.py` was already not `ruff format`-clean
on develop. Only the added H004 block was formatted, to keep the diff scoped.

## 8. Next

```text
NEXT_GATE = G1（identity / duplicate review, separate PR）
```
