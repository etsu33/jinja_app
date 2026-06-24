

from types import SimpleNamespace

from temples.services.reflection_state_change import (
    build_next_history_theme_hint,
    build_next_need_hint,
    build_reflection_state_change,
    infer_state_change_direction,
)


def _reflection(
    *,
    answer: str = "",
    mood_before: str = "",
    mood_after: str = "",
    history_theme: str = "",
):
    return SimpleNamespace(
        answer=answer,
        mood_before=mood_before,
        mood_after=mood_after,
        history_theme=history_theme,
    )


def test_infer_state_change_direction_returns_improved():
    reflection = _reflection(
        mood_before="不安",
        mood_after="落ち着いた",
        answer="気持ちが整理できた。次は前に進む準備をしたい。",
    )

    assert infer_state_change_direction(reflection) == "improved"


def test_infer_state_change_direction_returns_unchanged_when_mood_is_same():
    reflection = _reflection(
        mood_before="不安",
        mood_after="不安",
        answer="まだ分からない。",
    )

    assert infer_state_change_direction(reflection) == "unchanged"


def test_infer_state_change_direction_returns_worsened():
    reflection = _reflection(
        mood_before="不安",
        mood_after="もっと不安",
        answer="決めきれない気持ちが残っている。",
    )

    assert infer_state_change_direction(reflection) == "worsened"


def test_infer_state_change_direction_returns_unknown_when_no_signal():
    reflection = _reflection(answer="神社に行った。")

    assert infer_state_change_direction(reflection) == "unknown"


def test_build_next_need_hint_extracts_need_tags_from_reflection_text():
    reflection = _reflection(
        answer="少し落ち着いたが、次は仕事の方向性を決めて前に進みたい。",
    )

    assert build_next_need_hint(reflection) == ["courage", "mental", "career"]


def test_build_next_history_theme_hint_moves_from_silence_to_challenge_when_improved():
    reflection = _reflection(
        history_theme="静寂",
        mood_before="不安",
        mood_after="落ち着いた",
        answer="気持ちが整理できたので、次は少し動きたい。",
    )

    assert build_next_history_theme_hint(reflection) == ["勝負", "再出発"]


def test_build_next_history_theme_hint_keeps_protection_when_guarding_is_still_needed():
    reflection = _reflection(
        history_theme="守り",
        mood_before="不安",
        mood_after="もっと不安",
        answer="まだ不安が強く、守りを固めたい。",
    )

    assert build_next_history_theme_hint(reflection) == ["守り", "静寂"]


def test_build_reflection_state_change_returns_integrated_result():
    reflection = _reflection(
        history_theme="勝負",
        mood_before="迷い",
        mood_after="落ち着いた",
        answer="仕事の方向性が整理できた。次は前に進む。",
    )

    result = build_reflection_state_change(reflection)

    assert result.state_change_direction == "improved"
    assert result.next_need_hint == ["courage", "mental", "career"]
    assert result.next_history_theme_hint == ["勝負", "再出発"]
    assert result.state_change_summary == "参拝後に状態が少し整った可能性があります。 次回推薦では、振り返り内容を補助情報として扱います。"
