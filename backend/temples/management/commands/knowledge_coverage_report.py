"""Knowledge Coverageのread-only集計command。

Knowledge Pilot / Rollout Batch 1 / Batch 2で繰り返し手動実行してきた
Coverage集計クエリ（`docs/audit/shrine-knowledge-rollout-batch-2.md`
§O「同種の集計クエリを今回で通算7回目程度手動実行」参照）を置き換える。

DBへの書き込みは一切行わない。Recommendation Score / Candidate / Ranking /
Evidence Gate contract / Reason V4のいずれも変更しない。

母集団選択と集計の分離（P9,
`docs/audit/knowledge-coverage-canonical-scope-fix.md`）: 既定では従来どおり
QA fixture除外後の全DB行を対象にするが、`--scope-id` / `--scope-ids-file` で
明示スコープ（例: PR #2614 の canonical 103-identity 集合）を渡すと、その
スコープちょうどで集計する。canonical identity の自動判定は現モデルに
永続マーカーが無いため行わない（scope は呼び出し側が明示指定する）。
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from temples.services.knowledge_coverage_report import build_knowledge_coverage_report


def _format_count(entry: dict) -> str:
    return f"{entry['count']} ({entry['percentage']}%)"


def _parse_scope_ids_file(path_str: str) -> list[int]:
    """スコープidファイルを読む。

    受理する形式:
      - JSON 配列（例: ``[1, 2, 3]``）
      - 1行1id。空行と ``#`` から始まる行は無視。

    ファイルが存在するが有効idが0件 → 空の明示スコープ（0社監査）として扱う。
    ファイルが存在しない → 呼び出し側に誤りを気づかせるため CommandError。
    """
    path = Path(path_str).expanduser()
    if not path.is_file():
        raise CommandError(f"--scope-ids-file: file not found: {path}")
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise CommandError(f"--scope-ids-file: invalid JSON array: {exc}") from exc
        if not isinstance(data, list):
            raise CommandError("--scope-ids-file: JSON must be an array of integers")
        try:
            return [int(x) for x in data]
        except (TypeError, ValueError) as exc:
            raise CommandError(f"--scope-ids-file: non-integer id in JSON array: {exc}") from exc
    ids: list[int] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            ids.append(int(line))
        except ValueError as exc:
            raise CommandError(
                f"--scope-ids-file: line {lineno}: not an integer: {line!r}"
            ) from exc
    return ids


def render_text_report(report: dict) -> str:
    scope = report.get("scope", {})
    lines: list[str] = []
    lines.append("Knowledge Coverage Report")
    lines.append("=" * 40)
    lines.append(
        f"Coverage Scope: {scope.get('mode', 'qa_filtered_db')} "
        f"({scope.get('count', report['audit_target_shrines'])} shrines; "
        f"resolved_in_db={scope.get('resolved_in_db', '?')})"
    )
    if scope.get("note"):
        lines.append(f"  {scope['note']}")
    lines.append(f"Total DB Shrines: {report['total_db_shrines']}")
    lines.append(
        f"Audit Target Shrines: {report['audit_target_shrines']} "
        f"[= Coverage Scope count; mode={scope.get('mode', 'qa_filtered_db')} — "
        f"NOT necessarily the canonical unique-real-shrine denominator]"
    )
    lines.append(
        f"Excluded Test Shrines: {report['excluded_test_shrines']} "
        f"(QA/test fixture exclusion count over ALL DB rows — "
        f"exclude_qa_fixture_shrines; NOT 'rows outside the reporting scope')"
    )
    lines.append(
        f"Rows Outside Reporting Scope: {scope.get('outside_scope_count', '?')} "
        f"(total_db_shrines - Coverage Scope count)"
    )
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
        "--scope-id / --scope-ids-file で明示スコープ（例: canonical 103社）を指定可能。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="出力形式。text（既定、人間可読）またはjson。",
        )
        parser.add_argument(
            "--scope-id",
            action="append",
            type=int,
            dest="scope_ids",
            metavar="SHRINE_ID",
            help=(
                "明示スコープに含める Shrine id（繰り返し指定可）。"
                "指定した場合、既定のQA fixtureスコープではなくこのidちょうどで集計する。"
            ),
        )
        parser.add_argument(
            "--scope-ids-file",
            dest="scope_ids_file",
            metavar="PATH",
            help=(
                "明示スコープの Shrine id を読むファイル（1行1id、# コメント可、"
                "または JSON 配列）。--scope-id とは排他。"
            ),
        )

    def handle(self, *args, **options):
        cli_ids = options.get("scope_ids")
        scope_file = options.get("scope_ids_file")
        if cli_ids and scope_file:
            raise CommandError("--scope-id と --scope-ids-file は同時に指定できません。")

        # None → 既定スコープ。list（空可）→ 明示スコープ。
        shrine_ids = None
        if scope_file is not None:
            shrine_ids = _parse_scope_ids_file(scope_file)
        elif cli_ids is not None:
            shrine_ids = list(cli_ids)

        report = build_knowledge_coverage_report(shrine_ids=shrine_ids)
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            self.stdout.write(render_text_report(report))
