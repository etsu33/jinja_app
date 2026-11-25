# -*- coding: utf-8 -*-
"""import_shrines_seed：シードの空で本番の値を上書きしない契約。

2026-11-12、本番のブートストラップで Base Seed の取り込みが初めて実行され、
シードで goriyaku が空の4社の本番値を空文字で上書きした。その再発防止。

- 文字・数値・リストの項目：既存の神社を更新するとき、シードが空（None・空白だけ・空リスト）で
  本番に値がある項目は残し、`KEEP ... reason=seed_empty kept=[...]` を出す
- 新しく作る神社（CREATE）は今まで通り、シードの値（空を含む）で作る
- goriyaku_tags の `[]`：visit_style_tags と同じく書き間違いとして止める（key を省けば触らない）
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.management.commands.import_shrines_seed import _is_empty_value
from temples.models import Shrine

pytestmark = pytest.mark.django_db

NAME = "空上書きテスト神社"
ADDRESS = "東京都千代田区9-9"


def _write_seed(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


def _run(source: Path, *args: str) -> str:
    out = StringIO()
    call_command("import_shrines_seed", "--source", str(source), *args, stdout=out)
    return out.getvalue()


def _existing(**overrides) -> Shrine:
    values = dict(
        name_jp=NAME,
        address=ADDRESS,
        latitude=35.0,
        longitude=139.0,
        goriyaku="縁結び・厄除け",
        sajin="天照大御神",
        description="本番で書いた説明",
        name_romaji="Karitest Jinja",
        element="木",
        kyusei="一白水星",
        astro_elements=["火"],
    )
    values.update(overrides)
    return Shrine.objects.create(**values)


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, True),
        ("", True),
        ("   ", True),
        ([], True),
        ((), True),
        ("縁結び", False),
        (["火"], False),
        (0, False),
        (0.0, False),
        (False, False),
    ],
)
def test_is_empty_value(value, expected):
    assert _is_empty_value(value) is expected


def test_empty_seed_values_do_not_overwrite_existing_values(tmp_path):
    shrine = _existing()
    source = _write_seed(
        tmp_path,
        [
            {
                "name_jp": NAME,
                "address": ADDRESS,
                "latitude": 35.0,
                "longitude": 139.0,
                "goriyaku": "",
                "sajin": "   ",
                "description": None,
                "astro_elements": [],
                # name_romaji / element / kyusei は key ごと無い
            }
        ],
    )

    output = _run(source)

    shrine.refresh_from_db()
    assert shrine.goriyaku == "縁結び・厄除け"
    assert shrine.sajin == "天照大御神"
    assert shrine.description == "本番で書いた説明"
    assert shrine.astro_elements == ["火"]
    assert shrine.name_romaji == "Karitest Jinja"
    assert shrine.element == "木"
    assert shrine.kyusei == "一白水星"

    keep = [ln for ln in output.splitlines() if ln.startswith("KEEP ")]
    assert len(keep) == 1
    assert "reason=seed_empty" in keep[0]
    for field in ["goriyaku", "sajin", "description", "astro_elements", "name_romaji", "element", "kyusei"]:
        assert f"'{field}'" in keep[0], field
    assert "kept_existing shrines=1 field_count=7" in output
    # 何も書き換えていないので UPDATE ではなく SKIP
    assert "done created=0 updated=0 skipped=1 total_seed=1" in output


def test_non_empty_seed_values_still_update(tmp_path):
    shrine = _existing()
    source = _write_seed(
        tmp_path,
        [
            {
                "name_jp": NAME,
                "address": ADDRESS,
                "latitude": 35.0,
                "longitude": 139.0,
                "goriyaku": "商売繁盛",
                "sajin": "",
            }
        ],
    )

    output = _run(source)

    shrine.refresh_from_db()
    assert shrine.goriyaku == "商売繁盛"
    assert shrine.sajin == "天照大御神"
    assert "fields=['goriyaku']" in output
    assert "done created=0 updated=1 skipped=0 total_seed=1" in output


def test_empty_seed_over_empty_db_is_not_reported_as_keep(tmp_path):
    _existing(goriyaku="", sajin="")
    source = _write_seed(
        tmp_path,
        [{"name_jp": NAME, "address": ADDRESS, "latitude": 35.0, "longitude": 139.0, "goriyaku": "", "sajin": ""}],
    )

    output = _run(source)

    keep = [ln for ln in output.splitlines() if ln.startswith("KEEP ")]
    assert all("'goriyaku'" not in ln and "'sajin'" not in ln for ln in keep)


def test_missing_coordinates_in_seed_keep_existing_coordinates(tmp_path):
    shrine = _existing()
    source = _write_seed(
        tmp_path,
        [{"name_jp": NAME, "address": ADDRESS, "latitude": None, "longitude": None, "goriyaku": "縁結び・厄除け"}],
    )

    _run(source)

    shrine.refresh_from_db()
    assert shrine.latitude == 35.0
    assert shrine.longitude == 139.0


def test_create_still_uses_seed_values_including_empty(tmp_path):
    source = _write_seed(
        tmp_path,
        [{"name_jp": NAME, "address": ADDRESS, "latitude": 35.0, "longitude": 139.0, "goriyaku": ""}],
    )

    output = _run(source)

    shrine = Shrine.objects.get(name_jp=NAME, address=ADDRESS)
    assert shrine.goriyaku == ""
    assert "CREATE " in output
    assert "KEEP " not in output


def test_dry_run_reports_keep_without_writing(tmp_path):
    shrine = _existing()
    source = _write_seed(
        tmp_path,
        [{"name_jp": NAME, "address": ADDRESS, "latitude": 35.0, "longitude": 139.0, "goriyaku": ""}],
    )

    output = _run(source, "--dry-run")

    shrine.refresh_from_db()
    assert shrine.goriyaku == "縁結び・厄除け"
    assert "KEEP " in output


def test_empty_goriyaku_tags_list_is_rejected_before_any_write(tmp_path):
    shrine = _existing()
    source = _write_seed(
        tmp_path,
        [
            {
                "name_jp": NAME,
                "address": ADDRESS,
                "latitude": 35.0,
                "longitude": 139.0,
                "goriyaku": "商売繁盛",
                "goriyaku_tags": [],
            }
        ],
    )

    with pytest.raises(CommandError, match="goriyaku_tags must not be empty"):
        _run(source)

    shrine.refresh_from_db()
    assert shrine.goriyaku == "縁結び・厄除け"
