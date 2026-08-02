"""Evidence Gate Foundation。

docs/knowledge/shrine-knowledge-contract.md「Evidence Gate要件」の実装。

ShrineDeity / ShrineHistory（Fact）がRecommendation / Shrine Detailの両経路で
利用可能（usable）かどうかを、単一のロジックで判定する。従来はこの判定が
Recommendation側（shrine_knowledge_selector.pyのQuerySet条件）とShrine Detail側
（ShrineViewSet.get_queryset()のPrefetch + Serializer）とで別々に実装されており、
「Fact ready + fact-ready Sourceなし」のケースでRecommendationは除外・Detailは
表示という非対称性があった。本モジュールを両経路の正本とすることでこれを解消する。

PR-Aでは以下のみを扱う。confidenceによる表現制御・disputed専用表示・数値スコアは
PR-B以降へ延期する（本ファイルのdocstring/コメントを参照）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from temples.models import KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES

# Fact自身・Sourceの双方で「fact-ready」とみなすverification_status。
# 値そのものはtemples.models.KNOWLEDGE_FACT_READY_VERIFICATION_STATUSESを正本とし、
# ここでは再定義せず re-export するのみ（判定基準の二重管理を避ける）。
FACT_READY_VERIFICATION_STATUSES = KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES


@dataclass(frozen=True)
class EvidenceDecision:
    """Fact 1件の利用可否判定結果。

    display_mode / reason_strengthはPR-Aでは"usableの言い換え"に過ぎない
    固定契約（full/hidden, assertive/suppressed）。将来のPR-B以降で
    confidenceに応じたweakened/moderate等を追加する余地として型を分けている。
    """

    usable: bool
    display_mode: str
    reason_strength: str
    verification_status: str
    confidence: str
    reason: str


def decide_fact_usability(
    *,
    verification_status: str,
    confidence: str,
    source_verification_statuses: Iterable[str],
) -> EvidenceDecision:
    """Fact 1件のEvidence Gate判定。

    usable == True となる条件（PR-A契約）:
      1. Fact自身のverification_statusがFACT_READY_VERIFICATION_STATUSESに含まれる
      2. RelationされたSourceのうち最低1件のverification_statusが
         FACT_READY_VERIFICATION_STATUSESに含まれる
    上記のANDを満たさない場合はusable=Falseとし、display_mode="hidden"とする。
    confidenceは判定に使わず、metadataとしてDecisionへそのまま保持するのみ。
    """

    fact_ready = verification_status in FACT_READY_VERIFICATION_STATUSES
    has_ready_source = any(
        status in FACT_READY_VERIFICATION_STATUSES for status in source_verification_statuses
    )
    usable = fact_ready and has_ready_source

    if usable:
        reason = "fact_ready_with_source"
    elif not fact_ready:
        reason = "fact_not_ready"
    else:
        reason = "no_fact_ready_source"

    return EvidenceDecision(
        usable=usable,
        display_mode="full" if usable else "hidden",
        reason_strength="assertive" if usable else "suppressed",
        verification_status=verification_status,
        confidence=confidence,
        reason=reason,
    )


__all__ = [
    "FACT_READY_VERIFICATION_STATUSES",
    "EvidenceDecision",
    "decide_fact_usability",
]
