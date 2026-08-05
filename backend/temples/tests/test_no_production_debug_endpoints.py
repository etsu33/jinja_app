# backend/temples/tests/test_no_production_debug_endpoints.py
#
# /api/_debug/db/ and /api/_debug/media/ used to return, to any
# unauthenticated GET request, DB connection metadata (user/host/port),
# migration/schema state, server filesystem paths, and raw exception
# text. Unlike /admin/create-superuser/ (which falls through to Django
# Admin's own catch-all view), these paths are plain top-level path()
# entries with no sibling catch-all, so removing them makes them raise
# Resolver404 directly — confirmed empirically before writing this
# assertion, not assumed.
import pytest
from django.urls import Resolver404, resolve


@pytest.mark.parametrize("path", ["/api/_debug/db/", "/api/_debug/media/"])
def test_removed_debug_endpoint_does_not_resolve(path):
    with pytest.raises(Resolver404):
        resolve(path)


@pytest.mark.parametrize(
    "path",
    [
        "/admin/",
        "/healthz/",
        "/api/_debug/whoami/",
        "/api/shrines/",
    ],
)
def test_unrelated_routes_still_resolve(path):
    match = resolve(path)
    assert match is not None
