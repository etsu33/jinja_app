"""Evidence Coverage Audit（PR-E1）の read-only command。

`docs/audit/shrine-recommendation-evidence-eligibility-audit-2026-11-01.md` §6 の分類を
現DBで観測する。計算は `temples.services.evidence_coverage_audit` に一本化している。

安全性:
- DB へ書き込まない。PostgreSQL では全クエリを `SET TRANSACTION READ ONLY` の
  transaction 内で実行し、書き込みは DB 側で拒否される。
- `--data-origin production-readonly` は `--confirm-read-only-production` が無いと実行しない。
  Production での実行は、読み取り専用の認証経路の明示承認を得た運用者だけが行う
  （手順: docs/runbooks/evidence-coverage-audit.md）。
- 相談文・Concierge thread / message・利用ログは読まない。
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from temples.management.commands.knowledge_coverage_report import _parse_scope_ids_file
from temples.services.evidence_coverage_audit import (
    CLASSES,
    DATA_ORIGIN_PRODUCTION_READONLY,
    DATA_ORIGINS,
    NEEDS,
    EvidenceCoverageInputError,
    build_evidence_coverage_report,
    compare_reports,
    parse_axis_conflicts,
)


def _read_json(path_str: str, flag: str):
    path = Path(path_str).expanduser()
    if not path.is_file():
        raise CommandError(f"{flag}: file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CommandError(f"{flag}: invalid JSON: {exc}") from exc


def render_text_report(report: dict) -> str:
    s = report["summary"]
    lines = [
        "Evidence Coverage Audit",
        "=" * 40,
        f"Schema Version: {report['schema_version']}",
        f"Data Origin: {report['data_origin']}",
        f"Read-only Guard: {report.get('execution', {}).get('read_only_guard', 'n/a')}",
        f"Scope: {report['scope']['mode']} "
        f"(requested={report['scope']['requested_count']}, resolved_in_db={report['scope']['resolved_in_db']})",
        "",
        f"Shrines: {s['shrine_count']}",
        f"Eligible now (current Shared Eligibility): {s['eligible_now']}",
        f"Base complete (D and H): {s['base_complete']}",
        "Classes: " + ", ".join(f"{c}={s['class_counts'][c]}" for c in CLASSES),
        f"Pillars: D={s['pillar_counts']['D']} H={s['pillar_counts']['H']} "
        f"C(any need)={s['pillar_counts']['C_any_need']}",
        f"Pillar conflicts: {s['pillar_conflict_shrines']}  "
        f"Axis conflicts: {s['axis_conflict_shrines']}  "
        f"Shrines with disputed facts: {s['disputed_fact_shrines']}",
        "Attributable fact epistemic types: "
        + ", ".join(f"{k}={v}" for k, v in s["attributable_fact_epistemic"].items()),
        "",
        "By Need (legacy_unattributed / ∩eligible / ∩base_complete / C / verified / conflicting):",
    ]
    for need in NEEDS:
        n = s["by_need"][need]
        lines.append(
            f"  {need}: {n['legacy_unattributed']} / {n['legacy_unattributed_and_eligible_now']} / "
            f"{n['legacy_unattributed_and_base_complete']} / {n['c_source_backed']} / "
            f"{n['verified']} / {n['conflicting']}"
        )
    lines.append("")
    lines.append(
        "By Prefecture (total / eligible_now / base_complete / " + " / ".join(CLASSES) + "):"
    )
    for pref, b in s["by_prefecture"].items():
        lines.append(
            f"  {pref}: {b['total']} / {b['eligible_now']} / {b['base_complete']} / "
            + " / ".join(str(b[c]) for c in CLASSES)
        )
    lines.append("")
    lines.append(
        "Note: legacy_unattributed = provenance not traceable (unverified); it does NOT mean false."
    )
    if "comparison" in report:
        cmp_ = report["comparison"]
        lines.append("")
        lines.append(f"Comparison with: {cmp_['other_data_origin']}")
        lines.append(f"  only_in_current: {len(cmp_['only_in_current'])}")
        lines.append(f"  only_in_other: {len(cmp_['only_in_other'])}")
        lines.append(f"  changed: {len(cmp_['changed'])}")
        lines.append(
            "  class_count_delta: "
            + ", ".join(f"{c}={cmp_['class_count_delta'][c]:+d}" for c in CLASSES)
        )
    return "\n".join(lines)


class Command(BaseCommand):
    help = (
        "Evidence Coverage（D / H / C(need)、VERIFIED / PARTIAL_A / PARTIAL_B / INSUFFICIENT）"
        "の read-only 監査レポート。DB 書き込みは一切行わない。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-origin",
            required=True,
            choices=DATA_ORIGINS,
            help="接続先DBの由来。repository seed から作ったローカルDBか Production（読み取り専用）か。",
        )
        parser.add_argument(
            "--confirm-read-only-production",
            action="store_true",
            help="--data-origin production-readonly のときに必須。読み取り専用経路の承認済みであることの確認。",
        )
        parser.add_argument("--format", choices=["text", "json"], default="text")
        parser.add_argument(
            "--scope-id", action="append", type=int, dest="scope_ids", metavar="SHRINE_ID"
        )
        parser.add_argument("--scope-ids-file", dest="scope_ids_file", metavar="PATH")
        parser.add_argument(
            "--axis-conflicts-file",
            metavar="PATH",
            help="review 済みの軸単位 CONFLICTING（JSON 配列: name_jp / address / need / basis）。",
        )
        parser.add_argument(
            "--compare-with",
            metavar="PATH",
            help="別環境で出力した JSON report。identity（name_jp + address）で差分を出す。",
        )
        parser.add_argument("--trace-per-class", type=int, default=1, metavar="N")
        parser.add_argument(
            "--trace-shrine-id", action="append", type=int, default=[], metavar="SHRINE_ID"
        )

    def handle(self, *args, **options):
        origin = options["data_origin"]
        if (
            origin == DATA_ORIGIN_PRODUCTION_READONLY
            and not options["confirm_read_only_production"]
        ):
            raise CommandError(
                "--data-origin production-readonly requires --confirm-read-only-production "
                "(run only through an explicitly authorized read-only path)."
            )
        if options["trace_per_class"] < 0:
            raise CommandError("--trace-per-class must be >= 0")

        cli_ids = options.get("scope_ids")
        scope_file = options.get("scope_ids_file")
        if cli_ids and scope_file:
            raise CommandError("--scope-id と --scope-ids-file は同時に指定できません。")
        shrine_ids = None
        if scope_file is not None:
            shrine_ids = _parse_scope_ids_file(scope_file)
        elif cli_ids is not None:
            shrine_ids = list(cli_ids)

        try:
            axis_conflicts = (
                parse_axis_conflicts(
                    _read_json(options["axis_conflicts_file"], "--axis-conflicts-file")
                )
                if options.get("axis_conflicts_file")
                else {}
            )
            other = (
                _read_json(options["compare_with"], "--compare-with")
                if options.get("compare_with")
                else None
            )

            # 読み取り専用 guard は最外側の transaction でだけ張る（入れ子の savepoint 内で
            # 張ると呼び出し側の transaction 全体を read-only にしてしまうため）。
            outermost = not connection.in_atomic_block
            with transaction.atomic():
                if connection.vendor != "postgresql":
                    guard = "not_applied_non_postgresql"
                elif not outermost:
                    guard = "not_applied_nested_transaction"
                else:
                    with connection.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                    guard = "postgresql_transaction_read_only"
                report = build_evidence_coverage_report(
                    data_origin=origin,
                    shrine_ids=shrine_ids,
                    axis_conflicts=axis_conflicts,
                    trace_per_class=options["trace_per_class"],
                    trace_shrine_ids=options["trace_shrine_id"],
                )
            report["execution"] = {"read_only_guard": guard}
            if other is not None:
                report["comparison"] = compare_reports(report, other)
        except EvidenceCoverageInputError as exc:
            raise CommandError(str(exc)) from exc

        if options["format"] == "json":
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            self.stdout.write(render_text_report(report))
