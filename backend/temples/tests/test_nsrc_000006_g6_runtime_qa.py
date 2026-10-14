"""nsrc-000006 赤井神社の G6 Runtime QA。

authority:
- docs/knowledge/shrine-expansion-gate-contract.md §9
- docs/knowledge/recommendation-eligibility-contract.md

target は History-only Knowledge（Deity 0 / History 3）。
current Deity は NOT_FROZEN のため、1926年史料上の祭神・合祀神を
runtime Deity / Recommendation Reasonへ昇格させない。

G6は現行 Runtime をそのまま測る。
Ranking / Reason template / Concierge / Compass / Knowledge / Positionは変更しない。
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
from temples.services.recommendation_eligibility_verifier import (
    UNRESOLVED,
    ShrineIdentity,
    verify_recommendation_eligibility,
)

pytestmark = pytest.mark.django_db

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000006_seed.json"

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
SHRINE_LAT = 38.085938
SHRINE_LNG = 138.418312

S2_URL = "https://sado-geinou.com/geinou/kamoutashiro/"
S3_URL = "https://dl.ndl.go.jp/pid/971197"

H1_TYPE = "regional_context"
H1_TITLE = "4月16日の赤井神社例祭と鬼太鼓奉納"
H1_CONTENT = "赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が神社で舞を奉納した後、各地区を門付けする。"

H2_TYPE = "tradition"
H2_TITLE = "元日午前0時の鬼太鼓奉納"
H2_CONTENT = "加茂歌代の鬼太鼓は、元日の午前0時にも赤井神社で舞を奉納する。"

H3_TYPE = "regional_context"
H3_TITLE = "加茂の五神社としての記録"
H3_CONTENT = "1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を「加茂の五神社」と記録している。"

EXPECTED_DETAIL_HISTORIES = [
    (H1_TITLE, H1_TYPE, S2_URL),
    (H2_TITLE, H2_TYPE, S2_URL),
    (H3_TITLE, H3_TYPE, S3_URL),
]

UNSUPPORTED_CURRENT_DEITY_NAMES = (
    "素盞嗚尊",
    "別雷尊",
    "倉稲魂命",
    "菅原道真公",
)

NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
)

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
def nsrc_000006_runtime_state():
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
        trace_id="nsrc-000006-g6",
    )
    matches = [
        candidate
        for candidate in candidates
        if candidate.get("name") == SHRINE_NAME and candidate.get("address") == SHRINE_ADDRESS
    ]
    assert len(matches) == 1
    return matches[0]


def test_nsrc_000006_g6_detail_runtime(nsrc_000006_runtime_state):
    shrine = nsrc_000006_runtime_state
    client = APIClient()

    response = client.get(f"/api/shrines/{shrine.pk}/")

    assert response.status_code == 200
    body = response.json()

    assert body["deities"] == []
    assert len(body["histories"]) == 3

    observed = []
    for history in body["histories"]:
        assert history["verification_status"] == "source_confirmed"
        assert len(history["sources"]) == 1
        assert history["sources"][0]["verification_status"] == "source_confirmed"
        observed.append((history["title"], history["history_type"], history["sources"][0]["url"]))
    assert observed == EXPECTED_DETAIL_HISTORIES

    target_history_ids = set(
        ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
    )
    assert {row["id"] for row in body["histories"]} == target_history_ids
    assert len(target_history_ids) == 3

    returned_text = str(body)
    for name in UNSUPPORTED_CURRENT_DEITY_NAMES:
        assert name not in returned_text


def test_nsrc_000006_g6_concierge_candidate_path(nsrc_000006_runtime_state):
    shrine = nsrc_000006_runtime_state
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
        (H3_TYPE, H3_TITLE),
    ]
    assert candidate["goriyaku_tag_ids"] == []


def test_nsrc_000006_g6_recommendation_reason_is_history_backed_and_safe(
    nsrc_000006_runtime_state,
):
    _ = nsrc_000006_runtime_state
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

    assert candidate_profile["deity"] is None
    assert candidate_profile["shrine_history"] == H1_CONTENT
    assert candidate_profile["shrine_history_type"] == H1_TYPE
    assert candidate_profile["shrine_history_confidence"] == "high"
    assert candidate_profile["shrine_history"] in (H1_CONTENT, H2_CONTENT, H3_CONTENT)

    assert preview["fact"]["deity"] is None
    assert preview["fact"]["shrine_history"] == H1_CONTENT
    assert preview["fact"]["goriyaku"] is None
    assert f"shrine_history:{H1_CONTENT}" in preview["fact"]["evidence"]

    reason_text = preview["reason_text"]
    assert reason_text
    assert f"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。" in reason_text
    assert H2_CONTENT.rstrip("。") not in reason_text
    assert H3_CONTENT.rstrip("。") not in reason_text

    for name in UNSUPPORTED_CURRENT_DEITY_NAMES:
        assert name not in reason_text
    for phrase in FORBIDDEN_GUARANTEE_PHRASES:
        assert phrase not in reason_text


def test_nsrc_000006_g6_compass_uses_adopted_coordinate_for_distance_and_direction(
    nsrc_000006_runtime_state,
):
    _ = nsrc_000006_runtime_state
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


def test_nsrc_000006_g6_noncanonical_identities_fail_closed(nsrc_000006_runtime_state):
    _ = nsrc_000006_runtime_state

    report = verify_recommendation_eligibility(
        shrine_identities=[
            ShrineIdentity(name=SHRINE_NAME, address=address)
            for address in NON_CANONICAL_ADDRESSES
        ]
    )

    assert report.summary_counts() == (0, 0, 2)
    assert [result.status for result in report.results] == [UNRESOLVED, UNRESOLVED]
    assert all(result.shrine_id is None for result in report.results)

    candidate = _target_candidate()
    assert candidate["address"] == SHRINE_ADDRESS
    assert candidate["address"] not in NON_CANONICAL_ADDRESSES
