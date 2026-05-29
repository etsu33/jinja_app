

"""Trust metadata for shrine list cards.

This module keeps list-card trust signals separate from cultural translation.
Use this for concise, factual-looking metadata such as shrine class, cultural
status, lineage, and short origin summaries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShrineTrustMetadata:
    """Shrine trust signals used by list cards."""

    rank_class: str
    cultural_status: tuple[str, ...]
    lineage: str
    origin_summary: str


SHRINE_TRUST_METADATA: dict[int, ShrineTrustMetadata] = {
    17: ShrineTrustMetadata(
        rank_class="神社",
        cultural_status=("別表神社", "山岳信仰"),
        lineage="三峯信仰の中心的神社",
        origin_summary="山深い地で、自然への畏れと狼の守護信仰を受け継いできた神社です。",
    ),
    14: ShrineTrustMetadata(
        rank_class="神宮",
        cultural_status=("常陸国一宮", "勅祭社", "旧官幣大社"),
        lineage="全国鹿島神社総本社",
        origin_summary="武神・剣神を祀り、旅立ちや勝負の前に信仰されてきた神社です。",
    ),
}


def get_shrine_trust_metadata(shrine_id: int) -> ShrineTrustMetadata | None:
    """Return shrine trust metadata when available."""

    return SHRINE_TRUST_METADATA.get(shrine_id)
