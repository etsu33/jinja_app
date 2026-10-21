# NIIGATA-001-VPG002 G1 evidence reassessment (read-only)

Recorded 2026-10-21. Base `develop@45fb7fbb4c72af1c89dceaa1072fd6fcf60d074a`. Prior records: [VPG002 G1 preflight](niigata-vpg002-g1-preflight.md) and [connected-DB collision audit](niigata-vpg002-production-collision-readonly.md).

## 1. Active Render DATABASE_URL linkage

- Render service `jinja-backend` (ID `srv-d4sk1uscjiac739ko5r0`) is a live web service deployed from `etsu33/jinja_app` branch `develop`.
- The connected Supabase project `kami-musubi-db` (`uigvlbwnsthqqklzpfml`) is the DB queried in the preceding read-only audit; the Render workspace has no Render-hosted Postgres instance.
- [Earlier Mother Ship audit](shrine-expansion-wave0-db05-sunosaki-g1-decision.md) records that the Render DATABASE_URL's **Supabase project ID** matched `uigvlbwnsthqqklzpfml` based on a 2026-10-08 screenshot supplied by Mother Ship. Do not expose a DSN or its secret components.
- The available Render connector supplies service metadata but does **not** expose a secure *identity-only* read of the current DATABASE_URL target. Therefore today's active environment linkage cannot be newly verified. Do **not** infer its unchanged status from the previous audit.

```text
PREVIOUS_PRODUCTION_LINK_IDENTITY = VERIFIED_BY_MOTHER_SHIP_2026-10-08
CONNECTED_DB_PROJECT             = uigvlbwnsthqqklzpfml
CURRENT_RENDER_DATABASE_URL_ID   = NOT_REVERIFIED
```

## 2. Address evidence: direct sources

### 旦飯野神社 (page004-row009)

Directly opened 2026-10-21:

- New潟県神社庁 official listing, 阿賀野市, `宮下195番地`: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15223
- 阿賀野市 official listing `宮下195`, phone `0250-62-4755`: https://www.city.agano.niigata.jp/soshiki/shokokankoka/rekishi_bunkazai/1/2251.html
- Official shrine website access address `宮下968`, phone `0250-62-4755`: https://asaiino-jinja.or.jp/
- Shrine's official mailing instruction PDF `宮下968番地`: https://asaiino-jinja.or.jp/wp-content/themes/asaino/assets/images/pdf/pdf_flyer_02_r4.pdf
- Government corporate information (gBizINFO), entity `旦飯野神社`, registered principal office `宮下195番地`: https://info.gbiz.go.jp/hojin/ichiran?hojinBango=5110005003817

**Finding:** both addresses have authoritative but **different usage contexts**. Name, municipality and shrine-contact phone match across official shrine and city pages. The conflict is no longer merely a weak tourism search snippet or demonstrated typo. Preserve the frozen 神社庁 address as a **鎮座地/registry designation**, and the shrine-operator website address as a **visitor/mail address**. These are not interchangeable fields. Parcel boundaries/physical-site equivalence are not independently proven, and no canonical_address rewrite is authorized.

```text
ASAIINO_ADDRESS_RECONCILIATION = CONTEXTS_IDENTIFIED / CANONICAL_DECISION_PENDING
FROZEN_ADDRESS                = 阿賀野市宮下195番地 (UNCHANGED)
SHRINE_ACCESS_ADDRESS         = 阿賀野市宮下968 (independently sourced)
```

### 淡島神社 (page009-row003)

- 新潟県神社庁 official listing of 胎内市: `胎内市新栄町5番90号`: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15227
- 文化遺産オンライン listing for **淡島神社拝殿** (a building), owner/management field `淡島神社`, `胎内市新栄町3601-2`: https://online.bunka.go.jp/heritages/detail/541511

**Finding:** the strings refer to distinct **record types**: shrine listed location versus designated cultural-property building location. The record does **not** prove their geospatial equivalence or the correct canonical address for application identity. Frozen address remains unchanged.

```text
AWASHIMA_ADDRESS_RECONCILIATION = DISTINCT_RECORD_CONTEXTS / SITE_EQUIVALENCE_UNVERIFIED
FROZEN_ADDRESS                  = 胎内市新栄町5番90号 (UNCHANGED)
CULTURAL_BUILDING_ADDRESS       = 胎内市新栄町3601-2
```

## 3. H015 contract

The existing test file `backend/temples/tests/test_shrine_expansion_candidate_master.py` contains a VPG001 membership integrity negative test `vpg001-source-handoff-sibling-registered`. It injects **H015 page008-row001** `nsrc-000026` into Candidate Master and expects a VPG001 group-contract violation. The VPG001-specific frozen processing group has page008-row003 (`nsrc-000021`) as its sole chosen H015 source row.

**Distinction:** NIIGATA-001-H015 is the immutable five-row **Source provenance handoff**; NIIGATA-001-VPG001 is a **processing selection** of one source row. The negative test verifies the VPG001 processing-group registration invariant in today's implementation. It must not silently be interpreted as a permanent general prohibition on ever adding another source row under H015. Still, admitting page008-row001 today **would violate the current test**. A future VPG002 membership/registration design must explicitly preserve the historical VPG001 five selected identities while accommodating independent processing selections, with contract-level review and regression tests in a separate implementation PR. No test relaxation or production write here.

```text
H015_SOURCE_MEMBERSHIP    = IMMUTABLE
VPG001_SELECTED_MEMBER    = page008-row003
VPG002_PROPOSED_MEMBER    = page008-row001
CURRENT_TEST_CONFLICT     = YES, IF ADMITTED WITHOUT CONTRACT CHANGE
CONTRACT_CHANGE_APPROVED  = NO
```

## 4. G1 per candidate, evidence-based assessment

The previous SELECT probe on the connected Supabase project found **zero probed-name/address rows** for 赤塚・旦飯野・淺原・淡島 and one `temples_shrine.id=135` 荒川神社 located at **胎内市桃崎浜187番地**, rather than the proposed 村上市小岩内463番地. This was a bounded query; the active Render DATABASE_URL linkage has not been re-verified on 2026-10-21.

| Candidate | Evidence assessment | G1 formal gate |
| --- | --- | --- |
| 赤塚神社 (page003-row003) | No tested DB collision; historical 神明社 / 船江神社 alias/identity relation remains unproven | NOT_VERIFIED |
| 旦飯野神社 (page004-row009) | `宮下195` registry/municipal/corporate and `宮下968` operator access/mail contexts independently substantiated; canonical identity handling requires explicit decision | HOLD |
| 淺原神社 (page005-row002) | No tested DB collision; 王子権現 historical-name scope needs evidence classification | NOT_VERIFIED |
| 荒川神社 (page008-row001) | Matched one same-name, different-city/different-address row at connected DB `temples_shrine.id=135`; H015 contract change dependency | NOT_VERIFIED / CONTRACT_BLOCKED_FOR_G0 |
| 淡島神社 (page009-row003) | `新栄町5番90号` shrine listing and `新栄町3601-2` listed building; equivalence not proven | HOLD |

No G1 PASS assigned. G0 membership is not frozen. No Product Surface, G2/G3 or Production advancement is authorized. Mother Ship must decide the canonical identity/address treatment per candidate *after* unresolved evidence and contract questions are cleared.

## 5. Proposed later handoff and STOP

1. Safely re-verify the current Render `DATABASE_URL` target **project ID only**, without copying the URI, credentials, host, or environment-variable value into chat, logs or PRs. If a secure metadata-only view is unavailable, record `UNVERIFIED`.
2. Resolve 淡島神社 location equivalence with municipal property/registry evidence. For 旦飯野神社, distinguish shrine's own access address from official registration address in a candidate-level canonical-address decision.
3. Model VPG002 processing-group membership separately from existing immutable Source handoffs and frozen VPG001 selected five rows; regression-test planned sibling registration in a dedicated PR before admitting H015 page008-row001.
4. Conduct formal Mother Ship G1 classifications after the above, not by inference from a no-collision query.

```text
CHANGE_SCOPE                 = THIS_DOCUMENT_ONLY
EXISTING_AUDITS              = UNCHANGED
CANDIDATE_MASTER_AND_FIXTURES= UNCHANGED
DB_SEEDS_RUNTIME_PRODUCTION  = UNCHANGED
G1_PASS                     = NONE
STOP                        = TRUE
```
