"""未適用のマイグレーションがあるかを、ログに出すだけのコマンド（読むだけ。実行はしない）。

backend/start.sh が起動のたびに呼ぶ。起動時のマイグレーションの実行は
RUN_MIGRATIONS_ON_START=1 のときだけで、この方針は変えない。実行忘れに気づくためのもの。

出す行（ログで検索しやすいよう、すべて [migration-check] で始める）:
- 未適用がある:   [migration-check] UNAPPLIED MIGRATIONS count=<n> ...
                  [migration-check] UNAPPLIED <app>.<name>   （1件ずつ）
- 未適用が無い:   [migration-check] OK all migrations applied
- 確かめられない: [migration-check] CHECK FAILED error_type=<型> ...

どの場合も終了コードは 0（起動を止めない）。
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor

PREFIX = "[migration-check]"


def find_unapplied_migrations(database: str = DEFAULT_DB_ALIAS) -> list[str]:
    """未適用のマイグレーションの名前（<app>.<name>）を、適用する順に返す。"""
    executor = MigrationExecutor(connections[database])
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    return [f"{migration.app_label}.{migration.name}" for migration, backwards in plan if not backwards]


class Command(BaseCommand):
    help = "Log unapplied migrations without applying them (read-only, always exits 0)."

    def handle(self, *args, **options):
        try:
            unapplied = find_unapplied_migrations()
        except Exception as exc:  # noqa: BLE001 - 起動を止めないため、どの失敗も警告だけにする
            self.stdout.write(f"{PREFIX} CHECK FAILED error_type={type(exc).__name__}; startup continues")
            return

        if not unapplied:
            self.stdout.write(f"{PREFIX} OK all migrations applied")
            return

        self.stdout.write(
            f"{PREFIX} UNAPPLIED MIGRATIONS count={len(unapplied)}. "
            "Run 'python manage.py migrate' in the Render Shell."
        )
        for name in unapplied:
            self.stdout.write(f"{PREFIX} UNAPPLIED {name}")
