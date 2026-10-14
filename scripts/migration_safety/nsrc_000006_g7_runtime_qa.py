#!/usr/bin/env python3
"""nsrc-000006 赤井神社 G7 Production Runtime QA.

Read-only verification of the G5 / G6 runtime surfaces against the configured
database (History-only Knowledge: Deity 0 / History 3). The entire verification
runs inside a PostgreSQL READ ONLY transaction, so any accidental write attempt
fails closed. Aggregate counts are measured before and after the QA and must be
unchanged.

The target is always the exact (name_jp, address) identity; the noncanonical
address forms never resolve as the target. Recommendation Top1 / Compass Top1
is not required.
"""

# Django must be configured before the temples imports below.
# ruff: noqa: E402

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")

import django

django.setup()

from django.db import connection, transaction
from temples.api.serializers.shrine import ShrineDetailSerializer
from temples.models import Shrine, ShrineHistory
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.concierge_chat import (
    _build_reason_v4_authority_context,
    _build_score_v3_candidate_profile,
)
from temples.services.concierge_chat_candidates import (
    _distance_m,
    build_chat_candidates,
    filter_recommendation_eligible_candidates,
    partition_recommendation_eligible_shrines,
)
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.knowledge_seed import normalize_source_url, resolve_shrine
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    ShrineIdentity,
    verify_recommendation_eligibility,
)
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
SHRINE_LAT = 38.085938
SHRINE_LNG = 138.418312
NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
)

S2_TYPE = "tourism_official"
S2_URL = "https://sado-geinou.com/geinou/kamoutashiro/"
S3_TYPE = "local_history"
S3_URL = "https://dl.ndl.go.jp/pid/971197"

H1_TYPE = "regional_context"
H1_TITLE = "4月16日の赤井神社例祭と鬼太鼓奉納"
H1_CONTENT = (
    "赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が神社で舞を奉納した後、"
    "各地区を門付けする。"
)
H2_TYPE = "tradition"
H2_TITLE = "元日午前0時の鬼太鼓奉納"
H2_CONTENT = "加茂歌代の鬼太鼓は、元日の午前0時にも赤井神社で舞を奉納する。"
H3_TYPE = "regional_context"
H3_TITLE = "加茂の五神社としての記録"
H3_CONTENT = (
    "1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を「加茂の五神社」と記録している。"
)
# title -> (history_type, the only related Source type, the only related Source URL)
EXPECTED_HISTORIES = {
    H1_TITLE: (H1_TYPE, S2_TYPE, S2_URL),
    H2_TITLE: (H2_TYPE, S2_TYPE, S2_URL),
    H3_TITLE: (H3_TYPE, S3_TYPE, S3_URL),
}
UNSUPPORTED_CURRENT_DEITY_NAMES = ("素盞嗚尊", "別雷尊", "倉稲魂命", "菅原道真公")
FORBIDDEN_GUARANTEE_PHRASES = (
    "必ず",
    "確実",
    "保証",
    "叶う",
    "効果があります",
    "ご利益があります",
    "絶対",
    "成就します",
    "治ります",
    "合格します",
)
DIRECTIONS = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")
QA_ORIGIN = {"lat": 35.681236, "lng": 139.767125}
AGGREGATE_TABLES = (
    "temples_shrine",
    "temples_shrineknowledgesource",
    "temples_shrinedeity",
    "temples_shrinehistory",
    "temples_shrinesourcefact",
    "temples_shrinedeitycollective",
)


def _aggregates() -> tuple[int, ...]:
    counts = []
    with connection.cursor() as cursor:
        for table in AGGREGATE_TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts.append(cursor.fetchone()[0])
    return tuple(counts)


def main() -> None:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
        before = _aggregates()

        shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
        resolved = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
        assert resolved.status == "OK" and resolved.shrine.pk == shrine.pk
        for address in NON_CANONICAL_ADDRESSES:
            other = resolve_shrine(SHRINE_NAME, address)
            assert other.shrine is None or other.shrine.pk != shrine.pk
        assert shrine.latitude == SHRINE_LAT
        assert shrine.longitude == SHRINE_LNG
        print("EXACT_TARGET=PASS")

        body = ShrineDetailSerializer(shrine).data
        assert list(body["deities"]) == []
        assert len(body["histories"]) == 3
        assert [row["title"] for row in body["histories"]] == [H1_TITLE, H2_TITLE, H3_TITLE]
        for history in body["histories"]:
            history_type, source_type, source_url = EXPECTED_HISTORIES[history["title"]]
            assert history["history_type"] == history_type
            assert history["verification_status"] == "source_confirmed"
            assert len(history["sources"]) == 1
            # A reused pre-existing Source may differ only in URL syntax; compare importer identity.
            assert history["sources"][0]["source_type"] == source_type
            assert normalize_source_url(history["sources"][0]["url"]) == normalize_source_url(
                source_url
            )
            assert history["sources"][0]["verification_status"] == "source_confirmed"
        assert {row["id"] for row in body["histories"]} == set(
            ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
        )
        returned_text = str(body)
        for name in UNSUPPORTED_CURRENT_DEITY_NAMES:
            assert name not in returned_text
        print("DETAIL_RUNTIME=PASS")

        report = verify_recommendation_eligibility(
            shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
        )
        assert report.summary_counts() == (1, 0, 0)
        result = report.results[0]
        assert result.status == ELIGIBLE
        assert result.shrine_id == shrine.pk
        assert (result.usable_deity_fact_count, result.usable_history_fact_count) == (0, 3)
        partition = partition_recommendation_eligible_shrines([shrine])
        assert (partition.source_count, partition.eligible_count) == (1, 1)
        print("SHARED_RECOMMENDATION_ELIGIBILITY=PASS")

        candidates = build_chat_candidates(
            lat=SHRINE_LAT,
            lng=SHRINE_LNG,
            area=None,
            goriyaku_tag_ids=None,
            trace_id="nsrc-000006-g7-production-runtime",
        )
        matches = [
            candidate
            for candidate in candidates
            if candidate.get("name") == SHRINE_NAME and candidate.get("address") == SHRINE_ADDRESS
        ]
        assert len(matches) == 1
        candidate = matches[0]
        assert candidate["id"] == shrine.pk
        assert candidate["shrine_id"] == shrine.pk
        assert candidate["lat"] == SHRINE_LAT
        assert candidate["lng"] == SHRINE_LNG
        assert candidate["distance_m"] == 0
        assert candidate["knowledge_deities"] == []
        assert [(h["history_type"], h["title"]) for h in candidate["knowledge_histories"]] == [
            (H1_TYPE, H1_TITLE),
            (H2_TYPE, H2_TITLE),
            (H3_TYPE, H3_TITLE),
        ]
        assert candidate["goriyaku_tag_ids"] == []
        assert filter_recommendation_eligible_candidates([candidate]) == [candidate]
        print("CONCIERGE_CANDIDATE_PATH=PASS")

        candidate_profile = _build_score_v3_candidate_profile(candidate)
        recommendation_input = build_recommendation_input_profile(
            interpretation_profile={},
            translation_result={},
            candidate_profile=candidate_profile,
            score_v2_fields={},
        )
        preview = build_recommendation_reason_v4(
            recommendation_input_profile=recommendation_input,
            authority_context=_build_reason_v4_authority_context(candidate),
        )
        # G6 measured selection: the first knowledge_histories item (sort_order, id) = H1.
        assert candidate_profile["deity"] is None
        assert candidate_profile["shrine_history"] == H1_CONTENT
        assert candidate_profile["shrine_history_type"] == H1_TYPE
        assert preview["fact"]["deity"] is None
        assert preview["fact"]["shrine_history"] == H1_CONTENT
        assert preview["fact"]["goriyaku"] is None
        reason_text = preview["reason_text"]
        assert reason_text
        assert f"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。" in reason_text
        for other_content in (H2_CONTENT, H3_CONTENT):
            assert other_content.rstrip("。") not in reason_text
        for name in UNSUPPORTED_CURRENT_DEITY_NAMES:
            assert name not in reason_text
        for phrase in FORBIDDEN_GUARANTEE_PHRASES:
            assert phrase not in reason_text
        print("RECOMMENDATION_REASON=PASS")

        distance_m = _distance_m(
            QA_ORIGIN["lat"],
            QA_ORIGIN["lng"],
            candidate["lat"],
            candidate["lng"],
        )
        assert distance_m is not None
        assert isinstance(distance_m, int)
        assert distance_m > 0
        assert math.isfinite(distance_m)

        bearing = _bearing(
            from_lat=QA_ORIGIN["lat"],
            from_lng=QA_ORIGIN["lng"],
            to_lat=candidate["lat"],
            to_lng=candidate["lng"],
        )
        direction = _direction_label(bearing)
        assert 0.0 <= bearing < 360.0
        assert direction in DIRECTIONS
        assert filter_candidates_by_direction(
            [candidate],
            origin=QA_ORIGIN,
            reference_directions=[direction],
        ) == [candidate]
        assert (
            filter_candidates_by_direction(
                [candidate],
                origin=QA_ORIGIN,
                reference_directions=[label for label in DIRECTIONS if label != direction],
            )
            == []
        )
        print("COMPASS_DISTANCE=PASS")
        print("COMPASS_DIRECTION=PASS")

        assert _aggregates() == before
        print("AGGREGATES_UNCHANGED=PASS")

    print("G7_PRODUCTION_RUNTIME_QA=PASS")
    print("TRANSACTION_MODE=READ_ONLY")


if __name__ == "__main__":
    main()
