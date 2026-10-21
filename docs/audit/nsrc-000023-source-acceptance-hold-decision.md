# nsrc-000023 熱串彦神社 — Mother Ship Source Acceptance HOLD Decision

## 1. Decision

- Recorded at: **2026-10-21**
- Base: `develop@48e864832d1ab29d8378eab1648460812ba68cca`
- Decision authority: **Mother Ship** (explicit user instruction in this project)
- Candidate: `nsrc-000023` / 熱串彦神社
- Specific subject: **由緒書き (onsite notice) as a candidate current-principal-deity Source**

**Mother Ship decision: HOLD source acceptance.** This is an explicit *deferral of adoption*, not a rejection of the document's existence, not a reversal of option B and not a G3 transition.

```text
MOTHER_SHIP_OPTION                    = B (UNCHANGED)
MOTHER_SHIP_NOTICE_SOURCE_DECISION    = ACCEPTANCE_ON_HOLD
NOTICE_SOURCE_ACCEPTED                = NO
NOTICE_SOURCE_REJECTED                = NO
ACCEPTED_CURRENT_PRINCIPAL_DEITY_SRC  = NONE_NEW
G3_RELEASE_CONDITION_1                = NOT_MET
G3_RELEASE_CONDITION_2                = NOT_MET
G3_STATUS                             = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE
PRODUCT_SURFACE                       = NOT_YET_APPLICABLE
G4_AUTHORIZATION                      = NOT_AUTHORIZED
CANDIDATE_MASTER_STATUS               = DISCOVERED (UNCHANGED)
G3_REEVALUATION_AUTHORIZED            = NO
PRODUCTION_WRITE_AUTHORIZED           = NO
STOP                                  = TRUE
```

## 2. Evidence and decision boundary

- [`nsrc-000023-current-notice-evidence.md`](nsrc-000023-current-notice-evidence.md): the photographed notice text was assessed in conversation as `阿田都久志尼命` and the user reported that the same notice remains displayed, based on a recent on-site photo. The **receipt/recording date** is 2026-10-21; photo capture date and independent recent on-site photo review were not established.
- [`nsrc-000023-historical-source-followup.md`](nsrc-000023-historical-source-followup.md): historical transcriptions and reference works have nonidentical deity forms; original page scans were not directly collated.
- [`nsrc-000023-mother-ship-decision-b.md`](nsrc-000023-mother-ship-decision-b.md): option B authorizes **specific Source identification and verification as a path**, but does not itself approve Source adoption or G3 advancement.
- [`niigata-vpg001-g3-source-knowledge-fit.md`](niigata-vpg001-g3-source-knowledge-fit.md) §6 / §6.1 and [`../knowledge/shrine-expansion-gate-contract.md`](../knowledge/shrine-expansion-gate-contract.md) §6–7: accepted current-principal-deity evidence or a separately approved meaning-preserving representation is required before G3 can advance.

The Mother's Ship decision here concerns **this specific onsite-notice Source only**. It does not assert that the user report is false, does not select among `阿田都久志尼命`, `阿田都久志比尼命`, `阿都久志比古命`, or `加茂氏の祖神`, and does not reclassify `金山彦命` from 配祀 to principal deity.

## 3. Historical status compatibility

Earlier audits containing `SOURCE_ACCEPTANCE = PENDING_MOTHER_SHIP` or `MOTHER_SHIP_DECISION = NOT_RECORDED` accurately describe the state **at their recording time** and are not modified. This dated decision updates only the subsequent onsite-notice **acceptance decision** to `ACCEPTANCE_ON_HOLD`. The pre-existing Mother Ship option B remains selected; G3 HOLD and G4 NOT_AUTHORIZED continue unchanged.

## 4. Later work / stop conditions

If a new independently reviewable, identified Source establishes the **current** principal deity and its role, submit its precise provenance and any historical-name conflicts for a distinct Mother Ship Source-adoption decision. Only after documented adoption should a separate G3 review be proposed. No automatic promotion or runtime/data writes.

```text
CHANGED_FILES                     = THIS_DOCUMENT_ONLY
EXISTING_AUDITS                   = UNCHANGED
CANDIDATE_MASTER_FIXTURES_SEEDS   = UNCHANGED
DATABASE_PRODUCTION_RUNTIME       = UNCHANGED
RECOMMENDATION_RANKING            = UNCHANGED
NEXT_GATE                         = NONE_AUTHORIZED
STOP                              = TRUE
```
