"""Deep Dive Backend Retrieval Foundation。

docs/product/deep-dive-answer-generation-contract.md の実装検証。LLM生成
（PR-B3）は対象外であり、本テストもLLMを一切呼び出さない。安全性の核心
（Zero-Fact Short Circuit、Evidence Gate再利用、provenance整合）を検証する。
"""

from __future__ import annotations

import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.deep_dive_retrieval import (
    QUESTION_TYPE_DEITY_NATURE,
    QUESTION_TYPE_DEITY_WHO,
    QUESTION_TYPE_FOUNDING,
    QUESTION_TYPE_HISTORICAL_EVENTS,
    QUESTION_TYPE_OTHER,
    QUESTION_TYPE_TRADITION,
    build_deep_dive_context,
    classify_question,
    get_shrine_deep_dive_readiness,
)

pytestmark = pytest.mark.django_db


def _create_shrine(name: str) -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_source(
    title: str, verification_status: str = "source_confirmed", **kwargs
) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title=title,
        publisher="神社公式",
        url="https://example.com/",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


def _create_deity(shrine: Shrine, display_name: str, sort_order: int = 0, **kwargs) -> ShrineDeity:
    defaults = dict(
        display_name=display_name,
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _create_history(shrine: Shrine, title: str, sort_order: int = 0, **kwargs) -> ShrineHistory:
    defaults = dict(
        history_type="founding",
        title=title,
        content="内容の本文",
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineHistory.objects.create(shrine=shrine, **defaults)


# --- 1. 明治神宮 deity ---


def test_1_meiji_jingu_deity_who_returns_deity_facts_with_provenance():
    shrine = _create_shrine("明治神宮相当")
    source = _create_source("公式サイト「明治神宮とは」")
    deity1 = _create_deity(shrine, "明治天皇", sort_order=0)
    deity2 = _create_deity(shrine, "昭憲皇太后", sort_order=1)
    history = _create_history(shrine, "明治神宮の創建")
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="この神社は誰を祀っていますか？")

    assert context.readiness == "full"
    assert context.question_type == [QUESTION_TYPE_DEITY_WHO]
    assert {f.id for f in context.facts} == {deity1.id, deity2.id}
    assert all(f.type == "deity" for f in context.facts)
    assert all(f.reason_strength == "assertive" for f in context.facts)
    assert {s.id for s in context.sources} == {source.id}
    assert context.limitations is None
    assert context.unanswered_aspects == []


# --- 2. 明治神宮 history ---


def test_2_meiji_jingu_founding_question_returns_history_facts_only():
    shrine = _create_shrine("明治神宮相当2")
    source = _create_source("公式サイト")
    deity = _create_deity(shrine, "明治天皇")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    tradition = _create_history(shrine, "言い伝え", history_type="tradition", sort_order=1)
    for fact in (deity, founding, tradition):
        fact.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="なぜ創建されたのですか？")

    assert context.question_type == [QUESTION_TYPE_FOUNDING]
    assert [f.id for f in context.facts] == [founding.id]
    assert context.facts[0].type == "history"
    # traditionは対象外（founding/official_originのみ取得、Retrieval Contract §4）
    assert tradition.id not in [f.id for f in context.facts]


# --- 3. Full Ready通常神社 ---


def test_3_typical_full_ready_shrine_is_classified_full():
    shrine = _create_shrine("通常神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "何らかの神", confidence="high")
    history = _create_history(shrine, "由緒", confidence="medium")
    deity.sources.add(source)
    history.sources.add(source)

    assert get_shrine_deep_dive_readiness(shrine.id) == evidence_gate.DEEP_DIVE_FULL


# --- 4. 給田六所神社（Limited）相当 ---


def test_4_limited_shrine_all_medium_confidence_is_classified_limited_with_weakened_strength():
    shrine = _create_shrine("給田六所神社相当")
    source = _create_source("公式")
    deity1 = _create_deity(shrine, "大国魂大神", confidence="medium", role="primary")
    deity2 = _create_deity(shrine, "天照皇大神", confidence="medium", role="secondary", sort_order=1)
    history = _create_history(shrine, "神明社の合祀", confidence="medium", history_type="historical_event")
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    assert get_shrine_deep_dive_readiness(shrine.id) == evidence_gate.DEEP_DIVE_LIMITED

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")
    assert context.readiness == "limited"
    assert all(f.reason_strength == "weakened" for f in context.facts)
    assert context.limitations is not None
    assert "限られており" in context.limitations


# --- 5. Not Ready ---


def test_5_not_ready_shrine_short_circuits_without_classification_or_retrieval():
    shrine = _create_shrine("由緒未確認神社")
    # ShrineDeity/ShrineHistoryを一切作らない（Not Ready、structural条件を満たさない）。

    assert get_shrine_deep_dive_readiness(shrine.id) == evidence_gate.DEEP_DIVE_NOT_READY

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")
    assert context.readiness == "not_ready"
    # Not Readyでは質問分類すら行わない(Defense in depth、§8ステップ2)。
    assert context.question_type == []
    assert context.facts == []
    assert context.sources == []
    assert context.unanswered_aspects == []
    assert context.limitations is not None


def test_5b_not_ready_shrine_partial_knowledge_deity_only_no_history():
    shrine = _create_shrine("由緒未確認神社2")
    source = _create_source("公式")
    deity = _create_deity(shrine, "何らかの神")
    deity.sources.add(source)
    # historyを作らない → structural readyを満たさない。

    assert get_shrine_deep_dive_readiness(shrine.id) == evidence_gate.DEEP_DIVE_NOT_READY


# --- 6. Fact 0 ---


def test_6_zero_fact_short_circuit_returns_unavailable_message_without_llm_call():
    shrine = _create_shrine("伝承なし神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "何らかの神")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    for fact in (deity, founding):
        fact.sources.add(source)
    # tradition種別のHistoryは1件も無い。

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="どんな伝承がありますか？")

    assert context.question_type == [QUESTION_TYPE_TRADITION]
    assert context.facts == []
    assert context.sources == []
    assert context.limitations == "現在確認できる資料では、詳しい情報を確認できません。"
    assert context.unanswered_aspects == [QUESTION_TYPE_TRADITION]


def test_6b_unclassifiable_question_returns_other_without_guessing():
    shrine = _create_shrine("何でも神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "何らかの神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="今日の天気はどうですか？")

    assert context.question_type == [QUESTION_TYPE_OTHER]
    assert context.facts == []
    assert context.limitations is not None


# --- 7. Sourceなし ---


def test_7_fact_without_fact_ready_source_is_excluded_from_retrieval():
    shrine = _create_shrine("Source無し神社")
    deity_with_source = _create_deity(shrine, "Source有りの神")
    deity_without_source = _create_deity(shrine, "Source無しの神", sort_order=1)
    source = _create_source("公式")
    deity_with_source.sources.add(source)
    # deity_without_sourceにはSourceを一切addしない。

    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    fact_ids = {f.id for f in context.facts}
    assert deity_with_source.id in fact_ids
    assert deity_without_source.id not in fact_ids


def test_7b_fact_with_only_draft_source_is_excluded():
    shrine = _create_shrine("draft Source神社")
    deity = _create_deity(shrine, "神")
    draft_source = _create_source("未確認資料", verification_status="draft")
    deity.sources.add(draft_source)
    history = _create_history(shrine, "由緒")
    ready_source = _create_source("公式")
    history.sources.add(ready_source)

    # deityはfact-ready Sourceを持たないためnot usable → structural readyを満たさない
    assert get_shrine_deep_dive_readiness(shrine.id) == evidence_gate.DEEP_DIVE_NOT_READY


# --- 8. medium confidence ---


def test_8_medium_confidence_maps_to_weakened_reason_strength():
    shrine = _create_shrine("medium confidence神社")
    source = _create_source("公式")
    deity_high = _create_deity(shrine, "高確信度の神", confidence="high")
    deity_medium = _create_deity(shrine, "中確信度の神", confidence="medium", sort_order=1)
    for fact in (deity_high, deity_medium):
        fact.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    strengths_by_id = {f.id: f.reason_strength for f in context.facts}
    assert strengths_by_id[deity_high.id] == "assertive"
    assert strengths_by_id[deity_medium.id] == "weakened"


def test_8b_tradition_history_type_is_floored_to_weakened_even_with_high_confidence():
    shrine = _create_shrine("伝承神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    tradition = _create_history(shrine, "言い伝え", history_type="tradition", confidence="high")
    tradition.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="どんな伝承がありますか？")

    assert len(context.facts) == 1
    # confidence=highでもtradition floorによりweakenedへ引き下げられる
    # (既存recommendation_reason_v4.pyのTRADITION_ALWAYS_HEDGED契約と同一の規則)。
    assert context.facts[0].reason_strength == "weakened"


# --- 9. 複合質問 ---


def test_9_compound_question_retrieves_multiple_question_types_without_duplicates():
    shrine = _create_shrine("複合質問神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    for fact in (deity, founding):
        fact.sources.add(source)

    question_types = classify_question("誰を祀っていて、なぜ創建されたのですか？")
    assert question_types == [QUESTION_TYPE_DEITY_WHO, QUESTION_TYPE_FOUNDING]

    context = build_deep_dive_context(
        shrine_id=shrine.id, question_text="誰を祀っていて、なぜ創建されたのですか？"
    )

    assert context.question_type == [QUESTION_TYPE_DEITY_WHO, QUESTION_TYPE_FOUNDING]
    fact_ids = {f.id for f in context.facts}
    assert fact_ids == {deity.id, founding.id}
    assert context.unanswered_aspects == []


def test_9b_compound_question_deduplicates_overlapping_facts():
    shrine = _create_shrine("重複質問神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    # deity_who / deity_nature はどちらもShrineDeityを取得するため、同じ質問に
    # 両方のキーワードが含まれる場合でもfactsへ重複登録しない。
    context = build_deep_dive_context(
        shrine_id=shrine.id, question_text="誰を祀っていて、どんな神様ですか？"
    )

    assert set(context.question_type) == {QUESTION_TYPE_DEITY_WHO, QUESTION_TYPE_DEITY_NATURE}
    deity_fact_ids = [f.id for f in context.facts if f.type == "deity"]
    assert deity_fact_ids.count(deity.id) == 1


# --- 10. provenance整合 ---


def test_10_provenance_round_trips_from_facts_to_sources_exactly():
    shrine = _create_shrine("Provenance検証神社")
    source_a = _create_source("Source A")
    source_b = _create_source("Source B")
    unrelated_source = _create_source("無関係なSource")

    deity = _create_deity(shrine, "神")
    deity.sources.add(source_a, source_b)
    history = _create_history(shrine, "由緒")
    history.sources.add(source_a)
    # unrelated_sourceはどのFactにもRelationしない。

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    deity_fact = next(f for f in context.facts if f.id == deity.id)
    assert set(deity_fact.source_ids) == {source_a.id, source_b.id}

    returned_source_ids = {s.id for s in context.sources}
    # sourcesはfacts.source_idsの和集合と厳密に一致する（余分・不足なし）。
    expected_source_ids = {sid for f in context.facts for sid in f.source_ids}
    assert returned_source_ids == expected_source_ids
    assert unrelated_source.id not in returned_source_ids

    source_a_out = next(s for s in context.sources if s.id == source_a.id)
    assert source_a_out.title == "Source A"
    assert source_a_out.publisher == "神社公式"
    assert source_a_out.source_type == "shrine_official"


def test_10b_source_basis_question_derives_sources_from_prior_facts_not_new_retrieval():
    shrine = _create_shrine("根拠質問神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    first_context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")
    assert first_context.facts

    followup_context = build_deep_dive_context(
        shrine_id=shrine.id, question_text="その根拠は何ですか？", prior_facts=first_context.facts
    )

    assert followup_context.question_type == ["source_basis"]
    # source_basisは新規Fact取得を行わず、prior_factsをそのまま使う。
    assert followup_context.facts == first_context.facts
    assert {s.id for s in followup_context.sources} == {source.id}


def test_10c_source_basis_without_prior_facts_short_circuits():
    shrine = _create_shrine("根拠のみ神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="根拠は何ですか？")

    assert context.question_type == ["source_basis"]
    assert context.facts == []
    assert context.limitations is not None
