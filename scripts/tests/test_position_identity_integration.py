"""Position / Production Identity Integration（P2-B04）の regression。

中心的な不変条件を固定する。

```text
B03 SAME_SUPPORTED
!=
Seed ↔ Production exact identity
```

本 file は DB・Django・ネットワークをいっさい必要としない。
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "position_identity_integration.py"
IDENTITY_MODULE_PATH = REPO_ROOT / "scripts" / "shrine_identity_evidence.py"
ADDRESS_MODULE_PATH = REPO_ROOT / "scripts" / "japanese_address_normalization.py"
AUDIT_PATH = REPO_ROOT / "scripts" / "audit_shrine_positions_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("position_identity_integration", MODULE_PATH)
audit = _load("audit_shrine_positions_v2", AUDIT_PATH)
sie = adapter.identity_evidence


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


def _assessment(status: str):
    """B03 の評価結果を、その status になる入力から実際に作る。"""
    address_pairs = {
        "SAME_SUPPORTED": ("日本、〒101-0021 東京都千代田区外神田２－１６－２",
                           "東京都千代田区外神田2-16-2"),
        "REVIEW_REQUIRED": ("埼玉県某市大字石神976", "埼玉県某市石神976"),
        "INSUFFICIENT": ("○○県○○市○○町無番地", "東京都千代田区外神田2-16-2"),
        "CONFLICT": ("東京都千代田区外神田2-16-2", "東京都千代田区外神田2-16-2"),
    }
    left, right = address_pairs[status]
    kwargs = dict(
        address_comparison=sie.compare_addresses(left, right),
        name_identity_status=sie.NAME_EXACT_MATCH,
    )
    if status == "SAME_SUPPORTED":
        kwargs["official_source_entity_status"] = sie.OFFICIAL_SOURCE_SAME
    elif status == "REVIEW_REQUIRED":
        kwargs["official_source_entity_status"] = sie.OFFICIAL_SOURCE_SAME
    elif status == "CONFLICT":
        kwargs["place_id_status"] = sie.PLACE_ID_DIFFERENT
    result = sie.assess_identity_evidence(**kwargs)
    assert result.identity_evidence_status == status, (status, result)
    return result


def _audit_item(**overrides):
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
        spreadsheet=None,
        spreadsheet_join_status=audit.SHEET_JOIN_NONE,
        seed_production_join_status=audit.JOIN_MATCH_EXACT,
        anchor_semantics_status=audit.ANCHOR_SEMANTICS_CONFIRMED,
    )
    values.update(overrides)
    return audit.ShrinePositionAuditInput(**values)


def _evidence(**overrides):
    values = dict(
        status="OK",
        source_type="shrine_official",
        source_url="https://example.invalid/shrine/access",
        latitude=35.0,
        longitude=139.0,
        entity_match="SAME",
        poi_candidate_count=1,
        verified_at="2026-09-17",
    )
    values.update(overrides)
    return audit.PrimaryPositionEvidence(**values)


def _resolution(**overrides):
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


# ---------------------------------------------------------------------------
# 既存 exact join の不変性
# ---------------------------------------------------------------------------


def test_join_match_exact_still_means_raw_exact_single_row():
    """`JOIN_MATCH_EXACT` の意味を変えていない。"""
    status, row, duplicates = audit.join_seed_to_production(
        SEED_ROW, [_production_row()]
    )
    assert status == audit.JOIN_MATCH_EXACT
    assert row["id"] == 500
    assert duplicates == ()

    # 正規化で救わない。
    for overrides in (
        {"name_jp": "契約テスト神社 "},
        {"address": "東京都千代田区１−１"},
        {"address": "東京都千代田区1丁目1番"},
    ):
        status, row, _ = audit.join_seed_to_production(
            SEED_ROW, [_production_row(**overrides)]
        )
        assert status == audit.JOIN_MISSING_PRODUCTION, overrides
        assert row is None

    # 複数行は exact にしない。
    status, row, duplicates = audit.join_seed_to_production(
        SEED_ROW, [_production_row(), _production_row(id=501)]
    )
    assert status == audit.JOIN_DUPLICATE_MATCH
    assert duplicates == (500, 501)


def test_adapter_mirrors_the_position_audit_join_constant():
    assert adapter.JOIN_MATCH_EXACT == audit.JOIN_MATCH_EXACT


def test_identity_status_vocabulary_matches_between_adapter_and_audit():
    assert (
        adapter.SEED_PRODUCTION_IDENTITY_STATUSES
        == audit.SEED_PRODUCTION_IDENTITY_STATUSES
    )
    assert adapter.SEED_PRODUCTION_IDENTITY_STATUSES == {
        "EXACT",
        "SAME_SUPPORTED",
        "REVIEW_REQUIRED",
        "CONFLICT",
        "INSUFFICIENT",
        "NOT_EVALUATED",
    }


# ---------------------------------------------------------------------------
# Golden Cases
# ---------------------------------------------------------------------------


def test_b04_gc01_exact_raw_join_is_exact_identity():
    result = adapter.integrate_position_identity(
        join_status=audit.JOIN_MATCH_EXACT, production_id=500
    )
    assert result.join_status == audit.JOIN_MATCH_EXACT
    assert result.identity_status == adapter.IDENTITY_EXACT
    assert result.identity_is_exact is True
    assert result.production_id == 500
    assert result.identity_review_reasons == ()

    audited = audit.evaluate(
        _audit_item(
            seed_production_identity_status=result.identity_status,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.seed_production_identity_status == adapter.IDENTITY_EXACT
    assert audit.RC_SEED_PRODUCTION_EXACT in audited.reason_codes
    assert audited.audit_status == audit.AUTO_PASS


def test_b04_gc02_exact_miss_with_same_supported_is_review_not_exact():
    result = adapter.integrate_position_identity(
        join_status=audit.JOIN_MISSING_PRODUCTION,
        # 候補 id を渡しても非 exact join では採用してはならない。
        production_id=500,
        identity_assessment=_assessment("SAME_SUPPORTED"),
    )
    # join は未解決のまま。
    assert result.join_status == audit.JOIN_MISSING_PRODUCTION
    assert result.identity_status == adapter.IDENTITY_SAME_SUPPORTED
    assert result.identity_is_exact is False
    # 非 exact で Production 行を自動採用しない。
    assert result.production_id is None
    assert result.identity_review_reasons == ("IDENTITY_EVIDENCE_SAME_SUPPORTED",)

    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=result.identity_status,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.REVIEW
    assert audited.seed_production_identity_status == adapter.IDENTITY_SAME_SUPPORTED
    # exact identity にはならない。
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes
    assert audit.RC_IDENTITY_EVIDENCE_SAME_SUPPORTED in audited.reason_codes
    # identity 経由で AUTO_PASS しない。
    assert audited.audit_status != audit.AUTO_PASS


@pytest.mark.parametrize(
    ("case_id", "evidence_status", "identity_status", "reason_code"),
    [
        (
            "B04-GC03",
            "REVIEW_REQUIRED",
            "REVIEW_REQUIRED",
            "IDENTITY_EVIDENCE_REVIEW_REQUIRED",
        ),
        (
            "B04-GC04",
            "INSUFFICIENT",
            "INSUFFICIENT",
            "IDENTITY_EVIDENCE_INSUFFICIENT",
        ),
        ("B04-GC05", "CONFLICT", "CONFLICT", "IDENTITY_EVIDENCE_CONFLICT"),
    ],
)
def test_b04_gc03_gc04_gc05_non_exact_identity_evidence_is_review(
    case_id, evidence_status, identity_status, reason_code
):
    """REVIEW_REQUIRED / INSUFFICIENT / CONFLICT はいずれも REVIEW。

    B03 の CONFLICT 単独では新しい HOLD を作らない（P2-B04 v1）。
    """
    result = adapter.integrate_position_identity(
        join_status=audit.JOIN_MISSING_PRODUCTION,
        identity_assessment=_assessment(evidence_status),
    )
    assert result.identity_status == identity_status, case_id
    assert result.identity_is_exact is False, case_id
    assert result.identity_review_reasons == (reason_code,), case_id

    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=identity_status,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.REVIEW, case_id
    assert audited.audit_status != audit.HOLD, case_id
    assert reason_code in audited.reason_codes, case_id
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes, case_id


def test_b04_gc05_conflict_does_not_become_hold_or_primary_entity_evidence():
    """Seed ↔ Production identity conflict を Primary entity 証拠と同一視しない。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=adapter.IDENTITY_CONFLICT,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.REVIEW
    for code in (
        audit.RC_PRIMARY_SOURCE_WRONG_ENTITY,
        audit.RC_PRIMARY_SOURCE_NON_SHRINE_ENTITY,
    ):
        assert code not in audited.reason_codes
    assert audit.RC_IDENTITY_EVIDENCE_CONFLICT not in audit.HOLD_REASON_CODES

    # Primary 側の entity 証拠は依然として独立に HOLD を作る。
    stronger = audit.evaluate(
        _audit_item(
            seed_production_identity_status=adapter.IDENTITY_EXACT,
            primary_position_evidence=_evidence(entity_match="DIFFERENT"),
        )
    )
    assert stronger.audit_status == audit.HOLD
    assert audit.RC_PRIMARY_SOURCE_WRONG_ENTITY in stronger.reason_codes


def test_b04_gc06_same_supported_does_not_enable_resolution_fallback():
    """Resolution fallback は exact identity を要求し続ける（P2-A02）。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert audited.position_proof_path != audit.PROOF_RESOLUTION_FALLBACK
    assert audited.position_proof_path == audit.PROOF_NONE
    assert audit.RC_RESOLUTION_RECORD_REUSED not in audited.reason_codes
    assert audited.audit_status == audit.REVIEW

    # exact identity なら従来どおり fallback が成立する。
    exact = audit.evaluate(
        _audit_item(
            seed_production_identity_status=adapter.IDENTITY_EXACT,
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert exact.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert audit.RC_RESOLUTION_RECORD_REUSED in exact.reason_codes


def test_b04_gc06_same_supported_blocks_fallback_even_with_a_production_row():
    """Production 行があっても非 exact identity では fallback を開かない。

    `identity_is_exact` は exact join と `IDENTITY_EXACT` の **両方**を
    要求する。SAME_SUPPORTED が片方でも満たしてはならない。
    """
    item = _audit_item(
        # Production 行も座標も揃っているが、join は exact ではない。
        production=audit.ProductionPosition(latitude=35.0, longitude=139.0),
        seed_production_join_status=audit.JOIN_IDENTITY_REVIEW_REQUIRED,
        seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
        primary_position_evidence=None,
        existing_resolution=_resolution(),
    )
    audited = audit.evaluate(item)
    assert audited.position_proof_path == audit.PROOF_NONE
    assert audit.RC_RESOLUTION_RECORD_REUSED not in audited.reason_codes
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes
    assert audited.audit_status == audit.REVIEW
    # Seed/Production 座標差の観測も exact identity 前提なので出さない。
    assert audit.RC_SEED_PRODUCTION_COORDINATE_DIFFERS not in audited.reason_codes

    # 同じ入力で join が exact なら fallback が開く（対比）。
    exact = audit.evaluate(
        _audit_item(
            production=audit.ProductionPosition(latitude=35.0, longitude=139.0),
            seed_production_join_status=audit.JOIN_MATCH_EXACT,
            primary_position_evidence=None,
            existing_resolution=_resolution(),
        )
    )
    assert exact.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK


def test_b04_gc07_same_supported_keeps_artifact_sync_unknown():
    """非 exact join では Production を artifact 参照基準にしない。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.artifact_sync_status == audit.ARTIFACT_UNKNOWN
    assert audit.RC_ARTIFACT_SYNC_INPUT_UNAVAILABLE in audited.reason_codes
    # 非 exact identity から Production drift を出さない。
    assert audit.RC_ARTIFACT_PRODUCTION_DRIFT not in audited.reason_codes
    for code in (
        audit.RC_ARTIFACT_BASE_SEED_DRIFT,
        audit.RC_ARTIFACT_CANDIDATE_MASTER_DRIFT,
        audit.RC_ARTIFACT_RESOLUTION_DRIFT,
    ):
        assert code not in audited.reason_codes


def test_b04_gc08_exact_join_resolution_fallback_behaviour_is_unchanged():
    """MATCH_EXACT 時の Resolution fallback 挙動が従来のまま。"""
    reused = audit.evaluate(
        _audit_item(primary_position_evidence=None, existing_resolution=_resolution())
    )
    assert reused.position_proof_path == audit.PROOF_RESOLUTION_FALLBACK
    assert audit.RC_RESOLUTION_RECORD_REUSED in reused.reason_codes
    assert reused.audit_status == audit.AUTO_PASS

    # provenance 欠落なら従来どおり fail closed。
    incomplete = audit.evaluate(
        _audit_item(
            primary_position_evidence=None,
            existing_resolution=_resolution(position_source_url=None),
        )
    )
    assert incomplete.audit_status == audit.HOLD
    assert audit.RC_RESOLUTION_SOURCE_URL_MISSING in incomplete.reason_codes


def test_b04_gc09_exact_join_artifact_sync_behaviour_is_unchanged():
    """MATCH_EXACT 時の Artifact Sync 挙動が従来のまま。"""
    synced = audit.evaluate(_audit_item(primary_position_evidence=_evidence()))
    assert synced.artifact_sync_status == audit.ARTIFACT_SYNCED

    drifted = audit.evaluate(
        _audit_item(
            seed=audit.SeedPosition(latitude=34.9, longitude=138.9),
            primary_position_evidence=_evidence(),
        )
    )
    assert drifted.artifact_sync_status == audit.ARTIFACT_DRIFT
    assert audit.RC_ARTIFACT_BASE_SEED_DRIFT in drifted.reason_codes
    # Position の正しさとは独立のまま。
    assert drifted.audit_status == audit.AUTO_PASS


def test_b04_gc10_b04_depends_on_b03_only_and_never_directly_on_b02():
    """依存グラフ: B04 -> B03 -> B02。B04 は B02 を直接読まない。"""
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "japanese_address_normalization" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            assert "japanese_address_normalization" not in (node.module or "")

    # B02 の module 名・path・住所語彙を一切持たない。
    for forbidden in (
        "japanese_address_normalization",
        "ADDRESS_EXACT_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
        "compare_addresses",
        "lexical_normalize",
    ):
        assert forbidden not in source, forbidden

    # B03 は canonical path から読んでいる。
    assert adapter.identity_evidence.__file__ == str(IDENTITY_MODULE_PATH)
    # 推移的には B02 に到達する（B03 経由）。
    assert adapter.identity_evidence.address_contract.__file__ == str(
        ADDRESS_MODULE_PATH
    )


def test_b04_gc11_b03_direct_consumers_are_exactly_the_b04_adapter():
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == IDENTITY_MODULE_PATH:
            continue
        if "shrine_identity_evidence" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert set(callers) == {"scripts/position_identity_integration.py"}, callers


def test_b04_gc11_b02_direct_consumers_remain_exactly_b03():
    """B02 の allowlist は変えない。B04 を B02 の allowlist に足さない。"""
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == ADDRESS_MODULE_PATH:
            continue
        if "japanese_address_normalization" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert set(callers) == {"scripts/shrine_identity_evidence.py"}, callers


def test_b04_gc12_deterministic_byte_stable_result():
    kwargs = dict(
        join_status=audit.JOIN_MISSING_PRODUCTION,
        identity_assessment=_assessment("SAME_SUPPORTED"),
    )
    runs = [
        adapter.integrate_position_identity(**kwargs).to_dict() for _ in range(5)
    ]
    assert all(run == runs[0] for run in runs)
    serialized = {json.dumps(run, ensure_ascii=False, sort_keys=True) for run in runs}
    assert len(serialized) == 1

    audited = [
        audit.evaluate(
            _audit_item(
                production=None,
                seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
                seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
                primary_position_evidence=_evidence(),
            )
        ).to_dict()
        for _ in range(5)
    ]
    assert all(row == audited[0] for row in audited)
    assert (
        len({json.dumps(row, ensure_ascii=False, sort_keys=True) for row in audited})
        == 1
    )


# ---------------------------------------------------------------------------
# 中心的な不変条件
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "evidence_status", ["SAME_SUPPORTED", "REVIEW_REQUIRED", "CONFLICT", "INSUFFICIENT"]
)
@pytest.mark.parametrize(
    "join_status",
    ["MISSING_PRODUCTION", "MISSING_SEED", "DUPLICATE_MATCH", "IDENTITY_REVIEW_REQUIRED"],
)
def test_no_identity_evidence_ever_produces_exact_identity(
    evidence_status, join_status
):
    """どの evidence も、どの非 exact join も exact identity を生まない。"""
    result = adapter.integrate_position_identity(
        join_status=join_status, identity_assessment=_assessment(evidence_status)
    )
    assert result.identity_status != adapter.IDENTITY_EXACT
    assert result.identity_is_exact is False
    assert result.join_status == join_status


def test_supplied_exact_on_a_non_exact_join_is_refused():
    """非 exact join へ `EXACT` を持ち込んでも採用しない（fail safe）。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=audit.IDENTITY_EXACT,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes
    # 未評価なので従来どおりの identity HOLD に戻る。
    assert audited.audit_status == audit.HOLD
    assert audit.RC_MISSING_PRODUCTION in audited.reason_codes


def test_unknown_identity_status_fails_safe_to_not_evaluated():
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status="PROBABLY_THE_SAME",
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED
    assert audited.audit_status == audit.HOLD


def test_identity_evidence_codes_never_belong_to_hold():
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audit.HOLD_REASON_CODES, code
        assert code in audit.REVIEW_REASON_CODES, code
        assert audit._classify({code}) == audit.REVIEW, code
    # 未評価は観測のみ。
    assert audit.RC_IDENTITY_EVIDENCE_NOT_EVALUATED not in audit.HOLD_REASON_CODES
    assert audit.RC_IDENTITY_EVIDENCE_NOT_EVALUATED not in audit.REVIEW_REASON_CODES
    assert audit._classify({audit.RC_IDENTITY_EVIDENCE_NOT_EVALUATED}) == audit.AUTO_PASS


def test_identity_codes_are_separate_from_seed_production_exact():
    assert audit.RC_SEED_PRODUCTION_EXACT not in audit.IDENTITY_EVIDENCE_REVIEW_CODES
    assert audit.RC_SEED_PRODUCTION_EXACT == "SEED_PRODUCTION_EXACT"
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code.startswith("IDENTITY_EVIDENCE_")


def test_same_supported_is_not_auto_pass_evidence():
    """identity 経由で AUTO_PASS へ到達しないこと。"""
    for primary in (None, _evidence()):
        audited = audit.evaluate(
            _audit_item(
                production=None,
                seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
                seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
                primary_position_evidence=primary,
                existing_resolution=_resolution(),
            )
        )
        assert audited.audit_status != audit.AUTO_PASS


def test_canonical_hold_still_wins_over_identity_evidence():
    """canonical HOLD は identity 軸より優先される。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            seed_production_identity_status=adapter.IDENTITY_SAME_SUPPORTED,
            primary_position_evidence=_evidence(),
            existing_resolution=audit.ExistingResolution(
                record_path="docs/audit/shrine-position/example.md",
                position_status="HOLD_POSITION_REVIEW",
            ),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audit.RC_POSITION_CONTRACT_HOLD_RECORD in audited.reason_codes


# ---------------------------------------------------------------------------
# 候補探索の境界
# ---------------------------------------------------------------------------


def test_adapter_never_searches_for_production_candidates():
    """B03 を Production 候補探索エンジンとして使わない。"""
    result = adapter.integrate_position_identity(
        join_status=audit.JOIN_MISSING_PRODUCTION
    )
    assert result.join_status == audit.JOIN_MISSING_PRODUCTION
    assert result.identity_status == adapter.IDENTITY_NOT_EVALUATED
    assert result.production_id is None
    assert result.identity_review_reasons == ("IDENTITY_EVIDENCE_NOT_EVALUATED",)


def test_build_inputs_uses_identity_only_when_explicitly_supplied():
    candidate = {
        "candidate_id": "wave0-999",
        "candidate_name": SEED_ROW["name_jp"],
        "official_name": SEED_ROW["name_jp"],
        "official_address": SEED_ROW["address"],
        "build_batch": "W0-TEST",
        "candidate_status": "IMPORTED",
        "latitude": 35.0,
        "longitude": 139.0,
    }
    # 未供給なら NOT_EVALUATED（既存挙動と同じ）。
    items = audit.build_inputs(
        seed_rows=[SEED_ROW],
        production_rows=[],
        spreadsheet_rows=None,
        candidates=[candidate],
        resolution_records={},
    )
    assert items[0].seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED
    assert audit.evaluate(items[0]).audit_status == audit.HOLD

    # 明示的に供給したときだけ identity 軸が動く。
    items = audit.build_inputs(
        seed_rows=[SEED_ROW],
        production_rows=[],
        spreadsheet_rows=None,
        candidates=[candidate],
        resolution_records={},
        identity_statuses_by_candidate={"wave0-999": adapter.IDENTITY_SAME_SUPPORTED},
    )
    assert items[0].seed_production_identity_status == adapter.IDENTITY_SAME_SUPPORTED
    result = audit.evaluate(items[0])
    assert result.audit_status == audit.REVIEW
    assert audit.RC_IDENTITY_EVIDENCE_SAME_SUPPORTED in result.reason_codes


def test_adapter_does_not_perform_io_or_search():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_imports = {
        "django",
        "psycopg",
        "psycopg2",
        "sqlite3",
        "requests",
        "httpx",
        "urllib",
        "http",
        "socket",
        "os",
        "subprocess",
        "difflib",
        "random",
    }
    forbidden_calls = {
        "save",
        "create",
        "execute",
        "cursor",
        "connect",
        "urlopen",
        "write_text",
        "write_bytes",
        "getenv",
        "environ",
        "glob",
        "rglob",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls, node.func.attr
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec"}


def test_integration_core_is_pure():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "integrate_position_identity":
            target = node
    assert target is not None
    for child in ast.walk(target):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            assert child.func.attr not in {
                "read_text",
                "exec_module",
                "spec_from_file_location",
                "module_from_spec",
                "glob",
                "exists",
            }


def test_adapter_result_is_immutable():
    import dataclasses

    result = adapter.integrate_position_identity(
        join_status=audit.JOIN_MATCH_EXACT, production_id=500
    )
    assert dataclasses.is_dataclass(result)
    assert type(result).__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.identity_status = adapter.IDENTITY_SAME_SUPPORTED  # type: ignore[misc]


def test_b04_is_not_wired_into_any_further_consumer():
    """**暫定の layer-boundary 不変条件**（P2-B04 時点）。

    現時点で B04 adapter を消費する層は存在しない。次の層が導入される
    ときは、B02 / B03 と同じ厳密 allowlist 方式へ置き換えること。

    ```python
    SANCTIONED_CONSUMERS = {"scripts/<next layer>.py"}
    assert set(callers) == SANCTIONED_CONSUMERS, callers
    ```

    `<=` ではなく `==` を使う。推移的依存は上流の allowlist に載せない。
    """
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == MODULE_PATH:
            continue
        if "position_identity_integration" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert callers == [], callers
