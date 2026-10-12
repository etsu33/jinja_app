#!/usr/bin/env python3
"""Shrine Expansion G7 target-only Base Seed subset extraction (generic).

Extracts exactly one row from the canonical Base Seed for the candidate of a
validated G7 spec (``g7_specs/<candidate>.json``) and writes it, unchanged, as a
one-element JSON list for
``import_shrines_seed --source <subset> --skip-goriyaku-tags``.

- target = exact ``candidate.name_jp`` + ``candidate.address`` (no normalization)
- 0 or >1 exact matches => BLOCKED
- the selected row must equal ``base_subset.expected_row`` (the reviewed frozen G7
  row) as a whole => otherwise BLOCKED
- the output is exactly one row, rendered deterministically; the full Base Seed
  can never be written
- the output path must be outside the repository (guard.is_safe_dump_path) and an
  existing file is never replaced without --overwrite

This script performs no DB access, no network access and reads no credential.
The historical ``nsrc_000002_g7_extract_base_subset.py`` is kept as the golden
reference; for nsrc-000002 both produce byte-identical output.

Usage:
    g7_extract_base_subset.py --spec <G7_SPEC> --output <OUTPUT_PATH> [--overwrite]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from g7_sql_generator import SpecError, _load_guard, load_spec  # noqa: E402

BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
_is_safe_dump_path = _load_guard().is_safe_dump_path


class SubsetBlocked(ValueError):
    """Target-only subset extraction failed closed."""


def extract_subset(spec: dict, base_rows) -> list[dict]:
    """Return the one Base Seed row of the spec's candidate as a one-element list."""
    if not isinstance(base_rows, list):
        raise SubsetBlocked("BLOCKED: Base Seed must be a JSON list")
    name = spec["candidate"]["name_jp"]
    address = spec["candidate"]["address"]
    subset = [
        row
        for row in base_rows
        if isinstance(row, dict) and row.get("name_jp") == name and row.get("address") == address
    ]
    if len(subset) != 1:
        raise SubsetBlocked(f"BLOCKED: expected exactly 1 target row, found {len(subset)}")
    if subset[0] != spec["base_subset"]["expected_row"]:
        raise SubsetBlocked("BLOCKED: target Base Seed row differs from the frozen G7 row")
    return [copy.deepcopy(subset[0])]


def render(subset: list[dict]) -> str:
    if not isinstance(subset, list) or len(subset) != 1 or not isinstance(subset[0], dict):
        raise SubsetBlocked("BLOCKED: a G7 subset must contain exactly 1 row")
    return json.dumps(subset, ensure_ascii=False, indent=2) + "\n"


def _check_output(output: Path, *, overwrite: bool) -> None:
    ok, reason = _is_safe_dump_path(str(output), str(REPO_ROOT))
    if not ok:
        raise SubsetBlocked(f"BLOCKED: {reason}")
    if output.exists() or output.is_symlink():
        if not overwrite:
            raise SubsetBlocked(f"BLOCKED: {output} exists (use --overwrite to replace it)")
        if output.is_symlink() or not output.is_file():
            raise SubsetBlocked(f"BLOCKED: {output} is not a regular file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    args = parser.parse_args(argv)
    output = Path(args.output)
    try:
        spec = load_spec(Path(args.spec))
        _check_output(output, overwrite=args.overwrite)
        rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
        text = render(extract_subset(spec, rows))
    except (SpecError, SubsetBlocked, json.JSONDecodeError, OSError) as error:
        message = str(error)
        print(message if message.startswith("BLOCKED") else f"BLOCKED: {message}", file=sys.stderr)
        return 1
    output.write_text(text, encoding="utf-8")
    print("SUBSET_ROWS=1")
    print(f"candidate_id={spec['candidate']['candidate_id']}")
    print(f"name_jp={spec['candidate']['name_jp']}")
    print(f"address={spec['candidate']['address']}")
    print(f"SUBSET_SHA256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
