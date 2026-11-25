"""GET /api/concierge-threads/<id>/ の所有者分離（認証 user / 匿名 identity）の回帰テスト。

docs/audit/concierge-thread-authorization-isolation-audit.md
"""

import pytest
from rest_framework.test import APIClient

from temples.models import ConciergeMessage, ConciergeThread
from temples.services.anonymous_id import ANONYMOUS_ID_COOKIE_NAME, build_anonymous_cookie_value

PRIVATE_TEXT = "非公開の相談本文"


def _detail(client: APIClient, thread: ConciergeThread):
    return client.get(f"/api/concierge-threads/{thread.pk}/")


def _anon_client(anonymous_id: str) -> APIClient:
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = build_anonymous_cookie_value(anonymous_id)
    return client


def _user_thread(user) -> ConciergeThread:
    thread = ConciergeThread.objects.create(user=user, title="Aさんの相談")
    ConciergeMessage.objects.create(thread=thread, role="user", content=PRIVATE_TEXT)
    return thread


def _anon_thread(anonymous_id: str) -> ConciergeThread:
    thread = ConciergeThread.objects.create(anonymous_id=anonymous_id, title="匿名の相談")
    ConciergeMessage.objects.create(thread=thread, role="user", content=PRIVATE_TEXT)
    return thread


def _assert_not_found_without_content(response):
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}
    assert PRIVATE_TEXT not in response.content.decode("utf-8")


@pytest.mark.django_db
def test_account_a_reads_its_own_thread(django_user_model):
    a = django_user_model.objects.create_user(username="account-a", password="unused")
    thread = _user_thread(a)
    client = APIClient()
    client.force_authenticate(user=a)

    response = _detail(client, thread)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == thread.pk
    assert [m["content"] for m in body["messages"]] == [PRIVATE_TEXT]


@pytest.mark.django_db
def test_account_b_cannot_read_account_a_thread(django_user_model):
    a = django_user_model.objects.create_user(username="account-a", password="unused")
    b = django_user_model.objects.create_user(username="account-b", password="unused")
    thread = _user_thread(a)
    client = APIClient()
    client.force_authenticate(user=b)

    _assert_not_found_without_content(_detail(client, thread))


@pytest.mark.django_db
def test_anonymous_visitor_cannot_read_authenticated_thread(django_user_model):
    a = django_user_model.objects.create_user(username="account-a", password="unused")
    thread = _user_thread(a)

    # cookie なし（新しい Incognito session 相当）
    _assert_not_found_without_content(_detail(APIClient(), thread))
    # 別の匿名 identity の cookie あり
    _assert_not_found_without_content(_detail(_anon_client("anon-visitor"), thread))


@pytest.mark.django_db
def test_anonymous_cookie_never_reaches_a_user_owned_thread_even_if_ids_match(django_user_model):
    # user が付いた thread は、同じ anonymous_id の cookie でも匿名 fallback の対象にならない。
    a = django_user_model.objects.create_user(username="account-a", password="unused")
    thread = ConciergeThread.objects.create(user=a, anonymous_id="shared-browser-anon", title="t")
    ConciergeMessage.objects.create(thread=thread, role="user", content=PRIVATE_TEXT)

    _assert_not_found_without_content(_detail(_anon_client("shared-browser-anon"), thread))


@pytest.mark.django_db
def test_anonymous_owner_reads_its_own_thread():
    thread = _anon_thread("anon-owner")

    response = _detail(_anon_client("anon-owner"), thread)

    assert response.status_code == 200
    assert response.json()["id"] == thread.pk


@pytest.mark.django_db
def test_different_anonymous_identity_cannot_read_the_thread():
    thread = _anon_thread("anon-owner")

    _assert_not_found_without_content(_detail(_anon_client("anon-other"), thread))


@pytest.mark.django_db
def test_forged_or_unsigned_anonymous_cookie_cannot_read_the_thread():
    thread = _anon_thread("anon-owner")
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = "anon-owner"  # unsigned raw value

    _assert_not_found_without_content(_detail(client, thread))


@pytest.mark.django_db
def test_authenticated_user_with_other_anonymous_cookie_cannot_read_the_thread(django_user_model):
    b = django_user_model.objects.create_user(username="account-b", password="unused")
    thread = _anon_thread("anon-owner")
    client = _anon_client("anon-other")
    client.force_authenticate(user=b)

    _assert_not_found_without_content(_detail(client, thread))


@pytest.mark.django_db
def test_thread_list_returns_only_the_requesting_accounts_threads(django_user_model):
    a = django_user_model.objects.create_user(username="account-a", password="unused")
    b = django_user_model.objects.create_user(username="account-b", password="unused")
    own = _user_thread(a)
    _user_thread(b)
    _anon_thread("anon-owner")
    client = APIClient()
    client.force_authenticate(user=a)

    response = client.get("/api/concierge-threads/")

    assert response.status_code == 200
    assert [row["id"] for row in response.json()["results"]] == [own.pk]


@pytest.mark.django_db
def test_thread_list_requires_authentication():
    response = APIClient().get("/api/concierge-threads/")
    assert response.status_code in (401, 403)
