# nsrc-000023 熱串彦神社 — Advancement Readiness Audit

## 1. Status

```text
candidate_id                         = nsrc-000023
official_name / address（G1）         = 熱串彦神社 / 新潟県佐渡市長江854番地
current G3                           = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE（unchanged）
NEW_ACCEPTED_EVIDENCE                = NONE
RELEASE_CONDITION_1（accepted Source names current principal deity） = NOT_MET
RELEASE_CONDITION_2（contract-compliant representation, no meaning loss） = NOT_MET
CURRENT_PRINCIPAL_DEITY_PROPER_NAME  = CONFLICTING / NOT_FROZEN（unchanged）

ADVANCEMENT_READINESS                = STOP（G3 re-entry not justified by evidence）
RESEARCH_TRACK                       = OPEN
PRODUCT_SURFACE                      = NOT_YET_APPLICABLE（unchanged）
G4                                   = NOT_AUTHORIZED（unchanged）
MOTHER_SHIP_DECISION                 = NOT_RECORDED（options in §8）
```

- Recorded at: 2026-10-21
- Base: `origin/develop@5e41231`（PR #3288 merge, VPG001 G8 closure）
- Scope: read-only research and evaluation. This record does not modify the Candidate Master, fixtures,
  Seeds, Production, DB, runtime, Recommendation, Ranking or any existing audit record. It does not make the
  Mother Ship decision, does not authorize G4, does not change Product Surface and does not resolve the
  principal-deity identity by inference.

Labels used below:

- **VERIFIED**: confirmed in this repository's merged records or the current Candidate Master.
- **SEARCH_SUMMARY**: seen only in web-search result text on 2026-10-21. The page itself was not opened
  (§5.2). Not an accepted Source.
- **RESERVED**: a decision that belongs to Mother Ship.

---

## 2. Authority

- [`niigata-vpg001-g3-source-knowledge-fit.md`](niigata-vpg001-g3-source-knowledge-fit.md) §3.1, §6, §6.1, §9, §10
- [`niigata-vpg001-g1-identity-duplicate.md`](niigata-vpg001-g1-identity-duplicate.md)
- [`shrine-position/niigata-vpg001-nsrc-000023-position-review.md`](shrine-position/niigata-vpg001-nsrc-000023-position-review.md)
- [`../knowledge/shrine-expansion-gate-contract.md`](../knowledge/shrine-expansion-gate-contract.md) §6, §7, §11A, §13, §14
- [`model-risk-release-contract.md`](model-risk-release-contract.md) §5.1–§5.5
- [`../knowledge/shrine-knowledge-contract.md`](../knowledge/shrine-knowledge-contract.md)
- [`niigata-001-expansion-priority-screening.md`](niigata-001-expansion-priority-screening.md)（[S5] screening row）
- `backend/temples/data/shrine_expansion_candidate_master.json`

---

## 3. Current repository state（VERIFIED）

### 3.1 Candidate Master row（`develop@5e41231`）

```text
candidate_id           = nsrc-000023
candidate_name         = 熱串彦神社
prefecture             = 新潟県
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
identity_status        = CONFIRMED
duplicate_status       = NEW
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate

admission_provenance:
  track                  = nationwide_source_candidate
  prefecture             = 新潟県
  source_batch_id        = NIIGATA-001
  handoff_id             = NIIGATA-001-H012
  source_position        = page006-row010
  source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
  source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
  source_verified_at     = 2026-10-08
  captured_at            = 2026-10-08T14:27:00+09:00
```

This matches the G0 / G1 state. The VPG001 G7 / G8 work did not touch it: the G7 closure records
`nsrc-000023 NOT WRITTEN`, and G8 kept it excluded and unchanged.

### 3.2 Gate state

| Gate | Result | Record |
| --- | --- | --- |
| G1 Identity / Duplicate | PASS / NEW（Mother Ship 2026-10-18） | `niigata-vpg001-g1-identity-duplicate.md` |
| G2 Position | PASS, 38.072529 / 138.407913（CODH facility point accepted as primary, Mother Ship 2026-10-19） | `shrine-position/niigata-vpg001-nsrc-000023-position-review.md` |
| G3 Source + Model Fit | HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE | `niigata-vpg001-g3-source-knowledge-fit.md` §6 / §6.1 |
| Product Surface | NOT_YET_APPLICABLE | same, §9 |
| G4 | NOT_AUTHORIZED | same, §10 |

Not part of this audit's question, but recorded: the G2 corroboration (Wikidata) is still
`PROVENANCE_PENDING`（URL / QID not recorded）. G2 itself is PASS on the CODH primary point.

### 3.3 Newer overlapping work

- No audit merged after the G3 record（PR #3272, 2026-10-19）adds deity evidence for nsrc-000023.
  Later VPG001 records（G4–G8）mention it only as excluded / not written.
- A repository-wide search finds 阿都久志比古命 / 阿田都久志比尼命 / 加茂氏 / 金山彦 only in the G3 record
  and the priority-screening record.
- Open PRs on 2026-10-21: dependabot dependency updates only. There is no open PR touching nsrc-000023 or 熱串彦神社.

---

## 4. Principal-deity identity evidence matrix

The four labels are kept **separate**. None of them is treated as equal to another.

| label | how it is described | where | evidence level | role it can play |
| --- | --- | --- | --- | --- |
| 加茂氏の祖神 | the main deity, described only as "the ancestral deity of the 加茂 clan"; no proper name | [S5] 新潟県観光協会 spot/42601; 佐渡観光交流機構 / さど観光ナビ（G3 §6.1） | SEARCH_SUMMARY in the repository（[S5] was never upgraded to PRIMARY_PAGE_VERIFIED）; same wording again in 2026-10-21 search results | a **description**, not a deity name. G3 prohibits a Deity row from it |
| 金山彦命 | explicitly 配祀（secondary enshrinement）, said to have been enshrined on 金北山 | same sources as above | SEARCH_SUMMARY | a named deity, but explicitly **not** the principal deity. Registering it alone is prohibited（G3 §6: misleading partial deity set） |
| 阿都久志比古命 | given as 祭神 | 精選版 日本国語大辞典（via コトバンク）（G3 §6.1） | reference-work lead; not an accepted Source | a candidate proper name. It conflicts with the next row |
| 阿田都久志比尼命 | given as 祭神, in an entry that also says the 祭神 is regarded as the 加茂氏 ancestor | 日本歴史地名大系（via コトバンク）（G3 §6.1） | reference-work lead; not an accepted Source | a candidate proper name. It conflicts with the row above |

What the matrix supports（VERIFIED from repository records）:

1. Both tourism sources agree only on "main deity = 加茂氏の祖神, 金山彦命 = 配祀".
2. The two reference works give **different** proper names（阿都久志比古命 vs 阿田都久志比尼命）.
   They differ in more than spelling: 比古 vs 比尼, and 阿都 vs 阿田都.
3. 日本歴史地名大系 places 阿田都久志比尼命 next to the 加茂氏-ancestor description. That is a statement
   by one reference work. It is **not** evidence that either name is the shrine's current principal
   deity, nor that 加茂氏の祖神 = 阿田都久志比尼命.
4. No source in the repository, and none found on 2026-10-21, gives the shrine's own current deity list
   （a 由緒書き, a 神社庁 detail page, or an official site）.

Unresolved conflicts（not to be resolved by inference）:

```text
C1  加茂氏の祖神（description） vs a proper name: no accepted Source links them
C2  阿都久志比古命 vs 阿田都久志比尼命: two reference works disagree
C3  reference-work 祭神 vs current principal deity: neither reference work is a current-state Source
C4  金山彦命: its 配祀 role is consistent across sources, but it cannot stand in for the principal deity
```

---

## 5. Source provenance

### 5.1 Sources already in the repository

| id | publisher / work | URL | level in repository | supports |
| --- | --- | --- | --- | --- |
| S5 | 新潟県観光協会 | https://niigata-kankou.or.jp/spot/42601 | SEARCH_SUMMARY（screening, G3 §3.1） | 式内社, founding, 正徳4 hall, 能舞台, 加茂氏の祖神 / 金山彦命 配祀 |
| — | 新潟県神社庁 directory | https://niigata-jinjacho.jp/shrine_niigata/search.php | identity / address only（G0 provenance; G3 §6.1） | name / reading / 佐渡市長江854番地. **No deity name** |
| — | 佐渡観光交流機構 / さど観光ナビ | URL not recorded in G3 §6.1 | focused research（G3 §6.1） | 加茂氏の祖神 / 金山彦命 配祀 only |
| — | 精選版 日本国語大辞典（コトバンク） | URL not recorded in G3 §6.1 | research lead | 阿都久志比古命 |
| — | 日本歴史地名大系（コトバンク） | URL not recorded in G3 §6.1 | research lead | 阿田都久志比尼命 + 加茂氏 ancestor note |
| — | 『日本歴史地名大系』施設・地点項目データセット / CODH | https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000593300.html | G2 primary（position only） | coordinate / address. Not a deity Source |

Provenance gap: G3 §6.1 did not record URLs for the さど観光ナビ and コトバンク pages. Before any of them
could be weighed as a Source, their exact URL, entry, publisher and retrieval date would have to be recorded.

### 5.2 Read-only research on 2026-10-21（SEARCH_SUMMARY only）

The container's network policy denies direct page fetches（the egress proxy returned 403 for
niigata-kankou.or.jp, kotobank.jp, niigata-jinjacho.jp and ja.wikipedia.org; the page fetcher could not
resolve niigata-kankou.or.jp）. Only web-search result text was available. Nothing below was read
from the page itself.

| query | result（search-result text only） |
| --- | --- |
| 熱串彦神社 佐渡 祭神 阿都久志比古命 | Results（niigata-kankou.or.jp spot/42601 and detail_42601, 4travel, a 日本大学 paper F2-29）repeat "主祭神 = 加茂氏の祖神, 金山彦命 配祀". **阿都久志比古命 does not appear.** |
| 熱串彦神社 阿田都久志比尼命 祭神 | No result links 阿田都久志比尼命 to this shrine（unrelated shrines returned）. |
| 熱串彦神社 佐渡市長江 祭神 神社庁 OR 佐渡市 由緒 | Same tourism wording. **No 神社庁 detail page was found.** A 文化遺産オンライン record（https://online.bunka.go.jp/heritages/detail/209695）about the 能舞台 appeared; see §5.3. |

Result URLs seen（not opened; not accepted Sources）:

- https://niigata-kankou.or.jp/spot/42601
- https://niigata-kankou.or.jp/spot/detail_42601.html
- https://www.cst.nihon-u.ac.jp/research/gakujutu/62/pdf/F2-29.pdf
- https://4travel.jp/dm_shisetsu/11833634
- https://online.bunka.go.jp/heritages/detail/209695

```text
NEW_ACCEPTED_EVIDENCE_FOUND_2026_10_21 = NONE
```

### 5.3 Side finding: 能舞台 dating（History, not deity）

The [S5] screening row dates the thatched 能舞台 to the 安永 era. The 文化遺産オンライン search snippet
instead says a 文久3年（1863）document records performances, and estimates construction as "before early
Meiji". This is SEARCH_SUMMARY level, and the two may not even conflict（a building can predate a record）.
It does not affect the deity HOLD. It does mean a future History Fact about the 能舞台 needs a primary
check before its date wording is frozen. Per gate contract §6, History must not be used to bypass the deity HOLD.

---

## 6. Release-condition evaluation

G3 §6 release condition（either one）:

### 6.1 Alternative 1: an accepted Source confirms the proper name of the current principal deity

| requirement | status | basis |
| --- | --- | --- |
| a Source that states the **current** principal deity by proper name | NOT MET | the only current-state sources say "加茂氏の祖神" |
| the Source is accepted（at least PRIMARY_PAGE_VERIFIED, provenance recorded） | NOT MET | the reference-work leads are not current-state Sources and their URLs are not recorded; [S5] is SEARCH_SUMMARY |
| no unresolved conflict with other accepted evidence | NOT MET | C2: the two reference works disagree |

```text
ALTERNATIVE_1 = NOT_MET
```

### 6.2 Alternative 2: a contract-compliant representation without meaning loss

Representations considered, and why none is compliant under the current contract text:

| representation | contract check | result |
| --- | --- | --- |
| Deity row "加茂氏の祖神" | G3 §6 prohibits it explicitly; it is an unnamed descriptor（model-risk §5.4 example: 匿名・未確定の集合祭神 / unnamed deity） | NOT COMPLIANT |
| 金山彦命 alone as the deity set | G3 §6 prohibits it; it is a partial deity list that hides the principal deity（gate contract §6 Model Risk STOP） | NOT COMPLIANT |
| 阿都久志比古命 or 阿田都久志比尼命 as principal deity | it chooses one reference work over the other without an accepted Source; that is inference | NOT COMPLIANT |
| both names as one identity / normalized name | G3 §6.1 forbids normalizing them into one name | NOT COMPLIANT |
| no Deity, History only（式内社 / 能舞台） | gate contract §6 Eligibility Bypass禁止 and G3 §6 "History-only promotion past this HOLD" prohibited | NOT COMPLIANT |
| a new representation for an unnamed / descriptor-only principal deity | not in the current `ShrineDeity` contract. It would be Model / Contract work（model-risk §5.3 / §5.4）, decided by Mother Ship | NOT AVAILABLE UNDER CURRENT CONTRACT |

```text
ALTERNATIVE_2 = NOT_MET
```

### 6.3 Classification check

- **RESEARCH_REQUIRED_BEFORE_RELEASE remains the correct classification**（model-risk §5.2). The current
  model may well be able to represent the shrine once a proper name is accepted. Nothing shows that it
  cannot, so this is **not** MODEL_CHANGE_REQUIRED.
- If Mother Ship later decides that no Source will ever give a proper name, this becomes a model-risk
  question（MODEL_REVIEW_REMAINS / MODEL_CHANGE_REQUIRED）. That reclassification is RESERVED（§8, option C）.

---

## 7. Risks

| risk | consequence if ignored |
| --- | --- |
| R1 inference across the four labels | a Deity Fact that no accepted Source supports（G4 STOP: FactがSource本文を越えている） |
| R2 partial deity set（金山彦命 only） | Recommendation shows a misleading deity structure（G3 Model Risk STOP） |
| R3 History-only bypass | the eligibility rule is bypassed（gate contract §6）; the shrine would join Recommendation with an unresolved deity |
| R4 reference work treated as current state | a historical / scholarly 祭神 is recorded as the current principal deity |
| R5 SEARCH_SUMMARY treated as accepted | provenance cannot be traced; G3 §3.1 already refuses this for nsrc-000023 |
| R6 能舞台 date wording | a History Fact with a wrong period（§5.3） |
| R7 identity drift | none found: G1 / G2 identity and coordinate are unchanged and consistent |

---

## 8. Mother Ship decision options（RESERVED; none is chosen here）

| option | what it means | next gate | what it does not do |
| --- | --- | --- | --- |
| A. Keep HOLD, continue research | Commission primary-source acquisition: the shrine's own 由緒書き / 境内掲示, a 新潟県神社庁 detail page, a 佐渡市 cultural-property or 市史 record, or a scholarly 式内社 study. Record exact URL / publisher / retrieval date | G3 re-entry only when a source names the current principal deity | does not change any state |
| B. Accept a specific source | Mother Ship supplies or approves a primary source that names the current principal deity, verified at PRIMARY_PAGE_VERIFIED with full provenance | G3 re-evaluation → then the Product Surface decision → G4 only if RECOMMENDATION | does not decide between 阿都久志比古命 and 阿田都久志比尼命 without that source |
| C. Open a model-risk review | Decide whether a descriptor-only principal deity（加茂氏の祖神）can be represented without meaning loss. That needs contract / model work（model-risk §5.3 / §5.4） | Model track → G3 from scratch（gate contract §14） | does not register "加茂氏の祖神" under the current contract |
| D. Consider CATALOG_ONLY | Product decision under gate contract §6 / §11A. Note: C4 requires a **traceable accepted Source**. The only shrine-content source for nsrc-000023 is SEARCH_SUMMARY [S5]; the 神社庁 directory confirms identity / address only | Product decision; C4 evidence would need its own accepted-Source check | does not create Deity / History / goriyaku Facts |
| E. Defer | Leave nsrc-000023 at DISCOVERED / G3 HOLD with no active research | none | — |

---

## 9. Final classification

```text
VERIFIED
  Candidate Master row                    = DISCOVERED / REGISTRY_ADMISSION_COMPLETE / AVAILABLE / UNREVIEWED（unchanged）
  G1                                      = PASS / NEW
  G2                                      = PASS（38.072529 / 138.407913）
  G3                                      = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE
  open overlapping PRs                    = NONE

UNRESOLVED
  C1 加茂氏の祖神 vs proper name           = OPEN
  C2 阿都久志比古命 vs 阿田都久志比尼命     = OPEN
  C3 reference 祭神 vs current deity       = OPEN
  C4 金山彦命 = 配祀 only                  = consistent; not a substitute

EVALUATION
  NEW_ACCEPTED_EVIDENCE                    = NONE
  ALTERNATIVE_1                            = NOT_MET
  ALTERNATIVE_2                            = NOT_MET
  CLASSIFICATION                           = RESEARCH_REQUIRED_BEFORE_RELEASE（unchanged）

ADVANCEMENT_READINESS                      = STOP
RESEARCH_TRACK                             = OPEN
PRODUCT_SURFACE                            = NOT_YET_APPLICABLE
G4                                         = NOT_AUTHORIZED
MOTHER_SHIP_DECISION                       = NOT_RECORDED（options A–E in §8）
```

Changes made by this audit:

```text
Candidate Master / fixtures / Seeds / Production / DB / runtime   NONE
Recommendation / Ranking / Concierge / Compass                    NONE
existing audit records                                            NONE（this file only）
```
