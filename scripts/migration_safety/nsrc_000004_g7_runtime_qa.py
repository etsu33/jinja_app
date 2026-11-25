#!/usr/bin/env python3
"""nsrc-000004 G7 Production Runtime QA.

Read-only verification of the four G6 runtime surfaces against the configured
database. The entire verification runs inside a PostgreSQL READ ONLY
transaction, so any accidental write attempt fails closed.
"""

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
from temples.models import Shrine
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.concierge_chat import (
    _build_reason_v4_authority_context,
    _build_score_v3_candidate_profile,
)
from temples.services.concierge_chat_candidates import _distance_m, build_chat_candidates
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

SHRINE_NAME = "青海神社"
SHRINE_ADDRESS = "新潟県加茂市大字加茂字宮山229番地"
SHRINE_LAT = 37.65657387
SHRINE_LNG = 139.0536436

EXPECTED_DEITIES = {"椎根津彦命", "大国魂命"}
EXPECTED_HISTORY_TITLES = {"神亀3年の創建", "明治5年の三社本殿合殿"}
H1_CONTENT = "神亀3年（726）、青海首一族が加茂山山麓に青海神社を創建した。"
EXCLUDED_DEITIES = {"賀茂別雷命", "多多須玉依媛命", "賀茂建角身命"}
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


def main() -> None:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")

        shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

        body = ShrineDetailSerializer(shrine).data
        assert {row["display_name"] for row in body["deities"]} == EXPECTED_DEITIES
        assert {row["title"] for row in body["histories"]} == EXPECTED_HISTORY_TITLES
        assert len(body["deities"]) == 2
        assert len(body["histories"]) == 2
        for row in [*body["deities"], *body["histories"]]:
            assert row["verification_status"] == "source_confirmed"
            assert len(row["sources"]) == 1
            assert row["sources"][0]["verification_status"] == "source_confirmed"
        returned_text = str(body)
        for excluded in EXCLUDED_DEITIES:
            assert excluded not in returned_text
        print("DETAIL_RUNTIME=PASS")

        candidates = build_chat_candidates(
            lat=SHRINE_LAT,
            lng=SHRINE_LNG,
            area=None,
            goriyaku_tag_ids=None,
            trace_id="nsrc-000004-g7-production-runtime",
        )
        matches = [
            candidate
            for candidate in candidates
            if candidate.get("name") == SHRINE_NAME
            and candidate.get("address") == SHRINE_ADDRESS
        ]
        assert len(matches) == 1
        candidate = matches[0]
        assert candidate["id"] == shrine.pk
        assert candidate["shrine_id"] == shrine.pk
        assert candidate["lat"] == SHRINE_LAT
        assert candidate["lng"] == SHRINE_LNG
        assert candidate["distance_m"] == 0
        assert {row["display_name"] for row in candidate["knowledge_deities"]} == EXPECTED_DEITIES
        assert {row["title"] for row in candidate["knowledge_histories"]} == EXPECTED_HISTORY_TITLES
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
        deity_text = candidate_profile["deity"]
        assert deity_text
        for deity in EXPECTED_DEITIES:
            assert deity in deity_text
        for excluded in EXCLUDED_DEITIES:
            assert excluded not in deity_text
        assert candidate_profile["shrine_history"] == H1_CONTENT
        assert preview["fact"]["deity"] == deity_text
        assert preview["fact"]["shrine_history"] == H1_CONTENT
        assert preview["fact"]["goriyaku"] is None
        reason_text = preview["reason_text"]
        assert reason_text
        for deity in EXPECTED_DEITIES:
            assert deity in reason_text
        for excluded in EXCLUDED_DEITIES:
            assert excluded not in reason_text
        for phrase in FORBIDDEN_GUARANTEE_PHRASES:
            assert phrase not in reason_text
        print("RECOMMENDATION_REASON=PASS")

        origin = {"lat": 35.681236, "lng": 139.767125}
        distance_m = _distance_m(
            origin["lat"],
            origin["lng"],
            candidate["lat"],
            candidate["lng"],
        )
        assert distance_m is not None
        assert isinstance(distance_m, int)
        assert distance_m > 0
        assert math.isfinite(distance_m)

        bearing = _bearing(
            from_lat=origin["lat"],
            from_lng=origin["lng"],
            to_lat=candidate["lat"],
            to_lng=candidate["lng"],
        )
        direction = _direction_label(bearing)
        directions = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")
        assert 0.0 <= bearing < 360.0
        assert direction in directions
        assert filter_candidates_by_direction(
            [candidate],
            origin=origin,
            reference_directions=[direction],
        ) == [candidate]
        assert filter_candidates_by_direction(
            [candidate],
            origin=origin,
            reference_directions=[label for label in directions if label != direction],
        ) == []
        print("COMPASS_DISTANCE=PASS")
        print("COMPASS_DIRECTION=PASS")

    print("G7_PRODUCTION_RUNTIME_QA=PASS")
    print("TRANSACTION_MODE=READ_ONLY")


if __name__ == "__main__":
    main()
