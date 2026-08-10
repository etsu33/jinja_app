"""Export existing Shrine Knowledge (Source/Deity/History) into the versioned
canonical seed format consumed by `import_shrine_knowledge`.

This is the reproducibility-gap fix: Batch 1-7 Knowledge Data
(docs/audit/shrine-knowledge-rollout-batch-1.md through -7.md) was entered
directly via Django ORM / shell, with no durable structured seed file ever
produced. This command converts whatever is currently in the source DB into
a reviewable, re-importable JSON file, using each Shrine's `{name_jp,
address}` as its identity (never a numeric PK — see
docs/audit/knowledge-production-import-foundation.md).

Read-only: this command never writes to the DB it's pointed at.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import SCHEMA_VERSION
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines


def _source_key(source: ShrineKnowledgeSource) -> str:
    """Stable-within-this-export key, not persisted anywhere. Derived only
    from content already validated unique enough by `title`/`source_type`/pk
    for the purpose of linking facts to sources within a single seed file."""
    return f"src-{source.pk}"


def _serialize_source(source: ShrineKnowledgeSource) -> dict:
    return {
        "key": _source_key(source),
        "source_type": source.source_type,
        "title": source.title,
        "publisher": source.publisher,
        "url": source.url,
        "bibliography": source.bibliography,
        "accessed_at": source.accessed_at.isoformat() if source.accessed_at else None,
        "verified_at": source.verified_at.isoformat() if source.verified_at else None,
        "verification_status": source.verification_status,
        "confidence": source.confidence,
        "language": source.language,
        "note": source.note,
    }


class Command(BaseCommand):
    help = (
        "Export existing Shrine Knowledge into the versioned canonical seed "
        "format. Read-only. See docs/audit/knowledge-production-import-foundation.md."
    )

    def add_arguments(self, parser):
        parser.add_argument("output_path", type=str, help="Path to write the seed JSON file to.")

    def handle(self, *args, **options):
        output_path = Path(options["output_path"])

        deity_shrine_ids = set(ShrineDeity.objects.values_list("shrine_id", flat=True))
        history_shrine_ids = set(ShrineHistory.objects.values_list("shrine_id", flat=True))
        all_shrine_ids = deity_shrine_ids | history_shrine_ids

        qa_fixture_ids = set(
            exclude_qa_fixture_shrines(Shrine.objects.filter(id__in=all_shrine_ids)).values_list(
                "id", flat=True
            )
        )
        excluded = all_shrine_ids - qa_fixture_ids
        if excluded:
            raise CommandError(
                "refusing to export: Knowledge Data exists on QA-fixture-pattern "
                f"shrine ids {sorted(excluded)}. This is unexpected for real Batch "
                "1-7 rollout data; investigate before exporting."
            )

        sources_seen: dict[int, ShrineKnowledgeSource] = {}
        shrine_blocks = []

        for shrine in Shrine.objects.filter(id__in=all_shrine_ids).order_by("id"):
            deities = list(
                ShrineDeity.objects.filter(shrine=shrine)
                .prefetch_related("sources")
                .order_by("sort_order", "id")
            )
            histories = list(
                ShrineHistory.objects.filter(shrine=shrine)
                .prefetch_related("sources")
                .order_by("sort_order", "id")
            )
            if not deities and not histories:
                continue

            deity_payload = []
            for d in deities:
                srcs = list(d.sources.all())
                for s in srcs:
                    sources_seen[s.pk] = s
                deity_payload.append(
                    {
                        "display_name": d.display_name,
                        "canonical_name": d.canonical_name,
                        "role": d.role,
                        "sort_order": d.sort_order,
                        "verification_status": d.verification_status,
                        "confidence": d.confidence,
                        "verified_at": d.verified_at.isoformat() if d.verified_at else None,
                        "note": d.note,
                        "source_keys": [_source_key(s) for s in srcs],
                    }
                )

            history_payload = []
            for h in histories:
                srcs = list(h.sources.all())
                for s in srcs:
                    sources_seen[s.pk] = s
                history_payload.append(
                    {
                        "history_type": h.history_type,
                        "title": h.title,
                        "content": h.content,
                        "period_text": h.period_text,
                        "event_date": h.event_date.isoformat() if h.event_date else None,
                        "sort_order": h.sort_order,
                        "verification_status": h.verification_status,
                        "confidence": h.confidence,
                        "verified_at": h.verified_at.isoformat() if h.verified_at else None,
                        "note": h.note,
                        "source_keys": [_source_key(s) for s in srcs],
                    }
                )

            shrine_blocks.append(
                {
                    "shrine_ref": {"name_jp": shrine.name_jp, "address": shrine.address},
                    "deities": deity_payload,
                    "histories": history_payload,
                }
            )

        seed = {
            "schema_version": SCHEMA_VERSION,
            "sources": [_serialize_source(s) for s in sources_seen.values()],
            "shrines": shrine_blocks,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(seed, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"exported {len(sources_seen)} sources, {len(shrine_blocks)} shrines "
                f"({sum(len(b['deities']) for b in shrine_blocks)} deities, "
                f"{sum(len(b['histories']) for b in shrine_blocks)} histories) to {output_path}"
            )
        )
