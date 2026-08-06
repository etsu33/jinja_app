import io
import json

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource


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
