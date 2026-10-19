# nsrc-000024 秋葉神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000024
position_status          = PASS
new_latitude             = 37.7863255
new_longitude            = 139.1351949
new_position_source_type = official_linked_map_provider_navigation_target
new_position_source_url  = https://www.google.com/maps/place/%E3%80%92956-0832+%E6%96%B0%E6%BD%9F%E7%9C%8C%E6%96%B0%E6%BD%9F%E5%B8%82%E7%A7%8B%E8%91%89%E5%8C%BA%E7%A7%8B%E8%91%89%EF%BC%93%E4%B8%81%E7%9B%AE%EF%BC%98%E2%88%92%EF%BC%91%EF%BC%99/@37.7863226,139.1351315,142m/data=!3m1!1e3!4m6!3m5!1s0x5ff4da6185158fed:0x772d4e3a0bb54ea1!8m2!3d37.7863255!4d139.1351949!16s%2Fg%2F12hnpqljd?authuser=0&entry=ttu&g_ep=EgoyMDI2MTAxMy4wIKXMDSoASAFQAw%3D%3D
verified_at              = 2026-10-19
official_visitor_source  = https://www.niitsu.or.jp/~akiha-jinja/
google_maps_feature_id   = 0x5ff4da6185158fed:0x772d4e3a0bb54ea1
google_maps_entity_token = /g/12hnpqljd
MOTHER_SHIP_G2_DECISION  = PASS（2026-10-19）
ADOPTED_COORDINATE       = 37.7863255, 139.1351949
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- First recorded: 2026-10-18（PR #3267, HOLD_POSITION_REVIEW）
- Resolved: 2026-10-19（base `develop@07d62c86`, Mother Ship final decision）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. Both URLs were supplied by Mother Ship on 2026-10-19 and are
recorded verbatim, not reconstructed or normalized. They were not re-fetched in this environment（its
network policy denies the hosts）. `verified_at` is the Mother Ship supply / decision date.

## Canonical identity（G1, unchanged）

```text
official_name    = 秋葉神社
official_address = 新潟県新潟市秋葉区秋葉3丁目8番19号
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

The 10 other frozen 秋葉神社 rows（different addresses）are different shrines and are not position
sources. Name-only matching is not used.

## Visitor-facing authority

```text
official shrine website（宗教法人 秋葉神社）
  url  = https://www.niitsu.or.jp/~akiha-jinja/
  role = visitor-facing authority; links directly to the Google Maps navigation target below

新潟県神社庁（official shrine directory; identity corroboration, recorded 2026-10-18）
  url     = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15105
  address = 新潟市秋葉区秋葉3丁目8番19号
```

## Adopted Visitor / Navigation Anchor（Mother Ship final decision, 2026-10-19）

```text
latitude  = 37.7863255
longitude = 139.1351949

primary navigation anchor:
  type        = official_linked_map_provider_navigation_target
  provider    = Google Maps
  linked from = https://www.niitsu.or.jp/~akiha-jinja/
  feature_id  = 0x5ff4da6185158fed:0x772d4e3a0bb54ea1
  entity      = /g/12hnpqljd
  url         = new_position_source_url（Status block, verbatim）
```

The adopted coordinate is the place-entity coordinate embedded in the URL:

```text
entity block  = !3m5!1s0x5ff4da6185158fed:0x772d4e3a0bb54ea1!8m2!3d37.7863255!4d139.1351949
entity token  = !16s%2Fg%2F12hnpqljd（/g/12hnpqljd）
```

Points **not** adopted（distances from the adopted point; audit observations only）:

```text
viewport centre   37.7863226, 139.1351315   URL @ map view   5.58 m
right-click point 37.786353, 139.135193     separately observed by Mother Ship   3.06 m
```

Observation: the URL's place path decodes to the postal address
`〒956-0832 新潟県新潟市秋葉区秋葉３丁目８−１９`, not to the name 秋葉神社. The navigation target is
therefore an address-labelled place. That address matches the canonical identity
（秋葉区秋葉3丁目8番19号; full-width digits and `−` are notation only）. The target is adopted because the
official shrine website links to it directly（contract: "神社公式が直接掲載・リンクするnavigation map / map
provider"）, not because of a shrine-named POI.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（official website, 神社庁, G1） |
| 2. primary source is the same shrine's POI / navigation target | PASS（official-site-linked navigation target） |
| 3. latitude / longitude traceable from the primary source | PASS（entity coordinate embedded in the recorded URL） |
| 4. primary point consistent with visitor-facing identity | PASS（target address = canonical address） |
| 5. conflict explained | no conflict; viewport / right-click points are not adopted |

## Previous HOLD（2026-10-18）— resolved

```text
OFFICIAL_VISITOR_NUMERIC_COORDINATE_NOT_OBTAINED  -> RESOLVED（official site's linked Google Maps target）
PRIMARY_POI_OR_NAVIGATION_TARGET_NOT_ESTABLISHED  -> RESOLVED（same）
```

No coordinate was inferred from the address.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
