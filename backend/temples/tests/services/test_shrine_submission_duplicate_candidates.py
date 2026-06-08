from __future__ import annotations

import pytest

from temples.models import Shrine

from temples.services.shrine_submission import find_duplicate_candidates


pytestmark = pytest.mark.django_db


def test_find_duplicate_candidates_parenthesis_form_variant():
    Shrine.objects.create(
        name_jp="神田神社（神田明神）",
        address="東京都千代田区神田2-16-2",
        latitude=35.7023,
        longitude=139.7745,
        owner=None,
    )

    hits = find_duplicate_candidates(
        name="神田神社(神田明神)",
        address="東京都 千代田区 神田 2-16-2",
        limit=5,
    )

    assert len(hits) >= 1
    assert hits[0].name == "神田神社（神田明神）"




def test_find_duplicate_candidates_address_only_match_is_not_returned():
    Shrine.objects.create(
        name_jp="住所テスト神社",
        address="東京都千代田区1-1-1",
        latitude=35.6940,
        longitude=139.7540,
        owner=None,
    )

    hits = find_duplicate_candidates(
        name="無関係でも住所が一致すれば候補",
        address="東京都　千代田区  1−1−1",
        limit=5,
    )

    assert hits == []


def test_find_duplicate_candidates_base_key_match_is_returned():
    Shrine.objects.create(
        name_jp="神田神社（神田明神）",
        address="東京都千代田区外神田2-16-2",
        latitude=35.7023,
        longitude=139.7745,
        owner=None,
    )

    hits = find_duplicate_candidates(
        name="神田神社",
        address="東京都千代田区別住所1-2-3",
        limit=5,
    )

    assert len(hits) >= 1
    assert hits[0].name == "神田神社（神田明神）"


def test_find_duplicate_candidates_address_match_affects_order_only():
    Shrine.objects.create(
        name_jp="神田神社（神田明神）",
        address="東京都千代田区神田2-16-2",
        latitude=35.7023,
        longitude=139.7745,
        owner=None,
    )
    Shrine.objects.create(
        name_jp="神田神社別院",
        address="大阪府大阪市中央区1-2-3",
        latitude=34.6937,
        longitude=135.5023,
        owner=None,
    )

    hits = find_duplicate_candidates(
        name="神田神社",
        address="東京都 千代田区 神田 2-16-2",
        limit=5,
    )

    assert len(hits) >= 2
    assert hits[0].name == "神田神社（神田明神）"
    assert hits[1].name == "神田神社別院"
