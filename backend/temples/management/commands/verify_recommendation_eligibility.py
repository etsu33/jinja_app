"""Shared Recommendation Eligibilityのread-only検証command。

W0-DB01 CORE READY Gateで手動実行したper-shrine eligibility確認を、再利用可能
かつ決定的な形へ置き換える。DBへの書き込み（create / update / delete /
migration / status遷移）は一切行わない。

eligibility ruleとEvidence Gate条件は本commandで定義せず、既存authorityへ
委譲する（`temples.services.recommendation_eligibility_verifier`参照）。

使用例:

    # Data Build Batch単位（Candidate Masterのbuild_batchで解決）
    python manage.py verify_recommendation_eligibility --batch W0-DB01

    # Shrine id指定
    python manage.py verify_recommendation_eligibility --shrine-id 12 --shrine-id 34

    # Shrine名指定
    python manage.py verify_recommendation_eligibility --shrine-name 三輪神社

    # JSON出力（Batch QA記録へ貼り付ける用途）
    python manage.py verify_recommendation_eligibility --batch W0-DB01 --json

`--require-all-eligible` を付けると、ELIGIBLE以外が1件でもあれば非0で終了する
（CI / Gate用途）。既定では終了コードを立てず、観測結果の出力のみを行う。
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from temples.services.recommendation_eligibility_verifier import (
    load_batch_shrine_names,
    render_text_report,
    verify_recommendation_eligibility,
)


class Command(BaseCommand):
    help = (
        "Shared Recommendation Eligibilityをread-onlyで検証し、Shrineごとに "
        "ELIGIBLE / INELIGIBLE と最小限のEvidence件数を出力する（DB書き込みなし）。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch",
            dest="batch",
            help="Candidate Masterのbuild_batch（例: W0-DB01）で対象Shrineを解決する",
        )
        parser.add_argument(
            "--shrine-id",
            dest="shrine_ids",
            action="append",
            type=int,
            default=[],
            help="対象Shrine id（複数指定可）",
        )
        parser.add_argument(
            "--shrine-name",
            dest="shrine_names",
            action="append",
            default=[],
            help="対象Shrineのname_jp（複数指定可）",
        )
        parser.add_argument(
            "--json",
            dest="as_json",
            action="store_true",
            help="JSONで出力する",
        )
        parser.add_argument(
            "--require-all-eligible",
            dest="require_all_eligible",
            action="store_true",
            help="ELIGIBLE以外が1件でもあれば非0終了する（Gate用途）",
        )

    def handle(self, *args, **options):
        batch = options.get("batch")
        shrine_ids = list(options.get("shrine_ids") or [])
        shrine_names = list(options.get("shrine_names") or [])

        if batch:
            try:
                batch_names = load_batch_shrine_names(batch)
            except (FileNotFoundError, ValueError) as exc:
                raise CommandError(str(exc)) from exc
            if not batch_names:
                raise CommandError(f"--batch: no candidates found for build_batch={batch}")
            shrine_names.extend(batch_names)

        if not shrine_ids and not shrine_names:
            raise CommandError(
                "対象を指定してください（--batch / --shrine-id / --shrine-name のいずれか）"
            )

        report = verify_recommendation_eligibility(
            shrine_ids=shrine_ids,
            shrine_names=shrine_names,
        )

        if options.get("as_json"):
            self.stdout.write(
                json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            )
        else:
            self.stdout.write(render_text_report(report))

        if options.get("require_all_eligible") and not report.all_eligible:
            raise CommandError(
                "ALL_ELIGIBLE=FAIL: "
                f"ELIGIBLE={report.eligible_count} "
                f"INELIGIBLE={report.ineligible_count} "
                f"UNRESOLVED={report.unresolved_count}"
            )
