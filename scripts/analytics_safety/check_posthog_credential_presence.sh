#!/usr/bin/env bash
# Check whether a PostHog read-only credential is present and well-formed,
# WITHOUT ever printing its value, host, project id, or any other
# identifying substring.
#
# Usage:
#   scripts/analytics_safety/check_posthog_credential_presence.sh <CREDENTIAL_FILE>
#
# CREDENTIAL_FILE: a shell-sourceable file living OUTSIDE this repository,
#   e.g. ~/.config/kami-musubi/posthog-readonly.env, containing:
#     export POSTHOG_PERSONAL_API_KEY="phx_..."
#     export POSTHOG_PROJECT_ID="12345"
#     export POSTHOG_HOST="https://us.posthog.com"   # optional, has a default
#
#   This tooling never creates or populates this file. A human (Mother
#   Ship) creates a Personal API Key in PostHog with ONLY the `query:read`
#   scope (see README.md "Creating the key") and writes it here once,
#   locally, outside the repository, chmod 600.
#
# Prints only: VAR_SET=0|1 per variable, and if set, a shape dict
# (length_bucket, has_whitespace). Never echoes the file, never uses
# `set -x`, never greps for the value.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ $# -ne 1 ]; then
  echo "[check_posthog_credential_presence] usage: $0 <CREDENTIAL_FILE>" >&2
  exit 2
fi

CRED_FILE="$1"

case "${CRED_FILE}" in
  "${REPO_ROOT}"/*)
    echo "[check_posthog_credential_presence] BLOCKED: credential file must be outside the repository." >&2
    exit 1
    ;;
esac

if [ ! -f "${CRED_FILE}" ]; then
  echo "VAR_SET=0"
  echo "[check_posthog_credential_presence] no credential file at that path yet — this is expected before a Personal API Key has been provisioned. See README.md." >&2
  exit 0
fi

PERMS="$(stat -f '%OLp' "${CRED_FILE}" 2>/dev/null || stat -c '%a' "${CRED_FILE}" 2>/dev/null)"
if [ "${PERMS}" != "600" ]; then
  echo "[check_posthog_credential_presence] BLOCKED: file permissions are ${PERMS}, expected 600 (owner read/write only). Run: chmod 600 ${CRED_FILE}" >&2
  exit 1
fi

for VAR_NAME in POSTHOG_PERSONAL_API_KEY POSTHOG_PROJECT_ID POSTHOG_HOST; do
  # Source in a throwaway subshell so nothing leaks into this script's own
  # environment, and the value never touches argv or stdout directly —
  # only guard.py's shape-only JSON output does.
  SHAPE_OUTPUT="$(
    bash -c "
      set -a
      # shellcheck disable=SC1090
      source '${CRED_FILE}'
      set +a
      printf '%s' \"\${${VAR_NAME}:-}\"
    " | python3 "${SCRIPT_DIR}/guard.py" describe-credential-shape
  )"

  VAR_IS_SET="$(bash -c "
    set -a
    # shellcheck disable=SC1090
    source '${CRED_FILE}'
    set +a
    [ -n \"\${${VAR_NAME}:-}\" ] && echo 1 || echo 0
  ")"

  echo "${VAR_NAME}_SET=${VAR_IS_SET}"
  if [ "${VAR_IS_SET}" = "1" ]; then
    echo "${VAR_NAME}_SHAPE=${SHAPE_OUTPUT}"
  fi
done
