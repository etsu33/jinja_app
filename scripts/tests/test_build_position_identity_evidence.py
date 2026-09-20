"""Real-data Identity Evidence Supply（Pilot 1）の regression。

supply layer が固定すべき不変条件:

```text
1. 下流規則（B02 / B03 / B04）を再実装しない
2. 欠損・未確定は fail closed する
3. 自動 activation は単独 signal からは起こらない
4. Position Audit へ渡すのは本物の B04 結果だけ
```

本 file は DB・Django・ネットワーク・Production 資格情報をいっさい
必要としない。
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "build_position_identity_evidence.py"
B03_PATH = REPO_ROOT / "scripts" / "shrine_identity_evidence.py"
B04_PATH = REPO_ROOT / "scripts" / "position_identity_integration.py"
B02_PATH = REPO_ROOT / "scripts" / "japanese_address_normalization.py"
AUDIT_PATH = REPO_ROOT / "scripts" / "audit_shrine_positions_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


supply = _load("build_position_identity_evidence", MODULE_PATH)
sie = supply.identity_evidence
b04 = supply.identity_integration
audit = supply.position_audit

SOURCE = MODULE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


# ---------------------------------------------------------------------------
# fixtures（すべて in-memory。file / DB / network を触らない）
# ---------------------------------------------------------------------------

OFFICIAL_NAME = "供給テスト神社"
OFFICIAL_ADDRESS = "東京都千代田区丸の内1丁目1番1号"


def _candidate(**overrides):
    row = {
        "candidate_id": "pilot-001",
        "identity_status": "CONFIRMED",
        "official_source_status": "CONFIRMED",
        "official_name": OFFICIAL_NAME,
        "official_address": OFFICIAL_ADDRESS,
        "official_source_type": "shrine_official",
        "official_source_url": "https://example.invalid/supply-pilot",
        "verified_at": "2026-09-15",
    }
    row.update(overrides)
    return row


def _seed_row(**overrides):
    row = {
        "name_jp": OFFICIAL_NAME,
        "address": OFFICIAL_ADDRESS,
        "latitude": 35.681236,
        "longitude": 139.767125,
    }
    row.update(overrides)
    return row


def _production_row(**overrides):
    row = {
        "id": 900,
        "name_jp": OFFICIAL_NAME,
        "address": OFFICIAL_ADDRESS,
        "latitude": 35.681236,
        "longitude": 139.767125,
        "kind": "shrine",
        "place_ref_id": "PLACE-900",
    }
    row.update(overrides)
    return row


def _sheet_row(**overrides):
    fields = {
        "row_id": "42",
        "name_jp": OFFICIAL_NAME,
        "address": OFFICIAL_ADDRESS,
        "official_name": OFFICIAL_NAME,
        "official_address": OFFICIAL_ADDRESS,
        "google_place_id": "PLACE-900",
        "reference_latitude": 35.681236,
        "reference_longitude": 139.767125,
    }
    fields.update(overrides)
    return audit.SpreadsheetRow(**fields)


_DEFAULT = object()


def _build(
    *,
    candidate=_DEFAULT,
    candidate_id="pilot-001",
    seed_rows=None,
    production_rows=None,
    spreadsheet_rows=None,
    resolution=None,
):
    return supply.build_candidate_identity_supply(
        candidate=_candidate() if candidate is _DEFAULT else candidate,
        candidate_id=candidate_id,
        seed_rows=[_seed_row()] if seed_rows is None else seed_rows,
        production_rows=production_rows,
        spreadsheet_rows=spreadsheet_rows,
        resolution=resolution,
    )


# ---------------------------------------------------------------------------
# SUP-GC01..GC08 — supply の決定的挙動
# ---------------------------------------------------------------------------


def test_gc01_exact_join_with_full_corroboration_activates():
    """exact join + 完全な corroboration -> EXACT / ACTIVATED。"""
    result = _build(
        production_rows=[_production_row()], spreadsheet_rows=[_sheet_row()]
    )
    assert result.join_status == audit.JOIN_MATCH_EXACT
    assert result.identity_status == b04.IDENTITY_EXACT
    assert result.identity_evidence_status == sie.SAME_SUPPORTED
    assert result.name_identity_status == sie.NAME_EXACT_MATCH
    assert result.address_identity_status == sie.ADDRESS_EXACT_MATCH
    assert result.official_source_entity_status == sie.OFFICIAL_SOURCE_SAME
    assert result.place_id_status == sie.PLACE_ID_MATCH
    assert result.existing_resolution_status == sie.RESOLUTION_UNAVAILABLE
    assert result.activation_status == supply.ACTIVATED
    assert result.integration.production_id == 900


def test_gc02_missing_candidate_master_row_fails_closed():
    result = _build(candidate=None, candidate_id="pilot-missing")
    assert result.activation_status == supply.INPUT_UNAVAILABLE
    assert result.integration is None
    assert supply.REASON_CANDIDATE_MASTER_ROW_MISSING in result.review_reasons


@pytest.mark.parametrize("field", supply.REQUIRED_CANDIDATE_FIELDS[1:])
def test_gc03_incomplete_candidate_metadata_fails_closed(field):
    """必須 identity metadata の欠損を推測で補完しない。"""
    result = _build(candidate=_candidate(**{field: None}))
    assert result.activation_status == supply.INPUT_UNAVAILABLE
    assert result.integration is None
    assert result.identity_evidence_status == sie.INSUFFICIENT


PROVENANCE_FIELDS = ("official_source_type", "official_source_url", "verified_at")


@pytest.mark.parametrize("field", PROVENANCE_FIELDS)
def test_gc03b_incomplete_provenance_fails_closed_even_with_all_inputs_present(
    field,
):
    """入力が全部そろっていても、provenance が欠ければ評価に入らない。

    GC03 は production snapshot 未指定のまま落ちるため、metadata gate が
    消えても INPUT_UNAVAILABLE のままになりうる。ここは snapshot も
    spreadsheet も供給し、gate 自体を撃つ。
    """
    result = _build(
        candidate=_candidate(**{field: None}),
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet_row()],
    )
    assert result.activation_status == supply.INPUT_UNAVAILABLE
    assert result.integration is None
    assert result.join_status == supply.JOIN_NOT_EVALUATED
    assert result.identity_status == b04.IDENTITY_NOT_EVALUATED


def test_join_not_evaluated_is_report_only_and_not_a_position_audit_join_status():
    audit_join_statuses = {
        value
        for name, value in vars(audit).items()
        if name.startswith("JOIN_") and isinstance(value, str)
    }
    assert supply.JOIN_NOT_EVALUATED not in audit_join_statuses


def test_gc04_missing_seed_row_fails_closed():
    result = _build(seed_rows=[])
    assert result.join_status == audit.JOIN_MISSING_SEED
    assert result.activation_status == supply.INPUT_UNAVAILABLE
    assert result.integration is None
    assert supply.REASON_SEED_ROW_MISSING in result.review_reasons


def test_gc05_absent_production_snapshot_fails_closed():
    result = _build(production_rows=None)
    assert result.join_status == audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE
    assert result.activation_status == supply.INPUT_UNAVAILABLE
    assert result.integration is None
    assert supply.REASON_PRODUCTION_SNAPSHOT_UNAVAILABLE in result.review_reasons


def test_gc06_duplicate_production_rows_are_not_auto_adopted():
    rows = [_production_row(), _production_row(id=901, place_ref_id="PLACE-901")]
    result = _build(production_rows=rows, spreadsheet_rows=[_sheet_row()])
    assert result.join_status == audit.JOIN_DUPLICATE_MATCH
    assert result.integration.production_id is None
    assert result.integration.duplicate_production_ids == (900, 901)
    assert result.activation_status != supply.ACTIVATED


def test_gc07_spreadsheet_row_id_is_never_treated_as_production_id():
    """Spreadsheet の row id を Production id と同一視しない。"""
    sheet = _sheet_row(row_id="900", google_place_id=None)
    result = _build(
        production_rows=[_production_row(id=777, place_ref_id=None)],
        spreadsheet_rows=[sheet],
    )
    assert result.place_id_status == sie.PLACE_ID_UNAVAILABLE
    assert result.integration.production_id == 777
    assert supply.REASON_PLACE_ID_UNAVAILABLE in result.review_reasons


def test_gc08_absent_spreadsheet_snapshot_is_recorded_not_inferred():
    result = _build(production_rows=[_production_row()], spreadsheet_rows=None)
    assert supply.REASON_SPREADSHEET_SNAPSHOT_UNAVAILABLE in result.review_reasons
    assert result.place_id_status == sie.PLACE_ID_UNAVAILABLE


# ---------------------------------------------------------------------------
# name evidence（fuzzy を使わない / alias を発明しない）
# ---------------------------------------------------------------------------

NEVER_EMITTED_NAME_STATUSES = (
    sie.NAME_NORMALIZED_MATCH,
    sie.NAME_ALIAS_CONFIRMED,
    sie.NAME_DIFFERENT,
)

NAME_MATRIX = (
    (OFFICIAL_NAME, OFFICIAL_NAME, sie.NAME_EXACT_MATCH),
    (OFFICIAL_NAME, "供給テスト神社 ", sie.NAME_EXACT_MATCH),  # 前後空白のみ
    (OFFICIAL_NAME, "供給テスト神社（旧称）", sie.NAME_AMBIGUOUS),
    (OFFICIAL_NAME, "きゅうきゅうテスト神社", sie.NAME_AMBIGUOUS),
    (OFFICIAL_NAME, None, sie.NAME_UNSUPPORTED),
    (None, OFFICIAL_NAME, sie.NAME_UNSUPPORTED),
    (None, None, sie.NAME_UNSUPPORTED),
)


@pytest.mark.parametrize(("left", "right", "expected"), NAME_MATRIX)
def test_name_identity_is_raw_equality_only(left, right, expected):
    assert supply.derive_name_identity_status(left, right) == expected


@pytest.mark.parametrize(("left", "right", "_expected"), NAME_MATRIX)
def test_name_identity_never_emits_normalized_alias_or_conflict(
    left, right, _expected
):
    """canonical な名称正規化契約が無いので正規化一致も trusted conflict も出さない。"""
    assert (
        supply.derive_name_identity_status(left, right)
        not in NEVER_EMITTED_NAME_STATUSES
    )


def _referenced_evidence_constants() -> set[str]:
    """module の **実行コード** が参照する evidence 定数名を集める。

    docstring は仕様の説明のために禁止値の名前を書くことがあるため、
    素の文字列走査ではなく AST の属性参照だけを見る。
    """
    names: set[str] = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names


def test_no_alias_registry_is_introduced():
    assert "NAME_ALIAS_CONFIRMED" not in _referenced_evidence_constants()
    assert "alias_registry" not in SOURCE


# ---------------------------------------------------------------------------
# mutation 1 — confirmed Candidate Master status 単独では SAME_SUPPORTED にしない
# ---------------------------------------------------------------------------


def test_mutation_confirmed_candidate_status_alone_cannot_produce_same_supported():
    """`identity_status = CONFIRMED` 単独を同一性の証明に使わない。

    Candidate Master が CONFIRMED でも、突き合わせ対象の Production 行が
    無ければ evidence は成立しない。
    """
    reasons: list[str] = []
    status = supply.derive_official_source_entity_status(
        _candidate(), None, None, reasons
    )
    assert status == sie.OFFICIAL_SOURCE_UNAVAILABLE
    assert supply.REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED in reasons

    result = _build(production_rows=[], spreadsheet_rows=[_sheet_row()])
    assert result.join_status == audit.JOIN_MISSING_PRODUCTION
    assert result.identity_evidence_status != sie.SAME_SUPPORTED
    assert result.identity_status != b04.IDENTITY_SAME_SUPPORTED
    assert result.activation_status != supply.ACTIVATED


def test_mutation_confirmed_status_with_different_production_name_is_not_same():
    reasons: list[str] = []
    status = supply.derive_official_source_entity_status(
        _candidate(), "別の神社", OFFICIAL_ADDRESS, reasons
    )
    assert status == sie.OFFICIAL_SOURCE_UNAVAILABLE
    assert supply.REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED in reasons


# ---------------------------------------------------------------------------
# mutation 2 — official_source_url 単独では OFFICIAL_SOURCE_SAME にしない
# ---------------------------------------------------------------------------

UNCONFIRMED_STATUS_CASES = (
    {"identity_status": "PENDING"},
    {"identity_status": None},
    {"official_source_status": "PENDING"},
    {"official_source_status": None},
)


@pytest.mark.parametrize("overrides", UNCONFIRMED_STATUS_CASES)
def test_mutation_official_source_url_alone_cannot_produce_official_source_same(
    overrides,
):
    """URL の存在は同一 entity の証明ではない。"""
    candidate = _candidate(**overrides)
    assert candidate["official_source_url"]
    reasons: list[str] = []
    status = supply.derive_official_source_entity_status(
        candidate, OFFICIAL_NAME, OFFICIAL_ADDRESS, reasons
    )
    assert status == sie.OFFICIAL_SOURCE_UNAVAILABLE


def test_mutation_official_source_requires_complete_provenance():
    for field in ("official_source_type", "verified_at"):
        reasons: list[str] = []
        status = supply.derive_official_source_entity_status(
            _candidate(**{field: None}), OFFICIAL_NAME, OFFICIAL_ADDRESS, reasons
        )
        assert status == sie.OFFICIAL_SOURCE_UNAVAILABLE, field
        assert supply.REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE in reasons


def test_official_source_address_corroboration_is_decided_by_b02_not_raw_equality():
    """住所 corroboration の判定は B02 が持つ（raw 等値ではない）。

    raw では異なるが B02 上は同一住所、というケースで
    `OFFICIAL_SOURCE_SAME` が出ることを固定する。raw 比較に退行すると
    この test が落ちる。
    """
    variant = "日本、東京都千代田区丸の内１丁目１番１号"
    assert variant != OFFICIAL_ADDRESS
    comparison = supply.compare_addresses(OFFICIAL_ADDRESS, variant)
    assert comparison.address_identity_status == sie.ADDRESS_NORMALIZED_MATCH

    reasons: list[str] = []
    status = supply.derive_official_source_entity_status(
        _candidate(), OFFICIAL_NAME, variant, reasons
    )
    assert status == sie.OFFICIAL_SOURCE_SAME
    assert reasons == []


def test_official_source_different_is_never_emitted():
    """trusted conflict（別 entity 断定）は Pilot 1 では出さない。"""
    assert "OFFICIAL_SOURCE_DIFFERENT" not in _referenced_evidence_constants()


# ---------------------------------------------------------------------------
# mutation 3 — 座標近接から PLACE_ID_MATCH を作らない
# ---------------------------------------------------------------------------


def test_mutation_coordinate_proximity_cannot_produce_place_id_match():
    """座標が完全一致していても provider 識別子が無ければ UNAVAILABLE。"""
    production = _production_row(place_ref_id=None)
    sheet = _sheet_row(
        google_place_id=None,
        reference_latitude=production["latitude"],
        reference_longitude=production["longitude"],
    )
    result = _build(production_rows=[production], spreadsheet_rows=[sheet])
    assert result.place_id_status == sie.PLACE_ID_UNAVAILABLE
    assert supply.REASON_PLACE_ID_UNAVAILABLE in result.review_reasons


def test_place_id_derivation_only_reads_provider_identifiers():
    parameters = list(
        inspect.signature(supply.derive_place_id_status).parameters
    )
    assert parameters == [
        "production_place_ref_id",
        "spreadsheet_google_place_id",
    ]
    assert (
        supply.derive_place_id_status("PLACE-1", "PLACE-2") == sie.PLACE_ID_DIFFERENT
    )
    assert supply.derive_place_id_status("PLACE-1", None) == sie.PLACE_ID_UNAVAILABLE


def test_place_id_is_not_derived_from_urls():
    assert (
        supply.derive_place_id_status(
            "https://maps.example.invalid/x", "https://maps.example.invalid/x"
        )
        == sie.PLACE_ID_MATCH
    )
    # 上は「同じ文字列なら一致」という素朴な比較でしかない。URL を
    # provider 識別子として **読みに行く** 経路が無いことを固定する。
    assert "position_source_url" not in SOURCE
    assert "provider_poi_url" not in SOURCE


# ---------------------------------------------------------------------------
# mutation 4 — raw status 文字列は B04 信頼境界を迂回できない
# ---------------------------------------------------------------------------


def test_mutation_supply_emits_real_b04_results_only():
    supplies = supply.build_identity_supply(
        candidate_ids=["pilot-001"],
        candidates=[_candidate()],
        seed_rows=[_seed_row()],
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet_row()],
    )
    mapping = supply.identity_integrations_by_candidate(supplies)
    assert set(mapping) == {"pilot-001"}
    for value in mapping.values():
        assert isinstance(value, b04.PositionIdentityIntegrationResult)
        assert type(value) is audit.PositionIdentityIntegrationResult


def test_mutation_raw_status_string_cannot_bypass_the_trust_boundary():
    """supply が文字列を渡しても Position Audit は identity を採用しない。"""
    assert (
        audit._integration_identity_status(
            "SAME_SUPPORTED", audit.JOIN_MISSING_PRODUCTION
        )
        == audit.IDENTITY_NOT_EVALUATED
    )


def test_mutation_look_alike_object_cannot_bypass_the_trust_boundary():
    class LookAlike:
        join_status = audit.JOIN_MISSING_PRODUCTION
        identity_status = "SAME_SUPPORTED"
        production_id = 900
        duplicate_production_ids = ()
        identity_review_reasons = ()

    assert (
        audit._integration_identity_status(
            LookAlike(), audit.JOIN_MISSING_PRODUCTION
        )
        == audit.IDENTITY_NOT_EVALUATED
    )


def test_supply_never_constructs_assessments_or_integrations_by_hand():
    assert "IdentityEvidenceAssessment(" not in SOURCE
    assert "PositionIdentityIntegrationResult(" not in SOURCE
    assert "assess_identity_evidence(" in SOURCE
    assert "integrate_position_identity(" in SOURCE


def test_supply_mapping_feeds_position_audit_without_changing_canonical_decisions():
    supplies = supply.build_identity_supply(
        candidate_ids=["pilot-001"],
        candidates=[_candidate()],
        seed_rows=[_seed_row()],
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet_row()],
    )
    inputs = audit.build_inputs(
        seed_rows=[_seed_row()],
        production_rows=[_production_row()],
        spreadsheet_rows=[],
        candidates=[_candidate()],
        resolution_records={},
        identity_integrations_by_candidate=(
            supply.identity_integrations_by_candidate(supplies)
        ),
        candidate_ids=["pilot-001"],
    )
    assert len(inputs) == 1
    assert inputs[0].seed_production_join_status == audit.JOIN_MATCH_EXACT


# ---------------------------------------------------------------------------
# mutation 5 — Production 候補が無くても fuzzy discovery を起こさない
# ---------------------------------------------------------------------------


def test_mutation_missing_production_candidate_does_not_trigger_fuzzy_discovery():
    """正規化すれば一致しうる行が居ても、exact join でなければ採用しない。"""
    near_miss = _production_row(
        id=901, address="東京都千代田区丸の内１丁目１番１号", place_ref_id="PLACE-901"
    )
    result = _build(production_rows=[near_miss], spreadsheet_rows=[_sheet_row()])
    assert result.join_status == audit.JOIN_MISSING_PRODUCTION
    assert result.integration.production_id is None
    assert result.identity_evidence_status == sie.INSUFFICIENT
    assert result.identity_status == b04.IDENTITY_INSUFFICIENT
    assert result.activation_status == supply.NOT_ACTIVATED
    assert supply.REASON_PRODUCTION_CANDIDATE_UNRESOLVED in result.review_reasons


def test_supply_has_no_similarity_or_scan_machinery():
    forbidden_imports = {"difflib", "rapidfuzz", "Levenshtein", "re"}
    for node in ast.walk(TREE):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports, alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in forbidden_imports, node.module
    for forbidden in (
        "SequenceMatcher",
        "get_close_matches",
        "similarity",
        "join_production_to_spreadsheet",
        "lexical_normalize",
    ):
        assert forbidden not in SOURCE, forbidden


def test_production_rows_are_only_read_through_the_canonical_exact_join():
    assert SOURCE.count("join_seed_to_production") == 1


# ---------------------------------------------------------------------------
# existing resolution（Production linkage が証明できない）
# ---------------------------------------------------------------------------


def test_existing_resolution_is_always_unavailable_in_pilot_1():
    """PASS な Resolution Record は entity identity の証明にならない。"""
    reasons: list[str] = []
    assert (
        supply.derive_existing_resolution_status(None, reasons)
        == sie.RESOLUTION_UNAVAILABLE
    )
    assert reasons == []

    record = audit.ExistingResolution(
        record_path="docs/audit/shrine-position/example.md",
        position_status="PASS",
        adopted_latitude=43.0,
        adopted_longitude=141.0,
    )
    reasons = []
    assert (
        supply.derive_existing_resolution_status(record, reasons)
        == sie.RESOLUTION_UNAVAILABLE
    )
    assert reasons == [supply.REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN]


def test_resolution_same_is_never_emitted():
    referenced = _referenced_evidence_constants()
    assert "RESOLUTION_SAME" not in referenced
    assert "RESOLUTION_DIFFERENT" not in referenced


def test_resolution_record_does_not_activate_a_candidate():
    record = audit.ExistingResolution(record_path="x.md", position_status="PASS")
    result = _build(production_rows=[], resolution=record)
    assert result.activation_status != supply.ACTIVATED
    assert supply.REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN in result.review_reasons


# ---------------------------------------------------------------------------
# 住所は必ず B02 を通す（raw のまま渡す）
# ---------------------------------------------------------------------------


def test_address_comparison_goes_through_the_canonical_b02_api():
    b02 = _load("b02_for_supply_assertion", B02_PATH)
    assert supply.compare_addresses.__name__ == "compare_addresses"
    assert supply.compare_addresses is sie.compare_addresses
    assert (
        supply.compare_addresses.__code__.co_code
        == b02.compare_addresses.__code__.co_code
    )


def test_legacy_position_audit_normalize_address_is_never_called():
    assert "position_audit.normalize_address" not in SOURCE
    for node in ast.walk(TREE):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            assert name != "normalize_address"


def test_addresses_stay_raw_until_they_enter_b02():
    """B02 へ渡す前に住所を加工しない（`_text` の trim のみ）。"""
    source_lines = [
        line.strip()
        for line in SOURCE.splitlines()
        if "compare_addresses(" in line and "def " not in line
    ]
    assert source_lines, "compare_addresses call sites not found"
    for line in source_lines:
        assert "normalize" not in line, line
        assert ".replace(" not in line, line


def test_component_difference_does_not_activate():
    production = _production_row(address=OFFICIAL_ADDRESS + " 社務所")
    seed = _seed_row(address=production["address"])
    # Seed は Candidate Master の identity で引くため、住所差があると
    # Seed 行が引けない。住所差そのものの扱いは B02/B03 が決める。
    comparison = supply.compare_addresses(OFFICIAL_ADDRESS, production["address"])
    assert comparison.address_identity_status != sie.ADDRESS_EXACT_MATCH
    reasons: list[str] = []
    status = supply.derive_official_source_entity_status(
        _candidate(), OFFICIAL_NAME, production["address"], reasons
    )
    assert status != sie.OFFICIAL_SOURCE_SAME
    assert seed["address"] == production["address"]


# ---------------------------------------------------------------------------
# 決定性 / byte 安定性
# ---------------------------------------------------------------------------


def test_results_are_ordered_by_candidate_id():
    supplies = supply.build_identity_supply(
        candidate_ids=["pilot-003", "pilot-001", "pilot-002"],
        candidates=[
            _candidate(candidate_id="pilot-001"),
            _candidate(candidate_id="pilot-002"),
            _candidate(candidate_id="pilot-003"),
        ],
        seed_rows=[_seed_row()],
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet_row()],
    )
    assert [item.candidate_id for item in supplies] == [
        "pilot-001",
        "pilot-002",
        "pilot-003",
    ]


def test_report_serialization_is_byte_stable():
    def _run():
        supplies = supply.build_identity_supply(
            candidate_ids=list(reversed(["pilot-001", "pilot-002"])),
            candidates=[
                _candidate(candidate_id="pilot-002"),
                _candidate(candidate_id="pilot-001"),
            ],
            seed_rows=[_seed_row()],
            production_rows=[_production_row()],
            spreadsheet_rows=[_sheet_row()],
        )
        return supply.dump_json(supply.build_report(supplies))

    assert _run() == _run()


def test_markdown_render_is_byte_stable():
    supplies = supply.build_identity_supply(
        candidate_ids=["pilot-001"],
        candidates=[_candidate()],
        seed_rows=[_seed_row()],
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet_row()],
    )
    report = supply.build_report(supplies)
    assert supply.render_markdown(report) == supply.render_markdown(report)
    assert report["schema_version"] == supply.SCHEMA_VERSION


def test_review_reasons_use_the_canonical_order():
    result = _build(production_rows=[], spreadsheet_rows=None)
    ranks = [supply.REVIEW_REASON_ORDER.index(r) for r in result.review_reasons]
    assert ranks == sorted(ranks)
    assert set(result.review_reasons) <= supply.REVIEW_REASONS


def test_activation_statuses_are_report_only_and_disjoint_from_audit_status():
    assert supply.ACTIVATION_STATUSES.isdisjoint(
        {audit.AUTO_PASS, audit.REVIEW, audit.HOLD}
    )


# ---------------------------------------------------------------------------
# 副作用の禁止（evaluation core）
# ---------------------------------------------------------------------------

FORBIDDEN_RUNTIME_IMPORTS = {
    "django",
    "psycopg2",
    "psycopg",
    "sqlite3",
    "socket",
    "http",
    "urllib",
    "requests",
    "httpx",
    "subprocess",
    "os",
}


def test_evaluation_core_requires_no_db_network_or_credentials():
    for node in ast.walk(TREE):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in FORBIDDEN_RUNTIME_IMPORTS, alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_RUNTIME_IMPORTS, node.module
    for forbidden in ("environ", "getenv", "DATABASE_URL", "connect("):
        assert forbidden not in SOURCE, forbidden


def test_only_the_cli_entrypoint_writes_files():
    writers = []
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call):
                    name = getattr(inner.func, "attr", None)
                    if name in {"write_text", "write_bytes", "mkdir", "unlink"}:
                        writers.append(node.name)
    assert set(writers) == {"main"}


def test_supply_performs_no_production_writes():
    """ORM / SQL 経由の書き込み経路が存在しないこと（AST で確認）。"""
    forbidden_calls = {"save", "bulk_update", "bulk_create", "create", "delete"}
    for node in ast.walk(TREE):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_calls, ast.dump(node.func)
        if isinstance(node, ast.Attribute):
            assert node.attr != "objects", "ORM manager access"
    for node in ast.walk(TREE):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            upper = node.value.upper()
            for sql in ("INSERT INTO", "UPDATE ", "DELETE FROM"):
                assert sql not in upper, node.value


# ---------------------------------------------------------------------------
# 実データ（repository 裏付け）— read-only
# ---------------------------------------------------------------------------


def test_w0_db02_candidates_exist_and_are_confirmed_in_candidate_master():
    rows = {
        row["candidate_id"]: row for row in audit.load_candidate_master()
    }
    for candidate_id in supply.W0_DB02_CANDIDATE_IDS:
        assert candidate_id in rows, candidate_id
        row = rows[candidate_id]
        assert row["identity_status"] == "CONFIRMED"
        assert row["official_source_status"] == "CONFIRMED"
        for field in supply.REQUIRED_CANDIDATE_FIELDS:
            assert row.get(field), (candidate_id, field)


def test_real_data_without_production_snapshot_fails_closed():
    """repository 単体では Production snapshot が無い（Pilot 1 の実測）。"""
    supplies = supply.build_identity_supply(
        candidate_ids=supply.W0_DB02_CANDIDATE_IDS,
        candidates=audit.load_candidate_master(),
        seed_rows=audit.load_base_seed(),
        production_rows=None,
        spreadsheet_rows=None,
        resolution_records=audit.load_resolution_records(),
    )
    assert len(supplies) == len(supply.W0_DB02_CANDIDATE_IDS)
    assert {item.activation_status for item in supplies} == {
        supply.INPUT_UNAVAILABLE
    }
    assert supply.identity_integrations_by_candidate(supplies) == {}


def test_real_data_candidate_identities_resolve_to_seed_rows():
    seed_index = {
        (row["name_jp"], row["address"]) for row in audit.load_base_seed()
    }
    rows = {row["candidate_id"]: row for row in audit.load_candidate_master()}
    for candidate_id in supply.W0_DB02_CANDIDATE_IDS:
        row = rows[candidate_id]
        assert (row["official_name"], row["official_address"]) in seed_index


REAL_PILOT_RECORD = (
    REPO_ROOT
    / "docs"
    / "audit"
    / "position-audit-v2"
    / "w0-db02-real-data-pilot-2026-09-18.json"
)


def _recorded_real_pilot_results():
    """2026-09-18 Real-Data Position Pilot の machine audit 転記記録。

    raw Production snapshot は repository へ commit されていない
    （`raw_input_snapshots_committed = false`）。転記された
    `production_id` / `name_jp` / `stored_address` は repository が
    裏付けている唯一の real Production identity である。
    """
    payload = json.loads(REAL_PILOT_RECORD.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in payload["results"]}


def test_recorded_real_pilot_covers_the_w0_db02_set_with_exact_joins():
    recorded = _recorded_real_pilot_results()
    assert set(recorded) == set(supply.W0_DB02_CANDIDATE_IDS)
    for candidate_id, row in sorted(recorded.items()):
        assert row["join_status"] == audit.JOIN_MATCH_EXACT, candidate_id
        assert row["spreadsheet_join_status"] == "JOIN_NONE", candidate_id
        assert isinstance(row["production_id"], int), candidate_id


def test_real_data_supply_reproduces_the_recorded_production_identity():
    """記録された real Production identity で経路全体を通す。

    DB には接続しない。転記記録から組み立てた in-memory Production 行を
    使い、supply layer が記録どおりの join / production_id を再現し、
    かつ **記録に無い evidence を捏造しない** ことを固定する。
    """
    recorded = _recorded_real_pilot_results()
    production_rows = [
        {
            "id": row["production_id"],
            "name_jp": row["name_jp"],
            "address": row["stored_address"],
            "latitude": row["stored_latitude"],
            "longitude": row["stored_longitude"],
            "kind": "shrine",
            # place_ref_id は転記対象外。無い evidence を作らない。
            "place_ref_id": None,
        }
        for row in recorded.values()
    ]

    supplies = supply.build_identity_supply(
        candidate_ids=supply.W0_DB02_CANDIDATE_IDS,
        candidates=audit.load_candidate_master(),
        seed_rows=audit.load_base_seed(),
        production_rows=production_rows,
        # 記録は 5/5 SPREADSHEET_ROW_MISSING である。
        spreadsheet_rows=[],
        resolution_records=audit.load_resolution_records(),
    )
    assert len(supplies) == len(supply.W0_DB02_CANDIDATE_IDS)

    for item in supplies:
        row = recorded[item.candidate_id]
        assert item.join_status == audit.JOIN_MATCH_EXACT, item.candidate_id
        assert item.integration.production_id == row["production_id"]
        assert item.identity_status == b04.IDENTITY_EXACT
        assert item.identity_evidence_status == sie.SAME_SUPPORTED
        assert item.name_identity_status == sie.NAME_EXACT_MATCH
        assert item.address_identity_status == sie.ADDRESS_EXACT_MATCH
        assert item.official_source_entity_status == sie.OFFICIAL_SOURCE_SAME
        # Spreadsheet 行も place_ref_id も無い。
        assert item.place_id_status == sie.PLACE_ID_UNAVAILABLE
        # Resolution Record は Production linkage を証明しない。
        assert item.existing_resolution_status == sie.RESOLUTION_UNAVAILABLE
        assert item.activation_status == supply.ACTIVATED

    mapping = supply.identity_integrations_by_candidate(supplies)
    assert set(mapping) == set(supply.W0_DB02_CANDIDATE_IDS)


def test_real_data_resolution_records_do_not_supply_identity():
    """wave0-007 / wave0-010 には Resolution Record が実在する。

    それでも `RESOLUTION_SAME` にはならない（Production linkage が
    canonical loader から取れない）。
    """
    records = audit.load_resolution_records()
    assert {"wave0-007", "wave0-010"} <= set(records)
    for candidate_id, record in sorted(records.items()):
        reasons: list[str] = []
        assert (
            supply.derive_existing_resolution_status(record, reasons)
            == sie.RESOLUTION_UNAVAILABLE
        ), candidate_id
        assert reasons == [supply.REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN]


def test_existing_resolution_loader_exposes_no_production_identifier():
    """Pilot 1 の構造的所見を固定する。

    `ExistingResolution` は Production 側識別子を公開していない。これが
    `RESOLUTION_UNAVAILABLE` になる理由であり、loader を拡張すれば
    変わりうる（Position Audit 契約の変更なので Pilot 1 の scope 外）。
    """
    fields = {field.name for field in dataclasses.fields(audit.ExistingResolution)}
    assert not fields & {
        "production_shrine_id",
        "production_id",
        "shrine_id",
        "place_ref_id",
    }


# ---------------------------------------------------------------------------
# canonical loader（型による信頼境界の前提）
# ---------------------------------------------------------------------------


def test_supply_reuses_the_canonical_sibling_modules():
    assert supply.identity_evidence.__file__ == str(B03_PATH)
    assert supply.identity_integration.__file__ == str(B04_PATH)
    assert supply.position_audit.__file__ == str(AUDIT_PATH)
    assert supply.position_audit.identity_integration is supply.identity_integration


def test_supply_does_not_load_b02_directly():
    """B02 の直接 consumer は B03 のままに保つ（推移的依存を上流に載せない）。"""
    assert "japanese_address_normalization" not in SOURCE


def test_cli_is_read_only_by_default():
    args = supply.build_arg_parser().parse_args([])
    assert args.production_snapshot is None
    assert args.spreadsheet_snapshot is None
    assert args.output_json is None
    assert args.output_md is None
    assert args.candidate_ids == list(supply.W0_DB02_CANDIDATE_IDS)
