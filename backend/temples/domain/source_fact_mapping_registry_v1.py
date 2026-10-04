# backend/temples/domain/source_fact_mapping_registry_v1.py
"""Policy C / Channel B: S3a versioned code registry（ShrineSourceFact → canonical concept）。

docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md §12.9.8 / §12.12.8 /
§12.15.H〜J の実装（PR-B）。

    ShrineSourceFact.stable_key  →  既存の canonical GoriyakuTag.name

registry は repository が正本である（MAPPING_CANONICAL_AUTHORITY = REPOSITORY）。
runtime から変更する経路（create / update / delete / admin / API / 環境変数 / DB）は持たない。
変更は repository の code change と review だけで行う。

1件の record が持つのは3つだけ:
    source_fact_key        ShrineSourceFact.stable_key（DB の PK・shrine 名・wording は使わない）
    canonical_concept_name 既存の GoriyakuTag.name（DB の id は持たない）
    mapping_classification EXACT | SAFE_NORMALIZATION（review の分類。lookup 時の文字列正規化ではない）

否定の mapping は持たない（NEGATIVE_MAPPING_STORAGE = ABSENCE_SUFFICIENT）。
record が無い stable_key は lookup で None（NO_SIGNAL）であり、エラーではない。

検証は2段に分ける:
    静的検証  registry の形（version / 型 / 空白 / 重複 / 分類）。DB を使わない
    DB 整合   stable_key → ShrineSourceFact がちょうど1件、concept name → GoriyakuTag が
              ちょうど1件（exact name。alias / fuzzy / 正規化はしない）
不正な正の record は fail-closed（黙って捨てない・直さない）。

本 module は Recommendation から読まれない（Need mapping / TypedNeedMatch / scoring は PR-C 以降）。
W0-DB04 の実 mapping は PR-E が追加する。本 foundation の registry は空である。
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional

# registry 全体で1つの version。DB の状態や時刻からは導かない。
REGISTRY_VERSION = "source_fact_mapping_registry_v1"

MAPPING_CLASSIFICATION_EXACT = "EXACT"
MAPPING_CLASSIFICATION_SAFE_NORMALIZATION = "SAFE_NORMALIZATION"
ALLOWED_MAPPING_CLASSIFICATIONS = frozenset(
    {MAPPING_CLASSIFICATION_EXACT, MAPPING_CLASSIFICATION_SAFE_NORMALIZATION}
)
# frozen crosswalk の分類のうち、正の record にしてはならないもの（明示的に拒否する）。
REJECTED_MAPPING_CLASSIFICATIONS = frozenset({"AMBIGUOUS", "NO_CANONICAL_TAG"})


@dataclass(frozen=True)
class SourceFactMappingRecord:
    """承認済みの正の mapping 1件（immutable）。"""

    source_fact_key: str
    canonical_concept_name: str
    mapping_classification: str


SOURCE_FACT_MAPPING_RECORD_FIELDS = tuple(f.name for f in fields(SourceFactMappingRecord))

# 正本の record 列。tuple で持ち、dict にする前に重複を検出する（後の値で黙って上書きしない）。
# PR-B foundation では空。W0-DB04 の実 mapping は Mother Ship の承認後に PR-E が追加する。
SOURCE_FACT_MAPPING_RECORDS: tuple[SourceFactMappingRecord, ...] = ()


class SourceFactMappingRegistryError(ValueError):
    """registry が不正（静的検証または DB 整合）。fail-closed のため例外にする。"""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def _check_text(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: required, must be a non-blank string, got {value!r}")
    elif value != value.strip():
        errors.append(f"{label}: must not have leading/trailing whitespace, got {value!r}")


def validate_registry_static(
    records: Iterable[Any] = SOURCE_FACT_MAPPING_RECORDS,
    version: Any = REGISTRY_VERSION,
) -> tuple[str, ...]:
    """registry の形だけを検証する（DB を使わない）。エラーの tuple を返す（空なら合格）。

    同じ入力に対して常に同じ順序の同じ結果を返す。
    """
    errors: list[str] = []
    _check_text(version, "registry_version", errors)

    seen_keys: dict[str, int] = {}
    for i, record in enumerate(records):
        prefix = f"records[{i}]"
        if not isinstance(record, SourceFactMappingRecord):
            errors.append(
                f"{prefix}: must be a SourceFactMappingRecord, got {type(record).__name__}"
            )
            continue
        _check_text(record.source_fact_key, f"{prefix}.source_fact_key", errors)
        # concept は canonical name（文字列）で参照する。DB の id（int）は受け付けない。
        _check_text(record.canonical_concept_name, f"{prefix}.canonical_concept_name", errors)

        classification = record.mapping_classification
        if classification in REJECTED_MAPPING_CLASSIFICATIONS:
            errors.append(
                f"{prefix}.mapping_classification: {classification!r} must not be a positive "
                "mapping (absence is the negative mapping)"
            )
        elif classification not in ALLOWED_MAPPING_CLASSIFICATIONS:
            errors.append(f"{prefix}.mapping_classification: invalid value {classification!r}")

        key = record.source_fact_key
        if isinstance(key, str) and key.strip():
            if key in seen_keys:
                errors.append(
                    f"{prefix}.source_fact_key: duplicate {key!r} "
                    f"(first at records[{seen_keys[key]}])"
                )
            else:
                seen_keys[key] = i
    return tuple(errors)


def validate_registry_db_consistency(
    records: Iterable[SourceFactMappingRecord] = SOURCE_FACT_MAPPING_RECORDS,
) -> tuple[str, ...]:
    """registry と DB の整合を検証する（読むだけ。何も作らない）。

    - source_fact_key → ShrineSourceFact.stable_key がちょうど1件
    - canonical_concept_name → GoriyakuTag.name がちょうど1件（exact name）

    canonical 39 の正本は既存の GoriyakuTag master（exact39 bootstrap contract で固定）であり、
    ここに2つ目の name 一覧は作らない。静的検証に通らない record は対象外として先に報告する。
    """
    from temples.models import GoriyakuTag, ShrineSourceFact

    records = tuple(records)
    static_errors = validate_registry_static(records)
    if static_errors:
        return static_errors

    keys = [r.source_fact_key for r in records]
    names = [r.canonical_concept_name for r in records]
    fact_counts: dict[str, int] = {}
    for key in ShrineSourceFact.objects.filter(stable_key__in=keys).values_list(
        "stable_key", flat=True
    ):
        fact_counts[key] = fact_counts.get(key, 0) + 1
    tag_counts: dict[str, int] = {}
    for name in GoriyakuTag.objects.filter(name__in=names).values_list("name", flat=True):
        tag_counts[name] = tag_counts.get(name, 0) + 1

    errors: list[str] = []
    for i, record in enumerate(records):
        prefix = f"records[{i}]"
        n_facts = fact_counts.get(record.source_fact_key, 0)
        if n_facts != 1:
            errors.append(
                f"{prefix}.source_fact_key: {record.source_fact_key!r} resolves to "
                f"{n_facts} ShrineSourceFact rows (expected exactly 1)"
            )
        n_tags = tag_counts.get(record.canonical_concept_name, 0)
        if n_tags != 1:
            errors.append(
                f"{prefix}.canonical_concept_name: {record.canonical_concept_name!r} resolves to "
                f"{n_tags} GoriyakuTag rows by exact name (expected exactly 1)"
            )
    return tuple(errors)


@dataclass(frozen=True)
class SourceFactMappingRegistry:
    """静的検証を通った registry（immutable）。lookup だけを提供する。"""

    version: str
    records: tuple[SourceFactMappingRecord, ...]
    _by_key: Mapping[str, SourceFactMappingRecord]

    def lookup(self, source_fact_key: Any) -> Optional[SourceFactMappingRecord]:
        """stable_key の承認済み mapping を返す。無ければ None（NO_SIGNAL。エラーではない）。

        exact string equality だけで引く。PK（int）・正規化・alias は使わない。
        """
        if not isinstance(source_fact_key, str):
            return None
        return self._by_key.get(source_fact_key)


def build_registry(
    records: Iterable[Any] = SOURCE_FACT_MAPPING_RECORDS,
    version: Any = REGISTRY_VERSION,
) -> SourceFactMappingRegistry:
    """静的検証に通った場合だけ registry を作る。不正なら SourceFactMappingRegistryError。"""
    records = tuple(records)
    errors = validate_registry_static(records, version)
    if errors:
        raise SourceFactMappingRegistryError(errors)
    by_key = MappingProxyType({r.source_fact_key: r for r in records})
    return SourceFactMappingRegistry(version=version, records=records, _by_key=by_key)


_default_registry: Optional[SourceFactMappingRegistry] = None


def get_registry() -> SourceFactMappingRegistry:
    """repository の registry（SOURCE_FACT_MAPPING_RECORDS / REGISTRY_VERSION）。

    不正な registry は例外になる（不正な record を黙って飛ばして lookup を続けない）。
    """
    global _default_registry
    if _default_registry is None:
        # module の正本を呼び出し時点で読む（引数の既定値に固定しない）。
        _default_registry = build_registry(SOURCE_FACT_MAPPING_RECORDS, REGISTRY_VERSION)
    return _default_registry


def lookup_source_fact_mapping(source_fact_key: Any) -> Optional[SourceFactMappingRecord]:
    """repository の registry で stable_key を引く。無ければ None。"""
    return get_registry().lookup(source_fact_key)


__all__ = [
    "REGISTRY_VERSION",
    "MAPPING_CLASSIFICATION_EXACT",
    "MAPPING_CLASSIFICATION_SAFE_NORMALIZATION",
    "ALLOWED_MAPPING_CLASSIFICATIONS",
    "REJECTED_MAPPING_CLASSIFICATIONS",
    "SourceFactMappingRecord",
    "SOURCE_FACT_MAPPING_RECORD_FIELDS",
    "SOURCE_FACT_MAPPING_RECORDS",
    "SourceFactMappingRegistryError",
    "validate_registry_static",
    "validate_registry_db_consistency",
    "SourceFactMappingRegistry",
    "build_registry",
    "get_registry",
    "lookup_source_fact_mapping",
]
