# Analytics Safety Tooling — PostHog Read-only Access

Tooling to read aggregate PostHog analytics data (Knowledge recommendation
quality metrics) without ever being able to mutate PostHog, and without a
credential ever appearing in `ps`, shell history, or a raised exception's
text.

**This tooling never connects to real PostHog on its own.** It has no
built-in Personal API Key, does not create one, and does not prompt for
one. A human (Mother Ship) provisions a credential file, once, outside
this repository — every script here reads it explicitly, there is no
default and nothing is wired into CI or a deploy pipeline.

Background reading:

1. [`docs/audit/knowledge-recommendation-analytics-baseline-readiness.md`](../../docs/audit/knowledge-recommendation-analytics-baseline-readiness.md) — why this tooling exists (no PostHog read access existed before it)
2. [`docs/audit/posthog-readonly-analytics-access.md`](../../docs/audit/posthog-readonly-analytics-access.md) — this Foundation's design record
3. [`docs/audit/knowledge-recommendation-analytics-contract.md`](../../docs/audit/knowledge-recommendation-analytics-contract.md) — the event/property contract these queries read
4. [`docs/audit/posthog-production-read-access-gate.md`](../../docs/audit/posthog-production-read-access-gate.md) — the first real Production smoke test, which found the raw-response leak fixed by `guard.sanitize_query_result()`
5. [`docs/audit/posthog-readonly-output-minimization.md`](../../docs/audit/posthog-readonly-output-minimization.md) — that fix's design record

## What's here

| File | Purpose |
|---|---|
| `guard.py` | Pure-Python safety guard. Allow-list (not deny-list) check for the one HTTP endpoint this tooling may ever call; mutation-keyword rejection for HogQL query text; credential shape description (never the value); error-text redaction. No network code. |
| `check_posthog_credential_presence.sh` | Reports whether `POSTHOG_PERSONAL_API_KEY` / `POSTHOG_PROJECT_ID` / `POSTHOG_HOST` are set in a credential file — booleans and coarse shape only, never the values. |
| `posthog_readonly_query.py` | Sends exactly one query to PostHog: `POST {host}/api/projects/{project_id}/query/` (PostHog's HogQL query endpoint — POST by HTTP method, but semantically read-only: it executes a query and returns rows, it does not mutate state, per [PostHog's own API docs](https://posthog.com/docs/api/queries)). Every other PostHog endpoint is unreachable through this module by construction. On any failure, prints one fixed generic message and exits non-zero — never the credential, host, project id, or raw response body. |
| `posthog_baseline_report.py` | Runs the fixed named query set in `QUERY_CONTRACT` and prints one aggregate-only JSON report. `--fixture <dir>` mode reads canned per-query JSON instead of calling PostHog — no network call, no credential needed. Without `--fixture` and without a credential configured, exits with `POSTHOG_READ_CREDENTIAL_REQUIRED` rather than fabricating a result. |
| `fixtures/sample_baseline/` | Canned all-zero fixture files (one per query in `QUERY_CONTRACT`) for `--fixture` dry runs and tests. Not real data. |
| `tests/test_guard.py` | Unit tests for `guard.py`: endpoint allow-list, HogQL mutation-keyword rejection, credential-shape description, error redaction. No network. |
| `tests/test_posthog_readonly_query.py` | Tests for `posthog_readonly_query.py` using `requests_mock` (a fake, obviously-not-real credential value): success, 401/403, timeout, DNS/connection failure, malformed response, 5xx, missing credential, mutation-attempt rejection, endpoint-allow-list rejection, secret non-exposure in every error path, fixture mode. |
| `tests/test_posthog_baseline_report.py` | Tests for `posthog_baseline_report.py`: fixture mode, credential-required gate, every contract query is called exactly once in real mode (mocked), PII guard (no query template references a free-text field), every query template passes the read-only HogQL check. |

## Creating the key (a human does this, not this tooling)

1. Sign in to PostHog, go to **Personal API keys** in account settings.
2. Click **+ Create a personal API Key**.
3. Under scopes, select **only** `query:read`. Do not grant `*` (full
   access), event capture, feature flag, project settings, person, or
   billing scopes — this tooling never needs them and never uses them.
4. Note the numeric **Project ID** (Project settings) you want to query.
5. Create a file **outside this repository**, e.g.
   `~/.config/kami-musubi/posthog-readonly.env`, containing:

   ```bash
   export POSTHOG_PERSONAL_API_KEY="phx_..."
   export POSTHOG_PROJECT_ID="12345"
   export POSTHOG_HOST="https://us.posthog.com"   # or your region's host
   ```

6. `chmod 600` that file.
7. Verify presence (never prints the value):

   ```bash
   scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
   ```

Never paste the key value into a chat session with an AI assistant or
anyone else. This tooling never asks for it directly — only via the
environment, after you `source` the credential file yourself.

## Running a query

```bash
set -a; source ~/.config/kami-musubi/posthog-readonly.env; set +a
python3 scripts/analytics_safety/posthog_readonly_query.py \
  --query "SELECT count() FROM events WHERE event = 'recommendation_quality'"
```

## Running the baseline report

```bash
set -a; source ~/.config/kami-musubi/posthog-readonly.env; set +a
python3 scripts/analytics_safety/posthog_baseline_report.py
```

Or, without any credential, to see the report shape:

```bash
python3 scripts/analytics_safety/posthog_baseline_report.py \
  --fixture scripts/analytics_safety/fixtures/sample_baseline
```

## The core safety properties

- **Endpoint allow-list, not deny-list.** `guard.is_endpoint_allowed()`
  only returns true for `POST /api/projects/{project_id}/query/`.
  Nothing else — event capture, feature flags, project settings, person
  deletion — is reachable through this tooling's code paths, because no
  function here accepts an arbitrary path.
- **HogQL mutation-keyword rejection as defense in depth.** Even though
  the query endpoint is itself read-only by PostHog's design, every
  query text is checked for `INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/
  `TRUNCATE`/`CREATE`/`GRANT`/`REVOKE`/`MERGE` before it is sent.
- **Credential never appears in `ps`, shell history, or an exception.**
  The key is read only from the environment, sent only in the
  `Authorization` header, and every failure path raises one of a fixed
  set of generic `ERROR_*` messages — never the exception's raw text,
  the request URL, or the response body.
- **Fixture mode makes zero network calls.** `--fixture` is the default
  way to develop against and test this tooling; a real credential is
  only needed for `--fixture`-less runs.
- **Query contract is a fixed, reviewed list.** `QUERY_CONTRACT` in
  `posthog_baseline_report.py` is the only set of queries the baseline
  report will ever send — no caller-supplied query text reaches
  PostHog through that command. Every template references only event
  names, enum property values, boolean property values, and counts —
  never free-text properties, person properties, emails, or names (see
  PII Guard tests in `tests/test_posthog_baseline_report.py`).
- **Output minimization.** The report contains only counts, rates
  (where computed), enum labels, and the query period — never a
  per-user/per-thread/per-event raw row dump. Enforced by
  `guard.sanitize_query_result()`: every successful response — real or
  `--fixture` — is reduced to an allow-list of `results`/`columns`/
  `error` before it reaches any caller. PostHog's own response
  metadata (`cache_key`/`clickhouse`/`hogql`/`query_metadata`/etc.,
  which can embed the project's internal team id) never reaches
  stdout. This was added after the first real Production smoke test
  found the gap — see
  [`docs/audit/posthog-readonly-output-minimization.md`](../../docs/audit/posthog-readonly-output-minimization.md).

## What this Foundation does not do

- It does not create, register, or rotate a PostHog Personal API Key.
- `posthog_readonly_query.py` and `posthog_baseline_report.py` are
  fully tested against mocked HTTP; the sanitizer has also been
  verified once against a real Production response (see
  [`posthog-production-read-access-gate.md`](../../docs/audit/posthog-production-read-access-gate.md)
  and
  [`posthog-readonly-output-minimization.md`](../../docs/audit/posthog-readonly-output-minimization.md)),
  but this remains a thin slice of real-world coverage.
- The `ctr_by_classification` / save-rate / visit-intent "segmented by
  Knowledge classification" queries
  (`UNVERIFIED_SEGMENTED_QUERY_CONTRACT` in
  `posthog_baseline_report.py`) are a best-effort HogQL design, not
  verified against real data. Treat their exact correctness as
  unconfirmed until run once against real PostHog and checked by a
  human.
