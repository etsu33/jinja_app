"""Compass Monthly Public Projection（HTTP境界のallowlist投影）。

docs/audit/compass-monthly-api-boundary.md Section 9-11 の実装。

責務は「Shared Recommendation dict → Compass Monthly公開表現」への
**投影のみ**。Recommendation の再計算・ranking・scoring・reason再生成・
Meaning生成・DBアクセス・LLM呼び出しは一切行わない（そもそも行えないよう、
このモジュールは domain/service 層を一切importしない）。

Allowlist（denylistではない）:
  Shared Recommendation に新しいfieldが増えても、ここに明示的に列挙されない
  限り Compass Monthly API からは出ない。既知の内部field名を消す実装
  （denylist）は Section 10 で明示的に禁止されている。

Fail-safe（Section 11）:
  公開対象のsource fieldが存在しない場合、代わりの値をでっち上げない。
  nested構造（breakdown / reason_facts）が期待した型でない場合、生の値は
  絶対に露出させず、そのkey自体を落とす。

`recommendation_instance_id` だけは例外で、source ではなく View が
request単位で生成した transport metadata を各itemへ互換aliasとして
注入する（Section 8: canonicalはtop-level側）。
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

# recommendation item の top-level 公開field（instance_id以外）。
# source に存在するときのみコピーする。
COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS: tuple[str, ...] = (
    "shrine_id",
    "id",
    "name",
    "address",
    "distance_m",
    "reason",
)

# breakdown の公開nested field。
COMPASS_MONTHLY_PUBLIC_BREAKDOWN_FIELDS: tuple[str, ...] = ("matched_need_tags",)

# reason_facts[] の公開field。
COMPASS_MONTHLY_PUBLIC_REASON_FACT_FIELDS: tuple[str, ...] = ("type", "label")

# Public Contract v1 で recommendation item が取り得るkeyの全体集合。
# 実際のitemはこの部分集合であればよく、全keyを持つ必要はない（Section 9.2）。
COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST: frozenset[str] = frozenset(
    (
        *COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS,
        "recommendation_instance_id",
        "breakdown",
        "reason_facts",
    )
)


def _project_breakdown(raw: Any) -> dict[str, Any] | None:
    """breakdown を matched_need_tags のみへ投影する。

    mapping でなければ None（= keyごと落とす）。matched_need_tags が list で
    なければそのnested値は載せない（生の値を露出させない）。
    """
    if not isinstance(raw, Mapping):
        return None

    projected: dict[str, Any] = {}
    for key in COMPASS_MONTHLY_PUBLIC_BREAKDOWN_FIELDS:
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, list):
            continue
        # source の list オブジェクトを共有しない（source側を変化させない）。
        projected[key] = list(value)
    return projected


def _project_reason_facts(raw: Any) -> list[dict[str, Any]] | None:
    """reason_facts を type / label のみへ投影する。

    list でなければ None（= keyごと落とす）。mapping でない要素は落とす
    （生の要素を露出させない）。
    """
    if not isinstance(raw, list):
        return None

    projected: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, Mapping):
            continue
        fact = {
            key: entry[key] for key in COMPASS_MONTHLY_PUBLIC_REASON_FACT_FIELDS if key in entry
        }
        projected.append(fact)
    return projected


def project_compass_recommendation(
    recommendation: Any,
    *,
    recommendation_instance_id: str,
) -> dict[str, Any]:
    """Shared Recommendation 1件を Compass Monthly 公開shapeへ投影する。

    source は読むだけで、書き換えない。
    """
    source: Mapping[str, Any] = recommendation if isinstance(recommendation, Mapping) else {}

    projected: dict[str, Any] = {
        key: source[key] for key in COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS if key in source
    }

    if "breakdown" in source:
        breakdown = _project_breakdown(source["breakdown"])
        if breakdown is not None:
            projected["breakdown"] = breakdown

    if "reason_facts" in source:
        reason_facts = _project_reason_facts(source["reason_facts"])
        if reason_facts is not None:
            projected["reason_facts"] = reason_facts

    # Section 11 の唯一の例外: source 由来ではなく、View が生成した
    # request単位のIDを互換aliasとして注入する。
    projected["recommendation_instance_id"] = recommendation_instance_id
    return projected


def project_compass_recommendations(
    recommendations: Iterable[Any] | None,
    *,
    recommendation_instance_id: str,
) -> list[dict[str, Any]]:
    """recommendations[] 全体を投影する。順序と件数は変えない。"""
    return [
        project_compass_recommendation(
            recommendation,
            recommendation_instance_id=recommendation_instance_id,
        )
        for recommendation in (recommendations or [])
    ]


__all__ = [
    "COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_BREAKDOWN_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_REASON_FACT_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST",
    "project_compass_recommendation",
    "project_compass_recommendations",
]
