"""相談の種類 → ご利益の概念 の対応表（temples.domain.need_to_goriyaku_concepts）の契約。

docs/knowledge/goriyaku-concept-rules.md（ルール5・6）と「相談の種類との対応（v1）」。
- 対応表には概念の識別子だけを書く。札の番号・札の名前は書かない。
- 札は、札の名前から概念を引いて一致を決める。未分類の札・番号だけの札は一致しない。

以前の need_to_goriyaku_tag_ids.py（札の番号で結んでいた）のテスト
（test_need_to_goriyaku_tag_ids / test_family_gid_mapping_narrow /
test_communication_gid_evidence_disabled）は、このファイルに置き換えた。
"""

from __future__ import annotations

import pytest

from temples.domain.goriyaku_concepts_v1 import CONCEPTS_BY_KEY
from temples.domain.need_tags import NEED_TAGS, extract_need_tags
from temples.domain.need_to_goriyaku_concepts import (
    NEED_TO_GORIYAKU_CONCEPTS,
    matching_tag_names,
    need_concept_keys,
    needs_for_tag_name,
    tag_matches_need,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_need import resolve_need_payload
from temples.services.concierge_chat_ranking import NEED_TEXT_WEIGHTS, _attach_breakdown

_NEED_WEIGHTS = {"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0}

EXPECTED = {
    "love": {"love_fulfillment", "relationship_bonding"},
    "relationship": {"relationship_bonding"},
    "marriage": {"relationship_bonding", "marital_harmony"},
    "communication": set(),
    "career": {"work_fortune", "career_advancement", "guidance"},
    "money": {"financial_fortune", "business_prosperity"},
    "study": {"academic_success", "exam_success"},
    "focus": {"skill_improvement", "academic_success"},
    "health": {"illness_recovery", "longevity", "leg_lower_back_health"},
    "mental": set(),
    "protection": {"misfortune_warding", "all_direction_warding", "strong_fortune_warding"},
    "courage": {"good_fortune", "victory_fortune"},
    "rest": set(),
    "family": {"safe_childbirth", "fertility"},
    "travel_safe": {"traffic_safety", "maritime_safety"},
}


def _breakdown(*, need_tags, tag_names=None, goriyaku="", tag_ids=None, description=""):
    rec = {
        "id": 1,
        "name": "テスト神社",
        "astro_tags": [],
        "astro_elements": [],
        "goriyaku": goriyaku,
        "description": description,
        "goriyaku_tag_ids": tag_ids or [],
        "goriyaku_tag_names": tag_names or [],
        "popular_score": 0,
    }
    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=need_tags,
        weights=_NEED_WEIGHTS,
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="",
        requested_goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=None,
    )
    return rec


# --- 対応表の中身 ----------------------------------------------------------------


def test_table_is_exactly_the_decided_v1_mapping():
    assert {need: set(keys) for need, keys in NEED_TO_GORIYAKU_CONCEPTS.items()} == EXPECTED


def test_every_need_tag_has_a_row_and_every_key_is_a_known_concept():
    assert set(NEED_TO_GORIYAKU_CONCEPTS) == set(NEED_TAGS)
    for keys in NEED_TO_GORIYAKU_CONCEPTS.values():
        assert all(key in CONCEPTS_BY_KEY for key in keys)


def test_household_safety_is_tied_to_no_need():
    # family は狭い意味（安産・子宝）だけ（Mother Ship 2026-08-29）。家内安全はどこにも結ばない。
    assert all("household_safety" not in keys for keys in NEED_TO_GORIYAKU_CONCEPTS.values())
    assert needs_for_tag_name("家内安全") == ()


@pytest.mark.parametrize("need", ["communication", "mental", "rest"])
def test_needs_chosen_by_place_or_limited_evidence_have_no_concepts(need):
    assert need_concept_keys(need) == frozenset()
    assert not _breakdown(need_tags=[need], tag_names=["勝運", "家内安全", "福徳", "厄除け"])["breakdown"][
        "matched_need_tags"
    ]


def test_illness_prevention_is_not_added_until_its_source_is_confirmed():
    assert "illness_prevention" not in CONCEPTS_BY_KEY
    assert all("illness_prevention" not in keys for keys in NEED_TO_GORIYAKU_CONCEPTS.values())


# --- 札の名前からの一致 ------------------------------------------------------------


@pytest.mark.parametrize(
    "tag_name,need",
    [
        ("八方除け", "protection"),  # 別名 → all_direction_warding
        ("方除け", "protection"),
        ("八難除", "protection"),  # 別名 → misfortune_warding
        ("延命長寿", "health"),  # 別名 → longevity
        ("航海安全", "travel_safe"),  # 別名 → maritime_safety
        ("福徳", "courage"),  # 別名 → good_fortune
        ("武運長久", "courage"),  # 別名 → victory_fortune
        ("技芸上達", "focus"),
        ("金運・商売繁盛", "money"),  # 組み合わせの札
    ],
)
def test_aliases_and_combined_tags_match_through_their_concept(tag_name, need):
    assert tag_matches_need(tag_name, need)
    rec = _breakdown(need_tags=[need], tag_names=[tag_name])
    assert rec["breakdown"]["matched_need_tags"] == [need]
    assert rec["breakdown"]["need_evidence_winner_by_tag"] == {need: "gid"}


@pytest.mark.parametrize(
    "tag_name,need",
    [
        ("家内安全", "rest"),
        ("福徳", "rest"),
        ("家内安全", "health"),
        ("勝運", "mental"),
        ("金運", "mental"),
        ("勝運", "protection"),
        ("開運", "career"),
        ("五穀豊穣", "money"),
        ("合格祈願", "focus"),
        ("家庭円満", "family"),
        ("知らない札", "love"),
    ],
)
def test_former_mismatched_or_unclassified_tags_no_longer_match(tag_name, need):
    assert not tag_matches_need(tag_name, need)
    assert _breakdown(need_tags=[need], tag_names=[tag_name])["breakdown"]["matched_need_tags"] == []


def test_tag_ids_without_names_do_not_match():
    # 札の番号は環境で変わるので使わない（本番の 7＝家内安全 を rest として数えていたずれの元）。
    rec = _breakdown(need_tags=["protection"], tag_ids=[2])
    assert rec["breakdown"]["matched_need_tags"] == []


def test_matching_tag_names_keeps_tag_order_and_dedupes():
    assert matching_tag_names(["八方除け", "勝運", "厄除け", "八方除け"], "protection") == ["八方除け", "厄除け"]
    assert matching_tag_names(None, "protection") == []


def test_needs_for_tag_name():
    assert needs_for_tag_name("縁結び") == ("love", "marriage", "relationship")
    assert needs_for_tag_name("学業成就") == ("focus", "study")
    assert needs_for_tag_name("知らない札") == ()


def test_matched_benefit_names_follow_the_concept_match():
    rec = _breakdown(need_tags=["rest", "mental", "protection"], tag_names=["勝運", "厄除け", "家内安全"])
    facts = {(f["type"], f["label"]): f for f in rec["reason_facts"]}
    assert facts[("goriyaku_tag", "protection")]["matched_benefit_names"] == ["厄除け"]
    assert ("goriyaku_tag", "rest") not in facts
    assert ("goriyaku_tag", "mental") not in facts


# --- communication（札でも言葉でも結ばない。読み取りは残す） ----------------------------


def test_communication_has_no_text_evidence_path():
    assert "communication" not in NEED_TEXT_WEIGHTS


@pytest.mark.parametrize("query", ["コミュニケーション能力を上げたい", "人とうまく話せるようになりたい", "営業で成果を出したい"])
def test_communication_interpreter_recognition_preserved(query):
    assert "communication" in extract_need_tags(query, max_tags=3).tags
    assert "communication" in resolve_need_payload(query=query, need_tags=None, max_tags=3)["tags"]


def test_communication_only_query_scores_need_zero_end_to_end():
    recs = build_chat_recommendations(
        query="コミュニケーション能力を上げたい",
        language="ja",
        candidates=[
            {
                "name": "強運厄除け神社",
                "goriyaku_tag_ids": [30, 33, 37, 39],
                "goriyaku_tag_names": ["強運厄除け", "病気平癒", "延命長寿", "農業守護"],
                "goriyaku": "強運厄除け・病気平癒・延命長寿・農業守護",
                "description": "",
                "astro_tags": [],
                "astro_elements": [],
                "astro_priority": 0,
                "popular_score": 5.0,
            }
        ],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert recs["_need"]["tags"] == ["communication"]
    assert top1["breakdown"]["matched_need_tags"] == []
    assert top1["breakdown"]["score_need"] == 0
    for rf in top1.get("reason_facts") or []:
        assert rf.get("label") != "communication"
