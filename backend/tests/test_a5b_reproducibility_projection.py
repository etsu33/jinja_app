"""A-5b §10.1 reproducibility projection tests.

Contract: ``docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md``
§10.1. These tests read git-tracked records at HEAD. They live outside
``temples/tests`` so that no autouse ``db`` fixture applies: without a ``db``
fixture, pytest-django blocks every DB access, so any DB use fails the test. No
network access.

Generations here are development checks. They are not the contract run1 / run2.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest
from django.core.management import call_command
from temples.services.a5b_reproducibility_projection import (
    GitCommitReader,
    ProjectionUnresolved,
    build_projection,
    projection_sha256,
    serialize_projection,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
YASAKA = "docs/audit/collective-deity-a5b-yasaka-freeze-evidence.md"
ASO = "docs/audit/collective-deity-a5b-aso-freeze-evidence.md"

CANDIDATE_KEYS = {
    "a5b_freeze_status",
    "assertion_sources",
    "candidate_order",
    "collective",
    "memberships",
    "reason_code",
    "shrine_ref",
    "source_attested_label",
    "sources",
}
COLLECTIVE_KEYS = {
    "confidence",
    "member_count",
    "member_count_relation",
    "member_list_status",
    "role",
    "sort_order",
    "verification_status",
}
MEMBERSHIP_KEYS = {"confidence", "deity_ref", "sort_order", "verification_status"}


class OverlayReader:
    """Git reader with in-memory replacements, for negative cases."""

    def __init__(self, base: GitCommitReader, overrides: dict[str, str]) -> None:
        self.base = base
        self.overrides = overrides

    def read_text(self, path: str) -> str:
        if path in self.overrides:
            return self.overrides[path]
        return self.base.read_text(path)

    def list_paths(self, prefix: str) -> list[str]:
        paths = set(self.base.list_paths(prefix))
        paths.update(p for p in self.overrides if p.startswith(prefix))
        return sorted(paths)


@pytest.fixture(scope="module")
def reader() -> GitCommitReader:
    return GitCommitReader("HEAD", REPO_ROOT)


@pytest.fixture(scope="module")
def projection(reader: GitCommitReader) -> dict:
    return build_projection(reader)


def _by_order(projection: dict) -> dict[int, dict]:
    return {c["candidate_order"]: c for c in projection["candidates"]}


def _all_keys(value) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(key)
            keys |= _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            keys |= _all_keys(item)
    return keys


def _without_field_row(text: str, field: str) -> str:
    return re.sub(rf"^\| `{re.escape(field)}` \|.*\n", "", text, count=1, flags=re.M)


def test_exactly_ten_logical_candidates_in_candidate_order(projection):
    orders = [c["candidate_order"] for c in projection["candidates"]]
    assert orders == list(range(1, 11))
    assert projection["projection"] == "a5b-reproducibility-projection"
    assert projection["projection_version"] == 1


def test_repeated_generation_is_byte_identical(reader):
    first = serialize_projection(build_projection(reader))
    second = serialize_projection(build_projection(reader))
    assert first == second
    assert projection_sha256(first) == projection_sha256(second)


def test_canonical_serialization_rules(projection):
    data = serialize_projection(projection)
    assert not data.startswith(b"\xef\xbb\xbf")
    assert data.endswith(b"}\n") and not data.endswith(b"\n\n")
    assert data.count(b"\n") == 1
    assert b"\\u" not in data  # non-ASCII written literally
    assert data == (
        json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    # No whitespace outside strings: re-encoding the parsed value gives the same bytes.
    assert serialize_projection(json.loads(data.decode("utf-8"))) == data


def test_serialization_escapes_and_rejects_non_integer_numbers():
    assert serialize_projection({"b": "\x1f/\n", "a": 1}) == b'{"a":1,"b":"\\u001f/\\n"}\n'
    for bad in (True, 1.0):
        with pytest.raises(ProjectionUnresolved):
            serialize_projection({"a": bad})


def test_unicode_is_preserved_without_normalization(projection):
    candidates = _by_order(projection)
    tomioka = candidates[9]["source_attested_label"]
    assert tomioka == "応神天皇（誉田別命）外８柱"
    assert "８" in tomioka and "（" in tomioka
    assert unicodedata.normalize("NFKC", tomioka) != tomioka
    assert candidates[10]["source_attested_label"] == "健磐龍命をはじめ家族神12神"
    assert "応神天皇（誉田別命）外８柱".encode() in serialize_projection(projection)


def test_hold_candidate_projects_null_packet(projection):
    tomioka = _by_order(projection)[9]
    assert tomioka["a5b_freeze_status"] == "HOLD"
    assert tomioka["reason_code"] == "UNSATISFIED_FREEZE_CONDITIONS"
    for key in ("collective", "memberships", "sources", "assertion_sources"):
        assert tomioka[key] is None
    # The HOLD Artifact names a Source, but HOLD has no frozen packet.
    assert b"tomiokahachimangu" not in serialize_projection(projection)


@pytest.mark.parametrize("field", ["member_count", "role", "confidence", "reason_code"])
def test_freeze_candidate_missing_required_value_is_unresolved(reader, field):
    text = reader.read_text(YASAKA)
    mutated = _without_field_row(text, field)
    assert mutated != text
    with pytest.raises(ProjectionUnresolved):
        build_projection(OverlayReader(reader, {YASAKA: mutated}))


def test_invalidated_replacement_is_not_an_extra_candidate(projection):
    aso = [c for c in projection["candidates"] if c["shrine_ref"]["name_jp"] == "阿蘇神社"]
    assert len(aso) == 1
    assert aso[0]["candidate_order"] == 10
    assert aso[0]["a5b_freeze_status"] == "FREEZE"
    assert "健磐龍命をはじめ家族神１２神".encode() not in serialize_projection(projection)


def test_second_artifact_claiming_a_position_is_unresolved(reader):
    extra = "docs/audit/collective-deity-a5b-tomioka-second-evidence.md"
    overrides = {extra: "# A-5b Freeze Evidence Artifact — 富岡八幡宮\n"}
    with pytest.raises(ProjectionUnresolved):
        build_projection(OverlayReader(reader, overrides))


def test_pattern_b_read_from_contract_and_seed_without_artifacts(reader, projection):
    candidates = _by_order(projection)
    artifact_titles = [
        reader.read_text(p).split("\n", 1)[0]
        for p in reader.list_paths("docs/audit/collective-deity-a5b-")
    ]
    for order in range(1, 7):
        candidate = candidates[order]
        assert candidate["a5b_freeze_status"] == "FREEZE"
        assert candidate["reason_code"] == "ALL_FREEZE_CONDITIONS_SATISFIED"
        assert candidate["memberships"]
        assert not any(
            title.endswith("Evidence Artifact — " + candidate["shrine_ref"]["name_jp"])
            for title in artifact_titles
        )
    assert sum(len(candidates[o]["memberships"]) for o in range(1, 7)) == 23
    assert [m["deity_ref"]["display_name"] for m in candidates[1]["memberships"]] == [
        "瓊瓊杵尊",
        "木花咲耶姫命",
        "彦火火出見尊",
    ]


def test_counts_unchanged(projection):
    statuses = [c["a5b_freeze_status"] for c in projection["candidates"]]
    assert statuses.count("FREEZE") == 9
    assert statuses.count("HOLD") == 1
    assert statuses.count("EXCLUDE") == 0


def test_only_closed_list_keys_are_projected(projection):
    for candidate in projection["candidates"]:
        assert set(candidate) == CANDIDATE_KEYS
        assert set(candidate["shrine_ref"]) == {"address", "name_jp"}
        if candidate["collective"] is not None:
            assert set(candidate["collective"]) == COLLECTIVE_KEYS
            for member in candidate["memberships"]:
                assert set(member) == MEMBERSHIP_KEYS
    assert "resolved_shrine_id" not in _all_keys(projection)


def test_excluded_timestamps_notes_and_prose_do_not_enter_output(projection):
    keys = _all_keys(projection)
    for excluded in (
        "verified_at",
        "accessed_at",
        "note",
        "review_note",
        "excerpt",
        "location",
        "support_status",
        "source_key",
        "source_keys",
        "title",
        "publisher",
    ):
        assert excluded not in keys
    data = serialize_projection(projection).decode("utf-8")
    for prose in (
        "2026-10-02T12:35:39",
        "2026-10-01T21:08:33",
        "2026-08-10",
        "FREEZE: all applicable",
    ):
        assert prose not in data


def test_command_writes_canonical_bytes(tmp_path, projection):
    output = tmp_path / "projection.json"
    call_command("a5b_reproducibility_projection", "--commit", "HEAD", "--output", str(output))
    assert output.read_bytes() == serialize_projection(projection)


def test_git_reader_resolves_a_full_commit(reader):
    assert re.fullmatch(r"[0-9a-f]{40}", reader.commit)
