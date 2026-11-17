# Migration Safety Tooling — Backup / Restore Runbook

Tooling to make Production migrations (starting with `users 0006` and
`temples 0090-0093`) safely reversible. Everything here is read-only with
respect to Production, or operates only on local/isolated databases.

**This tooling never runs a command against Production automatically.**
Every script here requires a `DATABASE_URL`-style argument explicitly —
there is no default, no ambient credential lookup, and nothing is wired
into CI or a deploy pipeline. A human decides when and against what to
run these, every time.

Background reading (read in this order):

1. [`docs/audit/supabase-backup-capability-gate.md`](../../docs/audit/supabase-backup-capability-gate.md) — why Supabase's Free plan has no native backup/PITR
2. [`docs/audit/production-manual-backup-restore-gate.md`](../../docs/audit/production-manual-backup-restore-gate.md) — why manual dump/restore was chosen, and the credential-access block that stopped it from being exercised against real Production
3. [`docs/audit/production-migration-execution-gate.md`](../../docs/audit/production-migration-execution-gate.md) — why Production migration execution stays paused until this Gate passes
4. [`docs/audit/production-all-app-migration-state-audit.md`](../../docs/audit/production-all-app-migration-state-audit.md) — the `users 0006` / `temples 0090-0093` content this tooling protects

## What's here

| File | Purpose |
|---|---|
| `guard.py` | Pure-Python safety guard. Allow-list (not deny-list) check for restore targets; repo-boundary check for dump/credential-file paths; credential redaction and structural-shape-only description for logging; read-only SQL statement allow-list; URI → `PG*` env-var export so a credential never needs to appear on a command line. No DB/network code. |
| `check_credential_presence.sh` | Reports whether a credential file/variable is set and well-formed — booleans only, never the value, host, or length. |
| `readonly_query.sh` | Runs a SQL file against a database using a credential file outside the repo, after checking every statement is read-only. Connects via `PG*` env vars so the credential never appears in `ps`. See "Credential Bridge" below. |
| `dump_readonly.sh` | Read-only logical dump (`pg_dumpall --roles-only` + `pg_dump --schema-only` + `pg_dump --data-only`, `public` schema only) of a URL you pass explicitly. Logs no connection-target component and keeps the URL out of child-process argv. |
| `restore_isolated.sh` | Restores a dump into a target URL only after `guard.py` confirms the target is a disposable local database. Logs no connection-target component and keeps the URL out of `psql` argv. |
| `sql/migration_state.sql` | SELECT-only. Per-app latest applied migration. |
| `sql/pre_migration_snapshot.sql` | SELECT-only. **Historical runbook for `users 0006` / `temples 0090-0093` only.** Run immediately before that backup/migration attempt; records the baseline to compare against later. Not used for, and not updated for, the `temples 0095-0098` preflight below — that is a separate, later migration boundary with its own file. |
| `sql/post_migration_verification.sql` | SELECT-only. **Historical runbook for `users 0006` / `temples 0090-0093` only**, paired with `pre_migration_snapshot.sql` above. Run after that migration; every value must match the pre-migration snapshot except the two migrations intentionally applied. Same scope note as above — not reused for `temples 0095-0098`. |
| `sql/temples_0095_0098_preflight.sql` | SELECT-only. **`temples` 0095→0096→0097→0098 Production-apply preflight — use this immediately before applying those four, and only those four.** Confirms `temples` migration ledger position (0094 applied, 0095-0098 not) and, section by section, the exact precondition each of the four migrations' own `forward` implementation checks before mutating anything — derived by reading each migration's code and tests, not guessed. See "Runbook: temples 0095-0098 Preflight" below. |
| `sql/users_0011_0015_preflight.sql` | SELECT-only. **`users` 0011→0012→0013→0014→0015 Production-apply preflight — only those five.** Ledger position (0010 applied, 0011-0015 not), schema pre-state, baseline counts, every condition under which 0011 / 0013 / 0015's `RunPython` raises, the rows 0011 / 0013 will write, and a pre-image of the billing rows they change (internal ids and billing state only). See "Runbook: users 0011-0015" below. |
| `sql/users_0011_0015_postcheck.sql` | SELECT-only. Post-check for the same five migrations, compared number by number with the saved preflight output. |
| `tests/test_guard.py` | Unit tests for `guard.py`, including the credential-bridge functions (`describe_url_shape`, `is_readonly_sql`, `pg_env_exports`). No DB required. |
| `tests/test_backup_restore_e2e.sh` | End-to-end local test: builds a `users=0005`/`temples=0089` local database, dumps it, restores it into a second isolated database through the actual guarded scripts, verifies they match, applies `users 0006` + `temples 0090-0093` to the restored copy, verifies again, rolls back. Never touches Production. |
| `tests/test_credential_bridge_e2e.sh` | End-to-end local test of the credential bridge using a fake local credential (never Production): presence check leaks nothing, a read-only query actually connects, writes/`EXPLAIN ANALYZE`/wrong-permissions/in-repo-path are all refused pre-connection. |
| `tests/test_backup_logging.sh` | No-network regression test using fake clients. Proves successful and failed dumps never log URL, username, password, hostname, port, database name, or query parameters while retaining safe file-size/status metadata. |

## The core safety property

`guard.py`'s restore-target check is an **allow-list**, not a deny-list of
"things that look like Production." This tooling does not know
Production's real hostname, so guessing at patterns to block would be
incomplete by construction. Instead, a restore target must satisfy *all*
of:

- host is `localhost`, `127.0.0.1`, or `::1`
- database name is not one of the protected existing local databases
  (`jinja_db`, `jinja_app_dev`, `jinja_test`, `postgres`, ...)
- database name contains `audit`, `restore_test`, or `migration_safety`

Anything else — including every real Production hostname, whatever it
turns out to be — is blocked by default. `restore_isolated.sh` calls this
check before touching the target and aborts with a non-zero exit if it
fails.

The dump-path check works the other way: a dump's *output path* must
resolve outside the git repository, so a Production dump can never end up
staged for commit.

## Connection-target logging contract

Backup and restore tooling must never print a string that describes its
connection target. This includes the full URL and every component: username,
password, hostname, port, database name, and query/SSL parameters. Masking only
userinfo is insufficient because a redacted URL still reveals the target.

The scripts print generic connection-configured messages, convert URLs to
libpq `PG*` environment variables before invoking clients, and replace client
connection diagnostics with generic failures. Safe metadata remains visible:
operation start, roles/schema/data phase, output file names and sizes, generic
safety status, and success/failure. Dump files must remain outside the repo.

## Credential Bridge

**Problem:** an AI assistant (Claude Code / Codex) driving this tooling
runs each shell command as a *separate* process — `export FOO=bar` in one
command does not carry over to the next one (verified empirically: it
doesn't). So "export the credential in your shell" doesn't actually work
for AI-assisted runs the way it would in a human's interactive terminal.
The fix used here is a credential **file** that gets sourced fresh inside
a single script invocation, never split across multiple commands.

**Setup (you do this yourself, once, locally):**

```bash
mkdir -p ~/.config/kami-musubi
cp ~/.config/kami-musubi/production-db.env.example ~/.config/kami-musubi/production-db.env
# edit production-db.env yourself — fill in the real value.
# Never paste it into a chat with an AI assistant. Never commit it.
chmod 600 ~/.config/kami-musubi/production-db.env
```

The file just needs one line: `export DATABASE_URL="postgres://..."` (or
whatever variable name you choose — you pass the name explicitly to every
script that uses it, nothing is assumed).

**How an AI session uses it without ever seeing the value:**

```bash
# Presence check — prints only booleans (VAR_SET, scheme_is_postgres,
# has_host, has_port, has_dbname, has_userinfo). No host, no length, no value.
scripts/migration_safety/check_credential_presence.sh ~/.config/kami-musubi/production-db.env DATABASE_URL

# Read-only query — refuses to run anything but SELECT/SHOW/EXPLAIN(no
# ANALYZE)/WITH, checked BEFORE the credential is ever touched. Connects
# via PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE/PGSSLMODE (parsed from
# the URI internally) so the credential never appears in `ps` output —
# psql is invoked with no connection string on its command line at all.
scripts/migration_safety/readonly_query.sh ~/.config/kami-musubi/production-db.env DATABASE_URL scripts/migration_safety/sql/migration_state.sql
```

Both scripts refuse to run if the credential file is inside this
repository, or if its permissions aren't exactly `600`.

**What this bridge does NOT do:** it doesn't stop a human from misusing
`psql` directly with the same file, and it doesn't encrypt the file at
rest (ordinary filesystem permissions only — adequate for a single-user
laptop, not a shared machine). It also can't verify the connection string
you put in the file is actually read-only at the database-role level;
read-only-ness is enforced at the SQL-statement layer by
`readonly_query.sh`'s allow-list, not by trusting the role's grants.

## Running the tests

```bash
# Unit tests (fast, no DB):
backend/.venv/bin/python3 -m pytest scripts/migration_safety/tests/test_guard.py -v

# End-to-end local drill (needs local PostgreSQL with postgis available,
# ~1-2 minutes — it replays temples migrations 0001-0093):
scripts/migration_safety/tests/test_backup_restore_e2e.sh

# Credential bridge end-to-end drill (seconds, uses a fake local
# credential — never Production):
scripts/migration_safety/tests/test_credential_bridge_e2e.sh

# Backup logging contract (seconds, fake clients only; no DB/network):
scripts/migration_safety/tests/test_backup_logging.sh
```

All three are safe to run repeatedly and clean up everything they create
(both `_e2e.sh` tests use a `trap ... EXIT` that removes temp databases/
files even on failure).

None of these are wired into any CI workflow's `testpaths`
(`backend/pytest.ini` only scopes `temples/tests`, `users/tests`,
`tests`) — they are standalone tooling, run manually. Wiring the unit
tests into CI would be a reasonable follow-up but is out of scope here
and wasn't requested.

## Runbook: Manual Backup Route (Phase 1)

1. Obtain a read-only-capable Production connection string and set up the
   Credential Bridge above (`~/.config/kami-musubi/production-db.env`,
   `chmod 600`). **Never paste it into chat with an AI assistant; never
   commit it.**
2. Confirm your local `pg_dump`/`pg_dumpall` major version matches
   Production's Postgres version (check via Supabase Dashboard → Database
   settings, or `SELECT version();`). If they don't match, set
   `PG_DUMP_BIN` / `PG_DUMPALL_BIN` to a matching Homebrew install (e.g.
   `postgresql@18`) — mismatched major versions make `pg_dumpall` refuse
   to run at all (`server version mismatch`); this was hit and fixed
   during development of this tooling, see `dump_readonly.sh` comments.
3. Pick an output directory **outside this repository**, e.g.
   `~/kami-musubi-backups/$(date +%Y%m%d%H%M%S)/`.
4. Run, sourcing the credential file and invoking `dump_readonly.sh` in
   the *same* command (an AI-driven session can't rely on a separate
   `export` step persisting — see "Credential Bridge" above; a human
   typing this directly in their own terminal could instead just
   `export`/run interactively, but the one-liner below works either way):
   ```bash
   ( set -a; source ~/.config/kami-musubi/production-db.env; set +a; \
     scripts/migration_safety/dump_readonly.sh "$DATABASE_URL" ~/kami-musubi-backups/<timestamp>/ )
   ```
   `dump_readonly.sh` receives the connection string as its own argument, then
   consumes it through `guard.py pg-env-exports` and unsets it before invoking
   `pg_dump`/`pg_dumpall`. Database-client argv and success/failure logs contain
   no connection URL or target component.
5. Confirm all three files (`roles.sql`, `schema.sql`, `data.sql`) exist
   and have non-zero size (the script prints sizes; it also warns on any
   zero-byte file).
6. Record the timestamp and file sizes in the execution gate document —
   this becomes the "backup timestamp" referenced by the pre-migration
   checklist.

Supabase's own CLI (`supabase db dump`) remains the officially recommended
tool for a real Production dump against Supabase specifically (see the
Backup Capability Gate doc) — it handles Supabase-managed schema/extension
placement automatically. `dump_readonly.sh` here uses plain `pg_dump`
because that's what could actually be exercised end-to-end without
Supabase CLI installed; it needed two fixes to work at all (server-version
mismatch, and `public`-schema-only dumps needing `postgis`/`pg_trgm`
extensions pre-created on restore — see "What broke during testing"
below). If Supabase CLI is used for a real Production dump instead, the
resulting `roles.sql`/`schema.sql`/`data.sql` files are restored the same
way, through `restore_isolated.sh`.

## Runbook: Restore Verification Route (Phase 2)

1. Create a disposable target database whose name contains `audit`,
   `restore_test`, or `migration_safety` — e.g.:
   ```bash
   createdb kami_musubi_migration_safety_$(date +%Y%m%d%H%M%S)
   ```
2. Restore into it:
   ```bash
   scripts/migration_safety/restore_isolated.sh ~/kami-musubi-backups/<timestamp>/ \
     "postgres://$(whoami)@localhost:5432/<the db you just created>"
   ```
   If `guard.py` rejects the target, the script exits non-zero before
   touching the database at all — fix the naming/host, don't work around
   the check.
3. Run `sql/migration_state.sql` against the restored DB and compare to
   what you expect (`users=0005`, `temples=0089` before any migration has
   been applied to the restore source).
4. Run the aggregate-count queries in `sql/pre_migration_snapshot.sql`
   against both the original Production values you recorded and the
   restored copy; they must match.
5. Only after 3-4 both check out is the backup considered verified.

## Runbook: Pre-Migration Checklist (Phase 3)

Before ever running a real migration command against Production:

- [ ] Run `sql/migration_state.sql` against Production (read-only) —
      confirm `users=0005`, `temples=0089`, and that no other app's state
      has drifted from the last audit
- [ ] Complete the Manual Backup Route above against Production
- [ ] Complete the Restore Verification Route above against the resulting
      dump
- [ ] Record the backup timestamp, dump file sizes, and restore
      verification result in the execution gate document
- [ ] Re-run `sql/migration_state.sql` against Production one more time
      immediately before migrating — if it has changed since step 1,
      **stop** (`PRODUCTION_MIGRATION_STATE_CHANGED`, see the execution
      gate doc)

**How fresh must the backup be?** No fixed number is asserted here
without a real timing measurement. As a starting point: treat a backup as
stale if more than the time it took to *also* complete the restore
verification route has passed since it was taken — i.e., don't sit on a
verified-good dump for hours before migrating. Mother Ship should set an
explicit staleness threshold once real Production dump/restore timing is
known; this hasn't been measured against Production and is marked
`UNVERIFIED` accordingly.

## Runbook: `temples` 0095-0098 Preflight

**This is a separate, later precondition check from the Phase 1-3 backup/
restore runbook above.** `sql/pre_migration_snapshot.sql` and
`sql/post_migration_verification.sql` are the historical runbook for `users
0006` / `temples 0090-0093` — they check that earlier migration boundary
and are not edited or reused here. `sql/temples_0095_0098_preflight.sql` is
its own file, scoped only to confirming Production is in the expected
pre-state for applying `temples` **0095 → 0096 → 0097 → 0098**, in that
order, as a group.

Each of that file's sections was derived by reading the named migration's
own `forward` implementation and its own test suite — not guessed — so it
checks exactly the condition that migration's code checks before mutating
anything:

- **Section 0** — `django_migrations` ledger: `0094` applied, `0095-0098`
  not; a STOP-worthy output if that's not the case.
- **Section 1** (`0095`) — shrine 107 / 108 identity, empty `goriyaku` +
  zero `goriyaku_tags`, and that every canonical PASS label already exists
  in the `GoriyakuTag` master. `0095` is **best-effort, not fail-closed** —
  a deviation makes that shrine a silent no-op, not an error.
- **Section 2** (`0096`) — shrine 10 / 22 identity, target `ShrineHistory`
  rows, existing-vs-to-be-created state of each target `ShrineKnowledgeSource`
  (matched by `url` + `source_type`, never pk), and existing history↔Source
  relation state.
- **Section 3** (`0097`) — shrine 21 / 22 identity, required `GoriyakuTag`
  rows + required relations, and the optional `地域安泰` tag's 3-state
  STRICT_EXACT contract (row absent = safe; row + relation present = safe;
  row present with relation absent = **will raise and block the whole
  migration**). `0095`/`0096` are best-effort; `0097` (and `0098`) are
  **fail-closed** — any violation here changes zero rows.
- **Section 4** (`0098`) — shrine 1 identity, the exact 5-field stray
  `ShrineKnowledgeSource` semantic identity, the two target `ShrineDeity`
  rows, and that the Source is cited by exactly those two relations and no
  `ShrineHistory`. Fail-closed, same as `0097`.

**How to run** (read-only; never paste the credential into chat):

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/temples_0095_0098_preflight.sql
```

Run it once well ahead of the migration window, and again immediately
before the actual `migrate` command — treat any change in Section 0's
ledger output between the two runs as a reason to stop and re-derive.

## Runbook: users 0011-0015

Applies `users` **0011 → 0012 → 0013 → 0014 → 0015** to Production, for the
case where code that depends on them is already deployed (symptom: `column
users_userprofile.legacy_premium_until does not exist` when a `UserProfile`
is loaded). Separate from every runbook above; uses only its own two files,
`sql/users_0011_0015_preflight.sql` and `sql/users_0011_0015_postcheck.sql`.

What the five migrations do (read from their code, not guessed):

| migration | schema | data |
|---|---|---|
| `0011_separate_premium_entitlements` | adds `UserProfile.legacy_premium_until`, `UserProfile.account_entitlement_disabled`, `PremiumPassPurchase.effective_period_end` | **rewrites existing rows.** For every profile with no Stripe subscription/price id: moves `current_period_end` to `legacy_premium_until` (non-Pass users), then sets `current_period_end = NULL`, `subscription_status = 'inactive'`, `cancel_at_period_end = false`. Copies `period_end_after` to `effective_period_end` on every Pass row. Raises instead of guessing on 7 conditions (preflight 3-R). |
| `0012_premium_subscription` | creates `users_premiumsubscription` | none |
| `0013_backfill_stripe_premium_subscriptions` | none | inserts one `users_premiumsubscription` row per profile with a Stripe subscription id. Raises on 7 conditions (preflight 4-R). Reverse is a no-op. |
| `0014_apple_storekit_receipt` | creates `users_applestorekitreceipt` | none (reverse refuses if Apple billing data exists) |
| `0015_apple_billing_environments` | adds `PremiumPassPurchase.environment`, replaces Pass / subscription unique constraints | for each Apple Pass row, looks up its receipt; **raises for any Apple Pass row**, because 0014 just created the receipts table empty (preflight 5-R). |

Each migration is its own transaction on PostgreSQL. A raise rolls back
**that migration only**; the ones before it stay applied. So if 0013 raises
during `migrate users 0015`, 0011's data rewrite is already committed. That is
why this runbook applies them one at a time and checks every raise condition
before the first one.

### Step 0 — Before starting

- `RUN_MIGRATIONS_ON_START` is `0` on Render.
- No deploy during the window.

### Step 1 — Preflight (read-only), well ahead of the window

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/users_0011_0015_preflight.sql \
  > ~/kami-musubi-backups/<timestamp>/users_0011_0015_preflight.txt
```

Keep the output **outside the repository**. STOP if any of these holds:

- Section 0 or 1 differs from its "Expected" comment.
- Any column of 3-R, 4-R or 5-R is non-zero. Fixing the offending row is a
  Production write and a separate decision (prefer re-syncing from Stripe over
  editing values by hand). Re-run the preflight after any fix.

Sections 3-P and 4-P are the pre-image of every billing row 0011 / 0013 will
touch. 0011's reverse cannot restore `subscription_status` exactly, so this
output and the dump are the recovery record.

### Step 2 — Backup

Follow "Runbook: Manual Backup Route (Phase 1)" above:

1. Check Production's major version with `SELECT version();` and use a
   matching `pg_dump` / `pg_dumpall` (`PG_DUMP_BIN` / `PG_DUMPALL_BIN`).
2. Dump:
   ```bash
   ( set -a; source ~/.config/kami-musubi/production-db.env; set +a; \
     scripts/migration_safety/dump_readonly.sh "$DATABASE_URL" \
       ~/kami-musubi-backups/<timestamp>-users-0011-0015/ )
   ```
3. Confirm `roles.sql` / `schema.sql` / `data.sql` are all non-zero and record
   the timestamp and sizes.
4. Restore into a disposable local database ("Runbook: Restore Verification
   Route (Phase 2)"). Whether to wait for this while Production is failing is
   the operator's decision; the dump itself is not optional.

### Step 3 — Preflight again, immediately before `migrate`

Re-run Step 1. STOP if Section 0 changed. Compare Section 4 too: 0013 judges
"Premium now" with `timezone.now()` at the moment it runs, and the preflight
uses `now()` at the moment it runs.

### Step 4 — Apply one at a time (Render Shell)

```bash
python manage.py migrate users 0011 --noinput
python manage.py migrate users 0012 --noinput
python manage.py migrate users 0013 --noinput
python manage.py migrate users 0014 --noinput
python manage.py migrate users 0015 --noinput
```

After each command, `python manage.py showmigrations users` must show exactly
that one more `[X]`. Never use `migrate` without an app and target. Keep the
gap between 0012 and 0013 short: the service is live, and a Stripe webhook that
creates a `PremiumSubscription` row in between sends 0013 down its
"existing row" branch, which raises if that row's user or price differs from
the profile.

### Step 5 — Post-check

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/users_0011_0015_postcheck.sql
```

Compare with the saved preflight: row counts equal to 2-a, `legacy_premium_until`
count equal to 3-E `e2`, inserted rows equal to 4-E, every `expected_0` column
zero, the 7 constraints / partial unique indexes present and the 2 removed ones
absent. Then check at runtime: login, MyPage and the billing status API return
no 500, Render logs show no `UndefinedColumn`, and the next startup logs
`[migration-check] OK all migrations applied`. Finally, check Stripe's webhook
deliveries that failed during the outage and resend them if needed.

### If something goes wrong

**0013 raised during `migrate` — (a)**

- 0013 is rolled back; the ledger stops at 0012 with 0011's rewrite committed.
- Entitlement still works for Stripe subscribers: when a user has no
  `PremiumSubscription` row, `temples/services/billing_state.py` falls back to
  the profile fields, which 0013 never changes.
- Fix the offending row (see Step 1), re-run preflight Section 4, then run
  `python manage.py migrate users 0013 --noinput` again.

**0013 succeeded but inserted wrong rows — (b)**

Rows inserted by 0013 are exactly those with `source = 'stripe'` and
`last_event_at IS NULL`: the application always sets `last_event_at` when it
writes a row (`users/services/premium_subscription.py`). Deleting them puts
those users back on the profile-based check, i.e. the pre-0013 behaviour.
Do not use `migrate users 0012` for this: it would have to unapply 0015 and
0014 first, and 0013's reverse is a no-op, so the rows would stay anyway.

> **⚠ Write operation. Not a runnable file on purpose. Requires a human
> decision, a fresh backup, and the saved preflight 4-E total.**
> Run by hand in one transaction; COMMIT only if the deleted count equals the
> preflight 4-E total, otherwise ROLLBACK.
>
> ```text
> BEGIN;
> DELETE FROM users_premiumsubscription
> WHERE source = 'stripe'
>   AND last_event_at IS NULL
>   AND created_at BETWEEN '<migrate start, UTC>' AND '<migrate end, UTC>'
> RETURNING id, user_id;
> -- deleted count = preflight 4-E total  -> COMMIT;
> -- anything else                        -> ROLLBACK;
> ```

**Last resort — (c)**

Restore the Step 2 dump (Restore Verification Route, then a Production restore
decided by the owner). Everything written after the dump is lost.

**0011**

- Raised during `migrate`: rolled back completely, including the added
  columns; the ledger stays at 0010.
- Succeeded but must be undone: `python manage.py migrate users 0010` works
  (it unapplies 0015 → 0011), but 0011's reverse writes
  `subscription_status = 'active'` for restored deadlines, so a profile that was
  `trialing` comes back as `inactive` and a granted profile as `active`. Its
  reverse also refuses if later data (account stop, newly separated deadlines)
  would be merged. Restore exact values from preflight 3-P.

### Verified locally, and not verified

Verified on a local PostgreSQL 16 database migrated to `users 0010` with
Django 5.2.17 (the `users` app only), with seeded profiles covering each
billing shape (no billing, granted deadline, Stripe active / canceled /
cancel-scheduled, a two-purchase Pass chain, an odd `trialing` legacy row):

- Both SQL files pass `guard.py check-readonly-sql`.
- Clean case: preflight predictions (rows 0011 writes, rows and status mix 0013
  inserts) matched the real `migrate users 0015` result, and every post-check
  `expected_0` was 0.
- 0011 raise (Pass deadline ≠ profile deadline): preflight 3-R `r6` = 1, and
  `migrate` raised exactly that; ledger stayed at 0010, no column added.
- 0013 raise (`past_due` with a future deadline): preflight 4-R `r7` = 1, and
  `migrate` raised in 0013; ledger stopped at 0012, 0011 applied, 0 rows in
  `users_premiumsubscription`.
- `migrate users 0010` from that state reversed 0012 and 0011; a `trialing`
  row came back as `inactive`.

Not verified: Production row counts and which raise conditions Production hits,
Production's PostgreSQL version (17.6 in the June audit), Supabase-specific
behaviour, Render Shell's working directory, and the 0015 Apple-Pass raise
(read from code only; no Apple Pass row was seeded).

## Runbook: Migration Execution Candidates (Phase 4) — reference only, not endorsement

These commands are documented for completeness; **do not run them without
completing the Pre-Migration Checklist first, and only with Mother Ship's
explicit go-ahead.** This tooling does not execute them.

```bash
# users first (smaller, independently reversible):
python manage.py migrate users 0006 --noinput

# then temples:
python manage.py migrate temples 0093 --noinput
```

Deliberately **not** `python manage.py migrate` with no app name — that
form applies every pending migration across every app, which is exactly
the confounding risk documented in
`docs/audit/migration-execution-method-reality-audit.md` Phase 4 and
confirmed to actually apply here (`users 0006` is pending, not just
`temples`) in `docs/audit/production-all-app-migration-state-audit.md`.

After each command: run `sql/post_migration_verification.sql` before
proceeding to the next one. If `users 0006` verification fails, do not
run the `temples` migration.

## What broke during local testing (keep this — it's the point of testing)

Building `tests/test_backup_restore_e2e.sh` surfaced three real problems
that a design-only Runbook would not have caught:

1. **`pg_dumpall` refuses cross-major-version connections.** The local
   Postgres *server* here is 18.0; the default `pg_dump`/`pg_dumpall` on
   `PATH` is 16.10 (Homebrew's generic symlink). `pg_dumpall` hard-fails
   with "server version mismatch" rather than degrading. Fixed by adding
   `PG_DUMP_BIN`/`PG_DUMPALL_BIN`/`PSQL_BIN` overrides to the scripts.
   **Before a real Production dump, confirm the Postgres major version
   Supabase reports and use a matching client — do not assume the
   default `pg_dump` on any machine matches.**
2. **A `--schema=public` dump's `CREATE SCHEMA public;` collides with a
   freshly-created target database**, which already has an empty
   `public` schema by default. Fixed by stripping that one line before
   restoring (a fresh `createdb` target always has this collision; it is
   not a sign of a bad dump).
3. **PostGIS/pg_trgm types are undefined on the restore target** unless
   those extensions are created there first — a `--schema=public`-only
   dump does not carry extension objects (Supabase installs extensions
   outside `public` by design). Fixed by running
   `CREATE EXTENSION IF NOT EXISTS postgis;` /
   `... pg_trgm;` on the target before applying `schema.sql`.

All three are now handled inside `restore_isolated.sh` — a real restore
drill should not hit any of them. But they are exactly the kind of thing
a paper Runbook would have missed, which is why Phase 7 required actually
running this end-to-end rather than just describing it.

## Known gaps (be honest about these)

- Every fix above was validated against a **local** Postgres 18 instance,
  not against Supabase's actual Postgres version or its actual extension
  layout. Supabase may install `postgis`/`pg_trgm` in a schema other than
  what a plain local install uses, or may already have them present in
  every project by default — this needs to be confirmed once a real
  Production dump is attempted with Mother Ship's own credentials.
- `roles.sql` restore is treated as best-effort (`|| continue on error`)
  because roles like the local Unix user commonly already exist on a dev
  machine. Against a truly fresh restore target this may hide a real
  roles-restore failure — inspect its output, don't just trust the
  "continuing" message.
- No timing data exists for how long a real Production dump/restore
  takes. The "backup freshness" guidance above is a placeholder, not a
  measured number.
- This tooling was never run against Production, because no Production
  credential is available to this environment (see the Manual Backup
  Restore Gate doc). Everything above is proven against a local
  simulation of Production's known shape, not against Production itself.
- `readonly_query.sh` / `check_credential_presence.sh`'s permission check
  (`stat -f '%OLp' ... || stat -c '%a' ...`) assumes a BSD-style `stat -f`
  that either succeeds with the requested format or fails cleanly to
  stderr. On at least one Linux sandbox with GNU coreutils `stat`, `-f`
  instead means "filesystem status" and both prints unrelated filesystem
  info to stdout *and* still exits non-zero, so the `||` fallback to
  `stat -c` never triggers and the script reports a false "BLOCKED: file
  permissions are ..." even on an actual `600` file. This reproduces
  identically against pre-existing scripts and SQL (`migration_state.sql`,
  `test_readonly_query_hostname_redaction.sh`) — it is a pre-existing
  environment-portability gap, not something introduced by
  `temples_0095_0098_preflight.sql`. The read-only-SQL check itself
  (`guard.py check-readonly-sql`, `is_readonly_sql`) does not use `stat` and
  is unaffected — verified directly against the new SQL file and covered by
  `tests/test_guard.py::TestTemples0095_0098PreflightSqlIsReadonly`. On a
  real macOS/BSD `stat` (or a Linux fix using `stat -c` first) this
  end-to-end path is expected to work as designed.
