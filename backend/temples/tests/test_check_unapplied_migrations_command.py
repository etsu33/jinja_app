"""起動時の「未適用のマイグレーション」の確認コマンド（読むだけ。実行はしない）。"""

from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from temples.management.commands import check_unapplied_migrations as command_module


def _run() -> str:
    out = StringIO()
    call_command("check_unapplied_migrations", stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_all_applied_prints_one_ok_line():
    output = _run()

    assert output.strip().splitlines() == ["[migration-check] OK all migrations applied"]


@pytest.mark.django_db
def test_unapplied_migrations_are_listed_by_name(monkeypatch):
    plan = [
        (SimpleNamespace(app_label="users", name="0010_premium_pass_purchase"), False),
        (SimpleNamespace(app_label="temples", name="0122_example"), False),
        (SimpleNamespace(app_label="temples", name="0121_rollback"), True),
    ]
    monkeypatch.setattr(command_module.MigrationExecutor, "migration_plan", lambda self, targets: plan)

    lines = _run().strip().splitlines()

    assert lines[0].startswith("[migration-check] UNAPPLIED MIGRATIONS count=2.")
    assert lines[1:] == [
        "[migration-check] UNAPPLIED users.0010_premium_pass_purchase",
        "[migration-check] UNAPPLIED temples.0122_example",
    ]


@pytest.mark.django_db
def test_check_failure_is_logged_and_does_not_raise(monkeypatch):
    def boom(self, targets):
        raise RuntimeError("db down")

    monkeypatch.setattr(command_module.MigrationExecutor, "migration_plan", boom)

    output = _run()

    assert output.strip() == "[migration-check] CHECK FAILED error_type=RuntimeError; startup continues"


def test_start_sh_runs_the_check_without_blocking_startup():
    from pathlib import Path

    start_sh = (Path(__file__).resolve().parents[2] / "start.sh").read_text(encoding="utf-8")

    assert "python manage.py check_unapplied_migrations" in start_sh
    assert '} || echo "[migration-check] CHECK FAILED (command error); startup continues"' in start_sh
    # 起動時のマイグレーションの実行は、今までどおり RUN_MIGRATIONS_ON_START=1 のときだけ。
    assert start_sh.count("python manage.py migrate --noinput") == 1
