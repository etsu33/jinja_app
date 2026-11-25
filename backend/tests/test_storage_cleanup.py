"""Storage cleanup の共通契約（backend/common/storage_cleanup.py）。

storage abstraction だけを使うこと、失敗を握りつぶさないこと、
log に PII を出さないことを固定する。
"""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest
from django.db import transaction

from common.storage_cleanup import (
    _safe_prefix,
    delete_stored_file,
    schedule_stored_file_delete,
)


def _mock_storage():
    """`delete` しか持たない storage。

    spec を絞ることで、Local filesystem 固有API（`path` など）に触れたら
    AttributeError で落ちる。R2 のような非ローカル backend で動く保証になる。
    """
    return Mock(spec=["delete", "exists", "open", "save", "url"])


class _StubFieldFile:
    """FieldFile の最小の代役。

    Mock ではなく実クラスにしているのは、`__bool__` が name 依存という
    FieldFile の実挙動（空なら falsy）をそのまま再現するため。
    """

    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

    def __bool__(self):
        return bool(self.name)


def _fieldfile(storage, name):
    return _StubFieldFile(storage, name)


# --- storage abstraction ----------------------------------------------------


def test_delete_uses_storage_delete_with_the_name():
    storage = _mock_storage()

    assert delete_stored_file(storage, "goshuin/a.jpg") is True
    storage.delete.assert_called_once_with("goshuin/a.jpg")


def test_delete_does_not_touch_local_filesystem_apis():
    """`path` / `location` などローカル専用APIへ触れていないこと。"""
    storage = _mock_storage()

    delete_stored_file(storage, "icons/a.png")

    for local_only in ("path", "location", "base_location"):
        assert not hasattr(storage, local_only)


def test_delete_does_not_call_exists_first():
    """S3/R2 で往復を増やさない。存在確認はしない。"""
    storage = _mock_storage()

    delete_stored_file(storage, "icons/a.png")

    storage.exists.assert_not_called()


# --- failure handling -------------------------------------------------------


def test_delete_failure_is_not_swallowed_silently(caplog):
    storage = _mock_storage()
    storage.delete.side_effect = OSError("boom")

    with caplog.at_level(logging.ERROR, logger="common.storage_cleanup"):
        assert delete_stored_file(storage, "icons/secret-user-photo.png") is False

    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert "failed to delete stored file" in errors[0].getMessage()


def test_delete_failure_log_contains_no_pii_or_credentials(caplog):
    storage = _mock_storage()
    storage.delete.side_effect = RuntimeError(
        "AccessDenied: key=icons/secret-user-photo.png "
        "AWSAccessKeyId=AKIAEXAMPLE secret=shhh"
    )

    with caplog.at_level(logging.ERROR, logger="common.storage_cleanup"):
        delete_stored_file(storage, "icons/secret-user-photo.png")

    message = caplog.records[0].getMessage()
    # ファイル名本体・credential・例外メッセージ本文は出さない
    for secret in ("secret-user-photo", "AKIAEXAMPLE", "shhh", "AccessDenied"):
        assert secret not in message
    # traceback も付けない
    assert caplog.records[0].exc_info is None
    # 調査に足りる情報は出す
    assert "icons/" in message
    assert "RuntimeError" in message


def test_delete_failure_log_says_the_file_is_orphaned_not_rolled_back(caplog):
    """DB は既に消えている。rollback したかのような文言にしない。"""
    storage = _mock_storage()
    storage.delete.side_effect = OSError("boom")

    with caplog.at_level(logging.ERROR, logger="common.storage_cleanup"):
        delete_stored_file(storage, "icons/a.png")

    message = caplog.records[0].getMessage()
    assert "orphaned" in message
    assert "rollback" not in message.lower()


def test_safe_prefix_drops_the_filename():
    assert _safe_prefix("icons/abc.png") == "icons/"
    assert _safe_prefix("goshuin/2026/x.jpg") == "goshuin/2026/"
    assert _safe_prefix("noslash.png") == "<root>"


# --- transaction 境界 -------------------------------------------------------


def test_schedule_ignores_empty_fieldfile():
    storage = _mock_storage()

    assert schedule_stored_file_delete(None) is None
    assert schedule_stored_file_delete(_fieldfile(storage, "")) is None
    storage.delete.assert_not_called()


@pytest.mark.django_db
def test_schedule_does_not_delete_before_commit():
    storage = _mock_storage()

    with transaction.atomic():
        schedule_stored_file_delete(_fieldfile(storage, "icons/a.png"))
        # commit 前には呼ばれない
        storage.delete.assert_not_called()


@pytest.mark.django_db
def test_schedule_deletes_on_commit(django_capture_on_commit_callbacks):
    storage = _mock_storage()

    with django_capture_on_commit_callbacks(execute=True):
        schedule_stored_file_delete(_fieldfile(storage, "icons/a.png"))

    storage.delete.assert_called_once_with("icons/a.png")


@pytest.mark.django_db
def test_schedule_does_not_delete_when_the_transaction_rolls_back():
    storage = _mock_storage()

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            schedule_stored_file_delete(_fieldfile(storage, "icons/a.png"))
            raise RuntimeError("rollback")

    storage.delete.assert_not_called()
