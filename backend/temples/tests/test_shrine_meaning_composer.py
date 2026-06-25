import pytest

from temples.services.shrine_meaning_composer import (
    _build_direction_support_copy,
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


def test_normalize_shrine_meaning_source_reads_direction_fields():
    normalized = normalize_shrine_meaning_source(
        {
            "id": 10,
            "name_jp": "方位補助神社",
            "direction_bonus": "0.2",
            "direction_reason": "東の方位が補助的に合う",
        }
    )

    assert normalized.direction_bonus == 0.2
    assert normalized.direction_reason == "東の方位が補助的に合う"


def test_direction_support_copy_is_none_without_bonus_or_reason():
    no_bonus = normalize_shrine_meaning_source(
        {
            "id": 11,
            "name_jp": "方位なし神社",
            "direction_reason": "東の方位が補助的に合う",
        }
    )
    no_reason = normalize_shrine_meaning_source(
        {
            "id": 12,
            "name_jp": "理由なし神社",
            "direction_bonus": 0.2,
        }
    )

    assert _build_direction_support_copy(no_bonus) is None
    assert _build_direction_support_copy(no_reason) is None


def test_compose_shrine_meaning_payload_adds_direction_support_copy_without_changing_main_copy():
    payload = compose_shrine_meaning_payload(
        {
            "id": 13,
            "name_jp": "補助確認神社",
            "history_theme": "導き",
            "direction_bonus": 0.2,
            "direction_reason": "東の方位が補助的に合う",
        }
    )

    assert payload["source"]["directionBonus"] == 0.2
    assert payload["source"]["directionReason"] == "東の方位が補助的に合う"
    assert payload["generated"]["directionSupportCopy"] == "方位は主理由ではなく、補助要素として「東の方位が補助的に合う」を参考にしています。"

    direction_reason = "東の方位が補助的に合う"
    assert direction_reason not in payload["generated"]["heroMeaningCopy"]
    assert direction_reason not in payload["generated"]["shrineMeaning"]
    assert direction_reason not in payload["generated"]["actionMeaning"]

    block_ids = [block["id"] for block in payload["display"]["blocks"]]
    assert "direction_support" not in block_ids


def test_meaning_layer_keeps_consultation_summary_as_display_copy_only():
    payload = compose_shrine_meaning_payload(
        {
            "id": 101,
            "name_jp": "整理神社",
            "history_theme": "再出発",
            "goriyaku": "開運",
            "description": "気持ちを切り替える節目に参拝される神社。",
        }
    )

    summary = payload["generated"]["consultationSummary"]

    assert summary
    assert "整理神社" not in summary
    assert "参拝前" not in summary
    assert "参拝中" not in summary
    assert payload["source"]["historyTheme"] == "再出発"


def test_meaning_layer_keeps_history_theme_in_source_and_uses_it_for_meaning_copy():
    payload = compose_shrine_meaning_payload(
        {
            "id": 102,
            "name_jp": "勝負神社",
            "history_theme": "勝負",
            "goriyaku": "仕事運",
        }
    )

    generated = payload["generated"]

    assert payload["source"]["historyTheme"] == "勝負"
    assert "勝負神社" in generated["shrineMeaning"]
    assert "決断や挑戦" in generated["shrineMeaning"]
    assert "急いで叶えるためではなく" in generated["actionMeaning"]


def test_meaning_layer_action_meaning_uses_history_theme_action_context():
    payload = compose_shrine_meaning_payload(
        {
            "id": 103,
            "name_jp": "静寂神社",
            "history_theme": "静寂",
        }
    )

    action_meaning = payload["generated"]["actionMeaning"]

    assert action_meaning
    assert "参拝中" in action_meaning
    assert "意識します" in action_meaning
    assert "結果" not in action_meaning


def test_meaning_layer_action_meaning_prefers_translation_result_action_context():
    payload = compose_shrine_meaning_payload(
        {
            "id": 104,
            "name_jp": "行動神社",
            "history_theme": "静寂",
            "translation_result": {
                "action_context": "実際に足を運び、今の状態を確認する",
            },
        }
    )

    action_meaning = payload["generated"]["actionMeaning"]

    assert payload["source"]["translationResult"]["action_context"] == "実際に足を運び、今の状態を確認する"
    assert "実際に足を運び、今の状態を確認する" in action_meaning
    assert "判断を急がず" not in action_meaning


def test_meaning_layer_basic_info_only_does_not_invent_strong_meaning():
    payload = compose_shrine_meaning_payload(
        {
            "id": 105,
            "name_jp": "基本情報神社",
            "address": "東京都千代田区",
        }
    )

    generated = payload["generated"]

    assert "確認済みの基本情報" in generated["heroMeaningCopy"]
    assert "相談内容との強い結びつきは断定せず" in generated["consultationSummary"]
    assert "断定的な説明を行いません" in generated["shrineMeaning"]
    assert "意味やご利益を決めつけず" in generated["actionMeaning"]
