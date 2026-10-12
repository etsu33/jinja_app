#!/usr/bin/env python3
"""nsrc-000002 G7 target-only Base Seed subset extraction.

Extracts exactly one row (青澤神社 / 新潟県糸魚川市大字青海2696番地) from the
canonical Base Seed and writes it, unchanged, as a one-element JSON list for
``import_shrines_seed --source <subset> --skip-goriyaku-tags``.

Full canonical Base Seed Production apply is prohibited; only this subset may
be imported. The output path must be outside the repository so the generated
file can never be committed. This script performs no DB access.

Usage:
    scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py <OUTPUT_PATH>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from guard import is_safe_dump_path  # noqa: E402

BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
TARGET_NAME = "青澤神社"
TARGET_ADDRESS = "新潟県糸魚川市大字青海2696番地"
EXPECTED_ROW = {
    "name_jp": TARGET_NAME,
    "address": TARGET_ADDRESS,
    "latitude": 37.00763484,
    "longitude": 137.79024297,
    "goriyaku": "",
    "kyusei": None,
    "astro_elements": [],
    "location": {"lat": 37.00763484, "lng": 137.79024297},
}


def extract_subset(base_seed_path: Path = BASE_SEED_PATH) -> list[dict]:
    rows = json.loads(base_seed_path.read_text(encoding="utf-8"))
    subset = [
        row
        for row in rows
        if row.get("name_jp") == TARGET_NAME and row.get("address") == TARGET_ADDRESS
    ]
    if len(subset) != 1:
        raise SystemExit(f"BLOCKED: expected exactly 1 target row, found {len(subset)}")
    if subset[0] != EXPECTED_ROW:
        raise SystemExit("BLOCKED: target Base Seed row differs from the frozen G7 row")
    return subset


def render(subset: list[dict]) -> str:
    return json.dumps(subset, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <OUTPUT_PATH>", file=sys.stderr)
        return 2
    output = Path(argv[1])
    ok, reason = is_safe_dump_path(str(output), str(REPO_ROOT))
    if not ok:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 1
    text = render(extract_subset())
    output.write_text(text, encoding="utf-8")
    print("SUBSET_ROWS=1")
    print(f"name_jp={TARGET_NAME}")
    print(f"address={TARGET_ADDRESS}")
    print(f"SUBSET_SHA256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
