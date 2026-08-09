#!/usr/bin/env bash
# Restore a dump produced by dump_readonly.sh into an isolated PostgreSQL
# database. Refuses to run unless guard.py confirms the target is a
# disposable local database — never Production, never an existing local
# dev database.
#
# Usage:
#   scripts/migration_safety/restore_isolated.sh <DUMP_DIR> <TARGET_DATABASE_URL>
#
# TARGET_DATABASE_URL must point at a database that:
#   - has host in {localhost, 127.0.0.1, ::1}
#   - has a name containing "audit", "restore_test", or "migration_safety"
#   - is not one of the protected existing local dev DB names
# (see guard.py for the exact allow-list — deny-by-default).
#
# This script does NOT create the target database. Create it first with
# `createdb <name>` so the intent to make a disposable DB is explicit and
# visible in your shell history, separate from this script's guard check.
#
# Override PSQL_BIN if the default `psql` on PATH doesn't match the
# target server's major version (see dump_readonly.sh for why this matters).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -ne 2 ]; then
  echo "[restore_isolated] usage: $0 <DUMP_DIR> <TARGET_DATABASE_URL>" >&2
  exit 2
fi

DUMP_DIR="$1"
TARGET_DATABASE_URL="$2"

PSQL_BIN="${PSQL_BIN:-psql}"

REDACTED_URL="$(python3 "${SCRIPT_DIR}/guard.py" redact "${TARGET_DATABASE_URL}")"
echo "[restore_isolated] target: ${REDACTED_URL}"

if ! python3 "${SCRIPT_DIR}/guard.py" check-restore-target "${TARGET_DATABASE_URL}"; then
  echo "[restore_isolated] BLOCKED: target failed the isolation-target guard. Aborting. See stderr above for reason." >&2
  exit 1
fi

for f in roles.sql schema.sql data.sql; do
  if [ ! -s "${DUMP_DIR}/${f}" ]; then
    echo "[restore_isolated] BLOCKED: ${DUMP_DIR}/${f} is missing or empty. Aborting." >&2
    exit 1
  fi
done

echo "[restore_isolated] applying roles.sql (best-effort; roles may already exist)..."
"${PSQL_BIN}" --dbname="${TARGET_DATABASE_URL}" --file="${DUMP_DIR}/roles.sql" --quiet || \
  echo "[restore_isolated] roles.sql had non-fatal errors (likely pre-existing roles); continuing"

echo "[restore_isolated] ensuring required extensions exist (postgis, pg_trgm — a --schema=public dump omits extension objects, since Supabase installs extensions outside public; this app's migrations only ever require these two, see backend/temples/migrations/0001_initial.py, 0027, 0036)..."
"${PSQL_BIN}" --dbname="${TARGET_DATABASE_URL}" --variable ON_ERROR_STOP=1 --quiet \
  --command "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pg_trgm;"

echo "[restore_isolated] applying schema.sql (dropping the redundant 'CREATE SCHEMA public;' line — a fresh target DB already has an empty public schema from createdb, so re-issuing it would error)..."
grep -v '^CREATE SCHEMA public;$' "${DUMP_DIR}/schema.sql" | "${PSQL_BIN}" --dbname="${TARGET_DATABASE_URL}" \
  --single-transaction --variable ON_ERROR_STOP=1 --quiet

echo "[restore_isolated] applying data.sql..."
"${PSQL_BIN}" --dbname="${TARGET_DATABASE_URL}" --single-transaction --variable ON_ERROR_STOP=1 \
  --command "SET session_replication_role = replica;" \
  --file="${DUMP_DIR}/data.sql" --quiet

echo "[restore_isolated] done."
