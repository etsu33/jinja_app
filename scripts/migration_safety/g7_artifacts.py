#!/usr/bin/env python3
"""Shrine Expansion G7 artifact generator (read-only, no DB access).

Generates the G7 Production Import artifacts of one candidate from an explicit,
validated input spec (``g7_candidate_specs.json``):

    1. <slug>_g7_preflight.sql
    2. <slug>_g7_pre_base_guard.sql
    3. <slug>_g7_post_base_guard.sql
    4. <slug>_g7_post_knowledge_verification.sql
    5. <slug>_g7_base_subset.json   (target-only Base Seed subset)
    6. <slug>_g7_runtime_qa.py

The templates in ``g7_templates/`` are derived from the nsrc-000002 G7 artifacts,
which are the golden case: generating nsrc-000002 reproduces the committed files
byte for byte. Only the ``HISTORY_ONLY_SINGLE_SOURCE`` Knowledge profile (the
validated nsrc-000002 shape) is supported; any other shape fails closed instead
of inventing gate semantics.

Every value comes from the spec. Nothing is inferred from the candidate name.
This module opens no database connection, reads no credentials and executes
no SQL. Generated SQL is SELECT-only.

Usage:
    g7_artifacts.py validate [--spec PATH]
    g7_artifacts.py generate --candidate ID --output-dir DIR [--spec PATH] [--base-seed PATH]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from guard import is_readonly_sql, is_safe_dump_path  # noqa: E402

SPEC_PATH = SCRIPT_DIR / "g7_candidate_specs.json"
TEMPLATE_DIR = SCRIPT_DIR / "g7_templates"
BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"

SPEC_SCHEMA_VERSION = 1
KNOWLEDGE_PROFILE = "HISTORY_ONLY_SINGLE_SOURCE"

# Copies of the model choices (temples.models). A backend test keeps them equal.
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
MIGRATION_RE = re.compile(r"^[0-9]{4}_[a-z0-9_]+$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f  ]")

ARTIFACT_KINDS = (
    ("preflight", "{slug}_g7_preflight.sql"),
    ("pre_base_guard", "{slug}_g7_pre_base_guard.sql"),
    ("post_base_guard", "{slug}_g7_post_base_guard.sql"),
    ("post_knowledge_verification", "{slug}_g7_post_knowledge_verification.sql"),
    ("base_subset", "{slug}_g7_base_subset.json"),
    ("runtime_qa", "{slug}_g7_runtime_qa.py"),
)
SQL_KINDS = ("preflight", "pre_base_guard", "post_base_guard", "post_knowledge_verification")

_TOP_FIELDS = {"schema_version", "purpose", "candidates"}
_CANDIDATE_FIELDS = {
    "candidate_id",
    "knowledge_profile",
    "identity",
    "base_seed_row",
    "frozen_pre_state",
    "expected_delta",
    "knowledge",
    "runtime_qa",
    "source_identity_regression_test",
}
_IDENTITY_FIELDS = {"official_name", "official_address", "identity_label", "name_variants"}
_VARIANT_FIELDS = {"name_jp", "label"}
_BASE_ROW_FIELDS = {
    "name_jp",
    "address",
    "latitude",
    "longitude",
    "goriyaku",
    "kyusei",
    "astro_elements",
    "location",
}
_FROZEN_FIELDS = {
    "shrine_total",
    "source_total",
    "deity_total",
    "history_total",
    "source_fact_total",
    "accepted_source_count",
    "server_version",
    "latest_temples_migration",
    "preflight_result",
    "production_state_class",
    "source_identity_state",
}
_DELTA_FIELDS = {"shrine", "source", "deity", "history", "source_fact"}
_KNOWLEDGE_FIELDS = {"source", "deities", "histories", "source_facts"}
_SOURCE_FIELDS = {
    "source_type",
    "url",
    "normalized_url",
    "publisher",
    "verification_status",
    "confidence",
    "bibliography",
    "language",
    "lookalike_like_patterns",
}
_HISTORY_FIELDS = {
    "history_type",
    "title",
    "content",
    "period_text",
    "event_date",
    "verification_status",
    "confidence",
}
_RUNTIME_QA_FIELDS = {
    "unsupported_deity_names",
    "expect_history_background_sentence",
    "compass_origin",
}
_ORIGIN_FIELDS = {"lat", "lng"}


class SpecError(ValueError):
    """The G7 input spec is invalid (fail closed)."""


class SubsetError(ValueError):
    """Target-only subset extraction failed (fail closed)."""


# --- spec validation ----------------------------------------------------------------------


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
        raise SpecError(f"{where}: must not be blank")
    if value != value.strip():
        raise SpecError(f"{where}: must not have leading/trailing whitespace")
    if CONTROL_RE.search(value):
        raise SpecError(f"{where}: must not contain control characters")
    return value


def _count(value, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SpecError(f"{where}: must be a non-negative integer")
    return value


def _coordinate(value, where: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpecError(f"{where}: must be a number")
    if not math.isfinite(value) or not low <= value <= high:
        raise SpecError(f"{where}: out of range")
    return float(value)


def _enum(value, allowed, where: str) -> str:
    if value not in allowed:
        raise SpecError(f"{where}: {value!r} is not one of {sorted(allowed)}")
    return value


def _validate_candidate(candidate, where: str) -> None:
    _fields(candidate, _CANDIDATE_FIELDS, where)
    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not CANDIDATE_ID_RE.fullmatch(candidate_id):
        raise SpecError(f"{where}.candidate_id: {candidate_id!r} is not nsrc-NNNNNN")
    where = f"{where}[{candidate_id}]"
    if candidate["knowledge_profile"] != KNOWLEDGE_PROFILE:
        raise SpecError(
            f"{where}.knowledge_profile: only {KNOWLEDGE_PROFILE} is supported "
            f"(got {candidate['knowledge_profile']!r})"
        )

    identity = _fields(candidate["identity"], _IDENTITY_FIELDS, f"{where}.identity")
    name = _text(identity["official_name"], f"{where}.identity.official_name")
    address = _text(identity["official_address"], f"{where}.identity.official_address")
    if not isinstance(identity["identity_label"], str) or not LABEL_RE.fullmatch(
        identity["identity_label"]
    ):
        raise SpecError(f"{where}.identity.identity_label: must match {LABEL_RE.pattern}")
    variants = identity["name_variants"]
    if not isinstance(variants, list) or not variants:
        raise SpecError(f"{where}.identity.name_variants: must be a non-empty list")
    for index, variant in enumerate(variants):
        _fields(variant, _VARIANT_FIELDS, f"{where}.identity.name_variants[{index}]")
        _text(variant["name_jp"], f"{where}.identity.name_variants[{index}].name_jp")
        if not isinstance(variant["label"], str) or not LABEL_RE.fullmatch(variant["label"]):
            raise SpecError(f"{where}.identity.name_variants[{index}].label: invalid label")
    if variants[0]["name_jp"] != name:
        raise SpecError(f"{where}.identity.name_variants[0]: must be the official_name")
    if len({v["name_jp"] for v in variants}) != len(variants):
        raise SpecError(f"{where}.identity.name_variants: duplicate name_jp")
    if len({v["label"] for v in variants}) != len(variants):
        raise SpecError(f"{where}.identity.name_variants: duplicate label")

    row = _fields(candidate["base_seed_row"], _BASE_ROW_FIELDS, f"{where}.base_seed_row")
    if row["name_jp"] != name or row["address"] != address:
        raise SpecError(f"{where}.base_seed_row: identity differs from identity.official_*")
    _coordinate(row["latitude"], f"{where}.base_seed_row.latitude", -90.0, 90.0)
    _coordinate(row["longitude"], f"{where}.base_seed_row.longitude", -180.0, 180.0)
    if row["location"] != {"lat": row["latitude"], "lng": row["longitude"]}:
        raise SpecError(f"{where}.base_seed_row.location: must mirror latitude/longitude")
    if row["goriyaku"] != "":
        raise SpecError(f"{where}.base_seed_row.goriyaku: profile requires ''")

    frozen = _fields(candidate["frozen_pre_state"], _FROZEN_FIELDS, f"{where}.frozen_pre_state")
    for key in (
        "shrine_total",
        "source_total",
        "deity_total",
        "history_total",
        "source_fact_total",
    ):
        _count(frozen[key], f"{where}.frozen_pre_state.{key}")
    accepted = frozen["accepted_source_count"]
    if accepted not in (0, 1) or isinstance(accepted, bool):
        raise SpecError(f"{where}.frozen_pre_state.accepted_source_count: must be 0 or 1")
    if not isinstance(frozen["server_version"], str) or not SERVER_VERSION_RE.fullmatch(
        frozen["server_version"]
    ):
        raise SpecError(f"{where}.frozen_pre_state.server_version: invalid")
    if not isinstance(frozen["latest_temples_migration"], str) or not MIGRATION_RE.fullmatch(
        frozen["latest_temples_migration"]
    ):
        raise SpecError(f"{where}.frozen_pre_state.latest_temples_migration: invalid")
    _enum(frozen["preflight_result"], {"PASS"}, f"{where}.frozen_pre_state.preflight_result")
    _enum(
        frozen["production_state_class"],
        {"CLEAN_CREATE"},
        f"{where}.frozen_pre_state.production_state_class",
    )
    expected_state = "ABSENT" if accepted == 0 else "REUSABLE"
    if frozen["source_identity_state"] != expected_state:
        raise SpecError(
            f"{where}.frozen_pre_state.source_identity_state: must be {expected_state} "
            f"for accepted_source_count={accepted}"
        )

    knowledge = _fields(candidate["knowledge"], _KNOWLEDGE_FIELDS, f"{where}.knowledge")
    source = _fields(knowledge["source"], _SOURCE_FIELDS, f"{where}.knowledge.source")
    _enum(source["source_type"], SOURCE_TYPES, f"{where}.knowledge.source.source_type")
    _text(source["url"], f"{where}.knowledge.source.url")
    _text(source["normalized_url"], f"{where}.knowledge.source.normalized_url")
    _text(source["publisher"], f"{where}.knowledge.source.publisher", allow_empty=True)
    _enum(
        source["verification_status"],
        VERIFICATION_STATUSES,
        f"{where}.knowledge.source.verification_status",
    )
    _enum(source["confidence"], CONFIDENCES, f"{where}.knowledge.source.confidence")
    _text(source["bibliography"], f"{where}.knowledge.source.bibliography", allow_empty=True)
    _text(source["language"], f"{where}.knowledge.source.language", allow_empty=True)
    patterns = source["lookalike_like_patterns"]
    if not isinstance(patterns, list) or not patterns:
        raise SpecError(f"{where}.knowledge.source.lookalike_like_patterns: non-empty list")
    for index, pattern in enumerate(patterns):
        pwhere = f"{where}.knowledge.source.lookalike_like_patterns[{index}]"
        _text(pattern, pwhere)
        if pattern != pattern.lower() or "\\" in pattern or "'" in pattern or "%" not in pattern:
            raise SpecError(f"{pwhere}: must be a lowercase LIKE pattern with % and no quote")
    if knowledge["deities"] != []:
        raise SpecError(f"{where}.knowledge.deities: profile requires []")
    if knowledge["source_facts"] != []:
        raise SpecError(f"{where}.knowledge.source_facts: profile requires []")
    histories = knowledge["histories"]
    if not isinstance(histories, list) or len(histories) != 1:
        raise SpecError(f"{where}.knowledge.histories: profile requires exactly 1 history")
    history = _fields(histories[0], _HISTORY_FIELDS, f"{where}.knowledge.histories[0]")
    _enum(history["history_type"], HISTORY_TYPES, f"{where}.knowledge.histories[0].history_type")
    _text(history["title"], f"{where}.knowledge.histories[0].title")
    _text(history["content"], f"{where}.knowledge.histories[0].content")
    _text(history["period_text"], f"{where}.knowledge.histories[0].period_text")
    if history["event_date"] is not None:
        raise SpecError(f"{where}.knowledge.histories[0].event_date: profile requires null")
    _enum(
        history["verification_status"],
        VERIFICATION_STATUSES,
        f"{where}.knowledge.histories[0].verification_status",
    )
    _enum(history["confidence"], CONFIDENCES, f"{where}.knowledge.histories[0].confidence")

    delta = _fields(candidate["expected_delta"], _DELTA_FIELDS, f"{where}.expected_delta")
    for key in _DELTA_FIELDS:
        _count(delta[key], f"{where}.expected_delta.{key}")
    want_delta = {
        "shrine": 1,
        "source": 1 - accepted,
        "deity": len(knowledge["deities"]),
        "history": len(histories),
        "source_fact": len(knowledge["source_facts"]),
    }
    if delta != want_delta:
        raise SpecError(f"{where}.expected_delta: {delta} != {want_delta} (from knowledge/frozen)")

    qa = _fields(candidate["runtime_qa"], _RUNTIME_QA_FIELDS, f"{where}.runtime_qa")
    names = qa["unsupported_deity_names"]
    if not isinstance(names, list):
        raise SpecError(f"{where}.runtime_qa.unsupported_deity_names: must be a list")
    for index, deity in enumerate(names):
        _text(deity, f"{where}.runtime_qa.unsupported_deity_names[{index}]")
    if not isinstance(qa["expect_history_background_sentence"], bool):
        raise SpecError(f"{where}.runtime_qa.expect_history_background_sentence: must be bool")
    origin = _fields(qa["compass_origin"], _ORIGIN_FIELDS, f"{where}.runtime_qa.compass_origin")
    _coordinate(origin["lat"], f"{where}.runtime_qa.compass_origin.lat", -90.0, 90.0)
    _coordinate(origin["lng"], f"{where}.runtime_qa.compass_origin.lng", -180.0, 180.0)

    test_path = candidate["source_identity_regression_test"]
    _text(test_path, f"{where}.source_identity_regression_test")
    if test_path.startswith("/") or ".." in Path(test_path).parts:
        raise SpecError(f"{where}.source_identity_regression_test: must be repo-relative")
    if not (REPO_ROOT / test_path).is_file():
        raise SpecError(f"{where}.source_identity_regression_test: {test_path} does not exist")


def validate_spec(spec) -> dict:
    """Validate the whole spec document; return it unchanged. Raises SpecError."""
    _fields(spec, _TOP_FIELDS, "spec")
    if spec["schema_version"] != SPEC_SCHEMA_VERSION or isinstance(spec["schema_version"], bool):
        raise SpecError(f"spec.schema_version: must be {SPEC_SCHEMA_VERSION}")
    _text(spec["purpose"], "spec.purpose")
    candidates = spec["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise SpecError("spec.candidates: must be a non-empty list")
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        _validate_candidate(candidate, f"spec.candidates[{index}]")
        if candidate["candidate_id"] in seen:
            raise SpecError(f"spec.candidates: duplicate candidate_id {candidate['candidate_id']}")
        seen.add(candidate["candidate_id"])
    return spec


def load_spec(path: Path = SPEC_PATH) -> dict:
    return validate_spec(json.loads(Path(path).read_text(encoding="utf-8")))


def candidate_spec(spec: dict, candidate_id: str) -> dict:
    matches = [c for c in spec["candidates"] if c["candidate_id"] == candidate_id]
    if len(matches) != 1:
        raise SpecError(
            f"candidate {candidate_id!r}: expected exactly 1 spec, found {len(matches)}"
        )
    return matches[0]


# --- target-only subset -------------------------------------------------------------------


def extract_target_subset(
    base_rows: list, *, name_jp: str, address: str, expected_row: dict
) -> list[dict]:
    """Return exactly the one Base Seed row with this exact identity (no normalization).

    0 or >1 exact matches, or a row that differs from ``expected_row``, fail closed.
    The returned row is a copy of the source row with its data and key order unchanged.
    """
    if not isinstance(base_rows, list):
        raise SubsetError("BLOCKED: Base Seed must be a JSON list")
    subset = [
        row
        for row in base_rows
        if isinstance(row, dict) and row.get("name_jp") == name_jp and row.get("address") == address
    ]
    if len(subset) != 1:
        raise SubsetError(f"BLOCKED: expected exactly 1 target row, found {len(subset)}")
    if subset[0] != expected_row:
        raise SubsetError("BLOCKED: target Base Seed row differs from the frozen G7 row")
    return [copy.deepcopy(subset[0])]


def render_subset(subset: list[dict]) -> str:
    if not isinstance(subset, list) or len(subset) != 1:
        raise SubsetError("BLOCKED: a G7 subset must contain exactly 1 row")
    return json.dumps(subset, ensure_ascii=False, indent=2) + "\n"


# --- rendering ----------------------------------------------------------------------------

_MARKER_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _py(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _number(value: float) -> str:
    return repr(float(value))


def _render(template: str, values: dict[str, str]) -> str:
    used = set(_MARKER_RE.findall(template))
    missing = sorted(used - values.keys())
    if missing:
        raise SpecError(f"template placeholders without value: {missing}")
    return _MARKER_RE.sub(lambda m: values[m.group(1)], template)


def _template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _h1_content_assignment(content: str) -> str:
    sentences = re.findall(r"[^。]*。|[^。]+$", content)
    if len(sentences) <= 1:
        return f"H1_CONTENT = {_py(content)}"
    lines = "".join(f"    {_py(sentence)}\n" for sentence in sentences)
    return f"H1_CONTENT = (\n{lines})"


def _tuple_py(values: list[str]) -> str:
    if not values:
        return "()"
    if len(values) == 1:
        return f"({_py(values[0])},)"
    return "(" + ", ".join(_py(value) for value in values) + ")"


def _values(candidate: dict) -> dict[str, str]:
    identity = candidate["identity"]
    variants = identity["name_variants"]
    frozen = candidate["frozen_pre_state"]
    source = candidate["knowledge"]["source"]
    history = candidate["knowledge"]["histories"][0]
    row = candidate["base_seed_row"]
    qa = candidate["runtime_qa"]
    slug = candidate["candidate_id"].replace("-", "_")
    canonical, others = variants[0], variants[1:]
    patterns = source["lookalike_like_patterns"]

    values = {
        "candidate_id": candidate["candidate_id"],
        "candidate_slug": slug,
        "official_name": identity["official_name"],
        "official_name_sql": _sql(identity["official_name"]),
        "official_address_sql": _sql(identity["official_address"]),
        "official_name_py": _py(identity["official_name"]),
        "official_address_py": _py(identity["official_address"]),
        "latitude": _number(row["latitude"]),
        "longitude": _number(row["longitude"]),
        "source_identity_regression_test": candidate["source_identity_regression_test"],
        "source_type": source["source_type"],
        "source_type_sql": _sql(source["source_type"]),
        "source_type_py": _py(source["source_type"]),
        "source_url_py": _py(source["url"]),
        "normalized_url": source["normalized_url"],
        "normalized_url_sql": _sql(source["normalized_url"]),
        "source_publisher_sql": _sql(source["publisher"]),
        "source_verification_status_sql": _sql(source["verification_status"]),
        "source_verification_status_py": _py(source["verification_status"]),
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
        "history_type_py": _py(history["history_type"]),
        "history_title_py": _py(history["title"]),
        "history_verification_status_py": _py(history["verification_status"]),
        "history_confidence_py": _py(history["confidence"]),
        "h1_content_assignment": _h1_content_assignment(history["content"]),
        "unsupported_deity_names_py": _tuple_py(qa["unsupported_deity_names"]),
        "qa_origin_lat": _number(qa["compass_origin"]["lat"]),
        "qa_origin_lng": _number(qa["compass_origin"]["lng"]),
        "reason_background_assertion": (
            "        assert f\"{SHRINE_NAME}には、{H1_CONTENT.rstrip('。')}という背景があります。\""
            " in reason_text\n"
            if qa["expect_history_background_sentence"]
            else ""
        ),
        "frozen_shrine_total": str(frozen["shrine_total"]),
        "frozen_source_total": str(frozen["source_total"]),
        "frozen_deity_total": str(frozen["deity_total"]),
        "frozen_history_total": str(frozen["history_total"]),
        "frozen_source_fact_total": str(frozen["source_fact_total"]),
        "frozen_accepted_source_count": str(frozen["accepted_source_count"]),
        "frozen_server_version": frozen["server_version"],
        "frozen_latest_temples_migration": frozen["latest_temples_migration"],
        "frozen_preflight_result": frozen["preflight_result"],
        "frozen_production_state_class": frozen["production_state_class"],
        "frozen_source_identity_state": frozen["source_identity_state"],
        "same_name_comment": " / ".join(f"same-name {v['name_jp']}" for v in variants),
        "name_variants_in_list_sql": ", ".join(_sql(v["name_jp"]) for v in variants),
        "preflight_same_name_count_columns": "".join(
            f"  COUNT(*) FILTER (WHERE name_jp = {_sql(v['name_jp'])})"
            f" AS same_name_{identity['identity_label']}_{v['label']}_count,\n"
            for v in variants
        ),
        "counts_same_name_columns": "".join(
            f"    (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = {_sql(v['name_jp'])})"
            f" AS same_name_{v['label']},\n"
            for v in variants
        ),
        "conflict_same_name_predicates": f"      OR same_name_{canonical['label']} <> target_exact\n"
        + "".join(f"      OR same_name_{v['label']} > 0\n" for v in others),
    }
    values["source_identity_block"] = _render(_template("source_identity_block.sql.tmpl"), values)
    return values


def generate_artifacts(candidate: dict, base_rows: list) -> dict[str, tuple[str, str]]:
    """Return {kind: (file_name, text)} in the fixed ARTIFACT_KINDS order."""
    _validate_candidate(candidate, "candidate")
    values = _values(candidate)
    slug = values["candidate_slug"]
    texts = {
        "preflight": _render(_template("preflight.sql.tmpl"), values),
        "pre_base_guard": _render(
            _template("pre_base_guard.sql.tmpl"),
            {**values, "same_name_guard_predicates": _guard(candidate, 0)},
        ),
        "post_base_guard": _render(
            _template("post_base_guard.sql.tmpl"),
            {**values, "same_name_guard_predicates": _guard(candidate, 1)},
        ),
        "post_knowledge_verification": _render(
            _template("post_knowledge_verification.sql.tmpl"), values
        ),
        "base_subset": render_subset(
            extract_target_subset(
                base_rows,
                name_jp=candidate["identity"]["official_name"],
                address=candidate["identity"]["official_address"],
                expected_row=candidate["base_seed_row"],
            )
        ),
        "runtime_qa": _render(_template("runtime_qa.py.tmpl"), values),
    }
    for kind in SQL_KINDS:
        ok, reason = is_readonly_sql(texts[kind])
        if not ok:
            raise SpecError(f"generated {kind} SQL is not read-only: {reason}")
    return {kind: (pattern.format(slug=slug), texts[kind]) for kind, pattern in ARTIFACT_KINDS}


def _guard(candidate: dict, canonical_count: int) -> str:
    variants = candidate["identity"]["name_variants"]
    lines = [
        f"  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = {_sql(variants[0]['name_jp'])})"
        f" = {canonical_count}\n"
    ]
    lines += [
        f"  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = {_sql(v['name_jp'])}) = 0\n"
        for v in variants[1:]
    ]
    return "".join(lines)


# --- CLI ----------------------------------------------------------------------------------


def _cmd_validate(args) -> int:
    spec = load_spec(Path(args.spec))
    for candidate in spec["candidates"]:
        print(f"VALID {candidate['candidate_id']} {candidate['knowledge_profile']}")
    return 0


def _cmd_generate(args) -> int:
    output_dir = Path(args.output_dir)
    ok, reason = is_safe_dump_path(str(output_dir), str(REPO_ROOT))
    if not ok:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 1
    if output_dir.exists() and any(output_dir.iterdir()):
        print("BLOCKED: output directory must be new or empty", file=sys.stderr)
        return 1
    candidate = candidate_spec(load_spec(Path(args.spec)), args.candidate)
    base_rows = json.loads(Path(args.base_seed).read_text(encoding="utf-8"))
    artifacts = generate_artifacts(candidate, base_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    for kind, (name, text) in artifacts.items():
        (output_dir / name).write_text(text, encoding="utf-8")
        print(f"{kind} {name} sha256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    print("PRODUCTION_CONNECTION=NONE")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate", help="validate the G7 input spec")
    p_validate.add_argument("--spec", default=str(SPEC_PATH))
    p_generate = sub.add_parser("generate", help="generate the G7 artifacts of one candidate")
    p_generate.add_argument("--candidate", required=True)
    p_generate.add_argument("--output-dir", required=True)
    p_generate.add_argument("--spec", default=str(SPEC_PATH))
    p_generate.add_argument("--base-seed", default=str(BASE_SEED_PATH))
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _cmd_validate(args)
        return _cmd_generate(args)
    except (SpecError, SubsetError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
