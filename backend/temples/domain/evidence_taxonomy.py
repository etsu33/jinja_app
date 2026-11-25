# backend/temples/domain/evidence_taxonomy.py
"""Evidence Foundation PR-F1: Taxonomy Registry Infrastructure.

taxonomyをDB正本ではなく code-level versioned registry として扱うための
基盤のみを提供する。

重要（PR-F1のscope境界）:
    - history_theme / goriyaku の実際のcanonical key一覧（例:
      "history_theme:再出発" が有効かどうか）は、ここでは一切定義しない。
      既存canonical値は docs/product/history-theme-taxonomy.md
      （7カテゴリ: 守り/静寂/再出発/復興/勝負/学び/縁、日本語ラベルそのもの
      がstorage値）にあり、それをcanonical keyへどう対応させるかは
      Mother Ship HOLD（F2で決定）。
    - namespace（"history_theme" / "goriyaku"）2つは、Mother Ship指定の
      canonical key format例 (`history_theme:<key>` / `goriyaku:<key>`)
      からそのまま採用したものであり、本モジュールが独自に考案した名称
      ではない。
    - 既存taxonomy（Shrine.history_theme, GoriyakuTag.name等）のrename /
      merge / deleteはここでは一切行わない。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

TaxonomyNamespace = str

# Mother Ship指定のcanonical key format
# (`history_theme:<key>` / `goriyaku:<key>`) にある2つのnamespaceを、
# そのまま登録する。第3のnamespaceを推測で追加してはいない。
EVIDENCE_TAXONOMY_NAMESPACES: List[TaxonomyNamespace] = [
    "history_theme",
    "goriyaku",
]

EVIDENCE_TAXONOMY_NAMESPACE_SET = set(EVIDENCE_TAXONOMY_NAMESPACES)


@dataclass(frozen=True)
class TaxonomyVersion:
    """あるnamespaceのtaxonomyが、どのversionで意味づけされたかを追跡する
    ための最小contract。

    versionはMother Ship FINAL contractに従い文字列（例: "v1"）。将来の
    normalized Evidence transport（PR-F5）のtaxonomyVersionも文字列であり、
    Foundation全体で単一の表現（文字列）のみを正とする。整数表現との
    変換ヘルパーは意図的に用意しない。
    """

    namespace: TaxonomyNamespace
    version: str


# 両namespaceとも、PR-F1時点ではまだ実際のcanonical key一覧を持たない
# （F2/F3で決定）。そのため両方ともbaseline版として"v1"から開始する。
# これは「既存taxonomy内容を再設計した」という意味ではなく、versioning
# infrastructureそのものの初期値。
_CURRENT_TAXONOMY_VERSION_BY_NAMESPACE: Dict[TaxonomyNamespace, str] = {
    "history_theme": "v1",
    "goriyaku": "v1",
}


def is_registered_taxonomy_namespace(namespace: str) -> bool:
    return namespace in EVIDENCE_TAXONOMY_NAMESPACE_SET


def get_current_taxonomy_version(namespace: str) -> TaxonomyVersion:
    """登録済みnamespaceの現行versionを返す。未登録namespaceには
    ValueErrorを送出する -- 未知のnamespaceに対して黙って既定値を返す
    ことはしない（taxonomy versionの取り違えは、Consultation Relevance
    Contractの前提を壊すため、fail-fastとする）。"""
    if not is_registered_taxonomy_namespace(namespace):
        raise ValueError(
            f"unregistered_taxonomy_namespace: {namespace!r} is not one of "
            f"{sorted(EVIDENCE_TAXONOMY_NAMESPACE_SET)}"
        )
    return TaxonomyVersion(
        namespace=namespace,
        version=_CURRENT_TAXONOMY_VERSION_BY_NAMESPACE[namespace],
    )


_KEY_SEPARATOR = ":"


@dataclass(frozen=True)
class CanonicalKeyValidationResult:
    valid: bool
    reason: str
    namespace: Optional[TaxonomyNamespace]
    key: Optional[str]


# F1-5: canonical semantic key format ("<namespace>:<key>") のvalidator。
#
# scope境界（意図的、Fail Safe記録）:
#   key part（":"より後ろ）の文字種ルールは、既存taxonomy実態
#   （Shrine.history_theme: 日本語ラベルそのもの＝再出発/静寂/復興/勝負/
#   縁/学び/守り。GoriyakuTag.name: 日本語、一部「・」区切りの複合語＝
#   例えば「厄除け・方除け」）を確認した上で、[a-z0-9_-]+のようなASCII
#   限定regexへ固定しないことを明示的に選んだ。実際のcanonical key文字列
#   （日本語を含めるか、ローマ字化するか等）はF2/F3でMother Shipが確定する
#   HOLD事項であり、本validatorはformat（namespace + separator + 非空key）
#   のみを検証し、key内部の文字種は制限しない。
def validate_canonical_semantic_key(value: Optional[str]) -> CanonicalKeyValidationResult:
    raw = value if isinstance(value, str) else ""
    raw = raw.strip()

    if not raw:
        return CanonicalKeyValidationResult(valid=False, reason="empty_key", namespace=None, key=None)

    parts = raw.split(_KEY_SEPARATOR)

    if len(parts) < 2:
        return CanonicalKeyValidationResult(valid=False, reason="malformed_key", namespace=None, key=None)

    if len(parts) > 2:
        # 複数区切り文字（例: "history_theme:a:b"）はformatが一意に定まら
        # ないため malformed として reject する。key内部の文字種そのものを
        # 制限する話とは別（":"はformat上のseparatorとして予約されている）。
        return CanonicalKeyValidationResult(valid=False, reason="malformed_key", namespace=None, key=None)

    namespace, key = parts[0].strip(), parts[1].strip()

    if not namespace:
        return CanonicalKeyValidationResult(valid=False, reason="missing_namespace", namespace=None, key=None)

    if not is_registered_taxonomy_namespace(namespace):
        return CanonicalKeyValidationResult(
            valid=False, reason="unknown_namespace", namespace=namespace, key=None
        )

    if not key:
        return CanonicalKeyValidationResult(valid=False, reason="empty_key", namespace=namespace, key=None)

    return CanonicalKeyValidationResult(valid=True, reason="valid", namespace=namespace, key=key)


__all__ = [
    "EVIDENCE_TAXONOMY_NAMESPACES",
    "EVIDENCE_TAXONOMY_NAMESPACE_SET",
    "TaxonomyVersion",
    "is_registered_taxonomy_namespace",
    "get_current_taxonomy_version",
    "CanonicalKeyValidationResult",
    "validate_canonical_semantic_key",
]
