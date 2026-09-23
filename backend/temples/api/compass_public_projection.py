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

R-3 Identity Gate（docs/audit/compass-shrine-id-presence-audit.md §10 / §11）:
  `state == recommendation_success` の Monthly レスポンスに限り、
  `project_compass_recommendations(..., require_shrine_id=True)` が
  `shrine_id` の存在と非nullを要求する。違反時は
  `CompassPublicProjectionContractError` を送出し、View 側が既存の
  error boundary（HTTP 500 / {"state": "error"}）へ正規化する。

  この gate は fail-closed であり、
    - 不正itemだけを落とさない（部分成功を作らない）
    - `shrine_id` を合成しない
    - `id` を identity として代用しない
  `id` は COMPATIBILITY_FIELD であって identity authority ではない（R-2 / #2952）。

  本moduleはDBを引かない。`shrine_id` が実在Shrine行へ解決するかの検証は
  HTTP境界のDB-backed regression（R-1 / #2951）の責務であり、ここでは
  「存在すること・nullでないこと」だけを見る。
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


class CompassPublicProjectionContractError(Exception):
    """Compass Monthly Public Contract の identity 要件違反。

    `require_shrine_id=True` で投影した recommendations[] に、
    `shrine_id` を持たない / `shrine_id is None` のitemが含まれていたときに
    送出される。View はこれを既存の error boundary へ正規化する。

    投影結果は返さない。部分的に投影済みのlistも返さない（fail-closed）。
    """


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


def _assert_identity_contract(source: Any, *, index: int) -> None:
    """R-3 identity gate。`shrine_id` の存在と非nullのみを検査する。

    DBは引かない。`id` の有無は一切見ない（identity authority ではないため、
    `id` があっても `shrine_id` の不在を埋め合わせない）。
    """
    if not isinstance(source, Mapping):
        raise CompassPublicProjectionContractError(
            f"recommendations[{index}] is not a mapping; "
            "recommendation_success items must carry shrine_id"
        )
    if "shrine_id" not in source:
        raise CompassPublicProjectionContractError(
            f"recommendations[{index}] has no shrine_id; "
            "`id` is a compatibility field and is not identity authority"
        )
    if source["shrine_id"] is None:
        raise CompassPublicProjectionContractError(
            f"recommendations[{index}] has shrine_id=None; "
            "recommendation_success requires a non-null shrine_id"
        )


def project_compass_recommendations(
    recommendations: Iterable[Any] | None,
    *,
    recommendation_instance_id: str,
    require_shrine_id: bool,
) -> list[dict[str, Any]]:
    """recommendations[] 全体を投影する。順序と件数は変えない。

    `require_shrine_id` は keyword-only の必須引数。Monthly の呼び出し側が
    ambiguous mode へ暗黙に落ちないよう、既定値を持たせない。
    `state == recommendation_success` のときだけ True を渡す。

    True のとき、1件でも identity 要件を満たさなければ
    `CompassPublicProjectionContractError` を送出し、**何も返さない**。
    部分的に投影したlistは返さない。
    """
    source_items = list(recommendations or [])

    if require_shrine_id:
        # 投影を始める前に全件を検査する。1件でも違反があれば、
        # 有効なitemだけを返す余地を作らない（partial success の禁止）。
        for index, source in enumerate(source_items):
            _assert_identity_contract(source, index=index)

    return [
        project_compass_recommendation(
            recommendation,
            recommendation_instance_id=recommendation_instance_id,
        )
        for recommendation in source_items
    ]


__all__ = [
    "CompassPublicProjectionContractError",
    "COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_BREAKDOWN_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_REASON_FACT_FIELDS",
    "COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST",
    "project_compass_recommendation",
    "project_compass_recommendations",
]
