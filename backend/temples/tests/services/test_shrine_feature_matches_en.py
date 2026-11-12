# -*- coding: utf-8 -*-
"""英語の相談の語と神社の語の重なり（temples/services/shrine_features_en.py）のテスト。"""

import pytest

from temples.models import Shrine
from temples.services.shrine_features_en import build_shrine_feature_matches


def _create(name_jp, address):
    return Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)


@pytest.mark.django_db
def test_overlap_for_covered_shrines_and_uncovered_ones():
    hie = _create("日枝神社", "東京都千代田区永田町2-10-5")
    mitake = _create("武蔵御嶽神社", "東京都青梅市御岳山176")
    other = _create("どこかの神社", "どこかの住所")

    result = build_shrine_feature_matches(
        [{"shrine_id": hie.pk}, {"shrine_id": mitake.pk}, {"shrine_id": other.pk}],
        ["S_FOREST", "F_HIKE", "S_VIEW"],
    )

    hie_row, mitake_row, other_row = result["matches"]
    assert hie_row["covered"] is True
    assert hie_row["name_jp"] == "日枝神社"
    assert hie_row["overlap_ids"] == ["S_FOREST"]
    assert mitake_row["overlap_ids"] == ["F_HIKE", "S_VIEW"]
    assert mitake_row["overlap_count"] == 2
    assert other_row == {"shrine_id": other.pk, "covered": False}

    # 作っていない8社は結びつけられず、名前が残る
    assert len(result["unresolved"]) == 8
    assert "日枝神社" not in result["unresolved"]


@pytest.mark.django_db
def test_same_name_at_another_address_is_not_used():
    # 名前が同じでも住所が違えば結びつけない（推測しない）
    wrong = _create("日枝神社", "別の住所")
    result = build_shrine_feature_matches([{"shrine_id": wrong.pk}], ["S_FOREST"])
    assert result["matches"] == [{"shrine_id": wrong.pk, "covered": False}]
    assert "日枝神社" in result["unresolved"]


@pytest.mark.django_db
def test_falls_back_to_id_and_skips_bad_items():
    hie = _create("日枝神社", "東京都千代田区永田町2-10-5")
    result = build_shrine_feature_matches(
        [{"id": hie.pk}, "not-a-dict", {"shrine_id": "abc"}],
        [],
    )
    assert result["matches"][0]["covered"] is True
    assert result["matches"][0]["overlap_ids"] == []
    assert result["matches"][1] == {"shrine_id": None, "covered": False}
