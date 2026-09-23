# -*- coding: utf-8 -*-
"""R-4: Compass Monthly OpenAPI が shrine_id を必須・non-null として記述すること。

docs/audit/compass-shrine-id-presence-audit.md §12

R-2（#2952）が identity contract を決定し、R-3（#2953）が Public Projection で
runtime 強制を実装した。本fileはその契約が **OpenAPI/schema 表現側にも反映されて
いる** ことを固定する。

serializer は OpenAPI 記述専用（api_views_compass.py の comment 参照）であり、
本fileは runtime 挙動を検証しない。runtime の fail-closed は
test_compass_public_projection.py / test_compass_recommendations_api.py が担う。
"""

from __future__ import annotations

import json

import pytest
from django.urls import reverse

from temples.api.serializers.compass import CompassRecommendationItemSerializer


# ---------------------------------------------------------------------------
# A / B: serializer field declaration
# ---------------------------------------------------------------------------


def test_serializer_marks_shrine_id_required_and_non_null():
    """A: shrine_id は required=True かつ allow_null=False。"""
    field = CompassRecommendationItemSerializer().fields["shrine_id"]

    assert field.required is True, "shrine_id は required でなければならない（R-2 / R-4）"
    assert field.allow_null is False, "shrine_id は non-null でなければならない（R-2 / R-4）"


def test_serializer_keeps_id_optional_as_compatibility_field():
    """B: `id` は COMPATIBILITY_FIELD として optional のまま。

    identity authority ではないので、必須化しない・削除しない（R-2）。
    """
    fields = CompassRecommendationItemSerializer().fields

    assert "id" in fields, "`id` は互換fieldとして残す（削除しない）"
    assert fields["id"].required is False
    assert fields["id"].allow_null is True


def test_serializer_only_shrine_id_became_required_among_payload_fields():
    """R-4 の影響範囲が shrine_id だけであることの negative guard。

    recommendation_instance_id は View 注入の transport metadata なので
    従来どおり required のまま。それ以外の payload field は optional を維持する。
    """
    fields = CompassRecommendationItemSerializer().fields
    required_fields = {name for name, f in fields.items() if f.required}

    assert required_fields == {"shrine_id", "recommendation_instance_id"}


# ---------------------------------------------------------------------------
# C: generated drf-spectacular schema
# ---------------------------------------------------------------------------


def _compass_item_schema(client) -> dict:
    """生成済み OpenAPI から Compass recommendation item の component を取り出す。"""
    res = client.get(reverse("schema"))
    assert res.status_code == 200

    if "application/json" in res["Content-Type"]:
        schema = res.json()
    else:
        schema = json.loads(res.content.decode("utf-8"))

    components = (schema.get("components") or {}).get("schemas") or {}
    item = components.get("CompassRecommendationItem")
    assert item is not None, (
        "CompassRecommendationItem component が生成schemaに存在しない: "
        f"{sorted(k for k in components if 'Compass' in k)}"
    )
    return item


@pytest.mark.django_db
def test_generated_schema_lists_shrine_id_as_required(client):
    """C-1: 生成schemaの required に shrine_id が含まれる。"""
    item = _compass_item_schema(client)

    assert "shrine_id" in (item.get("required") or []), (
        f"required={item.get('required')!r}"
    )


@pytest.mark.django_db
def test_generated_schema_does_not_describe_shrine_id_as_nullable(client):
    """C-2: 生成schemaが shrine_id を nullable として記述しない。"""
    item = _compass_item_schema(client)
    shrine_id = (item.get("properties") or {}).get("shrine_id") or {}

    assert shrine_id.get("nullable") is not True, f"shrine_id={shrine_id!r}"
    # OpenAPI 3.1 形式（type: [integer, "null"]）でも null を許さないこと。
    declared_type = shrine_id.get("type")
    if isinstance(declared_type, list):
        assert "null" not in declared_type, f"shrine_id.type={declared_type!r}"


@pytest.mark.django_db
def test_generated_schema_keeps_id_optional(client):
    """C-3: `id` は生成schemaでも required に含まれない。"""
    item = _compass_item_schema(client)

    assert "id" in (item.get("properties") or {}), "`id` はschemaに残る"
    assert "id" not in (item.get("required") or [])
