# backend/temples/domain/goriyaku_taxonomy_v1.py
"""Evidence Foundation: Goriyaku v1 canonical taxonomy registry。

PR-F1（`evidence_taxonomy.py`）は namespace（"history_theme" / "goriyaku"）と
canonical key format (`<namespace>:<key>`) のみを定義し、実際に有効な
key一覧はF2/F3のHOLD事項として意図的に未定義のままだった。PR-F2は
history_theme側のみを解決し、PR-F3は goriyaku の**構造**だけを解決した
（`GORIYAKU_V1_CANONICAL_KEYS`は意図的に空のまま）。

本モジュールはG1時点の状態を表す。PR-F3のHOLD事項であった canonical key
registryは、Mother Ship DATA_REVIEWで承認された18件のcanonical semantic
identityで**activated済み**である（PR-F3時点の「意図的に空」は当時の
point-in-time recordであり、現行のCURRENT FACTではない）。

G1 canonical mapping（承認済み18件、canonical key → 日本語表示ラベル）:
    relationship_bonding   → 縁結び
    misfortune_warding     → 厄除け
    traffic_safety         → 交通安全
    business_prosperity    → 商売繁盛
    good_fortune           → 開運
    household_safety       → 家内安全
    academic_success       → 学業成就
    exam_success           → 合格祈願
    victory_fortune        → 勝運
    maritime_safety        → 海上安全
    safe_childbirth        → 安産
    all_direction_warding  → 八方除
    career_advancement     → 出世運
    financial_fortune      → 金運
    strong_fortune_warding → 強運厄除け
    illness_recovery       → 病気平癒
    wish_fulfillment       → 心願成就
    leg_lower_back_health  → 足腰健康

canonical keyは機械識別子（machine identity）であり、日本語ラベルは表示値
（display value）に過ぎない。`GoriyakuTag` PK・Purpose・Shrine identityとは
独立した、Evidence Foundation側の識別子体系である。

本モジュールはalias解決を一切行わない（Decision 2の分離を維持）。承認済み
aliasの解決責務は `goriyaku_alias_v1.py` にあり、canonical registryへalias
（表記ゆれ・spelling variant）を混ぜない。`resolve != validate`。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from temples.domain.evidence_taxonomy import (
    TaxonomyNamespace,
    get_current_taxonomy_version,
    validate_canonical_semantic_key,
)

GORIYAKU_TAXONOMY_NAMESPACE: TaxonomyNamespace = "goriyaku"

# PR-F1のtaxonomy version infrastructureをそのまま参照する
# （バージョン番号をここで再定義しない）。
GORIYAKU_TAXONOMY_VERSION = get_current_taxonomy_version(GORIYAKU_TAXONOMY_NAMESPACE).version

# Mother Ship DATA_REVIEW FINAL（G1）: 承認済みcanonical key（ローカル部分、
# namespace prefixなし）→ 日本語表示ラベル。exactly 18件。
#
# この18件はMother Ship DATA_REVIEWで確定した集合をそのまま転記したもので
# あり、Codexがslug生成・英訳・名称変更・追加・削除を行っていない。
# DEFERRED 20 conceptsはこの集合に含まれない（後続DATA_REVIEW事項）。
GORIYAKU_V1_CANONICAL_KEYS: Dict[str, str] = {
    "relationship_bonding": "縁結び",
    "misfortune_warding": "厄除け",
    "traffic_safety": "交通安全",
    "business_prosperity": "商売繁盛",
    "good_fortune": "開運",
    "household_safety": "家内安全",
    "academic_success": "学業成就",
    "exam_success": "合格祈願",
    "victory_fortune": "勝運",
    "maritime_safety": "海上安全",
    "safe_childbirth": "安産",
    "all_direction_warding": "八方除",
    "career_advancement": "出世運",
    "financial_fortune": "金運",
    "strong_fortune_warding": "強運厄除け",
    "illness_recovery": "病気平癒",
    "wish_fulfillment": "心願成就",
    "leg_lower_back_health": "足腰健康",
}

GORIYAKU_V1_CANONICAL_KEY_SET = set(GORIYAKU_V1_CANONICAL_KEYS)


@dataclass(frozen=True)
class GoriyakuV1KeyValidationResult:
    valid: bool
    reason: str
    canonical_key: Optional[str]
    display_label_ja: Optional[str]


def validate_goriyaku_v1_canonical_key(value: Optional[str]) -> GoriyakuV1KeyValidationResult:
    """`<namespace>:<key>`形式の入力を検証し、goriyaku v1の承認済みkeyの
    いずれかであることまで確認する。

    - PR-F1のformat validatorをそのまま利用（namespace/separator/非空key
      のformat検証を重複実装しない）。
    - namespaceが"goriyaku"以外（例: "history_theme:restart"）の場合は
      reject。
    - keyが承認済み18件に含まれない場合はreject（reason=
      "unknown_goriyaku_key"）。fuzzy normalization・日本語ラベルからの
      自動推定・alias解決はここでは一切行わない（alias解決は
      `goriyaku_alias_v1.resolve_goriyaku_alias()`の責務であり、本
      validatorへは統合しない）。
    """
    format_result = validate_canonical_semantic_key(value)

    if not format_result.valid:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason=format_result.reason,
            canonical_key=None,
            display_label_ja=None,
        )

    if format_result.namespace != GORIYAKU_TAXONOMY_NAMESPACE:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason="wrong_namespace",
            canonical_key=None,
            display_label_ja=None,
        )

    key = format_result.key
    if key not in GORIYAKU_V1_CANONICAL_KEY_SET:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason="unknown_goriyaku_key",
            canonical_key=None,
            display_label_ja=None,
        )

    return GoriyakuV1KeyValidationResult(
        valid=True,
        reason="valid",
        canonical_key=f"{GORIYAKU_TAXONOMY_NAMESPACE}:{key}",
        display_label_ja=GORIYAKU_V1_CANONICAL_KEYS[key],
    )


__all__ = [
    "GORIYAKU_TAXONOMY_NAMESPACE",
    "GORIYAKU_TAXONOMY_VERSION",
    "GORIYAKU_V1_CANONICAL_KEYS",
    "GORIYAKU_V1_CANONICAL_KEY_SET",
    "GoriyakuV1KeyValidationResult",
    "validate_goriyaku_v1_canonical_key",
]
