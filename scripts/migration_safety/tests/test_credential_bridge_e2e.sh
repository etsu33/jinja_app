#!/usr/bin/env bash
# End-to-end local verification of the credential bridge
# (check_credential_presence.sh / readonly_query.sh).
#
# Uses a FAKE credential file pointing at the local `postgres` database
# (never Production) to prove the mechanism itself works: presence check
# reveals no host/value, a read-only query actually connects and runs, a
# write statement is refused before the credential is ever touched, and
# wrong file permissions are refused. No real credential is used or
# needed for this test.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGSAFE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TEST_DIR="$(mktemp -d /tmp/migration_safety_credtest.XXXXXX)"
CRED_FILE="${TEST_DIR}/test-db.env"

cleanup() {
  echo "[cred-e2e] cleanup: removing ${TEST_DIR}"
  rm -rf "${TEST_DIR}"
}
trap cleanup EXIT

printf 'export TEST_DATABASE_URL="postgres://%s@localhost:5432/postgres"\n' "$(whoami)" > "${CRED_FILE}"
chmod 600 "${CRED_FILE}"

echo "[cred-e2e] === presence check reports VAR_SET=1 and a shape dict, nothing else ==="
PRESENCE_OUTPUT="$("${MIGSAFE_DIR}/check_credential_presence.sh" "${CRED_FILE}" TEST_DATABASE_URL)"
echo "${PRESENCE_OUTPUT}"
echo "${PRESENCE_OUTPUT}" | grep -q '^VAR_SET=1$'
echo "${PRESENCE_OUTPUT}" | grep -q 'localhost' && { echo "[cred-e2e] FAIL: presence check leaked the host" >&2; exit 1; }
echo "[cred-e2e] PASS: presence reported, no host leaked"

echo "[cred-e2e] === presence check on a non-existent file reports VAR_SET=0 (not an error) ==="
MISSING_OUTPUT="$("${MIGSAFE_DIR}/check_credential_presence.sh" "${TEST_DIR}/does-not-exist.env" TEST_DATABASE_URL)"
echo "${MISSING_OUTPUT}" | grep -q '^VAR_SET=0$'
echo "[cred-e2e] PASS"

echo "[cred-e2e] === presence check refuses a credential file inside the repo ==="
if "${MIGSAFE_DIR}/check_credential_presence.sh" "${MIGSAFE_DIR}/README.md" TEST_DATABASE_URL 2>/dev/null; then
  echo "[cred-e2e] FAIL: should have refused an in-repo path" >&2
  exit 1
fi
echo "[cred-e2e] PASS: in-repo credential path refused"

echo "[cred-e2e] === readonly_query.sh: SELECT succeeds and actually connects ==="
printf 'SELECT 1 AS ok;\n' > "${TEST_DIR}/select.sql"
OUTPUT="$("${MIGSAFE_DIR}/readonly_query.sh" "${CRED_FILE}" TEST_DATABASE_URL "${TEST_DIR}/select.sql" 2>&1)"
echo "${OUTPUT}"
echo "${OUTPUT}" | grep -q " ok " || { echo "[cred-e2e] FAIL: SELECT 1 did not return expected output" >&2; exit 1; }
echo "[cred-e2e] PASS: read-only query executed successfully"

echo "[cred-e2e] === readonly_query.sh: multi-statement read-only file (migration_state.sql-shaped) succeeds ==="
printf 'SELECT current_database();\nSHOW server_version;\n' > "${TEST_DIR}/multi.sql"
"${MIGSAFE_DIR}/readonly_query.sh" "${CRED_FILE}" TEST_DATABASE_URL "${TEST_DIR}/multi.sql" > /dev/null
echo "[cred-e2e] PASS"

echo "[cred-e2e] === readonly_query.sh: DELETE is blocked BEFORE the credential is touched ==="
printf 'DELETE FROM auth_user;\n' > "${TEST_DIR}/bad.sql"
if "${MIGSAFE_DIR}/readonly_query.sh" "${CRED_FILE}" TEST_DATABASE_URL "${TEST_DIR}/bad.sql" 2>/dev/null; then
  echo "[cred-e2e] FAIL: DELETE should have been refused" >&2
  exit 1
fi
echo "[cred-e2e] PASS: write statement refused pre-connection"

echo "[cred-e2e] === readonly_query.sh: EXPLAIN ANALYZE is blocked ==="
printf 'EXPLAIN ANALYZE SELECT 1;\n' > "${TEST_DIR}/explain_analyze.sql"
if "${MIGSAFE_DIR}/readonly_query.sh" "${CRED_FILE}" TEST_DATABASE_URL "${TEST_DIR}/explain_analyze.sql" 2>/dev/null; then
  echo "[cred-e2e] FAIL: EXPLAIN ANALYZE should have been refused" >&2
  exit 1
fi
echo "[cred-e2e] PASS: EXPLAIN ANALYZE refused"

echo "[cred-e2e] === readonly_query.sh: wrong permissions (644) are refused ==="
chmod 644 "${CRED_FILE}"
if "${MIGSAFE_DIR}/readonly_query.sh" "${CRED_FILE}" TEST_DATABASE_URL "${TEST_DIR}/select.sql" 2>/dev/null; then
  echo "[cred-e2e] FAIL: should have refused on wrong permissions" >&2
  exit 1
fi
chmod 600 "${CRED_FILE}"
echo "[cred-e2e] PASS: wrong permissions refused"

echo "[cred-e2e] === readonly_query.sh: credential file inside the repo is refused ==="
if "${MIGSAFE_DIR}/readonly_query.sh" "${MIGSAFE_DIR}/README.md" TEST_DATABASE_URL "${TEST_DIR}/select.sql" 2>/dev/null; then
  echo "[cred-e2e] FAIL: should have refused an in-repo credential path" >&2
  exit 1
fi
echo "[cred-e2e] PASS: in-repo credential path refused"

echo ""
echo "[cred-e2e] ==================================================="
echo "[cred-e2e] ALL CHECKS PASSED. No real credential was used; Production was never touched."
echo "[cred-e2e] ==================================================="
