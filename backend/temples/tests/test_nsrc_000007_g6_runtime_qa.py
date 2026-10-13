"""nsrc-000007 赤城社の G6 Runtime QA（docs/knowledge/shrine-expansion-gate-contract.md §9）。

赤城社（新潟県十日町市四日町2534番地）は History-only Knowledge（Deity 0 / History 2）。
S2 の historical 記載（土田岐入彦命）/ research lead（経津主命）は current ShrineDeity ではないため、
Deity が無いことを G6 の失敗理由にしない。
現行 Runtime をそのまま使い、Ranking / Reason template / Concierge / Compass は変更しない。
H002 には別実体の同名 `赤城社` があるため、target は常に exact (name_jp, address) で特定する。
"""

import io
import math
from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineHistory
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.concierge_chat import (
    _build_reason_v4_authority_context,
    _build_score_v3_candidate_profile,
)
from temples.services.concierge_chat_candidates import (
    _distance_m,
    build_chat_candidates,
)
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

pytestmark = pytest.mark.django_db

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000007_seed.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
SHRINE_LAT = 37.14755658
SHRINE_LNG = 138.76887612

S2_URL = "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf"
S3_URL = "https://www.tokamachi-museum.jp/archives/bunka023/"

H1_TYPE = "historical_event"
H1_TITLE = "安政7年正月の再建"
H1_CONTENT = "赤城社は安政7年正月に再建された。"
H2_TYPE = "regional_context"
H2_TITLE = "赤城社に伝わった越後縮幡"
H2_CONTENT = "越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。"
EXPECTED_DETAIL_HISTORIES = [
    (H1_TITLE, H1_TYPE, S2_URL),
    (H2_TITLE, H2_TYPE, S3_URL),
]

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


@pytest.fixture
def nsrc_000007_runtime_state():
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
        trace_id="nsrc-000007-g6",
    )
    matches = [
        candidate
        for candidate in candidates
        if candidate.get("name") == SHRINE_NAME and candidate.get("address") == SHRINE_ADDRESS
    ]
    assert len(matches) == 1
    return matches[0]


def test_nsrc_000007_g6_detail_runtime(nsrc_000007_runtime_state):
    shrine = nsrc_000007_runtime_state
    client = APIClient()

    response = client.get(f"/api/shrines/{shrine.pk}/")

    assert response.status_code == 200
    body = response.json()

    assert body["deities"] == []
    assert len(body["histories"]) == 2

    observed = []
    for history in body["histories"]:
        assert history["verification_status"] == "source_confirmed"
        assert len(history["sources"]) == 1
        assert history["sources"][0]["verification_status"] == "source_confirmed"
        observed.append((history["title"], history["history_type"], history["sources"][0]["url"]))
    assert observed == EXPECTED_DETAIL_HISTORIES

    # unrelated Knowledge Fact が混入しない: 返る History は target Shrine 自身のものだけ。
    target_history_ids = set(
        ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
    )
    assert {row["id"] for row in body["histories"]} == target_history_ids
    assert len(target_history_ids) == 2

    # historical Source evidence != current ShrineDeity
    returned_text = str(body)
    for name in UNSUPPORTED_DEITY_NAMES:
        assert name not in returned_text


def test_nsrc_000007_g6_concierge_candidate_path(nsrc_000007_runtime_state):
    shrine = nsrc_000007_runtime_state
    candidate = _target_candidate()

    assert candidate["id"] == shrine.pk
    assert candidate["shrine_id"] == shrine.pk
    assert candidate["name"] == SHRINE_NAME
    assert candidate["address"] == SHRINE_ADDRESS
    assert candidate["lat"] == pytest.approx(SHRINE_LAT)
    assert candidate["lng"] == pytest.approx(SHRINE_LNG)
    assert candidate["distance_m"] == 0

    assert candidate["knowledge_deities"] == []
    assert [(h["history_type"], h["title"]) for h in candidate["knowledge_histories"]] == [
        (H1_TYPE, H1_TITLE),
        (H2_TYPE, H2_TITLE),
    ]

    assert candidate["goriyaku_tag_ids"] == []


def test_nsrc_000007_g6_recommendation_reason_is_history_backed_and_safe(
    nsrc_000007_runtime_state,
):
    _ = nsrc_000007_runtime_state
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

    # 実測: 現行 runtime は knowledge_histories の先頭（sort_order, id 順 = H1）を選ぶ。
    assert candidate_profile["deity"] is None
    assert candidate_profile["shrine_history"] == H1_CONTENT
    assert candidate_profile["shrine_history_type"] == H1_TYPE
    assert candidate_profile["shrine_history_confidence"] == "high"
    assert candidate_profile["shrine_history"] in (H1_CONTENT, H2_CONTENT)

    assert preview["fact"]["deity"] is None
    assert preview["fact"]["shrine_history"] == H1_CONTENT
    assert preview["fact"]["goriyaku"] is None
    assert f"shrine_history:{H1_CONTENT}" in preview["fact"]["evidence"]

    reason_text = preview["reason_text"]
    assert reason_text
    # 実測の現行 Reason v4 文。target 自身の Source-backed History（H1 / S2）だけを使う。
    assert f"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。" in reason_text
    assert H2_CONTENT.rstrip("。") not in reason_text

    for name in UNSUPPORTED_DEITY_NAMES:
        assert name not in reason_text
    for phrase in FORBIDDEN_GUARANTEE_PHRASES:
        assert phrase not in reason_text


def test_nsrc_000007_g6_compass_uses_adopted_coordinate_for_distance_and_direction(
    nsrc_000007_runtime_state,
):
    _ = nsrc_000007_runtime_state
    candidate = _target_candidate()

    assert candidate["lat"] == pytest.approx(SHRINE_LAT)
    assert candidate["lng"] == pytest.approx(SHRINE_LNG)

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

    matched = filter_candidates_by_direction(
        [candidate],
        origin=QA_ORIGIN,
        reference_directions=[direction],
    )
    assert matched == [candidate]

    other_directions = [label for label in DIRECTIONS if label != direction]
    unmatched = filter_candidates_by_direction(
        [candidate],
        origin=QA_ORIGIN,
        reference_directions=other_directions,
    )
    assert unmatched == []
