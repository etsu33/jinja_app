#!/usr/bin/env python3
"""nsrc-000002 青澤神社 G7 Production Runtime QA.

Read-only verification of the G6 runtime surfaces against the configured
database (History-only Knowledge: Deity 0 / History 1). The entire verification
runs inside a PostgreSQL READ ONLY transaction, so any accidental write attempt
fails closed.
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
from temples.services.concierge_chat_candidates import _distance_m, build_chat_candidates
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.knowledge_seed import normalize_source_url
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

SHRINE_NAME = "青澤神社"
SHRINE_ADDRESS = "新潟県糸魚川市大字青海2696番地"
SHRINE_LAT = 37.00763484
SHRINE_LNG = 137.79024297

HISTORY_TYPE = "regional_context"
HISTORY_TITLE = "青沢神社の春季祭礼"
H1_CONTENT = (
    "青沢神社では毎年4月第3日曜日に春季祭礼が行われ、前日の宵宮には神楽が奉納される。"
    "祭礼当日は神輿・子供みこしの地区巡回、神楽奉納、手踊りが行われる。"
)
SOURCE_TYPE = "government"
SOURCE_URL = "https://matsuri.geo-itoigawa.com/calendar/m04/"
UNSUPPORTED_DEITY_NAMES = ("沼河比賣命", "沼河比売命")
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


def main() -> None:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")

        shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

        body = ShrineDetailSerializer(shrine).data
        assert list(body["deities"]) == []
        assert len(body["histories"]) == 1
        history = body["histories"][0]
        assert history["title"] == HISTORY_TITLE
        assert history["history_type"] == HISTORY_TYPE
        assert history["verification_status"] == "source_confirmed"
        assert len(history["sources"]) == 1
        # A reused pre-existing Source may differ only in URL syntax; compare importer identity.
        assert history["sources"][0]["source_type"] == SOURCE_TYPE
        assert normalize_source_url(history["sources"][0]["url"]) == normalize_source_url(
            SOURCE_URL
        )
        assert history["sources"][0]["verification_status"] == "source_confirmed"
        assert {row["id"] for row in body["histories"]} == set(
            ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
        )
        returned_text = str(body)
        for name in UNSUPPORTED_DEITY_NAMES:
            assert name not in returned_text
        print("DETAIL_RUNTIME=PASS")

        candidates = build_chat_candidates(
            lat=SHRINE_LAT,
            lng=SHRINE_LNG,
            area=None,
            goriyaku_tag_ids=None,
            trace_id="nsrc-000002-g7-production-runtime",
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
        assert len(candidate["knowledge_histories"]) == 1
        assert candidate["knowledge_histories"][0]["history_type"] == HISTORY_TYPE
        assert candidate["knowledge_histories"][0]["title"] == HISTORY_TITLE
        assert candidate["goriyaku_tag_ids"] == []
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
        assert candidate_profile["deity"] is None
        assert candidate_profile["shrine_history"] == H1_CONTENT
        assert candidate_profile["shrine_history_type"] == HISTORY_TYPE
        assert candidate_profile["shrine_history_confidence"] == "high"
        assert preview["fact"]["deity"] is None
        assert preview["fact"]["shrine_history"] == H1_CONTENT
        assert preview["fact"]["goriyaku"] is None
        reason_text = preview["reason_text"]
        assert reason_text
        assert f"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。" in reason_text
        for name in UNSUPPORTED_DEITY_NAMES:
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

    print("G7_PRODUCTION_RUNTIME_QA=PASS")
    print("TRANSACTION_MODE=READ_ONLY")


if __name__ == "__main__":
    main()
