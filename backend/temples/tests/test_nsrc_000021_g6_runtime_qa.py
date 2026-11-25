"""nsrc-000021 荒川神社 の G6 Runtime QA.

Deity 1 / History 1 の Knowledge を持つ nsrc-000021 が、現行 Runtime の
Detail / Concierge candidate path / Recommendation Reason / Compass で壊れず扱えるかを測定する。

Authority:
- docs/knowledge/shrine-expansion-gate-contract.md §9
- docs/audit/niigata-vpg001-nsrc-000021-g5-recommendation-eligibility.md
- docs/audit/niigata-vpg001-nsrc-000021-g6-runtime-qa.md

Top1 / ranking 位置は Acceptance Criteria にしない。
"""

import io
import math
from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineDeity, ShrineHistory
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
from temples.services.recommendation_eligibility_verifier import (
    UNRESOLVED,
    ShrineIdentity,
    verify_recommendation_eligibility,
)
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

pytestmark = pytest.mark.django_db

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_DIR = TEMPLES_DIR / "data" / "knowledge_seeds"
KNOWLEDGE_SEED_PATH = KNOWLEDGE_SEED_DIR / "nsrc_000021_seed.json"
VPG001_KNOWLEDGE_SEED_PATHS = [
    KNOWLEDGE_SEED_DIR / f"nsrc_{cid}_seed.json" for cid in ("000021", "000022", "000024", "000025")
]

SHRINE_NAME = "荒川神社"
SHRINE_ADDRESS = "新潟県胎内市桃崎浜187番地"
# frozen G2 adopted coordinate
SHRINE_LAT = 38.1409456
SHRINE_LNG = 139.4073314

SOURCE_URL = "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html"
EXPECTED_DEITIES = ["天鈿女命"]
EXPECTED_HISTORIES = [("regional_context", "船主による船絵馬の奉納")]
# G1 で記録済みの同名・別住所 identity（Base Seed には materialize されていない）。
OTHER_SAME_NAME_ADDRESSES = (
    "新潟県新発田市荒川5431番地",
    "新潟県村上市小岩内463番地",
    "新潟県村上市荒川542番地",
)
# 同一境内の別 Fact owner（Base Seed にも Knowledge Seed にも存在しない）。
FOREIGN_SAME_ADDRESS_NAMES = ()
FORBIDDEN_TEXT = ("1814", "1841", "天保12")
FORBIDDEN_GUARANTEE_PHRASES = (
    "必ず",
    "確実",
    "保証",
    "絶対",
    "叶う",
    "成就します",
    "治ります",
    "合格します",
    "効果があります",
    "ご利益があります",
)
DIRECTIONS = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")
QA_ORIGIN = {"lat": 35.681236, "lng": 139.767125}


def _import(*knowledge_seed_paths: Path) -> Shrine:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    for path in knowledge_seed_paths:
        call_command(
            "import_shrine_knowledge",
            str(path),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


@pytest.fixture
def target_runtime_state():
    return _import(KNOWLEDGE_SEED_PATH)


@pytest.fixture
def vpg001_runtime_state():
    return _import(*VPG001_KNOWLEDGE_SEED_PATHS)


def _candidates() -> list[dict]:
    return build_chat_candidates(
        lat=SHRINE_LAT,
        lng=SHRINE_LNG,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="nsrc-000021-g6",
    )


def _target_candidate() -> dict:
    matches = [
        candidate
        for candidate in _candidates()
        if candidate.get("name") == SHRINE_NAME and candidate.get("address") == SHRINE_ADDRESS
    ]
    assert len(matches) == 1
    return matches[0]


def _detail(shrine: Shrine) -> dict:
    response = APIClient().get(f"/api/shrines/{shrine.pk}/")
    assert response.status_code == 200
    return response.json()


def _detail_shape(body: dict) -> tuple[list, list]:
    deities = [
        (d["display_name"], d["verification_status"], [s["url"] for s in d["sources"]])
        for d in body["deities"]
    ]
    histories = [
        (h["title"], h["history_type"], h["verification_status"], [s["url"] for s in h["sources"]])
        for h in body["histories"]
    ]
    return deities, histories


def _expected_detail_shape() -> tuple[list, list]:
    return (
        [(name, "source_confirmed", [SOURCE_URL]) for name in EXPECTED_DEITIES],
        [(title, kind, "source_confirmed", [SOURCE_URL]) for kind, title in EXPECTED_HISTORIES],
    )


def _reason(candidate: dict) -> tuple[dict, dict]:
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
    return candidate_profile, preview


# ---------- Surface 1: Shrine Detail -------------------------------------------------------------


def test_g6_detail_runtime(target_runtime_state):
    shrine = target_runtime_state
    body = _detail(shrine)

    assert body["id"] == shrine.pk
    assert body["name_jp"] == SHRINE_NAME
    assert body["address"] == SHRINE_ADDRESS
    assert _detail_shape(body) == _expected_detail_shape()
    for row in [*body["deities"], *body["histories"]]:
        for source in row["sources"]:
            assert source["verification_status"] == "source_confirmed"

    assert {row["id"] for row in body["deities"]} == set(
        ShrineDeity.objects.filter(shrine=shrine).values_list("id", flat=True)
    )
    assert {row["id"] for row in body["histories"]} == set(
        ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
    )
    returned_text = str(body)
    for needle in FORBIDDEN_TEXT:
        assert needle not in returned_text


# ---------- Surface 2: Concierge candidate path ---------------------------------------------------


def test_g6_concierge_candidate_path(target_runtime_state):
    shrine = target_runtime_state
    candidate = _target_candidate()

    assert candidate["id"] == shrine.pk
    assert candidate["shrine_id"] == shrine.pk
    assert candidate["name"] == SHRINE_NAME
    assert candidate["address"] == SHRINE_ADDRESS
    assert candidate["lat"] == pytest.approx(SHRINE_LAT)
    assert candidate["lng"] == pytest.approx(SHRINE_LNG)
    assert candidate["distance_m"] == 0

    assert [d["display_name"] for d in candidate["knowledge_deities"]] == EXPECTED_DEITIES
    assert [
        (h["history_type"], h["title"]) for h in candidate["knowledge_histories"]
    ] == EXPECTED_HISTORIES
    assert candidate["goriyaku_tag_ids"] == []
    candidate_text = str(candidate["knowledge_deities"]) + str(candidate["knowledge_histories"])
    for needle in FORBIDDEN_TEXT:
        assert needle not in candidate_text


# ---------- Surface 3: Recommendation Reason / Copy -----------------------------------------------


def test_g6_recommendation_reason_is_source_backed_and_safe(target_runtime_state):
    _ = target_runtime_state
    candidate = _target_candidate()
    candidate_profile, preview = _reason(candidate)

    assert candidate_profile["deity"] == "天鈿女命"
    assert (
        candidate_profile["shrine_history"]
        == "荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。"
    )
    assert preview["fact"]["deity"] == "天鈿女命"
    assert (
        preview["fact"]["shrine_history"]
        == "荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。"
    )
    assert preview["fact"]["goriyaku"] is None
    assert preview["fact"]["history_theme"] is None
    assert preview["fact"]["name"] == SHRINE_NAME
    assert "deity:天鈿女命" in preview["fact"]["evidence"]

    reason_text = preview["reason_text"]
    assert reason_text
    assert reason_text.startswith("荒川神社では、天鈿女命が祀られています。")
    for needle in FORBIDDEN_TEXT:
        assert needle not in reason_text
    for phrase in FORBIDDEN_GUARANTEE_PHRASES:
        assert phrase not in reason_text
    # 歴史的記述（船絵馬の奉納）を効能へ転化しない。
    for phrase in ("航海安全の効果", "航海安全が叶"):
        assert phrase not in reason_text


# ---------- Surfaces 4 / 5: Compass distance and direction ----------------------------------------


def test_g6_compass_distance_uses_adopted_coordinate(target_runtime_state):
    _ = target_runtime_state
    candidate = _target_candidate()

    assert (candidate["lat"], candidate["lng"]) == (SHRINE_LAT, SHRINE_LNG)
    distance_m = _distance_m(QA_ORIGIN["lat"], QA_ORIGIN["lng"], candidate["lat"], candidate["lng"])

    assert isinstance(distance_m, int)
    assert math.isfinite(distance_m)
    assert distance_m == 275370


def test_g6_compass_direction_uses_adopted_coordinate(target_runtime_state):
    _ = target_runtime_state
    candidate = _target_candidate()

    bearing = _bearing(
        from_lat=QA_ORIGIN["lat"],
        from_lng=QA_ORIGIN["lng"],
        to_lat=candidate["lat"],
        to_lng=candidate["lng"],
    )
    direction = _direction_label(bearing)

    assert 0.0 <= bearing < 360.0
    assert bearing == pytest.approx(353.43671632022944)
    assert direction == "北"

    matched = filter_candidates_by_direction(
        [candidate], origin=QA_ORIGIN, reference_directions=[direction]
    )
    assert matched == [candidate]
    for other in DIRECTIONS:
        if other == direction:
            continue
        assert (
            filter_candidates_by_direction(
                [candidate], origin=QA_ORIGIN, reference_directions=[other]
            )
            == []
        ), other


# ---------- Identity fail-closed ------------------------------------------------------------------


def test_g6_identity_fail_closed(target_runtime_state):
    shrine = target_runtime_state
    candidates = _candidates()

    same_name = [c for c in candidates if c.get("name") == SHRINE_NAME]
    assert [c["shrine_id"] for c in same_name] == [shrine.pk]

    identities = [ShrineIdentity(name=SHRINE_NAME, address=a) for a in OTHER_SAME_NAME_ADDRESSES]
    identities += [
        ShrineIdentity(name=n, address=SHRINE_ADDRESS) for n in FOREIGN_SAME_ADDRESS_NAMES
    ]
    if identities:
        report = verify_recommendation_eligibility(shrine_identities=identities)
        assert [r.status for r in report.results] == [UNRESOLVED] * len(identities)
        assert all(r.shrine_id is None for r in report.results)
    for address in OTHER_SAME_NAME_ADDRESSES:
        assert not Shrine.objects.filter(name_jp=SHRINE_NAME, address=address).exists()
        assert not [c for c in candidates if c.get("address") == address]
    for name in FOREIGN_SAME_ADDRESS_NAMES:
        assert not Shrine.objects.filter(name_jp=name).exists()
        assert not [c for c in candidates if c.get("name") == name]

    assert ShrineDeity.objects.exclude(shrine=shrine).count() == 0
    assert ShrineHistory.objects.exclude(shrine=shrine).count() == 0


# ---------- Cross-candidate isolation -------------------------------------------------------------


def test_g6_cross_candidate_isolation(vpg001_runtime_state):
    shrine = vpg001_runtime_state

    assert _detail_shape(_detail(shrine)) == _expected_detail_shape()

    candidate = _target_candidate()
    assert candidate["shrine_id"] == shrine.pk
    assert [d["display_name"] for d in candidate["knowledge_deities"]] == EXPECTED_DEITIES
    assert [
        (h["history_type"], h["title"]) for h in candidate["knowledge_histories"]
    ] == EXPECTED_HISTORIES

    for fact in [
        *ShrineDeity.objects.filter(shrine=shrine),
        *ShrineHistory.objects.filter(shrine=shrine),
    ]:
        assert [s.url for s in fact.sources.all()] == [SOURCE_URL]
    other_facts = [
        *ShrineDeity.objects.exclude(shrine=shrine),
        *ShrineHistory.objects.exclude(shrine=shrine),
    ]
    assert other_facts
    for fact in other_facts:
        assert SOURCE_URL not in [s.url for s in fact.sources.all()]

    candidate_text = str(candidate["knowledge_deities"]) + str(candidate["knowledge_histories"])
    for needle in FORBIDDEN_TEXT:
        assert needle not in candidate_text
