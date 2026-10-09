import io
import math
from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from temples.models import Shrine
from temples.services.concierge_chat import (
    _build_reason_v4_authority_context,
    _build_score_v3_candidate_profile,
)
from temples.services.concierge_chat_candidates import (
    _distance_m,
    build_chat_candidates,
)
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

pytestmark = pytest.mark.django_db

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000004_seed.json"

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


@pytest.fixture
def nsrc_000004_runtime_state():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(KNOWLEDGE_SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


def _target_candidate() -> dict:
    candidates = build_chat_candidates(
        lat=SHRINE_LAT,
        lng=SHRINE_LNG,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="nsrc-000004-g6",
    )
    matches = [
        candidate
        for candidate in candidates
        if candidate.get("name") == SHRINE_NAME
        and candidate.get("address") == SHRINE_ADDRESS
    ]
    assert len(matches) == 1
    return matches[0]


def test_nsrc_000004_g6_detail_runtime(nsrc_000004_runtime_state):
    shrine = nsrc_000004_runtime_state
    client = APIClient()

    response = client.get(f"/api/shrines/{shrine.pk}/")

    assert response.status_code == 200
    body = response.json()

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


def test_nsrc_000004_g6_concierge_candidate_path(nsrc_000004_runtime_state):
    shrine = nsrc_000004_runtime_state
    candidate = _target_candidate()

    assert candidate["id"] == shrine.pk
    assert candidate["shrine_id"] == shrine.pk
    assert candidate["name"] == SHRINE_NAME
    assert candidate["address"] == SHRINE_ADDRESS
    assert candidate["lat"] == pytest.approx(SHRINE_LAT)
    assert candidate["lng"] == pytest.approx(SHRINE_LNG)
    assert candidate["distance_m"] == 0

    assert {row["display_name"] for row in candidate["knowledge_deities"]} == EXPECTED_DEITIES
    assert {row["title"] for row in candidate["knowledge_histories"]} == EXPECTED_HISTORY_TITLES
    assert candidate["goriyaku_tag_ids"] == []


def test_nsrc_000004_g6_recommendation_reason_is_source_backed_and_safe(
    nsrc_000004_runtime_state,
):
    _ = nsrc_000004_runtime_state
    candidate = _target_candidate()

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


def test_nsrc_000004_g6_compass_uses_adopted_coordinate_for_distance_and_direction(
    nsrc_000004_runtime_state,
):
    _ = nsrc_000004_runtime_state
    candidate = _target_candidate()

    assert candidate["lat"] == pytest.approx(SHRINE_LAT)
    assert candidate["lng"] == pytest.approx(SHRINE_LNG)

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

    assert 0.0 <= bearing < 360.0
    assert direction in {"北", "北東", "東", "南東", "南", "南西", "西", "北西"}

    matched = filter_candidates_by_direction(
        [candidate],
        origin=origin,
        reference_directions=[direction],
    )
    assert matched == [candidate]

    other_directions = [
        label
        for label in ("北", "北東", "東", "南東", "南", "南西", "西", "北西")
        if label != direction
    ]
    unmatched = filter_candidates_by_direction(
        [candidate],
        origin=origin,
        reference_directions=other_directions,
    )
    assert unmatched == []
