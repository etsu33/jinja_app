# backend/temples/tests/test_no_superuser_bootstrap_endpoint.py
#
# /admin/create-superuser/ used to create or reset a Django superuser
# account (hardcoded username/password) for any unauthenticated request.
# Django's admin app registers a catch-all under /admin/ (AdminSite.
# catch_all_view), so an unmatched /admin/* sub-path still "resolves" in
# the django.urls.resolve() sense; the security property that actually
# matters is that hitting this path no longer creates/resets that account
# and no longer returns the old {"ok": true, "is_superuser": true, ...}
# response. This guards that behavior directly via the test client, while
# confirming the real Django Admin site itself is unaffected.
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import resolve


@pytest.mark.django_db
def test_create_superuser_bootstrap_route_no_longer_creates_or_resets_account():
    User = get_user_model()
    assert not User.objects.filter(username="morietsu").exists()

    resp = Client().get("/admin/create-superuser/")

    assert resp.status_code != 200
    assert b'"is_superuser": true' not in resp.content
    assert not User.objects.filter(username="morietsu").exists()


def test_django_admin_site_still_resolves():
    match = resolve("/admin/")
    assert match is not None
