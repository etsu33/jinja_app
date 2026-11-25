"""F-6B: collision の 409 が **両 live endpoint** の OpenAPI に記述されること。

    POST /api/places/resolve/
    POST /api/shrines/ingest/

どちらも body は detail + code のみ。候補 Shrine の id は公開契約に載せない
（AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED）。

docs/audit/place-id-shadow-identity-hardening.md §14.5
"""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

#: 409 を記述すべき live endpoint（path, method）。
COLLISION_ENDPOINTS = [
    pytest.param("/api/places/resolve/", "post", id="places-resolve"),
    pytest.param("/api/shrines/ingest/", "post", id="shrines-ingest"),
]


@pytest.fixture(scope="module")
def schema():
    res = APIClient().get(reverse("schema"), {"format": "json"})
    assert res.status_code == 200
    return res.json()


def _operation(schema, path, method):
    assert path in schema["paths"], sorted(schema["paths"])[:40]
    assert method in schema["paths"][path], sorted(schema["paths"][path])
    return schema["paths"][path][method]


def _conflict_properties(schema, path, method):
    responses = _operation(schema, path, method)["responses"]
    assert "409" in responses, sorted(responses)
    body = responses["409"]["content"]["application/json"]["schema"]
    name = body["$ref"].rsplit("/", 1)[-1]
    return schema["components"]["schemas"][name]["properties"]


@pytest.mark.parametrize(("path", "method"), COLLISION_ENDPOINTS)
def test_endpoint_documents_the_409_collision_response(schema, path, method):
    responses = _operation(schema, path, method)["responses"]

    assert "409" in responses, sorted(responses)
    assert "200" in responses, sorted(responses)


@pytest.mark.parametrize(("path", "method"), COLLISION_ENDPOINTS)
def test_409_properties_are_detail_and_code_only(schema, path, method):
    props = _conflict_properties(schema, path, method)

    assert set(props) == {"detail", "code"}


@pytest.mark.parametrize(("path", "method"), COLLISION_ENDPOINTS)
def test_409_does_not_expose_shrine_id(schema, path, method):
    assert "shrine_id" not in _conflict_properties(schema, path, method)


@pytest.mark.parametrize(("path", "method"), COLLISION_ENDPOINTS)
def test_409_does_not_expose_candidates(schema, path, method):
    assert "candidates" not in _conflict_properties(schema, path, method)


def test_both_endpoints_share_one_conflict_schema():
    """同じ 409 契約を 2 箇所で別々に定義しない。"""
    res = APIClient().get(reverse("schema"), {"format": "json"})
    doc = res.json()
    refs = {
        doc["paths"][path][method]["responses"]["409"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        for path, method in (("/api/places/resolve/", "post"), ("/api/shrines/ingest/", "post"))
    }

    assert len(refs) == 1, refs
