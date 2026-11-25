"""Offline validation of the v1.1 psql CSV stream; never opens a database."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Exact output columns of docs/audit/sql/sph21_permission_snapshot.sql v1.1.
HEADERS = tuple(
    tuple(("snapshot_query," + columns).split(","))
    for columns in (
        "server_version_num,transaction_isolation,transaction_read_only,snapshot,snapshot_started_at,guard",
        "record_kind,object_name,grantor_key,detail",
        "schema_name,object_name,object_kind,owner_role,raw_acl,acl_is_null,default_acl,rls_enabled,force_rls",
        "schema_name,sequence_name,owner_role,raw_acl,acl_is_null,default_acl",
        "creator_role,target_schema,object_type,raw_acl,acl_is_null",
        "record_kind,schema_name,object_name,owner_role,raw_acl,default_acl,detail",
        "schema_name,table_name,owner_role,rls_enabled,force_rls,policy_name,command,permissive,policy_roles,using_expression,with_check_expression",
        "schema_name,object_name,column_name,raw_acl",
        "owner_role,raw_acl,acl_is_null,default_acl",
        "object_type,schema_name,object_name,acl_source,grantee,privilege_type,is_grantable,grantor,grantee_is_owner",
    )
)


class ValidationError(ValueError):
    """Invalid snapshot or mismatch against a trusted manifest."""


def build_manifest(raw: bytes) -> dict:
    """Validate and hash the same immutable bytes, including BOM and line endings."""
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("CSV must be UTF-8") from exc
    if "\x00" in source:
        raise ValidationError("CSV contains NUL")
    counts = [0] * 10
    section = -1
    metadata = None
    try:
        for row in csv.reader(io.StringIO(source, newline=""), strict=True):
            if row and row[0] == "snapshot_query":
                section += 1
                if section >= 10 or tuple(row) != HEADERS[section]:
                    raise ValidationError("Missing, duplicate, reordered or invalid section header")
                continue
            if section < 0 or len(row) != len(HEADERS[section]):
                raise ValidationError("Invalid CSV row width or missing header")
            if row[0] != f"S{section}":
                raise ValidationError("Invalid section label")
            counts[section] += 1
            if section == 0:
                metadata = dict(zip(HEADERS[0], row, strict=True))
    except csv.Error as exc:
        raise ValidationError("Malformed CSV") from exc
    if section != 9:
        raise ValidationError("Expected exactly S0 through S9")
    if counts[0] != 1 or counts[8] != 1:
        raise ValidationError("S0 and S8 must each contain exactly one row")
    if (
        metadata["transaction_isolation"] != "repeatable read"
        or metadata["transaction_read_only"] != "on"
        or metadata["guard"] != "ok"
    ):
        raise ValidationError("S0 READ ONLY / REPEATABLE READ guard failed")
    timestamp = metadata["snapshot_started_at"]
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3])(?::?[0-5]\d)?)",
        timestamp,
    ):
        raise ValidationError("S0 timestamp must include date, time and timezone")
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValidationError("Invalid S0 timestamp") from exc
    if not re.fullmatch(r"[1-9]\d*", metadata["server_version_num"]):
        raise ValidationError("Invalid S0 server version")
    if not re.fullmatch(r"\d+:\d+:(?:\d+(?:,\d+)*)?", metadata["snapshot"]):
        raise ValidationError("Invalid S0 snapshot identifier")
    return {
        "manifest_version": 1,
        "snapshot_query_set": "sph21_permission_snapshot/v1.1",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "snapshot_started_at": timestamp,
        "sections": [{"id": f"S{i}", "row_count": n} for i, n in enumerate(counts)],
    }


def verify_manifest(raw: bytes, expected: object) -> dict:
    actual = build_manifest(raw)
    if expected != actual:
        raise ValidationError("CSV does not match the trusted manifest")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--output", type=Path, help="Create a new private JSON manifest (no overwrite)"
    )
    mode.add_argument("--verify", type=Path, help="Compare against a previously trusted manifest")
    args = parser.parse_args(argv)
    try:
        raw = args.csv.read_bytes()
        if args.verify:
            verify_manifest(raw, json.loads(args.verify.read_text(encoding="utf-8")))
            print("Snapshot verified")
        else:
            manifest = build_manifest(raw)
            # Exclusive creation also rejects symlinks, hardlinks and aliases to the CSV.
            with args.output.open("x", encoding="utf-8") as output:
                output.write(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
            print("Manifest created")
    except (OSError, ValueError) as exc:
        # Do not echo CSV cells, role inventories, paths or JSON decoder excerpts.
        message = str(exc) if isinstance(exc, ValidationError) else "File or JSON operation failed"
        print(f"Validation failed: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
