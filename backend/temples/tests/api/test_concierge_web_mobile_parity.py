"""Replay JSON pinned by webMobileParity.test.tsx through the real API and ranker.

Only candidate retrieval, LLM availability, quota and external calls are fixed.
No organic analytics: these are synthetic fixtures in an isolated test database.
"""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.cache import cache

from temples.services.concierge_chat import build_chat_recommendations

FIXTURE = json.loads(
    (
        Path(__file__).resolve().parents[4] / "docs/audit/fixtures/concierge-web-mobile-parity.json"
    ).read_text()
)
CANDIDATES = [
    dict(
        id=31,
        shrine_id=31,
        name="audit-career",
        address="fixture address",
        location="fixture address",
        astro_tags=["career"],
        goriyaku="仕事運",
        description="",
        visit_style_tags=["classic"],
        distance_m=1000,
    ),
    dict(
        id=12,
        shrine_id=12,
        name="audit-quiet",
        address="fixture address",
        location="fixture address",
        astro_tags=["career"],
        goriyaku="仕事運",
        description="",
        visit_style_tags=["quiet"],
        distance_m=1000,
    ),
    dict(
        id=24,
        shrine_id=24,
        name="audit-nature",
        address="fixture address",
        location="fixture address",
        astro_tags=["career"],
        goriyaku="仕事運",
        description="",
        visit_style_tags=["nature"],
        distance_m=1000,
    ),
]


def semantics(kwargs):
    """Omitted/null/empty constraints mean no constraint; keep flow and actual tags distinct."""
    return {
        "query": kwargs["query"],
        "language": kwargs["language"],
        "mode": kwargs["public_mode"],
        "flow": kwargs["flow"],
        "birthdate": kwargs["birthdate"],
        "goriyaku_tag_ids": kwargs["goriyaku_tag_ids"] or [],
        "extra_condition": kwargs["extra_condition"] or "",
        "visit_preferences": kwargs["visit_preferences"] or [],
        "bias": kwargs["bias"],
        # Empty profile containers have no supported scoring signals after birth stripping.
        "profile_birth": (kwargs.get("profile_context") or {})
        .get("user_profile", {})
        .get("birthday"),
        "profile_derived": (kwargs.get("profile_context") or {}).get("derived_profile"),
    }


def identity_and_explanations(recs):
    # Runtime recommendation_instance_id is intentionally new per request; compare
    # domain identity/rank/explanations, not that UUID, trace IDs, or quota counters.
    fields = (
        "shrine_id",
        "reason",
        "reason_facts",
        "recommendation_reason_v4",
        "recommendation_reason_v4_detail",
        "breakdown",
        "breakdown_detail",
    )
    return [{key: rec.get(key) for key in fields} for rec in recs]


def agreement(a, b):
    return {
        "id_set": len(set(a) & set(b)) / len(set(a) | set(b)),
        "rank": sum(x == y for x, y in zip(a, b, strict=False)) / max(len(a), len(b)),
    }


@pytest.mark.django_db
@pytest.mark.parametrize("scenario", FIXTURE["scenarios"], ids=lambda s: s["name"])
def test_actual_platform_payloads_through_api_and_ranker(client, monkeypatch, settings, scenario):
    import temples.api_views_concierge as view

    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("SCORE_V3_MODE", "shadow")
    monkeypatch.setattr(
        view,
        "check_quota",
        lambda *a, **k: SimpleNamespace(allowed=True, remaining=100, limit=100, unlimited=False),
    )
    monkeypatch.setattr(
        view,
        "_build_chat_candidates_pipeline",
        lambda *a, **k: (copy.deepcopy(CANDIDATES), 0, 3, 3),
    )
    monkeypatch.setattr(
        view, "_geocode_area_for_chat", lambda **k: pytest.fail("Unexpected external geocode")
    )
    captured = []
    returned = []

    def rank(**kwargs):
        captured.append(copy.deepcopy(kwargs))
        result = build_chat_recommendations(**kwargs, need_tags=["career"], llm_enabled=False)
        returned.append(result)
        return result

    monkeypatch.setattr(view, "build_chat_recommendations", rank)
    responses = []
    for platform in ("web", "mobile"):
        cache.clear()
        response = client.post(
            "/api/concierge/chat/",
            data=json.dumps(scenario[platform]),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        responses.append(response.json()["data"]["recommendations"])
    assert len(captured) == 2
    assert (semantics(captured[0]) == semantics(captured[1])) is scenario["canonical_equal"]
    assert all(k["birthdate"] is None for k in captured)
    assert all((k.get("profile_context") or {}).get("derived_profile") is None for k in captured)
    for recs, result in zip(responses, returned, strict=True):
        assert len(recs) == 3
        # The API response builder must not reorder or replace shrine identity.
        assert [r["shrine_id"] for r in recs] == [r["shrine_id"] for r in result["recommendations"]]
        assert all(r["id"] == r["shrine_id"] for r in recs)
    for platform, recs in zip(("web", "mobile"), responses, strict=True):
        expected = FIXTURE["responses"][scenario["expected_responses"][platform]]
        assert [{key: r.get(key) for key in expected[0]} for r in recs] == expected
    a, b = ([r["shrine_id"] for r in recs] for recs in responses)
    result = agreement(a, b)
    explanations_equal = identity_and_explanations(responses[0]) == identity_and_explanations(
        responses[1]
    )
    if scenario["canonical_equal"]:
        assert result == {"id_set": 1, "rank": 1}
        assert explanations_equal
    print(
        json.dumps(
            {
                "scenario": scenario["name"],
                "web_ids": a,
                "mobile_ids": b,
                **result,
                "explanations_equal": explanations_equal,
            },
            ensure_ascii=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.parametrize("empty", [None, "", []])
def test_missing_empty_null_optional_constraints_do_not_create_filters(empty):
    from temples.services.concierge_input_contract import normalize_concierge_request

    missing = normalize_concierge_request({"query": FIXTURE["query"]})
    supplied = normalize_concierge_request(
        {
            "query": FIXTURE["query"],
            "goriyaku_tag_ids": empty,
            "extra_condition": empty,
            "visit_preferences": empty,
        }
    )
    assert (supplied.goriyaku_tag_ids or []) == (missing.goriyaku_tag_ids or [])
    assert (supplied.extra_condition or "") == (missing.extra_condition or "")
    assert supplied.visit_preferences == missing.visit_preferences == []
