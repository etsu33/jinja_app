"""Shrine Source Candidate Extraction Runner（新潟県 Batch 001）の contract test。

正本: docs/audit/shrine-source-candidate-extraction-contract.md（§17 T1〜T14 + 実装 contract T15〜T20）。
snapshot は架空の fixture だけを使う（実在の新潟県 Source 行は含めない）。network は使わない。
"""

from __future__ import annotations

import copy
import io
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction

from temples.models import Shrine
from temples.services import shrine_source_candidate_extraction as extraction
from temples.services.shrine_submission import DuplicateCandidate
from temples.services.shrine_duplicate_normalize import (
    normalize_shrine_address_for_duplicate,
    normalize_shrine_name_for_duplicate,
)
from temples.services.shrine_source_candidate_extraction import (
    DUPLICATE_LOOKUP_LIMIT,
    FAIL_DB_MUTATION,
    INVALID,
    JAPANESE_PREFECTURES,
    PLANNED_ACTION_HANDOFF,
    PLANNED_ACTION_STOP_MOTHER_SHIP_REVIEW,
    PLANNED_ACTION_STOP_PREFECTURE_REVIEW,
    PLANNED_ACTION_STOP_SOURCE_REVIEW,
    READY_CANDIDATE,
    READY_HANDOFF_MAX,
    REVIEW_PACKET_FIELDS,
    REVIEW_REQUIRED,
    STOP_BATCH_CONTRACT,
    STOP_INPUT,
    STOP_PREFECTURE,
    STOP_REPRODUCIBILITY,
    STOP_SOURCE_DRIFT,
    CandidateExtractionStop,
    diff_runs,
    read_only_guard,
    run_extraction,
    run_with_reproducibility_check,
)
from temples.services.shrine_source_candidate_niigata import (
    NIIGATA_BATCH_001,
    parse_niigata_batch_001_snapshot,
)

SOURCE_URL = "https://example.invalid/niigata-jinjacho/directory"
DETAIL_URL = "https://example.invalid/niigata-jinjacho/detail"


def _row(n: int, **overrides) -> dict:
    row = {
        "source_position": f"page{(n - 1) // 10 + 1:03d}-row{(n - 1) % 10 + 1:03d}",
        "raw_name": f"試験抽出神社{n:03d}",
        "raw_address": f"新潟県試験市試験町{n}-1",
    }
    row.update(overrides)
    return row


def _snapshot(rows: list[dict] | None = None, **meta_overrides) -> dict:
    meta = {
        "prefecture": "新潟県",
        "batch_id": "NIIGATA-001",
        "source_type": "prefectural_jinjacho_official",
        "source_url": SOURCE_URL,
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T00:00:00+09:00",
        "selection_rule": "検索条件なし / Source既定表示順 / ordinal 1-100",
    }
    meta.update(meta_overrides)
    return {
        "snapshot": meta,
        "candidates": rows if rows is not None else [_row(n) for n in range(1, 101)],
    }


def _run(snapshot: dict) -> dict:
    contract, meta, raws = parse_niigata_batch_001_snapshot(snapshot)
    return run_extraction(contract, meta, raws)


def _by_position(artifact: dict) -> dict:
    return {row["source_position"]: row for row in artifact["rows"]}


def _shrine(name: str, address: str) -> Shrine:
    return Shrine.objects.create(
        name_jp=name, kind="shrine", address=address, latitude=37.9, longitude=139.0
    )


def _replace(rows: list[dict], n: int, **overrides) -> list[dict]:
    rows = copy.deepcopy(rows)
    rows[n - 1] = _row(n, **overrides)
    return rows


BASE_ROWS = [_row(n) for n in range(1, 101)]
pytestmark = pytest.mark.django_db


# ---------- T1 / T2: required fields ----------


@pytest.mark.parametrize("value", [None, "", "   ", "　"])
def test_t1_missing_name_is_invalid_without_lookup(value):
    artifact = _run(_snapshot(_replace(BASE_ROWS, 1, raw_name=value)))
    row = artifact["rows"][0]
    assert row["classification"] == INVALID
    assert row["planned_action"] == PLANNED_ACTION_STOP_SOURCE_REVIEW
    assert row["schema_name"] == "FAIL"
    assert row["schema_gate_result"] == "FAIL"
    assert row["duplicate_lookup_performed"] is False
    assert row["returned_candidate_count"] is None
    assert row["identity_candidate"] is None
    assert row["raw_name"] == value


@pytest.mark.parametrize("value", [None, "", "  "])
def test_t2_missing_address_is_invalid_without_lookup(value):
    artifact = _run(_snapshot(_replace(BASE_ROWS, 2, raw_address=value)))
    row = artifact["rows"][1]
    assert row["classification"] == INVALID
    assert row["planned_action"] == PLANNED_ACTION_STOP_SOURCE_REVIEW
    assert row["schema_address"] == "FAIL"
    assert row["duplicate_lookup_performed"] is False


# ---------- T3 / T20: prefecture ----------


def test_t3_explicit_other_prefecture_is_review_required_and_not_corrected():
    artifact = _run(_snapshot(_replace(BASE_ROWS, 3, raw_address="山形県試験市試験町3-1")))
    row = artifact["rows"][2]
    assert row["classification"] == REVIEW_REQUIRED
    assert row["planned_action"] == PLANNED_ACTION_STOP_PREFECTURE_REVIEW
    assert "PREFECTURE_MISMATCH" in row["review_reason"]
    assert row["schema_prefecture"] == "FAIL"
    assert row["raw_address"] == "山形県試験市試験町3-1"


def test_t20_address_without_prefecture_prefix_is_not_a_mismatch():
    artifact = _run(_snapshot(_replace(BASE_ROWS, 4, raw_address="試験市試験町4-1")))
    row = artifact["rows"][3]
    assert row["classification"] == READY_CANDIDATE
    assert row["schema_prefecture"] == "PASS"
    assert row["raw_address"] == "試験市試験町4-1"
    assert row["normalized_address"] == "試験市試験町4-1"


def test_prefecture_list_is_the_existing_47():
    assert len(JAPANESE_PREFECTURES) == 47
    assert "新潟県" in JAPANESE_PREFECTURES


# ---------- T4〜T7: collision lookup ----------


def test_t4_zero_lookup_candidates_is_ready_candidate():
    row = _run(_snapshot())["rows"][0]
    assert row["returned_candidate_count"] == 0
    assert row["possibly_truncated"] is False
    assert row["classification"] == READY_CANDIDATE
    assert row["planned_action"] == PLANNED_ACTION_HANDOFF
    assert row["schema_gate_result"] == "PASS"


def test_t5_one_lookup_candidate_is_review_required_not_duplicate():
    existing = _shrine("試験抽出神社005", "新潟県試験市試験町5-1")
    row = _run(_snapshot())["rows"][4]
    assert row["returned_candidate_count"] == 1
    assert row["returned_candidate_ids"] == [existing.id]
    assert row["returned_candidate_names"] == ["試験抽出神社005"]
    assert row["returned_candidate_addresses"] == ["新潟県試験市試験町5-1"]
    assert row["classification"] == REVIEW_REQUIRED
    assert row["planned_action"] == PLANNED_ACTION_STOP_MOTHER_SHIP_REVIEW
    assert row["review_reason"] == ["COLLISION_CANDIDATES_RETURNED"]
    assert row["schema_gate_result"] == "NOT_EVALUATED"


def test_t6_multiple_lookup_candidates_is_review_required():
    a = _shrine("試験抽出神社006", "新潟県別市1-1")
    b = _shrine("試験抽出神社006", "新潟県別市2-2")
    row = _run(_snapshot())["rows"][5]
    assert row["returned_candidate_count"] == 2
    assert row["returned_candidate_ids"] == sorted([a.id, b.id])
    assert row["classification"] == REVIEW_REQUIRED
    assert row["possibly_truncated"] is False


def test_t7_lookup_at_limit_is_review_required_and_possibly_truncated():
    for i in range(DUPLICATE_LOOKUP_LIMIT + 5):
        _shrine(f"試験抽出神社007分社{i:03d}", f"新潟県別市{i}-7")
    artifact = _run(_snapshot())
    row = artifact["rows"][6]
    assert row["returned_candidate_count"] == DUPLICATE_LOOKUP_LIMIT
    assert row["possibly_truncated"] is True
    assert row["classification"] == REVIEW_REQUIRED
    assert "COLLISION_LOOKUP_POSSIBLY_TRUNCATED" in row["review_reason"]
    assert artifact["summary"]["possibly_truncated_count"] == 1


# ---------- T8〜T10: no identity / merge inference ----------


def test_t8_shared_source_url_and_detail_url_alone_do_not_imply_duplicate():
    rows = _replace(BASE_ROWS, 8, detail_url=DETAIL_URL)
    rows = _replace(rows, 9, detail_url=DETAIL_URL)
    artifact = _run(_snapshot(rows))
    for index in (7, 8):
        row = artifact["rows"][index]
        assert row["source_url"] == SOURCE_URL
        assert row["detail_url"] == DETAIL_URL
        assert row["classification"] == READY_CANDIDATE


def test_t9_same_source_id_alone_does_not_imply_identity():
    rows = _replace(BASE_ROWS, 10, source_id="SRC-1")
    rows = _replace(rows, 11, source_id="SRC-1")
    artifact = _run(_snapshot(rows))
    assert [artifact["rows"][i]["classification"] for i in (9, 10)] == [READY_CANDIDATE] * 2
    assert artifact["rows"][9]["raw_name"] != artifact["rows"][10]["raw_name"]


def test_t10_same_identity_candidate_alone_does_not_auto_merge():
    rows = _replace(BASE_ROWS, 13, raw_name="試験抽出神社012", raw_address="新潟県試験市試験町12-1")
    artifact = _run(_snapshot(rows))
    a, b = artifact["rows"][11], artifact["rows"][12]
    assert a["identity_candidate"] == b["identity_candidate"]
    assert a["source_position"] != b["source_position"]
    assert artifact["summary"]["total_raw"] == 100
    assert a["classification"] == b["classification"] == READY_CANDIDATE


# ---------- T11: raw preservation ----------


def test_t11_raw_values_are_preserved_and_normalized_separately():
    raw_name = " 髙 試験（旧称）神社　本宮 "
    raw_address = " 試験市　試験町１４－１ "
    rows = _replace(
        BASE_ROWS,
        14,
        raw_name=raw_name,
        raw_address=raw_address,
        kana="しけん",
        phone="000-0000-0000",
        source_id="SRC-14",
        detail_url=DETAIL_URL,
    )
    row = _run(_snapshot(rows))["rows"][13]
    assert row["raw_name"] == raw_name
    assert row["raw_address"] == raw_address
    assert (row["kana"], row["phone"], row["source_id"], row["detail_url"]) == (
        "しけん",
        "000-0000-0000",
        "SRC-14",
        DETAIL_URL,
    )
    assert row["source_position"] == "page002-row004"
    assert row["normalized_name"] == normalize_shrine_name_for_duplicate(raw_name)
    assert row["normalized_address"] == normalize_shrine_address_for_duplicate(raw_address)
    assert not row["raw_address"].startswith("新潟県")


def test_omitted_optional_fields_stay_none():
    row = _run(_snapshot())["rows"][0]
    assert (row["kana"], row["phone"], row["source_id"], row["detail_url"]) == (None,) * 4


# ---------- T12 / reproducibility ----------


def test_t12_same_input_and_db_state_is_deterministic():
    _shrine("試験抽出神社020", "新潟県試験市試験町20-1")
    snapshot = _snapshot()
    first, second = _run(snapshot), _run(copy.deepcopy(snapshot))
    assert diff_runs(first, second) == []
    from temples.management.commands.extract_shrine_source_candidates import render_artifact

    assert render_artifact(first) == render_artifact(second)
    contract, meta, raws = parse_niigata_batch_001_snapshot(snapshot)
    artifact, diffs = run_with_reproducibility_check(contract, meta, raws)
    assert diffs == []
    assert artifact["summary"] == first["summary"]


def test_reproducibility_diff_is_reported_not_hidden(monkeypatch):
    contract, meta, raws = parse_niigata_batch_001_snapshot(_snapshot())
    real = extraction.find_duplicate_candidates
    calls = {"n": 0}

    def _flaky(**kwargs):
        calls["n"] += 1
        result = real(**kwargs)
        if calls["n"] > len(raws) and kwargs["name"] == "試験抽出神社001":
            return [DuplicateCandidate(id=1, name="x", address="y")]
        return result

    monkeypatch.setattr(extraction, "find_duplicate_candidates", _flaky, raising=True)
    with pytest.raises(CandidateExtractionStop) as exc:
        run_with_reproducibility_check(contract, meta, raws)
    assert exc.value.code == STOP_REPRODUCIBILITY
    assert "rows[0].classification" in exc.value.detail


# ---------- T13: read-only ----------


def test_t13_run_leaves_shrine_rows_unchanged():
    _shrine("試験抽出神社030", "新潟県試験市試験町30-1")
    before = list(Shrine.objects.order_by("id").values_list("id", "name_jp", "address"))
    _run(_snapshot())
    after = list(Shrine.objects.order_by("id").values_list("id", "name_jp", "address"))
    assert after == before


def test_read_only_guard_fails_on_any_write():
    with pytest.raises(CandidateExtractionStop) as exc:
        with transaction.atomic(), read_only_guard():
            _shrine("書き込み禁止神社", "新潟県試験市1-1")
    assert exc.value.code == FAIL_DB_MUTATION
    assert not Shrine.objects.filter(name_jp="書き込み禁止神社").exists()


# ---------- T14: totals ----------


def test_t14_classification_totals_sum_to_total():
    _shrine("試験抽出神社040", "新潟県試験市試験町40-1")
    rows = _replace(BASE_ROWS, 41, raw_name="")
    rows = _replace(rows, 42, raw_address="福島県試験市1-1")
    summary = _run(_snapshot(rows))["summary"]
    assert summary == {
        "total_raw": 100,
        "ready_count": 97,
        "review_required_count": 2,
        "invalid_count": 1,
        "possibly_truncated_count": 0,
    }


# ---------- T15 / T16: batch contract ----------


@pytest.mark.parametrize("count", [101, 99, 0])
def test_t15_batch_001_requires_exactly_100_raw_rows(count):
    rows = [_row(n) for n in range(1, count + 1)]
    contract, meta, raws = parse_niigata_batch_001_snapshot(_snapshot(rows))
    with pytest.raises(CandidateExtractionStop) as exc:
        run_extraction(contract, meta, raws)
    assert exc.value.code == STOP_BATCH_CONTRACT


@pytest.mark.parametrize("position", ["page001-row001", "", "  "])
def test_t16_duplicate_or_empty_source_position_is_rejected(position):
    rows = _replace(BASE_ROWS, 2, source_position=position)
    contract, meta, raws = parse_niigata_batch_001_snapshot(_snapshot(rows))
    with pytest.raises(CandidateExtractionStop) as exc:
        run_extraction(contract, meta, raws)
    assert exc.value.code == STOP_BATCH_CONTRACT


# ---------- T17〜T19: handoff ----------


def _mixed_snapshot() -> dict:
    """READY 11件（handoff 5 / 5 / 1）と REVIEW 1件・INVALID 88件を source 順で混ぜた batch。"""
    rows = copy.deepcopy(BASE_ROWS)
    for n in range(13, 101):
        rows[n - 1] = _row(n, raw_name="")
    rows = _replace(rows, 3, raw_address="秋田県試験市1-1")
    return _snapshot(rows)


def test_t17_handoff_groups_have_at_most_five_ready_rows():
    artifact = _run(_mixed_snapshot())
    sizes = [len(h["members"]) for h in artifact["ready_handoffs"]]
    assert artifact["summary"]["ready_count"] == 11
    assert sizes == [5, 5, 1]
    assert all(size <= READY_HANDOFF_MAX for size in sizes)
    assert [h["handoff_id"] for h in artifact["ready_handoffs"]] == [
        "NIIGATA-001-H001",
        "NIIGATA-001-H002",
        "NIIGATA-001-H003",
    ]


def test_t18_review_and_invalid_never_enter_handoffs():
    artifact = _run(_mixed_snapshot())
    rows = _by_position(artifact)
    members = [m["source_position"] for h in artifact["ready_handoffs"] for m in h["members"]]
    assert all(rows[p]["classification"] == READY_CANDIDATE for p in members)
    assert len(members) == artifact["summary"]["ready_count"]


def test_t19_handoffs_preserve_source_traversal_order():
    artifact = _run(_mixed_snapshot())
    members = [m["source_position"] for h in artifact["ready_handoffs"] for m in h["members"]]
    ready_in_order = [
        r["source_position"] for r in artifact["rows"] if r["classification"] == READY_CANDIDATE
    ]
    assert members == ready_in_order
    assert [r["source_position"] for r in artifact["rows"]] == [
        r["source_position"] for r in BASE_ROWS
    ]


# ---------- M5 review packets ----------


def test_review_packets_carry_mother_ship_evidence_without_resolution():
    existing = _shrine("試験抽出神社005", "新潟県試験市試験町5-1")
    artifact = _run(_snapshot(_replace(BASE_ROWS, 3, raw_address="山形県試験市1-1")))
    packets = artifact["review_packets"]
    assert [p["source_position"] for p in packets] == ["page001-row003", "page001-row005"]
    for packet in packets:
        assert set(packet) == set(REVIEW_PACKET_FIELDS)
        assert packet["batch_id"] == "NIIGATA-001"
        assert "classification" not in packet
    assert packets[1]["returned_candidate_ids"] == [existing.id]
    assert {r["classification"] for r in artifact["rows"]} <= {
        READY_CANDIDATE,
        REVIEW_REQUIRED,
        INVALID,
    }


# ---------- adapter boundary ----------


def test_adapter_rejects_unknown_candidate_key_as_source_drift():
    rows = _replace(BASE_ROWS, 1, deity="架空")
    with pytest.raises(CandidateExtractionStop) as exc:
        parse_niigata_batch_001_snapshot(_snapshot(rows))
    assert exc.value.code == STOP_SOURCE_DRIFT


def test_adapter_rejects_missing_required_key_as_source_drift():
    rows = copy.deepcopy(BASE_ROWS)
    del rows[0]["raw_address"]
    with pytest.raises(CandidateExtractionStop) as exc:
        parse_niigata_batch_001_snapshot(_snapshot(rows))
    assert exc.value.code == STOP_SOURCE_DRIFT


def test_adapter_rejects_non_string_raw_value_as_source_drift():
    rows = _replace(BASE_ROWS, 1, raw_name=123)
    with pytest.raises(CandidateExtractionStop) as exc:
        parse_niigata_batch_001_snapshot(_snapshot(rows))
    assert exc.value.code == STOP_SOURCE_DRIFT


@pytest.mark.parametrize(
    "key", ["source_url", "source_verified_at", "captured_at", "selection_rule"]
)
def test_adapter_rejects_empty_snapshot_metadata_as_stop_input(key):
    with pytest.raises(CandidateExtractionStop) as exc:
        parse_niigata_batch_001_snapshot(_snapshot(**{key: ""}))
    assert exc.value.code == STOP_INPUT


def test_unexpected_prefecture_metadata_stops():
    contract, meta, raws = parse_niigata_batch_001_snapshot(_snapshot(prefecture="山形県"))
    with pytest.raises(CandidateExtractionStop) as exc:
        run_extraction(contract, meta, raws)
    assert exc.value.code == STOP_PREFECTURE


def test_unexpected_batch_id_or_source_type_stops():
    for overrides, code in (
        ({"batch_id": "NIIGATA-002"}, STOP_BATCH_CONTRACT),
        ({"source_type": "other"}, STOP_INPUT),
    ):
        contract, meta, raws = parse_niigata_batch_001_snapshot(_snapshot(**overrides))
        with pytest.raises(CandidateExtractionStop) as exc:
            run_extraction(contract, meta, raws)
        assert exc.value.code == code


def test_niigata_batch_001_contract_values():
    assert NIIGATA_BATCH_001.prefecture == "新潟県"
    assert NIIGATA_BATCH_001.batch_id == "NIIGATA-001"
    assert NIIGATA_BATCH_001.required_raw_count == 100
    assert NIIGATA_BATCH_001.source_type == "prefectural_jinjacho_official"


# ---------- command ----------


def test_command_writes_artifact_only_when_output_is_given(tmp_path):
    input_path = tmp_path / "snapshot.json"
    input_path.write_text(json.dumps(_snapshot(), ensure_ascii=False), encoding="utf-8")
    out = io.StringIO()
    call_command(
        "extract_shrine_source_candidates",
        "--adapter",
        "niigata-batch-001",
        "--input",
        str(input_path),
        "--verify-reproducibility",
        stdout=out,
    )
    assert "total_raw=100 ready=100" in out.getvalue()
    assert "reproducibility=PASS db_write=0" in out.getvalue()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["snapshot.json"]

    output_path = tmp_path / "artifact.json"
    call_command(
        "extract_shrine_source_candidates",
        "--adapter",
        "niigata-batch-001",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        stdout=io.StringIO(),
    )
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["batch_id"] == "NIIGATA-001"
    assert artifact["summary"]["total_raw"] == 100
    assert len(artifact["ready_handoffs"]) == 20


def test_command_stop_is_a_command_error(tmp_path):
    input_path = tmp_path / "snapshot.json"
    input_path.write_text(
        json.dumps(_snapshot([_row(n) for n in range(1, 102)]), ensure_ascii=False),
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match=STOP_BATCH_CONTRACT):
        call_command(
            "extract_shrine_source_candidates",
            "--adapter",
            "niigata-batch-001",
            "--input",
            str(input_path),
            stdout=io.StringIO(),
        )
