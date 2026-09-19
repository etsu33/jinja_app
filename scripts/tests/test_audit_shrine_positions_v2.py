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
        # Anchor Semantics は明示的な入力であり、既定では未評価 = REVIEW。
        # 既存 contract test の関心は Position proof 側なので、fixture 側で
        # 「意味論は確認済み」を明示して gate を開けておく（P2-A02 §7）。
        # gate 自体は Anchor Semantics 専用の test が固定する。
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
    )
    values.update(overrides)
    return audit.ShrinePositionAuditInput(**values)


def _resolution(**overrides) -> "audit.ExistingResolution":
    """provenance が完備した PASS Resolution Record。

    Resolution Record 再利用も PrimaryPositionEvidence 経由と同じ
    traceability（source_type / source_url / verified_at）を要求する。
    """
    values = dict(
        record_path="docs/audit/shrine-position/example.md",
        position_status="PASS",
        adopted_latitude=35.0,
        adopted_longitude=139.0,
        position_source_type="shrine_authority_access_map",
        position_source_url="https://example.invalid/authority/access",
        verified_at="2026-09-16",
    )
    values.update(overrides)
    return audit.ExistingResolution(**values)


def _evidence(**overrides) -> "audit.PrimaryPositionEvidence":
    values = dict(
        status="OK",
        source_type="shrine_official",
        source_url="https://example.invalid/shrine/access",
        latitude=35.0,
        longitude=139.0,
        entity_match="SAME",
        poi_candidate_count=1,
        # Anchor Semantics は evidence snapshot 行が明示的に運ぶ入力。
        # build_inputs() 経由の path でも gate を通せるようにしておく。
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
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


def test_j_no_evidence_and_no_fallback_has_no_proof_path():
    """evidence 未取得 + 再利用可能な Resolution 無し => proof path 不在。

    P2-A02 §12 / GC-24。取得できていないこと自体は observation であり、
    status を決めるのは「有効な proof path が存在しない」という事実である。
    `PRIMARY_SOURCE_MISSING`（HOLD）は **取得できた evidence の source
    identity が不明** な場合の code であって、未取得の場合の code ではない。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(position_source_url=None, official_source_url=None),
            primary_position_evidence=None,
        )
    )
    assert result.position_proof_path == audit.PROOF_NONE
    assert result.audit_status == audit.REVIEW
    assert audit.RC_PRIMARY_EVIDENCE_NOT_RETRIEVED in result.reason_codes
    assert audit.RC_POSITION_PROOF_UNAVAILABLE in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_MISSING not in result.reason_codes


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


def test_multiple_poi_candidates_is_observation_only():
    """POI 候補が複数でも、Anchor Semantics が解決済みなら status を下げない。

    P2-A02 §13 / §18 / GC-12。複数候補は構造の observation であり、
    意味論を決めるのは `anchor_semantics_status` である。
    """
    result = audit.evaluate(
        _item(primary_position_evidence=_evidence(poi_candidate_count=3))
    )
    assert audit.RC_MULTIPLE_POI_CANDIDATES in result.reason_codes
    assert audit.RC_MULTIPLE_POI_CANDIDATES not in audit.REVIEW_REASON_CODES
    assert audit.RC_MULTIPLE_POI_CANDIDATES not in audit.HOLD_REASON_CODES
    assert result.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE
    assert result.audit_status == audit.AUTO_PASS

    # Anchor Semantics が未解決なら、複数候補ではなく gate が REVIEW を作る。
    unresolved = audit.evaluate(
        _item(
            primary_position_evidence=_evidence(poi_candidate_count=3),
            anchor_semantics_status=audit.ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        )
    )
    assert unresolved.audit_status == audit.REVIEW
    assert audit.RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED in unresolved.reason_codes


# ---------------------------------------------------------------------------
# M-N. Resolution Record 再利用
# ---------------------------------------------------------------------------


def test_m_existing_pass_resolution_record_is_reusable():
    """Seed == Production == adopted のときだけ再利用できる。"""
    result = audit.evaluate(
        _item(
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes


def test_m2_resolution_record_coordinate_mismatch_blocks_reuse():
    result = audit.evaluate(
        _item(
            primary_position_evidence=None,
            existing_resolution=_resolution(
                adopted_latitude=35.5, adopted_longitude=139.5
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
            existing_resolution=_resolution(position_status="HOLD_POSITION_REVIEW"),
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_POSITION_CONTRACT_HOLD_RECORD in result.reason_codes


def test_n_newer_conflict_overrides_resolution_reuse():
    """Record が PASS でも、新しい evidence が矛盾すれば自動再利用しない。"""
    result = audit.evaluate(
        _item(
            primary_position_evidence=_evidence(latitude=35.002, longitude=139.002),
            existing_resolution=_resolution(),
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
    # Seed ↔ Production の差は **artifact 同期**の問題であり、
    # Position の正しさではない（P2-A02 §22 / GC-20）。
    assert audit.RC_SEED_PRODUCTION_COORDINATE_DIFFERS in result.reason_codes
    assert audit.RC_ARTIFACT_BASE_SEED_DRIFT in result.reason_codes
    assert result.artifact_sync_status == audit.ARTIFACT_DRIFT
    # Primary Evidence は現在の Production 座標を独立に証明できている。
    assert result.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE
    assert result.audit_status == audit.AUTO_PASS


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
    # corroboration は proof path を作らない（P2-A02 §12）。
    assert result.position_proof_path == audit.PROOF_NONE
    assert audit.RC_POSITION_PROOF_UNAVAILABLE in result.reason_codes


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
        # 取得できた evidence の source identity が不明 => HOLD（GC-18）。
        audit.evaluate(
            _item(
                spreadsheet=_bare_sheet(),
                primary_position_evidence=_evidence(source_url=None),
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

    # Position / Anchor / Artifact は独立の軸として集計される。
    assert report["position_proof_path_counts"] == {
        audit.PROOF_NONE: 2,
        audit.PROOF_PRIMARY_EVIDENCE: 1,
    }
    assert report["anchor_semantics_counts"] == {
        audit.ANCHOR_SEMANTICS_CONFIRMED: 3
    }
    assert report["artifact_sync_counts"] == {audit.ARTIFACT_SYNCED: 3}
    for key in (
        "position_proof_path_counts",
        "anchor_semantics_counts",
        "artifact_sync_counts",
    ):
        assert list(report[key]) == sorted(report[key])


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


# ---------------------------------------------------------------------------
# Review fix: AUTO_PASS は traceable primary-source provenance を要求する
#
# Position Contract §Audit Record は position_source_type / position_source_url /
# verified_at の追跡可能性を求める。座標と entity だけでは machine-verified と
# 言えない。effective provenance は evidence を優先し、欠けた field だけ
# joined Spreadsheet で補う。
# ---------------------------------------------------------------------------


def _full_evidence(**overrides) -> "audit.PrimaryPositionEvidence":
    """provenance を evidence 側で完結させた fixture。"""
    values = dict(
        status="OK",
        source_type="shrine_official",
        source_url="https://example.invalid/shrine/access",
        latitude=35.0,
        longitude=139.0,
        entity_match="SAME",
        poi_candidate_count=1,
        verified_at="2026-09-17",
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
    )
    values.update(overrides)
    return audit.PrimaryPositionEvidence(**values)


def _bare_sheet(**overrides) -> "audit.SpreadsheetRow":
    """provenance を持たない Spreadsheet 行（fallback させない）。"""
    values = {
        "row_id": "500",
        "official_name": SEED_ROW["name_jp"],
        "official_address": SEED_ROW["address"],
        "position_source_type": None,
        "position_source_url": None,
        "official_source_type": None,
        "official_source_url": None,
        "verified_at": None,
    }
    values.update(overrides)
    return audit.SpreadsheetRow(**values)


def test_complete_provenance_is_auto_pass_eligible():
    """OK + SAME + 座標 + source_type + source_url + verified_at => AUTO_PASS。"""
    result = audit.evaluate(
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence())
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    assert result.primary_source_type == "shrine_official"
    assert result.primary_source_url == "https://example.invalid/shrine/access"
    assert result.verified_at == "2026-09-17"


def test_missing_source_url_never_auto_pass():
    """source_url が無ければ HOLD / PRIMARY_SOURCE_MISSING。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(source_url=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_MISSING in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes


def test_missing_source_type_never_auto_pass():
    """source_type が無ければ stable な explicit reason code で fail closed。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(source_type=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_TYPE_MISSING in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes


def test_missing_verified_at_never_auto_pass():
    """verified_at が無ければ REVIEW（stable な explicit reason code）。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(verified_at=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert result.audit_status == audit.REVIEW
    assert audit.RC_PRIMARY_SOURCE_VERIFIED_AT_MISSING in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes


def test_spreadsheet_cannot_supply_a_missing_primary_source_url():
    """Primary source_url が無いとき、Spreadsheet の URL を流し込まない。

    P2-A02 §15 / GC-18。Primary の座標がその URL 由来である証拠が無い以上、
    同一 source だと機械的に確認できない。provenance を合成してはならない。
    """
    evidence_without_metadata = _full_evidence(
        source_type=None, source_url=None, verified_at=None
    )
    sheet_with_provenance = _sheet(
        position_source_type="shrine_authority_access_map",
        position_source_url="https://example.invalid/authority/access",
        verified_at="2026-09-15",
    )
    result = audit.evaluate(
        _item(
            spreadsheet=sheet_with_provenance,
            primary_position_evidence=evidence_without_metadata,
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_MISSING in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes
    assert result.position_proof_path == audit.PROOF_NONE
    # Spreadsheet の値が Primary provenance へ漏れていない。
    assert result.primary_source_url is None
    assert result.primary_source_type is None
    assert result.verified_at is None
    # 比較対象の Primary URL が無いので「不一致」ではない（P2-A02 §16）。
    assert audit.RC_SPREADSHEET_POSITION_SOURCE_MISMATCH not in result.reason_codes


def test_spreadsheet_supplements_only_when_the_position_source_is_identical():
    """同一 Position source だと確認できたときだけ metadata を補完する。

    P2-A02 §15。`official_source_url` / `official_source_type` は identity
    provenance であり、Position provenance の代用にはならない。
    """
    evidence = _full_evidence(source_type=None, verified_at=None)
    same_source_sheet = _sheet(
        position_source_url=evidence.source_url,
        position_source_type="shrine_official",
        verified_at="2026-09-15",
    )
    supplemented = audit.evaluate(
        _item(spreadsheet=same_source_sheet, primary_position_evidence=evidence)
    )
    assert supplemented.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE
    assert supplemented.audit_status == audit.AUTO_PASS
    assert supplemented.primary_source_type == "shrine_official"
    assert supplemented.verified_at == "2026-09-15"

    # 別 source の行は補完できず、mismatch として観測されるだけ。
    other_source_sheet = _sheet(
        position_source_url="https://example.invalid/other/source",
        position_source_type="shrine_official",
        verified_at="2026-09-15",
    )
    not_supplemented = audit.evaluate(
        _item(spreadsheet=other_source_sheet, primary_position_evidence=evidence)
    )
    assert not_supplemented.primary_source_type is None
    assert not_supplemented.verified_at is None
    assert audit.RC_PRIMARY_SOURCE_TYPE_MISSING in not_supplemented.reason_codes
    assert (
        audit.RC_SPREADSHEET_POSITION_SOURCE_MISMATCH
        in not_supplemented.reason_codes
    )
    assert not_supplemented.audit_status == audit.REVIEW


def test_official_source_url_is_never_position_provenance():
    """identity provenance を Position provenance に流用しない（P2-A02 §15）。"""
    identity_only_sheet = _bare_sheet(
        official_source_type="shrine_official",
        official_source_url="https://example.invalid/identity/source",
        verified_at="2026-09-15",
    )
    result = audit.evaluate(
        _item(
            spreadsheet=identity_only_sheet,
            primary_position_evidence=_full_evidence(
                source_type=None, source_url=None, verified_at=None
            ),
        )
    )
    assert result.primary_source_url is None
    assert result.primary_source_type is None
    assert result.verified_at is None
    assert audit.RC_PRIMARY_SOURCE_MISSING in result.reason_codes


def test_evidence_verified_at_overrides_spreadsheet_verified_at():
    """出力の verified_at は evidence を優先し、次に Spreadsheet を使う。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(verified_at="2026-01-01"),
            primary_position_evidence=_full_evidence(verified_at="2026-09-17"),
        )
    )
    assert result.verified_at == "2026-09-17"
    assert result.audit_status == audit.AUTO_PASS

    # evidence 側が無いときだけ Spreadsheet の値になる。
    fallback = audit.evaluate(
        _item(
            spreadsheet=_sheet(verified_at="2026-01-01"),
            primary_position_evidence=_full_evidence(verified_at=None),
        )
    )
    assert fallback.verified_at == "2026-01-01"


def test_evidence_source_url_overrides_spreadsheet_source_url():
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(
                position_source_url="https://example.invalid/sheet",
                position_source_type="map_provider_poi",
            ),
            primary_position_evidence=_full_evidence(),
        )
    )
    assert result.primary_source_url == "https://example.invalid/shrine/access"
    assert result.primary_source_type == "shrine_official"


def test_primary_evidence_snapshot_reads_verified_at(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(
        json.dumps(
            [
                {
                    "candidate_id": "wave0-999",
                    "status": "OK",
                    "source_type": "shrine_official",
                    "source_url": "https://example.invalid/access",
                    "latitude": 35.0,
                    "longitude": 139.0,
                    "entity_match": "SAME",
                    "verified_at": "2026-09-17",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    by_candidate, _by_identity = audit.load_primary_evidence_snapshot(path)
    assert by_candidate["wave0-999"].verified_at == "2026-09-17"


def test_provenance_gap_reaches_auto_pass_only_with_full_provenance_via_build_inputs():
    """build_inputs() 経由でも provenance 不足は AUTO_PASS にならない。"""
    complete = _build(
        spreadsheet_rows=[_bare_sheet()],
        primary_evidence_by_candidate={"wave0-999": _full_evidence()},
    )
    assert audit.evaluate(complete[0]).audit_status == audit.AUTO_PASS

    incomplete = _build(
        spreadsheet_rows=[_bare_sheet()],
        primary_evidence_by_candidate={
            "wave0-999": _full_evidence(verified_at=None, source_type=None)
        },
    )
    result = audit.evaluate(incomplete[0])
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_TYPE_MISSING in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED_AT_MISSING in result.reason_codes


# ---------------------------------------------------------------------------
# Review fix: Resolution Record 再利用は provenance bypass ではない
#
# PrimaryPositionEvidence 経由の AUTO_PASS と同じ traceability
# （position_source_type / position_source_url / verified_at）を要求する。
# ---------------------------------------------------------------------------


def test_resolution_reuse_requires_complete_provenance():
    """PASS record + 座標一致 + provenance 完備 => AUTO_PASS。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes
    # 出力は record 自身の provenance を引き継ぐ（追跡可能なまま）。
    assert result.primary_source_type == "shrine_authority_access_map"
    assert result.primary_source_url == "https://example.invalid/authority/access"
    assert result.verified_at == "2026-09-16"


def test_resolution_missing_source_url_never_auto_pass():
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(position_source_url=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert result.audit_status == audit.HOLD
    assert audit.RC_RESOLUTION_SOURCE_URL_MISSING in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_resolution_missing_source_type_never_auto_pass():
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(position_source_type=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_RESOLUTION_SOURCE_TYPE_MISSING in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_resolution_missing_verified_at_never_auto_pass():
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(verified_at=None),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_RESOLUTION_VERIFIED_AT_MISSING in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_sapporo_suwa_resolution_record_parses_full_provenance():
    """実 repository の Position Resolution Record が provenance まで読める。"""
    records = audit.load_resolution_records()
    record = records["wave0-010"]

    assert record.position_status == "PASS"
    assert record.adopted_latitude == 43.07603505258046
    assert record.adopted_longitude == 141.3540979693115
    assert record.position_source_type == "shrine_authority_access_map"
    assert record.position_source_url == (
        "https://jinjasapporo.net/find-shrine/"
        "%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/"
    )
    assert record.verified_at == "2026-09-16"


def test_sapporo_suwa_record_is_reusable_when_coordinates_agree():
    """実 record + 実採用座標なら再利用できる（provenance 完備のため）。"""
    records = audit.load_resolution_records()
    record = records["wave0-010"]
    lat, lng = record.adopted_latitude, record.adopted_longitude

    result = audit.evaluate(
        _item(
            seed=audit.SeedPosition(latitude=lat, longitude=lng),
            production=audit.ProductionPosition(latitude=lat, longitude=lng),
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=record,
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes
    assert result.verified_at == "2026-09-16"


def test_newer_conflicting_evidence_still_overrides_complete_resolution():
    """provenance が完備していても、新しい evidence の矛盾が優先する。

    freshness threshold は導入しない（Position Contract に定義が無い）。
    """
    result = audit.evaluate(
        _item(
            primary_position_evidence=_full_evidence(
                latitude=35.002, longitude=139.002
            ),
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_PRIMARY_COORDINATE_DIFFERS in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_newer_evidence_supplies_output_provenance_over_resolution():
    """新しい evidence が adopted source を供給するなら、その provenance を出す。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert result.primary_source_url == "https://example.invalid/shrine/access"
    assert result.primary_source_type == "shrine_official"
    assert result.verified_at == "2026-09-17"


def test_no_freshness_threshold_is_applied_to_resolution_records():
    """古い verified_at でも、それだけでは再利用を止めない。

    Position Contract は「N 日より古ければ stale」という閾値を定義していない。
    発明しない。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(verified_at="2001-01-01"),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes
    assert result.verified_at == "2001-01-01"


def test_resolution_provenance_output_is_byte_stable():
    items = [
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
        for _ in range(3)
    ]
    first = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    second = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")


# ---------------------------------------------------------------------------
# Review fix: path isolation
#
# Resolution Record の provenance 欠落は **Resolution 再利用経路だけ** を塞ぐ。
# 有効な PrimaryPositionEvidence 経路を汚染してはならない。
# ---------------------------------------------------------------------------

RESOLUTION_MISSING_CODES = (
    "RESOLUTION_SOURCE_URL_MISSING",
    "RESOLUTION_SOURCE_TYPE_MISSING",
    "RESOLUTION_VERIFIED_AT_MISSING",
)


def test_incomplete_resolution_does_not_poison_valid_primary_evidence():
    """C: 完全な新 evidence があるなら、古い不完全 record は影響しない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(
                position_source_url=None,
                position_source_type=None,
                verified_at=None,
            ),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    for code in RESOLUTION_MISSING_CODES:
        assert code not in result.reason_codes, code
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_complete_resolution_with_wrong_entity_evidence_is_hold():
    """D: wrong-entity の新 evidence があれば再利用を主張しない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(entity_match="DIFFERENT"),
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_WRONG_ENTITY in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_complete_resolution_with_coordinate_conflicting_evidence_is_review():
    """D: 座標が矛盾する新 evidence があれば再利用を主張しない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(
                latitude=35.01, longitude=139.01
            ),
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_PRIMARY_COORDINATE_DIFFERS in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_no_new_evidence_with_incomplete_resolution_url_is_hold():
    """B: Resolution 経路に依存しているなら provenance 欠落で fail closed。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(position_source_url=None),
        )
    )
    assert result.audit_status == audit.HOLD
    assert audit.RC_RESOLUTION_SOURCE_URL_MISSING in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_no_new_evidence_with_complete_resolution_is_auto_pass():
    """A: 新 evidence が無く record が完備なら再利用できる。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes


@pytest.mark.parametrize(
    "conflicting_evidence",
    [
        pytest.param({"entity_match": "DIFFERENT"}, id="wrong_entity"),
        pytest.param({"entity_match": "NON_SHRINE"}, id="non_shrine"),
        pytest.param({"entity_match": "AMBIGUOUS"}, id="ambiguous"),
        pytest.param({"entity_match": None}, id="identity_evidence_missing"),
        pytest.param({"latitude": 35.01, "longitude": 139.01}, id="coordinate_differs"),
    ],
)
def test_every_conflicting_evidence_kind_blocks_resolution_reuse(conflicting_evidence):
    """D の列挙すべてが RESOLUTION_RECORD_REUSED を止める。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(**conflicting_evidence),
            existing_resolution=_resolution(),
        )
    )
    assert result.audit_status != audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_multiple_poi_candidates_alone_does_not_block_resolution_reuse():
    """複数 POI 候補は「より新しい矛盾」ではない（P2-A02 §13）。

    Anchor Semantics が明示的に解決されていれば、候補数だけを理由に
    Resolution fallback を塞いではならない。
    """
    assert audit.RC_MULTIPLE_POI_CANDIDATES not in audit.PRIMARY_BLOCKING_CONFLICT_CODES

    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            # 取得はできたが provenance が無く、Primary 単独では証明できない。
            primary_position_evidence=_full_evidence(
                status="FETCH_FAILED", poi_candidate_count=4
            ),
            existing_resolution=_resolution(),
        )
    )
    assert result.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes
    assert result.audit_status == audit.AUTO_PASS


def test_conflicting_evidence_does_not_add_resolution_missing_codes():
    """矛盾しているときは Resolution の provenance 欠落 code も足さない。

    矛盾自体が既に HOLD / REVIEW を生んでいる。経路が使われていない以上、
    その経路の欠落を理由として並べない。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(entity_match="DIFFERENT"),
            existing_resolution=_resolution(
                position_source_url=None, position_source_type=None, verified_at=None
            ),
        )
    )
    assert result.audit_status == audit.HOLD
    for code in RESOLUTION_MISSING_CODES:
        assert code not in result.reason_codes, code


def test_resolution_candidate_and_reusable_are_separate_concepts():
    """candidate（座標一致）と reusable（provenance 完備）は別物。

    不完全 record + 完全 evidence では、record は candidate だが reusable では
    ない。にもかかわらず evidence 経路は独立に AUTO_PASS へ到達する。
    """
    incomplete_record = _resolution(verified_at=None)

    # evidence 無し -> record 経路に依存 -> fail closed
    without_evidence = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=incomplete_record,
        )
    )
    assert without_evidence.audit_status == audit.REVIEW
    assert audit.RC_RESOLUTION_VERIFIED_AT_MISSING in without_evidence.reason_codes

    # 同じ record + 完全 evidence -> evidence 経路が独立に成立
    with_evidence = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=incomplete_record,
        )
    )
    assert with_evidence.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_VERIFIED_AT_MISSING not in with_evidence.reason_codes


def test_resolution_coordinate_mismatch_does_not_downgrade_verified_evidence():
    """歴史的 record の座標食い違いで、検証済み evidence 経路を引き下げない。

    以前はこの code を evidence の有無に関わらず出していたため、古い record が
    有効な PrimaryPositionEvidence 経路を REVIEW へ落としていた。
    現在の position を evidence が独立に検証できているなら、過去の record の
    食い違いは status を駆動しない。
    """
    mismatched = _resolution(adopted_latitude=35.9, adopted_longitude=139.9)
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=mismatched,
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH not in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes
    # 履歴としての追跡可能性は保持する。
    assert result.existing_resolution_record == mismatched.record_path


# ---------------------------------------------------------------------------
# Review fix: exclusive positive proof paths + mismatch isolation
#
# RESOLUTION_RECORD_REUSED は「Resolution Record を fallback proof path として
# 実際に使った」という意味に限定する。evidence 経路が現在の position を独立に
# 検証できているなら record は使っていないので出さない。履歴としての
# 追跡可能性は existing_resolution_record が担う。
# ---------------------------------------------------------------------------


def test_case_a_valid_evidence_with_mismatched_resolution_is_auto_pass():
    """A: 有効な evidence + 古い/食い違う record -> AUTO_PASS。"""
    mismatched = _resolution(adopted_latitude=35.9, adopted_longitude=139.9)
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=mismatched,
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH not in result.reason_codes
    assert result.existing_resolution_record == mismatched.record_path


def test_case_b_no_valid_evidence_with_mismatched_resolution_is_review():
    """B: 有効な evidence なし + 食い違う record -> REVIEW。

    Spreadsheet は traceable な source を持つ（`_sheet()`）。持たない
    `_bare_sheet()` だと `PRIMARY_SOURCE_MISSING` が別途 HOLD を立ててしまい、
    mismatch が status を駆動しているかを測れない。
    """
    mismatched = _resolution(adopted_latitude=35.9, adopted_longitude=139.9)
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(),
            primary_position_evidence=None,
            existing_resolution=mismatched,
        )
    )
    assert result.audit_status == audit.REVIEW
    assert audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes


def test_case_c_valid_evidence_with_matching_complete_resolution_is_exclusive():
    """C: 有効な evidence + 一致する完備 record -> PRIMARY_SOURCE_VERIFIED のみ。"""
    record = _resolution()
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=record,
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_PRIMARY_SOURCE_VERIFIED in result.reason_codes
    assert audit.RC_RESOLUTION_RECORD_REUSED not in result.reason_codes
    # 履歴としての追跡可能性は残る。
    assert result.existing_resolution_record == record.record_path
    # 出力 provenance は evidence 側。
    assert result.primary_source_url == "https://example.invalid/shrine/access"
    assert result.verified_at == "2026-09-17"


def test_case_d_no_evidence_with_matching_complete_resolution_is_reused():
    """D: evidence なし + 一致する完備 record -> RESOLUTION_RECORD_REUSED。"""
    record = _resolution()
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=None,
            existing_resolution=record,
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    assert audit.RC_RESOLUTION_RECORD_REUSED in result.reason_codes
    assert audit.RC_PRIMARY_SOURCE_VERIFIED not in result.reason_codes
    assert result.existing_resolution_record == record.record_path
    # 出力 provenance は record 側。
    assert result.primary_source_url == "https://example.invalid/authority/access"
    assert result.verified_at == "2026-09-16"


def test_positive_proof_codes_are_mutually_exclusive():
    """PRIMARY_SOURCE_VERIFIED と RESOLUTION_RECORD_REUSED は同時に立たない。"""
    combinations = [
        (_full_evidence(), _resolution()),
        (_full_evidence(), _resolution(verified_at=None)),
        (None, _resolution()),
        (None, None),
    ]
    for evidence, record in combinations:
        result = audit.evaluate(
            _item(
                spreadsheet=_bare_sheet(),
                primary_position_evidence=evidence,
                existing_resolution=record,
            )
        )
        positives = {
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_RESOLUTION_RECORD_REUSED,
        } & set(result.reason_codes)
        assert len(positives) <= 1, (evidence, record, result.reason_codes)


def test_incomplete_resolution_with_valid_evidence_emits_no_resolution_codes():
    """指示3: 「不完全 record + 完全 evidence -> REUSED」は誤り。

    evidence 経路が単独で成立している場合、Resolution 由来の code は
    positive（REUSED）も negative（*_MISSING / MISMATCH）も出さない。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(
                position_source_url=None,
                position_source_type=None,
                verified_at=None,
            ),
        )
    )
    assert result.audit_status == audit.AUTO_PASS
    resolution_codes = [
        code for code in result.reason_codes if code.startswith("RESOLUTION_")
    ]
    assert resolution_codes == []


# ---------------------------------------------------------------------------
# P2-A03 Golden Cases
#
# `docs/audit/position-audit-v2/p2-a03-golden-cases.md` を authority として、
# 承認済み 12 ケースを決定的な regression test に固定する。
#
# 各ケースで最低限そろえて固定するもの:
#   position_proof_path / anchor_semantics_status / artifact_sync_status /
#   expected_reason_codes / forbidden_reason_codes / audit_status
#
# final status だけでは不十分（P2-A02 §26）。
# ---------------------------------------------------------------------------

ANCHOR_REASON_CODES = (
    audit.RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED,
    audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
    audit.RC_ANCHOR_SEMANTICS_UNKNOWN,
)

ARTIFACT_DRIFT_CODES = (
    audit.RC_ARTIFACT_BASE_SEED_DRIFT,
    audit.RC_ARTIFACT_PRODUCTION_DRIFT,
    audit.RC_ARTIFACT_CANDIDATE_MASTER_DRIFT,
    audit.RC_ARTIFACT_RESOLUTION_DRIFT,
)


def _assert_golden_case(
    result,
    *,
    case_id: str,
    position_proof_path: str,
    anchor_semantics_status: str,
    artifact_sync_status: str,
    expected_reason_codes: tuple[str, ...],
    forbidden_reason_codes: tuple[str, ...],
    audit_status: str,
) -> None:
    """Golden Case が固定する6軸をすべて検証する。"""
    codes = set(result.reason_codes)
    assert result.position_proof_path == position_proof_path, case_id
    assert result.anchor_semantics_status == anchor_semantics_status, case_id
    assert result.artifact_sync_status == artifact_sync_status, case_id
    for code in expected_reason_codes:
        assert code in codes, f"{case_id}: expected {code}"
    for code in forbidden_reason_codes:
        assert code not in codes, f"{case_id}: forbidden {code}"
    assert result.audit_status == audit_status, case_id


def test_gc_01_clean_primary_auto_pass():
    """完備した Primary Evidence が単独で現在の Position を証明する。"""
    result = audit.evaluate(
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence())
    )
    _assert_golden_case(
        result,
        case_id="GC-01",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_PRIMARY_SOURCE_VERIFIED,),
        forbidden_reason_codes=(
            audit.RC_RESOLUTION_RECORD_REUSED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            *ANCHOR_REASON_CODES,
        ),
        audit_status=audit.AUTO_PASS,
    )


def test_gc_02_valid_primary_isolates_broken_resolution():
    """使っていない Resolution 経路の欠陥が、選ばれた経路を汚染しない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(
                position_source_url=None,
                position_source_type=None,
                verified_at=None,
            ),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-02",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_PRIMARY_SOURCE_VERIFIED,),
        forbidden_reason_codes=(
            audit.RC_RESOLUTION_RECORD_REUSED,
            audit.RC_RESOLUTION_SOURCE_URL_MISSING,
            audit.RC_RESOLUTION_SOURCE_TYPE_MISSING,
            audit.RC_RESOLUTION_VERIFIED_AT_MISSING,
            audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
        ),
        audit_status=audit.AUTO_PASS,
    )


def test_gc_03_fetch_failed_with_valid_resolution_fallback():
    """取得失敗は observation。有効な fallback があれば status を下げない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-03",
        position_proof_path=audit.PROOF_RESOLUTION_FALLBACK,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(
            audit.RC_SOURCE_FETCH_FAILED,
            audit.RC_RESOLUTION_RECORD_REUSED,
        ),
        forbidden_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_RESOLUTION_SOURCE_URL_MISSING,
            audit.RC_RESOLUTION_SOURCE_TYPE_MISSING,
            audit.RC_RESOLUTION_VERIFIED_AT_MISSING,
            audit.RC_RESOLUTION_RECORD_COORDINATE_MISMATCH,
            *ANCHOR_REASON_CODES,
        ),
        audit_status=audit.AUTO_PASS,
    )

    # 出力 provenance は選ばれた経路（Resolution Record）から取る。
    assert result.primary_source_url == "https://example.invalid/authority/access"
    assert result.primary_source_type == "shrine_authority_access_map"
    assert result.verified_at == "2026-09-16"

    # Resolution fallback も Anchor Semantics gate を迂回しない。
    # 同じ入力で anchor を NOT_EVALUATED にすると REVIEW になる。
    gated = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
            anchor_semantics_status=audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
        )
    )
    assert gated.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert gated.audit_status == audit.REVIEW
    assert audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED in gated.reason_codes


def test_gc_06_newer_coordinate_conflict_blocks_fallback():
    """より新しい Primary の座標矛盾は、歴史的 Resolution の再利用を塞ぐ。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(
                latitude=35.02, longitude=139.02
            ),
            existing_resolution=_resolution(),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-06",
        position_proof_path=audit.PROOF_NONE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_PRIMARY_COORDINATE_DIFFERS,),
        forbidden_reason_codes=(
            audit.RC_RESOLUTION_RECORD_REUSED,
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
        ),
        audit_status=audit.REVIEW,
    )

    # FETCH_FAILED（証明も反証もできない）と COORDINATE_CONFLICT
    # （能動的に食い違う）の境界を固定する。
    fetch_failed = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
        )
    )
    assert fetch_failed.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert fetch_failed.audit_status == audit.AUTO_PASS


def test_gc_10_valid_primary_with_unevaluated_semantics_is_review():
    """有効な proof path でも Anchor Semantics gate は迂回できない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            anchor_semantics_status=audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-10",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
        ),
        forbidden_reason_codes=(
            audit.RC_RESOLUTION_RECORD_REUSED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED,
            audit.RC_ANCHOR_SEMANTICS_UNKNOWN,
        ),
        audit_status=audit.REVIEW,
    )


def test_gc_12_multi_site_with_confirmed_semantics_is_auto_pass_eligible():
    """構造的な複雑さは、確認済みの Anchor Semantics を覆さない。

    `multi_site_status` / `anchor_complexity` は入力 model に存在しない
    （Anchor Semantics をそこから導出してはならないため / P2-A02 §6）。
    Golden Case の言う "equivalent supporting evidence" として、機械可読な
    `poi_candidate_count > 1` で複数拠点性を表現する。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(poi_candidate_count=3),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-12",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_PRIMARY_SOURCE_VERIFIED,),
        forbidden_reason_codes=(
            *ANCHOR_REASON_CODES,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_RESOLUTION_RECORD_REUSED,
        ),
        audit_status=audit.AUTO_PASS,
    )
    # 後方互換の observation として出てよいが、status は駆動しない。
    assert audit.RC_MULTIPLE_POI_CANDIDATES in result.reason_codes


def test_gc_15_spreadsheet_row_missing_does_not_downgrade():
    """Spreadsheet 行の欠落は、完備した Primary proof path を下げない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=None,
            spreadsheet_join_status=audit.SHEET_JOIN_NONE,
            spreadsheet_snapshot_available=True,
            primary_position_evidence=_full_evidence(),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-15",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_SPREADSHEET_ROW_MISSING,
        ),
        forbidden_reason_codes=(
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_RESOLUTION_RECORD_REUSED,
            *ANCHOR_REASON_CODES,
        ),
        audit_status=audit.AUTO_PASS,
    )
    # Spreadsheet は canonical な Position artifact ではない。
    assert audit.RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE not in result.reason_codes


def test_gc_18_missing_primary_source_url_cannot_be_supplemented():
    """Primary source_url 不在を Spreadsheet の URL で埋めてはならない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_sheet(
                position_source_type="shrine_authority_access_map",
                position_source_url="https://example.invalid/authority/access",
                verified_at="2026-09-15",
            ),
            primary_position_evidence=_full_evidence(source_url=None),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-18",
        position_proof_path=audit.PROOF_NONE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_PRIMARY_SOURCE_MISSING,),
        forbidden_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_RESOLUTION_RECORD_REUSED,
            # 比較対象の Primary URL が無いので「不一致」ではない。
            audit.RC_SPREADSHEET_POSITION_SOURCE_MISMATCH,
        ),
        audit_status=audit.HOLD,
    )
    # Spreadsheet の provenance が Primary 側へ漏れていない。
    assert result.primary_source_url is None


def test_gc_20_position_auto_pass_with_artifact_drift():
    """artifact の drift は、有効な proof path を単独で下げない。"""
    result = audit.evaluate(
        _item(
            seed=audit.SeedPosition(latitude=34.9, longitude=138.9),
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-20",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_DRIFT,
        expected_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_ARTIFACT_BASE_SEED_DRIFT,
        ),
        forbidden_reason_codes=(
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_RESOLUTION_RECORD_REUSED,
            *ANCHOR_REASON_CODES,
        ),
        audit_status=audit.AUTO_PASS,
    )
    # legacy code は後方互換で出てよいが、Position status は駆動しない。
    assert audit.RC_SEED_PRODUCTION_COORDINATE_DIFFERS in result.reason_codes


def test_gc_21_artifact_synced_with_position_review():
    """artifact が揃っていることは Position の正しさの証明ではない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            candidate_master=audit.CandidateMasterPosition(
                latitude=35.0, longitude=139.0
            ),
            existing_resolution=_resolution(),
            primary_position_evidence=_full_evidence(),
            anchor_semantics_status=audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-21",
        position_proof_path=audit.PROOF_PRIMARY_EVIDENCE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
        ),
        forbidden_reason_codes=(
            audit.RC_POSITION_PROOF_UNAVAILABLE,
            audit.RC_RESOLUTION_RECORD_REUSED,
            *ARTIFACT_DRIFT_CODES,
        ),
        audit_status=audit.REVIEW,
    )


def test_gc_23_canonical_hold_wins():
    """canonical HOLD は Machine Audit が自動解除できない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(
                position_status="HOLD_POSITION_REVIEW"
            ),
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-23",
        position_proof_path=audit.PROOF_NONE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(audit.RC_POSITION_CONTRACT_HOLD_RECORD,),
        forbidden_reason_codes=(
            audit.RC_RESOLUTION_RECORD_REUSED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
        ),
        audit_status=audit.HOLD,
    )

    # canonical HOLD が無ければ同じ入力は AUTO_PASS になりうる、という対比。
    without_hold = audit.evaluate(
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence())
    )
    assert without_hold.audit_status == audit.AUTO_PASS
    assert without_hold.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE


def test_gc_24_no_proof_path_is_review():
    """有効な proof path が無いことを明示し、AUTO_PASS を主張しない。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=None,
        )
    )
    _assert_golden_case(
        result,
        case_id="GC-24",
        position_proof_path=audit.PROOF_NONE,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
        artifact_sync_status=audit.ARTIFACT_SYNCED,
        expected_reason_codes=(
            audit.RC_SOURCE_FETCH_FAILED,
            audit.RC_POSITION_PROOF_UNAVAILABLE,
        ),
        forbidden_reason_codes=(
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_RESOLUTION_RECORD_REUSED,
            *ANCHOR_REASON_CODES,
        ),
        audit_status=audit.REVIEW,
    )


# ---------------------------------------------------------------------------
# P2-A02 §17 / §22 — Reason Code responsibility classes
# ---------------------------------------------------------------------------


def test_artifact_reason_codes_never_drive_position_status():
    """artifact 同期の code は HOLD / REVIEW のどちらにも属さない（§22）。"""
    for code in audit.ARTIFACT_SYNC_REASON_CODES:
        assert code not in audit.HOLD_REASON_CODES, code
        assert code not in audit.REVIEW_REASON_CODES, code
    assert not (audit.ARTIFACT_SYNC_REASON_CODES & audit.HOLD_REASON_CODES)
    assert not (audit.ARTIFACT_SYNC_REASON_CODES & audit.REVIEW_REASON_CODES)


def test_observation_reason_codes_never_drive_position_status():
    """§18 が observation と定めた code は status を駆動しない。"""
    observation_only = {
        audit.RC_SOURCE_FETCH_FAILED,
        audit.RC_SOURCE_PARSE_FAILED,
        audit.RC_POSITION_SOURCE_REDIRECTED,
        audit.RC_PRIMARY_EVIDENCE_NOT_RETRIEVED,
        audit.RC_SPREADSHEET_ROW_MISSING,
        audit.RC_SPREADSHEET_SNAPSHOT_UNAVAILABLE,
        audit.RC_SPREADSHEET_IDENTITY_REVIEW,
        audit.RC_IDENTITY_NORMALIZATION_REQUIRED,
        audit.RC_MULTIPLE_POI_CANDIDATES,
        audit.RC_SEED_PRODUCTION_EXACT,
        # §22: legacy 観測値。Position の正しさを単独で定義しない。
        audit.RC_SEED_PRODUCTION_COORDINATE_DIFFERS,
        # §16
        audit.RC_SPREADSHEET_POSITION_SOURCE_MISMATCH,
    }
    for code in observation_only:
        assert code not in audit.HOLD_REASON_CODES, code
        assert code not in audit.REVIEW_REASON_CODES, code
        assert audit._classify({code}) == audit.AUTO_PASS, code


def test_reason_code_string_values_are_preserved():
    """既存の stable な reason code 文字列を改名・削除しない（§17 / §27）。"""
    for name, value in (
        ("RC_SEED_PRODUCTION_EXACT", "SEED_PRODUCTION_EXACT"),
        ("RC_PRIMARY_SOURCE_VERIFIED", "PRIMARY_SOURCE_VERIFIED"),
        ("RC_RESOLUTION_RECORD_REUSED", "RESOLUTION_RECORD_REUSED"),
        ("RC_POSITION_CONTRACT_HOLD_RECORD", "POSITION_CONTRACT_HOLD_RECORD"),
        ("RC_PRIMARY_SOURCE_MISSING", "PRIMARY_SOURCE_MISSING"),
        ("RC_PRIMARY_COORDINATE_DIFFERS", "PRIMARY_COORDINATE_DIFFERS"),
        ("RC_SOURCE_FETCH_FAILED", "SOURCE_FETCH_FAILED"),
        ("RC_SPREADSHEET_ROW_MISSING", "SPREADSHEET_ROW_MISSING"),
        ("RC_SEED_PRODUCTION_COORDINATE_DIFFERS", "SEED_PRODUCTION_COORDINATE_DIFFERS"),
        # P2-B01 で追加した承認済み code
        ("RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED", "ANCHOR_SEMANTICS_REVIEW_REQUIRED"),
        ("RC_ANCHOR_SEMANTICS_NOT_EVALUATED", "ANCHOR_SEMANTICS_NOT_EVALUATED"),
        ("RC_ANCHOR_SEMANTICS_UNKNOWN", "ANCHOR_SEMANTICS_UNKNOWN"),
        ("RC_POSITION_PROOF_UNAVAILABLE", "POSITION_PROOF_UNAVAILABLE"),
        (
            "RC_SPREADSHEET_POSITION_SOURCE_MISMATCH",
            "SPREADSHEET_POSITION_SOURCE_MISMATCH",
        ),
        ("RC_ARTIFACT_BASE_SEED_DRIFT", "ARTIFACT_BASE_SEED_DRIFT"),
        ("RC_ARTIFACT_PRODUCTION_DRIFT", "ARTIFACT_PRODUCTION_DRIFT"),
        ("RC_ARTIFACT_CANDIDATE_MASTER_DRIFT", "ARTIFACT_CANDIDATE_MASTER_DRIFT"),
        ("RC_ARTIFACT_RESOLUTION_DRIFT", "ARTIFACT_RESOLUTION_DRIFT"),
        ("RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE", "ARTIFACT_SYNC_INPUT_UNAVAILABLE"),
    ):
        assert getattr(audit, name) == value, name


# ---------------------------------------------------------------------------
# P2-A02 §6 / §7 — Anchor Semantics
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected_status", "expected_code"),
    [
        (audit.ANCHOR_SEMANTICS_CONFIRMED, audit.AUTO_PASS, None),
        (audit.ANCHOR_SEMANTICS_NOT_APPLICABLE, audit.AUTO_PASS, None),
        (
            audit.ANCHOR_SEMANTICS_REVIEW_REQUIRED,
            audit.REVIEW,
            audit.RC_ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        ),
        (
            audit.ANCHOR_SEMANTICS_NOT_EVALUATED,
            audit.REVIEW,
            audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED,
        ),
        (None, audit.REVIEW, audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED),
        ("", audit.REVIEW, audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED),
        ("PROBABLY_FINE", audit.REVIEW, audit.RC_ANCHOR_SEMANTICS_UNKNOWN),
        ("confirmed-ish", audit.REVIEW, audit.RC_ANCHOR_SEMANTICS_UNKNOWN),
    ],
)
def test_anchor_semantics_gate(status, expected_status, expected_code):
    """AUTO_PASS 資格は CONFIRMED / NOT_APPLICABLE のみ。未知は fail safe。"""
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            anchor_semantics_status=status,
        )
    )
    assert result.audit_status == expected_status
    if expected_code is None:
        assert not (set(result.reason_codes) & audit.ANCHOR_SEMANTICS_REASON_CODES)
    else:
        assert expected_code in result.reason_codes
    # proof path は Anchor Semantics とは独立に成立している。
    assert result.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE


def test_anchor_semantics_alone_never_creates_hold():
    """Anchor Semantics 単独では HOLD 経路を作らない（§7）。"""
    for code in audit.ANCHOR_SEMANTICS_REASON_CODES:
        assert code not in audit.HOLD_REASON_CODES, code
        assert audit._classify({code}) == audit.REVIEW, code


def test_anchor_semantics_is_case_and_whitespace_insensitive():
    assert audit.normalize_anchor_semantics("  confirmed  ") == (
        audit.ANCHOR_SEMANTICS_CONFIRMED
    )
    assert audit.normalize_anchor_semantics("Not_Applicable") == (
        audit.ANCHOR_SEMANTICS_NOT_APPLICABLE
    )


def test_anchor_semantics_is_never_derived_from_supporting_evidence():
    """支援的な evidence から意味論を導出しない（§6）。

    POI 候補数・provider・座標距離・名称類似度が何であれ、
    `anchor_semantics_status` を与えなければ `NOT_EVALUATED` のままである。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(
                poi_candidate_count=1,
                source_type="shrine_official",
            ),
            corroboration=(
                audit.CorroborationSource(
                    source_type="osm",
                    source_url="https://example.invalid/osm",
                    latitude=35.0,
                    longitude=139.0,
                ),
            ),
            anchor_semantics_status=None,
        )
    )
    assert result.anchor_semantics_status == audit.ANCHOR_SEMANTICS_NOT_EVALUATED
    assert audit.RC_ANCHOR_SEMANTICS_NOT_EVALUATED in result.reason_codes


def test_anchor_semantics_status_is_a_closed_enum_in_output():
    """出力 field は閉じた enum。未知入力をそのまま serialize しない。"""
    allowed = audit.ANCHOR_SEMANTICS_INPUT_VALUES | {audit.ANCHOR_SEMANTICS_UNKNOWN}
    for supplied in ("CONFIRMED", "REVIEW_REQUIRED", "NOT_EVALUATED",
                     "NOT_APPLICABLE", "totally bogus", None, ""):
        result = audit.evaluate(
            _item(
                spreadsheet=_bare_sheet(),
                primary_position_evidence=_full_evidence(),
                anchor_semantics_status=supplied,
            )
        )
        assert result.anchor_semantics_status in allowed
        assert result.to_dict()["anchor_semantics_status"] in allowed


def test_anchor_semantics_flows_from_the_evidence_snapshot(tmp_path):
    """snapshot が明示的に書いた値だけが入力として流れる。"""
    path = tmp_path / "evidence.json"
    path.write_text(
        json.dumps(
            [
                {
                    "candidate_id": "wave0-999",
                    "status": "OK",
                    "source_type": "shrine_official",
                    "source_url": "https://example.invalid/access",
                    "latitude": 35.0,
                    "longitude": 139.0,
                    "entity_match": "SAME",
                    "verified_at": "2026-09-17",
                    "anchor_semantics_status": "CONFIRMED",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    by_candidate, _ = audit.load_primary_evidence_snapshot(path)
    assert by_candidate["wave0-999"].anchor_semantics_status == "CONFIRMED"

    items = _build(primary_evidence_by_candidate=by_candidate)
    assert items[0].anchor_semantics_status == "CONFIRMED"
    result = audit.evaluate(items[0])
    assert result.anchor_semantics_status == audit.ANCHOR_SEMANTICS_CONFIRMED
    assert result.audit_status == audit.AUTO_PASS

    # 書かれていなければ未評価のまま（推測で埋めない）。
    without = _build(primary_evidence_by_candidate={})
    assert without[0].anchor_semantics_status is None
    assert (
        audit.evaluate(without[0]).anchor_semantics_status
        == audit.ANCHOR_SEMANTICS_NOT_EVALUATED
    )


# ---------------------------------------------------------------------------
# P2-A02 §8 — Position proof path
# ---------------------------------------------------------------------------


def test_position_proof_path_is_a_closed_enum():
    assert {
        audit.PROOF_PRIMARY_EVIDENCE,
        audit.PROOF_RESOLUTION_FALLBACK,
        audit.PROOF_NONE,
    } == {"PRIMARY_EVIDENCE", "RESOLUTION_FALLBACK", "NONE"}


def test_only_one_proof_path_is_ever_selected():
    """positive proof reason は排他的（§8 / §9）。"""
    cases = [
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence()),
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(),
        ),
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
        ),
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=None),
    ]
    for item in cases:
        result = audit.evaluate(item)
        codes = set(result.reason_codes)
        positives = codes & {
            audit.RC_PRIMARY_SOURCE_VERIFIED,
            audit.RC_RESOLUTION_RECORD_REUSED,
        }
        assert len(positives) <= 1, result.reason_codes
        if result.position_proof_path == audit.PROOF_PRIMARY_EVIDENCE:
            assert positives == {audit.RC_PRIMARY_SOURCE_VERIFIED}
        elif result.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK:
            assert positives == {audit.RC_RESOLUTION_RECORD_REUSED}
        else:
            assert positives == set()


def test_position_proof_unavailable_only_when_it_drives_status():
    """NONE の理由が別にあるなら proof unavailable を重ねて言わない（§12）。"""
    # 説明する code がある -> 出さない
    explained = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(latitude=35.02, longitude=139.02),
        )
    )
    assert explained.position_proof_path == audit.PROOF_NONE
    assert audit.RC_POSITION_PROOF_UNAVAILABLE not in explained.reason_codes

    # 説明する code が無い -> 出す
    unexplained = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
        )
    )
    assert unexplained.position_proof_path == audit.PROOF_NONE
    assert audit.RC_POSITION_PROOF_UNAVAILABLE in unexplained.reason_codes


def test_output_provenance_comes_only_from_the_selected_proof_path():
    """無関係な経路の metadata を混ぜた hybrid provenance を作らない（§24）。"""
    fallback = audit.evaluate(
        _item(
            spreadsheet=_sheet(
                position_source_url="https://example.invalid/sheet-only",
                position_source_type="map_provider_poi",
                verified_at="2020-01-01",
            ),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
        )
    )
    assert fallback.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert fallback.primary_source_url == "https://example.invalid/authority/access"
    assert fallback.primary_source_type == "shrine_authority_access_map"
    assert fallback.verified_at == "2026-09-16"


# ---------------------------------------------------------------------------
# P2-A02 §20 / §21 — Artifact Synchronization
# ---------------------------------------------------------------------------


def test_artifact_sync_status_is_a_closed_enum():
    assert {audit.ARTIFACT_SYNCED, audit.ARTIFACT_DRIFT, audit.ARTIFACT_UNKNOWN} == {
        "SYNCED",
        "DRIFT",
        "UNKNOWN",
    }


def test_candidate_master_drift_is_detected_independently():
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            candidate_master=audit.CandidateMasterPosition(
                latitude=34.5, longitude=138.5
            ),
            primary_position_evidence=_full_evidence(),
        )
    )
    assert audit.RC_ARTIFACT_CANDIDATE_MASTER_DRIFT in result.reason_codes
    assert result.artifact_sync_status == audit.ARTIFACT_DRIFT
    assert result.audit_status == audit.AUTO_PASS


def test_resolution_record_drift_is_detected_independently():
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            existing_resolution=_resolution(
                adopted_latitude=34.5, adopted_longitude=138.5
            ),
            primary_position_evidence=_full_evidence(),
        )
    )
    assert audit.RC_ARTIFACT_RESOLUTION_DRIFT in result.reason_codes
    assert result.artifact_sync_status == audit.ARTIFACT_DRIFT
    # 使っていない Resolution 経路の欠陥は Position status を下げない。
    assert result.audit_status == audit.AUTO_PASS


def test_artifact_sync_is_unknown_when_inputs_cannot_be_compared():
    result = audit.evaluate(
        _item(
            production=None,
            spreadsheet=None,
            spreadsheet_join_status=audit.SHEET_JOIN_NONE,
            seed_production_join_status=audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE,
            production_snapshot_available=False,
            spreadsheet_snapshot_available=False,
        )
    )
    assert result.artifact_sync_status == audit.ARTIFACT_UNKNOWN
    assert audit.RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE in result.reason_codes
    # 入力不在は依然として Position 側の HOLD である。
    assert result.audit_status == audit.HOLD


def test_missing_production_row_is_artifact_production_drift():
    result = audit.evaluate(
        _item(
            production=None,
            spreadsheet=_bare_sheet(),
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
        )
    )
    assert audit.RC_ARTIFACT_PRODUCTION_DRIFT in result.reason_codes
    assert result.artifact_sync_status == audit.ARTIFACT_DRIFT
    assert result.audit_status == audit.HOLD


def test_historical_artifacts_are_not_synchronization_authorities():
    """canonical HOLD record は adopted Position ではない（§21）。

    HOLD record の座標が現在値と違っても artifact drift にはしない。
    """
    result = audit.evaluate(
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            existing_resolution=_resolution(
                position_status="HOLD_POSITION_REVIEW",
                adopted_latitude=34.5,
                adopted_longitude=138.5,
            ),
        )
    )
    assert audit.RC_ARTIFACT_RESOLUTION_DRIFT not in result.reason_codes
    assert result.artifact_sync_status == audit.ARTIFACT_SYNCED
    assert result.audit_status == audit.HOLD


# ---------------------------------------------------------------------------
# P2-A02 §25 — 決定的評価順
# ---------------------------------------------------------------------------


def test_later_layers_never_override_canonical_hold():
    """後段（proof path / anchor / artifact）が canonical HOLD を覆さない。"""
    for overrides in (
        {"primary_position_evidence": _full_evidence()},
        {"primary_position_evidence": _full_evidence(status="FETCH_FAILED")},
        {"anchor_semantics_status": audit.ANCHOR_SEMANTICS_NOT_APPLICABLE},
        {"candidate_master": audit.CandidateMasterPosition(34.5, 138.5)},
    ):
        result = audit.evaluate(
            _item(
                spreadsheet=_bare_sheet(),
                existing_resolution=_resolution(
                    position_status="HOLD_POSITION_REVIEW"
                ),
                **overrides,
            )
        )
        assert result.audit_status == audit.HOLD, overrides
        assert result.position_proof_path == audit.PROOF_NONE, overrides
        assert audit.RC_POSITION_CONTRACT_HOLD_RECORD in result.reason_codes


# ---------------------------------------------------------------------------
# P2-A02 §28 — schema version gate
# ---------------------------------------------------------------------------


def test_schema_version_reflects_the_added_contract_fields():
    """contract-significant field を足したので schema を意図的に上げる。

    既存 field の削除・改名・再解釈は無く、後方互換な追加なので minor bump。
    Repository の慣行（candidate master schema 1.1 -> 1.2）と同じ扱い。
    """
    assert audit.SCHEMA_VERSION == "position-audit-v2/1.1"

    report = audit.build_report(
        [
            audit.evaluate(
                _item(
                    spreadsheet=_bare_sheet(),
                    primary_position_evidence=_full_evidence(),
                )
            )
        ]
    )
    assert report["schema_version"] == "position-audit-v2/1.1"
    row = report["results"][0]
    for field_name in (
        "position_proof_path",
        "anchor_semantics_status",
        "artifact_sync_status",
    ):
        assert field_name in row


def test_existing_serialized_fields_are_not_reinterpreted():
    """既存 field を黙って作り替えない（§27）。"""
    result = audit.evaluate(
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence())
    )
    row = result.to_dict()
    for field_name in (
        "candidate_id",
        "production_id",
        "name_jp",
        "join_status",
        "spreadsheet_join_status",
        "audit_status",
        "reason_codes",
        "stored_address",
        "official_address",
        "stored_latitude",
        "stored_longitude",
        "seed_latitude",
        "seed_longitude",
        "primary_latitude",
        "primary_longitude",
        "coordinate_delta_m",
        "primary_source_type",
        "primary_source_url",
        "corroboration_sources",
        "existing_resolution_record",
        "verified_at",
    ):
        assert field_name in row, field_name
    assert row["audit_status"] in {audit.AUTO_PASS, audit.REVIEW, audit.HOLD}


# ---------------------------------------------------------------------------
# 決定的 serialization（新 field を含む）
# ---------------------------------------------------------------------------


def test_new_contract_fields_are_byte_stable():
    items = [
        _item(spreadsheet=_bare_sheet(), primary_position_evidence=_full_evidence()),
        _item(
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(status="FETCH_FAILED"),
            existing_resolution=_resolution(),
        ),
        _item(
            seed=audit.SeedPosition(latitude=34.9, longitude=138.9),
            spreadsheet=_bare_sheet(),
            primary_position_evidence=_full_evidence(),
            anchor_semantics_status=audit.ANCHOR_SEMANTICS_REVIEW_REQUIRED,
        ),
    ]
    first = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    second = audit.dump_json(audit.build_report([audit.evaluate(i) for i in items]))
    assert first.encode("utf-8") == second.encode("utf-8")

    decoded = json.loads(first)
    assert [r["position_proof_path"] for r in decoded["results"]] == [
        audit.PROOF_PRIMARY_EVIDENCE,
        audit.PROOF_RESOLUTION_FALLBACK,
        audit.PROOF_PRIMARY_EVIDENCE,
    ]
    assert [r["artifact_sync_status"] for r in decoded["results"]] == [
        audit.ARTIFACT_SYNCED,
        audit.ARTIFACT_SYNCED,
        audit.ARTIFACT_DRIFT,
    ]
    # reason_codes は常に sorted（集合順に依存しない）。
    for row in decoded["results"]:
        assert row["reason_codes"] == sorted(row["reason_codes"])


def test_reason_code_ordering_is_independent_of_input_ordering():
    """同一入力なら reason-code 順序も安定する。"""
    item = _item(
        seed=audit.SeedPosition(latitude=34.9, longitude=138.9),
        spreadsheet=_bare_sheet(),
        primary_position_evidence=_full_evidence(poi_candidate_count=5),
        anchor_semantics_status="unrecognised",
    )
    runs = [audit.evaluate(item).reason_codes for _ in range(5)]
    assert all(run == runs[0] for run in runs)
    assert runs[0] == sorted(runs[0])


# ---------------------------------------------------------------------------
# Zero-write guarantee — P2-B01 で追加した経路の追加防御
# ---------------------------------------------------------------------------

# evaluate() 内で禁止する I/O 呼び出し。評価は純粋な in-memory 変換であり、
# Anchor Semantics / Artifact Synchronization を足したあとも file / network /
# DB に触れてはならない。
FORBIDDEN_EVALUATE_CALL_ATTRS = frozenset(
    {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "glob",
        "iterdir",
        "exists",
        "mkdir",
        "unlink",
        "urlopen",
        "get",
        "post",
        "request",
    }
)


def _function_node(name: str):
    import ast

    tree = ast.parse(AUDIT_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


def test_evaluate_performs_no_io():
    """新しい評価層（anchor / proof path / artifact sync）が I/O を持たない。"""
    import ast

    node = _function_node("evaluate")
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            assert child.func.attr not in FORBIDDEN_EVALUATE_CALL_ATTRS, (
                child.func.attr
            )
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
            assert child.func.id != "open", "evaluate() must not open files"


def test_new_input_dataclasses_are_frozen():
    """新しい入力 model も immutable（評価が入力を書き換えない）。"""
    import dataclasses

    for cls in (
        audit.CandidateMasterPosition,
        audit.ShrinePositionAuditInput,
        audit.PrimaryPositionEvidence,
    ):
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen, cls.__name__

    master = audit.CandidateMasterPosition(latitude=35.0, longitude=139.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        master.latitude = 1.0  # type: ignore[misc]


def test_evaluate_does_not_mutate_its_input():
    """同じ入力 object を再評価しても結果が変わらない（純関数）。"""
    item = _item(
        spreadsheet=_bare_sheet(),
        candidate_master=audit.CandidateMasterPosition(latitude=34.5, longitude=138.5),
        primary_position_evidence=_full_evidence(),
        existing_resolution=_resolution(),
    )
    before = audit.evaluate(item).to_dict()
    again = audit.evaluate(item).to_dict()
    assert before == again


def test_artifact_sync_layer_has_no_new_write_path():
    """artifact sync は snapshot file を読み直さず、既存入力だけを使う。"""
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
    # P2-B01 後も書き込み先は report file 2つだけ。
    assert sorted(set(write_targets)) == ["args.output_json", "args.output_md"]
