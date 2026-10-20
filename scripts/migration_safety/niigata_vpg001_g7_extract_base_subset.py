#!/usr/bin/env python3
"""NIIGATA-001-VPG001 G7 cohort target-only Base Seed subset extraction.

Composes exactly the four canonical VPG001 Recommendation-track Base rows
(nsrc-000021 / 000022 / 000024 / 000025) from the canonical Base Seed and writes
them, unchanged and in candidate order, as a four-element JSON list for one
``import_shrines_seed --source <subset> --skip-goriyaku-tags`` run
(PRODUCTION_EXECUTION_MODE = VPG001_4_CANDIDATE_BATCH).

- the row authority is each candidate's existing one-row extractor
  (nsrc_0000XX_g7_extract_base_subset.EXPECTED_ROW); this script only composes them
- every row must also carry the frozen G2 coordinate listed below => otherwise BLOCKED
- target = exact (name_jp, address) only; 0 or >1 exact matches for any target => BLOCKED
- every selected row must equal the frozen row as a whole (neutral goriyaku / kyusei /
  astro_elements) => otherwise BLOCKED
- the requested target set must be exactly the frozen four, in order; nsrc-000023 or any
  other id => BLOCKED
- the output is exactly four rows, rendered deterministically; the full Base Seed is never
  written (FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED)
- the output path must be outside the repository (guard.is_safe_dump_path) and an
  existing file is never replaced without --overwrite

This script performs no DB access, no network access and reads no credential.

Usage:
    niigata_vpg001_g7_extract_base_subset.py --output <OUTPUT_PATH> [--overwrite]
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

import nsrc_000021_g7_extract_base_subset as _nsrc_000021  # noqa: E402
import nsrc_000022_g7_extract_base_subset as _nsrc_000022  # noqa: E402
import nsrc_000024_g7_extract_base_subset as _nsrc_000024  # noqa: E402
import nsrc_000025_g7_extract_base_subset as _nsrc_000025  # noqa: E402
from guard import is_safe_dump_path  # noqa: E402

BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
EXCLUDED_CANDIDATE_ID = "nsrc-000023"

# candidate order = output order; row authority = the #3279 one-row extractors
EXPECTED_ROWS: dict[str, dict] = {
    "nsrc-000021": _nsrc_000021.EXPECTED_ROW,
    "nsrc-000022": _nsrc_000022.EXPECTED_ROW,
    "nsrc-000024": _nsrc_000024.EXPECTED_ROW,
    "nsrc-000025": _nsrc_000025.EXPECTED_ROW,
}
TARGET_IDS: tuple[str, ...] = tuple(EXPECTED_ROWS)
# frozen G2 adopted coordinates (independent cross-check of the composed rows)
FROZEN_G2_COORDINATES: dict[str, tuple[float, float]] = {
    "nsrc-000021": (38.1409456, 139.4073314),
    "nsrc-000022": (37.573979, 139.048758),
    "nsrc-000024": (37.7863255, 139.1351949),
    "nsrc-000025": (37.0397729, 137.8644153),
}


class SubsetBlocked(ValueError):
    """Cohort target-only subset extraction failed closed."""


def _check_frozen_rows() -> None:
    if tuple(FROZEN_G2_COORDINATES) != TARGET_IDS:
        raise SubsetBlocked("BLOCKED: frozen G2 coordinate set differs from the cohort")
    for candidate_id, (lat, lng) in FROZEN_G2_COORDINATES.items():
        row = EXPECTED_ROWS[candidate_id]
        if (
            row["latitude"] != lat
            or row["longitude"] != lng
            or row["location"] != {"lat": lat, "lng": lng}
        ):
            raise SubsetBlocked(
                f"BLOCKED: {candidate_id} row differs from the frozen G2 coordinate"
            )
        if (row["goriyaku"], row["kyusei"], row["astro_elements"]) != ("", None, []):
            raise SubsetBlocked(
                f"BLOCKED: {candidate_id} row is not goriyaku / kyusei / astro neutral"
            )


def extract_subset(base_rows, target_ids=TARGET_IDS) -> list[dict]:
    """Return the four frozen Base Seed rows, in candidate order."""
    _check_frozen_rows()
    requested = tuple(target_ids)
    if EXCLUDED_CANDIDATE_ID in requested:
        raise SubsetBlocked(f"BLOCKED: {EXCLUDED_CANDIDATE_ID} is not in the VPG001 G7 cohort")
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
        raise SubsetBlocked(
            f"BLOCKED: the VPG001 subset must contain exactly {len(TARGET_IDS)} rows"
        )
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
