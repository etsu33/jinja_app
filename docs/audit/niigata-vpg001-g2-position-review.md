# NIIGATA-001-VPG001 G2 Position Review

## 1. Status

```text
G2                          = IN PROGRESS（NOT FROZEN, NOT CLOSED）
G2 final freeze             = NOT PERFORMED
Position Resolution Records = 5 of 5 persisted（docs/audit/shrine-position/niigata-vpg001-*）
position_status             = PASS ×5（nsrc-000021 / 000022 / 000023 / 000024 / 000025）
                              HOLD_POSITION_REVIEW ×0
Mother Ship decision        = final for all five
Mother Ship decisions 2026-10-19 = §6.1（CODH primary for 000022 / 000023; 000025 HOLD then final PASS
                              on the shared-precinct Google Maps entity;
                              000021 PASS on Google Maps POI; 000024 PASS on official-linked
                              Google Maps navigation target）
open items                  = no status open; corroboration URLs only: nsrc-000021 Yahoo!/Zenrin,
                              nsrc-000023 Wikidata, nsrc-000025 A / B / CODH（§6）
coordinates generated or inferred = NONE
Production write            = NONE
```

- Bootstrap recorded at: 2026-10-18（PR #3266, base `develop@df7cb791`）
- Evidence persisted at: 2026-10-18（base `develop@225352c5`, branch `audit/niigata-vpg001-g2-position-evidence`）
- Mother Ship decisions recorded at: 2026-10-19（§6.1）

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
| nsrc-000021 | PASS（2026-10-19） | PASS | Google Maps POI entity adopted（URL, feature id, entity token persisted）; Yahoo!/Zenrin + 國學院 corroboration; Yahoo URL not supplied |
| nsrc-000022 | PASS adopted; CODH accepted as primary（2026-10-19, candidate-specific） | PASS | CODH coordinate + URL persisted; no corroboration |
| nsrc-000023 | PASS adopted; CODH accepted as primary（2026-10-19, candidate-specific） | PASS | CODH coordinate + URL persisted; Wikidata corroboration provenance pending |
| nsrc-000024 | PASS（2026-10-19） | PASS | official website links to the Google Maps navigation target; URL, feature id, entity token persisted |
| nsrc-000025 | PASS adopted（historical, preserved）→ HOLD（2026-10-19）→ final PASS（2026-10-19） | PASS | shared-precinct Google Maps entity adopted（URL, feature id, entity token persisted）; A / B / CODH kept as not-adopted records |

Historical Mother Ship decisions are preserved as made. For nsrc-000025, Mother Ship set the current
contract status to HOLD_POSITION_REVIEW on 2026-10-19 and then made the final PASS decision on the
shared-precinct anchor（§6.1）. The historical PASS is not rewritten.

## 5. Evidence table

| candidate_id | latitude | longitude | primary source / type | corroboration | verified_at | position_status |
|---|---|---|---|---|---|---|
| nsrc-000021 | 38.1409456 | 139.4073314 | Google Maps 荒川神社 POI（`map_provider_poi`）, feature id `0x5f8b6bd0cbf5ba91:0xa762ad68fe889819`, `/g/11v4bqq35k`; URL in the record | Yahoo!/Zenrin `38.1409423, 139.4072801`（4.50 m）; 國學院 `38.140916, 139.407516` https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468（16.48 m）; identity: 観光協会, 文化庁 | 2026-10-19 | PASS |
| nsrc-000022 | 37.573979 | 139.048758 | CODH 日本歴史地名大系 facility point（`public_reference_dataset_facility_point`）, https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000311900.html | none supplied | 2026-10-18 | PASS |
| nsrc-000023 | 38.072529 | 138.407913 | CODH 日本歴史地名大系 facility point（`public_reference_dataset_facility_point`）, https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000593300.html | Wikidata `38.072471, 138.407785`, delta 12.93 m（provenance pending: URL / QID not recorded） | 2026-10-18 | PASS |
| nsrc-000024 | 37.7863255 | 139.1351949 | Google Maps navigation target linked from the official website https://www.niitsu.or.jp/~akiha-jinja/（`official_linked_map_provider_navigation_target`）, feature id `0x5ff4da6185158fed:0x772d4e3a0bb54ea1`, `/g/12hnpqljd`; URL in the record | identity: 新潟県神社庁 https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15105 | 2026-10-19 | PASS |
| nsrc-000025 | 37.0397729 | 137.8644153 | Google Maps shared-precinct entity 天津神社・奴奈川神社（`official_linked_shared_precinct_map_provider_poi`）, feature id `0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2`, `/m/0nb82lf`; URL in the record; official context https://amatsujinja.com/（交通案内） | not adopted: A Wikipedia `37.0401500, 137.8642250`（45.21 m）; B Open Data Japan / 糸魚川市 `37.0399114, 137.864377`（15.77 m, corroboration）; CODH 天津神社祭祀遺跡 `37.039941, 137.864358`（19.37 m, corroboration）; identity: 糸魚川観光ガイド | 2026-10-19 | PASS |

Records:

- `docs/audit/shrine-position/niigata-vpg001-nsrc-000021-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000022-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000023-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000024-position-review.md`
- `docs/audit/shrine-position/niigata-vpg001-nsrc-000025-position-review.md`

These records are the G2 current-state evidence. The Position Contract remains the rule authority.

## 6. Contract / evidence notes and unresolved items

```text
nsrc-000021  PASS（2026-10-19）
  - previous HOLD reasons（no independent numeric corroboration; no primary POI; reference DB only）
    RESOLVED by the Google Maps POI primary with Yahoo!/Zenrin + 國學院 corroboration
  - primary provenance finalized: Google Maps POI URL recorded verbatim; adopted coordinate is the
    POI entity coordinate 38.1409456, 139.4073314（replaces the earlier rounded 38.140945, 139.407348;
    precision correction, not a new decision）
  - OPEN: Yahoo!/Zenrin URL not supplied（corroboration provenance only; does not change the PASS）

nsrc-000024  PASS（2026-10-19）
  - previous HOLD reasons（no official visitor-facing numeric coordinate; no navigation target）RESOLVED
    by the Google Maps navigation target linked from the official shrine website
  - observation: the linked target is an address-labelled place（〒956-0832 …秋葉３丁目８−１９）, not a
    shrine-named POI; the address matches the canonical identity

nsrc-000022  PASS
  - CODH primary-source-type note: RESOLVED by Mother Ship（§6.1）
  - no corroboration supplied; no conflict observed

nsrc-000023  PASS
  - CODH primary-source-type note: RESOLVED by Mother Ship（§6.1）
  - OPEN: Wikidata corroboration provenance pending until a reproducible URL / QID is recorded;
    its independence from the CODH dataset is not verified. This does not invalidate the CODH primary.

nsrc-000025  PASS（final, 2026-10-19; historical PASS and 2026-10-19 HOLD preserved in the record）
  - HOLD reasons RESOLVED: adopted coordinate determined（37.0397729, 137.8644153）; primary source
    traceable（Google Maps entity URL）; semantics = shared-precinct Visitor / Navigation Anchor,
    not the 天津神社御本殿 coordinate
  - 天津神社 / 奴奈川神社 remain separate Fact owners; G3 model-risk stays open
  - OPEN: source URLs for A / B / CODH not supplied（historical / corroboration records only）
```

### 6.1 Mother Ship decisions（2026-10-19）

```text
nsrc-000022  CODH 日本歴史地名大系 facility point accepted as the primary position source
             scope = this candidate only; position_status = PASS（kept）

nsrc-000023  CODH 日本歴史地名大系 facility point accepted as the primary position source
             scope = this candidate only; position_status = PASS（kept）
             Wikidata = corroboration provenance pending until its URL / QID is recorded

nsrc-000025  MOTHER_SHIP_G2_DECISION = PASS（adopted）preserved as the historical decision
             current contract position_status = HOLD_POSITION_REVIEW
             reason = adopted coordinate not determined; primary coordinate source not traceable;
                      candidate A / B semantics within the two-honden precinct unresolved
             A / B not chosen; no provenance inferred or manufactured

global rule  NONE. CODH does not automatically qualify as a primary position source for other
             candidates. Each candidate needs its own Mother Ship decision.

nsrc-000021  PASS. Adopted Visitor / Navigation Anchor = 38.1409456, 139.4073314
             primary = Google Maps 荒川神社 POI entity（map_provider_poi）
                       feature id 0x5f8b6bd0cbf5ba91:0xa762ad68fe889819, /g/11v4bqq35k
             corroboration = Yahoo!/Zenrin 38.1409423, 139.4072801;
                             國學院 式内社DB 38.140916, 139.407516
             deltas are audit observations only（4.50 m / 16.48 m）; no distance threshold
             not adopted: right-click point 38.141030, 139.407468; URL viewport / dropped-pin points

nsrc-000024  PASS. Adopted Visitor / Navigation Anchor = 37.7863255, 139.1351949
             visitor-facing authority = official shrine website https://www.niitsu.or.jp/~akiha-jinja/
             primary = Google Maps navigation target linked from that site
                       （official_linked_map_provider_navigation_target）
                       feature id 0x5ff4da6185158fed:0x772d4e3a0bb54ea1, /g/12hnpqljd
             not adopted: viewport centre 37.7863226, 139.1351315（5.58 m）;
                          right-click point 37.786353, 139.135193（3.06 m）

nsrc-000025  final PASS. Adopted Visitor / Navigation Anchor = 37.0397729, 137.8644153
             semantics = shared 天津神社・奴奈川神社 precinct anchor; NOT the 天津神社御本殿 coordinate
             primary = Google Maps entity 天津神社・奴奈川神社
                       （official_linked_shared_precinct_map_provider_poi）
                       feature id 0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2, /m/0nb82lf
             official context = https://amatsujinja.com/（交通案内）
             not adopted: A（Wikipedia, provenance unresolved）; B（Open Data Japan / 糸魚川市,
                          corroboration）; CODH 天津神社祭祀遺跡（corroboration only）
             historical PASS（2026-10-18）and HOLD（2026-10-19）preserved
```

## 7. Cross-candidate validation

Validation only. None of these checks is used as evidence or to adopt a coordinate.

```text
identity vs G1 canonical identity        all five match by name + address（notation differences only:
                                         大字 / 番地 / 丁目番号 forms）
similarly named different shrines         not used as sources（荒川神社 ×3, 秋葉神社 ×10, 天津神社 ×1
                                         other frozen rows; 奴奈川神社 is a separate Fact owner）
duplicate coordinates across candidates  NONE（all supplied points distinct）
nearest pair between candidates          nsrc-000022 ↔ nsrc-000024 = 24.8 km
within-candidate deltas                  nsrc-000021 Google↔Yahoo 4.50 m, Google↔國學院 16.48 m;
                                         nsrc-000023 CODH↔Wikidata 12.93 m; nsrc-000025 entity↔B 15.77 m,
                                         entity↔CODH 19.37 m, entity↔A 45.21 m
prefecture bounding-box check            all supplied points inside Niigata（approx. 36.7–38.6 N,
                                         137.6–139.95 E）
unexplained conflicts                    NONE（nsrc-000025 A / B / CODH explained as not adopted）
```

## 8. Not done

```text
G2 final freeze                          NOT PERFORMED
G2 CLOSED / FROZEN                       NO
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
1. nsrc-000021: PASS. Yahoo!/Zenrin URL still to be recorded（corroboration provenance only; does
   not block the PASS）.
2. nsrc-000024: PASS（2026-10-19）. No open item.
3. nsrc-000025: PASS（final, 2026-10-19）. A / B / CODH source URLs to be recorded（provenance only;
   does not block the PASS）.
4. nsrc-000023: Wikidata item URL / QID to complete corroboration provenance（does not block the PASS）.
5. Every candidate now has one final status（PASS ×5 / HOLD ×0）. G2 final freeze is a separate
   change and a Mother Ship decision. The open items above are corroboration provenance only.
```
