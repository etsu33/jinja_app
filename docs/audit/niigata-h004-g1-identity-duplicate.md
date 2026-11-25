# NIIGATA-001-H004 G1 Identity / Duplicate Gate（evidence review）

> Status: **G1 = PENDING_MOTHER_SHIP_DECISION**
>
> Recorded at: 2026-10-18
>
> Base: `develop@84a369b`（PR #3257 merge, H004 G0 registration）
>
> Candidate Master write: 0
> Identity manifest write: 0
> Production write: 0
> G2 execution: 0
> Base Seed / Knowledge / Recommendation change: 0

```text
G0 = PASS
G1 = PENDING_MOTHER_SHIP_DECISION
G2 = NOT STARTED
```

This document is evidence only. It does not change `identity_status` or `duplicate_status`. Every
classification below is an **EVIDENCE_RESULT candidate**. The **MOTHER_SHIP_DECISION** section is
empty until Mother Ship confirms all five.

## 1. Scope and authority

| candidate_id | source_position | frozen_name | frozen_address |
|---|---|---|---|
| nsrc-000016 | page002-row006 | 赤坂神社 | 燕市笈ケ島2103番地 |
| nsrc-000017 | page002-row007 | 赤坂諏訪神社 | 燕市下粟生津515番地 |
| nsrc-000018 | page002-row008 | 赤崎神社 | 燕市吉田宮小路874番地 |
| nsrc-000019 | page002-row009 | 赤鏥神社 | 新潟市西蒲区赤鏥538番地 |
| nsrc-000020 | page002-row010 | 赤澤神社 | 上越市吉川区赤沢313番地 |

Authority:

- `docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H004（frozen accepted Source rows, `ready_basis = RUNNER_READY`）
- `docs/audit/niigata-h004-g0-candidate-registry.md`
- `docs/knowledge/shrine-expansion-gate-contract.md` §4（PASS: canonical identity explainable, duplicate /
  alias / same-name-different-shrine classified, Production collision explainable）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（Sub-status / Duplicate Rule）
- Precedent: `docs/audit/niigata-h003-g1-identity-duplicate.md`

## 2. Canonical identity

### 2.1 Proposed canonical identities（EVIDENCE_RESULT）

The accepted Source is the frozen NIIGATA-001 snapshot（`source_snapshot_sha256 =
f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380`, `niigata-jinjacho.jp`）. As in H003,
the canonical address is the frozen Source address with Candidate Master `prefecture = 新潟県`
prefixed. No other change is made.

| candidate_id | proposed_canonical_name | proposed_canonical_address |
|---|---|---|
| nsrc-000016 | 赤坂神社 | 新潟県燕市笈ケ島2103番地 |
| nsrc-000017 | 赤坂諏訪神社 | 新潟県燕市下粟生津515番地 |
| nsrc-000018 | 赤崎神社 | 新潟県燕市吉田宮小路874番地 |
| nsrc-000019 | 赤鏥神社 | 新潟県新潟市西蒲区赤鏥538番地 |
| nsrc-000020 | 赤澤神社 | 新潟県上越市吉川区赤沢313番地 |

No `reading` is recorded. G1 does not require it, and no reading is source-backed in this review.

### 2.2 Exact-kanji integrity

Codepoints are preserved exactly as frozen. Equality with the frozen Ready Set and the G0 Candidate
Master rows is checked by the existing G0 test.

```text
nsrc-000019  鏥 = U+93E5（name and address locality）  ≠ 錆 U+9306
nsrc-000020  澤 = U+6FA4（name）, 沢 = U+6CA2（address locality）
nsrc-000016  ケ = U+30B1（笈ケ島）  ≠ ヶ U+30F6
```

- **赤鏥神社:** the Source uses `鏥` consistently in both the shrine name and the locality（`西蒲区赤鏥`）.
  No accepted Source in this review supports `赤錆`. The name is **not** normalized.
- **赤澤神社 / 赤沢:** the Source writes the shrine name with `澤` and the address locality with `沢`.
  This is a name-vs-locality spelling difference inside one Source row, not a conflict between two
  Sources. No accepted Source supports `赤沢神社` as the shrine name. Neither is normalized.
- **笈ケ島:** kept as `ケ` exactly as frozen.

Variants（`赤錆`, `赤沢神社`, `ヶ`）are used **only as search probes** in the Production query（§4.2）,
never as identity.

### 2.3 Live Source cross-check

```text
LIVE_SOURCE_CROSS_CHECK = NOT_PERFORMED
```

This environment's network policy denied `niigata-jinjacho.jp`（proxy 403）. Identity therefore rests
on the frozen snapshot only, as in H003 G1. A live re-read can confirm the rare kanji, but it does not
replace the frozen authority.

## 3. Same-name / similar-name risk

Each check is reported separately. Name similarity alone produces no duplicate or alias conclusion.

| check | result |
|---|---|
| exact same name within H004 | none（five distinct names） |
| exact same name elsewhere in the repository | none（Base Seed 129 rows, Candidate Master 64 rows, identity manifest H001–H003, all `backend/temples/data/**/*.json`） |
| similar name in the repository | 赤坂氷川神社（東京都港区赤坂）, 諏訪大社（上社本宮）（長野県）, 札幌諏訪神社（北海道）, wave0 諏訪大社 下社秋宮. All in another prefecture, so no identity relation |
| same municipality within H004 | nsrc-000016 / 000017 / 000018 are all 燕市 |
| same or overlapping address | none. Localities 笈ケ島 / 下粟生津 / 吉田宮小路 / 西蒲区赤鏥 / 吉川区赤沢 are all different |
| obvious alias evidence | none found |
| distinct-shrine evidence | different Source rows, different names and different addresses |

### 3.1 赤坂神社（nsrc-000016）vs 赤坂諏訪神社（nsrc-000017）

```text
nsrc-000016  赤坂神社      燕市笈ケ島2103番地    page002-row006
nsrc-000017  赤坂諏訪神社  燕市下粟生津515番地   page002-row007
```

Both are in 燕市 and share the `赤坂` prefix. The official Source lists them as **separate rows**, with
different names and different localities（笈ケ島 vs 下粟生津）and lot numbers. No Source says one is an
alias, a former name or an enshrined sub-shrine of the other. **No duplicate or alias relation is
proposed.** Because the names differ, `SAME_NAME_DIFFERENT_SHRINE` does not apply either.

### 3.2 赤澤神社（nsrc-000020）vs locality 赤沢

See §2.2. The locality name does not identify a different shrine. No other row named 赤沢神社 or
赤澤神社 exists in the repository. Production is checked by §4.2.

### 3.3 赤鏥神社（nsrc-000019）

See §2.2. The rare kanji is consistent within the Source row, and `赤錆` is probed in Production only
as a variant.

## 4. Production collision

### 4.1 Historical evidence（not current）

`docs/audit/niigata-batch001-real-data-run1-run2.md`: on 2026-10-08 the runner-equivalent lookup
（`find_duplicate_candidates`: exact name, name containing the base key, address containing the
normalized Source address）ran twice against Production `temples_shrine`（120 rows, fingerprint
`cfac51b6cddc54d62c951545f5fd0f12`）. It returned **0 candidates** for all five H004 rows, so they were
`READY_CANDIDATE` / `RUNNER_READY`. None of the five was among the 19 REVIEW_REQUIRED rows.

Limits of this evidence:

```text
temples_shrine count then          = 120（now 129 per H003 C6 post-Base verification）
temples_shrinecandidate            = NOT CHECKED by the runner
locality-only / spelling variants  = NOT CHECKED by the runner
```

### 4.2 Current Production inspection（required, read-only, Mother Ship）

```text
PRODUCTION_COLLISION_CURRENT = NOT MEASURED（no Production access in this environment）
```

Mother Ship runs the following through `scripts/migration_safety/readonly_query.sh`. It is SELECT /
WITH only（`guard.py check-readonly-sql` = `SAFE: ok`）. It covers `temples_shrine` **and**
`temples_shrinecandidate`, uses name plus municipality + locality pairs only, and never matches a bare
number.

```sql
-- NIIGATA-001-H004 G1 Production collision inspection（read-only）
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- No credential, hostname or database identifier is recorded.
-- Locality tokens include spelling variants（ケ/ヶ, 鏥/錆, 澤/沢）so a variant spelling in
-- Production is reported, never assumed away. No bare numeric LIKE is used.

-- 1. totals
SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrinecandidate) AS shrinecandidate_total;

-- 2. per candidate, per table: exact / same-name other address / same-address other name
WITH
targets (candidate_id, name_jp, frozen_address, canonical_address) AS (
  VALUES
    ('nsrc-000016', '赤坂神社', '燕市笈ケ島2103番地', '新潟県燕市笈ケ島2103番地'),
    ('nsrc-000017', '赤坂諏訪神社', '燕市下粟生津515番地', '新潟県燕市下粟生津515番地'),
    ('nsrc-000018', '赤崎神社', '燕市吉田宮小路874番地', '新潟県燕市吉田宮小路874番地'),
    ('nsrc-000019', '赤鏥神社', '新潟市西蒲区赤鏥538番地', '新潟県新潟市西蒲区赤鏥538番地'),
    ('nsrc-000020', '赤澤神社', '上越市吉川区赤沢313番地', '新潟県上越市吉川区赤沢313番地')
),
rows_all (source_table, id, name_jp, address) AS (
  SELECT 'temples_shrine', id, name_jp, COALESCE(address, '') FROM temples_shrine
  UNION ALL
  SELECT 'temples_shrinecandidate', id, name_jp, COALESCE(address, '') FROM temples_shrinecandidate
)
SELECT
  t.candidate_id,
  tbl.source_table,
  (SELECT COUNT(*) FROM rows_all r WHERE r.source_table = tbl.source_table
     AND r.name_jp = t.name_jp
     AND r.address IN (t.frozen_address, t.canonical_address)) AS exact_match_count,
  (SELECT COUNT(*) FROM rows_all r WHERE r.source_table = tbl.source_table
     AND r.name_jp = t.name_jp
     AND r.address NOT IN (t.frozen_address, t.canonical_address)) AS same_name_other_address_count,
  (SELECT COUNT(*) FROM rows_all r WHERE r.source_table = tbl.source_table
     AND r.address IN (t.frozen_address, t.canonical_address)
     AND r.name_jp <> t.name_jp) AS same_address_other_name_count
FROM targets t
CROSS JOIN (VALUES ('temples_shrine'), ('temples_shrinecandidate')) AS tbl (source_table)
ORDER BY t.candidate_id, tbl.source_table;

-- 3. diagnostics: every row matching a candidate name or a name variant, or a
--    municipality + locality token pair. Each row needs an explanation.
WITH
probes (candidate_id, probe_kind, name_jp, municipality, locality) AS (
  VALUES
    ('nsrc-000016', 'name', '赤坂神社', NULL, NULL),
    ('nsrc-000016', 'locality', NULL, '燕市', '笈ケ島'),
    ('nsrc-000016', 'locality', NULL, '燕市', '笈ヶ島'),
    ('nsrc-000017', 'name', '赤坂諏訪神社', NULL, NULL),
    ('nsrc-000017', 'locality', NULL, '燕市', '粟生津'),
    ('nsrc-000018', 'name', '赤崎神社', NULL, NULL),
    ('nsrc-000018', 'locality', NULL, '燕市', '宮小路'),
    ('nsrc-000019', 'name', '赤鏥神社', NULL, NULL),
    ('nsrc-000019', 'name_variant', '赤錆神社', NULL, NULL),
    ('nsrc-000019', 'locality', NULL, '西蒲区', '赤鏥'),
    ('nsrc-000019', 'locality', NULL, '西蒲区', '赤錆'),
    ('nsrc-000020', 'name', '赤澤神社', NULL, NULL),
    ('nsrc-000020', 'name_variant', '赤沢神社', NULL, NULL),
    ('nsrc-000020', 'locality', NULL, '吉川区', '赤沢'),
    ('nsrc-000020', 'locality', NULL, '吉川区', '赤澤')
),
rows_all (source_table, id, name_jp, address) AS (
  SELECT 'temples_shrine', id, name_jp, COALESCE(address, '') FROM temples_shrine
  UNION ALL
  SELECT 'temples_shrinecandidate', id, name_jp, COALESCE(address, '') FROM temples_shrinecandidate
)
SELECT
  p.candidate_id,
  p.probe_kind,
  COALESCE(p.name_jp, p.municipality || ' + ' || p.locality) AS probe,
  r.source_table,
  r.id,
  r.name_jp,
  r.address
FROM probes p
JOIN rows_all r
  ON (p.probe_kind IN ('name', 'name_variant') AND r.name_jp = p.name_jp)
  OR (p.probe_kind = 'locality'
      AND position(p.municipality IN r.address) > 0
      AND position(p.locality IN r.address) > 0)
ORDER BY p.candidate_id, p.probe_kind, r.source_table, r.id;
```

Expected result for the proposed classifications（§5）:

```text
statement 2: every count = 0（10 rows）
statement 3: 0 rows
```

Any non-zero count or listed row must be explained before G1 can close. A listed row is not
automatically a duplicate.

Local verification of this query（disposable PostgreSQL 16, **not Production**）:

```text
repository Base Seed DB（129 Shrine, 0 ShrineCandidate） -> all counts 0, 0 diagnostic rows
planted rows inside a rolled-back transaction:
  temples_shrinecandidate 赤坂神社 / 新潟県燕市別所1           -> nsrc-000016 same_name_other_address = 1 + listed
  temples_shrine 諏訪神社 / 新潟県燕市下粟生津515番地           -> nsrc-000017 same_address_other_name = 1 + listed
  temples_shrinecandidate 赤錆神社 / 新潟県新潟市西蒲区赤錆538  -> listed by name_variant and locality probes
transaction rolled back（ShrineCandidate count back to 0）
```

## 5. Evidence table

`production_*` counts are **NOT MEASURED** for the current state（§4.2）. The historical runner lookup
（§4.1）returned 0 for all five on `temples_shrine` only.

| candidate_id | source_position | frozen_name | frozen_address | proposed_canonical_name | proposed_canonical_address | identity_evidence | production_exact_match_count | production_same_name_other_address_count | production_same_address_other_name_count | duplicate_classification_candidate | unresolved_issue |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nsrc-000016 | page002-row006 | 赤坂神社 | 燕市笈ケ島2103番地 | 赤坂神社 | 新潟県燕市笈ケ島2103番地 | frozen Source row; repository has no other 赤坂神社; runner lookup 0（2026-10-08） | NOT MEASURED | NOT MEASURED | NOT MEASURED | NEW（conditional on §4.2 = 0） | current Production collision（§4.2）; relation to nsrc-000017 is name-prefix only, no alias evidence |
| nsrc-000017 | page002-row007 | 赤坂諏訪神社 | 燕市下粟生津515番地 | 赤坂諏訪神社 | 新潟県燕市下粟生津515番地 | frozen Source row; repository has no other 赤坂諏訪神社; runner lookup 0 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NEW（conditional on §4.2 = 0） | current Production collision（§4.2）, including a plain 諏訪神社 at 下粟生津 |
| nsrc-000018 | page002-row008 | 赤崎神社 | 燕市吉田宮小路874番地 | 赤崎神社 | 新潟県燕市吉田宮小路874番地 | frozen Source row; repository has no 赤崎 row; runner lookup 0 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NEW（conditional on §4.2 = 0） | current Production collision（§4.2） |
| nsrc-000019 | page002-row009 | 赤鏥神社 | 新潟市西蒲区赤鏥538番地 | 赤鏥神社 | 新潟県新潟市西蒲区赤鏥538番地 | frozen Source row; 鏥 U+93E5 consistent in name and locality; no 赤鏥 / 赤錆 row in repository; runner lookup 0 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NEW（conditional on §4.2 = 0） | current Production collision incl. 赤錆 variant（§4.2）; live Source cross-check not performed（§2.3） |
| nsrc-000020 | page002-row010 | 赤澤神社 | 上越市吉川区赤沢313番地 | 赤澤神社 | 新潟県上越市吉川区赤沢313番地 | frozen Source row; 澤 in name and 沢 in locality, both kept as frozen; no 赤澤 / 赤沢 row in repository; runner lookup 0 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NEW（conditional on §4.2 = 0） | current Production collision incl. 赤沢神社 variant（§4.2） |

## 6. Repository identity check

```text
shrine_expansion_nationwide_identity_manifest.json  handoffs = H001, H002, H003. H004 absent. No H004 name or locality string present
Candidate Master                                     H004 only as nsrc-000016〜000020（G0）. No other row with these names
Base Seed（shrines_seed_clean.json, 129 rows）       no row in 燕市 / 西蒲区 / 吉川区. No 赤坂神社 / 赤坂諏訪神社 / 赤崎 / 赤鏥 / 赤錆 / 赤澤 / 赤沢
other backend data JSON / audits                     H004 strings only in the Ready Set freeze, the G0 audit and G0 test / fixture
```

H004 is not represented under any other candidate identity in the repository.

## 7. EVIDENCE_RESULT

```text
nsrc-000016 = NEW（conditional）
nsrc-000017 = NEW（conditional）
nsrc-000018 = NEW（conditional）
nsrc-000019 = NEW（conditional）
nsrc-000020 = NEW（conditional）

condition         = current Production inspection（§4.2）returns 0 in every count and 0 diagnostic rows
ALIAS / DUPLICATE = no supporting evidence for any candidate
UNRESOLVED        = none on Source / repository evidence. The current Production state is not yet measured.
```

If §4.2 returns any row for a candidate, that candidate moves to `UNRESOLVED` until the row is
explained. It is never auto-classified as DUPLICATE or ALIAS from the query alone.

## 8. MOTHER_SHIP_DECISION

```text
PRODUCTION_COLLISION_CURRENT = PENDING（§4.2 not yet executed）

nsrc-000016 = PENDING
nsrc-000017 = PENDING
nsrc-000018 = PENDING
nsrc-000019 = PENDING
nsrc-000020 = PENDING

G1 = PENDING_MOTHER_SHIP_DECISION
```

## 9. Not changed

```text
Candidate Master（identity_status / duplicate_status / lifecycle）  NONE
handoff fixture lifecycle                                           NONE
reviewed identity manifest                                          NONE（H004 not added）
coordinates / G2                                                    NONE
Base Seed / Knowledge                                               NONE
Product Surface                                                     NOT DECIDED
Recommendation logic                                                NONE
Production                                                          NONE（no connection）
```

## 10. Next

After Mother Ship runs §4.2 and records the decision in §8, a separate PR confirms G1 in Candidate
Master（`identity_status = CONFIRMED`, `duplicate_status` per decision）and adds H004 to the reviewed
identity manifest.
