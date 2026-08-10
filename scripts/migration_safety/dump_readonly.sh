#!/usr/bin/env bash
# Take a read-only logical dump (roles/schema/data, public schema only) of
# a PostgreSQL database, using plain pg_dump.
#
# This script never has a default DATABASE_URL. It only ever dumps a URL
# you pass in explicitly, and only ever runs SELECT-equivalent (read-only)
# pg_dump commands — no destructive statement is possible via this script.
#
# Usage:
#   scripts/migration_safety/dump_readonly.sh <SOURCE_DATABASE_URL> <OUTPUT_DIR>
#
# Output: <OUTPUT_DIR>/roles.sql, schema.sql, data.sql
#
# pg_dump/pg_dumpall refuse to talk to a server whose major version is
# newer than the client (a real risk: Homebrew's default `pg_dump` may not
# match the target server's version — this bit us during local testing,
# see docs/audit/migration-safety-tooling.md). Override the binaries used
# via PG_DUMP_BIN / PG_DUMPALL_BIN if the default `pg_dump`/`pg_dumpall`
# on PATH don't match the source server's version, e.g.:
#   PG_DUMP_BIN=/opt/homebrew/opt/postgresql@18/bin/pg_dump \
#   PG_DUMPALL_BIN=/opt/homebrew/opt/postgresql@18/bin/pg_dumpall \
#     scripts/migration_safety/dump_readonly.sh ...
#
# Safety:
#   - OUTPUT_DIR is checked with guard.py and rejected if it resolves
#     inside this git repository (prevents an accidental `git add`).
#   - No connection-target component is logged: not URL, user, password,
#     hostname, port, database name, or query parameters.
#   - The URL is converted to libpq PG* environment variables before the
#     dump clients run, so child-process arguments contain no connection URL.
#   - Client stderr is replaced with a generic failure message because libpq
#     connection errors can include hostname, port, user, and database name.
#   - Dump is scoped to `--schema=public` only (see docs/audit/
#     production-manual-backup-restore-gate.md Phase 2 for why).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ $# -ne 2 ]; then
  echo "[dump_readonly] usage: $0 <SOURCE_DATABASE_URL> <OUTPUT_DIR>" >&2
  exit 2
fi

SOURCE_DATABASE_URL="$1"
OUTPUT_DIR="$2"

PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"
PG_DUMPALL_BIN="${PG_DUMPALL_BIN:-pg_dumpall}"

echo "[dump_readonly] source connection configured"

if ! python3 "${SCRIPT_DIR}/guard.py" check-dump-path "${OUTPUT_DIR}" "${REPO_ROOT}"; then
  echo "[dump_readonly] BLOCKED: output dir must be outside the repository. Aborting." >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# Consume the URL without printing it and keep it out of pg_dump/pg_dumpall
# argv. Never print the generated exports: they contain the credential.
eval "$(printf '%s' "${SOURCE_DATABASE_URL}" | python3 "${SCRIPT_DIR}/guard.py" pg-env-exports)"
unset SOURCE_DATABASE_URL

echo "[dump_readonly] dumping roles (read-only)..."
if ! "${PG_DUMPALL_BIN}" --roles-only --no-role-passwords \
  > "${OUTPUT_DIR}/roles.sql" 2>/dev/null; then
  echo "[dump_readonly] FAILED: roles dump command failed; connection details suppressed" >&2
  exit 1
fi

echo "[dump_readonly] dumping schema (read-only, public schema only)..."
if ! "${PG_DUMP_BIN}" --schema-only --schema=public --no-owner --no-privileges \
  > "${OUTPUT_DIR}/schema.sql" 2>/dev/null; then
  echo "[dump_readonly] FAILED: schema dump command failed; connection details suppressed" >&2
  exit 1
fi

echo "[dump_readonly] dumping data (read-only, public schema only)..."
if ! "${PG_DUMP_BIN}" --data-only --schema=public --no-owner --no-privileges \
  > "${OUTPUT_DIR}/data.sql" 2>/dev/null; then
  echo "[dump_readonly] FAILED: data dump command failed; connection details suppressed" >&2
  exit 1
fi

for f in roles.sql schema.sql data.sql; do
  size=$(wc -c < "${OUTPUT_DIR}/${f}" | tr -d ' ')
  if [ "${size}" -eq 0 ]; then
    echo "[dump_readonly] WARNING: ${f} is empty (size=0)" >&2
  fi
  echo "[dump_readonly] ${f}: ${size} bytes"
done

echo "[dump_readonly] done. Files never leave ${OUTPUT_DIR} automatically — do not commit them."
