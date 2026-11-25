# Read-only Query Hostname/Credential Leak Remediation

**Base commit:** `e349956468e9b512f74cf2bd24fc15574c41ed2b` (`develop`)

## 1. Incident classification

`READONLY_QUERY_CONNECTION_ERROR_METADATA_EXPOSURE`

While running the very first Production read-only query for Batch 10 seed
preparation (see `docs/audit/knowledge-batch10-target-selection.md`), the
connection attempt failed with a DNS resolution error. `psql`'s own native
connection-failure message was printed directly to this operator's tool
output, and that message included the real Production database hostname
that `psql` had attempted to resolve.

Scope of the finding:

- The leak is a **connection-failure metadata exposure**, not a SQL-content
  problem. The SQL file itself is validated by `guard.py check-readonly-sql`
  before the credential is ever touched, and was not implicated.
- `scripts/migration_safety/readonly_query.sh` never echoes, logs, or
  `set -x`-prints the credential value itself. The leak came from `psql`'s
  own stderr on a failed connection attempt, not from this repo's tooling
  printing a secret it held.
- The underlying DNS/connectivity problem that caused the query to fail is
  explicitly **out of scope** for this remediation — Production
  connectivity itself was not investigated or touched, and no retry was
  attempted.
- No Production write occurred, before, during, or after this incident.
- The actual leaked hostname is not reproduced anywhere in this document,
  in the code, in commit messages, or in test fixtures. All examples and
  regression tests below use clearly-fake values only (e.g.
  `hlr-test-unresolvable-host.invalid`).

## 2. Affected script and root cause

**Affected script:** `scripts/migration_safety/readonly_query.sh`

**Root cause:** the script's final step inside the credential-bearing
subshell invoked `psql` directly with no stderr redirection:

```bash
"${PSQL_BIN}" --set ON_ERROR_STOP=1 --no-psqlrc -f "${SQL_FILE}"
```

The subshell exports real `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/
`PGDATABASE`/`PGSSLMODE` values (via `guard.py pg-env-exports`) so that
`psql` can connect without the connection string ever appearing in argv.
This part of the design was already correct. But when `psql` itself fails
to *connect* (as opposed to a query-level error after a successful
connection), libpq's own diagnostic message — which can include hostname,
port, username, and database name — is written to `psql`'s stderr. Because
that stderr stream was never captured or redirected, it flowed straight
through the subshell and the script to the caller, unfiltered.

This is the same general class of risk that `scripts/migration_safety/
dump_readonly.sh` and `scripts/migration_safety/restore_isolated.sh`
already defend against (see their inline comments: "libpq connection
errors can include hostname, port, user, and database name"). Those two
scripts already redirect every `pg_dump`/`pg_dumpall`/`psql` invocation's
stderr to `/dev/null` and replace it with a generic, safe failure message.
`readonly_query.sh` was the one script in this family that had not yet
been given the same treatment.

## 3. Remediation

Minimal, targeted fix reusing the existing repo convention (no new
mechanism introduced):

```bash
if ! "${PSQL_BIN}" --set ON_ERROR_STOP=1 --no-psqlrc -f "${SQL_FILE}" 2>/dev/null; then
  echo "[readonly_query] ERROR: read-only database query failed" >&2
  exit 1
fi
```

- `2>/dev/null` discards `psql`'s own stderr unconditionally (both the
  connection-failure case and any post-connection query-level error case),
  so no libpq diagnostic text — of any kind — can reach the caller.
- On failure, the script prints exactly one generic, safe line and exits
  non-zero. No raw driver text, no `DATABASE_URL`, no hostname, username,
  password, port, database name, or SSL parameters are ever included.
- On success, `psql`'s stdout (the query results) is completely untouched
  — only stderr is affected — so the existing caller contract (stdout
  carries results, exit 0 on success) is fully preserved.
- No ad-hoc string-substitution redaction was used. No new credential
  handling, logging, or `set -x` was introduced. The fix is confined to
  the single unredirected `psql` invocation that was the actual leak
  point; nothing else in the script changed behavior.

## 4. Success-path result

Verified locally against the local `postgres` database (never Production),
using the same fixture pattern as the existing
`scripts/migration_safety/tests/test_credential_bridge_e2e.sh`:

- `SELECT 1 AS ok;` returns the expected result row on stdout.
- Exit code is `0`.
- The `[readonly_query] done.` completion marker is printed, matching
  pre-fix behavior exactly.

## 5. Failure-path result

Verified locally using exclusively fake, non-Production credentials
(fake hostname, fake username, fake password, fake database, fake port —
see the regression test file for exact values):

- Connection failure (DNS-style, unresolvable fake hostname) now produces
  only: `[readonly_query] ERROR: read-only database query failed`, with a
  non-zero exit code.
- Connection failure (connection-refused, unreachable fake local port)
  produces the same single generic line, with a non-zero exit code.
- No raw `psql`/libpq connection error text reaches the caller in either
  case.

## 6. Hostname disclosure test

Automated (see Section 9). Both failure-simulation scenarios assert that
the fake hostname value does not appear anywhere in the script's combined
stdout+stderr output. Both assertions pass.

## 7. Credential disclosure test

Automated (see Section 9). Both failure-simulation scenarios assert that
the fake username, fake password, fake port, fake database name, and the
full fake connection URL do not appear anywhere in the output. All
assertions pass.

## 8. Exit-code preservation

- Success path: exit `0` (unchanged from pre-fix behavior).
- Failure path (both simulated failure classes): exit `1` (non-zero,
  matching the pre-fix contract that callers must treat non-zero as
  failure — pre-fix, `psql`'s own exit code would also have been non-zero
  under `set -e`, so the success/failure signal callers rely on is
  unchanged).

## 9. Regression tests

New file: `scripts/migration_safety/tests/test_readonly_query_hostname_redaction.sh`

Covers all required scenarios, using fake credentials only (no Production
connection is attempted anywhere in this suite):

1. Successful query — result present, exit 0.
2. Failed query — generic error message present, exit non-zero.
3. DNS-style failure (unresolvable fake hostname) — generic message only.
4. Connection-refused failure (fake credentials against an unreachable
   local port) — a second, distinct failure class, generic message only.
5. Hostname not present in failure output (both failure classes).
6. Username not present in failure output (both failure classes).
7. Password not present in failure output (both failure classes).
8. Port not present in failure output (both failure classes).
9. Database name not present in failure output (both failure classes).
10. Exit-code contract: success = 0, both failure classes = non-zero.

Also re-ran unchanged, still passing:

- `scripts/migration_safety/tests/test_credential_bridge_e2e.sh`
- `scripts/migration_safety/tests/test_backup_logging.sh`
- `scripts/migration_safety/tests/test_guard.py` (pytest, 47 tests)

## 10. Related safety-tool audit

Statically audited for the same raw-stderr-leak pattern:

- **`scripts/migration_safety/dump_readonly.sh`** — already safe. Every
  `pg_dump`/`pg_dumpall` invocation already redirects stderr to
  `/dev/null` and replaces it with a generic "connection details
  suppressed" message. No change needed. (This script's existing pattern
  is in fact what the `readonly_query.sh` fix above reuses.)
- **`scripts/migration_safety/check_credential_presence.sh`** — not
  exposed to this leak class at all. This script never invokes `psql` or
  `pg_dump` and never opens a database connection; it only parses a URL
  string locally via `guard.py describe-url-shape`, which already returns
  structural booleans only (never the raw value). No finding.
- **`scripts/migration_safety/restore_isolated.sh`** (reviewed
  proactively as the fourth script in this family, though not explicitly
  named in the remediation request) — already safe. Every `psql`
  invocation already redirects stderr to `/dev/null` with a generic
  failure message. No change needed.

**Finding: non-blocking, no further action required.** `readonly_query.sh`
was the only script in the `migration_safety` family with an unredirected
`psql` invocation.

## 11. Secret / hostname scan

- `git diff --check`: clean (no whitespace/conflict-marker issues).
- `gitleaks detect --no-git --source <changed files>`: `no leaks found`.
- Manual grep of the diff and the new test file for known real
  infrastructure fragments (e.g. hosting-provider domains): none found.
  All hostnames/credentials appearing in the diff or the new test file are
  clearly-fake placeholder values (e.g. `hlr-test-unresolvable-host.invalid`,
  `hlr_dns_test_user`) constructed specifically for this remediation and do
  not correspond to any real system.

## 12. Remaining limitations

- This fix only addresses `readonly_query.sh`'s final `psql` invocation,
  which was the confirmed, actual leak point. It does not change the
  earlier `eval "$(... | guard.py pg-env-exports)"` step; a malformed URL
  could theoretically make `urlparse` raise an exception whose message
  echoes a fragment of the input, which would not be suppressed by this
  fix. This is a much lower-probability, different failure mode than the
  confirmed incident (a well-formed URL failing to connect) and was left
  out of scope to keep this a minimal, targeted fix rather than a
  speculative rewrite; it is noted here for future reference.
- Production connectivity itself (the underlying DNS/network issue that
  triggered the original failed query) was not investigated or fixed by
  this remediation, per explicit instruction. The next Production
  read-only query attempt may still fail for the same underlying
  connectivity reason — but if it does, it will now fail safely, with no
  hostname or credential disclosure.
- This remediation did not re-attempt any Production connection, and none
  is planned as part of this task.
