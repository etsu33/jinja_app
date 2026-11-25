"""見どころ（ShrineHighlight）の公開判定（Highlights PR-3 Publication Gate）。

神社詳細などの利用者向けの表示は、この判定を通った見どころだけを出す。
由緒・歴史の evidence_gate と同じ基準（source_confirmed / reviewed）を使い、
新しい確認状態の基準は作らない。

表示してよい条件（すべて満たすこと）:
  1. publication_status が published
  2. 見どころ自身の verification_status が fact-ready（source_confirmed / reviewed）
  3. fact-ready な出典のうち、公開の根拠になる種類（PUBLIC_EVIDENCE_EXCLUDED_SOURCE_TYPES 以外）が1件以上
  4. 表示する言語の翻訳が approved で、名前と説明（description）が空でない

現地観察（user_observation）だけでは公開しない。現地観察は公式の情報と混同しないため
（docs/knowledge/shrine-knowledge-contract.md「Observational Knowledge」）、
「現地で確認した日」の印としてだけ使う（observed_on）。

DBの直接更新（raw SQL / QuerySet.update）で状態が変わった場合も、この判定は
表示のたびに現在の値で行うため、表示側の保証は崩れない。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Optional

from temples.services import evidence_gate

# 公開の根拠に数えない出典の種類。
# - user_observation: 現地観察。公式の情報と混同しない（印としてだけ使う）
# - internal_research: 社内調査記録。利用者が確かめられる出典ではない
PUBLIC_EVIDENCE_EXCLUDED_SOURCE_TYPES = frozenset({"user_observation", "internal_research"})
OBSERVATION_SOURCE_TYPE = "user_observation"

# 公開判定で落ちた理由（管理画面での確認用）。
REASON_NOT_PUBLISHED = "not_published"
REASON_NOT_VERIFIED = "highlight_not_verified"
REASON_NO_PUBLIC_SOURCE = "no_public_source"
REASON_NO_APPROVED_TRANSLATION = "no_approved_translation"
REASON_EMPTY_DESCRIPTION = "empty_description"


@dataclass(frozen=True)
class HighlightPublicationDecision:
    displayable: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


def is_fact_ready_source(source) -> bool:
    return source.verification_status in evidence_gate.FACT_READY_VERIFICATION_STATUSES


def public_evidence_sources(sources: Iterable) -> list:
    """公開の根拠になる出典だけを返す（fact-ready かつ除外する種類でない）。"""
    return [
        s
        for s in sources
        if is_fact_ready_source(s) and s.source_type not in PUBLIC_EVIDENCE_EXCLUDED_SOURCE_TYPES
    ]


def latest_observed_on(sources: Iterable) -> Optional[date]:
    """fact-ready な現地観察の出典のうち、いちばん新しい観察日（accessed_at）。"""
    dates = [
        s.accessed_at
        for s in sources
        if s.source_type == OBSERVATION_SOURCE_TYPE
        and is_fact_ready_source(s)
        and s.accessed_at is not None
    ]
    return max(dates) if dates else None


def find_translation(translations: Iterable, language_code: str):
    for t in translations:
        if t.language_code == language_code:
            return t
    return None


def decide_highlight_publication(
    *,
    publication_status: str,
    verification_status: str,
    sources: Iterable,
    translation,
) -> HighlightPublicationDecision:
    """値だけで判定する（DBを読まない）。sources は ShrineKnowledgeSource の並び。"""
    reasons: list[str] = []
    if publication_status != "published":
        reasons.append(REASON_NOT_PUBLISHED)
    if verification_status not in evidence_gate.FACT_READY_VERIFICATION_STATUSES:
        reasons.append(REASON_NOT_VERIFIED)
    if not public_evidence_sources(sources):
        reasons.append(REASON_NO_PUBLIC_SOURCE)
    if translation is None or translation.review_status != "approved":
        reasons.append(REASON_NO_APPROVED_TRANSLATION)
    elif not (translation.name or "").strip() or not (translation.description or "").strip():
        reasons.append(REASON_EMPTY_DESCRIPTION)
    return HighlightPublicationDecision(displayable=not reasons, reasons=tuple(reasons))


def decide_for_highlight(highlight, language_code: str) -> HighlightPublicationDecision:
    """ShrineHighlight のインスタンスで判定する。prefetch 済みならDBを追加で読まない。"""
    sources = [link.source for link in highlight.source_links.all()]
    translation = find_translation(highlight.translations.all(), language_code)
    return decide_highlight_publication(
        publication_status=highlight.publication_status,
        verification_status=highlight.verification_status,
        sources=sources,
        translation=translation,
    )


# --- 見どころへのアンサー（見どころ単位の推薦 段階A） --------------------------------

REASON_ANSWER_NOT_APPROVED = "answer_not_approved"
REASON_ANSWER_LANGUAGE_MISMATCH = "answer_language_mismatch"
REASON_ANSWER_EMPTY = "answer_empty"
REASON_HIGHLIGHT_NOT_DISPLAYABLE = "highlight_not_displayable"


def decide_answer_publication(answer, language_code: str) -> HighlightPublicationDecision:
    """アンサーを出してよいか。

    見どころ自体が同じ言語で公開判定を通っていること ＋ アンサーが承認済みで空でないこと。
    見どころが出せないのにアンサーだけ出すことはしない（つながった事実の確認が前提のため）。
    prefetch 済みの answer.highlight（translations / source_links__source）ならDBを追加で読まない。
    """
    reasons: list[str] = []
    if answer.language_code != language_code:
        reasons.append(REASON_ANSWER_LANGUAGE_MISMATCH)
    if answer.review_status != "approved":
        reasons.append(REASON_ANSWER_NOT_APPROVED)
    if not (answer.answer_text or "").strip():
        reasons.append(REASON_ANSWER_EMPTY)
    if not decide_for_highlight(answer.highlight, language_code).displayable:
        reasons.append(REASON_HIGHLIGHT_NOT_DISPLAYABLE)
    return HighlightPublicationDecision(displayable=not reasons, reasons=tuple(reasons))
