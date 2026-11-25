# backend/temples/domain/goriyaku_alias_v1.py
"""Evidence Foundation G1: Goriyaku v1 alias registry / resolver。

canonical registry（`goriyaku_taxonomy_v1.GORIYAKU_V1_CANONICAL_KEYS`）は
承認済みsemantic identityの集合であり、そこへalias（表記ゆれ・spelling
variant）を混ぜない。本モジュールはその分離を保つために独立して存在する。

責務は3つだけ:
    1. `GORIYAKU_V1_ALIASES`（承認済みalias registry）
    2. immutable alias resolution result
    3. alias resolver（pure / deterministic / DB-free）

`resolve != validate`:
    alias resolverは「surface stringを承認済みcanonical identityへ写す」
    責務のみを持つ。canonical key format / namespace / v1 registry
    membershipの検証は、既存の
    `goriyaku_taxonomy_v1.validate_goriyaku_v1_canonical_key()`の責務であり、
    そちらへalias lookup・日本語label lookup・fuzzy normalizationを
    追加しない。

    公式flow:
        surface alias
        -> resolve_goriyaku_alias()
        -> canonical full key
        -> validate_goriyaku_v1_canonical_key()

Exact-Match Contract（Mother Ship FINAL）:
    alias lookup前にpreprocessingを一切行わない。strip / lower / replace /
    Unicode normalization / prefix match / suffix match / substring match /
    regex normalization / delimiter splitのいずれも禁止であり、唯一の一致
    条件はexact string equalityである。

    したがって whitespace-only string（半角/全角問わず）もstripされず、
    registryに存在しないsurfaceとしてunknown_aliasになる（invalid_input
    ではない）。

Fuzzy Normalizationは全面禁止:
    spelling similarity / semantic similarity / LLM inference / embedding
    similarity / 自動suffix・prefix除去 / Recommendation mapping fallback /
    legacy GoriyakuTag fallbackのいずれも行わない。unknown aliasは
    「invalid concept」ではなく「v1で未解決」を意味するため、例外ではなく
    resolved=False / reason="unknown_alias"として返す。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_TAXONOMY_NAMESPACE,
    GORIYAKU_V1_CANONICAL_KEYS,
)

# Mother Ship DATA_REVIEW FINAL（G1）: 承認済みalias（surface string）→
# canonical local key。exactly 1件。
#
# `八方除`はcanonical display labelそのものであり、aliasではないため
# ここには登録しない（canonical display labelをalias registryへ混ぜると、
# alias registryがcanonical registryの写しになってしまう）。
GORIYAKU_V1_ALIASES: Dict[str, str] = {
    "八方除け": "all_direction_warding",
}

GORIYAKU_V1_ALIAS_SURFACE_SET = set(GORIYAKU_V1_ALIASES)


@dataclass(frozen=True)
class GoriyakuAliasResolutionResult:
    """alias解決結果のimmutable contract。

    reason vocabulary（4状態、意味を変更しない）:
        - "resolved"             : exact registered aliasを解決した
        - "unknown_alias"        : v1 alias registryに存在しないsurface
        - "invalid_input"        : resolver contractに適合しない入力
        - "invalid_alias_target" : alias targetがcanonical registryに不在
    """

    resolved: bool
    reason: str
    input_alias: Optional[str]
    canonical_key: Optional[str]
    display_label_ja: Optional[str]


def _failure(reason: str, input_alias: Optional[str]) -> GoriyakuAliasResolutionResult:
    return GoriyakuAliasResolutionResult(
        resolved=False,
        reason=reason,
        input_alias=input_alias,
        canonical_key=None,
        display_label_ja=None,
    )


def resolve_goriyaku_alias(value: Optional[str]) -> GoriyakuAliasResolutionResult:
    """1件のsurface stringを、承認済みcanonical identityへ解決する。

    pure / deterministic / DB-free。同じ入力に対して常に同じ結果を返し、
    DB・現在時刻・LLM・外部APIへ依存しない。

    - invalid input（None / non-string / empty string）はfail closedで
      reason="invalid_input"。
    - exact string equalityで一致しないsurfaceはreason="unknown_alias"
      （例外は送出しない。「v1で未解決」であって「invalid concept」では
      ないため）。
    - alias targetがcanonical registryに存在しない場合は
      reason="invalid_alias_target"。fake full canonical keyを生成して
      後工程へ流さない。
    """
    if not isinstance(value, str):
        return _failure("invalid_input", None)

    # 意図的にstrip / normalizeしない。空文字だけがinvalid_inputであり、
    # whitespace-only stringはregistryに無いsurfaceとしてunknown_alias。
    if value == "":
        return _failure("invalid_input", value)

    local_key = GORIYAKU_V1_ALIASES.get(value)
    if local_key is None:
        return _failure("unknown_alias", value)

    display_label_ja = GORIYAKU_V1_CANONICAL_KEYS.get(local_key)
    if display_label_ja is None:
        return _failure("invalid_alias_target", value)

    return GoriyakuAliasResolutionResult(
        resolved=True,
        reason="resolved",
        input_alias=value,
        canonical_key=f"{GORIYAKU_TAXONOMY_NAMESPACE}:{local_key}",
        display_label_ja=display_label_ja,
    )


__all__ = [
    "GORIYAKU_V1_ALIASES",
    "GORIYAKU_V1_ALIAS_SURFACE_SET",
    "GoriyakuAliasResolutionResult",
    "resolve_goriyaku_alias",
]
