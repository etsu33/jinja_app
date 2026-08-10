"""Import a versioned Shrine Knowledge seed (ShrineKnowledgeSource/ShrineDeity/
ShrineHistory) safely and idempotently.

See docs/audit/knowledge-production-import-foundation.md for the full
design rationale (seed format, shrine identity strategy, idempotency,
transaction boundary, validation rules).

Usage:
    python manage.py import_shrine_knowledge <seed.json> --validate-only
    python manage.py import_shrine_knowledge <seed.json> --dry-run
    python manage.py import_shrine_knowledge <seed.json>

--validate-only: structural/schema validation + shrine identity resolution
    only. No existing-row lookups, no DB writes. Fastest check.
--dry-run: everything --validate-only does, plus computes the full
    CREATE/SKIP/UPDATE plan against the target DB. No DB writes.
(no flag): computes the same plan as --dry-run; if the plan has zero
    errors, applies it inside a single atomic transaction (all-or-nothing).
    A validation or identity-resolution failure anywhere aborts the entire
    run before any write happens.

Exit code is non-zero whenever any error is found, in every mode.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import (
    ParsedSeed,
    find_existing_deity,
    find_existing_history,
    find_existing_source,
    parse_seed,
    resolve_shrine,
)


@dataclass
class PlanItem:
    kind: str  # "source" | "deity" | "history"
    shrine_name: str
    label: str
    action: str  # "CREATE" | "SKIP_EXISTS"
    detail: str = ""


@dataclass
class Plan:
    items: list[PlanItem]
    errors: list[str]

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items:
            out[f"{item.kind}_{item.action}"] = out.get(f"{item.kind}_{item.action}", 0) + 1
        return out


def _build_plan(parsed: ParsedSeed) -> tuple[Plan, dict[str, ShrineKnowledgeSource | None]]:
    """Resolve every shrine identity and compute the CREATE/SKIP plan.

    Returns the plan and a key->existing-or-None map for sources so a
    second pass (apply) doesn't need to re-run identity resolution.
    """
    errors = list(parsed.errors)
    items: list[PlanItem] = []

    source_existing: dict[str, ShrineKnowledgeSource | None] = {}
    for key, entry in parsed.sources.items():
        existing = find_existing_source(
            source_type=entry.source_type,
            title=entry.title,
            url=entry.url,
            bibliography=entry.bibliography,
        )
        source_existing[key] = existing
        items.append(
            PlanItem(
                kind="source",
                shrine_name="",
                label=f"[{key}] {entry.source_type}: {entry.title}",
                action="SKIP_EXISTS" if existing else "CREATE",
                detail=f"matched existing id={existing.pk}" if existing else "",
            )
        )

    for block in parsed.shrines:
        result = resolve_shrine(block.name_jp, block.address)
        if result.status == "NOT_FOUND":
            errors.append(f"shrine {block.name_jp!r}: NOT_FOUND ({result.detail})")
            continue
        if result.status == "AMBIGUOUS":
            errors.append(f"shrine {block.name_jp!r}: IMPORT_IDENTITY_AMBIGUOUS ({result.detail})")
            continue

        shrine = result.shrine
        assert shrine is not None

        for d in block.deities:
            existing = find_existing_deity(shrine, d.display_name)
            items.append(
                PlanItem(
                    kind="deity",
                    shrine_name=block.name_jp,
                    label=d.display_name,
                    action="SKIP_EXISTS" if existing else "CREATE",
                    detail=f"matched existing id={existing.pk}" if existing else "",
                )
            )

        for h in block.histories:
            existing = find_existing_history(shrine, h.history_type, h.title)
            items.append(
                PlanItem(
                    kind="history",
                    shrine_name=block.name_jp,
                    label=f"{h.history_type}: {h.title}",
                    action="SKIP_EXISTS" if existing else "CREATE",
                    detail=f"matched existing id={existing.pk}" if existing else "",
                )
            )

    return Plan(items=items, errors=errors), source_existing


def _apply(
    parsed: ParsedSeed, source_existing: dict[str, ShrineKnowledgeSource | None]
) -> dict[str, int]:
    """Apply the seed inside the caller's transaction. Assumes the plan has
    zero errors — the caller must check that before calling this."""
    created = {"source": 0, "deity": 0, "history": 0}

    source_objs: dict[str, ShrineKnowledgeSource] = {}
    for key, entry in parsed.sources.items():
        existing = source_existing.get(key)
        if existing is not None:
            source_objs[key] = existing
            continue
        obj = ShrineKnowledgeSource(
            source_type=entry.source_type,
            title=entry.title,
            publisher=entry.publisher,
            url=entry.url,
            bibliography=entry.bibliography,
            accessed_at=entry.accessed_at,
            verified_at=entry.verified_at,
            verification_status=entry.verification_status,
            confidence=entry.confidence,
            language=entry.language,
            note=entry.note,
        )
        obj.full_clean()
        obj.save()
        source_objs[key] = obj
        created["source"] += 1

    for block in parsed.shrines:
        result = resolve_shrine(block.name_jp, block.address)
        shrine = result.shrine
        assert shrine is not None, "plan validation must reject unresolved shrines before apply"

        for d in block.deities:
            existing = find_existing_deity(shrine, d.display_name)
            if existing is not None:
                continue
            obj = ShrineDeity(
                shrine=shrine,
                display_name=d.display_name,
                canonical_name=d.canonical_name,
                role=d.role,
                sort_order=d.sort_order,
                verification_status=d.verification_status,
                confidence=d.confidence,
                verified_at=d.verified_at,
                note=d.note,
            )
            obj.full_clean()
            obj.save()
            if d.source_keys:
                obj.sources.set([source_objs[k] for k in d.source_keys])
            created["deity"] += 1

        for h in block.histories:
            existing = find_existing_history(shrine, h.history_type, h.title)
            if existing is not None:
                continue
            obj = ShrineHistory(
                shrine=shrine,
                history_type=h.history_type,
                title=h.title,
                content=h.content,
                period_text=h.period_text,
                event_date=h.event_date,
                sort_order=h.sort_order,
                verification_status=h.verification_status,
                confidence=h.confidence,
                verified_at=h.verified_at,
                note=h.note,
            )
            obj.full_clean()
            obj.save()
            if h.source_keys:
                obj.sources.set([source_objs[k] for k in h.source_keys])
            created["history"] += 1

    return created


class Command(BaseCommand):
    help = (
        "Import a versioned Shrine Knowledge seed (Source/Deity/History) "
        "idempotently. See docs/audit/knowledge-production-import-foundation.md."
    )

    def add_arguments(self, parser):
        parser.add_argument("seed_path", type=str, help="Path to the seed JSON file.")
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Structural/schema validation + shrine identity resolution only. No DB writes.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute the full CREATE/SKIP plan against the target DB. No DB writes.",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["seed_path"])
        if not seed_path.exists():
            raise CommandError(f"seed file not found: {seed_path}")

        try:
            raw = json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"seed file is not valid JSON: {exc}") from exc

        parsed = parse_seed(raw)

        if options["validate_only"]:
            errors = list(parsed.errors)
            if not errors:
                for block in parsed.shrines:
                    result = resolve_shrine(block.name_jp, block.address)
                    if result.status not in ("OK", "OK_CANONICAL_PREFERRED"):
                        errors.append(
                            f"shrine {block.name_jp!r}: {result.status} ({result.detail})"
                        )
            self._report_errors(errors)
            if errors:
                raise CommandError(f"validation failed with {len(errors)} error(s)")
            self.stdout.write(self.style.SUCCESS("validate-only: OK, no errors"))
            return

        plan, source_existing = _build_plan(parsed)
        self._report_plan(plan)

        if plan.errors:
            raise CommandError(f"import blocked: {len(plan.errors)} error(s), see above")

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("dry-run: OK, no DB writes performed"))
            return

        with transaction.atomic():
            created = _apply(parsed, source_existing)

        self.stdout.write(
            self.style.SUCCESS(
                "import complete: "
                f"sources created={created['source']}, "
                f"deities created={created['deity']}, "
                f"histories created={created['history']}"
            )
        )

    def _report_errors(self, errors: list[str]) -> None:
        for err in errors:
            self.stderr.write(self.style.ERROR(f"ERROR: {err}"))

    def _report_plan(self, plan: Plan) -> None:
        for item in plan.items:
            shrine_prefix = f"{item.shrine_name}: " if item.shrine_name else ""
            self.stdout.write(
                f"[{item.kind}] {item.action} {shrine_prefix}{item.label} {item.detail}"
            )
        counts = plan.counts
        self.stdout.write(self.style.SUCCESS(f"plan summary: {counts}"))
        self._report_errors(plan.errors)
