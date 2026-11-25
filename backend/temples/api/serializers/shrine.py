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
from temples.services import evidence_gate, highlight_publication

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


# A6-02 Step 2: Shrine Detail へ admitted Collective を渡す serializer context key。
# 値は fetch_runtime_admitted_collectives() の戻り値（shrine_id -> list[AdmittedCollective]）。
# View（ShrineViewSet.retrieve）が request ごとに 1 回だけ selector を呼んで格納する。
ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY = "admitted_deity_collectives"


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


# 神社詳細で見どころを出す言語。英語は旅行パス・英語版の画面で使う（今は日本語だけ）。
HIGHLIGHT_DETAIL_LANGUAGE = "ja"


def _detail_displayed_histories(obj) -> list[ShrineHistory]:
    """神社詳細に出す由緒・歴史（full / disputed）。histories と highlights で同じ判定を使う。"""
    return [
        h
        for h in obj.histories.all()
        if evidence_gate.decide_detail_display_state(
            verification_status=h.verification_status,
            source_verification_statuses=(s.verification_status for s in h.sources.all()),
        )
        in ("full", "disputed")
    ]


class ShrineHighlightDetailSerializer(serializers.Serializer):
    """神社詳細の見どころ（Highlights PR-4）。公開判定は highlight_publication で済ませてから渡す。

    - 文章（name / description / historical_connection / location_hint）は承認済みの翻訳から出す
    - sources は公開の根拠になる出典だけ（現地観察は observed_on の日付として別に出す）
    - linked_history_ids は、同じ神社で神社詳細に実際に出ている由緒・歴史の id だけ
    """

    id = serializers.IntegerField()
    category = serializers.CharField()
    sort_order = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    historical_connection = serializers.CharField()
    location_hint = serializers.CharField()
    linked_history_ids = serializers.ListField(child=serializers.IntegerField())
    sources = ShrineKnowledgeSourceSerializer(many=True)
    observed_on = serializers.DateField(allow_null=True)


def build_highlight_detail_items(
    obj, *, language_code: str, displayed_histories: list[ShrineHistory]
) -> list[dict]:
    displayed_history_order = {h.pk: i for i, h in enumerate(displayed_histories)}
    items: list[dict] = []
    highlights = sorted(obj.highlights.all(), key=lambda h: (h.sort_order, h.pk))
    for highlight in highlights:
        decision = highlight_publication.decide_for_highlight(highlight, language_code)
        if not decision.displayable:
            continue
        translation = highlight_publication.find_translation(
            highlight.translations.all(), language_code
        )
        sources = [link.source for link in highlight.source_links.all()]
        linked = sorted(
            {
                link.history_id
                for link in highlight.history_links.all()
                if link.shrine_id == obj.pk and link.history_id in displayed_history_order
            },
            key=displayed_history_order.__getitem__,
        )
        items.append(
            {
                "id": highlight.pk,
                "category": highlight.category,
                "sort_order": highlight.sort_order,
                "name": translation.name,
                "description": translation.description,
                "historical_connection": translation.historical_connection,
                "location_hint": translation.location_hint,
                "linked_history_ids": linked,
                "sources": highlight_publication.public_evidence_sources(sources),
                "observed_on": highlight_publication.latest_observed_on(sources),
            }
        )
    return items


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

    deity_collectives（A6-02 Step 2）は、A6-01 selector
    （temples.services.collective_runtime_selector.fetch_runtime_admitted_collectives）が
    admit した Collective だけを、serializer context
    （ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY）経由で受け取って表示する。Serializer は
    admission を再判定せず、model relation（Shrine.deity_collectives）も読まず、順序も
    並べ替えない。context が無い呼び出し（例: ingest）は [] を返す（fail closed）。
    """

    deities = serializers.SerializerMethodField(read_only=True)
    histories = serializers.SerializerMethodField(read_only=True)
    highlights = serializers.SerializerMethodField(read_only=True)
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
            "highlights",
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
        items = _detail_displayed_histories(obj)
        return ShrineHistorySerializer(items, many=True, context=self.context).data

    @extend_schema_field(ShrineHighlightDetailSerializer(many=True))
    def get_highlights(self, obj):
        items = build_highlight_detail_items(
            obj,
            language_code=HIGHLIGHT_DETAIL_LANGUAGE,
            displayed_histories=_detail_displayed_histories(obj),
        )
        return ShrineHighlightDetailSerializer(items, many=True, context=self.context).data

    @extend_schema_field(ShrineDeityCollectiveSerializer(many=True))
    def get_deity_collectives(self, obj):
        admitted_by_shrine = self.context.get(ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY) or {}
        items = admitted_by_shrine.get(obj.pk, [])
        return ShrineDeityCollectiveSerializer(items, many=True, context=self.context).data


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
    "ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY",
]
