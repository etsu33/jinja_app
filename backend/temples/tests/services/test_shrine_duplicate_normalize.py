from __future__ import annotations

import pytest

from temples.services.shrine_duplicate_normalize import (
    normalize_shrine_address_for_duplicate,
    normalize_shrine_name_for_duplicate,
    shrine_name_duplicate_base_key,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  foo  ", "foo"),
        ("あ\u3000い", "あ い"),
        ("神田　神社", "神田 神社"),
        ("a   b\t c", "a b c"),
        ("神田神社（神田明神）", "神田神社(神田明神)"),
        ("（先頭）名称", "(先頭)名称"),
    ],
)
def test_normalize_shrine_name_for_duplicate(raw: str, expected: str):
    assert normalize_shrine_name_for_duplicate(raw) == expected


@pytest.mark.parametrize(
    ("normalized", "expected_base"),
    [
        ("神田神社(神田明神)", "神田神社"),
        ("複合(別名) テスト", "複合 テスト"),
        ("括弧なし", "括弧なし"),
    ],
)
def test_shrine_name_duplicate_base_key(normalized: str, expected_base: str):
    assert shrine_name_duplicate_base_key(normalized) == expected_base


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  ", ""),
        ("東京都 千代田区", "東京都千代田区"),
        ("大阪府\u3000北区1−1", "大阪府北区1-1"),
        ("京都府京都市−左京区", "京都府京都市-左京区"),
    ],
)
def test_normalize_shrine_address_for_duplicate(raw: str, expected: str):
    assert normalize_shrine_address_for_duplicate(raw) == expected
