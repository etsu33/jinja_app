"""Canonical Shrine Anchor（神社中心座標）の値定義と決定論的mean helper.

正本: docs/core/split-anchor-architecture.md（PHASE_1）
      docs/knowledge/shrine-position-contract.md §A-7b

本moduleはDBへアクセスしない。model / migration / 将来のPHASE_2手順は
ここで定義する値とhelperだけを参照し、同じ規則を二重実装しない。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

# --- ShrineCanonicalAnchor.status -------------------------------------------
# row不在 = NOT_ADJUDICATED。NOT_ADJUDICATED はDB値として持たない。
ANCHOR_STATUS_CONFIRMED = "CONFIRMED"
ANCHOR_STATUS_HOLD_POSITION_REVIEW = "HOLD_POSITION_REVIEW"
ANCHOR_STATUSES = (ANCHOR_STATUS_CONFIRMED, ANCHOR_STATUS_HOLD_POSITION_REVIEW)

# --- ShrineCanonicalAnchor.subject_type -------------------------------------
SUBJECT_TYPE_SINGLE_PRINCIPAL_UNIT = "SINGLE_PRINCIPAL_UNIT"
SUBJECT_TYPE_MULTI_PRINCIPAL_UNIT = "MULTI_PRINCIPAL_UNIT"
SUBJECT_TYPE_NON_BUILDING_RITUAL_CENTER = "NON_BUILDING_RITUAL_CENTER"
SUBJECT_TYPES = (
    SUBJECT_TYPE_SINGLE_PRINCIPAL_UNIT,
    SUBJECT_TYPE_MULTI_PRINCIPAL_UNIT,
    SUBJECT_TYPE_NON_BUILDING_RITUAL_CENTER,
)

# --- ShrineCanonicalAnchor.point_method -------------------------------------
POINT_METHOD_DIRECT_POINT = "DIRECT_POINT"
POINT_METHOD_UNWEIGHTED_COMPONENT_MEAN = "UNWEIGHTED_COMPONENT_MEAN"
POINT_METHODS = (POINT_METHOD_DIRECT_POINT, POINT_METHOD_UNWEIGHTED_COMPONENT_MEAN)

# --- ShrineCanonicalAnchor.component_set_status -----------------------------
COMPONENT_SET_STATUS_COMPLETE = "COMPLETE"
COMPONENT_SET_STATUS_INCOMPLETE = "INCOMPLETE"
COMPONENT_SET_STATUSES = (COMPONENT_SET_STATUS_COMPLETE, COMPONENT_SET_STATUS_INCOMPLETE)

# --- ShrineCanonicalAnchorComponent.classification --------------------------
COMPONENT_INCLUDED = "INCLUDED"
COMPONENT_EXCLUDED = "EXCLUDED"
COMPONENT_UNCLASSIFIED = "UNCLASSIFIED"
COMPONENT_CLASSIFICATIONS = (COMPONENT_INCLUDED, COMPONENT_EXCLUDED, COMPONENT_UNCLASSIFIED)

# --- ShrineCanonicalAnchorEvidence.evidence_role ----------------------------
# source_type / extraction_method / evidence_strength / stated_precision は
# PHASE_1で正式taxonomyが未定義のためenumを持たない（文字列保存のみ）。
EVIDENCE_ROLE_SEMANTIC = "SEMANTIC"
EVIDENCE_ROLE_COORDINATE = "COORDINATE"
EVIDENCE_ROLES = (EVIDENCE_ROLE_SEMANTIC, EVIDENCE_ROLE_COORDINATE)


class CanonicalMeanError(ValueError):
    """UNWEIGHTED_COMPONENT_MEAN を算出できない（fail closed）。"""


class _ComponentLike(Protocol):
    classification: str
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass(frozen=True)
class CanonicalPoint:
    latitude: float
    longitude: float


def requires_component_mean(*, status, subject_type, point_method) -> bool:
    """cross-row検証（component集合とのmean一致）が必要な組合せか。"""
    return (
        status == ANCHOR_STATUS_CONFIRMED
        and subject_type == SUBJECT_TYPE_MULTI_PRINCIPAL_UNIT
        and point_method == POINT_METHOD_UNWEIGHTED_COMPONENT_MEAN
    )


def compute_unweighted_component_mean(components: Iterable[_ComponentLike]) -> CanonicalPoint:
    """INCLUDED component全件の緯度・経度を非加重の算術平均で返す。

    - EXCLUDED / UNCLASSIFIED は入力に含まれていても計算へ入れない
    - INCLUDED が0件なら拒否する
    - INCLUDED のうち1件でも座標pairを欠けば拒否する（一部だけのmeanを作らない）
    - 重み付け・距離補正は行わない
    - `math.fsum` は正しく丸められた和を返すため、入力順序に依存しない
    """
    included = [c for c in components if c.classification == COMPONENT_INCLUDED]
    if not included:
        raise CanonicalMeanError("INCLUDED component が0件のため mean を算出できません。")
    if any(c.latitude is None or c.longitude is None for c in included):
        raise CanonicalMeanError(
            "座標を持たない INCLUDED component があるため mean を算出できません。"
        )
    n = len(included)
    return CanonicalPoint(
        latitude=math.fsum(float(c.latitude) for c in included) / n,
        longitude=math.fsum(float(c.longitude) for c in included) / n,
    )
