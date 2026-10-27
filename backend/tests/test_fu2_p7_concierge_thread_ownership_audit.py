"""FU-2-P7: Concierge thread ownership — audit tests（behaviour is NOT changed by this file）.

docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md

The existing isolation tests（temples/tests/api/test_concierge_thread_detail_authorization.py）cover the detail and
list views for A/B accounts and A/B anonymous identities. This file adds the cases the audit found uncovered:

- the write path（`append_chat`）for foreign thread ids;
- 404 uniformity between "missing" and "not yours"（enumeration）;
- tampered and very old signed anonymous cookies;
- forged identity headers and an invalid bearer next to a valid anonymous cookie;
- the shared-browser case（authenticated user + matching anonymous cookie）, pinned as the current contract;
- the `concierge` throttle scope shared by thread reads and chat;
- one latent gap, kept as a strict xfail so a future fix flips it.
"""

from __future__ import annotations

from unittest import mock

import pytest
from django.core import signing
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from temples.api.views.concierge import ConciergeThreadDetailView, ConciergeThreadListView
from temples.api_views_concierge import ConciergeChatView, ConciergePlanView
from temples.models import ConciergeMessage, ConciergeThread
from temples.services.anonymous_id import (
    ANONYMOUS_ID_COOKIE_NAME,
    ANONYMOUS_ID_SALT,
    build_anonymous_cookie_value,
    get_anonymous_id,
)
from temples.services.concierge_history import append_chat

pytestmark = pytest.mark.django_db

PRIVATE_TEXT = "P7監査用の非公開相談本文"
NOT_FOUND = {"detail": "not found"}


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _user(django_user_model, username):
    return django_user_model.objects.create_user(username=username, password="unused-p7")


def _user_thread(user, *, anonymous_id=None):
    thread = ConciergeThread.objects.create(user=user, anonymous_id=anonymous_id, title="user thread")
    ConciergeMessage.objects.create(thread=thread, role="user", content=PRIVATE_TEXT)
    return thread


def _anon_thread(anonymous_id):
    thread = ConciergeThread.objects.create(anonymous_id=anonymous_id, title="anon thread")
    ConciergeMessage.objects.create(thread=thread, role="user", content=PRIVATE_TEXT)
    return thread


def _anon_client(anonymous_id):
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = build_anonymous_cookie_value(anonymous_id)
    return client


def _detail(client, pk, **extra):
    return client.get(f"/api/concierge-threads/{pk}/", **extra)


def _messages(thread):
    return list(ConciergeMessage.objects.filter(thread=thread).values_list("content", flat=True))


def _throttle_keys():
    keys = set()
    for raw in list(cache._cache.keys()):  # noqa: SLF001 — isolated LocMemCache in tests
        name = raw.split(":", 2)[-1]
        if name.startswith("throttle_"):
            keys.add(name)
    return keys


# --- write path: append_chat never writes into a thread the caller does not own -------------------------------


def test_anonymous_b_cannot_append_to_anonymous_a_thread():
    victim = _anon_thread("anon-a")

    with pytest.raises(ConciergeThread.DoesNotExist):
        append_chat(anonymous_id="anon-b", query="attacker text", thread_id=victim.pk)

    assert _messages(victim) == [PRIVATE_TEXT]


def test_authenticated_b_cannot_append_to_authenticated_a_thread(django_user_model):
    a, b = _user(django_user_model, "p7-a"), _user(django_user_model, "p7-b")
    victim = _user_thread(a)

    with pytest.raises(ConciergeThread.DoesNotExist):
        append_chat(user=b, query="attacker text", thread_id=victim.pk)

    assert _messages(victim) == [PRIVATE_TEXT]


def test_authenticated_user_cannot_append_to_an_anonymous_thread(django_user_model):
    b = _user(django_user_model, "p7-b")
    victim = _anon_thread("anon-a")

    with pytest.raises(ConciergeThread.DoesNotExist):
        append_chat(user=b, query="attacker text", thread_id=victim.pk)

    assert _messages(victim) == [PRIVATE_TEXT]


def test_anonymous_cannot_append_to_a_user_thread_without_anonymous_id(django_user_model):
    a = _user(django_user_model, "p7-a")
    victim = _user_thread(a)

    with pytest.raises(ConciergeThread.DoesNotExist):
        append_chat(anonymous_id="anon-a", query="attacker text", thread_id=victim.pk)

    assert _messages(victim) == [PRIVATE_TEXT]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "P7-F3（latent）: append_chat's anonymous branch has no user__isnull=True. The check constraint allows a row "
        "with both user and anonymous_id; no current write path creates one, but a future handoff that keeps "
        "anonymous_id would let the old anonymous cookie append to the user's thread. The detail view already "
        "requires user IS NULL."
    ),
)
def test_anonymous_cookie_cannot_append_to_a_user_thread_that_still_carries_its_anonymous_id(django_user_model):
    a = _user(django_user_model, "p7-a")
    victim = _user_thread(a, anonymous_id="anon-a")  # allowed by concierge_thread_user_or_anonymous_required

    with pytest.raises(ConciergeThread.DoesNotExist):
        append_chat(anonymous_id="anon-a", query="attacker text", thread_id=victim.pk)


def test_detail_view_does_not_serve_a_user_thread_that_still_carries_its_anonymous_id(django_user_model):
    a = _user(django_user_model, "p7-a")
    victim = _user_thread(a, anonymous_id="anon-a")

    response = _detail(_anon_client("anon-a"), victim.pk)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


# --- read path: enumeration and metadata -----------------------------------------------------------------------


def test_missing_and_foreign_thread_ids_are_indistinguishable(django_user_model):
    a, b = _user(django_user_model, "p7-a"), _user(django_user_model, "p7-b")
    foreign_user_thread = _user_thread(a)
    foreign_anon_thread = _anon_thread("anon-a")
    missing_pk = max(foreign_user_thread.pk, foreign_anon_thread.pk) + 1000

    for client in (APIClient(), _anon_client("anon-b")):
        responses = [_detail(client, pk) for pk in (missing_pk, foreign_user_thread.pk, foreign_anon_thread.pk)]
        assert {r.status_code for r in responses} == {404}
        assert {r.content for r in responses} == {_detail(client, missing_pk).content}

    client = APIClient()
    client.force_authenticate(user=b)
    responses = [_detail(client, pk) for pk in (missing_pk, foreign_user_thread.pk, foreign_anon_thread.pk)]
    assert {r.status_code for r in responses} == {404}
    assert all(r.json() == NOT_FOUND for r in responses)
    assert all(PRIVATE_TEXT not in r.content.decode("utf-8") for r in responses)


def test_owner_payload_carries_no_identity_metadata():
    thread = _anon_thread("anon-a")

    body = _detail(_anon_client("anon-a"), thread.pk).json()

    assert "anonymous_id" not in body
    assert "user" not in body and "user_id" not in body
    assert "anon-a" not in str(body)


# --- anonymous identity ---------------------------------------------------------------------------------------


def test_tampered_signed_cookie_is_rejected():
    thread = _anon_thread("anon-a")
    signed = build_anonymous_cookie_value("anon-a")
    tampered = signed[:-1] + ("A" if signed[-1] != "A" else "B")
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = tampered

    response = _detail(client, thread.pk)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_cookie_signed_for_another_purpose_is_rejected():
    thread = _anon_thread("anon-a")
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = signing.dumps("anon-a", salt="some.other.salt")

    assert _detail(client, thread.pk).status_code == 404


def test_signed_anonymous_id_has_no_server_side_expiry():
    """P7-F1: the cookie Max-Age is 90 days, but the signature is checked with max_age=None.

    A value signed long ago is still accepted, so the cookie is a bearer credential with no server-side lifetime.
    Pinned as current behaviour, not endorsed.
    """
    with mock.patch("django.core.signing.time.time", return_value=946684800):  # 2000-01-01
        ancient = signing.dumps("anon-a", salt=ANONYMOUS_ID_SALT)
    request = mock.Mock(COOKIES={ANONYMOUS_ID_COOKIE_NAME: ancient})

    assert get_anonymous_id(request) == "anon-a"


@pytest.mark.parametrize(
    "headers",
    [
        {"HTTP_X_USER_ID": "1"},
        {"HTTP_X_ANONYMOUS_ID": "anon-a"},
        {"HTTP_X_CONCIERGE_ANON_ID": "anon-a"},
        {"HTTP_X_KM_CLIENT_IP": "192.0.2.1", "HTTP_X_KM_CLIENT_TS": "1", "HTTP_X_KM_CLIENT_SIG": "f" * 64},
        {"HTTP_X_FORWARDED_FOR": "192.0.2.1"},
    ],
)
def test_forged_identity_headers_grant_nothing(django_user_model, headers):
    a = _user(django_user_model, "p7-a")
    user_thread = _user_thread(a)
    anon_thread = _anon_thread("anon-a")

    for pk in (user_thread.pk, anon_thread.pk):
        response = _detail(APIClient(), pk, **headers)
        assert response.status_code == 404
        assert PRIVATE_TEXT not in response.content.decode("utf-8")


def test_invalid_bearer_with_a_valid_anonymous_cookie_is_401_without_content():
    """An expired / invalid access token is rejected before the view runs（JWTAuthentication → 401）.

    The anonymous thread is NOT served on that request; the BFF refreshes or the SSR helper returns null.
    """
    thread = _anon_thread("anon-a")
    client = _anon_client("anon-a")

    response = _detail(client, thread.pk, HTTP_AUTHORIZATION="Bearer not-a-jwt")

    assert response.status_code == 401
    assert PRIVATE_TEXT not in response.content.decode("utf-8")


# --- authenticated user + anonymous cookie（shared browser）------------------------------------------------------


def test_authenticated_user_with_matching_anonymous_cookie_reads_the_anonymous_thread(django_user_model):
    """P7-F2: current contract. Any principal holding the browser's anonymous cookie reads that cookie's threads.

    On a shared browser, user B logging in after an anonymous session still reads the anonymous threads
    of that browser through the detail view（not through the list, which is user-only）.
    """
    b = _user(django_user_model, "p7-b")
    thread = _anon_thread("anon-a")
    client = _anon_client("anon-a")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(b)}")

    response = _detail(client, thread.pk)

    assert response.status_code == 200
    assert [m["content"] for m in response.json()["messages"]] == [PRIVATE_TEXT]

    listed = client.get("/api/concierge-threads/").json()["results"]
    assert thread.pk not in [row["id"] for row in listed]


def test_login_does_not_transfer_anonymous_threads(django_user_model):
    """No handoff exists: after login the anonymous thread keeps user=NULL and its anonymous_id."""
    b = _user(django_user_model, "p7-b")
    thread = _anon_thread("anon-a")
    client = _anon_client("anon-a")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(b)}")

    _detail(client, thread.pk)
    client.get("/api/concierge-threads/")

    thread.refresh_from_db()
    assert thread.user_id is None
    assert thread.anonymous_id == "anon-a"


# --- throttle scope -------------------------------------------------------------------------------------------


def test_thread_reads_share_the_concierge_scope_with_chat_and_plan():
    assert {
        ConciergeThreadDetailView.throttle_scope,
        ConciergeThreadListView.throttle_scope,
        ConciergeChatView.throttle_scope,
        ConciergePlanView.throttle_scope,
    } == {"concierge"}


def test_an_authenticated_detail_read_spends_the_users_concierge_bucket(django_user_model):
    a = _user(django_user_model, "p7-a")
    thread = _user_thread(a)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(a)}")

    assert _detail(client, thread.pk).status_code == 200

    assert f"throttle_concierge_{a.pk}" in _throttle_keys()
