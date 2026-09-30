"""A6-00b Collective Runtime Activation seed workflow の test。

production-equivalent fixture は repository 正本の A-5b seed を既存 importer
（import_shrine_knowledge）でそのまま取り込んで作る。production の数値 PK には依存しない。
"""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from temples.models import (
    CollectiveRuntimeActivation,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineKnowledgeSource,
)
from temples.services import collective_runtime_activation_seed as activation_seed
from temples.services.collective_runtime_activation_seed import (
    parse_activation_seed,
    resolve_activation_targets,
)

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ACTIVATION_SEED_PATH = DATA_DIR / "runtime_rollout" / "a6_collective_runtime_activation_v1.json"
A5B_SEED_PATH = DATA_DIR / "knowledge_seeds" / "a5b_collective_pattern_b_seed.json"

EXPECTED_IDENTITIES = [
    ("箱根神社", "神奈川県足柄下郡箱根町元箱根80-1", "箱根大神"),
    ("寒川神社", "神奈川県高座郡寒川町宮山3916", "寒川大明神"),
    ("二荒山神社", "栃木県日光市山内2307", "二荒山大神"),
    ("住吉神社（博多）", "福岡県福岡市博多区住吉3-1-51", "住吉五所大神"),
    ("安房神社", "千葉県館山市大神宮589", "忌部五部神"),
    ("王子神社", "東京都北区王子本町1-1-12", "王子大神"),
]


# ---------- helpers ----------


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _activation_seed() -> dict:
    return _load(ACTIVATION_SEED_PATH)


def _entry(name_jp: str, address: str, label: str) -> dict:
    return {"shrine_ref": {"name_jp": name_jp, "address": address}, "source_attested_label": label}


def _seed(*entries: dict) -> dict:
    return {"schema_version": "1.0", "collectives": list(entries)}


def _write(tmp_path, seed, name: str = "activation.json") -> str:
    path = tmp_path / name
    text = seed if isinstance(seed, str) else json.dumps(seed, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _run(path: str, *args: str) -> str:
    out = io.StringIO()
    call_command("activate_collective_runtime", path, *args, stdout=out, stderr=io.StringIO())
    return out.getvalue()


def _run_blocked(path: str, *args: str) -> tuple[str, str]:
    out, err = io.StringIO(), io.StringIO()
    with pytest.raises(CommandError):
        call_command("activate_collective_runtime", path, *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def _create_shrine(name_jp: str, address: str, latitude: float = 35.0) -> Shrine:
    return Shrine.objects.create(
        name_jp=name_jp, address=address, latitude=latitude, longitude=139.0
    )


def _production_equivalent_state() -> None:
    """A-5b Production の前提（6 Shrine + 23 既存 Deity）を作り、A-5b seed を既存 importer で適用する。"""
    a5b = _load(A5B_SEED_PATH)
    for block in a5b["shrines"]:
        shrine = _create_shrine(block["shrine_ref"]["name_jp"], block["shrine_ref"]["address"])
        for collective in block["collectives"]:
            for membership in collective["memberships"]:
                ShrineDeity.objects.create(
                    shrine=shrine, display_name=membership["deity_ref"]["display_name"]
                )
    call_command(
        "import_shrine_knowledge", str(A5B_SEED_PATH), stdout=io.StringIO(), stderr=io.StringIO()
    )
    assert ShrineDeityCollective.objects.count() == 6
    assert ShrineDeityCollectiveMembership.objects.count() == 23


def _db_state() -> dict:
    return {
        "shrine": list(Shrine.objects.order_by("id").values_list("id", "name_jp", "address")),
        "collective": list(ShrineDeityCollective.objects.order_by("id").values()),
        "membership": list(ShrineDeityCollectiveMembership.objects.order_by("id").values()),
        "source": list(ShrineKnowledgeSource.objects.order_by("id").values()),
        "deity": list(ShrineDeity.objects.order_by("id").values()),
        "activation": list(CollectiveRuntimeActivation.objects.order_by("id").values()),
        "collective_sources": list(
            ShrineDeityCollective.sources.through.objects.order_by("id").values()
        ),
        "membership_sources": list(
            ShrineDeityCollectiveMembership.sources.through.objects.order_by("id").values()
        ),
    }


@pytest.fixture
def production_equivalent():
    _production_equivalent_state()


@pytest.fixture
def seed_path():
    return str(ACTIVATION_SEED_PATH)


# ---------- scope: authoritative seed ----------


def test_authoritative_seed_contains_exactly_the_six_a5b_collectives():
    raw = _activation_seed()
    parsed = parse_activation_seed(raw)

    assert parsed.errors == []
    assert raw["schema_version"] == "1.0"
    assert [(e.name_jp, e.address, e.source_attested_label) for e in parsed.entries] == (
        EXPECTED_IDENTITIES
    )


def test_authoritative_seed_reuses_exact_a5b_shrine_refs_and_labels():
    a5b = _load(A5B_SEED_PATH)
    a5b_identities = [
        (b["shrine_ref"]["name_jp"], b["shrine_ref"]["address"], c["source_attested_label"])
        for b in a5b["shrines"]
        for c in b["collectives"]
    ]
    activation = [
        (e["shrine_ref"]["name_jp"], e["shrine_ref"]["address"], e["source_attested_label"])
        for e in _activation_seed()["collectives"]
    ]
    assert activation == a5b_identities


def test_authoritative_seed_carries_no_pattern_or_runtime_fields():
    raw = _activation_seed()
    assert set(raw) == {"schema_version", "collectives"}
    for entry in raw["collectives"]:
        assert set(entry) == {"shrine_ref", "source_attested_label"}
        assert set(entry["shrine_ref"]) == {"name_jp", "address"}


# ---------- seed parsing ----------


def test_valid_seed_parses():
    parsed = parse_activation_seed(_seed(_entry("甲神社", "東京都1", "甲大神")))
    assert parsed.errors == []
    assert len(parsed.entries) == 1


@pytest.mark.parametrize("version", ["1.1", "2.0", "", None, 1.0])
def test_unsupported_schema_version_rejected(version):
    seed = _seed(_entry("甲神社", "東京都1", "甲大神"))
    seed["schema_version"] = version
    assert any("schema_version: unsupported" in e for e in parse_activation_seed(seed).errors)


@pytest.mark.parametrize(
    "entry, needle",
    [
        ("not-an-object", "must be an object"),
        ({"source_attested_label": "甲大神"}, "shrine_ref: required object"),
        ({"shrine_ref": {"name_jp": "甲神社"}, "source_attested_label": "甲大神"}, "address"),
        ({"shrine_ref": {"address": "東京都1"}, "source_attested_label": "甲大神"}, "name_jp"),
        ({"shrine_ref": {"name_jp": "甲神社", "address": "東京都1"}}, "source_attested_label"),
        (_entry("甲神社", "東京都1", "  "), "required non-blank string"),
        (_entry("甲神社", "東京都1", " 甲大神"), "whitespace"),
        (_entry("甲神社", "東京都1", 123), "required non-blank string"),
        ({**_entry("甲神社", "東京都1", "甲大神"), "pattern": "B"}, "unexpected key"),
        (
            {
                "shrine_ref": {"name_jp": "甲神社", "address": "東京都1", "id": 1},
                "source_attested_label": "甲大神",
            },
            "unexpected key",
        ),
    ],
)
def test_malformed_entry_rejected(entry, needle):
    errors = parse_activation_seed(_seed(entry)).errors
    assert any(needle in e for e in errors), errors


@pytest.mark.parametrize(
    "raw, needle",
    [
        ([], "top-level must be an object"),
        ({"schema_version": "1.0"}, "collectives: required non-empty list"),
        ({"schema_version": "1.0", "collectives": []}, "collectives: required non-empty list"),
        ({"schema_version": "1.0", "collectives": {}}, "collectives: required non-empty list"),
        (
            {"schema_version": "1.0", "collectives": [_entry("甲", "a", "b")], "x": 1},
            "unexpected key",
        ),
    ],
)
def test_malformed_top_level_rejected(raw, needle):
    assert any(needle in e for e in parse_activation_seed(raw).errors)


def test_duplicate_entry_rejected():
    entry = _entry("甲神社", "東京都1", "甲大神")
    errors = parse_activation_seed(_seed(entry, copy.deepcopy(entry))).errors
    assert any("DUPLICATE_SEED_ENTRY" in e for e in errors)


# ---------- resolution ----------


def _targets(*entries: dict):
    parsed = parse_activation_seed(_seed(*entries))
    assert parsed.errors == []
    return resolve_activation_targets(parsed.entries)


def test_shrine_and_collective_resolve_uniquely():
    shrine = _create_shrine("甲神社", "東京都1")
    collective = ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="甲大神")
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))

    assert errors == []
    assert [t.collective.pk for t in targets] == [collective.pk]


def test_shrine_not_found_fails():
    targets, errors = _targets(_entry("存在しない神社", "東京都1", "甲大神"))
    assert targets == []
    assert any("SHRINE_NOT_FOUND" in e for e in errors)


def test_shrine_ambiguous_fails():
    # 同名・同住所・どちらも canonical（place_ref_id IS NULL）→ 既存 resolve_shrine が AMBIGUOUS。
    _create_shrine("甲神社", "東京都1")
    _create_shrine("甲神社", "東京都1", latitude=35.1)
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))
    assert targets == []
    assert any("SHRINE_AMBIGUOUS" in e for e in errors)


def test_collective_not_found_fails():
    shrine = _create_shrine("甲神社", "東京都1")
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="乙大神")
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))
    assert targets == []
    assert any("COLLECTIVE_NOT_FOUND" in e for e in errors)


def test_collective_on_other_shrine_is_not_found():
    _create_shrine("甲神社", "東京都1")
    other = _create_shrine("乙神社", "東京都2")
    ShrineDeityCollective.objects.create(shrine=other, source_attested_label="甲大神")
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))
    assert targets == []
    assert any("COLLECTIVE_NOT_FOUND" in e for e in errors)


def test_collective_ambiguous_fails():
    shrine = _create_shrine("甲神社", "東京都1")
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="甲大神")
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="甲大神")
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))
    assert targets == []
    assert any("COLLECTIVE_AMBIGUOUS" in e for e in errors)


def test_resolution_does_not_infer_from_membership_or_list_status():
    """member_list_status / member_count / Membership 0件でも label 一致なら解決する（Pattern 推論なし）。"""
    shrine = _create_shrine("甲神社", "東京都1")
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine, source_attested_label="甲大神", member_list_status="partial"
    )
    targets, errors = _targets(_entry("甲神社", "東京都1", "甲大神"))
    assert errors == []
    assert [t.collective.pk for t in targets] == [collective.pk]


def test_two_entries_resolving_to_same_collective_is_identity_conflict():
    # 住所違いの ref が既存 resolve_shrine の name_jp フォールバックで同一 Shrine へ解決される場合。
    shrine = _create_shrine("甲神社", "東京都1")
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="甲大神")
    targets, errors = _targets(
        _entry("甲神社", "東京都1", "甲大神"), _entry("甲神社", "東京都9", "甲大神")
    )
    assert any("IDENTITY_CONFLICT" in e for e in errors)


# ---------- execution modes (production-equivalent) ----------


def test_validate_only_resolves_six_and_performs_zero_writes(production_equivalent, seed_path):
    before = _db_state()
    out = _run(seed_path, "--validate-only")

    assert _db_state() == before
    assert out.count("[activation] RESOLVED") == 6
    assert "validate-only: OK, 6 Collective(s) resolved" in out


def test_dry_run_initial_plan_is_create_6_and_performs_zero_writes(
    production_equivalent, seed_path
):
    before = _db_state()
    out = _run(seed_path, "--dry-run")

    assert _db_state() == before
    assert CollectiveRuntimeActivation.objects.count() == 0
    assert "plan summary: CREATE=6 SKIP_EXISTS=0" in out
    assert out.count("[activation] CREATE") == 6


def test_apply_creates_six_activations_for_the_resolved_collectives(
    production_equivalent, seed_path
):
    out = _run(seed_path)

    assert "activation complete: created=6, skipped=0" in out
    activated = {
        (a.collective.shrine.name_jp, a.collective.source_attested_label)
        for a in CollectiveRuntimeActivation.objects.select_related("collective__shrine")
    }
    assert activated == {(name, label) for name, _, label in EXPECTED_IDENTITIES}


def test_repeated_apply_is_idempotent(production_equivalent, seed_path):
    first = _run(seed_path)
    state_after_first = _db_state()
    second = _run(seed_path)
    third = _run(seed_path)
    dry_run_after = _run(seed_path, "--dry-run")

    assert "created=6, skipped=0" in first
    assert "created=0, skipped=6" in second
    assert "created=0, skipped=6" in third
    assert "plan summary: CREATE=0 SKIP_EXISTS=6" in dry_run_after
    assert second.count("[activation] SKIP_EXISTS") == 6
    assert _db_state() == state_after_first
    assert CollectiveRuntimeActivation.objects.count() == 6


def test_apply_does_not_mutate_knowledge_rows(production_equivalent, seed_path):
    before = _db_state()
    _run(seed_path)
    after = _db_state()

    for key in (
        "shrine",
        "collective",
        "membership",
        "source",
        "deity",
        "collective_sources",
        "membership_sources",
    ):
        assert after[key] == before[key], key
    assert len(after["activation"]) == 6


def test_apply_skips_preexisting_activation_without_recreating_it(production_equivalent, seed_path):
    collective = ShrineDeityCollective.objects.get(source_attested_label="箱根大神")
    existing = CollectiveRuntimeActivation.objects.create(collective=collective)
    existing_row = CollectiveRuntimeActivation.objects.filter(pk=existing.pk).values().get()

    out = _run(seed_path)

    assert "created=5, skipped=1" in out
    assert "[activation] SKIP_EXISTS 箱根神社 / 箱根大神" in out
    assert CollectiveRuntimeActivation.objects.filter(pk=existing.pk).values().get() == (
        existing_row
    )


def test_mode_flags_are_mutually_exclusive(production_equivalent, seed_path):
    before = _db_state()
    with pytest.raises(CommandError):
        call_command(
            "activate_collective_runtime",
            seed_path,
            "--validate-only",
            "--dry-run",
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
    assert _db_state() == before


# ---------- fail-closed / atomicity ----------


def test_invalid_json_fails_closed(tmp_path):
    _run_blocked(_write(tmp_path, "{not json"))
    assert CollectiveRuntimeActivation.objects.count() == 0


def test_missing_seed_file_fails_closed(tmp_path):
    _run_blocked(str(tmp_path / "missing.json"))


@pytest.mark.parametrize("mode", [(), ("--dry-run",), ("--validate-only",)])
def test_five_valid_plus_one_unresolvable_commits_nothing(production_equivalent, tmp_path, mode):
    seed = _activation_seed()
    seed["collectives"][3]["source_attested_label"] = "存在しない集合祭神"
    before = _db_state()

    _, err = _run_blocked(_write(tmp_path, seed), *mode)

    assert "COLLECTIVE_NOT_FOUND" in err
    assert _db_state() == before
    assert CollectiveRuntimeActivation.objects.count() == 0


@pytest.mark.parametrize(
    "mutate, needle",
    [
        (lambda s: s.update(schema_version="9.9"), "unsupported"),
        (lambda s: s["collectives"].append(copy.deepcopy(s["collectives"][0])), "DUPLICATE"),
        (lambda s: s["collectives"][2].pop("source_attested_label"), "source_attested_label"),
        (
            lambda s: s["collectives"][1]["shrine_ref"].update(name_jp="不明神社"),
            "SHRINE_NOT_FOUND",
        ),
    ],
)
def test_contract_failures_abort_whole_apply(production_equivalent, tmp_path, mutate, needle):
    seed = _activation_seed()
    mutate(seed)
    before = _db_state()

    _, err = _run_blocked(_write(tmp_path, seed))

    assert needle in err
    assert _db_state() == before


def test_database_write_failure_mid_apply_rolls_back_everything(
    production_equivalent, seed_path, monkeypatch
):
    real_create = CollectiveRuntimeActivation.objects.create
    calls = {"n": 0}

    def flaky_create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 4:
            raise IntegrityError("simulated write failure")
        return real_create(**kwargs)

    monkeypatch.setattr(activation_seed.CollectiveRuntimeActivation.objects, "create", flaky_create)
    before = _db_state()

    _, err = _run_blocked(seed_path)

    assert calls["n"] == 4
    assert _db_state() == before
    assert CollectiveRuntimeActivation.objects.count() == 0
