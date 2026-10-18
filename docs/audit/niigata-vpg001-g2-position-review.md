# NIIGATA-001-VPG001 G2 Position Review

## 1. Status

```text
G2                          = IN PROGRESS（NOT FROZEN, NOT CLOSED）
G2 final freeze             = NOT PERFORMED
Position Resolution Records = 5 of 5 persisted（docs/audit/shrine-position/niigata-vpg001-*）
position_status             = PASS ×3（Mother Ship: nsrc-000022 / 000023 / 000025）
                              HOLD_POSITION_REVIEW ×2（technical: nsrc-000021 / 000024）
Mother Ship decision        = PENDING for nsrc-000021 / nsrc-000024
open contract / evidence notes = nsrc-000022, nsrc-000023, nsrc-000025（§6）
coordinates generated or inferred = NONE
Production write            = NONE
```

- Bootstrap recorded at: 2026-10-18（PR #3266, base `develop@df7cb791`）
- Evidence persisted at: 2026-10-18（base `develop@225352c5`, branch `audit/niigata-vpg001-g2-position-evidence`）

The bootstrap（PR #3266）recorded the G2 scope and Mother Ship decision state. This update persists the
position evidence Mother Ship supplied on 2026-10-18 as one Position Resolution Record per candidate.
It evaluates each against the Position Contract. It does not freeze G2.

Evidence level for all five: `MOTHER_SHIP_SUPPLIED`. The sources were not re-fetched in this
environment. Its network policy denies the source hosts. Values are recorded exactly as supplied.

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §5 G2 Position / Navigation Anchor Gate
- `docs/knowledge/shrine-position-contract.md`（Source Adoption Rule, Audit Record, Position Status:
  `PASS` / `HOLD_POSITION_REVIEW`）
- `docs/audit/niigata-vpg001-g1-identity-duplicate.md`（G1 PASS / CLOSED; canonical identities）
- Mother Ship: G2 candidate set, the three PASS decisions（§4）and the evidence in the records（§5）

## 3. G2 scope

Exactly the five VPG001 candidates. Addresses are recorded as supplied by Mother Ship for G2. The
canonical identity is unchanged and remains the G1 `official_address`（reviewed identity manifest）.

| candidate_id | name | G2 scope address（as supplied by Mother Ship） | G1 canonical official_address（unchanged） |
|---|---|---|---|
| nsrc-000021 | 荒川神社 | 新潟県胎内市桃崎浜187 | 新潟県胎内市桃崎浜187番地 |
| nsrc-000022 | 五十嵐神社 | 新潟県三条市飯田2283 | 新潟県三条市大字飯田2283番地 |
| nsrc-000023 | 熱串彦神社 | 新潟県佐渡市長江854 | 新潟県佐渡市長江854番地 |
| nsrc-000024 | 秋葉神社 | 新潟県新潟市秋葉区秋葉3-8-19 | 新潟県新潟市秋葉区秋葉3丁目8番19号 |
| nsrc-000025 | 天津神社 | 新潟県糸魚川市一の宮1-3-34 | 新潟県糸魚川市一の宮1丁目3番34号 |

No other candidate is in G2 scope. No G2 candidate is added.

## 4. Mother Ship decision state vs repository evidence state

These are two separate axes. A Mother Ship decision is recorded exactly as made. Repository evidence
state records only what the repository contains.

| candidate_id | Mother Ship decision | position_status（record） | repository evidence state |
|---|---|---|---|
| nsrc-000021 | PENDING | HOLD_POSITION_REVIEW（technical proposal） | one numeric source（國學院）; no independent numeric corroboration |
| nsrc-000022 | PASS adopted | PASS | CODH coordinate + URL persisted; no corroboration; source-type note |
| nsrc-000023 | PASS adopted | PASS | CODH coordinate + URL persisted; Wikidata corroboration without URL; source-type note |
| nsrc-000024 | PENDING | HOLD_POSITION_REVIEW（technical proposal） | identity sources only; no numeric coordinate |
| nsrc-000025 | PASS adopted | PASS | two unattributed numeric candidates; adopted coordinate not determined |

The three PASS decisions are not reinterpreted. Where the supplied evidence does not fully satisfy
the contract's Audit Record, the gap is reported in §6, and the decision is left as made.

## 5. Evidence table

| candidate_id | latitude | longitude | primary source / type | corroboration | verified_at | position_status |
|---|---|---|---|---|---|---|
| nsrc-000021 | — | — | none adopted. Candidate only: 國學院 式内社DB `38.140916, 139.407516`（`independent_shrine_reference_database`）, https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468 | identity only: 新潟県観光協会 https://niigata-kankou.or.jp/spot/7288 ; 文化庁 https://kunishitei.bunka.go.jp/bsys/maindetails/101/00013085 | 2026-10-18 | HOLD_POSITION_REVIEW |
| nsrc-000022 | 37.573979 | 139.048758 | CODH 日本歴史地名大系 facility point（`public_reference_dataset_facility_point`）, https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000311900.html | none supplied | 2026-10-18 | PASS |
| nsrc-000023 | 38.072529 | 138.407913 | CODH 日本歴史地名大系 facility point（`public_reference_dataset_facility_point`）, https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000593300.html | Wikidata `38.072471, 138.407785`（URL not supplied）, delta 12.93 m | 2026-10-18 | PASS |
| nsrc-000024 | — | — | none. Identity only: official page https://www.niitsu.or.jp/~akiha-jinja/ ; 新潟県神社庁 https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15105 | — | 2026-10-18 | HOLD_POSITION_REVIEW |
| nsrc-000025 | NOT_DETERMINED | NOT_DETERMINED | not supplied. Candidates A `37.0401500, 137.8642250` / B `37.0399114, 137.864377`, 29.76 m apart | identity only: 糸魚川観光ガイド https://www.itoigawa-kanko.net/trad/amatsu_shrine/ ; official site https://amatsujinja.com/contact/ | 2026-10-18 | PASS（Mother Ship） |

Records:

- `docs/audit/shrine-position/niigata-vpg001-nsrc-000021-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000022-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000023-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000024-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000025-position-review.md`

These records are the G2 current-state evidence. The Position Contract remains the rule authority.

## 6. Contract / evidence notes and unresolved items

```text
nsrc-000021  HOLD_POSITION_REVIEW
  - only one numeric source; the independence requirement cannot be met with a single source
  - identity sources（観光協会, 文化庁）are independent but carry no coordinate
  - 國學院 records are used in repository precedent only as corroboration of a map-provider POI
  - the supplied 國學院 record names 胎内市, not the locality 桃崎浜

nsrc-000024  HOLD_POSITION_REVIEW
  - no official visitor-facing numeric coordinate was supplied; address identity alone is not PASS

nsrc-000022  PASS（Mother Ship）
  - primary is a CODH 日本歴史地名大系 facility point; repository precedent used CODH only as
    corroboration（docs/audit/niigata-h001-g2-position-gate.md, nsrc-000003）
  - no corroboration and no current map-provider POI / official navigation target persisted

nsrc-000023  PASS（Mother Ship）
  - same primary-source-type note as nsrc-000022
  - Wikidata corroboration has no item URL / QID → not reproducible from the record
  - independence of the Wikidata point from the CODH dataset is not verified

nsrc-000025  PASS（Mother Ship）
  - two numeric candidates, neither with a source; the adopted coordinate is not determined
  - Audit Record fields position_source_type / position_source_url cannot be filled
  - A and B are 29.76 m apart in a two-honden precinct（天津神社・奴奈川神社）; which point, if
    either, is the 天津神社 visitor anchor is not shown by the evidence
```

## 7. Cross-candidate validation

Validation only. None of these checks is used as evidence or to adopt a coordinate.

```text
identity vs G1 canonical identity        all five match by name + address（notation differences only:
                                         大字 / 番地 / 丁目番号 forms）
similarly named different shrines         not used as sources（荒川神社 ×3, 秋葉神社 ×10, 天津神社 ×1
                                         other frozen rows; 奴奈川神社 is a separate Fact owner）
duplicate coordinates across candidates  NONE（all supplied points distinct）
nearest pair between candidates          nsrc-000021 ↔ nsrc-000022 = 70.5 km
within-candidate deltas                  nsrc-000023 CODH↔Wikidata 12.93 m; nsrc-000025 A↔B 29.76 m
prefecture bounding-box check            all supplied points inside Niigata（approx. 36.7–38.6 N,
                                         137.6–139.95 E）
unexplained conflicts                    nsrc-000025 A↔B（§6）
```

## 8. Not done

```text
G2 final freeze                          NOT PERFORMED
G2 CLOSED / FROZEN                       NO
Mother Ship decision for 000021 / 000024 NOT MADE
re-fetch / independent verification      NOT DONE（network policy）
coordinate generated or inferred         NONE（no geocoding, no address conversion, no snippets）
Candidate Master / identity manifest     UNCHANGED
G1 records                               UNCHANGED
Base Seed / Knowledge / Production       UNCHANGED, NO WRITE
Recommendation / Ranking / Meaning       UNCHANGED
G3 model-risk（天津神社・奴奈川神社）     OPEN（not a G2 question）
```

## 9. Next

```text
1. nsrc-000021: a map-provider POI / official navigation target, or a second independent numeric
   source; then Mother Ship decides.
2. nsrc-000024: an official visitor-facing numeric coordinate; then Mother Ship decides.
3. nsrc-000025: Mother Ship names the adopted point（A, B or other）and its source.
4. nsrc-000022 / 000023: Mother Ship confirms the CODH primary-source type under the contract;
   nsrc-000023 Wikidata item URL to be supplied.
5. Only when every candidate has one final status with complete provenance: G2 final freeze
   （separate change）.
```
