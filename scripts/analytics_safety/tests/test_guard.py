"""Pure unit tests for scripts/analytics_safety/guard.py.

No database, no network. Run with:
    python3 -m pytest scripts/analytics_safety/tests/test_guard.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guard import (  # noqa: E402
    UnsafeQueryResultError,
    build_allowed_path,
    describe_credential_shape,
    is_endpoint_allowed,
    is_readonly_hogql,
    redact_error_text,
    sanitize_query_result,
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


# --- sanitize_query_result: safe output allow-list --------------------------


def test_sanitize_safe_count_result():
    raw = {"results": [[42]], "columns": ["count"], "error": None}
    assert sanitize_query_result(raw) == {"results": [[42]], "columns": ["count"], "error": None}


def test_sanitize_safe_classification_aggregate():
    raw = {
        "results": [["FULLY_KNOWLEDGE_BACKED", 5], ["UNKNOWN", 3]],
        "columns": ["classification", "count"],
    }
    assert sanitize_query_result(raw) == {
        "results": [["FULLY_KNOWLEDGE_BACKED", 5], ["UNKNOWN", 3]],
        "columns": ["classification", "count"],
        "error": None,
    }


def test_sanitize_safe_property_completeness_aggregate():
    raw = {"results": [[0, 0, 0, 0]], "columns": ["a", "b", "c", "total"]}
    sanitized = sanitize_query_result(raw)
    assert sanitized["results"] == [[0, 0, 0, 0]]
    assert sanitized["error"] is None


def test_sanitize_null_results_handled():
    raw = {"results": None, "columns": None, "error": None}
    assert sanitize_query_result(raw) == {"error": None}


def test_sanitize_empty_rows_handled():
    raw = {"results": [], "columns": ["classification", "count"]}
    sanitized = sanitize_query_result(raw)
    assert sanitized["results"] == []
    assert sanitized["columns"] == ["classification", "count"]


def test_sanitize_preserves_error_string():
    raw = {"results": None, "columns": None, "error": "some upstream issue"}
    assert sanitize_query_result(raw) == {"error": "some upstream issue"}


# --- sanitize_query_result: metadata rejection (allow-list drops the rest) --


def test_sanitize_drops_project_identifier_field():
    raw = {"results": [[1]], "columns": ["count"], "team_id": 999999999}
    sanitized = sanitize_query_result(raw)
    assert "team_id" not in sanitized
    assert 999999999 not in sanitized.values()


def test_sanitize_drops_organization_identifier_field():
    raw = {"results": [[1]], "columns": ["count"], "organization_id": "org_fake_12345"}
    sanitized = sanitize_query_result(raw)
    assert "organization_id" not in sanitized
    assert "org_fake_12345" not in str(sanitized)


def test_sanitize_drops_host_field():
    raw = {"results": [[1]], "columns": ["count"], "host": "https://us.posthog.com"}
    sanitized = sanitize_query_result(raw)
    assert "host" not in sanitized
    assert "us.posthog.com" not in str(sanitized)


def test_sanitize_drops_authorization_like_field():
    raw = {"results": [[1]], "columns": ["count"], "authorization": "Bearer phx_fake_secret"}
    sanitized = sanitize_query_result(raw)
    assert "authorization" not in sanitized
    assert "phx_fake_secret" not in str(sanitized)


def test_sanitize_drops_clickhouse_and_cache_key_fields():
    raw = {
        "results": [[0]],
        "columns": ["count"],
        "clickhouse": "SELECT count() FROM events WHERE team_id = 999999999",
        "cache_key": "cache_999999999_deadbeef",
        "hogql": "SELECT count() FROM events",
        "query_metadata": {"events": []},
        "timezone": "UTC",
    }
    sanitized = sanitize_query_result(raw)
    assert set(sanitized.keys()) <= {"results", "columns", "error"}
    assert "999999999" not in str(sanitized)


def test_sanitize_drops_unknown_top_level_key():
    raw = {"results": [[1]], "columns": ["count"], "some_future_field": "unexpected"}
    sanitized = sanitize_query_result(raw)
    assert "some_future_field" not in sanitized


def test_sanitize_drops_distinct_id_and_email_if_present_as_metadata():
    raw = {
        "results": [[1]],
        "columns": ["count"],
        "distinct_id": "user_fake_abc123",
        "person_email": "fake@example.com",
    }
    sanitized = sanitize_query_result(raw)
    assert "distinct_id" not in sanitized
    assert "fake@example.com" not in str(sanitized)


# --- sanitize_query_result: schema failure (fail closed) --------------------


def test_sanitize_rejects_non_dict_response():
    for bad in (None, [], "not a dict", 42):
        try:
            sanitize_query_result(bad)
            assert False, f"expected UnsafeQueryResultError for {bad!r}"
        except UnsafeQueryResultError:
            pass


def test_sanitize_rejects_non_list_results():
    try:
        sanitize_query_result({"results": "not a list", "columns": ["count"]})
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_sanitize_rejects_non_list_row():
    try:
        sanitize_query_result({"results": [{"count": 1}], "columns": ["count"]})
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_sanitize_rejects_nested_dict_in_result_row():
    """A row containing a nested object (e.g. a person/consultation payload
    accidentally surfaced by a future query change) must fail closed rather
    than being passed through."""
    raw = {"results": [[1, {"email": "fake@example.com"}]], "columns": ["count", "person"]}
    try:
        sanitize_query_result(raw)
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_sanitize_rejects_nested_list_in_result_row():
    raw = {"results": [[1, ["nested", "list"]]], "columns": ["count", "extra"]}
    try:
        sanitize_query_result(raw)
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_sanitize_rejects_non_string_columns():
    try:
        sanitize_query_result({"results": [[1]], "columns": [{"name": "count"}]})
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_sanitize_rejects_non_string_error():
    try:
        sanitize_query_result({"results": None, "columns": None, "error": {"code": 500}})
        assert False, "expected UnsafeQueryResultError"
    except UnsafeQueryResultError:
        pass


def test_unsafe_query_result_error_is_a_value_error():
    """Callers that only catch ValueError (the general contract) still
    catch this specific error type."""
    assert issubclass(UnsafeQueryResultError, ValueError)
