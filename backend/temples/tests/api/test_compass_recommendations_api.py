from __future__ import annotations

import copy
import json
from unittest.mock import patch

import pytest

from temples.models import Shrine
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact

URL = "/api/compass/recommendations/"
ORIGIN = {"lat": 35.0, "lng": 135.0}
BIRTHDATE = "1984-05-15"
TARGET_DATE = "2026-09-15"

# Shrine fixture coordinates below are chosen to stay within the Compass
# Geographic Distance Boundary's 60km outer stage while preserving the same
# direction label as before this feature existed -- verified against the
# real _bearing()/_direction_label() functions. See
# test_compass_recommendation_orchestrator.py for the boundary behavior
# itself (this file only checks the metadata round-trips through the API).


@pytest.fixture
def shrine_factory(db):
    def _factory(
        *,
        name: str,
        latitude: float,
        longitude: float,
        goriyaku: str = "",
        usable_knowledge: bool = True,
    ) -> Shrine:
        shrine = Shrine(
            name_jp=name,
            address="東京都千代田区",
            latitude=latitude,
            longitude=longitude,
            goriyaku=goriyaku,
        )
        Shrine.objects.bulk_create([shrine])
        created = Shrine.objects.get(pk=shrine.pk)
        if usable_knowledge:
            attach_usable_deity_fact(created, display_name=f"{name}の祭神")
        return created

    return _factory


@pytest.mark.django_db
def test_valid_request_returns_recommendation_success(client, shrine_factory):
    # 2026-09-15 + 1984-05-15 birthdate resolves to 北西 (see test_kyusei_direction.py)
    shrine_factory(name="北西の神社", latitude=35.25, longitude=134.75, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_success"
    assert body["purpose"] == "career"
    assert body["direction_context"]["referenceDirections"] == ["北西"]
    names = [rec["name"] for rec in body["recommendations"]]
    assert "北西の神社" in names
    assert len(body["recommendation_instance_id"]) == 8
    assert all(
        rec["recommendation_instance_id"] == body["recommendation_instance_id"]
        for rec in body["recommendations"]
    )


@pytest.mark.django_db
def test_separate_compass_results_get_separate_recommendation_instances(client, shrine_factory):
    shrine_factory(name="北西の神社", latitude=35.25, longitude=134.75, goriyaku="仕事運")
    payload = json.dumps(
        {
            "purpose": "career",
            "origin": ORIGIN,
            "birthdate": BIRTHDATE,
            "target_date": TARGET_DATE,
        }
    )

    first = client.post(URL, data=payload, content_type="application/json").json()
    second = client.post(URL, data=payload, content_type="application/json").json()

    assert first["recommendation_instance_id"] != second["recommendation_instance_id"]


@pytest.mark.django_db
def test_invalid_purpose_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "not_a_real_tag",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 400
    assert r.json()["state"] == "invalid_purpose"


@pytest.mark.django_db
def test_missing_birthdate_returns_direction_filter_unavailable(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "direction_filter_unavailable"
    assert body["direction_context"] is None
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_no_common_direction_returns_dedicated_state_not_unavailable(client):
    # Synthetic birthdate (not a real user's). For target_date 2026-11-15
    # this honmei star's annual/monthly lucky directions share nothing
    # (empty intersection) AND monthly-only guidance is also empty -- the
    # narrowed no_common_direction residual case under Monthly Fallback
    # (Product Contract Section 2.2-4, #2508 Option C), distinct from
    # test_monthly_fallback_returns_recommendation_flow_state below where
    # the intersection is empty but monthly-only guidance is not.
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": "1976-06-15",
                "target_date": "2026-11-15",
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "no_common_direction"
    assert body["state"] != "direction_filter_unavailable"
    assert body["direction_context"] is None
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_monthly_fallback_returns_recommendation_flow_state(client, shrine_factory):
    """Product Contract Section 2.2 / Runtime Contract Section 5-1 (#2508
    Option C): synthetic birthdate (not a real user's) where, for
    target_date 2026-08-20, the annual/monthly intersection is empty but
    monthly-only guidance (["南東"]) is available. This must reach the
    normal recommendation flow -- not no_common_direction, not
    direction_filter_unavailable -- with calculationMethod="monthly_kyusei_v1"
    (never "annual_monthly_kyusei_v1", which would misrepresent this as
    annual/monthly agreement)."""
    shrine_factory(name="南東の神社", latitude=34.825, longitude=135.35, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": "1975-06-15",
                "target_date": "2026-08-20",
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_success"
    assert body["state"] != "no_common_direction"
    assert body["direction_context"]["referenceDirections"] == ["南東"]
    assert body["direction_context"]["calculationMethod"] == "monthly_kyusei_v1"
    names = [rec["name"] for rec in body["recommendations"]]
    assert "南東の神社" in names


@pytest.mark.django_db
def test_missing_origin_returns_direction_filter_unavailable(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    assert r.json()["state"] == "direction_filter_unavailable"


@pytest.mark.django_db
def test_no_shrines_in_sector_returns_direction_zero_candidates(client, shrine_factory):
    # South of origin -- outside the 北西 (northwest) authorized sector.
    shrine_factory(name="南の神社", latitude=34.0, longitude=135.0)

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "direction_zero_candidates"
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_missing_purpose_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps({"origin": ORIGIN, "birthdate": BIRTHDATE, "target_date": TARGET_DATE}),
        content_type="application/json",
    )

    assert r.status_code == 400
    assert r.json()["state"] == "invalid_purpose"


@pytest.mark.django_db
def test_recommendation_success_response_includes_distance_stage_metadata(client, shrine_factory):
    # ~35.9km from ORIGIN, northwest -- the only candidate, so it lands at
    # Stage 60 (too few candidates within 15km/30km's expansion threshold).
    shrine_factory(name="北西の神社", latitude=35.25, longitude=134.75, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_success"
    assert body["distance_stage_km"] == 60
    assert body["direction_candidate_count"] == 1
    assert body["distance_candidate_count"] == 1


@pytest.mark.django_db
def test_direction_zero_candidates_response_has_null_stage_and_zero_counts(client, shrine_factory):
    # South of origin -- outside the 北西 (northwest) authorized sector, so
    # excluded by Direction Filter itself; the distance stage is never
    # reached.
    shrine_factory(name="南の神社", latitude=34.0, longitude=135.0)

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "direction_zero_candidates"
    assert body["distance_stage_km"] is None
    assert body["direction_candidate_count"] == 0
    assert body["distance_candidate_count"] == 0


@pytest.mark.django_db
def test_invalid_purpose_response_has_null_distance_stage_metadata(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "not_a_real_tag",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 400
    body = r.json()
    assert body["distance_stage_km"] is None
    assert body["direction_candidate_count"] is None
    assert body["distance_candidate_count"] is None


@pytest.mark.django_db
def test_response_never_leaks_internal_direction_fields(client, shrine_factory):
    shrine_factory(name="北西の神社", latitude=35.25, longitude=134.75, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    direction_context = r.json()["direction_context"]
    assert "excludedDirections" not in direction_context
    assert "luckyDirection" not in direction_context


@pytest.mark.django_db
def test_eligibility_zero_state_is_a_normal_200_result_not_an_error(client, shrine_factory):
    """Shared Recommendation Eligibility gateが候補を全て除外した状態は、
    正常なproduct result（HTTP 200）としてそのままAPI契約に載る。
    backend error（4xx/5xx）にも、他のzero stateにも変換しない。"""
    shrine_factory(
        name="北西の不適格神社",
        latitude=35.25,
        longitude=134.75,
        goriyaku="仕事運",
        usable_knowledge=False,
    )

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_eligibility_zero_candidates"
    assert body["recommendations"] == []
    # Direction / Distance stageへ到達していないためmetadataはnullのまま
    # （でっち上げない）。
    assert body["distance_stage_km"] is None
    assert body["direction_candidate_count"] is None
    assert body["distance_candidate_count"] is None


# ---------------------------------------------------------------------------
# Compass Monthly Public Contract v1 (docs/audit/compass-monthly-api-boundary.md
# Section 9 / 12). HTTP境界としてのallowlist回帰。投影そのものの性質は
# test_compass_public_projection.py が単体で固定している。
# ---------------------------------------------------------------------------

PUBLIC_ITEM_ALLOWLIST = {
    "shrine_id",
    "id",
    "name",
    "address",
    "distance_m",
    "reason",
    "recommendation_instance_id",
    "breakdown",
    "reason_facts",
}

PUBLIC_TOP_LEVEL_KEYS = {
    "state",
    "purpose",
    "direction_context",
    "recommendation_instance_id",
    "recommendations",
    "distance_stage_km",
    "direction_candidate_count",
    "distance_candidate_count",
}

# audit Section 7 の Confirmed leakage + 実装が知らない将来field。
INTERNAL_FIELDS_THAT_MUST_NOT_LEAK = {
    "_explanation_payload": {"prompt": "internal"},
    "_prefilter_debug": {"stage": "debug"},
    "_primary_reason_label": "内部ラベル",
    "_primary_reason_source": "goriyaku_tag",
    "_reason_facts": [{"type": "element", "label": "内部"}],
    "_score_total": 12.5,
    "breakdown_detail": {"a": 1},
    "score_v2": {"total": 9.9},
    "popular_score": 3.0,
    "rank_comparison": {"rank": 1},
    "rank_explanation": {"why": "internal"},
    "recommendation_reason_quality": {"score": 0.8},
    "recommendation_reason_v4_detail": {"draft": "internal"},
    "future_internal_field": "leak?",
    "new_experiment_score": 42,
    "future_debug_payload": {"nested": "leak?"},
}


def _post_valid(client, **overrides):
    payload = {
        "purpose": "career",
        "origin": ORIGIN,
        "birthdate": BIRTHDATE,
        "target_date": TARGET_DATE,
    }
    payload.update(overrides)
    return client.post(URL, data=json.dumps(payload), content_type="application/json")


def _polluted_result(count: int = 2):
    """内部fieldを載せたShared Recommendationを返すorchestrator結果を組み立てる。"""
    from temples.services.compass_recommendation_orchestrator import (
        CompassRecommendationResult,
    )

    recommendations = [
        {
            "shrine_id": 100 + index,
            "id": 100 + index,
            "name": f"神社{index}",
            "address": "東京都千代田区",
            "distance_m": 1000.0 * (index + 1),
            "reason": f"理由{index}",
            "breakdown": {
                "matched_need_tags": ["career"],
                "score_total": 88.0,
                "weights": {"need": 1.0},
            },
            "reason_facts": [
                {
                    "type": "history_theme",
                    "label": "守り",
                    "label_ja": "守り",
                    "is_primary": True,
                    "evidence": ["history_theme"],
                }
            ],
            **INTERNAL_FIELDS_THAT_MUST_NOT_LEAK,
        }
        for index in range(count)
    ]
    return CompassRecommendationResult(
        state="recommendation_success",
        recommendations=recommendations,
        purpose="career",
        direction_context=None,
        distance_stage_km=15,
        direction_candidate_count=count,
        distance_candidate_count=count,
    )


@pytest.mark.django_db
def test_recommendation_items_never_expose_keys_outside_public_allowlist(client, shrine_factory):
    """実データ経路（patchなし）でもitem keyがPublic Contract v1の部分集合。"""
    shrine_factory(name="北西の神社", latitude=35.25, longitude=134.75, goriyaku="仕事運")

    body = _post_valid(client).json()

    assert body["state"] == "recommendation_success"
    assert body["recommendations"], "回帰の前提として候補が1件以上必要"
    assert set(body) == PUBLIC_TOP_LEVEL_KEYS
    for rec in body["recommendations"]:
        assert set(rec).issubset(PUBLIC_ITEM_ALLOWLIST), sorted(set(rec) - PUBLIC_ITEM_ALLOWLIST)


@pytest.mark.django_db
def test_known_internal_and_unknown_future_fields_do_not_leak(client):
    with patch(
        "temples.api_views_compass.get_compass_recommendations",
        return_value=_polluted_result(),
    ):
        body = _post_valid(client).json()

    assert body["recommendations"]
    for rec in body["recommendations"]:
        for field in INTERNAL_FIELDS_THAT_MUST_NOT_LEAK:
            assert field not in rec
        assert set(rec).issubset(PUBLIC_ITEM_ALLOWLIST)


@pytest.mark.django_db
def test_public_recommendation_values_survive_projection(client):
    with patch(
        "temples.api_views_compass.get_compass_recommendations",
        return_value=_polluted_result(count=1),
    ):
        body = _post_valid(client).json()

    rec = body["recommendations"][0]
    assert rec["shrine_id"] == 100
    assert rec["id"] == 100
    assert rec["name"] == "神社0"
    assert rec["address"] == "東京都千代田区"
    assert rec["distance_m"] == 1000.0
    assert rec["reason"] == "理由0"
    assert rec["breakdown"] == {"matched_need_tags": ["career"]}
    assert rec["reason_facts"] == [{"type": "history_theme", "label": "守り"}]


@pytest.mark.django_db
def test_breakdown_exposes_only_matched_need_tags_over_http(client):
    with patch(
        "temples.api_views_compass.get_compass_recommendations",
        return_value=_polluted_result(count=1),
    ):
        body = _post_valid(client).json()

    assert set(body["recommendations"][0]["breakdown"]) == {"matched_need_tags"}


@pytest.mark.django_db
def test_reason_facts_expose_only_type_and_label_over_http(client):
    with patch(
        "temples.api_views_compass.get_compass_recommendations",
        return_value=_polluted_result(count=1),
    ):
        body = _post_valid(client).json()

    for fact in body["recommendations"][0]["reason_facts"]:
        assert set(fact) <= {"type", "label"}


@pytest.mark.django_db
def test_malformed_nested_payloads_fail_safe_without_leaking_raw_values(client):
    from temples.services.compass_recommendation_orchestrator import (
        CompassRecommendationResult,
    )

    result = CompassRecommendationResult(
        state="recommendation_success",
        recommendations=[
            {
                "shrine_id": 1,
                "name": "壊れたbreakdownの神社",
                "breakdown": "matched_need_tags=career",
                "reason_facts": {"type": "element", "label": "水"},
            },
            {
                "shrine_id": 2,
                "name": "壊れたnestedの神社",
                "breakdown": {"matched_need_tags": {"career": True}, "score_total": 1.0},
                "reason_facts": ["element", None, {"type": "element", "label": "水", "score": 1}],
            },
        ],
        purpose="career",
        distance_stage_km=15,
        direction_candidate_count=2,
        distance_candidate_count=2,
    )

    with patch("temples.api_views_compass.get_compass_recommendations", return_value=result):
        body = _post_valid(client).json()

    first, second = body["recommendations"]
    assert "breakdown" not in first
    assert "reason_facts" not in first
    assert second["breakdown"] == {}
    assert second["reason_facts"] == [{"type": "element", "label": "水"}]


@pytest.mark.django_db
def test_projection_preserves_recommendation_order_and_count(client):
    result = _polluted_result(count=3)
    source_ids = [rec["shrine_id"] for rec in result.recommendations]

    with patch("temples.api_views_compass.get_compass_recommendations", return_value=result):
        body = _post_valid(client).json()

    assert [rec["shrine_id"] for rec in body["recommendations"]] == source_ids
    assert len(body["recommendations"]) == len(source_ids)


@pytest.mark.django_db
def test_item_instance_id_equals_top_level_even_when_source_carries_its_own(client):
    """source側のrecommendation_instance_idは採用せず、request単位のcanonicalで上書きする。"""
    result = _polluted_result(count=2)
    for rec in result.recommendations:
        rec["recommendation_instance_id"] = "stale999"

    with patch("temples.api_views_compass.get_compass_recommendations", return_value=result):
        body = _post_valid(client).json()

    canonical = body["recommendation_instance_id"]
    assert canonical != "stale999"
    assert all(rec["recommendation_instance_id"] == canonical for rec in body["recommendations"])


@pytest.mark.django_db
def test_projection_does_not_mutate_the_shared_recommendation_source(client):
    result = _polluted_result(count=1)
    snapshot = copy.deepcopy(result.recommendations)

    with patch("temples.api_views_compass.get_compass_recommendations", return_value=result):
        _post_valid(client)

    assert result.recommendations == snapshot


@pytest.mark.django_db
def test_unexpected_exception_returns_500_error_state(client):
    with patch(
        "temples.api_views_compass.get_compass_recommendations",
        side_effect=RuntimeError("boom"),
    ):
        r = _post_valid(client)

    assert r.status_code == 500
    assert r.json() == {"state": "error"}
