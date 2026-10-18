# NIIGATA-001-VPG001 — Value-Selected Processing Group Freeze

## 1. Status

```text
processing_group_id   = NIIGATA-001-VPG001
group_type            = VALUE_SELECTED_PROCESSING_GROUP
member_count          = 5

SELECTION_POLICY      = VALUE_FIRST
POPULARITY_REQUIRED   = NO
MEMBERSHIP_FROZEN     = YES
G0                    = NOT_EXECUTED
```

- Recorded at: 2026-10-18
- Base: `develop@3e48fe1`（PR #3259 merge, priority policy + NIIGATA-001 screening）
- Branch: `docs/niigata-vpg001-freeze`

## 2. Authority

- `docs/audit/niigata-batch001-ready-set-freeze.md`（frozen Ready Set, source rows and handoff membership）
- `docs/knowledge/shrine-expansion-priority-policy.md`（value-first selection; popularity not required）
- `docs/audit/niigata-001-expansion-priority-screening.md`（PRIORITY_A screening, PROPOSED_NEXT_HANDOFF）
- Mother Ship decision: member list of this freeze

## 3. Frozen membership

`source_position`, `raw_name` and `raw_address` are copied byte-for-byte from the frozen Ready Set. The
order is the processing-group order given by Mother Ship.

| # | source_position | raw_name | raw_address | source_handoff | ready_basis | screening class at freeze |
|---|---|---|---|---|---|---|
| 1 | page008-row003 | 荒川神社 | 胎内市桃崎浜187番地 | NIIGATA-001-H015 | RUNNER_READY | PRIORITY_A |
| 2 | page010-row004 | 五十嵐神社 | 三条市大字飯田2283番地 | NIIGATA-001-H019 | RUNNER_READY | PRIORITY_A |
| 3 | page006-row010 | 熱串彦神社 | 佐渡市長江854番地 | NIIGATA-001-H012 | RUNNER_READY | PRIORITY_A |
| 4 | page003-row007 | 秋葉神社 | 新潟市秋葉区秋葉3丁目8番19号 | NIIGATA-001-H006 | RUNNER_READY | PRIORITY_A |
| 5 | page007-row006 | 天津神社 | 糸魚川市一の宮1丁目3番34号 | NIIGATA-001-H014 | RUNNER_READY | PRIORITY_A |

Membership fingerprint（sha256 of the lines `source_position|raw_name|raw_address|source_handoff` in the
order above, UTF-8, `\n`-terminated）:

```text
4523e6688f5d5ba7fb4d883607b4ebb15ad90345989efd81e4b63b34aff2bd77
```

### 3.1 Screening class at freeze

All five members are **PRIORITY_A** in the screening audit.

天津神社（page007-row006）was moved PRIORITY_B → PRIORITY_A in the screening audit（§6.1）before this
freeze, after primary-source deity verification on 2026-10-18.

```text
primary_source     = 天津神社・奴奈川神社 公式サイト「御由緒・御祭神」
primary_source_url = https://amatsujinja.com/story/
天津神社 御祭神     = 天津彦々火瓊々杵尊 / 天児屋根命 / 天太玉命
```

The same official source separately records 奴奈川神社御祭神 as 奴奈川媛命 / 八千矛命, so G1 / G3
must preserve deity Fact ownership between the two honden.

For G1 / G3, carried forward: the precinct has two honden（天津神社・奴奈川神社）. This stays a
`MODEL_RISK = POSSIBLE` entity-granularity question. The freeze does not decide it.

Google Maps screenshots supplied by Mother Ship for 天津神社 are only future G2 preflight visual
evidence. No coordinate is adopted.

## 4. Source handoff membership（unchanged）

VPG001 selects one row from each of five frozen handoffs. The frozen handoffs are **not** modified. They
keep all five members, in Source order, and remain the provenance unit.

| source_handoff | frozen members（unchanged） | selected into VPG001 |
|---|---|---|
| NIIGATA-001-H006 | page003-row006, page003-row007, page003-row008, page003-row009, page003-row010 | page003-row007 |
| NIIGATA-001-H012 | page006-row006, page006-row007, page006-row008, page006-row009, page006-row010 | page006-row010 |
| NIIGATA-001-H014 | page007-row006, page007-row007, page007-row008, page007-row009, page007-row010 | page007-row006 |
| NIIGATA-001-H015 | page008-row001, page008-row002, page008-row003, page008-row004, page008-row005 | page008-row003 |
| NIIGATA-001-H019 | page010-row001, page010-row002, page010-row003, page010-row004, page010-row005 | page010-row004 |

The other 20 rows of these five handoffs are not selected. They keep their screening class and are not
affected by this freeze.

## 5. What VPG001 is and is not

```text
VPG001 = audit-level processing selection（which candidates to process next）

VPG001 != Candidate Master field          no field, enum or lifecycle state
VPG001 != Operating Group                 an Operating Group = 2 whole existing frozen handoffs（D-1）
VPG001 != Data Build Batch                build_batch stays the downstream Data Build provenance
VPG001 != frozen Source handoff           source handoffs stay the provenance unit（§4）
VPG001 != Recommendation ranking input    no runtime score, ranking or eligibility effect
```

## 6. Consequences for the later G0 PR（noted, not decided here）

- When the members are admitted at G0, `admission_provenance.handoff_id` would be each member's
  **source handoff**（H015 / H019 / H012 / H006 / H014）, because VPG001 is not a Candidate Master field.
- Each source handoff would then be **partially** registered（1 of 5 members）. The current handoff
  contract / fixture tests were written for whole-handoff registration（H001–H004）. The G0 PR must
  decide how a partially registered handoff is represented. This freeze does not change that contract.
- `candidate_id` values are assigned at G0, not here.

## 7. Not done in this PR

```text
candidate_id assignment                 NOT DONE
G0 / G1 / G2                            NOT EXECUTED
Base Seed / Knowledge                   NOT CREATED
Product Surface                         NOT DECIDED
Candidate Master / handoff fixture      UNCHANGED
frozen Ready Set / handoff membership   UNCHANGED
Recommendation ranking                  UNCHANGED
Production                              NO ACCESS, NO WRITE
H004                                    UNCHANGED（PR #3258 still evidence only）
```

## 8. Validation

Independent re-parse of this document against the frozen Ready Set:

```text
5 members: source_position / raw_name / raw_address / source_handoff == Ready Set   exact（byte-for-byte）
membership fingerprint recomputed                                                 matches §3
5 distinct source handoffs, each still exactly 5 frozen members                     yes
frozen Ready Set document vs origin/develop                                         unchanged
Candidate Master / handoff fixture / identity manifest vs origin/develop            unchanged
Base Seed / Knowledge Seeds vs origin/develop                                       unchanged
git diff --check                                                                   clean
```
