"""Deep Dive Deterministic Answer Builder Foundation(PR-ND1)のテスト。

docs/audit/deep-dive-non-llm-runtime-alignment.md §5 Non-LLM Answer
Contractの実装検証。build_deterministic_answer()はpure function
（DeepDiveFactの引用・連結のみ）であり、DBもLLMも一切使わない
——このテストファイルはdjango_db markerを持たない。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from temples.services.deep_dive_deterministic_answer import build_deterministic_answer
from temples.services.deep_dive_retrieval import (
    QUESTION_TYPE_DEITY_NATURE,
    QUESTION_TYPE_DEITY_WHO,
    QUESTION_TYPE_FOUNDING,
    QUESTION_TYPE_HISTORICAL_EVENTS,
    QUESTION_TYPE_OTHER,
    QUESTION_TYPE_TRADITION,
    DeepDiveFact,
)


def _deity_fact(
    label: str,
    *,
    question_type: str = QUESTION_TYPE_DEITY_WHO,
    reason_strength: str = "assertive",
    id: int = 1,
) -> DeepDiveFact:
    return DeepDiveFact(
        type="deity",
        id=id,
        question_type=question_type,
        label=label,
        content=label,
        verification_status="source_confirmed",
        confidence="high" if reason_strength == "assertive" else "medium",
        reason_strength=reason_strength,
        source_ids=(1,),
    )


def _history_fact(
    content: str,
    *,
    question_type: str = QUESTION_TYPE_FOUNDING,
    reason_strength: str = "assertive",
    id: int = 1,
    label: str = "由緒",
) -> DeepDiveFact:
    return DeepDiveFact(
        type="history",
        id=id,
        question_type=question_type,
        label=label,
        content=content,
        verification_status="source_confirmed",
        confidence="high" if reason_strength == "assertive" else "medium",
        reason_strength=reason_strength,
        source_ids=(1,),
    )


# --- 1. deity_who ---


def test_1_deity_who_assertive_builds_sentence_from_labels():
    facts = [_deity_fact("明治天皇"), _deity_fact("昭憲皇太后", id=2)]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer == "明治天皇・昭憲皇太后をお祀りしています。"


# --- 2. deity_nature safe degradation ---


def test_2_deity_nature_ignores_history_facts_and_degrades_to_deity_who_output():
    deity_facts = [_deity_fact("大国魂大神", question_type=QUESTION_TYPE_DEITY_NATURE)]
    history_facts = [
        _history_fact(
            "この神は不安を鎮める神として知られる。",
            question_type=QUESTION_TYPE_DEITY_NATURE,
        )
    ]

    answer = build_deterministic_answer(
        question_type=QUESTION_TYPE_DEITY_NATURE, facts=deity_facts + history_facts
    )

    # deity_whoと同一の出力になる(安全な縮退、PR #2456 §5.3)。
    deity_who_equivalent = build_deterministic_answer(
        question_type=QUESTION_TYPE_DEITY_WHO,
        facts=[replace(deity_facts[0], question_type=QUESTION_TYPE_DEITY_WHO)],
    )
    assert answer == deity_who_equivalent
    assert answer == "大国魂大神をお祀りしています。"
    # history Factの内容(性質の説明)がどこにも混入していないことを明示的に確認する。
    assert "不安を鎮める" not in answer


# --- 3. history (historical_events) ---


def test_3_historical_events_assertive_uses_content_verbatim():
    facts = [
        _history_fact(
            "村社に列格した。",
            question_type=QUESTION_TYPE_HISTORICAL_EVENTS,
        )
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_HISTORICAL_EVENTS, facts=facts)

    assert answer == "村社に列格した。"


# --- 4. founding ---


def test_4_founding_assertive_uses_content_verbatim():
    facts = [
        _history_fact(
            "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
            question_type=QUESTION_TYPE_FOUNDING,
        )
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_FOUNDING, facts=facts)

    assert answer == "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。"


# --- 5. tradition ---


def test_5_tradition_weakened_appends_hedge_and_preserves_content():
    # retrieval層(_apply_tradition_hedge_floor)がtraditionを常にweakenedへ
    # floorするため、ここでもweakenedとして渡す。
    facts = [
        _history_fact(
            "武蔵国府中の武蔵総社六所宮の分霊を勧請して創建した",
            question_type=QUESTION_TYPE_TRADITION,
            reason_strength="weakened",
        )
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_TRADITION, facts=facts)

    assert answer == "武蔵国府中の武蔵総社六所宮の分霊を勧請して創建したと伝わっています。"


def test_5b_tradition_content_ending_with_period_is_trimmed_before_hedge():
    facts = [
        _history_fact(
            "分霊を勧請して創建した。",
            question_type=QUESTION_TYPE_TRADITION,
            reason_strength="weakened",
        )
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_TRADITION, facts=facts)

    assert answer == "分霊を勧請して創建したと伝わっています。"
    assert "。と伝わっています" not in answer


# --- 6. Limited / weakened wording ---


def test_6_deity_weakened_wording_differs_from_assertive():
    facts = [_deity_fact("大国魂大神", reason_strength="weakened")]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer == "大国魂大神をお祀りしていると伝わっています。"


def test_6b_mixed_assertive_and_weakened_deities_produce_two_sentences_not_blended():
    facts = [
        _deity_fact("明治天皇", reason_strength="assertive", id=1),
        _deity_fact("昭憲皇太后", reason_strength="weakened", id=2),
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer == "明治天皇をお祀りしています。\n昭憲皇太后をお祀りしていると伝わっています。"


# --- 7. zero facts ---


def test_7_empty_facts_returns_none():
    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=[])
    assert answer is None


def test_7b_facts_present_but_none_match_question_type_returns_none():
    facts = [_deity_fact("明治天皇", question_type=QUESTION_TYPE_FOUNDING)]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer is None


def test_7c_unsupported_question_type_returns_none_without_guessing():
    facts = [_deity_fact("明治天皇", question_type=QUESTION_TYPE_OTHER)]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_OTHER, facts=facts)

    assert answer is None


# --- 8. multiple facts ---


def test_8_multiple_deity_facts_joined_with_nakaguro():
    facts = [
        _deity_fact("大国魂大神", id=1),
        _deity_fact("天照皇大神", id=2),
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer == "大国魂大神・天照皇大神をお祀りしています。"


def test_8b_multiple_history_facts_joined_with_newline_each_content_preserved():
    facts = [
        _history_fact("村社に列格した。", id=1, question_type=QUESTION_TYPE_HISTORICAL_EVENTS),
        _history_fact("社殿を改築した。", id=2, question_type=QUESTION_TYPE_HISTORICAL_EVENTS),
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_HISTORICAL_EVENTS, facts=facts)

    assert answer == "村社に列格した。\n社殿を改築した。"


# --- 9. suppressed facts exclusion ---


def test_9_suppressed_fact_is_excluded_from_output():
    facts = [
        _deity_fact("明治天皇", reason_strength="assertive", id=1),
        _deity_fact("除外されるべき神", reason_strength="suppressed", id=2),
    ]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer == "明治天皇をお祀りしています。"
    assert "除外されるべき神" not in answer


def test_9b_all_facts_suppressed_returns_none_not_empty_string():
    facts = [_deity_fact("神", reason_strength="suppressed")]

    answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert answer is None


# --- 10. deterministic output ---


def test_10_same_input_produces_identical_output_across_calls():
    facts = [
        _deity_fact("明治天皇", id=1),
        _deity_fact("昭憲皇太后", reason_strength="weakened", id=2),
    ]

    first = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)
    second = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)

    assert first == second
    assert first is not None


# --- 11. no LLM construction/call ---


def test_11_never_constructs_or_calls_llm_client(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("LLM must not be constructed by a deterministic answer builder")

    monkeypatch.setattr("temples.llm.client.LLMClient", _boom)

    facts = [_deity_fact("明治天皇"), _history_fact("創建された。", question_type=QUESTION_TYPE_FOUNDING)]

    deity_answer = build_deterministic_answer(question_type=QUESTION_TYPE_DEITY_WHO, facts=facts)
    history_answer = build_deterministic_answer(question_type=QUESTION_TYPE_FOUNDING, facts=facts)

    assert deity_answer == "明治天皇をお祀りしています。"
    assert history_answer == "創建された。"


def test_11b_module_does_not_import_llm_client_at_all():
    import temples.services.deep_dive_deterministic_answer as mod

    assert "LLMClient" not in vars(mod)
    assert not hasattr(mod, "LLMClient")


# --- Absolute Safety Rules: source_basisはPR-ND1の対象外 ---


def test_source_basis_is_out_of_scope_for_pr_nd1_returns_none():
    facts = [_deity_fact("明治天皇", question_type="source_basis")]

    answer = build_deterministic_answer(question_type="source_basis", facts=facts)

    assert answer is None
