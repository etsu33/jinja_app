# backend/temples/tests/test_queries_gis_import_guard.py
#
# temples/queries.py は import 時点で GDAL を要求してはいけない
# (USE_GIS=False の環境で `python manage.py makemigrations --check` や
# urlconf のロードが GDAL 未導入のまま落ちていた実障害の再発防止)。
import ast
import inspect

import pytest
from django.db import connection

from temples import queries as queries_module
from temples.models import Shrine
from temples.queries import nearest_queryset, nearest_shrines

GIS_MODULE_PREFIX = "django.contrib.gis"


def _module_ast() -> ast.Module:
    source = inspect.getsource(queries_module)
    return ast.parse(source, filename=queries_module.__file__)


def test_queries_module_has_no_top_level_gis_import():
    """temples.queries を import するだけでは GDAL を要求しない。"""
    tree = _module_ast()
    top_level_gis_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith(GIS_MODULE_PREFIX)
    ]
    assert top_level_gis_imports == []


def test_gis_symbols_are_locally_imported_inside_real_gis_branches():
    """Distance/Transform/Point は _use_real_gis() で分岐した関数内でのみ import される
    （GIS有効時の挙動は維持しつつ、import自体は遅延させていることを保証する）。"""
    tree = _module_ast()
    function_defs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert {f.name for f in function_defs} >= {"nearest_queryset", "nearest_shrines"}

    for func in function_defs:
        if func.name not in {"nearest_queryset", "nearest_shrines"}:
            continue
        local_gis_imports = [
            node
            for node in ast.walk(func)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith(GIS_MODULE_PREFIX)
        ]
        imported_names = {alias.name for node in local_gis_imports for alias in node.names}
        assert {"Distance", "Transform", "Point"} <= imported_names, func.name


@pytest.mark.django_db
def test_non_gis_path_works_when_real_gis_is_disabled(settings):
    """USE_GIS=False（DISABLE_GIS_FOR_TESTS相当）でも nearest_queryset/nearest_shrines は
    Postgres非GIS(haversine)経路で正しく動く。"""
    settings.USE_GIS = False
    assert queries_module._use_real_gis() is False
    assert connection.vendor == "postgresql"

    shrine = Shrine.objects.create(
        name_jp="Non-GIS経路テスト神社",
        address="dummy",
        latitude=35.0,
        longitude=135.0,
    )

    qs = nearest_queryset(135.0, 35.0)
    by_id = {row.id: row for row in qs}
    assert shrine.id in by_id
    assert float(by_id[shrine.id].d_m) < 1

    limited = nearest_shrines(135.0, 35.0, limit=1)
    assert list(limited.values_list("id", flat=True)) == [shrine.id]
