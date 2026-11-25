# backend/temples/management/commands/purge_expired_guest_data.py
"""匿名Ownerに紐づく永続データを保持期限（既定90日）で削除する。

既定は dry-run。実際に削除するには `--execute` を明示する。
これは「うっかり本番で消える」経路を作らないための既定値であり、
利便性のために反転させないこと。

自動実行はしない:
    このcommandは startup でも app ready でも呼ばれない。
    定期実行の方式（cron / scheduler / 手動）は別Gateで決める。

出力:
    件数と cutoff だけを出す。anonymous_id / query本文 / lat / lng /
    message本文 / email などの PII は出力しない。
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from temples.services.guest_data_retention import (
    DEFAULT_RETENTION_DAYS,
    run_guest_data_retention,
)

MODEL_ORDER = (
    "ConciergeThread",
    "ConciergeMessage",
    "ConciergeRecommendationLog",
    "FeatureUsage",
    "WeeklyPresentationSnapshot",
)


class Command(BaseCommand):
    help = (
        "Purge anonymous guest data older than the retention window "
        "(default: 90 days). Dry-run unless --execute is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=DEFAULT_RETENTION_DAYS,
            help=(
                f"Retention window in days (default: {DEFAULT_RETENTION_DAYS}). "
                "Production is not expected to run with any other value."
            ),
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete. Without this flag the command only reports counts.",
        )

    def handle(self, *args, **opts):
        days = opts["days"]
        execute = opts["execute"]

        if days < 1:
            raise CommandError("--days must be 1 or greater.")

        report = run_guest_data_retention(days=days, execute=execute)

        mode = "EXECUTE" if report.executed else "DRY-RUN"
        self.stdout.write(f"[guest-retention] mode={mode} days={report.days}")
        self.stdout.write(f"[guest-retention] cutoff={report.cutoff.isoformat()}")

        label = "deleted" if report.executed else "matched"
        for model_name in MODEL_ORDER:
            self.stdout.write(
                f"[guest-retention] {model_name}: {label}={report.counts.get(model_name, 0)}"
            )

        summary = f"[guest-retention] total {label}={report.total}"
        if report.executed:
            self.stdout.write(self.style.SUCCESS(summary))
        else:
            self.stdout.write(summary)
            self.stdout.write(
                "[guest-retention] dry-run: no rows were modified. "
                "Re-run with --execute to delete."
            )
