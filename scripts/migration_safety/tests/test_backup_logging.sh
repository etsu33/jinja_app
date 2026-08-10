#!/usr/bin/env bash
# Logging-contract regression tests for dump_readonly.sh.
# Uses fake client binaries only: no database or network connection occurs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGSAFE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEST_DIR="$(mktemp -d /tmp/migration_safety_logging.XXXXXX)"
SUCCESS_DUMP="${TEST_DIR}/success"
FAIL_DUMP="${TEST_DIR}/failure"
FAKE_DUMP="${TEST_DIR}/fake-pg-dump"
FAKE_DUMPALL="${TEST_DIR}/fake-pg-dumpall"
FAIL_DUMP_BIN="${TEST_DIR}/failing-pg-dump"

DUMMY_USER="logging-regression-user"
DUMMY_PASSWORD="logging-regression-password"
DUMMY_HOST="logging-target.example.invalid"
DUMMY_PORT="6543"
DUMMY_DB="logging_regression_database"
DUMMY_QUERY="sslmode=require"
DUMMY_URL="postgresql://${DUMMY_USER}:${DUMMY_PASSWORD}@${DUMMY_HOST}:${DUMMY_PORT}/${DUMMY_DB}?${DUMMY_QUERY}"

cleanup() {
  rm -rf "${TEST_DIR}"
}
trap cleanup EXIT

cat > "${FAKE_DUMP}" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' 'fake dump content'
FAKE
cat > "${FAKE_DUMPALL}" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' 'fake roles content'
FAKE
cat > "${FAIL_DUMP_BIN}" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "simulated client error user=${PGUSER} password=${PGPASSWORD} host=${PGHOST} port=${PGPORT} database=${PGDATABASE}" >&2
exit 1
FAKE
chmod +x "${FAKE_DUMP}" "${FAKE_DUMPALL}" "${FAIL_DUMP_BIN}"

assert_no_connection_detail() {
  local output="$1"
  local token
  for token in "${DUMMY_USER}" "${DUMMY_PASSWORD}" "${DUMMY_HOST}" "${DUMMY_PORT}" "${DUMMY_DB}" "${DUMMY_QUERY}" "${DUMMY_URL}"; do
    if grep -Fq "${token}" <<<"${output}"; then
      echo "[logging-test] FAIL: output leaked a connection-target component" >&2
      exit 1
    fi
  done
}

echo "[logging-test] === successful fake dump ==="
SUCCESS_OUTPUT="$(
  PG_DUMP_BIN="${FAKE_DUMP}" PG_DUMPALL_BIN="${FAKE_DUMPALL}" \
    "${MIGSAFE_DIR}/dump_readonly.sh" "${DUMMY_URL}" "${SUCCESS_DUMP}" 2>&1
)"
assert_no_connection_detail "${SUCCESS_OUTPUT}"
grep -Fq '[dump_readonly] source connection configured' <<<"${SUCCESS_OUTPUT}"
grep -Eq 'roles\.sql: [1-9][0-9]* bytes' <<<"${SUCCESS_OUTPUT}"
grep -Eq 'schema\.sql: [1-9][0-9]* bytes' <<<"${SUCCESS_OUTPUT}"
grep -Eq 'data\.sql: [1-9][0-9]* bytes' <<<"${SUCCESS_OUTPUT}"
grep -Fq '[dump_readonly] done.' <<<"${SUCCESS_OUTPUT}"
echo "[logging-test] PASS: safe metadata remains and all target components are hidden"

echo "[logging-test] === failed fake dump ==="
set +e
FAIL_OUTPUT="$(
  PG_DUMP_BIN="${FAIL_DUMP_BIN}" PG_DUMPALL_BIN="${FAKE_DUMPALL}" \
    "${MIGSAFE_DIR}/dump_readonly.sh" "${DUMMY_URL}" "${FAIL_DUMP}" 2>&1
)"
FAIL_STATUS=$?
set -e
if [ "${FAIL_STATUS}" -eq 0 ]; then
  echo "[logging-test] FAIL: failing client unexpectedly returned success" >&2
  exit 1
fi
assert_no_connection_detail "${FAIL_OUTPUT}"
grep -Fq 'connection details suppressed' <<<"${FAIL_OUTPUT}"
echo "[logging-test] PASS: failed-client diagnostics cannot leak connection details"

echo "[logging-test] ALL CHECKS PASSED. No database connection was attempted."
