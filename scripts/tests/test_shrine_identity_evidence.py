"""Address Identity Evidence Layer（P2-B03）の regression。

`scripts/shrine_identity_evidence.py` が B02 の canonical 住所 evidence を
消費し、identity evidence assessment を決定的・副作用なしに返すことを固定する。

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
MODULE_PATH = REPO_ROOT / "scripts" / "shrine_identity_evidence.py"
ADDRESS_MODULE_PATH = REPO_ROOT / "scripts" / "japanese_address_normalization.py"
LEGACY_AUDIT_PATH = REPO_ROOT / "scripts" / "audit_shrine_positions_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sie = _load("shrine_identity_evidence", MODULE_PATH)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

ADDRESS_A = "東京都千代田区外神田2-16-2"
ADDRESS_A_DECORATED = "日本、〒101-0021 東京都千代田区外神田２－１６－２"
ADDRESS_A_WITH_BUILDING = "東京都千代田区外神田2-16-2 神田明神文化交流館3階"
ADDRESS_B = "東京都江東区富岡1-20-3"
ADDRESS_OAZA = "埼玉県某市大字石神976"
ADDRESS_NO_OAZA = "埼玉県某市石神976"
ADDRESS_UNPARSEABLE = "○○県○○市○○町無番地"
ADDRESS_PARK_TOWER = "東京都中央区銀座1-2-3 パークタワー3階"
ADDRESS_PARK_TOWER_DECORATED = "日本、〒104-0061 東京都中央区銀座1-2-3 パークタワー3階"


def _address(left: str, right: str):
    """B02 の canonical な比較結果を得る（B03 は正規化を再実装しない）。"""
    return sie.compare_addresses(left, right)


# ---------------------------------------------------------------------------
# 入力 / 出力の閉じた enum
# ---------------------------------------------------------------------------


def test_name_identity_statuses_are_closed():
    assert sie.NAME_IDENTITY_STATUSES == {
        "NAME_EXACT_MATCH",
        "NAME_NORMALIZED_MATCH",
        "NAME_ALIAS_CONFIRMED",
        "NAME_DIFFERENT",
        "NAME_AMBIGUOUS",
        "NAME_UNSUPPORTED",
    }


def test_official_source_entity_statuses_are_closed():
    assert sie.OFFICIAL_SOURCE_ENTITY_STATUSES == {
        "OFFICIAL_SOURCE_SAME",
        "OFFICIAL_SOURCE_DIFFERENT",
        "OFFICIAL_SOURCE_AMBIGUOUS",
        "OFFICIAL_SOURCE_UNAVAILABLE",
    }


def test_place_id_statuses_are_closed():
    assert sie.PLACE_ID_STATUSES == {
        "PLACE_ID_MATCH",
        "PLACE_ID_DIFFERENT",
        "PLACE_ID_UNAVAILABLE",
    }


def test_existing_resolution_statuses_are_closed():
    assert sie.EXISTING_RESOLUTION_STATUSES == {
        "RESOLUTION_SAME",
        "RESOLUTION_DIFFERENT",
        "RESOLUTION_UNAVAILABLE",
    }


def test_identity_evidence_statuses_are_closed():
    assert sie.IDENTITY_EVIDENCE_STATUSES == {
        "SAME_SUPPORTED",
        "CONFLICT",
        "REVIEW_REQUIRED",
        "INSUFFICIENT",
    }


REQUIRED_OUTPUT_FIELDS = (
    "identity_evidence_status",
    "name_identity_status",
    "address_identity_status",
    "official_source_entity_status",
    "place_id_status",
    "existing_resolution_status",
    "supporting_evidence",
    "conflicting_evidence",
    "review_reasons",
)


def test_result_exposes_the_required_output_model():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
    )
    assert tuple(result.to_dict()) == REQUIRED_OUTPUT_FIELDS


# ---------------------------------------------------------------------------
# B02 authority / legacy boundary
# ---------------------------------------------------------------------------


def test_b03_consumes_the_canonical_b02_address_module():
    """B02 の住所語彙・比較関数をそのまま使う（再実装しない）。"""
    # B03 が実際に読み込んだ module が canonical な B02 実装であること。
    address_module = sie.address_contract
    assert address_module.__file__ == str(ADDRESS_MODULE_PATH)
    assert address_module.__file__ != str(LEGACY_AUDIT_PATH)

    assert sie.compare_addresses is address_module.compare_addresses
    assert sie.lexical_normalize is address_module.lexical_normalize
    assert sie.ADDRESS_IDENTITY_STATUSES == address_module.ADDRESS_IDENTITY_STATUSES
    for name in (
        "ADDRESS_EXACT_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
        "ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF",
        "ADDRESS_DIFFERENT",
        "ADDRESS_AMBIGUOUS",
        "ADDRESS_UNSUPPORTED",
    ):
        assert getattr(sie, name) == getattr(address_module, name)

    # 独立に読み込んだ B02 とも値として一致する（語彙を再定義していない）。
    fresh = _load("japanese_address_normalization_fresh_for_b03", ADDRESS_MODULE_PATH)
    assert sie.ADDRESS_IDENTITY_STATUSES == fresh.ADDRESS_IDENTITY_STATUSES


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """docstring の Constant node id を集める（説明文を検査対象外にする）。"""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    found.add(id(first.value))
    return found


def test_b03_does_not_reference_legacy_position_audit_normalization():
    """legacy `normalize_address` に import も呼び出しも参照も持たない。

    docstring は legacy との境界を **説明する** ために legacy 名を含むので、
    検査対象は実行されるコードに限る。
    """
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "audit_shrine_positions" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            assert "audit_shrine_positions" not in (node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr != "normalize_address"
            if isinstance(node.func, ast.Name):
                assert node.func.id != "normalize_address"
        elif isinstance(node, ast.Attribute):
            assert node.attr != "normalize_address"
        elif isinstance(node, ast.Name):
            assert node.id != "normalize_address"
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # docstring 以外の文字列 literal は legacy path を指さない。
            if id(node) not in docstrings:
                assert "audit_shrine_positions" not in node.value, node.value

    # canonical module だけを読む。
    assert sie.address_contract.__file__ == str(ADDRESS_MODULE_PATH)
    assert "audit_shrine_positions_v2" not in sys.modules.get(
        "shrine_identity_evidence"
    ).__dict__.get("_ADDRESS_MODULE_PATH", Path()).name


def test_b03_does_not_reimplement_address_normalization():
    """住所正規化を B03 側で再実装していないこと。"""
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("NFKC", "_DASH_VARIANTS", "丁目", "大字", "unicodedata"):
        assert forbidden not in source, forbidden


def test_legacy_position_audit_module_is_untouched_by_this_layer():
    """legacy の Stage 1 は別実装のまま（B03 は寄せない）。"""
    legacy = _load("audit_shrine_positions_v2_for_b03_test", LEGACY_AUDIT_PATH)
    value = "東京都中央区銀座1-2-3 パークタワー3階"
    # 意図的な差分が残っていること。
    assert legacy.normalize_address(value) != sie.lexical_normalize(value)
    assert sie.lexical_normalize(value) == value


# ---------------------------------------------------------------------------
# Golden Cases
# ---------------------------------------------------------------------------


def _assert_case(case_id: str, result, expected_status: str):
    assert result.identity_evidence_status == expected_status, case_id
    assert result.identity_evidence_status in sie.IDENTITY_EVIDENCE_STATUSES, case_id
    # entity verdict は返さない。
    assert result.identity_evidence_status not in ("SAME", "DIFFERENT", "NON_SHRINE")
    return result


def test_id_gc01_name_exact_address_exact_official_source_same():
    result = _assert_case(
        "ID-GC01",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_A),
            name_identity_status=sie.NAME_EXACT_MATCH,
            official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        ),
        sie.SAME_SUPPORTED,
    )
    assert result.address_identity_status == sie.ADDRESS_EXACT_MATCH
    assert result.supporting_evidence == (
        "NAME_EXACT_MATCH",
        "ADDRESS_EXACT_MATCH",
        "OFFICIAL_SOURCE_SAME",
    )
    assert result.conflicting_evidence == ()
    assert result.review_reasons == ()


def test_id_gc02_name_normalized_address_normalized_place_id_match():
    result = _assert_case(
        "ID-GC02",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
            name_identity_status=sie.NAME_NORMALIZED_MATCH,
            place_id_status=sie.PLACE_ID_MATCH,
        ),
        sie.SAME_SUPPORTED,
    )
    assert result.address_identity_status == sie.ADDRESS_NORMALIZED_MATCH
    assert result.supporting_evidence == (
        "NAME_NORMALIZED_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
        "PLACE_ID_MATCH",
    )


def test_id_gc03_name_alias_confirmed_address_normalized_resolution_same():
    result = _assert_case(
        "ID-GC03",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
            name_identity_status=sie.NAME_ALIAS_CONFIRMED,
            existing_resolution_status=sie.RESOLUTION_SAME,
        ),
        sie.SAME_SUPPORTED,
    )
    assert result.supporting_evidence == (
        "NAME_ALIAS_CONFIRMED",
        "ADDRESS_NORMALIZED_MATCH",
        "RESOLUTION_SAME",
    )


def test_id_gc04_address_exact_match_alone_is_insufficient():
    """住所 evidence だけからは決して SAME_SUPPORTED にしない。"""
    result = _assert_case(
        "ID-GC04",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_A)
        ),
        sie.INSUFFICIENT,
    )
    assert result.name_identity_status == sie.NAME_UNSUPPORTED
    assert "NAME_EVIDENCE_UNAVAILABLE" in result.review_reasons


def test_id_gc05_no_independent_corroborator_is_insufficient():
    result = _assert_case(
        "ID-GC05",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
            name_identity_status=sie.NAME_EXACT_MATCH,
        ),
        sie.INSUFFICIENT,
    )
    assert result.official_source_entity_status == sie.OFFICIAL_SOURCE_UNAVAILABLE
    assert result.place_id_status == sie.PLACE_ID_UNAVAILABLE
    assert result.existing_resolution_status == sie.RESOLUTION_UNAVAILABLE
    assert "INDEPENDENT_CORROBORATION_MISSING" in result.review_reasons


def test_id_gc06_address_component_difference_is_review_required():
    """建物差は他の同一 evidence があっても自動 SAME_SUPPORTED にしない。"""
    result = _assert_case(
        "ID-GC06",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_A_WITH_BUILDING),
            name_identity_status=sie.NAME_EXACT_MATCH,
            official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        ),
        sie.REVIEW_REQUIRED,
    )
    assert result.address_identity_status == sie.ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF
    assert result.review_reasons == ("ADDRESS_COMPONENT_DIFFERENCE",)
    # corroborator があっても格上げされない。
    assert "OFFICIAL_SOURCE_SAME" in result.supporting_evidence


def test_id_gc07_ambiguous_address_is_review_required():
    result = _assert_case(
        "ID-GC07",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_OAZA, ADDRESS_NO_OAZA),
            name_identity_status=sie.NAME_EXACT_MATCH,
            official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        ),
        sie.REVIEW_REQUIRED,
    )
    assert result.address_identity_status == sie.ADDRESS_AMBIGUOUS
    assert result.review_reasons == ("ADDRESS_EVIDENCE_AMBIGUOUS",)


def test_id_gc08_unsupported_address_is_insufficient():
    result = _assert_case(
        "ID-GC08",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_UNPARSEABLE, ADDRESS_A),
            name_identity_status=sie.NAME_EXACT_MATCH,
        ),
        sie.INSUFFICIENT,
    )
    assert result.address_identity_status == sie.ADDRESS_UNSUPPORTED
    assert result.review_reasons == ("ADDRESS_EVIDENCE_UNSUPPORTED",)


def test_id_gc09_address_different_without_explicit_conflict_is_review_required():
    """住所が違うだけでは別神社とみなさない。"""
    result = _assert_case(
        "ID-GC09",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_B),
            name_identity_status=sie.NAME_EXACT_MATCH,
        ),
        sie.REVIEW_REQUIRED,
    )
    assert result.address_identity_status == sie.ADDRESS_DIFFERENT
    assert result.review_reasons == ("ADDRESS_DIFFERENT_WITHOUT_TRUSTED_CONFLICT",)
    assert result.identity_evidence_status != sie.CONFLICT


def test_id_gc10_name_different_is_conflict_even_with_place_id_match():
    """多数決にしない。同一支持 signal が blocking conflict を打ち消さない。"""
    result = _assert_case(
        "ID-GC10",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_A),
            name_identity_status=sie.NAME_DIFFERENT,
            place_id_status=sie.PLACE_ID_MATCH,
        ),
        sie.CONFLICT,
    )
    assert "NAME_DIFFERENT" in result.conflicting_evidence
    # 同一を支持する evidence も記録されるが、status は覆らない。
    assert "PLACE_ID_MATCH" in result.supporting_evidence
    assert "ADDRESS_EXACT_MATCH" in result.supporting_evidence
    assert result.review_reasons == ("EXPLICIT_IDENTITY_CONFLICT",)


def test_id_gc11_official_source_different_is_conflict():
    result = _assert_case(
        "ID-GC11",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A, ADDRESS_A),
            name_identity_status=sie.NAME_EXACT_MATCH,
            official_source_entity_status=sie.OFFICIAL_SOURCE_DIFFERENT,
        ),
        sie.CONFLICT,
    )
    assert "OFFICIAL_SOURCE_DIFFERENT" in result.conflicting_evidence


def test_id_gc12_place_id_different_is_conflict():
    result = _assert_case(
        "ID-GC12",
        sie.assess_identity_evidence(
            address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
            name_identity_status=sie.NAME_EXACT_MATCH,
            place_id_status=sie.PLACE_ID_DIFFERENT,
        ),
        sie.CONFLICT,
    )
    assert "PLACE_ID_DIFFERENT" in result.conflicting_evidence


def test_id_gc13_legacy_normalized_only_address_is_insufficient():
    """legacy 正規化済みしか無く raw が無いなら同値を推測しない。"""
    result = _assert_case(
        "ID-GC13",
        sie.assess_identity_evidence(
            address_comparison=None,
            name_identity_status=sie.NAME_EXACT_MATCH,
            official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        ),
        sie.INSUFFICIENT,
    )
    assert result.address_identity_status == sie.ADDRESS_UNSUPPORTED
    assert result.review_reasons == ("ADDRESS_EVIDENCE_UNAVAILABLE",)
    # corroborator が揃っていても格上げしない。
    assert "OFFICIAL_SOURCE_SAME" in result.supporting_evidence

    # 「unavailable」と「解析不能な住所形式」は別 reason で区別される。
    unsupported = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_UNPARSEABLE, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
    )
    assert unsupported.review_reasons == ("ADDRESS_EVIDENCE_UNSUPPORTED",)


def test_id_gc14_canonical_address_keeps_prolonged_sound_mark_and_is_usable():
    """canonical Stage 1 経由なので長音が保持され、evidence として使える。"""
    result = _assert_case(
        "ID-GC14",
        sie.assess_identity_evidence_from_addresses(
            left_address=ADDRESS_PARK_TOWER,
            right_address=ADDRESS_PARK_TOWER_DECORATED,
            name_identity_status=sie.NAME_EXACT_MATCH,
            place_id_status=sie.PLACE_ID_MATCH,
        ),
        sie.SAME_SUPPORTED,
    )
    assert result.address_identity_status == sie.ADDRESS_NORMALIZED_MATCH

    comparison = result.address_comparison
    assert comparison.left.building_component == "パークタワー"
    assert comparison.right.building_component == "パークタワー"
    assert "ー" in comparison.left.building_component
    assert "パークタワ-" not in comparison.left.lexical_address


def test_id_gc15_repeated_inputs_are_byte_identical():
    kwargs = dict(
        left_address=ADDRESS_PARK_TOWER,
        right_address=ADDRESS_PARK_TOWER_DECORATED,
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        place_id_status=sie.PLACE_ID_MATCH,
        existing_resolution_status=sie.RESOLUTION_SAME,
    )
    runs = [
        sie.assess_identity_evidence_from_addresses(**kwargs).to_dict()
        for _ in range(5)
    ]
    assert all(run == runs[0] for run in runs)
    serialized = {json.dumps(run, ensure_ascii=False, sort_keys=True) for run in runs}
    assert len(serialized) == 1

    first = runs[0]
    assert first["supporting_evidence"] == [
        "NAME_EXACT_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
        "OFFICIAL_SOURCE_SAME",
        "PLACE_ID_MATCH",
        "RESOLUTION_SAME",
    ]
    assert first["conflicting_evidence"] == []
    assert first["review_reasons"] == []


# ---------------------------------------------------------------------------
# SAME_SUPPORTED contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name_status",
    ["NAME_EXACT_MATCH", "NAME_NORMALIZED_MATCH", "NAME_ALIAS_CONFIRMED"],
)
@pytest.mark.parametrize(
    ("corroborator_field", "corroborator_value"),
    [
        ("official_source_entity_status", "OFFICIAL_SOURCE_SAME"),
        ("place_id_status", "PLACE_ID_MATCH"),
        ("existing_resolution_status", "RESOLUTION_SAME"),
    ],
)
def test_same_supported_requires_name_address_and_one_corroborator(
    name_status, corroborator_field, corroborator_value
):
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
        name_identity_status=name_status,
        **{corroborator_field: corroborator_value},
    )
    assert result.identity_evidence_status == sie.SAME_SUPPORTED


def test_same_supported_is_never_derived_from_address_alone():
    """あらゆる住所 evidence 単独では SAME_SUPPORTED にならない。"""
    for left, right in (
        (ADDRESS_A, ADDRESS_A),
        (ADDRESS_A_DECORATED, ADDRESS_A),
        (ADDRESS_A, ADDRESS_A_WITH_BUILDING),
        (ADDRESS_OAZA, ADDRESS_NO_OAZA),
        (ADDRESS_A, ADDRESS_B),
        (ADDRESS_UNPARSEABLE, ADDRESS_A),
    ):
        result = sie.assess_identity_evidence(address_comparison=_address(left, right))
        assert result.identity_evidence_status != sie.SAME_SUPPORTED, (left, right)


def test_corroborator_alone_without_usable_address_is_not_same_supported():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_B),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        place_id_status=sie.PLACE_ID_MATCH,
        existing_resolution_status=sie.RESOLUTION_SAME,
    )
    assert result.identity_evidence_status == sie.REVIEW_REQUIRED


def test_usable_evidence_sets_match_the_contract():
    assert sie.USABLE_NAME_EVIDENCE == {
        "NAME_EXACT_MATCH",
        "NAME_NORMALIZED_MATCH",
        "NAME_ALIAS_CONFIRMED",
    }
    assert sie.USABLE_ADDRESS_EVIDENCE == {
        "ADDRESS_EXACT_MATCH",
        "ADDRESS_NORMALIZED_MATCH",
    }
    assert sie.INDEPENDENT_CORROBORATORS == {
        "OFFICIAL_SOURCE_SAME",
        "PLACE_ID_MATCH",
        "RESOLUTION_SAME",
    }
    # 建物差は usable address evidence ではない（B03 v1）。
    assert (
        sie.ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF not in sie.USABLE_ADDRESS_EVIDENCE
    )


def test_name_alias_confirmed_is_explicit_evidence_not_similarity():
    """alias は明示的 evidence としてのみ与えられる（類似度から導出しない）。"""
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("SequenceMatcher", "difflib", "ratio(", "similarity", "levenshtein"):
        assert forbidden.lower() not in source.lower(), forbidden


# ---------------------------------------------------------------------------
# conflict precedence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name_identity_status", "NAME_DIFFERENT"),
        ("official_source_entity_status", "OFFICIAL_SOURCE_DIFFERENT"),
        ("place_id_status", "PLACE_ID_DIFFERENT"),
        ("existing_resolution_status", "RESOLUTION_DIFFERENT"),
    ],
)
def test_every_explicit_trusted_conflict_produces_conflict(field, value):
    """同一を支持する evidence を最大限そろえても conflict が勝つ。"""
    kwargs = dict(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        place_id_status=sie.PLACE_ID_MATCH,
        existing_resolution_status=sie.RESOLUTION_SAME,
    )
    kwargs[field] = value
    result = sie.assess_identity_evidence(**kwargs)
    assert result.identity_evidence_status == sie.CONFLICT
    assert value in result.conflicting_evidence


def test_address_different_is_not_an_explicit_trusted_conflict():
    assert sie.ADDRESS_DIFFERENT not in sie.EXPLICIT_TRUSTED_CONFLICTS
    assert sie.EXPLICIT_TRUSTED_CONFLICTS == {
        "NAME_DIFFERENT",
        "OFFICIAL_SOURCE_DIFFERENT",
        "PLACE_ID_DIFFERENT",
        "RESOLUTION_DIFFERENT",
    }


def test_conflict_precedes_unsupported_and_ambiguous():
    """1. explicit conflict は 2/3/4 より先に効く。"""
    # unsupported address + conflict
    unsupported = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_UNPARSEABLE, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        place_id_status=sie.PLACE_ID_DIFFERENT,
    )
    assert unsupported.identity_evidence_status == sie.CONFLICT

    # address evidence 不在 + conflict
    unavailable = sie.assess_identity_evidence(
        address_comparison=None,
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_DIFFERENT,
    )
    assert unavailable.identity_evidence_status == sie.CONFLICT

    # ambiguous address + conflict
    ambiguous = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_OAZA, ADDRESS_NO_OAZA),
        name_identity_status=sie.NAME_EXACT_MATCH,
        existing_resolution_status=sie.RESOLUTION_DIFFERENT,
    )
    assert ambiguous.identity_evidence_status == sie.CONFLICT


def test_unsupported_precedes_ambiguous_and_divergence():
    """2. unsupported/missing は 3/4 より先に効く。"""
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A_WITH_BUILDING),
        name_identity_status=None,  # NAME_UNSUPPORTED
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
    )
    assert result.identity_evidence_status == sie.INSUFFICIENT
    assert "NAME_EVIDENCE_UNAVAILABLE" in result.review_reasons


def test_ambiguous_name_is_review_required():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
        name_identity_status=sie.NAME_AMBIGUOUS,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
    )
    assert result.identity_evidence_status == sie.REVIEW_REQUIRED
    assert "NAME_EVIDENCE_AMBIGUOUS" in result.review_reasons


def test_official_source_ambiguous_is_not_a_corroborator():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A_DECORATED, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_AMBIGUOUS,
    )
    assert result.identity_evidence_status == sie.INSUFFICIENT
    assert "OFFICIAL_SOURCE_AMBIGUOUS_EVIDENCE" in result.review_reasons
    assert "INDEPENDENT_CORROBORATION_MISSING" in result.review_reasons


# ---------------------------------------------------------------------------
# fail-safe
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "fallback_field", "fallback_value"),
    [
        ("name_identity_status", "name_identity_status", "NAME_UNSUPPORTED"),
        (
            "official_source_entity_status",
            "official_source_entity_status",
            "OFFICIAL_SOURCE_UNAVAILABLE",
        ),
        ("place_id_status", "place_id_status", "PLACE_ID_UNAVAILABLE"),
        (
            "existing_resolution_status",
            "existing_resolution_status",
            "RESOLUTION_UNAVAILABLE",
        ),
    ],
)
def test_unknown_evidence_values_fail_safe(field, fallback_field, fallback_value):
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        **{field: "PROBABLY_THE_SAME"},
    )
    assert getattr(result, fallback_field) == fallback_value
    assert "UNKNOWN_EVIDENCE_VALUE" in result.review_reasons
    assert result.identity_evidence_status != sie.SAME_SUPPORTED


def test_evidence_values_are_case_and_whitespace_insensitive():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        name_identity_status="  name_exact_match  ",
        official_source_entity_status="official_source_same",
    )
    assert result.name_identity_status == sie.NAME_EXACT_MATCH
    assert result.identity_evidence_status == sie.SAME_SUPPORTED
    assert "UNKNOWN_EVIDENCE_VALUE" not in result.review_reasons


def test_no_evidence_at_all_is_insufficient():
    result = sie.assess_identity_evidence(address_comparison=None)
    assert result.identity_evidence_status == sie.INSUFFICIENT
    assert result.review_reasons == (
        "NAME_EVIDENCE_UNAVAILABLE",
        "ADDRESS_EVIDENCE_UNAVAILABLE",
    )


def test_layer_never_returns_a_canonical_entity_verdict():
    forbidden = ("SAME", "DIFFERENT", "NON_SHRINE")
    exported = {
        name: value
        for name, value in vars(sie).items()
        if isinstance(value, str) and not name.startswith("_")
    }
    for name, value in exported.items():
        assert value not in forbidden, name


# ---------------------------------------------------------------------------
# 決定性
# ---------------------------------------------------------------------------

DETERMINISM_CASES = [
    dict(
        address_comparison_pair=(ADDRESS_A, ADDRESS_A),
        name_identity_status="NAME_EXACT_MATCH",
        official_source_entity_status="OFFICIAL_SOURCE_SAME",
    ),
    dict(
        address_comparison_pair=(ADDRESS_A, ADDRESS_B),
        name_identity_status="NAME_EXACT_MATCH",
        place_id_status="PLACE_ID_DIFFERENT",
    ),
    dict(
        address_comparison_pair=(ADDRESS_OAZA, ADDRESS_NO_OAZA),
        name_identity_status="NAME_AMBIGUOUS",
        existing_resolution_status="RESOLUTION_SAME",
    ),
    dict(
        address_comparison_pair=(ADDRESS_A, ADDRESS_A_WITH_BUILDING),
        name_identity_status="NAME_ALIAS_CONFIRMED",
        official_source_entity_status="OFFICIAL_SOURCE_AMBIGUOUS",
    ),
]


@pytest.mark.parametrize("case", DETERMINISM_CASES)
def test_same_inputs_produce_identical_serialized_results(case):
    kwargs = dict(case)
    left, right = kwargs.pop("address_comparison_pair")
    runs = [
        sie.assess_identity_evidence(
            address_comparison=_address(left, right), **kwargs
        ).to_dict()
        for _ in range(5)
    ]
    assert all(run == runs[0] for run in runs)
    serialized = {json.dumps(run, ensure_ascii=False, sort_keys=True) for run in runs}
    assert len(serialized) == 1


def test_evidence_and_reason_order_follows_canonical_order_not_set_order():
    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
        official_source_entity_status=sie.OFFICIAL_SOURCE_SAME,
        place_id_status=sie.PLACE_ID_MATCH,
        existing_resolution_status=sie.RESOLUTION_SAME,
    )
    order = list(sie.EVIDENCE_ORDER)
    ranks = [order.index(value) for value in result.supporting_evidence]
    assert ranks == sorted(ranks)

    noisy = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A_WITH_BUILDING),
        name_identity_status="???",
        official_source_entity_status=sie.OFFICIAL_SOURCE_AMBIGUOUS,
    )
    reason_order = list(sie.REVIEW_REASON_ORDER)
    reason_ranks = [reason_order.index(reason) for reason in noisy.review_reasons]
    assert reason_ranks == sorted(reason_ranks)


def test_review_reasons_use_only_the_declared_vocabulary():
    for case in DETERMINISM_CASES:
        kwargs = dict(case)
        left, right = kwargs.pop("address_comparison_pair")
        result = sie.assess_identity_evidence(
            address_comparison=_address(left, right), **kwargs
        )
        for reason in result.review_reasons:
            assert reason in sie.REVIEW_REASONS, reason


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
        "os",
        "shutil",
        "subprocess",
        "random",
        "time",
        "datetime",
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
        "mkdir",
        "unlink",
        "system",
        "popen",
        "getenv",
        "environ",
        "now",
        "today",
    }
)


def test_module_has_no_db_network_or_write_path():
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


def _function_node(name: str):
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


def test_evaluation_core_performs_no_io_at_all():
    """評価 core は純粋。module bootstrap の I/O も持ち込まない。"""
    node = _function_node("assess_identity_evidence")
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            assert child.func.attr not in {
                "read_text",
                "read_bytes",
                "exec_module",
                "spec_from_file_location",
                "module_from_spec",
                "open",
                "glob",
                "exists",
            }, child.func.attr
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
            assert child.func.id not in {"open", "__import__"}


def test_result_model_is_immutable():
    import dataclasses

    result = sie.assess_identity_evidence(
        address_comparison=_address(ADDRESS_A, ADDRESS_A),
        name_identity_status=sie.NAME_EXACT_MATCH,
    )
    assert dataclasses.is_dataclass(result)
    assert type(result).__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.identity_evidence_status = "SAME_SUPPORTED"  # type: ignore[misc]


def test_evaluation_does_not_mutate_inputs():
    comparison = _address(ADDRESS_A_DECORATED, ADDRESS_A)
    before = comparison.to_dict()
    sie.assess_identity_evidence(
        address_comparison=comparison, name_identity_status=sie.NAME_EXACT_MATCH
    )
    assert comparison.to_dict() == before


# ---------------------------------------------------------------------------
# 非結線（P2-B04 scope）
# ---------------------------------------------------------------------------


def test_b03_is_not_wired_into_any_existing_caller():
    """**暫定の layer-boundary 不変条件**（P2-B03 時点）。

    現時点で B03 を消費する層は存在しない。ただしこれは恒久的な契約では
    なく、P2-B04 の導入によって **設計どおり失効する**。

    B04 実装時にはこの test を、B02 側と同じ厳密な allowlist 方式へ
    置き換えること。

    ```python
    SANCTIONED_CONSUMERS = {"scripts/<b04 module>.py"}
    assert set(callers) == SANCTIONED_CONSUMERS, callers
    ```

    `<=` ではなく `==` を使う（必要な依存が消えたことも検出するため）。
    推移的依存は上流の allowlist に載せない。B02 が sanction するのは
    B03 だけであり、B04 は B03 の allowlist にだけ載る。
    """
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == MODULE_PATH:
            continue
        if "shrine_identity_evidence" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert callers == [], callers


def test_position_audit_join_semantics_are_not_referenced():
    """Position Audit の join / status へ結線していないこと（B04 scope）。"""
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "join_seed_to_production",
        "JOIN_MATCH_EXACT",
        "JOIN_MATCH_NORMALIZED",
        "artifact_sync_status",
        "AUTO_PASS",
        "position_proof_path",
    ):
        assert forbidden not in source, forbidden
