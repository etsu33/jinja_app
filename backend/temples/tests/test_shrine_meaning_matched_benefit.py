"""意味の窓口で、相談と一致したご利益の名前(引数 benefits)を「使うご利益」にする契約。

- 引数があるとき: 神社が実際に持っているご利益(タグの名前、またはご利益の文字列を区切った1つ)に
  入る名前の最初の1つを、4つの欄(この場所が合う理由・ここで試したいこと・ご利益の受け取り方・
  今のあなたとの接点)すべてで使う。使える名前が無ければ「ご利益なし」で、タグの先頭には戻らない。
- 引数が無いとき: 今までとまったく同じ。
- 文化の訳・個別の物語・歴史のテーマ・説明文が先に使われる順は変えない。
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from temples.models import GoriyakuTag, Shrine
from temples.services.shrine_meaning_composer import (
    SHRINE_HISTORY_STORY_OVERRIDES,
    compose_shrine_meaning_payload,
)
from temples.services.shrine_culture_translation import SHRINE_CULTURE_TRANSLATIONS

# 個別の物語・文化の訳が無い番号。
PLAIN_SHRINE_ID = 990001
assert PLAIN_SHRINE_ID not in SHRINE_HISTORY_STORY_OVERRIDES
assert PLAIN_SHRINE_ID not in SHRINE_CULTURE_TRANSLATIONS

# 4つの欄(generated の名前)
FOUR_FIELDS = ("shrineMeaning", "actionMeaning", "benefitActionContext", "heroMeaningCopy")
# 名前を文に入れる3つの欄
NAMED_FIELDS = ("shrineMeaning", "actionMeaning", "benefitActionContext")


def _source(**overrides):
    source = {
        "id": PLAIN_SHRINE_ID,
        "name_jp": "例の宮",
        "goriyaku": "勝運・厄除け・家内安全",
        "goriyaku_tags": ["勝運", "厄除け・方除け"],
        "sajin": "例の祭神",
    }
    source.update(overrides)
    return source


def _generated(source, matched_benefit_names=None):
    if matched_benefit_names is None:
        return compose_shrine_meaning_payload(source)["generated"]
    return compose_shrine_meaning_payload(source, matched_benefit_names=matched_benefit_names)["generated"]


# --- 引数が無いとき -------------------------------------------------------------


def test_without_names_the_payload_is_exactly_the_same_as_before():
    source = _source()

    assert compose_shrine_meaning_payload(source) == compose_shrine_meaning_payload(
        source, matched_benefit_names=None
    )
    generated = _generated(source)
    # 今までどおり、タグの先頭(勝運)を使う。
    assert generated["shrineMeaning"] == (
        "例の宮は「勝運」に関わる神社として確認できます。現時点では、願いごとの方向性を整理するための候補として扱います。"
    )
    assert "勝運" in generated["actionMeaning"]
    assert "「勝運」" in generated["benefitActionContext"]
    assert generated["heroMeaningCopy"] == "例の宮は、願いごとを手がかりに候補として確認しやすい神社です。"


# --- 一致したご利益を使う ---------------------------------------------------------


@pytest.mark.parametrize(
    "names,expected",
    [
        # ご利益の文字列を区切った1つ
        (["厄除け"], "厄除け"),
        # タグの名前
        (["厄除け・方除け"], "厄除け・方除け"),
        # 持っていない名前は飛ばし、持っている最初の1つ
        (["縁結び", "家内安全", "厄除け"], "家内安全"),
    ],
)
def test_the_first_owned_name_is_used_with_the_same_wording(names, expected):
    generated = _generated(_source(), names)

    assert generated["shrineMeaning"] == (
        f"例の宮は「{expected}」に関わる神社として確認できます。現時点では、願いごとの方向性を整理するための候補として扱います。"
    )


def test_the_same_matched_name_is_used_in_all_four_fields():
    generated = _generated(_source(), ["縁結び", "家内安全", "厄除け"])

    # 名前を入れる3つの欄は、どれも同じ「家内安全」を使い、ほかのご利益の名前を入れない。
    assert generated["shrineMeaning"].startswith("例の宮は「家内安全」に関わる神社")
    assert generated["actionMeaning"] == (
        "参拝前に、家内安全という願いの中で今いちばん整理したいことを一つだけ確認します。"
        "結果を急がず、参拝先を選ぶ前の小さな整理として扱います。"
    )
    assert generated["benefitActionContext"].startswith("「家内安全」は結果を急ぐためではなく、")
    for field in NAMED_FIELDS:
        for other in ("勝運", "厄除け"):
            assert other not in generated[field], (field, other)
    # 今のあなたとの接点は、ご利益がある扱い(名前は入れない)。
    assert generated["heroMeaningCopy"] == "例の宮は、願いごとを手がかりに候補として確認しやすい神社です。"


def test_the_same_matched_name_is_used_when_the_history_theme_drives_the_action():
    # 歴史のテーマがあるとき、この場所が合う理由は歴史のテーマが先(変えない)。
    # ここで試したいこと・ご利益の受け取り方は、同じ一致したご利益を使う。
    generated = _generated(_source(history_theme="再出発"), ["厄除け"])
    without = _generated(_source(history_theme="再出発"))

    assert generated["shrineMeaning"] == without["shrineMeaning"]
    assert generated["actionMeaning"].startswith("参拝を、厄除けという願いを急いで叶えるためではなく、")
    assert generated["benefitActionContext"].startswith("「厄除け」は結果を急ぐためではなく、")
    for field in FOUR_FIELDS:
        assert "勝運" not in generated[field], field


# --- ご利益の受け取り方のテーマ ---------------------------------------------------

WINNING_THEMES = ("決断", "主導権", "停滞打破", "勝負前の整理")


def test_benefit_action_uses_only_the_themes_of_the_matched_benefit():
    generated = _generated(_source(), ["厄除け"])

    # 厄除けのテーマ(BENEFIT_STATE_THEME_MAP の先頭から3つ)を使う。
    assert generated["benefitActionContext"] == (
        "「厄除け」は結果を急ぐためではなく、不安整理・境界線・守りを見直すための手がかりとして扱います。"
    )
    for theme in WINNING_THEMES:
        assert theme not in generated["benefitActionContext"], theme


def test_benefit_action_without_registered_themes_moves_to_the_next_form():
    # タグの名前「厄除け・方除け」にはテーマの登録が無い。勝運のテーマには戻らず、次の文の形へ進む。
    generated = _generated(_source(), ["厄除け・方除け"])

    assert generated["benefitActionContext"] == (
        "「厄除け・方除け」は願望成就の断定ではなく、今の行動テーマを整える補助軸として扱います。"
    )
    for theme in WINNING_THEMES:
        assert theme not in generated["benefitActionContext"], theme


def test_benefit_action_themes_are_unchanged_without_names():
    assert _generated(_source())["benefitActionContext"] == (
        "「勝運」は結果を急ぐためではなく、決断・主導権・停滞打破を見直すための手がかりとして扱います。"
    )


# --- 使える名前が無いとき ---------------------------------------------------------


@pytest.mark.parametrize("names", [[], ["縁結び"], ["勝"], ["  "], ["勝運・厄除け"]])
def test_no_usable_name_means_no_benefit_and_never_falls_back_to_the_first_tag(names):
    generated = _generated(_source(), names)

    for field in FOUR_FIELDS:
        value = generated[field] or ""
        assert "勝運" not in value, (field, value)
    # それぞれの欄の今の決まりどおり、次の材料へ進むか、欄を出さない。
    assert generated["shrineMeaning"] == (
        "例の宮は、祭神の情報を手がかりに確認できる神社です。現時点では、相談内容との強い接続は断定せず、参拝先を選ぶための補助情報として扱います。"
    )
    assert generated["actionMeaning"] == (
        "参拝前に、今気になっていることを一つだけ確認します。神社側の情報だけで意味を決めつけず、静かに整理するための候補として扱います。"
    )
    assert generated["benefitActionContext"] is None
    assert generated["heroMeaningCopy"] == "例の宮は、基本情報をもとに参拝先の候補として確認しやすい神社です。"


def test_no_usable_name_hides_the_benefit_action_block():
    payload = compose_shrine_meaning_payload(_source(), matched_benefit_names=["縁結び"])

    block_ids = [block["id"] for block in payload["display"]["blocks"]]
    assert "benefit_action" not in block_ids
    assert "勝運" not in str(payload["display"])


# --- 先に使われる材料は変えない ---------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"description": "静かに心を整えやすい神社。"},
        {"history_theme": "再出発"},
        {"id": next(iter(SHRINE_HISTORY_STORY_OVERRIDES))},
        {"id": next(iter(SHRINE_CULTURE_TRANSLATIONS))},
    ],
)
@pytest.mark.parametrize("names", [["厄除け"], ["縁結び"]])
def test_earlier_materials_still_take_precedence_for_shrine_meaning(overrides, names):
    source = _source(**overrides)

    assert _generated(source, names)["shrineMeaning"] == _generated(source)["shrineMeaning"]


# --- 意味の窓口(API) -------------------------------------------------------------


def _create_shrine() -> Shrine:
    shrine = Shrine.objects.create(
        kind="shrine",
        name_jp="例の宮",
        address="東京都世田谷区",
        latitude=35.0,
        longitude=139.0,
        goriyaku="勝運・厄除け・家内安全",
        sajin="例の祭神",
    )
    tag, _ = GoriyakuTag.objects.get_or_create(name="勝運")
    shrine.goriyaku_tags.add(tag)
    return shrine


def _get(shrine: Shrine, query: str = ""):
    url = reverse("temples:shrine_meaning", kwargs={"pk": shrine.pk}) + query
    response = APIClient().get(url)
    assert response.status_code == 200
    return response.json()


@pytest.mark.django_db
def test_api_without_benefits_param_is_unchanged():
    shrine = _create_shrine()

    payload = _get(shrine)

    assert payload["generated"]["shrineMeaning"].startswith("例の宮は「勝運」に関わる神社")


@pytest.mark.django_db
def test_api_uses_the_first_owned_benefit_from_the_param():
    shrine = _create_shrine()

    payload = _get(shrine, "?benefits=%E7%B8%81%E7%B5%90%E3%81%B3&benefits=%E5%8E%84%E9%99%A4%E3%81%91")

    # 縁結び(持っていない)は飛ばし、厄除け(ご利益の文字列の1つ)を使う。
    assert payload["generated"]["shrineMeaning"].startswith("例の宮は「厄除け」に関わる神社")
    assert "勝運" not in str(payload["display"])


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?benefits=", "?benefits=%E7%B8%81%E7%B5%90%E3%81%B3"])
def test_api_with_param_but_no_usable_name_does_not_fall_back_to_the_first_tag(query):
    shrine = _create_shrine()

    payload = _get(shrine, query)

    assert payload["generated"]["shrineMeaning"].startswith("例の宮は、祭神の情報を手がかりに")
    assert "勝運" not in str(payload["display"])
