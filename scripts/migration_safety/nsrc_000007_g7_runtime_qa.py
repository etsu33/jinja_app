#!/usr/bin/env python3
"""nsrc-000007 赤城社 G7 Production Runtime QA.

Read-only verification of the G6 runtime surfaces against the configured
database (History-only Knowledge: Deity 0 / History 2). The entire verification
runs inside a PostgreSQL READ ONLY transaction, so any accidental write attempt
fails closed.

The target is always the exact (name_jp, address) identity. H002 has other
distinct shrines named 赤城社; they are never used as the target. Recommendation
Top1 / Compass Top1 is not required.
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

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
SHRINE_LAT = 37.14755658
SHRINE_LNG = 138.76887612

S2_TYPE = "government"
S2_URL = "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf"
S3_TYPE = "museum_or_archive"
S3_URL = "https://www.tokamachi-museum.jp/archives/bunka023/"

H1_TYPE = "historical_event"
H1_TITLE = "安政7年正月の再建"
H1_CONTENT = "赤城社は安政7年正月に再建された。"
H2_TYPE = "regional_context"
H2_TITLE = "赤城社に伝わった越後縮幡"
H2_CONTENT = "越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。"
# title -> (history_type, the only related Source type, the only related Source URL)
EXPECTED_HISTORIES = {
    H1_TITLE: (H1_TYPE, S2_TYPE, S2_URL),
    H2_TITLE: (H2_TYPE, S3_TYPE, S3_URL),
}
UNSUPPORTED_DEITY_NAMES = ("土田岐入彦命", "経津主命")
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
        assert len(body["histories"]) == 2
        assert [row["title"] for row in body["histories"]] == [H1_TITLE, H2_TITLE]
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
        for name in UNSUPPORTED_DEITY_NAMES:
            assert name not in returned_text
        print("DETAIL_RUNTIME=PASS")

        candidates = build_chat_candidates(
            lat=SHRINE_LAT,
            lng=SHRINE_LNG,
            area=None,
            goriyaku_tag_ids=None,
            trace_id="nsrc-000007-g7-production-runtime",
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
        ]
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
        # G6 measured selection: the first knowledge_histories item (sort_order, id) = H1.
        assert candidate_profile["deity"] is None
        assert candidate_profile["shrine_history"] == H1_CONTENT
        assert candidate_profile["shrine_history_type"] == H1_TYPE
        assert candidate_profile["shrine_history_confidence"] == "high"
        assert preview["fact"]["deity"] is None
        assert preview["fact"]["shrine_history"] == H1_CONTENT
        assert preview["fact"]["goriyaku"] is None
        reason_text = preview["reason_text"]
        assert reason_text
        assert f"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。" in reason_text
        assert H2_CONTENT.rstrip("。") not in reason_text
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
