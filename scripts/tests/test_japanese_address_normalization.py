"""Japanese Address Structured Normalization Contract v1 の regression。

`docs/audit/position-audit-v2/japanese-address-structured-normalization-contract.md`
を authority として、`scripts/japanese_address_normalization.py` が
Stage 1 / Stage 2 を決定的かつ副作用なしに実装していることを固定する。

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
MODULE_PATH = REPO_ROOT / "scripts" / "japanese_address_normalization.py"
AUDIT_PATH = REPO_ROOT / "scripts" / "audit_shrine_positions_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


jan = _load("japanese_address_normalization", MODULE_PATH)


# ---------------------------------------------------------------------------
# Contract §2 — Structured Output Schema
# ---------------------------------------------------------------------------

CONTRACT_SCHEMA_FIELDS = (
    "raw_address",
    "lexical_address",
    "prefecture",
    "municipality",
    "locality",
    "oaza",
    "aza",
    "koaza",
    "block",
    "lot",
    "sub_lot",
    "address_core",
    "building_component",
    "floor_component",
    "unit_component",
    "structured_address",
    "normalization_status",
    "normalization_rules_applied",
    "review_reasons",
)


def test_result_exposes_every_contract_schema_field():
    result = jan.normalize_address_structured("東京都千代田区外神田2-16-2")
    payload = result.to_dict()
    assert tuple(payload) == CONTRACT_SCHEMA_FIELDS


def test_raw_address_is_never_modified():
    """`raw_address` は原文をそのまま保持する（Contract §2.1 変更禁止）。"""
    raw = "日本、〒135-0047 東京都江東区富岡１丁目２０番３号"
    result = jan.normalize_address_structured(raw)
    assert result.raw_address == raw
    assert result.lexical_address != raw


def test_normalization_status_is_a_closed_enum():
    assert jan.NORMALIZATION_STATUSES == {
        "NORMALIZED",
        "NO_CHANGE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    }


def test_address_identity_status_is_a_closed_enum():
    assert jan.ADDRESS_IDENTITY_STATUSES == {
        "ADDRESS_EXACT_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
        "ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF",
        "ADDRESS_DIFFERENT",
        "ADDRESS_AMBIGUOUS",
        "ADDRESS_UNSUPPORTED",
    }


def test_rule_and_reason_vocabularies_match_the_contract():
    assert jan.NORMALIZATION_RULES == {
        "CHOME_TO_BLOCK",
        "BAN_TO_LOT",
        "BANCHI_TO_LOT",
        "GO_TO_SUB_LOT",
        "STRUCTURED_NUMERIC_KANJI",
        "BUILDING_COMPONENT_SPLIT",
        "FLOOR_COMPONENT_SPLIT",
        "UNIT_COMPONENT_SPLIT",
    }
    assert jan.REVIEW_REASONS == {
        "OAZA_STRUCTURE_AMBIGUOUS",
        "AZA_STRUCTURE_AMBIGUOUS",
        "KOAZA_STRUCTURE_AMBIGUOUS",
        "SPECIAL_ADDRESS_NOTATION",
        "BUILDING_BOUNDARY_AMBIGUOUS",
        "UNBANCHED_ADDRESS",
        "UNSUPPORTED_LOT_STRUCTURE",
        "UNKNOWN_ADDRESS_PATTERN",
    }


# ---------------------------------------------------------------------------
# Contract §2.2 — Stage 1 Lexical Normalization
# ---------------------------------------------------------------------------

STAGE1_SAMPLES = (
    "日本、〒101-0021 東京都千代田区外神田２－１６－２",
    "日本、〒135-0047 東京都江東区富岡１丁目２０−３",
    "　東京都江東区富岡　1丁目20番3号　",
    "東京都千代田区外神田2-16-2",
    "〒000-0000東京都某区某町二丁目3番4号",
    "",
)


@pytest.mark.parametrize("raw", STAGE1_SAMPLES)
def test_stage1_matches_the_existing_position_audit_lexical_contract(raw):
    """Stage 1 は既存 Position Audit v2 の `normalize_address()` と同値。

    依存方向を作らないため実装は分けているが、規則が分岐しないことを
    ここで固定する。既存側の挙動は本 PR で変更していない。
    """
    audit = _load("audit_shrine_positions_v2_for_address_test", AUDIT_PATH)
    assert jan.lexical_normalize(raw) == audit.normalize_address(raw)


def test_stage1_applies_only_lexical_rules():
    """Stage 1 は意味的な住所書き換えを行わない（Contract §2.2）。"""
    # NFKC / 郵便番号 / 日本、 / dash / 空白 は適用される。
    assert (
        jan.lexical_normalize("日本、〒101-0021 東京都千代田区外神田２－１６－２")
        == "東京都千代田区外神田2-16-2"
    )
    # 丁目 / 番 / 号 は Stage 1 では変換されない。
    assert (
        jan.lexical_normalize("東京都江東区富岡1丁目20番3号")
        == "東京都江東区富岡1丁目20番3号"
    )


# ---------------------------------------------------------------------------
# P2-A03 相当の Golden Cases（Contract §15）
# ---------------------------------------------------------------------------


def _assert_pair(
    case_id: str,
    left: str,
    right: str,
    *,
    expected_status: str,
    expected_reasons: tuple[str, ...] = (),
):
    result = jan.compare_addresses(left, right)
    assert result.address_identity_status == expected_status, case_id
    assert result.review_reasons == expected_reasons, case_id
    return result


def test_gc_a01_exact_address():
    """完全一致は最も強い住所 evidence。"""
    address = "東京都千代田区外神田2-16-2"
    result = _assert_pair(
        "GC-A01", address, address, expected_status=jan.ADDRESS_EXACT_MATCH
    )
    assert result.left.normalization_status == jan.NO_CHANGE
    assert result.left.address_core == "東京都千代田区外神田2-16-2"


def test_gc_a02_full_width_and_postal_prefix():
    """Stage 1 だけで一致する（全角 + 郵便番号 prefix + `日本、`）。"""
    left = "日本、〒101-0021 東京都千代田区外神田２－１６－２"
    right = "東京都千代田区外神田2-16-2"
    result = _assert_pair(
        "GC-A02", left, right, expected_status=jan.ADDRESS_NORMALIZED_MATCH
    )
    # Stage 1 match
    assert result.left.lexical_address == result.right.lexical_address
    assert result.left.lexical_address == "東京都千代田区外神田2-16-2"


def test_gc_a03_chome_ban_go():
    """`1丁目20番3号` -> block/lot/sub_lot。"""
    left = "東京都江東区富岡1丁目20番3号"
    right = "東京都江東区富岡1-20-3"
    result = _assert_pair(
        "GC-A03", left, right, expected_status=jan.ADDRESS_NORMALIZED_MATCH
    )
    assert result.left.normalization_status == jan.NORMALIZED
    assert (result.left.block, result.left.lot, result.left.sub_lot) == (1, 20, 3)
    assert result.left.normalization_rules_applied == (
        "CHOME_TO_BLOCK",
        "BAN_TO_LOT",
        "GO_TO_SUB_LOT",
    )
    assert result.left.address_core == "東京都江東区富岡1-20-3"


@pytest.mark.parametrize(
    "variant",
    ["東京都江東区富岡1丁目20番3号", "東京都江東区富岡1丁目20番地3", "東京都江東区富岡1丁目20番3"],
)
def test_contract_safe_transformations_all_reach_the_same_core(variant):
    """Contract §6 が列挙する3形はすべて同じ構造へ落ちる。"""
    result = jan.normalize_address_structured(variant)
    assert (result.block, result.lot, result.sub_lot) == (1, 20, 3)
    assert result.address_core == "東京都江東区富岡1-20-3"
    assert result.normalization_status == jan.NORMALIZED


def test_gc_a04_numeric_kanji_in_structured_token():
    """`二丁目` は住所数値 token なので block=2 へ変換する。"""
    left = "東京都某区某町二丁目3番4号"
    right = "東京都某区某町2-3-4"
    result = _assert_pair(
        "GC-A04", left, right, expected_status=jan.ADDRESS_NORMALIZED_MATCH
    )
    assert result.left.normalization_status == jan.NORMALIZED
    assert result.left.block == 2
    assert "STRUCTURED_NUMERIC_KANJI" in result.left.normalization_rules_applied
    assert result.left.address_core == "東京都某区某町2-3-4"


def test_gc_a05_kanji_in_locality_name_is_never_converted():
    """町名の漢数字は変換しない（`二本松` -> `2本松` 禁止）。"""
    result = jan.normalize_address_structured("福島県二本松市○○1-2")
    assert result.municipality == "二本松市"
    assert result.address_core == "福島県二本松市○○1-2"
    assert "二本松" in result.address_core
    assert "2本松" not in result.address_core
    assert "STRUCTURED_NUMERIC_KANJI" not in result.normalization_rules_applied


@pytest.mark.parametrize(
    ("address", "preserved"),
    [
        ("福島県二本松市○○1-2", "二本松"),
        ("静岡県三島市○○1-2", "三島"),
        ("京都府八幡市○○1-2", "八幡"),
        # `十番` を lot=10 と誤読しないこと（実在町名）。
        ("東京都港区麻布十番1-2-3", "麻布十番"),
    ],
)
def test_locality_kanji_numerals_are_preserved(address, preserved):
    result = jan.normalize_address_structured(address)
    assert result.address_core is not None
    assert preserved in result.address_core
    assert "STRUCTURED_NUMERIC_KANJI" not in result.normalization_rules_applied


def test_gc_a06_oaza():
    """`大字` の有無だけが違う住所を自動一致させない。"""
    result = _assert_pair(
        "GC-A06",
        "埼玉県某市大字石神976",
        "埼玉県某市石神976",
        expected_status=jan.ADDRESS_AMBIGUOUS,
        expected_reasons=("OAZA_STRUCTURE_AMBIGUOUS",),
    )
    # `大字` は削除されず component として保持される。
    assert result.left.oaza == "石神"
    assert result.left.address_core == "埼玉県某市大字石神976"
    assert result.right.oaza is None
    assert result.right.locality == "石神"
    assert result.address_identity_status != jan.ADDRESS_NORMALIZED_MATCH


def test_gc_a07_aza():
    """`字` を黙って除去しない。"""
    result = _assert_pair(
        "GC-A07",
        "青森県某市大字藤崎字西村井8-2",
        "青森県某市藤崎西村井8-2",
        expected_status=jan.ADDRESS_AMBIGUOUS,
        expected_reasons=("OAZA_STRUCTURE_AMBIGUOUS", "AZA_STRUCTURE_AMBIGUOUS"),
    )
    assert result.left.oaza == "藤崎"
    assert result.left.aza == "西村井"
    assert result.left.address_core == "青森県某市大字藤崎字西村井8-2"


def test_gc_a08_koaza():
    """`小字` も identity 構成要素として保持する。"""
    result = _assert_pair(
        "GC-A08",
        "宮城県某市○○小字△△12",
        "宮城県某市○○△△12",
        expected_status=jan.ADDRESS_AMBIGUOUS,
        expected_reasons=("KOAZA_STRUCTURE_AMBIGUOUS",),
    )
    assert result.left.locality == "○○"
    assert result.left.koaza == "△△"
    assert result.left.address_core == "宮城県某市○○小字△△12"


def test_gc_a09_building_component():
    """建物情報は address_core から分離し、かつ捨てない。"""
    result = _assert_pair(
        "GC-A09",
        "東京都千代田区外神田2-16-2",
        "東京都千代田区外神田2-16-2 神田明神文化交流館3階",
        expected_status=jan.ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF,
    )
    assert result.left.address_core == result.right.address_core
    assert result.right.building_component == "神田明神文化交流館"
    assert result.right.floor_component == "3階"
    assert result.right.unit_component is None
    # 建物は address_core に混ざらない。
    assert "神田明神文化交流館" not in result.right.address_core
    # ただし structured_address には残る（差分を捨てない）。
    assert "神田明神文化交流館" in result.right.structured_address
    assert result.right.normalization_rules_applied == (
        "BUILDING_COMPONENT_SPLIT",
        "FLOOR_COMPONENT_SPLIT",
    )


def test_gc_a10_different_buildings_on_same_lot():
    """同一地番の別建物を SAME にしない。"""
    result = _assert_pair(
        "GC-A10",
        "東京都中央区銀座1-2-3 Aビル1F",
        "東京都中央区銀座1-2-3 Bビル2F",
        expected_status=jan.ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF,
    )
    assert result.left.address_core == result.right.address_core == "東京都中央区銀座1-2-3"
    assert result.left.building_component == "Aビル"
    assert result.left.floor_component == "1F"
    assert result.right.building_component == "Bビル"
    assert result.right.floor_component == "2F"
    assert result.address_identity_status != jan.ADDRESS_NORMALIZED_MATCH


def test_gc_a11_unsupported_special_address():
    """`無番地` に数値構造を発明しない。"""
    result = jan.normalize_address_structured("○○県○○市○○町無番地")
    assert result.normalization_status == jan.UNSUPPORTED
    assert result.review_reasons == ("UNBANCHED_ADDRESS",)
    # 推測された数値構造が無いこと。
    assert result.block is None
    assert result.lot is None
    assert result.sub_lot is None
    assert result.address_core is None

    pair = jan.compare_addresses("○○県○○市○○町無番地", "○○県○○市○○町1-2")
    assert pair.address_identity_status == jan.ADDRESS_UNSUPPORTED


def test_gc_a12_tomioka_hachimangu_precedent():
    """富岡八幡宮の3表記がすべて同じ address_core に落ちる。"""
    a = "東京都江東区富岡 1丁目20番3号"
    b = "日本、〒135-0047 東京都江東区富岡１丁目２０−３"
    c = "東京都江東区富岡1-20-3"

    cores = {
        jan.normalize_address_structured(value).address_core for value in (a, b, c)
    }
    assert cores == {"東京都江東区富岡1-20-3"}

    for left, right in ((a, b), (a, c), (b, c)):
        result = jan.compare_addresses(left, right)
        assert result.address_identity_status == jan.ADDRESS_NORMALIZED_MATCH

    # `八幡` を含む地名が数値化されないこと（GC-A05 と同じ保護）。
    assert "八" in jan.normalize_address_structured("東京都江東区富岡八幡1-2").address_core


# ---------------------------------------------------------------------------
# Contract §10 / §11 — Identity 判定の禁止
# ---------------------------------------------------------------------------

FORBIDDEN_ENTITY_VERDICTS = ("SAME", "DIFFERENT", "NON_SHRINE")


def test_stage2_never_returns_an_entity_verdict():
    """Stage 2 は `SAME` / `DIFFERENT` / `NON_SHRINE` を返さない（§10）。"""
    result = jan.compare_addresses(
        "東京都江東区富岡1丁目20番3号", "東京都江東区富岡1-20-3"
    )
    assert result.address_identity_status in jan.ADDRESS_IDENTITY_STATUSES
    assert result.address_identity_status not in FORBIDDEN_ENTITY_VERDICTS
    # `ADDRESS_DIFFERENT` は住所レベルの evidence であり entity 判定ではない。
    assert result.address_identity_status.startswith("ADDRESS_")


def test_module_exposes_no_entity_decision_vocabulary():
    """module が entity 判定語彙を公開しないこと（§10 / §11）。"""
    exported = {
        name: value
        for name, value in vars(jan).items()
        if isinstance(value, str) and not name.startswith("_")
    }
    for name, value in exported.items():
        assert value not in FORBIDDEN_ENTITY_VERDICTS, name


# ---------------------------------------------------------------------------
# Contract §16 — fail-safe
# ---------------------------------------------------------------------------


def test_unparseable_addresses_fail_safe_instead_of_guessing():
    for address in ("", "   ", "住所不明", "外神田2-16-2", "東京都"):
        result = jan.normalize_address_structured(address)
        assert result.normalization_status in (jan.UNSUPPORTED, jan.AMBIGUOUS), address
        assert result.review_reasons, address
        assert result.address_core is None, address


def test_ambiguous_building_boundary_is_not_split():
    """建物境界を確定できないときは分割しない（Contract §8）。"""
    result = jan.normalize_address_structured("東京都中央区銀座1-2-3 4号館別棟")
    assert result.normalization_status == jan.AMBIGUOUS
    assert result.review_reasons == ("BUILDING_BOUNDARY_AMBIGUOUS",)
    assert result.building_component is None


def test_missing_components_are_never_inferred():
    """欠落した prefecture / municipality / lot を補完しない。"""
    result = jan.normalize_address_structured("千代田区外神田2-16-2")
    assert result.normalization_status == jan.UNSUPPORTED
    assert result.prefecture is None
    assert result.municipality is None

    no_lot = jan.normalize_address_structured("東京都千代田区外神田")
    assert no_lot.normalization_status == jan.UNSUPPORTED
    assert no_lot.lot is None
    assert no_lot.block is None


def test_review_reasons_are_only_present_for_ambiguous_or_unsupported():
    for address in ("東京都江東区富岡1丁目20番3号", "東京都千代田区外神田2-16-2"):
        result = jan.normalize_address_structured(address)
        assert result.normalization_status in (jan.NORMALIZED, jan.NO_CHANGE)
        assert result.review_reasons == ()


def test_only_applied_rules_are_recorded():
    """適用していないルールを記録しない（Contract §4）。"""
    plain = jan.normalize_address_structured("東京都千代田区外神田2-16-2")
    assert plain.normalization_rules_applied == ()
    assert plain.normalization_status == jan.NO_CHANGE

    banchi = jan.normalize_address_structured("東京都江東区富岡1丁目20番地3")
    assert "BANCHI_TO_LOT" in banchi.normalization_rules_applied
    assert "BAN_TO_LOT" not in banchi.normalization_rules_applied

    ban = jan.normalize_address_structured("東京都江東区富岡1丁目20番3号")
    assert "BAN_TO_LOT" in ban.normalization_rules_applied
    assert "BANCHI_TO_LOT" not in ban.normalization_rules_applied

    for result in (plain, banchi, ban):
        for rule in result.normalization_rules_applied:
            assert rule in jan.NORMALIZATION_RULES


def test_unit_component_is_separated_when_present():
    result = jan.normalize_address_structured("東京都中央区銀座1-2-3 Aビル2階201号室")
    assert result.address_core == "東京都中央区銀座1-2-3"
    assert result.building_component == "Aビル"
    assert result.floor_component == "2階"
    assert result.unit_component == "201号室"
    assert result.normalization_rules_applied == (
        "BUILDING_COMPONENT_SPLIT",
        "FLOOR_COMPONENT_SPLIT",
        "UNIT_COMPONENT_SPLIT",
    )


def test_identical_area_markers_are_compared_on_the_core():
    """marker が両側にそろっていれば通常の core 比較に進む。"""
    result = jan.compare_addresses("埼玉県某市大字石神976", "埼玉県某市大字石神976番地")
    assert result.address_identity_status == jan.ADDRESS_NORMALIZED_MATCH

    different = jan.compare_addresses("埼玉県某市大字石神976", "埼玉県某市大字石神977")
    assert different.address_identity_status == jan.ADDRESS_DIFFERENT


# ---------------------------------------------------------------------------
# 決定性
# ---------------------------------------------------------------------------

DETERMINISM_SAMPLES = (
    "東京都江東区富岡1丁目20番3号",
    "日本、〒135-0047 東京都江東区富岡１丁目２０−３",
    "青森県某市大字藤崎字西村井8-2",
    "東京都中央区銀座1-2-3 Aビル2階201号室",
    "○○県○○市○○町無番地",
    "東京都中央区銀座1-2-3 4号館別棟",
)


@pytest.mark.parametrize("address", DETERMINISM_SAMPLES)
def test_same_input_produces_the_same_structured_output(address):
    runs = [jan.normalize_address_structured(address).to_dict() for _ in range(5)]
    assert all(run == runs[0] for run in runs)
    serialized = [
        json.dumps(run, ensure_ascii=False, sort_keys=True) for run in runs
    ]
    assert len(set(serialized)) == 1


def test_rules_and_reason_ordering_is_stable():
    result = jan.normalize_address_structured("東京都某区某町二丁目3番4号")
    for _ in range(5):
        again = jan.normalize_address_structured("東京都某区某町二丁目3番4号")
        assert again.normalization_rules_applied == result.normalization_rules_applied

    pair = jan.compare_addresses("青森県某市大字藤崎字西村井8-2", "青森県某市藤崎西村井8-2")
    for _ in range(5):
        again = jan.compare_addresses(
            "青森県某市大字藤崎字西村井8-2", "青森県某市藤崎西村井8-2"
        )
        assert again.review_reasons == pair.review_reasons
    # canonical order（集合順に依存しない）。
    assert pair.review_reasons == ("OAZA_STRUCTURE_AMBIGUOUS", "AZA_STRUCTURE_AMBIGUOUS")


def test_comparison_is_symmetric_for_status():
    for left, right in (
        ("東京都江東区富岡1丁目20番3号", "東京都江東区富岡1-20-3"),
        ("埼玉県某市大字石神976", "埼玉県某市石神976"),
        ("東京都中央区銀座1-2-3 Aビル1F", "東京都中央区銀座1-2-3 Bビル2F"),
        ("○○県○○市○○町無番地", "○○県○○市○○町1-2"),
    ):
        assert (
            jan.compare_addresses(left, right).address_identity_status
            == jan.compare_addresses(right, left).address_identity_status
        )


# ---------------------------------------------------------------------------
# side-effect free
# ---------------------------------------------------------------------------

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
        "pathlib",
        "os",
        "shutil",
        "subprocess",
    }
)

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
        "commit",
        "cursor",
        "connect",
        "urlopen",
        "write_text",
        "write_bytes",
        "read_text",
        "read_bytes",
        "mkdir",
        "unlink",
        "system",
        "popen",
        "run",
    }
)


def test_module_has_no_io_or_persistence_path():
    """構文木で I/O・DB・network 経路が無いことを固定する。"""
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS, alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, node.module
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALL_ATTRS, node.func.attr
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__"}


def test_module_declares_no_module_level_mutable_state():
    """module level の可変状態を持たない（呼び出し間で状態を持ち越さない）。"""
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if isinstance(value, (ast.List, ast.Set)):
                raise AssertionError("module level mutable literal is not allowed")


def test_results_are_immutable():
    import dataclasses

    result = jan.normalize_address_structured("東京都千代田区外神田2-16-2")
    assert dataclasses.is_dataclass(result)
    assert type(result).__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.address_core = "x"  # type: ignore[misc]

    pair = jan.compare_addresses("東京都千代田区外神田2-16-2", "東京都千代田区外神田2-16-2")
    assert type(pair).__dataclass_params__.frozen


def test_normalization_does_not_mutate_its_input_arguments():
    raw = "東京都江東区富岡1丁目20番3号"
    before = str(raw)
    jan.normalize_address_structured(raw)
    jan.compare_addresses(raw, raw)
    assert raw == before


# ---------------------------------------------------------------------------
# 既存実装との非干渉（Contract §16 / §12）
# ---------------------------------------------------------------------------


def test_existing_normalizers_keep_their_own_behavior():
    """既存の住所正規化を置き換えていないこと。

    `shrine_duplicate_normalize` は空白除去 + dash 寄せだけを行い、
    丁目・番地の表記ゆれを扱わない。本 module はそれを変更しない。
    """
    duplicate_module = _load(
        "shrine_duplicate_normalize_for_address_test",
        REPO_ROOT / "backend" / "temples" / "services" / "shrine_duplicate_normalize.py",
    )
    value = "東京都江東区富岡1丁目20番3号"
    # 既存の挙動: 丁目・番・号 は保持されたまま。
    assert duplicate_module.normalize_shrine_address_for_duplicate(value) == value
    # Stage 2 は別責務として構造化する。
    assert jan.normalize_address_structured(value).address_core == "東京都江東区富岡1-20-3"


def test_stage2_module_is_not_wired_into_any_existing_caller():
    """P2-B02 は foundation。既存経路へは結線しない。"""
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == MODULE_PATH:
            continue
        if "japanese_address_normalization" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert callers == [], callers


@pytest.mark.parametrize(
    "address",
    [
        "東京都千代田区外神田2-16-2",
        "東京都 千代田区外神田2-16-2",
        "東京都千代田区 外神田2-16-2",
    ],
)
def test_whitespace_between_administrative_components_is_tolerated(address):
    """行政区画の区切り空白は identity の意味を持たない。

    Stage 1 は連続空白を1つに畳むだけで削除しないため、Stage 2 側で
    読み飛ばす。住所そのものを書き換えるわけではない。
    """
    result = jan.normalize_address_structured(address)
    assert result.prefecture == "東京都"
    assert result.municipality == "千代田区"
    assert result.locality == "外神田"
    assert result.address_core == "東京都千代田区外神田2-16-2"
