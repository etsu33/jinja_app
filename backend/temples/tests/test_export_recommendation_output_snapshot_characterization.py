"""export_recommendation_output_snapshot の現行挙動を固定する（F-5A §7.4）。

F-5A は当該 command に専用 test が 1 件も存在しないことを記録した
（UNPROTECTED_SITES = 5 のうち 1 件）。F-5B で共有 resolver へ集約する前に、
**現在の well-formed な出力**を固定する。

malformed legacy 挙動は F-5A §3 の matrix が記録済みであり、ここでは
望ましい挙動として凍結しない。
"""
from __future__ import annotations

from temples.management.commands.export_recommendation_output_snapshot import (
    _format_recommendation,
)


def _shrine_id_line(rec: dict) -> str:
    lines = _format_recommendation(rec, rank=1)
    matched = [line for line in lines if line.startswith("- shrine_id:")]
    assert len(matched) == 1, lines[:5]
    return matched[0]


class TestFormatRecommendationShrineId:
    def test_shrine_id_is_rendered(self):
        assert _shrine_id_line({"shrine_id": 42, "name": "A神社"}) == "- shrine_id: `42`"

    def test_id_only_positive_integer_remains_compatibility_readable(self):
        assert _shrine_id_line({"id": 42, "name": "A神社"}) == "- shrine_id: `42`"

    def test_shrine_id_wins_over_generic_id(self):
        assert _shrine_id_line({"shrine_id": 42, "id": 999, "name": "A神社"}) == "- shrine_id: `42`"

    def test_missing_identity_renders_the_existing_dash(self):
        assert _shrine_id_line({"name": "A神社"}) == "- shrine_id: `-`"

    def test_none_identity_renders_the_existing_dash(self):
        assert _shrine_id_line({"shrine_id": None, "id": None, "name": "A神社"}) == "- shrine_id: `-`"

    def test_string_shrine_id_is_rendered_as_given(self):
        assert _shrine_id_line({"shrine_id": "42", "name": "A神社"}) == "- shrine_id: `42`"


class TestFormatRecommendationSurroundingOutput:
    def test_heading_and_other_lines_are_unchanged(self):
        lines = _format_recommendation(
            {
                "shrine_id": 42,
                "display_name": "A神社",
                "history_theme": "再出発",
                "reason_source": "knowledge",
                "action_state": "none",
            },
            rank=3,
        )

        assert lines[0] == "#### 3. A神社"
        assert "- history_theme: `再出発`" in lines
        assert "- reason_source: `knowledge`" in lines
        assert "- action_state: `none`" in lines

    def test_empty_recommendation_does_not_raise(self):
        lines = _format_recommendation({}, rank=1)

        assert lines[0] == "#### 1. -"
        assert "- shrine_id: `-`" in lines
