# -*- coding: utf-8 -*-
"""相談の語と神社の語の重なり（temples/services/shrine_features_en.py）のテスト。"""

from datetime import date

import pytest

from temples.models import Shrine, ShrineFeatureWordEn
from temples.services.shrine_features_en import build_shrine_feature_matches


def _shrine_with(name_jp, word_ids):
    shrine = Shrine.objects.create(name_jp=name_jp, kind="shrine", address=f"{name_jp}の住所")
    for i, word_id in enumerate(word_ids):
        ShrineFeatureWordEn.objects.create(
            shrine=shrine,
            word_id=word_id,
            vocabulary_version="2026-11-12",
            evidence_quote=f"根拠{i}",
            source_url="https://example.com/",
            source_type="神社公式",
            checked_on=date(2026, 11, 12),
        )
    return shrine


@pytest.mark.django_db
def test_overlap_for_covered_shrines_and_uncovered_ones():
    forest = _shrine_with("杜の神社", ["S_FOREST", "F_URBAN_OASIS"])
    mountain = _shrine_with("山の神社", ["S_MOUNTAIN", "S_VIEW", "F_HIKE"])
    other = _shrine_with("語の無い神社", [])

    result = build_shrine_feature_matches(
        [{"shrine_id": forest.pk}, {"shrine_id": mountain.pk}, {"shrine_id": other.pk}],
        ["S_FOREST", "F_HIKE", "S_VIEW"],
    )

    forest_row, mountain_row, other_row = result["matches"]
    assert forest_row["covered"] is True
    assert forest_row["overlap_ids"] == ["S_FOREST"]
    assert mountain_row["overlap_ids"] == ["F_HIKE", "S_VIEW"]
    assert mountain_row["overlap_count"] == 2
    assert other_row == {"shrine_id": other.pk, "covered": False}
    assert result["version"] == "2026-11-12"


@pytest.mark.django_db
def test_two_evidence_rows_for_one_word_count_once():
    shrine = _shrine_with("彫刻の神社", ["C_CARVINGS", "C_CARVINGS"])
    result = build_shrine_feature_matches([{"shrine_id": shrine.pk}], ["C_CARVINGS"])
    assert result["matches"][0]["shrine_feature_ids"] == ["C_CARVINGS"]
    assert result["matches"][0]["overlap_count"] == 1


@pytest.mark.django_db
def test_falls_back_to_id_and_skips_bad_items():
    shrine = _shrine_with("杜の神社", ["S_FOREST"])
    result = build_shrine_feature_matches(
        [{"id": shrine.pk}, "not-a-dict", {"shrine_id": "abc"}],
        [],
    )
    assert result["matches"][0]["covered"] is True
    assert result["matches"][0]["overlap_ids"] == []
    assert result["matches"][1] == {"shrine_id": None, "covered": False}
    assert len(result["matches"]) == 2


@pytest.mark.django_db
def test_no_recommendations_makes_no_query(django_assert_num_queries):
    with django_assert_num_queries(0):
        result = build_shrine_feature_matches([], ["S_FOREST"])
    assert result == {"version": "", "matches": []}


@pytest.mark.django_db
def test_one_query_for_many_shrines(django_assert_num_queries):
    shrines = [_shrine_with(f"神社{i}", ["S_FOREST"]) for i in range(5)]
    with django_assert_num_queries(1):
        build_shrine_feature_matches([{"shrine_id": s.pk} for s in shrines], ["S_FOREST"])
