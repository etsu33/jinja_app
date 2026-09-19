#!/usr/bin/env python
"""Position Audit v2 — Shrine position ground-truth audit（read-only / deterministic）。

`docs/knowledge/shrine-position-contract.md` を authority として、
`Shrine.latitude` / `Shrine.longitude`（= Visitor / Navigation Anchor）が
machine-verifiable かどうかを triage する。

**本 script は座標補正 tool ではない。** 判定するのは
「どの Shrine が機械的に検証済みと言えるか」「どれが人間のレビューを要するか」
だけであり、座標・Seed・Candidate Master・Spreadsheet・Production を
いっさい書き換えない。

## Triage layer

Position Contract の canonical status（`PASS` / `HOLD_POSITION_REVIEW`）は
変更しない。本 script はその上に **audit status** を重ねるだけである。

```text
AUTO_PASS  必要な evidence がすべて machine-verifiable
REVIEW     evidence は存在しうるが人間の解釈が必要
HOLD       必要な evidence または identity certainty が欠けている
```

## Zero-write guarantee

* Django ORM を import しない。save/update/create/delete が存在しない。
* DB へ接続しない。Production 入力は read-only snapshot **file** のみ。
* Spreadsheet は読むだけで、書き戻し経路を持たない。
* 出力は `--output-json` / `--output-md` で指定された新規 report file のみ。

Production snapshot の取得と監査の評価は**別ステップ**である。取得は
`scripts/migration_safety/sql/shrine_position_audit_snapshot.sql` を
既存の sanctioned read-only credential bridge で実行する。

    scripts/migration_safety/readonly_query.sh \\
      ~/.config/kami-musubi/production-db.env DATABASE_URL \\
      scripts/migration_safety/sql/shrine_position_audit_snapshot.sql \\
      > /path/outside/repo/production-position-snapshot.txt

    python scripts/audit_shrine_positions_v2.py \\
      --production-snapshot /path/outside/repo/production-position-snapshot.txt \\
      --spreadsheet-snapshot /path/outside/repo/spreadsheet-snapshot.json \\
      --output-json /path/outside/repo/position-audit-v2.json \\
      --output-md   /path/outside/repo/position-audit-v2.md

監査 core は ambient credential をいっさい要求しない。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
CANDIDATE_MASTER_PATH = (
    REPO_ROOT / "backend" / "temples" / "data" / "shrine_expansion_candidate_master.json"
)
RESOLUTION_RECORD_DIR = REPO_ROOT / "docs" / "audit" / "shrine-position"

# P2-B01 で contract-significant な serialized field を **追加**した
# （`position_proof_path` / `anchor_semantics_status` / `artifact_sync_status`）。
# 既存 field の削除・改名・再解釈は行っていないため、後方互換な追加として
# minor を上げる。Repository の慣行（`shrine_expansion_candidate_master.json`
# の `schema_version` 1.1 -> 1.2 = 後方互換な追加/改名）と同じ扱いである。
#
# P2-B04 で `seed_production_identity_status` を追加した。これも
# contract-significant な serialized field の追加であり、P2-A02 §28 の
# 「silent schema drift を許さない」に従って意図的に minor を上げる。
# 既存 field の意味は変えていない（`join_status` は従来どおり）。
SCHEMA_VERSION = "position-audit-v2/1.2"

# ---------------------------------------------------------------------------
# Float Comparison Contract v1
# ---------------------------------------------------------------------------
# Seed ↔ Production の座標同値判定は、Importer と同一の契約を再利用する
# （`backend/temples/management/commands/import_shrines_seed.py` の
# `COORDINATE_ABS_TOLERANCE`）。PostgreSQL の extra_float_digits=0 による
# float8 text round-trip 差分を UPDATE / 差分として扱わないための tolerance
# であり、**実世界の空間的品質の閾値ではない**。
#
# Django に依存しないよう値をここで持ち、Importer 側と同値であることは
# scripts/tests/test_audit_shrine_positions_v2.py が source を読んで固定する。
COORDINATE_ABS_TOLERANCE = 1e-12
COORDINATE_REL_TOLERANCE = 0.0

# 地球平均半径（m）。coordinate_delta_m は **報告専用の観測値**であり、
# 「N m 以内なら PASS」という判定には絶対に使わない。Position Contract は
# そのような固定閾値を定義していない。
EARTH_MEAN_RADIUS_M = 6371008.8

# ---------------------------------------------------------------------------
# Audit statuses（Position Contract の PASS / HOLD_POSITION_REVIEW とは別レイヤ）
# ---------------------------------------------------------------------------
AUTO_PASS = "AUTO_PASS"
REVIEW = "REVIEW"
HOLD = "HOLD"

# ---------------------------------------------------------------------------
# Anchor Semantics（P2-A02 §6 / §7）
# ---------------------------------------------------------------------------
# 「その座標が Visitor / Navigation Anchor として妥当か」という**意味的**判断。
# 座標が追跡可能であることとは別の責務であり、**明示的な入力としてのみ**受け取る。
# entry_status / multi_site_status / anchor_complexity / poi_candidate_count /
# provider / 座標距離 / 名称類似度 / source authority / visitor_flow_note /
# navigation_risk_note からは導出しない（P2-A02 §6）。
ANCHOR_SEMANTICS_CONFIRMED = "CONFIRMED"
ANCHOR_SEMANTICS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
ANCHOR_SEMANTICS_NOT_EVALUATED = "NOT_EVALUATED"
ANCHOR_SEMANTICS_NOT_APPLICABLE = "NOT_APPLICABLE"
# 入力が上記4値のいずれでもなかったことを表す **出力専用** の正規化値。
# 未知の文字列をそのまま serialize すると field が閉じた enum でなくなるため、
# 「未知だった」という事実だけを明示する（値を発明しない / P2-A02 §29）。
ANCHOR_SEMANTICS_UNKNOWN = "UNKNOWN"

ANCHOR_SEMANTICS_INPUT_VALUES = frozenset(
    {
        ANCHOR_SEMANTICS_CONFIRMED,
        ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        ANCHOR_SEMANTICS_NOT_EVALUATED,
        ANCHOR_SEMANTICS_NOT_APPLICABLE,
    }
)
# AUTO_PASS 資格を保持できるのはこの2値だけ（P2-A02 §7）。
ANCHOR_SEMANTICS_AUTO_PASS_ELIGIBLE = frozenset(
    {ANCHOR_SEMANTICS_CONFIRMED, ANCHOR_SEMANTICS_NOT_APPLICABLE}
)

# ---------------------------------------------------------------------------
# Position proof path（P2-A02 §8）
# ---------------------------------------------------------------------------
# 現在の Position を **どの経路で機械的に証明したか**。排他的に1つだけ選ぶ。
# 優先順位は PRIMARY_EVIDENCE > RESOLUTION_FALLBACK > NONE。
PROOF_PRIMARY_EVIDENCE = "PRIMARY_EVIDENCE"
PROOF_RESOLUTION_FALLBACK = "RESOLUTION_FALLBACK"
PROOF_NONE = "NONE"

# ---------------------------------------------------------------------------
# Artifact Synchronization（P2-A02 §20）
# ---------------------------------------------------------------------------
# repository が管理する current-state artifact が adopted Position と揃って
# いるか。Position の正しさとは **独立** の軸であり、audit_status を左右しない。
ARTIFACT_SYNCED = "SYNCED"
ARTIFACT_DRIFT = "DRIFT"
ARTIFACT_UNKNOWN = "UNKNOWN"

# Seed ↔ Production join
JOIN_MATCH_EXACT = "MATCH_EXACT"
JOIN_MISSING_SEED = "MISSING_SEED"
JOIN_MISSING_PRODUCTION = "MISSING_PRODUCTION"
JOIN_DUPLICATE_MATCH = "DUPLICATE_MATCH"
JOIN_IDENTITY_REVIEW_REQUIRED = "IDENTITY_REVIEW_REQUIRED"
# Production snapshot 自体が無い場合。MATCH_EXACT を騙らせない。
JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE = "PRODUCTION_SNAPSHOT_UNAVAILABLE"

# ---------------------------------------------------------------------------
# Seed ↔ Production identity 軸（P2-B04）
# ---------------------------------------------------------------------------
# `seed_production_join_status` とは **別の軸**である。join status を
# 上書きしない。`JOIN_MATCH_EXACT` の意味は従来どおり
#
#     raw exact (name_jp, address) で Production 行がちょうど1件
#
# だけであり、normalization / fuzzy / alias / B03 evidence のいずれも
# `JOIN_MATCH_EXACT` を生まない。
#
# exact identity と認められるのは `IDENTITY_EXACT` だけである。
# B03 の `SAME_SUPPORTED` は強い支持 evidence だが exact identity ではない。
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

# Production ↔ Spreadsheet join
SHEET_JOIN_EXACT = "JOIN_EXACT"
SHEET_JOIN_CORROBORATED = "JOIN_CORROBORATED"
SHEET_JOIN_REVIEW_CANDIDATE = "JOIN_REVIEW_CANDIDATE"
SHEET_JOIN_NONE = "JOIN_NONE"

# ---------------------------------------------------------------------------
# Reason codes（stable。値を変えると下流のレポート比較が壊れる）
# ---------------------------------------------------------------------------
# --- AUTO_PASS の根拠 ---
RC_SEED_PRODUCTION_EXACT = "SEED_PRODUCTION_EXACT"
RC_PRIMARY_SOURCE_VERIFIED = "PRIMARY_SOURCE_VERIFIED"
RC_RESOLUTION_RECORD_REUSED = "RESOLUTION_RECORD_REUSED"

# --- HOLD ---
RC_MISSING_SEED = "MISSING_SEED"
RC_MISSING_PRODUCTION = "MISSING_PRODUCTION"
RC_DUPLICATE_PRODUCTION_IDENTITY = "DUPLICATE_PRODUCTION_IDENTITY"
RC_IDENTITY_NOT_EXACT = "IDENTITY_NOT_EXACT"
RC_PRODUCTION_SNAPSHOT_UNAVAILABLE = "PRODUCTION_SNAPSHOT_UNAVAILABLE"
RC_PRIMARY_SOURCE_MISSING = "PRIMARY_SOURCE_MISSING"
RC_PRIMARY_SOURCE_WRONG_ENTITY = "PRIMARY_SOURCE_WRONG_ENTITY"
RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY = "PRIMARY_SOURCE_NON_SHRINE_ENTITY"
RC_PRIMARY_COORDINATE_UNTRACEABLE = "PRIMARY_COORDINATE_UNTRACEABLE"
RC_AMBIGUOUS_SAME_NAME_SHRINE = "AMBIGUOUS_SAME_NAME_SHRINE"
RC_IDENTITY_EVIDENCE_MISSING = "IDENTITY_EVIDENCE_MISSING"
RC_POSITION_CONTRACT_HOLD_RECORD = "POSITION_CONTRACT_HOLD_RECORD"

# --- REVIEW ---
RC_PRIMARY_COORDINATE_DIFFERS = "PRIMARY_COORDINATE_DIFFERS"
RC_SOURCE_PARSE_FAILED = "SOURCE_PARSE_FAILED"
RC_SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
RC_PRIMARY_EVIDENCE_NOT_RETRIEVED = "PRIMARY_EVIDENCE_NOT_RETRIEVED"
RC_ADDRESS_CONFLICT_UNEXPLAINED = "ADDRESS_CONFLICT_UNEXPLAINED"
RC_CORROBORATION_CONFLICT = "CORROBORATION_CONFLICT"
RC_MULTIPLE_POI_CANDIDATES = "MULTIPLE_POI_CANDIDATES"
RC_PRIMARY_ENTITY_AMBIGUOUS = "PRIMARY_ENTITY_AMBIGUOUS"
RC_SPREADSHEET_ROW_MISSING = "SPREADSHEET_ROW_MISSING"
RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE = "SPREADSHEET_SNAPSHOT_UNAVAILABLE"
RC_SPREADSHEET_IDENTITY_REVIEW = "SPREADSHEET_IDENTITY_REVIEW"
RC_IDENTITY_NORMALIZATION_REQUIRED = "IDENTITY_NORMALIZATION_REQUIRED"
RC_POSITION_SOURCE_REDIRECTED = "POSITION_SOURCE_REDIRECTED"
RC_SEED_PRODUCTION_COORDINATE_DIFFERS = "SEED_PRODUCTION_COORDINATE_DIFFERS"
RC_PRIMARY_SOURCE_TYPE_MISSING = "PRIMARY_SOURCE_TYPE_MISSING"
RC_PRIMARY_SOURCE_VERIFIED_AT_MISSING = "PRIMARY_SOURCE_VERIFIED_AT_MISSING"
RC_RESOLUTION_SOURCE_URL_MISSING = "RESOLUTION_SOURCE_URL_MISSING"
RC_RESOLUTION_SOURCE_TYPE_MISSING = "RESOLUTION_SOURCE_TYPE_MISSING"
RC_RESOLUTION_VERIFIED_AT_MISSING = "RESOLUTION_VERIFIED_AT_MISSING"
RC_RESOLUTION_RECORD_COORDINATE_MISMATCH = "RESOLUTION_RECORD_COORDINATE_MISMATCH"

# --- Anchor Semantics（P2-A02 §19。いずれも REVIEW へ写像する）---
RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED = "ANCHOR_SEMANTICS_REVIEW_REQUIRED"
RC_ANCHOR_SEMANTICS_NOT_EVALUATED = "ANCHOR_SEMANTICS_NOT_EVALUATED"
RC_ANCHOR_SEMANTICS_UNKNOWN = "ANCHOR_SEMANTICS_UNKNOWN"
# `CONFIRMED` に対応する positive code は定義しない。構造化 field
# `anchor_semantics_status` 自身がその状態を表現する（P2-A02 §19）。

# --- proof path 不在（P2-A02 §12）---
RC_POSITION_PROOF_UNAVAILABLE = "POSITION_PROOF_UNAVAILABLE"

# --- Spreadsheet provenance（P2-A02 §16。observation）---
RC_SPREADSHEET_POSITION_SOURCE_MISMATCH = "SPREADSHEET_POSITION_SOURCE_MISMATCH"

# --- Artifact Synchronization（P2-A02 §22）---
# これらは `artifact_sync_status` だけを駆動する。HOLD / REVIEW には入れない。
RC_ARTIFACT_BASE_SEED_DRIFT = "ARTIFACT_BASE_SEED_DRIFT"
RC_ARTIFACT_PRODUCTION_DRIFT = "ARTIFACT_PRODUCTION_DRIFT"
RC_ARTIFACT_CANDIDATE_MASTER_DRIFT = "ARTIFACT_CANDIDATE_MASTER_DRIFT"
RC_ARTIFACT_RESOLUTION_DRIFT = "ARTIFACT_RESOLUTION_DRIFT"
RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE = "ARTIFACT_SYNC_INPUT_UNAVAILABLE"

# --- Seed ↔ Production identity 軸（P2-B04）---
#
# `RC_SEED_PRODUCTION_EXACT` とは **別語彙**である。混ぜてはならない。
# `SAME_SUPPORTED` を AUTO_PASS evidence として扱わない。
# B03 の `CONFLICT` 単独を HOLD にしない（P2-B04 v1）。
RC_IDENTITY_EVIDENCE_SAME_SUPPORTED = "IDENTITY_EVIDENCE_SAME_SUPPORTED"
RC_IDENTITY_EVIDENCE_REVIEW_REQUIRED = "IDENTITY_EVIDENCE_REVIEW_REQUIRED"
RC_IDENTITY_EVIDENCE_CONFLICT = "IDENTITY_EVIDENCE_CONFLICT"
RC_IDENTITY_EVIDENCE_INSUFFICIENT = "IDENTITY_EVIDENCE_INSUFFICIENT"
RC_IDENTITY_EVIDENCE_NOT_EVALUATED = "IDENTITY_EVIDENCE_NOT_EVALUATED"

# 評価済み identity evidence は REVIEW を駆動する（HOLD は作らない）。
IDENTITY_EVIDENCE_REVIEW_CODES = frozenset(
    {
        RC_IDENTITY_EVIDENCE_SAME_SUPPORTED,
        RC_IDENTITY_EVIDENCE_REVIEW_REQUIRED,
        RC_IDENTITY_EVIDENCE_CONFLICT,
        RC_IDENTITY_EVIDENCE_INSUFFICIENT,
    }
)

# identity status -> reason code。
IDENTITY_STATUS_REASON_CODES = {
    IDENTITY_SAME_SUPPORTED: RC_IDENTITY_EVIDENCE_SAME_SUPPORTED,
    IDENTITY_REVIEW_REQUIRED: RC_IDENTITY_EVIDENCE_REVIEW_REQUIRED,
    IDENTITY_CONFLICT: RC_IDENTITY_EVIDENCE_CONFLICT,
    IDENTITY_INSUFFICIENT: RC_IDENTITY_EVIDENCE_INSUFFICIENT,
    IDENTITY_NOT_EVALUATED: RC_IDENTITY_EVIDENCE_NOT_EVALUATED,
}

ANCHOR_SEMANTICS_REASON_CODES = frozenset(
    {
        RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
        RC_ANCHOR_SEMANTICS_UNKNOWN,
    }
)

# artifact drift を表す code（`ARTIFACT_SYNC_INPUT_UNAVAILABLE` は drift では
# なく「判定できない」なので含めない）。
ARTIFACT_DRIFT_REASON_CODES = frozenset(
    {
        RC_ARTIFACT_BASE_SEED_DRIFT,
        RC_ARTIFACT_PRODUCTION_DRIFT,
        RC_ARTIFACT_CANDIDATE_MASTER_DRIFT,
        RC_ARTIFACT_RESOLUTION_DRIFT,
    }
)

# P2-A02 §17 の ARTIFACT_SYNC_REASON class。
ARTIFACT_SYNC_REASON_CODES = ARTIFACT_DRIFT_REASON_CODES | {
    RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE
}

HOLD_REASON_CODES = frozenset(
    {
        RC_MISSING_SEED,
        RC_MISSING_PRODUCTION,
        RC_DUPLICATE_PRODUCTION_IDENTITY,
        RC_IDENTITY_NOT_EXACT,
        RC_PRODUCTION_SNAPSHOT_UNAVAILABLE,
        RC_PRIMARY_SOURCE_MISSING,
        RC_PRIMARY_SOURCE_WRONG_ENTITY,
        RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY,
        RC_PRIMARY_COORDINATE_UNTRACEABLE,
        RC_AMBIGUOUS_SAME_NAME_SHRINE,
        RC_IDENTITY_EVIDENCE_MISSING,
        RC_POSITION_CONTRACT_HOLD_RECORD,
        RC_RESOLUTION_SOURCE_URL_MISSING,
    }
)

REVIEW_REASON_CODES = frozenset(
    {
        RC_PRIMARY_COORDINATE_DIFFERS,
        RC_ADDRESS_CONFLICT_UNEXPLAINED,
        RC_CORROBORATION_CONFLICT,
        RC_PRIMARY_ENTITY_AMBIGUOUS,
        RC_RESOLUTION_RECORD_COORDINATE_MISMATCH,
        RC_PRIMARY_SOURCE_TYPE_MISSING,
        RC_PRIMARY_SOURCE_VERIFIED_AT_MISSING,
        RC_RESOLUTION_SOURCE_TYPE_MISSING,
        RC_RESOLUTION_VERIFIED_AT_MISSING,
        # P2-A02 §12 / §19
        RC_POSITION_PROOF_UNAVAILABLE,
        RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
        RC_ANCHOR_SEMANTICS_UNKNOWN,
        # P2-B04: 評価済み identity evidence は REVIEW を駆動する。
        # HOLD には入れない（B03 の CONFLICT 単独を HOLD にしない）。
        RC_IDENTITY_EVIDENCE_SAME_SUPPORTED,
        RC_IDENTITY_EVIDENCE_REVIEW_REQUIRED,
        RC_IDENTITY_EVIDENCE_CONFLICT,
        RC_IDENTITY_EVIDENCE_INSUFFICIENT,
    }
)

# ---------------------------------------------------------------------------
# OBSERVATION_REASON（P2-A02 §17 / §18）
# ---------------------------------------------------------------------------
# 報告はするが **単独では Position status を動かさない** code。
# 後方互換のため `reason_codes` には出し続けるが、`_classify()` には
# 参加させない（P2-A02 §18 の「reason_codes に出ること」と
# 「status を駆動すること」の分離）。
OBSERVATION_REASON_CODES = frozenset(
    {
        # retrieval observation（P2-A02 §12）
        RC_SOURCE_FETCH_FAILED,
        RC_SOURCE_PARSE_FAILED,
        RC_POSITION_SOURCE_REDIRECTED,
        RC_PRIMARY_EVIDENCE_NOT_RETRIEVED,
        # Spreadsheet observation（P2-A02 §14 / §16）
        RC_SPREADSHEET_ROW_MISSING,
        RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE,
        RC_SPREADSHEET_IDENTITY_REVIEW,
        RC_SPREADSHEET_POSITION_SOURCE_MISMATCH,
        # identity / anchor 構造の observation（P2-A02 §13 / §18）
        RC_IDENTITY_NORMALIZATION_REQUIRED,
        RC_MULTIPLE_POI_CANDIDATES,
        # 後方互換の legacy 観測値（P2-A02 §22）。
        # artifact drift は `ARTIFACT_BASE_SEED_DRIFT` が所有する。
        RC_SEED_PRODUCTION_COORDINATE_DIFFERS,
        # positive な観測
        RC_SEED_PRODUCTION_EXACT,
        # P2-B04: identity evidence 未評価は観測のみ。status を動かさない
        # （既存挙動との後方互換）。
        RC_IDENTITY_EVIDENCE_NOT_EVALUATED,
    }
)

# Primary Evidence 側の **blocking conflict**（P2-A02 §9 / §13）。
#
# これらが立っているとき:
#   * Primary Evidence 経路は現在の Position を証明できない
#   * より新しい矛盾として Resolution Record の再利用も塞ぐ
#
# `MULTIPLE_POI_CANDIDATES` は **含めない**。POI 候補が複数あることは
# 構造の観測であって座標の矛盾ではなく、Anchor Semantics が明示的に
# 解決された後は単独で再利用を塞いではならない（P2-A02 §13）。
PRIMARY_BLOCKING_CONFLICT_CODES = frozenset(
    {
        RC_PRIMARY_COORDINATE_DIFFERS,
        RC_PRIMARY_SOURCE_WRONG_ENTITY,
        RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY,
        RC_PRIMARY_ENTITY_AMBIGUOUS,
        RC_IDENTITY_EVIDENCE_MISSING,
    }
)

# 後方互換の別名（既存 report / test からの参照を壊さない）。
RESOLUTION_CONFLICTING_EVIDENCE_CODES = PRIMARY_BLOCKING_CONFLICT_CODES

# `POSITION_PROOF_UNAVAILABLE` を抑止する code。
#
# proof path が NONE でも、**なぜ NONE なのか**を説明する status-driving な
# Position reason が既にあるなら、重ねて proof unavailable とは言わない
# （P2-A02 §12 / GC-06 / GC-18 / GC-23）。
#
# Anchor Semantics code は除外する。Anchor gate は proof path が NONE で
# ある理由の説明ではなく独立した gate であり、proof 不在という事実を
# 隠してはならない。
POSITION_PROOF_EXPLAINING_CODES = frozenset(
    (HOLD_REASON_CODES | REVIEW_REASON_CODES)
    - ANCHOR_SEMANTICS_REASON_CODES
    - {RC_POSITION_PROOF_UNAVAILABLE}
)

# 類似候補の表示しきい値。REVIEW 候補の提示専用であり、自動 MATCH には使わない。
SIMILARITY_THRESHOLD = 0.80


class AuditError(Exception):
    """監査を実行できない入力状態。"""


# ---------------------------------------------------------------------------
# Normalization（比較専用。永続値を書き換えない）
# ---------------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r"\s+")
_POSTAL_PREFIX_RE = re.compile(r"^〒?\s*\d{3}\s*-?\s*\d{4}\s*")
_DASH_VARIANTS = "－‐‑‒–—―ー−"
_DASH_TABLE = {ord(ch): "-" for ch in _DASH_VARIANTS}


def normalize_name(value: str | None) -> str:
    """名称比較用の正規化。NFKC / 前後空白 / 連続空白のみ。"""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_address(value: str | None) -> str:
    """住所比較用の正規化。

    行うのは NFKC / `日本、` prefix / 郵便番号 prefix / 全角 ASCII 数字
    （NFKC が担当）/ dash 異体字 / 空白のみ。

    丁目・番・番地・号 の意味的な書き換えは **行わない**。その変換を所有する
    テスト済みの既存 utility が repository に無いため、過剰正規化して
    別地番を同一視するより fail closed（差分として表面化）を選ぶ。
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.strip()
    if text.startswith("日本、"):
        text = text[len("日本、"):]
    text = _POSTAL_PREFIX_RE.sub("", text)
    text = text.translate(_DASH_TABLE)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def normalize_anchor_semantics(value: str | None) -> str:
    """Anchor Semantics 入力を閉じた enum へ正規化する（P2-A02 §6 / §7）。

    * 4つの許可値 -> その値
    * 未設定 / 空 -> `NOT_EVALUATED`（「まだ評価していない」を明示）
    * それ以外 -> `UNKNOWN`（未知を `CONFIRMED` と解釈しない = fail safe）

    どちらの fail-safe も REVIEW へ写像する。値は発明しない（P2-A02 §29）。
    """
    if value is None:
        return ANCHOR_SEMANTICS_NOT_EVALUATED
    text = str(value).strip().upper()
    if not text:
        return ANCHOR_SEMANTICS_NOT_EVALUATED
    if text in ANCHOR_SEMANTICS_INPUT_VALUES:
        return text
    return ANCHOR_SEMANTICS_UNKNOWN


def _similarity(a: str, b: str) -> float:
    from difflib import SequenceMatcher  # 局所 import（CLI 起動を軽くする）

    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------


def coordinates_equal(a: float | None, b: float | None) -> bool:
    """Float Comparison Contract v1 に従う同値判定。

    None の意味は厳密に維持する（None vs numeric は different）。
    """
    if a is None or b is None:
        return a is None and b is None
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a == b
    return math.isclose(
        float(a),
        float(b),
        rel_tol=COORDINATE_REL_TOLERANCE,
        abs_tol=COORDINATE_ABS_TOLERANCE,
    )


def coordinate_delta_m(
    lat_a: float | None,
    lng_a: float | None,
    lat_b: float | None,
    lng_b: float | None,
) -> float | None:
    """haversine 距離（m）。**報告専用の観測値**であり判定閾値ではない。"""
    if None in (lat_a, lng_a, lat_b, lng_b):
        return None
    phi1 = math.radians(float(lat_a))
    phi2 = math.radians(float(lat_b))
    d_phi = phi2 - phi1
    d_lambda = math.radians(float(lng_b) - float(lng_a))
    h = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_MEAN_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


def _round_delta(value: float | None) -> float | None:
    """報告用に丸める。出力の byte 安定性のため桁を固定する。"""
    if value is None:
        return None
    return round(value, 3)


# ---------------------------------------------------------------------------
# Normalized input model（Django model に結合しない）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Identity:
    candidate_id: str | None = None
    production_id: int | None = None
    name_jp: str = ""
    official_name: str | None = None
    address: str = ""
    official_address: str | None = None


@dataclass(frozen=True)
class SeedPosition:
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class ProductionPosition:
    latitude: float | None = None
    longitude: float | None = None
    kind: str | None = None
    # `temples_shrine.place_ref_id` は `PlaceRef.place_id`（CharField primary key）
    # への FK 値であり、Google Place ID の文字列である。内部の連番 id ではない。
    place_ref_id: str | None = None


@dataclass(frozen=True)
class CandidateMasterPosition:
    """Candidate Master が保持する座標。

    Artifact Synchronization の比較対象であり、Position の真値ではない。
    """

    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class SpreadsheetRow:
    row_id: str | None = None
    name_jp: str | None = None
    address: str | None = None
    official_name: str | None = None
    official_address: str | None = None
    official_source_type: str | None = None
    official_source_url: str | None = None
    verified_at: str | None = None
    reference_latitude: float | None = None
    reference_longitude: float | None = None
    coordinate_delta_m: float | None = None
    coordinate_status: str | None = None
    google_place_id: str | None = None
    position_source_type: str | None = None
    position_source_url: str | None = None
    position_source_note: str | None = None


@dataclass(frozen=True)
class PrimaryPositionEvidence:
    """primary position source から追跡した観測値。

    `status` は retrieval の結果を表す:
      OK / NOT_RETRIEVED / FETCH_FAILED / PARSE_FAILED / REDIRECTED
    """

    status: str = "NOT_RETRIEVED"
    source_type: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    source_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    entity_match: str | None = None  # SAME / DIFFERENT / NON_SHRINE / AMBIGUOUS
    poi_candidate_count: int | None = None
    verified_at: str | None = None
    # Anchor Semantics は **evidence から導出しない**（P2-A02 §6）。
    # この field は snapshot file が明示的に書いた値を
    # `ShrinePositionAuditInput.anchor_semantics_status` まで運ぶだけの
    # transport であり、`evaluate()` はこの field を直接読まない。
    anchor_semantics_status: str | None = None


@dataclass(frozen=True)
class CorroborationSource:
    source_type: str | None = None
    source_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class ExistingResolution:
    record_path: str | None = None
    position_status: str | None = None
    adopted_latitude: float | None = None
    adopted_longitude: float | None = None
    # Position Contract §Audit Record が追跡可能性を求める provenance。
    # Resolution Record 再利用も他の AUTO_PASS 経路と同じ基準を満たす必要がある。
    position_source_type: str | None = None
    position_source_url: str | None = None
    verified_at: str | None = None


@dataclass(frozen=True)
class ShrinePositionAuditInput:
    identity: Identity
    seed: SeedPosition | None = None
    production: ProductionPosition | None = None
    candidate_master: CandidateMasterPosition | None = None
    spreadsheet: SpreadsheetRow | None = None
    spreadsheet_join_status: str = SHEET_JOIN_NONE
    spreadsheet_review_candidates: tuple[str, ...] = ()
    primary_position_evidence: PrimaryPositionEvidence | None = None
    corroboration: tuple[CorroborationSource, ...] = ()
    existing_resolution: ExistingResolution | None = None
    # 明示的な Anchor Semantics 入力（P2-A02 §6）。
    # None は「未評価」であって「確認済み」ではない。
    anchor_semantics_status: str | None = None
    seed_production_join_status: str = JOIN_MATCH_EXACT
    # P2-B04: join status とは **別軸** の identity evidence（B04 adapter 由来）。
    # 既定は未評価で、その場合の挙動は P2-B04 以前と完全に同じである。
    # 非 exact join からここへ `EXACT` を持ち込むことはできない。
    seed_production_identity_status: str = IDENTITY_NOT_EVALUATED
    production_snapshot_available: bool = True
    spreadsheet_snapshot_available: bool = True
    duplicate_production_ids: tuple[int, ...] = ()


@dataclass
class ShrinePositionAuditResult:
    candidate_id: str | None
    production_id: int | None
    name_jp: str
    join_status: str
    spreadsheet_join_status: str
    audit_status: str
    # P2-B04 で追加した identity 軸（join_status とは別）。
    seed_production_identity_status: str = IDENTITY_NOT_EVALUATED
    # P2-B01 で追加した contract-significant field（schema 1.1）。
    position_proof_path: str = PROOF_NONE
    anchor_semantics_status: str = ANCHOR_SEMANTICS_NOT_EVALUATED
    artifact_sync_status: str = ARTIFACT_UNKNOWN
    reason_codes: list[str] = field(default_factory=list)
    stored_address: str | None = None
    official_address: str | None = None
    stored_latitude: float | None = None
    stored_longitude: float | None = None
    seed_latitude: float | None = None
    seed_longitude: float | None = None
    primary_latitude: float | None = None
    primary_longitude: float | None = None
    coordinate_delta_m: float | None = None
    primary_source_type: str | None = None
    primary_source_url: str | None = None
    corroboration_sources: list[dict[str, Any]] = field(default_factory=list)
    existing_resolution_record: str | None = None
    verified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "production_id": self.production_id,
            "name_jp": self.name_jp,
            "join_status": self.join_status,
            "spreadsheet_join_status": self.spreadsheet_join_status,
            "audit_status": self.audit_status,
            "seed_production_identity_status": self.seed_production_identity_status,
            "position_proof_path": self.position_proof_path,
            "anchor_semantics_status": self.anchor_semantics_status,
            "artifact_sync_status": self.artifact_sync_status,
            "reason_codes": list(self.reason_codes),
            "stored_address": self.stored_address,
            "official_address": self.official_address,
            "stored_latitude": self.stored_latitude,
            "stored_longitude": self.stored_longitude,
            "seed_latitude": self.seed_latitude,
            "seed_longitude": self.seed_longitude,
            "primary_latitude": self.primary_latitude,
            "primary_longitude": self.primary_longitude,
            "coordinate_delta_m": self.coordinate_delta_m,
            "primary_source_type": self.primary_source_type,
            "primary_source_url": self.primary_source_url,
            "corroboration_sources": list(self.corroboration_sources),
            "existing_resolution_record": self.existing_resolution_record,
            "verified_at": self.verified_at,
        }


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


def _classify(reason_codes: Iterable[str]) -> str:
    """HOLD > REVIEW > AUTO_PASS の優先順で audit status を決める。"""
    codes = set(reason_codes)
    if codes & HOLD_REASON_CODES:
        return HOLD
    if codes & REVIEW_REASON_CODES:
        return REVIEW
    return AUTO_PASS


def _artifact_sync_status(reason_codes: Iterable[str]) -> str:
    """artifact reason code から `artifact_sync_status` を決める。

    DRIFT > UNKNOWN > SYNCED。Position の audit_status には一切影響しない。
    """
    codes = set(reason_codes)
    if codes & ARTIFACT_DRIFT_REASON_CODES:
        return ARTIFACT_DRIFT
    if RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE in codes:
        return ARTIFACT_UNKNOWN
    return ARTIFACT_SYNCED


def evaluate(item: ShrinePositionAuditInput) -> ShrinePositionAuditResult:
    """1件分の triage。純関数。同じ入力からは常に同じ出力を返す。

    P2-A02 §25 の決定的評価順に従う:

    ```text
    1. canonical HOLD          6. Anchor Semantics gate
    2. identity validation     7. Position status reason
    3. Primary Evidence        8. Artifact Synchronization
    4. newer conflict          9. final audit status
    5. proof path selection   10. serialization
    ```

    後段の層が前段の権威ある結果を黙って上書きしてはならない。
    """
    codes: set[str] = set()

    ident = item.identity
    seed = item.seed
    prod = item.production
    sheet = item.spreadsheet
    evidence = item.primary_position_evidence
    resolution = item.existing_resolution

    # =====================================================================
    # 1. canonical HOLD（P2-A02 §11）
    # =====================================================================
    # canonical な `HOLD_POSITION_REVIEW` は Machine Audit が自動で解除できない。
    # 新しい evidence がどれだけ良く見えても HOLD を維持する。
    canonical_hold = (
        resolution is not None
        and resolution.position_status == "HOLD_POSITION_REVIEW"
    )
    if canonical_hold:
        codes.add(RC_POSITION_CONTRACT_HOLD_RECORD)

    # =====================================================================
    # 2. identity validation
    # =====================================================================
    # --- identity 軸の確定（P2-B04）---------------------------------------
    #
    # `EXACT` は raw exact join だけが生み出す。B03 evidence がどれほど
    # 強くても exact identity にはならない。非 exact join から `EXACT` が
    # 持ち込まれた場合は採用せず未評価へ倒す（fail safe）。
    if item.seed_production_join_status == JOIN_MATCH_EXACT:
        identity_status = IDENTITY_EXACT
    else:
        supplied = str(item.seed_production_identity_status or "").strip().upper()
        identity_status = (
            supplied
            if supplied in SEED_PRODUCTION_IDENTITY_STATUSES
            and supplied != IDENTITY_EXACT
            else IDENTITY_NOT_EVALUATED
        )

    identity_evidence_evaluated = identity_status not in (
        IDENTITY_EXACT,
        IDENTITY_NOT_EVALUATED,
    )

    if not item.production_snapshot_available:
        codes.add(RC_PRODUCTION_SNAPSHOT_UNAVAILABLE)
    elif identity_evidence_evaluated:
        # 非 exact join に対して B03 identity evidence が明示的に供給された。
        # 「identity evidence が欠けている」状態ではないので、従来の
        # identity HOLD ではなく identity 軸の REVIEW code を出す。
        #
        # exact identity ではないことは変わらない。`RC_SEED_PRODUCTION_EXACT`
        # は出さず、Resolution fallback も artifact Production 参照も
        # 開かない。B03 の CONFLICT 単独でも HOLD にしない（v1）。
        codes.add(IDENTITY_STATUS_REASON_CODES[identity_status])
    elif item.seed_production_join_status == JOIN_MISSING_PRODUCTION:
        codes.add(RC_MISSING_PRODUCTION)
    elif item.seed_production_join_status == JOIN_MISSING_SEED:
        codes.add(RC_MISSING_SEED)
    elif item.seed_production_join_status == JOIN_DUPLICATE_MATCH:
        codes.add(RC_DUPLICATE_PRODUCTION_IDENTITY)
    elif item.seed_production_join_status == JOIN_IDENTITY_REVIEW_REQUIRED:
        codes.add(RC_IDENTITY_NOT_EXACT)
    else:
        codes.add(RC_SEED_PRODUCTION_EXACT)

    # exact identity 条件は **両方**を要求する。片方だけでは成立しない。
    identity_is_exact = (
        RC_SEED_PRODUCTION_EXACT in codes and identity_status == IDENTITY_EXACT
    )

    # Seed ↔ Production の座標差は **artifact 同期の観測**であって Position の
    # 正しさではない（P2-A02 §22）。legacy code は後方互換のため出し続けるが、
    # status は駆動しない。実際の drift 判定は §8 で行う。
    if identity_is_exact and seed is not None and prod is not None:
        if not (
            coordinates_equal(seed.latitude, prod.latitude)
            and coordinates_equal(seed.longitude, prod.longitude)
        ):
            codes.add(RC_SEED_PRODUCTION_COORDINATE_DIFFERS)

    # Spreadsheet identity は observation のみ（P2-A02 §14）。
    if not item.spreadsheet_snapshot_available:
        codes.add(RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE)
    elif item.spreadsheet_join_status == SHEET_JOIN_NONE or sheet is None:
        codes.add(RC_SPREADSHEET_ROW_MISSING)
    elif item.spreadsheet_join_status == SHEET_JOIN_REVIEW_CANDIDATE:
        codes.add(RC_SPREADSHEET_IDENTITY_REVIEW)

    # 住所の不一致は identity の矛盾であり、observation ではなく REVIEW。
    if sheet is not None and item.spreadsheet_join_status in (
        SHEET_JOIN_EXACT,
        SHEET_JOIN_CORROBORATED,
    ):
        stored = normalize_address(ident.address)
        official = normalize_address(sheet.official_address or sheet.address)
        if stored and official and stored != official:
            codes.add(RC_ADDRESS_CONFLICT_UNEXPLAINED)

    # =====================================================================
    # 3. Primary Evidence evaluation
    # =====================================================================
    # --- Position provenance の確定（P2-A02 §15）-------------------------
    #
    # Position provenance と identity provenance は別責務である。
    # `official_source_url` / `official_source_type` を Position provenance の
    # 代用にしてはならない。
    #
    # Spreadsheet による補完は「同じ Position source だと機械的に確認できる」
    # ときに限る。Primary source_url が無い状態で Spreadsheet の URL を
    # 流し込むと、その URL から座標を得た証拠が無いのに provenance を
    # 捏造することになる（GC-18）。
    evidence_url = evidence.source_url if evidence is not None else None
    evidence_type = evidence.source_type if evidence is not None else None
    evidence_verified_at = evidence.verified_at if evidence is not None else None

    sheet_position_url = sheet.position_source_url if sheet is not None else None
    sheet_position_type = sheet.position_source_type if sheet is not None else None
    sheet_verified_at = sheet.verified_at if sheet is not None else None

    same_position_source = bool(
        evidence_url and sheet_position_url and evidence_url == sheet_position_url
    )
    # mismatch は **実際に比較できたとき**にだけ言える（P2-A02 §16 / GC-18）。
    # Primary URL が無い場合の問題は「不一致」ではなく「source identity 不明」。
    if evidence_url and sheet_position_url and evidence_url != sheet_position_url:
        codes.add(RC_SPREADSHEET_POSITION_SOURCE_MISMATCH)

    primary_url = evidence_url
    primary_type = evidence_type or (
        sheet_position_type if same_position_source else None
    )
    effective_verified_at = evidence_verified_at or (
        sheet_verified_at if same_position_source else None
    )

    evidence_status = evidence.status if evidence is not None else "NOT_RETRIEVED"

    # Primary Evidence が現在の Production 座標を独立に証明できたか。
    primary_coordinate_proves = False
    primary_provenance_complete = False

    if evidence is not None and evidence_status == "OK":
        # --- entity 同定（fail closed）---
        #
        # entity_match が未設定・空・未知の値のときは「同一と示せていない」
        # のであって「同一である」ではない。
        entity_match = (evidence.entity_match or "").strip().upper()

        if entity_match == "DIFFERENT":
            codes.add(RC_PRIMARY_SOURCE_WRONG_ENTITY)
        elif entity_match == "NON_SHRINE":
            codes.add(RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY)
        elif entity_match == "AMBIGUOUS":
            codes.add(RC_PRIMARY_ENTITY_AMBIGUOUS)
        elif entity_match == "":
            codes.add(RC_IDENTITY_EVIDENCE_MISSING)
        elif entity_match != "SAME":
            codes.add(RC_PRIMARY_ENTITY_AMBIGUOUS)

        # POI 候補が複数あることは構造の observation（P2-A02 §13 / GC-12）。
        # 単独で REVIEW を駆動せず、proof path も塞がない。
        if (evidence.poi_candidate_count or 0) > 1:
            codes.add(RC_MULTIPLE_POI_CANDIDATES)

        if evidence.latitude is None or evidence.longitude is None:
            codes.add(RC_PRIMARY_COORDINATE_UNTRACEABLE)
        elif entity_match == "SAME":
            # 現在の Production 座標と一致して初めて「現在の Position を
            # 証明した」と言える。差があれば自動採用せず矛盾として扱う。
            if prod is not None and (
                coordinates_equal(evidence.latitude, prod.latitude)
                and coordinates_equal(evidence.longitude, prod.longitude)
            ):
                primary_coordinate_proves = True
            elif prod is not None:
                codes.add(RC_PRIMARY_COORDINATE_DIFFERS)

            # provenance は座標一致とは独立に観測する。
            # Position Contract §Audit Record が position_source_type /
            # position_source_url / verified_at の追跡可能性を求める。
            if not primary_url:
                codes.add(RC_PRIMARY_SOURCE_MISSING)
            else:
                if not primary_type:
                    codes.add(RC_PRIMARY_SOURCE_TYPE_MISSING)
                if not effective_verified_at:
                    codes.add(RC_PRIMARY_SOURCE_VERIFIED_AT_MISSING)
                primary_provenance_complete = bool(
                    primary_type and effective_verified_at
                )
    elif evidence_status == "FETCH_FAILED":
        codes.add(RC_SOURCE_FETCH_FAILED)
    elif evidence_status == "PARSE_FAILED":
        codes.add(RC_SOURCE_PARSE_FAILED)
    elif evidence_status == "REDIRECTED":
        codes.add(RC_POSITION_SOURCE_REDIRECTED)
    else:
        # 取得していない。これ自体は observation であり、Position status は
        # 「有効な proof path があるか」で決まる（P2-A02 §12 / GC-24）。
        codes.add(RC_PRIMARY_EVIDENCE_NOT_RETRIEVED)

    # =====================================================================
    # 4. newer conflict evaluation（P2-A02 §13）
    # =====================================================================
    primary_conflict = bool(codes & PRIMARY_BLOCKING_CONFLICT_CODES)

    # --- Resolution Record が fallback 候補かどうか ------------------------
    #
    # provenance 欠落の reason code をここで出すと、有効な Primary Evidence
    # 経路まで巻き添えで REVIEW / HOLD に落ちる（path poisoning）。
    # どちらの経路を使うか決めてから §5 でまとめて判定する。
    #
    # canonical HOLD record は再利用可能な PASS fallback ではない（GC-23）。
    resolution_is_pass = (
        resolution is not None and resolution.position_status == "PASS"
    )
    resolution_candidate = False
    resolution_provenance_complete = False
    resolution_coordinate_mismatch = False
    if (
        resolution_is_pass
        and identity_is_exact
        and seed is not None
        and prod is not None
    ):
        matches_seed = coordinates_equal(
            seed.latitude, resolution.adopted_latitude
        ) and coordinates_equal(seed.longitude, resolution.adopted_longitude)
        matches_prod = coordinates_equal(
            prod.latitude, resolution.adopted_latitude
        ) and coordinates_equal(prod.longitude, resolution.adopted_longitude)
        if not (matches_seed and matches_prod):
            resolution_coordinate_mismatch = True
        else:
            resolution_candidate = True
            resolution_provenance_complete = bool(
                resolution.position_source_url
                and resolution.position_source_type
                and resolution.verified_at
            )

    # =====================================================================
    # 5. proof path selection（P2-A02 §8 / §9 / §10）
    # =====================================================================
    # 有効な proof path は **排他的に1つ**。positive な proof reason も排他的で、
    # `PRIMARY_SOURCE_VERIFIED` と `RESOLUTION_RECORD_REUSED` が同時に立つことは
    # ない。使わなかった経路の欠陥は、選ばれた経路を汚染しない（GC-02）。
    if canonical_hold:
        # canonical HOLD は proof path の選択より前に効く（P2-A02 §25-1）。
        position_proof_path = PROOF_NONE
    elif (
        primary_coordinate_proves
        and primary_provenance_complete
        and not primary_conflict
    ):
        position_proof_path = PROOF_PRIMARY_EVIDENCE
        codes.add(RC_PRIMARY_SOURCE_VERIFIED)
    elif (
        resolution_candidate
        and resolution_provenance_complete
        and not primary_conflict
    ):
        position_proof_path = PROOF_RESOLUTION_FALLBACK
        codes.add(RC_RESOLUTION_RECORD_REUSED)
    else:
        position_proof_path = PROOF_NONE

    # --- Resolution 経路の欠陥は、その経路が実際に必要なときだけ効く -------
    # （P2-A02 §23）
    if position_proof_path == PROOF_NONE and not canonical_hold:
        if resolution_coordinate_mismatch:
            codes.add(RC_RESOLUTION_RECORD_COORDINATE_MISMATCH)
        elif (
            resolution_candidate
            and not primary_conflict
            and not resolution_provenance_complete
        ):
            # fallback に依存しているのに provenance が追跡できない。
            # ここで初めて fail closed する（fallback は発明しない）。
            if not resolution.position_source_url:
                codes.add(RC_RESOLUTION_SOURCE_URL_MISSING)
            if not resolution.position_source_type:
                codes.add(RC_RESOLUTION_SOURCE_TYPE_MISSING)
            if not resolution.verified_at:
                codes.add(RC_RESOLUTION_VERIFIED_AT_MISSING)

    # --- 出力 provenance は選ばれた経路からのみ取る（P2-A02 §24）----------
    # 無関係な経路の metadata を混ぜた hybrid provenance を作らない。
    if position_proof_path == PROOF_RESOLUTION_FALLBACK:
        primary_type = resolution.position_source_type
        primary_url = resolution.position_source_url
        effective_verified_at = resolution.verified_at

    # =====================================================================
    # 6. Anchor Semantics gate（P2-A02 §7 / §19）
    # =====================================================================
    # proof path が成立していても、その座標が Visitor / Navigation Anchor と
    # して妥当かは別問題。Resolution fallback もこの gate を迂回できない。
    # Anchor Semantics 単独では HOLD を作らない（P2-A02 §7）。
    anchor_semantics_status = normalize_anchor_semantics(
        item.anchor_semantics_status
    )
    if anchor_semantics_status == ANCHOR_SEMANTICS_REVIEW_REQUIRED:
        codes.add(RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED)
    elif anchor_semantics_status == ANCHOR_SEMANTICS_NOT_EVALUATED:
        codes.add(RC_ANCHOR_SEMANTICS_NOT_EVALUATED)
    elif anchor_semantics_status == ANCHOR_SEMANTICS_UNKNOWN:
        codes.add(RC_ANCHOR_SEMANTICS_UNKNOWN)

    # =====================================================================
    # 7. Position status-driving reason（P2-A02 §12）
    # =====================================================================
    # proof path が無いこと **自体** が status を決める条件であるときだけ
    # `POSITION_PROOF_UNAVAILABLE` を出す。なぜ NONE なのかを説明する
    # status-driving な reason が既にあるなら重ねて言わない。
    #
    #   SOURCE_FETCH_FAILED        = 取得できなかったという観測
    #   POSITION_PROOF_UNAVAILABLE = 有効な proof path が存在しない
    if position_proof_path == PROOF_NONE and not (
        codes & POSITION_PROOF_EXPLAINING_CODES
    ):
        codes.add(RC_POSITION_PROOF_UNAVAILABLE)

    # =====================================================================
    # 8. Artifact Synchronization（P2-A02 §20 / §21 / §22）
    # =====================================================================
    # Position の正しさとは独立に、repository が管理する current-state
    # artifact が adopted Position と揃っているかを見る。
    #
    # 参照基準は **Production 座標**（= live な adopted Position）。
    # 歴史的 artifact（closed audit / Source Packet / superseded record /
    # snapshot）は同期の authority ではないので比較対象にしない。
    artifact_reference_available = (
        item.production_snapshot_available
        and item.seed_production_join_status == JOIN_MATCH_EXACT
        and prod is not None
        and prod.latitude is not None
        and prod.longitude is not None
    )
    if not artifact_reference_available:
        # 参照基準（Production 座標）が無いので、揃っているともずれている
        # とも言えない。snapshot 不在 / 重複 / identity 未確定 / 座標欠落 /
        # `MISSING_PRODUCTION` のすべてがここに入る。
        #
        # `MISSING_PRODUCTION` を drift と断定しないことが重要である。
        # この join status が示すのは次だけであり、
        #
        #   production snapshot が存在する
        #   かつ Seed identity が存在する
        #   かつ exact (name_jp, address) の一致件数が 0
        #
        # 「その Shrine が Production に**存在しない**」ことは証明していない。
        # 同じ Shrine が別の name / address 表現で存在しうる（§3 の join は
        # 正規化も fuzzy match も行わない）。したがって不在ではなく
        # **判定不能**として扱う。
        #
        # `ARTIFACT_PRODUCTION_DRIFT` は、より強い identity resolution に
        # よって Production 不在を確定できる将来の状態のために予約する。
        codes.add(RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE)
    else:
        ref_lat = prod.latitude
        ref_lng = prod.longitude

        if seed is not None and seed.latitude is not None and seed.longitude is not None:
            if not (
                coordinates_equal(seed.latitude, ref_lat)
                and coordinates_equal(seed.longitude, ref_lng)
            ):
                codes.add(RC_ARTIFACT_BASE_SEED_DRIFT)
        else:
            codes.add(RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE)

        master = item.candidate_master
        if (
            master is not None
            and master.latitude is not None
            and master.longitude is not None
        ):
            if not (
                coordinates_equal(master.latitude, ref_lat)
                and coordinates_equal(master.longitude, ref_lng)
            ):
                codes.add(RC_ARTIFACT_CANDIDATE_MASTER_DRIFT)

        # current adopted Position Resolution Record のみ。
        # canonical HOLD record は adopted Position を持たないため対象外。
        if (
            resolution_is_pass
            and resolution.adopted_latitude is not None
            and resolution.adopted_longitude is not None
        ):
            if not (
                coordinates_equal(resolution.adopted_latitude, ref_lat)
                and coordinates_equal(resolution.adopted_longitude, ref_lng)
            ):
                codes.add(RC_ARTIFACT_RESOLUTION_DRIFT)

    artifact_sync_status = _artifact_sync_status(codes)

    # =====================================================================
    # Corroboration（単独では AUTO_PASS へ昇格させない）
    # =====================================================================
    corroboration_payload: list[dict[str, Any]] = []
    for source in item.corroboration:
        corroboration_payload.append(
            {
                "source_type": source.source_type,
                "source_url": source.source_url,
                "latitude": source.latitude,
                "longitude": source.longitude,
                "coordinate_delta_m": _round_delta(
                    coordinate_delta_m(
                        prod.latitude if prod else None,
                        prod.longitude if prod else None,
                        source.latitude,
                        source.longitude,
                    )
                ),
            }
        )
    # corroboration は proof path を作らない。primary / resolution の
    # どちらも成立しなければ proof path は NONE のままである。

    # =====================================================================
    # 9. final audit status / 10. serialization
    # =====================================================================
    primary_lat = evidence.latitude if evidence is not None else None
    primary_lng = evidence.longitude if evidence is not None else None
    delta = _round_delta(
        coordinate_delta_m(
            prod.latitude if prod else None,
            prod.longitude if prod else None,
            primary_lat,
            primary_lng,
        )
    )

    result = ShrinePositionAuditResult(
        candidate_id=ident.candidate_id,
        production_id=ident.production_id,
        name_jp=ident.name_jp,
        join_status=item.seed_production_join_status,
        spreadsheet_join_status=item.spreadsheet_join_status,
        audit_status=_classify(codes),
        seed_production_identity_status=identity_status,
        position_proof_path=position_proof_path,
        anchor_semantics_status=anchor_semantics_status,
        artifact_sync_status=artifact_sync_status,
        reason_codes=sorted(codes),
        stored_address=ident.address or None,
        official_address=(sheet.official_address if sheet else None)
        or ident.official_address,
        stored_latitude=prod.latitude if prod else None,
        stored_longitude=prod.longitude if prod else None,
        seed_latitude=seed.latitude if seed else None,
        seed_longitude=seed.longitude if seed else None,
        primary_latitude=primary_lat,
        primary_longitude=primary_lng,
        coordinate_delta_m=delta,
        primary_source_type=primary_type,
        primary_source_url=primary_url,
        corroboration_sources=corroboration_payload,
        existing_resolution_record=resolution.record_path if resolution else None,
        verified_at=effective_verified_at,
    )
    return result


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_base_seed(path: Path = BASE_SEED_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise AuditError(f"Base Seed not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise AuditError("Base Seed must be a JSON list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise AuditError(f"Base Seed row {index} is not a JSON object")
        rows.append(
            {
                "name_jp": row.get("name_jp") or "",
                "address": row.get("address") or "",
                "latitude": _as_float(row.get("latitude")),
                "longitude": _as_float(row.get("longitude")),
            }
        )
    return rows


def extract_snapshot_json(text: str) -> str:
    """psql の aligned 出力から json_agg 結果を取り出す。純 JSON もそのまま通す。"""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise AuditError(
            "production snapshot does not contain a JSON array; expected the output "
            "of sql/shrine_position_audit_snapshot.sql"
        )
    return text[start : end + 1]


def load_production_snapshot(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AuditError(f"production snapshot not found: {path}")
    payload = json.loads(extract_snapshot_json(path.read_text(encoding="utf-8")))
    if not isinstance(payload, list):
        raise AuditError("production snapshot must decode to a JSON list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise AuditError(f"production snapshot row {index} is not an object")
        missing = {"id", "name_jp", "address"} - set(row)
        if missing:
            raise AuditError(
                f"production snapshot row {index} is missing {sorted(missing)}"
            )
        rows.append(
            {
                "id": row["id"],
                "name_jp": row["name_jp"] or "",
                "address": row["address"] or "",
                "latitude": _as_float(row.get("latitude")),
                "longitude": _as_float(row.get("longitude")),
                "kind": row.get("kind"),
                "place_ref_id": _as_str(row.get("place_ref_id")),
            }
        )
    return rows


_SPREADSHEET_FIELDS = (
    "id",
    "name_jp",
    "address",
    "official_name",
    "official_address",
    "official_source_type",
    "official_source_url",
    "verified_at",
    "reference_latitude",
    "reference_longitude",
    "coordinate_delta_m",
    "coordinate_status",
    "google_place_id",
    "position_source_type",
    "position_source_url",
    "position_source_note",
)


def _spreadsheet_row_from_mapping(row: dict[str, Any]) -> SpreadsheetRow:
    return SpreadsheetRow(
        row_id=_as_str(row.get("id")),
        name_jp=_as_str(row.get("name_jp")),
        address=_as_str(row.get("address")),
        official_name=_as_str(row.get("official_name")),
        official_address=_as_str(row.get("official_address")),
        official_source_type=_as_str(row.get("official_source_type")),
        official_source_url=_as_str(row.get("official_source_url")),
        verified_at=_as_str(row.get("verified_at")),
        reference_latitude=_as_float(row.get("reference_latitude")),
        reference_longitude=_as_float(row.get("reference_longitude")),
        coordinate_delta_m=_as_float(row.get("coordinate_delta_m")),
        coordinate_status=_as_str(row.get("coordinate_status")),
        google_place_id=_as_str(row.get("google_place_id")),
        position_source_type=_as_str(row.get("position_source_type")),
        position_source_url=_as_str(row.get("position_source_url")),
        position_source_note=_as_str(row.get("position_source_note")),
    )


def load_spreadsheet_snapshot(path: Path) -> list[SpreadsheetRow]:
    """Spreadsheet の export snapshot（JSON / CSV）を読む。

    Spreadsheet は **Evidence Index** であって Ground Truth ではない。
    live Google Sheets 認証は監査 core の要件にしない。
    """
    if not path.exists():
        raise AuditError(f"spreadsheet snapshot not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        reader = csv.DictReader(text.splitlines())
        return [_spreadsheet_row_from_mapping(dict(row)) for row in reader]

    payload = json.loads(text)
    if isinstance(payload, dict):
        payload = payload.get("rows", [])
    if not isinstance(payload, list):
        raise AuditError("spreadsheet snapshot must decode to a list (or {'rows': [...]})")
    return [
        _spreadsheet_row_from_mapping(row)
        for row in payload
        if isinstance(row, dict)
    ]


_EVIDENCE_STATUSES = frozenset(
    {"OK", "NOT_RETRIEVED", "FETCH_FAILED", "PARSE_FAILED", "REDIRECTED"}
)


def _evidence_from_mapping(row: dict[str, Any]) -> PrimaryPositionEvidence:
    status = (_as_str(row.get("status")) or "NOT_RETRIEVED").upper()
    if status not in _EVIDENCE_STATUSES:
        raise AuditError(
            f"unknown primary evidence status {status!r}; "
            f"expected one of {sorted(_EVIDENCE_STATUSES)}"
        )
    count = row.get("poi_candidate_count")
    return PrimaryPositionEvidence(
        status=status,
        source_type=_as_str(row.get("source_type")),
        source_url=_as_str(row.get("source_url")),
        source_name=_as_str(row.get("source_name")),
        source_address=_as_str(row.get("source_address")),
        latitude=_as_float(row.get("latitude")),
        longitude=_as_float(row.get("longitude")),
        entity_match=_as_str(row.get("entity_match")),
        poi_candidate_count=(None if count in (None, "") else int(count)),
        verified_at=_as_str(row.get("verified_at")),
        # 明示的に書かれた値だけを読む。他 field から導出しない（P2-A02 §6）。
        anchor_semantics_status=_as_str(row.get("anchor_semantics_status")),
    )


def load_primary_evidence_snapshot(
    path: Path,
) -> tuple[dict[str, PrimaryPositionEvidence], dict[tuple[str, str], PrimaryPositionEvidence]]:
    """Primary Position Evidence snapshot（JSON / CSV）を read-only で読む。

    本 PR では **live retrieval を行わない**。evidence は明示的な file 入力
    としてのみ受け取る（検索エンジンによる広域探索は導入しない）。

    各行は次のいずれかで対象 Shrine を指す。両方あっても良い。

    * `candidate_id`
    * verified shrine identity = `official_name` + `official_address`

    どちらも無い行は identity を推測せず `AuditError` にする（fail closed）。

    戻り値は (candidate_id 索引, (name, address) 索引)。
    """
    if not path.exists():
        raise AuditError(f"primary evidence snapshot not found: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        payload: list[dict[str, Any]] = [dict(row) for row in csv.DictReader(text.splitlines())]
    else:
        decoded = json.loads(text)
        if isinstance(decoded, dict):
            decoded = decoded.get("rows", [])
        if not isinstance(decoded, list):
            raise AuditError(
                "primary evidence snapshot must decode to a list (or {'rows': [...]})"
            )
        payload = [row for row in decoded if isinstance(row, dict)]

    by_candidate: dict[str, PrimaryPositionEvidence] = {}
    by_identity: dict[tuple[str, str], PrimaryPositionEvidence] = {}

    for index, row in enumerate(payload):
        evidence = _evidence_from_mapping(row)
        candidate_id = _as_str(row.get("candidate_id"))
        official_name = _as_str(row.get("official_name"))
        official_address = _as_str(row.get("official_address"))

        if not candidate_id and not (official_name and official_address):
            raise AuditError(
                f"primary evidence row {index} has neither candidate_id nor "
                "official_name + official_address; identity は推測しない"
            )
        if candidate_id:
            if candidate_id in by_candidate:
                raise AuditError(
                    f"duplicate primary evidence for candidate_id {candidate_id!r}"
                )
            by_candidate[candidate_id] = evidence
        if official_name and official_address:
            key = (official_name, official_address)
            if key in by_identity:
                raise AuditError(f"duplicate primary evidence for identity {key!r}")
            by_identity[key] = evidence

    return by_candidate, by_identity


def load_candidate_master(path: Path = CANDIDATE_MASTER_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise AuditError(f"candidate master not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(candidates, list):
        raise AuditError("candidate master must contain a 'candidates' list")
    return [row for row in candidates if isinstance(row, dict)]


_RECORD_FIELD_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _record_field(text: str, name: str) -> str | None:
    pattern = _RECORD_FIELD_RE_CACHE.get(name)
    if pattern is None:
        pattern = re.compile(r"^%s\s+= (.+)$" % re.escape(name), re.M)
        _RECORD_FIELD_RE_CACHE[name] = pattern
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def load_resolution_records(
    directory: Path = RESOLUTION_RECORD_DIR,
) -> dict[str, ExistingResolution]:
    """Position Resolution Record を candidate_id -> record で読む。

    Record は **採用した Position と判断履歴の point-in-time 記録**であり、
    Position 採用ルールの authority は `docs/knowledge/shrine-position-contract.md`
    が持つ。自動的な現在の外部真値ではない。
    """
    records: dict[str, ExistingResolution] = {}
    if not directory.exists():
        return records
    for md_path in sorted(directory.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        candidate_id = _record_field(text, "candidate_id")
        if not candidate_id:
            continue
        records[candidate_id] = ExistingResolution(
            record_path=str(md_path.relative_to(REPO_ROOT)),
            position_status=_record_field(text, "position_status"),
            adopted_latitude=_as_float(_record_field(text, "new_latitude")),
            adopted_longitude=_as_float(_record_field(text, "new_longitude")),
            # record に書かれている値だけを読む。fallback を発明しない。
            position_source_type=_record_field(text, "new_position_source_type"),
            position_source_url=_record_field(text, "new_position_source_url"),
            verified_at=_record_field(text, "verified_at"),
        )
    return records


# ---------------------------------------------------------------------------
# Identity joins
# ---------------------------------------------------------------------------


def join_seed_to_production(
    seed_row: dict[str, Any], production_rows: Sequence[dict[str, Any]]
) -> tuple[str, dict[str, Any] | None, tuple[int, ...]]:
    """Seed ↔ Production を exact `(name_jp, address)` で突合する。

    normalization / fuzzy / coordinate rescue は一切行わない。
    exactly one Production row を要求する。
    """
    key = (seed_row["name_jp"], seed_row["address"])
    matches = [
        row for row in production_rows if (row["name_jp"], row["address"]) == key
    ]
    if len(matches) == 1:
        return JOIN_MATCH_EXACT, matches[0], ()
    if len(matches) > 1:
        return (
            JOIN_DUPLICATE_MATCH,
            None,
            tuple(sorted(int(row["id"]) for row in matches)),
        )
    return JOIN_MISSING_PRODUCTION, None, ()


def join_production_to_spreadsheet(
    production_row: dict[str, Any] | None,
    seed_row: dict[str, Any],
    spreadsheet_rows: Sequence[SpreadsheetRow],
    *,
    production_place_id: str | None = None,
) -> tuple[str, SpreadsheetRow | None, tuple[str, ...]]:
    """Production ↔ Spreadsheet の fallback join。

    1. normalized official_name + official_address の unique match
    2. name または address の一致を google_place_id が corroborate
    3. name または address の一致を coordinate evidence が corroborate
    4. 同一 id かつ corroborating identity field が1つ以上

    Spreadsheet の id 単独では identity を成立させない。
    座標単独でも identity を成立させない。
    fuzzy 類似は REVIEW 候補を作るだけで、自動 match にはしない。
    """
    if not spreadsheet_rows:
        return SHEET_JOIN_NONE, None, ()

    # Production 行があればそれを、無ければ Seed 行を identity の出発点にする。
    identity_row = production_row if production_row is not None else seed_row
    name = normalize_name(identity_row.get("name_jp"))
    address = normalize_address(identity_row.get("address"))
    prod_lat = production_row.get("latitude") if production_row else None
    prod_lng = production_row.get("longitude") if production_row else None
    prod_id = str(production_row["id"]) if production_row else None

    # --- 1. official_name + official_address の unique match ---
    exact = [
        row
        for row in spreadsheet_rows
        if normalize_name(row.official_name or row.name_jp) == name
        and normalize_address(row.official_address or row.address) == address
        and name
        and address
    ]
    if len(exact) == 1:
        return SHEET_JOIN_EXACT, exact[0], ()
    if len(exact) > 1:
        return (
            SHEET_JOIN_REVIEW_CANDIDATE,
            None,
            tuple(sorted(str(row.row_id) for row in exact)),
        )

    def name_or_address_matches(row: SpreadsheetRow) -> bool:
        return (
            bool(name) and normalize_name(row.official_name or row.name_jp) == name
        ) or (
            bool(address)
            and normalize_address(row.official_address or row.address) == address
        )

    # --- 2. google_place_id による corroboration ---
    if production_place_id:
        corroborated = [
            row
            for row in spreadsheet_rows
            if row.google_place_id
            and row.google_place_id == production_place_id
            and name_or_address_matches(row)
        ]
        if len(corroborated) == 1:
            return SHEET_JOIN_CORROBORATED, corroborated[0], ()

    # --- 3. coordinate evidence による corroboration ---
    if prod_lat is not None and prod_lng is not None:
        corroborated = [
            row
            for row in spreadsheet_rows
            if coordinates_equal(row.reference_latitude, prod_lat)
            and coordinates_equal(row.reference_longitude, prod_lng)
            and name_or_address_matches(row)
        ]
        if len(corroborated) == 1:
            return SHEET_JOIN_CORROBORATED, corroborated[0], ()

    # --- 4. 同一 id + corroborating identity field ---
    if prod_id is not None:
        same_id = [row for row in spreadsheet_rows if row.row_id == prod_id]
        corroborated = [row for row in same_id if name_or_address_matches(row)]
        if len(corroborated) == 1:
            return SHEET_JOIN_CORROBORATED, corroborated[0], ()
        # id だけの一致は identity を成立させない（REVIEW 候補として残す）。

    # --- fuzzy は REVIEW 候補のみ ---
    candidates: list[tuple[float, str]] = []
    for row in spreadsheet_rows:
        score = max(
            _similarity(name, normalize_name(row.official_name or row.name_jp)),
            _similarity(address, normalize_address(row.official_address or row.address)),
        )
        if score >= SIMILARITY_THRESHOLD:
            candidates.append((score, str(row.row_id)))
    if candidates:
        candidates.sort(key=lambda pair: (-pair[0], pair[1]))
        return (
            SHEET_JOIN_REVIEW_CANDIDATE,
            None,
            tuple(row_id for _score, row_id in candidates[:3]),
        )

    return SHEET_JOIN_NONE, None, ()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def build_inputs(
    *,
    seed_rows: Sequence[dict[str, Any]],
    production_rows: Sequence[dict[str, Any]] | None,
    spreadsheet_rows: Sequence[SpreadsheetRow] | None,
    candidates: Sequence[dict[str, Any]],
    resolution_records: dict[str, ExistingResolution],
    primary_evidence_by_candidate: dict[str, PrimaryPositionEvidence] | None = None,
    primary_evidence_by_identity: dict[tuple[str, str], PrimaryPositionEvidence]
    | None = None,
    identity_statuses_by_candidate: dict[str, str] | None = None,
    candidate_ids: Sequence[str] | None = None,
    batch: str | None = None,
) -> list[ShrinePositionAuditInput]:
    """Candidate Master を起点に監査対象を組み立てる。

    Candidate Master は candidate_id / 履歴を持つが、**自動的な現在の
    外部真値ではない**。ここでは監査対象の選択と identity の出発点として
    のみ使う。
    """
    selected: list[dict[str, Any]] = []
    for row in candidates:
        if candidate_ids and row.get("candidate_id") not in set(candidate_ids):
            continue
        if batch and row.get("build_batch") != batch:
            continue
        if not candidate_ids and not batch:
            selected.append(row)
            continue
        selected.append(row)
    selected.sort(key=lambda row: str(row.get("candidate_id")))

    seed_index = {(row["name_jp"], row["address"]): row for row in seed_rows}
    # P2-B04: identity 軸は **明示的に供給されたときだけ** 使う。
    # 候補探索も推測もしない（未供給は NOT_EVALUATED）。
    identity_statuses = identity_statuses_by_candidate or {}
    evidence_by_candidate = primary_evidence_by_candidate or {}
    evidence_by_identity = primary_evidence_by_identity or {}

    def _evidence_for(
        candidate_id: str | None, official_name: str | None, official_address: str | None
    ) -> PrimaryPositionEvidence | None:
        """candidate_id を優先し、無ければ verified identity で引く。"""
        if candidate_id and candidate_id in evidence_by_candidate:
            return evidence_by_candidate[candidate_id]
        if official_name and official_address:
            return evidence_by_identity.get((official_name, official_address))
        return None

    items: list[ShrinePositionAuditInput] = []
    for row in selected:
        candidate_id = row.get("candidate_id")
        official_name = row.get("official_name")
        official_address = row.get("official_address")

        evidence_row = _evidence_for(candidate_id, official_name, official_address)
        # Anchor Semantics は evidence snapshot が明示的に書いた値だけを運ぶ。
        # 行が無い / 値が無い場合は `NOT_EVALUATED` として fail safe に扱われる
        # （`normalize_anchor_semantics`）。推測で埋めない（P2-A02 §6 / §29）。
        anchor_semantics_status = (
            evidence_row.anchor_semantics_status if evidence_row is not None else None
        )

        if not official_name or not official_address:
            # canonical identity が未確定。推測で candidate_name 等へ代替しない。
            items.append(
                ShrinePositionAuditInput(
                    identity=Identity(
                        candidate_id=candidate_id,
                        name_jp=str(row.get("candidate_name") or ""),
                    ),
                    anchor_semantics_status=anchor_semantics_status,
                    seed_production_identity_status=identity_statuses.get(
                        candidate_id or "", IDENTITY_NOT_EVALUATED
                    ),
                    seed_production_join_status=JOIN_IDENTITY_REVIEW_REQUIRED,
                    production_snapshot_available=production_rows is not None,
                    spreadsheet_snapshot_available=spreadsheet_rows is not None,
                )
            )
            continue

        seed_row = seed_index.get((official_name, official_address))
        if seed_row is None:
            items.append(
                ShrinePositionAuditInput(
                    identity=Identity(
                        candidate_id=candidate_id,
                        name_jp=official_name,
                        official_name=official_name,
                        address=official_address,
                        official_address=official_address,
                    ),
                    anchor_semantics_status=anchor_semantics_status,
                    seed_production_identity_status=identity_statuses.get(
                        candidate_id or "", IDENTITY_NOT_EVALUATED
                    ),
                    seed_production_join_status=JOIN_MISSING_SEED,
                    production_snapshot_available=production_rows is not None,
                    spreadsheet_snapshot_available=spreadsheet_rows is not None,
                    existing_resolution=resolution_records.get(candidate_id or ""),
                )
            )
            continue

        if production_rows is None:
            join_status: str = JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE
            production_row: dict[str, Any] | None = None
            duplicates: tuple[int, ...] = ()
        else:
            join_status, production_row, duplicates = join_seed_to_production(
                seed_row, production_rows
            )

        if spreadsheet_rows is None:
            sheet_status, sheet_row, sheet_candidates = SHEET_JOIN_NONE, None, ()
        else:
            sheet_status, sheet_row, sheet_candidates = join_production_to_spreadsheet(
                production_row,
                seed_row,
                spreadsheet_rows,
                # Production 側 place_ref_id は PlaceRef.place_id（= Google Place ID）
                # の文字列。join rule 2（place_id corroboration）を実際に到達可能にする。
                production_place_id=(
                    production_row.get("place_ref_id") if production_row else None
                ),
            )

        items.append(
            ShrinePositionAuditInput(
                identity=Identity(
                    candidate_id=candidate_id,
                    production_id=int(production_row["id"]) if production_row else None,
                    name_jp=official_name,
                    official_name=official_name,
                    address=official_address,
                    official_address=official_address,
                ),
                seed=SeedPosition(
                    latitude=seed_row.get("latitude"),
                    longitude=seed_row.get("longitude"),
                ),
                candidate_master=CandidateMasterPosition(
                    latitude=_as_float(row.get("latitude")),
                    longitude=_as_float(row.get("longitude")),
                ),
                production=(
                    ProductionPosition(
                        latitude=production_row.get("latitude"),
                        longitude=production_row.get("longitude"),
                        kind=production_row.get("kind"),
                        place_ref_id=production_row.get("place_ref_id"),
                    )
                    if production_row
                    else None
                ),
                spreadsheet=sheet_row,
                spreadsheet_join_status=sheet_status,
                spreadsheet_review_candidates=sheet_candidates,
                primary_position_evidence=evidence_row,
                anchor_semantics_status=anchor_semantics_status,
                existing_resolution=resolution_records.get(candidate_id or ""),
                seed_production_identity_status=identity_statuses.get(
                    candidate_id or "", IDENTITY_NOT_EVALUATED
                ),
                seed_production_join_status=join_status,
                production_snapshot_available=production_rows is not None,
                spreadsheet_snapshot_available=spreadsheet_rows is not None,
                duplicate_production_ids=duplicates,
            )
        )
    return items


def build_report(
    results: Sequence[ShrinePositionAuditResult],
    *,
    unresolved_inputs: Sequence[str] = (),
) -> dict[str, Any]:
    """deterministic な JSON report を組み立てる。"""
    reason_counts: dict[str, int] = {}
    for result in results:
        for code in result.reason_codes:
            reason_counts[code] = reason_counts.get(code, 0) + 1

    totals = {
        "total": len(results),
        "auto_pass": sum(1 for r in results if r.audit_status == AUTO_PASS),
        "review": sum(1 for r in results if r.audit_status == REVIEW),
        "hold": sum(1 for r in results if r.audit_status == HOLD),
    }

    def _counts(attribute: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in results:
            value = getattr(result, attribute)
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    return {
        "schema_version": SCHEMA_VERSION,
        "totals": totals,
        # Position の証明経路 / 意味的 gate / artifact 同期は互いに独立の軸。
        # 集計も分けて出す（P2-A02 §20）。
        "seed_production_identity_counts": _counts("seed_production_identity_status"),
        "position_proof_path_counts": _counts("position_proof_path"),
        "anchor_semantics_counts": _counts("anchor_semantics_status"),
        "artifact_sync_counts": _counts("artifact_sync_status"),
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "unresolved_input_dependencies": list(unresolved_inputs),
        "results": [result.to_dict() for result in results],
    }


def render_markdown(report: dict[str, Any]) -> str:
    totals = report["totals"]
    lines: list[str] = []
    lines.append("# Position Audit v2 — Shrine Position Ground Truth")
    lines.append("")
    lines.append(
        "本レポートは read-only な triage 結果である。座標・Seed・Candidate Master・"
    )
    lines.append(
        "Spreadsheet・Production をいっさい変更していない。`AUTO_PASS` / `REVIEW` / `HOLD` は"
    )
    lines.append(
        "audit status であり、Position Contract の `PASS` / `HOLD_POSITION_REVIEW` を置き換えない。"
    )
    lines.append("")
    lines.append("## 集計")
    lines.append("")
    lines.append("```text")
    lines.append(f"total     = {totals['total']}")
    lines.append(f"AUTO_PASS = {totals['auto_pass']}")
    lines.append(f"REVIEW    = {totals['review']}")
    lines.append(f"HOLD      = {totals['hold']}")
    lines.append("```")
    lines.append("")

    for key, heading in (
        ("seed_production_identity_counts", "seed_production_identity_status"),
        ("position_proof_path_counts", "position_proof_path"),
        ("anchor_semantics_counts", "anchor_semantics_status"),
        ("artifact_sync_counts", "artifact_sync_status"),
    ):
        counts = report.get(key) or {}
        if not counts:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        lines.append("```text")
        for value, count in counts.items():
            lines.append(f"{value} = {count}")
        lines.append("```")
        lines.append("")

    if report["reason_code_counts"]:
        lines.append("### reason_code_counts")
        lines.append("")
        lines.append("| reason_code | count |")
        lines.append("| --- | --- |")
        for code, count in report["reason_code_counts"].items():
            lines.append(f"| `{code}` | {count} |")
        lines.append("")

    for status, heading in (
        (AUTO_PASS, "AUTO_PASS"),
        (REVIEW, "REVIEW"),
        (HOLD, "HOLD"),
    ):
        rows = [r for r in report["results"] if r["audit_status"] == status]
        lines.append(f"## {heading}（{len(rows)}件）")
        lines.append("")
        if not rows:
            lines.append("なし。")
            lines.append("")
            continue
        lines.append(
            "| candidate_id | production_id | name_jp | join | proof_path | "
            "anchor_semantics | artifact_sync | reason_codes | delta_m |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in rows:
            codes = ", ".join(f"`{code}`" for code in row["reason_codes"]) or "-"
            delta = row["coordinate_delta_m"]
            lines.append(
                f"| {row['candidate_id'] or '-'} | {row['production_id'] or '-'} | "
                f"{row['name_jp']} | {row['join_status']} | "
                f"{row['position_proof_path']} | {row['anchor_semantics_status']} | "
                f"{row['artifact_sync_status']} | {codes} | "
                f"{'-' if delta is None else delta} |"
            )
        lines.append("")

    lines.append("## 未解決の入力依存")
    lines.append("")
    unresolved = report["unresolved_input_dependencies"]
    if unresolved:
        for entry in unresolved:
            lines.append(f"- {entry}")
    else:
        lines.append("なし。")
    lines.append("")
    return "\n".join(lines)


def dump_json(report: dict[str, Any]) -> str:
    """byte 安定な JSON 文字列を返す。"""
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Position Audit v2 — read-only shrine position ground-truth triage. "
            "座標・Seed・Candidate Master・Spreadsheet・Production を変更しない。"
        )
    )
    parser.add_argument(
        "--production-snapshot",
        type=Path,
        default=None,
        help=(
            "sql/shrine_position_audit_snapshot.sql の出力 file。"
            "省略時は Production 由来の判定を fail closed にする。"
        ),
    )
    parser.add_argument(
        "--spreadsheet-snapshot",
        type=Path,
        default=None,
        help="Spreadsheet export snapshot（.json / .csv）。Evidence Index であり Ground Truth ではない。",
    )
    parser.add_argument(
        "--primary-evidence-snapshot",
        type=Path,
        default=None,
        help=(
            "Primary Position Evidence snapshot（.json / .csv）。"
            "candidate_id または official_name + official_address で Shrine を指す。"
            "live retrieval は行わない（file 入力のみ）。"
        ),
    )
    parser.add_argument("--output-json", type=Path, default=None, help="JSON report 出力先")
    parser.add_argument("--output-md", type=Path, default=None, help="Markdown summary 出力先")
    parser.add_argument(
        "--candidate-ids",
        nargs="*",
        default=None,
        help="対象 candidate_id を明示する（例: wave0-007 wave0-008）",
    )
    parser.add_argument(
        "--batch", default=None, help="対象 build_batch を明示する（例: W0-DB02）"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    unresolved: list[str] = []

    seed_rows = load_base_seed()
    candidates = load_candidate_master()
    resolution_records = load_resolution_records()

    production_rows = None
    if args.production_snapshot is not None:
        production_rows = load_production_snapshot(args.production_snapshot)
    else:
        unresolved.append(
            "production snapshot 未指定。sql/shrine_position_audit_snapshot.sql を "
            "readonly_query.sh 経由で取得し --production-snapshot で渡すこと。"
        )

    spreadsheet_rows = None
    if args.spreadsheet_snapshot is not None:
        spreadsheet_rows = load_spreadsheet_snapshot(args.spreadsheet_snapshot)
    else:
        unresolved.append(
            "spreadsheet snapshot 未指定。Evidence Index を export し "
            "--spreadsheet-snapshot で渡すこと。"
        )

    evidence_by_candidate: dict[str, PrimaryPositionEvidence] = {}
    evidence_by_identity: dict[tuple[str, str], PrimaryPositionEvidence] = {}
    if args.primary_evidence_snapshot is not None:
        evidence_by_candidate, evidence_by_identity = load_primary_evidence_snapshot(
            args.primary_evidence_snapshot
        )
    else:
        unresolved.append(
            "primary evidence snapshot 未指定。Position Contract 適合の一次位置資料を "
            "--primary-evidence-snapshot で渡すこと。"
        )

    items = build_inputs(
        seed_rows=seed_rows,
        production_rows=production_rows,
        spreadsheet_rows=spreadsheet_rows,
        candidates=candidates,
        resolution_records=resolution_records,
        primary_evidence_by_candidate=evidence_by_candidate,
        primary_evidence_by_identity=evidence_by_identity,
        candidate_ids=args.candidate_ids,
        batch=args.batch,
    )
    results = [evaluate(item) for item in items]
    report = build_report(results, unresolved_inputs=unresolved)

    payload = dump_json(report)
    markdown = render_markdown(report)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown, encoding="utf-8")
    if not args.output_json and not args.output_md:
        sys.stdout.write(payload)

    totals = report["totals"]
    sys.stderr.write(
        "position-audit-v2 total={total} auto_pass={auto_pass} "
        "review={review} hold={hold}\n".format(**totals)
    )
    # 監査は Gate ではないため、HOLD/REVIEW があっても exit 0 を返す。
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
