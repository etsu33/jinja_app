"""Synthetic-only, offline tests. Run with unittest; Django is not loaded."""

import csv
import hashlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit" / "sph21_snapshot_manifest.py"
spec = importlib.util.spec_from_file_location("snapshot_manifest", SCRIPT)
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)

# Pinned independently to the v1.1 SQL output, including empty sections.
DUMMY = """snapshot_query,server_version_num,transaction_isolation,transaction_read_only,snapshot,snapshot_started_at,guard
S0,170000,repeatable read,on,10:20:,2026-11-24 10:00:00+09,ok
snapshot_query,record_kind,object_name,grantor_key,detail
S1,role,dummy_role,,{}
snapshot_query,schema_name,object_name,object_kind,owner_role,raw_acl,acl_is_null,default_acl,rls_enabled,force_rls
snapshot_query,schema_name,sequence_name,owner_role,raw_acl,acl_is_null,default_acl
snapshot_query,creator_role,target_schema,object_type,raw_acl,acl_is_null
snapshot_query,record_kind,schema_name,object_name,owner_role,raw_acl,default_acl,detail
snapshot_query,schema_name,table_name,owner_role,rls_enabled,force_rls,policy_name,command,permissive,policy_roles,using_expression,with_check_expression
snapshot_query,schema_name,object_name,column_name,raw_acl
snapshot_query,owner_role,raw_acl,acl_is_null,default_acl
S8,dummy_owner,,t,{}
snapshot_query,object_type,schema_name,object_name,acl_source,grantee,privilege_type,is_grantable,grantor,grantee_is_owner
"""


class SnapshotTests(unittest.TestCase):
    def test_exact_bytes_and_empty_sections(self):
        for raw in (
            DUMMY.encode(),
            DUMMY.replace("\n", "\r\n").encode(),
            b"\xef\xbb\xbf" + DUMMY.encode(),
            DUMMY.rstrip("\n").encode(),
        ):
            with self.subTest(raw_size=len(raw)):
                result = manifest.build_manifest(raw)
                self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(result["size_bytes"], len(raw))
                self.assertEqual(result["snapshot_started_at"], "2026-11-24 10:00:00+09")
                self.assertEqual(
                    [s["row_count"] for s in result["sections"]], [1, 1, 0, 0, 0, 0, 0, 0, 1, 0]
                )
                self.assertEqual(manifest.verify_manifest(raw, result), result)

    def test_quoted_comma_quote_unicode_and_multiline(self):
        rows = list(csv.reader(io.StringIO(DUMMY)))
        rows[3][2] = 'dummy,"神社"\nsecond line'
        output = io.StringIO(newline="")
        csv.writer(output).writerows(rows)
        self.assertEqual(
            manifest.build_manifest(output.getvalue().encode())["sections"][1]["row_count"], 1
        )

    def test_populated_sections_and_multiple_rows(self):
        rows = list(csv.reader(io.StringIO(DUMMY)))
        populated = []
        section = -1
        for row in rows:
            populated.append(row)
            if row[0] == "snapshot_query":
                section += 1
                if section not in (0, 1, 8):
                    populated.extend([[f"S{section}", *(["dummy"] * (len(row) - 1))]] * 2)
        output = io.StringIO(newline="")
        csv.writer(output).writerows(populated)
        result = manifest.build_manifest(output.getvalue().encode())
        self.assertEqual(
            [s["row_count"] for s in result["sections"]], [1, 1, 2, 2, 2, 2, 2, 2, 1, 2]
        )

    def test_invalid_structure(self):
        lines = DUMMY.splitlines(keepends=True)
        variants = [
            b"",
            b"\xff",
            b"\x00" + DUMMY.encode(),
            b"log\n" + DUMMY.encode(),
            DUMMY.encode() + b"\n",
            DUMMY.encode() + b"(0 rows)\n",
            DUMMY.encode() + b"S9,relation\n",
            DUMMY.replace("S1,role", "S2,role").encode(),
            DUMMY.replace("dummy_role", "dummy_role,extra").encode(),
            DUMMY.replace("S1,role,dummy_role,,{}", 'S1,"unclosed').encode(),
            DUMMY.replace("S1,role,dummy_role,,{}", 'S1,role,"x"junk,,{}').encode(),
            DUMMY.replace("S8,dummy_owner,,t,{}\n", "").encode(),
            DUMMY.replace(lines[1], lines[1] * 2).encode(),
            DUMMY.replace(lines[1], "").encode(),
        ]
        # Drop or duplicate every individual section, including its data rows.
        starts = [i for i, line in enumerate(lines) if line.startswith("snapshot_query,")]
        blocks = [
            "".join(lines[a:b]) for a, b in zip(starts, starts[1:] + [len(lines)], strict=True)
        ]
        for i in range(10):
            variants.append("".join(blocks[:i] + blocks[i + 1 :]).encode())
            variants.append("".join(blocks[:i] + [blocks[i]] + blocks[i:]).encode())
        variants.append("".join([blocks[1], blocks[0]] + blocks[2:]).encode())
        for raw in variants:
            with self.subTest(case=variants.index(raw)):
                with self.assertRaises(manifest.ValidationError):
                    manifest.build_manifest(raw)

    def test_invalid_s0_metadata(self):
        for before, after in [
            ("repeatable read", "read committed"),
            (",on,", ",off,"),
            (",ok\n", ",STOP\n"),
            ("170000", "unknown"),
            ("10:20:", "bad-snapshot"),
            ("2026-11-24 10:00:00+09", "2026-02-30 10:00:00+09"),
            ("2026-11-24 10:00:00+09", "2026-11-24 10:00:00"),
            ("2026-11-24 10:00:00+09", "2026-11-24 10:00:00+09:60"),
            ("2026-11-24 10:00:00+09", ""),
        ]:
            with self.subTest(value=after), self.assertRaises(manifest.ValidationError):
                manifest.build_manifest(DUMMY.replace(before, after).encode())

    def test_byte_changes_rejected_against_trusted_manifest(self):
        trusted = manifest.build_manifest(DUMMY.encode())
        for modified in [
            DUMMY.replace("dummy_role", "other_role"),
            DUMMY.replace("\n", "\r\n"),
            DUMMY.replace("S1,role,dummy_role,,{}\n", ""),
            DUMMY[:-10],
        ]:
            with self.subTest(change=len(modified)), self.assertRaises(manifest.ValidationError):
                manifest.verify_manifest(modified.encode(), trusted)
        for expected in [
            None,
            [],
            {},
            {**trusted, "size_bytes": 0},
            {**trusted, "sha256": "0" * 64},
        ]:
            with self.assertRaises(manifest.ValidationError):
                manifest.verify_manifest(DUMMY.encode(), expected)

    def test_cli_round_trip_and_failure_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "dummy.csv", Path(tmp) / "manifest.json"
            source.write_bytes(DUMMY.encode())

            def run(*args):
                return subprocess.run(
                    [sys.executable, str(SCRIPT), str(source), *map(str, args)],
                    capture_output=True,
                    text=True,
                )

            self.assertEqual(run("--output", target).returncode, 0)
            saved = target.read_bytes()
            self.assertEqual(run("--verify", target).returncode, 0)
            self.assertEqual(run("--output", target).returncode, 1)
            self.assertEqual(run("--output", source).returncode, 1)
            alias = Path(tmp) / "alias"
            alias.symlink_to(source)
            self.assertEqual(run("--output", alias).returncode, 1)
            self.assertEqual(source.read_bytes(), DUMMY.encode())
            self.assertEqual(target.read_bytes(), saved)
            source.write_bytes(DUMMY.replace("dummy_role", "altered_role").encode())
            self.assertEqual(run("--verify", target).returncode, 1)
            source.write_bytes(b"broken")
            new = Path(tmp) / "new.json"
            self.assertEqual(run("--output", new).returncode, 1)
            self.assertFalse(new.exists())
            target.write_text("{bad json")
            self.assertEqual(run("--verify", target).returncode, 1)
            source.unlink()
            self.assertEqual(run("--output", new).returncode, 1)
            self.assertFalse(new.exists())


if __name__ == "__main__":
    unittest.main()
