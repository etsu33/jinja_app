"""Collective Runtime Activation seed を明示・冪等・all-or-nothing で適用する（A6-00b）。

Usage:
    python manage.py activate_collective_runtime <seed.json> --validate-only
    python manage.py activate_collective_runtime <seed.json> --dry-run
    python manage.py activate_collective_runtime <seed.json>

--validate-only: JSON / schema / entry 構造 / seed 内重複の検証と、
    shrine_ref -> Shrine -> ShrineDeityCollective の厳密解決（読み取りのみ）。DB write なし。
--dry-run: validate-only の内容に加え、各 entry を CREATE / SKIP_EXISTS に分類した
    正確な apply plan を出力する。DB write なし。
(no flag): 1つの transaction.atomic() 内で解決・plan を再計算し、CREATE の
    CollectiveRuntimeActivation row だけを作る。既存 row は更新・再作成しない。

どの mode でも error が1件でもあれば全体を中断し、非 0 終了する（部分 activation なし）。
Activation は rollout 承認にすぎず、Runtime admission 判定（A6-01）は行わない。
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction
from temples.services.collective_runtime_activation_seed import (
    ACTION_CREATE,
    ACTION_SKIP_EXISTS,
    ActivationPlan,
    apply_activation_plan,
    build_activation_plan,
    parse_activation_seed,
    resolve_activation_targets,
)


class Command(BaseCommand):
    help = (
        "Validate / dry-run / apply a Collective Runtime Activation seed "
        "(creates CollectiveRuntimeActivation rows only)."
    )

    def add_arguments(self, parser):
        parser.add_argument("seed_path", type=str)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--validate-only",
            action="store_true",
            help="Structural validation + Shrine/Collective resolution only. No DB writes.",
        )
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute the exact CREATE / SKIP_EXISTS plan. No DB writes.",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["seed_path"])
        if not seed_path.exists():
            raise CommandError(f"seed file not found: {seed_path}")
        try:
            raw = json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"seed file is not valid JSON: {exc}") from exc

        parsed = parse_activation_seed(raw)
        if parsed.errors:
            self._report_errors(parsed.errors)
            raise CommandError(f"seed validation failed with {len(parsed.errors)} error(s)")

        if options["validate_only"]:
            targets, errors = resolve_activation_targets(parsed.entries)
            self._fail_on(errors, "validation failed")
            for target in targets:
                self.stdout.write(f"[activation] RESOLVED {target.entry.display}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"validate-only: OK, {len(targets)} Collective(s) resolved, no DB writes"
                )
            )
            return

        if options["dry_run"]:
            targets, errors = resolve_activation_targets(parsed.entries)
            self._fail_on(errors, "activation blocked")
            self._report_plan(build_activation_plan(targets))
            self.stdout.write(self.style.SUCCESS("dry-run: OK, no DB writes performed"))
            return

        try:
            with transaction.atomic():
                targets, errors = resolve_activation_targets(parsed.entries)
                self._fail_on(errors, "activation blocked")
                plan = build_activation_plan(targets)
                self._report_plan(plan)
                created = apply_activation_plan(plan)
                expected = plan.counts[ACTION_CREATE]
                if created != expected:
                    raise CommandError(
                        f"created={created} differs from planned CREATE={expected}; rolled back"
                    )
        except DatabaseError as exc:
            raise CommandError(f"database write failed; rolled back: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"activation complete: created={created}, "
                f"skipped={plan.counts[ACTION_SKIP_EXISTS]}"
            )
        )

    def _fail_on(self, errors: list[str], message: str) -> None:
        if errors:
            self._report_errors(errors)
            raise CommandError(f"{message}: {len(errors)} error(s), see above")

    def _report_errors(self, errors: list[str]) -> None:
        for err in errors:
            self.stderr.write(self.style.ERROR(f"ERROR: {err}"))

    def _report_plan(self, plan: ActivationPlan) -> None:
        for item in plan.items:
            self.stdout.write(f"[activation] {item.action} {item.entry.display}")
        counts = plan.counts
        self.stdout.write(
            self.style.SUCCESS(
                f"plan summary: {ACTION_CREATE}={counts[ACTION_CREATE]} "
                f"{ACTION_SKIP_EXISTS}={counts[ACTION_SKIP_EXISTS]}"
            )
        )
