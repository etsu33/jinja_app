#!/usr/bin/env bash
# Regression tests for the readonly_query.sh hostname/credential leak fix.
#
# Incident: on a connection failure (e.g. DNS resolution failure), psql's
# own stderr — which can include hostname, port, user, and database name —
# used to flow straight through to the caller uncaptured. This suite proves
# the fix: the success path is unchanged, and every failure path produces
# only a generic message with no connection-target component, using FAKE
# credentials only. No real (Production or otherwise sensitive) credential
# is used, and no Production connection is attempted.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGSAFE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEST_DIR="$(mktemp -d /tmp/migration_safety_hostname_redaction.XXXXXX)"

cleanup() {
  rm -rf "${TEST_DIR}"
}
trap cleanup EXIT

FAIL() {
  echo "[hostname-redaction-test] FAIL: $1" >&2
  exit 1
}

assert_absent() {
  local output="$1" needle="$2" label="$3"
  if grep -Fq -- "${needle}" <<<"${output}"; then
    FAIL "output leaked ${label} (${needle})"
  fi
}

printf 'SELECT 1 AS ok;\n' > "${TEST_DIR}/select.sql"

# ---------------------------------------------------------------------------
# Scenario 1 + 10a: successful query — output and exit code unchanged.
# ---------------------------------------------------------------------------
echo "[hostname-redaction-test] === successful query (local postgres) ==="
SUCCESS_CRED="${TEST_DIR}/success-db.env"
printf 'export TEST_DATABASE_URL="postgres://%s@localhost:5432/postgres"\n' "$(whoami)" > "${SUCCESS_CRED}"
chmod 600 "${SUCCESS_CRED}"

set +e
SUCCESS_OUTPUT="$("${MIGSAFE_DIR}/readonly_query.sh" "${SUCCESS_CRED}" TEST_DATABASE_URL "${TEST_DIR}/select.sql" 2>&1)"
SUCCESS_STATUS=$?
set -e

[ "${SUCCESS_STATUS}" -eq 0 ] || FAIL "successful query returned exit ${SUCCESS_STATUS}, expected 0"
grep -Fq " ok " <<<"${SUCCESS_OUTPUT}" || FAIL "successful query did not return expected result row"
grep -Fq "[readonly_query] done." <<<"${SUCCESS_OUTPUT}" || FAIL "successful query missing done marker"
echo "[hostname-redaction-test] PASS: success path unchanged (exit 0, result present, done marker present)"

# ---------------------------------------------------------------------------
# Scenario 3 + 5-9: DNS-style failure — unresolvable fake hostname.
# ---------------------------------------------------------------------------
echo "[hostname-redaction-test] === DNS-style failure (fake unresolvable host) ==="
DNS_HOST="hlr-test-unresolvable-host.invalid"
DNS_USER="hlr_dns_test_user"
DNS_PASSWORD="hlr_dns_test_password"
DNS_DB="hlr_dns_test_database"
DNS_PORT="54329"
DNS_URL="postgresql://${DNS_USER}:${DNS_PASSWORD}@${DNS_HOST}:${DNS_PORT}/${DNS_DB}"
DNS_CRED="${TEST_DIR}/dns-fail-db.env"
printf 'export FAKE_DATABASE_URL="%s"\n' "${DNS_URL}" > "${DNS_CRED}"
chmod 600 "${DNS_CRED}"

set +e
DNS_OUTPUT="$("${MIGSAFE_DIR}/readonly_query.sh" "${DNS_CRED}" FAKE_DATABASE_URL "${TEST_DIR}/select.sql" 2>&1)"
DNS_STATUS=$?
set -e

[ "${DNS_STATUS}" -ne 0 ] || FAIL "DNS-style failure unexpectedly returned exit 0"
grep -Fq "[readonly_query] ERROR: read-only database query failed" <<<"${DNS_OUTPUT}" || FAIL "DNS-style failure missing generic error message"
assert_absent "${DNS_OUTPUT}" "${DNS_HOST}" "hostname"
assert_absent "${DNS_OUTPUT}" "${DNS_USER}" "username"
assert_absent "${DNS_OUTPUT}" "${DNS_PASSWORD}" "password"
assert_absent "${DNS_OUTPUT}" "${DNS_PORT}" "port"
assert_absent "${DNS_OUTPUT}" "${DNS_DB}" "database name"
assert_absent "${DNS_OUTPUT}" "${DNS_URL}" "full connection URL"
echo "[hostname-redaction-test] PASS: DNS-style failure produces only a generic message; exit ${DNS_STATUS}, no connection-target component leaked"

# ---------------------------------------------------------------------------
# Scenario 4 + 5-9: a second, distinct failure class (connection refused on
# an unreachable local port) — proves the fix isn't specific to DNS errors.
# ---------------------------------------------------------------------------
echo "[hostname-redaction-test] === credential-like URL failure (connection refused) ==="
REFUSED_HOST="127.0.0.1"
REFUSED_USER="hlr_refused_test_user"
REFUSED_PASSWORD="hlr_refused_test_password"
REFUSED_DB="hlr_refused_test_database"
REFUSED_PORT="1"
REFUSED_URL="postgresql://${REFUSED_USER}:${REFUSED_PASSWORD}@${REFUSED_HOST}:${REFUSED_PORT}/${REFUSED_DB}"
REFUSED_CRED="${TEST_DIR}/refused-fail-db.env"
printf 'export FAKE_DATABASE_URL="%s"\n' "${REFUSED_URL}" > "${REFUSED_CRED}"
chmod 600 "${REFUSED_CRED}"

set +e
REFUSED_OUTPUT="$("${MIGSAFE_DIR}/readonly_query.sh" "${REFUSED_CRED}" FAKE_DATABASE_URL "${TEST_DIR}/select.sql" 2>&1)"
REFUSED_STATUS=$?
set -e

[ "${REFUSED_STATUS}" -ne 0 ] || FAIL "connection-refused failure unexpectedly returned exit 0"
grep -Fq "[readonly_query] ERROR: read-only database query failed" <<<"${REFUSED_OUTPUT}" || FAIL "connection-refused failure missing generic error message"
assert_absent "${REFUSED_OUTPUT}" "${REFUSED_USER}" "username"
assert_absent "${REFUSED_OUTPUT}" "${REFUSED_PASSWORD}" "password"
assert_absent "${REFUSED_OUTPUT}" "${REFUSED_PORT}" "port"
assert_absent "${REFUSED_OUTPUT}" "${REFUSED_DB}" "database name"
assert_absent "${REFUSED_OUTPUT}" "${REFUSED_URL}" "full connection URL"
echo "[hostname-redaction-test] PASS: connection-refused failure produces only a generic message; exit ${REFUSED_STATUS}, no connection-target component leaked"

# ---------------------------------------------------------------------------
# Scenario 10b: exit-code contract preserved across both failure classes.
# ---------------------------------------------------------------------------
echo "[hostname-redaction-test] === exit-code preservation summary ==="
[ "${SUCCESS_STATUS}" -eq 0 ] || FAIL "expected success exit 0"
[ "${DNS_STATUS}" -ne 0 ] || FAIL "expected DNS-style failure exit non-zero"
[ "${REFUSED_STATUS}" -ne 0 ] || FAIL "expected connection-refused failure exit non-zero"
echo "[hostname-redaction-test] PASS: success=0, DNS-style failure=${DNS_STATUS}, connection-refused failure=${REFUSED_STATUS}"

echo ""
echo "[hostname-redaction-test] ==================================================="
echo "[hostname-redaction-test] ALL CHECKS PASSED. Only fake credentials were used;"
echo "[hostname-redaction-test] no Production connection was attempted."
echo "[hostname-redaction-test] ==================================================="
