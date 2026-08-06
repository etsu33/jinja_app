# -*- coding: utf-8 -*-
import pytest

from temples.models import Shrine
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines


def _shrine(name: str) -> Shrine:
    return Shrine.objects.create(name_jp=name, address="東京都千代田区", popular_score=0.0)


@pytest.mark.django_db
def test_excludes_known_qa_fixture_naming_patterns():
    _shrine("実在神社")
    _shrine("承認テスト神社")
    _shrine("admin承認テスト神社")
    _shrine("重複検証神社")
    _shrine("重複検証神社（別宮）")
    _shrine("テスト神社")
    _shrine("test神社")

    remaining = list(
        exclude_qa_fixture_shrines(Shrine.objects.exclude(pk=1)).values_list("name_jp", flat=True)
    )

    assert remaining == ["実在神社"]


@pytest.mark.django_db
def test_does_not_over_exclude_mid_name_test_substring():
    _shrine("距離テスト神社")
    _shrine("place_idテスト神社")

    remaining = set(
        exclude_qa_fixture_shrines(Shrine.objects.exclude(pk=1)).values_list("name_jp", flat=True)
    )

    assert "距離テスト神社" in remaining
    assert "place_idテスト神社" in remaining
