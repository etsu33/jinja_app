"""G-6: Nationwide handoff identity manifest と `verify_recommendation_eligibility --handoff`。

- manifest は reviewed canonical identity の exact 文字列だけを持ち、Candidate Master と照合して
  fail closed する（正規化・補完・推論をしない）。
- `--handoff` は既存の Recommendation Eligibility authority（shrine_knowledge_selector ->
  evidence_gate.decide_fact_usability() -> is_recommendation_eligible()）へそのまま委譲する。
- identity が manifest にあることは eligibility を意味しない。
- Production には接続しない（isolated test DB のみ）。
"""

import ast
import copy
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import recommendation_eligibility_verifier as verifier
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    INELIGIBLE,
    UNRESOLVED,
    HandoffIdentityError,
    ShrineIdentity,
    load_handoff_shrine_identities,
    validate_nationwide_identity_manifest,
    verify_recommendation_eligibility,
)

TEMPLES_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TEMPLES_DIR.parents[1]
DATA_DIR = TEMPLES_DIR / "data"
MANIFEST_PATH = DATA_DIR / "shrine_expansion_nationwide_identity_manifest.json"
MASTER_PATH = DATA_DIR / "shrine_expansion_candidate_master.json"
BASE_SEED_PATH = DATA_DIR / "shrines_seed_clean.json"
SEED_DIR = DATA_DIR / "knowledge_seeds"
DECISION = "docs/audit/niigata-h001-g6-verifier-identity-decision.md"

H001 = "NIIGATA-001-H001"
H002 = "NIIGATA-001-H002"
# G1 reviewed canonical identity 登録済みの handoff。
H003 = "NIIGATA-001-H003"
# G0 登録済み（Candidate Master）だが G1 未実施のため identity manifest には無い handoff。
H004 = "NIIGATA-001-H004"
H003_AUDIT = "docs/audit/niigata-h003-g1-identity-duplicate.md"
# どこにも登録されていない handoff（frozen Ready Set の範囲外）。
UNREGISTERED_HANDOFF = "NIIGATA-001-H999"
# docs/audit/niigata-h001-g6-verifier-identity-decision.md §3（Mother Ship freeze）
H001_IDENTITIES = [
    ShrineIdentity("相吉神社", "新潟県中魚沼郡津南町大字谷内4797番地"),
    ShrineIdentity("青澤神社", "新潟県糸魚川市大字青海2696番地"),
    ShrineIdentity("蒼柴神社", "新潟県長岡市悠久町707"),
    ShrineIdentity("青海神社", "新潟県加茂市大字加茂字宮山229番地"),
    ShrineIdentity("青山稲荷神社", "新潟県柏崎市荒浜4丁目1754番地2"),
]
# 各 G1 audit の official_name / official_address
H002_IDENTITIES = [
    ShrineIdentity("赤井神社", "新潟県佐渡市加茂歌代2662番地"),
    ShrineIdentity("赤城社", "新潟県十日町市四日町2534番地"),
    ShrineIdentity("赤城社", "新潟県十日町市上組2059番地子"),
    ShrineIdentity("赤城社", "新潟県十日町市伊達乙48番地"),
    ShrineIdentity("赤城社", "新潟県南魚沼市芹田79番地"),
]
H003_IDENTITIES = [
    ShrineIdentity("赤城神社", "新潟県新潟市江南区二本木1丁目7番16号"),
    ShrineIdentity("赤城神社", "新潟県長岡市四郎丸2丁目5番33号"),
    ShrineIdentity("赤城神社", "新潟県長岡市山屋314番地"),
    ShrineIdentity("赤城神社", "新潟県五泉市上杉川1310番地2"),
    ShrineIdentity("赤城神社", "新潟県魚沼市湯之谷芋川311番地"),
]


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _master() -> dict:
    return json.loads(MASTER_PATH.read_text(encoding="utf-8"))


# --- manifest content / authority -----------------------------------------------------------


def test_handoff_identities_are_the_frozen_exact_strings():
    assert load_handoff_shrine_identities(H001) == H001_IDENTITIES
    assert load_handoff_shrine_identities(H002) == H002_IDENTITIES
    assert load_handoff_shrine_identities(H003) == H003_IDENTITIES


def test_nsrc_000003_keeps_707_without_banchi():
    identities = load_handoff_shrine_identities(H001)
    assert identities[2].address == "新潟県長岡市悠久町707"
    assert "707番地" not in MANIFEST_PATH.read_text(encoding="utf-8")


def test_h001_identities_equal_the_mother_ship_decision_record():
    text = (REPO_ROOT / DECISION).read_text(encoding="utf-8")
    block = re.search(r"```text\n(nsrc-000001.*?)```", text, re.DOTALL).group(1)
    frozen = [line.split() for line in block.strip().splitlines()]
    members = next(h for h in _manifest()["handoffs"] if h["handoff_id"] == H001)["members"]
    assert [[m["candidate_id"], m["name"], m["address"]] for m in members] == frozen
    for member in members:
        assert member["identity_evidence"]["verifier_identity_authority"] == DECISION


def test_h002_identities_equal_each_g1_audit_record():
    members = next(h for h in _manifest()["handoffs"] if h["handoff_id"] == H002)["members"]
    for member in members:
        audit = member["identity_evidence"]["verifier_identity_authority"]
        assert audit == f"docs/audit/niigata-h002-{member['candidate_id']}-g1-identity-duplicate.md"
        text = (REPO_ROOT / audit).read_text(encoding="utf-8")
        assert re.findall(r"^official_name\s*=\s*(.+)$", text, re.MULTILINE) == [member["name"]]
        assert re.findall(r"^official_address\s*=\s*(.+)$", text, re.MULTILINE) == [
            member["address"]
        ]


def test_h003_identities_equal_g1_audit_record():
    members = next(h for h in _manifest()["handoffs"] if h["handoff_id"] == H003)["members"]
    assert all(
        member["identity_evidence"]["verifier_identity_authority"] == H003_AUDIT
        and member["identity_evidence"]["g1_identity_audit"] == H003_AUDIT
        for member in members
    )
    text = (REPO_ROOT / H003_AUDIT).read_text(encoding="utf-8")
    assert re.findall(r"^official_name\s*=\s*(.+)$", text, re.MULTILINE)[:5] == [
        member["name"] for member in members
    ]
    assert re.findall(r"^official_address\s*=\s*(.+)$", text, re.MULTILINE)[:5] == [
        member["address"] for member in members
    ]


def test_every_evidence_reference_exists_in_the_repository():
    for handoff in _manifest()["handoffs"]:
        for member in handoff["members"]:
            for ref in member["identity_evidence"].values():
                assert (REPO_ROOT / ref).is_file(), ref


def test_same_name_is_allowed_but_exact_pairs_are_unique():
    h002 = load_handoff_shrine_identities(H002)
    assert [i.name for i in h002].count("赤城社") == 4
    assert len(set(h002)) == len(h002)
    h003 = load_handoff_shrine_identities(H003)
    assert [i.name for i in h003].count("赤城神社") == 5
    assert len(set(h003)) == len(h003)


def test_loader_does_not_touch_the_database(django_assert_num_queries):
    with django_assert_num_queries(0):
        load_handoff_shrine_identities(H001)
        load_handoff_shrine_identities(H002)
        load_handoff_shrine_identities(H003)


# --- fail-closed mutations ----------------------------------------------------------------------


def _member(manifest, handoff_id, index):
    return next(h for h in manifest["handoffs"] if h["handoff_id"] == handoff_id)["members"][index]


def _members(manifest, handoff_id):
    return next(h for h in manifest["handoffs"] if h["handoff_id"] == handoff_id)["members"]


def _cm_rows(master, handoff_id):
    return [
        r
        for r in master["candidates"]
        if (r.get("admission_provenance") or {}).get("handoff_id") == handoff_id
    ]


def _m(fn):
    """manifest mutation"""
    return ("manifest", fn)


def _c(fn):
    """Candidate Master mutation"""
    return ("master", fn)


def _swap(items, i, j):
    items[i], items[j] = items[j], items[i]


def _cm_swap(master, handoff_id):
    rows = _cm_rows(master, handoff_id)
    candidates = master["candidates"]
    a, b = candidates.index(rows[0]), candidates.index(rows[1])
    _swap(candidates, a, b)


MUTATIONS = {
    "member-removed": _m(lambda m: _members(m, H001).pop()),
    "member-added": _m(
        lambda m: _members(m, H001).append(
            {**copy.deepcopy(_member(m, H001, 4)), "candidate_id": "nsrc-000099", "address": "x"}
        )
    ),
    "member-reordered": _m(lambda m: _swap(_members(m, H001), 0, 1)),
    "candidate-id-changed": _m(lambda m: _member(m, H001, 1).update(candidate_id="nsrc-000099")),
    "source-position-changed": _m(
        lambda m: _member(m, H001, 1).update(source_position="page001-row009")
    ),
    "handoff-id-changed": _m(lambda m: m["handoffs"][0].update(handoff_id="NIIGATA-001-H099")),
    "canonical-name-changed": _m(lambda m: _member(m, H001, 1).update(name="青沢神社")),
    "member-identity-copied-from-another-member": _m(
        lambda m: _member(m, H001, 3).update(
            name=_member(m, H001, 1)["name"], address=_member(m, H001, 1)["address"]
        )
    ),
    "duplicate-candidate-id": _m(
        lambda m: m["handoffs"].append(
            {"handoff_id": "NIIGATA-001-H099", "members": [copy.deepcopy(_member(m, H001, 0))]}
        )
    ),
    "duplicate-exact-name-address": _m(
        lambda m: _member(m, H002, 1).update(address=_member(m, H002, 2)["address"])
    ),
    "address-surrounding-whitespace": _m(
        lambda m: _member(m, H001, 1).update(address=_member(m, H001, 1)["address"] + " ")
    ),
    "address-control-character": _m(
        lambda m: _member(m, H001, 1).update(address="新潟県糸魚川市\n大字青海2696番地")
    ),
    "empty-handoff": _m(lambda m: _members(m, H002).clear()),
    "duplicate-handoff-id": _m(lambda m: m["handoffs"].append(copy.deepcopy(m["handoffs"][0]))),
    "missing-evidence-reference": _m(
        lambda m: _member(m, H001, 0)["identity_evidence"].pop("verifier_identity_authority")
    ),
    "empty-evidence-reference": _m(
        lambda m: _member(m, H001, 0)["identity_evidence"].update(g1_identity_audit="")
    ),
    "evidence-reference-outside-docs": _m(
        lambda m: _member(m, H001, 0)["identity_evidence"].update(g1_identity_audit="../secrets.md")
    ),
    "missing-identity-evidence": _m(lambda m: _member(m, H001, 0).pop("identity_evidence")),
    "unknown-top-field": _m(lambda m: m.update(defaults={})),
    "unknown-handoff-field": _m(lambda m: m["handoffs"][0].update(build_batch="W0-DB08")),
    "unknown-member-field": _m(lambda m: _member(m, H001, 0).update(official_name="相吉神社")),
    "unknown-evidence-field": _m(
        lambda m: _member(m, H001, 0)["identity_evidence"].update(note="x")
    ),
    "malformed-schema-version": _m(lambda m: m.update(schema_version=2)),
    "malformed-handoffs": _m(lambda m: m.update(handoffs={})),
    "malformed-member": _m(lambda m: _members(m, H001).__setitem__(0, "nsrc-000001")),
    "malformed-candidate-id": _m(lambda m: _member(m, H001, 0).update(candidate_id="wave0-001")),
    "missing-name": _m(lambda m: _member(m, H001, 0).pop("name")),
    "cm-identity-status-regression": _c(
        lambda c: _cm_rows(c, H001)[1].update(identity_status="UNREVIEWED")
    ),
    "cm-membership-drift-removed": _c(lambda c: c["candidates"].remove(_cm_rows(c, H002)[-1])),
    "cm-membership-drift-added": _c(
        lambda c: c["candidates"].append(
            {
                **copy.deepcopy(_cm_rows(c, H002)[-1]),
                "candidate_id": "nsrc-000099",
            }
        )
    ),
    "cm-order-drift": _c(lambda c: _cm_swap(c, H002)),
    "cm-source-position-drift": _c(
        lambda c: _cm_rows(c, H001)[0]["admission_provenance"].update(
            source_position="page009-row009"
        )
    ),
    "cm-candidate-name-drift": _c(lambda c: _cm_rows(c, H001)[0].update(candidate_name="相吉社")),
    "cm-gained-official-address": _c(
        lambda c: _cm_rows(c, H001)[1].update(official_address="新潟県糸魚川市大字青海2696番地")
    ),
    "cm-gained-official-name": _c(lambda c: _cm_rows(c, H001)[1].update(official_name="青澤神社")),
    "cm-build-batch-assigned": _c(lambda c: _cm_rows(c, H001)[0].update(build_batch="W0-DB08")),
    "cm-shape": _c(lambda c: c.pop("candidates")),
}


def test_current_manifest_validates():
    validate_nationwide_identity_manifest(_manifest(), _master())


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_mutation_fails_closed(name):
    target, mutate = MUTATIONS[name]
    manifest, master = _manifest(), _master()
    mutate(manifest if target == "manifest" else master)
    with pytest.raises(HandoffIdentityError):
        validate_nationwide_identity_manifest(manifest, master)


# Candidate Master は address を持たない（official_address なし）。そのため canonical address の
# exact 文字列は runtime validator ではなく、manifest と authority record（Mother Ship decision /
# 各 G1 audit）の regression 照合で fail closed にする。


def _authority_identities() -> dict[str, tuple[str, str]]:
    frozen = {}
    text = (REPO_ROOT / DECISION).read_text(encoding="utf-8")
    block = re.search(r"```text\n(nsrc-000001.*?)```", text, re.DOTALL).group(1)
    for line in block.strip().splitlines():
        candidate_id, name, address = line.split()
        frozen[candidate_id] = (name, address)
    for n in range(6, 11):
        candidate_id = f"nsrc-{n:06d}"
        audit = (
            REPO_ROOT / f"docs/audit/niigata-h002-{candidate_id}-g1-identity-duplicate.md"
        ).read_text(encoding="utf-8")
        (name,) = re.findall(r"^official_name\s*=\s*(.+)$", audit, re.MULTILINE)
        (address,) = re.findall(r"^official_address\s*=\s*(.+)$", audit, re.MULTILINE)
        frozen[candidate_id] = (name, address)
    h003_text = (REPO_ROOT / H003_AUDIT).read_text(encoding="utf-8")
    h003_names = re.findall(r"^official_name\s*=\s*(.+)$", h003_text, re.MULTILINE)[:5]
    h003_addresses = re.findall(r"^official_address\s*=\s*(.+)$", h003_text, re.MULTILINE)[:5]
    for n, name, address in zip(range(11, 16), h003_names, h003_addresses, strict=True):
        frozen[f"nsrc-{n:06d}"] = (name, address)
    return frozen


def _authority_mismatches(manifest) -> list[str]:
    frozen = _authority_identities()
    seen = {}
    for handoff in manifest["handoffs"]:
        for member in handoff["members"]:
            seen[member["candidate_id"]] = (member["name"], member["address"])
    return sorted(cid for cid in frozen.keys() | seen.keys() if frozen.get(cid) != seen.get(cid))


def test_manifest_equals_the_authority_records():
    assert _authority_mismatches(_manifest()) == []


ADDRESS_MUTATIONS = {
    "prefecture-stripped": lambda m: _member(m, H001, 1).update(address="糸魚川市大字青海2696番地"),
    "707-banchi-added": lambda m: _member(m, H001, 2).update(address="新潟県長岡市悠久町707番地"),
    "h002-address-rewritten": lambda m: _member(m, H002, 2).update(
        address="新潟県十日町市上組2059番地"
    ),
    "h003-address-rewritten": lambda m: _member(m, H003, 3).update(
        address="新潟県五泉市上杉川1310番地"
    ),
    "width-normalized": lambda m: _member(m, H001, 4).update(
        address="新潟県柏崎市荒浜４丁目1754番地2"
    ),
}


@pytest.mark.parametrize("name", sorted(ADDRESS_MUTATIONS))
def test_canonical_address_change_fails_closed_against_the_authority(name):
    manifest = _manifest()
    ADDRESS_MUTATIONS[name](manifest)
    assert _authority_mismatches(manifest) != []


def _write(tmp_path, name, data) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_unknown_handoff_fails_closed():
    for handoff_id in (UNREGISTERED_HANDOFF, "W0-DB01", "", "niigata-001-h001"):
        with pytest.raises(HandoffIdentityError, match="unknown handoff"):
            load_handoff_shrine_identities(handoff_id)


def test_h003_is_a_reviewed_identity_handoff_after_g1():
    """H003 は G1 PASS 後の reviewed identity handoff。G2 / eligibility はまだ主張しない。"""
    master = _master()
    rows = _cm_rows(master, H003)
    assert [r["candidate_id"] for r in rows] == [
        "nsrc-000011",
        "nsrc-000012",
        "nsrc-000013",
        "nsrc-000014",
        "nsrc-000015",
    ]
    assert all(r["identity_status"] == "CONFIRMED" for r in rows)
    assert all(r["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE" for r in rows)
    assert H003 in [h["handoff_id"] for h in _manifest()["handoffs"]]
    assert load_handoff_shrine_identities(H003) == H003_IDENTITIES


def test_g0_only_handoff_is_not_a_reviewed_identity_handoff():
    """H004 は G0 Admission だけ（identity / duplicate UNREVIEWED）。G1 前は manifest に無く fail closed。"""
    rows = _cm_rows(_master(), H004)
    assert [r["candidate_id"] for r in rows] == [
        "nsrc-000016",
        "nsrc-000017",
        "nsrc-000018",
        "nsrc-000019",
        "nsrc-000020",
    ]
    assert all(r["identity_status"] == "UNREVIEWED" for r in rows)
    assert all(r["duplicate_status"] == "UNREVIEWED" for r in rows)
    assert H004 not in [h["handoff_id"] for h in _manifest()["handoffs"]]
    with pytest.raises(HandoffIdentityError, match="unknown handoff"):
        load_handoff_shrine_identities(H004)


def test_loader_rejects_mutated_files(tmp_path):
    manifest = _manifest()
    _swap(_members(manifest, H001), 0, 1)
    with pytest.raises(HandoffIdentityError):
        load_handoff_shrine_identities(H001, manifest_path=_write(tmp_path, "m.json", manifest))
    with pytest.raises(HandoffIdentityError, match="not found"):
        load_handoff_shrine_identities(H001, manifest_path=tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(HandoffIdentityError, match="invalid JSON"):
        load_handoff_shrine_identities(H001, manifest_path=bad)
    master = _master()
    _cm_rows(master, H002)[0]["identity_status"] = "UNREVIEWED"
    # 1 handoff の drift でも manifest 全体を信頼しない
    with pytest.raises(HandoffIdentityError):
        load_handoff_shrine_identities(
            H001, candidate_master_path=_write(tmp_path, "cm.json", master)
        )


# --- boundary --------------------------------------------------------------------------------


def test_candidate_master_nationwide_rows_keep_their_boundary():
    for row in _master()["candidates"]:
        if not (row.get("admission_provenance") or {}).get("handoff_id"):
            continue
        assert row["build_batch"] is None, row["candidate_id"]
        assert "official_name" not in row, row["candidate_id"]
        assert "official_address" not in row, row["candidate_id"]


def test_verifier_identity_authority_is_only_the_nationwide_manifest():
    source = Path(verifier.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "shrine_expansion_handoffs",  # G-5 test-only manifest
        "g7_specs",  # G7 artifact specs
        "shrines_seed_clean",  # Base Seed
        "knowledge_seeds",  # Knowledge Seed
        "fixtures",
    ):
        assert forbidden not in source, forbidden
    command = (
        TEMPLES_DIR / "management" / "commands" / "verify_recommendation_eligibility.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("shrine_expansion_handoffs", "g7_specs", "knowledge_seeds"):
        assert forbidden not in command, forbidden


def test_g5_test_only_manifest_is_not_imported_by_runtime_code():
    hits = []
    for path in TEMPLES_DIR.rglob("*.py"):
        if "tests" in path.relative_to(TEMPLES_DIR).parts:
            continue
        if "shrine_expansion_handoffs" in path.read_text(encoding="utf-8"):
            hits.append(str(path))
    assert hits == []


def test_verifier_and_command_contain_no_write_operation():
    for path in (
        Path(verifier.__file__),
        TEMPLES_DIR / "management" / "commands" / "verify_recommendation_eligibility.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "save",
                    "create",
                    "update",
                    "delete",
                    "bulk_create",
                    "bulk_update",
                    "get_or_create",
                    "update_or_create",
                    "write_text",
                    "call_command",
                }, (path.name, ast.unparse(node))


# --- --handoff command on the isolated test DB ---------------------------------------------------


def _import_h001_proven_state():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    for seed in ("nsrc_000002_seed.json", "nsrc_000004_seed.json"):
        call_command(
            "import_shrine_knowledge",
            str(SEED_DIR / seed),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )


def _counts():
    return (
        Shrine.objects.count(),
        ShrineKnowledgeSource.objects.count(),
        ShrineDeity.objects.count(),
        ShrineHistory.objects.count(),
    )


def _run_json(*args) -> dict:
    out = io.StringIO()
    call_command("verify_recommendation_eligibility", *args, "--json", stdout=out)
    return json.loads(out.getvalue())


@pytest.mark.django_db
def test_handoff_reproduces_the_proven_h001_eligibility():
    _import_h001_proven_state()
    report = verify_recommendation_eligibility(
        shrine_identities=load_handoff_shrine_identities(H001)
    )
    by_label = {r.requested: r for r in report.results}
    n2 = by_label["青澤神社 / 新潟県糸魚川市大字青海2696番地"]
    n4 = by_label["青海神社 / 新潟県加茂市大字加茂字宮山229番地"]
    assert (n2.status, n2.usable_deity_fact_count, n2.usable_history_fact_count) == (ELIGIBLE, 0, 1)
    assert (n4.status, n4.usable_deity_fact_count, n4.usable_history_fact_count) == (ELIGIBLE, 2, 2)

    # direct ShrineIdentity（既存 G5 test の経路）と同一の結果
    for identity, result in ((H001_IDENTITIES[1], n2), (H001_IDENTITIES[3], n4)):
        direct = verify_recommendation_eligibility(shrine_identities=[identity])
        assert direct.results == [result]


@pytest.mark.django_db
def test_handoff_group_reports_current_state_without_forcing_eligibility():
    _import_h001_proven_state()
    before = _counts()
    payload = _run_json("--handoff", H001)
    assert _counts() == before

    results = payload["results"]
    assert [r["requested"] for r in results] == [i.label() for i in H001_IDENTITIES]
    assert [r["status"] for r in results] == [
        UNRESOLVED,
        ELIGIBLE,
        UNRESOLVED,
        ELIGIBLE,
        UNRESOLVED,
    ]
    assert payload["summary"] == {
        "requested_count": 5,
        "eligible_count": 2,
        "ineligible_count": 0,
        "unresolved_count": 3,
        "all_eligible": False,
    }
    # handoff 経路は既存 direct 経路と同じ report を返す
    direct = verify_recommendation_eligibility(shrine_identities=H001_IDENTITIES)
    assert payload == json.loads(json.dumps(direct.as_dict(), ensure_ascii=False))

    with pytest.raises(CommandError, match="ALL_ELIGIBLE=FAIL"):
        call_command(
            "verify_recommendation_eligibility",
            "--handoff",
            H001,
            "--require-all-eligible",
            stdout=io.StringIO(),
        )
    assert _counts() == before


@pytest.mark.django_db
def test_handoff_text_output_and_h002_unresolved_state():
    _import_h001_proven_state()
    out = io.StringIO()
    call_command("verify_recommendation_eligibility", "--handoff", H001, stdout=out)
    text = out.getvalue()
    assert "ELIGIBLE   = 2" in text and "UNRESOLVED = 3" in text
    assert "ALL_ELIGIBLE = FAIL" in text

    payload = _run_json("--handoff", H002)
    # nsrc-000006 / nsrc-000007 / nsrc-000009 の Base Shrine materialization 後:
    # 3 Shrineは exact identity で解決されるが、この helper は対象Knowledgeを投入しないため INELIGIBLE。
    # nsrc-000008 / 000010 は未materializeのため UNRESOLVED。
    assert [r["status"] for r in payload["results"]] == [
        INELIGIBLE,
        INELIGIBLE,
        UNRESOLVED,
        INELIGIBLE,
        UNRESOLVED,
    ]
    assert payload["summary"] == {
        "requested_count": 5,
        "eligible_count": 0,
        "ineligible_count": 3,
        "unresolved_count": 2,
        "all_eligible": False,
    }


@pytest.mark.django_db
def test_handoff_input_contract():
    with pytest.raises(CommandError, match="併用できない"):
        call_command(
            "verify_recommendation_eligibility",
            "--batch",
            "W0-DB01",
            "--handoff",
            H001,
            stdout=io.StringIO(),
        )
    with pytest.raises(CommandError, match="unknown handoff"):
        call_command(
            "verify_recommendation_eligibility",
            "--handoff",
            UNREGISTERED_HANDOFF,
            stdout=io.StringIO(),
        )
    with pytest.raises(CommandError, match="--handoff"):
        call_command("verify_recommendation_eligibility", stdout=io.StringIO())
    # --batch は従来どおり Wave0 build_batch 経路（Nationwide handoff として解釈しない）
    with pytest.raises(CommandError, match="build_batch=NIIGATA-001-H001"):
        call_command("verify_recommendation_eligibility", "--batch", H001, stdout=io.StringIO())
