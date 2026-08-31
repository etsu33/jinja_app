# backend/temples/services/consultation_meaning.py
"""Consultation Meaning v1 -- stable Structured Consultation Context.

Extracts `StructuredConsultationContextV1` from `free_text` only. This is a
deliberately independent module from `consultation_interpreter.py`: the
legacy `InterpretationProfile` (state_profile / emotion_profile /
direction_profile / action_intent / decision_context / constraint_profile /
outcome_hint) stays debug-only and is NOT a source of truth for this
contract, and this module does not import from or call into it. See
docs/audit (need_tag Responsibility Audit, InterpretationProfile
Re-evaluation, PR-C Stable API Contract & Implementation Scope) for the
full design history behind this boundary.

Contract (fixed, approved by Mother Ship -- do not loosen):
- Extraction reads `free_text` only. It never reads need_tag,
  matched_need_tags, Recommendation results, Ranking output, shrine data,
  or any legacy InterpretationProfile field, and never derives a signal
  backward from any of those.
- A signal is emitted only when a contiguous literal substring of
  `free_text` satisfies that signal type's positive expression. Evidence
  is mandatory -- there is no signal without a literal span.
- Negated, third-person, reported-speech, topic-only, ambiguous/homonym,
  or delegated-desire expressions produce no signal. Double negation is
  fail-safe No-signal (never resolved back to an affirmative reading).
- No primary/secondary ranking, no confidence score, no psychological
  inference (tone/intensity/personality) anywhere in this module.
- The same signal type appears at most once per family; multiple valid
  evidence spans for that type are aggregated into its `evidence` array.
- One evidence span is never reused as the basis for more than one
  signal (the taxonomy's positive-expression vocabularies are disjoint by
  design -- see the Consultation Meaning Signal Taxonomy v1 audit).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Pattern

# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsultationMeaningEvidence:
    text: str

    def as_dict(self) -> dict:
        return {"text": self.text}


@dataclass(frozen=True)
class SituationSignal:
    type: str
    evidence: List[ConsultationMeaningEvidence]

    def as_dict(self) -> dict:
        return {"type": self.type, "evidence": [e.as_dict() for e in self.evidence]}


@dataclass(frozen=True)
class DesiredOutcomeSignal:
    type: str
    evidence: List[ConsultationMeaningEvidence]

    def as_dict(self) -> dict:
        return {"type": self.type, "evidence": [e.as_dict() for e in self.evidence]}


@dataclass(frozen=True)
class ExplicitConstraintSignal:
    type: str
    evidence: List[ConsultationMeaningEvidence]

    def as_dict(self) -> dict:
        return {"type": self.type, "evidence": [e.as_dict() for e in self.evidence]}


@dataclass(frozen=True)
class StructuredConsultationContextV1:
    situation_signals: List[SituationSignal] = field(default_factory=list)
    desired_outcome_signals: List[DesiredOutcomeSignal] = field(default_factory=list)
    explicit_constraint_signals: List[ExplicitConstraintSignal] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "situation_signals": [s.as_dict() for s in self.situation_signals],
            "desired_outcome_signals": [s.as_dict() for s in self.desired_outcome_signals],
            "explicit_constraint_signals": [s.as_dict() for s in self.explicit_constraint_signals],
        }


# ---------------------------------------------------------------------------
# Shared guards (apply across all three families)
# ---------------------------------------------------------------------------

# Clause boundary: split on sentence/clause punctuation only. A negation or
# third-person marker on one side of a boundary must never suppress a
# signal on the other side (see docs: "疲れてはいないが、迷っている" must
# still produce undecided).
_CLAUSE_SPLIT_PATTERN = re.compile(r"[、。！？!?\n]+")

# Negation phrases, checked anywhere within the same clause as a positive
# match. Deliberately specific phrases, not a bare "ない" check -- several
# positive patterns (e.g. stalled's "動けない") lexically contain "ない" as
# part of their own meaning, not as a negation of it.
_NEGATION_PATTERNS: List[Pattern[str]] = [
    re.compile(r"わけではない"),
    re.compile(r"とは言えない"),
    re.compile(r"ではない"),
    re.compile(r"はいない"),
    re.compile(r"していない"),
    re.compile(r"つもりはない"),
    re.compile(r"必要はない"),
    re.compile(r"なかった"),
    re.compile(r"たくない"),
]

# Third-person subject markers. Checked for presence anywhere before the
# positive match within the same clause.
_THIRD_PERSON_MARKERS = (
    "彼が",
    "彼女が",
    "友人が",
    "友達が",
    "相手が",
    "家族が",
    "同僚が",
    "上司が",
    "みんなが",
    "誰かが",
    "知人が",
)

# Reported-speech markers. Checked for presence anywhere within the clause.
_REPORTED_SPEECH_PATTERNS: List[Pattern[str]] = [
    re.compile(r"と言っていた"),
    re.compile(r"だそうだ"),
    re.compile(r"らしい"),
    re.compile(r"と聞いた"),
    re.compile(r"とのことだ"),
]

# Delegated-desire guard (decide only, defense-in-depth -- the positive
# pattern already requires the desiderative "たい" form, which does not
# match "てほしい"/"てもらいたい" delegation phrasing by construction).
_DELEGATION_PATTERNS: List[Pattern[str]] = [
    re.compile(r"てほしい"),
    re.compile(r"てもらいたい"),
]

# clarify homonym guard: "整理したい" can mean tidying a physical space
# rather than organizing thoughts/feelings. Suppressed when a physical-
# object context word appears in the same clause.
_CLARIFY_PHYSICAL_CONTEXT = ("部屋", "机", "クローゼット", "荷物", "デスク", "本棚")


def _split_clauses(free_text: str) -> List[str]:
    return [c for c in _CLAUSE_SPLIT_PATTERN.split(free_text) if c]


def _has_negation(clause: str) -> bool:
    return any(p.search(clause) for p in _NEGATION_PATTERNS)


def _has_third_person_subject(clause: str, match_start: int) -> bool:
    prefix = clause[:match_start]
    return any(marker in prefix for marker in _THIRD_PERSON_MARKERS)


def _has_reported_speech(clause: str) -> bool:
    return any(p.search(clause) for p in _REPORTED_SPEECH_PATTERNS)


def _has_delegation(clause: str) -> bool:
    return any(p.search(clause) for p in _DELEGATION_PATTERNS)


def _clause_is_safe(clause: str, match_start: int) -> bool:
    """Shared guard: negation / third-person / reported-speech all suppress."""
    if _has_negation(clause):
        return False
    if _has_third_person_subject(clause, match_start):
        return False
    if _has_reported_speech(clause):
        return False
    return True


# ---------------------------------------------------------------------------
# Per-type positive expression patterns
# ---------------------------------------------------------------------------

_SITUATION_PATTERNS: dict = {
    "depleted": [
        re.compile(r"疲れ(ている|ていた|て|きった)"),
        re.compile(r"疲労(が溜まっている|がたまっている)"),
        re.compile(r"しんどい"),
        re.compile(r"体力がない"),
    ],
    "undecided": [
        re.compile(r"迷って(いる|いて|いた)"),
        re.compile(r"決められない"),
        re.compile(r"どちらか選べない"),
    ],
    "stalled": [
        re.compile(r"動けない"),
        re.compile(r"進まない"),
        re.compile(r"停滞して(いる|いて|いた)"),
        re.compile(r"詰まって(いる|いて|いた)"),
    ],
}

_DESIRED_OUTCOME_PATTERNS: dict = {
    "decide": [
        re.compile(r"決めたい"),
        re.compile(r"決断したい"),
        re.compile(r"選びたい"),
    ],
    "clarify": [
        re.compile(r"整理したい"),
        re.compile(r"考えたい"),
        re.compile(r"見直したい"),
    ],
    "progress": [
        re.compile(r"前に進みたい"),
        re.compile(r"一歩踏み出したい"),
        re.compile(r"踏み出したい"),
        re.compile(r"始めたい"),
    ],
    "calm": [
        re.compile(r"落ち着きたい"),
        re.compile(r"安心したい"),
    ],
}

_EXPLICIT_CONSTRAINT_PATTERNS: dict = {
    "time": [
        re.compile(r"時間が(ない|足りない|足りなくて)"),
        re.compile(r"余裕が(ない|なくて)"),
    ],
    "money": [
        re.compile(r"お金が(ない|なくて|足りない|足りなくて|足りず)"),
        re.compile(r"(収入|生活費|資金)が(足りない|足りなくて|足りず|なく)"),
    ],
    "other_person_availability": [
        re.compile(
            r"(相手|家族|パートナー|上司).{0,2}(都合|事情)で.{0,10}(動けない|決められない|進められない)"
        ),
    ],
}


# ---------------------------------------------------------------------------
# Family extractors
# ---------------------------------------------------------------------------


def _extract_family(
    free_text: str,
    patterns_by_type: dict,
    *,
    extra_guard=None,
) -> dict:
    """Shared extraction loop: clause-by-clause, type-by-type, pattern-by-pattern.

    Returns {type: [ConsultationMeaningEvidence, ...]} for types with at
    least one valid (non-suppressed) match. Duplicate literal spans for the
    same type are not repeated.
    """
    clauses = _split_clauses(free_text)
    hits: dict = {}

    for clause in clauses:
        for sig_type, patterns in patterns_by_type.items():
            for pattern in patterns:
                m = pattern.search(clause)
                if not m:
                    continue
                if not _clause_is_safe(clause, m.start()):
                    continue
                if extra_guard is not None and not extra_guard(sig_type, clause, m):
                    continue

                span_text = m.group(0)
                existing = hits.setdefault(sig_type, [])
                if span_text not in [e.text for e in existing]:
                    existing.append(ConsultationMeaningEvidence(text=span_text))

    return hits


def _situation_guard(sig_type: str, clause: str, match: re.Match) -> bool:
    return True


def _desired_outcome_guard(sig_type: str, clause: str, match: re.Match) -> bool:
    if sig_type == "decide" and _has_delegation(clause):
        return False
    if sig_type == "clarify" and any(word in clause for word in _CLARIFY_PHYSICAL_CONTEXT):
        return False
    return True


def _explicit_constraint_guard(sig_type: str, clause: str, match: re.Match) -> bool:
    return True


def extract_consultation_meaning(free_text: str) -> StructuredConsultationContextV1:
    """Extracts StructuredConsultationContextV1 from free_text only.

    Accepts only `free_text`. Never reads need_tags, Recommendation
    results, Ranking output, shrine data, or legacy InterpretationProfile
    fields -- none of those are parameters here by design.
    """
    text = str(free_text or "").strip()
    if not text:
        return StructuredConsultationContextV1()

    situation_hits = _extract_family(text, _SITUATION_PATTERNS, extra_guard=_situation_guard)
    outcome_hits = _extract_family(
        text, _DESIRED_OUTCOME_PATTERNS, extra_guard=_desired_outcome_guard
    )
    constraint_hits = _extract_family(
        text, _EXPLICIT_CONSTRAINT_PATTERNS, extra_guard=_explicit_constraint_guard
    )

    return StructuredConsultationContextV1(
        situation_signals=[
            SituationSignal(type=t, evidence=ev) for t, ev in situation_hits.items()
        ],
        desired_outcome_signals=[
            DesiredOutcomeSignal(type=t, evidence=ev) for t, ev in outcome_hits.items()
        ],
        explicit_constraint_signals=[
            ExplicitConstraintSignal(type=t, evidence=ev) for t, ev in constraint_hits.items()
        ],
    )


__all__ = [
    "ConsultationMeaningEvidence",
    "SituationSignal",
    "DesiredOutcomeSignal",
    "ExplicitConstraintSignal",
    "StructuredConsultationContextV1",
    "extract_consultation_meaning",
]
