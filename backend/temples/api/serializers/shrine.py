from typing import Optional

from rest_framework import serializers
from drf_spectacular.utils import OpenApiTypes, extend_schema_field

from temples.geo_utils import to_lat_lng_dict
from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
    Visit,
)
from temples.services import evidence_gate
from temples.services.collective_runtime_selector import fetch_runtime_admitted_collectives

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


def _fact_ready_sources(obj) -> list[ShrineKnowledgeSource]:
    """関連Sourceのうちfact-readyなものだけを返す。

    View側のPrefetchで既に絞り込まれている場合はそのまま、Serializerが
    Prefetchを経由せず単独で呼ばれた場合（例: 単体テスト）でも同じ結果になるよう、
    ここでも明示的にevidence_gateの基準でフィルタする。
    """
    return [
        s
        for s in obj.sources.all()
        if s.verification_status in evidence_gate.FACT_READY_VERIFICATION_STATUSES
    ]


class ShrineDeitySerializer(serializers.ModelSerializer):
    """docs/knowledge/shrine-knowledge-contract.md「deity契約」のRead専用表示。"""

    sources = serializers.SerializerMethodField(read_only=True)

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

    @extend_schema_field(ShrineKnowledgeSourceSerializer(many=True))
    def get_sources(self, obj):
        return ShrineKnowledgeSourceSerializer(
            _fact_ready_sources(obj), many=True, context=self.context
        ).data


class ShrineHistorySerializer(serializers.ModelSerializer):
    """docs/knowledge/shrine-knowledge-contract.md「shrine_history契約」のRead専用表示。"""

    sources = serializers.SerializerMethodField(read_only=True)

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

    @extend_schema_field(ShrineKnowledgeSourceSerializer(many=True))
    def get_sources(self, obj):
        return ShrineKnowledgeSourceSerializer(
            _fact_ready_sources(obj), many=True, context=self.context
        ).data


# --- A6-02: admitted Collective（temples.services.collective_runtime_selector）の Read 専用表示 ---
# 入力は selector が admission 済みにした AdmittedCollective / AdmittedCollectiveMembership
# （frozen dataclass）であり、model instance ではない。Serializer は属性を写像するだけで、
# Evidence Gate の再判定・admission の再計算・DB アクセスを行わない。Sources はこの段階では出さない。


class _CollectiveMembershipDeitySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="deity_id", read_only=True)
    display_name = serializers.CharField(source="deity_display_name", read_only=True)


class ShrineDeityCollectiveMembershipSerializer(serializers.Serializer):
    """AdmittedCollectiveMembership の Read 専用表示。deity は {id, display_name} に入れ子にする。"""

    deity = _CollectiveMembershipDeitySerializer(source="*", read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    confidence = serializers.CharField(read_only=True)


class ShrineDeityCollectiveSerializer(serializers.Serializer):
    """AdmittedCollective の Read 専用表示。ShrineDeitySerializer へ flatten しない。

    memberships の順序は selector が決めた (sort_order, id) 順をそのまま保持する。
    """

    id = serializers.IntegerField(source="collective_id", read_only=True)
    source_attested_label = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    member_count = serializers.IntegerField(read_only=True, allow_null=True)
    member_count_relation = serializers.CharField(read_only=True)
    member_list_status = serializers.CharField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    confidence = serializers.CharField(read_only=True)
    memberships = ShrineDeityCollectiveMembershipSerializer(many=True, read_only=True)


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
            # 一覧側の「新着」表示（Frontend判定）が参照する事実値。
            # Backendはcreated_atという事実を返すだけで、新着かどうかの判定は持たない。
            "created_at",
        ]
        read_only_fields = (
            "latitude",
            "longitude",
            "location",
            "created_at",
            "updated_at",
        )


class ShrineDetailSerializer(ShrineBaseSerializer):
    """Shrine Detail API専用。deities/historiesはtemples.services.evidence_gateの
    decide_detail_display_state()判定（"full"または"disputed"）を満たすものだけを
    返却する（PR-C4B1。"hidden"は返さない）。full/disputedいずれも既存の
    verification_status/confidence/sources fieldのみで表現し、新規fieldは
    追加しない。verification_status="disputed"のFactは、fact-readyなSourceを
    1件以上Relationしていれば返る（本文・Source Relationは加工しない）。
    Recommendation側（shrine_knowledge_selector.pyのdecide_fact_usability()）とは
    別のPolicyであり、disputedの扱いは経路ごとに異なる（PR-C4A Disputed Evidence
    Contractの契約通り、Recommendationはdisputedを常に除外する）。Knowledge未登録時は
    []を返し、Legacy Field（sajin/description）へのfallbackは行わない。

    deity_collectives（A6-02）は temples.services.collective_runtime_selector の
    fetch_runtime_admitted_collectives() が admit した Collective だけを返す。
    Runtime admission の唯一の authority は selector であり、ここでは Evidence Gate の
    再判定・Collective/Membership model への直接 query・deities への flatten を行わない。
    admit された Collective が無ければ [] を返す（null / field 省略はしない）。
    selector は呼び出し1回あたり最大5クエリのため、Detail（単一 Shrine）専用とし、
    ShrineListSerializer 等の複数 Shrine 経路へは接続しない。
    """

    deities = serializers.SerializerMethodField(read_only=True)
    histories = serializers.SerializerMethodField(read_only=True)
    deity_collectives = serializers.SerializerMethodField(read_only=True)

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
            "deity_collectives",
        ]

    @extend_schema_field(ShrineDeitySerializer(many=True))
    def get_deities(self, obj):
        items = [
            d
            for d in obj.deities.all()
            if evidence_gate.decide_detail_display_state(
                verification_status=d.verification_status,
                source_verification_statuses=(s.verification_status for s in d.sources.all()),
            )
            in ("full", "disputed")
        ]
        return ShrineDeitySerializer(items, many=True, context=self.context).data

    @extend_schema_field(ShrineHistorySerializer(many=True))
    def get_histories(self, obj):
        items = [
            h
            for h in obj.histories.all()
            if evidence_gate.decide_detail_display_state(
                verification_status=h.verification_status,
                source_verification_statuses=(s.verification_status for s in h.sources.all()),
            )
            in ("full", "disputed")
        ]
        return ShrineHistorySerializer(items, many=True, context=self.context).data

    @extend_schema_field(ShrineDeityCollectiveSerializer(many=True))
    def get_deity_collectives(self, obj):
        result = fetch_runtime_admitted_collectives([obj.pk])
        admitted = result.get(obj.pk, [])
        return ShrineDeityCollectiveSerializer(admitted, many=True, context=self.context).data


class ShrineIngestResponseSerializer(ShrineDetailSerializer):
    """ShrineViewSet.ingest() の応答。A6-02 以前の Detail 契約（deity_collectives なし）を保持する。

    deity_collectives（A6-02）は Shrine Detail（retrieve）専用であり、ingest へは広げない。
    field 自体を持たないため Collective runtime selector を呼ばない。
    """

    deity_collectives = None

    class Meta(ShrineDetailSerializer.Meta):
        fields = [f for f in ShrineDetailSerializer.Meta.fields if f != "deity_collectives"]


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
    "ShrineDeityCollectiveSerializer",
    "ShrineDeityCollectiveMembershipSerializer",
    "ShrineIngestResponseSerializer",
]
