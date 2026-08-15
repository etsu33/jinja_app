"""Deep Dive Answer Generation (PR-B3 + PR-B4)。

docs/product/deep-dive-answer-generation-contract.md の実装。
temples.services.deep_dive_retrieval（PR-B1・PR-B2・#2450でmerge済み）を
唯一のFact取得経路とし、そのretrieval結果のみを根拠にLLMへ回答文を生成させる
（closed-book、§6・§8ステップ6-7）。

**LLMはKnowledge Retrieverではない**: LLMへ渡すShrine固有情報は
build_deep_dive_context()が返したusable factsのみであり、LLMにDB再検索・
Fact選択・Source選択・readiness判定・一般知識によるFact補完のいずれも
させない。質問分類・Fact取得・Evidence filtering・readiness判定は
deep_dive_retrieval.py側で既にdeterministicに確定済みであり、本モジュールは
それを変更しない。

**Call Gate（最重要のsafety layer、§6・§8ステップ6）**: 以下の場合、LLMを
一切呼び出さない。
  - readiness == "not_ready"
  - usable factsが0件（confidence="low"→"suppressed"によりgeneration対象外に
    なった結果0件になる場合を含む）
呼び出し自体をしないことで、grounded answerを構成できない状態でLLMが
何かを生成してしまうリスクを構造的に排除する
（temples.services.deep_dive_retrievalのZero-Fact Short Circuitと同じ設計思想）。

**Provenance（§9）**: facts_used/sources_usedは、LLMのテキスト出力から抽出
しない。build_deep_dive_context()がretrieval時に確定したFact/Sourceの集合
から機械的に導出する。LLMへ渡したFactの集合＝facts_usedであり、closed-book
promptなので後から集合が変化することもない。

**LLM統合方式**: 既存のtemples.llm.client.LLMClient / settings.CONCIERGE_USE_LLM
feature-flagパターン（temples/services/concierge_chat_llm_route.pyが確立した
パターン）をそのまま再利用する。新規のLLM統合方式・新規feature flagは発明しない。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from temples.llm.client import PLACEHOLDER, LLMClient
from temples.services import evidence_gate
from temples.services.deep_dive_retrieval import (
    DeepDiveFact,
    DeepDiveSource,
    build_deep_dive_context,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output Contract (docs/product/deep-dive-answer-generation-contract.md §10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeepDiveFactUsed:
    """Output Contractの facts_used 1件。

    LLM出力からではなく、retrieval時に確定したFact集合(DeepDiveFact)から
    機械的に導出する(§9)。verification_status/confidence/content等の内部
    fieldはOutput Contractの対象外のため保持しない。
    """

    type: str
    id: int
    label: str


@dataclass(frozen=True)
class DeepDiveAnswer:
    """docs/product/deep-dive-answer-generation-contract.md §10 Output Contract。

    question_typeは§10の元表には無いが、build_deep_dive_context()が既に
    確定させているclassification結果であり、API層(PR-B5)がこれを再分類せずに
    そのまま公開できるよう、ここでpass throughする(§3の分類結果そのもの、
    複合質問の場合は複数要素を持つlist)。
    """

    answer: str
    readiness: str
    question_type: list[str]
    facts_used: list[DeepDiveFactUsed]
    sources_used: list[DeepDiveSource]
    limitations: Optional[str]
    unanswered_aspects: list[str]
    # Output Contract §10の「最低限」フィールドには含まれない、observability専用の値。
    # LLMが実際に呼ばれ、その出力がそのままanswerに使われたかどうかを示す
    # (呼ばれなかった/失敗した場合はFalse。テストでのCall Gate検証に使う)。
    llm_used: bool


# ---------------------------------------------------------------------------
# No-Hallucination Contract (§6): confidence="low"→reason_strength="suppressed"の
# Factはgeneration対象から除外する。deep_dive_retrieval.py自体はconfidenceで
# フィルタしない設計(usable判定はverification_statusのみ、§5)であり、
# suppressed除外はAnswer Generation層の責務としてここで行う。
# ---------------------------------------------------------------------------

_SUPPRESSED_REASON_STRENGTH = "suppressed"


def _usable_for_generation(facts: Iterable[DeepDiveFact]) -> list[DeepDiveFact]:
    return [f for f in facts if f.reason_strength != _SUPPRESSED_REASON_STRENGTH]


# ---------------------------------------------------------------------------
# Closed-book prompt (§6・§8ステップ7)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "あなたは神社の詳細情報について、与えられたFactのみを根拠に回答するアシスタントです。"
    "以下を厳密に守ってください。\n"
    "- 与えられたFact以外の情報を、神社固有の事実として述べない。\n"
    "- Fact間に明示されていない因果関係を推測して繋げない。\n"
    "- 一般的な神道知識・他の神社との比較・あなたが妥当と判断した推測を、"
    "この神社のFactとして混ぜない。\n"
    "- reason_strengthが「weakened」のFactは、断定調ではなく「〜と伝わる」"
    "「〜とされる」のように弱めた表現で述べる。\n"
    "- reason_strengthが「assertive」のFactは断定調で述べてよい。\n"
    "- 尋ねられた内容に対応するFactが無い場合、無理に埋めず、確認できない旨を述べる。\n"
    "- 出力は回答本文の自然文のみとし、前置き・見出し・断り書きを含めない。"
)


def _build_user_prompt(question_text: str, facts: list[DeepDiveFact]) -> str:
    fact_lines = "\n".join(
        f"- [{fact.label}] {fact.content}（reason_strength: {fact.reason_strength}）"
        for fact in facts
    )
    return f"質問: {question_text}\n\n利用できるFact（これ以外の情報は使わない）:\n{fact_lines}"


def _call_llm(question_text: str, facts: list[DeepDiveFact]) -> Optional[str]:
    """Closed-book生成を1回呼び出す。使えない/失敗した場合はNoneを返す(fabricateしない)。"""
    client = LLMClient()
    if getattr(client, "_client", None) is None or getattr(client, "_mode", None) is None:
        return None

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(question_text, facts)},
    ]

    try:
        msg = client.chat(messages)
    except Exception as exc:
        log.warning(
            "[deep_dive_answer] LLM call raised error_class=%s", type(exc).__name__
        )
        return None

    content = msg.get("content") if isinstance(msg, dict) else None
    if not content or content == PLACEHOLDER["content"]:
        return None
    return content.strip() or None


# ---------------------------------------------------------------------------
# Failure Modes (§12)
# ---------------------------------------------------------------------------

_LLM_FAILURE_MESSAGE = (
    "現在、回答の生成に失敗しました。時間をおいて再度お試しください。"
)


def _facts_used_from(facts: Iterable[DeepDiveFact]) -> list[DeepDiveFactUsed]:
    return [DeepDiveFactUsed(type=f.type, id=f.id, label=f.label) for f in facts]


def _sources_used_for(
    facts: list[DeepDiveFact], all_sources: list[DeepDiveSource]
) -> list[DeepDiveSource]:
    """facts(generation対象に絞り込み済み)のsource_idsに限定してsourcesを絞る(§9)。"""
    source_ids: set[int] = set()
    for fact in facts:
        source_ids.update(fact.source_ids)
    return [source for source in all_sources if source.id in source_ids]


def _empty_answer(readiness: str, limitations: Optional[str]) -> DeepDiveAnswer:
    return DeepDiveAnswer(
        answer="",
        readiness=readiness,
        question_type=[],
        facts_used=[],
        sources_used=[],
        limitations=limitations,
        unanswered_aspects=[],
        llm_used=False,
    )


# ---------------------------------------------------------------------------
# Entry point (§8)
# ---------------------------------------------------------------------------


def generate_deep_dive_answer(
    *,
    shrine_id: int,
    question_text: Optional[str],
    prior_facts: Optional[Iterable[DeepDiveFact]] = None,
) -> DeepDiveAnswer:
    """Deep Dive Answer Generationの全体pipeline(§8ステップ1-9)を1回実行する。

    Guard(§8ステップ2)・質問分類・Fact取得・Evidence filtering・provenanceは
    build_deep_dive_context()(既存Retrieval Foundation、PR #2450)にそのまま
    委譲し、本関数はLLM呼び出しの要否判定(Call Gate)とclosed-book生成のみを
    追加する。readiness判定・Fact取得ロジック自体はここで再実装しない。
    """
    context = build_deep_dive_context(
        shrine_id=shrine_id, question_text=question_text, prior_facts=prior_facts
    )

    if context.readiness == evidence_gate.DEEP_DIVE_NOT_READY:
        # Not Ready: Retrieval Foundation側で既にfacts取得を行っていない
        # (defense in depth)。ここでもLLMは呼び出さない。
        return _empty_answer(context.readiness, context.limitations)

    generation_facts = _usable_for_generation(context.facts)

    if not generation_facts:
        # Zero-Fact Short Circuit(§6・§8ステップ6a)。context.factsが0件の場合と、
        # confidence="low"(suppressed)のみで実質使えるFactが無い場合の両方を含む。
        unanswered = context.unanswered_aspects or context.question_type
        limitations = context.limitations
        return DeepDiveAnswer(
            answer="",
            readiness=context.readiness,
            question_type=context.question_type,
            facts_used=[],
            sources_used=[],
            limitations=limitations,
            unanswered_aspects=unanswered,
            llm_used=False,
        )

    answer_text = _call_llm(question_text or "", generation_facts)

    facts_used = _facts_used_from(generation_facts)
    sources_used = _sources_used_for(generation_facts, context.sources)

    if answer_text is None:
        # LLM未使用/失敗: Factを捏造したfallback文章は作らない。retrieval済みの
        # facts_used/sources_used(mechanicalに確定済み、safeな情報)はそのまま返し、
        # answerのみ固定のdeterministicな失敗文言にする(§12)。
        return DeepDiveAnswer(
            answer=_LLM_FAILURE_MESSAGE,
            readiness=context.readiness,
            question_type=context.question_type,
            facts_used=facts_used,
            sources_used=sources_used,
            limitations=context.limitations,
            unanswered_aspects=context.unanswered_aspects,
            llm_used=False,
        )

    return DeepDiveAnswer(
        answer=answer_text,
        readiness=context.readiness,
        question_type=context.question_type,
        facts_used=facts_used,
        sources_used=sources_used,
        limitations=context.limitations,
        unanswered_aspects=context.unanswered_aspects,
        llm_used=True,
    )


__all__ = [
    "DeepDiveFactUsed",
    "DeepDiveAnswer",
    "generate_deep_dive_answer",
]
