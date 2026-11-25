#!/usr/bin/env python3
"""Shrine Expansion G7 Runtime QA generator (no DB access, performs no QA itself).

Generates one candidate-specific read-only Runtime QA script from a validated G7
spec (``g7_specs/<candidate>.json``). ``runtime_qa.family`` selects the template
family in ``g7_templates/runtime_qa/``; the two families are derived from the
historical scripts and are not merged into one inferred rule:

    history_only_v1   nsrc-000002: Deity 0 / History 1, normalize_source_url()
                      Source comparison, background sentence in the reason text
    deity_history_v1  nsrc-000004: exact Deity / History title sets, per-row
                      source verification, deities in the reason text

Every generated script keeps ``transaction.atomic()`` + ``SET TRANSACTION READ
ONLY`` and the four G6 runtime surfaces (Shrine Detail, Concierge candidate path,
Recommendation Reason, Compass distance / direction). Every expectation comes from
the spec; nothing is inferred from the candidate id or shrine name.

Usage:
    g7_runtime_qa_generator.py --spec <G7_SPEC> --output <OUTPUT_PATH> [--overwrite]
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from g7_sql_generator import (  # noqa: E402
    RUNTIME_DEITY_HISTORY,
    RUNTIME_HISTORY_ONLY,
    TEMPLATE_DIR,
    SpecError,
    _number,
    _render,
    load_spec,
    validate_spec,
)

RUNTIME_TEMPLATE_DIR = TEMPLATE_DIR / "runtime_qa"


def _py(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _h1_content_assignment(content: str) -> str:
    # Presentation only: one string literal per sentence ending in 。 when there are several.
    sentences = re.findall(r"[^。]*。|[^。]+$", content)
    if len(sentences) <= 1:
        return f"H1_CONTENT = {_py(content)}"
    return "H1_CONTENT = (\n" + "".join(f"    {_py(s)}\n" for s in sentences) + ")"


def _tuple_inline(values: list[str]) -> str:
    if len(values) == 1:
        return f"({_py(values[0])},)"
    return "(" + ", ".join(_py(value) for value in values) + ")"


def _tuple_block(values: list[str]) -> str:
    return "(\n" + "".join(f"    {_py(value)},\n" for value in values) + ")"


def _set(values: list[str]) -> str:
    return "{" + ", ".join(_py(value) for value in values) + "}"


def _values(spec: dict) -> dict[str, str]:
    candidate = spec["candidate"]
    qa = spec["runtime_qa"]
    knowledge = spec["knowledge"]
    values = {
        "candidate_id": candidate["candidate_id"],
        "name_jp": candidate["name_jp"],
        "name_py": _py(candidate["name_jp"]),
        "address_py": _py(candidate["address"]),
        "latitude": _number(candidate["latitude"]),
        "longitude": _number(candidate["longitude"]),
        "trace_id_py": _py(qa["trace_id"]),
        "qa_origin_lat": _number(qa["qa_origin"]["lat"]),
        "qa_origin_lng": _number(qa["qa_origin"]["lng"]),
        "h1_content_assignment": _h1_content_assignment(qa["primary_history_content"]),
        "forbidden_phrases_tuple": _tuple_block(qa["forbidden_guarantee_phrases"]),
    }
    if qa["family"] == RUNTIME_HISTORY_ONLY:
        source = spec["source_identity"]
        history = spec["normalized_url_identity_sql"]["history_attributes"][0]
        values.update(
            history_type_py=_py(history["history_type"]),
            history_title_py=_py(knowledge["history_titles"][0]),
            history_verification_status_py=_py(history["verification_status"]),
            history_confidence_py=_py(history["confidence"]),
            source_type_py=_py(source["source_type"]),
            source_url_py=_py(qa["source_url"]),
            source_verification_status_py=_py(source["verification_status"]),
            excluded_deity_names_tuple=_tuple_inline(qa["excluded_deity_names"]),
        )
    else:
        values.update(
            deity_names_set=_set(knowledge["deity_names"]),
            history_titles_set=_set(knowledge["history_titles"]),
            excluded_deity_names_set=_set(qa["excluded_deity_names"]),
            expected_deity_count=str(knowledge["expected_deity_count"]),
            expected_history_count=str(knowledge["expected_history_count"]),
            knowledge_row_verification_status_py=_py(qa["knowledge_row_verification_status"]),
            sources_per_knowledge_row=str(qa["sources_per_knowledge_row"]),
            source_verification_status_py=_py(qa["source_verification_status"]),
        )
    return values


def generate_runtime_qa(spec: dict) -> str:
    """Return the Runtime QA script text for one validated spec."""
    validate_spec(spec)
    family = spec["runtime_qa"]["family"]
    if family not in (RUNTIME_HISTORY_ONLY, RUNTIME_DEITY_HISTORY):
        raise SpecError(f"unsupported runtime_qa.family {family!r}")
    template = (RUNTIME_TEMPLATE_DIR / f"{family}.py.tmpl").read_text(encoding="utf-8")
    text = _render(template, _values(spec))
    compile(text, f"{spec['candidate']['candidate_id']}_g7_runtime_qa.py", "exec")
    for required in ("with transaction.atomic():", 'cursor.execute("SET TRANSACTION READ ONLY")'):
        if required not in text:
            raise SpecError(f"generated Runtime QA lost {required!r}")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    args = parser.parse_args(argv)
    output = Path(args.output)
    try:
        text = generate_runtime_qa(load_spec(Path(args.spec)))
        if output.exists() or output.is_symlink():
            if not args.overwrite:
                raise SpecError(f"{output} exists (use --overwrite to replace it)")
            if output.is_symlink() or not output.is_file():
                raise SpecError(f"{output} is not a regular file")
        output.write_text(text, encoding="utf-8")
    except (SpecError, OSError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(f"RUNTIME_QA={output.name} sha256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    print("PRODUCTION_CONNECTION=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
