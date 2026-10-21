# NIIGATA-001-VPG002 G1 Identity / Duplicate Preflight（read-only）

## 1. Status

```text
scope                     = 5 frozen Ready Set rows（below）; read-only preflight
VPG002 membership record  = NOT_FOUND in repository（no freeze / G0 record exists）
G0 admission              = NOT PERFORMED（no nsrc-* ID, no Candidate Master row）
Production DB access      = NOT AVAILABLE in this environment
PRODUCTION_G1_COLLISION   = NOT_VERIFIED（SELECT-only query proposed in §6）

per candidate（§7）:
  page003-row003 赤塚神社    = NOT_VERIFIED
  page004-row009 旦飯野神社  = HOLD（address conflict 宮下195 vs 宮下968）
  page005-row002 淺原神社    = NOT_VERIFIED
  page008-row001 荒川神社    = NOT_VERIFIED
  page009-row003 淡島神社    = HOLD（address conflict 新栄町5番90号 vs 新栄町3601-2）

G1 PASS                   = NONE（no Production verification; no Mother Ship decision）
Production / Seed / Candidate Master / DB / migration / runtime write = NONE
```

- Recorded at: 2026-10-21
- Base: `origin/develop@caa682c`
- This is a read-only **preflight**. It does not admit any candidate at G0, does not assign `nsrc-*` IDs, and
  does not record a G1 PASS. Without a current Production check it cannot claim
  "no Production collision".

Evidence labels:

- **VERIFIED_REPO**: confirmed from merged repository records or data files at this base.
- **SEARCH_SUMMARY**: seen only in web-search result text on 2026-10-21. The page itself was not opened.
  Not an accepted Source.
- **DERIVED**: follows from merged records. It is not a fresh Production measurement.
- **HYPOTHESIS**: a possible explanation, not established.

---

## 2. Authority

- [`niigata-batch001-ready-set-freeze.md`](niigata-batch001-ready-set-freeze.md)（frozen NIIGATA-001 Ready Set, 100 rows）
- [`niigata-001-expansion-priority-screening.md`](niigata-001-expansion-priority-screening.md)（screening rows and [S1]–[S11]）
- [`../knowledge/shrine-expansion-gate-contract.md`](../knowledge/shrine-expansion-gate-contract.md) §4 G1 Identity / Duplicate Gate
- [`../knowledge/shrine-expansion-candidate-master-contract.md`](../knowledge/shrine-expansion-candidate-master-contract.md)（schema 1.4 Nationwide Source Track）
- [`niigata-vpg001-g1-identity-duplicate.md`](niigata-vpg001-g1-identity-duplicate.md)（precedent）
- `backend/temples/data/shrine_expansion_candidate_master.json`, `shrines_seed_clean.json`,
  `shrine_expansion_nationwide_identity_manifest.json`, `knowledge_seeds/*.json`

G1 PASS conditions（gate contract §4）:

- the canonical identity can be explained;
- duplicate / alias / same-name-different-shrine are classified;
- any collision with an existing Production row can be explained.

STOP conditions include: identity ambiguous, duplicate relation unresolved, and a same-name shrine
treated as identical without an address.

---

## 3. Targets（frozen Ready Set, VERIFIED_REPO）

| handoff | source_position | raw_name | frozen raw_address | Ready Set state | screening |
| --- | --- | --- | --- | --- | --- |
| NIIGATA-001-H005 | page003-row003 | 赤塚神社 | 新潟市西区赤塚2709番地 | RUNNER_READY | PRIORITY_B |
| NIIGATA-001-H008 | page004-row009 | 旦飯野神社 | 阿賀野市宮下195番地 | RUNNER_READY | PRIORITY_B |
| NIIGATA-001-H009 | page005-row002 | 淺原神社 | 小千谷市片貝町6548番地 | RUNNER_READY | PRIORITY_B |
| NIIGATA-001-H015 | page008-row001 | 荒川神社 | 村上市小岩内463番地 | RUNNER_READY | PRIORITY_B |
| NIIGATA-001-H017 | page009-row003 | 淡島神社 | 胎内市新栄町5番90号 | RUNNER_READY | PRIORITY_B |

Frozen Ready Set provenance（all rows）: NIIGATA-001 snapshot of
`https://niigata-jinjacho.jp/shrine_niigata/search.php`
（`source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380`）.

No repository record defines "NIIGATA-001-VPG002". This preflight uses the five rows named in the
request. The membership itself is a Mother Ship decision（§8, D1）.

---

## 4. Repository comparison（VERIFIED_REPO）

Normalization: NFKC with all whitespace removed. For addresses, a leading 新潟県 is also removed.

### 4.1 Frozen Ready Set（100 rows）

| target | same name, other address | same address, other name | same address fragment |
| --- | --- | --- | --- |
| 赤塚神社 / 新潟市西区赤塚2709番地 | none | none | none |
| 旦飯野神社 / 阿賀野市宮下195番地 | **page004-row010 旦飯野神社 / 新潟市秋葉区朝日535番地**（H008, PRIORITY_C） | none | none |
| 淺原神社 / 小千谷市片貝町6548番地 | none | none | none |
| 荒川神社 / 村上市小岩内463番地 | page007-row010 新発田市荒川5431番地; page008-row002 村上市荒川542番地; **page008-row003 胎内市桃崎浜187番地（= nsrc-000021）** | none | none |
| 淡島神社 / 胎内市新栄町5番90号 | none | none | none |

### 4.2 Other repository data

| data | result |
| --- | --- |
| Candidate Master（69 rows） | No target position is registered. The only same-name row is **nsrc-000021 荒川神社 / 胎内市桃崎浜187番地**（CORE_READY）. 若宮神明社（wave0-043）matches the alias probe "神明社" only and is unrelated. |
| Base Seed（133 rows） | Only same-name row: **荒川神社 / 新潟県胎内市桃崎浜187番地**（nsrc-000021）. 王子神社 / 東京都北区 matches only an alias probe and is unrelated. No same-address or same-fragment row for any target. |
| Nationwide identity manifest | 荒川神社 appears only as the nsrc-000021 identity. None of the five frozen addresses appears. |
| Knowledge Seeds | 荒川神社 appears only in `nsrc_000021_seed.json`. None of the five frozen addresses appears. |

Alias probes run against the Candidate Master and Base Seed: 浅原神社 / 淺原社 / 王子権現 / 王子神社;
粟島神社 / 淡嶋神社 / 粟嶋神社 / 淡島社; 旦飯野社 / 朝飯野神社; 神明社 / 船江神社 / 赤塚社; 荒川社.
No relevant hit.

### 4.3 荒川神社: two rows are not equated

```text
target       荒川神社 / 村上市小岩内463番地（page008-row001, H015）
nsrc-000021  荒川神社 / 胎内市桃崎浜187番地（page008-row003, H015; G1 SAME_NAME_DIFFERENT_SHRINE, now CORE_READY）
```

The two rows are in different municipalities, at different addresses, and are separate Source rows. The
VPG001 G1 record already lists 村上市小岩内463番地 among the "other-address" 荒川神社 identities that do
**not** identify nsrc-000021. The name match alone is not evidence that they are the same shrine.

---

## 5. Address reconciliation

### 5.1 旦飯野神社: 宮下195 vs 宮下968

| address | source | level |
| --- | --- | --- |
| 阿賀野市宮下195番地 | frozen Ready Set（新潟県神社庁 snapshot） | VERIFIED_REPO |
| 阿賀野市宮下968 | 新潟県観光協会 spot/42269 and blog/37（screening [S3]）; also in tenki.jp results | SEARCH_SUMMARY（2026-10-21） |

- The difference is confirmed: the frozen address is 宮下**195**番地, and the tourism sources give 宮下**968**.
  The screening record had already noted "lot 宮下195 not in source".
- The tourism sources describe 祭神 誉田別命, at the current site since 寛政4（1792）, with hereditary 鈴木氏
  priests. That is the same shrine description the screening attributed to page004-row009.
- HYPOTHESIS（not established）: the two numbers may be different lots of the same precinct, or one may be
  a 社務所 / registered vs postal address. Two other explanations have not been ruled out: an address
  error, or a different shrine.
- A second Ready Set row 旦飯野神社 / 新潟市秋葉区朝日535番地（page004-row010）is in another municipality.
  The screening found only the 阿賀野 shrine for it. It is a separate Source row and is not merged.

```text
旦飯野神社 address = CONFLICT（unresolved）
```

### 5.2 淡島神社: 新栄町5番90号 vs 新栄町3601-2

| address | source | level |
| --- | --- | --- |
| 胎内市新栄町5番90号 | frozen Ready Set（新潟県神社庁 snapshot） | VERIFIED_REPO |
| 胎内市新栄町3601-2 | 文化遺産オンライン 淡島神社拝殿（登録有形文化財）（screening [S9]） | SEARCH_SUMMARY（2026-10-21）; already flagged in screening: "G1 must reconcile" |

- The difference is confirmed.
- HYPOTHESIS（not established）: "5番90号" reads like a 住居表示 address and "3601-2" like a 地番, so both
  could denote the same site. A different 淡島神社 in 新栄町 has not been ruled out.
- The cultural-property record names a **building**（拝殿）. Even if the site matches, it is an
  attribute of a shrine and not by itself the shrine's identity.

```text
淡島神社 address = CONFLICT（unresolved）
```

### 5.3 Other targets

| target | open identity question | level |
| --- | --- | --- |
| 赤塚神社 | Screening: relation to 赤塚の神明社（伝・船江神社, 式内）not confirmed. Possible alias / predecessor relation | HYPOTHESIS |
| 淺原神社 | Screening: called 王子権現 in the 神仏習合 era. A historical name, not a current alias of another Production row | HYPOTHESIS |
| 荒川神社（小岩内） | founding is oral tradition; 式内社 claim not cross-checked（[S7] 村上市 PDF citing 神林村誌）. Not an identity conflict | — |

---

## 6. Production comparison（NOT_VERIFIED）

This environment has no Production DB access, so no current Production result is claimed.

What merged records already establish（DERIVED, not re-measured）:

- On 2026-10-18 the VPG001 G1 Production inspection found 129 Shrine rows, 2 ShrineCandidate rows and
  no 荒川神社. The five VPG002 rows were not part of that query.
- VPG001 G7 then imported 荒川神社 / 新潟県胎内市桃崎浜187番地（G7 P5: Shrine = 133）. Current Production is
  therefore expected to contain **one** 荒川神社 at a different address from the VPG002 target. If that
  holds, it is a same-name-other-address row to explain, not a duplicate.
- The 2026-10-08 runner lookup（Production, 120 rows）returned RUNNER_READY for all five. It did not check
  `temples_shrinecandidate`, NFKC, aliases or old municipality names, and Production has changed since.

Proposed SELECT-only inspection for Mother Ship, to run through `scripts/migration_safety/readonly_query.sh`.
It follows the VPG001 pattern. It is shown here only and **not** added as a script file in this
docs-only PR（§8, D2）:

```sql
-- NIIGATA-001-VPG002 G1 collision inspection (read-only). SELECT / WITH only.
WITH
targets (source_position, name_jp, frozen_address) AS (
  VALUES
    ('page003-row003', '赤塚神社',   '新潟市西区赤塚2709番地'),
    ('page004-row009', '旦飯野神社', '阿賀野市宮下195番地'),
    ('page005-row002', '淺原神社',   '小千谷市片貝町6548番地'),
    ('page008-row001', '荒川神社',   '村上市小岩内463番地'),
    ('page009-row003', '淡島神社',   '胎内市新栄町5番90号')
),
t AS (
  SELECT source_position,
         regexp_replace(normalize(name_jp, NFKC), '[[:space:]]', '', 'g') AS name_key,
         regexp_replace(regexp_replace(normalize(frozen_address, NFKC), '[[:space:]]', '', 'g'), '^新潟県', '') AS address_key
  FROM targets
),
rows AS (
  SELECT 'temples_shrine' AS tbl,
         regexp_replace(normalize(name_jp, NFKC), '[[:space:]]', '', 'g') AS name_key,
         regexp_replace(regexp_replace(normalize(COALESCE(address, ''), NFKC), '[[:space:]]', '', 'g'), '^新潟県', '') AS address_key
  FROM temples_shrine
  UNION ALL
  SELECT 'temples_shrinecandidate',
         regexp_replace(normalize(name_jp, NFKC), '[[:space:]]', '', 'g'),
         regexp_replace(regexp_replace(normalize(COALESCE(address, ''), NFKC), '[[:space:]]', '', 'g'), '^新潟県', '')
  FROM temples_shrinecandidate
)
SELECT t.source_position, r.tbl,
       COUNT(*) FILTER (WHERE r.name_key = t.name_key AND r.address_key = t.address_key) AS exact_identity,
       COUNT(*) FILTER (WHERE r.name_key = t.name_key AND r.address_key <> t.address_key) AS same_name_other_address,
       COUNT(*) FILTER (WHERE r.name_key <> t.name_key AND r.address_key = t.address_key) AS same_address_other_name,
       COUNT(*) FILTER (WHERE r.address_key LIKE '%' || split_part(t.address_key, '町', 1) || '%'
                          AND r.name_key <> t.name_key) AS same_area_other_name
FROM t CROSS JOIN rows r
GROUP BY t.source_position, r.tbl
ORDER BY t.source_position, r.tbl;
```

Before it is used:

- **Columns:** `temples_shrinecandidate.name_jp` / `address` are the columns the merged
  `niigata_vpg001_g1_collision_inspection.sql` already reads.
- **Aliases:** extend the probe to cover 宮下968, 新栄町3601-2, 浅原, 粟島 and 王子権現.
- **Diagnostics:** list the matching rows as diagnostics, not only counts.
- **Fragment counter:** the `same_area_other_name` column is a coarse diagnostic only, not a G1 criterion.

```text
PRODUCTION_G1_COLLISION = NOT_VERIFIED ×5
```

---

## 7. Per-candidate result

| source_position | name / frozen address | repository | Production | open conflict | result |
| --- | --- | --- | --- | --- | --- |
| page003-row003 | 赤塚神社 / 新潟市西区赤塚2709番地 | no collision | NOT_VERIFIED | 神明社 / 船江神社 relation（HYPOTHESIS） | **NOT_VERIFIED** |
| page004-row009 | 旦飯野神社 / 阿賀野市宮下195番地 | no Candidate Master / Base Seed collision; another Ready Set row at 秋葉区朝日535 | NOT_VERIFIED | 宮下195 vs 宮下968 | **HOLD** |
| page005-row002 | 淺原神社 / 小千谷市片貝町6548番地 | no collision | NOT_VERIFIED | historical name 王子権現（HYPOTHESIS） | **NOT_VERIFIED** |
| page008-row001 | 荒川神社 / 村上市小岩内463番地 | same name at 胎内市桃崎浜187番地（nsrc-000021）; not equated | NOT_VERIFIED（expected same_name_other_address = 1, DERIVED） | none beyond explaining nsrc-000021 | **NOT_VERIFIED** |
| page009-row003 | 淡島神社 / 胎内市新栄町5番90号 | no collision | NOT_VERIFIED | 新栄町5番90号 vs 3601-2 | **HOLD** |

How the results are assigned:

- **PASS:** not assigned to any candidate. It needs both an explained Production comparison and a Mother
  Ship G1 decision.
- **HOLD:** an identity / address conflict exists that G1 must resolve before any classification.
- **NOT_VERIFIED:** the repository is clean, but the Production comparison has not been run.

---

## 8. Mother Ship decision list

| id | decision | why it is needed |
| --- | --- | --- |
| D1 | Freeze VPG002 membership（these five rows, or another set）in a membership record | no repository record defines VPG002 |
| D2 | Approve the SELECT-only collision SQL, as a script file in a follow-up PR or as shown in §6, and run it through `readonly_query.sh` | without it no candidate can pass G1 |
| D3 | 旦飯野神社: choose the canonical address（宮下195番地 frozen vs 宮下968 tourism）, or require a primary source（神社庁 detail page, 阿賀野市 record, shrine notice） | address conflict blocks the canonical identity |
| D4 | 淡島神社: decide whether 新栄町3601-2（cultural-property 地番）and 新栄町5番90号（frozen）are the same site, on primary evidence | address conflict blocks the canonical identity |
| D5 | 荒川神社: after the Production run, classify the relation to nsrc-000021（expected SAME_NAME_DIFFERENT_SHRINE; not equated by name） | collision must be explained |
| D6 | 赤塚神社: decide whether the 神明社 / 船江神社 relation is an identity question for G1 or a history question for G3 | alias scope |
| D7 | 淺原神社: confirm 王子権現 is treated as a historical name, not a current alias | alias scope |
| D8 | **H015 handoff boundary**: page008-row001 belongs to NIIGATA-001-H015, the same Source handoff as nsrc-000021. Current tests assert that page008-row003 is the only registered H015 row; the VPG001 mutation `vpg001-source-handoff-sibling-registered` registers exactly page008-row001 and expects a contract violation. Admitting this row at G0 needs an explicit decision and a matching test / contract update in that G0 PR | prevents an accidental contract break at G0 |
| D9 | Classify each candidate（NEW / SAME_NAME_DIFFERENT_SHRINE / DUPLICATE / HOLD）after D2–D7 | the G1 decision itself |

---

## 9. Sources

Repository（VERIFIED_REPO）: §2 authority files.

Web search on 2026-10-21（SEARCH_SUMMARY; pages not opened; not accepted Sources）:

- 新潟県観光協会 旦飯野神社: https://niigata-kankou.or.jp/spot/42269 ; https://niigata-kankou.or.jp/blog/37
- tenki.jp 旦飯野神社: https://tenki.jp/lite/leisure/4/18/116/46554/
- 文化遺産オンライン 胎内市: https://online.bunka.go.jp/heritages/region/15/15227

Screening sources already in the repository: [S1] 新潟市 西区, [S3] 新潟県観光協会, [S4] tourism / JR East,
[S7] 村上市 PDF, [S9] 文化遺産オンライン（URLs in the screening record）.

---

## 10. Not done

```text
G0 admission / nsrc-* ID assignment        NONE
G1 PASS / duplicate classification         NONE（Mother Ship, after D2）
Production query                           NOT EXECUTED（no access）
SQL script file                            NOT ADDED（docs-only; D2）
Candidate Master / fixtures / Seeds / DB / migrations / Knowledge / Ranking / Recommendation / runtime   UNCHANGED
existing audit records                     UNCHANGED
```
