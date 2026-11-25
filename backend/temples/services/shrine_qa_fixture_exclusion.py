"""QA fixture Shrine除外契約。

PR2271（audit/knowledge-coverage-shadow-105、id=101-105の「承認テスト神社」
「重複検証神社」等）で確立した、Recommendation candidate pool
（temples.services.concierge_chat_candidates.build_chat_candidates）と
Knowledge Coverage集計（temples.management.commands.knowledge_coverage_report）
の両方が共有すべき「テスト/QA用fixture Shrineの除外」条件を一箇所にまとめる。

この関数は「どのShrineが実在神社（audit対象）か」を判定する唯一の正本であり、
呼び出し側は本関数の結果をそのまま使い、除外条件を独自に再実装しない。
name_jpの命名規約にのみ依存し、id範囲のhardcodeは行わない
（新しいfixtureがid=106以降に追加されても、同じ命名規約に従う限り
再定義なしで機能する）。
"""

from __future__ import annotations

from django.db.models import QuerySet

_NOISY_SHRINE_NAMES = [
    "x",
    "x2",
    "noaddr",
    "住所なし神社",
    "test神社",
    "テスト候補神社",
    "テスト神社",
    "テスト神社2",
    "テスト神社-1770895174",
]


def exclude_qa_fixture_shrines(queryset: QuerySet) -> QuerySet:
    """QA用fixture Shrineをquerysetから除外する。

    Recommendation candidate pool（concierge_chat_candidates.build_chat_candidates）
    と同一の除外条件を適用する。地理座標・住所の有無等、Candidate固有のfilterは
    ここに含めない（Coverage集計等、Candidate以外の用途で母集団が変わらないため）。
    """
    qs = queryset.exclude(name_jp__in=_NOISY_SHRINE_NAMES)
    qs = qs.exclude(name_jp__startswith="テスト")
    qs = qs.exclude(name_jp__istartswith="test")
    qs = qs.exclude(name_jp__icontains="承認テスト")
    qs = qs.exclude(name_jp__icontains="検証")
    return qs


__all__ = ["exclude_qa_fixture_shrines"]
