from __future__ import annotations

import io
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed, resolve_shrine

SCHEMA_VERSION = "1.0"


def _minimal_seed(**overrides) -> dict:
    seed = {
        "schema_version": SCHEMA_VERSION,
        "sources": [
            {
                "key": "src-1",
                "source_type": "shrine_official",
                "title": "公式サイト",
                "url": "https://example.jp/",
                "verification_status": "source_confirmed",
                "verified_at": "2026-01-01T00:00:00Z",
                "confidence": "high",
            }
        ],
        "shrines": [
            {
                "shrine_ref": {"name_jp": "テスト対象神社", "address": "東京都テスト区1-1-1"},
                "deities": [
                    {
                        "display_name": "テスト祭神",
                        "role": "primary",
                        "verification_status": "source_confirmed",
                        "verified_at": "2026-01-01T00:00:00Z",
                        "confidence": "high",
                        "source_keys": ["src-1"],
                    }
                ],
                "histories": [
                    {
                        "history_type": "official_origin",
                        "title": "由緒",
                        "content": "テスト由緒本文",
                        "verification_status": "source_confirmed",
                        "verified_at": "2026-01-01T00:00:00Z",
                        "confidence": "high",
                        "source_keys": ["src-1"],
                    }
                ],
            }
        ],
    }
    seed.update(overrides)
    return seed


# ---------- parse_seed ----------


def test_parse_seed_valid_has_no_errors():
    parsed = parse_seed(_minimal_seed())
    assert parsed.errors == []
    assert len(parsed.sources) == 1
    assert len(parsed.shrines) == 1
    assert parsed.shrines[0].deities[0].display_name == "テスト祭神"


def test_parse_seed_rejects_wrong_schema_version():
    seed = _minimal_seed(schema_version="0.9")
    parsed = parse_seed(seed)
    assert any("schema_version" in e for e in parsed.errors)


def test_parse_seed_rejects_invalid_enum_values():
    seed = _minimal_seed()
    seed["sources"][0]["source_type"] = "not_a_real_type"
    seed["shrines"][0]["deities"][0]["role"] = "not_a_real_role"
    seed["shrines"][0]["histories"][0]["history_type"] = "not_a_real_type"
    parsed = parse_seed(seed)
    assert any("source_type" in e for e in parsed.errors)
    assert any(".role:" in e for e in parsed.errors)
    assert any("history_type" in e for e in parsed.errors)


def test_parse_seed_requires_verified_at_when_source_confirmed():
    seed = _minimal_seed()
    del seed["sources"][0]["verified_at"]
    parsed = parse_seed(seed)
    assert any("verified_at" in e and "sources[0]" in e for e in parsed.errors)


def test_parse_seed_rejects_unknown_source_key_reference():
    seed = _minimal_seed()
    seed["shrines"][0]["deities"][0]["source_keys"] = ["does-not-exist"]
    parsed = parse_seed(seed)
    assert any("unknown source key" in e for e in parsed.errors)


def test_parse_seed_rejects_blank_required_fields():
    seed = _minimal_seed()
    seed["shrines"][0]["shrine_ref"]["name_jp"] = "   "
    seed["shrines"][0]["deities"][0]["display_name"] = ""
    seed["shrines"][0]["histories"][0]["content"] = ""
    parsed = parse_seed(seed)
    assert any("name_jp" in e for e in parsed.errors)
    assert any("display_name" in e for e in parsed.errors)
    assert any("content" in e for e in parsed.errors)


# ---------- resolve_shrine ----------


@pytest.mark.django_db
def test_resolve_shrine_single_match_ok():
    shrine = Shrine.objects.create(name_jp="単独神社", kind="shrine", address="住所A")
    result = resolve_shrine("単独神社", "住所A")
    assert result.status == "OK"
    assert result.shrine == shrine


@pytest.mark.django_db
def test_resolve_shrine_not_found():
    result = resolve_shrine("存在しない神社", "")
    assert result.status == "NOT_FOUND"
    assert result.shrine is None


@pytest.mark.django_db
def test_resolve_shrine_duplicate_resolved_via_canonical_preference():
    """Mirrors the real 0091 production pattern: a canonical row
    (place_ref_id NULL) plus a later place-resolved duplicate sharing the
    same name_jp and address."""
    canonical = Shrine.objects.create(
        name_jp="重複名神社", kind="shrine", address="同一住所", place_ref_id=None
    )
    from temples.models import PlaceRef

    place_ref = PlaceRef.objects.create(place_id="dummy-place-id-1", name="重複名神社")
    Shrine.objects.create(
        name_jp="重複名神社", kind="shrine", address="同一住所", place_ref_id=place_ref.pk
    )

    result = resolve_shrine("重複名神社", "同一住所")
    assert result.status == "OK_CANONICAL_PREFERRED"
    assert result.shrine == canonical


@pytest.mark.django_db
def test_resolve_shrine_ambiguous_when_both_canonical():
    Shrine.objects.create(name_jp="真の重複神社", kind="shrine", address="住所X", place_ref_id=None)
    Shrine.objects.create(name_jp="真の重複神社", kind="shrine", address="住所Y", place_ref_id=None)
    result = resolve_shrine("真の重複神社", "")
    assert result.status == "AMBIGUOUS"
    assert result.shrine is None


# ---------- import_shrine_knowledge command ----------


@pytest.mark.django_db
def test_import_validate_only_passes_for_valid_seed_with_existing_shrine(tmp_path):
    Shrine.objects.create(name_jp="テスト対象神社", kind="shrine", address="東京都テスト区1-1-1")
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(seed_path), "--validate-only", stdout=out)
    assert "OK" in out.getvalue()
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0
    assert ShrineKnowledgeSource.objects.count() == 0


@pytest.mark.django_db
def test_import_validate_only_fails_when_shrine_not_found(tmp_path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", str(seed_path), "--validate-only")
    assert ShrineDeity.objects.count() == 0


@pytest.mark.django_db
def test_import_dry_run_computes_plan_without_writing(tmp_path):
    Shrine.objects.create(name_jp="テスト対象神社", kind="shrine", address="東京都テスト区1-1-1")
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(seed_path), "--dry-run", stdout=out)
    text = out.getvalue()
    assert "CREATE" in text
    assert "dry-run: OK" in text
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0
    assert ShrineKnowledgeSource.objects.count() == 0


@pytest.mark.django_db
def test_import_applies_and_links_sources(tmp_path):
    Shrine.objects.create(name_jp="テスト対象神社", kind="shrine", address="東京都テスト区1-1-1")
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(seed_path), stdout=out)

    assert ShrineKnowledgeSource.objects.count() == 1
    assert ShrineDeity.objects.count() == 1
    assert ShrineHistory.objects.count() == 1

    deity = ShrineDeity.objects.get()
    history = ShrineHistory.objects.get()
    assert deity.display_name == "テスト祭神"
    assert list(deity.sources.values_list("title", flat=True)) == ["公式サイト"]
    assert list(history.sources.values_list("title", flat=True)) == ["公式サイト"]


@pytest.mark.django_db
def test_import_is_idempotent_on_second_run(tmp_path):
    Shrine.objects.create(name_jp="テスト対象神社", kind="shrine", address="東京都テスト区1-1-1")
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    call_command("import_shrine_knowledge", str(seed_path), stdout=io.StringIO())
    call_command("import_shrine_knowledge", str(seed_path), stdout=io.StringIO())

    assert ShrineKnowledgeSource.objects.count() == 1
    assert ShrineDeity.objects.count() == 1
    assert ShrineHistory.objects.count() == 1


@pytest.mark.django_db
def test_import_blocks_entirely_on_ambiguous_shrine_no_partial_write(tmp_path):
    """Second shrine block is unresolvable (two canonical-looking duplicates);
    the whole import must abort with zero writes, including for the first,
    perfectly valid shrine block (atomic all-or-nothing)."""
    Shrine.objects.create(name_jp="テスト対象神社", kind="shrine", address="東京都テスト区1-1-1")
    Shrine.objects.create(name_jp="曖昧神社", kind="shrine", address="住所X", place_ref_id=None)
    Shrine.objects.create(name_jp="曖昧神社", kind="shrine", address="住所Y", place_ref_id=None)

    seed = _minimal_seed()
    seed["shrines"].append(
        {
            "shrine_ref": {"name_jp": "曖昧神社", "address": ""},
            "deities": [
                {
                    "display_name": "曖昧祭神",
                    "verification_status": "draft",
                }
            ],
            "histories": [],
        }
    )
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", str(seed_path), stdout=io.StringIO())

    assert ShrineKnowledgeSource.objects.count() == 0
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0


@pytest.mark.django_db
def test_import_blocks_on_shrine_not_found(tmp_path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_minimal_seed()), encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", str(seed_path), stdout=io.StringIO())
    assert ShrineKnowledgeSource.objects.count() == 0


@pytest.mark.django_db
def test_import_rejects_malformed_json(tmp_path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", str(seed_path))


@pytest.mark.django_db
def test_import_rejects_missing_file(tmp_path):
    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", str(tmp_path / "does-not-exist.json"))


# ---------- export_shrine_knowledge command + round-trip ----------


@pytest.mark.django_db
def test_export_then_reimport_round_trip(tmp_path):
    shrine = Shrine.objects.create(
        name_jp="ラウンドトリップ神社", kind="shrine", address="東京都ラウンドトリップ区1-1-1"
    )
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式サイト",
        url="https://roundtrip.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="ラウンドトリップ祭神",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    deity.sources.set([source])
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="ラウンドトリップ由緒本文",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    history.sources.set([source])

    export_path = tmp_path / "exported.json"
    call_command("export_shrine_knowledge", str(export_path), stdout=io.StringIO())

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported["schema_version"] == SCHEMA_VERSION
    assert len(exported["sources"]) == 1
    assert len(exported["shrines"]) == 1

    # Wipe Knowledge data (but keep the Shrine) and re-import from the export.
    ShrineDeity.objects.all().delete()
    ShrineHistory.objects.all().delete()
    ShrineKnowledgeSource.objects.all().delete()

    call_command("import_shrine_knowledge", str(export_path), stdout=io.StringIO())

    assert ShrineKnowledgeSource.objects.count() == 1
    assert ShrineDeity.objects.count() == 1
    assert ShrineHistory.objects.count() == 1
    assert ShrineDeity.objects.get().display_name == "ラウンドトリップ祭神"

    # Re-importing the same export again must not duplicate anything.
    call_command("import_shrine_knowledge", str(export_path), stdout=io.StringIO())
    assert ShrineKnowledgeSource.objects.count() == 1
    assert ShrineDeity.objects.count() == 1
    assert ShrineHistory.objects.count() == 1


@pytest.mark.django_db
def test_export_refuses_when_knowledge_exists_on_qa_fixture_shrine(tmp_path):
    qa_shrine = Shrine.objects.create(name_jp="テスト神社", kind="shrine", address="")
    ShrineDeity.objects.create(shrine=qa_shrine, display_name="QA祭神", verification_status="draft")
    output_path = tmp_path / "should-not-be-written.json"
    with pytest.raises(CommandError):
        call_command("export_shrine_knowledge", str(output_path), stdout=io.StringIO())
    assert not output_path.exists()
