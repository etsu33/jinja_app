"""reason_facts の matched_benefit_names(相談と一致したご利益の名前)の契約。

- goriyaku_tag: 神社のタグのうち、名前がその相談の種類の概念に入るタグの名前（番号は使わない）。
- text_hint: 一致した言葉がご利益の文字列(Shrine.goriyaku)の中にあるときだけ。
  言葉を含むタグがあればタグの名前だけ、無いときだけご利益の文字列を区切った1つずつ。
  説明文の中だけで一致したときは空。
- それ以外(need_tag など): 空。
- 順位・点数は変えない。今ある項目の値も変えない。
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat_ranking import (
    _attach_breakdown,
    _build_reason_facts,
    _collect_matched_benefit_names,
    _to_rank_explanation,
)

# 札の番号は一致に使わない。番号は名前と一緒に持たせるだけの任意の値。
SOME_GID = 2
OTHER_GID = 7
UNRELATED_GID = 9999


def _rec(**overrides):
    rec = {
        "id": 1,
        "shrine_id": 1,
        "name": "テスト神社",
        "goriyaku": "",
        "description": "",
        "goriyaku_tag_ids": [],
        "goriyaku_tag_names": [],
        "astro_tags": [],
        "astro_elements": [],
        "distance_m": 1000,
        "popular_score": 0.5,
    }
    rec.update(overrides)
    return rec


def _facts_of(rec, need_tags):
    _attach_breakdown(rec, birthdate=None, need_tags=need_tags, weights={}, astro_bonus_enabled=False)
    return {(fact["type"], fact["label"]): fact for fact in rec["reason_facts"]}


# --- goriyaku_tag -------------------------------------------------------------


def test_goriyaku_tag_returns_only_the_matched_tag_names():
    rec = _rec(
        goriyaku_tag_ids=[OTHER_GID, SOME_GID],
        goriyaku_tag_names=["家内安全", "厄除け"],
    )

    facts = _facts_of(rec, ["protection"])

    assert facts[("goriyaku_tag", "protection")]["matched_benefit_names"] == ["厄除け"]


def test_goriyaku_tag_without_tag_names_does_not_match_by_id():
    rec = _rec(goriyaku_tag_ids=[SOME_GID], goriyaku_tag_names=[])

    facts = _facts_of(rec, ["protection"])

    assert ("goriyaku_tag", "protection") not in facts


# --- text_hint ----------------------------------------------------------------


def test_text_hint_in_goriyaku_returns_the_goriyaku_segment_name():
    rec = _rec(goriyaku="勝運・厄除け・家内安全")

    facts = _facts_of(rec, ["mental"])

    assert facts[("text_hint", "mental")]["matched_benefit_names"] == ["厄除け"]


def test_text_hint_prefers_the_tag_name_over_the_goriyaku_segment():
    rec = _rec(
        goriyaku="勝運・厄除け・家内安全",
        goriyaku_tag_ids=[UNRELATED_GID],
        goriyaku_tag_names=["厄除け・方除け"],
    )

    facts = _facts_of(rec, ["mental"])

    assert facts[("text_hint", "mental")]["matched_benefit_names"] == ["厄除け・方除け"]


def test_text_hint_only_in_description_is_empty():
    rec = _rec(goriyaku="勝運", description="不安な気持ちを落ち着ける場所")

    facts = _facts_of(rec, ["mental"])

    assert ("text_hint", "mental") in facts
    assert facts[("text_hint", "mental")]["matched_benefit_names"] == []


def test_text_hint_only_in_description_is_empty_even_if_a_tag_has_the_same_word():
    rec = _rec(
        goriyaku="勝運",
        description="厄除けで知られる",
        goriyaku_tag_ids=[UNRELATED_GID],
        goriyaku_tag_names=["厄除け・方除け"],
    )

    facts = _facts_of(rec, ["mental"])

    assert facts[("text_hint", "mental")]["matched_benefit_names"] == []


# --- その他 --------------------------------------------------------------------


def test_need_tag_has_empty_matched_benefit_names():
    rec = _rec(astro_tags=["rest"])

    facts = _facts_of(rec, ["rest"])

    assert facts[("need_tag", "rest")]["matched_benefit_names"] == []


def test_every_reason_fact_has_matched_benefit_names_list():
    rec = _rec(
        goriyaku="勝運・厄除け",
        astro_tags=["rest"],
        goriyaku_tag_ids=[SOME_GID],
        goriyaku_tag_names=["厄除け"],
    )

    _attach_breakdown(rec, birthdate=None, need_tags=["rest", "mental", "protection"], weights={}, astro_bonus_enabled=False)

    assert rec["reason_facts"]
    for fact in rec["reason_facts"]:
        assert isinstance(fact["matched_benefit_names"], list)


def test_names_are_deduped_and_ordered_the_same_every_time():
    rec_kwargs = dict(
        goriyaku="厄除け・不安除け・厄除け",
        goriyaku_tag_ids=[],
        goriyaku_tag_names=[],
    )

    results = [
        _collect_matched_benefit_names(
            rec=_rec(**rec_kwargs),
            goriyaku_text=rec_kwargs["goriyaku"],
            matched_by_gid=[],
            text_hints_by_tag={"mental": ["不安", "厄除"]},
        )["text_hint"]["mental"]
        for _ in range(3)
    ]

    # 文字列の中の順(厄除け → 不安除け)で、同じ名前は1回だけ。言葉の順には左右されない。
    assert results[0] == ["厄除け", "不安除け"]
    assert results[1] == results[0] and results[2] == results[0]


def test_tag_names_follow_the_tag_order():
    pairs = {
        "rec": _rec(
            goriyaku_tag_ids=[OTHER_GID, UNRELATED_GID],
            goriyaku_tag_names=["厄除け・方除け", "心願成就"],
        ),
        "goriyaku_text": "心願・厄除",
    }

    names = _collect_matched_benefit_names(
        matched_by_gid=[],
        text_hints_by_tag={"mental": ["厄除", "心願"]},
        **pairs,
    )["text_hint"]["mental"]

    assert names == ["厄除け・方除け", "心願成就"]


# --- 今ある項目と順位・点数は変えない -------------------------------------------


def test_existing_reason_fact_fields_are_unchanged():
    facts = _build_reason_facts(
        matched_by_tag=["rest"],
        matched_by_gid=["money"],
        matched_by_text=["mental"],
        matched_by_user_selected_gid=[],
        goriyaku_tag_label_by_id={},
        text_score_by_tag={"mental": 5},
        score_element=0,
        astro_bonus_enabled=False,
        matched_benefit_names_by_type={
            "goriyaku_tag": {"money": ["金運・商売繁盛"]},
            "text_hint": {"mental": ["厄除け"]},
        },
    )
    by_type = {fact["type"]: fact for fact in facts}

    assert {key: value for key, value in by_type["text_hint"].items() if key != "matched_benefit_names"} == {
        "type": "text_hint",
        "label": "mental",
        "label_ja": "不安・心",
        "evidence": ["text_score:5"],
        "score": 5.0,
        "is_primary": False,
    }
    assert by_type["text_hint"]["matched_benefit_names"] == ["厄除け"]
    assert by_type["goriyaku_tag"]["label"] == "money"
    assert by_type["goriyaku_tag"]["evidence"] == ["goriyaku_tag_ids"]
    assert by_type["goriyaku_tag"]["score"] == 2.0
    assert by_type["goriyaku_tag"]["matched_benefit_names"] == ["金運・商売繁盛"]
    assert by_type["need_tag"]["matched_benefit_names"] == []


def test_scores_and_primary_reason_do_not_depend_on_tag_ids():
    # 一致は札の名前で決まる。同じ名前なら、番号が違っても点数・主な理由・根拠は同じ。
    base = dict(goriyaku="勝運・厄除け・家内安全", goriyaku_tag_names=["厄除け"])
    rec_a = _rec(**base, goriyaku_tag_ids=[SOME_GID])
    rec_b = _rec(**base, goriyaku_tag_ids=[UNRELATED_GID])

    for rec in (rec_a, rec_b):
        _attach_breakdown(rec, birthdate=None, need_tags=["protection", "mental"], weights={}, astro_bonus_enabled=False)

    assert rec_a["breakdown"] == rec_b["breakdown"]
    assert rec_a["_score_total"] == rec_b["_score_total"]
    assert rec_a["_primary_reason_source"] == rec_b["_primary_reason_source"]
    assert rec_a["_primary_reason_label"] == rec_b["_primary_reason_label"]
    assert rec_a["reason_facts"] == rec_b["reason_facts"]


# --- 「この神社が1位の理由」の空白 ----------------------------------------------


def _rank_rec(contributions: dict[str, float]):
    features = {
        "need": {"rank_weighted_contribution": contributions.get("need", 0.0)},
        "element": {"contribution": contributions.get("element", 0.0)},
        "distance": {"contribution": contributions.get("distance", 0.0)},
        "popular": {"contribution": contributions.get("popular", 0.0)},
        "direction": {"contribution": contributions.get("direction", 0.0)},
    }
    return {
        "breakdown": {},
        "breakdown_detail": {"features": features},
        "_primary_reason_source": "text_hint",
        "_primary_reason_label": "mental",
    }


@pytest.mark.parametrize(
    "contributions,expected_tail",
    [
        ({"need": 1.0}, "特に悩みとの一致が順位を押し上げています。"),
        ({"need": 1.0, "distance": 0.5}, "特に悩みとの一致・距離が順位を押し上げています。"),
    ],
)
def test_rank_summary_has_no_extra_spaces(contributions, expected_tail):
    summary = _to_rank_explanation(rec=_rank_rec(contributions))["summary"]

    assert summary == f"相談内容との一致は「不安・心」が主因です。{expected_tail}"
    assert " " not in summary
