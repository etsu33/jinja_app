"""Pure unit tests for scripts/migration_safety/guard.py.

No database, no network, no Django. Run with:
    python3 -m pytest scripts/migration_safety/tests/test_guard.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guard import is_safe_dump_path, is_safe_restore_target, redact_url  # noqa: E402


class TestIsSafeRestoreTarget:
    def test_allows_localhost_with_isolation_marker(self):
        ok, _ = is_safe_restore_target("postgres://morietsu@localhost:5432/jinja_migration_audit_users_temp")
        assert ok is True

    def test_allows_127_0_0_1_with_migration_safety_marker(self):
        ok, _ = is_safe_restore_target("postgres://user:pw@127.0.0.1:5432/kami_musubi_migration_safety_20260810")
        assert ok is True

    def test_allows_restore_test_marker(self):
        ok, _ = is_safe_restore_target("postgres://user@localhost/some_restore_test_db")
        assert ok is True

    def test_blocks_non_local_host_even_with_marker(self):
        ok, reason = is_safe_restore_target(
            "postgres://user:pw@db.abcdefgh.supabase.co:5432/postgres_audit_restore_test"
        )
        assert ok is False
        assert "allow-list" in reason

    def test_blocks_render_internal_hostname(self):
        ok, _ = is_safe_restore_target("postgres://user:pw@dpg-abc123-a.oregon-postgres.render.com/audit_restore_test")
        assert ok is False

    def test_blocks_protected_existing_dev_db_jinja_db(self):
        ok, reason = is_safe_restore_target("postgres://morietsu@localhost:5432/jinja_db")
        assert ok is False
        assert "protected" in reason

    def test_blocks_protected_existing_dev_db_jinja_app_dev(self):
        ok, reason = is_safe_restore_target("postgres://morietsu@localhost:5432/jinja_app_dev")
        assert ok is False
        assert "protected" in reason

    def test_blocks_localhost_without_isolation_marker(self):
        ok, reason = is_safe_restore_target("postgres://morietsu@localhost:5432/some_random_db")
        assert ok is False
        assert "isolation marker" in reason

    def test_blocks_empty_database_name(self):
        ok, reason = is_safe_restore_target("postgres://morietsu@localhost:5432/")
        assert ok is False
        assert "empty" in reason

    def test_blocks_postgres_default_db_even_with_marker_in_query(self):
        # dbname is parsed from the path, not the query string — a marker
        # tacked on as a query param must not count.
        ok, _ = is_safe_restore_target("postgres://morietsu@localhost:5432/postgres?comment=audit_restore_test")
        assert ok is False

    def test_blocks_unparseable_url(self):
        ok, reason = is_safe_restore_target("not a url at all ://[[[")
        assert ok is False
        assert reason


class TestIsSafeDumpPath:
    def test_blocks_path_inside_repo_root(self, tmp_path):
        repo_root = str(tmp_path)
        inside = os.path.join(repo_root, "docs", "audit", "dump.sql")
        ok, reason = is_safe_dump_path(inside, repo_root)
        assert ok is False
        assert "inside the repository" in reason

    def test_blocks_repo_root_itself(self, tmp_path):
        ok, _ = is_safe_dump_path(str(tmp_path), str(tmp_path))
        assert ok is False

    def test_allows_path_outside_repo_root(self, tmp_path):
        repo_root = str(tmp_path / "repo")
        os.makedirs(repo_root, exist_ok=True)
        outside = str(tmp_path / "elsewhere" / "dump.sql")
        ok, reason = is_safe_dump_path(outside, repo_root)
        assert ok is True
        assert reason == "ok"

    def test_blocks_sneaky_relative_path_that_resolves_inside_repo(self, tmp_path):
        repo_root = str(tmp_path)
        sneaky = os.path.join(repo_root, "..", os.path.basename(repo_root), "dump.sql")
        ok, _ = is_safe_dump_path(sneaky, repo_root)
        assert ok is False


class TestRedactUrl:
    def test_masks_user_and_password(self):
        redacted = redact_url("postgres://myuser:supersecret@db.example.com:5432/mydb")
        assert "supersecret" not in redacted
        assert "myuser" not in redacted
        assert "db.example.com" in redacted
        assert "mydb" in redacted

    def test_masks_user_only_no_password(self):
        redacted = redact_url("postgres://myuser@localhost:5432/mydb")
        assert "myuser" not in redacted
        assert "localhost" in redacted

    def test_leaves_url_without_credentials_unchanged_in_shape(self):
        redacted = redact_url("postgres://localhost:5432/mydb")
        assert "localhost" in redacted
        assert "mydb" in redacted
