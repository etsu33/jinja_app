"""Collective Runtime selector / admission（A6-01）。

ShrineDeityCollective のうち Runtime に admit してよいものだけを、shrine_id 単位で返す
読み取り専用 selector。Serializer / API / Recommendation / Deep Dive には接続しない
（外部 payload 契約は A6-02 の責務）。

Admission 条件（すべて AND。1つでも欠ければ Collective ごと除外）:
  1. CollectiveRuntimeActivation row が存在する（必要条件であり十分条件ではない）
  2. Collective 自身が evidence_gate.decide_fact_usability() で usable
  3. member_list_status == "complete"
  4. Membership が1件以上
  5. 全 Membership が各自の sources で decide_fact_usability() usable
  6. 全 Membership が既存 ShrineDeity へ解決する
  7. 全 Membership の ShrineDeity が Collective と同じ Shrine に属する

Evidence 判定は既存 evidence_gate を唯一の authority とし、ここで再定義しない。
Membership の判定には Membership 自身の sources だけを渡し、Collective.sources を継承・
補完に使わない。Pattern A/B/C/D は推論しない。confidence は判定に使わず metadata として保持する。

候補取得は activated Collective に限定し、sources / memberships / membership sources /
membership deity を一括 prefetch する（候補がある場合 5 クエリ、候補 0 件なら 1 クエリ、
空入力なら 0 クエリ。対象 Shrine / Collective / Membership 数に依らず一定）。
最終判定は Python 側で evidence_gate へ委譲する。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from django.db.models import Prefetch
from temples.models import ShrineDeity, ShrineDeityCollective, ShrineDeityCollectiveMembership
from temples.services import evidence_gate

REQUIRED_MEMBER_LIST_STATUS = "complete"


@dataclass(frozen=True)
class AdmittedCollectiveMembership:
    membership_id: int
    deity_id: int
    deity_display_name: str
    sort_order: int
    verification_status: str
    confidence: str


@dataclass(frozen=True)
class AdmittedCollective:
    collective_id: int
    shrine_id: int
    source_attested_label: str
    role: str
    sort_order: int
    member_count: int | None
    member_count_relation: str
    member_list_status: str
    verification_status: str
    confidence: str
    memberships: tuple[AdmittedCollectiveMembership, ...]


def _is_usable(fact) -> bool:
    return evidence_gate.decide_fact_usability(
        verification_status=fact.verification_status,
        confidence=fact.confidence,
        source_verification_statuses=(s.verification_status for s in fact.sources.all()),
    ).usable


def _admit_membership(
    membership: ShrineDeityCollectiveMembership, collective: ShrineDeityCollective
) -> AdmittedCollectiveMembership | None:
    # Membership 自身の sources だけで判定する（Collective.sources を継承しない）。
    if not _is_usable(membership):
        return None
    # prefetch で解決できなかった deity は参照時に DoesNotExist となる（未解決 = 不合格）。
    try:
        deity = membership.deity
    except ShrineDeity.DoesNotExist:
        return None
    if deity is None:
        return None
    if deity.shrine_id != collective.shrine_id:
        return None
    return AdmittedCollectiveMembership(
        membership_id=membership.pk,
        deity_id=deity.pk,
        deity_display_name=deity.display_name,
        sort_order=membership.sort_order,
        verification_status=membership.verification_status,
        confidence=membership.confidence,
    )


def _admit_collective(collective: ShrineDeityCollective) -> AdmittedCollective | None:
    """prefetch 済み Collective 1件の admission 判定。1条件でも欠ければ None（部分返却しない）。

    Activation row の存在は候補取得 query 側（fetch_runtime_admitted_collectives）で保証する。
    """
    if not _is_usable(collective):
        return None
    if collective.member_list_status != REQUIRED_MEMBER_LIST_STATUS:
        return None

    memberships = list(collective.memberships.all())
    if not memberships:
        return None

    admitted: list[AdmittedCollectiveMembership] = []
    for membership in memberships:
        result = _admit_membership(membership, collective)
        if result is None:
            # Collective 境界で fail-safe: 1件でも不合格なら Collective ごと除外。
            return None
        admitted.append(result)

    return AdmittedCollective(
        collective_id=collective.pk,
        shrine_id=collective.shrine_id,
        source_attested_label=collective.source_attested_label,
        role=collective.role,
        sort_order=collective.sort_order,
        member_count=collective.member_count,
        member_count_relation=collective.member_count_relation,
        member_list_status=collective.member_list_status,
        verification_status=collective.verification_status,
        confidence=collective.confidence,
        memberships=tuple(admitted),
    )


def fetch_runtime_admitted_collectives(
    shrine_ids: Iterable[int],
) -> dict[int, list[AdmittedCollective]]:
    """対象 shrine_ids の admitted Collective を shrine_id 単位で返す（読み取り専用）。

    順序は Collective / Membership とも backend 所有の (sort_order, id)。
    admitted Collective が無い shrine_id は key を持たない。空入力はクエリを発行せず {} を返す。
    """
    ids = sorted({int(sid) for sid in shrine_ids})
    if not ids:
        return {}

    # deity は select_related（non-null FK → INNER JOIN）ではなく prefetch で取得する。
    # INNER JOIN だと未解決 deity の Membership 行が黙って落ち、部分集合を complete と
    # 誤認し得るため。prefetch なら Membership 行は残り、未解決は deity 参照時の DoesNotExist として除外される。
    memberships_qs = ShrineDeityCollectiveMembership.objects.prefetch_related(
        "sources", "deity"
    ).order_by("sort_order", "id")
    candidates = (
        ShrineDeityCollective.objects.filter(
            shrine_id__in=ids,
            runtime_activation__isnull=False,
        )
        .order_by("sort_order", "id")
        .prefetch_related("sources", Prefetch("memberships", queryset=memberships_qs))
    )

    result: dict[int, list[AdmittedCollective]] = defaultdict(list)
    for collective in candidates:
        admitted = _admit_collective(collective)
        if admitted is not None:
            result[collective.shrine_id].append(admitted)
    return dict(result)


__all__ = [
    "REQUIRED_MEMBER_LIST_STATUS",
    "AdmittedCollective",
    "AdmittedCollectiveMembership",
    "fetch_runtime_admitted_collectives",
]
