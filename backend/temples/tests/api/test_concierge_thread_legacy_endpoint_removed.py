"""旧 GET /api/concierge/thread/?tid= を撤去した回帰テスト（WS-03）。

旧 endpoint は AllowAny かつ所有者フィルタなしで、任意の thread の title（相談本文の先頭）と
recommendations を返していた。呼び出し元が無いため撤去し、相談の閲覧は所有者分離済みの
GET /api/concierge-threads/<id>/ に一本化する。
"""

import pytest
from rest_framework.test import APIClient

from temples.models import ConciergeThread
from temples.services.anonymous_id import ANONYMOUS_ID_COOKIE_NAME, build_anonymous_cookie_value

PRIVATE_TITLE = "非公開の相談タイトル"
PRIVATE_RECOMMENDATION = "非公開の推薦"


def _legacy(client: APIClient, tid):
    return client.get("/api/concierge/thread/", {"tid": tid})


def _anon_client(anonymous_id: str) -> APIClient:
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = build_anonymous_cookie_value(anonymous_id)
    return client


def _user_thread(user) -> ConciergeThread:
    return ConciergeThread.objects.create(
        user=user,
        title=PRIVATE_TITLE,
        recommendations=[{"name": PRIVATE_RECOMMENDATION}],
    )


def _assert_no_thread_data(response):
    assert response.status_code == 404
    body = response.content.decode("utf-8")
    assert PRIVATE_TITLE not in body
    assert PRIVATE_RECOMMENDATION not in body


@pytest.mark.django_db
def test_legacy_endpoint_is_not_readable_anonymously(django_user_model):
    thread = _user_thread(django_user_model.objects.create_user(username="a", password="pw-a-123"))

    _assert_no_thread_data(_legacy(APIClient(), thread.pk))


@pytest.mark.django_db
def test_legacy_endpoint_is_not_readable_by_another_account(django_user_model):
    a = django_user_model.objects.create_user(username="a", password="pw-a-123")
    b = django_user_model.objects.create_user(username="b", password="pw-b-123")
    thread = _user_thread(a)
    client = APIClient()
    client.force_authenticate(b)

    _assert_no_thread_data(_legacy(client, thread.pk))


@pytest.mark.django_db
def test_legacy_endpoint_no_longer_exists_even_for_the_owner(django_user_model):
    a = django_user_model.objects.create_user(username="a", password="pw-a-123")
    thread = _user_thread(a)
    client = APIClient()
    client.force_authenticate(a)

    _assert_no_thread_data(_legacy(client, thread.pk))


@pytest.mark.django_db
def test_legacy_endpoint_does_not_expose_anonymous_threads():
    thread = ConciergeThread.objects.create(anonymous_id="anon-owner", title=PRIVATE_TITLE)

    _assert_no_thread_data(_legacy(_anon_client("someone-else"), thread.pk))
    _assert_no_thread_data(_legacy(_anon_client("anon-owner"), thread.pk))


@pytest.mark.django_db
@pytest.mark.parametrize("tid", ["999999", "abc", "", "1 OR 1=1"])
def test_legacy_endpoint_rejects_invalid_identifiers(tid):
    assert _legacy(APIClient(), tid).status_code == 404


@pytest.mark.django_db
def test_legacy_endpoint_without_tid_is_not_found():
    assert APIClient().get("/api/concierge/thread/").status_code == 404


@pytest.mark.django_db
def test_owner_still_reads_the_thread_through_the_protected_detail_endpoint(django_user_model):
    a = django_user_model.objects.create_user(username="a", password="pw-a-123")
    thread = _user_thread(a)
    client = APIClient()
    client.force_authenticate(a)

    res = client.get(f"/api/concierge-threads/{thread.pk}/")

    assert res.status_code == 200
    assert res.json()["id"] == thread.pk


@pytest.mark.django_db
def test_protected_detail_endpoint_returns_not_found_for_a_missing_thread(django_user_model):
    a = django_user_model.objects.create_user(username="a", password="pw-a-123")
    client = APIClient()
    client.force_authenticate(a)

    res = client.get("/api/concierge-threads/999999/")

    assert res.status_code == 404
    assert res.json() == {"detail": "not found"}


@pytest.mark.django_db
@pytest.mark.parametrize("bad", ["abc", "-1", "1.5"])
def test_protected_detail_endpoint_rejects_non_integer_identifiers(bad):
    assert APIClient().get(f"/api/concierge-threads/{bad}/").status_code == 404
