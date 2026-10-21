# NIIGATA-001-VPG002 — Map Screenshot Address Evidence (read-only)

## 1. Scope
- Recorded: 2026-10-21
- Base: `develop@18690407b7ebb757c205a40d11402810074cf906`
- Evidence: two screenshots **supplied by Mother Ship** in the conversation on 2026-10-21, showing Google Maps detail cards and map pins for 旦飯野神社 and 淡島神社. Screenshots are conversation attachments, **not** repository files; this audit documents the observed UI text rather than embedding images.
- Authority: [VPG002 G1 evidence reassessment](niigata-vpg002-g1-evidence-reassessment.md), [VPG002 Production collision read-only audit](niigata-vpg002-production-collision-readonly.md), [G1 gate contract](../knowledge/shrine-expansion-gate-contract.md) §4.
- No user-supplied screenshot of the Render Environment / DATABASE_URL was provided.

## 2. Screenshots: observed facts and limits

| Source row | Shrine | Google Maps card address (screenshot) | Previously frozen Ready Set address | Independent primary evidence |
| --- | --- | --- | --- | --- |
| page004-row009 | 旦飯野神社 | 〒959-1947 新潟県阿賀野市宮下968番地 | 阿賀野市宮下195番地 | Shrine's official visitor/mail address = 宮下968; 神社庁/city/corporate location = 宮下195 |
| page009-row003 | 淡島神社 | 〒959-2632 新潟県胎内市新栄町5-3601-2 | 胎内市新栄町5番90号 | Cultural-property record for 淡島神社拝殿 = 新栄町3601-2; shrine registry listing = 新栄町5番90号 |

**Evidence classification:** `USER_PROVIDED_GOOGLE_MAPS_SCREENSHOT`. It is an observed third-party place-card display at the time of submission, not a proof of legal parcel boundaries, precise coordinate ownership, postal/lot equivalence, or a shrine-issued identity declaration. The pin positions are visible but were not independently measured or adopted as G2 coordinates.

For **旦飯野神社**, the Maps display corroborates the shrine-operator's own access-address form. For **淡島神社**, the map address appears to combine a `5-` prefix with `3601-2`; do **not** assert byte-identical equality with the cultural-property record's `新栄町3601-2`. Further municipality/registry confirmation would be required to prove site equivalence.

## 3. Source and address decision boundary

- Keep `阿賀野市宮下195番地` and `胎内市新栄町5番90号` **unchanged** in the frozen Ready Set.
- Candidate-level representation proposal only (NOT Mother Ship approval): treat 旦飯野 `宮下195` as registry address and `宮下968` as official shrine-operator access/mail address; treat 淡島 `新栄町5番90号` as registered shrine listing, and `新栄町3601-2` as cultural-property building location.
- Do not overwrite canonical identity fields or treat the two different strings as verified equivalent addresses. Mother Ship has **not yet issued** the final address adoption decision for VPG002.
- G1 formal PASS remains **not granted** for either shrine; other three candidates likewise remain without a formal G1 decision. H015 G0-registration contract remains unresolved.

## 4. Render database linkage

- Render `jinja-backend` service metadata was confirmed on 2026-10-21.
- Earlier Mother Ship audit records `DATABASE_URL` project ref matching the connected Supabase `uigvlbwnsthqqklzpfml` on 2026-10-08.
- Current Render service metadata **does not expose a secure current `DATABASE_URL` target identity**; neither the current runtime connection nor environment-variable target was independently reverified.
- No DB credential, full URI, hostname, password or environment secret is reproduced. Do not use a public screenshot containing secrets as evidence.

```text
CURRENT_RENDER_DATABASE_URL_REFERENCE = NOT_REVERIFIED
ASAIINO_MAP_DISPLAY_ADDRESS           = 阿賀野市宮下968番地 (USER_SCREENSHOT)
AWASHIMA_MAP_DISPLAY_ADDRESS          = 胎内市新栄町5-3601-2 (USER_SCREENSHOT)
FROZEN_READY_SET_ADDRESSES            = UNCHANGED
MOTHER_SHIP_CANONICAL_ADDRESS_DECISION= NOT_RECORDED
VPG002_MEMBERSHIP_FREEZE              = NOT_RECORDED
G1_PASS                               = NONE
G0_ADMISSION                          = NONE
G2_POSITION_ADOPTION                  = NONE
DB_PRODUCTION_SEED_RUNTIME_WRITE      = NONE
STOP                                  = TRUE
```

## 5. Next authority
1. Mother Ship may decide whether to **preserve dual-address metadata, without changing frozen Source**; approval must specify whether it is an identity annotation only or an actual schema/update task.
2. Independent evidence must establish any same-site relation asserted for 淡島.
3. Verify current Render-to-Supabase link by a safe identity-only attestation before claiming a current Production G1 DB inspection.
4. Resolve H015 contract before any sibling G0 registration; conduct separate G1 formal decision, do not auto-pass from screenshots.

This PR adds this audit record only; no existing audits, contracts, Candidate Master, tests, fixtures, DB, or runtime are changed.
