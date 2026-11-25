# -*- coding: utf-8 -*-
import json

import pytest

URL = "/api/concierge/chat/"


@pytest.mark.django_db
def test_chat_promotes_filters_to_top_level_and_keeps_need_mode_when_query_exists(client, monkeypatch):
    """
    CR-001:
    filters.birthdate / filters.goriyaku_tag_ids / filters.extra_condition が
    top-level 未指定時に build_chat_recommendations へ渡ること。
    ただし message/query があるので public_mode='need', flow='A' を維持すること。
    """
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {
        "message": "近場で参拝したい",
        "lat": 35.0,
        "lng": 139.0,
        "filters": {
            "birthdate": "1984-05-15",
            "goriyaku_tag_ids": [10, 20],
            "extra_condition": "静か",
        },
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert captured["query"] == "近場で参拝したい"
    assert captured["birthdate"] is None  # コンシェルジュでは生年月日を使わない
    assert captured["goriyaku_tag_ids"] == [10, 20]
    assert captured["extra_condition"] == "静か"
    assert captured["public_mode"] == "need"
    assert captured["flow"] == "B"


@pytest.mark.django_db
def test_chat_top_level_values_override_filters_values_and_keep_need_mode(client, monkeypatch):
    """
    CR-001:
    top-level と filters の両方に値があるときは top-level 優先。
    かつ query/message があるため public_mode='need', flow='A' を維持する。
    """
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {
        "message": "転職が気になる",
        "lat": 35.0,
        "lng": 139.0,
        "birthdate": "1990-01-01",
        "goriyaku_tag_ids": [999],
        "extra_condition": "にぎやか",
        "filters": {
            "birthdate": "1984-05-15",
            "goriyaku_tag_ids": [10, 20],
            "extra_condition": "静か",
        },
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert captured["query"] == "転職が気になる"
    assert captured["birthdate"] is None  # コンシェルジュでは生年月日を使わない
    assert captured["goriyaku_tag_ids"] == [999]
    assert captured["extra_condition"] == "にぎやか"
    assert captured["public_mode"] == "need"
    assert captured["flow"] == "B"

@pytest.mark.django_db
def test_chat_date_only_query_is_rejected_not_rescued_as_birthdate(client, monkeypatch):
    """
    CR-002:
    以前は query が YYYY-MM-DD 形式なら birthdate に救済し、compat にしていた。
    コンシェルジュでは生年月日を使わないため、相談の文が無い扱いで 400 になる。
    """
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {
        "query": "1984-05-15",
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    # コンシェルジュでは生年月日を使わない: 日付だけ・生年月日だけでは相談にしない（相性モードにもしない）。
    assert r.status_code == 400
    assert captured == {}


@pytest.mark.django_db
def test_chat_birthdate_only_is_rejected_without_query(client, monkeypatch):
    """
    CR-002:
    以前は birthdate だけの入力でも compat として推薦へ進んでいた。
    コンシェルジュでは生年月日を使わないため、相談の文が無い扱いで 400 になる。
    """
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {
        "birthdate": "1984-05-15",
        "query": "",
    }

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    # コンシェルジュでは生年月日を使わない: 日付だけ・生年月日だけでは相談にしない（相性モードにもしない）。
    assert r.status_code == 400
    assert captured == {}

@pytest.mark.django_db
def test_chat_slash_date_only_query_is_rejected(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {"query": "1984/05/15"}

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    # コンシェルジュでは生年月日を使わない: 日付だけ・生年月日だけでは相談にしない（相性モードにもしない）。
    assert r.status_code == 400
    assert captured == {}

@pytest.mark.django_db
def test_chat_slash_date_only_query_is_rejected(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {"query": "1984/05/15"}

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    # コンシェルジュでは生年月日を使わない: 日付だけ・生年月日だけでは相談にしない（相性モードにもしない）。
    assert r.status_code == 400
    assert captured == {}


@pytest.mark.django_db
def test_chat_compact_date_only_query_is_rejected(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {"query": "19840515"}

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    # コンシェルジュでは生年月日を使わない: 日付だけ・生年月日だけでは相談にしない（相性モードにもしない）。
    assert r.status_code == 400
    assert captured == {}

@pytest.mark.django_db
def test_chat_does_not_rescue_invalid_birthdate_query(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_candidates",
        lambda **kwargs: [],
    )

    def fake_build_chat_recommendations(**kwargs):
        captured.update(kwargs)
        return {
            "recommendations": [
                {"name": "A", "reason": "ok", "breakdown": {"matched_need_tags": []}}
            ]
        }

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        fake_build_chat_recommendations,
    )

    payload = {"query": "1984-02-30"}

    r = client.post(URL, data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200

    assert captured["query"] == "1984-02-30"
    assert captured["birthdate"] is None
    assert captured["public_mode"] == "need"
    assert captured["flow"] == "A"
