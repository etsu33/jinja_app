# NIIGATA-001-H001 G2 Position / Navigation Anchor Gate

> Status: **PARTIAL PASS — 3 PASS / 2 HOLD**
>
> Recorded at: 2026-10-10
>
> G0: PASS
> G1: PASS 5 / 5
> Production write: 0
> Candidate Master write: 0
> Base Seed write: 0
> G3 execution: 0

## Scope

Execute G2 Position / Navigation Anchor for the five registered
`NIIGATA-001-H001` Candidates under:

`docs/knowledge/shrine-position-contract.md`.

No address geocoding, Mapcode conversion, opaque provider Place-ID conversion, or map-center
guess is promoted to an adopted coordinate.

## Results

| candidate_id | Shrine | G2 | adopted coordinate | reason |
|---|---|---|---|---|
| nsrc-000001 | 相吉神社 | HOLD_POSITION_REVIEW | — | current traceable coordinate-bearing primary POI not obtained |
| nsrc-000002 | 青澤神社 | PASS | 37.00763484, 137.79024297 | Mapion POI payload + route destination bind name / locality / coordinate |
| nsrc-000003 | 蒼柴神社 | HOLD_POSITION_REVIEW | — | official map center semantics vs facility point unresolved |
| nsrc-000004 | 青海神社（加茂市） | PASS | 37.65657387, 139.0536436 | Mapion POI + official visitor route + Kokugakuin corroboration |
| nsrc-000005 | 青山稲荷神社（柏崎市） | PASS | 37.4172812, 138.5910754 | Yahoo! Map exact-address POI + selected map pin coordinate |

```text
G2_PASS = 3
G2_HOLD_POSITION_REVIEW = 2
```

## PASS: nsrc-000004 青海神社

Official visitor page:
- https://aomi-jinjya.or.jp/acsess.html

Primary map-provider POI:
- https://www.mapion.co.jp/phonebook/M06005/15209/ILSP0061134757_ipclm/
- `37.65657387, 139.0536436`

Independent corroboration:
- https://jmapps.ne.jp/kokugakuin/det.html?data_id=182448
- `37.656662, 139.053621`

Observed delta:
- `10.00 m`

The G1 same-name risk is controlled by matching the 加茂市 / あおみ identity and visitor-facing
official address. The 糸魚川市 same-name shrine is not used.

## PASS: nsrc-000002 青澤神社

Canonical identity:
- 新潟県神社庁
- 青澤神社
- 新潟県糸魚川市大字青海2696番地

Primary map-provider POI:
- https://www.mapion.co.jp/phonebook/M51020/15216/120399442_ipcbl/
- displayed name: 青沢神社
- reading: あおさわじんじゃ
- locality: 新潟県糸魚川市大字青海
- coordinate: `37.00763484, 137.79024297`

Human QA on 2026-10-10 confirmed the current Mapion page binds the same coordinate to the
`青沢神社` POI in `data-spotinfo` and uses it as the route destination
(`n_end_name=青沢神社`, `n_end_lat`, `n_end_lon`).

The G1 spelling `青澤` and Mapion spelling `青沢` are controlled by the matching reading,
municipality / locality, and the separately observed exact-address provider listing at
`2696 Oumi, Itoigawa`. No coordinate is inferred from that provider ID or from the address.

## HOLD: nsrc-000003 蒼柴神社

Official access page:
- https://www.aoshijinja.or.jp/アクセス/

Observed official Google iframe:
- query: 蒼柴神社
- `ll=37.4325553,138.883193`

Independent facility point:
- https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000282500.html
- `37.433212,138.882950`

Observed delta:
- `76.11 m`

The iframe `ll` parameter is a map-view center and is not deterministically proven to be the
POI marker / Visitor Anchor. The Gate therefore does not choose either point.

## PASS: nsrc-000005 青山稲荷神社

Canonical identity:
- 新潟県神社庁
- 青山稲荷神社
- 新潟県柏崎市荒浜4丁目1754番地2

Primary map-provider POI:
- https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
- name: 青山稲荷神社
- address: 新潟県柏崎市荒浜4丁目1754-2
- selected POI pin: `37.4172812, 138.5910754`

Human QA on 2026-10-10 confirmed the Yahoo! Map POI HTML binds the selected map marker coordinate
to the 青山稲荷神社 static map / place summary. The coordinate is not adopted from address
geocoding or a generic map viewport.

The `番地` / hyphenated parcel notation difference is explainably aligned and the exact
柏崎市荒浜 address controls same-name shrine risk.

## HOLD: remaining two

- 相吉神社: official address is confirmed, but no traceable numeric primary POI coordinate was
  obtained.
- 蒼柴神社: official map center semantics vs facility point remain unresolved.

The Gate does not reverse-geocode or infer coordinates from address / Mapcode / provider IDs.

## Position Resolution Records

- `docs/audit/shrine-position/niigata-h001-aiyoshi-jinja-position-resolution.md`
- `docs/audit/shrine-position/niigata-h001-aosawa-jinja-position-resolution.md`
- `docs/audit/shrine-position/niigata-h001-aoshi-jinja-position-resolution.md`
- `docs/audit/shrine-position/niigata-h001-aomi-jinja-position-resolution.md`
- `docs/audit/shrine-position/niigata-h001-aoyama-inari-jinja-position-resolution.md`

These records are the G2 current-state evidence. The Position Contract remains the rule authority.

## Candidate Master / lifecycle boundary

No Candidate Master field is changed in this G2 re-entry PR.

Current lifecycle state remains authoritative in Candidate Master and is not rewritten by this
Position audit.

G2 PASS does not mean BUILD_READY, FACT_READY, imported, or CORE_READY.

Position status is kept in the Position Resolution Record, not pushed into
`candidate_status`.

## Downstream Gate boundary

```text
nsrc-000002 -> G3 eligible after this G2 re-entry record is merged
nsrc-000004 -> downstream gates already progressed separately
nsrc-000005 -> G3 HOLD / source wait tracked separately

nsrc-000001 -> G2 HOLD
nsrc-000003 -> G2 HOLD
```

Do not execute G3 for the two G2 HOLD Candidates.

## STOP

This task stops at G2. No Source / Knowledge Model Fit, Base Seed, Production import, or
Recommendation change is executed here.
