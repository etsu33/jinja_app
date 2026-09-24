"""F-6B: OpenAPI に collision の 409 が記述されることの回帰。"""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _schema():
    res = APIClient().get(reverse("schema"), {"format": "json"})
    assert res.status_code == 200
    return res.json()


def test_places_resolve_post_documents_the_409_collision_response():
    schema = _schema()
    post = schema["paths"]["/api/places/resolve/"]["post"]

    assert "409" in post["responses"], sorted(post["responses"])
    assert "200" in post["responses"]


def test_409_schema_exposes_detail_and_code_but_no_shrine_id():
    schema = _schema()
    ref = schema["paths"]["/api/places/resolve/"]["post"]["responses"]["409"]
    body = ref["content"]["application/json"]["schema"]
    name = body["$ref"].rsplit("/", 1)[-1]
    props = schema["components"]["schemas"][name]["properties"]

    assert set(props) == {"detail", "code"}
    # AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED: 候補 id を公開契約に載せない。
    assert "shrine_id" not in props
    assert "candidates" not in props
