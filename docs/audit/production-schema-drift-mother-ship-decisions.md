# Production Schema Drift - Mother Ship Decisions

Date: 2026-09-13
Status: DECIDED
Scope: temples schema drift remediation

## Background

Production schema audit identified six tables that are present in Django ProjectState but physically absent from Production:

- places_seed
- places_seed_state
- temples_concierge_recommendation_click_log
- temples_conciergehistory
- temples_like
- temples_rankinglog

Production migration history also shows historical divergence between the nogis migration lineage and the canonical temples migration lineage.

This decision does not attempt to rewrite historical migration records.
The objective is to converge the current Product Model, Migration State, and Production Physical Schema.

---

## Mother Ship Decisions

### D1 - Like

Decision: REMOVE

Reason:
- No current live query references
- No active endpoint
- No current test or product specification dependency
- Favorite already owns the active saved-shrine responsibility
- Keeping both Like and Favorite would retain overlapping concepts

Implementation direction:
- Remove Like from current Django model state through a normal forward migration
- Do not create the missing temples_like table only to make User.delete() succeed

---

### D2 - ConciergeRecommendationClickLog

Decision: REMOVE

Reason:
- No current live query references
- No active application wiring
- Recommendation analytics already has newer analytics/event responsibilities
- Future analytics requirements should be designed against the current analytics contract rather than retaining an unused legacy model

Implementation direction:
- Retire the model through a forward migration
- Do not restore the missing table solely for deletion-collector compatibility

---

### D3 - ConciergeHistory

Decision: REMOVE

Reason:
- No current ConciergeHistory.objects query path
- No active endpoint
- Existing serializer/import references are not active DB usage
- Migration 0047 and the current Django model disagree about shrine_id
- Restoring the historical table would reintroduce an unresolved model/schema contradiction
- Current concierge history responsibilities are handled by newer thread / visit / reflection / recommendation structures

Implementation direction:
- Retire the legacy ConciergeHistory model
- Remove remaining dead imports, serializer definitions, type annotations or dead helper code as part of the retirement scope
- Do not reconstruct the legacy table

---

### D4 - RankingLog

Decision: REMOVE

Reason:
- No current writer
- No current reader
- No current active product specification depends on RankingLog
- Current ranking functionality does not require this legacy model

Implementation direction:
- Retire RankingLog through a forward migration
- Ranking functionality itself remains in scope and is not being removed

---

### D5 - PlacesSeed / PlacesSeedState

Decision: RESTORE_NOW

Reason:
- Both models have live management-command read/write paths
- They belong to the shrine discovery / geographic expansion pipeline
- Their responsibility remains valid in the current product architecture
- PlacesSeedState is structurally dependent on PlacesSeed and must be restored together

Implementation direction:
- Restore both physical tables through a forward migration
- Derive canonical DDL mechanically from the existing migrations / Django schema
- Do not hand-write an approximate schema
- Keep Django ProjectState unchanged because the models already exist there

---

## Migration Strategy

The remediation must be split by responsibility.

### PR1 - RESTORE

Restore:

- places_seed
- places_seed_state

Expected migration:
- 0107

Goal:
Bring Production physical schema back into alignment for models that remain part of the product.

---

### PR2 - REMOVE

Retire:

- Like
- ConciergeRecommendationClickLog
- ConciergeHistory
- RankingLog

Expected migration:
- 0108

Goal:
Remove unused legacy models from Django state without creating missing Production tables first.

Because some target tables do not physically exist in Production, a plain DeleteModel must not be assumed safe.

The implementation must explicitly handle the difference between:
- Django ProjectState
- existing physical Production schema

The migration must be idempotent with regard to the currently missing tables.

---

## Explicit Non-Goals

This decision does NOT:

- remove Favorite
- remove the ranking feature
- remove current recommendation analytics
- remove ConciergeThread
- remove Visit
- remove ShrineReflection
- remove current recommendation logs/events
- rewrite historical django_migrations records
- use --fake
- manually CREATE or DROP Production tables outside migrations
- repair the historical nogis/canonical lineage itself

Historical migration-lineage normalization remains a separate architecture task.

---

## Safety Contract

Before Production application:

1. Local migration graph must remain valid
2. makemigrations --check must report no unintended model drift
3. Fresh DB migration must succeed
4. Current-style drifted DB reproduction must succeed
5. User deletion regression must be tested
6. Shrine deletion regression must be tested
7. Production migration plan must be reviewed before execution
8. Production application must remain app/target scoped
9. Bare migrate is prohibited for this remediation

---

## Final Decision

D1 Like: REMOVE
D2 ConciergeRecommendationClickLog: REMOVE
D3 ConciergeHistory: REMOVE
D4 RankingLog: REMOVE
D5 PlacesSeed / PlacesSeedState: RESTORE_NOW

Status: MOTHER_SHIP_DECIDED
