#!/usr/bin/env python3
"""NIIGATA-001-H003 C6 Catalog-only target-only Base Seed subset extraction.

Extracts exactly the four C4 / C5 PASS Catalog-only rows (nsrc-000011 / 000012 /
000013 / 000015, all 赤城神社) from the canonical Base Seed and writes them,
unchanged and in candidate order, as a four-element JSON list for
``import_shrines_seed --source <subset> --skip-goriyaku-tags``.

- target = exact (name_jp, address) only, never a name-only match
  (H003 has five distinct 赤城神社 and the Base Seed also has 群馬県の赤城神社)
- 0 or >1 exact matches for any target => BLOCKED
- every selected row must equal the frozen Base Seed row as a whole => otherwise BLOCKED
- the requested target set must be exactly the frozen four; nsrc-000014
  (G2 HOLD_POSITION_REVIEW) or any other id => BLOCKED
- the output is exactly four rows, rendered deterministically; the full Base Seed
  can never be written (full 129-row Production import is prohibited)
- the output path must be outside the repository (guard.is_safe_dump_path) and an
  existing file is never replaced without --overwrite

This script performs no DB access, no network access and reads no credential.

Usage:
    niigata_h003_c6_extract_base_subset.py --output <OUTPUT_PATH> [--overwrite]
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

from guard import is_safe_dump_path  # noqa: E402

BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
TARGET_NAME = "赤城神社"
HOLD_CANDIDATE_ID = "nsrc-000014"
HOLD_ADDRESS = "新潟県五泉市上杉川1310番地2"


def _frozen_row(address: str, lat: float, lng: float) -> dict:
    return {
        "name_jp": TARGET_NAME,
        "address": address,
        "latitude": lat,
        "longitude": lng,
        "goriyaku": "",
        "kyusei": None,
        "astro_elements": [],
        "location": {"lat": lat, "lng": lng},
    }


# candidate order = output order
EXPECTED_ROWS: dict[str, dict] = {
    "nsrc-000011": _frozen_row("新潟県新潟市江南区二本木1丁目7番16号", 37.841794, 139.118507),
    "nsrc-000012": _frozen_row("新潟県長岡市四郎丸2丁目5番33号", 37.440743, 138.855238),
    "nsrc-000013": _frozen_row("新潟県長岡市山屋314番地", 37.496407, 139.008620),
    "nsrc-000015": _frozen_row("新潟県魚沼市湯之谷芋川311番地", 37.214543, 139.036468),
}
TARGET_IDS: tuple[str, ...] = tuple(EXPECTED_ROWS)


class SubsetBlocked(ValueError):
    """Target-only subset extraction failed closed."""


def extract_subset(base_rows, target_ids=TARGET_IDS) -> list[dict]:
    """Return the four frozen Base Seed rows, in candidate order."""
    requested = tuple(target_ids)
    if HOLD_CANDIDATE_ID in requested:
        raise SubsetBlocked(
            f"BLOCKED: {HOLD_CANDIDATE_ID} is G2 HOLD_POSITION_REVIEW, not in the write cohort"
        )
    if requested != TARGET_IDS:
        raise SubsetBlocked(
            f"BLOCKED: target set must be exactly {','.join(TARGET_IDS)}, got {','.join(requested)}"
        )
    if not isinstance(base_rows, list):
        raise SubsetBlocked("BLOCKED: Base Seed must be a JSON list")

    subset = []
    for candidate_id in TARGET_IDS:
        expected = EXPECTED_ROWS[candidate_id]
        matches = [
            row
            for row in base_rows
            if isinstance(row, dict)
            and row.get("name_jp") == expected["name_jp"]
            and row.get("address") == expected["address"]
        ]
        if len(matches) != 1:
            raise SubsetBlocked(
                f"BLOCKED: {candidate_id} expected exactly 1 target row, found {len(matches)}"
            )
        if matches[0] != expected:
            raise SubsetBlocked(
                f"BLOCKED: {candidate_id} Base Seed row differs from the frozen row"
            )
        subset.append(copy.deepcopy(matches[0]))
    return subset


def render(subset: list[dict]) -> str:
    if not isinstance(subset, list) or len(subset) != len(TARGET_IDS):
        raise SubsetBlocked(f"BLOCKED: the H003 subset must contain exactly {len(TARGET_IDS)} rows")
    if any(row.get("address") == HOLD_ADDRESS for row in subset):
        raise SubsetBlocked(f"BLOCKED: {HOLD_CANDIDATE_ID} row must never be in the subset")
    if subset != [EXPECTED_ROWS[candidate_id] for candidate_id in TARGET_IDS]:
        raise SubsetBlocked("BLOCKED: subset differs from the frozen rows or candidate order")
    return json.dumps(subset, ensure_ascii=False, indent=2) + "\n"


def _check_output(output: Path, *, overwrite: bool) -> None:
    ok, reason = is_safe_dump_path(str(output), str(REPO_ROOT))
    if not ok:
        raise SubsetBlocked(f"BLOCKED: {reason}")
    if output.exists() or output.is_symlink():
        if not overwrite:
            raise SubsetBlocked(f"BLOCKED: {output} exists (use --overwrite to replace it)")
        if output.is_symlink() or not output.is_file():
            raise SubsetBlocked(f"BLOCKED: {output} is not a regular file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    args = parser.parse_args(argv)
    output = Path(args.output)
    try:
        _check_output(output, overwrite=args.overwrite)
        rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
        text = render(extract_subset(rows))
    except (SubsetBlocked, json.JSONDecodeError, OSError) as error:
        message = str(error)
        print(message if message.startswith("BLOCKED") else f"BLOCKED: {message}", file=sys.stderr)
        return 1
    output.write_text(text, encoding="utf-8")
    print(f"SUBSET_ROWS={len(TARGET_IDS)}")
    print(f"candidate_ids={','.join(TARGET_IDS)}")
    print(f"SUBSET_SHA256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
