# -*- coding: utf-8 -*-
"""本番から削除した神社（temples/domain/removed_shrines.py）を、取り込みで作り直さないことのテスト。"""

import copy
import io
import json

import pytest
from django.core.management import call_command

from temples.domain.removed_shrines import REMOVED_SHRINES, is_removed_shrine
from temples.models import Shrine, ShrineDeity, ShrineHistory

KYUDEN = ("給田六所神社", "日本、〒157-0064 東京都世田谷区給田１丁目３−７")
CHOTA = ("長太稲荷神社", "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０")


def _run(command, *args):
    out = io.StringIO()
    call_command(command, *args, stdout=out, stderr=io.StringIO())
    return out.getvalue()


def test_removed_list_matches_the_seed_rows_exactly():
    # 住所が1文字でも違うと飛ばせないので、Base Seed の行と完全に一致していること
    with open("temples/data/shrines_seed_clean.json", encoding="utf-8") as f:
        rows = {(r["name_jp"], r["address"]) for r in json.load(f)}
    assert REMOVED_SHRINES == {KYUDEN, CHOTA}
    assert REMOVED_SHRINES <= rows


def test_is_removed_shrine_trims_whitespace():
    assert is_removed_shrine(f" {KYUDEN[0]} ", f"{KYUDEN[1]} ")
    assert not is_removed_shrine(KYUDEN[0], "別の住所")


@pytest.mark.django_db
def test_base_seed_import_does_not_recreate_removed_shrines():
    out = _run("import_shrines_seed", "--skip-goriyaku-tags")
    assert not Shrine.objects.filter(name_jp__in=[KYUDEN[0], CHOTA[0]]).exists()
    assert f"SKIP removed {KYUDEN[0]}" in out
    assert f"SKIP removed {CHOTA[0]}" in out
    # ほかの神社は今までどおり作られる（Base Seed 133行のうち2行だけを飛ばす）
    with open("temples/data/shrines_seed_clean.json", encoding="utf-8") as f:
        expected = {(r["name_jp"], r["address"]) for r in json.load(f)} - REMOVED_SHRINES
    assert len(expected) == 131
    assert expected <= set(Shrine.objects.values_list("name_jp", "address"))


@pytest.mark.django_db
def test_base_seed_import_leaves_an_existing_removed_row_untouched():
    # 万一まだ残っている環境でも、取り込みで書き換えない
    shrine = Shrine.objects.create(
        name_jp=KYUDEN[0], address=KYUDEN[1], kind="shrine", goriyaku="手で入れた文章"
    )
    _run("import_shrines_seed", "--skip-goriyaku-tags")
    shrine.refresh_from_db()
    assert shrine.goriyaku == "手で入れた文章"


@pytest.mark.django_db
def test_knowledge_import_skips_removed_shrine_instead_of_blocking(tmp_path):
    with open("temples/data/knowledge_seeds/batch_1_7_seed.json", encoding="utf-8") as f:
        seed = json.load(f)
    block = copy.deepcopy(
        next(b for b in seed["shrines"] if b["shrine_ref"]["name_jp"] == KYUDEN[0])
    )
    used = {
        k
        for key in ("deities", "histories")
        for fact in block.get(key, [])
        for k in fact.get("source_keys", [])
    }
    mini = {
        "schema_version": seed["schema_version"],
        "sources": [s for s in seed["sources"] if s["key"] in used],
        "shrines": [block],
    }
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(mini, ensure_ascii=False), encoding="utf-8")

    out = _run("import_shrine_knowledge", str(path))

    assert f"SKIP removed shrine {KYUDEN[0]!r}" in out
    assert not ShrineDeity.objects.filter(shrine__name_jp=KYUDEN[0]).exists()
    assert not ShrineHistory.objects.filter(shrine__name_jp=KYUDEN[0]).exists()
