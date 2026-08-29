import io
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource


def _shrine(name: str) -> Shrine:
    return Shrine.objects.create(name_jp=name, address="東京都千代田区", popular_score=0.0)


@pytest.mark.django_db
def test_command_text_output_contains_expected_labels():
    out = io.StringIO()
    call_command("knowledge_coverage_report", stdout=out)
    text = out.getvalue()

    assert "Knowledge Coverage Report" in text
    assert "Total DB Shrines:" in text
    assert "Audit Target Shrines:" in text
    assert "Knowledge Coverage:" in text
    assert "Zero Knowledge:" in text
    assert "Fact-ready Coverage:" in text
    assert "Verified Source Count:" in text


@pytest.mark.django_db
def test_command_json_output_is_valid_and_has_expected_shape():
    out = io.StringIO()
    call_command("knowledge_coverage_report", "--format", "json", stdout=out)
    payload = json.loads(out.getvalue())

    assert "total_db_shrines" in payload
    assert "audit_target_shrines" in payload
    assert "excluded_test_shrines" in payload
    assert set(payload["knowledge_coverage"].keys()) == {"count", "percentage"}
    assert set(payload["zero_knowledge"].keys()) == {"count", "percentage"}
    fact_ready = payload["fact_ready_coverage"]
    assert set(fact_ready.keys()) == {
        "fact_ready_deity_shrines",
        "fact_ready_history_shrines",
        "fact_ready_any_shrines",
    }
    assert isinstance(payload["deity_count_distribution"], dict)
    assert isinstance(payload["source_type_distribution"], dict)


@pytest.mark.django_db
def test_command_does_not_write_to_database():
    shrine_count_before = Shrine.objects.count()
    deity_count_before = ShrineDeity.objects.count()
    history_count_before = ShrineHistory.objects.count()
    source_count_before = ShrineKnowledgeSource.objects.count()

    out = io.StringIO()
    call_command("knowledge_coverage_report", stdout=out)
    call_command("knowledge_coverage_report", "--format", "json", stdout=out)

    assert Shrine.objects.count() == shrine_count_before
    assert ShrineDeity.objects.count() == deity_count_before
    assert ShrineHistory.objects.count() == history_count_before
    assert ShrineKnowledgeSource.objects.count() == source_count_before


# --------------------------------------------------------------------------
# P9: 明示スコープ（--scope-id / --scope-ids-file）
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_command_default_output_labels_scope_without_implying_canonical():
    out = io.StringIO()
    call_command("knowledge_coverage_report", stdout=out)
    text = out.getvalue()
    assert "Coverage Scope: qa_filtered_db" in text
    assert "Audit Target Shrines:" in text  # 後方互換ラベルは維持
    assert "NOT necessarily the canonical" in text


@pytest.mark.django_db
def test_command_scope_id_repeated_json():
    a = _shrine("実在神社A")
    b = _shrine("実在神社B")
    _shrine("承認テスト神社")

    out = io.StringIO()
    call_command(
        "knowledge_coverage_report", "--format", "json",
        "--scope-id", str(a.id), "--scope-id", str(b.id), stdout=out,
    )
    payload = json.loads(out.getvalue())
    assert payload["scope"]["mode"] == "explicit"
    assert payload["audit_target_shrines"] == 2
    assert payload["scope"]["count"] == 2


@pytest.mark.django_db
def test_command_scope_ids_file_json_array_and_line_forms(tmp_path):
    a = _shrine("実在神社A")
    b = _shrine("実在神社B")

    jf = tmp_path / "scope.json"
    jf.write_text(json.dumps([a.id, b.id]), encoding="utf-8")
    out = io.StringIO()
    call_command("knowledge_coverage_report", "--format", "json", "--scope-ids-file", str(jf), stdout=out)
    assert json.loads(out.getvalue())["audit_target_shrines"] == 2

    lf = tmp_path / "scope.txt"
    lf.write_text(f"# canonical scope\n{a.id}\n{b.id}\n", encoding="utf-8")
    out = io.StringIO()
    call_command("knowledge_coverage_report", "--format", "json", "--scope-ids-file", str(lf), stdout=out)
    assert json.loads(out.getvalue())["audit_target_shrines"] == 2


@pytest.mark.django_db
def test_command_scope_id_and_file_are_mutually_exclusive(tmp_path):
    f = tmp_path / "scope.txt"
    f.write_text("1\n", encoding="utf-8")
    with pytest.raises(CommandError):
        call_command("knowledge_coverage_report", "--scope-id", "1", "--scope-ids-file", str(f))


@pytest.mark.django_db
def test_command_scope_ids_file_missing_is_hard_error(tmp_path):
    with pytest.raises(CommandError):
        call_command("knowledge_coverage_report", "--scope-ids-file", str(tmp_path / "nope.txt"))


@pytest.mark.django_db
def test_command_empty_scope_file_audits_zero_not_all(tmp_path):
    _shrine("実在神社A")
    _shrine("実在神社B")
    f = tmp_path / "scope.txt"
    f.write_text("# only comments, no ids\n\n", encoding="utf-8")

    out = io.StringIO()
    call_command("knowledge_coverage_report", "--format", "json", "--scope-ids-file", str(f), stdout=out)
    payload = json.loads(out.getvalue())
    assert payload["scope"]["mode"] == "explicit"
    assert payload["audit_target_shrines"] == 0
    assert payload["knowledge_coverage"]["count"] == 0


@pytest.mark.django_db
def test_command_explicit_scope_does_not_write(tmp_path):
    a = _shrine("実在神社A")
    f = tmp_path / "scope.txt"
    f.write_text(f"{a.id}\n", encoding="utf-8")
    before = Shrine.objects.count()
    out = io.StringIO()
    call_command("knowledge_coverage_report", "--scope-ids-file", str(f), stdout=out)
    assert Shrine.objects.count() == before
