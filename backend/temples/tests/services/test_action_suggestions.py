from temples.services.action_suggestions import (
    HISTORY_THEME_ACTION_SUGGESTIONS,
    get_action_suggestions_for_theme,
    normalize_history_theme,
)


def test_get_action_suggestions_for_each_history_theme():
    for history_theme in HISTORY_THEME_ACTION_SUGGESTIONS:
        suggestions = get_action_suggestions_for_theme(history_theme)

        assert suggestions
        assert suggestions[0]["history_theme"] == history_theme
        assert suggestions[0]["id"]
        assert suggestions[0]["title"]
        assert suggestions[0]["category"]
        assert suggestions[0]["measurement_key"]


def test_get_action_suggestions_for_unknown_theme_falls_back_to_default():
    suggestions = get_action_suggestions_for_theme("未知のテーマ")

    assert suggestions
    assert suggestions[0]["history_theme"] == "静寂"


def test_normalize_history_theme_returns_default_for_blank_value():
    assert normalize_history_theme("") == "静寂"
    assert normalize_history_theme(None) == "静寂"


def test_get_action_suggestions_respects_limit():
    suggestions = get_action_suggestions_for_theme("勝負", limit=1)

    assert len(suggestions) == 1
    assert suggestions[0]["history_theme"] == "勝負"


def test_get_action_suggestions_returns_empty_when_limit_is_zero():
    assert get_action_suggestions_for_theme("勝負", limit=0) == []


def test_action_suggestions_do_not_include_after_visit_or_record():
    for history_theme in HISTORY_THEME_ACTION_SUGGESTIONS:
        suggestions = get_action_suggestions_for_theme(history_theme)

        for suggestion in suggestions:
            assert suggestion["timing"] != "after_visit"
            assert suggestion["category"] != "record"
