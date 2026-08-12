#!/usr/bin/env python3
"""Knowledge Recommendation Analytics baseline report (read-only).

Combines a fixed set of named, read-only HogQL queries (see
QUERY_CONTRACT below) into one aggregate-only report. Every query goes
through posthog_readonly_query.run_readonly_hogql_query(), which enforces
the endpoint allow-list and the mutation-keyword rejection in
guard.py — this module adds no new HTTP path.

Output contract: the report contains only counts, rates, enum labels,
and the query period. It never contains a per-user/per-thread/per-event
row dump, and no query template in QUERY_CONTRACT selects a raw
property that could carry consultation text, email, name, or other PII
(see PII Guard in README.md and
docs/audit/posthog-readonly-analytics-access.md).

Two modes:

  --fixture <dir>   Read canned per-query JSON files from a local
                     directory instead of calling PostHog. No network
                     call is made. Use this for dry runs and tests.
  (no --fixture)    Call the real PostHog query endpoint for each named
                     query, using POSTHOG_PERSONAL_API_KEY/
                     POSTHOG_PROJECT_ID/POSTHOG_HOST from the
                     environment. Requires those to be set — see
                     check_posthog_credential_presence.sh. If they are
                     not set, this exits non-zero with
                     POSTHOG_READ_CREDENTIAL_REQUIRED rather than
                     guessing or fabricating a result.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from posthog_readonly_query import (  # noqa: E402
    PostHogReadOnlyQueryError,
    run_readonly_hogql_query,
)

# PR #2384 Production deployment timestamp (Vercel production deployment
# dpl_AcehvHCZesf5j8xYqwqK4d7k9xwC, per
# docs/audit/knowledge-recommendation-analytics-observability.md). The
# default query window never reaches further back than this, so
# pre-rollout events (which cannot carry the new properties) are not
# counted as if they were missing-property post-rollout events.
DEFAULT_ROLLOUT_SINCE = "2026-08-12T04:12:15Z"

# Every query this tool will ever send. Each entry is read-only HogQL
# (enforced again, redundantly, by guard.is_readonly_hogql at call time)
# selecting only: event name, enum property values, boolean property
# values, and counts. No query here selects free-text properties,
# person properties, emails, or names.
QUERY_CONTRACT: dict[str, str] = {
    "recommendation_quality_count": (
        "SELECT count() AS count FROM events "
        "WHERE event = 'recommendation_quality' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "classification_distribution": (
        "SELECT properties.knowledge_backing_class AS classification, count() AS count "
        "FROM events "
        "WHERE event = 'recommendation_quality' "
        "AND timestamp >= {since} AND timestamp < {until} "
        "GROUP BY classification"
    ),
    "property_completeness": (
        "SELECT "
        "countIf(isNotNull(properties.knowledge_backing_class)) AS knowledge_backing_class_present, "
        "countIf(isNotNull(properties.deity_knowledge_used)) AS deity_knowledge_used_present, "
        "countIf(isNotNull(properties.history_knowledge_used)) AS history_knowledge_used_present, "
        "count() AS total "
        "FROM events "
        "WHERE event = 'recommendation_quality' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "unique_recommendation_sessions": (
        "SELECT count(DISTINCT properties.threadId) AS count FROM events "
        "WHERE event = 'concierge_result_impression' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "impression_count": (
        "SELECT count() AS count FROM events WHERE event = 'concierge_result_impression' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "detail_transition_count": (
        "SELECT count() AS count FROM events WHERE event = 'shrine_detail_transition' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "save_count": (
        "SELECT count() AS count FROM events WHERE event = 'shrine_decision' "
        "AND properties.action = 'save' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
    "route_open_count": (
        "SELECT count() AS count FROM events WHERE event = 'route_open' "
        "AND timestamp >= {since} AND timestamp < {until}"
    ),
}

# These two require joining recommendation_quality's classification onto
# impression/click events by (threadId, shrineId, recommendationRank), per
# the join key contract in
# docs/audit/knowledge-recommendation-analytics-contract.md §7. They are
# recorded here as a best-effort design and have never been executed
# against real PostHog data (no credential exists in this session, see
# docs/audit/knowledge-recommendation-analytics-baseline-readiness.md) —
# treat their exact HogQL correctness as UNVERIFIED until run once against
# real data and checked by a human.
UNVERIFIED_SEGMENTED_QUERY_CONTRACT: dict[str, str] = {
    "ctr_by_classification": (
        "SELECT rq.properties.knowledge_backing_class AS classification, "
        "count(DISTINCT imp.uuid) AS impressions, "
        "count(DISTINCT dt.uuid) AS detail_transitions "
        "FROM events AS imp "
        "LEFT JOIN events AS dt "
        "ON dt.event = 'shrine_detail_transition' "
        "AND dt.properties.threadId = imp.properties.threadId "
        "AND dt.properties.shrineId = imp.properties.shrineId "
        "AND dt.properties.recommendationRank = imp.properties.recommendationRank "
        "LEFT JOIN events AS rq "
        "ON rq.event = 'recommendation_quality' "
        "AND rq.properties.threadId = imp.properties.threadId "
        "AND rq.properties.shrineId = imp.properties.shrineId "
        "AND rq.properties.recommendationRank = imp.properties.recommendationRank "
        "WHERE imp.event = 'concierge_result_impression' "
        "AND imp.timestamp >= {since} AND imp.timestamp < {until} "
        "GROUP BY classification"
    ),
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_query(template: str, *, since: str, until: str) -> str:
    return template.format(since=repr(since), until=repr(until))


def _run_real(since: str, until: str) -> dict:
    results: dict = {}
    for name, template in QUERY_CONTRACT.items():
        query_text = _render_query(template, since=since, until=until)
        results[name] = run_readonly_hogql_query(query_text)
    return results


def _run_fixture(fixture_dir: str) -> dict:
    results: dict = {}
    for name in QUERY_CONTRACT:
        path = os.path.join(fixture_dir, f"{name}.json")
        if not os.path.exists(path):
            results[name] = None
            continue
        with open(path, encoding="utf-8") as f:
            results[name] = json.load(f)
    return results


def build_report(*, since: str, until: str, fixture_dir: str | None) -> dict:
    if fixture_dir:
        raw = _run_fixture(fixture_dir)
    else:
        raw = _run_real(since, until)

    return {
        "period": {"since": since, "until": until},
        "queries": raw,
        "note": (
            "Aggregates only. No per-user/per-thread/per-event raw rows are "
            "included. ctr_by_classification / save_rate_by_classification / "
            "visit_intent_by_classification are not computed by this command "
            "(see UNVERIFIED_SEGMENTED_QUERY_CONTRACT — unverified against "
            "real data, run separately once access exists)."
        ),
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=DEFAULT_ROLLOUT_SINCE, help="ISO8601 window start (default: PR #2384 rollout time)")
    parser.add_argument("--until", default=None, help="ISO8601 window end (default: now)")
    parser.add_argument(
        "--fixture",
        default=None,
        help="Directory of per-query fixture JSON files. No network call is made in this mode.",
    )
    args = parser.parse_args()

    until = args.until or _iso_now()

    if not args.fixture:
        key_present = bool(os.environ.get("POSTHOG_PERSONAL_API_KEY"))
        project_present = bool(os.environ.get("POSTHOG_PROJECT_ID"))
        if not key_present or not project_present:
            print("POSTHOG_READ_CREDENTIAL_REQUIRED", file=sys.stderr)
            return 1

    try:
        report = build_report(since=args.since, until=until, fixture_dir=args.fixture)
    except PostHogReadOnlyQueryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
