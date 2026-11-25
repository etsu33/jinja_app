"""Collective Runtime Activation seed workflow（A6-00b）。

`activate_collective_runtime` management command の parse / resolve / plan / apply。

Activation seed の `shrine_ref`（name_jp + address）は Runtime の Shrine identity ではなく、
activation import 時にだけ使う portable な deployment reference である。
解決は既存 Knowledge import と同じ helper（`knowledge_seed.resolve_shrine` /
`knowledge_seed.find_collectives_by_identity`）へ委譲し、Shrine identity ロジックを複製しない。
Activation 作成後の Runtime は `CollectiveRuntimeActivation.collective` FK だけを使う。

Activation は rollout 承認にすぎない。Evidence / member_list_status / Membership /
same-Shrine 等の Runtime admission 判定は A6-01 の責務であり、本モジュールでは行わない。
Pattern も推論しない（member_count / member_list_status / Membership 形状を見ない）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from temples.models import CollectiveRuntimeActivation, ShrineDeityCollective
from temples.services.knowledge_seed import find_collectives_by_identity, resolve_shrine

ACTIVATION_SCHEMA_VERSION = "1.0"
SUPPORTED_ACTIVATION_SCHEMA_VERSIONS = (ACTIVATION_SCHEMA_VERSION,)

# 既存 Knowledge import と同じ「解決済み」扱い（resolve_shrine の契約をそのまま使う）。
_RESOLVED_SHRINE_STATUSES = ("OK", "OK_CANONICAL_PREFERRED")

_TOP_LEVEL_KEYS = {"schema_version", "collectives"}
_ENTRY_KEYS = {"shrine_ref", "source_attested_label"}
_SHRINE_REF_KEYS = {"name_jp", "address"}

ACTION_CREATE = "CREATE"
ACTION_SKIP_EXISTS = "SKIP_EXISTS"


@dataclass(frozen=True)
class ActivationEntry:
    name_jp: str
    address: str
    source_attested_label: str

    @property
    def display(self) -> str:
        return f"{self.name_jp} / {self.source_attested_label}"


@dataclass
class ParsedActivationSeed:
    schema_version: str | None
    entries: list[ActivationEntry]
    errors: list[str]


@dataclass(frozen=True)
class ActivationTarget:
    entry: ActivationEntry
    collective: ShrineDeityCollective


@dataclass(frozen=True)
class ActivationPlanItem:
    entry: ActivationEntry
    collective: ShrineDeityCollective
    action: str  # ACTION_CREATE | ACTION_SKIP_EXISTS


@dataclass
class ActivationPlan:
    items: list[ActivationPlanItem] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {
            ACTION_CREATE: sum(1 for i in self.items if i.action == ACTION_CREATE),
            ACTION_SKIP_EXISTS: sum(1 for i in self.items if i.action == ACTION_SKIP_EXISTS),
        }


def _unexpected_keys(raw: dict, allowed: set[str], prefix: str, errors: list[str]) -> None:
    extra = sorted(set(raw) - allowed)
    if extra:
        errors.append(f"{prefix}: unexpected key(s) {extra}")


def _required_text(raw: dict, key: str, prefix: str, errors: list[str]) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{key}: required non-blank string")
        return ""
    # 値を trim して別 identity へ寄せない（knowledge_seed の label 契約と同じく拒否する）。
    if value != value.strip():
        errors.append(f"{prefix}.{key}: leading/trailing whitespace is not allowed")
        return ""
    return value


def parse_activation_seed(raw: Any) -> ParsedActivationSeed:
    """Activation seed の構造検証（DB に触れない）。error が1件でもあれば entries を使わない。"""
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ParsedActivationSeed(None, [], ["seed: top-level must be an object"])

    _unexpected_keys(raw, _TOP_LEVEL_KEYS, "seed", errors)

    schema_version = raw.get("schema_version")
    if schema_version not in SUPPORTED_ACTIVATION_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version: unsupported {schema_version!r} "
            f"(supported: {list(SUPPORTED_ACTIVATION_SCHEMA_VERSIONS)})"
        )

    collectives = raw.get("collectives")
    if not isinstance(collectives, list) or not collectives:
        errors.append("collectives: required non-empty list")
        return ParsedActivationSeed(schema_version, [], errors)

    entries: list[ActivationEntry] = []
    seen: dict[ActivationEntry, int] = {}
    for index, item in enumerate(collectives):
        prefix = f"collectives[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        entry_errors: list[str] = []
        _unexpected_keys(item, _ENTRY_KEYS, prefix, entry_errors)
        shrine_ref = item.get("shrine_ref")
        name_jp = address = ""
        if not isinstance(shrine_ref, dict):
            entry_errors.append(f"{prefix}.shrine_ref: required object")
        else:
            _unexpected_keys(shrine_ref, _SHRINE_REF_KEYS, f"{prefix}.shrine_ref", entry_errors)
            name_jp = _required_text(shrine_ref, "name_jp", f"{prefix}.shrine_ref", entry_errors)
            address = _required_text(shrine_ref, "address", f"{prefix}.shrine_ref", entry_errors)
        label = _required_text(item, "source_attested_label", prefix, entry_errors)
        if entry_errors:
            errors.extend(entry_errors)
            continue

        entry = ActivationEntry(name_jp=name_jp, address=address, source_attested_label=label)
        if entry in seen:
            errors.append(
                f"{prefix}: DUPLICATE_SEED_ENTRY ({entry.display}; same as collectives[{seen[entry]}])"
            )
            continue
        seen[entry] = index
        entries.append(entry)

    return ParsedActivationSeed(schema_version, entries, errors)


def resolve_activation_targets(
    entries: list[ActivationEntry],
) -> tuple[list[ActivationTarget], list[str]]:
    """seed shrine_ref -> Shrine -> ShrineDeityCollective を読み取り専用で厳密に解決する。

    Collective は resolved Shrine + source_attested_label の完全一致だけで解決する。
    0件は COLLECTIVE_NOT_FOUND、2件以上は COLLECTIVE_AMBIGUOUS（`.first()` で隠さない）。
    異なる seed entry が同一 Collective へ解決された場合は IDENTITY_CONFLICT。
    """
    targets: list[ActivationTarget] = []
    errors: list[str] = []
    resolved_by_collective: dict[int, ActivationEntry] = {}

    for entry in entries:
        shrine_result = resolve_shrine(entry.name_jp, entry.address)
        if shrine_result.status not in _RESOLVED_SHRINE_STATUSES or shrine_result.shrine is None:
            errors.append(
                f"{entry.display}: SHRINE_{shrine_result.status} ({shrine_result.detail})"
            )
            continue

        matches = find_collectives_by_identity(shrine_result.shrine, entry.source_attested_label)
        if not matches:
            errors.append(f"{entry.display}: COLLECTIVE_NOT_FOUND")
            continue
        if len(matches) > 1:
            errors.append(
                f"{entry.display}: COLLECTIVE_AMBIGUOUS "
                f"({len(matches)} rows match resolved Shrine + label)"
            )
            continue

        collective = matches[0]
        previous = resolved_by_collective.get(collective.pk)
        if previous is not None:
            errors.append(
                f"{entry.display}: IDENTITY_CONFLICT "
                f"(resolves to the same Collective as {previous.display})"
            )
            continue
        resolved_by_collective[collective.pk] = entry
        targets.append(ActivationTarget(entry=entry, collective=collective))

    return targets, errors


def build_activation_plan(targets: list[ActivationTarget]) -> ActivationPlan:
    """既存 Activation row の有無だけで CREATE / SKIP_EXISTS を決める（読み取り専用）。"""
    existing = set(
        CollectiveRuntimeActivation.objects.filter(
            collective_id__in=[t.collective.pk for t in targets]
        ).values_list("collective_id", flat=True)
    )
    return ActivationPlan(
        items=[
            ActivationPlanItem(
                entry=t.entry,
                collective=t.collective,
                action=ACTION_SKIP_EXISTS if t.collective.pk in existing else ACTION_CREATE,
            )
            for t in targets
        ]
    )


def apply_activation_plan(plan: ActivationPlan) -> int:
    """CREATE の Activation row だけを作る。既存 row は更新・再作成しない。

    呼び出し側の transaction.atomic() 内で実行すること（例外で全体が巻き戻る）。
    """
    created = 0
    for item in plan.items:
        if item.action != ACTION_CREATE:
            continue
        CollectiveRuntimeActivation.objects.create(collective=item.collective)
        created += 1
    return created


__all__ = [
    "ACTIVATION_SCHEMA_VERSION",
    "SUPPORTED_ACTIVATION_SCHEMA_VERSIONS",
    "ACTION_CREATE",
    "ACTION_SKIP_EXISTS",
    "ActivationEntry",
    "ActivationPlan",
    "ActivationPlanItem",
    "ActivationTarget",
    "ParsedActivationSeed",
    "apply_activation_plan",
    "build_activation_plan",
    "parse_activation_seed",
    "resolve_activation_targets",
]
