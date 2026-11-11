"""休息・不安の相談で、参拝の好み（静か・自然・人が少なめ）を自動で足す（点数だけ）。

- 相談の種類が rest / mental のとき、quiet・nature・less_crowded を自動で足す。
- 利用者が選んだ好み・相談文の言葉から拾った好みと同じものは足さない（重ねて数えない）。
- 自動で足した好みは、何個一致しても1つ分（× 0.35）まで。
- 自動で足した好みは点数にだけ使い、主な根拠・説明の文には使わない。
"""

from __future__ import annotations

import pytest

from temples.domain.visit_preference import (
    IMPLIED_VISIT_STYLE_MAX_MATCHES,
    implied_visit_style_tags_for_needs,
)
from temples.services import concierge_chat
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import _attach_breakdown

REST_TAGS = {"quiet", "nature", "less_crowded"}
VISIT_STYLE_WEIGHT = 0.35


def _candidate(name: str, visit_style_tags: list[str], **overrides) -> dict:
    row = {
        "id": sum(map(ord, name)),
        "shrine_id": sum(map(ord, name)),
        "name": name,
        "address": "東京都試験区1-1-1",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": None,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "goriyaku_tag_names": [],
        "visit_style_tags": visit_style_tags,
        "popular_score": 0.0,
    }
    row.update(overrides)
    return row


def _recommend(query: str, candidates: list[dict]) -> list[dict]:
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    return recs["recommendations"]


def _without_implied(monkeypatch) -> None:
    """変更の前と同じ動き（自動で足す好みが無い）にする。"""
    monkeypatch.setattr(concierge_chat, "implied_visit_style_tags_for_needs", lambda *a, **k: frozenset())


def _features(rec: dict) -> dict:
    return rec["breakdown_detail"]["features"]


# ---------- 相談の種類 → 自動で足す好み ----------


@pytest.mark.parametrize("need", ["rest", "mental"])
def test_rest_and_mental_imply_quiet_nature_less_crowded(need):
    assert implied_visit_style_tags_for_needs([need]) == REST_TAGS


@pytest.mark.parametrize("needs", [[], ["money"], ["love", "study"], None])
def test_other_needs_imply_nothing(needs):
    assert implied_visit_style_tags_for_needs(needs) == frozenset()


def test_explicit_tags_are_not_added_again():
    assert implied_visit_style_tags_for_needs(["rest"], explicit_tags={"quiet"}) == {"nature", "less_crowded"}
    assert implied_visit_style_tags_for_needs(["rest", "mental"], explicit_tags=REST_TAGS) == frozenset()


def test_cap_is_one_match():
    assert IMPLIED_VISIT_STYLE_MAX_MATCHES == 1


# ---------- 点数（_attach_breakdown）----------


def _breakdown(visit_style_tags, *, user_tags, implied_tags, need_tags=("rest",)):
    rec = _candidate("試験神社", list(visit_style_tags))
    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=list(need_tags),
        weights={"element": 0.6, "need": 0.3, "popular": 0.1, "distance": 0.35},
        astro_bonus_enabled=False,
        visit_style_tags=set(user_tags),
        implied_visit_style_tags=set(implied_tags),
    )
    return rec


def test_implied_matches_count_as_one_even_if_three_match():
    rec = _breakdown(["quiet", "nature", "less_crowded"], user_tags=set(), implied_tags=REST_TAGS)
    implied = _features(rec)["implied_visit_style"]
    assert implied["matched_tags"] == ["less_crowded", "nature", "quiet"]
    assert implied["raw"] == 1
    assert implied["contribution"] == pytest.approx(VISIT_STYLE_WEIGHT)
    assert rec["_score_total"] == pytest.approx(VISIT_STYLE_WEIGHT)


def test_implied_matches_are_not_reasons():
    rec = _breakdown(["quiet", "nature"], user_tags=set(), implied_tags=REST_TAGS)
    visit_style = _features(rec)["visit_style"]
    assert visit_style["raw"] == 0
    assert visit_style["matched_tags"] == []
    assert visit_style["contribution"] == 0.0
    assert all(fact["type"] != "visit_style" for fact in rec["reason_facts"])
    assert rec["_primary_reason_source"] == "fallback"


def test_user_tags_keep_counting_and_implied_adds_at_most_one():
    rec = _breakdown(
        ["quiet", "nature", "less_crowded"],
        user_tags={"quiet"},
        implied_tags={"nature", "less_crowded"},
    )
    features = _features(rec)
    assert features["visit_style"]["matched_tags"] == ["quiet"]
    assert features["visit_style"]["raw"] == 1
    assert features["implied_visit_style"]["raw"] == 1
    assert rec["_score_total"] == pytest.approx(VISIT_STYLE_WEIGHT * 2)
    visit_facts = [fact for fact in rec["reason_facts"] if fact["type"] == "visit_style"]
    assert [fact["evidence"] for fact in visit_facts] == [["quiet"]]


def test_implied_tag_that_the_user_also_chose_is_not_counted_twice():
    rec = _breakdown(["quiet"], user_tags={"quiet"}, implied_tags={"quiet"})
    features = _features(rec)
    assert features["visit_style"]["raw"] == 1
    assert features["implied_visit_style"]["raw"] == 0
    assert rec["_score_total"] == pytest.approx(VISIT_STYLE_WEIGHT)


def test_no_implied_tags_means_no_implied_score():
    rec = _breakdown(["quiet", "nature"], user_tags=set(), implied_tags=set(), need_tags=("money",))
    implied = _features(rec)["implied_visit_style"]
    assert implied["raw"] == 0
    assert implied["contribution"] == 0.0
    assert rec["_score_total"] == 0.0


# ---------- 相談全体（build_chat_recommendations）----------


REASON_KEYS = ("_primary_reason_source", "_primary_reason_label", "reason", "reason_facts")


def _reason_view(rec: dict) -> dict:
    view = {key: rec.get(key) for key in REASON_KEYS}
    view["explanation"] = rec.get("explanation")
    view["interpretation"] = ((rec.get("recommendation_reason_v4_detail") or {}).get("interpretation") or {}).get(
        "text"
    )
    view["rank_summary"] = (rec.get("rank_explanation") or {}).get("summary")
    return view


@pytest.mark.django_db
def test_rest_only_implied_match_keeps_primary_reason_and_explanation(monkeypatch, settings):
    """「休みたい」で、自動で足した好みだけが一致したとき、主な根拠と説明の文は変更の前と同じ。"""
    settings.CONCIERGE_USE_LLM = False
    candidate = _candidate("静かな杜の神社", ["quiet", "nature"])

    after = _recommend("休みたい", [dict(candidate)])[0]
    with monkeypatch.context() as m:
        _without_implied(m)
        before = _recommend("休みたい", [dict(candidate)])[0]

    assert after["breakdown"]["matched_need_tags"] == []
    assert _features(after)["implied_visit_style"]["matched_tags"] == ["nature", "quiet"]
    assert _features(after)["visit_style"]["matched_tags"] == []
    assert _reason_view(after) == _reason_view(before)
    assert before["_primary_reason_source"] == "fallback"
    # 点数だけが 1つ分（0.35）上がる。
    assert after["_score_total"] == pytest.approx(before["_score_total"] + VISIT_STYLE_WEIGHT)


@pytest.mark.django_db
def test_rest_ranks_quiet_nature_shrine_above_untagged_shrine(settings):
    settings.CONCIERGE_USE_LLM = False
    recs = _recommend(
        "休みたい",
        [_candidate("あ街なかの神社", ["urban"]), _candidate("ん静かな杜の神社", ["quiet", "nature"])],
    )
    assert [rec["name"] for rec in recs][:2] == ["ん静かな杜の神社", "あ街なかの神社"]


@pytest.mark.django_db
def test_query_derived_quiet_still_counts_as_reason_and_implied_adds_nature(settings):
    """相談文の「落ち着」から拾った quiet は今までどおり根拠。自動で足すのは nature・less_crowded だけ。"""
    settings.CONCIERGE_USE_LLM = False
    rec = _recommend("気持ちを落ち着けて休みたい", [_candidate("静かな杜の神社", ["quiet", "nature"])])[0]
    features = _features(rec)
    assert features["visit_style"]["matched_tags"] == ["quiet"]
    assert features["implied_visit_style"]["requested_tags"] == ["less_crowded", "nature"]
    assert features["implied_visit_style"]["matched_tags"] == ["nature"]
    assert rec["_primary_reason_source"] == "visit_style"
    visit_facts = [fact for fact in rec["reason_facts"] if fact["type"] == "visit_style"]
    assert [fact["evidence"] for fact in visit_facts] == [["quiet"]]


@pytest.mark.django_db
def test_other_consultations_are_unchanged(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    candidate = _candidate("静かな杜の神社", ["quiet", "nature"], goriyaku="金運")

    after = _recommend("金運を上げたい", [dict(candidate)])[0]
    with monkeypatch.context() as m:
        _without_implied(m)
        before = _recommend("金運を上げたい", [dict(candidate)])[0]

    assert _features(after)["implied_visit_style"]["raw"] == 0
    assert after["_score_total"] == before["_score_total"]
    assert _reason_view(after) == _reason_view(before)
