"""Knowledge推薦理由 品質Baseline計測のread-only CLI。

DBへの書き込みは一切行わない。Recommendation Runtime（chat POST等）は呼び出さず、
Django ORMのSELECTのみでBaselineを算出する。Production write禁止・
thread/message write禁止・Analytics送信禁止（temples.services.
recommendation_quality_measurementのdocstring参照）。
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from temples.services.recommendation_quality_measurement import (
    build_recommendation_quality_measurement_report,
)


def render_text_report(report: dict) -> str:
    lines: list[str] = []
    lines.append("Knowledge Recommendation Quality Baseline")
    lines.append("=" * 42)
    lines.append(f"Sample Count: {report['sample_count']}")
    lines.append("")
    lines.append(
        f"Fully Knowledge-backed: {report['fully_knowledge_backed']} "
        f"({report['fully_knowledge_backed_rate']:.2%})"
    )
    lines.append(
        f"Partially Knowledge-backed: {report['partially_knowledge_backed']} "
        f"({report['partially_knowledge_backed_rate']:.2%})"
    )
    lines.append(
        f"Legacy-backed: {report['legacy_backed']} ({report['legacy_backed_rate']:.2%})"
    )
    lines.append(f"Unknown: {report['unknown']} ({report['unknown_rate']:.2%})")
    lines.append("")
    lines.append(f"Knowledge-backed rate (Fully+Partially): {report['knowledge_backed_rate']:.2%}")
    lines.append(f"Deity Knowledge usage rate: {report['deity_knowledge_usage_rate']:.2%}")
    lines.append(f"History Knowledge usage rate: {report['history_knowledge_usage_rate']:.2%}")
    lines.append(f"Deity Legacy fallback rate: {report['deity_legacy_fallback_rate']:.2%}")
    lines.append(f"History Legacy fallback rate: {report['history_legacy_fallback_rate']:.2%}")
    lines.append("")
    sc = report["source_confirmed_fact"]
    lines.append(
        f"Source-confirmed Fact rate: {sc['source_confirmed_count']}/"
        f"{sc['fact_ready_total']} ({sc['source_confirmed_fact_rate']:.2%})"
    )
    lines.append(f"Verification Status Distribution: {sc['verification_status_distribution']}")
    return "\n".join(lines)


class Command(BaseCommand):
    help = (
        "Knowledge推薦理由の品質Baselineをread-only計測して表示する。"
        "DB書き込み・Recommendation Runtime呼び出しは一切行わない。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="出力形式。text（既定、人間可読）またはjson。",
        )
        parser.add_argument(
            "--shrine-ids",
            type=str,
            default=None,
            help="カンマ区切りのshrine id一覧。未指定時はQA fixtureを除外した全Shrineが対象。",
        )
        parser.add_argument(
            "--no-detail",
            action="store_true",
            help="classification_by_shrine（神社別内訳）をjson出力から省略する。",
        )

    def handle(self, *args, **options):
        shrine_ids = None
        if options["shrine_ids"]:
            shrine_ids = [int(x) for x in options["shrine_ids"].split(",") if x.strip()]

        report = build_recommendation_quality_measurement_report(shrine_ids=shrine_ids)

        if options["format"] == "json":
            if options["no_detail"]:
                report = {k: v for k, v in report.items() if k != "classification_by_shrine"}
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            self.stdout.write(render_text_report(report))
