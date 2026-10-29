"""Shrine catalog writes are staff-only on every registered route.

Collects every URL pattern that dispatches to ShrineViewSet and checks each mutation method
against anonymous, ordinary authenticated and staff clients. Public reads and the throttled
ingest action stay open to everyone.
"""

from __future__ import annotations

import pytest
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.test import APIClient
from temples.api.views.shrine import ShrineViewSet
from temples.models import Shrine

MUTATION_METHODS = ("post", "put", "patch", "delete")
DENIED = {401, 403, 405}


def _shrine_routes():
    """(regex source, group names) for every pattern whose callback is ShrineViewSet."""

    def walk(patterns, prefix):
        for p in patterns:
            if isinstance(p, URLResolver):
                yield from walk(p.url_patterns, prefix + [p.pattern.regex.pattern])
            elif isinstance(p, URLPattern):
                if getattr(p.callback, "cls", None) is ShrineViewSet:
                    yield prefix + [p.pattern.regex.pattern], p

    return list(walk(get_resolver().url_patterns, []))


def _concrete_path(parts, pattern, pk: int) -> str:
    """Builds a request path from the pattern's own route, filling pk and format."""
    from django.urls.resolvers import RoutePattern

    path = ""
    for part in parts[:-1]:
        path += part.lstrip("^").rstrip("$")
    pat = pattern.pattern
    if isinstance(pat, RoutePattern):
        leaf = str(pat).replace("<int:pk>", str(pk))
    else:
        leaf = (
            pat.regex.pattern.lstrip("^")
            .rstrip("$")
            .replace("(?P<pk>[^/.]+)", str(pk))
            .replace("(?P<format>[a-z0-9]+)", "json")
            .replace("\\.", ".")
            .replace("/?", "/")
        )
    return "/" + (path + leaf).replace("//", "/")


@pytest.fixture
def shrine(db):
    return Shrine.objects.create(
        name_jp="書き込み権限テスト神社", address="東京都", latitude=35.0, longitude=139.0
    )


@pytest.fixture
def plain_client(django_user_model):
    user = django_user_model.objects.create_user(username="plain-writer", password="unused-x")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def staff_client(django_user_model):
    user = django_user_model.objects.create_user(
        username="staff-writer", password="unused-y", is_staff=True
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload():
    return {"name_jp": "改変", "address": "大阪府", "latitude": 34.0, "longitude": 135.0}


def test_shrine_routes_are_discovered():
    routes = _shrine_routes()
    # canonical list / detail paths plus the router's list / detail / ingest variants
    assert len(routes) >= 6


@pytest.mark.django_db
@pytest.mark.parametrize("who", ["anonymous", "plain"])
def test_non_staff_cannot_mutate_shrines_on_any_route(who, shrine, plain_client):
    client = APIClient() if who == "anonymous" else plain_client
    before_count = Shrine.objects.count()
    checked = 0

    for parts, pattern in _shrine_routes():
        path = _concrete_path(parts, pattern, shrine.pk)
        if "ingest" in path:
            continue  # public by design; covered below
        for method in MUTATION_METHODS:
            res = getattr(client, method)(path, _payload(), format="json")
            assert res.status_code in DENIED, (who, method, path, res.status_code)
            checked += 1

    shrine.refresh_from_db()
    assert shrine.name_jp == "書き込み権限テスト神社"
    assert Shrine.objects.count() == before_count
    assert checked >= 16


@pytest.mark.django_db
def test_plain_user_gets_403_not_405_where_the_action_exists(shrine, plain_client):
    # create is wired on the canonical list route: the permission layer, not routing, denies it
    before_count = Shrine.objects.count()
    res = plain_client.post("/api/shrines/", _payload(), format="json")
    assert res.status_code == 403
    assert Shrine.objects.count() == before_count


@pytest.mark.django_db
def test_staff_keeps_create_update_and_delete(shrine, staff_client):
    res = staff_client.post("/api/shrines/", _payload(), format="json")
    assert res.status_code == 201, res.content

    updated = deleted = False
    for parts, pattern in _shrine_routes():
        path = _concrete_path(parts, pattern, shrine.pk)
        if not updated:
            r = staff_client.patch(path, {"name_jp": "staff 更新"}, format="json")
            if r.status_code == 200:
                updated = True
    shrine.refresh_from_db()
    assert updated and shrine.name_jp == "staff 更新"

    for parts, pattern in _shrine_routes():
        path = _concrete_path(parts, pattern, shrine.pk)
        r = staff_client.delete(path)
        if r.status_code == 204:
            deleted = True
            break
    assert deleted
    assert not Shrine.objects.filter(pk=shrine.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("who", ["anonymous", "plain"])
def test_public_reads_stay_open(who, shrine, plain_client):
    client = APIClient() if who == "anonymous" else plain_client

    assert client.get("/api/shrines/").status_code == 200
    assert client.get(f"/api/shrines/{shrine.pk}/").status_code == 200


@pytest.mark.django_db
def test_ingest_stays_public(shrine):
    # no place_id → 400 from the view itself, i.e. the permission layer let it through
    res = APIClient().post("/api/shrines/ingest/", {}, format="json")
    assert res.status_code == 400
