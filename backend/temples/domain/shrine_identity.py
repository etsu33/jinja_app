"""Canonical backend Shrine identity resolver (F-5B).

    SHRINE_IDENTITY_AUTHORITY = Shrine.id
    PUBLIC_IDENTITY_KEY       = shrine_id
    VALID_SHRINE_ID           = POSITIVE_INTEGER_ONLY
    CANONICAL_RESOLVER_MODE   = STRICT_FAIL_CLOSED
    LEGACY_FALSY_FALLBACK     = NO

契約記録:
    docs/audit/backend-shrine-identity-fallback-consolidation.md  (F-5A / F-5B)
    docs/audit/shrine-identity-compass-concierge-contract.md
    docs/audit/shared-shrine-identity-resolver-design.md          (F-3.1, Web 側)

本 module は backend における **唯一の** Shrine identity 解決実装である。
consumer は正規化・alias 優先順位・conflict 判定をローカルに再実装しない。

`domain/` に置く理由（F-5A §5.2 の依存実測）:

    domain/  -> services/   0 件
    services/ -> domain/    10+ module

layer 方向は services/ -> domain/ の一方向であり、`domain/weekly_presentation.py`
が consumer に含まれる（F-5A #14）。`services/` に置くとその 1 件だけが
既存の一方向依存を破る。

identity として **決して** 採用しないもの:
    place_id / placeId / place.id / Google Places id  -- F-6 のスコープ
    name / address / 座標 / anchor

`int(True) == 1` / `int(1.5) == 1` による誤解決を構造的に塞ぐ。
例外を投げない。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Optional

__all__ = [
    "ShrineIdentityPolicy",
    "ShrineIdentityResolution",
    "resolve_shrine_identity",
    "resolve_shrine_id",
]


#: 解決 policy。既定値は持たせない -- 呼び出し側が必ず明示する。
ShrineIdentityPolicy = Literal["live_candidate", "historical_snapshot"]


@dataclass(frozen=True)
class ShrineIdentityResolution:
    """解決結果。status を潰さずに保つ（Web 側 F-3.1 と同じ形）。

    非 identity fallback（place_id 導線、name 突合など）を持つ consumer は
    必ず `status` で分岐すること。「identity が主張されていない」(`absent`) と
    「identity は主張されているが使えない」(`invalid` / `conflict`) では
    取るべき挙動が逆になる。
    """

    status: Literal["resolved", "absent", "invalid", "conflict"]
    shrine_id: Optional[int]


_ABSENT = ShrineIdentityResolution(status="absent", shrine_id=None)
_INVALID = ShrineIdentityResolution(status="invalid", shrine_id=None)
_CONFLICT = ShrineIdentityResolution(status="conflict", shrine_id=None)


#: policy ごとの許可 alias。宣言順がそのまま読み取り順。
_LIVE_CANDIDATE_KEYS: tuple[str, ...] = ("shrine_id", "id")
_HISTORICAL_SNAPSHOT_KEYS: tuple[str, ...] = ("shrine_id", "shrineId", "shrine", "id")


def _allowed_keys(policy: ShrineIdentityPolicy) -> Optional[tuple[str, ...]]:
    if policy == "live_candidate":
        return _LIVE_CANDIDATE_KEYS
    if policy == "historical_snapshot":
        return _HISTORICAL_SNAPSHOT_KEYS
    return None


def _normalize(value: Any) -> Optional[int]:
    """許可 alias の値 1 個を正の整数 Shrine PK へ正規化する。

    ACCEPT  42, "42"
    REJECT  0, "0", 負数, 負数文字列, float, float 文字列, bool,
            空白のみの文字列, 非数値文字列, それ以外すべて

    bool は int のサブクラスなので **必ず先に** 弾く。`int(True) == 1` を
    許すと `True` が Shrine 1 に化ける（F-5A §3.1 D-2）。
    """
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str):
        stripped = value.strip()
        # 数字のみ。"-1" / "1.5" / "1e3" / "" / " " / "abc" / "０" を弾く。
        # str.isdigit() は全角数字や上付き数字も True にするため ASCII を明示する。
        if not stripped or not all(c in "0123456789" for c in stripped):
            return None
        parsed = int(stripped)
        return parsed if parsed > 0 else None

    return None


def resolve_shrine_identity(
    source: Any,
    *,
    policy: ShrineIdentityPolicy,
) -> ShrineIdentityResolution:
    """Authoritative resolver。

    status:
        absent    許可 alias が 1 つも present でない（Mapping でない場合も含む）
        invalid   present な許可 alias のうち 1 つでも正規化できない
        conflict  2 つ以上の有効な alias が異なる値へ正規化される
        resolved  present な有効 alias がすべて同じ値へ正規化される

    presence:
        key が存在し、かつ値が None でないとき **のみ** present。
        したがって ``{"shrine_id": None, "id": 42}`` は shrine_id が absent で
        あり、id が 42 へ解決される。

    precedence:
        absent -> invalid -> conflict -> resolved
        `invalid` を `conflict` / `resolved` より先に評価する。壊れた alias が
        有効な alias と同居する状態は fail closed とする（INVALID_WINS）。

    例外は投げない。
    """
    keys = _allowed_keys(policy)
    # 未知の policy: absent へ倒すと呼び出し側の非 identity fallback を
    # 開いてしまうため invalid（fail closed）。
    if keys is None:
        return _INVALID

    if not isinstance(source, Mapping):
        return _ABSENT

    present_count = 0
    saw_unusable = False
    normalized: set[int] = set()

    for key in keys:
        raw = source.get(key)
        if raw is None:
            continue

        present_count += 1
        value = _normalize(raw)
        if value is None:
            saw_unusable = True
            continue
        normalized.add(value)

    if present_count == 0:
        return _ABSENT
    if saw_unusable:
        return _INVALID
    if len(normalized) > 1:
        return _CONFLICT

    return ShrineIdentityResolution(status="resolved", shrine_id=normalized.pop())


def resolve_shrine_id(
    source: Any,
    *,
    policy: ShrineIdentityPolicy,
) -> Optional[int]:
    """Convenience wrapper。`resolve_shrine_identity()` へ委譲するだけ。

    identity 解決の実装は 1 つしか存在しない。

    非 identity fallback（name 突合 / place_id 導線 / reporting sentinel）を
    持つ consumer は `resolve_shrine_identity()` を使い、`absent` と
    `invalid` / `conflict` を区別すること。
    """
    return resolve_shrine_identity(source, policy=policy).shrine_id
