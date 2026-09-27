"""Knowledge Seed 1.1 Collective / Membership import（A-5a）。

契約: docs/audit/collective-deity-knowledge-seed-v1-1-contract.md
"""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.knowledge_seed import (
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    parse_seed,
)

SHRINE_NAME = "集合祭神試験神社"
SHRINE_ADDRESS = "東京都試験区1-1-1"
VERIFIED_AT = "2026-09-27T00:00:00+09:00"
SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds"


def _source(key: str, url: str) -> dict:
    return {
        "key": key,
        "source_type": "shrine_official",
        "title": f"御祭神 {key}",
        "publisher": "集合祭神試験神社",
        "url": url,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
    }


def _deity(name: str, **overrides) -> dict:
    deity = {
        "display_name": name,
        "role": "enshrined",
        "verification_status": "source_confirmed",
        "verified_at": VERIFIED_AT,
        "confidence": "high",
        "source_keys": ["src-group"],
    }
    deity.update(overrides)
    return deity


def _membership(name: str, source_key: str, **overrides) -> dict:
    membership = {
        "deity_ref": {"display_name": name},
        "sort_order": 0,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
        "note": "",
        "source_keys": [source_key],
    }
    membership.update(overrides)
    return membership


def _collective(**overrides) -> dict:
    collective = {
        "source_attested_label": "祭神A・祭神B",
        "role": "enshrined",
        "sort_order": 2,
        "member_count": 2,
        "member_count_relation": "exact",
        "member_list_status": "complete",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
        "note": "",
        "source_keys": ["src-group"],
        "memberships": [
            _membership("祭神A", "src-member-a"),
            _membership("祭神B", "src-member-b", sort_order=1),
        ],
    }
    collective.update(overrides)
    return collective


def _seed_v11(**block_overrides) -> dict:
    block = {
        "shrine_ref": {"name_jp": SHRINE_NAME, "address": SHRINE_ADDRESS},
        "deities": [_deity("祭神A"), _deity("祭神B")],
        "histories": [],
        "collectives": [_collective()],
    }
    block.update(block_overrides)
    return {
        "schema_version": "1.1",
        "sources": [
            _source("src-group", "https://collective.example.jp/saijin"),
            _source("src-member-a", "https://collective.example.jp/member-a"),
            _source("src-member-b", "https://collective.example.jp/member-b"),
        ],
        "shrines": [block],
    }


def _errors(seed: dict) -> list[str]:
    return parse_seed(seed).errors


def _collective_errors(**overrides) -> list[str]:
    return _errors(_seed_v11(collectives=[_collective(**overrides)]))


def _write(tmp_path, seed: dict, name: str = "seed.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _run(path: str, *args: str) -> str:
    out = io.StringIO()
    call_command("import_shrine_knowledge", path, *args, stdout=out, stderr=io.StringIO())
    return out.getvalue()


def _run_blocked(path: str, *args: str) -> str:
    out, err = io.StringIO(), io.StringIO()
    with pytest.raises(CommandError, match="import blocked"):
        call_command("import_shrine_knowledge", path, *args, stdout=out, stderr=err)
    return out.getvalue() + err.getvalue()


def _shrine() -> Shrine:
    return Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=SHRINE_ADDRESS)


def _counts() -> dict[str, int]:
    return {
        "source": ShrineKnowledgeSource.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "collective": ShrineDeityCollective.objects.count(),
        "membership": ShrineDeityCollectiveMembership.objects.count(),
    }


# ---------- schema version / 1.0 compatibility ----------


def test_supported_versions_and_export_version_is_unchanged():
    assert SUPPORTED_SCHEMA_VERSIONS == ("1.0", "1.1")
    assert SCHEMA_VERSION == "1.0"


def test_all_repository_seeds_are_1_0_and_still_parse_without_collectives():
    paths = sorted(SEED_DIR.glob("*.json"))
    assert paths
    for path in paths:
        parsed = parse_seed(json.loads(path.read_text(encoding="utf-8")))
        assert parsed.schema_version == "1.0", path.name
        assert parsed.errors == [], path.name
        assert all(block.collectives == [] for block in parsed.shrines), path.name


@pytest.mark.parametrize("collectives", [[], [_collective()]])
def test_schema_1_0_rejects_collectives_key_even_when_empty(collectives):
    seed = _seed_v11(collectives=collectives)
    seed["schema_version"] = "1.0"
    errors = _errors(seed)
    assert any("shrines[0].collectives: not allowed in schema_version '1.0'" in e for e in errors)


@pytest.mark.parametrize("version", ["0.9", "1.2", "", None, 1.1])
def test_unsupported_schema_version_rejected(version):
    seed = _seed_v11(collectives=[])
    seed["schema_version"] = version
    assert any(e.startswith("schema_version:") for e in _errors(seed))


# ---------- 1.1 parser ----------


def test_schema_1_1_without_collectives_is_valid():
    seed = _seed_v11()
    del seed["shrines"][0]["collectives"]
    parsed = parse_seed(seed)
    assert parsed.errors == []
    assert parsed.shrines[0].collectives == []


def test_valid_collective_and_memberships_are_parsed():
    parsed = parse_seed(_seed_v11())
    assert parsed.errors == []
    collective = parsed.shrines[0].collectives[0]
    assert collective.source_attested_label == "祭神A・祭神B"
    assert (collective.member_count, collective.member_count_relation) == (2, "exact")
    assert collective.source_keys == ["src-group"]
    assert [m.deity_display_name for m in collective.memberships] == ["祭神A", "祭神B"]
    assert [m.source_keys for m in collective.memberships] == [["src-member-a"], ["src-member-b"]]


def test_collective_defaults_and_zero_memberships():
    parsed = parse_seed(
        _seed_v11(collectives=[{"source_attested_label": "ほか8柱", "source_keys": ["src-group"]}])
    )
    assert parsed.errors == []
    c = parsed.shrines[0].collectives[0]
    assert (c.role, c.sort_order, c.member_count) == ("unknown", 0, None)
    assert (c.member_count_relation, c.member_list_status) == ("unspecified", "not_determined")
    assert (c.verification_status, c.confidence, c.verified_at, c.note) == ("draft", "", None, "")
    assert c.memberships == []


def test_membership_defaults():
    membership = {"deity_ref": {"display_name": "祭神A"}, "source_keys": ["src-member-a"]}
    parsed = parse_seed(_seed_v11(collectives=[_collective(memberships=[membership])]))
    assert parsed.errors == []
    m = parsed.shrines[0].collectives[0].memberships[0]
    assert (m.sort_order, m.verification_status, m.confidence, m.verified_at, m.note) == (
        0,
        "draft",
        "",
        None,
        "",
    )


@pytest.mark.parametrize(
    "overrides, needle",
    [
        ({"role": "main"}, ".role: invalid value"),
        ({"member_count_relation": "at_least", "member_count": 2}, ".member_count_relation:"),
        ({"member_list_status": "unknown"}, ".member_list_status: invalid value"),
        ({"verification_status": "approved"}, ".verification_status: invalid value"),
        ({"confidence": "certain"}, ".confidence: invalid value"),
        ({"role": ["primary"]}, ".role: invalid value"),
    ],
)
def test_invalid_collective_enums_rejected(overrides, needle):
    assert any(needle in e for e in _collective_errors(**overrides))


@pytest.mark.parametrize(
    "overrides, needle",
    [
        ({"verification_status": "approved"}, ".verification_status: invalid value"),
        ({"confidence": "certain"}, ".confidence: invalid value"),
        ({"verified_at": None}, ".verified_at: required"),
    ],
)
def test_invalid_membership_verification_rejected(overrides, needle):
    errors = _collective_errors(memberships=[_membership("祭神A", "src-member-a", **overrides)])
    assert any("memberships[0]" in e and needle in e for e in errors)


def test_collective_source_confirmed_requires_verified_at():
    assert any(".verified_at: required" in e for e in _collective_errors(verified_at=None))


@pytest.mark.parametrize("label", [" 祭神A・祭神B", "祭神A・祭神B ", "　祭神A・祭神B"])
def test_whitespace_padded_label_rejected_not_trimmed(label):
    parsed = parse_seed(_seed_v11(collectives=[_collective(source_attested_label=label)]))
    assert any("leading/trailing whitespace" in e for e in parsed.errors)
    assert parsed.shrines[0].collectives[0].source_attested_label == label


@pytest.mark.parametrize("label", ["", "   ", None, 12])
def test_blank_or_non_string_label_rejected(label):
    errors = _collective_errors(source_attested_label=label)
    assert any("source_attested_label: required" in e for e in errors)


def test_duplicate_collective_identity_in_block_rejected():
    seed = _seed_v11(collectives=[_collective(), _collective(sort_order=3, memberships=[])])
    assert any("collectives[1].source_attested_label: duplicate" in e for e in _errors(seed))


@pytest.mark.parametrize("value", [-1, 1.5, "1", True, False, None])
def test_invalid_collective_sort_order_rejected(value):
    assert any(
        ".sort_order: must be an integer >= 0" in e for e in _collective_errors(sort_order=value)
    )


@pytest.mark.parametrize("value", [-1, "1", True])
def test_invalid_membership_sort_order_rejected(value):
    errors = _collective_errors(
        memberships=[_membership("祭神A", "src-member-a", sort_order=value)]
    )
    assert any("memberships[0].sort_order: must be an integer >= 0" in e for e in errors)


@pytest.mark.parametrize("value", [True, False, -1, 2.0, "2"])
def test_invalid_member_count_rejected(value):
    assert any(
        ".member_count: must be an integer >= 0" in e
        for e in _collective_errors(member_count=value)
    )


@pytest.mark.parametrize(
    "relation, count, needle",
    [
        ("exact", None, "member_count: required when member_count_relation='exact'"),
        ("minimum", None, "member_count: required when member_count_relation='minimum'"),
        ("approximate", None, "member_count: required when member_count_relation='approximate'"),
        ("unspecified", 8, "member_count: must be null when member_count_relation='unspecified'"),
    ],
)
def test_invalid_count_relation_pairs_rejected(relation, count, needle):
    errors = _collective_errors(member_count=count, member_count_relation=relation)
    assert any(needle in e for e in errors)


@pytest.mark.parametrize(
    "relation, count",
    [("exact", 0), ("minimum", 15), ("approximate", 56091), ("unspecified", None)],
)
def test_valid_count_relation_pairs_accepted_including_exact_zero(relation, count):
    assert _collective_errors(member_count=count, member_count_relation=relation) == []


@pytest.mark.parametrize("source_keys", ["missing", [], None, "src-group"])
def test_collective_source_keys_required_non_empty_list(source_keys):
    collective = _collective()
    if source_keys == "missing":
        del collective["source_keys"]
    else:
        collective["source_keys"] = source_keys
    errors = _errors(_seed_v11(collectives=[collective]))
    assert any(
        "collectives[0].source_keys: required, must be a non-empty list" in e for e in errors
    )


@pytest.mark.parametrize("source_keys", ["missing", [], None])
def test_membership_source_keys_required_and_not_inherited(source_keys):
    membership = _membership("祭神A", "src-member-a")
    if source_keys == "missing":
        del membership["source_keys"]
    else:
        membership["source_keys"] = source_keys
    errors = _collective_errors(memberships=[membership])
    assert any(
        "memberships[0].source_keys: required, must be a non-empty list" in e for e in errors
    )


def test_unknown_source_keys_rejected():
    errors = _collective_errors(
        source_keys=["no-such-source"],
        memberships=[_membership("祭神A", "no-such-member-source")],
    )
    assert any(
        "collectives[0].source_keys: unknown source key 'no-such-source'" in e for e in errors
    )
    assert any(
        "memberships[0].source_keys: unknown source key 'no-such-member-source'" in e
        for e in errors
    )


@pytest.mark.parametrize(
    "deity_ref",
    [
        None,
        123,
        "祭神A",
        {"id": 1},
        {"pk": 1},
        {"display_name": 1},
        {"display_name": ""},
        {"display_name": "   "},
        {"display_name": "祭神A", "canonical_name": "祭神A"},
        {"display_name": "祭神A", "id": 1},
    ],
)
def test_malformed_or_numeric_deity_ref_rejected(deity_ref):
    membership = _membership("祭神A", "src-member-a")
    membership["deity_ref"] = deity_ref
    errors = _collective_errors(memberships=[membership])
    assert any("memberships[0].deity_ref" in e for e in errors)


def test_duplicate_membership_deity_ref_rejected():
    errors = _collective_errors(
        memberships=[
            _membership("祭神A", "src-member-a"),
            _membership("祭神A", "src-member-b", sort_order=1),
        ]
    )
    assert any("memberships[1].deity_ref.display_name: duplicate '祭神A'" in e for e in errors)


@pytest.mark.parametrize(
    "block_overrides, needle",
    [
        ({"collectives": {}}, "shrines[0].collectives: must be a list"),
        ({"collectives": None}, "shrines[0].collectives: must be a list"),
        ({"collectives": ["x"]}, "shrines[0].collectives[0]: must be an object"),
    ],
)
def test_non_list_collectives_rejected(block_overrides, needle):
    assert any(needle in e for e in _errors(_seed_v11(**block_overrides)))


def test_non_list_memberships_rejected():
    assert any(
        "collectives[0].memberships: must be a list" in e
        for e in _collective_errors(memberships={"deity_ref": {"display_name": "祭神A"}})
    )


# ---------- plan / apply: Collective ----------


@pytest.mark.django_db
def test_validate_only_and_dry_run_do_not_write(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed_v11())

    assert "validate-only: OK" in _run(path, "--validate-only")
    out = _run(path, "--dry-run")
    assert "'collective_CREATE': 1" in out
    assert "'membership_CREATE': 2" in out
    assert "dry-run: OK" in out
    assert _counts() == {"source": 0, "deity": 0, "history": 0, "collective": 0, "membership": 0}


@pytest.mark.django_db
def test_apply_creates_collective_memberships_and_independent_sources(tmp_path):
    shrine = _shrine()
    path = _write(tmp_path, _seed_v11())

    out = _run(path)

    assert "collectives created=1, memberships created=2" in out
    collective = ShrineDeityCollective.objects.get()
    assert collective.shrine_id == shrine.id
    assert collective.source_attested_label == "祭神A・祭神B"
    assert (collective.member_count, collective.member_count_relation) == (2, "exact")
    assert collective.member_list_status == "complete"
    assert list(collective.sources.values_list("url", flat=True)) == [
        "https://collective.example.jp/saijin"
    ]
    memberships = list(collective.memberships.all())
    assert [m.deity.display_name for m in memberships] == ["祭神A", "祭神B"]
    assert [list(m.sources.values_list("url", flat=True)) for m in memberships] == [
        ["https://collective.example.jp/member-a"],
        ["https://collective.example.jp/member-b"],
    ]
    # Membership は Collective の Source を継承しない。
    for m in memberships:
        assert not m.sources.filter(url="https://collective.example.jp/saijin").exists()


@pytest.mark.django_db
def test_collective_with_zero_memberships_creates_only_collective(tmp_path):
    _shrine()
    seed = _seed_v11(
        deities=[],
        collectives=[
            _collective(
                source_attested_label="明治維新以降戦歿者の御霊",
                member_count=56091,
                member_list_status="not_enumerated",
                memberships=[],
            )
        ],
    )
    _run(_write(tmp_path, seed))

    assert ShrineDeityCollective.objects.count() == 1
    assert ShrineDeityCollectiveMembership.objects.count() == 0
    assert ShrineDeity.objects.count() == 0


@pytest.mark.django_db
def test_idempotent_second_dry_run_and_second_apply(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed_v11())
    _run(path)
    after_first = _counts()
    assert after_first == {"source": 3, "deity": 2, "history": 0, "collective": 1, "membership": 2}

    out = _run(path, "--dry-run")
    assert "collective_CREATE" not in out
    assert "membership_CREATE" not in out
    assert "CONFLICT" not in out
    assert "'collective_SKIP_EXISTS': 1" in out
    assert "'membership_SKIP_EXISTS': 2" in out

    out = _run(path)
    assert "collectives created=0, memberships created=0" in out
    assert _counts() == after_first


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, value",
    [
        ("role", "primary"),
        ("sort_order", 5),
        ("member_count", 3),
        ("member_count_relation", "minimum"),
        ("member_list_status", "partial"),
        ("verification_status", "reviewed"),
        ("confidence", "medium"),
        ("verified_at", "2026-09-28T00:00:00+09:00"),
        ("note", "差分"),
    ],
)
def test_existing_collective_metadata_mismatch_is_conflict(tmp_path, field_name, value):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))
    before = _counts()

    seed = _seed_v11(collectives=[_collective(**{field_name: value})])
    output = _run_blocked(_write(tmp_path, seed, "second.json"))

    assert "COLLECTIVE_CONFLICT" in output
    assert field_name in output
    assert _counts() == before


@pytest.mark.django_db
def test_existing_collective_source_set_mismatch_is_conflict(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))
    before = _counts()

    seed = _seed_v11(collectives=[_collective(source_keys=["src-group", "src-member-a"])])
    output = _run_blocked(_write(tmp_path, seed, "second.json"))

    assert "COLLECTIVE_CONFLICT" in output
    assert "source ids differ" in output
    assert _counts() == before
    assert ShrineDeityCollective.objects.get().sources.count() == 1


@pytest.mark.django_db
def test_existing_collective_with_newly_created_source_is_conflict(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))
    before = _counts()

    seed = _seed_v11(collectives=[_collective(source_keys=["src-new"])])
    seed["sources"].append(_source("src-new", "https://collective.example.jp/new"))
    output = _run_blocked(_write(tmp_path, seed, "second.json"))

    assert "COLLECTIVE_CONFLICT" in output
    assert _counts() == before


@pytest.mark.django_db
def test_duplicate_db_collective_identity_is_ambiguous(tmp_path):
    shrine = _shrine()
    for _ in range(2):
        ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="祭神A・祭神B")
    before = _counts()

    output = _run_blocked(_write(tmp_path, _seed_v11()), "--dry-run")

    assert "COLLECTIVE_AMBIGUOUS" in output
    assert _counts() == before


@pytest.mark.django_db
def test_label_identity_is_exact_and_not_canonicalized(tmp_path):
    shrine = _shrine()
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="祭神A、祭神B")

    out = _run(_write(tmp_path, _seed_v11()), "--dry-run")

    assert "'collective_CREATE': 1" in out


@pytest.mark.django_db
def test_same_identity_across_two_blocks_for_same_shrine_is_blocked(tmp_path):
    _shrine()
    seed = _seed_v11()
    second = copy.deepcopy(seed["shrines"][0])
    second["deities"] = []
    second["collectives"][0]["memberships"] = []
    seed["shrines"].append(second)

    output = _run_blocked(_write(tmp_path, seed))

    assert "COLLECTIVE_DUPLICATE_IN_SEED" in output
    assert _counts()["collective"] == 0


# ---------- plan / apply: Membership deity resolution ----------


@pytest.mark.django_db
def test_membership_resolves_existing_same_shrine_deity(tmp_path):
    shrine = _shrine()
    existing = ShrineDeity.objects.create(shrine=shrine, display_name="祭神A")
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神B")

    _run(_write(tmp_path, _seed_v11(deities=[])))

    assert ShrineDeity.objects.count() == 2
    membership = ShrineDeityCollectiveMembership.objects.get(deity__display_name="祭神A")
    assert membership.deity_id == existing.id


@pytest.mark.django_db
def test_membership_resolves_same_seed_deity_planned_for_creation(tmp_path):
    shrine = _shrine()

    out = _run(_write(tmp_path, _seed_v11()))

    assert "deities created=2" in out
    for name in ("祭神A", "祭神B"):
        deity = ShrineDeity.objects.get(shrine=shrine, display_name=name)
        assert deity.collective_memberships.count() == 1


@pytest.mark.django_db
def test_membership_missing_deity_stops_and_does_not_create_deity(tmp_path):
    _shrine()
    output = _run_blocked(_write(tmp_path, _seed_v11(deities=[_deity("祭神A")])))

    assert "MEMBERSHIP_DEITY_NOT_FOUND" in output
    assert _counts() == {"source": 0, "deity": 0, "history": 0, "collective": 0, "membership": 0}


@pytest.mark.django_db
def test_membership_does_not_match_canonical_name(tmp_path):
    shrine = _shrine()
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神A")
    ShrineDeity.objects.create(shrine=shrine, display_name="別表記", canonical_name="祭神B")

    output = _run_blocked(_write(tmp_path, _seed_v11(deities=[])), "--dry-run")

    assert "MEMBERSHIP_DEITY_NOT_FOUND" in output


@pytest.mark.django_db
def test_membership_duplicate_matching_deities_is_ambiguous(tmp_path):
    shrine = _shrine()
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神A")
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神A")
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神B")
    before = _counts()

    output = _run_blocked(_write(tmp_path, _seed_v11(deities=[])))

    assert "MEMBERSHIP_DEITY_AMBIGUOUS" in output
    assert _counts() == before


@pytest.mark.django_db
def test_membership_duplicate_same_seed_deities_is_ambiguous(tmp_path):
    _shrine()
    seed = _seed_v11(deities=[_deity("祭神A"), _deity("祭神A"), _deity("祭神B")])

    output = _run_blocked(_write(tmp_path, seed), "--dry-run")

    assert "MEMBERSHIP_DEITY_AMBIGUOUS" in output


@pytest.mark.django_db
def test_membership_deity_on_another_shrine_stops(tmp_path):
    _shrine()
    other = Shrine.objects.create(name_jp="別神社", kind="shrine", address="別住所")
    ShrineDeity.objects.create(shrine=other, display_name="祭神A")
    before = _counts()

    output = _run_blocked(_write(tmp_path, _seed_v11(deities=[_deity("祭神B")])))

    assert "MEMBERSHIP_DEITY_WRONG_SHRINE" in output
    assert _counts() == before


# ---------- plan / apply: Membership identity ----------


@pytest.mark.django_db
def test_existing_identical_membership_is_skip_exists(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))

    out = _run(_write(tmp_path, _seed_v11(), "second.json"), "--dry-run")

    assert "'membership_SKIP_EXISTS': 2" in out


@pytest.mark.django_db
def test_new_membership_on_existing_collective_is_created(tmp_path):
    _shrine()
    first = _collective(memberships=[_membership("祭神A", "src-member-a")])
    _run(_write(tmp_path, _seed_v11(collectives=[first]), "first.json"))

    out = _run(_write(tmp_path, _seed_v11(), "second.json"))

    assert "collectives created=0, memberships created=1" in out
    assert ShrineDeityCollective.objects.get().memberships.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, value",
    [
        ("sort_order", 7),
        ("verification_status", "reviewed"),
        ("confidence", "low"),
        ("verified_at", "2026-09-28T00:00:00+09:00"),
        ("note", "差分"),
    ],
)
def test_membership_metadata_mismatch_is_conflict(tmp_path, field_name, value):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))
    before = _counts()

    seed = _seed_v11(
        collectives=[
            _collective(
                memberships=[
                    _membership("祭神A", "src-member-a", **{field_name: value}),
                    _membership("祭神B", "src-member-b", sort_order=1),
                ]
            )
        ]
    )
    output = _run_blocked(_write(tmp_path, seed, "second.json"))

    assert "MEMBERSHIP_CONFLICT" in output
    assert field_name in output
    assert _counts() == before


@pytest.mark.django_db
def test_membership_source_set_mismatch_is_conflict(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed_v11(), "first.json"))
    before = _counts()

    seed = _seed_v11(
        collectives=[
            _collective(
                memberships=[
                    _membership("祭神A", "src-member-b"),
                    _membership("祭神B", "src-member-b", sort_order=1),
                ]
            )
        ]
    )
    output = _run_blocked(_write(tmp_path, seed, "second.json"))

    assert "MEMBERSHIP_CONFLICT" in output
    assert "source ids differ" in output
    assert _counts() == before


@pytest.mark.django_db
def test_collective_source_is_never_inherited_by_membership(tmp_path):
    """Collective と Membership が同じ Source を使う場合も、Membership 側が明示したものだけが付く。"""
    _shrine()
    seed = _seed_v11(
        collectives=[
            _collective(
                source_keys=["src-group", "src-member-a"],
                memberships=[
                    _membership("祭神A", "src-member-a"),
                    _membership("祭神B", "src-member-b", sort_order=1),
                ],
            )
        ]
    )
    _run(_write(tmp_path, seed))

    collective = ShrineDeityCollective.objects.get()
    shared = ShrineKnowledgeSource.objects.get(url="https://collective.example.jp/member-a")
    assert set(collective.sources.all()) == {
        ShrineKnowledgeSource.objects.get(url="https://collective.example.jp/saijin"),
        shared,
    }
    member_a = collective.memberships.get(deity__display_name="祭神A")
    member_b = collective.memberships.get(deity__display_name="祭神B")
    assert list(member_a.sources.all()) == [shared]
    assert list(member_b.sources.values_list("url", flat=True)) == [
        "https://collective.example.jp/member-b"
    ]
    assert ShrineKnowledgeSource.objects.count() == 3
    assert shared.deity_collectives.count() == 1
    assert shared.deity_collective_memberships.count() == 1


# ---------- atomicity ----------


@pytest.mark.django_db
def test_later_collective_failure_blocks_all_writes_including_earlier_block(tmp_path):
    shrine = _shrine()
    other = Shrine.objects.create(name_jp="後続神社", kind="shrine", address="後続住所")
    for _ in range(2):
        ShrineDeityCollective.objects.create(shrine=other, source_attested_label="後続集合")
    before = _counts()

    seed = _seed_v11(
        histories=[
            {
                "history_type": "official_origin",
                "title": "由緒",
                "content": "試験由緒",
                "verification_status": "source_confirmed",
                "verified_at": VERIFIED_AT,
                "confidence": "high",
                "source_keys": ["src-group"],
            }
        ]
    )
    seed["shrines"].append(
        {
            "shrine_ref": {"name_jp": "後続神社", "address": "後続住所"},
            "deities": [],
            "histories": [],
            "collectives": [
                _collective(source_attested_label="後続集合", memberships=[]),
            ],
        }
    )
    output = _run_blocked(_write(tmp_path, seed))

    assert "COLLECTIVE_AMBIGUOUS" in output
    assert _counts() == before
    assert not ShrineDeity.objects.filter(shrine=shrine).exists()


@pytest.mark.django_db
def test_later_membership_failure_blocks_all_writes(tmp_path):
    _shrine()
    Shrine.objects.create(name_jp="後続神社", kind="shrine", address="後続住所")

    seed = _seed_v11()
    seed["shrines"].append(
        {
            "shrine_ref": {"name_jp": "後続神社", "address": "後続住所"},
            "deities": [],
            "histories": [],
            "collectives": [
                _collective(
                    source_attested_label="後続集合",
                    memberships=[_membership("存在しない祭神", "src-member-a")],
                )
            ],
        }
    )
    output = _run_blocked(_write(tmp_path, seed))

    assert "MEMBERSHIP_DEITY_NOT_FOUND" in output
    assert _counts() == {"source": 0, "deity": 0, "history": 0, "collective": 0, "membership": 0}


@pytest.mark.django_db
def test_apply_rechecks_collective_identity_and_rolls_back(tmp_path, monkeypatch):
    """plan 後に identity が変わった場合、apply は別判断をせず全体を巻き戻す。"""
    from temples.management.commands import import_shrine_knowledge as command_module

    shrine = _shrine()
    original_apply_collectives = command_module._apply_collectives

    def racing_apply(collective_plans, source_objs, created):
        ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="祭神A・祭神B")
        return original_apply_collectives(collective_plans, source_objs, created)

    monkeypatch.setattr(command_module, "_apply_collectives", racing_apply)

    with pytest.raises(CommandError, match="already exists at apply time"):
        _run(_write(tmp_path, _seed_v11()))
    assert _counts() == {"source": 0, "deity": 0, "history": 0, "collective": 0, "membership": 0}


@pytest.mark.django_db
def test_import_uses_validated_save_path(tmp_path, monkeypatch):
    """Collective / Membership は full_clean() + save() で作成し、bulk_create を使わない。"""
    calls: list[str] = []
    for model in (ShrineDeityCollective, ShrineDeityCollectiveMembership):
        original = model.full_clean

        def recording(self, *args, _original=original, _name=model.__name__, **kwargs):
            calls.append(_name)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(model, "full_clean", recording)

    def forbidden(*args, **kwargs):
        raise AssertionError("bulk_create is prohibited for collective import")

    monkeypatch.setattr(ShrineDeityCollective.objects, "bulk_create", forbidden)
    monkeypatch.setattr(ShrineDeityCollectiveMembership.objects, "bulk_create", forbidden)

    _shrine()
    _run(_write(tmp_path, _seed_v11()))

    assert calls.count("ShrineDeityCollective") == 1
    # Membership は importer の full_clean() と save() 内の full_clean() の2回。
    assert calls.count("ShrineDeityCollectiveMembership") == 4
    assert timezone.is_aware(ShrineDeityCollective.objects.get().verified_at)
