# Knowledge Batch 9 Source Semantic Conflict Remediation

## Executive Summary

- Date: 2026-08-10
- Base: `develop` / `9519b7aa04b210eee1b083b59094cd0733c610bf`
- Conflict: identical official Hakone URL was planned as a second Source because title differed
- Classification before remediation: `SOURCE_SEMANTIC_DUPLICATE_CONFIRMED`
- Selected design: unique `source_type + normalized URL` reuse with strict metadata compatibility
- Revised Production delta: Source +5 / Deity +13 / History +5 / relations +13/+5
- Production-equivalent: PASS; Hakone URL Source remains one row
- Production validate-only/dry-run: PASS; CREATE 5, REUSE 1, Deity 13, History 5
- Final classification: **`BATCH9_SOURCE_REMEDIATION_READY`**
- Production DB writes: **0**
- Batch 9 Production import: **NOT_EXECUTED**

## 1. Conflict reproduction

Production read-only inspection found one existing `shrine_official` Source at
`https://hakonejinja.or.jp/hakone/`. It is titled
「箱根神社・九頭龍神社・箱根元宮の由緒並に宝物と文化財」 and is already
related to 九頭龍神社 新宮のDeity「九頭龍大神」とHistory「新宮の建立」。

The original Batch 9 seed used the same URL under title
「箱根神社の由緒｜箱根神社」. The old importer queried
`source_type + title + exact URL`, found no row, and planned `CREATE`. This
would have produced two Source rows for one official Web document.

**Reproduction classification: `SOURCE_SEMANTIC_DUPLICATE_CONFIRMED`.**

## 2. Previous identity behavior

The implementation was read fresh. It had no URL normalization. For a URL-backed
Source, scheme, host case, trailing slash, query, fragment, and title all had to
match the stored values exactly. Publisher, verification status, confidence,
language, and note were not considered by matching. The first title-based match
was silently selected. This explained both the false CREATE and the inability to
detect multiple semantic URL matches.

## 3. Design comparison and decision

| Candidate | Result |
| --- | --- |
| A — retain old key and align seed title | Fixes only the observed row; future title drift can recreate the bug |
| B — `source_type + normalized URL` identity | Selected; portable, no schema/PK dependency, detects the whole bug class |
| C — explicit reuse marker in seed | Rejected for now; introduces a new seed contract and still needs identity resolution |
| D — stable external key/model field | Deferred; requires schema migration and Production model change |

Candidate B is implemented without schema changes. URL normalization:

- lowercases scheme and host;
- removes default ports;
- ignores fragments and a non-root trailing slash;
- preserves query strings;
- keeps http and https distinct.

Exactly one same-type normalized-URL match is reusable only when publisher,
verification status, confidence, bibliography, and language agree after outer
whitespace trimming. Title, access/verification timestamps, and note do not
define document identity and are not overwritten.

- unique and compatible: `SOURCE_REUSE_SAFE` / `REUSE_EXISTING`
- unique but important metadata differs: `SOURCE_REUSE_CONFLICT` / hard stop
- multiple matches: `SOURCE_REUSE_AMBIGUOUS` / hard stop
- no match: `CREATE`

URL-less Sources retain the previous `source_type + title + bibliography`
lookup. Existing rows are never updated.

## 4. Seed remediation and hashes

The Hakone seed Source title, publisher, and language now match the existing
portable Source metadata. No Production Source PK or environment-specific ID is
stored.

- Old STOP-state SHA-256:
  `a4acc276839e8b25937f6a5d7e830365783c7fb787ff5b5d01f29e20dc5116e4`
- Remediated SHA-256:
  `8178e49da03ec4d2a1024e3708c2d16c35e549c6c70e3a6aeb439ef156f98be4`

The portable seed still contains six Source descriptions, 13 Deities, five
Histories, and relation references 13/5. Against current Production, one Source
is reused, so the write delta is Source +5, Deity +13, History +5, and relations
+13/+5.

## 5. Regression protection

The importer tests now cover:

1. same type + normalized URL + different title reuses rather than creates;
2. newly created Facts link to the reused Source;
3. multiple existing semantic matches stop atomically;
4. meaningful metadata conflict stops atomically;
5. host case and trailing-slash normalization;
6. Batch 1–7 and Batch 8 seeds still parse, while the existing importer suite
   preserves create, validation, ambiguity, atomicity, round-trip, and
   idempotency behavior.

Focused remediation suite: **27 passed**.

## 6. Disposable local validation

A clean disposable local PostgreSQL database was migrated and populated with
the five canonical target identities plus one compatible existing Hakone
Source. Results:

- validate-only: PASS
- first dry-run: Source CREATE 5 / REUSE 1 / Deity CREATE 13 / History CREATE 5
- one local import: exit 0; created 5/13/5
- relations: 13/5
- source-less Deity/History: 0/0
- Hakone normalized URL Source count after import: 1
- second dry-run: Source REUSE 6 / Deity SKIP 13 / History SKIP 5 / CREATE 0

## 7. Fresh Production-equivalent validation

A fresh read-only Production dump was restored into a guard-approved isolated
local database. The existing Hakone Source and its 九頭龍神社 新宮 relations
were present before import.

| Metric | Before | After | Delta | Result |
| --- | ---: | ---: | ---: | --- |
| Shrine | 105 | 105 | 0 | PASS |
| Knowledge Shrine | 46 | 51 | +5 | PASS |
| Source | 65 | 70 | +5 | PASS |
| Deity | 117 | 130 | +13 | PASS |
| History | 91 | 96 | +5 | PASS |
| Deity–Source | 130 | 143 | +13 | PASS |
| History–Source | 96 | 101 | +5 | PASS |
| Hakone normalized URL Source | 1 | 1 | 0 | PASS |
| complete | 44 | 49 | +5 | PASS |
| partial | 2 | 2 | 0 | PASS |
| none (105-row operational classification) | 59 | 54 | -5 | PASS |

Source-less Deity/History remained 0/0. Users 1, profiles 1, shrines 105,
favorites 0, visits 2, and goriyaku relations 283 were unchanged. The second
dry-run planned Source REUSE 6 and Fact SKIP 18 with no CREATE or error.

## 8. Production read-only validation

Production `--validate-only` passed. Production `--dry-run` planned:

- Source CREATE: 5
- Source REUSE_EXISTING: 1 (Hakone official Source)
- Deity CREATE: 13
- History CREATE: 5
- UPDATE: 0
- ambiguous: 0
- conflict: 0
- error: 0

No Production import or Source update was executed.

## 9. Remaining risks and execution boundary

- Redirect-equivalent URLs and query-parameter equivalence are not inferred.
  Query strings deliberately remain identity-significant.
- The compatibility field set is conservative. A blank/nonblank difference in
  publisher, status, confidence, bibliography, or language stops reuse and must
  be reviewed rather than silently enriched.
- The database has no uniqueness constraint on semantic URL identity. The
  importer detects multiple matches at planning time, but concurrent creation
  outside this importer remains a residual risk.
- Existing Fact `SKIP_EXISTS` still does not compare every Fact field. Any
  unexpected Fact skip in a future execution gate remains a hard stop.

The next Production Execution Gate must use only remediated hash
`8178e49d…98be4` and expected Source CREATE 5 + REUSE 1. The old all-Source-
CREATE expectation and old seed hash are invalid for execution.

**Final classification: `BATCH9_SOURCE_REMEDIATION_READY`.**

- Production DB writes: **0**
- Batch 9 Production import: **NOT_EXECUTED**
- Batch 10: **NOT_STARTED**
