#!/usr/bin/env bash
# Check whether a Production credential is present and well-formed, WITHOUT
# ever printing its value, length, host, or any other identifying substring.
#
# Usage:
#   scripts/migration_safety/check_credential_presence.sh <CREDENTIAL_FILE> <VAR_NAME>
#
# CREDENTIAL_FILE: a shell-sourceable file (e.g. `export DATABASE_URL="..."`)
#   living OUTSIDE this repository. Never create this file with a real value
#   from this tooling — a human sets it up once, locally. See README.md.
# VAR_NAME: the variable name inside that file to check, e.g. DATABASE_URL.
#
# Prints only: VAR_SET=0|1, and if set, a dict of structural booleans
# (scheme_is_postgres, has_host, has_port, has_dbname, has_userinfo).
# Never echoes the file, never uses `set -x`, never greps for the value.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ $# -ne 2 ]; then
  echo "[check_credential_presence] usage: $0 <CREDENTIAL_FILE> <VAR_NAME>" >&2
  exit 2
fi

CRED_FILE="$1"
VAR_NAME="$2"

if ! python3 "${SCRIPT_DIR}/guard.py" check-dump-path "${CRED_FILE}" "${REPO_ROOT}" 2>/dev/null; then
  echo "[check_credential_presence] BLOCKED: credential file must be outside the repository." >&2
  exit 1
fi

if [ ! -f "${CRED_FILE}" ]; then
  echo "VAR_SET=0"
  echo "[check_credential_presence] no credential file at that path yet — this is expected before local setup is complete" >&2
  exit 0
fi

PERMS="$(stat -f '%OLp' "${CRED_FILE}" 2>/dev/null || stat -c '%a' "${CRED_FILE}" 2>/dev/null)"
if [ "${PERMS}" != "600" ]; then
  echo "[check_credential_presence] BLOCKED: file permissions are ${PERMS}, expected 600 (owner read/write only). Run: chmod 600 ${CRED_FILE}" >&2
  exit 1
fi

# Source in a throwaway subshell so nothing leaks into this script's own
# environment beyond the single value we need, and that value never
# touches argv or stdout directly — only guard.py's boolean-only output does.
SHAPE_OUTPUT="$(
  bash -c "
    set -a
    # shellcheck disable=SC1090
    source '${CRED_FILE}'
    set +a
    printf '%s' \"\${${VAR_NAME}:-}\"
  " | python3 "${SCRIPT_DIR}/guard.py" describe-url-shape
)"

VAR_IS_SET="$(bash -c "
  set -a
  # shellcheck disable=SC1090
  source '${CRED_FILE}'
  set +a
  [ -n \"\${${VAR_NAME}:-}\" ] && echo 1 || echo 0
")"

echo "VAR_SET=${VAR_IS_SET}"
if [ "${VAR_IS_SET}" = "1" ]; then
  echo "SHAPE=${SHAPE_OUTPUT}"
fi
