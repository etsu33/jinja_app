"""B-1: Concierge recommendation history batch loading（concierge_history.load_shrine_history_facts）.

The per-shrine functions（classify_shrine_action_state / calculate_shrine_behavior_signal_breakdown /
build_recent_reflection_hint）are unchanged and serve as the oracle. These tests check that:

- the batch facts reproduce their output exactly, per shrine and end to end;
- anonymous behaviour is unchanged;
- authenticated queries no longer scale with the candidate count.
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from temples.models import ShrineReflection
from temples.services import concierge_history as ch
from temples.services.concierge_chat import _attach_chat_rec_enrichment, _sort_chat_recommendations

from tests import concierge_history_fixtures as fx

pytestmark = pytest.mark.django_db

MAX_BATCH_QUERIES = 5  # interaction logs, favorites, visits, completed actions, reflections


@pytest.fixture(autouse=True)
def _frozen_now(monkeypatch):
    monkeypatch.setattr("temples.services.concierge_history.timezone.now", lambda: fx.NOW)


@pytest.fixture
def users(django_user_model):
    return (
        django_user_model.objects.create_user(username="b1-user", password="pw-b1"),
        django_user_model.objects.create_user(username="b1-other", password="pw-b1"),
    )


@pytest.fixture
def shrines():
    return fx.make_shrines(20)


@pytest.fixture
def mixed(users, shrines):
    user, other = users
    fx.build_mixed_history(user, other, shrines)
    return user, other, shrines


def _legacy(user, shrine_id):
    return (
        ch.calculate_shrine_behavior_signal_breakdown(user=user, shrine_id=shrine_id),
        ch.classify_shrine_action_state(user=user, shrine_id=shrine_id),
        ch.build_recent_reflection_hint(user=user, shrine_id=shrine_id),
    )


def _batched(facts_by_id, shrine_id):
    facts = facts_by_id.get(shrine_id, ch.EMPTY_SHRINE_HISTORY_FACTS)
    return (
        ch.behavior_signal_breakdown_from_facts(facts),
        ch.action_state_from_facts(facts),
        ch.reflection_hint_from_facts(facts),
    )


def _enrich(recs, user, *, batch):
    _attach_chat_rec_enrichment(
        recs,
        public_mode="need",
        query="仕事 縁結び",
        birthdate=None,
        need_tags=["career", "love"],
        weights={"element": 0.0, "need": 1.0, "popular": 0.2, "distance": 0.1},
        astro_bonus_enabled=False,
        soft_signal_tags=set(),
        visit_style_tags=set(),
        goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=user,
        batch_history=batch,
    )
    return recs


# --- per-shrine equivalence -------------------------------------------------------------------------


def test_mixed_history_matches_per_shrine_functions_for_every_candidate(mixed):
    user, _other, shrines = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[s.pk for s in shrines])
    for shrine in shrines:
        assert _batched(facts, shrine.pk) == _legacy(user, shrine.pk), shrine.name_jp


def test_expected_states_for_the_fixture(mixed):
    """Pins the fixture semantics, so that the equivalence above cannot pass trivially."""
    user, _other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[x.pk for x in s])
    states = [ch.action_state_from_facts(facts.get(x.pk, ch.EMPTY_SHRINE_HISTORY_FACTS)) for x in s[:10]]
    assert states == ["reflected", "saved", "none", "route_opened", "reflected", "detail_viewed", "visited", "none", "none", "none"]
    f0 = facts[s[0].pk]
    assert (f0.detail_view_count, f0.route_open_count) == (3, 1)
    assert f0.detail_view_latest == fx.ago(1)
    assert f0.visit_added_latest == fx.ago(10)  # the newer "removed" visit is ignored
    assert f0.action_completed_latest == fx.ago(100)  # action_started is ignored
    assert f0.latest_reflection.answer == "前より落ち着いた"  # newest of two reflections
    assert facts[s[6].pk].visit_added_latest == fx.ago(15)


def test_empty_history_matches_per_shrine_functions(users, shrines):
    user, _other = users
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[s.pk for s in shrines])
    assert facts == {}
    for shrine in shrines:
        assert _batched(facts, shrine.pk) == _legacy(user, shrine.pk)
    assert _batched(facts, shrines[0].pk) == (
        {k: 0.0 for k in ("detail_view_signal", "route_open_signal", "save_signal", "visit_signal", "reflection_signal", "action_completed_signal", "total")},
        "none",
        None,
    )


def test_same_timestamp_records_count_and_latest_match(mixed):
    user, _other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[s[3].pk])
    f3 = facts[s[3].pk]
    assert (f3.route_open_count, f3.route_open_latest) == (2, fx.ago(20))
    assert (f3.detail_view_count, f3.detail_view_latest) == (1, fx.ago(20))
    assert _batched(facts, s[3].pk) == _legacy(user, s[3].pk)


def test_reflections_with_the_same_timestamp(users, shrines):
    """Signals are identical. The hint row is deterministic in the batch（highest id）; the per-shrine query's tie order
    is unspecified, so it must merely be one of the tied rows."""
    user, _other = users
    shrine = shrines[0]
    first = ShrineReflection.objects.create(user=user, shrine=shrine, answer="A", created_at=fx.ago(3))
    second = ShrineReflection.objects.create(user=user, shrine=shrine, answer="B", created_at=fx.ago(3))
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[shrine.pk])

    b_breakdown, b_state, b_hint = _batched(facts, shrine.pk)
    l_breakdown, l_state, l_hint = _legacy(user, shrine.pk)
    assert b_breakdown == l_breakdown
    assert b_state == l_state == "reflected"
    assert b_hint["source_reflection_id"] == max(first.id, second.id)
    assert l_hint["source_reflection_id"] in {first.id, second.id}
    assert {k: v for k, v in b_hint.items() if k != "source_reflection_id"}.keys() == l_hint.keys() - {"source_reflection_id"}


def test_favorites_and_visits_respect_status_and_latest(mixed):
    user, _other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[s[0].pk, s[1].pk, s[2].pk])
    assert facts[s[1].pk].favorite_latest == fx.ago(3)
    assert s[2].pk not in facts  # a removed visit only → no history at all
    assert ch.action_state_from_facts(facts.get(s[2].pk, ch.EMPTY_SHRINE_HISTORY_FACTS)) == "none"
    for sh in s[:3]:
        assert _batched(facts, sh.pk) == _legacy(user, sh.pk)


def test_reflection_hint_uses_the_latest_reflection(mixed):
    user, _other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[s[0].pk, s[4].pk])
    hint0 = ch.reflection_hint_from_facts(facts[s[0].pk])
    hint4 = ch.reflection_hint_from_facts(facts[s[4].pk])
    assert hint0 == ch.build_recent_reflection_hint(user=user, shrine_id=s[0].pk)
    assert hint0["created_at"] == fx.ago(5).isoformat()
    assert hint4["source_shrine_name"] == s[4].name_jp


def test_other_users_history_is_never_used(mixed):
    user, other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[x.pk for x in s])
    assert set(facts) == {s[i].pk for i in (0, 1, 3, 4, 5, 6)}
    other_facts = ch.load_shrine_history_facts(user=other, shrine_ids=[x.pk for x in s])
    for shrine in s:
        assert _batched(other_facts, shrine.pk) == _legacy(other, shrine.pk)


def test_ignores_non_integer_and_missing_ids(mixed):
    user, _other, s = mixed
    facts = ch.load_shrine_history_facts(user=user, shrine_ids=[None, True, s[0].pk, s[0].pk])
    assert set(facts) == {s[0].pk}


# --- anonymous ------------------------------------------------------------------------------------


@pytest.mark.parametrize("anon", [None, AnonymousUser()])
def test_anonymous_loads_nothing_and_enrichment_is_unchanged(mixed, anon):
    _user, _other, s = mixed
    with CaptureQueriesContext(connection) as ctx:
        assert ch.load_shrine_history_facts(user=anon, shrine_ids=[x.pk for x in s]) is None
    assert len(ctx.captured_queries) == 0

    with CaptureQueriesContext(connection) as ctx:
        batched = _enrich({"recommendations": fx.candidate_recs(s)}, anon, batch=True)
    assert len(ctx.captured_queries) == 0
    legacy = _enrich({"recommendations": fx.candidate_recs(s)}, anon, batch=False)
    assert batched == legacy


# --- end-to-end: scores, ranking, reasons ---------------------------------------------------------


def test_enrichment_scores_ranking_and_reasons_are_unchanged(mixed):
    user, _other, s = mixed
    batched = _enrich({"recommendations": fx.candidate_recs(s)}, user, batch=True)
    legacy = _enrich({"recommendations": fx.candidate_recs(s)}, user, batch=False)
    assert batched == legacy  # breakdown, breakdown_detail, _score_total, action_state, reflection_hint, reason

    ranked_b = _sort_chat_recommendations(batched, sort_tags=set(), need_tags=["career", "love"])
    ranked_l = _sort_chat_recommendations(legacy, sort_tags=set(), need_tags=["career", "love"])
    assert [r["shrine_id"] for r in ranked_b["recommendations"]] == [r["shrine_id"] for r in ranked_l["recommendations"]]
    assert [r["reason"] for r in ranked_b["recommendations"]] == [r["reason"] for r in ranked_l["recommendations"]]
    # the fixture must actually move scores, or this comparison proves nothing
    by_id = {r["shrine_id"]: r for r in batched["recommendations"]}
    assert by_id[s[0].pk]["action_state"] == "reflected"
    assert by_id[s[0].pk]["reflection_hint"] is not None


def test_candidate_without_shrine_id_keeps_the_legacy_path(mixed):
    """build_recent_reflection_hint(shrine_id=None) returns the user's latest reflection on any shrine; preserved."""
    user, _other, s = mixed
    recs = fx.candidate_recs(s[:3])
    recs.append({"name": "id のない候補", "astro_tags": [], "popular_score": 1})
    batched = _enrich({"recommendations": [dict(r) for r in recs]}, user, batch=True)
    legacy = _enrich({"recommendations": [dict(r) for r in recs]}, user, batch=False)
    assert batched == legacy


# --- query counts -----------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 5, 20])
def test_authenticated_query_count_is_bounded_and_independent_of_candidate_count(mixed, n):
    user, _other, s = mixed
    with CaptureQueriesContext(connection) as ctx:
        _enrich({"recommendations": fx.candidate_recs(s[:n])}, user, batch=True)
    assert len(ctx.captured_queries) <= MAX_BATCH_QUERIES


def test_legacy_per_shrine_path_scales_with_candidates(mixed):
    """Documents the pre-B-1 cost（the per-shrine path is still available with batch_history=False）."""
    user, _other, s = mixed
    with CaptureQueriesContext(connection) as ctx:
        _enrich({"recommendations": fx.candidate_recs(s)}, user, batch=False)
    assert len(ctx.captured_queries) > 200


def test_loader_issues_at_most_five_queries(mixed):
    user, _other, s = mixed
    with CaptureQueriesContext(connection) as ctx:
        ch.load_shrine_history_facts(user=user, shrine_ids=[x.pk for x in s])
    assert len(ctx.captured_queries) <= MAX_BATCH_QUERIES
