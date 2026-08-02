from __future__ import annotations

import pytest
from django.utils import timezone

from temples.api.serializers.shrine import ShrineDetailSerializer, ShrineListSerializer
from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "Serializer監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_deity(shrine: Shrine, verification_status: str, **kwargs) -> ShrineDeity:
    defaults = dict(display_name="祭神", verification_status=verification_status)
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _create_history(shrine: Shrine, verification_status: str, **kwargs) -> ShrineHistory:
    defaults = dict(
        history_type="official_origin",
        title="由緒",
        content="内容",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineHistory.objects.create(shrine=shrine, **defaults)


def test_shrine_detail_serializer_returns_empty_list_when_no_knowledge():
    shrine = _create_shrine()
    data = ShrineDetailSerializer(shrine).data
    assert data["deities"] == []
    assert data["histories"] == []


def test_shrine_detail_serializer_returns_only_fact_ready_deities():
    shrine = _create_shrine()
    # Evidence Gateはstatus判定に加えてfact-ready Source Relationも要求するため、
    # 全候補へ共通のfact-ready Sourceを付与し、status差だけを検証対象にする。
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="共通出典",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    for verification_status, name in [
        ("source_confirmed", "確認済み祭神"),
        ("reviewed", "レビュー済み祭神"),
        ("draft", "下書き祭神"),
        ("unverified", "未確認祭神"),
        ("disputed", "矛盾祭神"),
        ("outdated", "陳腐化祭神"),
        ("rejected", "却下祭神"),
    ]:
        deity = _create_deity(shrine, verification_status, display_name=name)
        deity.sources.add(source)

    data = ShrineDetailSerializer(shrine).data
    names = {d["display_name"] for d in data["deities"]}
    assert names == {"確認済み祭神", "レビュー済み祭神"}


def test_shrine_detail_serializer_returns_only_fact_ready_histories():
    shrine = _create_shrine()
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="共通出典",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    for verification_status, title in [
        ("source_confirmed", "確認済み由緒"),
        ("draft", "下書き由緒"),
        ("disputed", "矛盾由緒"),
    ]:
        history = _create_history(shrine, verification_status, title=title)
        history.sources.add(source)

    data = ShrineDetailSerializer(shrine).data
    titles = {h["title"] for h in data["histories"]}
    assert titles == {"確認済み由緒"}


def test_shrine_detail_serializer_does_not_fallback_to_legacy_fields():
    shrine = _create_shrine()
    shrine.sajin = "レガシー祭神テキスト"
    shrine.description = "レガシー由緒テキスト"
    shrine.save(update_fields=["sajin", "description"])
    # deities/historiesは未登録のまま

    data = ShrineDetailSerializer(shrine).data
    assert data["deities"] == []
    assert data["histories"] == []
    # sajin/descriptionそのものはShrineDetailSerializerのfieldsに含まれない
    assert "sajin" not in data
    assert "description" not in data


def test_shrine_detail_serializer_includes_nested_sources():
    shrine = _create_shrine()
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式サイト",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(source)

    data = ShrineDetailSerializer(shrine).data
    assert len(data["deities"]) == 1
    sources = data["deities"][0]["sources"]
    assert len(sources) == 1
    assert sources[0]["title"] == "公式サイト"
    assert sources[0]["source_type"] == "shrine_official"


def test_shrine_list_serializer_has_no_knowledge_fields():
    shrine = _create_shrine()
    _create_deity(shrine, "source_confirmed")

    data = ShrineListSerializer(shrine).data
    assert "deities" not in data
    assert "histories" not in data
