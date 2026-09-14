# Production Schema Remediation Post-Migration Gate

Date: 2026-09-14
Status: PASS
Scope: temples 0107 / 0108 post-migration Production verification

## Summary

Production was inspected through the existing SELECT-only credential bridge. No Production migration, restore, write, --fake, or django_migrations modification was performed in this gate.

At gate start, Production migration ledger already recorded both target migrations as applied:

- 0107_restore_places_seed_schema — 2026-09-13 21:46:12.406168+00
- 0108_remove_legacy_temples_models — 2026-09-13 22:35:18.341672+00

Because both migrations were already applied, migration execution was stopped and the gate changed to post-migration verification.

## Physical Schema Result

Expected and observed table state matched:

- places_seed: PRESENT
- places_seed_state: PRESENT
- temples_like: ABSENT
- temples_concierge_recommendation_click_log: ABSENT
- temples_conciergehistory: ABSENT
- temples_rankinglog: ABSENT

## Restored Schema Verification

places_seed and places_seed_state exposed the expected 25 columns in total. Primary-key and foreign-key structure matched the current model / migration contract:

- places_seed.seed_key: PRIMARY KEY
- places_seed_state.seed_id: PRIMARY KEY
- places_seed_state.seed_id -> places_seed.seed_key: FOREIGN KEY

Migration 0075 explicit indexes were all present:

- places_seed_pref_co_27f61e_idx
- places_seed_is_acti_04817c_idx
- places_seed_last_st_b771ca_idx
- places_seed_cooldow_b4ea36_idx

## Safety Evidence

The dedicated postcheck SQL passed scripts/migration_safety/guard.py check-readonly-sql with SAFE: ok before Production execution. Production verification was then executed only through scripts/migration_safety/readonly_query.sh.

## Gate Decision

PASS within the defined remediation contract.

The Production physical schema now matches the intended D1-D5 remediation outcome for the verified tables, columns, PK/FK structure, and explicit 0075 indexes.

This gate does not claim a complete audit of every default, constraint, index, row value, or unrelated Production schema object. It also does not attribute who or which deployment path applied 0107 / 0108; the ledger already contained both migrations when this gate began.

Status: PRODUCTION_SCHEMA_REMEDIATION_GATE_PASS
