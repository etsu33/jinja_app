# NIIGATA-001-VPG001 G3 Source + Knowledge Model Fit

## 1. Status

```text
VPG001 G3（global）              = OPEN（not closed: Mother Ship Product Surface decisions pending）
technical G3 classification     = recorded for all five（§4–§8）
NORMAL_MODEL_FIT                 = 3（nsrc-000021 / 000022 / 000024）
CURATION_RELEASE_CANDIDATE       = 1（nsrc-000025）
RESEARCH_REQUIRED_BEFORE_RELEASE = 1（nsrc-000023）
MODEL_REVIEW_REMAINS             = 0
MODEL_CHANGE_REQUIRED            = 0
PRODUCT_DECISION_REQUIRED        = 0
Mother Ship Product Surface      = PENDING ×4（000021 / 000022 / 000024 / 000025）; NOT_YET_APPLICABLE ×1（000023）
G4                               = NOT AUTHORIZED（all five）
Production / Seed / Candidate Master write = NONE
```

- Recorded at: 2026-10-19
- Base: `develop@e0a3cf3e`（PR #3271 merge, VPG001 G2 final freeze）
- Branch: `audit/niigata-vpg001-g3-source-knowledge-fit`

This audit records the **technical** G3 classification supplied by Mother Ship on 2026-10-19, with the
repository evidence each one rests on. It does not choose a Product Surface and does not perform G4.

Three things are kept separate throughout:

```text
technical G3 classification     = this audit（model fit of the Source-backed Knowledge）
Mother Ship Product Surface     = RECOMMENDATION / CATALOG_ONLY, decided by Mother Ship per candidate（PENDING）
G4 authorization                = a later gate; requires PRODUCT_SURFACE = RECOMMENDATION（gate contract §7）
```

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §6 G3 Source + Knowledge Model Fit Gate,
  §7 G4 Knowledge Fact + Evidence Gate
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md` §5 Release Classification Rules
- Upstream: `docs/audit/niigata-vpg001-g1-identity-duplicate.md`（G1 PASS / CLOSED）,
  `docs/audit/niigata-vpg001-g2-position-review.md`（G2 CLOSED / PASS, FROZEN）,
  `docs/audit/niigata-001-expansion-priority-screening.md`（screening evidence）
- Precedents: `docs/audit/niigata-h001-g3-source-knowledge-fit.md`,
  `docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md`

## 3. Upstream frozen identity / position（unchanged by G3）

| candidate_id | official_name | official_address（G1） | G2 adopted anchor（frozen） |
|---|---|---|---|
| nsrc-000021 | 荒川神社 | 新潟県胎内市桃崎浜187番地 | 38.1409456, 139.4073314 |
| nsrc-000022 | 五十嵐神社 | 新潟県三条市大字飯田2283番地 | 37.573979, 139.048758 |
| nsrc-000023 | 熱串彦神社 | 新潟県佐渡市長江854番地 | 38.072529, 138.407913 |
| nsrc-000024 | 秋葉神社 | 新潟県新潟市秋葉区秋葉3丁目8番19号 | 37.7863255, 139.1351949 |
| nsrc-000025 | 天津神社 | 新潟県糸魚川市一の宮1丁目3番34号 | 37.0397729, 137.8644153 |

G3 does not modify identity, duplicate classification or coordinates.

### 3.1 Accepted G3 Source evidence and verification level

The earlier priority-screening record contained SEARCH_SUMMARY evidence for nsrc-000021 / 000022 /
000023 / 000024. G3 re-verification on 2026-10-19 directly opened the authoritative pages below for
nsrc-000021 / 000022 / 000024. Those direct checks supersede SEARCH_SUMMARY as the G3 acceptance basis
for the stated Fact candidates. The screening record itself is not rewritten.

| candidate_id | accepted G3 Source | verification level |
|---|---|---|
| nsrc-000021 | 新潟県「北前船の魅力を訪ねて」 https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html ; 新潟県 cultural-property material https://www.pref.niigata.lg.jp/uploaded/attachment/180012.pdf | PRIMARY_PAGE_VERIFIED（2026-10-19） |
| nsrc-000022 | 三条市「五十嵐神社」 https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html | PRIMARY_PAGE_VERIFIED（2026-10-19） |
| nsrc-000023 | [S5] 新潟県観光協会 spot/42601 | SEARCH_SUMMARY（principal-deity identity remains unresolved; G3 HOLD） |
| nsrc-000024 | 新潟市「文化資源ガイド（秋葉区）」 https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf | PRIMARY_PAGE_VERIFIED（2026-10-19） |
| nsrc-000025 | 天津神社・奴奈川神社 公式サイト「御由緒・御祭神」 https://amatsujinja.com/story/ | PRIMARY_PAGE_VERIFIED（2026-10-18） |

G3 accepted-Source condition is therefore satisfied for nsrc-000021 / 000022 / 000024 / 000025.
nsrc-000023 remains RESEARCH_REQUIRED_BEFORE_RELEASE and does not use SEARCH_SUMMARY to bypass the HOLD.
Exact G4 Source rows / Fact-Source relations are still a later Source Packet responsibility.

## 4. nsrc-000021 荒川神社 — NORMAL_MODEL_FIT

```text
Fact owner                      = 荒川神社（胎内市桃崎浜187番地）; clear
current deity                   = 天鈿女命（named, Source-backed）
History candidates              = usable, Source-backed（see below）
sub-shrine / associated target  = none required
anonymous collective            = none
unresolved deity identity       = none
classification                  = NORMAL_MODEL_FIT
```

Directly verified 新潟県 material supports: 御祭神 = 天鈿女命; shipowners' 船絵馬 offered for safe
voyages; 86 船絵馬; the 荒川神社大祭 / 模型和船 context; and the registered cultural-property status.

Localized chronology conflict:

```text
official article  = 天保12年（1814年）
official cultural-property material = 天保12年（1841年）
G3 ruling         = chronology is conflicting inside the accepted official Source set
                    and no normalized building year is authorized here
scope             = localized; it does not invalidate the unrelated accepted Facts above
```

G4 proposed boundary（not authorized; §10）:

- named Deity candidate 天鈿女命 may proceed;
- safe Source-backed History candidates may proceed;
- the conflicted normalized chronology Fact is excluded.

## 5. nsrc-000022 五十嵐神社 — NORMAL_MODEL_FIT

```text
Fact owner                      = 五十嵐神社（三条市大字飯田2283番地）; clear
current deity                   = 五十日帯日子命（direct 三条市 Source spelling）
History                         = traditional founding / development narratives
sub-shrine / associated target  = none
anonymous collective            = none
unresolved deity identity       = none
classification                  = NORMAL_MODEL_FIT
```

The directly verified 三条市 page states the祭神 as **五十日帯日子命** and records the 越国 / 頸城 /
上田郷 / 下田郷 development narrative, the 飯田宮沢 / 舞鶴の丘 burial tradition, the 江戸期「若一王子」
name, 安産信仰, and the 明治期「御陵墓伝説地」record.

Tradition semantics:

- the development / burial narrative preserves the Source's 「といわれています」 framing and is represented
  as `ShrineHistory.tradition`, not upgraded into independently verified historical fact;
- this direct G3 Source supersedes the screening-only spelling ambiguity for the current Deity candidate;
- the screening-only 式内社 / scholarly-view material is not required for this G3 PASS and is not promoted
  by this audit.

G4 proposed boundary（not authorized; §10）:

- named Deity candidate may proceed;
- Source-backed History candidates may proceed, with tradition semantics preserved.

## 6. nsrc-000023 熱串彦神社 — RESEARCH_REQUIRED_BEFORE_RELEASE

```text
G3                              = HOLD
classification                  = RESEARCH_REQUIRED_BEFORE_RELEASE
PRODUCT_SURFACE                 = NOT_YET_APPLICABLE
G4                              = NOT_AUTHORIZED
```

Repository evidence（[S5]）: 式内社（佐渡国 九社の一）, early-Heian founding, hall 正徳4（1714）, thatched
能舞台 of the 安永 era（市文化財）; main deity = 加茂氏の祖神, 金山彦命 = 配祀.

Why HOLD:

- the accepted Source identifies the current principal deity only as `加茂氏の祖神`;
- the proper-name identity of the current principal deity is unresolved;
- 金山彦命 is explicitly 配祀. It is not a substitute for the unresolved principal deity;
- registering 金山彦命 alone would hide the current deity structure and create a misleading partial
  deity set（gate contract §6 Model Risk STOP: "Source上重要な構造を消して成立させるpartial deity list"）;
- usable History（式内社, 能舞台）must not be used to bypass this Model Risk（gate contract §6
  Eligibility Bypass禁止）.

Why not MODEL_CHANGE_REQUIRED: no evidence establishes that the current model cannot represent the deity
set. Focused Source research may resolve the principal deity's proper name（model-risk contract §5.2:
"これはMODEL_CHANGE_REQUIREDとは異なる"）.

Prohibited:

```text
Deity row from "加茂氏の祖神"                        PROHIBITED
金山彦命 as the complete current deity set          PROHIBITED
History-only promotion past this HOLD               PROHIBITED
```

Release condition（either）:

1. an accepted Source confirms the proper-name identity of the current principal deity; or
2. a focused review establishes another contract-compliant representation without meaning loss.

## 7. nsrc-000024 秋葉神社 — NORMAL_MODEL_FIT

```text
Fact owner                      = 秋葉神社（新潟市秋葉区秋葉3丁目8番19号）; clear
current deities                 = 大己貴神 / 大物主命 / 菅原道真公（named, Source-backed）
sub-shrine / associated target  = none
anonymous collective            = none
unresolved deity identity       = none
classification                  = NORMAL_MODEL_FIT
```

The directly verified 新潟市 PDF supports: 御祭神 = 大己貴神, with 大物主命 and 菅原道真公 also
enshrined; former 桂家 guardian context; transfer to 秋葉町内 in 1964; the 2013 250th-year statement;
and the listed annual festivals.

Localized chronology conflict:

```text
official Source wording = 明治3年（1872）
problem                 = the era-year / Gregorian-year pair is internally inconsistent
G3 ruling               = the year is NOT normalized or silently corrected in G3
scope                   = localized; the rebuild-year normalization is excluded until separately resolved
```

The other frozen 秋葉神社 rows are different shrines. No Fact from them is attributed here.

G4 proposed boundary（not authorized; §10）:

- named Deity candidates may proceed;
- safe Source-backed History candidates may proceed;
- the conflicted rebuild-year normalization is excluded until separately resolved.

## 8. nsrc-000025 天津神社 — CURATION_RELEASE_CANDIDATE

```text
Fact owner（current main shrine） = 天津神社
official Source                  = https://amatsujinja.com/story/（PRIMARY_PAGE_VERIFIED 2026-10-18）
classification                   = CURATION_RELEASE_CANDIDATE
```

Ownership boundary（the curation this class requires）:

| Deity | Fact owner | nsrc-000025 Fact? |
|---|---|---|
| 天津彦々火瓊々杵尊 | 天津神社 | YES |
| 天児屋根命 | 天津神社 | YES |
| 天太玉命 | 天津神社 | YES |
| 奴奈川媛命 | 奴奈川神社 | **NO** |
| 八千矛命 | 奴奈川神社 | **NO** |

- The official Source identifies 天津神社 and 奴奈川神社 separately.
- The 天津神社 deity set is individually representable, one named deity per row.
- The shared precinct and the shared G2 navigation anchor do **not** merge Knowledge ownership.
- No anonymous collective remains. No unresolved current principal-deity identity remains for 天津神社.
- The existing schema is sufficient if the cross-shrine exclusion boundary is preserved
  （model-risk contract §5.1 conditions 1–6）.

G4 proposed boundary（not authorized; §10）:

- only 天津神社-owned Deity / History Facts;
- 奴奈川神社 Facts explicitly excluded;
- the ownership boundary is recorded in the future Source Packet / Seed preflight.

This classification is the technical G3 answer to the 天津神社・奴奈川神社 model-risk question carried
from G1 / G2: the existing schema is sufficient **on condition that** the cross-shrine exclusion boundary
is preserved. Release still depends on the Product Surface decision and G4.

## 9. Product Surface（Mother Ship decision; not made here）

| candidate_id | technical G3 classification | TECHNICAL_PRODUCT_SURFACE_PROPOSAL | MOTHER_SHIP_PRODUCT_SURFACE_DECISION |
|---|---|---|---|
| nsrc-000021 | NORMAL_MODEL_FIT | RECOMMENDATION | PENDING |
| nsrc-000022 | NORMAL_MODEL_FIT | RECOMMENDATION | PENDING |
| nsrc-000023 | RESEARCH_REQUIRED_BEFORE_RELEASE | — | PRODUCT_SURFACE = NOT_YET_APPLICABLE（G3 HOLD） |
| nsrc-000024 | NORMAL_MODEL_FIT | RECOMMENDATION | PENDING |
| nsrc-000025 | CURATION_RELEASE_CANDIDATE | RECOMMENDATION | PENDING |

The technical proposal is not a decision. This audit chooses neither `RECOMMENDATION` nor `CATALOG_ONLY`.

## 10. G4 authorization（future gate; not performed）

```text
G4 = NOT AUTHORIZED for all five
```

G4 applies only to a candidate with `PRODUCT_SURFACE = RECOMMENDATION`（gate contract §7）. Before any G4
Fact is created:

- nsrc-000021 / 000022 / 000024 / 000025: the directly verified G3 Sources in §3.1 must be persisted as
  exact Source Packet rows / provenance before Fact materialization.
- nsrc-000022: the accepted 三条市 Source spelling is 五十日帯日子命; G4 must preserve the cited Source wording.
- nsrc-000021 / 000024: the conflicted chronology normalizations stay excluded.
- nsrc-000025: the 天津神社 / 奴奈川神社 exclusion boundary is recorded in the Source Packet / Seed preflight.
- nsrc-000023: not eligible until the §6 release condition is met.

## 11. Validation

```text
identities vs G1 canonical identity            match ×5（name + address, reviewed identity manifest）
adopted coordinates vs frozen G2               unchanged ×5
Fact attributed to another shrine              none（same-name rows and 奴奈川神社 excluded）
天津神社 / 奴奈川神社 ownership                 separated（§8 table）
anonymous collective introduced                none
partial deity list asserted complete（000023） none; 金山彦命 alone prohibited（§6）
aggregate                                      NORMAL 3 / CURATION 1 / RESEARCH 1 / REVIEW 0 / CHANGE 0 / PRODUCT 0
```

## 12. Not done

```text
Product Surface decision                 NOT MADE（Mother Ship, PENDING ×4）
G4 / Source Packet / Fact creation       NOT PERFORMED
VPG001 G3 global closure                 NOT DONE（Product Surface pending）
Candidate Master / Base Seed / Knowledge Seed / Production   UNCHANGED, NO WRITE
Position records / G1 / G2 values        UNCHANGED
Recommendation / Ranking / Concierge / Compass / API / frontend / analytics   UNCHANGED
Model / Migration / Serializer           UNCHANGED
```

## 13. Current state

```text
nsrc-000021  G3 = NORMAL_MODEL_FIT                   PRODUCT_SURFACE = PENDING              G4 = NOT AUTHORIZED
nsrc-000022  G3 = NORMAL_MODEL_FIT                   PRODUCT_SURFACE = PENDING              G4 = NOT AUTHORIZED
nsrc-000023  G3 = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE  PRODUCT_SURFACE = NOT_YET_APPLICABLE  G4 = NOT AUTHORIZED
nsrc-000024  G3 = NORMAL_MODEL_FIT                   PRODUCT_SURFACE = PENDING              G4 = NOT AUTHORIZED
nsrc-000025  G3 = CURATION_RELEASE_CANDIDATE         PRODUCT_SURFACE = PENDING              G4 = NOT AUTHORIZED

VPG001 G3（global） = OPEN
NEXT              = Mother Ship Product Surface decisions for 000021 / 000022 / 000024 / 000025;
                    focused Source research for 000023
STOP              = TRUE
```
