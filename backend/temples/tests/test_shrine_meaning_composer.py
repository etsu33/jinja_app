import pytest

from temples.services.shrine_meaning_composer import (
    compose_shrine_meaning_payload,
    normalize_shrine_meaning_source,
)


def test_compose_shrine_meaning_payload_from_dict_returns_v2_shape():
    payload = compose_shrine_meaning_payload(
        {
            "id": 1,
            "name_jp": "例の神社",
            "address": "東京都世田谷区",
            "latitude": "35.0",
            "longitude": "139.0",
            "goriyaku": "厄除け / 縁結び",
            "goriyaku_tags": [{"name": "厄除け"}, {"name": "縁結び"}],
            "sajin": "例の祭神",
            "description": "静かに心を整えやすい神社。",
            "history_theme": "再出発",
            "element": "木",
            "place_tags": ["静寂", "節目"],
        }
    )

    assert payload["version"] == "v2"
    assert payload["source"]["shrineId"] == 1
    assert payload["source"]["nameJp"] == "例の神社"
    assert payload["source"]["latitude"] == 35.0
    assert payload["source"]["longitude"] == 139.0
    assert payload["source"]["goriyakuTags"] == ["厄除け", "縁結び"]
    assert payload["source"]["historyTheme"] == "再出発"

    generated = payload["generated"]
    assert generated["heroMeaningCopy"]
    assert generated["consultationSummary"]
    assert generated["shrineMeaning"]
    assert generated["actionMeaning"]
    assert generated["historyContext"]
    assert generated["deitySymbolContext"]
    assert generated["benefitActionContext"]

    blocks = payload["display"]["blocks"]
    assert blocks
    assert payload["display"]["fallbackMessage"] is None


def test_normalize_shrine_meaning_source_requires_shrine_id():
    with pytest.raises(ValueError, match="shrine_id is required"):
        normalize_shrine_meaning_source({"name_jp": "例の神社"})


def test_normalize_shrine_meaning_source_requires_name_jp():
    with pytest.raises(ValueError, match="name_jp is required"):
        normalize_shrine_meaning_source({"id": 1})


def test_compose_shrine_meaning_payload_display_blocks_include_access_levels():
    payload = compose_shrine_meaning_payload(
        {
            "id": 2,
            "name_jp": "節目神社",
            "goriyaku": "仕事運",
            "history_theme": "勝負",
            "sajin": "例の祭神",
        }
    )

    access_levels = {block["access"] for block in payload["display"]["blocks"]}

    assert "anonymous" in access_levels
    assert "free" in access_levels
    assert "premium" in access_levels


@pytest.mark.parametrize(
    ("shrine_id", "name_jp", "history_theme", "expected_hero", "expected_shrine", "expected_action"),
    [
        (
            17,
            "三峯神社",
            "勝負",
            "前に進む覚悟を固めたい時",
            "狼は単なる象徴ではなく",
            "今いちばん決めきれていないことを一つだけ書き出します",
        ),
        (
            14,
            "鹿島神宮",
            "勝負",
            "流れを変える一歩を踏み出したい時",
            "武神・剣神として信仰される武甕槌大神",
            "今止まっている理由を一つだけ言葉にします",
        ),
        (
            4,
            "出雲大社",
            "縁",
            "人や機会とのつながりを見直したい時",
            "縁結びの信仰で知られ",
            "今大切にしたい関係を一つだけ思い浮かべます",
        ),
    ],
)
def test_compose_shrine_meaning_payload_keeps_story_overrides(
    shrine_id,
    name_jp,
    history_theme,
    expected_hero,
    expected_shrine,
    expected_action,
):
    payload = compose_shrine_meaning_payload(
        {
            "id": shrine_id,
            "name_jp": name_jp,
            "history_theme": history_theme,
            "goriyaku": "開運",
        }
    )

    generated = payload["generated"]

    assert expected_hero in generated["heroMeaningCopy"]
    assert expected_shrine in generated["shrineMeaning"]
    assert expected_action in generated["actionMeaning"]


def test_normalize_shrine_meaning_source_splits_string_lists_and_dedupes():
    normalized = normalize_shrine_meaning_source(
        {
            "id": "3",
            "name": "文字列神社",
            "goriyaku": "厄除け/縁結び、厄除け",
            "placeTags": "静寂/節目/静寂",
        }
    )

    assert normalized.shrine_id == 3
    assert normalized.name_jp == "文字列神社"
    assert normalized.place_tags == ("静寂", "節目")
