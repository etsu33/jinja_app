# backend/users/tests/test_views_no_sensitive_logging.py
#
# users/views.py (MeView.patch / MeIconUploadView.post) is not currently wired
# into ROOT_URLCONF (shrine_project.urls) — it's only reachable via the unused
# backend/config/urls.py. It is still exercised directly here (bypassing URL
# routing) so a regression of the JWT/PII logging bug fixed in this file would
# be caught even though no live HTTP route currently reaches this code.
from __future__ import annotations

import logging

import pytest
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request as DRFRequest
from rest_framework.test import APIRequestFactory

from tests.factories import UserFactory
from users.models import UserProfile
from users.views import MeIconUploadView, MeView

SENTINEL_JWT = "eyJhbGciOiJIUzI1NiJ9.SENTINEL_PAYLOAD.SENTINEL_SIGNATURE"


class _FakeToken:
    """SimpleJWT's Token.__str__() signs and returns the raw JWT string.
    This double reproduces that behavior so the test fails loudly if
    request.auth is ever passed into a log call again."""

    def __str__(self) -> str:
        return SENTINEL_JWT


def _drf_request(django_request, parsers):
    request = DRFRequest(django_request, parsers=parsers)
    request._user = django_request.user
    request._auth = django_request.auth
    return request


@pytest.mark.django_db
def test_me_view_patch_does_not_log_auth_token_or_username(caplog):
    user = UserFactory(username="sensitive-username-should-not-log")
    UserProfile.objects.get_or_create(user=user)

    django_request = APIRequestFactory().patch(
        "/users/me/", {"nickname": "NewNick"}, format="json"
    )
    django_request.user = user
    django_request.auth = _FakeToken()
    request = _drf_request(django_request, [JSONParser()])

    view = MeView()
    view.request = request
    view.format_kwarg = None

    with caplog.at_level(logging.INFO, logger="users.views"):
        view.patch(request)

    logged_text = "\n".join(record.getMessage() for record in caplog.records)
    assert SENTINEL_JWT not in logged_text
    assert user.username not in logged_text


@pytest.mark.django_db
def test_me_icon_upload_view_does_not_log_raw_files_or_username(caplog):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = UserFactory(username="another-sensitive-username")
    UserProfile.objects.get_or_create(user=user)

    icon = SimpleUploadedFile("icon.png", b"fake-image-bytes", content_type="image/png")
    django_request = APIRequestFactory().post(
        "/users/me/icon/", {"icon": icon}, format="multipart"
    )
    django_request.user = user
    django_request.auth = _FakeToken()
    request = _drf_request(django_request, [MultiPartParser(), FormParser()])

    view = MeIconUploadView()
    view.request = request
    view.format_kwarg = None

    with caplog.at_level(logging.INFO, logger="users.views"):
        view.post(request)

    logged_text = "\n".join(record.getMessage() for record in caplog.records)
    assert SENTINEL_JWT not in logged_text
    assert user.username not in logged_text
