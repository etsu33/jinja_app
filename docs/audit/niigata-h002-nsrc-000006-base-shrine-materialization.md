# NIIGATA-001-H002 — nsrc-000006 Base Shrine Materialization

## 1. Status

```text
candidate_id                  = nsrc-000006
name_jp                       = 赤井神社
address                       = 新潟県佐渡市加茂歌代2662番地

G1                            = PASS / NEW
G2                            = CLOSED / PASS
G3                            = PASS / NORMAL_MODEL_FIT
G4 Source Packet Freeze       = PASS / FROZEN / G4_EVIDENCE_READY

BASE_SHRINE_MATERIALIZATION   = PASS

Base Seed row count           = 123 -> 124
target exact identity count   = 1
existing 123 rows             = UNCHANGED_BY_SEMANTIC_DIFF
duplicate identity            = 0
required fields missing       = 0

Knowledge Seed                = NOT_CREATED
FORMAL_G4                     = NOT_EXECUTED
G5 / G6 / G7 / G8             = NOT_EXECUTED
Production write              = NONE
```

- Recorded at: 2026-10-14
- Base: `develop@5371a8f929eb832117fb916892f6e858de0ee491`（PR #3205 merged）
- Branch: `feature/nsrc-000006-base-shrine`

## 2. Authority

Identity:

`docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md`

Position authority:

`docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`

```text
official_name    = 赤井神社
official_address = 新潟県佐渡市加茂歌代2662番地
latitude         = 38.08593800
longitude        = 138.41831200
```

G4 Source Packet:

`docs/audit/niigata-h002-nsrc-000006-g4-source-packet-freeze.md`

No coordinate is re-derived in this PR.

## 3. Preconditions

Before this materialization:

```text
Base Seed rows            = 123
target exact rows         = 0
target name rows          = 0
Knowledge Seed            = absent
Production write          = none
```

The current Base Seed contains nsrc-000007 but not nsrc-000006.

## 4. Materialized row

Appended as the last element of
`backend/temples/data/shrines_seed_clean.json`:

```json
{
  "name_jp": "赤井神社",
  "address": "新潟県佐渡市加茂歌代2662番地",
  "latitude": 38.085938,
  "longitude": 138.418312,
  "goriyaku": "",
  "kyusei": null,
  "astro_elements": [],
  "location": {
    "lat": 38.085938,
    "lng": 138.418312
  }
}
```

The JSON numeric representation omits insignificant trailing zeros.
The adopted G2 values remain semantically:

```text
latitude  = 38.08593800
longitude = 138.41831200
```

Neutral-value boundary:

```text
goriyaku       = ""
kyusei         = null
astro_elements = []
```

Not added:

- goriyaku_tags
- visit_style_tags
- history_theme
- Deity
- History
- Source
- Recommendation mapping
- Ranking / score fields

## 5. Existing-row isolation

The target is appended after the existing 123-row historical prefix.

```text
historical prefix rows = rows[0:123]
target cohort           = rows[123:124]
```

The regression test freezes the existing 123-row prefix fingerprint recorded by the prior
nsrc-000007 materialization:

```text
85782dcb735fd695a8e8d79fc0ab21918347666c6127cee1f450210a6531e0dd
```

It rejects:

- target removal;
- address mutation;
- coordinate mutation;
- replacement;
- movement;
- earlier-prefix removal / mutation;
- duplicate target append.

Later append-only rows remain allowed.

## 6. Identity / resolution boundary

Target resolution must be exact:

```text
resolve_shrine(
  "赤井神社",
  "新潟県佐渡市加茂歌代2662番地"
)
= OK
```

Research-observed noncanonical addresses are explicitly rejected:

```text
新潟県佐渡市加茂歌代2622番地
新潟県佐渡市加茂歌代1164-7
```

An additional test-only same-name row at another address must not make the target ambiguous.

## 7. H002 verifier state transition

The read-only H002 Recommendation Eligibility verifier imports the Base Seed but only the proven H001 Knowledge seeds.

Therefore, after this Base materialization:

```text
nsrc-000006 = INELIGIBLE
nsrc-000007 = INELIGIBLE
nsrc-000008 = UNRESOLVED
nsrc-000009 = UNRESOLVED
nsrc-000010 = UNRESOLVED
```

This is expected.

```text
Shrine DB presence != Recommendation eligibility
```

No eligibility contract is changed.

## 8. Test scope

New:

`backend/temples/tests/test_nsrc_000006_base_shrine_seed.py`

Covers:

- exact frozen row;
- append-safe cohort accounting;
- historical prefix preservation;
- duplicate prevention;
- no inferred fields;
- exact-address resolution;
- noncanonical address fail-closed behavior;
- same-name other-address isolation.

Updated:

`backend/temples/tests/test_g6_nationwide_handoff_identity.py`

Only the expected H002 read-only current-state output changes from one Base-resolved candidate to two.

First CI run exposed one stale append-safety expectation in existing nsrc-000007 tests:

```text
test_nsrc_000007_base_shrine_seed.py
  expected total_seed=123
  actual   total_seed=124
```

The nsrc-000007 cohort contract already allows later appends; only the importer-summary assertion was stale.
The same hard-coded count in `test_nsrc_000007_knowledge_seed.py` was corrected at the same time.

Both now derive the current Base Seed count dynamically. No runtime or historical cohort boundary changed.

Second code-head validation:

```text
dependency-review = PASS
CodeQL             = PASS
backend-pr         = PASS
Vercel             = PASS

schema drift check = PASS
unit job           = PASS
integration job    = SKIPPED by workflow contract

CI_RESULT          = PASS
```

## 9. Impact boundary

```text
Base Seed                              +1 row（nsrc-000006）
Knowledge Seed                         NONE
Candidate Master                       NONE
other H002 candidates                  NONE

resolve_shrine() implementation        NONE
Knowledge importer                     NONE
Evidence Gate                          NONE
Recommendation / Ranking / Score       NONE
Concierge / Compass                    NONE
goriyaku / goriyaku_tags / mappings    NONE
models / migrations                    NONE
Production DB                          NONE
```

## 10. Rollback

Revert this PR.

No migration or Production data is involved.

## 11. Next work item

After merge:

```text
nsrc-000006 Knowledge Seed materialization
+ isolated G4 Evidence Gate measurement
```

## 12. STOP

```text
FORMAL_G4 = NOT_EXECUTED
G5        = NOT_EXECUTED
PRODUCTION_WRITE = NONE
STOP = TRUE
```

Do not create the Knowledge Seed or execute G5 in this PR.
