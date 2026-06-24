from __future__ import annotations

import pytest

from temples.models import ActionEvent, Shrine, ShrineReflection
from temples.services.action_completion_observation import build_action_completion_observation


@pytest.fixture
def shrine():
    return Shrine.objects.create(
        name_jp="行動完了観測神社",
        address="東京都千代田区",
    )


def _create_action_event(
    *,
    user,
    shrine=None,
    action_type: str,
    action_suggestion_id: str = "challenge_choose_this_week",
    history_theme: str = "勝負",
    action_category: str = "prepare",
) -> ActionEvent:
    return ActionEvent.objects.create(
        user=user,
        shrine=shrine,
        action_type=action_type,
        action_suggestion_id=action_suggestion_id,
        history_theme=history_theme,
        action_category=action_category,
        source="concierge_result",
        metadata={"screen": "result"},
    )


@pytest.mark.django_db
def test_build_action_completion_observation_counts_started_and_completed(user, shrine):
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_STARTED,
    )
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_COMPLETED,
    )

    observation = build_action_completion_observation(user=user)

    assert observation["action_started_count"] == 1
    assert observation["action_completed_count"] == 1
    assert observation["started_to_completed_rate"] == 1.0


@pytest.mark.django_db
def test_build_action_completion_observation_groups_completion_by_history_theme(user, shrine):
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_STARTED,
        history_theme="勝負",
    )
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_COMPLETED,
        history_theme="勝負",
    )
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_STARTED,
        history_theme="静寂",
    )

    observation = build_action_completion_observation(user=user)
    by_theme = {row["history_theme"]: row for row in observation["history_theme_completion"]}

    assert by_theme["勝負"] == {
        "history_theme": "勝負",
        "action_started_count": 1,
        "action_completed_count": 1,
        "completion_rate": 1.0,
    }
    assert by_theme["静寂"] == {
        "history_theme": "静寂",
        "action_started_count": 1,
        "action_completed_count": 0,
        "completion_rate": 0.0,
    }


@pytest.mark.django_db
def test_build_action_completion_observation_matches_completed_action_and_reflection_by_user_and_shrine(user, shrine):
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_COMPLETED,
        history_theme="勝負",
    )
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="勝負",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="少し落ち着いたので、次に動きたい。",
        mood_before="不安",
        mood_after="落ち着いた",
    )

    observation = build_action_completion_observation(user=user)

    assert observation["completed_pair_count"] == 1
    assert observation["completed_with_reflection_count"] == 1
    assert observation["completed_to_reflection_rate"] == 1.0


@pytest.mark.django_db
def test_build_action_completion_observation_filters_by_shrine(user, shrine):
    other_shrine = Shrine.objects.create(
        name_jp="別の神社",
        address="東京都港区",
    )
    _create_action_event(
        user=user,
        shrine=shrine,
        action_type=ActionEvent.ActionType.ACTION_STARTED,
    )
    _create_action_event(
        user=user,
        shrine=other_shrine,
        action_type=ActionEvent.ActionType.ACTION_STARTED,
    )

    observation = build_action_completion_observation(user=user, shrine_id=shrine.id)

    assert observation["action_started_count"] == 1
    assert observation["action_completed_count"] == 0
    assert observation["started_to_completed_rate"] == 0.0


@pytest.mark.django_db
def test_build_action_completion_observation_marks_view_to_started_as_unavailable(user):
    observation = build_action_completion_observation(user=user)

    assert observation["view_to_started_rate"] is None
    assert observation["view_to_started_rate_reason"] == "action_suggestion_view is not persisted in backend DB."
