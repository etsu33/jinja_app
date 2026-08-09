#!/usr/bin/env bash
# Run a SELECT-only SQL file against a Production (or any) database using a
# credential that lives outside this repo, WITHOUT the connection string
# ever appearing on the command line (visible via `ps`) or in any output.
#
# Usage:
#   scripts/migration_safety/readonly_query.sh <CREDENTIAL_FILE> <VAR_NAME> <SQL_FILE>
#
# Safety, in order:
#   1. CREDENTIAL_FILE must be outside this repo (guard.py check-dump-path).
#   2. CREDENTIAL_FILE must have mode 600.
#   3. SQL_FILE is checked with guard.py check-readonly-sql BEFORE the
#      credential is ever touched — every statement must start with
#      SELECT/SHOW/EXPLAIN(no ANALYZE)/WITH, or this refuses to run at all.
#   4. The credential is parsed into PGHOST/PGPORT/PGUSER/PGPASSWORD/
#      PGDATABASE/PGSSLMODE and exported inside a subshell via `eval`
#      (never printed — command substitution output is consumed silently).
#      `psql` is then invoked with NO connection string argument at all,
#      so the secret never appears in argv / `ps`.
#   5. No `set -x`, no echo/printenv of the credential, anywhere in this
#      script or the subshell it spawns.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ $# -ne 3 ]; then
  echo "[readonly_query] usage: $0 <CREDENTIAL_FILE> <VAR_NAME> <SQL_FILE>" >&2
  exit 2
fi

CRED_FILE="$1"
VAR_NAME="$2"
SQL_FILE="$3"

PSQL_BIN="${PSQL_BIN:-psql}"

if ! python3 "${SCRIPT_DIR}/guard.py" check-dump-path "${CRED_FILE}" "${REPO_ROOT}" 2>/dev/null; then
  echo "[readonly_query] BLOCKED: credential file must be outside the repository." >&2
  exit 1
fi

if [ ! -f "${CRED_FILE}" ]; then
  echo "[readonly_query] BLOCKED: credential file not found at ${CRED_FILE}. See README.md for local setup." >&2
  exit 1
fi

PERMS="$(stat -f '%OLp' "${CRED_FILE}" 2>/dev/null || stat -c '%a' "${CRED_FILE}" 2>/dev/null)"
if [ "${PERMS}" != "600" ]; then
  echo "[readonly_query] BLOCKED: file permissions are ${PERMS}, expected 600. Run: chmod 600 ${CRED_FILE}" >&2
  exit 1
fi

if [ ! -f "${SQL_FILE}" ]; then
  echo "[readonly_query] BLOCKED: SQL file not found: ${SQL_FILE}" >&2
  exit 1
fi

if ! python3 "${SCRIPT_DIR}/guard.py" check-readonly-sql "${SQL_FILE}"; then
  echo "[readonly_query] BLOCKED: SQL failed the read-only allow-list check (see reason above). Aborting before touching any credential." >&2
  exit 1
fi

echo "[readonly_query] SQL passed the read-only check. Connecting..." >&2

(
  set -a
  # shellcheck disable=SC1090
  source "${CRED_FILE}"
  set +a
  URL="$(eval "printf '%s' \"\${${VAR_NAME}:-}\"")"
  if [ -z "${URL}" ]; then
    echo "[readonly_query] BLOCKED: ${VAR_NAME} is not set in ${CRED_FILE}" >&2
    exit 1
  fi
  eval "$(printf '%s' "${URL}" | python3 "${SCRIPT_DIR}/guard.py" pg-env-exports)"
  unset URL
  # shellcheck disable=SC2086
  unset ${VAR_NAME}
  "${PSQL_BIN}" --set ON_ERROR_STOP=1 --no-psqlrc -f "${SQL_FILE}"
)

echo "[readonly_query] done." >&2
