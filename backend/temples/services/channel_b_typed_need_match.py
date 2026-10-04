"""Policy C / Channel B: typed Recommendation read（PR-C）。

docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md
§12.11（read boundary / verification gate）/ §12.13（Need mapping）/ §12.15.K〜M /
§12.17 Mother Ship Decision（carrier の公開禁止、Need key の exact equality）の実装。

    ShrineSourceFact
    → verification gate（Fact と Source の verification_status。confidence / verified_at は gate にしない）
    → S3a registry（stable_key で lookup。mapping が無ければ NO_SIGNAL）
    → canonical concept（GoriyakuTag.name の exact 一致。id は Need の意味の参照にだけ使う）
    → 共有の Need の意味（NEED_TO_GORIYAKU_IDS を参照だけする）
    → TypedNeedMatch

Channel A（goriyaku_tags / goriyaku_tag_ids / matched_by_* / matched_all）とは別の signal であり、
それらへ書かない。数値の関連性（prefilter / ranking / score_need）は持たない（PR-F）。

carrier（候補 dict の CHANNEL_B_TYPED_NEED_MATCHES_KEY）は内部の runtime data である。
build_chat_recommendations() の出口で strip_channel_b_carrier() により取り除き、
公開 response・永続化（thread / recommendation log）へ出さない。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
from temples.domain.source_fact_mapping_registry_v1 import (
    SourceFactMappingRegistryError,
    get_registry,
)
from temples.models import (
    KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
    GoriyakuTag,
    ShrineSourceFact,
)

# 候補 dict 上の内部 carrier。値は tuple[TypedNeedMatch, ...]（一致がある候補にだけ付く）。
CHANNEL_B_TYPED_NEED_MATCHES_KEY = "_channel_b_typed_need_matches"

_VALID_EVIDENCE_CHARACTERIZATIONS = frozenset(
    value for value, _ in ShrineSourceFact.EVIDENCE_CHARACTERIZATION_CHOICES
)
_READABLE_VERIFICATION_STATUSES = frozenset(KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES)


@dataclass(frozen=True)
class TypedNeedMatch:
    """Channel B の型付きの Need 一致 1件（immutable）。数値の重みは持たない。

    need                    共有の Need の意味が使う Need key（alias 正規化をしない）
    canonical_concept_name  registry の canonical GoriyakuTag.name（分類）
    signal_type             ShrineSourceFact.evidence_characterization（claim の上限。強めない）
    source_fact_key         ShrineSourceFact.stable_key
    source_attested_wording Source 上の表記そのもの（concept name へ書き換えない）
    """

    need: str
    canonical_concept_name: str
    signal_type: str
    source_fact_key: str
    source_attested_wording: str


def is_source_fact_recommendation_readable(fact: ShrineSourceFact, sources: Iterable[Any]) -> bool:
    """Channel B の runtime の verification gate と構造の検査（§12.11.6）。

    - Fact の verification_status が source_confirmed / reviewed
    - Source が1件以上あり、そのうち1件以上の verification_status が source_confirmed / reviewed
    - source_attested_wording が空白でない
    - evidence_characterization が PR-A の3値のどれか
    confidence と verified_at は gate にしない。不合格の Fact は NO_SIGNAL（修復しない）。
    """
    if fact.verification_status not in _READABLE_VERIFICATION_STATUSES:
        return False
    if (
        not isinstance(fact.source_attested_wording, str)
        or not fact.source_attested_wording.strip()
    ):
        return False
    if fact.evidence_characterization not in _VALID_EVIDENCE_CHARACTERIZATIONS:
        return False
    return any(
        getattr(source, "verification_status", None) in _READABLE_VERIFICATION_STATUSES
        for source in sources
    )


def needs_for_concept_id(concept_id: int) -> Tuple[str, ...]:
    """共有の Need の意味（NEED_TO_GORIYAKU_IDS）で、concept を含む Need key をすべて返す。

    Need key はそのまま返す（alias 正規化をしない）。順序は決定的（key の昇順）。
    """
    return tuple(sorted(need for need, ids in NEED_TO_GORIYAKU_IDS.items() if concept_id in ids))


def fetch_typed_need_matches(shrine_ids: Iterable[int]) -> Dict[int, Tuple[TypedNeedMatch, ...]]:
    """shrine_id → TypedNeedMatch の tuple を一括で作る（候補ごとの query はしない）。

    query: registry に record が無ければ 0回。あれば Source Fact 1回 + Source の prefetch 1回 +
    （mapping された Fact があれば）GoriyakuTag 1回。registry の DB 整合検証は実行しない。

    registry が不正なら SourceFactMappingRegistryError（PR-B の fail-closed をそのまま伝える）。
    正の mapping の concept が GoriyakuTag に無い場合も同じ例外にする（黙って飛ばさない）。
    """
    registry = get_registry()
    ids = sorted({int(i) for i in shrine_ids if i is not None})
    if not ids or not registry.records:
        return {}

    facts = list(
        ShrineSourceFact.objects.filter(shrine_id__in=ids)
        .prefetch_related("sources")
        .order_by("shrine_id", "id")
    )

    mapped: List[Tuple[ShrineSourceFact, Any]] = []
    for fact in facts:
        if not is_source_fact_recommendation_readable(fact, fact.sources.all()):
            continue
        record = registry.lookup(fact.stable_key)
        if record is None:
            # mapping が無い（AMBIGUOUS / NO_CANONICAL_TAG を含む）= NO_SIGNAL。エラーではない。
            continue
        mapped.append((fact, record))
    if not mapped:
        return {}

    names = sorted({record.canonical_concept_name for _, record in mapped})
    concept_id_by_name = dict(GoriyakuTag.objects.filter(name__in=names).values_list("name", "id"))
    missing = [name for name in names if name not in concept_id_by_name]
    if missing:
        raise SourceFactMappingRegistryError(
            [f"canonical_concept_name {name!r}: no GoriyakuTag by exact name" for name in missing]
        )

    out: Dict[int, List[TypedNeedMatch]] = {}
    for fact, record in mapped:
        for need in needs_for_concept_id(concept_id_by_name[record.canonical_concept_name]):
            out.setdefault(fact.shrine_id, []).append(
                TypedNeedMatch(
                    need=need,
                    canonical_concept_name=record.canonical_concept_name,
                    signal_type=fact.evidence_characterization,
                    source_fact_key=fact.stable_key,
                    source_attested_wording=fact.source_attested_wording,
                )
            )
    return {shrine_id: tuple(matches) for shrine_id, matches in out.items()}


def without_channel_b_carrier(candidates: Iterable[Any]) -> List[Any]:
    """carrier を除いた候補の list（元の dict は変えない。carrier の無い dict はそのまま返す）。

    LLM 成功経路の入力を Channel B 導入前と同じに保つために使う。
    """
    return [
        (
            {k: v for k, v in c.items() if k != CHANNEL_B_TYPED_NEED_MATCHES_KEY}
            if isinstance(c, dict) and CHANNEL_B_TYPED_NEED_MATCHES_KEY in c
            else c
        )
        for c in candidates
    ]


def strip_channel_b_carrier(recs: Dict[str, Any]) -> Dict[str, Any]:
    """recommendation の dict から内部 carrier を取り除く（in-place）。

    build_chat_recommendations() の出口で呼ぶ。以降の公開 response・thread 保存・
    recommendation log・Compass の投影に carrier が出ないようにする。
    """
    for key in ("recommendations", "recommendations_v2"):
        rows = recs.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                row.pop(CHANNEL_B_TYPED_NEED_MATCHES_KEY, None)
    return recs


__all__ = [
    "CHANNEL_B_TYPED_NEED_MATCHES_KEY",
    "TypedNeedMatch",
    "is_source_fact_recommendation_readable",
    "needs_for_concept_id",
    "fetch_typed_need_matches",
    "without_channel_b_carrier",
    "strip_channel_b_carrier",
]
