# NIIGATA-001-H002 — nsrc-000007 Base Shrine Materialization

## 1. Status

```text
candidate_id                  = nsrc-000007
name_jp                       = 赤城社
address                       = 新潟県十日町市四日町2534番地

resolves                      = BASE_SHRINE_NOT_MATERIALIZED（G4 preflight blocker）
BASE_SHRINE_MATERIALIZATION   = PASS

Base Seed row count           = 122 -> 123
target exact identity count   = 1
existing 122 rows             = UNCHANGED
duplicate identity            = 0
required fields missing       = 0
Base Seed validation          = PASS
resolve_shrine exact target   = OK

Knowledge Seed                = NOT CREATED
FORMAL_G4                     = HOLD（unchanged; re-entry not executed）
G5 / G6 / G7 / G8             = NOT EXECUTED
Production write              = NONE
```

- Recorded at: 2026-10-13
- Base: `develop@7f88f5e96ba158831d28a661d46f7a25c01c7b22`（includes #3188 exact-address `resolve_shrine()`）
- Branch: `feature/nsrc-000007-base-shrine`
- Blocker source: `docs/audit/niigata-h002-nsrc-000007-g4-evidence-preflight.md`（`FORMAL_G4 = HOLD / BASE_SHRINE_NOT_MATERIALIZED`）

## 2. Authority

Position authority（only source of the values below）:
`docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`

```text
official_name    = 赤城社
official_address = 新潟県十日町市四日町2534番地
latitude         = 37.14755658
longitude        = 138.76887612
```

The same record also lists other coordinates as supporting / observation values（e.g. a manual-QA
observation `37.147573, 138.768900`）. They are not used. No coordinate was derived, rounded, or replaced.

## 3. Preconditions（develop@7f88f5e9）

```text
#3188 present                    = YES
  resolve_shrine(): address supplied + 0 exact-address rows -> NOT_FOUND
Base Seed rows                   = 122
赤城社 rows（any address）        = 0
exact target rows                = 0
Base Seed sha256（file）          = 60ed829f9b21ffb91609da41a687f624f1ba101edb9f0be8c40fc99570d3a0bb
```

## 4. Materialized row

Appended as the last element of `backend/temples/data/shrines_seed_clean.json`（rows[122]）:

```json
{
  "name_jp": "赤城社",
  "address": "新潟県十日町市四日町2534番地",
  "latitude": 37.14755658,
  "longitude": 138.76887612,
  "goriyaku": "",
  "kyusei": null,
  "astro_elements": [],
  "location": {
    "lat": 37.14755658,
    "lng": 138.76887612
  }
}
```

Content boundary:

- The shape is the existing minimal Base Shrine shape. It is already used by 6 rows, including the
  nsrc-000002（青澤神社）and nsrc-000004（青海神社）materializations.
- `goriyaku = ""`, `kyusei = null`, `astro_elements = []` are the repository neutral values.
- `location` mirrors `latitude` / `longitude`.
- Not added: `goriyaku_tags`, `visit_style_tags`, `history_theme`, astro / kyusei values,
  Recommendation fields, Deity / History / Source / Knowledge Facts.

The file was rewritten with the repository's own serialization（`json.dumps(indent=2, ensure_ascii=False)`
+ trailing newline）. A round-trip of the 122-row file was byte-identical before the append, so the
diff is the 13 added lines only.

## 5. 122 -> 123 evidence

Deterministic identity / fingerprint comparison（same method as the nsrc-000002 / nsrc-000004 tests:
rows sorted by `(name_jp, address)`, `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`, sha256）:

```text
before rows                        = 122
after rows                         = 123
added                              = 1   [("赤城社", "新潟県十日町市四日町2534番地")]
removed                            = 0
modified existing rows             = 0
after[:122] == before（in order）   = True

before fingerprint（122 rows）      = 02983b6dcc54591c7a9a88923a9c5998cf942bbdf25e8589b623463a82c26efc
after[:122] fingerprint            = 02983b6dcc54591c7a9a88923a9c5998cf942bbdf25e8589b623463a82c26efc
after fingerprint（123 rows）       = 85782dcb735fd695a8e8d79fc0ab21918347666c6127cee1f450210a6531e0dd

duplicate (name_jp, address)       = 0
rows missing name_jp / address / latitude / longitude / location = 0
赤城社 rows in Base Seed            = 1（四日町2534番地 only）
```

## 6. Exact target identity evidence（isolated pytest DB）

After `import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags`:

```text
importer summary                       contains total_seed=123
Shrine(name_jp=赤城社, address=四日町2534番地)  = 1 row, latitude/longitude = 37.14755658 / 138.76887612
resolve_shrine("赤城社", "新潟県十日町市四日町2534番地") = OK, pk == that row
```

Exact-address safety（#3188 behavior applied to this candidate）:

```text
resolve_shrine("赤城社", "新潟県十日町市上組2059番地子") = NOT_FOUND（not nsrc-000007）
resolve_shrine("赤城社", "新潟県十日町市伊達乙48番地")   = NOT_FOUND（not nsrc-000007）
resolve_shrine("赤城社", "新潟県南魚沼市芹田79番地")     = NOT_FOUND（not nsrc-000007）
```

With the other three H002 `赤城社` rows also present（test-only rows）, every address resolves to its own
row and nsrc-000007 still resolves `OK` to the exact target. Same-name rows do not create ambiguity.

Name-only matching is not used as evidence anywhere in this materialization.

## 7. Tests

New: `backend/temples/tests/test_nsrc_000007_base_shrine_seed.py`（20 tests, same append-safe cohort
pattern as `test_nsrc_000002_base_shrine_seed.py`）:

- identity occurs exactly once; row equals the frozen values; no inferred fields;
- cohort position rows[122:123]; existing 122-row prefix fingerprint unchanged;
- accounting allows later appends and rejects remove / address change / coordinate change /
  prefix removal / prefix mutation / later duplicate;
- no duplicate identity; only the nsrc-000007 `赤城社` is in the Base Seed;
- isolated DB: Base Seed import gives `total_seed=123`, `resolve_shrine` exact target `OK`;
  other H002 `赤城社` addresses → `NOT_FOUND`; same-name rows do not make nsrc-000007 ambiguous.

Updated（state change caused by this materialization）:
`backend/temples/tests/test_g6_nationwide_handoff_identity.py::test_handoff_text_output_and_h002_unresolved_state`.

- Before: H002 = 5 / 5 `UNRESOLVED`.
- After: nsrc-000007 = `INELIGIBLE`. The Shrine resolves by exact identity but has no Knowledge yet, as
  required by "Shrine DB presence != Recommendation eligibility". The other 4 stay `UNRESOLVED`.
- The eligibility rule, verifier, and H001 expectations are unchanged.

Results:

```text
test_nsrc_000007_base_shrine_seed.py           20 passed
backend full suite（-n auto）                   5385 passed, 12 skipped
scripts/tests                                  685 passed
scripts/migration_safety/tests                 320 passed
makemigrations --check                         No changes detected
ruff check / format --check（changed tests）    clean
git diff --check                               clean
```

## 8. Impact boundary

```text
Base Seed                              +1 row（nsrc-000007）
Knowledge Seed（nsrc_000007_seed.json） NOT CREATED
Candidate Master                       NONE
other H002 candidates                  NONE
resolve_shrine() / Knowledge importer  NONE
Evidence Gate / Recommendation / Ranking / Score  NONE
Concierge / Compass                    NONE
goriyaku / goriyaku_tags / mappings    NONE
models / migrations                    NONE
Production DB                          NONE（not connected）
```

Runtime effect after a future Base Seed import: one additional `Shrine` row. With no Knowledge, the
existing eligibility contract keeps it `INELIGIBLE`.

## 9. Rollback

Revert the commit. This removes the appended row, the new test, the updated G6 expectation, and this
audit. No migration or Production data is involved.

## 10. Next work item

```text
nsrc-000007 Knowledge Seed materialization + G4 re-entry
```

The frozen payload and remaining measurements are in
`docs/audit/niigata-h002-nsrc-000007-g4-evidence-preflight.md` §9 / §12.
That includes the `verified_at` time-component decision in §5 of the same document.

## 11. STOP

Do not create the Knowledge Seed, re-enter G4, execute G5, or write Production in this PR.
