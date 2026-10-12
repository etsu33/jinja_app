#!/usr/bin/env python3
"""Shrine Expansion G7 SQL artifact generator (Phase 1, read-only, no DB access).

Generates the four G7 Production Import SQL artifacts of one candidate from an
explicit, validated spec in ``g7_specs/``:

    1. g7_preflight.sql
    2. g7_pre_base_guard.sql
    3. g7_post_base_guard.sql
    4. g7_post_knowledge_verification.sql

Each ``source_identity.strategy`` owns its SQL template family in
``g7_templates/<strategy>/``. The two families are derived mechanically from the
historical artifacts and are not merged into one inferred rule:

    normalized_url_identity  nsrc-000002: source_type + normalize_source_url()
                             semantic identity, frozen pre-state CTE, state class
    url_pattern_set          nsrc-000004: source_type + explicit URL LIKE patterns

Every value comes from the spec; nothing is inferred from the candidate name.
This module opens no database connection, makes no network call, reads no
credential and executes no SQL. Every generated statement is SELECT/WITH only.

Subset extraction and Runtime QA generation are intentionally out of scope
(G-7 next subphase).

Usage:
    g7_sql_generator.py validate SPEC [SPEC ...]
    g7_sql_generator.py generate --spec SPEC --output-dir DIR [--overwrite]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]


def _load_guard():
    # Load migration_safety/guard.py under a private name. scripts/analytics_safety also
    # has a guard.py; importing either as the top-level module "guard" would shadow the other.
    spec = importlib.util.spec_from_file_location(
        "_g7_migration_safety_guard", SCRIPT_DIR / "guard.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


is_readonly_sql = _load_guard().is_readonly_sql

SPEC_DIR = SCRIPT_DIR / "g7_specs"
TEMPLATE_DIR = SCRIPT_DIR / "g7_templates"
SCHEMA_VERSION = 1

NORMALIZED = "normalized_url_identity"
URL_PATTERNS = "url_pattern_set"
STRATEGIES = (NORMALIZED, URL_PATTERNS)

# Fixed output order and names.
ARTIFACTS = (
    ("preflight", "g7_preflight.sql"),
    ("pre_base_guard", "g7_pre_base_guard.sql"),
    ("post_base_guard", "g7_post_base_guard.sql"),
    ("post_knowledge_verification", "g7_post_knowledge_verification.sql"),
)

# Copies of temples.models choices; a backend test keeps them equal.
SOURCE_TYPES = frozenset(
    {
        "shrine_official",
        "government",
        "cultural_property",
        "academic",
        "museum_or_archive",
        "local_history",
        "tourism_official",
        "secondary_editorial",
        "user_observation",
        "internal_research",
    }
)
VERIFICATION_STATUSES = frozenset(
    {"draft", "unverified", "source_confirmed", "reviewed", "disputed", "outdated", "rejected"}
)
CONFIDENCES = frozenset({"low", "medium", "high"})
HISTORY_TYPES = frozenset(
    {
        "official_origin",
        "founding",
        "historical_event",
        "tradition",
        "regional_context",
        "editorial_summary",
    }
)

CANDIDATE_ID_RE = re.compile(r"^nsrc-[0-9]{6}$")
LABEL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SERVER_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")
MIGRATION_RE = re.compile(r"^([0-9]{4})_[a-z0-9_]+$")
STABLE_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f  ]")
TOTAL_KEYS = ("shrine_total", "source_total", "deity_total", "history_total", "source_fact_total")

COMMON_TOP = {
    "schema_version",
    "candidate",
    "production_pre_state",
    "base",
    "source_identity",
    "knowledge",
    "post_state",
}
STRATEGY_SECTION = {NORMALIZED: "normalized_url_identity_sql", URL_PATTERNS: "url_pattern_set_sql"}
CANDIDATE_FIELDS = {
    "candidate_id",
    "name_jp",
    "address",
    "latitude",
    "longitude",
    "alternate_names",
}
BASE_FIELDS = {
    "expected_exact_before",
    "expected_exact_after",
    "expected_same_name_before",
    "expected_same_name_after",
    "expected_goriyaku_tag_links_after",
    "expected_goriyaku_text",
}
SOURCE_FIELDS = {
    NORMALIZED: {
        "strategy",
        "source_type",
        "normalized_url",
        "publisher",
        "verification_status",
        "confidence",
        "language",
        "bibliography",
        "diagnostic_host_tokens",
        "diagnostic_path_tokens",
        "accepted_source_count",
    },
    URL_PATTERNS: {"strategy", "source_type", "url_patterns"},
}
KNOWLEDGE_FIELDS = {
    "expected_source_count",
    "expected_deity_count",
    "expected_history_count",
    "expected_source_fact_count",
    "expected_goriyaku_tag_links",
    "deity_names",
    "history_titles",
    "source_fact_stable_keys",
}
NORMALIZED_SQL_FIELDS = {
    "frozen_evidence",
    "sql_labels",
    "history_attributes",
    "source_identity_regression_test",
}
FROZEN_EVIDENCE_FIELDS = {
    "server_version",
    "latest_temples_migration",
    "preflight_result",
    "production_state_class",
    "source_identity_state",
}
SQL_LABEL_FIELDS = {"identity", "canonical", "alternates"}
HISTORY_ATTRIBUTE_FIELDS = {
    "title",
    "history_type",
    "period_text",
    "event_date",
    "verification_status",
    "confidence",
}
URL_SQL_FIELDS = {"required_temples_migration"}

# Values each SQL family can express (both families are CLEAN_CREATE single-target imports).
SUPPORTED_BASE = {
    "expected_exact_before": 0,
    "expected_exact_after": 1,
    "expected_same_name_before": 0,
    "expected_same_name_after": 1,
    "expected_goriyaku_tag_links_after": 0,
    "expected_goriyaku_text": "",
}


class SpecError(ValueError):
    """The G7 SQL spec is invalid (fail closed)."""


# --- validation ---------------------------------------------------------------------------


def _fields(obj, expected: set[str], where: str) -> dict:
    if not isinstance(obj, dict):
        raise SpecError(f"{where}: must be an object")
    missing = sorted(expected - obj.keys())
    unknown = sorted(obj.keys() - expected)
    if missing:
        raise SpecError(f"{where}: missing field(s) {missing}")
    if unknown:
        raise SpecError(f"{where}: unknown field(s) {unknown}")
    return obj


def _text(value, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise SpecError(f"{where}: must be a string")
    if not allow_empty and not value.strip():
        raise SpecError(f"{where}: must not be empty")
    if value != value.strip():
        raise SpecError(f"{where}: must not have leading/trailing whitespace")
    if CONTROL_RE.search(value):
        raise SpecError(f"{where}: must not contain control characters")
    return value


def _count(value, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SpecError(f"{where}: must be a non-negative integer")
    return value


def _coordinate(value, where: str, limit: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpecError(f"{where}: must be a number")
    if not math.isfinite(value) or not -limit <= value <= limit:
        raise SpecError(f"{where}: out of range")


def _enum(value, allowed, where: str) -> None:
    if value not in allowed:
        raise SpecError(f"{where}: {value!r} is not one of {sorted(allowed)}")


def _unique_texts(values, where: str, *, pattern: re.Pattern | None = None) -> list[str]:
    if not isinstance(values, list):
        raise SpecError(f"{where}: must be a list")
    for index, value in enumerate(values):
        _text(value, f"{where}[{index}]")
        if pattern is not None and not pattern.fullmatch(value):
            raise SpecError(f"{where}[{index}]: invalid value {value!r}")
    if len(set(values)) != len(values):
        raise SpecError(f"{where}: duplicate values")
    return values


def _like_token(value, where: str) -> None:
    _text(value, where)
    if value != value.lower() or any(char in value for char in "%'\\"):
        raise SpecError(f"{where}: must be lowercase without % / quote / backslash")


def validate_spec(spec) -> dict:
    """Validate one candidate spec; return it unchanged. Raises SpecError."""
    if not isinstance(spec, dict):
        raise SpecError("spec: must be an object")
    if spec.get("schema_version") != SCHEMA_VERSION or isinstance(spec.get("schema_version"), bool):
        raise SpecError(f"spec.schema_version: must be {SCHEMA_VERSION}")
    source = spec.get("source_identity")
    if not isinstance(source, dict) or source.get("strategy") not in STRATEGIES:
        raise SpecError(
            f"spec.source_identity.strategy: must be one of {list(STRATEGIES)} "
            f"(got {source.get('strategy') if isinstance(source, dict) else source!r})"
        )
    strategy = source["strategy"]
    _fields(spec, COMMON_TOP | {STRATEGY_SECTION[strategy]}, "spec")

    candidate = _fields(spec["candidate"], CANDIDATE_FIELDS, "spec.candidate")
    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not CANDIDATE_ID_RE.fullmatch(candidate_id):
        raise SpecError(f"spec.candidate.candidate_id: {candidate_id!r} is not nsrc-NNNNNN")
    name = _text(candidate["name_jp"], "spec.candidate.name_jp")
    _text(candidate["address"], "spec.candidate.address")
    _coordinate(candidate["latitude"], "spec.candidate.latitude", 90.0)
    _coordinate(candidate["longitude"], "spec.candidate.longitude", 180.0)
    alternates = _unique_texts(candidate["alternate_names"], "spec.candidate.alternate_names")
    if name in alternates:
        raise SpecError("spec.candidate.alternate_names: must not repeat name_jp")

    pre = _fields(spec["production_pre_state"], set(TOTAL_KEYS), "spec.production_pre_state")
    post = _fields(spec["post_state"], set(TOTAL_KEYS), "spec.post_state")
    for key in TOTAL_KEYS:
        _count(pre[key], f"spec.production_pre_state.{key}")
        _count(post[key], f"spec.post_state.{key}")

    base = _fields(spec["base"], BASE_FIELDS, "spec.base")
    for key, supported in SUPPORTED_BASE.items():
        if key != "expected_goriyaku_text":
            _count(base[key], f"spec.base.{key}")
        if base[key] != supported or isinstance(base[key], bool):
            raise SpecError(f"spec.base.{key}: only {supported!r} is supported (CLEAN_CREATE)")

    _fields(source, SOURCE_FIELDS[strategy], "spec.source_identity")
    _enum(source["source_type"], SOURCE_TYPES, "spec.source_identity.source_type")

    knowledge = _fields(spec["knowledge"], KNOWLEDGE_FIELDS, "spec.knowledge")
    for key in (
        "expected_source_count",
        "expected_deity_count",
        "expected_history_count",
        "expected_source_fact_count",
        "expected_goriyaku_tag_links",
    ):
        _count(knowledge[key], f"spec.knowledge.{key}")
    if knowledge["expected_goriyaku_tag_links"] != 0:
        raise SpecError("spec.knowledge.expected_goriyaku_tag_links: only 0 is supported")
    deities = _unique_texts(knowledge["deity_names"], "spec.knowledge.deity_names")
    titles = _unique_texts(knowledge["history_titles"], "spec.knowledge.history_titles")
    keys = _unique_texts(
        knowledge["source_fact_stable_keys"],
        "spec.knowledge.source_fact_stable_keys",
        pattern=STABLE_KEY_RE,
    )
    for listed, key in (
        (deities, "expected_deity_count"),
        (titles, "expected_history_count"),
        (keys, "expected_source_fact_count"),
    ):
        if len(listed) != knowledge[key]:
            raise SpecError(f"spec.knowledge.{key}: {knowledge[key]} != {len(listed)} listed")
    if knowledge["expected_source_count"] < 1:
        raise SpecError("spec.knowledge.expected_source_count: must be at least 1")

    if strategy == NORMALIZED:
        accepted = _validate_normalized(spec, source, knowledge)
    else:
        accepted = _validate_url_patterns(spec, source, knowledge)

    want = {
        "shrine_total": base["expected_exact_after"] - base["expected_exact_before"],
        "source_total": knowledge["expected_source_count"] - accepted,
        "deity_total": knowledge["expected_deity_count"],
        "history_total": knowledge["expected_history_count"],
        "source_fact_total": knowledge["expected_source_fact_count"],
    }
    delta = {key: post[key] - pre[key] for key in TOTAL_KEYS}
    if delta != want:
        raise SpecError(f"spec.post_state: delta {delta} != expected {want}")
    return spec


def _validate_normalized(spec: dict, source: dict, knowledge: dict) -> int:
    where = "spec.source_identity"
    _text(source["normalized_url"], f"{where}.normalized_url")
    _text(source["publisher"], f"{where}.publisher", allow_empty=True)
    _enum(source["verification_status"], VERIFICATION_STATUSES, f"{where}.verification_status")
    _enum(source["confidence"], CONFIDENCES, f"{where}.confidence")
    _text(source["language"], f"{where}.language", allow_empty=True)
    _text(source["bibliography"], f"{where}.bibliography", allow_empty=True)
    for key in ("diagnostic_host_tokens", "diagnostic_path_tokens"):
        tokens = _unique_texts(source[key], f"{where}.{key}")
        if not tokens:
            raise SpecError(f"{where}.{key}: must not be empty")
        for index, token in enumerate(tokens):
            _like_token(token, f"{where}.{key}[{index}]")
    accepted = source["accepted_source_count"]
    if accepted not in (0, 1) or isinstance(accepted, bool):
        raise SpecError(f"{where}.accepted_source_count: must be 0 or 1")

    # The normalized_url_identity SQL family expresses exactly the nsrc-000002 Knowledge shape.
    shape = {
        "expected_source_count": 1,
        "expected_deity_count": 0,
        "expected_history_count": 1,
        "expected_source_fact_count": 0,
    }
    for key, value in shape.items():
        if knowledge[key] != value:
            raise SpecError(f"spec.knowledge.{key}: {NORMALIZED} SQL supports only {value}")

    section = _fields(
        spec["normalized_url_identity_sql"],
        NORMALIZED_SQL_FIELDS,
        "spec.normalized_url_identity_sql",
    )
    swhere = "spec.normalized_url_identity_sql"
    evidence = _fields(
        section["frozen_evidence"], FROZEN_EVIDENCE_FIELDS, f"{swhere}.frozen_evidence"
    )
    if not isinstance(evidence["server_version"], str) or not SERVER_VERSION_RE.fullmatch(
        evidence["server_version"]
    ):
        raise SpecError(f"{swhere}.frozen_evidence.server_version: invalid")
    if not isinstance(evidence["latest_temples_migration"], str) or not MIGRATION_RE.fullmatch(
        evidence["latest_temples_migration"]
    ):
        raise SpecError(f"{swhere}.frozen_evidence.latest_temples_migration: invalid")
    _enum(evidence["preflight_result"], {"PASS"}, f"{swhere}.frozen_evidence.preflight_result")
    _enum(
        evidence["production_state_class"],
        {"CLEAN_CREATE"},
        f"{swhere}.frozen_evidence.production_state_class",
    )
    state = "ABSENT" if accepted == 0 else "REUSABLE"
    if evidence["source_identity_state"] != state:
        raise SpecError(
            f"{swhere}.frozen_evidence.source_identity_state: must be {state} "
            f"for accepted_source_count={accepted}"
        )

    labels = _fields(section["sql_labels"], SQL_LABEL_FIELDS, f"{swhere}.sql_labels")
    for key in ("identity", "canonical"):
        if not isinstance(labels[key], str) or not LABEL_RE.fullmatch(labels[key]):
            raise SpecError(f"{swhere}.sql_labels.{key}: must match {LABEL_RE.pattern}")
    alternates = labels["alternates"]
    if not isinstance(alternates, dict) or list(alternates) != spec["candidate"]["alternate_names"]:
        raise SpecError(
            f"{swhere}.sql_labels.alternates: keys must equal candidate.alternate_names"
        )
    all_labels = [labels["canonical"], *alternates.values()]
    if not all(isinstance(label, str) and LABEL_RE.fullmatch(label) for label in all_labels):
        raise SpecError(f"{swhere}.sql_labels.alternates: invalid label")
    if len(set(all_labels)) != len(all_labels):
        raise SpecError(f"{swhere}.sql_labels: duplicate label")

    attributes = section["history_attributes"]
    if not isinstance(attributes, list) or len(attributes) != knowledge["expected_history_count"]:
        raise SpecError(f"{swhere}.history_attributes: one entry per history title")
    for index, attribute in enumerate(attributes):
        awhere = f"{swhere}.history_attributes[{index}]"
        _fields(attribute, HISTORY_ATTRIBUTE_FIELDS, awhere)
        if attribute["title"] != knowledge["history_titles"][index]:
            raise SpecError(f"{awhere}.title: must equal knowledge.history_titles[{index}]")
        _enum(attribute["history_type"], HISTORY_TYPES, f"{awhere}.history_type")
        _text(attribute["period_text"], f"{awhere}.period_text")
        if attribute["event_date"] is not None:
            raise SpecError(f"{awhere}.event_date: {NORMALIZED} SQL supports only null")
        _enum(
            attribute["verification_status"], VERIFICATION_STATUSES, f"{awhere}.verification_status"
        )
        _enum(attribute["confidence"], CONFIDENCES, f"{awhere}.confidence")

    test_path = section["source_identity_regression_test"]
    _text(test_path, f"{swhere}.source_identity_regression_test")
    if test_path.startswith("/") or ".." in Path(test_path).parts:
        raise SpecError(f"{swhere}.source_identity_regression_test: must be repo-relative")
    if not (REPO_ROOT / test_path).is_file():
        raise SpecError(f"{swhere}.source_identity_regression_test: {test_path} does not exist")
    return accepted


def _validate_url_patterns(spec: dict, source: dict, knowledge: dict) -> int:
    where = "spec.source_identity"
    patterns = _unique_texts(source["url_patterns"], f"{where}.url_patterns")
    if not patterns:
        raise SpecError(f"{where}.url_patterns: must not be empty")
    for index, pattern in enumerate(patterns):
        _like_token(pattern, f"{where}.url_patterns[{index}]")
    if spec["candidate"]["alternate_names"]:
        raise SpecError(
            f"spec.candidate.alternate_names: {URL_PATTERNS} SQL has no alternate checks"
        )
    if not knowledge["source_fact_stable_keys"]:
        raise SpecError(f"spec.knowledge.source_fact_stable_keys: {URL_PATTERNS} SQL needs >= 1")
    section = _fields(spec["url_pattern_set_sql"], URL_SQL_FIELDS, "spec.url_pattern_set_sql")
    migration = section["required_temples_migration"]
    if not isinstance(migration, str) or not MIGRATION_RE.fullmatch(migration):
        raise SpecError("spec.url_pattern_set_sql.required_temples_migration: invalid")
    return 0


def load_spec(path: Path) -> dict:
    return validate_spec(json.loads(Path(path).read_text(encoding="utf-8")))


def load_specs(paths) -> list[dict]:
    specs = [load_spec(path) for path in paths]
    ids = [spec["candidate"]["candidate_id"] for spec in specs]
    duplicated = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicated:
        raise SpecError(f"duplicate candidate spec {duplicated}")
    return specs


# --- rendering ----------------------------------------------------------------------------

_MARKER_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _number(value: float) -> str:
    return repr(float(value))


def _render(template: str, values: dict[str, str]) -> str:
    missing = sorted(set(_MARKER_RE.findall(template)) - values.keys())
    if missing:
        raise SpecError(f"template placeholders without value: {missing}")
    return _MARKER_RE.sub(lambda match: values[match.group(1)], template)


def _template(strategy: str, name: str) -> str:
    return (TEMPLATE_DIR / strategy / f"{name}.sql.tmpl").read_text(encoding="utf-8")


def _normalized_values(spec: dict) -> dict[str, dict[str, str]]:
    candidate = spec["candidate"]
    source = spec["source_identity"]
    pre = spec["production_pre_state"]
    section = spec["normalized_url_identity_sql"]
    evidence = section["frozen_evidence"]
    labels = section["sql_labels"]
    history = section["history_attributes"][0]
    names = [candidate["name_jp"], *candidate["alternate_names"]]
    label_of = {candidate["name_jp"]: labels["canonical"], **labels["alternates"]}
    host_patterns = [f"%{token}%" for token in source["diagnostic_host_tokens"]]
    path_pattern = "%" + "%".join(source["diagnostic_path_tokens"]) + "%"
    patterns = [*host_patterns, path_pattern]

    def guard(canonical_count: str) -> str:
        return "".join(
            f"  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = {_sql(name)})"
            f" = {canonical_count if name == candidate['name_jp'] else 0}\n"
            for name in names
        )

    values = {
        "candidate_id": candidate["candidate_id"],
        "candidate_slug": candidate["candidate_id"].replace("-", "_"),
        "official_name": candidate["name_jp"],
        "official_name_sql": _sql(candidate["name_jp"]),
        "official_address_sql": _sql(candidate["address"]),
        "latitude": _number(candidate["latitude"]),
        "longitude": _number(candidate["longitude"]),
        "source_identity_regression_test": section["source_identity_regression_test"],
        "source_type": source["source_type"],
        "source_type_sql": _sql(source["source_type"]),
        "normalized_url": source["normalized_url"],
        "normalized_url_sql": _sql(source["normalized_url"]),
        "source_publisher_sql": _sql(source["publisher"]),
        "source_verification_status_sql": _sql(source["verification_status"]),
        "source_confidence_sql": _sql(source["confidence"]),
        "source_bibliography_sql": _sql(source["bibliography"]),
        "source_language_sql": _sql(source["language"]),
        "lookalike_raw_predicate": "("
        + " AND ".join(f"lower(url) LIKE {_sql(p)}" for p in patterns)
        + ")",
        "lookalike_normalized_predicate": "("
        + "\n         AND ".join(
            f"lower(COALESCE(normalized_url, '')) LIKE {_sql(p)}" for p in patterns
        )
        + ")",
        "history_type_sql": _sql(history["history_type"]),
        "history_title_sql": _sql(history["title"]),
        "history_period_text_sql": _sql(history["period_text"]),
        "history_verification_status_sql": _sql(history["verification_status"]),
        "history_confidence_sql": _sql(history["confidence"]),
        "frozen_shrine_total": str(pre["shrine_total"]),
        "frozen_source_total": str(pre["source_total"]),
        "frozen_deity_total": str(pre["deity_total"]),
        "frozen_history_total": str(pre["history_total"]),
        "frozen_source_fact_total": str(pre["source_fact_total"]),
        "frozen_accepted_source_count": str(source["accepted_source_count"]),
        "frozen_server_version": evidence["server_version"],
        "frozen_latest_temples_migration": evidence["latest_temples_migration"],
        "frozen_preflight_result": evidence["preflight_result"],
        "frozen_production_state_class": evidence["production_state_class"],
        "frozen_source_identity_state": evidence["source_identity_state"],
        "same_name_comment": " / ".join(f"same-name {name}" for name in names),
        "name_variants_in_list_sql": ", ".join(_sql(name) for name in names),
        "preflight_same_name_count_columns": "".join(
            f"  COUNT(*) FILTER (WHERE name_jp = {_sql(name)})"
            f" AS same_name_{labels['identity']}_{label_of[name]}_count,\n"
            for name in names
        ),
        "counts_same_name_columns": "".join(
            f"    (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = {_sql(name)})"
            f" AS same_name_{label_of[name]},\n"
            for name in names
        ),
        "conflict_same_name_predicates": f"      OR same_name_{labels['canonical']} <> target_exact\n"
        + "".join(f"      OR same_name_{label_of[name]} > 0\n" for name in names[1:]),
    }
    values["source_identity_block"] = _render(
        _template(NORMALIZED, "source_identity_block"), values
    )
    base = spec["base"]
    return {
        "preflight": values,
        "pre_base_guard": {
            **values,
            "same_name_guard_predicates": guard(str(base["expected_same_name_before"])),
        },
        "post_base_guard": {
            **values,
            "same_name_guard_predicates": guard(str(base["expected_same_name_after"])),
        },
        "post_knowledge_verification": values,
    }


def _url_pattern_values(spec: dict) -> dict[str, dict[str, str]]:
    candidate = spec["candidate"]
    source = spec["source_identity"]
    pre = spec["production_pre_state"]
    base = spec["base"]
    keys = spec["knowledge"]["source_fact_stable_keys"]
    migration = spec["url_pattern_set_sql"]["required_temples_migration"]

    def patterns(column: str, indent: str) -> str:
        return f"\n{indent}OR ".join(
            f"lower({column}) LIKE {_sql('%' + pattern + '%')}"
            for pattern in source["url_patterns"]
        )

    def stable_keys(indent: str) -> str:
        return ",\n".join(f"{indent}{_sql(key)}" for key in keys)

    values = {
        "candidate_id": candidate["candidate_id"],
        "name_sql": _sql(candidate["name_jp"]),
        "address_sql": _sql(candidate["address"]),
        "latitude": _number(candidate["latitude"]),
        "longitude": _number(candidate["longitude"]),
        "source_type_sql": _sql(source["source_type"]),
        "url_patterns_s_url_4": patterns("s.url", "    "),
        "url_patterns_url_4": patterns("url", "    "),
        "stable_keys_2": stable_keys("  "),
        "stable_keys_4": stable_keys("    "),
        "required_temples_migration_sql": _sql(migration),
        "required_temples_migration_number": MIGRATION_RE.fullmatch(migration).group(1),
        "pre_shrine_total": str(pre["shrine_total"]),
        "pre_source_total": str(pre["source_total"]),
        "pre_deity_total": str(pre["deity_total"]),
        "pre_history_total": str(pre["history_total"]),
        "pre_source_fact_total": str(pre["source_fact_total"]),
        "post_base_shrine_total": str(
            pre["shrine_total"] + base["expected_exact_after"] - base["expected_exact_before"]
        ),
        "expected_exact_before": str(base["expected_exact_before"]),
        "expected_exact_after": str(base["expected_exact_after"]),
        "expected_same_name_before": str(base["expected_same_name_before"]),
        "expected_same_name_after": str(base["expected_same_name_after"]),
        "expected_goriyaku_tag_links_after": str(base["expected_goriyaku_tag_links_after"]),
        "goriyaku_text_sql": _sql(base["expected_goriyaku_text"]),
    }
    return {kind: values for kind, _ in ARTIFACTS}


def generate_sql(spec: dict) -> list[tuple[str, str]]:
    """Return [(file_name, sql_text)] in the fixed ARTIFACTS order."""
    validate_spec(spec)
    strategy = spec["source_identity"]["strategy"]
    per_kind = _normalized_values(spec) if strategy == NORMALIZED else _url_pattern_values(spec)
    artifacts = []
    for kind, file_name in ARTIFACTS:
        text = _render(_template(strategy, kind), per_kind[kind])
        ok, reason = is_readonly_sql(text)
        if not ok:
            raise SpecError(f"generated {file_name} is not read-only: {reason}")
        artifacts.append((file_name, text))
    return artifacts


def write_sql(spec: dict, output_dir: Path, *, overwrite: bool = False) -> list[tuple[str, str]]:
    """Write the four SQL files into output_dir; existing files need overwrite=True."""
    artifacts = generate_sql(spec)
    output_dir = Path(output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise SpecError(f"output path {output_dir} is not a directory")
    existing = [name for name, _ in artifacts if (output_dir / name).exists()]
    if existing and not overwrite:
        raise SpecError(f"refusing to overwrite {existing} (use --overwrite)")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, text in artifacts:
        (output_dir / name).write_text(text, encoding="utf-8")
    return artifacts


# --- CLI ----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate", help="validate G7 SQL specs")
    p_validate.add_argument("specs", nargs="+")
    p_generate = sub.add_parser("generate", help="write the four G7 SQL artifacts")
    p_generate.add_argument("--spec", required=True)
    p_generate.add_argument("--output-dir", required=True)
    p_generate.add_argument(
        "--overwrite", action="store_true", help="replace the four generated files if present"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            for spec in load_specs([Path(path) for path in args.specs]):
                print(
                    f"VALID {spec['candidate']['candidate_id']} "
                    f"{spec['source_identity']['strategy']}"
                )
            return 0
        artifacts = write_sql(
            load_spec(Path(args.spec)), Path(args.output_dir), overwrite=args.overwrite
        )
    except (SpecError, json.JSONDecodeError, OSError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    for name, text in artifacts:
        print(f"{name} sha256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    print("PRODUCTION_CONNECTION=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
