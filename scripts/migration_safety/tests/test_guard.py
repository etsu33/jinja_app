"""Pure unit tests for scripts/migration_safety/guard.py.

No database, no network, no Django. Run with:
    python3 -m pytest scripts/migration_safety/tests/test_guard.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guard import (  # noqa: E402
    describe_url_shape,
    is_readonly_sql,
    is_safe_dump_path,
    is_safe_restore_target,
    pg_env_exports,
    redact_url,
)


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


class TestDescribeUrlShape:
    def test_full_url_reports_all_true(self):
        shape = describe_url_shape("postgres://myuser:supersecret@db.example.supabase.co:5432/postgres?sslmode=require")
        assert shape == {
            "parses": True,
            "scheme_is_postgres": True,
            "has_host": True,
            "has_port": True,
            "has_dbname": True,
            "has_userinfo": True,
        }

    def test_never_contains_the_secret_or_host_substring(self):
        url = "postgres://myuser:supersecret@db.example.supabase.co:5432/postgres"
        shape = describe_url_shape(url)
        rendered = str(shape)
        assert "supersecret" not in rendered
        assert "myuser" not in rendered
        assert "db.example.supabase.co" not in rendered
        assert "postgres.co" not in rendered  # no partial host leakage either

    def test_never_contains_a_length_field(self):
        shape = describe_url_shape("postgres://myuser:supersecret@db.example.supabase.co:5432/postgres")
        assert "length" not in shape
        assert "len" not in shape

    def test_non_postgres_scheme_reported_false(self):
        shape = describe_url_shape("mysql://user:pw@host:3306/db")
        assert shape["scheme_is_postgres"] is False

    def test_missing_dbname_reported_false(self):
        shape = describe_url_shape("postgres://user@localhost:5432/")
        assert shape["has_dbname"] is False

    def test_no_userinfo_reported_false(self):
        shape = describe_url_shape("postgres://localhost:5432/mydb")
        assert shape["has_userinfo"] is False


class TestIsReadonlySql:
    def test_allows_plain_select(self):
        ok, _ = is_readonly_sql("SELECT 1;")
        assert ok is True

    def test_allows_show(self):
        ok, _ = is_readonly_sql("SHOW transaction_read_only;")
        assert ok is True

    def test_allows_with_cte_select(self):
        ok, _ = is_readonly_sql("WITH x AS (SELECT 1) SELECT * FROM x;")
        assert ok is True

    def test_allows_explain_without_analyze(self):
        ok, _ = is_readonly_sql("EXPLAIN SELECT * FROM django_migrations;")
        assert ok is True

    def test_allows_multiple_readonly_statements(self):
        ok, _ = is_readonly_sql("SELECT 1;\nSHOW server_version;\n")
        assert ok is True

    def test_allows_information_schema_query(self):
        ok, _ = is_readonly_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        assert ok is True

    def test_blocks_explain_analyze(self):
        ok, reason = is_readonly_sql("EXPLAIN ANALYZE SELECT 1;")
        assert ok is False
        assert "ANALYZE" in reason

    def test_blocks_insert(self):
        ok, reason = is_readonly_sql("INSERT INTO foo VALUES (1);")
        assert ok is False
        assert "forbidden" in reason

    def test_blocks_update(self):
        ok, _ = is_readonly_sql("UPDATE foo SET x = 1;")
        assert ok is False

    def test_blocks_delete(self):
        ok, _ = is_readonly_sql("DELETE FROM foo;")
        assert ok is False

    def test_blocks_drop(self):
        ok, _ = is_readonly_sql("DROP TABLE foo;")
        assert ok is False

    def test_blocks_alter(self):
        ok, _ = is_readonly_sql("ALTER TABLE foo ADD COLUMN bar int;")
        assert ok is False

    def test_blocks_truncate(self):
        ok, _ = is_readonly_sql("TRUNCATE foo;")
        assert ok is False

    def test_blocks_second_statement_being_a_write_even_if_first_is_select(self):
        ok, reason = is_readonly_sql("SELECT 1; DELETE FROM auth_user;")
        assert ok is False
        assert "delete" in reason

    def test_blocks_grant_revoke_vacuum(self):
        for verb in ("GRANT SELECT ON foo TO bar;", "REVOKE SELECT ON foo FROM bar;", "VACUUM foo;"):
            ok, _ = is_readonly_sql(verb)
            assert ok is False, verb

    def test_ignores_sql_line_comments(self):
        ok, _ = is_readonly_sql("-- this is a comment\nSELECT 1;")
        assert ok is True

    def test_ignores_sql_block_comments(self):
        ok, _ = is_readonly_sql("/* block comment */ SELECT 1;")
        assert ok is True

    def test_empty_sql_is_blocked(self):
        ok, reason = is_readonly_sql("   \n-- only a comment\n")
        assert ok is False
        assert "no SQL" in reason

    def test_unknown_verb_blocked_not_silently_allowed(self):
        ok, reason = is_readonly_sql("CALL some_procedure();")
        assert ok is False


class TestPgEnvExports:
    def test_produces_all_expected_vars(self):
        exports = pg_env_exports("postgres://myuser:supersecret@db.example.supabase.co:5432/postgres?sslmode=require")
        assert "export PGHOST=db.example.supabase.co" in exports
        assert "export PGPORT=5432" in exports
        assert "export PGUSER=myuser" in exports
        assert "export PGPASSWORD=supersecret" in exports
        assert "export PGDATABASE=postgres" in exports
        assert "export PGSSLMODE=require" in exports

    def test_omits_password_var_when_absent(self):
        exports = pg_env_exports("postgres://myuser@localhost:5432/mydb")
        assert "PGPASSWORD" not in exports
        assert "export PGUSER=myuser" in exports

    def test_omits_sslmode_when_not_specified(self):
        exports = pg_env_exports("postgres://myuser:pw@localhost:5432/mydb")
        assert "PGSSLMODE" not in exports

    def test_shell_quotes_special_characters_in_password(self):
        # No '@', ':', '/', or space — those require percent-encoding in a
        # real URI and would change how urlparse splits the netloc, which
        # is a separate concern from what this test targets: does
        # shlex.quote protect the shell metacharacters that ARE valid
        # unencoded in a password (quotes, $, backticks, parens)?
        exports = pg_env_exports("postgres://myuser:it's$(touch_pwned)`x`@localhost:5432/mydb")
        password_line = next(line for line in exports.splitlines() if line.startswith("export PGPASSWORD="))
        import subprocess

        result = subprocess.run(
            ["bash", "-c", f"{password_line}; printf '%s' \"$PGPASSWORD\""],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout == "it's$(touch_pwned)`x`"


class TestTemples0095_0098PreflightSqlIsReadonly:
    """No DB, no shell wrapper -- exercises exactly the check
    `readonly_query.sh` runs before ever touching a credential
    (`guard.py check-readonly-sql`), directly against the real preflight
    SQL file for temples migrations 0095-0098."""

    SQL_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "sql",
        "temples_0095_0098_preflight.sql",
    )

    def test_file_exists(self):
        assert os.path.isfile(self.SQL_PATH)

    def test_every_statement_is_readonly(self):
        with open(self.SQL_PATH, encoding="utf-8") as f:
            sql_text = f.read()
        ok, reason = is_readonly_sql(sql_text)
        assert ok is True, reason
