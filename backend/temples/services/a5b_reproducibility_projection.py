"""A-5b reproducibility projection (A-5b contract §10.1).

Builds the canonical comparison projection of the fixed 10-candidate A-5b state
from git-tracked records at one commit, and serializes it to the §10.1 H bytes.

Contract: ``docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md``
§10.1. This module implements that section only. It does not re-evaluate any
candidate, and it never defaults a missing value: anything that §10.1 cannot
resolve raises ``ProjectionUnresolved`` (§10.1 I, ``UNRESOLVED``).

Read-only: files are read with ``git show <commit>:<path>``. No DB, network,
importer, Seed, or Artifact write. ``normalize_source_url`` is the only
repository function called (§10.1 L).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from temples.services.knowledge_seed import normalize_source_url

PROJECTION_NAME = "a5b-reproducibility-projection"
PROJECTION_VERSION = 1
CANDIDATE_COUNT = 10

CONTRACT_PATH = "docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md"
HISTORICAL_INPUT_PATH = "docs/audit/collective-deity-backfill-candidate-freeze.md"
PATTERN_B_SEED_PATH = "backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json"
CANDIDATE_ARTIFACT_GLOB_PREFIX = "docs/audit/collective-deity-a5b-"

FREEZE = "FREEZE"
HOLD = "HOLD"
EXCLUDE = "EXCLUDE"

COLLECTIVE_FIELDS = (
    "role",
    "sort_order",
    "member_count",
    "member_count_relation",
    "member_list_status",
    "verification_status",
    "confidence",
)
COLLECTIVE_INT_FIELDS = ("sort_order",)
COLLECTIVE_NULLABLE_INT_FIELDS = ("member_count",)
EVIDENCE_ASSERTIONS = (
    "source_attested_label",
    "role",
    "member_count",
    "member_count_relation",
)

# Seed 1.1 contract §5.1 / §6.1 defaults: the contract-defined meaning of an
# omitted Seed field (§10.1 E). Used only for Seed entries.
SEED_COLLECTIVE_DEFAULTS: dict[str, Any] = {
    "role": "unknown",
    "sort_order": 0,
    "member_count": None,
    "member_count_relation": "unspecified",
    "member_list_status": "not_determined",
    "verification_status": "draft",
    "confidence": "",
}
SEED_MEMBERSHIP_DEFAULTS: dict[str, Any] = {
    "sort_order": 0,
    "verification_status": "draft",
    "confidence": "",
}


class ProjectionUnresolved(Exception):
    """§10.1 I ``UNRESOLVED``: no valid projection can be produced."""


class RecordReader(Protocol):
    def read_text(self, path: str) -> str: ...

    def list_paths(self, prefix: str) -> list[str]: ...


class GitCommitReader:
    """Reads git-tracked files at one commit (§10.1 B). Never the working tree."""

    def __init__(self, commit: str, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.commit = self._git("rev-parse", "--verify", f"{commit}^{{commit}}").strip()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ProjectionUnresolved(
                f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace').strip()}"
            )
        return result.stdout.decode("utf-8")

    def read_text(self, path: str) -> str:
        return self._git("show", f"{self.commit}:{path}")

    def list_paths(self, prefix: str) -> list[str]:
        directory = prefix.rsplit("/", 1)[0]
        names = self._git("ls-tree", "--name-only", self.commit, f"{directory}/").splitlines()
        return sorted(name for name in names if name.startswith(prefix))


# ---------------------------------------------------------------------------
# Record map (§10.1 E). "current: 1–6 / 7, 8, 10 / 9". A record that no longer
# matches this map makes the Gate UNRESOLVED until the map is revised.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactSections:
    identity: str
    fields: str | None = None
    verification: str | None = None
    evidence: str | None = None
    final_record: str | None = None
    current_section: str | None = None


@dataclass(frozen=True)
class FreezeArtifactRecord:
    path: str
    sections: ArtifactSections


@dataclass(frozen=True)
class HoldArtifactRecord:
    path: str
    sections: ArtifactSections


GRANDFATHERED_POSITIONS = (1, 2, 3, 4, 5, 6)

ARTIFACT_RECORDS: dict[int, FreezeArtifactRecord | HoldArtifactRecord] = {
    7: FreezeArtifactRecord(
        path="docs/audit/collective-deity-a5b-yasaka-freeze-evidence.md",
        sections=ArtifactSections(
            identity="## 1. Candidate identity",
            verification="## 2. Direct verification event",
            evidence="## 4. Evidence block (§7.1)",
            fields="## 8. Current candidate fields (§7)",
        ),
    ),
    8: FreezeArtifactRecord(
        path="docs/audit/collective-deity-a5b-tokyo-daijingu-freeze-evidence.md",
        sections=ArtifactSections(
            identity="## 1. Candidate identity",
            verification="## 2. Direct verification event",
            evidence="## 4. Evidence block (§7.1)",
            fields="## 8. Current candidate fields (§7)",
        ),
    ),
    9: HoldArtifactRecord(
        path="docs/audit/collective-deity-a5b-tomioka-hold-evidence.md",
        sections=ArtifactSections(
            identity="## 1. Candidate identity",
            final_record="## 10. Final record",
        ),
    ),
    # Position 10: only the current authoritative section C applies (§6.5 C).
    10: FreezeArtifactRecord(
        path="docs/audit/collective-deity-a5b-aso-freeze-evidence.md",
        sections=ArtifactSections(
            current_section="## C. Current authoritative evaluation — original candidate",
            identity="### C.2 Original candidate",
            verification="### C.1 Current direct verification event",
            evidence="### C.4 Evidence block (§7.1)",
            fields="### C.5 Current candidate fields (§7)",
        ),
    ),
}


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6}) ")
_BACKTICK = re.compile(r"`([^`]*)`")


def _section(text: str, heading: str, where: str) -> str:
    lines = text.split("\n")
    matches = [i for i, line in enumerate(lines) if line.rstrip() == heading]
    if len(matches) != 1:
        raise ProjectionUnresolved(f"{where}: heading {heading!r} found {len(matches)} times")
    start = matches[0]
    level = len(_HEADING.match(heading).group(1))  # type: ignore[union-attr]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        m = _HEADING.match(lines[i])
        if m and len(m.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start + 1 : end])


def _table_rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _tables(block: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[str] = []
    for line in block.split("\n") + [""]:
        if line.startswith("|"):
            current.append(line)
        elif current:
            tables.append(_table_rows("\n".join(current)))
            current = []
    return tables


def _assignments(block: str) -> dict[str, str]:
    """``key = value`` lines from fenced text blocks."""
    values: dict[str, str] = {}
    for line in block.split("\n"):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s+=\s+(.*)$", line)
        if m:
            key = m.group(1)
            if key in values:
                raise ProjectionUnresolved(f"duplicate assignment {key!r}")
            values[key] = m.group(2).rstrip()
    return values


def _backticked(cell: str, where: str) -> str:
    m = re.fullmatch(r"`([^`]*)`", cell)
    if not m:
        raise ProjectionUnresolved(f"{where}: expected one backticked value, got {cell!r}")
    value = m.group(1)
    return "" if value == '""' else value


def _int(value: str, where: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ProjectionUnresolved(f"{where}: not an integer: {value!r}")
    return int(value)


def _source(source_type: Any, url: Any, where: str) -> dict[str, str]:
    if not isinstance(source_type, str) or not source_type or not isinstance(url, str) or not url:
        raise ProjectionUnresolved(f"{where}: incomplete Source identity")
    normalized = normalize_source_url(url)
    if not normalized:
        raise ProjectionUnresolved(f"{where}: URL normalizes to empty")
    return {"source_type": source_type, "url": normalized}


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def fixed_universe(reader: RecordReader) -> list[tuple[str, str]]:
    """§7 candidate_order rule: first appearance of (Shrine, label) over every
    table row of the historical fixed input document, top to bottom."""
    text = reader.read_text(HISTORICAL_INPUT_PATH)
    seen: list[tuple[str, str]] = []
    for table in _tables(text):
        if len(table) < 2 or table[0][0] != "Shrine":
            raise ProjectionUnresolved(f"historical input: unexpected table header {table[:1]!r}")
        for row in table[1:]:
            key = (row[0], row[1])
            if key not in seen:
                seen.append(key)
    if len(seen) != CANDIDATE_COUNT:
        raise ProjectionUnresolved(
            f"fixed universe has {len(seen)} positions, expected {CANDIDATE_COUNT}"
        )
    return seen


def reason_code_mapping(reader: RecordReader) -> dict[str, str]:
    contract = reader.read_text(CONTRACT_PATH)
    block = contract.split("A-5b reason_code rule.", 1)
    if len(block) != 2:
        raise ProjectionUnresolved("contract: reason_code rule not found")
    table = _tables(block[1])[0]
    mapping = {
        _backticked(row[0], "reason_code rule"): _backticked(row[1], "reason_code rule")
        for row in table[1:]
    }
    if set(mapping) != {FREEZE, HOLD, EXCLUDE}:
        raise ProjectionUnresolved(f"contract: unexpected reason_code mapping {mapping!r}")
    return mapping


def grandfathered_rows(reader: RecordReader) -> dict[int, dict[str, str]]:
    contract = reader.read_text(CONTRACT_PATH)
    block = _section(
        contract, "#### 7.3.1 Current lifecycle status (Mother Ship, 2026-10-02)", "contract"
    )
    table = _tables(block)[0]
    rows: dict[int, dict[str, str]] = {}
    for row in table[1:]:
        order = _int(row[0], "§7.3.1")
        rows[order] = {
            "name_jp": row[1],
            "source_attested_label": row[2],
            "a5b_freeze_status": _backticked(row[3], "§7.3.1"),
            "reason_code": _backticked(row[4], "§7.3.1"),
        }
    if tuple(sorted(rows)) != GRANDFATHERED_POSITIONS:
        raise ProjectionUnresolved(f"§7.3.1 positions {sorted(rows)} do not match the record map")
    return rows


def _check_one_record_per_position(reader: RecordReader, universe: list[tuple[str, str]]) -> None:
    """§10.1 D: zero, or two or more, current records for a position -> UNRESOLVED."""
    artifact_titles: dict[str, str] = {}
    for path in reader.list_paths(CANDIDATE_ARTIFACT_GLOB_PREFIX):
        if not path.endswith(".md"):
            continue
        first_line = reader.read_text(path).split("\n", 1)[0]
        if first_line.startswith("# A-5b ") and "Evidence Artifact — " in first_line:
            artifact_titles[path] = first_line.split("Evidence Artifact — ", 1)[1].strip()
    for order, (name_jp, _label) in enumerate(universe, start=1):
        claiming = sorted(path for path, shrine in artifact_titles.items() if shrine == name_jp)
        expected = [ARTIFACT_RECORDS[order].path] if order in ARTIFACT_RECORDS else []
        if claiming != expected:
            raise ProjectionUnresolved(
                f"position {order}: candidate-level Artifacts {claiming} do not match the record map {expected}"
            )


# ---------------------------------------------------------------------------
# Candidate builders
# ---------------------------------------------------------------------------


def _grandfathered_candidate(
    order: int, row: dict[str, str], seed: dict[str, Any]
) -> dict[str, Any]:
    where = f"position {order} (Pattern B Seed)"
    blocks = [
        b
        for b in seed.get("shrines", [])
        if b.get("shrine_ref", {}).get("name_jp") == row["name_jp"]
    ]
    if len(blocks) != 1:
        raise ProjectionUnresolved(f"{where}: {len(blocks)} Seed blocks for {row['name_jp']!r}")
    block = blocks[0]
    collectives = [
        c
        for c in block.get("collectives", [])
        if c.get("source_attested_label") == row["source_attested_label"]
    ]
    if len(collectives) != 1:
        raise ProjectionUnresolved(f"{where}: {len(collectives)} Seed Collectives for the label")
    entry = collectives[0]
    sources_by_key = {s.get("key"): s for s in seed.get("sources", [])}

    def resolve(keys: Any, assertion: str) -> list[dict[str, str]]:
        if not isinstance(keys, list) or not keys:
            raise ProjectionUnresolved(f"{where}: {assertion} has no source_keys")
        refs = []
        for key in keys:
            source = sources_by_key.get(key)
            if source is None:
                raise ProjectionUnresolved(f"{where}: unknown source_key {key!r}")
            refs.append(
                {
                    "assertion": assertion,
                    **_source(source.get("source_type"), source.get("url"), where),
                }
            )
        return refs

    collective = {
        field: entry.get(field, SEED_COLLECTIVE_DEFAULTS[field]) for field in COLLECTIVE_FIELDS
    }
    assertion_sources = resolve(entry.get("source_keys"), "collective")
    memberships = []
    for member in entry.get("memberships", []):
        display_name = (member.get("deity_ref") or {}).get("display_name")
        if not isinstance(display_name, str) or not display_name:
            raise ProjectionUnresolved(f"{where}: Membership without deity_ref.display_name")
        memberships.append(
            {
                "deity_ref": {"display_name": display_name},
                **{
                    field: member.get(field, default)
                    for field, default in SEED_MEMBERSHIP_DEFAULTS.items()
                },
            }
        )
        assertion_sources += resolve(member.get("source_keys"), f"membership:{display_name}")

    return {
        "candidate_order": order,
        "shrine_ref": {"address": block["shrine_ref"].get("address"), "name_jp": row["name_jp"]},
        "source_attested_label": row["source_attested_label"],
        "a5b_freeze_status": row["a5b_freeze_status"],
        "reason_code": row["reason_code"],
        "collective": collective,
        "memberships": memberships,
        "sources": [{"source_type": r["source_type"], "url": r["url"]} for r in assertion_sources],
        "assertion_sources": assertion_sources,
    }


def _artifact_identity(text: str, sections: ArtifactSections, where: str) -> dict[str, str]:
    values = _assignments(_section(text, sections.identity, where))
    keys = ("shrine_ref.name_jp", "shrine_ref.address", "source_attested_label")
    if any(key not in values for key in keys):
        raise ProjectionUnresolved(f"{where}: candidate identity incomplete")
    return {key: values[key] for key in keys}


def _freeze_artifact_candidate(
    order: int, record: FreezeArtifactRecord, reader: RecordReader
) -> dict[str, Any]:
    where = f"position {order} ({record.path})"
    text = reader.read_text(record.path)
    sections = record.sections
    if sections.current_section is not None:
        text = _section(text, sections.current_section, where)
    identity = _artifact_identity(text, sections, where)

    fields: dict[str, str] = {}
    for row in _tables(_section(text, sections.fields, where))[0][1:]:  # type: ignore[arg-type]
        single = re.fullmatch(r"`([^`]*)`", row[0])
        key = single.group(1) if single else row[0]
        if key in fields:
            raise ProjectionUnresolved(f"{where}: duplicate field row {key!r}")
        fields[key] = row[1]

    def field(name: str) -> str:
        if name not in fields:
            raise ProjectionUnresolved(f"{where}: required field {name!r} missing")
        return _backticked(fields[name], f"{where} {name}")

    if _int(field("candidate_order"), where) != order:
        raise ProjectionUnresolved(f"{where}: candidate_order does not match the record map")
    if fields.get("source_attested_label") != identity["source_attested_label"]:
        raise ProjectionUnresolved(f"{where}: field-table label differs from candidate identity")

    collective: dict[str, Any] = {}
    for name in COLLECTIVE_FIELDS:
        raw = field(name)
        if name in COLLECTIVE_INT_FIELDS:
            collective[name] = _int(raw, f"{where} {name}")
        elif name in COLLECTIVE_NULLABLE_INT_FIELDS:
            collective[name] = None if raw == "null" else _int(raw, f"{where} {name}")
        else:
            collective[name] = raw

    if fields.get("memberships[]") != "none":
        raise ProjectionUnresolved(
            f"{where}: memberships[] is not recorded as none; no Membership mapping defined"
        )

    # sources[] of the current verification event, and the S-label definitions.
    verification = _section(text, sections.verification, where)  # type: ignore[arg-type]
    labels: dict[str, dict[str, str]] = {}
    for row in _table_rows(verification):
        m = re.fullmatch(r"(S\d+): `([^`]+)` \+ `([^`]+)`", row[-1]) if len(row) == 2 else None
        if m:
            labels[m.group(1)] = _source(m.group(2), m.group(3), where)
    source_tables = [
        t for t in _tables(verification) if t[0][:2] == ["source_type", "url (normalized)"]
    ]
    if len(source_tables) != 1:
        raise ProjectionUnresolved(
            f"{where}: expected one sources[] table, found {len(source_tables)}"
        )
    sources = [_source(row[0], row[1], where) for row in source_tables[0][1:]]

    evidence = _section(text, sections.evidence, where)  # type: ignore[arg-type]
    refs = set(re.findall(r"`source_ref` = (S\d+)", evidence))
    if len(refs) != 1:
        raise ProjectionUnresolved(
            f"{where}: evidence block source_ref not uniquely stated: {sorted(refs)}"
        )
    ref = refs.pop()
    if ref not in labels or labels[ref] not in sources:
        raise ProjectionUnresolved(
            f"{where}: source_ref {ref} does not resolve to a sources[] entry"
        )
    evidence_tables = [t for t in _tables(evidence) if len(t[0]) > 1 and t[0][1] == "Assertion"]
    if len(evidence_tables) != 1:
        raise ProjectionUnresolved(
            f"{where}: expected one evidence table, found {len(evidence_tables)}"
        )
    assertion_sources = []
    for row in evidence_tables[0][1:]:
        assertion = _backticked(row[1], where)
        if assertion not in EVIDENCE_ASSERTIONS:
            raise ProjectionUnresolved(f"{where}: unmapped evidence assertion {assertion!r}")
        assertion_sources.append({"assertion": assertion, **labels[ref]})

    return {
        "candidate_order": order,
        "shrine_ref": {
            "address": identity["shrine_ref.address"],
            "name_jp": identity["shrine_ref.name_jp"],
        },
        "source_attested_label": identity["source_attested_label"],
        "a5b_freeze_status": field("a5b_freeze_status"),
        "reason_code": field("reason_code"),
        "collective": collective,
        "memberships": [],
        "sources": sources
        + [{"source_type": r["source_type"], "url": r["url"]} for r in assertion_sources],
        "assertion_sources": assertion_sources,
    }


def _hold_artifact_candidate(
    order: int, record: HoldArtifactRecord, reader: RecordReader
) -> dict[str, Any]:
    where = f"position {order} ({record.path})"
    text = reader.read_text(record.path)
    identity = _artifact_identity(text, record.sections, where)
    final = _assignments(_section(text, record.sections.final_record, where))  # type: ignore[arg-type]
    for key in ("candidate_order", "a5b_freeze_status", "reason_code"):
        if key not in final:
            raise ProjectionUnresolved(f"{where}: final record lacks {key!r}")
    if _int(final["candidate_order"], where) != order:
        raise ProjectionUnresolved(f"{where}: candidate_order does not match the record map")
    # §10.1 F null rule: a HOLD / EXCLUDE candidate has no frozen packet.
    return {
        "candidate_order": order,
        "shrine_ref": {
            "address": identity["shrine_ref.address"],
            "name_jp": identity["shrine_ref.name_jp"],
        },
        "source_attested_label": identity["source_attested_label"],
        "a5b_freeze_status": final["a5b_freeze_status"],
        "reason_code": final["reason_code"],
        "collective": None,
        "memberships": None,
        "sources": None,
        "assertion_sources": None,
    }


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------


def _dedupe_sorted(items: list[dict[str, str]], keys: tuple[str, ...]) -> list[dict[str, str]]:
    unique = {tuple(item[k] for k in keys): item for item in items}
    return [unique[k] for k in sorted(unique)]


def _validate(candidate: dict[str, Any], mapping: dict[str, str]) -> None:
    where = f"position {candidate['candidate_order']}"
    status = candidate["a5b_freeze_status"]
    if status not in mapping:
        raise ProjectionUnresolved(f"{where}: unknown a5b_freeze_status {status!r}")
    if candidate["reason_code"] != mapping[status]:
        raise ProjectionUnresolved(f"{where}: reason_code does not match the §7 mapping")
    for key in ("name_jp", "address"):
        if not isinstance(candidate["shrine_ref"][key], str) or not candidate["shrine_ref"][key]:
            raise ProjectionUnresolved(f"{where}: shrine_ref.{key} missing")
    packet = ("collective", "memberships", "sources", "assertion_sources")
    if status == FREEZE:
        if any(candidate[key] is None for key in packet):
            raise ProjectionUnresolved(
                f"{where}: FREEZE candidate lacks a required projection value"
            )
        collective = candidate["collective"]
        for name in COLLECTIVE_FIELDS:
            value = collective.get(name)
            if name in COLLECTIVE_INT_FIELDS:
                ok = type(value) is int
            elif name in COLLECTIVE_NULLABLE_INT_FIELDS:
                ok = value is None or type(value) is int
            else:
                ok = isinstance(value, str)
            if not ok:
                raise ProjectionUnresolved(
                    f"{where}: collective.{name} missing or invalid: {value!r}"
                )
        for member in candidate["memberships"]:
            if type(member["sort_order"]) is not int or not all(
                isinstance(member[k], str) for k in ("verification_status", "confidence")
            ):
                raise ProjectionUnresolved(f"{where}: Membership value missing or invalid")
    elif any(candidate[key] is not None for key in packet):
        raise ProjectionUnresolved(f"{where}: {status} candidate must project null packet fields")


def build_projection(reader: RecordReader) -> dict[str, Any]:
    universe = fixed_universe(reader)
    mapping = reason_code_mapping(reader)
    grandfathered = grandfathered_rows(reader)
    _check_one_record_per_position(reader, universe)
    seed = json.loads(reader.read_text(PATTERN_B_SEED_PATH))

    candidates = []
    for order, (name_jp, label) in enumerate(universe, start=1):
        if order in grandfathered:
            candidate = _grandfathered_candidate(order, grandfathered[order], seed)
        elif isinstance(ARTIFACT_RECORDS.get(order), FreezeArtifactRecord):
            candidate = _freeze_artifact_candidate(order, ARTIFACT_RECORDS[order], reader)  # type: ignore[arg-type]
        elif isinstance(ARTIFACT_RECORDS.get(order), HoldArtifactRecord):
            candidate = _hold_artifact_candidate(order, ARTIFACT_RECORDS[order], reader)  # type: ignore[arg-type]
        else:
            raise ProjectionUnresolved(f"position {order}: no record in the record map")
        if (candidate["shrine_ref"]["name_jp"], candidate["source_attested_label"]) != (
            name_jp,
            label,
        ):
            raise ProjectionUnresolved(
                f"position {order}: record identity does not match the fixed universe"
            )
        if candidate["sources"] is not None:
            candidate["sources"] = _dedupe_sorted(candidate["sources"], ("source_type", "url"))
            candidate["assertion_sources"] = _dedupe_sorted(
                candidate["assertion_sources"], ("assertion", "source_type", "url")
            )
        _validate(candidate, mapping)
        candidates.append(candidate)

    return {
        "candidates": candidates,
        "projection": PROJECTION_NAME,
        "projection_version": PROJECTION_VERSION,
    }


def _reject_non_canonical_values(value: Any) -> None:
    if isinstance(value, bool) or isinstance(value, float):
        raise ProjectionUnresolved(f"non-canonical JSON value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _reject_non_canonical_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_non_canonical_values(item)


def serialize_projection(projection: dict[str, Any]) -> bytes:
    """§10.1 H canonical bytes."""
    _reject_non_canonical_values(projection)
    text = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return text.encode("utf-8")


def projection_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
