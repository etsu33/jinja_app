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
| `sql/pre_migration_snapshot.sql` | SELECT-only. Run immediately before a backup/migration attempt; records the baseline to compare against later. |
| `sql/post_migration_verification.sql` | SELECT-only. Run after migration; every value must match the pre-migration snapshot except the two migrations you intentionally applied. |
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
