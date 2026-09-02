# backend/temples/domain/history_theme_taxonomy_v1.py
"""Evidence Foundation PR-F2: HistoryTheme v1 canonical taxonomy registry.

PR-F1（`evidence_taxonomy.py`）は namespace（"history_theme" / "goriyaku"）と
canonical key format (`<namespace>:<key>`) のみを定義し、実際に有効な
key一覧はF2/F3のHOLD事項として意図的に未定義のままだった。

本モジュールは、そのHOLD事項のうち history_theme v1 のみを解決する。
PR-F1のformat validator (`validate_canonical_semantic_key`) をそのまま
再利用し、format検証ロジックを重複させない。goriyaku taxonomyの値は
本PR (F2) では一切登録しない（F3のscope）。

Mother Ship FINAL v1 canonical mapping（日本語表示値 → canonical key）:
    再出発 → history_theme:restart
    静寂   → history_theme:stillness
    復興   → history_theme:restoration
    勝負   → history_theme:challenge
    縁     → history_theme:connection
    学び   → history_theme:learning
    守り   → history_theme:protection

canonical keyが機械識別子（machine identity）であり、日本語ラベルは
表示値（display value）に過ぎない。既存`Shrine.history_theme`
（日本語ラベルそのものを格納するcompatibility path）とは異なる、
Evidence Foundation側の独立した識別子体系。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from temples.domain.evidence_taxonomy import (
    TaxonomyNamespace,
    get_current_taxonomy_version,
    validate_canonical_semantic_key,
)

HISTORY_THEME_TAXONOMY_NAMESPACE: TaxonomyNamespace = "history_theme"

# PR-F1のtaxonomy version infrastructureをそのまま参照する
# （バージョン番号をここで再定義しない）。
HISTORY_THEME_TAXONOMY_VERSION = get_current_taxonomy_version(
    HISTORY_THEME_TAXONOMY_NAMESPACE
).version

# Mother Ship FINAL: canonical key（ローカル部分、namespace prefixなし）→
# 日本語表示ラベル。表示ラベルは既存`docs/product/history-theme-taxonomy.md`
# の7カテゴリそのものであり、ここで新たな日本語表現を作っていない。
HISTORY_THEME_V1_CANONICAL_KEYS: Dict[str, str] = {
    "restart": "再出発",
    "stillness": "静寂",
    "restoration": "復興",
    "challenge": "勝負",
    "connection": "縁",
    "learning": "学び",
    "protection": "守り",
}

HISTORY_THEME_V1_CANONICAL_KEY_SET = set(HISTORY_THEME_V1_CANONICAL_KEYS)


@dataclass(frozen=True)
class HistoryThemeV1KeyValidationResult:
    valid: bool
    reason: str
    canonical_key: Optional[str]
    display_label_ja: Optional[str]


def validate_history_theme_v1_canonical_key(value: Optional[str]) -> HistoryThemeV1KeyValidationResult:
    """`<namespace>:<key>`形式の入力を検証し、history_theme v1の7値の
    いずれかであることまで確認する。

    - PR-F1のformat validatorをそのまま利用（namespace/separator/非空key
      のformat検証を重複実装しない）。
    - namespaceが"history_theme"以外（例: "goriyaku:love"）の場合は
      reject。
    - keyがv1の7値に含まれない場合はreject（fuzzy normalization、
      日本語ラベルからの自動推定は行わない）。
    """
    format_result = validate_canonical_semantic_key(value)

    if not format_result.valid:
        return HistoryThemeV1KeyValidationResult(
            valid=False,
            reason=format_result.reason,
            canonical_key=None,
            display_label_ja=None,
        )

    if format_result.namespace != HISTORY_THEME_TAXONOMY_NAMESPACE:
        return HistoryThemeV1KeyValidationResult(
            valid=False,
            reason="wrong_namespace",
            canonical_key=None,
            display_label_ja=None,
        )

    key = format_result.key
    if key not in HISTORY_THEME_V1_CANONICAL_KEY_SET:
        return HistoryThemeV1KeyValidationResult(
            valid=False,
            reason="unknown_history_theme_key",
            canonical_key=None,
            display_label_ja=None,
        )

    return HistoryThemeV1KeyValidationResult(
        valid=True,
        reason="valid",
        canonical_key=f"{HISTORY_THEME_TAXONOMY_NAMESPACE}:{key}",
        display_label_ja=HISTORY_THEME_V1_CANONICAL_KEYS[key],
    )


__all__ = [
    "HISTORY_THEME_TAXONOMY_NAMESPACE",
    "HISTORY_THEME_TAXONOMY_VERSION",
    "HISTORY_THEME_V1_CANONICAL_KEYS",
    "HISTORY_THEME_V1_CANONICAL_KEY_SET",
    "HistoryThemeV1KeyValidationResult",
    "validate_history_theme_v1_canonical_key",
]
