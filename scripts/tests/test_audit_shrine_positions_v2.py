"""Position Audit v2 contract。

`scripts/audit_shrine_positions_v2.py` が
`docs/knowledge/shrine-position-contract.md` を authority として、
Shrine position の machine-verifiability を deterministic に triage することを固定する。

本ファイルはDB・Django・ネットワークをいっさい必要としない。
外部 source の取得は fixture で与え、live network には出ない。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "scripts" / "audit_shrine_positions_v2.py"
SNAPSHOT_SQL_PATH = (
    REPO_ROOT
    / "scripts"
    / "migration_safety"
    / "sql"
    / "shrine_position_audit_snapshot.sql"
)
IMPORTER_PATH = (
    REPO_ROOT
    / "backend"
    / "temples"
    / "management"
    / "commands"
    / "import_shrines_seed.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "audit_shrine_positions_v2", AUDIT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    # dataclasses は解決時に sys.modules を引くため、exec 前に登録する。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = _load_module()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SEED_ROW = {
    "name_jp": "契約テスト神社",
    "address": "東京都千代田区1-1",
    "latitude": 35.0,
    "longitude": 139.0,
}


def _production_row(**overrides):
    row = {
        "id": 500,
        "name_jp": SEED_ROW["name_jp"],
        "address": SEED_ROW["address"],
        "latitude": 35.0,
        "longitude": 139.0,
        "kind": "shrine",
        "place_ref_id": None,
    }
    row.update(overrides)
    return row


def _sheet(**overrides) -> "audit.SpreadsheetRow":
    values = {
        "row_id": "500",
        "official_name": SEED_ROW["name_jp"],
        "official_address": SEED_ROW["address"],
        "position_source_type": "shrine_official",
        "position_source_url": "https://example.invalid/shrine/access",
        "verified_at": "2026-09-16",
    }
    values.update(overrides)
    return audit.SpreadsheetRow(**values)


def _item(**overrides) -> "audit.ShrinePositionAuditInput":
    values = dict(
        identity=audit.Identity(
            candidate_id="wave0-999",
            production_id=500,
            name_jp=SEED_ROW["name_jp"],
            official_name=SEED_ROW["name_jp"],
            address=SEED_ROW["address"],
            official_address=SEED_ROW["address"],
        ),
        seed=audit.SeedPosition(latitude=35.0, longitude=139.0),
        production=audit.ProductionPosition(latitude=35.0, longitude=139.0),
        spreadsheet=_sheet(),
        spreadsheet_join_status=audit.SHEET_JOIN_EXACT,
        seed_production_join_status=audit.JOIN_MATCH_EXACT,
    )
    values.update(overrides)
    return audit.ShrinePositionAuditInput(**values)


def _evidence(**overrides) -> "audit.PrimaryPositionEvidence":
    values = dict(
        status="OK",
        source_type="shrine_official",
        source_url="https://example.invalid/shrine/access",
        latitude=35.0,
        longitude=139.0,
        entity_match="SAME",
        poi_candidate_count=1,
    )
    values.update(overrides)
    return audit.PrimaryPositionEvidence(**values)


# ---------------------------------------------------------------------------
# A-C. Seed ↔ Production identity join
# ---------------------------------------------------------------------------


def test_a_exact_seed_production_match():
    status, row, duplicates = audit.join_seed_to_production(
        SEED_ROW, [_production_row()]
    )
    assert status == audit.JOIN_MATCH_EXACT
    assert row["id"] == 500
    assert duplicates == ()


def test_b_missing_production_row():
    status, row, duplicates = audit.join_seed_to_production(SEED_ROW, [])
    assert status == audit.JOIN_MISSING_PRODUCTION
    assert row is None
    assert duplicates == ()

    result = audit.evaluate(
        _item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_MISSING_PRODUCTION in result.reason_codes


def test_c_duplicate_production_row():
    status, row, duplicates = audit.join_seed_to_production(
        SEED_ROW, [_production_row(id=500), _production_row(id=501)]
    )
    assert status == audit.JOIN_DUPLICATE_MATCH
    assert row is None
    assert duplicates == (500, 501)

    result = audit.evaluate(
        _item(seed_production_join_status=audit.JOIN_DUPLICATE_MATCH)
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_DUPLICATE_PRODUCTION_IDENTITY in result.reason_codes


def test_seed_production_join_does_not_normalize():
    """normalization / fuzzy / coordinate rescue を行わない。"""
    production = _production_row(address="東京都千代田区１-１")  # 全角
    status, _row, _dups = audit.join_seed_to_production(SEED_ROW, [production])
    assert status == audit.JOIN_MISSING_PRODUCTION


# ---------------------------------------------------------------------------
# D-G. Production ↔ Spreadsheet identity join
# ---------------------------------------------------------------------------


def test_d_spreadsheet_normalized_identity_match():
    rows = [
        _sheet(
            official_name="契約テスト神社 ",  # 余分な空白
            official_address="〒100-0001 東京都千代田区1－1",  # 郵便番号 + 全角ダッシュ
        )
    ]
    status, row, _candidates = audit.join_production_to_spreadsheet(
        _production_row(), SEED_ROW, rows
    )
    assert status == audit.SHEET_JOIN_EXACT
    assert row is not None


def test_e_spreadsheet_id_only_match_is_rejected():
    """id だけの一致では identity を成立させない。"""
    rows = [_sheet(row_id="500", official_name="別の神社", official_address="大阪府大阪市1-1")]
    status, row, _candidates = audit.join_production_to_spreadsheet(
        _production_row(), SEED_ROW, rows
    )
    assert status != audit.SHEET_JOIN_EXACT
    assert status != audit.SHEET_JOIN_CORROBORATED
    assert row is None


def test_f_coordinate_only_match_is_rejected():
    """座標だけの一致では identity を成立させない。"""
    rows = [
        _sheet(
            row_id="999",
            official_name="別の神社",
            official_address="大阪府大阪市1-1",
            reference_latitude=35.0,
            reference_longitude=139.0,
        )
    ]
    status, row, _candidates = audit.join_production_to_spreadsheet(
        _production_row(), SEED_ROW, rows
    )
    assert status != audit.SHEET_JOIN_EXACT
    assert status != audit.SHEET_JOIN_CORROBORATED
    assert row is None


def test_g_google_place_id_plus_identity_corroboration():
    """place_id 一致 + name/address 一致で CORROBORATED になる。"""
    rows = [
        _sheet(
            row_id="different-id",
            official_name="契約テスト神社",
            official_address="大阪府大阪市1-1",  # address は不一致
            google_place_id="ChIJ_test",
        )
    ]
    status, row, _candidates = audit.join_production_to_spreadsheet(
        _production_row(),
        SEED_ROW,
        rows,
        production_place_id="ChIJ_test",
    )
    assert status == audit.SHEET_JOIN_CORROBORATED
    assert row is not None

    # place_id が一致しても name/address がまったく corroborate しなければ成立しない。
    rows_no_identity = [
        _sheet(
            row_id="different-id",
            official_name="無関係神社",
            official_address="北海道札幌市9-9",
            google_place_id="ChIJ_test",
        )
    ]
    status2, row2, _c2 = audit.join_production_to_spreadsheet(
        _production_row(),
        SEED_ROW,
        rows_no_identity,
        production_place_id="ChIJ_test",
    )
    assert status2 != audit.SHEET_JOIN_CORROBORATED
    assert row2 is None


def test_fuzzy_similarity_only_produces_review_candidates():
    rows = [_sheet(row_id="777", official_name="契約テスト神社北", official_address="東京都千代田区1-2")]
    status, row, candidates = audit.join_production_to_spreadsheet(
        _production_row(), SEED_ROW, rows
    )
    assert status == audit.SHEET_JOIN_REVIEW_CANDIDATE
    assert row is None
    assert candidates == ("777",)


# ---------------------------------------------------------------------------
# H-L. Triage
# ---------------------------------------------------------------------------


def test_h_exact_position_auto_pass():
    result = audit.evaluate(_item(primary_position_evidence=_evidence()))
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_SEED_PRODUCTION_EXACT in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    assert result.coordinate_delta_m == 0.0


def test_i_external_coordinate_conflict_is_review():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(latitude=35.001, longitude=139.001))
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_PRIMARY_COORDINATE_DIFFERS in result.reason_codes
    # delta は報告値として出るが、判定閾値には使われない。
    assert result.coordinate_delta_m is not None
    assert result.coordinate_delta_m > 0


def test_j_missing_primary_source_is_hold():
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(position_source_url=None, official_source_url=None),
            primary_position_evidence=None,
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_MISSING in result.reason_codes


def test_k_wrong_or_non_shrine_entity_is_hold():
    wrong = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match="DIFFERENT"))
    )
    assert wrong.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_WRONG_ENTITY in wrong.reason_codes

    non_shrine = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match="NON_SHRINE"))
    )
    assert non_shrine.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY in non_shrine.reason_codes


def test_k2_untraceable_primary_coordinate_is_hold():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(latitude=None, longitude=None))
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_COORDINATE_UNTRACEABLE in result.reason_codes


def test_l_parser_or_fetch_failure_is_review():
    """timeout / fetch / parser 失敗は fail closed で REVIEW。"""
    fetch = audit.evaluate(
        _item(primary_position_evidence=_evidence(status="FETCH_FAILED"))
    )
    assert fetch.audit_status == audit.REVIEW
    assert audit.RC_SOURCE_FETCH_FAILED in fetch.reason_codes

    parse = audit.evaluate(
        _item(primary_position_evidence=_evidence(status="PARSE_FAILED"))
    )
    assert parse.audit_status == audit.REVIEW
    assert audit.RC_SOURCE_PARSE_FAILED in parse.reason_codes

    redirected = audit.evaluate(
        _item(primary_position_evidence=_evidence(status="REDIRECTED"))
    )
    assert redirected.audit_status == audit.REVIEW
    assert audit.RC_POSITION_SOURCE_REDIRECTED in redirected.reason_codes


def test_multiple_poi_candidates_is_review():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(poi_candidate_count=3))
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_MULTIPLE_POI_CANDIDATES in result.reason_codes


# ---------------------------------------------------------------------------
# M-N. Resolution Record 再利用
# ---------------------------------------------------------------------------


def test_m_existing_pass_resolution_record_is_reusable():
    """Seed == Production == adopted のときだけ再利用できる。"""
    result = audit.evaluate(
        _item(
            primary_position_evidence=None,
            existing_resolution=audit.ExistingResolution(
                record_path="docs/audit/shrine-position/example.md",
                position_status="PASS",
                adopted_latitude=35.0,
                adopted_longitude=139.0,
            ),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes


def test_m2_resolution_record_coordinate_mismatch_blocks_reuse():
    result = audit.evaluate(
        _item(
            primary_position_evidence=None,
            existing_resolution=audit.ExistingResolution(
                record_path="docs/audit/shrine-position/example.md",
                position_status="PASS",
                adopted_latitude=35.5,
                adopted_longitude=139.5,
            ),
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_m3_hold_position_review_record_is_hold():
    result = audit.evaluate(
        _item(
            primary_position_evidence=_evidence(),
            existing_resolution=audit.ExistingResolution(
                record_path="docs/audit/shrine-position/example.md",
                position_status="HOLD_POSITION_REVIEW",
            ),
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_POSITION_CONTRACT_HOLD_RECORD in result.reason_codes


def test_n_newer_conflict_overrides_resolution_reuse():
    """Record が PASS でも、新しい evidence が矛盾すれば自動再利用しない。"""
    result = audit.evaluate(
        _item(
            primary_position_evidence=_evidence(latitude=35.002, longitude=139.002),
            existing_resolution=audit.ExistingResolution(
                record_path="docs/audit/shrine-position/example.md",
                position_status="PASS",
                adopted_latitude=35.0,
                adopted_longitude=139.0,
            ),
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_PRIMARY_COORDINATE_DIFFERS in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


# ---------------------------------------------------------------------------
# O-P. Float Comparison Contract v1
# ---------------------------------------------------------------------------


def test_o_float_round_trip_within_tolerance_is_equal():
    # Production float8 text round-trip 由来の微小差分（札幌諏訪神社 実測）。
    assert audit.coordinates_equal(43.07603505258046, 43.0760350525805)
    assert audit.coordinates_equal(141.3540979693115, 141.354097969312)
    # None semantics
    assert audit.coordinates_equal(None, None)
    assert not audit.coordinates_equal(None, 35.0)
    assert not audit.coordinates_equal(35.0, None)


def test_p_beyond_tolerance_remains_different():
    assert not audit.coordinates_equal(35.0, 35.0 + 1e-10)

    result = audit.evaluate(
        _item(
            seed=audit.SeedPosition(latitude=35.0, longitude=139.0),
            production=audit.ProductionPosition(
                latitude=35.0 + 1e-10, longitude=139.0
            ),
            primary_position_evidence=_evidence(
                latitude=35.0 + 1e-10, longitude=139.0
            ),
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_SEED_PRODUCTION_COORDINATE_DIFFERS in result.reason_codes


def test_tolerance_matches_the_importer_float_comparison_contract():
    """Importer 側の Float Comparison Contract v1 と同値であることを固定する。

    Django import を避けるため source を読んで突き合わせる。片方だけ動くと
    Seed ↔ Production の同値判定が2箇所で drift する。
    """
    importer_source = IMPORTER_PATH.read_text(encoding="utf-8")
    assert "COORDINATE_ABS_TOLERANCE = 1e-12" in importer_source
    assert "rel_tol=0.0" in importer_source
    assert audit.COORDINATE_ABS_TOLERANCE == 1e-12
    assert audit.COORDINATE_REL_TOLERANCE == 0.0


# ---------------------------------------------------------------------------
# Q. 距離だけでは AUTO_PASS にしない
# ---------------------------------------------------------------------------


def test_q_coordinate_distance_alone_never_produces_auto_pass():
    """delta = 0 でも、primary source が無ければ AUTO_PASS にしない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(position_source_url=None, official_source_url=None),
            primary_position_evidence=None,
            corroboration=(
                audit.CorroborationSource(
                    source_type="osm",
                    source_url="https://example.invalid/osm",
                    latitude=35.0,
                    longitude=139.0,
                ),
            ),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_MISSING in result.reason_codes


def test_corroboration_alone_never_promotes_to_auto_pass():
    """corroboration だけでは primary source の不足を埋められない。"""
    result = audit.evaluate(
        _item(
            primary_position_evidence=None,
            corroboration=(
                audit.CorroborationSource(
                    source_type="wikidata",
                    source_url="https://example.invalid/wikidata",
                    latitude=35.0,
                    longitude=139.0,
                ),
            ),
        )
    )
    assert result.audit_status != audit.AUTO_PASS


# ---------------------------------------------------------------------------
# R. 決定性 / 出力安定性
# ---------------------------------------------------------------------------


def test_r_identical_inputs_produce_byte_stable_json():
    items = [_item(primary_position_evidence=_evidence()) for _ in range(3)]
    first = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    second = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")
    # 再パース可能であること
    assert json.loads(first)["totals"]["total"] == 3


def test_report_totals_and_reason_code_counts():
    results = [
        audit.evaluate(_item(primary_position_evidence=_evidence())),
        audit.evaluate(
            _item(primary_position_evidence=_evidence(latitude=35.5, longitude=139.5))
        ),
        audit.evaluate(
            _item(
                spreadsheet=_sheet(position_source_url=None, official_source_url=None),
                primary_position_evidence=None,
            )
        ),
    ]
    report = audit.build_report(results)
    assert report["totals"] == {
        "total": 3,
        "auto_pass": 1,
        "review": 1,
        "hold": 1,
    }
    assert report["reason_code_counts"][audit.RC_SEED_PRODUCTION_EXACT] == 3
    # reason_code_counts は key 順が安定していること
    assert list(report["reason_code_counts"]) == sorted(report["reason_code_counts"])


def test_markdown_summary_contains_required_sections():
    report = audit.build_report(
        [audit.evaluate(_item(primary_position_evidence=_evidence()))],
        unresolved_inputs=["spreadsheet snapshot 未指定"],
    )
    markdown = audit.render_markdown(report)
    assert "AUTO_PASS" in markdown
    assert "REVIEW" in markdown
    assert "HOLD" in markdown
    assert "未解決の入力依存" in markdown
    assert "spreadsheet snapshot 未指定" in markdown


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def test_address_normalization_is_comparison_only_and_conservative():
    assert audit.normalize_address("日本、〒100-0001 東京都千代田区1－1") == "東京都千代田区1-1"
    assert audit.normalize_address("東京都千代田区  1-1 ") == "東京都千代田区 1-1"
    # 丁目 / 番 / 番地 / 号 の意味的書き換えは行わない（fail closed）。
    assert audit.normalize_address("愛知県名古屋市北区安井4丁目14-14") != audit.normalize_address(
        "愛知県名古屋市北区安井4-14-14"
    )


def test_name_normalization_is_nfkc_and_whitespace_only():
    assert audit.normalize_name("  戸隠神社　中社 ") == "戸隠神社 中社"
    assert audit.normalize_name("ｱｲｳ") == "アイウ"


# ---------------------------------------------------------------------------
# Loaders / snapshot 契約
# ---------------------------------------------------------------------------


def test_production_snapshot_parses_psql_aligned_output(tmp_path):
    payload = [
        {
            "id": 500,
            "name_jp": "契約テスト神社",
            "address": "東京都千代田区1-1",
            "latitude": 35.0,
            "longitude": 139.0,
            "kind": "shrine",
            "place_ref_id": None,
        }
    ]
    path = tmp_path / "snapshot.txt"
    path.write_text(
        " production_position_snapshot_json \n---\n "
        + json.dumps(payload, ensure_ascii=False)
        + "\n(1 row)\n",
        encoding="utf-8",
    )
    rows = audit.load_production_snapshot(path)
    assert rows[0]["id"] == 500
    assert rows[0]["latitude"] == 35.0


def test_production_snapshot_missing_required_field_fails_closed(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps([{"id": 1, "name_jp": "x"}]), encoding="utf-8")
    with pytest.raises(audit.AuditError):
        audit.load_production_snapshot(path)


def test_spreadsheet_snapshot_supports_json_and_csv(tmp_path):
    json_path = tmp_path / "sheet.json"
    json_path.write_text(
        json.dumps(
            [{"id": "500", "official_name": "契約テスト神社", "reference_latitude": "35.0"}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rows = audit.load_spreadsheet_snapshot(json_path)
    assert rows[0].row_id == "500"
    assert rows[0].reference_latitude == 35.0

    csv_path = tmp_path / "sheet.csv"
    csv_path.write_text(
        "id,official_name,reference_latitude\n500,契約テスト神社,35.0\n", encoding="utf-8"
    )
    csv_rows = audit.load_spreadsheet_snapshot(csv_path)
    assert csv_rows[0].row_id == "500"
    assert csv_rows[0].reference_latitude == 35.0


def test_snapshot_sql_is_select_only_and_separate_from_reconciliation():
    sql = SNAPSHOT_SQL_PATH.read_text(encoding="utf-8")
    # `--` コメントは日本語の説明を含むため、判定は本文（非コメント行）だけで行う。
    statements = [
        line.strip()
        for line in sql.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    body = " ".join(statements).lower()
    assert statements[0].upper().startswith("SELECT")
    for forbidden in (
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create ",
        "grant",
    ):
        assert forbidden not in body, forbidden
    # SELECT 1文のみ（終端の `;` が1つだけ）。
    assert body.count(";") == 1
    assert body.rstrip().endswith(";")
    # Position Audit v2 が必要とする field を含む。
    for column in ("id", "name_jp", "address", "latitude", "longitude", "kind", "place_ref_id"):
        assert column in body, column
    # 既存 Gate の契約ファイルとは別物であること。
    assert SNAPSHOT_SQL_PATH.name == "shrine_position_audit_snapshot.sql"


# ---------------------------------------------------------------------------
# Zero-write guarantee
# ---------------------------------------------------------------------------


# DB / network へ到達しうる import。監査 core はこれらを持たない。
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "django",
        "psycopg",
        "psycopg2",
        "sqlite3",
        "sqlalchemy",
        "requests",
        "httpx",
        "urllib",
        "http",
        "socket",
    }
)

# 永続層への write を示す呼び出し。
FORBIDDEN_CALL_ATTRS = frozenset(
    {
        "save",
        "create",
        "bulk_create",
        "bulk_update",
        "get_or_create",
        "update_or_create",
        "execute",
        "executemany",
        "executescript",
        "commit",
        "cursor",
        "connect",
    }
)


def test_audit_module_has_no_write_path():
    """監査 script に DB / network / write 経路が存在しないことを AST で固定する。

    文字列一致ではなく構文木で見る。日本語コメントに `UPDATE` の語が出ても
    誤検知せず、実際の import / 呼び出しだけを対象にする。
    """
    import ast

    tree = ast.parse(AUDIT_PATH.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in FORBIDDEN_IMPORT_ROOTS, alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, node.module
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_ATTRS, node.func.attr


def test_audit_module_writes_only_the_requested_report_files():
    """file への書き込みは --output-json / --output-md だけであること。"""
    import ast

    tree = ast.parse(AUDIT_PATH.read_text(encoding="utf-8"))
    write_targets: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"write_text", "write_bytes", "open"}
        ):
            write_targets.append(ast.unparse(node.func.value))
    assert sorted(set(write_targets)) == ["args.output_json", "args.output_md"]


def test_cli_does_not_require_ambient_credentials():
    parser = audit.build_arg_parser()
    args = parser.parse_args([])
    assert args.production_snapshot is None
    assert args.spreadsheet_snapshot is None


def test_missing_snapshots_fail_closed_into_hold():
    """snapshot が無い場合に AUTO_PASS へ倒れないこと。"""
    item = _item(
        production=None,
        spreadsheet=None,
        spreadsheet_join_status=audit.SHEET_JOIN_NONE,
        seed_production_join_status=audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE,
        production_snapshot_available=False,
        spreadsheet_snapshot_available=False,
    )
    result = audit.evaluate(item)
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRODUCTION_SNAPSHOT_UNAVAILABLE in result.reason_codes
    assert audit.RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE in result.reason_codes


# ---------------------------------------------------------------------------
# Address conflict
# ---------------------------------------------------------------------------


def test_unexplained_address_conflict_is_review():
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(official_address="大阪府大阪市中央区9-9"),
            primary_position_evidence=_evidence(),
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_ADDRESS_CONFLICT_UNEXPLAINED in result.reason_codes


# ---------------------------------------------------------------------------
# Real repository inputs（W0-DB02 pilot と同じ経路）
# ---------------------------------------------------------------------------


def test_repository_resolution_records_are_loadable():
    records = audit.load_resolution_records()
    assert "wave0-010" in records
    record = records["wave0-010"]
    assert record.position_status == "PASS"
    assert record.adopted_latitude == 43.07603505258046
    assert record.adopted_longitude == 141.3540979693115


def test_w0_db02_pilot_selects_exactly_five_candidates():
    seed_rows = audit.load_base_seed()
    candidates = audit.load_candidate_master()
    items = audit.build_inputs(
        seed_rows=seed_rows,
        production_rows=None,
        spreadsheet_rows=None,
        candidates=candidates,
        resolution_records=audit.load_resolution_records(),
        batch="W0-DB02",
    )
    assert len(items) == 5
    names = sorted(item.identity.name_jp for item in items)
    assert names == sorted(
        ["射水神社", "別小江神社", "戸隠神社 中社", "札幌諏訪神社", "少彦名神社"]
    )
    # Production snapshot が無い状態では全件 fail closed になる。
    results = [audit.evaluate(item) for item in items]
    assert all(r.audit_status == audit.HOLD for r in results)
    assert all(r.reason_codes for r in results)


# ---------------------------------------------------------------------------
# Review fix 1: Primary evidence snapshot が CLI pipeline から到達可能であること
# ---------------------------------------------------------------------------

CANDIDATE_ROW = {
    "candidate_id": "wave0-999",
    "candidate_name": "契約テスト神社",
    "official_name": SEED_ROW["name_jp"],
    "official_address": SEED_ROW["address"],
    "build_batch": "W0-TEST",
    "candidate_status": "IMPORTED",
}


def _build(**overrides):
    """build_inputs() を最小の hermetic 入力で呼ぶ。"""
    values = dict(
        seed_rows=[SEED_ROW],
        production_rows=[_production_row()],
        spreadsheet_rows=[_sheet()],
        candidates=[CANDIDATE_ROW],
        resolution_records={},
    )
    values.update(overrides)
    return audit.build_inputs(**values)


def test_primary_evidence_snapshot_loads_json_and_csv(tmp_path):
    json_path = tmp_path / "evidence.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "candidate_id": "wave0-999",
                    "status": "OK",
                    "source_type": "shrine_official",
                    "source_url": "https://example.invalid/access",
                    "source_name": "契約テスト神社",
                    "source_address": "東京都千代田区1-1",
                    "latitude": 35.0,
                    "longitude": 139.0,
                    "entity_match": "SAME",
                    "poi_candidate_count": 1,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    by_candidate, by_identity = audit.load_primary_evidence_snapshot(json_path)
    assert by_candidate["wave0-999"].status == "OK"
    assert by_candidate["wave0-999"].entity_match == "SAME"
    assert by_candidate["wave0-999"].latitude == 35.0
    assert by_identity == {}

    csv_path = tmp_path / "evidence.csv"
    csv_path.write_text(
        "official_name,official_address,status,latitude,longitude,entity_match\n"
        "契約テスト神社,東京都千代田区1-1,OK,35.0,139.0,SAME\n",
        encoding="utf-8",
    )
    csv_by_candidate, csv_by_identity = audit.load_primary_evidence_snapshot(csv_path)
    assert csv_by_candidate == {}
    key = (SEED_ROW["name_jp"], SEED_ROW["address"])
    assert csv_by_identity[key].entity_match == "SAME"


def test_primary_evidence_snapshot_rejects_rows_without_identity(tmp_path):
    """identity を推測しない（fail closed）。"""
    path = tmp_path / "evidence.json"
    path.write_text(
        json.dumps([{"status": "OK", "latitude": 35.0, "longitude": 139.0}]),
        encoding="utf-8",
    )
    with pytest.raises(audit.AuditError):
        audit.load_primary_evidence_snapshot(path)


def test_primary_evidence_snapshot_rejects_unknown_status(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(
        json.dumps([{"candidate_id": "wave0-999", "status": "TOTALLY_FINE"}]),
        encoding="utf-8",
    )
    with pytest.raises(audit.AuditError):
        audit.load_primary_evidence_snapshot(path)


def test_build_inputs_populates_primary_evidence_by_candidate_id():
    items = _build(
        primary_evidence_by_candidate={"wave0-999": _evidence()},
    )
    assert len(items) == 1
    assert items[0].primary_position_evidence is not None
    assert items[0].primary_position_evidence.entity_match == "SAME"

    # evidence が pipeline を通って AUTO_PASS まで到達する。
    result = audit.evaluate(items[0])
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes


def test_build_inputs_populates_primary_evidence_by_verified_identity():
    key = (SEED_ROW["name_jp"], SEED_ROW["address"])
    items = _build(primary_evidence_by_identity={key: _evidence()})
    assert items[0].primary_position_evidence is not None
    assert audit.evaluate(items[0]).audit_status == audit.AUTO_PASS


def test_build_inputs_without_evidence_never_reaches_auto_pass():
    items = _build()
    assert items[0].primary_position_evidence is None
    assert audit.evaluate(items[0]).audit_status != audit.AUTO_PASS


def test_cli_exposes_primary_evidence_snapshot_flag():
    parser = audit.build_arg_parser()
    args = parser.parse_args(["--primary-evidence-snapshot", "/tmp/evidence.json"])
    assert args.primary_evidence_snapshot == Path("/tmp/evidence.json")
    # 既定では要求しない（ambient credential も file も必須にしない）。
    assert parser.parse_args([]).primary_evidence_snapshot is None


# ---------------------------------------------------------------------------
# Review fix 2: place_ref_id = PlaceRef.place_id（Google Place ID 文字列）
# ---------------------------------------------------------------------------


def test_production_snapshot_keeps_place_ref_id_as_string(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 500,
                    "name_jp": SEED_ROW["name_jp"],
                    "address": SEED_ROW["address"],
                    "latitude": 35.0,
                    "longitude": 139.0,
                    "kind": "shrine",
                    "place_ref_id": "ChIJ_prod_place",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rows = audit.load_production_snapshot(path)
    assert rows[0]["place_ref_id"] == "ChIJ_prod_place"
    assert isinstance(rows[0]["place_ref_id"], str)


def test_build_inputs_wires_place_id_corroboration_end_to_end():
    """join rule 2 が build_inputs() 経由で実際に到達可能であること。

    直接 join_production_to_spreadsheet() を呼ぶ unit test だけでは、
    production_place_id=None のまま配線が死んでいても気づけない。
    """
    production = _production_row(place_ref_id="ChIJ_prod_place")
    # address は不一致。place_id + name 一致だけで CORROBORATED になるべき。
    sheet = _sheet(
        row_id="unrelated-row-id",
        official_name=SEED_ROW["name_jp"],
        official_address="大阪府大阪市中央区9-9",
        google_place_id="ChIJ_prod_place",
    )
    items = _build(production_rows=[production], spreadsheet_rows=[sheet])

    assert items[0].spreadsheet_join_status == audit.SHEET_JOIN_CORROBORATED
    assert items[0].spreadsheet is not None
    assert items[0].production.place_ref_id == "ChIJ_prod_place"


def test_build_inputs_place_id_mismatch_does_not_corroborate():
    production = _production_row(place_ref_id="ChIJ_prod_place")
    sheet = _sheet(
        row_id="unrelated-row-id",
        official_name="まったく別の神社",
        official_address="北海道札幌市9-9",
        google_place_id="ChIJ_other_place",
    )
    items = _build(production_rows=[production], spreadsheet_rows=[sheet])
    assert items[0].spreadsheet_join_status not in (
        audit.SHEET_JOIN_EXACT,
        audit.SHEET_JOIN_CORROBORATED,
    )


# ---------------------------------------------------------------------------
# Review fix 3: entity_match が SAME でなければ AUTO_PASS にしない
# ---------------------------------------------------------------------------


def test_entity_match_same_is_eligible_for_auto_pass():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match="SAME"))
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes


def test_entity_match_none_never_auto_pass():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match=None))
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes
    assert result.audit_status == audit.HOLD
    assert audit.RC_IDENTITY_EVIDENCE_MISSING in result.reason_codes


def test_entity_match_empty_never_auto_pass():
    for empty in ("", "   "):
        result = audit.evaluate(
            _item(primary_position_evidence=_evidence(entity_match=empty))
        )
        assert result.audit_status != audit.AUTO_PASS, empty
        assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes, empty
        assert audit.RC_IDENTITY_EVIDENCE_MISSING in result.reason_codes, empty


def test_unknown_entity_match_value_is_not_treated_as_same():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match="PROBABLY_OK"))
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes
    assert audit.RC_PRIMARY_ENTITY_AMBIGUOUS in result.reason_codes


def test_entity_match_is_case_and_whitespace_insensitive():
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(entity_match=" same "))
    )
    assert result.audit_status == audit.AUTO_PASS
