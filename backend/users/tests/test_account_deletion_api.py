"""DELETE /api/users/me/ の API 契約。

view は薄い。削除の順序 / Stripe 呼び出し / DB 削除 / Storage cleanup は
users.services.account_deletion が正本で、ここでは service を mock して
API 層の責務（status code / body / 例外 mapping）だけを検証する。
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from tests.factories import UserFactory
from tests.utils import api_client_as
from users.models import UserProfile
from users.services.account_deletion import (
    AccountDataDeletionFailed,
    AccountDeletionResult,
    BillingCleanupFailed,
    BillingCustomerCleanupFailed,
    BillingStateSyncFailed,
)

ME_URL_NAME = "users_api:me"

EXPECTED_503_BODY = {
    "code": "account_deletion_unavailable",
    "detail": "アカウント削除を完了できませんでした。時間をおいて再度お試しください。",
}

DOMAIN_FAILURES = [
    BillingCleanupFailed,
    BillingStateSyncFailed,
    BillingCustomerCleanupFailed,
    AccountDataDeletionFailed,
]


def _ok_result():
    return AccountDeletionResult(
        account_deleted=True,
        billing_cleanup_performed=False,
        tokens_blacklisted=0,
        recommendation_logs_deleted=0,
    )


@pytest.mark.django_db
def test_delete_me_requires_auth():
    """未認証は既存の認証 contract のまま。"""
    c = api_client_as()

    res = c.delete(reverse(ME_URL_NAME))

    assert res.status_code in (401, 403)


@pytest.mark.django_db
def test_delete_me_returns_204_with_empty_body():
    user = UserFactory()
    c = api_client_as(user)

    with patch(
        "users.api.views.delete_user_account", return_value=_ok_result()
    ) as service:
        res = c.delete(reverse(ME_URL_NAME))

    assert res.status_code == 204
    assert res.content == b""
    # service を単一入口として呼ぶ（個別 cleanup を API 層から叩かない）
    service.assert_called_once_with(user=user)


@pytest.mark.django_db
def test_delete_me_actually_deletes_the_user(settings):
    """service を mock せず、実際に User が消えることを確認する。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = UserFactory()
    user_id = user.pk
    c = api_client_as(user)

    res = c.delete(reverse(ME_URL_NAME))

    assert res.status_code == 204
    assert not get_user_model().objects.filter(pk=user_id).exists()
    assert not UserProfile.objects.filter(user_id=user_id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("failure", DOMAIN_FAILURES, ids=lambda e: e.__name__)
def test_domain_failures_map_to_503(failure):
    user = UserFactory()
    c = api_client_as(user)

    with patch("users.api.views.delete_user_account", side_effect=failure("boom")):
        res = c.delete(reverse(ME_URL_NAME))

    assert res.status_code == 503
    assert res.json() == EXPECTED_503_BODY
    # 失敗時に User は残る（API 層で削除しない）
    assert get_user_model().objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("failure", DOMAIN_FAILURES, ids=lambda e: e.__name__)
def test_503_body_does_not_reveal_which_step_failed(failure):
    """内部状態を区別できる情報を返さない（課金状態が推測できてしまうため）。"""
    user = UserFactory()
    c = api_client_as(user)

    with patch(
        "users.api.views.delete_user_account",
        side_effect=failure("stripe cus_SECRET sub_SECRET sk_live_SECRET failed"),
    ):
        res = c.delete(reverse(ME_URL_NAME))

    body = res.content.decode()
    assert set(res.json().keys()) == {"code", "detail"}
    for leaked in (
        "cus_",
        "sub_",
        "sk_live",
        failure.__name__,
        "Stripe",
        "stripe",
        "Traceback",
        user.email,
    ):
        assert leaked not in body


@pytest.mark.django_db
def test_unexpected_exception_is_not_converted_to_503():
    """domain exception 以外は握りつぶさない（未知の障害を隠さない）。"""
    user = UserFactory()
    c = api_client_as(user)

    with patch(
        "users.api.views.delete_user_account", side_effect=RuntimeError("unexpected")
    ):
        with pytest.raises(RuntimeError):
            c.delete(reverse(ME_URL_NAME))


@pytest.mark.django_db
def test_get_and_patch_still_work_on_the_same_view():
    """既存の GET / PATCH contract を壊していないこと。"""
    user = UserFactory()
    c = api_client_as(user)

    assert c.get(reverse(ME_URL_NAME)).status_code == 200

    patched = c.patch(reverse(ME_URL_NAME), {"nickname": "NewName"}, format="json")
    assert patched.status_code == 200
    assert patched.json()["profile"]["nickname"] == "NewName"


@pytest.mark.django_db
def test_openapi_schema_exposes_delete_on_users_me():
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    call_command("spectacular", "--format", "openapi-json", stdout=out)

    import json

    schema = json.loads(out.getvalue())
    me = schema["paths"]["/api/users/me/"]
    assert "delete" in me
    assert set(me["delete"]["responses"].keys()) == {"204", "503"}
