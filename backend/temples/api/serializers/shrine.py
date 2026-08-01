from typing import Optional

from rest_framework import serializers
from drf_spectacular.utils import OpenApiTypes, extend_schema_field

from temples.geo_utils import to_lat_lng_dict
from temples.models import (
    KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
    Visit,
)

from rest_framework import serializers
from temples.models import GoriyakuTag, Shrine



class GoriyakuTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoriyakuTag
        fields = ["id", "name", "category"]


class ShrineKnowledgeSourceSerializer(serializers.ModelSerializer):
    """docs/knowledge/shrine-knowledge-contract.md「Source契約」のRead専用表示。"""

    class Meta:
        model = ShrineKnowledgeSource
        fields = [
            "id",
            "source_type",
            "title",
            "publisher",
            "url",
            "verification_status",
            "confidence",
        ]
        read_only_fields = fields


class ShrineDeitySerializer(serializers.ModelSerializer):
    """docs/knowledge/shrine-knowledge-contract.md「deity契約」のRead専用表示。"""

    sources = ShrineKnowledgeSourceSerializer(many=True, read_only=True)

    class Meta:
        model = ShrineDeity
        fields = [
            "id",
            "display_name",
            "canonical_name",
            "role",
            "sort_order",
            "verification_status",
            "confidence",
            "sources",
        ]
        read_only_fields = fields


class ShrineHistorySerializer(serializers.ModelSerializer):
    """docs/knowledge/shrine-knowledge-contract.md「shrine_history契約」のRead専用表示。"""

    sources = ShrineKnowledgeSourceSerializer(many=True, read_only=True)

    class Meta:
        model = ShrineHistory
        fields = [
            "id",
            "history_type",
            "title",
            "content",
            "period_text",
            "event_date",
            "sort_order",
            "verification_status",
            "confidence",
            "sources",
        ]
        read_only_fields = fields


class _DistanceFieldsMixin:
    def _distance_m(self, obj) -> Optional[float]:
        d = getattr(obj, "d_m", None)
        if d is None:
            d = getattr(obj, "distance_m", None)
        if d is None:
            d = getattr(obj, "distance", None)
        if d is None:
            return None
        try:
            return float(getattr(d, "m", d))
        except Exception:
            return None

    def get_distance(self, obj) -> Optional[float]:
        m = self._distance_m(obj)
        return None if m is None else round(m, 1)

    def get_distance_text(self, obj) -> Optional[str]:
        m = self._distance_m(obj)
        if m is None:
            return None
        return f"{int(round(m))} m" if m < 1000 else f"{m / 1000:.1f} km"


class ShrineBaseSerializer(_DistanceFieldsMixin, serializers.ModelSerializer):
    goriyaku_tags = GoriyakuTagSerializer(many=True, read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)
    distance = serializers.SerializerMethodField(read_only=True)
    distance_text = serializers.SerializerMethodField(read_only=True)
    location = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_location(self, obj):
        d = to_lat_lng_dict(getattr(obj, "location", None))
        if d is not None:
            return d
        if getattr(obj, "latitude", None) is not None and getattr(obj, "longitude", None) is not None:
            return {"lat": float(obj.latitude), "lng": float(obj.longitude)}
        return None


class ShrineListSerializer(ShrineBaseSerializer):
    class Meta:
        model = Shrine
        fields = [
            "id",
            "kind",
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "goriyaku_tags",
            "is_favorite",
            "distance",
            "distance_text",
            "location",
            "kyusei",
        ]
        read_only_fields = (
            "latitude",
            "longitude",
            "location",
            "created_at",
            "updated_at",
        )


class ShrineDetailSerializer(ShrineBaseSerializer):
    """Shrine Detail API専用。deities/historiesはdocs/knowledge/shrine-knowledge-contract.md
    「Evidence Gate要件」に従い、verification_statusがFact利用可能な状態
    （source_confirmed/reviewed）のもののみ返却する。Knowledge未登録時は[]を返し、
    Legacy Field（sajin/description）へのfallbackは行わない。
    """

    deities = serializers.SerializerMethodField(read_only=True)
    histories = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Shrine
        fields = [
            "id",
            "kind",
            "name_jp",
            "name_romaji",
            "address",
            "latitude",
            "longitude",
            "goriyaku",
            "goriyaku_tags",
            "is_favorite",
            "distance",
            "distance_text",
            "location",
            "kyusei",
            "deities",
            "histories",
        ]

    @extend_schema_field(ShrineDeitySerializer(many=True))
    def get_deities(self, obj):
        items = [
            d
            for d in obj.deities.all()
            if d.verification_status in KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES
        ]
        return ShrineDeitySerializer(items, many=True, context=self.context).data

    @extend_schema_field(ShrineHistorySerializer(many=True))
    def get_histories(self, obj):
        items = [
            h
            for h in obj.histories.all()
            if h.verification_status in KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES
        ]
        return ShrineHistorySerializer(items, many=True, context=self.context).data


# 互換名
ShrineSerializer = ShrineDetailSerializer


class VisitSerializer(serializers.ModelSerializer):
    shrine = ShrineListSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = ["id", "shrine", "visited_at", "note", "status"]

class ShrineWriteSerializer(serializers.ModelSerializer):
    address = serializers.CharField(required=False, allow_blank=True, default="")

    goriyaku_tag_ids = serializers.PrimaryKeyRelatedField(
        source="goriyaku_tags",
        many=True,
        queryset=GoriyakuTag.objects.all(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Shrine
        fields = [
            "kind",
            "name_jp",
            "name_romaji",
            "address",
            "latitude",
            "longitude",
            "goriyaku",
            "sajin",            # ✅ モデルにある
            "description",      # ✅ モデルにある（必要なら）
            "element",          # ✅ モデルにある（必要なら）
            "kyusei",
            "goriyaku_tag_ids",
        ]


__all__ = [
    "ShrineSerializer",
    "ShrineListSerializer",
    "ShrineDetailSerializer",
    "GoriyakuTagSerializer",
    "VisitSerializer",
    "ShrineDeitySerializer",
    "ShrineHistorySerializer",
    "ShrineKnowledgeSourceSerializer",
]
