"""Deep Dive Answer Generation(PR-B3 + PR-B4)のテスト。

docs/product/deep-dive-answer-generation-contract.md の実装検証。
Call Gate(readiness=not_ready/usable facts=0でLLM未呼び出し)、provenanceの
機械的導出、Limitedでの非推測、LLM失敗時の安全なfallbackを検証する。
実LLM(openai SDK)は一切呼び出さない — LLMClientをテストダブルで差し替える。
"""

from __future__ import annotations

import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import deep_dive_answer
from temples.services.deep_dive_answer import generate_deep_dive_answer

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


def _boom(*args, **kwargs):
    raise AssertionError("LLM must not be constructed/called in this path")


class _FakeLLMClient:
    """テストダブル。実openai SDKは一切importしない。"""

    def __init__(self, content=None, raise_exc: Exception | None = None):
        self._client = object()
        self._mode = "chat"
        self._content = content
        self._raise_exc = raise_exc
        self.calls: list[list[dict]] = []

    def chat(self, messages):
        self.calls.append(messages)
        if self._raise_exc is not None:
            raise self._raise_exc
        return {"role": "assistant", "content": self._content}


# --- Call Gate: not_ready / zero-fact ではLLMを一切呼び出さない ---


def test_not_ready_shrine_never_constructs_llm_client(monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("由緒未確認神社")
    # ShrineDeity/ShrineHistoryを作らない → not_ready。

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "not_ready"
    assert result.answer == ""
    assert result.facts_used == []
    assert result.sources_used == []
    assert result.limitations is not None
    assert result.llm_used is False


def test_zero_fact_short_circuit_never_constructs_llm_client(monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("伝承なし神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "何らかの神")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    for fact in (deity, founding):
        fact.sources.add(source)
    # tradition種別のHistoryが無い → 該当質問はfacts=0件。

    result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="どんな伝承がありますか？"
    )

    assert result.answer == ""
    assert result.facts_used == []
    assert result.sources_used == []
    assert result.unanswered_aspects == ["tradition"]
    assert result.limitations is not None
    assert result.llm_used is False


def test_unclassifiable_question_never_constructs_llm_client(monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("何でも神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="今日の天気はどうですか？"
    )

    assert result.facts_used == []
    assert result.llm_used is False


def test_suppressed_low_confidence_facts_short_circuit_without_llm_call(monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("低確信度のみ神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "低確信度の神", confidence="low")
    history = _create_history(shrine, "由緒", confidence="high")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    # confidence="low"(reason_strength="suppressed")のFactはgeneration対象外。
    assert result.facts_used == []
    assert result.sources_used == []
    assert result.llm_used is False


# --- Full Ready: LLMが1回だけ呼ばれ、provenanceはmechanicalに導出される ---


def test_full_ready_calls_llm_once_and_derives_provenance_mechanically(monkeypatch):
    fake_client = _FakeLLMClient(content="明治天皇と昭憲皇太后をお祀りしています。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("明治神宮相当")
    source = _create_source("公式サイト「明治神宮とは」")
    deity1 = _create_deity(shrine, "明治天皇", sort_order=0)
    deity2 = _create_deity(shrine, "昭憲皇太后", sort_order=1)
    history = _create_history(shrine, "明治神宮の創建")
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="この神社は誰を祀っていますか？"
    )

    assert len(fake_client.calls) == 1
    assert result.llm_used is True
    assert result.answer == "明治天皇と昭憲皇太后をお祀りしています。"
    assert result.readiness == "full"
    assert {f.id for f in result.facts_used} == {deity1.id, deity2.id}
    assert all(f.type == "deity" for f in result.facts_used)
    assert {s.id for s in result.sources_used} == {source.id}
    assert result.limitations is None
    assert result.unanswered_aspects == []


def test_llm_output_is_not_parsed_for_provenance(monkeypatch):
    """factsに言及していないLLM出力でも、facts_usedはretrieval結果のまま変わらない。"""
    fake_client = _FakeLLMClient(content="（何も言及しない適当な文章）")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("provenance非依存神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.answer == "（何も言及しない適当な文章）"
    assert {f.id for f in result.facts_used} == {deity.id}
    assert {s.id for s in result.sources_used} == {source.id}


# --- Limited: 取得できたFactのみ回答し、推測で埋めない ---


def test_limited_shrine_prompt_marks_weakened_and_does_not_guess_missing_parts(monkeypatch):
    fake_client = _FakeLLMClient(content="確認できる範囲でお答えします。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("給田六所神社相当")
    source = _create_source("公式")
    deity1 = _create_deity(shrine, "大国魂大神", confidence="medium")
    deity2 = _create_deity(shrine, "天照皇大神", confidence="medium", sort_order=1)
    history = _create_history(shrine, "神明社の合祀", confidence="medium", history_type="historical_event")
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "limited"
    assert len(fake_client.calls) == 1
    user_message = fake_client.calls[0][1]["content"]
    # medium confidence → reason_strength="weakened"であることをpromptに明示する。
    assert "weakened" in user_message
    assert "assertive" not in user_message
    assert {f.id for f in result.facts_used} == {deity1.id, deity2.id}
    assert result.limitations is not None
    assert "限られており" in result.limitations


def test_full_ready_shrine_with_partial_facts_reports_unanswered_aspects(monkeypatch):
    """Full Ready神社でも、対応するFactが無い質問typeはunanswered_aspectsへ残る。"""
    fake_client = _FakeLLMClient(content="創建の経緯についてお答えします。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("複合質問神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    for fact in (deity, founding):
        fact.sources.add(source)
    # tradition種別のHistoryは無い。

    result = generate_deep_dive_answer(
        shrine_id=shrine.id,
        question_text="なぜ創建されたのですか？また、どんな伝承がありますか？",
    )

    assert result.llm_used is True
    assert {f.id for f in result.facts_used} == {founding.id}
    assert result.unanswered_aspects == ["tradition"]


# --- LLM Failure/Disabled(PR-ND2): Factを捏造せず、deterministic builder
# (PR-ND1)からretrieval済みFactに基づく実際の回答を構成する。既存の
# _LLM_FAILURE_MESSAGEは、deterministic builderも構成できない場合のみに
# 使われる最終fallbackへ後退する(意図的なcontract変更、
# docs/audit/deep-dive-non-llm-runtime-alignment.md §8.3)。 ---


def test_1_llm_disabled_full_ready_returns_deterministic_answer_not_fixed_message(settings):
    """1. LLM disabled Full"""
    settings.CONCIERGE_USE_LLM = False
    shrine = _create_shrine("LLM無効Full神社")
    source = _create_source("公式")
    deity1 = _create_deity(shrine, "明治天皇", sort_order=0)
    deity2 = _create_deity(shrine, "昭憲皇太后", sort_order=1)
    history = _create_history(shrine, "由緒")
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "full"
    assert result.llm_used is False
    assert result.answer == "明治天皇・昭憲皇太后をお祀りしています。"
    assert result.answer != deep_dive_answer._LLM_FAILURE_MESSAGE
    assert {f.id for f in result.facts_used} == {deity1.id, deity2.id}


def test_2_llm_disabled_limited_ready_returns_deterministic_answer_with_weakened_wording(settings):
    """2. LLM disabled Limited"""
    settings.CONCIERGE_USE_LLM = False
    shrine = _create_shrine("LLM無効Limited神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "大国魂大神", confidence="medium")
    history = _create_history(shrine, "由緒", confidence="medium")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "limited"
    assert result.llm_used is False
    assert result.answer == "大国魂大神をお祀りしていると伝わっています。"
    assert result.answer != deep_dive_answer._LLM_FAILURE_MESSAGE
    assert result.limitations is not None
    assert "限られており" in result.limitations


def test_3_llm_failure_full_ready_returns_deterministic_answer_with_retrieved_facts_preserved(
    monkeypatch,
):
    """3. LLM failure Full"""
    fake_client = _FakeLLMClient(raise_exc=RuntimeError("network down"))
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("LLM失敗Full神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "full"
    assert result.llm_used is False
    assert result.answer == "神をお祀りしています。"
    assert result.answer != deep_dive_answer._LLM_FAILURE_MESSAGE
    # facts_used/sources_usedはretrieval済みの安全な情報としてそのまま返す(捏造しない)。
    assert {f.id for f in result.facts_used} == {deity.id}
    assert {s.id for s in result.sources_used} == {source.id}


def test_4_llm_failure_limited_ready_returns_deterministic_answer_with_limitations(monkeypatch):
    """4. LLM failure Limited"""
    fake_client = _FakeLLMClient(raise_exc=RuntimeError("network down"))
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("LLM失敗Limited神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "大国魂大神", confidence="medium")
    history = _create_history(shrine, "由緒", confidence="medium")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.readiness == "limited"
    assert result.llm_used is False
    assert result.answer == "大国魂大神をお祀りしていると伝わっています。"
    assert result.limitations is not None
    assert "限られており" in result.limitations


# --- 7. sources provenance維持 / 8. limitations維持: answerの生成元
# (LLM成功/deterministic fallback/最終fallback)に関わらずfacts_used/
# sources_used/limitationsは不変。 ---


def test_7_sources_provenance_unchanged_between_llm_success_and_deterministic_fallback(
    monkeypatch,
):
    """7. sources provenance維持"""
    shrine = _create_shrine("Provenance比較神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    fake_client = _FakeLLMClient(content="LLM生成の回答文。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)
    llm_success_result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )

    fallback_client = _FakeLLMClient(raise_exc=RuntimeError("down"))
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fallback_client)
    fallback_result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )

    assert llm_success_result.answer == "LLM生成の回答文。"
    assert fallback_result.answer == "神をお祀りしています。"
    assert llm_success_result.answer != fallback_result.answer
    # answerの生成元が違っても、provenanceは完全に一致する。
    assert {f.id for f in llm_success_result.facts_used} == {
        f.id for f in fallback_result.facts_used
    }
    assert {s.id for s in llm_success_result.sources_used} == {
        s.id for s in fallback_result.sources_used
    }


def test_8_limitations_unchanged_between_llm_success_and_deterministic_fallback(monkeypatch):
    """8. limitations維持"""
    shrine = _create_shrine("Limitations比較神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神", confidence="medium")
    history = _create_history(shrine, "由緒", confidence="medium")
    for fact in (deity, history):
        fact.sources.add(source)

    fake_client = _FakeLLMClient(content="LLM生成の回答文。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)
    llm_success_result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )

    fallback_client = _FakeLLMClient(raise_exc=RuntimeError("down"))
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fallback_client)
    fallback_result = generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )

    assert llm_success_result.limitations == fallback_result.limitations
    assert llm_success_result.limitations is not None
    assert "限られており" in llm_success_result.limitations


# --- 9. LLM success regression: LLM経路は削除されておらず、成功時は
# 引き続きLLM出力がそのままanswerになる(Option C、既存挙動の非破壊)。 ---


def test_9_llm_success_path_is_not_deleted_llm_output_still_used_when_available(monkeypatch):
    """9. LLM success regression"""
    fake_client = _FakeLLMClient(content="LLMによる自然な回答文。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("LLM成功神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert len(fake_client.calls) == 1
    assert result.llm_used is True
    # LLMが成功した場合、deterministic answer("神をお祀りしています。")では
    # なく、LLM出力がそのままanswerになる(deterministic builderが
    # LLM成功pathを上書きしない)。
    assert result.answer == "LLMによる自然な回答文。"


# --- 10. deterministic builder None: PR-ND1が対応しないquestion_type
# (source_basis)では、deterministic builderもNoneを返すため、最終的に
# 既存の_LLM_FAILURE_MESSAGEへfall backする(Final Safe Fallback)。 ---


def test_10_deterministic_builder_none_falls_back_to_fixed_failure_message(settings):
    """10. deterministic builder None"""
    settings.CONCIERGE_USE_LLM = False
    shrine = _create_shrine("根拠質問LLM無効神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    from temples.services.deep_dive_retrieval import build_deep_dive_context

    first_context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    # source_basisはPR-ND1のbuild_deterministic_answer()が対応しない
    # question_type(deep_dive_deterministic_answer.pyのdocstring参照)。
    result = generate_deep_dive_answer(
        shrine_id=shrine.id,
        question_text="その根拠は何ですか？",
        prior_facts=first_context.facts,
    )

    assert result.llm_used is False
    assert result.answer == deep_dive_answer._LLM_FAILURE_MESSAGE
    # facts_used/sources_usedは、最終fallback時も安全な情報としてそのまま返る。
    assert result.facts_used


# --- 11. no hallucinated content: deterministic fallbackのanswerは、
# build_deterministic_answer()を直接呼んだ場合と完全に一致する(Fact本文の
# 引用・連結以外の文章が混入していない)。 ---


def test_11_deterministic_fallback_answer_contains_no_content_beyond_the_facts(settings):
    """11. no hallucinated content"""
    settings.CONCIERGE_USE_LLM = False
    shrine = _create_shrine("捏造なし確認神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "特定の神名")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)

    from temples.services.deep_dive_deterministic_answer import build_deterministic_answer
    from temples.services.deep_dive_retrieval import build_deep_dive_context

    context = build_deep_dive_context(shrine_id=shrine.id, question_text="誰を祀っていますか？")
    expected = build_deterministic_answer(question_type="deity_who", facts=context.facts)

    result = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")

    assert result.answer == expected
    assert result.answer == "特定の神名をお祀りしています。"
    # Fact(display_name)に無い固有名詞が混入していないことを確認する。
    assert "一般的" not in result.answer
    assert "神道" not in result.answer


# --- Regression: PR #2450のRetrieval Foundationは変更しない ---


def test_source_basis_followup_reuses_prior_facts_without_new_retrieval(monkeypatch):
    fake_client = _FakeLLMClient(content="公式サイトの記載を根拠にしています。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("根拠質問神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source)
    history = _create_history(shrine, "由緒")
    history.sources.add(source)

    first = generate_deep_dive_answer(shrine_id=shrine.id, question_text="誰を祀っていますか？")
    assert first.facts_used

    from temples.services.deep_dive_retrieval import build_deep_dive_context

    first_context = build_deep_dive_context(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )
    followup = generate_deep_dive_answer(
        shrine_id=shrine.id,
        question_text="その根拠は何ですか？",
        prior_facts=first_context.facts,
    )

    assert followup.llm_used is True
    assert {f.id for f in followup.facts_used} == {f.id for f in first_context.facts}
    assert {s.id for s in followup.sources_used} == {source.id}
