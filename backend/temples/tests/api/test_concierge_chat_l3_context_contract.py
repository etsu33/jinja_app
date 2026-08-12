# -*- coding: utf-8 -*-
"""Level 3 Recommendation Context contract tests (view / HTTP level).

Covers docs/product/concierge-input-architecture.md Addendum: Level 3
Profile / Explicit Constraint / Recommendation Context Contract.

Location source priority (top-level lat/lng > location{} > area geocode)
is already covered by
temples/tests/api/test_concierge_chat_view_characterization.py -- not
duplicated here.
"""
import json
from types import SimpleNamespace

import pytest

URL = "/api/concierge/chat/"


def _stub_recommendations(monkeypatch):
    """Returns (captured_kwargs, returned_recs_holder). Unlike the plain
    kwargs-only stubs elsewhere, this also exposes the actual dict object
    returned to the view, so tests can inspect what the view mutates onto
    it afterwards (e.g. recs["_debug"]["l3_context"])."""
    captured = {}
    holder = {}

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        recs = {
            "recommendations": [
                {
                    "name": "神社A",
                    "reason": "ok",
                    "reason_source": "reason:test",
                    "breakdown": {"matched_need_tags": []},
                }
            ]
        }
        holder["recs"] = recs
        return recs

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )
    return captured, holder


@pytest.mark.django_db
def test_l3_context_debug_payload_reflects_resolved_lat_lng_radius_visit_date(client, monkeypatch):
    captured, holder = _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    payload = {
        "message": "近場で参拝したい",
        "lat": 35.6812,
        "lng": 139.7671,
        "radius_m": 12000,
        "visit_date": "2026-09-01",
    }
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    l3_context = holder["recs"]["_debug"]["l3_context"]
    assert l3_context == {
        "lat": pytest.approx(35.6812),
        "lng": pytest.approx(139.7671),
        "radius_m": 12000,
        "visit_date": "2026-09-01",
    }


@pytest.mark.django_db
def test_l3_context_debug_payload_is_stripped_from_public_response(client, monkeypatch):
    _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    payload = {"message": "近場で参拝したい", "lat": 35.0, "lng": 139.0}
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    body = r.json()
    assert "_debug" not in body.get("data", {})


@pytest.mark.django_db
def test_l3_context_visit_date_wins_over_planned_visit_date_alias(client, monkeypatch):
    _, holder = _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    payload = {
        "message": "参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "visit_date": "2026-09-01",
        "planned_visit_date": "2026-12-25",
    }
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert holder["recs"]["_debug"]["l3_context"]["visit_date"] == "2026-09-01"


@pytest.mark.django_db
def test_l3_context_uses_planned_visit_date_when_visit_date_absent(client, monkeypatch):
    _, holder = _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    payload = {
        "message": "参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "planned_visit_date": "2026-12-25",
    }
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert holder["recs"]["_debug"]["l3_context"]["visit_date"] == "2026-12-25"


@pytest.mark.django_db
def test_radius_is_never_passed_to_candidate_building_hard_filter_parity(client, monkeypatch):
    """radius/radius_m never becomes a Candidate hard filter in the
    Concierge Chat pipeline (that's /nearest's responsibility, a different
    endpoint) -- this PR does not change that."""
    _stub_recommendations(monkeypatch)
    captured_cands = {}

    def fake_build_chat_candidates(**kwargs):
        captured_cands.update(kwargs)
        return []

    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", fake_build_chat_candidates)

    payload = {"message": "近場で参拝したい", "lat": 35.0, "lng": 139.0, "radius_m": 500}
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert "radius_m" not in captured_cands
    assert "radius" not in captured_cands


@pytest.mark.django_db
def test_profile_context_birthdate_takes_priority_over_canonical_birthdate_for_direction_calc(
    client, monkeypatch
):
    """Level 3-A: profile_context.user_profile.birthdate wins over the
    canonical scoring birthdate ONLY for the direction-calc call site --
    a documented, separate precedence chain (resolve_profile_context_birthdate
    docstring)."""
    _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    captured_direction_args = {}

    def fake_annual_lucky_directions(birthdate):
        captured_direction_args["birthdate"] = birthdate
        return None

    monkeypatch.setattr(
        "temples.api_views_concierge.annual_lucky_directions",
        fake_annual_lucky_directions,
    )

    payload = {
        "message": "参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "birthdate": "1990-01-01",
        "profile_context": {"user_profile": {"birthdate": "1985-06-15"}},
    }
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert captured_direction_args["birthdate"] == "1985-06-15"


@pytest.mark.django_db
def test_canonical_birthdate_used_for_direction_calc_when_profile_context_absent(client, monkeypatch):
    _stub_recommendations(monkeypatch)
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    captured_direction_args = {}

    def fake_annual_lucky_directions(birthdate):
        captured_direction_args["birthdate"] = birthdate
        return None

    monkeypatch.setattr(
        "temples.api_views_concierge.annual_lucky_directions",
        fake_annual_lucky_directions,
    )

    payload = {
        "message": "参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "birthdate": "1990-01-01",
    }
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert captured_direction_args["birthdate"] == "1990-01-01"


@pytest.mark.django_db
def test_blocked_request_does_not_trigger_geocode(client, monkeypatch):
    """Level 3-C Context construction (including lat/lng resolution, which
    can geocode `area`) must keep happening AFTER the quota gate -- moving
    it earlier would add wasted external geocode calls for requests that
    get rejected anyway (see ConciergeRecommendationContext docstring)."""

    def fake_resolve_plan_context(request):
        return SimpleNamespace(plan="anonymous", anon_id="anon-test-id")

    def fake_check_quota(plan_context, feature):
        return SimpleNamespace(allowed=False, unlimited=False, remaining=0, limit=0)

    geocode_calls = {"count": 0}

    def fake_geocode(*args, **kwargs):
        geocode_calls["count"] += 1
        return (35.0, 139.0)

    monkeypatch.setattr("temples.api_views_concierge.resolve_plan_context", fake_resolve_plan_context)
    monkeypatch.setattr("temples.api_views_concierge.check_quota", fake_check_quota)
    monkeypatch.setattr("temples.api_views_concierge.geocode_google_point", fake_geocode)

    payload = {"message": "近場で参拝したい", "area": "東京駅"}
    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200
    assert r.json().get("limitReached") is True
    assert geocode_calls["count"] == 0
