# nsrc-000023 熱串彦神社 — Mother Ship Advancement Decision B

## Decision authority and scope

- Recorded: 2026-10-21
- Base: `develop@26728ac7c5f144c42a4aba50678d913745b59a52`
- Candidate: `nsrc-000023` / 熱串彦神社
- Decision maker: Mother Ship (explicit user instruction in the KAMI MUSUBI project)
- Selected option: **B** from `docs/audit/nsrc-000023-historical-source-followup.md` §5 and `docs/audit/nsrc-000023-advancement-readiness.md` §8.
- This record **does not identify or accept any particular Source** and **does not authorize advancement**. B is the selected *conditional source verification / acceptance path*, not an assertion that its prerequisite has been met.

```text
MOTHER_SHIP_OPTION                  = B
MOTHER_SHIP_DECISION                = B_SELECTED_CONDITIONAL_SOURCE_VERIFICATION
SPECIFIC_CURRENT_DEITY_SOURCE       = NOT_IDENTIFIED_OR_APPROVED
ACCEPTED_SOURCE_FOR_RELEASE         = NONE_NEW
G3_RELEASE_CONDITION_1              = NOT_MET
G3_RELEASE_CONDITION_2              = NOT_MET
G3_STATUS                           = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE
G3_REEVALUATION                     = PENDING_ACCEPTED_CURRENT_SOURCE
PRODUCT_SURFACE                     = NOT_YET_APPLICABLE
G4                                  = NOT_AUTHORIZED
CANDIDATE_MASTER_STATUS             = DISCOVERED (unchanged)
PRODUCTION_WRITE                    = NOT_AUTHORIZED
STOP                                = TRUE
```

## Decision interpretation

Mother Ship explicitly selected option B on 2026-10-21. Under the previously documented option B, this means:

1. Identify a **specific** authoritative Source expressly naming the **current** principal deity of 熱串彦神社.
2. Verify the actual Source page / original text, issuer or publisher, exact URL or stable archival identifier, date accessed, name and role as stated, and whether it identifies current shrine practice.
3. Compare it without inference with the unresolved `加茂氏の祖神`, `金山彦命` (配祀), `阿都久志比古命` and `阿田都久志比尼命` descriptions, preserving conflicting forms.
4. Bring the source-specific acceptance decision and its evidence to Mother Ship for explicit approval. **No acceptance is recorded by choosing B alone.**
5. Only after a directly verified and accepted current-state Source passes the existing G3 release condition may a separate G3 re-evaluation be proposed. Product Surface and G4 remain distinct later decisions and are not automatically authorized.

Do not treat previously found historical transcriptions, search summaries, secondary descriptions, or historical deity references as an approved current principal-deity Source. The original NDL images and the current onsite notice remain unverified in the referenced audits.

## Pre-existing records remain authoritative and unchanged

- [`nsrc-000023-advancement-readiness.md`](nsrc-000023-advancement-readiness.md): G3 HOLD, both release alternatives NOT_MET, Source gaps.
- [`nsrc-000023-historical-source-followup.md`](nsrc-000023-historical-source-followup.md): historical research leads; original text not directly collated; option B previously unselected at the time of that audit.
- [`niigata-vpg001-g3-source-knowledge-fit.md`](niigata-vpg001-g3-source-knowledge-fit.md) §6 and §6.1: technical G3 release condition and forbidden inference.
- [`../knowledge/shrine-expansion-gate-contract.md`](../knowledge/shrine-expansion-gate-contract.md) §6–7: G3 Model Risk STOP, Mother Ship Product decision, G4 authorization requirements.
- VPG001 four-member G8 Closure remains CLOSED and is unrelated to this candidate's authorization.

Earlier `MOTHER_SHIP_DECISION = NOT_RECORDED` statements in historical audit documents describe the state **as of their recording time** and must not be retroactively rewritten. This later, candidate-specific record supersedes that field **only for the selected A–E option**, not any source acceptance or Gate status.

## Change boundary / next action

- Changed file: **this document only**.
- No Candidate Master, JSON fixture, Seed, production DB, model, migration, Recommendation, Ranking, runtime or earlier audit record changes.
- Next permitted activity: **read-only, specific current-principal-deity Source verification**. Upon verified evidence, submit a distinct Source-acceptance / G3 review proposal to Mother Ship; stop before any state transition.

```text
MOTHER_SHIP_OPTION_RECORDED      = YES (B)
SOURCE_ACCEPTANCE_RECORDED      = NO
G3_GATE_ADVANCEMENT_AUTHORIZED  = NO
G4_GATE_AUTHORIZED              = NO
```
