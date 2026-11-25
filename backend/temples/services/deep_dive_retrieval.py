"""Deep Dive Backend Retrieval Foundation.

docs/product/deep-dive-answer-generation-contract.md の実装。同書のPR-B1
（Question Classification）・PR-B2（Fact Retrieval + Evidence Filtering）・
PR-B4（Provenance + Output Contract）に相当する。PR-B3（LLMによるanswer
generation）は本モジュールの対象外であり、本モジュールはLLMを一切呼び出さない。

安全性の核心はLLMの判断に依存しないことである。retrieved usable factが0件の
場合、grounded answerを生成せずlimitations/unanswered_aspectsを返す
（Zero-Fact Short Circuit、docs/product/deep-dive-answer-generation-contract.md
§6・§8）。質問分類（classify_question）もdeterministicなキーワード一致のみで
行い、LLMを使わない。

Recommendation Authority（Ranking, Candidate filtering, Signal Authority,
Reason生成）へは一切接続しない。Readiness判定・Evidence Gate判定は既存の
docs/knowledge/shrine-knowledge-contract.md契約とtemples.services.evidence_gate
をそのまま再利用し、独自のverification/confidence判定を新設しない。
confidence→reason_strengthの変換値は、temples.services.recommendation_reason_v4.py
がすでに確立している変換（high/medium/low → assertive/weakened/suppressed、
history_type="tradition"のassertive floor）と同一の値を用いる（Recommendation
Authority領域である同ファイルはimportせず、値のみをここに複製する。
docs/product/deep-dive-answer-generation-contract.md §5）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from django.db.models import Prefetch
from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate

# ---------------------------------------------------------------------------
# Question Taxonomy (docs/product/deep-dive-answer-generation-contract.md §3)
# ---------------------------------------------------------------------------

QUESTION_TYPE_DEITY_WHO = "deity_who"
QUESTION_TYPE_DEITY_NATURE = "deity_nature"
QUESTION_TYPE_FOUNDING = "founding"
QUESTION_TYPE_HISTORICAL_EVENTS = "historical_events"
QUESTION_TYPE_TRADITION = "tradition"
QUESTION_TYPE_SOURCE_BASIS = "source_basis"
QUESTION_TYPE_OTHER = "other"

# question_type -> ShrineHistory.history_type（founding/historical_events/
# traditionのみHistoryを取得対象にする。deity_who/deity_nature/source_basis/
# otherはこの表を使わない、_retrieve_facts_for_question_type参照）。
_HISTORY_TYPES_BY_QUESTION_TYPE: dict[str, tuple[str, ...]] = {
    QUESTION_TYPE_FOUNDING: ("founding", "official_origin"),
    QUESTION_TYPE_HISTORICAL_EVENTS: ("historical_event", "regional_context", "editorial_summary"),
    QUESTION_TYPE_TRADITION: ("tradition",),
}

# 分類はdeterministicなキーワード一致のみで行う（LLMを使わない）。複合質問は
# 複数のquestion_typeを返してよい。いずれにも一致しない場合はOTHERとし、
# 推測でどれか1つへ寄せない（docs/product/deep-dive-answer-generation-contract.md §3・§12）。
_KEYWORDS_BY_QUESTION_TYPE: dict[str, tuple[str, ...]] = {
    QUESTION_TYPE_DEITY_WHO: ("誰を祀", "祭神は誰", "誰が祀られ", "祭神を教え"),
    QUESTION_TYPE_DEITY_NATURE: ("どんな神", "神様はどんな", "どういう神", "神様について"),
    QUESTION_TYPE_FOUNDING: ("創建", "なぜ建て", "由来", "起源"),
    QUESTION_TYPE_HISTORICAL_EVENTS: ("歴史", "出来事", "沿革"),
    QUESTION_TYPE_TRADITION: ("伝承", "言い伝え", "伝説"),
    QUESTION_TYPE_SOURCE_BASIS: ("根拠", "出典", "資料は", "情報源", "ソースは"),
}

_CLASSIFIABLE_QUESTION_TYPES = (
    QUESTION_TYPE_DEITY_WHO,
    QUESTION_TYPE_DEITY_NATURE,
    QUESTION_TYPE_FOUNDING,
    QUESTION_TYPE_HISTORICAL_EVENTS,
    QUESTION_TYPE_TRADITION,
    QUESTION_TYPE_SOURCE_BASIS,
)


def classify_question(question_text: Optional[str]) -> list[str]:
    """質問文をquestion_typeへ分類する（deterministic、LLMを使わない）。

    複合質問（例:「誰を祀っていて、なぜ創建されたのか」）は複数の
    question_typeを返す。いずれのキーワードにも一致しない場合は
    [QUESTION_TYPE_OTHER]を返す（推測でどれかへ寄せない）。
    """
    if not question_text:
        return [QUESTION_TYPE_OTHER]

    matched = [
        question_type
        for question_type in _CLASSIFIABLE_QUESTION_TYPES
        if any(keyword in question_text for keyword in _KEYWORDS_BY_QUESTION_TYPE[question_type])
    ]
    return matched if matched else [QUESTION_TYPE_OTHER]


# ---------------------------------------------------------------------------
# Output shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeepDiveFact:
    """取得されたFact 1件（既にEvidence Gateを通過済み）。"""

    type: str  # "deity" | "history"
    id: int
    question_type: str
    label: str  # deity: display_name / history: title
    content: str  # deity: canonical_name（無ければdisplay_name） / history: content
    verification_status: str
    confidence: str
    reason_strength: str
    source_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DeepDiveSource:
    """facts内のsource_idsから機械的に導出されたSource 1件。"""

    id: int
    title: str
    publisher: str
    source_type: str
    url: str


@dataclass(frozen=True)
class DeepDiveContext:
    """Retrieval Foundationの出力（Output Contract、LLM生成前）。

    "answer"文字列は含まない。LLMによるanswer生成（PR-B3、本書スコープ外）へ
    そのまま渡すためのcontextである。
    """

    readiness: str  # "full" | "limited" | "not_ready"
    question_type: list[str]
    facts: list[DeepDiveFact]
    sources: list[DeepDiveSource]
    limitations: Optional[str]
    unanswered_aspects: list[str]


# ---------------------------------------------------------------------------
# confidence -> reason_strength（既存recommendation_reason_v4.pyの値を複製、§5）
# ---------------------------------------------------------------------------

_CONFIDENCE_TO_REASON_STRENGTH: dict[str, str] = {
    "high": "assertive",
    "medium": "weakened",
    "low": "suppressed",
}

_TRADITION_HISTORY_TYPE = "tradition"


def _reason_strength_from_confidence(confidence: str) -> str:
    return _CONFIDENCE_TO_REASON_STRENGTH.get(confidence, "assertive")


def _apply_tradition_hedge_floor(reason_strength: str, history_type: Optional[str]) -> str:
    """history_type="tradition"のFactはassertiveを許さない（既存Authority契約と同じ規則）。"""
    if history_type == _TRADITION_HISTORY_TYPE and reason_strength == "assertive":
        return "weakened"
    return reason_strength


# ---------------------------------------------------------------------------
# Retrieval + Evidence filtering
# ---------------------------------------------------------------------------


def _fact_ready_sources_prefetch() -> Prefetch:
    return Prefetch(
        "sources",
        queryset=ShrineKnowledgeSource.objects.filter(
            verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES
        ),
    )


def _usable_deities(shrine_id: int) -> list[tuple[ShrineDeity, evidence_gate.EvidenceDecision]]:
    candidates = (
        ShrineDeity.objects.filter(
            shrine_id=shrine_id,
            verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
        )
        .order_by("sort_order", "id")
        .prefetch_related(_fact_ready_sources_prefetch())
    )
    result: list[tuple[ShrineDeity, evidence_gate.EvidenceDecision]] = []
    for deity in candidates:
        decision = evidence_gate.decide_fact_usability(
            verification_status=deity.verification_status,
            confidence=deity.confidence,
            source_verification_statuses=[s.verification_status for s in deity.sources.all()],
        )
        if decision.usable:
            result.append((deity, decision))
    return result


def _usable_histories(
    shrine_id: int, history_types: Optional[Iterable[str]] = None
) -> list[tuple[ShrineHistory, evidence_gate.EvidenceDecision]]:
    qs = ShrineHistory.objects.filter(
        shrine_id=shrine_id,
        verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
    )
    if history_types is not None:
        qs = qs.filter(history_type__in=list(history_types))
    candidates = qs.order_by("sort_order", "id").prefetch_related(_fact_ready_sources_prefetch())
    result: list[tuple[ShrineHistory, evidence_gate.EvidenceDecision]] = []
    for history in candidates:
        decision = evidence_gate.decide_fact_usability(
            verification_status=history.verification_status,
            confidence=history.confidence,
            source_verification_statuses=[s.verification_status for s in history.sources.all()],
        )
        if decision.usable:
            result.append((history, decision))
    return result


def _deity_to_fact(
    deity: ShrineDeity, decision: evidence_gate.EvidenceDecision, question_type: str
) -> DeepDiveFact:
    return DeepDiveFact(
        type="deity",
        id=deity.id,
        question_type=question_type,
        label=deity.display_name,
        content=deity.canonical_name or deity.display_name,
        verification_status=deity.verification_status,
        confidence=decision.confidence,
        reason_strength=_reason_strength_from_confidence(decision.confidence),
        source_ids=tuple(s.id for s in deity.sources.all()),
    )


def _history_to_fact(
    history: ShrineHistory, decision: evidence_gate.EvidenceDecision, question_type: str
) -> DeepDiveFact:
    reason_strength = _apply_tradition_hedge_floor(
        _reason_strength_from_confidence(decision.confidence), history.history_type
    )
    return DeepDiveFact(
        type="history",
        id=history.id,
        question_type=question_type,
        label=history.title,
        content=history.content,
        verification_status=history.verification_status,
        confidence=decision.confidence,
        reason_strength=reason_strength,
        source_ids=tuple(s.id for s in history.sources.all()),
    )


def get_shrine_deep_dive_readiness(shrine_id: int) -> str:
    """Shrine 1件のDeep Dive Readiness（"full" | "limited" | "not_ready"）。

    docs/audit/deep-dive-readiness-content-sufficiency.md §3.4・
    evidence_gate.decide_deep_dive_readiness()の実装。Recommendationや
    Shrine Detailのusable判定と同じEvidence Gate（decide_fact_usability）を
    再利用し、独自のverification/confidence判定は行わない。
    """
    deity_decisions = [decision for _, decision in _usable_deities(shrine_id)]
    history_decisions = [decision for _, decision in _usable_histories(shrine_id)]
    return evidence_gate.decide_deep_dive_readiness(
        deity_decisions=deity_decisions,
        history_decisions=history_decisions,
    )


def _retrieve_facts_for_question_type(shrine_id: int, question_type: str) -> list[DeepDiveFact]:
    """1つのquestion_typeに対応するKnowledgeを取得する（Retrieval Contract §4）。

    Frontendはこの判断を一切行わない。question_typeごとの取得対象Modelは
    固定されており、呼び出し側（build_deep_dive_context）が動的に変更する
    余地は無い。
    """
    if question_type == QUESTION_TYPE_DEITY_WHO:
        return [
            _deity_to_fact(deity, decision, question_type)
            for deity, decision in _usable_deities(shrine_id)
        ]

    if question_type == QUESTION_TYPE_DEITY_NATURE:
        # ShrineDeityにはrole/canonical_name以外の性質記述fieldが無いため、
        # 当該Shrineの全Historyも候補として渡す（Deityへの直接言及が無い
        # Historyを混ぜない判断はLLM生成側の責務、docs/product/
        # deep-dive-answer-generation-contract.md §3「deity_nature固有の注意」）。
        # 本Foundationは候補集合を渡すのみで、関連性の絞り込みは行わない。
        facts = [
            _deity_to_fact(deity, decision, question_type)
            for deity, decision in _usable_deities(shrine_id)
        ]
        facts += [
            _history_to_fact(history, decision, question_type)
            for history, decision in _usable_histories(shrine_id)
        ]
        return facts

    history_types = _HISTORY_TYPES_BY_QUESTION_TYPE.get(question_type)
    if history_types is not None:
        return [
            _history_to_fact(history, decision, question_type)
            for history, decision in _usable_histories(shrine_id, history_types=history_types)
        ]

    # QUESTION_TYPE_SOURCE_BASISはbuild_deep_dive_context側でprior_factsから
    # 導出する（新規Fact取得ではなく既存回答のprovenance参照、§3・§4）。
    # QUESTION_TYPE_OTHERは意図的に何も取得しない（一致するKnowledge種別が
    # 不明なまま推測で取得しない、§12）。
    return []


def _sources_from_facts(facts: Iterable[DeepDiveFact]) -> list[DeepDiveSource]:
    """factsのsource_idsから機械的にSourceを導出する（Provenance Contract §9）。

    LLM出力からfacts_used/sources_usedを逆生成しない。ここで確定した
    source_idsの集合が、そのままsources_used相当になる。
    """
    source_ids: set[int] = set()
    for fact in facts:
        source_ids.update(fact.source_ids)
    if not source_ids:
        return []
    sources = ShrineKnowledgeSource.objects.filter(id__in=source_ids).order_by("id")
    return [
        DeepDiveSource(
            id=source.id,
            title=source.title,
            publisher=source.publisher,
            source_type=source.source_type,
            url=source.url,
        )
        for source in sources
    ]


_UNAVAILABLE_MESSAGE = "現在確認できる資料では、詳しい情報を確認できません。"
_NOT_READY_MESSAGE = "この神社については、根拠付きで詳しくお答えできる情報がまだ十分ではありません。"
_LIMITED_PREFIX = "この神社について確認できる資料は限られており、確認できる範囲でお答えしています。"


def _build_limitations_message(readiness: str, unanswered_aspects: list[str]) -> Optional[str]:
    parts: list[str] = []
    if readiness == evidence_gate.DEEP_DIVE_LIMITED:
        parts.append(_LIMITED_PREFIX)
    if unanswered_aspects:
        parts.append(_UNAVAILABLE_MESSAGE)
    return "".join(parts) if parts else None


def build_deep_dive_context(
    *,
    shrine_id: int,
    question_text: Optional[str],
    prior_facts: Optional[Iterable[DeepDiveFact]] = None,
) -> DeepDiveContext:
    """Deep Dive Answer Generationの前段（Retrieval Foundation）を1回で実行する。

    LLM呼び出しは一切行わない（docs/product/deep-dive-answer-generation-contract.md
    のPR-B3はこの関数の対象外）。ここで返るcontextは、後続のLLM生成ステップへ
    そのまま渡すための入力であり、"answer"文字列は含まない。

    Zero-Fact Short Circuit: readinessが"not_ready"の場合、または取得された
    usable factが合計0件の場合、grounded answerを生成せずlimitations/
    unanswered_aspectsのみを返す。この判定はLLMの判断に依存しない
    （facts自体がそもそも構築されない、または空のまま返る）。
    """
    readiness = get_shrine_deep_dive_readiness(shrine_id)

    if readiness == evidence_gate.DEEP_DIVE_NOT_READY:
        # Not Readyの神社は、質問分類・Fact取得のいずれも行わない
        # (Defense in depth、docs/product/deep-dive-answer-generation-contract.md §8ステップ2)。
        return DeepDiveContext(
            readiness=readiness,
            question_type=[],
            facts=[],
            sources=[],
            limitations=_NOT_READY_MESSAGE,
            unanswered_aspects=[],
        )

    question_types = classify_question(question_text)

    facts: list[DeepDiveFact] = []
    seen_fact_keys: set[tuple[str, int]] = set()
    unanswered_aspects: list[str] = []

    for question_type in question_types:
        if question_type == QUESTION_TYPE_SOURCE_BASIS:
            type_facts = list(prior_facts or [])
        else:
            type_facts = _retrieve_facts_for_question_type(shrine_id, question_type)

        if not type_facts:
            unanswered_aspects.append(question_type)
            continue

        for fact in type_facts:
            key = (fact.type, fact.id)
            if key in seen_fact_keys:
                # 複合質問で複数question_typeが同じFactを指した場合、
                # 重複させずに1件のみ保持する（最初に一致したquestion_typeの
                # ラベルを使う）。
                continue
            seen_fact_keys.add(key)
            facts.append(fact)

    if not facts:
        return DeepDiveContext(
            readiness=readiness,
            question_type=question_types,
            facts=[],
            sources=[],
            limitations=_UNAVAILABLE_MESSAGE,
            unanswered_aspects=question_types,
        )

    sources = _sources_from_facts(facts)
    limitations = _build_limitations_message(readiness, unanswered_aspects)

    return DeepDiveContext(
        readiness=readiness,
        question_type=question_types,
        facts=facts,
        sources=sources,
        limitations=limitations,
        unanswered_aspects=unanswered_aspects,
    )


__all__ = [
    "QUESTION_TYPE_DEITY_WHO",
    "QUESTION_TYPE_DEITY_NATURE",
    "QUESTION_TYPE_FOUNDING",
    "QUESTION_TYPE_HISTORICAL_EVENTS",
    "QUESTION_TYPE_TRADITION",
    "QUESTION_TYPE_SOURCE_BASIS",
    "QUESTION_TYPE_OTHER",
    "DeepDiveFact",
    "DeepDiveSource",
    "DeepDiveContext",
    "classify_question",
    "get_shrine_deep_dive_readiness",
    "build_deep_dive_context",
]
