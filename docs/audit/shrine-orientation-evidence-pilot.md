# Shrine Orientation Evidence Pilot — 5 Shrines

## Status

- Status: `EXECUTED_EVIDENCE_ACQUISITION_BLOCKED`
- Recorded at: `2026-09-23`
- Pilot Shrines: 5
- Layer decisions: 15
- Production write: `NONE`
- Base Seed write: `NONE`
- Shrine model change: `NONE`
- Position Contract change: `NONE`
- Recommendation / Compass logic change: `NONE`
- Orientation Evidence Contract created: `NO`

本書は Contract ではない。`docs/knowledge/shrine-position-contract.md` の authority は
変更されない。

## 0. Executive Result

The pilot ran to completion against its own rules. It did not acquire evidence.

```text
PRIMARY_SOURCE_HOSTS_TESTED   = 22
PRIMARY_SOURCE_HOSTS_REACHED  = 0
PRIMARY_SOURCE_DOCUMENTS_READ = 0
CONFIRMED_CELLS               = 0 / 15
```

Every host in every tier of the Primary evidence policy — 文化庁 databases, 自治体
文化財資料, 公的研究機関, and all five 神社公式 sites — returned `403` at the session's
network egress gateway. The corroboration tier (国土地理院, map providers) is blocked
by the same policy.

This is an **environment constraint, not an evidence finding.** The pilot therefore
cannot report whether shrine orientation is reproducibly collectible from published
cultural-property evidence, because it could not open a single such document.

```text
ORIENTATION_EVIDENCE_PIPELINE = NOT_DETERMINED_IN_THIS_ENVIRONMENT
```

§10 records why none of `VIABLE` / `PARTIALLY_VIABLE` / `NOT_YET_VIABLE` can be
honestly selected, and what is required to run the pilot as specified.

## 1. Scope and Non-Goals

Purpose: test whether shrine orientation can be collected reproducibly from published
cultural-property / architectural evidence **without inference**.

### Non-Goals (all observed)

- No Production, Base Seed, or Shrine model change.
- No change to `docs/knowledge/shrine-position-contract.md` or any existing Contract.
- No change to recommendation / compass logic.
- No symbolic meaning inferred from geometry.
- No ritual meaning inferred from map alignment.
- No formal Orientation Evidence Contract created.

### Pilot Shrines

```text
1. 伏見稲荷大社
2. 日光東照宮
3. 宇佐神宮
4. 春日大社
5. 建勲神社
```

## 2. Evidence Policy Applied

### 2.1 Preferred primary sources

```text
P-1  文化庁 国指定文化財等データベース
P-2  国・自治体・教育委員会等の文化財資料
P-3  公開された文化財修理報告 / 建築調査 / 実測図
P-4  大学・公的研究機関が公開する建築調査資料
P-5  神社公式の建築・境内・祭祀構造資料
```

### 2.2 Corroboration only

```text
国土地理院
shrine official map showing spatial relationships without stating orientation
map providers
aerial imagery
```

### 2.3 Not canonical evidence

```text
personal blogs / SNS / reviews / unsourced tourism articles
visual alignment interpreted without documentary support
```

### 2.4 Evidence strength

```text
E1_AUTHORITATIVE  cultural-property authority / government / shrine official direct statement
E2_SCHOLARLY      university / public research institution / specialist architectural research
E3_MEASURED       official or scholarly measured drawing / plan / GIS-quality spatial evidence
E4_CORROBORATION  map / aerial imagery / non-semantic spatial corroboration
```

`E4` alone is not admissible for `RITUAL_AXIS` or `SYMBOLIC_ORIENTATION`.

### 2.5 Governing rule

```text
GEOMETRY PROVES DIRECTION.
DOCUMENTARY EVIDENCE PROVES MEANING.
```

`SYMBOLIC_ORIENTATION` is never derived from `PHYSICAL_ORIENTATION`.

### 2.6 Layer status values

```text
CONFIRMED                accepted source directly supports the claim
NOT_DETERMINED           available evidence does not establish the claim
HOLD_ORIENTATION_REVIEW  accepted sources provide competing or materially ambiguous claims
```

Missing evidence is **not** `HOLD`. `HOLD` requires two or more accepted sources in
conflict. No cell in this pilot reaches that condition, because no accepted source was
read at all.

### 2.7 Retrieval-status qualifier (added by this pilot)

The specified status set cannot distinguish two materially different situations that
both land on `NOT_DETERMINED`:

```text
EVIDENCE_INSUFFICIENT  the source was read and does not establish the claim
SOURCE_UNRETRIEVED     the source was identified but could not be opened
```

This pilot records the qualifier alongside each `NOT_DETERMINED`. It does not change
any cell's status value, and it does not introduce a fourth status. All 15 cells in
this run carry `SOURCE_UNRETRIEVED`; none carries `EVIDENCE_INSUFFICIENT`.

The distinction matters for §10: `NOT_YET_VIABLE` is a statement about sources, and
`SOURCE_UNRETRIEVED` says nothing about sources.

## 3. Evidence Acquisition Attempt — Result

### 3.1 Network egress outcome

All outbound HTTPS in this session passes through a policy-enforcing egress gateway.
Every candidate evidence host was refused at `CONNECT`.

```text
gateway response  = 403
proxy failure kind = connect_rejected
proxy detail       = "gateway answered 403 to CONNECT (policy denial or upstream failure)"
observed at        = 2026-09-23T01:21:36Z – 2026-09-23T01:23Z
```

Per the session's egress documentation (`/root/.ccr/README.md`, §"403 / 407 from the
proxy"): *"The destination host is not allowed by your organization's egress policy for
this session. Do not retry or route around it — report the blocked host."* No retry,
mirror, cache, or alternate route was attempted.

### 3.2 Blocked host inventory

| # | Host | Evidence tier | Result |
| ---: | --- | --- | --- |
| 01 | `kunishitei.bunka.go.jp` | P-1 文化庁 国指定文化財等データベース | `403` |
| 02 | `online.bunka.go.jp` | P-1 文化遺産オンライン（文化庁） | `403` |
| 03 | `bunka.nii.ac.jp` | P-1 文化遺産オンライン（NII ミラー） | `403` |
| 04 | `www.bunka.go.jp` | P-1 文化庁 | `403` |
| 05 | `www.pref.nara.lg.jp` | P-2 奈良県 文化資源 | `403` |
| 06 | `www.pref.oita.jp` | P-2 大分県 | `403` |
| 07 | `www.city.usa.oita.jp` | P-2 宇佐市 | `403` |
| 08 | `www.city.nikko.lg.jp` | P-2 日光市 | `403` |
| 09 | `www2.city.kyoto.lg.jp` | P-2 京都市 | `403` |
| 10 | `oita-digitalzukan.jp` | P-2 おおいた文化財ずかん | `403` |
| 11 | `cir.nii.ac.jp` | P-4 CiNii Research | `403` |
| 12 | `inari.jp` | P-5 伏見稲荷大社 公式 | `403` |
| 13 | `www.toshogu.jp` | P-5 日光東照宮 公式 | `403` |
| 14 | `www.usajinguu.com` | P-5 宇佐神宮 公式 | `403` |
| 15 | `www.kasugataisha.or.jp` | P-5 春日大社 公式 | `403` |
| 16 | `kenkun-jinja.org` | P-5 建勲神社 公式 | `403` |
| 17 | `www.rinnoji.or.jp` | P-5 日光山輪王寺 公式（大猷院） | `403` |
| 18 | `www.gsi.go.jp` | Corroboration 国土地理院 | `403` |
| 19 | `ja.wikipedia.org` | Corroboration / lead-finding | `403` |
| 20 | `www.nikko-kankou.org` | Non-canonical (tested for completeness) | `403` |
| 21 | `www.millennium-roman.jp` | Non-canonical (tested for completeness) | `403` |
| 22 | `github.com` | Control host — not evidence | reachable |

```text
HOSTS_TESTED  = 22
BLOCKED       = 21
REACHABLE     = 1  (control host only; carries no orientation evidence)
```

The control host confirms the session has working egress and that the refusals are
per-host policy denials, not a general network failure.

### 3.3 What was reachable, and why it is not evidence

A relayed web-search service remained available and returned result listings. Those
listings were used **only to identify candidate source URLs** (§4). They were not used
as evidence, for three reasons:

1. A search-result summary is a third party's rendering of a document, not the
   document. Its provenance is the search service, which appears in no tier of §2.
2. The summaries could not be checked against the underlying records, because those
   records are on blocked hosts.
3. Two summaries already demonstrate the hazard concretely:
   - the 宇佐神宮 summary reproduced 桁行 / 梁間 / 八幡造 structural detail but contained
     **no cardinal orientation statement at all**, although the pilot brief reports the
     Cultural Affairs record states the three Honden face south;
   - the 春日大社 summary contained `東側から第一殿〜第四殿まで4つの棟が横に並んで`,
     an *arrangement* statement carried by a non-accepted site, which under §2.5 does
     not establish a facing direction.

Recording either as `CONFIRMED` would have manufactured an `E1` citation out of an
unverifiable intermediary. No such cell exists in §6.

## 4. Primary Source Inventory

Every row below is a **lead**, not evidence. The required inventory fields that depend
on reading the document (`publication / update date`, `covered structure`,
`exact factual claim supported`, `evidence strength`, `limitations`) cannot be
populated without the document, and are recorded as `NOT_RETRIEVED` rather than
guessed.

Column key: `Layer` = the layer the source is expected to bear on, from its title and
record type — an acquisition target, not a supported claim.

### 4.1 伏見稲荷大社

| source_title | source_owner | source_type | source_url | Layer target | source_status |
| --- | --- | --- | --- | --- | --- |
| 国指定文化財等データベース 伏見稲荷大社 本殿 | 文化庁 | P-1 cultural-property database | `https://kunishitei.bunka.go.jp/heritage/detail/102/00004715` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 伏見稲荷大社 楼門 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/232051` | A / B | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 伏見稲荷大社 権殿 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/232061` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 伏見稲荷大社 外拝殿 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/279510` | A / B | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 伏見稲荷大社 南北廻廊（南廻廊） | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/260102` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 伏見稲荷大社 白狐社 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/274693` | A | `NOT_RETRIEVED` (`403`) |
| 伏見稲荷大社 公式「本殿」 | 伏見稲荷大社 | P-5 shrine official | `https://inari.jp/sp/map/spot_03/` | A / B | `NOT_RETRIEVED` (`403`) |

Acquisition note from the brief, to be verified and not adopted: Cultural Affairs
material is reported to state the precinct sits on the west foot of 稲荷山 and faces
west. A precinct-facing statement is not a Honden-facing statement. Under §2.5 the
equivalence must be established by the document itself, and the document is unread.

### 4.2 日光東照宮

| source_title | source_owner | source_type | source_url | Layer target | source_status |
| --- | --- | --- | --- | --- | --- |
| 文化遺産オンライン 東照宮 陽明門 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/179105` | A | `NOT_RETRIEVED` (`403`) |
| 日光市 文化財 / 建造物資料 | 日光市 | P-2 | `https://www.city.nikko.lg.jp/` (entry point) | A / B / C | `NOT_RETRIEVED` (`403`) |
| 日光山輪王寺 公式「大猷院」 | 日光山輪王寺 | P-5 (separate institution) | `https://www.rinnoji.or.jp/history/temple/taiyuuin.html` | C (Taiyuin-side claim only) | `NOT_RETRIEVED` (`403`) |

Direction-of-claim note: the documented relationship reported in the brief is that
**Taiyuin buildings face toward Toshogu**. That is a claim about Taiyuin's orientation,
owned by Rinnoji material. It is not a claim about Toshogu's own orientation and must
not be reversed into one. No cell in §6 carries it.

### 4.3 宇佐神宮

| source_title | source_owner | source_type | source_url | Layer target | source_status |
| --- | --- | --- | --- | --- | --- |
| 文化遺産オンライン 宇佐神宮本殿 | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/110754` | A / B | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 宇佐神宮本殿（第一殿） | 文化庁 | P-1 | `https://online.bunka.go.jp/heritages/detail/187746` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 宇佐神宮本殿（第二殿） | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/124607` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 宇佐神宮境内 | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/206773` | A / B | `NOT_RETRIEVED` (`403`) |
| おおいた文化財ずかん 宇佐神宮本殿 | 大分県（自治体系） | P-2 | `https://oita-digitalzukan.jp/cultural_property/宇佐神宮本殿/` | A | `NOT_RETRIEVED` (`403`) |
| 宇佐神宮 公式「境内のご案内」 | 宇佐神宮 | P-5 | `http://www.usajinguu.com/guide/` | A / B | `NOT_RETRIEVED` (`403`) |

Acquisition note, to be verified and not adopted: the brief reports the Cultural
Affairs record states the three Honden face south and are arranged east-west. The
pilot's own question for that record — *does it prove `PHYSICAL_ORIENTATION` only, or
also a documented `RITUAL_AXIS`?* — is exactly the question that requires the record's
wording, which is unread.

### 4.4 春日大社

| source_title | source_owner | source_type | source_url | Layer target | source_status |
| --- | --- | --- | --- | --- | --- |
| 奈良県「春日大社本社本殿」 | 奈良県 | P-2 | `https://www.pref.nara.lg.jp/ikasu-nara/bunkashigen/main04201.html` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 春日大社本社 捻廊 | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/123547` | A | `NOT_RETRIEVED` (`403`) |
| 春日大社 公式（社殿・境内） | 春日大社 | P-5 | `https://www.kasugataisha.or.jp/` (entry point) | A / B | `NOT_RETRIEVED` (`403`) |

Language-version note: the brief permits multilingual shrine pages only where
provenance is clearly the same official shrine source, with the language/version
recorded. No shrine page in any language was retrievable, so the provision was never
exercised.

### 4.5 建勲神社

| source_title | source_owner | source_type | source_url | Layer target | source_status |
| --- | --- | --- | --- | --- | --- |
| 国指定文化財等データベース 建勲神社本殿 | 文化庁 | P-1 | `https://kunishitei.bunka.go.jp/heritage/detail/101/00007059` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 建勲神社本殿 | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/191780` | A | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 建勲神社祝詞舎 | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/172362` | A / B | `NOT_RETRIEVED` (`403`) |
| 文化遺産オンライン 建勲神社祭器庫 | 文化庁 | P-1 | `https://bunka.nii.ac.jp/heritages/detail/183276` | A | `NOT_RETRIEVED` (`403`) |
| 京都市「建勲神社本殿真御柱跡」 | 京都市 | P-2 | `https://www2.city.kyoto.lg.jp/somu/rekishi/fm/ishibumi/html/ki016.html` | A | `NOT_RETRIEVED` (`403`) |
| 建勲神社 公式「境内案内」 | 建勲神社 | P-5 | `https://kenkun-jinja.org/precincts/` | A / B | `NOT_RETRIEVED` (`403`) |

Acquisition note, to be verified and not adopted: the brief reports the Cultural
Affairs database describes the Honden as east-facing, and directs that Haiden and
precinct-related registered buildings also be inspected. The registered 祝詞舎 and
祭器庫 records were located as leads for that inspection; none was readable.

### 4.6 Inventory totals

```text
LEADS_IDENTIFIED            = 25
LEADS_RETRIEVED             =  0
PRIMARY_SOURCE_COUNT (read) =  0
CORROBORATION_COUNT (read)  =  0
```

## 5. Recorded Orientation Values

No `orientation_degrees`, `orientation_cardinal`, `orientation_reference`,
`orientation_subject`, `axis_from`, `axis_to`, `axis_direction`, `ritual_function`,
`symbolic_target`, `symbolic_claim`, or `claim_attribution` value is recorded by this
pilot, for any of the five shrines.

```text
ORIENTATION_VALUES_RECORDED = 0
```

The rule *"Do NOT invent degree values from prose"* was not exercised, because no prose
was obtained. The stricter rule that no value may be recorded without a read accepted
source governs instead.

## 6. 15-Cell Result Matrix

Five shrines × three layers. Every cell carries the retrieval qualifier from §2.7.

| # | Shrine | Layer | Status | Qualifier | Accepted source read | Basis |
| ---: | --- | --- | --- | --- | --- | --- |
| 01 | 伏見稲荷大社 | A `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | 7 leads identified (§4.1), all `403` |
| 02 | 伏見稲荷大社 | B `RITUAL_AXIS` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no read source; B may not rest on E4 |
| 03 | 伏見稲荷大社 | C `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no documentary claim obtained; geometry excluded by §2.5 |
| 04 | 日光東照宮 | A `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | 3 leads identified (§4.2), all `403` |
| 05 | 日光東照宮 | B `RITUAL_AXIS` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no read source; B may not rest on E4 |
| 06 | 日光東照宮 | C `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | the located Taiyuin→Toshogu claim is Taiyuin's orientation, unread, and not reversible (§4.2) |
| 07 | 宇佐神宮 | A `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | 6 leads identified (§4.3), all `403` |
| 08 | 宇佐神宮 | B `RITUAL_AXIS` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | the physical-vs-ritual question for this record requires its wording (§4.3) |
| 09 | 宇佐神宮 | C `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no documentary claim obtained; geometry excluded by §2.5 |
| 10 | 春日大社 | A `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | 3 leads identified (§4.4), all `403` |
| 11 | 春日大社 | B `RITUAL_AXIS` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no read source; four-Honden layout unverified |
| 12 | 春日大社 | C `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no documentary claim obtained; geometry excluded by §2.5 |
| 13 | 建勲神社 | A `PHYSICAL_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | 6 leads identified (§4.5), all `403` |
| 14 | 建勲神社 | B `RITUAL_AXIS` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | Haiden / 祝詞舎 / 祭器庫 records located but unread |
| 15 | 建勲神社 | C `SYMBOLIC_ORIENTATION` | `NOT_DETERMINED` | `SOURCE_UNRETRIEVED` | none | no documentary claim obtained; geometry excluded by §2.5 |

```text
CELLS = 15
CONFIRMED               =  0
NOT_DETERMINED          = 15
HOLD_ORIENTATION_REVIEW =  0
```

No cell is `HOLD`. `HOLD` requires competing or materially ambiguous **accepted**
sources; zero accepted sources were read, so the condition is unreachable in this run.
Missing evidence was not upgraded to `HOLD`.

## 7. Required 5-Row Summary

| Shrine | PHYSICAL_ORIENTATION | RITUAL_AXIS | SYMBOLIC_ORIENTATION | Strongest Evidence Level | Primary Source Count | Corroboration Count | Open Evidence Gap |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| 伏見稲荷大社 | `NOT_DETERMINED` | `NOT_DETERMINED` | `NOT_DETERMINED` | `NONE_OBTAINED` | 0 | 0 | Whether the reported west-facing statement applies to the precinct or to the Honden; the equivalence is unproven and the record unread |
| 日光東照宮 | `NOT_DETERMINED` | `NOT_DETERMINED` | `NOT_DETERMINED` | `NONE_OBTAINED` | 0 | 0 | Toshogu's own orientation, stated independently of the Taiyuin→Toshogu relationship; city / measured-drawing sources unread |
| 宇佐神宮 | `NOT_DETERMINED` | `NOT_DETERMINED` | `NOT_DETERMINED` | `NONE_OBTAINED` | 0 | 0 | Whether the reported south-facing / east-west-arranged wording establishes only layer A or also layer B |
| 春日大社 | `NOT_DETERMINED` | `NOT_DETERMINED` | `NOT_DETERMINED` | `NONE_OBTAINED` | 0 | 0 | Any cardinal orientation statement at all for the four Honden; none located even in lead titles |
| 建勲神社 | `NOT_DETERMINED` | `NOT_DETERMINED` | `NOT_DETERMINED` | `NONE_OBTAINED` | 0 | 0 | The reported east-facing Honden wording, and whether Haiden / 祝詞舎 / 祭器庫 records carry a worship-sequence statement |

## 8. Rates

Computed directly from §6. Denominator is 5 per layer, 15 overall.

### 8.1 Per layer

```text
PHYSICAL_ORIENTATION
  PHYSICAL_EVIDENCE_ACQUISITION_RATE = 0 / 5  =   0.0 %
  NOT_DETERMINED_RATE                = 5 / 5  = 100.0 %
  HOLD_RATE                          = 0 / 5  =   0.0 %

RITUAL_AXIS
  RITUAL_AXIS_EVIDENCE_ACQUISITION_RATE = 0 / 5 =   0.0 %
  NOT_DETERMINED_RATE                   = 5 / 5 = 100.0 %
  HOLD_RATE                             = 0 / 5 =   0.0 %

SYMBOLIC_ORIENTATION
  SYMBOLIC_EVIDENCE_ACQUISITION_RATE = 0 / 5  =   0.0 %
  NOT_DETERMINED_RATE                = 5 / 5  = 100.0 %
  HOLD_RATE                          = 0 / 5  =   0.0 %
```

### 8.2 Overall

```text
TOTAL_CELLS                      = 15
OVERALL_EVIDENCE_ACQUISITION_RATE = 0 / 15 =   0.0 %
OVERALL_NOT_DETERMINED_RATE       = 15 / 15 = 100.0 %
OVERALL_HOLD_RATE                 = 0 / 15 =   0.0 %
```

`NOT_DETERMINED` and `HOLD` are reported separately and are not combined at any point.

### 8.3 Rate interpretation warning

These rates measure **this run's retrieval outcome**, not the availability or quality
of Japanese cultural-property orientation evidence. A `0.0 %` acquisition rate produced
by a uniform network denial carries no information about the sources themselves, and
must not be cited as evidence that the sources are inadequate.

## 9. Evidence-Source Gaps

### 9.1 Gap-1 — Environmental (blocking, and the only gap actually measured)

```text
GAP_1 = EGRESS_POLICY_DENIES_ALL_PRIMARY_AND_CORROBORATION_HOSTS
SEVERITY = BLOCKING
SCOPE    = all 5 shrines, all 3 layers, all 5 primary tiers, corroboration tier
```

21 of 22 hosts denied at `CONNECT` (§3.2). This gap is not a property of the evidence
domain and cannot be closed by changing the evidence policy.

### 9.2 Gap-2 — Methodological (identified from lead titles, unmeasured)

```text
GAP_2 = PRECINCT_VS_BUILDING_SCOPE_AMBIGUITY
```

Cultural-property records are registered per structure (本殿, 楼門, 権殿, 外拝殿,
祝詞舎, 祭器庫) and separately per 境内. A statement attached to a 境内 record does not
transfer to a 本殿 record. `orientation_subject` exists in the schema precisely to carry
this, and would need to be populated from the record's own scope on every cell. This is
recorded as a design observation from the lead structure; it was not tested, because no
record was read.

### 9.3 Gap-3 — Structural (identified, unmeasured)

```text
GAP_3 = LAYER_B_AND_C_SOURCE_CLASS_MAY_DIFFER_FROM_LAYER_A
```

Layer A is plausibly served by P-1 cultural-property records, whose standard fields
(`構造及び形式等`) are the natural home of 東面 / 南面 wording. Layers B and C are not
obviously served by the same records: a worship-sequence statement or a named
intentional target is more likely to sit in P-3 repair reports, P-4 architectural
research, or P-5 shrine material. If so, a per-layer source hierarchy would be needed
rather than one shared hierarchy. This is a hypothesis generated by the pilot's design,
not a result of it.

## 10. Pilot Decision

### 10.1 Decision

```text
ORIENTATION_EVIDENCE_PIPELINE = NOT_DETERMINED_IN_THIS_ENVIRONMENT
```

This value is **not** one of `VIABLE` / `PARTIALLY_VIABLE` / `NOT_YET_VIABLE`. It is
recorded deliberately, because each of the three specified values would assert
something this run did not test. The brief requires the decision to follow the
definitions deterministically rather than a subjective score; applied honestly, the
definitions do not select any of the three.

### 10.2 Why each specified value is unsupportable

```text
VIABLE
  requires: PHYSICAL orientation reproducibly obtainable for most Pilot Shrines
  observed: obtainable for 0 of 5
  -> unsupportable

PARTIALLY_VIABLE
  requires: PHYSICAL evidence usable, RITUAL / SYMBOLIC layers gapped,
            system correctly returning NOT_DETERMINED instead of guessing
  observed: the second and third conditions hold — the pilot returned
            NOT_DETERMINED on all 15 cells and declined every available
            shortcut (§3.3, §4.2, §5) — but the first condition fails
            outright, since PHYSICAL evidence was never usable
  -> unsupportable as stated; the pilot passed the discipline half of this
     definition and failed the evidence half for a reason external to evidence

NOT_YET_VIABLE
  requires: PHYSICAL orientation cannot be reproduced reliably FROM ACCEPTED
            SOURCES, or evidence classification is non-deterministic
  observed: no accepted source was consulted, so nothing was learned about
            reproducing orientation from accepted sources; and classification
            behaved deterministically throughout
  -> unsupportable, and actively misleading: it would attribute to the
     sources a failure that occurred in the network layer
```

Selecting `NOT_YET_VIABLE` is the specific error this section exists to prevent. It is
the value a careless run would record, and it would wrongly retire an approach that has
not yet been tested.

### 10.3 What the run did establish

Two things were genuinely tested, because they do not depend on network access.

```text
FINDING_1 = CLASSIFICATION_DETERMINISM_HELD
```

Every cell was classified by rule, and the rules produced the same answer every time.
`HOLD` was never reached by missing evidence (§6). `NOT_DETERMINED` was never upgraded.
The `E4`-exclusion rule for layers B and C was never overridden. The
`GEOMETRY → DIRECTION`, `DOCUMENT → MEANING` separation held on all five layer-C cells.

```text
FINDING_2 = REFUSAL_DISCIPLINE_HELD_UNDER_PRESSURE
```

Four separate shortcuts were available and each was declined: adopting search-summary
text as an `E1` citation (§3.3); adopting the brief's own reported wording for 建勲神社,
宇佐神宮 and 伏見稲荷大社 as though verified (§4.1, §4.3, §4.5); reversing the
Taiyuin→Toshogu relationship into a Toshogu orientation (§4.2); and deriving cardinal
values from precinct geometry (§5).

The brief states that the ability to correctly return `NOT_DETERMINED` is part of the
Pilot success criteria. On that criterion the run succeeded — but a 100 %
`NOT_DETERMINED` rate obtained without reading any source is a weak test of it, since
refusing every cell is also what a broken pipeline would do. The evidence half of the
pilot remains untested.

### 10.4 Requirement to complete the pilot as specified

Either of the following is sufficient.

```text
OPTION_1  Egress allowance for the §3.2 hosts, at minimum:
            kunishitei.bunka.go.jp
            online.bunka.go.jp
            bunka.nii.ac.jp
            inari.jp / www.toshogu.jp / www.usajinguu.com
            www.kasugataisha.or.jp / kenkun-jinja.org
          The 25 leads in §4 are already located; the pilot resumes at retrieval.

OPTION_2  A Mother Ship evidence packet carrying, per source, the verbatim
          record text (構造及び形式等 / 解説文), the source URL, and the retrieval
          date — the same pattern used for Production evidence in the
          position-audit series.
```

Under either option the 15 cells are re-decided from the documents. Nothing in this run
is carried forward as a finding about the sources.

## 11. Reproducibility Assessment

```text
RETRIEVAL_REPRODUCIBILITY   = NOT_ASSESSED   (0 documents retrieved)
CLASSIFICATION_REPRODUCIBILITY = HIGH
```

Classification reproducibility is assessed as high on the basis of §10.3 `FINDING_1`:
the rule set produced one determinate answer per cell with no discretionary step, and
the decision path for every cell is recorded in §6 against a named lead inventory in
§4. A second operator applying §2 to the same inputs would reach the same 15 values.

That assessment covers the decision procedure only. The acquisition procedure — locate,
retrieve, extract, cite — was exercised only as far as *locate*, which succeeded for all
five shrines (25 leads, every shrine represented in tiers P-1 and P-5). Whether
*retrieve → extract → cite* is reproducible is the open half.

## 12. Is a formal Orientation Evidence Contract supportable?

```text
ORIENTATION_EVIDENCE_CONTRACT_SUPPORTABLE = NOT_YET_ASSESSABLE
```

A Contract requires evidence that its rules can be satisfied in practice. This run
produced zero satisfied cells, so it supplies no such evidence — in either direction.

What the run does support, recorded for whoever drafts the Contract later:

1. **The three-layer separation is operationally meaningful.** It forced three distinct
   questions on each shrine and prevented a layer-A statement from silently answering
   layer B or C. §4.3 (宇佐神宮) is the clearest instance: the reported record wording
   plausibly settles A while leaving B open, and the split is what makes that visible.
2. **`E4`-exclusion for layers B and C is load-bearing.** Without it, map and aerial
   corroboration would have been the only reachable source class in this run, and would
   have produced symbolic conclusions from geometry alone.
3. **A retrieval-status qualifier is needed** (§2.7). Without it a Contract cannot
   distinguish "read and insufficient" from "never opened", and both collapse into
   `NOT_DETERMINED` — which is exactly the collapse that would have turned this run into
   a false `NOT_YET_VIABLE`.
4. **`orientation_subject` must be mandatory, not optional** (§9.2), because
   cultural-property records are registered per structure and per precinct, and the two
   scopes do not transfer.

None of the four is a Contract clause. They are inputs to drafting one, and drafting is
out of scope for this task.

## 13. Validation

```text
Pilot Shrines                                    = 5          ✓ exactly 5
Layer decisions                                  = 15         ✓ exactly 15
CONFIRMED cells without a cited accepted source  = 0          ✓ (0 CONFIRMED cells exist)
Symbolic meaning inferred from geometry          = none       ✓
Missing evidence classified as HOLD              = none       ✓ (HOLD = 0)
Rates recompute from §6                          = 0/15, 15/15, 0/15  ✓
NOT_DETERMINED combined with HOLD                = never      ✓
Production / Base Seed / Shrine model change     = NONE       ✓
Existing Contract change                         = NONE       ✓
Recommendation / Compass logic change            = NONE       ✓
Orientation Evidence Contract created            = NO         ✓
Repository diff                                  = this document only
```

## 14. STOP

```text
EVIDENCE_ACQUISITION          = BLOCKED (21/22 hosts, 403 at CONNECT)
LAYER_DECISIONS               = 15 / 15 recorded
CONFIRMED_CELLS               = 0
PIPELINE_DECISION             = NOT_DETERMINED_IN_THIS_ENVIRONMENT
CONTRACT_SUPPORTABILITY       = NOT_YET_ASSESSABLE
CONTRACT_CREATED              = NO
```

Next action requires a Mother Ship decision between `OPTION_1` (egress allowance) and
`OPTION_2` (evidence packet) in §10.4.
