# NIIGATA-001-VPG001 — Base Shrine Materialization

## 1. Status

```text
targets                       = nsrc-000021 / nsrc-000022 / nsrc-000024 / nsrc-000025
excluded                      = nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE / G4 NOT_AUTHORIZED）

BASE_SHRINE_MATERIALIZATION   = IMPLEMENTED
Base Seed row count           = 129 -> 133
existing 129-row prefix       = UNCHANGED（sha256 pinned）
target exact identity count   = 1 each
duplicate (name_jp, address)  = 0
nsrc-000023 rows              = 0

Knowledge Seed                = NOT_CREATED
Source Packet freeze          = NOT_EXECUTED
FORMAL_G4                     = NOT_EXECUTED
Evidence Gate measurement     = NOT_EXECUTED
G5 / G6 / G7 / G8             = NOT_EXECUTED
Candidate Master              = UNCHANGED
Production write              = NONE
```

- Recorded at: 2026-10-19
- BASE_SHA: `4e476076c913d53b9e38dcca80e68ee5ce8ca8c8`（develop, PR #3272 merge, VPG001 G3）
- Branch: `feature/niigata-vpg001-base-shrine-materialization`

Purpose: create only the Base Shrine rows the later G4 Knowledge importer needs to resolve the four exact
shrine identities（`import_shrine_knowledge` rejects a seed whose `shrine_ref` does not resolve）. This is
not a G4 Knowledge change.

## 2. Authority

- `docs/audit/niigata-vpg001-g1-identity-duplicate.md`（G1 PASS / CLOSED; canonical identity）
- `docs/audit/niigata-vpg001-g2-position-review.md`（G2 CLOSED / PASS, FROZEN 2026-10-19）and
  `docs/audit/shrine-position/niigata-vpg001-nsrc-0000{21,22,24,25}-position-review.md`
- `docs/audit/niigata-vpg001-g3-source-knowledge-fit.md`（PRODUCT_SURFACE = RECOMMENDATION ×4,
  G4 AUTHORIZED_TO_START ×4; nsrc-000023 NOT_AUTHORIZED）
- Precedents: `docs/audit/niigata-h002-nsrc-000006-base-shrine-materialization.md`,
  `docs/audit/niigata-h003-catalog-base-shrine-materialization.md`（latest append-safe convention）

| candidate_id | canonical name（G1） | canonical address（G1） | adopted coordinate（frozen G2） |
|---|---|---|---|
| nsrc-000021 | 荒川神社 | 新潟県胎内市桃崎浜187番地 | 38.1409456, 139.4073314 |
| nsrc-000022 | 五十嵐神社 | 新潟県三条市大字飯田2283番地 | 37.573979, 139.048758 |
| nsrc-000024 | 秋葉神社 | 新潟県新潟市秋葉区秋葉3丁目8番19号 | 37.7863255, 139.1351949 |
| nsrc-000025 | 天津神社 | 新潟県糸魚川市一の宮1丁目3番34号 | 37.0397729, 137.8644153 |

Names and addresses equal the reviewed identity manifest. Coordinates equal the Position Resolution
Records, read back by `scripts/audit_shrine_positions_v2.load_resolution_records`. They were not
re-researched, averaged, normalized or replaced.

## 3. Pre-check（develop@4e476076）

```text
Base Seed rows                                   129
exact (name_jp, address) for each target          0
same name_jp, any address, for each target        0
same address, any name_jp, for each target        0
locality fragments（桃崎浜 / 飯田2283 / 秋葉区秋葉 / 一の宮）  1 hit: 阿蘇神社（熊本県, matches 一の宮 only; unrelated）
```

No target resolves through another exact canonical row.

## 4. Materialized Base rows

Appended to `backend/temples/data/shrines_seed_clean.json` at index 129–132, in candidate order. Row shape
follows the latest precedent（H003, nsrc-000009）:

```json
{"name_jp": "荒川神社", "address": "新潟県胎内市桃崎浜187番地", "latitude": 38.1409456, "longitude": 139.4073314,
 "goriyaku": "", "kyusei": null, "astro_elements": [], "location": {"lat": 38.1409456, "lng": 139.4073314}}
{"name_jp": "五十嵐神社", "address": "新潟県三条市大字飯田2283番地", "latitude": 37.573979, "longitude": 139.048758,
 "goriyaku": "", "kyusei": null, "astro_elements": [], "location": {"lat": 37.573979, "lng": 139.048758}}
{"name_jp": "秋葉神社", "address": "新潟県新潟市秋葉区秋葉3丁目8番19号", "latitude": 37.7863255, "longitude": 139.1351949,
 "goriyaku": "", "kyusei": null, "astro_elements": [], "location": {"lat": 37.7863255, "lng": 139.1351949}}
{"name_jp": "天津神社", "address": "新潟県糸魚川市一の宮1丁目3番34号", "latitude": 37.0397729, "longitude": 137.8644153,
 "goriyaku": "", "kyusei": null, "astro_elements": [], "location": {"lat": 37.0397729, "lng": 137.8644153}}
```

The file diff is append-only（52 insertions, 0 deletions）. The existing 129 rows are byte-identical.

Neutral-value boundary:

```text
goriyaku        = ""
kyusei          = null
astro_elements  = []
location        = mirrors latitude / longitude
not added       = goriyaku_tags, visit_style_tags, history_theme, deities, histories, sources,
                  recommendation mappings, ranking / score fields
```

nsrc-000025: the shared 天津神社・奴奈川神社 precinct does not change the Base identity. The row is 天津神社
only. No 奴奈川神社 row is created.

## 5. Results

```text
existing-row isolation        rows[:129] sha256 = 5932f7a8afcf608c8591c826bef5f2b0310861be496147c869d221575655685d（unchanged）
duplicate identity            0 duplicate (name_jp, address) in the 133 rows
exact resolver                resolve_shrine(name_jp, address) = OK ×4, each to its own row
same-name isolation           荒川神社 ×3 other frozen addresses, 秋葉神社 古町通, 天津神社 上越市東京田 -> NOT_FOUND
shared-precinct isolation     奴奈川神社 / 糸魚川市一の宮1丁目3番34号 -> NOT_FOUND
nsrc-000023                   熱串彦神社 -> NOT_FOUND; no Base row
import rehearsal（test DB）    created=133, then dry-run / second import created=0 updated=0 skipped=133
imported targets              0 ShrineDeity, 0 ShrineHistory, goriyaku "", history_theme "", no goriyaku_tags
inferred fields               NONE
```

## 6. Changed files

| File | Change |
|---|---|
| `backend/temples/data/shrines_seed_clean.json` | 4 rows appended（129 → 133） |
| `backend/temples/tests/test_niigata_vpg001_base_shrine_seed.py` | new focused regression（27 tests） |
| `backend/temples/tests/test_shrine_expansion_candidate_master.py` | VPG001 G0 "no Base Seed" test narrowed to "only the four authorized neutral rows; nsrc-000023 none; Knowledge Seed none" |
| `backend/temples/tests/test_niigata_h003_c6_target_only_import.py` | stale global count `== 129` made append-safe（`>= 129`, others = total − 4）; the H003 subset assertions are unchanged |
| this file | — |

The two existing test changes were required by the append. Each one pinned a state this PR authorizes:
the VPG001 G0 "no Base Seed" rule, and the H003 global row count. Neither weakens what it protects. The
H003 extractor still returns exactly its 4 rows, and the VPG001 rows must equal the frozen values.

## 7. Not changed

```text
nsrc-000023                         UNCHANGED（no row）
Knowledge Seeds                     NOT_CREATED
G3 audit / Candidate Master         UNCHANGED
G1 identity / G2 coordinates        UNCHANGED
Production DB                       NO ACCESS, NO WRITE
Recommendation / Ranking / Concierge / Compass / API / frontend   UNCHANGED
models / migrations / serializers / Evidence Gate / goriyaku taxonomy   UNCHANGED
```

## 8. Validation

```text
new focused test（test_niigata_vpg001_base_shrine_seed.py）     27 passed
backend full suite（-n auto）                                  6275 passed, 8 skipped
scripts/tests                                                 685 passed
ruff check / format（changed tests）                           clean
git diff --check                                             clean
```

## 9. Next

```text
NEXT = G4 Source Packet freeze / Knowledge materialization for nsrc-000021 / 000022 / 000024 / 000025
       （separate PR; requires verifiable Source wording and real verified_at timestamps）
STOP = TRUE
```
