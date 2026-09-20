"""Canonical Production Candidate Linkage loader の regression。

正本契約: `docs/knowledge/production-candidate-linkage-contract.md`

固定する不変条件:

```text
1. artifact が無くても不正でも linkage を捏造しない
2. REVOKED は履歴として読めるが active にならない
3. 曖昧な active mapping は candidate 単位で fail closed
4. 同一 bytes は常に同一の結果を返す
5. loader は B02 / B03 / B04 / Position Audit / Production を触らない
```

本 file は DB・Django・ネットワーク・Production 資格情報をいっさい
必要としない。
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "production_candidate_linkage.py"
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "knowledge" / "production-candidate-linkage-contract.md"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


linkage = _load("production_candidate_linkage", MODULE_PATH)

SOURCE = MODULE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


# ---------------------------------------------------------------------------
# fixtures（すべて一時 file / in-memory。canonical artifact は作らない）
# ---------------------------------------------------------------------------


def _confirmed_row(**overrides):
    row = {
        "linkage_id": "wave0-007#1",
        "candidate_id": "wave0-007",
        "production_shrine_id": 114,
        "linkage_status": "CONFIRMED",
        "linkage_source": "PRODUCTION_RECONCILIATION",
        "verified_at": "2026-09-20",
        "official_name": "検証テスト神社",
        "official_address": "東京都千代田区丸の内1丁目1番1号",
        "evidence_refs": ["docs/audit/example.md", "pr:2893"],
        "note": "",
    }
    row.update(overrides)
    return row


def _revoked_row(**overrides):
    row = _confirmed_row(
        linkage_id="wave0-007#0",
        linkage_status="REVOKED",
        revoked_at="2026-09-21",
        revoked_reason="PRODUCTION_ROW_MERGED",
        revocation_evidence_refs=["docs/audit/revocation.md"],
    )
    row.update(overrides)
    return row


def _document(rows=None, **overrides):
    payload = {
        "schema_version": "production-candidate-linkage/1.0",
        "title": "KAMI MUSUBI Production Candidate Linkage",
        "contract": "docs/knowledge/production-candidate-linkage-contract.md",
        "recorded_at": "2026-09-20",
        "linkages": [] if rows is None else list(rows),
    }
    payload.update(overrides)
    return payload


def _write(tmp_path: Path, payload, name: str = "linkage.json") -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def _validate(payload):
    return linkage.validate_linkage_document(copy.deepcopy(payload))


def _codes(result):
    return set(result.issue_codes())


# ---------------------------------------------------------------------------
# artifact availability
# ---------------------------------------------------------------------------


def test_artifact_absent_is_a_valid_state(tmp_path):
    """artifact が無いのは正常。identity の問題の証拠ではない。"""
    result = linkage.load_linkage_artifact(tmp_path / "nope.json")
    assert result.artifact_state == linkage.ARTIFACT_NOT_PRESENT
    assert result.is_present is False
    assert result.rows == ()
    assert result.issues == ()
    assert result.active_linkages == {}
    assert result.active_linkage_for("wave0-007") is None
    assert linkage.active_linkage_map(result) == {}


def test_artifact_absence_is_distinguishable_from_invalid(tmp_path):
    absent = linkage.load_linkage_artifact(tmp_path / "nope.json")
    invalid = linkage.load_linkage_artifact(
        _write(tmp_path, {"schema_version": "other/9.9"})
    )
    assert absent.artifact_state == linkage.ARTIFACT_NOT_PRESENT
    assert invalid.artifact_state == linkage.ARTIFACT_INVALID
    assert absent.artifact_state != invalid.artifact_state


def test_loader_never_creates_the_artifact(tmp_path):
    target = tmp_path / "linkage.json"
    linkage.load_linkage_artifact(target)
    assert not target.exists()


def test_canonical_artifact_is_not_committed():
    """canonical artifact を本 PR で作らない。"""
    assert not linkage.DEFAULT_ARTIFACT_PATH.exists()
    result = linkage.load_linkage_artifact()
    assert result.artifact_state == linkage.ARTIFACT_NOT_PRESENT
    assert linkage.active_linkage_map(result) == {}


def test_unreadable_artifact_is_invalid_not_absent(tmp_path):
    directory = tmp_path / "linkage.json"
    directory.mkdir()
    result = linkage.load_linkage_artifact(directory)
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ARTIFACT_UNREADABLE in _codes(result)
    assert result.active_linkages == {}


def test_non_json_artifact_is_invalid(tmp_path):
    path = tmp_path / "linkage.json"
    path.write_text("{ not json", encoding="utf-8")
    result = linkage.load_linkage_artifact(path)
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ARTIFACT_NOT_JSON in _codes(result)


def test_json_list_top_level_is_invalid(tmp_path):
    result = linkage.load_linkage_artifact(_write(tmp_path, []))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ARTIFACT_NOT_OBJECT in _codes(result)


# ---------------------------------------------------------------------------
# 有効な artifact
# ---------------------------------------------------------------------------


def test_valid_empty_artifact(tmp_path):
    result = linkage.load_linkage_artifact(_write(tmp_path, _document()))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.is_valid is True
    assert result.rows == ()
    assert result.issues == ()
    assert result.active_linkages == {}
    assert result.schema_version == linkage.SUPPORTED_SCHEMA_VERSION
    assert result.recorded_at == "2026-09-20"


def test_valid_confirmed_row_is_queryable(tmp_path):
    result = linkage.load_linkage_artifact(
        _write(tmp_path, _document([_confirmed_row()]))
    )
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.issues == ()
    assert len(result.rows) == 1

    row = result.active_linkage_for("wave0-007")
    assert row is not None
    assert row.production_shrine_id == 114
    assert row.linkage_status == linkage.STATUS_CONFIRMED
    assert row.is_active is True
    assert row.evidence_refs == ("docs/audit/example.md", "pr:2893")
    assert linkage.active_linkage_map(result) == {"wave0-007": 114}


def test_valid_revoked_row_loads_as_history(tmp_path):
    result = linkage.load_linkage_artifact(
        _write(tmp_path, _document([_revoked_row()]))
    )
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.issues == ()
    assert len(result.rows) == 1

    row = result.rows[0]
    assert row.linkage_status == linkage.STATUS_REVOKED
    assert row.is_active is False
    assert row.revoked_at == "2026-09-21"
    assert row.revoked_reason == "PRODUCTION_ROW_MERGED"
    assert row.revocation_evidence_refs == ("docs/audit/revocation.md",)


def test_supersedes_is_optional_and_accepted(tmp_path):
    for value in (None, "wave0-007#0"):
        payload = _document([_confirmed_row(supersedes=value)])
        result = linkage.load_linkage_artifact(_write(tmp_path, payload))
        assert result.artifact_state == linkage.ARTIFACT_VALID, value
        assert result.rows[0].supersedes == value

    # 省略しても valid（MS-FOLLOWUP-03 は未決のため必須化しない）。
    row = _confirmed_row()
    assert "supersedes" not in row
    result = linkage.load_linkage_artifact(_write(tmp_path, _document([row])))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.rows[0].supersedes is None


def test_supersedes_empty_string_is_invalid():
    result = _validate(_document([_confirmed_row(supersedes="")]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_FIELD_EMPTY in _codes(result)


# ---------------------------------------------------------------------------
# schema version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "version",
    [
        "production-candidate-linkage/1.1",
        "production-candidate-linkage/0.9",
        "production-candidate-linkage/2.0",
        "production-candidate-linkage",
        "",
    ],
)
def test_unknown_schema_version_fails_closed(version):
    """未知の版を部分 parse しない。暗黙の up/down grade もしない。"""
    result = _validate(_document([_confirmed_row()], schema_version=version))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_SCHEMA_VERSION_UNSUPPORTED in _codes(result)
    assert result.rows == ()
    assert result.active_linkages == {}
    assert result.active_linkage_for("wave0-007") is None


def test_only_one_schema_version_is_supported():
    assert linkage.SUPPORTED_SCHEMA_VERSION == "production-candidate-linkage/1.0"


# ---------------------------------------------------------------------------
# top-level 構造
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field_name", linkage.TOP_LEVEL_FIELDS)
def test_missing_top_level_field_is_invalid(field_name):
    payload = _document([_confirmed_row()])
    payload.pop(field_name)
    result = _validate(payload)
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_TOP_LEVEL_FIELD_MISSING in _codes(result)
    assert result.active_linkages == {}


def test_unknown_top_level_field_is_invalid():
    result = _validate(_document([], extra_field="x"))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_TOP_LEVEL_FIELD_UNKNOWN in _codes(result)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", ""),
        ("title", 1),
        ("contract", 1),
        ("linkages", {}),
        ("linkages", "rows"),
    ],
)
def test_top_level_type_violations_are_invalid(field_name, value):
    result = _validate(_document([], **{field_name: value}))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_TOP_LEVEL_FIELD_TYPE in _codes(result)


def test_unexpected_contract_path_is_invalid():
    result = _validate(_document([], contract="docs/audit/other.md"))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_CONTRACT_PATH_UNEXPECTED in _codes(result)


def test_row_that_is_not_an_object_is_invalid():
    result = _validate(_document(["not a row"]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_NOT_OBJECT in _codes(result)


# ---------------------------------------------------------------------------
# row schema
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field_name", linkage.COMMON_ROW_FIELDS)
def test_missing_common_row_field_is_invalid(field_name):
    row = _confirmed_row()
    row.pop(field_name)
    result = _validate(_document([row]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_FIELD_MISSING in _codes(result)
    assert result.rows == ()


def test_unknown_row_field_is_invalid():
    result = _validate(_document([_confirmed_row(new_field="x")]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_FIELD_UNKNOWN in _codes(result)


@pytest.mark.parametrize(
    "status", ["confirmed", "PENDING", "REVIEW_REQUIRED", "ACTIVE", ""]
)
def test_unknown_linkage_status_is_invalid(status):
    result = _validate(_document([_confirmed_row(linkage_status=status)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_LINKAGE_STATUS_UNKNOWN in _codes(result)


@pytest.mark.parametrize(
    "source", ["POSITION_RESOLUTION_RECORD", "SPREADSHEET", "production_reconciliation", ""]
)
def test_unknown_linkage_source_is_invalid(source):
    result = _validate(_document([_confirmed_row(linkage_source=source)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_LINKAGE_SOURCE_UNKNOWN in _codes(result)


@pytest.mark.parametrize(
    "reason", ["PRODUCTION_ROW_MOVED", "production_row_merged", "OTHER", ""]
)
def test_unknown_revoked_reason_is_invalid(reason):
    result = _validate(_document([_revoked_row(revoked_reason=reason)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_REVOKED_REASON_UNKNOWN in _codes(result)


def test_closed_vocabularies_match_the_contract():
    assert linkage.LINKAGE_STATUSES == {"CONFIRMED", "REVOKED"}
    assert linkage.LINKAGE_SOURCES == {
        "PRODUCTION_RECONCILIATION",
        "HUMAN_IDENTITY_ADJUDICATION",
        "MIGRATION_RECORD",
    }
    assert linkage.REVOKED_REASONS == {
        "PRODUCTION_ROW_DELETED",
        "PRODUCTION_ROW_MERGED",
        "PRODUCTION_ROW_RECREATED",
        "PRODUCTION_ROW_RENUMBERED",
        "PRODUCTION_ROW_SUPERSEDED",
        "IDENTITY_ADJUDICATION_REVERSED",
    }


@pytest.mark.parametrize("source", sorted(linkage.LINKAGE_SOURCES))
def test_every_contract_source_is_accepted(source):
    result = _validate(_document([_confirmed_row(linkage_source=source)]))
    assert result.artifact_state == linkage.ARTIFACT_VALID


@pytest.mark.parametrize("reason", sorted(linkage.REVOKED_REASONS))
def test_every_contract_revoked_reason_is_accepted(reason):
    result = _validate(_document([_revoked_row(revoked_reason=reason)]))
    assert result.artifact_state == linkage.ARTIFACT_VALID


# ---------------------------------------------------------------------------
# date
# ---------------------------------------------------------------------------

INVALID_DATES = [
    "2026/09/20",
    "20260920",
    "2026-9-20",
    "2026-09-20T00:00:00",
    "2026-09-20 00:00",
    "2026-13-01",
    "2026-02-30",
    "",
    "yesterday",
]


@pytest.mark.parametrize("value", INVALID_DATES)
def test_invalid_verified_at_is_invalid(value):
    result = _validate(_document([_confirmed_row(verified_at=value)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_DATE_FORMAT_INVALID in _codes(result)


@pytest.mark.parametrize("value", INVALID_DATES)
def test_invalid_recorded_at_is_invalid(value):
    result = _validate(_document([], recorded_at=value))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_DATE_FORMAT_INVALID in _codes(result)


@pytest.mark.parametrize("value", INVALID_DATES)
def test_invalid_revoked_at_is_invalid(value):
    result = _validate(_document([_revoked_row(revoked_at=value)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_DATE_FORMAT_INVALID in _codes(result)


def test_dates_are_not_inferred_when_missing():
    row = _revoked_row()
    row.pop("revoked_at")
    result = _validate(_document([row]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert result.rows == ()


# ---------------------------------------------------------------------------
# linkage_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "wave0-007",
        "wave0-007#",
        "#1",
        "wave0-008#1",
        "wave0-007#a",
        "wave0-007#1#2",
        "",
    ],
)
def test_malformed_linkage_id_is_invalid(value):
    """`<candidate_id>#<連番>` を満たさない id は修復せず不正にする。"""
    result = _validate(_document([_confirmed_row(linkage_id=value)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_LINKAGE_ID_MALFORMED in _codes(result)
    assert result.rows == ()


def test_duplicate_linkage_id_is_invalid():
    rows = [
        _revoked_row(linkage_id="wave0-007#1"),
        _confirmed_row(linkage_id="wave0-007#1"),
    ]
    result = _validate(_document(rows))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_LINKAGE_ID_DUPLICATE in _codes(result)
    assert result.active_linkages == {}


# ---------------------------------------------------------------------------
# production_shrine_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["114", 114.0, None, True, False])
def test_non_integer_production_shrine_id_is_invalid(value):
    result = _validate(_document([_confirmed_row(production_shrine_id=value)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_FIELD_TYPE in _codes(result)


@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_production_shrine_id_is_invalid(value):
    result = _validate(_document([_confirmed_row(production_shrine_id=value)]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_PRODUCTION_SHRINE_ID_INVALID in _codes(result)


# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

REPOSITORY_TRACEABLE = [
    "README.md",
    "docs/audit/example.md",
    "docs/audit/example.md#gate-result",
    "git:" + "a" * 40,
    "git:" + "0123456789abcdef0123456789abcdef01234567",
    "pr:2893",
]

NOT_REPOSITORY_TRACEABLE = [
    "https://example.invalid/evidence",
    "http://example.invalid/evidence",
    "ftp://example.invalid/evidence",
]

UNRECOGNIZED = [
    "/absolute/path.md",
    "~/home/path.md",
    "../escape.md",
    "./relative.md",
    "docs//double.md",
    "docs\\windows.md",
    "docs/with space.md",
    "docs/example.md#",
    "git:abc",
    "git:" + "a" * 41,
    "pr:0",
    "pr:abc",
    "mailto:someone@example.invalid",
]


@pytest.mark.parametrize("value", REPOSITORY_TRACEABLE)
def test_repository_traceable_forms_are_recognized(value):
    assert linkage.is_repository_traceable(value) is True


@pytest.mark.parametrize("value", NOT_REPOSITORY_TRACEABLE)
def test_external_urls_are_not_repository_traceable(value):
    assert (
        linkage.classify_evidence_ref(value) == linkage.EVIDENCE_FORM_EXTERNAL_URL
    )
    assert linkage.is_repository_traceable(value) is False


@pytest.mark.parametrize("value", UNRECOGNIZED)
def test_unrecognized_forms_are_rejected(value):
    assert (
        linkage.classify_evidence_ref(value) == linkage.EVIDENCE_FORM_UNRECOGNIZED
    )
    assert linkage.is_repository_traceable(value) is False


def test_urls_are_never_classified_as_repository_paths():
    """任意の URL を repo-relative path と誤認しない。"""
    for value in NOT_REPOSITORY_TRACEABLE:
        assert (
            linkage.classify_evidence_ref(value) != linkage.EVIDENCE_FORM_REPO_PATH
        )


def test_missing_confirmation_evidence_is_invalid():
    result = _validate(_document([_confirmed_row(evidence_refs=[])]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_EMPTY in _codes(result)


def test_external_url_only_confirmation_evidence_is_invalid():
    result = _validate(
        _document([_confirmed_row(evidence_refs=["https://example.invalid/a"])])
    )
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_NOT_REPOSITORY_TRACEABLE in _codes(result)


def test_external_url_is_accepted_as_supplementary_evidence():
    refs = sorted(["docs/audit/example.md", "https://example.invalid/a"])
    result = _validate(_document([_confirmed_row(evidence_refs=refs)]))
    assert result.artifact_state == linkage.ARTIFACT_VALID


def test_unsorted_evidence_is_invalid():
    result = _validate(
        _document([_confirmed_row(evidence_refs=["pr:2893", "docs/a.md"])])
    )
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_UNSORTED in _codes(result)


def test_duplicate_evidence_is_invalid():
    result = _validate(
        _document([_confirmed_row(evidence_refs=["docs/a.md", "docs/a.md"])])
    )
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_DUPLICATE in _codes(result)


def test_empty_evidence_value_is_invalid():
    result = _validate(
        _document([_confirmed_row(evidence_refs=["", "docs/a.md"])])
    )
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_VALUE_EMPTY in _codes(result)


def test_evidence_must_be_a_list_of_strings():
    for value in ("docs/a.md", [1], {"a": 1}):
        result = _validate(_document([_confirmed_row(evidence_refs=value)]))
        assert result.artifact_state == linkage.ARTIFACT_INVALID
        assert linkage.ISSUE_ROW_FIELD_TYPE in _codes(result)


# --- revocation evidence ---------------------------------------------------


@pytest.mark.parametrize("field_name", linkage.REVOKED_ROW_FIELDS)
def test_revoked_row_requires_every_revocation_field(field_name):
    row = _revoked_row()
    row.pop(field_name)
    result = _validate(_document([row]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_ROW_FIELD_MISSING in _codes(result)
    assert result.rows == ()


def test_missing_revocation_evidence_is_invalid():
    result = _validate(_document([_revoked_row(revocation_evidence_refs=[])]))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_EMPTY in _codes(result)


def test_revoked_row_with_bad_revocation_evidence_is_not_parsed_as_a_row():
    """失効 evidence が不正な row は `rows` にも残さない。

    artifact が INVALID になることとは別に、**その row を成立した記録
    として扱わない**ことを固定する。
    """
    for refs in ([], ["https://example.invalid/why"], ["docs/a.md", "docs/a.md"]):
        result = _validate(
            _document([_revoked_row(revocation_evidence_refs=refs)])
        )
        assert result.artifact_state == linkage.ARTIFACT_INVALID, refs
        assert result.rows == (), refs


def test_external_url_only_revocation_evidence_is_invalid():
    result = _validate(
        _document(
            [
                _revoked_row(
                    revocation_evidence_refs=["https://example.invalid/why"]
                )
            ]
        )
    )
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.ISSUE_EVIDENCE_NOT_REPOSITORY_TRACEABLE in _codes(result)


def test_unsorted_and_duplicate_revocation_evidence_are_invalid():
    unsorted_result = _validate(
        _document(
            [_revoked_row(revocation_evidence_refs=["pr:1", "docs/a.md"])]
        )
    )
    assert linkage.ISSUE_EVIDENCE_UNSORTED in _codes(unsorted_result)

    duplicate_result = _validate(
        _document(
            [_revoked_row(revocation_evidence_refs=["docs/a.md", "docs/a.md"])]
        )
    )
    assert linkage.ISSUE_EVIDENCE_DUPLICATE in _codes(duplicate_result)


def test_confirmation_and_revocation_evidence_are_not_merged():
    """2つの evidence 集合を混ぜない。"""
    row = _revoked_row(
        evidence_refs=["docs/confirmation.md"],
        revocation_evidence_refs=["docs/revocation.md"],
    )
    result = _validate(_document([row]))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    parsed = result.rows[0]
    assert parsed.evidence_refs == ("docs/confirmation.md",)
    assert parsed.revocation_evidence_refs == ("docs/revocation.md",)
    assert set(parsed.evidence_refs).isdisjoint(parsed.revocation_evidence_refs)


def test_revocation_evidence_is_never_used_for_an_active_lookup():
    row = _confirmed_row()
    result = _validate(_document([row]))
    active = result.active_linkage_for("wave0-007")
    assert active is not None
    assert active.revocation_evidence_refs == ()
    assert active.revoked_at is None
    assert active.revoked_reason is None


def test_confirmed_row_cannot_carry_revocation_fields():
    for field_name in linkage.REVOKED_ROW_FIELDS:
        row = _confirmed_row(**{field_name: "x"})
        result = _validate(_document([row]))
        assert result.artifact_state == linkage.ARTIFACT_INVALID, field_name
        assert linkage.ISSUE_REVOKED_FIELD_PRESENT_ON_CONFIRMED in _codes(result)


# ---------------------------------------------------------------------------
# current-state invariants
# ---------------------------------------------------------------------------


def test_duplicate_active_candidate_fails_closed_for_that_candidate():
    """INV-5: どちらも選ばない。当該 candidate だけ active なし。"""
    rows = [
        _confirmed_row(linkage_id="wave0-007#1", production_shrine_id=114),
        _confirmed_row(linkage_id="wave0-007#2", production_shrine_id=115),
    ]
    result = _validate(_document(rows))
    # artifact 全体は不正にしない（契約 §7.1）。
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert linkage.ISSUE_ACTIVE_CANDIDATE_DUPLICATE in _codes(result)
    assert result.active_linkage_for("wave0-007") is None
    assert linkage.active_linkage_map(result) == {}
    assert len(result.rows) == 2


def test_multiple_historical_revoked_rows_are_allowed():
    rows = [
        _revoked_row(linkage_id="wave0-007#1", revoked_at="2026-09-18"),
        _revoked_row(linkage_id="wave0-007#2", revoked_at="2026-09-19"),
        _confirmed_row(linkage_id="wave0-007#3"),
    ]
    result = _validate(_document(rows))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.issues == ()
    assert len(result.rows) == 3
    active = result.active_linkage_for("wave0-007")
    assert active is not None
    assert active.linkage_id == "wave0-007#3"


def test_revoked_row_is_never_returned_as_active():
    result = _validate(_document([_revoked_row()]))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.active_linkage_for("wave0-007") is None
    assert linkage.active_linkage_map(result) == {}
    assert result.rows[0].is_active is False


def test_reverse_production_id_ambiguity_fails_closed_for_all_affected():
    """§7.4 暫定: 同一 production_shrine_id の active が複数なら全員を塞ぐ。"""
    rows = [
        _confirmed_row(
            linkage_id="wave0-007#1",
            candidate_id="wave0-007",
            production_shrine_id=114,
        ),
        _confirmed_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            production_shrine_id=114,
        ),
    ]
    result = _validate(_document(rows))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert linkage.ISSUE_ACTIVE_PRODUCTION_ID_AMBIGUOUS in _codes(result)
    assert result.active_linkage_for("wave0-007") is None
    assert result.active_linkage_for("wave0-008") is None
    assert linkage.active_linkage_map(result) == {}
    # row はどれも削除も選択もしない。
    assert len(result.rows) == 2


def test_unaffected_candidate_remains_usable_alongside_ambiguity():
    rows = [
        _confirmed_row(
            linkage_id="wave0-007#1",
            candidate_id="wave0-007",
            production_shrine_id=114,
        ),
        _confirmed_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            production_shrine_id=114,
        ),
        _confirmed_row(
            linkage_id="wave0-009#1",
            candidate_id="wave0-009",
            production_shrine_id=116,
        ),
    ]
    result = _validate(_document(rows))
    assert result.active_linkage_for("wave0-009") is not None
    assert linkage.active_linkage_map(result) == {"wave0-009": 116}


def test_revoked_rows_do_not_create_reverse_ambiguity():
    rows = [
        _revoked_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            production_shrine_id=114,
        ),
        _confirmed_row(
            linkage_id="wave0-007#1",
            candidate_id="wave0-007",
            production_shrine_id=114,
        ),
    ]
    result = _validate(_document(rows))
    assert result.issues == ()
    assert linkage.active_linkage_map(result) == {"wave0-007": 114}


def test_missing_candidate_returns_no_active_linkage():
    result = _validate(_document([_confirmed_row()]))
    assert result.active_linkage_for("wave0-999") is None
    assert result.active_linkage_for("") is None


def test_no_global_production_id_uniqueness_invariant_is_invented():
    """MS-FOLLOWUP-02 を解決しない。

    REVOKED を含めれば同一 production_shrine_id が複数 row に現れてよい。
    禁止ではなく「未決なので active では通さない」に留める。
    """
    rows = [
        _revoked_row(
            linkage_id="wave0-007#1",
            candidate_id="wave0-007",
            production_shrine_id=114,
        ),
        _revoked_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            production_shrine_id=114,
        ),
    ]
    result = _validate(_document(rows))
    assert result.artifact_state == linkage.ARTIFACT_VALID
    assert result.issues == ()


# ---------------------------------------------------------------------------
# 捏造しないこと（regression）
# ---------------------------------------------------------------------------


def test_absent_artifact_never_fabricates_linkage(tmp_path):
    result = linkage.load_linkage_artifact(tmp_path / "absent.json")
    assert linkage.active_linkage_map(result) == {}
    for candidate_id in ("wave0-007", "wave0-010", "wave0-011"):
        assert result.active_linkage_for(candidate_id) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "production-candidate-linkage/9.9"},
        {},
        [],
        "text",
        123,
    ],
)
def test_invalid_artifact_never_fabricates_linkage(payload):
    result = linkage.validate_linkage_document(payload)
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert linkage.active_linkage_map(result) == {}
    assert result.active_linkage_for("wave0-007") is None


def test_lookup_refuses_an_invalid_artifact_even_if_active_map_is_populated():
    """`active_linkage_for` 自身が artifact 妥当性を確認すること。

    `active_linkages` が空であることに依存しない二重の防御であり、
    その防御が実際に効いていることを直接固定する。
    """
    row = _validate(_document([_confirmed_row()])).rows[0]
    tampered = linkage.LinkageArtifact(
        artifact_state=linkage.ARTIFACT_INVALID,
        path="in-memory",
        active_linkages={"wave0-007": row},
    )
    assert tampered.active_linkage_for("wave0-007") is None
    assert linkage.active_linkage_map(tampered) == {}

    absent = linkage.LinkageArtifact(
        artifact_state=linkage.ARTIFACT_NOT_PRESENT,
        path="in-memory",
        active_linkages={"wave0-007": row},
    )
    assert absent.active_linkage_for("wave0-007") is None
    assert linkage.active_linkage_map(absent) == {}


def test_row_level_failure_blocks_every_active_linkage():
    """1 row でも schema 違反があれば active を1件も返さない。"""
    rows = [
        _confirmed_row(linkage_id="wave0-007#1", candidate_id="wave0-007"),
        _confirmed_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            linkage_source="UNKNOWN_SOURCE",
        ),
    ]
    result = _validate(_document(rows))
    assert result.artifact_state == linkage.ARTIFACT_INVALID
    assert result.active_linkages == {}
    assert result.active_linkage_for("wave0-007") is None


# ---------------------------------------------------------------------------
# 決定性
# ---------------------------------------------------------------------------


def test_same_bytes_produce_the_same_result(tmp_path):
    payload = _document(
        [
            _confirmed_row(
                linkage_id="wave0-008#1",
                candidate_id="wave0-008",
                production_shrine_id=115,
            ),
            _revoked_row(),
            _confirmed_row(),
        ]
    )
    path = _write(tmp_path, payload)
    first = linkage.load_linkage_artifact(path)
    second = linkage.load_linkage_artifact(path)

    assert first.artifact_state == second.artifact_state
    assert first.rows == second.rows
    assert first.issues == second.issues
    assert dict(first.active_linkages) == dict(second.active_linkages)
    assert linkage.dump_json(first) == linkage.dump_json(second)


def test_issue_ordering_is_canonical_and_input_order_independent():
    rows_a = [
        _confirmed_row(linkage_id="bad-id"),
        _confirmed_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            linkage_source="UNKNOWN_SOURCE",
        ),
    ]
    rows_b = list(reversed(rows_a))
    codes_a = _validate(_document(rows_a)).issue_codes()
    codes_b = _validate(_document(rows_b)).issue_codes()
    assert set(codes_a) == set(codes_b)

    ranks = [linkage.ISSUE_CODE_ORDER.index(code) for code in codes_a]
    assert ranks == sorted(ranks)


def test_all_issue_codes_are_in_the_canonical_order_tuple():
    assert len(linkage.ISSUE_CODE_ORDER) == len(set(linkage.ISSUE_CODE_ORDER))
    assert set(linkage.ISSUE_CODE_ORDER) == linkage.ISSUE_CODES
    for name, value in vars(linkage).items():
        if name.startswith("ISSUE_") and isinstance(value, str):
            assert value in linkage.ISSUE_CODES, name


def test_active_linkage_map_is_sorted_by_candidate_id():
    rows = [
        _confirmed_row(
            linkage_id="wave0-009#1",
            candidate_id="wave0-009",
            production_shrine_id=116,
        ),
        _confirmed_row(
            linkage_id="wave0-007#1",
            candidate_id="wave0-007",
            production_shrine_id=114,
        ),
        _confirmed_row(
            linkage_id="wave0-008#1",
            candidate_id="wave0-008",
            production_shrine_id=115,
        ),
    ]
    result = _validate(_document(rows))
    assert list(linkage.active_linkage_map(result)) == [
        "wave0-007",
        "wave0-008",
        "wave0-009",
    ]


def test_diagnostic_dump_is_stable_and_sorted(tmp_path):
    result = _validate(_document([_confirmed_row(), _revoked_row()]))
    dumped = linkage.dump_json(result)
    assert dumped == linkage.dump_json(result)
    payload = json.loads(dumped)
    assert payload["artifact_state"] == linkage.ARTIFACT_VALID
    assert payload["row_count"] == 2
    assert payload["active_candidate_ids"] == ["wave0-007"]
    assert list(payload) == sorted(payload)


# ---------------------------------------------------------------------------
# 責務境界（consumer / Production / network を触らない）
# ---------------------------------------------------------------------------

FORBIDDEN_IMPORT_ROOTS = {
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
    "importlib",
}


def test_loader_imports_nothing_that_reaches_db_network_or_consumers():
    for node in ast.walk(TREE):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, node.module


def test_loader_does_not_reference_b02_b03_b04_or_position_audit():
    for forbidden in (
        "audit_shrine_positions_v2",
        "build_position_identity_evidence",
        "compare_addresses",
        "assess_identity_evidence",
        "integrate_position_identity",
        "join_seed_to_production",
        "SAME_SUPPORTED",
    ):
        assert forbidden not in SOURCE, forbidden


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """module / class / function の docstring node id を集める。

    docstring は「使わない語彙」を説明のために書くことがあるため、
    実行コードの走査から除く。
    """
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(
                first.value, ast.Constant
            ):
                if isinstance(first.value.value, str):
                    ids.add(id(first.value))
    return ids


def test_loader_does_not_introduce_position_audit_vocabulary():
    """Position Audit の status 語彙を **実行コードに** 持ち込まない。

    docstring がそれらを「使わない」と説明することは許す。
    """
    forbidden = {"PASS", "HOLD", "REVIEW", "AUTO_PASS", "HOLD_POSITION_REVIEW"}
    skip = _docstring_nodes(TREE)
    for node in ast.walk(TREE):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in skip:
                continue
            assert node.value not in forbidden, node.value
        if isinstance(node, ast.Name):
            assert node.id not in forbidden, node.id

    for name, value in vars(linkage).items():
        if isinstance(value, str) and name.isupper():
            assert value not in forbidden, name


def test_loader_performs_no_production_or_credential_access():
    for forbidden in (
        "DATABASE_URL",
        "environ",
        "getenv",
        "connect(",
        "psql",
        "readonly_query",
        "production-db.env",
    ):
        assert forbidden not in SOURCE, forbidden


def test_loader_never_writes(tmp_path):
    for node in ast.walk(TREE):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None)
            assert name not in {
                "write_text",
                "write_bytes",
                "mkdir",
                "unlink",
                "touch",
                "rmdir",
            }, name

    path = _write(tmp_path, _document([_confirmed_row()]))
    before = path.read_bytes()
    linkage.load_linkage_artifact(path)
    assert path.read_bytes() == before


def test_loader_module_is_not_wired_into_any_consumer():
    """本 PR は foundation のみ。consumer へは接続しない。"""
    callers = []
    for path in sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(
        (REPO_ROOT / "backend").rglob("*.py")
    ):
        if path == MODULE_PATH:
            continue
        if "production_candidate_linkage" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert callers == [], callers


# ---------------------------------------------------------------------------
# 契約との対応
# ---------------------------------------------------------------------------


def test_contract_document_exists_and_is_referenced():
    assert CONTRACT_DOC.exists()
    assert linkage.CONTRACT_PATH == str(
        CONTRACT_DOC.relative_to(REPO_ROOT)
    ).replace("\\", "/")


def test_row_field_sets_match_the_contract():
    assert linkage.COMMON_ROW_FIELDS == (
        "linkage_id",
        "candidate_id",
        "production_shrine_id",
        "linkage_status",
        "linkage_source",
        "verified_at",
        "official_name",
        "official_address",
        "evidence_refs",
        "note",
    )
    assert linkage.REVOKED_ROW_FIELDS == (
        "revoked_at",
        "revoked_reason",
        "revocation_evidence_refs",
    )
    assert linkage.OPTIONAL_ROW_FIELDS == ("supersedes",)
    assert linkage.ALLOWED_ROW_FIELDS == set(
        linkage.COMMON_ROW_FIELDS
        + linkage.REVOKED_ROW_FIELDS
        + linkage.OPTIONAL_ROW_FIELDS
    )


def test_w1_mutation_boundary_is_recorded_but_not_enforced():
    """契約 §7.2 の集合は保持するが、履歴検証は行わない。

    現在の artifact 1枚からは、過去に immutable field が書き換えられ
    なかったことを証明できない。git history も読まない。
    """
    assert linkage.W1_MUTABLE_FIELDS == (
        "linkage_status",
        "revoked_at",
        "revoked_reason",
        "revocation_evidence_refs",
    )
    assert linkage.POST_CONFIRMATION_IMMUTABLE_FIELDS == (
        "candidate_id",
        "production_shrine_id",
        "linkage_source",
        "verified_at",
        "official_name",
        "official_address",
        "evidence_refs",
        "linkage_id",
    )
    # git history を読む経路が存在しないこと。
    for forbidden in ("git log", "git show", "gitpython", "dulwich", ".git"):
        assert forbidden not in SOURCE, forbidden


def test_module_documents_the_temporal_limitation():
    doc = linkage.__doc__ or ""
    assert "mutation" in doc
    assert "git history" in doc
