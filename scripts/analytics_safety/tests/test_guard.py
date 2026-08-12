"""Pure unit tests for scripts/analytics_safety/guard.py.

No database, no network. Run with:
    python3 -m pytest scripts/analytics_safety/tests/test_guard.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guard import (  # noqa: E402
    build_allowed_path,
    describe_credential_shape,
    is_endpoint_allowed,
    is_readonly_hogql,
    redact_error_text,
)


# --- is_endpoint_allowed: allow-list enforcement ----------------------------


def test_allows_exact_query_endpoint():
    assert is_endpoint_allowed(method="POST", path="/api/projects/12345/query/") is True


def test_rejects_get_method():
    assert is_endpoint_allowed(method="GET", path="/api/projects/12345/query/") is False


def test_rejects_delete_method():
    assert is_endpoint_allowed(method="DELETE", path="/api/projects/12345/query/") is False


def test_rejects_event_capture_endpoint():
    assert is_endpoint_allowed(method="POST", path="/capture/") is False


def test_rejects_feature_flag_endpoint():
    assert is_endpoint_allowed(method="POST", path="/api/projects/12345/feature_flags/") is False


def test_rejects_project_settings_endpoint():
    assert is_endpoint_allowed(method="PATCH", path="/api/projects/12345/") is False


def test_rejects_person_deletion_endpoint():
    assert is_endpoint_allowed(method="DELETE", path="/api/projects/12345/persons/999/") is False


def test_rejects_path_traversal_in_project_id():
    assert is_endpoint_allowed(method="POST", path="/api/projects/../admin/query/") is False


# --- build_allowed_path ------------------------------------------------------


def test_build_allowed_path_returns_query_endpoint():
    assert build_allowed_path("12345") == "/api/projects/12345/query/"


def test_build_allowed_path_rejects_empty_project_id():
    try:
        build_allowed_path("")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_build_allowed_path_rejects_slash_in_project_id():
    try:
        build_allowed_path("123/456")
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- is_readonly_hogql: mutation keyword rejection --------------------------


def test_allows_select_query():
    assert is_readonly_hogql("SELECT count() FROM events WHERE event = 'recommendation_quality'") is True


def test_rejects_empty_query():
    assert is_readonly_hogql("") is False


def test_rejects_none_query():
    assert is_readonly_hogql(None) is False


def test_rejects_insert():
    assert is_readonly_hogql("INSERT INTO events VALUES (1)") is False


def test_rejects_update():
    assert is_readonly_hogql("UPDATE events SET event = 'x'") is False


def test_rejects_delete():
    assert is_readonly_hogql("DELETE FROM events") is False


def test_rejects_drop():
    assert is_readonly_hogql("DROP TABLE events") is False


def test_rejects_alter():
    assert is_readonly_hogql("ALTER TABLE events ADD COLUMN x") is False


def test_rejects_truncate():
    assert is_readonly_hogql("TRUNCATE events") is False


def test_rejects_create():
    assert is_readonly_hogql("CREATE TABLE x (id int)") is False


def test_rejects_keyword_case_insensitively():
    assert is_readonly_hogql("insert into events values (1)") is False
    assert is_readonly_hogql("Insert Into events") is False


def test_allows_select_mentioning_word_containing_keyword_substring():
    # "updated_at" contains "update" as a substring but not as a standalone
    # word; word-boundary matching must not false-positive on this.
    assert is_readonly_hogql("SELECT updated_at FROM events LIMIT 1") is True


# --- describe_credential_shape: never leaks the value -----------------------


def test_describe_credential_shape_absent():
    assert describe_credential_shape(None) == {"present": False}
    assert describe_credential_shape("") == {"present": False}


def test_describe_credential_shape_present_does_not_include_value():
    shape = describe_credential_shape("phx_fake_credential_value_for_testing_only")
    assert shape["present"] is True
    assert "phx_fake_credential_value_for_testing_only" not in json_dump_safe(shape)
    assert "value" not in shape


def test_describe_credential_shape_length_buckets():
    assert describe_credential_shape("short")["length_bucket"] == "short"
    assert describe_credential_shape("x" * 40)["length_bucket"] == "typical"
    assert describe_credential_shape("x" * 80)["length_bucket"] == "long"


def json_dump_safe(d):
    import json

    return json.dumps(d)


# --- redact_error_text -------------------------------------------------------


def test_redact_error_text_removes_bearer_token():
    text = "request failed: Authorization: Bearer phx_fake_secret_value"
    redacted = redact_error_text(text)
    assert "phx_fake_secret_value" not in redacted


def test_redact_error_text_removes_urls():
    text = "connection refused to https://us.posthog.com/api/projects/12345/query/"
    redacted = redact_error_text(text)
    assert "us.posthog.com" not in redacted
    assert "12345" not in redacted


def test_redact_error_text_empty_input():
    assert redact_error_text("") == ""
    assert redact_error_text(None) is None
