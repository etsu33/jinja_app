#!/usr/bin/env python
"""Position / Production Identity Integration（P2-B04 / pure adapter）。

B03 の identity evidence を、既存の Seed ↔ Production exact identity flow へ
**別の軸として**持ち込むための純粋な変換層。

## 中心的な不変条件

```text
B03 SAME_SUPPORTED
!=
Seed ↔ Production exact identity
```

normalized / corroborated な identity evidence を `JOIN_MATCH_EXACT` へ
格上げしない。`JOIN_MATCH_EXACT` は従来どおり

```text
raw exact (name_jp, address) で Production 行がちょうど1件
```

だけを意味し、本 module はその意味を変更しない。

## 依存グラフ

```text
B04 adapter  ->  B03 (shrine_identity_evidence)  ->  B02 (canonical address layer)
```

B04 は **B02 を直接 import / load しない**。住所正規化の語彙にも触れず、
B02 の module 名すら本 file に現れない（B02 の consumer allowlist は B03
だけであり、推移的依存を上流の allowlist に載せないため）。
B02 への依存は B03 経由の推移的依存としてのみ存在する。

## 責務の外

* DB / network / filesystem write
* fuzzy discovery
* Production 全体の候補探索

exact join が Production 行を返さず、明示的な候補も B03 assessment も
無い場合は、候補を推測しない。`identity_status = NOT_EVALUATED` のまま
既存の未解決 join status を保つ。候補探索は別責務である。
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# canonical loader（B03 のみ）
# ---------------------------------------------------------------------------
# `scripts/` は package ではないため、既存の canonical loader pattern を使う。
# 同名 module が既に canonical path で読み込まれていれば再利用し、別名での
# 二重読み込みを避ける。B02 はここから直接読み込まない。
_IDENTITY_MODULE_NAME = "shrine_identity_evidence"
_IDENTITY_MODULE_PATH = Path(__file__).resolve().parent / f"{_IDENTITY_MODULE_NAME}.py"


def _load_identity_evidence_module() -> Any:
    cached = sys.modules.get(_IDENTITY_MODULE_NAME)
    if cached is not None and getattr(cached, "__file__", None) == str(
        _IDENTITY_MODULE_PATH
    ):
        return cached
    spec = importlib.util.spec_from_file_location(
        _IDENTITY_MODULE_NAME, _IDENTITY_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[_IDENTITY_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


identity_evidence = _load_identity_evidence_module()


# ---------------------------------------------------------------------------
# join status（Position Audit の値をミラーする）
# ---------------------------------------------------------------------------
# 循環依存を作らないため、Position Audit module を import せず値だけを持つ。
# 両者が同値であることは test が固定する。
JOIN_MATCH_EXACT = "MATCH_EXACT"


# ---------------------------------------------------------------------------
# identity status（join status とは別の閉じた軸）
# ---------------------------------------------------------------------------
# `seed_production_join_status` を上書きしない。別 field として並走させる。
IDENTITY_EXACT = "EXACT"
IDENTITY_SAME_SUPPORTED = "SAME_SUPPORTED"
IDENTITY_REVIEW_REQUIRED = "REVIEW_REQUIRED"
IDENTITY_CONFLICT = "CONFLICT"
IDENTITY_INSUFFICIENT = "INSUFFICIENT"
IDENTITY_NOT_EVALUATED = "NOT_EVALUATED"

SEED_PRODUCTION_IDENTITY_STATUSES = frozenset(
    {
        IDENTITY_EXACT,
        IDENTITY_SAME_SUPPORTED,
        IDENTITY_REVIEW_REQUIRED,
        IDENTITY_CONFLICT,
        IDENTITY_INSUFFICIENT,
        IDENTITY_NOT_EVALUATED,
    }
)

# exact identity と認められるのはこれだけ。
IDENTITY_EXACT_STATUSES = frozenset({IDENTITY_EXACT})

# B03 の evidence status -> identity status（非 exact join のときのみ適用）。
# `EXACT` はこの写像に **現れない**。exact identity は raw exact join だけが
# 生み出せる。
_EVIDENCE_TO_IDENTITY = {
    "SAME_SUPPORTED": IDENTITY_SAME_SUPPORTED,
    "REVIEW_REQUIRED": IDENTITY_REVIEW_REQUIRED,
    "CONFLICT": IDENTITY_CONFLICT,
    "INSUFFICIENT": IDENTITY_INSUFFICIENT,
}


# ---------------------------------------------------------------------------
# identity review reasons
# ---------------------------------------------------------------------------
# `RC_SEED_PRODUCTION_EXACT` とは別語彙にする。混ぜない。
IDENTITY_EVIDENCE_SAME_SUPPORTED = "IDENTITY_EVIDENCE_SAME_SUPPORTED"
IDENTITY_EVIDENCE_REVIEW_REQUIRED = "IDENTITY_EVIDENCE_REVIEW_REQUIRED"
IDENTITY_EVIDENCE_CONFLICT = "IDENTITY_EVIDENCE_CONFLICT"
IDENTITY_EVIDENCE_INSUFFICIENT = "IDENTITY_EVIDENCE_INSUFFICIENT"
IDENTITY_EVIDENCE_NOT_EVALUATED = "IDENTITY_EVIDENCE_NOT_EVALUATED"

IDENTITY_REVIEW_REASONS = frozenset(
    {
        IDENTITY_EVIDENCE_SAME_SUPPORTED,
        IDENTITY_EVIDENCE_REVIEW_REQUIRED,
        IDENTITY_EVIDENCE_CONFLICT,
        IDENTITY_EVIDENCE_INSUFFICIENT,
        IDENTITY_EVIDENCE_NOT_EVALUATED,
    }
)

_IDENTITY_STATUS_TO_REASON = {
    IDENTITY_SAME_SUPPORTED: IDENTITY_EVIDENCE_SAME_SUPPORTED,
    IDENTITY_REVIEW_REQUIRED: IDENTITY_EVIDENCE_REVIEW_REQUIRED,
    IDENTITY_CONFLICT: IDENTITY_EVIDENCE_CONFLICT,
    IDENTITY_INSUFFICIENT: IDENTITY_EVIDENCE_INSUFFICIENT,
    IDENTITY_NOT_EVALUATED: IDENTITY_EVIDENCE_NOT_EVALUATED,
}


@dataclass(frozen=True)
class PositionIdentityIntegrationResult:
    """exact join 結果と B03 evidence を合流させた結果。

    `join_status` は既存の値をそのまま保持する。`identity_status` は
    それとは独立の第2軸であり、`EXACT` は raw exact join からしか生じない。
    """

    join_status: str
    identity_status: str
    production_id: int | None = None
    duplicate_production_ids: tuple[int, ...] = ()
    identity_review_reasons: tuple[str, ...] = ()

    @property
    def identity_is_exact(self) -> bool:
        """Position Audit の exact identity 条件を満たすか。"""
        return self.identity_status in IDENTITY_EXACT_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "join_status": self.join_status,
            "identity_status": self.identity_status,
            "production_id": self.production_id,
            "duplicate_production_ids": list(self.duplicate_production_ids),
            "identity_review_reasons": list(self.identity_review_reasons),
        }


def _evidence_status(assessment: Any) -> str | None:
    """B03 assessment から evidence status を読む。未供給なら None。"""
    if assessment is None:
        return None
    value = getattr(assessment, "identity_evidence_status", None)
    if value is None:
        return None
    text = str(value).strip().upper()
    if text not in identity_evidence.IDENTITY_EVIDENCE_STATUSES:
        # 未知の値を同一性へ寄せない（fail safe）。
        return None
    return text


def integrate_position_identity(
    *,
    join_status: str,
    production_id: int | None = None,
    duplicate_production_ids: tuple[int, ...] = (),
    identity_assessment: Any = None,
) -> PositionIdentityIntegrationResult:
    """exact join 結果に identity evidence 軸を重ねる（純関数）。

    ## 写像

    ```text
    JOIN_MATCH_EXACT                     -> EXACT
    非 exact join + B03 SAME_SUPPORTED   -> SAME_SUPPORTED
    非 exact join + B03 REVIEW_REQUIRED  -> REVIEW_REQUIRED
    非 exact join + B03 CONFLICT         -> CONFLICT
    非 exact join + B03 INSUFFICIENT     -> INSUFFICIENT
    B03 未評価                            -> NOT_EVALUATED
    ```

    `EXACT` は raw exact join だけが生み出す。B03 の evidence がどれほど
    強くても `EXACT` にはならない。

    exact join が成立していれば B03 evidence は identity 軸を上書きしない
    （exact が最強のため）。

    候補探索は行わない。Production 行が見つからず B03 assessment も無い
    場合は、既存の未解決 join status を保ったまま `NOT_EVALUATED` を返す。
    """
    status = str(join_status)

    if status == JOIN_MATCH_EXACT:
        # exact join は identity 軸でも EXACT。B03 はこれを変更しない。
        return PositionIdentityIntegrationResult(
            join_status=status,
            identity_status=IDENTITY_EXACT,
            production_id=production_id,
            duplicate_production_ids=tuple(duplicate_production_ids),
            identity_review_reasons=(),
        )

    evidence_status = _evidence_status(identity_assessment)
    identity_status = _EVIDENCE_TO_IDENTITY.get(
        evidence_status or "", IDENTITY_NOT_EVALUATED
    )
    reason = _IDENTITY_STATUS_TO_REASON[identity_status]
    return PositionIdentityIntegrationResult(
        join_status=status,
        identity_status=identity_status,
        # 非 exact join では Production 行を採用しない（自動採用の禁止）。
        production_id=None,
        duplicate_production_ids=tuple(duplicate_production_ids),
        identity_review_reasons=(reason,),
    )
