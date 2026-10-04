"""Import a versioned Shrine Knowledge seed (ShrineKnowledgeSource/ShrineDeity/
ShrineHistory, for schema 1.1+ ShrineDeityCollective/ShrineDeityCollectiveMembership,
and for schema 1.2 ShrineSourceFact) safely and idempotently.

Schema 1.1 Collective / Membership contract:
docs/audit/collective-deity-knowledge-seed-v1-1-contract.md

Schema 1.2 Source Fact contract (create-only; same stable_key + any difference = CONFLICT):
docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md §12.15.C / §12.15.G

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
from dataclasses import dataclass, field
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.knowledge_seed import (
    CollectiveEntry,
    MembershipEntry,
    ParsedSeed,
    SourceFactEntry,
    diff_collective_fields,
    diff_membership_fields,
    diff_source_fact_fields,
    find_collectives_by_identity,
    find_existing_deity,
    find_existing_history,
    find_source_fact_by_stable_key,
    parse_seed,
    resolve_membership_deity,
    resolve_shrine,
    resolve_source_identity,
)


@dataclass
class PlanItem:
    kind: str  # "source" | "deity" | "history" | "collective" | "membership" | "source_fact"
    shrine_name: str
    label: str
    action: str  # "CREATE" | "REUSE_EXISTING" | "SKIP_EXISTS" | blocking status
    detail: str = ""


@dataclass
class MembershipPlan:
    entry: MembershipEntry
    action: str  # "CREATE" | "SKIP_EXISTS"
    # RESOLVED_EXISTING の場合は plan 時点の既存 ShrineDeity。RESOLVED_SEED の場合は None で、
    # apply 時に同じ Shrine + display_name で厳密に1件へ再解決する。
    deity: ShrineDeity | None
    existing: ShrineDeityCollectiveMembership | None = None


@dataclass
class CollectivePlan:
    shrine: Shrine
    entry: CollectiveEntry
    action: str  # "CREATE" | "SKIP_EXISTS"
    existing: ShrineDeityCollective | None = None
    memberships: list[MembershipPlan] = field(default_factory=list)


@dataclass
class SourceFactPlan:
    shrine: Shrine
    entry: SourceFactEntry
    action: str  # "CREATE" | "SKIP_EXISTS"
    existing: ShrineSourceFact | None = None


@dataclass
class Plan:
    items: list[PlanItem]
    errors: list[str]
    collectives: list[CollectivePlan] = field(default_factory=list)
    source_facts: list[SourceFactPlan] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items:
            out[f"{item.kind}_{item.action}"] = out.get(f"{item.kind}_{item.action}", 0) + 1
        return out


def _source_set_mismatch(
    existing_ids: set[int],
    source_keys: list[str],
    source_existing: dict[str, ShrineKnowledgeSource | None],
) -> str:
    """既存行の Source relation 集合と seed の source_keys が完全一致しないときの説明。"""
    expected_ids = set()
    for key in source_keys:
        source = source_existing.get(key)
        if source is None:
            return f"source {key!r} would be newly created, so the existing relation set differs"
        expected_ids.add(source.pk)
    if existing_ids != expected_ids:
        return f"source ids differ: existing={sorted(existing_ids)} seed={sorted(expected_ids)}"
    return ""


def _plan_collectives(
    shrine: Shrine,
    block_name: str,
    collectives: list[CollectiveEntry],
    seed_deity_names: list[str],
    source_existing: dict[str, ShrineKnowledgeSource | None],
    seen_identities: set[tuple[int, str]],
    items: list[PlanItem],
    errors: list[str],
) -> list[CollectivePlan]:
    plans: list[CollectivePlan] = []
    for entry in collectives:
        label = entry.source_attested_label
        identity = (shrine.pk, label)
        if identity in seen_identities:
            errors.append(
                f"collective {block_name!r}/{label!r}: COLLECTIVE_DUPLICATE_IN_SEED "
                "(another shrine block resolves to the same Shrine + label)"
            )
            items.append(PlanItem("collective", block_name, label, "COLLECTIVE_DUPLICATE_IN_SEED"))
            continue
        seen_identities.add(identity)

        rows = find_collectives_by_identity(shrine, label)
        existing: ShrineDeityCollective | None = None
        if len(rows) > 1:
            action = "COLLECTIVE_AMBIGUOUS"
            detail = f"{len(rows)} existing rows: ids={[r.pk for r in rows]}"
        elif len(rows) == 1:
            existing = rows[0]
            diffs = diff_collective_fields(existing, entry)
            source_diff = _source_set_mismatch(
                set(existing.sources.values_list("id", flat=True)),
                entry.source_keys,
                source_existing,
            )
            if diffs or source_diff:
                action = "COLLECTIVE_CONFLICT"
                parts = [f"fields differ: {', '.join(diffs)}"] if diffs else []
                parts += [source_diff] if source_diff else []
                detail = f"existing id={existing.pk}; " + "; ".join(parts)
            else:
                action = "SKIP_EXISTS"
                detail = f"matched existing id={existing.pk}"
        else:
            action = "CREATE"
            detail = ""
        items.append(PlanItem("collective", block_name, label, action, detail))
        blocked = action not in ("CREATE", "SKIP_EXISTS")
        if blocked:
            errors.append(f"collective {block_name!r}/{label!r}: {action} ({detail})")

        membership_plans: list[MembershipPlan] = []
        for m in entry.memberships:
            m_label = f"{label} <- {m.deity_display_name}"
            resolved = resolve_membership_deity(shrine, m.deity_display_name, seed_deity_names)
            if not resolved.resolved:
                errors.append(
                    f"membership {block_name!r}/{m_label!r}: {resolved.status} ({resolved.detail})"
                )
                items.append(
                    PlanItem("membership", block_name, m_label, resolved.status, resolved.detail)
                )
                continue
            if blocked:
                # 親 Collective が止まっているため Membership identity は判定しない（error は親側で計上済み）。
                items.append(PlanItem("membership", block_name, m_label, "BLOCKED_BY_COLLECTIVE"))
                continue

            existing_membership = None
            if existing is not None and resolved.deity is not None:
                existing_membership = ShrineDeityCollectiveMembership.objects.filter(
                    collective=existing, deity=resolved.deity
                ).first()  # Unique(collective, deity) により高々1件
            if existing_membership is None:
                m_action, m_detail = "CREATE", ""
            else:
                diffs = diff_membership_fields(existing_membership, m)
                source_diff = _source_set_mismatch(
                    set(existing_membership.sources.values_list("id", flat=True)),
                    m.source_keys,
                    source_existing,
                )
                if diffs or source_diff:
                    m_action = "MEMBERSHIP_CONFLICT"
                    parts = [f"fields differ: {', '.join(diffs)}"] if diffs else []
                    parts += [source_diff] if source_diff else []
                    m_detail = f"existing id={existing_membership.pk}; " + "; ".join(parts)
                    errors.append(f"membership {block_name!r}/{m_label!r}: {m_action} ({m_detail})")
                else:
                    m_action = "SKIP_EXISTS"
                    m_detail = f"matched existing id={existing_membership.pk}"
            items.append(PlanItem("membership", block_name, m_label, m_action, m_detail))
            membership_plans.append(
                MembershipPlan(
                    entry=m, action=m_action, deity=resolved.deity, existing=existing_membership
                )
            )

        if not blocked:
            plans.append(
                CollectivePlan(
                    shrine=shrine,
                    entry=entry,
                    action=action,
                    existing=existing,
                    memberships=membership_plans,
                )
            )
    return plans


def _plan_source_facts(
    shrine: Shrine,
    block_name: str,
    facts: list[SourceFactEntry],
    source_existing: dict[str, ShrineKnowledgeSource | None],
    items: list[PlanItem],
    errors: list[str],
) -> list[SourceFactPlan]:
    """stable_key で既存の Fact を照合する。既存 row は更新しない（create-only）。

    同じ stable_key で shrine / wording / characterization / verification 3列 / Source の集合の
    どれかが違えば SOURCE_FACT_CONFLICT（import 全体を止める）。
    """
    plans: list[SourceFactPlan] = []
    for entry in facts:
        key = entry.stable_key
        existing = find_source_fact_by_stable_key(key)
        if existing is None:
            action, detail = "CREATE", ""
        else:
            parts: list[str] = []
            if existing.shrine_id != shrine.pk:
                parts.append(f"shrine differs: existing={existing.shrine_id} seed={shrine.pk}")
            diffs = diff_source_fact_fields(existing, entry)
            if diffs:
                parts.append(f"fields differ: {', '.join(diffs)}")
            source_diff = _source_set_mismatch(
                set(existing.sources.values_list("id", flat=True)),
                entry.source_keys,
                source_existing,
            )
            if source_diff:
                parts.append(source_diff)
            if parts:
                action = "SOURCE_FACT_CONFLICT"
                detail = f"existing id={existing.pk}; " + "; ".join(parts)
                errors.append(f"source_fact {block_name!r}/{key!r}: {action} ({detail})")
            else:
                action, detail = "SKIP_EXISTS", f"matched existing id={existing.pk}"
        items.append(PlanItem("source_fact", block_name, key, action, detail))
        if action in ("CREATE", "SKIP_EXISTS"):
            plans.append(
                SourceFactPlan(shrine=shrine, entry=entry, action=action, existing=existing)
            )
    return plans


def _build_plan(parsed: ParsedSeed) -> tuple[Plan, dict[str, ShrineKnowledgeSource | None]]:
    """Resolve every shrine identity and compute the CREATE/SKIP plan.

    Returns the plan and a key->existing-or-None map for sources so a
    second pass (apply) doesn't need to re-run identity resolution.
    """
    errors = list(parsed.errors)
    items: list[PlanItem] = []
    collective_plans: list[CollectivePlan] = []
    source_fact_plans: list[SourceFactPlan] = []
    seen_collective_identities: set[tuple[int, str]] = set()

    source_existing: dict[str, ShrineKnowledgeSource | None] = {}
    for key, entry in parsed.sources.items():
        identity = resolve_source_identity(entry)
        existing = identity.source
        source_existing[key] = existing
        if identity.status in ("CONFLICT", "AMBIGUOUS"):
            errors.append(f"source {key!r}: SOURCE_REUSE_{identity.status} ({identity.detail})")
        items.append(
            PlanItem(
                kind="source",
                shrine_name="",
                label=f"[{key}] {entry.source_type}: {entry.title}",
                action=identity.status,
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

        collective_plans += _plan_collectives(
            shrine,
            block.name_jp,
            block.collectives,
            [d.display_name for d in block.deities],
            source_existing,
            seen_collective_identities,
            items,
            errors,
        )

        source_fact_plans += _plan_source_facts(
            shrine, block.name_jp, block.source_facts, source_existing, items, errors
        )

    return (
        Plan(
            items=items,
            errors=errors,
            collectives=collective_plans,
            source_facts=source_fact_plans,
        ),
        source_existing,
    )


def _apply_collectives(
    collective_plans: list[CollectivePlan],
    source_objs: dict[str, ShrineKnowledgeSource],
    created: dict[str, int],
) -> None:
    """Collective / Membership を plan どおりに作成する（通常の full_clean() + save() のみ）。

    plan と異なる identity 判断を apply で黙って下さない。plan 時点から DB 状態が変わって
    いれば CommandError を送出し、呼び出し側の transaction.atomic() ごと巻き戻す。
    """
    for cplan in collective_plans:
        entry = cplan.entry
        current = find_collectives_by_identity(cplan.shrine, entry.source_attested_label)
        if cplan.action == "SKIP_EXISTS":
            if [row.pk for row in current] != [cplan.existing.pk]:
                raise CommandError(
                    f"collective {entry.source_attested_label!r}: identity changed after planning"
                )
            collective = cplan.existing
        else:
            if current:
                raise CommandError(
                    f"collective {entry.source_attested_label!r}: already exists at apply time"
                )
            collective = ShrineDeityCollective(
                shrine=cplan.shrine,
                source_attested_label=entry.source_attested_label,
                role=entry.role,
                sort_order=entry.sort_order,
                member_count=entry.member_count,
                member_count_relation=entry.member_count_relation,
                member_list_status=entry.member_list_status,
                verification_status=entry.verification_status,
                confidence=entry.confidence,
                verified_at=entry.verified_at,
                note=entry.note,
            )
            collective.full_clean()
            collective.save()
            collective.sources.set([source_objs[k] for k in entry.source_keys])
            created["collective"] += 1

        for mplan in cplan.memberships:
            if mplan.action == "SKIP_EXISTS":
                continue
            m = mplan.entry
            deity = mplan.deity
            if deity is None:
                # same-seed Deity は上の Deity apply で作成済み。同じ Shrine + display_name で厳密に1件。
                rows = list(
                    ShrineDeity.objects.filter(
                        shrine=cplan.shrine, display_name=m.deity_display_name
                    )
                )
                if len(rows) != 1:
                    raise CommandError(
                        f"membership {m.deity_display_name!r}: expected exactly 1 ShrineDeity "
                        f"at apply time, found {len(rows)}"
                    )
                deity = rows[0]
            membership = ShrineDeityCollectiveMembership(
                collective=collective,
                deity=deity,
                sort_order=m.sort_order,
                verification_status=m.verification_status,
                confidence=m.confidence,
                verified_at=m.verified_at,
                note=m.note,
            )
            membership.full_clean()
            membership.save()
            # Membership Evidence = B: Collective の Source を継承せず、自分の source_keys だけを付ける。
            membership.sources.set([source_objs[k] for k in m.source_keys])
            created["membership"] += 1


def _apply_source_facts(
    source_fact_plans: list[SourceFactPlan],
    source_objs: dict[str, ShrineKnowledgeSource],
    created: dict[str, int],
) -> None:
    """Source Fact を plan どおりに作成する（create-only。既存 row は更新しない）。

    plan 時点から DB 状態が変わっていれば CommandError を送出し、呼び出し側の
    transaction.atomic() ごと巻き戻す。
    """
    for fplan in source_fact_plans:
        entry = fplan.entry
        current = find_source_fact_by_stable_key(entry.stable_key)
        if fplan.action == "SKIP_EXISTS":
            if current is None or current.pk != fplan.existing.pk:
                raise CommandError(
                    f"source_fact {entry.stable_key!r}: identity changed after planning"
                )
            continue
        if current is not None:
            raise CommandError(f"source_fact {entry.stable_key!r}: already exists at apply time")
        fact = ShrineSourceFact(
            shrine=fplan.shrine,
            stable_key=entry.stable_key,
            source_attested_wording=entry.source_attested_wording,
            evidence_characterization=entry.evidence_characterization,
            verification_status=entry.verification_status,
            confidence=entry.confidence,
            verified_at=entry.verified_at,
        )
        fact.full_clean()
        fact.save()
        # 自分の source_keys だけを付ける（他の Fact の Source を継承しない）。
        fact.sources.set([source_objs[k] for k in entry.source_keys])
        created["source_fact"] += 1


def _apply(
    parsed: ParsedSeed,
    source_existing: dict[str, ShrineKnowledgeSource | None],
    collective_plans: list[CollectivePlan] | None = None,
    source_fact_plans: list[SourceFactPlan] | None = None,
) -> dict[str, int]:
    """Apply the seed inside the caller's transaction. Assumes the plan has
    zero errors — the caller must check that before calling this."""
    created = {
        "source": 0,
        "deity": 0,
        "history": 0,
        "collective": 0,
        "membership": 0,
        "source_fact": 0,
    }

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

    # 全 shrine block の Deity を作成した後に Collective / Membership を作る
    # （same-seed Deity を Membership が参照できるように）。
    _apply_collectives(collective_plans or [], source_objs, created)
    _apply_source_facts(source_fact_plans or [], source_objs, created)

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

        expected = {
            kind: sum(1 for item in plan.items if item.kind == kind and item.action == "CREATE")
            for kind in ("collective", "membership", "source_fact")
        }
        with transaction.atomic():
            created = _apply(parsed, source_existing, plan.collectives, plan.source_facts)
            for kind, count in expected.items():
                if created[kind] != count:
                    raise CommandError(
                        f"{kind} created={created[kind]} differs from planned CREATE={count}; "
                        "rolled back"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "import complete: "
                f"sources created={created['source']}, "
                f"deities created={created['deity']}, "
                f"histories created={created['history']}, "
                f"collectives created={created['collective']}, "
                f"memberships created={created['membership']}, "
                f"source_facts created={created['source_fact']}"
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
