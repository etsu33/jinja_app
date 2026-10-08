"""Shrine Source Candidate Extraction Runner（read-only）。

正本: docs/audit/shrine-source-candidate-extraction-contract.md（M1〜M5 決定済み）。

外部で取得・凍結した Source snapshot（raw candidate の列）を受け取り、
既存の duplicate 正規化と collision lookup だけを使って
READY_CANDIDATE / REVIEW_REQUIRED / INVALID に分類し、決定的な監査 artifact を作る。

- Source の取得（scraping / fetch）は行わない。
- Shrine / Candidate Master / Knowledge / 座標 / goriyaku へは書き込まない。
  実行中に SELECT 以外の SQL が出たら FAIL として止める（`read_only_guard`）。
- `find_duplicate_candidates()` は COLLISION_SIGNAL_ONLY。候補が1件でも
  同一神社とは判定せず、DUPLICATE という分類は作らない。
- raw 値は受け取ったまま保持し、比較用の値は別 field に作る。
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from django.db import connection
from temples.forms import PREF_CHOICES
from temples.services.shrine_duplicate_normalize import (
    normalize_shrine_address_for_duplicate,
    normalize_shrine_name_for_duplicate,
)
from temples.services.shrine_submission import find_duplicate_candidates

RUNNER_VERSION = "shrine-source-candidate-runner/1"
CONTRACT_PATH = "docs/audit/shrine-source-candidate-extraction-contract.md"

SOURCE_TYPE_PREFECTURAL_JINJACHO_OFFICIAL = "prefectural_jinjacho_official"
# §9。M1 の BATCH_SIZE = 100 とは独立した値。
DUPLICATE_LOOKUP_LIMIT = 100
# M4。
READY_HANDOFF_MAX = 5

READY_CANDIDATE = "READY_CANDIDATE"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
INVALID = "INVALID"
CANONICAL_CLASSIFICATIONS = frozenset({READY_CANDIDATE, REVIEW_REQUIRED, INVALID})

PLANNED_ACTION_HANDOFF = "HANDOFF_NEXT_GATE"
PLANNED_ACTION_STOP_SOURCE_REVIEW = "STOP_SOURCE_REVIEW"
PLANNED_ACTION_STOP_PREFECTURE_REVIEW = "STOP_PREFECTURE_REVIEW"
# collision 候補あり / truncation の可能性。M5 により Mother Ship が判断する。
PLANNED_ACTION_STOP_MOTHER_SHIP_REVIEW = "STOP_MOTHER_SHIP_REVIEW"

REVIEW_REASON_MISSING_RAW_NAME = "MISSING_RAW_NAME"
REVIEW_REASON_MISSING_RAW_ADDRESS = "MISSING_RAW_ADDRESS"
REVIEW_REASON_PREFECTURE_MISMATCH = "PREFECTURE_MISMATCH"
REVIEW_REASON_COLLISION_CANDIDATES = "COLLISION_CANDIDATES_RETURNED"
REVIEW_REASON_POSSIBLY_TRUNCATED = "COLLISION_LOOKUP_POSSIBLY_TRUNCATED"

SCHEMA_PASS = "PASS"
SCHEMA_FAIL = "FAIL"
SCHEMA_NOT_EVALUATED = "NOT_EVALUATED"

# fail closed の停止コード（§20 / 実装 contract）。
STOP_INPUT = "STOP_INPUT"
STOP_BATCH_CONTRACT = "STOP_BATCH_CONTRACT"
STOP_PREFECTURE = "STOP_PREFECTURE"
STOP_SOURCE_DRIFT = "STOP_SOURCE_DRIFT"
STOP_CONTRACT = "STOP_CONTRACT"
STOP_REPRODUCIBILITY = "STOP_REPRODUCIBILITY"
FAIL_DB_MUTATION = "FAIL"

JAPANESE_PREFECTURES: tuple[str, ...] = tuple(value for value, _ in PREF_CHOICES if value)


class CandidateExtractionStop(Exception):
    """Batch 全体を止める fail closed の停止。行単位の INVALID / REVIEW_REQUIRED とは別。"""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class BatchContract:
    prefecture: str
    batch_id: str
    required_raw_count: int
    source_type: str


@dataclass(frozen=True)
class SnapshotMetadata:
    prefecture: str
    batch_id: str
    source_type: str
    source_url: str
    source_verified_at: str
    captured_at: str
    selection_rule: str


@dataclass(frozen=True)
class RawCandidate:
    """Source 上の1行。値は受け取ったまま保持する（None は「Source に無い」）。"""

    source_position: str
    raw_name: str | None
    raw_address: str | None
    kana: str | None = None
    phone: str | None = None
    source_id: str | None = None
    detail_url: str | None = None


# ---------------------------------------------------------------------------
# read-only guard
# ---------------------------------------------------------------------------


@contextmanager
def read_only_guard() -> Iterator[None]:
    """実行中の SQL を SELECT だけに限る。それ以外が出たら FAIL として止める。"""
    connection.ensure_connection()

    def _guard(execute, sql, params, many, context):
        if not str(sql).lstrip().upper().startswith("SELECT"):
            raise CandidateExtractionStop(
                FAIL_DB_MUTATION, f"non-SELECT SQL during extraction: {str(sql)[:80]!r}"
            )
        return execute(sql, params, many, context)

    with connection.execute_wrapper(_guard):
        yield


# ---------------------------------------------------------------------------
# row classification
# ---------------------------------------------------------------------------


def _is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def explicit_other_prefectures(raw_address: str, expected_prefecture: str) -> list[str]:
    """address に明示された、期待と異なる都道府県名（47 都道府県の正式名だけで判定）。

    都道府県名の省略は不一致としない。address は書き換えない。
    """
    return [
        prefecture
        for prefecture in JAPANESE_PREFECTURES
        if prefecture != expected_prefecture and prefecture in raw_address
    ]


def classify_candidate(meta: SnapshotMetadata, raw: RawCandidate) -> dict[str, Any]:
    """1行を contract どおりに分類し、canonical output の row を返す。"""
    row: dict[str, Any] = {
        "prefecture": meta.prefecture,
        "batch_id": meta.batch_id,
        "source_position": raw.source_position,
        "selection_rule": meta.selection_rule,
        "captured_at": meta.captured_at,
        "raw_name": raw.raw_name,
        "raw_address": raw.raw_address,
        "kana": raw.kana,
        "phone": raw.phone,
        "source_type": meta.source_type,
        "source_url": meta.source_url,
        "detail_url": raw.detail_url,
        "source_id": raw.source_id,
        "source_verified_at": meta.source_verified_at,
        "normalized_name": None,
        "normalized_address": None,
        "identity_candidate": None,
        "duplicate_lookup_limit": DUPLICATE_LOOKUP_LIMIT,
        "duplicate_lookup_performed": False,
        "returned_candidate_count": None,
        "returned_candidate_ids": [],
        "returned_candidate_names": [],
        "returned_candidate_addresses": [],
        "possibly_truncated": None,
        "classification": None,
        "planned_action": None,
        "review_reason": [],
        "schema_name": SCHEMA_FAIL if _is_blank(raw.raw_name) else SCHEMA_PASS,
        "schema_address": SCHEMA_FAIL if _is_blank(raw.raw_address) else SCHEMA_PASS,
        # source_url / source_type / source_verified_at / prefecture は snapshot の
        # entry gate（adapter）で検証済み。ここへ来た時点で PASS。
        "schema_source_url": SCHEMA_PASS,
        "schema_prefecture": SCHEMA_PASS,
        "schema_source_type": SCHEMA_PASS,
        "schema_source_verified_at": SCHEMA_PASS,
        "schema_gate_result": None,
    }

    # Step A: 必須入力。欠損なら INVALID で止め、lookup はしない。
    missing = []
    if row["schema_name"] == SCHEMA_FAIL:
        missing.append(REVIEW_REASON_MISSING_RAW_NAME)
    if row["schema_address"] == SCHEMA_FAIL:
        missing.append(REVIEW_REASON_MISSING_RAW_ADDRESS)
    if missing:
        row.update(
            classification=INVALID,
            planned_action=PLANNED_ACTION_STOP_SOURCE_REVIEW,
            review_reason=missing,
            schema_gate_result=SCHEMA_FAIL,
        )
        return row

    assert raw.raw_name is not None and raw.raw_address is not None
    reasons: list[str] = []

    # Step B: 都道府県の整合。明示された別の都道府県だけを不一致とする。
    if explicit_other_prefectures(raw.raw_address, meta.prefecture):
        row["schema_prefecture"] = SCHEMA_FAIL
        reasons.append(REVIEW_REASON_PREFECTURE_MISMATCH)

    # Step C: 既存の正規化だけを使う。identity_candidate は監査用 key（identity ではない）。
    normalized_name = normalize_shrine_name_for_duplicate(raw.raw_name)
    normalized_address = normalize_shrine_address_for_duplicate(raw.raw_address)
    row.update(
        normalized_name=normalized_name,
        normalized_address=normalized_address,
        identity_candidate=f"{normalized_name}|{normalized_address}",
    )

    # Step D: collision lookup（COLLISION_SIGNAL_ONLY）。不一致の行も Mother Ship 用の
    # Evidence として lookup する。
    candidates = find_duplicate_candidates(
        name=raw.raw_name,
        address=raw.raw_address,
        limit=DUPLICATE_LOOKUP_LIMIT,
    )
    count = len(candidates)
    possibly_truncated = count >= DUPLICATE_LOOKUP_LIMIT
    row.update(
        duplicate_lookup_performed=True,
        returned_candidate_count=count,
        returned_candidate_ids=[c.id for c in candidates],
        returned_candidate_names=[c.name for c in candidates],
        returned_candidate_addresses=[c.address for c in candidates],
        possibly_truncated=possibly_truncated,
    )
    if count:
        reasons.append(REVIEW_REASON_COLLISION_CANDIDATES)
    if possibly_truncated:
        reasons.append(REVIEW_REASON_POSSIBLY_TRUNCATED)

    # Step E: schema gate。候補0・必須 PASS・県整合 PASS のときだけ READY。
    if not reasons:
        row.update(
            classification=READY_CANDIDATE,
            planned_action=PLANNED_ACTION_HANDOFF,
            schema_gate_result=SCHEMA_PASS,
        )
        return row

    row.update(
        classification=REVIEW_REQUIRED,
        planned_action=(
            PLANNED_ACTION_STOP_PREFECTURE_REVIEW
            if REVIEW_REASON_PREFECTURE_MISMATCH in reasons
            else PLANNED_ACTION_STOP_MOTHER_SHIP_REVIEW
        ),
        review_reason=reasons,
        schema_gate_result=SCHEMA_NOT_EVALUATED,
    )
    return row


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------


def validate_batch_shape(
    contract: BatchContract, meta: SnapshotMetadata, rows: list[RawCandidate]
) -> None:
    """Batch contract（件数・source_position・都道府県・source_type）を fail closed で確認する。"""
    if meta.prefecture != contract.prefecture:
        raise CandidateExtractionStop(
            STOP_PREFECTURE, f"prefecture={meta.prefecture!r} expected={contract.prefecture!r}"
        )
    if meta.batch_id != contract.batch_id:
        raise CandidateExtractionStop(
            STOP_BATCH_CONTRACT, f"batch_id={meta.batch_id!r} expected={contract.batch_id!r}"
        )
    if meta.source_type != contract.source_type:
        raise CandidateExtractionStop(
            STOP_INPUT, f"source_type={meta.source_type!r} expected={contract.source_type!r}"
        )
    if len(rows) != contract.required_raw_count:
        raise CandidateExtractionStop(
            STOP_BATCH_CONTRACT,
            f"{contract.batch_id} requires exactly {contract.required_raw_count} raw candidates, "
            f"got {len(rows)}",
        )
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if _is_blank(raw.source_position):
            raise CandidateExtractionStop(
                STOP_BATCH_CONTRACT, f"candidates[{index}].source_position is empty"
            )
        if raw.source_position in seen:
            raise CandidateExtractionStop(
                STOP_BATCH_CONTRACT, f"duplicate source_position {raw.source_position!r}"
            )
        seen.add(raw.source_position)


def summarize(rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total_raw": len(rows),
        "ready_count": sum(1 for r in rows if r["classification"] == READY_CANDIDATE),
        "review_required_count": sum(1 for r in rows if r["classification"] == REVIEW_REQUIRED),
        "invalid_count": sum(1 for r in rows if r["classification"] == INVALID),
        "possibly_truncated_count": sum(1 for r in rows if r["possibly_truncated"] is True),
    }
    if (
        summary["ready_count"] + summary["review_required_count"] + summary["invalid_count"]
        != summary["total_raw"]
    ):
        raise CandidateExtractionStop(STOP_CONTRACT, f"classification totals mismatch: {summary}")
    return summary


def plan_ready_handoffs(batch_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """READY_CANDIDATE だけを source traversal 順に最大5件ずつ束ねる（計画のみ。書き込みなし）。"""
    ready = [r for r in rows if r["classification"] == READY_CANDIDATE]
    handoffs = []
    for start in range(0, len(ready), READY_HANDOFF_MAX):
        members = ready[start : start + READY_HANDOFF_MAX]
        handoffs.append(
            {
                "handoff_id": f"{batch_id}-H{len(handoffs) + 1:03d}",
                "batch_id": batch_id,
                "members": [
                    {
                        "source_position": r["source_position"],
                        "raw_name": r["raw_name"],
                        "raw_address": r["raw_address"],
                    }
                    for r in members
                ],
            }
        )
    return handoffs


REVIEW_PACKET_FIELDS = (
    "raw_name",
    "raw_address",
    "prefecture",
    "source_url",
    "source_position",
    "normalized_name",
    "normalized_address",
    "returned_candidate_count",
    "returned_candidate_ids",
    "returned_candidate_names",
    "returned_candidate_addresses",
    "review_reason",
    "source_verified_at",
    "batch_id",
)


def build_review_packets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """REVIEW_REQUIRED ごとの Mother Ship 用 Evidence（M5）。Runner は判断しない。"""
    return [
        {field: row[field] for field in REVIEW_PACKET_FIELDS}
        for row in rows
        if row["classification"] == REVIEW_REQUIRED
    ]


def run_extraction(
    contract: BatchContract, meta: SnapshotMetadata, raws: list[RawCandidate]
) -> dict[str, Any]:
    """凍結 snapshot 1 Batch を read-only で分類し、canonical artifact を返す。"""
    validate_batch_shape(contract, meta, raws)
    with read_only_guard():
        rows = [classify_candidate(meta, raw) for raw in raws]

    for row in rows:
        if row["classification"] not in CANONICAL_CLASSIFICATIONS:
            raise CandidateExtractionStop(
                STOP_CONTRACT, f"unclassified row {row['source_position']!r}"
            )

    return {
        "runner_version": RUNNER_VERSION,
        "contract": CONTRACT_PATH,
        "prefecture": meta.prefecture,
        "batch_id": meta.batch_id,
        "selection_rule": meta.selection_rule,
        "captured_at": meta.captured_at,
        "source_type": meta.source_type,
        "source_url": meta.source_url,
        "source_verified_at": meta.source_verified_at,
        "duplicate_lookup_limit": DUPLICATE_LOOKUP_LIMIT,
        "ready_handoff_max": READY_HANDOFF_MAX,
        "summary": summarize(rows),
        "rows": rows,
        "ready_handoffs": plan_ready_handoffs(meta.batch_id, rows),
        "review_packets": build_review_packets(rows),
    }


# ---------------------------------------------------------------------------
# reproducibility
# ---------------------------------------------------------------------------

DETERMINISTIC_ROW_FIELDS = (
    "source_position",
    "raw_name",
    "raw_address",
    "source_id",
    "normalized_name",
    "normalized_address",
    "identity_candidate",
    "returned_candidate_count",
    "returned_candidate_ids",
    "returned_candidate_names",
    "returned_candidate_addresses",
    "possibly_truncated",
    "classification",
    "planned_action",
    "review_reason",
    "schema_gate_result",
)


def deterministic_projection(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "batch_id": artifact["batch_id"],
        "rows": [
            {field: row[field] for field in DETERMINISTIC_ROW_FIELDS} for row in artifact["rows"]
        ],
        "ready_handoffs": [
            [m["source_position"] for m in handoff["members"]]
            for handoff in artifact["ready_handoffs"]
        ],
        "summary": artifact["summary"],
    }


def diff_runs(first: dict[str, Any], second: dict[str, Any]) -> list[str]:
    """2回の実行の決定的 field の差分（空なら REPRODUCIBILITY = PASS）。差分は隠さない。"""
    a, b = deterministic_projection(first), deterministic_projection(second)
    diffs: list[str] = []
    for key in ("batch_id", "summary", "ready_handoffs"):
        if a[key] != b[key]:
            diffs.append(f"{key}: {a[key]!r} != {b[key]!r}")
    if len(a["rows"]) != len(b["rows"]):
        diffs.append(f"row count: {len(a['rows'])} != {len(b['rows'])}")
    for index, (ra, rb) in enumerate(zip(a["rows"], b["rows"], strict=False)):
        for field in DETERMINISTIC_ROW_FIELDS:
            if ra[field] != rb[field]:
                diffs.append(f"rows[{index}].{field}: {ra[field]!r} != {rb[field]!r}")
    return diffs


def run_with_reproducibility_check(
    contract: BatchContract, meta: SnapshotMetadata, raws: list[RawCandidate]
) -> tuple[dict[str, Any], list[str]]:
    """同じ snapshot / DB 状態で独立に2回実行し、決定的 field を比較する。"""
    first = run_extraction(contract, meta, raws)
    second = run_extraction(contract, meta, raws)
    diffs = diff_runs(first, second)
    if diffs:
        raise CandidateExtractionStop(
            STOP_REPRODUCIBILITY, f"{len(diffs)} deterministic diff(s): " + "; ".join(diffs[:20])
        )
    return first, diffs
