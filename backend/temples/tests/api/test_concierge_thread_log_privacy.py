import logging

import pytest
from rest_framework.test import APIClient

from temples.models import ConciergeThread
from temples.services.anonymous_id import (
    ANONYMOUS_ID_COOKIE_NAME,
    attach_anonymous_cookie,
    build_anonymous_cookie_value,
)


@pytest.mark.django_db
def test_anonymous_thread_lookup_keeps_access_without_logging_identifiers(caplog):
    anonymous_id = "anon-private-regression-id"
    thread = ConciergeThread.objects.create(
        anonymous_id=anonymous_id,
        title="private thread title",
    )
    cookie_value = build_anonymous_cookie_value(anonymous_id)
    client = APIClient()
    client.cookies[ANONYMOUS_ID_COOKIE_NAME] = cookie_value

    with caplog.at_level(logging.INFO):
        response = client.get(f"/api/concierge-threads/{thread.pk}/")

    assert response.status_code == 200
    assert response.json()["id"] == thread.pk
    lookup = [record.getMessage() for record in caplog.records if "THREAD_DETAIL_LOOKUP" in record.getMessage()]
    assert lookup == ["THREAD_DETAIL_LOOKUP {'is_authenticated': False, 'anon_cookie_present': True}"]

    diagnostic = "\n".join(record.getMessage() for record in caplog.records)
    for forbidden in (anonymous_id, cookie_value, "private thread title", "anon_id_cookie", "user_id", "thread_id", "cookies"):
        assert forbidden not in diagnostic


@pytest.mark.django_db
def test_authenticated_thread_lookup_does_not_log_user_or_thread_id(django_user_model, caplog):
    user = django_user_model.objects.create_user(username="private-user", password="unused")
    thread = ConciergeThread.objects.create(user=user, title="authenticated private thread")
    client = APIClient()
    client.force_authenticate(user=user)

    with caplog.at_level(logging.INFO):
        response = client.get(f"/api/concierge-threads/{thread.pk}/")

    assert response.status_code == 200
    lookup = [record.getMessage() for record in caplog.records if "THREAD_DETAIL_LOOKUP" in record.getMessage()]
    assert lookup == ["THREAD_DETAIL_LOOKUP {'is_authenticated': True, 'anon_cookie_present': False}"]
    diagnostic = "\n".join(record.getMessage() for record in caplog.records)
    assert "private-user" not in diagnostic
    assert "user_id" not in diagnostic
    assert "thread_id" not in diagnostic


def test_anonymous_cookie_attachment_keeps_cookie_without_logging_value(caplog):
    from django.http import HttpResponse

    anonymous_id = "anon-cookie-attachment-private"
    response = HttpResponse()
    with caplog.at_level(logging.INFO):
        attach_anonymous_cookie(response, anonymous_id)

    cookie = response.cookies[ANONYMOUS_ID_COOKIE_NAME]
    assert cookie.value
    assert cookie["httponly"] is True
    diagnostic = "\n".join(record.getMessage() for record in caplog.records)
    assert anonymous_id not in diagnostic
    assert cookie.value not in diagnostic

