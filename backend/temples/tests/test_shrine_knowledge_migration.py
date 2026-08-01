from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.db import connection

from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource


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


@pytest.mark.django_db
def test_shrine_knowledge_migration_does_not_touch_legacy_shrine_fields():
    """Migration 0093はCreateModelのみで、既存Shrine.sajin/descriptionへのField変更・Data Migrationを含まない。"""
    from django.db.migrations.loader import MigrationLoader

    loader = MigrationLoader(connection, ignore_no_migrations=True)
    key = ("temples", "0093_shrine_knowledge_model_foundation")
    migration = loader.disk_migrations[key]

    operation_types = {type(op).__name__ for op in migration.operations}
    assert operation_types == {"CreateModel"}

    affected_models = {op.name for op in migration.operations}
    assert affected_models == {"ShrineKnowledgeSource", "ShrineHistory", "ShrineDeity"}
