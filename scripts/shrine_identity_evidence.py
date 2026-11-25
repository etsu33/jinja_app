#!/usr/bin/env python
"""Address Identity Evidence Layer（P2-B03 / deterministic / side-effect free）。

B02 の canonical な住所 evidence と、住所以外の明示的な identity evidence を
組み合わせて **identity evidence assessment** を返す。

## 位置づけ

```text
raw addresses
→ B02 canonical lexical + structured normalization
→ AddressComparisonResult
→ B03 identity evidence assessment   ← 本 module
→ later B04 Position / Production integration
```

本 module は **entity の最終判定を行わない**。`SAME` / `DIFFERENT` /
`NON_SHRINE` は返さず、下流の責務として残す。返すのは
「同一だと支持する evidence が揃っているか」という assessment だけである。

## canonical / legacy の境界

Stage 1 の canonical 実装は

```text
scripts/japanese_address_normalization.py::lexical_normalize
```

であり、本 module はそれだけを使う。

```text
scripts/audit_shrine_positions_v2.py::normalize_address
```

は legacy behavior として残るが、**import も呼び出しもしない**。両者は
U+30FC `ー` の扱いが意図的に異なる。legacy を本 PR で移行・統合しない。

legacy 正規化済みの住所しか無く、canonical 評価に必要な raw address が
無い場合は、同値だと推測しない。`address_comparison=None` として
fail safe に `INSUFFICIENT` へ倒す。

## Foundation only

本 module はまだどこからも呼ばれていない。Position Audit / Production join /
Shrine 永続化 / Recommendation / Compass / Ranking との結線は P2-B04 の
scope である。

## 純粋性

評価 core は純関数であり、DB / ORM / network / filesystem write /
environment variable に依存しない。同じ入力からは常に同じ構造・同じ順序を返す。
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# canonical な B02 住所 module の読み込み
# ---------------------------------------------------------------------------
# `scripts/` は package ではないため、兄弟 module を明示的な path で読む。
# 読むのは **canonical な B02 実装だけ**であり、legacy Position Audit の
# 正規化には触れない。import 時の read 以外に I/O を行わない。
_ADDRESS_MODULE_NAME = "japanese_address_normalization"
_ADDRESS_MODULE_PATH = Path(__file__).resolve().parent / f"{_ADDRESS_MODULE_NAME}.py"


def _load_canonical_address_module() -> Any:
    cached = sys.modules.get(_ADDRESS_MODULE_NAME)
    if cached is not None and getattr(cached, "__file__", None) == str(
        _ADDRESS_MODULE_PATH
    ):
        return cached
    spec = importlib.util.spec_from_file_location(
        _ADDRESS_MODULE_NAME, _ADDRESS_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[_ADDRESS_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


address_contract = _load_canonical_address_module()

# B02 の住所 evidence 語彙をそのまま再公開する（再定義・再実装しない）。
ADDRESS_EXACT_MATCH = address_contract.ADDRESS_EXACT_MATCH
ADDRESS_NORMALIZED_MATCH = address_contract.ADDRESS_NORMALIZED_MATCH
ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF = (
    address_contract.ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF
)
ADDRESS_DIFFERENT = address_contract.ADDRESS_DIFFERENT
ADDRESS_AMBIGUOUS = address_contract.ADDRESS_AMBIGUOUS
ADDRESS_UNSUPPORTED = address_contract.ADDRESS_UNSUPPORTED
ADDRESS_IDENTITY_STATUSES = address_contract.ADDRESS_IDENTITY_STATUSES

compare_addresses = address_contract.compare_addresses
lexical_normalize = address_contract.lexical_normalize


# ---------------------------------------------------------------------------
# 入力 evidence の閉じた enum
# ---------------------------------------------------------------------------

# --- name identity ---
# 類似度を自動的な identity 証明に使わない。`NAME_ALIAS_CONFIRMED` は
# **明示的な alias evidence** を要求し、文字列類似から導出してはならない。
NAME_EXACT_MATCH = "NAME_EXACT_MATCH"
NAME_NORMALIZED_MATCH = "NAME_NORMALIZED_MATCH"
NAME_ALIAS_CONFIRMED = "NAME_ALIAS_CONFIRMED"
NAME_DIFFERENT = "NAME_DIFFERENT"
NAME_AMBIGUOUS = "NAME_AMBIGUOUS"
NAME_UNSUPPORTED = "NAME_UNSUPPORTED"

NAME_IDENTITY_STATUSES = frozenset(
    {
        NAME_EXACT_MATCH,
        NAME_NORMALIZED_MATCH,
        NAME_ALIAS_CONFIRMED,
        NAME_DIFFERENT,
        NAME_AMBIGUOUS,
        NAME_UNSUPPORTED,
    }
)

# --- official source entity ---
OFFICIAL_SOURCE_SAME = "OFFICIAL_SOURCE_SAME"
OFFICIAL_SOURCE_DIFFERENT = "OFFICIAL_SOURCE_DIFFERENT"
OFFICIAL_SOURCE_AMBIGUOUS = "OFFICIAL_SOURCE_AMBIGUOUS"
OFFICIAL_SOURCE_UNAVAILABLE = "OFFICIAL_SOURCE_UNAVAILABLE"

OFFICIAL_SOURCE_ENTITY_STATUSES = frozenset(
    {
        OFFICIAL_SOURCE_SAME,
        OFFICIAL_SOURCE_DIFFERENT,
        OFFICIAL_SOURCE_AMBIGUOUS,
        OFFICIAL_SOURCE_UNAVAILABLE,
    }
)

# --- Place ID ---
PLACE_ID_MATCH = "PLACE_ID_MATCH"
PLACE_ID_DIFFERENT = "PLACE_ID_DIFFERENT"
PLACE_ID_UNAVAILABLE = "PLACE_ID_UNAVAILABLE"

PLACE_ID_STATUSES = frozenset(
    {PLACE_ID_MATCH, PLACE_ID_DIFFERENT, PLACE_ID_UNAVAILABLE}
)

# --- existing resolution ---
RESOLUTION_SAME = "RESOLUTION_SAME"
RESOLUTION_DIFFERENT = "RESOLUTION_DIFFERENT"
RESOLUTION_UNAVAILABLE = "RESOLUTION_UNAVAILABLE"

EXISTING_RESOLUTION_STATUSES = frozenset(
    {RESOLUTION_SAME, RESOLUTION_DIFFERENT, RESOLUTION_UNAVAILABLE}
)


# ---------------------------------------------------------------------------
# 出力 status
# ---------------------------------------------------------------------------
# entity の canonical verdict（`SAME` / `DIFFERENT` / `NON_SHRINE`）ではない。
SAME_SUPPORTED = "SAME_SUPPORTED"
CONFLICT = "CONFLICT"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
INSUFFICIENT = "INSUFFICIENT"

IDENTITY_EVIDENCE_STATUSES = frozenset(
    {SAME_SUPPORTED, CONFLICT, REVIEW_REQUIRED, INSUFFICIENT}
)


# ---------------------------------------------------------------------------
# 評価に使う集合
# ---------------------------------------------------------------------------

# 同一性を支持できる name evidence。
USABLE_NAME_EVIDENCE = frozenset(
    {NAME_EXACT_MATCH, NAME_NORMALIZED_MATCH, NAME_ALIAS_CONFIRMED}
)

# 同一住所として使える address evidence。
# `ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF` は **含めない**（B03 v1）。
USABLE_ADDRESS_EVIDENCE = frozenset({ADDRESS_EXACT_MATCH, ADDRESS_NORMALIZED_MATCH})

# 住所・名称から独立した corroborator。最低1つを要求する。
INDEPENDENT_CORROBORATORS = frozenset(
    {OFFICIAL_SOURCE_SAME, PLACE_ID_MATCH, RESOLUTION_SAME}
)

# 明示的に供給されたときに最優先で CONFLICT を生む evidence。
# **`ADDRESS_DIFFERENT` は含めない。** 法人住所 / 参拝者向け住所 / 歴史的
# 住所の差が実在するため、住所差だけで別神社とはみなさない。
EXPLICIT_TRUSTED_CONFLICTS = frozenset(
    {
        NAME_DIFFERENT,
        OFFICIAL_SOURCE_DIFFERENT,
        PLACE_ID_DIFFERENT,
        RESOLUTION_DIFFERENT,
    }
)

# 同一性を支持する向きの evidence（報告用）。
SUPPORTING_EVIDENCE_VALUES = frozenset(
    USABLE_NAME_EVIDENCE | USABLE_ADDRESS_EVIDENCE | INDEPENDENT_CORROBORATORS
)

# 乖離を表す evidence（報告用）。`ADDRESS_DIFFERENT` はここには入るが、
# `EXPLICIT_TRUSTED_CONFLICTS` ではないので単独で CONFLICT にはしない。
CONFLICTING_EVIDENCE_VALUES = frozenset(
    EXPLICIT_TRUSTED_CONFLICTS | {ADDRESS_DIFFERENT}
)

# serialize 順を固定する canonical order。集合順を出力に漏らさない。
EVIDENCE_ORDER = (
    NAME_EXACT_MATCH,
    NAME_NORMALIZED_MATCH,
    NAME_ALIAS_CONFIRMED,
    NAME_DIFFERENT,
    NAME_AMBIGUOUS,
    NAME_UNSUPPORTED,
    ADDRESS_EXACT_MATCH,
    ADDRESS_NORMALIZED_MATCH,
    ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF,
    ADDRESS_DIFFERENT,
    ADDRESS_AMBIGUOUS,
    ADDRESS_UNSUPPORTED,
    OFFICIAL_SOURCE_SAME,
    OFFICIAL_SOURCE_DIFFERENT,
    OFFICIAL_SOURCE_AMBIGUOUS,
    OFFICIAL_SOURCE_UNAVAILABLE,
    PLACE_ID_MATCH,
    PLACE_ID_DIFFERENT,
    PLACE_ID_UNAVAILABLE,
    RESOLUTION_SAME,
    RESOLUTION_DIFFERENT,
    RESOLUTION_UNAVAILABLE,
)
_EVIDENCE_RANK = {value: index for index, value in enumerate(EVIDENCE_ORDER)}


# ---------------------------------------------------------------------------
# review reasons
# ---------------------------------------------------------------------------
REASON_EXPLICIT_IDENTITY_CONFLICT = "EXPLICIT_IDENTITY_CONFLICT"
REASON_NAME_EVIDENCE_UNAVAILABLE = "NAME_EVIDENCE_UNAVAILABLE"
REASON_NAME_EVIDENCE_AMBIGUOUS = "NAME_EVIDENCE_AMBIGUOUS"
REASON_ADDRESS_EVIDENCE_UNAVAILABLE = "ADDRESS_EVIDENCE_UNAVAILABLE"
REASON_ADDRESS_EVIDENCE_UNSUPPORTED = "ADDRESS_EVIDENCE_UNSUPPORTED"
REASON_ADDRESS_EVIDENCE_AMBIGUOUS = "ADDRESS_EVIDENCE_AMBIGUOUS"
REASON_ADDRESS_COMPONENT_DIFFERENCE = "ADDRESS_COMPONENT_DIFFERENCE"
REASON_ADDRESS_DIFFERENT_WITHOUT_TRUSTED_CONFLICT = (
    "ADDRESS_DIFFERENT_WITHOUT_TRUSTED_CONFLICT"
)
REASON_OFFICIAL_SOURCE_AMBIGUOUS = "OFFICIAL_SOURCE_AMBIGUOUS_EVIDENCE"
REASON_INDEPENDENT_CORROBORATION_MISSING = "INDEPENDENT_CORROBORATION_MISSING"
REASON_UNKNOWN_EVIDENCE_VALUE = "UNKNOWN_EVIDENCE_VALUE"

REVIEW_REASON_ORDER = (
    REASON_EXPLICIT_IDENTITY_CONFLICT,
    REASON_NAME_EVIDENCE_UNAVAILABLE,
    REASON_NAME_EVIDENCE_AMBIGUOUS,
    REASON_ADDRESS_EVIDENCE_UNAVAILABLE,
    REASON_ADDRESS_EVIDENCE_UNSUPPORTED,
    REASON_ADDRESS_EVIDENCE_AMBIGUOUS,
    REASON_ADDRESS_COMPONENT_DIFFERENCE,
    REASON_ADDRESS_DIFFERENT_WITHOUT_TRUSTED_CONFLICT,
    REASON_OFFICIAL_SOURCE_AMBIGUOUS,
    REASON_INDEPENDENT_CORROBORATION_MISSING,
    REASON_UNKNOWN_EVIDENCE_VALUE,
)
REVIEW_REASONS = frozenset(REVIEW_REASON_ORDER)
_REVIEW_REASON_RANK = {reason: index for index, reason in enumerate(REVIEW_REASON_ORDER)}


# ---------------------------------------------------------------------------
# 出力 model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentityEvidenceAssessment:
    """identity evidence の評価結果。

    `identity_evidence_status` は **entity の verdict ではない**。
    `SAME` / `DIFFERENT` / `NON_SHRINE` を確定するのは下流の責務である。
    """

    identity_evidence_status: str

    name_identity_status: str
    address_identity_status: str
    official_source_entity_status: str
    place_id_status: str
    existing_resolution_status: str

    supporting_evidence: tuple[str, ...] = ()
    conflicting_evidence: tuple[str, ...] = ()
    review_reasons: tuple[str, ...] = ()

    # 追跡用。B02 の比較結果そのもの（serialize 対象外）。
    address_comparison: Any = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        """決定的な serialize（key 順は定義順で固定）。"""
        return {
            "identity_evidence_status": self.identity_evidence_status,
            "name_identity_status": self.name_identity_status,
            "address_identity_status": self.address_identity_status,
            "official_source_entity_status": self.official_source_entity_status,
            "place_id_status": self.place_id_status,
            "existing_resolution_status": self.existing_resolution_status,
            "supporting_evidence": list(self.supporting_evidence),
            "conflicting_evidence": list(self.conflicting_evidence),
            "review_reasons": list(self.review_reasons),
        }


def _order_evidence(values: list[str]) -> tuple[str, ...]:
    unique = {value for value in values if value in _EVIDENCE_RANK}
    return tuple(sorted(unique, key=lambda value: _EVIDENCE_RANK[value]))


def _order_reasons(reasons: list[str]) -> tuple[str, ...]:
    unique = {reason for reason in reasons if reason in _REVIEW_REASON_RANK}
    return tuple(sorted(unique, key=lambda reason: _REVIEW_REASON_RANK[reason]))


def _normalize(
    value: str | None,
    allowed: frozenset[str],
    fallback: str,
    unknown_reasons: list[str],
) -> str:
    """未知の値を fail safe に倒す。推測で同一性へ寄せない。"""
    if value is None:
        return fallback
    text = str(value).strip().upper()
    if not text:
        return fallback
    if text in allowed:
        return text
    unknown_reasons.append(REASON_UNKNOWN_EVIDENCE_VALUE)
    return fallback


def assess_identity_evidence(
    *,
    address_comparison: Any = None,
    name_identity_status: str | None = None,
    official_source_entity_status: str | None = None,
    place_id_status: str | None = None,
    existing_resolution_status: str | None = None,
) -> IdentityEvidenceAssessment:
    """identity evidence を決定的に評価する（純関数）。

    `address_comparison` は B02 の `compare_addresses()` の戻り値である。
    本 module は住所正規化を再実装せず、その結果だけを消費する。

    `address_comparison=None` は「canonical に評価できる住所 evidence が
    無い」ことを表す。legacy 正規化済みの文字列しか無く raw address が
    無い場合がこれにあたり、同値だと推測せず `INSUFFICIENT` へ倒す。

    ## 判定順（決定的）

    ```text
    1. explicit trusted conflict         -> CONFLICT
    2. unsupported / missing mandatory   -> INSUFFICIENT
    3. ambiguous name or address         -> REVIEW_REQUIRED
    4. address divergence                -> REVIEW_REQUIRED
    5. SAME_SUPPORTED eligibility        -> SAME_SUPPORTED
    6. otherwise                         -> INSUFFICIENT
    ```

    多数決を行わない。同一性を支持する signal が blocking conflict を
    打ち消すことはない。

    ### 4 の補足（必要な精緻化）

    元の方針は「address component difference」だけを 4 に置いていたが、
    `ADDRESS_DIFFERENT` も住所レベルの乖離であり、明示的な trusted
    conflict が無い限り `REVIEW_REQUIRED` にする必要がある（住所差だけで
    別神社とはみなさない）。両者を 4 の「住所乖離」としてまとめた。
    どちらも `REVIEW_REQUIRED` であり、優先順位の意味は変えていない。
    """
    unknown_reasons: list[str] = []

    name_status = _normalize(
        name_identity_status, NAME_IDENTITY_STATUSES, NAME_UNSUPPORTED, unknown_reasons
    )
    official_status = _normalize(
        official_source_entity_status,
        OFFICIAL_SOURCE_ENTITY_STATUSES,
        OFFICIAL_SOURCE_UNAVAILABLE,
        unknown_reasons,
    )
    place_status = _normalize(
        place_id_status, PLACE_ID_STATUSES, PLACE_ID_UNAVAILABLE, unknown_reasons
    )
    resolution_status = _normalize(
        existing_resolution_status,
        EXISTING_RESOLUTION_STATUSES,
        RESOLUTION_UNAVAILABLE,
        unknown_reasons,
    )

    # --- 住所 evidence は B02 の結果をそのまま読む ------------------------
    address_evidence_unavailable = address_comparison is None
    if address_evidence_unavailable:
        address_status = ADDRESS_UNSUPPORTED
    else:
        address_status = _normalize(
            getattr(address_comparison, "address_identity_status", None),
            ADDRESS_IDENTITY_STATUSES,
            ADDRESS_UNSUPPORTED,
            unknown_reasons,
        )

    statuses = [
        name_status,
        address_status,
        official_status,
        place_status,
        resolution_status,
    ]
    supporting = _order_evidence(
        [value for value in statuses if value in SUPPORTING_EVIDENCE_VALUES]
    )
    conflicting = _order_evidence(
        [value for value in statuses if value in CONFLICTING_EVIDENCE_VALUES]
    )

    reasons = list(unknown_reasons)
    if official_status == OFFICIAL_SOURCE_AMBIGUOUS:
        reasons.append(REASON_OFFICIAL_SOURCE_AMBIGUOUS)

    def _result(status: str, extra_reasons: list[str]) -> IdentityEvidenceAssessment:
        return IdentityEvidenceAssessment(
            identity_evidence_status=status,
            name_identity_status=name_status,
            address_identity_status=address_status,
            official_source_entity_status=official_status,
            place_id_status=place_status,
            existing_resolution_status=resolution_status,
            supporting_evidence=supporting,
            conflicting_evidence=conflicting,
            review_reasons=_order_reasons(reasons + extra_reasons),
            address_comparison=address_comparison,
        )

    # =====================================================================
    # 1. explicit trusted conflict（最優先）
    # =====================================================================
    # 多数決にしない。PLACE_ID_MATCH のような同一支持 signal があっても
    # blocking conflict を打ち消さない。
    if any(value in EXPLICIT_TRUSTED_CONFLICTS for value in statuses):
        return _result(CONFLICT, [REASON_EXPLICIT_IDENTITY_CONFLICT])

    # =====================================================================
    # 2. unsupported / missing mandatory evidence
    # =====================================================================
    # name と address は必須軸である。どちらかが評価不能なら、他の
    # corroborator がいくつあっても同一性を支持できない。
    mandatory_reasons: list[str] = []
    if name_status == NAME_UNSUPPORTED:
        mandatory_reasons.append(REASON_NAME_EVIDENCE_UNAVAILABLE)
    if address_status == ADDRESS_UNSUPPORTED:
        mandatory_reasons.append(
            REASON_ADDRESS_EVIDENCE_UNAVAILABLE
            if address_evidence_unavailable
            else REASON_ADDRESS_EVIDENCE_UNSUPPORTED
        )
    if mandatory_reasons:
        return _result(INSUFFICIENT, mandatory_reasons)

    # =====================================================================
    # 3. ambiguous name or address
    # =====================================================================
    ambiguous_reasons: list[str] = []
    if name_status == NAME_AMBIGUOUS:
        ambiguous_reasons.append(REASON_NAME_EVIDENCE_AMBIGUOUS)
    if address_status == ADDRESS_AMBIGUOUS:
        ambiguous_reasons.append(REASON_ADDRESS_EVIDENCE_AMBIGUOUS)
    if ambiguous_reasons:
        return _result(REVIEW_REQUIRED, ambiguous_reasons)

    # =====================================================================
    # 4. address divergence（component 差 / 住所差）
    # =====================================================================
    # 建物の自動 reconciliation は B03 v1 では実装しない。
    if address_status == ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF:
        return _result(REVIEW_REQUIRED, [REASON_ADDRESS_COMPONENT_DIFFERENCE])
    # 住所差だけで別神社とはみなさない（法人 / 参拝者向け / 歴史的住所）。
    if address_status == ADDRESS_DIFFERENT:
        return _result(
            REVIEW_REQUIRED, [REASON_ADDRESS_DIFFERENT_WITHOUT_TRUSTED_CONFLICT]
        )

    # =====================================================================
    # 5. SAME_SUPPORTED eligibility
    # =====================================================================
    # 住所 evidence だけからは決して導かない。
    has_usable_name = name_status in USABLE_NAME_EVIDENCE
    has_usable_address = address_status in USABLE_ADDRESS_EVIDENCE
    has_corroborator = any(
        value in INDEPENDENT_CORROBORATORS for value in statuses
    )
    if has_usable_name and has_usable_address and has_corroborator:
        return _result(SAME_SUPPORTED, [])

    # =====================================================================
    # 6. otherwise
    # =====================================================================
    remaining: list[str] = []
    if has_usable_name and has_usable_address and not has_corroborator:
        remaining.append(REASON_INDEPENDENT_CORROBORATION_MISSING)
    return _result(INSUFFICIENT, remaining)


def assess_identity_evidence_from_addresses(
    *,
    left_address: str | None,
    right_address: str | None,
    name_identity_status: str | None = None,
    official_source_entity_status: str | None = None,
    place_id_status: str | None = None,
    existing_resolution_status: str | None = None,
) -> IdentityEvidenceAssessment:
    """raw address から canonical に評価する便宜関数。

    住所は **必ず raw address** を渡すこと。legacy 正規化済みの文字列を
    raw のつもりで渡してはならない（U+30FC の扱いが異なるため、
    canonical 評価の前提が崩れる）。raw が無い場合は
    `assess_identity_evidence(address_comparison=None, ...)` を使う。
    """
    comparison = compare_addresses(left_address, right_address)
    return assess_identity_evidence(
        address_comparison=comparison,
        name_identity_status=name_identity_status,
        official_source_entity_status=official_source_entity_status,
        place_id_status=place_id_status,
        existing_resolution_status=existing_resolution_status,
    )
