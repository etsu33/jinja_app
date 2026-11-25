import json
import pytest

from temples.models import Shrine
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact


def _eligible_shrine(name: str) -> Shrine:
    """Shared Recommendation Eligibility gateを通過できるShrineを1件作る。

    requestで持ち込まれる候補も共有gateを通るため、eligibleなShrineを指す
    shrine_idが無い候補はRecommendationへ入れない（fallback再流入の禁止）。
    """
    shrine = Shrine.objects.create(
        name_jp=name, address="東京都千代田区1-1", latitude=35.0, longitude=139.0
    )
    attach_usable_deity_fact(shrine)
    return shrine

URL = "/api/concierge/chat/"


@pytest.mark.django_db
def test_concierge_chat_dedupes_user_and_built_candidates_by_place_id(
    client, monkeypatch, settings
):
    settings.CONCIERGE_USE_LLM = False

    import temples.api_views_concierge as concierge_mod
    captured = {}

    monkeypatch.setattr(
        concierge_mod,
        "build_chat_candidates",
        lambda **kwargs: [
            {
                "place_id": "PID_DUP",
                "name": "重複神社",
                "address": "東京都千代田区1-1",
                "lat": 35.0,
                "lng": 139.0,
                "distance_m": 120,
                "popular_score": 5.0,
                "astro_tags": ["mental"],
                "knowledge_deities": [{"display_name": "祭神", "sort_order": 0, "confidence": "high"}],
                "knowledge_histories": [],
            },
            {
                "place_id": "PID_ONLY_BUILT",
                "name": "別神社",
                "address": "東京都千代田区2-2",
                "lat": 35.01,
                "lng": 139.01,
                "distance_m": 220,
                "popular_score": 4.0,
                "astro_tags": ["rest"],
                "knowledge_deities": [{"display_name": "祭神", "sort_order": 0, "confidence": "high"}],
                "knowledge_histories": [],
            },
        ],
        raising=True,
    )

    def fake_build_chat_recommendations(**kwargs):
        captured["candidates"] = kwargs["candidates"]
        return {"recommendations": kwargs["candidates"][:3]}

    monkeypatch.setattr(
        concierge_mod,
        "build_chat_recommendations",
        fake_build_chat_recommendations,
        raising=True,
    )

    user_shrine = _eligible_shrine("重複神社")
    payload = {
        "message": "近場で静かに参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "candidates": [
            {
                "shrine_id": user_shrine.id,
                "place_id": "PID_DUP",
                "name": "重複神社",
                "address": "東京都千代田区1-1",
                "lat": 35.0,
                "lng": 139.0,
                "distance_m": 100,
                "popular_score": 8.0,
                "astro_tags": ["mental", "rest"],
            }
        ],
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    body = r.json()
    assert body["ok"] is True

    debug = body["_debug"]
    assert debug["before"] == 2

    cands = captured["candidates"]
    assert len(cands) == 2
    assert [c.get("place_id") for c in cands] == ["PID_DUP", "PID_ONLY_BUILT"]


@pytest.mark.django_db
def test_concierge_chat_dedupe_keeps_user_candidate_first(client, monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False

    import temples.api_views_concierge as concierge_mod
    captured = {}

    monkeypatch.setattr(
        concierge_mod,
        "build_chat_candidates",
        lambda **kwargs: [
            {
                "place_id": "PID_DUP",
                "name": "重複神社",
                "address": "東京都千代田区1-1",
                "popular_score": 1.0,
                "astro_tags": [],
                "knowledge_deities": [{"display_name": "祭神", "sort_order": 0, "confidence": "high"}],
                "knowledge_histories": [],
            }
        ],
        raising=True,
    )

    def fake_build_chat_recommendations(**kwargs):
        captured["candidates"] = kwargs["candidates"]
        return {"recommendations": kwargs["candidates"][:3]}

    monkeypatch.setattr(
        concierge_mod,
        "build_chat_recommendations",
        fake_build_chat_recommendations,
        raising=True,
    )

    user_shrine = _eligible_shrine("重複神社")
    payload = {
        "message": "近場で参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "candidates": [
            {
                "shrine_id": user_shrine.id,
                "place_id": "PID_DUP",
                "name": "重複神社",
                "address": "東京都千代田区1-1",
                "popular_score": 9.0,
                "astro_tags": ["rest"],
                "source": "user",
            }
        ],
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    cands = captured["candidates"]
    target = next(x for x in cands if x.get("place_id") == "PID_DUP")

    assert target["source"] == "user"
