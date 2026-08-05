from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState

from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource

# Knowledge Model Foundation（PR #2221）が導入した3モデル。
KNOWLEDGE_MODEL_NAMES = {"ShrineKnowledgeSource", "ShrineHistory", "ShrineDeity"}

# Knowledge Model導入によって型/DB semantics/validation semanticsが変わってはならない
# 既存Shrineのlegacy fields。
LEGACY_SHRINE_FIELDS = ("sajin", "description")

# legacy fieldのfield定義差分として許容するkwargs。help_textはDB column/validationに
# 影響しないDjango側の表示用メタデータのみのため、変更を許容する。
_METADATA_ONLY_ALLOWED_KEYS = {"help_text"}

_MISSING = object()


def test_makemigrations_check_reports_no_pending_changes():
    """Model定義とMigrationが一致していること（Data Migrationやfield追加漏れがないこと）を確認する。"""
    out = io.StringIO()
    err = io.StringIO()
    try:
        call_command(
            "makemigrations",
            "temples",
            "--check",
            "--dry-run",
            stdout=out,
            stderr=err,
        )
    except SystemExit as exc:
        pytest.fail(
            "makemigrations --check reported pending model changes:\n"
            f"stdout={out.getvalue()}\nstderr={err.getvalue()}\nexit_code={exc.code}"
        )


@pytest.mark.django_db
def test_shrine_knowledge_tables_exist_after_migration():
    table_names = set(connection.introspection.table_names())
    assert ShrineDeity._meta.db_table in table_names
    assert ShrineHistory._meta.db_table in table_names
    assert ShrineKnowledgeSource._meta.db_table in table_names


def _find_knowledge_migrations(loader: MigrationLoader) -> set[tuple[str, str]]:
    """現在有効なtemples migration graph（GIS/NoGISいずれか）から、KNOWLEDGE_MODEL_NAMESの
    いずれかをCreateModelするmigrationを動的に特定する。migration番号はハードコードしない。"""
    migrations_by_created_model: dict[str, set[tuple[str, str]]] = {}
    for key, migration in loader.disk_migrations.items():
        if key[0] != "temples":
            continue
        for op in migration.operations:
            if type(op).__name__ == "CreateModel" and op.name in KNOWLEDGE_MODEL_NAMES:
                migrations_by_created_model.setdefault(op.name, set()).add(key)

    missing = KNOWLEDGE_MODEL_NAMES - set(migrations_by_created_model)
    assert not missing, f"CreateModelするmigrationが見つからないKnowledge Model: {missing}"

    knowledge_keys: set[tuple[str, str]] = set()
    for keys in migrations_by_created_model.values():
        knowledge_keys |= keys
    return knowledge_keys


def _project_state_before(loader: MigrationLoader, key: tuple[str, str]) -> ProjectState:
    """指定migration key適用前のProjectStateを、依存グラフを辿って再構築する。"""
    plan = loader.graph.forwards_plan(key)
    assert plan[-1] == key
    state = ProjectState()
    for ancestor_key in plan[:-1]:
        # preserve=False: 逐次mutateして良い（このループ内でのみ使う使い捨てstate）
        state = loader.disk_migrations[ancestor_key].mutate_state(state, preserve=False)
    return state


def _field_diff_keys(before: tuple, after: tuple) -> set[str] | None:
    """2つのfield.deconstruct()結果を比較する。field class・位置引数が異なる場合はNoneを返す
    （呼び出し側で無条件failとして扱う）。それ以外は、値が異なるkwargキーの集合を返す。"""
    _, path_before, args_before, kwargs_before = before
    _, path_after, args_after, kwargs_after = after
    if path_before != path_after or args_before != args_after:
        return None
    all_keys = set(kwargs_before) | set(kwargs_after)
    return {k for k in all_keys if kwargs_before.get(k, _MISSING) != kwargs_after.get(k, _MISSING)}


@pytest.mark.django_db
def test_shrine_knowledge_model_foundation_does_not_touch_legacy_shrine_fields():
    """Knowledge Model Foundation（ShrineDeity/ShrineHistory/ShrineKnowledgeSource追加）を導入した
    migrationが、既存Shrineのlegacy fields(sajin/description)の型・DB semantics・validation
    semanticsを変更していないことを保証する。

    GIS環境とNoGIS環境（catch-up migrationへ統合済み）とでmigration番号・構成が異なるため、
    migration番号をハードコードせず、CreateModelの対象からmigrationを動的に解決する。
    「対象migrationがCreateModelのみで構成される」ことは要求しない（NoGIS側のcatch-up
    migrationは他の変更も含む squashed migrationのため）。代わりに、migration適用前後の
    ProjectStateを比較し、legacy fieldの実際の定義差分を検証する。help_textのみの差分は
    （DB column/validationに影響しないDjango側の表示用メタデータのため）許容するが、
    field class・null・blank・default等の変更やfield自体の消失/リネームは許容しない。
    """
    loader = MigrationLoader(connection, ignore_no_migrations=True)
    knowledge_keys = _find_knowledge_migrations(loader)

    for key in knowledge_keys:
        migration = loader.disk_migrations[key]

        # Data Operationの安全性は静的には証明できないため、存在自体を禁止する。
        operation_types = {type(op).__name__ for op in migration.operations}
        forbidden_data_ops = operation_types & {"RunPython", "RunSQL"}
        assert not forbidden_data_ops, (
            f"{key}: Knowledge Model migrationにRunPython/RunSQLが含まれている。"
            f"legacy fieldsへの影響を安全に検証できないため許容しない: {forbidden_data_ops}"
        )

        state_before = _project_state_before(loader, key)
        shrine_before = state_before.models[("temples", "shrine")]

        state_after = migration.mutate_state(state_before, preserve=True)
        shrine_after = state_after.models[("temples", "shrine")]

        for field_name in LEGACY_SHRINE_FIELDS:
            try:
                field_before = shrine_before.get_field(field_name)
            except KeyError:
                pytest.fail(f"{key}: legacy field '{field_name}' がmigration適用前に存在しない")
            try:
                field_after = shrine_after.get_field(field_name)
            except KeyError:
                pytest.fail(
                    f"{key}: legacy field '{field_name}' がmigration適用後に消失している"
                    "（RemoveField/RenameField相当の変更）"
                )

            diff_keys = _field_diff_keys(field_before.deconstruct(), field_after.deconstruct())
            if diff_keys is None:
                pytest.fail(
                    f"{key}: legacy field '{field_name}' のfield classまたは位置引数が変更されている "
                    f"(before={field_before.deconstruct()}, after={field_after.deconstruct()})"
                )

            disallowed_diff = diff_keys - _METADATA_ONLY_ALLOWED_KEYS
            assert not disallowed_diff, (
                f"{key}: legacy field '{field_name}' に許容外の変更がある: {disallowed_diff} "
                f"(before={field_before.deconstruct()}, after={field_after.deconstruct()})"
            )
