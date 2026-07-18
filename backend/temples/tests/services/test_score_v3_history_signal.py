from __future__ import annotations

import pytest

from temples.services.concierge_chat_ranking import (
    HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS,
    SCORE_V3_HISTORY_THEME_BY_AXIS,
    resolve_history_theme_candidate_boost,
    resolve_score_v3_history_signal,
)


@pytest.mark.parametrize(
    ("consultation_axis", "history_theme", "expected"),
    [
        ("career_change", "勝負", 1.0),
        ("relationship_repair", "縁", 1.0),
        ("money_growth", "守り", 1.0),
        ("restart_mindset", "再出発", 1.0),
        ("nature_reset", "静寂", 1.0),
        ("rest_healing", "静寂", 1.0),
        ("study_success", "学び", 1.0),
        ("health", "復興", 0.9),
        ("protection", "守り", 1.0),
        ("travel_safe", "守り", 1.0),
    ],
)
def test_resolve_score_v3_history_signal_primary_mapping(
    consultation_axis: str, history_theme: str, expected: float
) -> None:
    assert (
        resolve_score_v3_history_signal(
            consultation_axis=consultation_axis,
            history_theme=history_theme,
        )
        == expected
    )


def test_resolve_score_v3_history_signal_undefined_axis_returns_zero() -> None:
    assert (
        resolve_score_v3_history_signal(
            consultation_axis="undefined_axis",
            history_theme="静寂",
        )
        == 0.0
    )


def test_resolve_score_v3_history_signal_undefined_theme_returns_zero() -> None:
    assert (
        resolve_score_v3_history_signal(
            consultation_axis="rest_healing",
            history_theme="未定義テーマ",
        )
        == 0.0
    )


def test_resolve_score_v3_history_signal_other_axis_not_mapped() -> None:
    assert (
        resolve_score_v3_history_signal(
            consultation_axis="other",
            history_theme="静寂",
        )
        == 0.0
    )


@pytest.mark.parametrize(
    ("consultation_axis", "history_theme", "expected"),
    [
        ("career_change", "勝負", 1.0),
        ("relationship_repair", "縁", 1.0),
        ("money_growth", "守り", 1.0),
        ("restart_mindset", "再出発", 1.0),
        ("nature_reset", "静寂", 1.0),
        ("rest_healing", "静寂", 1.0),
        ("study_success", "学び", 1.0),
        ("health", "復興", 0.9),
        ("protection", "守り", 1.0),
        ("travel_safe", "守り", 1.0),
    ],
)
def test_resolve_history_theme_candidate_boost_matches_main_mapping(
    consultation_axis: str, history_theme: str, expected: float
) -> None:
    assert (
        resolve_history_theme_candidate_boost(
            consultation_axis=consultation_axis,
            history_theme=history_theme,
        )
        == expected
    )


def test_candidate_boost_mapping_derived_from_main_mapping() -> None:
    assert HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS == SCORE_V3_HISTORY_THEME_BY_AXIS
