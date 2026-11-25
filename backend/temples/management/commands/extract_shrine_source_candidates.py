"""凍結 Source snapshot から Shrine Source Candidate を read-only で抽出する command。

正本: docs/audit/shrine-source-candidate-extraction-contract.md

    python manage.py extract_shrine_source_candidates \\
        --adapter niigata-batch-001 \\
        --input /path/to/niigata_batch_001_snapshot.json \\
        [--output /path/to/artifact.json] \\
        [--verify-reproducibility]

- Source の取得はしない（--input は外部で凍結した snapshot）。
- DB へは書き込まない（SELECT 以外の SQL が出たら FAIL で止める）。
- artifact file は --output を指定したときだけ書く。
- 停止（STOP_*）は非0で終了する。行単位の INVALID / REVIEW_REQUIRED は停止ではない。
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from temples.services.shrine_source_candidate_extraction import (
    STOP_INPUT,
    CandidateExtractionStop,
    run_extraction,
    run_with_reproducibility_check,
)
from temples.services.shrine_source_candidate_niigata import parse_niigata_batch_001_snapshot

ADAPTERS = {
    "niigata-batch-001": parse_niigata_batch_001_snapshot,
}


def render_artifact(artifact: dict) -> str:
    """決定的な JSON 表現（key 順固定・raw の日本語はそのまま）。"""
    return json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


class Command(BaseCommand):
    help = (
        "凍結した Source snapshot を READY_CANDIDATE / REVIEW_REQUIRED / INVALID に分類する"
        "（read-only。DB 書き込みなし）。"
    )

    def add_arguments(self, parser):
        parser.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
        parser.add_argument("--input", required=True, help="凍結 Source snapshot（JSON）")
        parser.add_argument("--output", help="artifact JSON の出力先（指定時のみ書き込む）")
        parser.add_argument(
            "--verify-reproducibility",
            action="store_true",
            help="同じ snapshot / DB 状態で2回実行し、決定的 field を比較する",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        try:
            data = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"{STOP_INPUT}: cannot read snapshot: {exc}") from exc

        try:
            contract, meta, raws = ADAPTERS[options["adapter"]](data)
            if options["verify_reproducibility"]:
                artifact, _ = run_with_reproducibility_check(contract, meta, raws)
                reproducibility = "PASS"
            else:
                artifact = run_extraction(contract, meta, raws)
                reproducibility = "NOT_RUN"
        except CandidateExtractionStop as exc:
            raise CommandError(str(exc)) from exc

        if options["output"]:
            Path(options["output"]).write_text(render_artifact(artifact), encoding="utf-8")

        summary = artifact["summary"]
        self.stdout.write(
            "batch_id={batch_id} total_raw={total_raw} ready={ready_count} "
            "review_required={review_required_count} invalid={invalid_count} "
            "possibly_truncated={possibly_truncated_count} handoffs={handoffs} "
            "reproducibility={reproducibility} db_write=0".format(
                batch_id=artifact["batch_id"],
                handoffs=len(artifact["ready_handoffs"]),
                reproducibility=reproducibility,
                **summary,
            )
        )
