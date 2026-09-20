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


def _integration(join_status: str, evidence_status: str | None = None):
    """本物の B04 integration result を作る（信頼境界を通す唯一の経路）。"""
    return adapter.integrate_position_identity(
        join_status=join_status,
        identity_assessment=(
            _assessment(evidence_status) if evidence_status else None
        ),
    )


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
            position_identity_integration=result,
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
            position_identity_integration=result,
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
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, evidence_status
            ),
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
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "CONFLICT"
            ),
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
            position_identity_integration=_integration(audit.JOIN_MATCH_EXACT),
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
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            ),
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
            position_identity_integration=_integration(audit.JOIN_MATCH_EXACT),
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
        position_identity_integration=_integration(
            audit.JOIN_IDENTITY_REVIEW_REQUIRED, "SAME_SUPPORTED"
        ),
        primary_position_evidence=None,
        existing_resolution=_resolution(),
    )
    audited = audit.evaluate(item)
    assert audited.position_proof_path == audit.PROOF_NONE
    assert audit.RC_RESOLUTION_RECORD_REUSED not in audited.reason_codes
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes
    # B03 evidence は identity 軸として共存するが exact identity にしない。
    assert audited.seed_production_identity_status == adapter.IDENTITY_SAME_SUPPORTED
    # `JOIN_IDENTITY_REVIEW_REQUIRED` の既存 identity 状態は維持される。
    assert audit.RC_IDENTITY_NOT_EXACT in audited.reason_codes
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
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            ),
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


# B03 を **直接** 消費してよい module の厳密な集合。
#
# B04 導入時点では B04 adapter だけだったが、real-data supply layer の
# 追加でこの不変条件は設計どおり更新された（supply layer は B03 の
# `assess_identity_evidence()` を直接呼ぶ必要がある）。
# canonical な allowlist は `scripts/tests/test_shrine_identity_evidence.py`
# が持ち、ここではそれと同値であることを固定する。
B03_SANCTIONED_CONSUMERS = {
    "scripts/position_identity_integration.py",
    "scripts/build_position_identity_evidence.py",
}


def test_b04_gc11_b03_direct_consumers_are_exactly_the_sanctioned_set():
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == IDENTITY_MODULE_PATH:
            continue
        if "shrine_identity_evidence" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert set(callers) == B03_SANCTIONED_CONSUMERS, callers


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
                position_identity_integration=_integration(
                    audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
                ),
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
            position_identity_integration=audit.IDENTITY_EXACT,
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
            position_identity_integration="PROBABLY_THE_SAME",
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
                position_identity_integration=_integration(
                    audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
                ),
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
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            ),
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
    assert items[0].position_identity_integration is None
    assert (
        audit.evaluate(items[0]).seed_production_identity_status
        == audit.IDENTITY_NOT_EVALUATED
    )
    assert audit.evaluate(items[0]).audit_status == audit.HOLD

    # 明示的に供給したときだけ identity 軸が動く。
    items = audit.build_inputs(
        seed_rows=[SEED_ROW],
        production_rows=[],
        spreadsheet_rows=None,
        candidates=[candidate],
        resolution_records={},
        identity_integrations_by_candidate={
            "wave0-999": _integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            )
        },
    )
    assert isinstance(
        items[0].position_identity_integration,
        adapter.PositionIdentityIntegrationResult,
    )
    result = audit.evaluate(items[0])
    assert result.seed_production_identity_status == adapter.IDENTITY_SAME_SUPPORTED
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


# B04 integration boundary を **直接** 消費してよい module の厳密な集合。
#
# Position Audit は identity evidence に B04 を通してのみ触れる。
# B03 / B02 を直接 import / load してはならない（推移的依存は上流の
# allowlist に載せない）。
#
# supply layer（real-data identity evidence）は本物の
# `PositionIdentityIntegrationResult` を構成する必要があるため、B04 を
# 直接消費する。互換 object の捏造を避けるための sanction である。
B04_SANCTIONED_CONSUMERS = {
    "scripts/audit_shrine_positions_v2.py",
    "scripts/build_position_identity_evidence.py",
}


def test_b04_has_exactly_the_sanctioned_direct_consumers():
    """B04 の直接 consumer が allowlist と **完全一致** すること。

    ```text
    Position Audit        -> B04 integration boundary -> B03 -> B02
    real-data supply layer -> B04 integration boundary
    ```

    `<=` ではなく `==` を使う（必要な依存が消えたことも検出するため）。
    """
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == MODULE_PATH:
            continue
        if "position_identity_integration" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert set(callers) == B04_SANCTIONED_CONSUMERS, callers


def test_position_audit_never_directly_depends_on_b03_or_b02():
    """Position Audit は B03 / B02 を直接 import / load しない。"""
    source = AUDIT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "shrine_identity_evidence" not in alias.name
                assert "japanese_address_normalization" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "shrine_identity_evidence" not in module
            assert "japanese_address_normalization" not in module
    for forbidden in (
        "shrine_identity_evidence",
        "japanese_address_normalization",
        "compare_addresses",
        "assess_identity_evidence",
    ):
        assert forbidden not in source, forbidden

    # 読み込むのは B04 だけ。
    assert audit.identity_integration.__file__ == str(MODULE_PATH)
    # B03 / B02 へは B04 経由で推移的に到達する。
    assert audit.identity_integration.identity_evidence.__file__ == str(
        IDENTITY_MODULE_PATH
    )


# ---------------------------------------------------------------------------
# 構造的 join 失敗は B03 evidence で置き換えない（review correction）
# ---------------------------------------------------------------------------

STRUCTURAL_HOLD_JOINS = (
    ("MISSING_SEED", "JOIN_MISSING_SEED", "RC_MISSING_SEED"),
    ("DUPLICATE_MATCH", "JOIN_DUPLICATE_MATCH", "RC_DUPLICATE_PRODUCTION_IDENTITY"),
)


@pytest.mark.parametrize(("label", "join_attr", "code_attr"), STRUCTURAL_HOLD_JOINS)
@pytest.mark.parametrize(
    "identity_status",
    ["SAME_SUPPORTED", "REVIEW_REQUIRED", "CONFLICT", "INSUFFICIENT"],
)
def test_structural_join_failures_stay_hold_even_with_identity_evidence(
    label, join_attr, code_attr, identity_status
):
    """B03 evidence は構造的 join 失敗を修復しない。

    * `JOIN_MISSING_SEED`      Seed 側の identity anchor 不在
    * `JOIN_DUPLICATE_MATCH`   exact Production 行が複数

    B03 は Seed 不在を修復できず、duplicate resolution 機構でもない。
    複数の exact Production 行から1つを選んではならない。
    """
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=getattr(audit, join_attr),
            position_identity_integration=_integration(
                getattr(audit, join_attr), identity_status
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD, (label, identity_status)
    assert getattr(audit, code_attr) in audited.reason_codes, label
    # identity 軸としては記録されるが、HOLD を置き換えない。
    assert audited.seed_production_identity_status == identity_status
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audited.reason_codes, (label, code)
    # exact identity にはならない。
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes


@pytest.mark.parametrize(
    "identity_status",
    ["SAME_SUPPORTED", "REVIEW_REQUIRED", "CONFLICT", "INSUFFICIENT"],
)
def test_production_snapshot_unavailable_is_unchanged_by_identity_evidence(
    identity_status,
):
    """snapshot 不在は B03 evidence で代替されない。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE,
            production_snapshot_available=False,
            position_identity_integration=_integration(
                audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE, identity_status
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audit.RC_PRODUCTION_SNAPSHOT_UNAVAILABLE in audited.reason_codes
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audited.reason_codes, code


@pytest.mark.parametrize(
    "identity_status",
    ["SAME_SUPPORTED", "REVIEW_REQUIRED", "CONFLICT", "INSUFFICIENT"],
)
def test_identity_review_required_join_keeps_its_existing_state(identity_status):
    """`JOIN_IDENTITY_REVIEW_REQUIRED` は既存の identity 状態を保つ。

    B03 evidence は `seed_production_identity_status` として共存するが、

    * exact identity には変えない
    * B03 が `CONFLICT` でも **新しい** HOLD 経路を作らない
      （HOLD は既存の `RC_IDENTITY_NOT_EXACT` 由来のまま）
    """
    audited = audit.evaluate(
        _audit_item(
            seed_production_join_status=audit.JOIN_IDENTITY_REVIEW_REQUIRED,
            position_identity_integration=_integration(
                audit.JOIN_IDENTITY_REVIEW_REQUIRED, identity_status
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.seed_production_identity_status == identity_status
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes
    # B03 由来の新しい HOLD code は増えていない。
    assert audit.RC_IDENTITY_NOT_EXACT in audited.reason_codes
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audit.HOLD_REASON_CODES, code


def test_only_missing_production_gets_the_hold_to_review_transition():
    """承認された HOLD → REVIEW 転換は `JOIN_MISSING_PRODUCTION` だけ。"""
    transitioned = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert transitioned.audit_status == audit.REVIEW
    assert audit.RC_IDENTITY_EVIDENCE_SAME_SUPPORTED in transitioned.reason_codes
    # raw join の事実は join_status に残る。
    assert transitioned.join_status == audit.JOIN_MISSING_PRODUCTION

    # 他の非 exact join は転換しない。
    for join_status in (
        audit.JOIN_MISSING_SEED,
        audit.JOIN_DUPLICATE_MATCH,
        audit.JOIN_IDENTITY_REVIEW_REQUIRED,
    ):
        audited = audit.evaluate(
            _audit_item(
                production=None,
                seed_production_join_status=join_status,
                position_identity_integration=_integration(
                    join_status, "SAME_SUPPORTED"
                ),
                primary_position_evidence=_evidence(),
            )
        )
        assert audited.audit_status == audit.HOLD, join_status


def test_missing_production_without_identity_evidence_is_unchanged():
    """B03 未評価なら `JOIN_MISSING_PRODUCTION` は従来どおり HOLD。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audit.RC_MISSING_PRODUCTION in audited.reason_codes
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED


# ---------------------------------------------------------------------------
# 信頼境界の Golden Cases（B04-GC19 〜 GC26）
#
# HOLD → REVIEW の転換を起動できるのは、B04 adapter が返した
# `PositionIdentityIntegrationResult` の実体だけである。status 文字列を
# 直接渡しても起動しない。
# ---------------------------------------------------------------------------


def test_b04_gc19_raw_status_string_cannot_suppress_missing_production_hold():
    """生の status 文字列では HOLD を抑止できない（provenance 不足）。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            # B04 を通していない生文字列。
            position_identity_integration="SAME_SUPPORTED",
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audit.RC_MISSING_PRODUCTION in audited.reason_codes
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audited.reason_codes, code


def test_b04_gc19_look_alike_object_cannot_suppress_hold():
    """同じ形の別 object でも起動しない（型で認証する）。"""
    from dataclasses import dataclass as _dataclass

    @_dataclass(frozen=True)
    class FakeIntegration:
        join_status: str = "MISSING_PRODUCTION"
        identity_status: str = "SAME_SUPPORTED"
        production_id: int | None = None
        duplicate_production_ids: tuple = ()
        identity_review_reasons: tuple = ()

    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            position_identity_integration=FakeIntegration(),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audit.RC_MISSING_PRODUCTION in audited.reason_codes
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED


def test_b04_gc19_integration_for_a_different_join_is_not_reused():
    """別 join に対する integration result を流用しない。"""
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            position_identity_integration=_integration(
                audit.JOIN_IDENTITY_REVIEW_REQUIRED, "SAME_SUPPORTED"
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD
    assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED


def test_b04_gc20_valid_integration_same_supported_is_review():
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "SAME_SUPPORTED"
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.REVIEW
    assert audited.seed_production_identity_status == adapter.IDENTITY_SAME_SUPPORTED
    assert audit.RC_IDENTITY_EVIDENCE_SAME_SUPPORTED in audited.reason_codes
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes


def test_b04_gc21_valid_integration_conflict_is_review_without_new_hold():
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=audit.JOIN_MISSING_PRODUCTION,
            position_identity_integration=_integration(
                audit.JOIN_MISSING_PRODUCTION, "CONFLICT"
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.REVIEW
    assert audited.seed_production_identity_status == adapter.IDENTITY_CONFLICT
    assert audit.RC_IDENTITY_EVIDENCE_CONFLICT in audited.reason_codes
    assert audit.RC_IDENTITY_EVIDENCE_CONFLICT not in audit.HOLD_REASON_CODES


@pytest.mark.parametrize(
    ("case_id", "join_attr", "code_attr", "snapshot_available"),
    [
        ("B04-GC22", "JOIN_MISSING_SEED", "RC_MISSING_SEED", True),
        (
            "B04-GC23",
            "JOIN_DUPLICATE_MATCH",
            "RC_DUPLICATE_PRODUCTION_IDENTITY",
            True,
        ),
        (
            "B04-GC24",
            "JOIN_IDENTITY_REVIEW_REQUIRED",
            "RC_IDENTITY_NOT_EXACT",
            True,
        ),
        (
            "B04-GC25",
            "JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE",
            "RC_PRODUCTION_SNAPSHOT_UNAVAILABLE",
            False,
        ),
    ],
)
def test_b04_gc22_gc25_valid_integration_never_suppresses_structural_hold(
    case_id, join_attr, code_attr, snapshot_available
):
    """**有効な** B04 integration でも構造的 HOLD は抑止されない。

    転換が承認されているのは `JOIN_MISSING_PRODUCTION` だけである。
    `JOIN_IDENTITY_REVIEW_REQUIRED` は既存どおり `RC_IDENTITY_NOT_EXACT`
    による HOLD であり、review-class ではない。
    """
    join_status = getattr(audit, join_attr)
    audited = audit.evaluate(
        _audit_item(
            production=None,
            seed_production_join_status=join_status,
            production_snapshot_available=snapshot_available,
            position_identity_integration=_integration(
                join_status, "SAME_SUPPORTED"
            ),
            primary_position_evidence=_evidence(),
        )
    )
    assert audited.audit_status == audit.HOLD, case_id
    assert getattr(audit, code_attr) in audited.reason_codes, case_id
    for code in audit.IDENTITY_EVIDENCE_REVIEW_CODES:
        assert code not in audited.reason_codes, (case_id, code)
    assert audit.RC_SEED_PRODUCTION_EXACT not in audited.reason_codes, case_id


def test_b04_gc26_no_integration_supplied_is_identical_to_pre_b04():
    """integration 未供給なら P2-B04 以前と完全に同じ挙動。"""
    for join_attr, code_attr, snapshot in (
        ("JOIN_MISSING_PRODUCTION", "RC_MISSING_PRODUCTION", True),
        ("JOIN_MISSING_SEED", "RC_MISSING_SEED", True),
        ("JOIN_DUPLICATE_MATCH", "RC_DUPLICATE_PRODUCTION_IDENTITY", True),
        ("JOIN_IDENTITY_REVIEW_REQUIRED", "RC_IDENTITY_NOT_EXACT", True),
        (
            "JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE",
            "RC_PRODUCTION_SNAPSHOT_UNAVAILABLE",
            False,
        ),
    ):
        audited = audit.evaluate(
            _audit_item(
                production=None,
                seed_production_join_status=getattr(audit, join_attr),
                production_snapshot_available=snapshot,
                primary_position_evidence=_evidence(),
            )
        )
        assert audited.seed_production_identity_status == audit.IDENTITY_NOT_EVALUATED
        assert audited.audit_status == audit.HOLD, join_attr
        assert getattr(audit, code_attr) in audited.reason_codes, join_attr

    # exact join は従来どおり AUTO_PASS へ到達できる。
    exact = audit.evaluate(_audit_item(primary_position_evidence=_evidence()))
    assert exact.seed_production_identity_status == audit.IDENTITY_EXACT
    assert exact.audit_status == audit.AUTO_PASS


def test_schema_version_is_unchanged_by_the_trust_boundary_correction():
    """信頼境界の修正では schema を上げない（field は既に 1.2 で追加済み）。"""
    assert audit.SCHEMA_VERSION == "position-audit-v2/1.2"
    report = audit.build_report(
        [audit.evaluate(_audit_item(primary_position_evidence=_evidence()))]
    )
    assert report["schema_version"] == "position-audit-v2/1.2"
    assert "seed_production_identity_status" in report["results"][0]
