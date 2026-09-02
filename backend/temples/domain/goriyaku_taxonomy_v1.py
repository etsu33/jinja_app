# backend/temples/domain/goriyaku_taxonomy_v1.py
"""Evidence Foundation PR-F3: Goriyaku v1 canonical taxonomy registry.

PR-F1（`evidence_taxonomy.py`）は namespace（"history_theme" / "goriyaku"）と
canonical key format (`<namespace>:<key>`) のみを定義し、実際に有効な
key一覧はF2/F3のHOLD事項として意図的に未定義のままだった。PR-F2は
history_theme側のみを解決した。

本モジュールは、その残りのHOLD事項のうち goriyaku の**構造**だけを解決する。
PR-F1のformat validator (`validate_canonical_semantic_key`) をそのまま
再利用し、format検証ロジックを重複させない。

重要（Mother Ship FINAL、Decision 1 = Option B）:
    46件の既存GoriyakuTagに対応する具体的canonical key（例:
    "goriyaku:enmusubi"）は、本PRでは一切登録しない。
    `GORIYAKU_V1_CANONICAL_KEYS`は意図的に空である。

    これは未完成ではなく、意図されたfail-closed状態である:
    承認済みcanonical keyがまだ存在しないため、どのgoriyaku:*キーも
    現時点では有効なEvidence Foundation semantic identityとして
    受理されない。Codexはこの空集合へ、テストのためであっても
    具体的なkeyを追加しない（canonical key発明の禁止、Decision 1で
    確定）。実際のkey命名・46件対応表の確定は、後続のDATA_REVIEWで
    Mother Shipが行う。

    duplicate / near-duplicate（表記差・spelling variant等）の扱いも
    同様にDecision 2としてDATA_REVIEWへ分離されており、本モジュールは
    一切のnormalization / alias解決を行わない（Decision 2 = Option B）。
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

# Mother Ship FINAL（Decision 1 = Option B）: PR-F3時点では意図的に空。
# 46件のGoriyakuTagへのcanonical key割当はDATA_REVIEW事項であり、
# Codexが日本語ラベルからslugを生成することは禁止されている。
# この辞書が空である限り、validate_goriyaku_v1_canonical_key()は
# いかなる`goriyaku:<key>`も無条件でreject する（fail-closed）。
GORIYAKU_V1_CANONICAL_KEYS: Dict[str, str] = {}

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
    - `GORIYAKU_V1_CANONICAL_KEYS`が空である現時点では、format・namespace
      が正しくても、keyが承認済み集合に含まれることは決してないため、
      常にreject結果（reason="unknown_goriyaku_key"）を返す。これは
      意図されたfail-closed動作であり、バグではない。
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
