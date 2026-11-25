"""見どころ（Highlights）のテスト用データを作る関数。PR-3以降のテストで共有する。"""

from __future__ import annotations

from datetime import date
from itertools import count
from typing import Optional

from django.utils import timezone

from temples.models import (
    Shrine,
    ShrineHighlight,
    ShrineHighlightHistory,
    ShrineHighlightSource,
    ShrineHighlightTranslation,
    ShrineHistory,
    ShrineKnowledgeSource,
)

_seq = count(1)
FACT_READY = ("source_confirmed", "reviewed")


def make_shrine(name: str = "見どころ試験神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name, address="東京都新宿区1-2-3", latitude=35.69, longitude=139.70
    )


def make_source(
    source_type: str = "shrine_official",
    verification_status: str = "source_confirmed",
    accessed_at: Optional[date] = None,
    title: Optional[str] = None,
) -> ShrineKnowledgeSource:
    kwargs = {}
    if verification_status in FACT_READY:
        kwargs["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(
        source_type=source_type,
        title=title or f"出典-{source_type}-{next(_seq)}",
        url="https://example.com/official" if source_type != "user_observation" else "",
        verification_status=verification_status,
        accessed_at=accessed_at,
        **kwargs,
    )


def make_highlight(
    shrine: Shrine,
    *,
    publication_status: str = "published",
    verification_status: str = "source_confirmed",
    category: str = "architecture",
    sort_order: int = 0,
) -> ShrineHighlight:
    kwargs = {}
    if verification_status in FACT_READY:
        kwargs["verified_at"] = timezone.now()
    return ShrineHighlight.objects.create(
        shrine=shrine,
        stable_key=f"hl-{shrine.pk}-{next(_seq)}",
        category=category,
        sort_order=sort_order,
        publication_status=publication_status,
        verification_status=verification_status,
        **kwargs,
    )


def make_translation(
    highlight: ShrineHighlight,
    *,
    language_code: str = "ja",
    review_status: str = "approved",
    name: str = "拝殿の彫刻",
    description: str = "拝殿の正面上部にある彫刻を見る。",
    historical_connection: str = "",
    location_hint: str = "",
) -> ShrineHighlightTranslation:
    return ShrineHighlightTranslation.objects.create(
        highlight=highlight,
        language_code=language_code,
        name=name,
        description=description,
        historical_connection=historical_connection,
        location_hint=location_hint,
        review_status=review_status,
        reviewed_at=timezone.now() if review_status == "approved" else None,
    )


def link_source(highlight: ShrineHighlight, source: ShrineKnowledgeSource) -> ShrineHighlightSource:
    return ShrineHighlightSource.objects.create(highlight=highlight, source=source)


def link_history(highlight: ShrineHighlight, history: ShrineHistory) -> ShrineHighlightHistory:
    return ShrineHighlightHistory.objects.create(
        highlight=highlight, history=history, shrine=highlight.shrine
    )


def make_displayable_highlight(shrine: Shrine, **translation_kwargs) -> ShrineHighlight:
    """公開判定をすべて満たす見どころ（日本語の翻訳つき）。"""
    highlight = make_highlight(shrine)
    make_translation(highlight, **translation_kwargs)
    link_source(highlight, make_source())
    return highlight


def make_answer(
    highlight: ShrineHighlight,
    *,
    need_tag: str = "career",
    language_code: str = "ja",
    review_status: str = "approved",
    answer_text: str = "焼けたところから建て直した由来が、今のあなたの気持ちと重なるかもしれない。",
):
    from temples.models import ShrineHighlightAnswer

    return ShrineHighlightAnswer.objects.create(
        highlight=highlight,
        need_tag=need_tag,
        language_code=language_code,
        answer_text=answer_text,
        review_status=review_status,
        reviewed_at=timezone.now() if review_status == "approved" else None,
    )
