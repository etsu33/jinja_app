"""Knowledge Coverageのread-only集計command。

Knowledge Pilot / Rollout Batch 1 / Batch 2で繰り返し手動実行してきた
Coverage集計クエリ（`docs/audit/shrine-knowledge-rollout-batch-2.md`
§O「同種の集計クエリを今回で通算7回目程度手動実行」参照）を置き換える。

DBへの書き込みは一切行わない。Recommendation Score / Candidate / Ranking /
Evidence Gate contract / Reason V4のいずれも変更しない。
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from temples.services.knowledge_coverage_report import build_knowledge_coverage_report


def _format_count(entry: dict) -> str:
    return f"{entry['count']} ({entry['percentage']}%)"


def render_text_report(report: dict) -> str:
    lines: list[str] = []
    lines.append("Knowledge Coverage Report")
    lines.append("=" * 40)
    lines.append(f"Total DB Shrines: {report['total_db_shrines']}")
    lines.append(f"Audit Target Shrines: {report['audit_target_shrines']}")
    lines.append(f"Excluded Test Shrines: {report['excluded_test_shrines']}")
    lines.append("")
    lines.append(f"Knowledge Coverage: {_format_count(report['knowledge_coverage'])}")
    lines.append(f"Zero Knowledge: {_format_count(report['zero_knowledge'])}")
    lines.append(f"Deity Coverage: {_format_count(report['deity_coverage'])}")
    lines.append(f"History Coverage: {_format_count(report['history_coverage'])}")
    lines.append(f"Source Coverage: {_format_count(report['source_coverage'])}")
    lines.append(
        f"Both Deity and History Coverage: "
        f"{_format_count(report['both_deity_and_history_coverage'])}"
    )
    lines.append("")
    fact_ready = report["fact_ready_coverage"]
    lines.append("Fact-ready Coverage:")
    lines.append(f"  Deity: {_format_count(fact_ready['fact_ready_deity_shrines'])}")
    lines.append(f"  History: {_format_count(fact_ready['fact_ready_history_shrines'])}")
    lines.append(f"  Any: {_format_count(fact_ready['fact_ready_any_shrines'])}")
    lines.append("")
    lines.append(f"Verified Source Count: {report['verified_source_count']}")
    lines.append(f"Total Source Count: {report['total_source_count']}")
    lines.append("")
    lines.append(f"Deity Count Distribution: {report['deity_count_distribution']}")
    lines.append(f"History Count Distribution: {report['history_count_distribution']}")
    lines.append(f"Source Count Distribution: {report['source_count_distribution']}")
    lines.append(
        f"Verification Status Distribution: {report['verification_status_distribution']}"
    )
    lines.append(f"Confidence Distribution: {report['confidence_distribution']}")
    lines.append(f"Source Type Distribution: {report['source_type_distribution']}")
    return "\n".join(lines)


class Command(BaseCommand):
    help = (
        "Knowledge Coverageのread-only集計レポートを表示する。"
        "DB書き込みは一切行わない。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="出力形式。text（既定、人間可読）またはjson。",
        )

    def handle(self, *args, **options):
        report = build_knowledge_coverage_report()
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            self.stdout.write(render_text_report(report))
