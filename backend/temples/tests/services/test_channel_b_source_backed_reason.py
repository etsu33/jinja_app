"""MS-5: Channel B だけが一致した request の Need に、Source Fact に基づく理由文を付ける。

docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md §12.14
（REASON_COPY_BOUNDARY = EVIDENCE_TYPED_CLAIM_STRENGTH）。候補の既存の carrier
（TypedNeedMatch）だけを使い、DB は読まない。ranking・Channel A は変えない。
"""

from __future__ import annotations

import pytest

from temples.services import concierge_chat_ranking
from temples.services.channel_b_reason_copy import (
    CHANNEL_B_FACT_TEMPLATES,
    render_channel_b_reason,
    select_channel_b_reason_match,
)
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import build_recommendation_reason

PRAYER = "official_prayer_supported"
GUIDANCE = "official_current_guidance_supported"
COMBINED = "official_prayer_and_current_guidance_list_level"
GENERIC = "試験神社は、今の悩みや願いに合わせて参拝先の候補に入れています。"
INTERPRETATION = "今の悩みや願いに合わせて参拝先の候補に入れています。"
UNSUPPORTED_BENEFIT_CLAIMS = (
    "ご利益で知られる",
    "のご利益がある",
    "ご利益があります",
    "が叶います",
)


def _match(
    need: str = "money",
    key: str = "synthetic-ms5-0001",
    *,
    concept: str = "商売繁盛",
    wording: str = "商売繁昌",
    signal_type: str = PRAYER,
) -> TypedNeedMatch:
    return TypedNeedMatch(
        need=need,
        canonical_concept_name=concept,
        signal_type=signal_type,
        source_fact_key=key,
        source_attested_wording=wording,
    )


def _rec(*matches: TypedNeedMatch, **overrides) -> dict:
    rec = {
        "name": "試験神社",
        "goriyaku": "",
        "goriyaku_tag_ids": [],
        "breakdown": {"matched_need_tags": []},
        "_primary_reason_label": "fallback",
        "_primary_reason_source": "fallback",
        CHANNEL_B_TYPED_NEED_MATCHES_KEY: tuple(matches),
    }
    rec.update(overrides)
    return rec


def _reason(rec: dict, need_tags: list[str]) -> str:
    return build_recommendation_reason(rec, public_mode="need", birthdate=None, need_tags=need_tags)


def _assert_no_unsupported_claim(text: str) -> None:
    for claim in UNSUPPORTED_BENEFIT_CLAIMS:
        assert claim not in text


# ---------- A. Channel B だけの Need ----------


@pytest.mark.parametrize(
    "signal_type,fact",
    [
        (PRAYER, "試験神社の公式の祈願案内に『商売繁昌』の記載があります。"),
        (GUIDANCE, "試験神社の公式の現在の案内に『商売繁昌』の記載があります。"),
        (COMBINED, "試験神社の公式の祈願・現在の案内の一覧に『商売繁昌』が含まれています。"),
    ],
)
def test_a_channel_b_only_need_gets_a_source_backed_reason(signal_type, fact):
    text = _reason(_rec(_match(signal_type=signal_type)), ["money"])
    # signal_type（evidence characterization）が事実の文を決め、Need の文は分けて続ける。
    assert text == fact + INTERPRETATION
    # Source に帰属させるのは source wording。SAFE_NORMALIZATION の concept は Source の文言として示さない。
    assert "『商売繁昌』" in text
    assert "商売繁盛" not in text
    _assert_no_unsupported_claim(text)
    assert "ご利益" not in text


def test_a_templates_cover_exactly_the_frozen_characterizations():
    assert set(CHANNEL_B_FACT_TEMPLATES) == {PRAYER, GUIDANCE, COMBINED}
    for template in CHANNEL_B_FACT_TEMPLATES.values():
        assert "ご利益" not in template


def test_a_without_name_the_fact_sentence_has_no_subject():
    text = _reason(_rec(_match(wording="学業成就", need="study"), name=""), ["study"])
    assert text == "公式の祈願案内に『学業成就』の記載があります。" + INTERPRETATION


# ---------- E. A + B が同じ Need ----------


@pytest.mark.parametrize(
    "channel_a",
    [
        {"breakdown": {"matched_need_tags": ["money"]}},
        {"_primary_reason_label": "money", "_primary_reason_source": "need_tag"},
    ],
)
def test_e_channel_a_owns_the_reason_for_the_same_need(channel_a):
    without_b = _reason(_rec(**channel_a), ["money"])
    with_b = _reason(_rec(_match(), **channel_a), ["money"])
    assert with_b == without_b
    assert "『" not in with_b and "公式の" not in with_b


@pytest.mark.django_db
def test_e_end_to_end_channel_a_reason_and_score_are_unchanged(settings):
    settings.CONCIERGE_USE_LLM = False

    def _row(with_carrier: bool) -> dict:
        candidate = _candidate("金運神社", goriyaku_tag_ids=[4])
        if with_carrier:
            candidate[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = (_match(concept="金運", wording="金運"),)
        return _recommend([candidate], ["money"])["recommendations"][0]

    before, after = _row(False), _row(True)
    assert before["breakdown"]["matched_need_tags"] == ["money"]
    assert after["reason"] == before["reason"]
    assert after["_reason_facts"] == before["_reason_facts"]
    # 同じ Need は1回だけ（PR-F: Channel A がある Need に Channel B は寄与しない）。
    assert after["_score_total"] == before["_score_total"]
    assert after["breakdown_detail"] == before["breakdown_detail"]


# ---------- F. request の Need が無い ----------


@pytest.mark.parametrize("need_tags", [[], ["study"]])
def test_f_no_matching_request_need_gives_no_channel_b_clause(need_tags):
    # carrier の Need（money）が request に無ければ、Channel B の文は作らない。
    assert _reason(_rec(_match()), need_tags) == GENERIC


# ---------- G. 複数の一致 ----------

_MONEY_Z = _match("money", "z-money", wording="商売繁昌")
_MONEY_A = _match("money", "a-money", wording="金運祈願", concept="金運")
_STUDY_B = _match("study", "b-study", wording="学業成就", concept="学業成就")


@pytest.mark.parametrize(
    "need_tags,expected_key",
    [
        (["money", "study"], "a-money"),
        (["study", "money"], "b-study"),
    ],
)
def test_g_selection_follows_need_order_then_source_fact_key(need_tags, expected_key):
    for carrier in ((_MONEY_Z, _STUDY_B, _MONEY_A), (_MONEY_A, _MONEY_Z, _STUDY_B)):
        rec = _rec(*carrier)
        selected = select_channel_b_reason_match(rec, need_tags, [])
        assert selected is not None and selected.source_fact_key == expected_key
        assert _reason(rec, need_tags) == render_channel_b_reason(selected, name="試験神社")


def test_g_selection_skips_needs_that_channel_a_already_matched():
    rec = _rec(_MONEY_Z, _STUDY_B, _MONEY_A, breakdown={"matched_need_tags": ["money"]})
    assert select_channel_b_reason_match(rec, ["money", "study"], ["money"]) == _STUDY_B
    # Channel A の理由がある候補は Channel A の文のまま（Channel B の文を足さない）。
    assert "『" not in _reason(rec, ["money", "study"])


def test_g_order_does_not_depend_on_database_id():
    # source_fact_key の順だけで決まる（DB の id や carrier の並びでは決まらない）。
    selected = {
        select_channel_b_reason_match(_rec(*carrier), ["money"], []).source_fact_key
        for carrier in ((_MONEY_Z, _MONEY_A), (_MONEY_A, _MONEY_Z))
    }
    assert selected == {"a-money"}


# ---------- H. 想定外の signal_type ----------


@pytest.mark.parametrize(
    "match",
    [
        _match(signal_type="official_goriyaku_wording"),
        _match(signal_type=""),
        _match(wording=""),
        _match(wording="   "),
    ],
)
def test_h_unsupported_signal_or_blank_wording_falls_back_to_the_generic_reason(match):
    assert render_channel_b_reason(match, name="試験神社") is None
    text = _reason(_rec(match), ["money"])
    assert text == GENERIC
    _assert_no_unsupported_claim(text)


def test_h_non_typed_carrier_items_are_ignored():
    rec = _rec()
    rec[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = ({"need": "money", "source_fact_key": "x"},)
    assert _reason(rec, ["money"]) == GENERIC


# ---------- I. 公開 response / ranking ----------


def _candidate(name: str, **overrides) -> dict:
    row = {
        "id": sum(map(ord, name)),
        "shrine_id": sum(map(ord, name)),
        "name": name,
        "address": "東京都試験区1-1-1",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 100.0,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
    }
    row.update(overrides)
    return row


def _recommend(candidates: list[dict], need_tags: list[str]) -> dict:
    return build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        bias={"lat": 35.0, "lng": 139.0},
        public_mode="need",
        flow="A",
        need_tags=need_tags,
        llm_enabled=False,
    )


@pytest.mark.django_db
def test_i_carrier_is_stripped_and_ranking_is_unchanged(settings, monkeypatch):
    settings.CONCIERGE_USE_LLM = False

    def _candidates() -> list[dict]:
        b_only = _candidate("経路B神社", distance_m=900.0)
        b_only[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = (_match(),)
        return [b_only, _candidate("近い神社", distance_m=100.0)]

    with_reason = _recommend(_candidates(), ["money"])["recommendations"]
    monkeypatch.setattr(concierge_chat_ranking, "select_channel_b_reason_match", lambda *a: None)
    without_reason = _recommend(_candidates(), ["money"])["recommendations"]

    b_row = next(r for r in with_reason if r["name"] == "経路B神社")
    assert b_row["reason"] == (
        "経路B神社の公式の祈願案内に『商売繁昌』の記載があります。" + INTERPRETATION
    )
    assert next(r for r in without_reason if r["name"] == "経路B神社")["reason"] == (
        "経路B神社は、今の悩みや願いに合わせて参拝先の候補に入れています。"
    )
    # 理由文は順位・score を変えない。
    assert [r["name"] for r in with_reason] == [r["name"] for r in without_reason]
    for row, base in zip(with_reason, without_reason, strict=True):
        assert row["_score_total"] == base["_score_total"]
        assert row["breakdown"] == base["breakdown"]
        assert row["breakdown_detail"] == base["breakdown_detail"]
        assert row["_reason_facts"] == base["_reason_facts"]
        # carrier は公開 row に残らず、source_fact_key も出ない。
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in row
        assert "synthetic-ms5-0001" not in repr(row)
