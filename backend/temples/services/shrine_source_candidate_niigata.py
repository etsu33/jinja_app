"""新潟県 Batch 001 の凍結 Source snapshot adapter。

外部で取得・凍結した snapshot（JSON）を共通の raw candidate へ変換する。
値は変換・補完しない（都道府県の前置、旧字体変換、語尾除去などはしない）。
schema が想定と違えば STOP_SOURCE_DRIFT / STOP_INPUT で止める。

snapshot の形:

    {
      "snapshot": {
        "prefecture": "新潟県",
        "batch_id": "NIIGATA-001",
        "source_type": "prefectural_jinjacho_official",
        "source_url": "...",
        "source_verified_at": "...",
        "captured_at": "...",
        "selection_rule": "..."
      },
      "candidates": [
        {"source_position": "...", "raw_name": "...", "raw_address": "...",
         "kana": null, "phone": null, "source_id": null, "detail_url": null}
      ]
    }

candidate の optional key（kana / phone / source_id / detail_url）は省略してよい。
省略と null はどちらも「Source に無い」として None のまま保持する。
"""

from __future__ import annotations

from typing import Any

from temples.services.shrine_source_candidate_extraction import (
    SOURCE_TYPE_PREFECTURAL_JINJACHO_OFFICIAL,
    STOP_INPUT,
    STOP_SOURCE_DRIFT,
    BatchContract,
    CandidateExtractionStop,
    RawCandidate,
    SnapshotMetadata,
)

NIIGATA_BATCH_001 = BatchContract(
    prefecture="新潟県",
    batch_id="NIIGATA-001",
    # M1 = 最大100。新潟県の Source は100件を超えるため Batch 001 は部分 Batch にならない。
    required_raw_count=100,
    source_type=SOURCE_TYPE_PREFECTURAL_JINJACHO_OFFICIAL,
)

_TOP_LEVEL_KEYS = frozenset({"snapshot", "candidates"})
_SNAPSHOT_KEYS = frozenset(
    {
        "prefecture",
        "batch_id",
        "source_type",
        "source_url",
        "source_verified_at",
        "captured_at",
        "selection_rule",
    }
)
_CANDIDATE_REQUIRED_KEYS = frozenset({"source_position", "raw_name", "raw_address"})
_CANDIDATE_OPTIONAL_KEYS = frozenset({"kana", "phone", "source_id", "detail_url"})


def _require_keys(obj: Any, *, where: str, required: frozenset, optional: frozenset) -> dict:
    if not isinstance(obj, dict):
        raise CandidateExtractionStop(STOP_SOURCE_DRIFT, f"{where} must be an object")
    keys = set(obj)
    unknown = sorted(keys - required - optional)
    if unknown:
        raise CandidateExtractionStop(STOP_SOURCE_DRIFT, f"{where} has unknown keys {unknown}")
    absent = sorted(required - keys)
    if absent:
        raise CandidateExtractionStop(STOP_SOURCE_DRIFT, f"{where} is missing keys {absent}")
    return obj


def _optional_str(value: Any, *, where: str) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise CandidateExtractionStop(STOP_SOURCE_DRIFT, f"{where} must be a string or null")


def parse_niigata_batch_001_snapshot(
    data: Any,
) -> tuple[BatchContract, SnapshotMetadata, list[RawCandidate]]:
    """凍結 snapshot を検証して共通の raw candidate に変換する（値は書き換えない）。"""
    _require_keys(data, where="snapshot file", required=_TOP_LEVEL_KEYS, optional=frozenset())
    meta_raw = _require_keys(
        data["snapshot"], where="snapshot", required=_SNAPSHOT_KEYS, optional=frozenset()
    )
    for key in sorted(_SNAPSHOT_KEYS):
        value = meta_raw[key]
        if not isinstance(value, str) or not value.strip():
            # Source registry の entry gate（§3.1）: 欠けた snapshot は Extraction を始めない。
            raise CandidateExtractionStop(STOP_INPUT, f"snapshot.{key} must be a non-empty string")
    meta = SnapshotMetadata(**{key: meta_raw[key] for key in _SNAPSHOT_KEYS})

    candidates_raw = data["candidates"]
    if not isinstance(candidates_raw, list):
        raise CandidateExtractionStop(STOP_SOURCE_DRIFT, "candidates must be a list")

    raws: list[RawCandidate] = []
    for index, item in enumerate(candidates_raw):
        where = f"candidates[{index}]"
        _require_keys(
            item, where=where, required=_CANDIDATE_REQUIRED_KEYS, optional=_CANDIDATE_OPTIONAL_KEYS
        )
        position = item["source_position"]
        if not isinstance(position, str):
            raise CandidateExtractionStop(
                STOP_SOURCE_DRIFT, f"{where}.source_position must be a string"
            )
        raws.append(
            RawCandidate(
                source_position=position,
                raw_name=_optional_str(item["raw_name"], where=f"{where}.raw_name"),
                raw_address=_optional_str(item["raw_address"], where=f"{where}.raw_address"),
                kana=_optional_str(item.get("kana"), where=f"{where}.kana"),
                phone=_optional_str(item.get("phone"), where=f"{where}.phone"),
                source_id=_optional_str(item.get("source_id"), where=f"{where}.source_id"),
                detail_url=_optional_str(item.get("detail_url"), where=f"{where}.detail_url"),
            )
        )
    return NIIGATA_BATCH_001, meta, raws
