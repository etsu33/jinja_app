# -*- coding: utf-8 -*-
"""import_feature_words_en コマンドのテスト。"""

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import Shrine, ShrineFeatureWordEn

HIE = ("日枝神社", "東京都千代田区永田町2-10-5")
MITAKE = ("武蔵御嶽神社", "東京都青梅市御岳山176")


def _create(name_jp, address):
    return Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)


def _run(*args):
    out, err = StringIO(), StringIO()
    call_command("import_feature_words_en", *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


@pytest.mark.django_db
def test_imports_resolved_shrines_and_reports_the_rest():
    hie = _create(*HIE)
    mitake = _create(*MITAKE)

    out, err = _run()

    assert ShrineFeatureWordEn.objects.filter(shrine=hie).count() == 10
    assert ShrineFeatureWordEn.objects.filter(shrine=mitake).count() == 13
    row = ShrineFeatureWordEn.objects.get(shrine=hie, word_id="C_VERMILION")
    assert row.note == "現在の社殿は1958年の再建"
    assert row.source_url == "https://www.hiejinja.net/english/"
    assert str(row.checked_on) == "2026-11-12"
    # 作っていない8社は推測で入れず、ERROR として報告する
    assert err.count("ERROR") == 8
    assert "shrines=2 rows=23 problems=8" in out


@pytest.mark.django_db
def test_rerun_replaces_rows_instead_of_duplicating():
    hie = _create(*HIE)
    _run()
    _run()
    assert ShrineFeatureWordEn.objects.filter(shrine=hie).count() == 10


@pytest.mark.django_db
def test_dry_run_writes_nothing():
    _create(*HIE)
    out, _ = _run("--dry-run")
    assert ShrineFeatureWordEn.objects.count() == 0
    assert "PLAN shrine='日枝神社'" in out


@pytest.mark.django_db
def test_strict_fails_when_a_shrine_cannot_be_resolved():
    _create(*HIE)
    with pytest.raises(CommandError):
        _run("--strict")


@pytest.mark.django_db
def test_same_name_at_another_address_is_not_used():
    _create("日枝神社", "別の住所")
    _run()
    assert ShrineFeatureWordEn.objects.count() == 0


@pytest.mark.django_db
def test_unknown_word_id_skips_that_shrine(tmp_path):
    _create(*HIE)
    seed = {
        "schema_version": "1.0",
        "vocabulary_version": "2026-11-12",
        "shrines": [
            {
                "shrine_ref": {"name_jp": HIE[0], "address": HIE[1]},
                "features": [
                    {
                        "word_id": "NOT_A_WORD",
                        "evidence_quote": "x",
                        "note": "",
                        "source_url": "https://example.com/",
                        "source_type": "神社公式",
                        "checked_on": "2026-11-12",
                    }
                ],
            }
        ],
    }
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    _, err = _run(str(path))
    assert ShrineFeatureWordEn.objects.count() == 0
    assert "unknown word_id" in err
