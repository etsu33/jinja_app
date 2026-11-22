"""見どころ単位の推薦 段階A：推薦に「ここで見る」見どころを付ける（順位は変えない）。"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.highlight_pick import attach_highlight_picks, ordered_need_tags
from temples.tests.highlight_factories import (
    link_source,
    make_answer,
    make_displayable_highlight,
    make_highlight,
    make_shrine,
    make_source,
    make_translation,
)

pytestmark = pytest.mark.django_db


def _rec(shrine):
    return {"shrine_id": shrine.pk, "name": shrine.name_jp}


# --- 選び方 -------------------------------------------------------------------


def test_need_tags_are_ordered_by_priority_and_unknown_dropped():
    assert ordered_need_tags(["rest", "career", "unknown", "protection"]) == [
        "protection",
        "career",
        "rest",
    ]


def test_pick_is_attached_when_answer_matches_need():
    shrine = make_shrine("芸能の社")
    highlight = make_displayable_highlight(shrine, name="芸能浅間神社")
    make_answer(highlight, need_tag="career", answer_text="建て直した由来が重なるかもしれない。")
    recs = [_rec(shrine)]

    observation = attach_highlight_picks(recs, ["career"], "ja")

    assert recs[0]["highlight_pick"] == {
        "highlight_id": highlight.pk,
        "shrine_id": shrine.pk,
        "name": "芸能浅間神社",
        "need_tag": "career",
        "answer_text": "建て直した由来が重なるかもしれない。",
    }
    assert observation["shown_count"] == 1


def test_no_pick_when_need_does_not_match():
    shrine = make_shrine()
    make_answer(make_displayable_highlight(shrine), need_tag="career")
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["love"], "ja")
    assert recs[0]["highlight_pick"] is None


def test_no_pick_without_need_tags_and_no_query():
    shrine = make_shrine()
    make_answer(make_displayable_highlight(shrine), need_tag="career")
    recs = [_rec(shrine)]
    with CaptureQueriesContext(connection) as ctx:
        attach_highlight_picks(recs, [], "ja")
    assert recs[0]["highlight_pick"] is None
    assert len(ctx.captured_queries) == 0


def test_unapproved_answer_is_not_picked():
    shrine = make_shrine()
    make_answer(make_displayable_highlight(shrine), need_tag="career", review_status="draft")
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["career"], "ja")
    assert recs[0]["highlight_pick"] is None


def test_answer_on_unpublished_highlight_is_not_picked():
    shrine = make_shrine()
    highlight = make_highlight(shrine, publication_status="draft")
    make_translation(highlight)
    link_source(highlight, make_source())
    make_answer(highlight, need_tag="career")
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["career"], "ja")
    assert recs[0]["highlight_pick"] is None


def test_higher_priority_need_wins_over_sort_order():
    shrine = make_shrine()
    first = make_displayable_highlight(shrine, name="鳥居")  # sort_order 0
    second = make_displayable_highlight(shrine, name="拝殿")
    second.sort_order = 5
    second.save()
    make_answer(first, need_tag="rest")
    make_answer(second, need_tag="career")  # career は rest より優先順が高い
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["rest", "career"], "ja")
    assert recs[0]["highlight_pick"]["highlight_id"] == second.pk


def test_same_need_picks_smaller_sort_order():
    shrine = make_shrine()
    late = make_displayable_highlight(shrine, name="唐獅子")
    late.sort_order = 6
    late.save()
    early = make_displayable_highlight(shrine, name="大鳥居")
    early.sort_order = 1
    early.save()
    make_answer(late, need_tag="career")
    make_answer(early, need_tag="career")
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["career"], "ja")
    assert recs[0]["highlight_pick"]["highlight_id"] == early.pk


def test_answer_of_other_shrine_is_not_used():
    shrine_a = make_shrine("社A")
    shrine_b = make_shrine("社B")
    make_answer(make_displayable_highlight(shrine_b), need_tag="career")
    recs = [_rec(shrine_a), _rec(shrine_b)]
    attach_highlight_picks(recs, ["career"], "ja")
    assert recs[0]["highlight_pick"] is None
    assert recs[1]["highlight_pick"]["shrine_id"] == shrine_b.pk


def test_english_uses_only_english_answers():
    shrine = make_shrine()
    highlight = make_displayable_highlight(shrine)  # 日本語の翻訳だけ
    make_answer(highlight, need_tag="career", language_code="ja")
    recs = [_rec(shrine)]
    attach_highlight_picks(recs, ["career"], "en")
    assert recs[0]["highlight_pick"] is None


def test_order_and_other_fields_are_not_changed():
    shrines = [make_shrine(f"社{i}") for i in range(3)]
    make_answer(make_displayable_highlight(shrines[2]), need_tag="career")
    recs = [{**_rec(s), "score": 3 - i, "reason": f"理由{i}"} for i, s in enumerate(shrines)]
    before = [(r["shrine_id"], r["score"], r["reason"]) for r in recs]
    attach_highlight_picks(recs, ["career"], "ja")
    assert [(r["shrine_id"], r["score"], r["reason"]) for r in recs] == before


def test_query_count_does_not_grow_with_recommendations():
    def build(n, prefix):
        shrines = [make_shrine(f"{prefix}{i}") for i in range(n)]
        for s in shrines:
            make_answer(make_displayable_highlight(s), need_tag="career")
        return [_rec(s) for s in shrines]

    small = build(1, "少")
    with CaptureQueriesContext(connection) as one:
        attach_highlight_picks(small, ["career"], "ja")
    large = build(3, "多")
    with CaptureQueriesContext(connection) as three:
        attach_highlight_picks(large, ["career"], "ja")
    assert len(three.captured_queries) == len(one.captured_queries)
    assert all(r["highlight_pick"] for r in large)


# --- build_chat_recommendations との結合 -------------------------------------


def _candidate(shrine, popular):
    return {
        "id": shrine.pk,
        "shrine_id": shrine.pk,
        "name": shrine.name_jp,
        "address": shrine.address,
        "distance_m": 500.0,
        "lat": shrine.latitude,
        "lng": shrine.longitude,
        "popular_score": popular,
    }


def _run(candidates):
    return build_chat_recommendations(query="転職したい", language="ja", candidates=candidates)


def test_chat_recommendations_get_pick_without_changing_order(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")
    shrines = [make_shrine(f"結合の社{i}") for i in range(3)]
    for i, s in enumerate(shrines):
        s.latitude = 35.0 + i * 0.001
        s.save()
    candidates = [_candidate(s, 9.0 - i) for i, s in enumerate(shrines)]

    before = _run(candidates)
    order_before = [r["shrine_id"] for r in before["recommendations"]]
    assert all(r.get("highlight_pick") is None for r in before["recommendations"])

    target = shrines[1]
    make_answer(make_displayable_highlight(target, name="芸能浅間神社"), need_tag="career")
    after = _run(candidates)

    assert [r["shrine_id"] for r in after["recommendations"]] == order_before
    picks = {r["shrine_id"]: r.get("highlight_pick") for r in after["recommendations"]}
    assert picks[target.pk]["name"] == "芸能浅間神社"
    assert after["_debug"]["highlight_pick"]["need_tags"] == ["career"]
    # 推薦理由には入れない
    target_rec = next(r for r in after["recommendations"] if r["shrine_id"] == target.pk)
    assert all("highlight" not in str(f.get("type")) for f in target_rec.get("reason_facts") or [])
