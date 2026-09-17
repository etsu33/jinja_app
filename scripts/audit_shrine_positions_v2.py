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

SCHEMA_VERSION = "position-audit-v2/1.0"

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

# Seed ↔ Production join
JOIN_MATCH_EXACT = "MATCH_EXACT"
JOIN_MISSING_SEED = "MISSING_SEED"
JOIN_MISSING_PRODUCTION = "MISSING_PRODUCTION"
JOIN_DUPLICATE_MATCH = "DUPLICATE_MATCH"
JOIN_IDENTITY_REVIEW_REQUIRED = "IDENTITY_REVIEW_REQUIRED"
# Production snapshot 自体が無い場合。MATCH_EXACT を騙らせない。
JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE = "PRODUCTION_SNAPSHOT_UNAVAILABLE"

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
RC_RESOLUTION_RECORD_COORDINATE_MISMATCH = "RESOLUTION_RECORD_COORDINATE_MISMATCH"

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
    }
)

REVIEW_REASON_CODES = frozenset(
    {
        RC_PRIMARY_COORDINATE_DIFFERS,
        RC_SOURCE_PARSE_FAILED,
        RC_SOURCE_FETCH_FAILED,
        RC_PRIMARY_EVIDENCE_NOT_RETRIEVED,
        RC_ADDRESS_CONFLICT_UNEXPLAINED,
        RC_CORROBORATION_CONFLICT,
        RC_MULTIPLE_POI_CANDIDATES,
        RC_PRIMARY_ENTITY_AMBIGUOUS,
        RC_SPREADSHEET_ROW_MISSING,
        RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE,
        RC_SPREADSHEET_IDENTITY_REVIEW,
        RC_IDENTITY_NORMALIZATION_REQUIRED,
        RC_POSITION_SOURCE_REDIRECTED,
        RC_SEED_PRODUCTION_COORDINATE_DIFFERS,
        RC_RESOLUTION_RECORD_COORDINATE_MISMATCH,
    }
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
    place_ref_id: int | None = None


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


@dataclass(frozen=True)
class ShrinePositionAuditInput:
    identity: Identity
    seed: SeedPosition | None = None
    production: ProductionPosition | None = None
    spreadsheet: SpreadsheetRow | None = None
    spreadsheet_join_status: str = SHEET_JOIN_NONE
    spreadsheet_review_candidates: tuple[str, ...] = ()
    primary_position_evidence: PrimaryPositionEvidence | None = None
    corroboration: tuple[CorroborationSource, ...] = ()
    existing_resolution: ExistingResolution | None = None
    seed_production_join_status: str = JOIN_MATCH_EXACT
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


def evaluate(item: ShrinePositionAuditInput) -> ShrinePositionAuditResult:
    """1件分の triage。純関数。同じ入力からは常に同じ出力を返す。"""
    codes: set[str] = set()

    ident = item.identity
    seed = item.seed
    prod = item.production
    sheet = item.spreadsheet
    evidence = item.primary_position_evidence
    resolution = item.existing_resolution

    # --- 1. Seed ↔ Production identity ---------------------------------
    if not item.production_snapshot_available:
        codes.add(RC_PRODUCTION_SNAPSHOT_UNAVAILABLE)
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

    identity_is_exact = RC_SEED_PRODUCTION_EXACT in codes

    # --- 2. Seed ↔ Production coordinate equivalence --------------------
    if identity_is_exact and seed is not None and prod is not None:
        if not (
            coordinates_equal(seed.latitude, prod.latitude)
            and coordinates_equal(seed.longitude, prod.longitude)
        ):
            codes.add(RC_SEED_PRODUCTION_COORDINATE_DIFFERS)

    # --- 3. Spreadsheet identity ----------------------------------------
    if not item.spreadsheet_snapshot_available:
        codes.add(RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE)
    elif item.spreadsheet_join_status == SHEET_JOIN_NONE or sheet is None:
        codes.add(RC_SPREADSHEET_ROW_MISSING)
    elif item.spreadsheet_join_status == SHEET_JOIN_REVIEW_CANDIDATE:
        codes.add(RC_SPREADSHEET_IDENTITY_REVIEW)

    # --- 4. Address conflict --------------------------------------------
    if sheet is not None and item.spreadsheet_join_status in (
        SHEET_JOIN_EXACT,
        SHEET_JOIN_CORROBORATED,
    ):
        stored = normalize_address(ident.address)
        official = normalize_address(sheet.official_address or sheet.address)
        if stored and official and stored != official:
            codes.add(RC_ADDRESS_CONFLICT_UNEXPLAINED)

    # --- 5. Primary position evidence ------------------------------------
    primary_url = None
    primary_type = None
    if sheet is not None:
        primary_url = sheet.position_source_url or sheet.official_source_url
        primary_type = sheet.position_source_type or sheet.official_source_type
    if evidence is not None:
        primary_url = evidence.source_url or primary_url
        primary_type = evidence.source_type or primary_type

    resolution_is_pass = (
        resolution is not None and resolution.position_status == "PASS"
    )
    if resolution is not None and resolution.position_status == "HOLD_POSITION_REVIEW":
        codes.add(RC_POSITION_CONTRACT_HOLD_RECORD)

    # 既存 PASS Resolution Record の再利用条件:
    #   current Seed == current Production == recorded adopted coordinate
    resolution_reusable = False
    if resolution_is_pass and identity_is_exact and seed is not None and prod is not None:
        matches_seed = coordinates_equal(
            seed.latitude, resolution.adopted_latitude
        ) and coordinates_equal(seed.longitude, resolution.adopted_longitude)
        matches_prod = coordinates_equal(
            prod.latitude, resolution.adopted_latitude
        ) and coordinates_equal(prod.longitude, resolution.adopted_longitude)
        if matches_seed and matches_prod:
            resolution_reusable = True
        else:
            codes.add(RC_RESOLUTION_RECORD_COORDINATE_MISMATCH)

    evidence_status = evidence.status if evidence is not None else "NOT_RETRIEVED"

    if evidence is not None and evidence_status == "OK":
        # entity 同定
        if evidence.entity_match == "DIFFERENT":
            codes.add(RC_PRIMARY_SOURCE_WRONG_ENTITY)
        elif evidence.entity_match == "NON_SHRINE":
            codes.add(RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY)
        elif evidence.entity_match == "AMBIGUOUS":
            codes.add(RC_PRIMARY_ENTITY_AMBIGUOUS)
        if (evidence.poi_candidate_count or 0) > 1:
            codes.add(RC_MULTIPLE_POI_CANDIDATES)
        if evidence.latitude is None or evidence.longitude is None:
            codes.add(RC_PRIMARY_COORDINATE_UNTRACEABLE)
        else:
            codes.add(RC_PRIMARY_SOURCE_VERIFIED)
            # primary 座標 vs Production 座標。差があれば REVIEW（自動採用しない）。
            if prod is not None and not (
                coordinates_equal(evidence.latitude, prod.latitude)
                and coordinates_equal(evidence.longitude, prod.longitude)
            ):
                codes.add(RC_PRIMARY_COORDINATE_DIFFERS)
    elif evidence_status == "FETCH_FAILED":
        codes.add(RC_SOURCE_FETCH_FAILED)
    elif evidence_status == "PARSE_FAILED":
        codes.add(RC_SOURCE_PARSE_FAILED)
    elif evidence_status == "REDIRECTED":
        codes.add(RC_POSITION_SOURCE_REDIRECTED)
    else:
        # evidence を取得していない。Resolution Record で代替できるか。
        if resolution_reusable:
            codes.add(RC_RESOLUTION_RECORD_REUSED)
        elif not primary_url:
            codes.add(RC_PRIMARY_SOURCE_MISSING)
        else:
            codes.add(RC_PRIMARY_EVIDENCE_NOT_RETRIEVED)

    # evidence を取得していても、Record と矛盾しないことを併せて記録する。
    if resolution_reusable and RC_RESOLUTION_RECORD_REUSED not in codes:
        if RC_PRIMARY_COORDINATE_DIFFERS not in codes:
            codes.add(RC_RESOLUTION_RECORD_REUSED)

    # --- 6. Corroboration -------------------------------------------------
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
    # corroboration は単独で AUTO_PASS へ昇格させない。
    #
    # primary が無い状態は上の分岐で既に PRIMARY_SOURCE_MISSING /
    # PRIMARY_EVIDENCE_NOT_RETRIEVED / FETCH・PARSE 失敗などとして code 化されて
    # いる。ここで corroboration の存在を理由に code を足すと、「取得済みだが
    # entity が違う」ケースに NOT_RETRIEVED を付けるなど実態とずれるため、
    # 追加の code は付けない。この行は「corroboration では昇格しない」ことを
    # 明示するためのガードである。
    # primary 不在時には上の分岐が必ず HOLD / REVIEW の code を付けているため、
    # corroboration があっても AUTO_PASS には到達しない。ここでは何も足さない。

    # --- 7. 出力 ----------------------------------------------------------
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
        verified_at=sheet.verified_at if sheet else None,
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
                "place_ref_id": row.get("place_ref_id"),
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

    items: list[ShrinePositionAuditInput] = []
    for row in selected:
        candidate_id = row.get("candidate_id")
        official_name = row.get("official_name")
        official_address = row.get("official_address")

        if not official_name or not official_address:
            # canonical identity が未確定。推測で candidate_name 等へ代替しない。
            items.append(
                ShrinePositionAuditInput(
                    identity=Identity(
                        candidate_id=candidate_id,
                        name_jp=str(row.get("candidate_name") or ""),
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
                production_place_id=None,
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
                existing_resolution=resolution_records.get(candidate_id or ""),
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

    return {
        "schema_version": SCHEMA_VERSION,
        "totals": totals,
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
        lines.append("| candidate_id | production_id | name_jp | join | reason_codes | delta_m |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in rows:
            codes = ", ".join(f"`{code}`" for code in row["reason_codes"]) or "-"
            delta = row["coordinate_delta_m"]
            lines.append(
                f"| {row['candidate_id'] or '-'} | {row['production_id'] or '-'} | "
                f"{row['name_jp']} | {row['join_status']} | {codes} | "
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

    items = build_inputs(
        seed_rows=seed_rows,
        production_rows=production_rows,
        spreadsheet_rows=spreadsheet_rows,
        candidates=candidates,
        resolution_records=resolution_records,
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
