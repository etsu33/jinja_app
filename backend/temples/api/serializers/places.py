from rest_framework import serializers


class PlaceItemSerializer(serializers.Serializer):
    place_id = serializers.CharField()
    name = serializers.CharField(allow_null=True, required=False)
    address = serializers.CharField(allow_null=True, required=False)
    lat = serializers.FloatField(allow_null=True, required=False)
    lng = serializers.FloatField(allow_null=True, required=False)
    types = serializers.ListField(child=serializers.CharField(), required=False)


class PlacesSearchResponse(serializers.Serializer):
    results = PlaceItemSerializer(many=True, required=False)
    cached = serializers.BooleanField(required=False)
    provider = serializers.CharField(required=False)


class TextSearchResponse(PlacesSearchResponse):
    pass


class NearbySearchResponse(PlacesSearchResponse):
    pass


class PlaceDetailResponse(serializers.Serializer):
    place_id = serializers.CharField()
    name = serializers.CharField(allow_null=True, required=False)
    address = serializers.CharField(allow_null=True, required=False)
    rating = serializers.FloatField(allow_null=True, required=False)
    user_ratings_total = serializers.IntegerField(allow_null=True, required=False)
    types = serializers.ListField(child=serializers.CharField(), required=False)
    location = serializers.DictField(child=serializers.FloatField(), required=False)
    photo_reference = serializers.CharField(required=False, allow_blank=True)


class PlacePhotoResponse(serializers.Serializer):
    url = serializers.CharField(required=False)


class PlaceLiteSerializer(serializers.Serializer):
    place_id = serializers.CharField()
    name = serializers.CharField(allow_blank=True, required=False)
    address = serializers.CharField(allow_null=True, required=False)
    lat = serializers.FloatField(allow_null=True, required=False)
    lng = serializers.FloatField(allow_null=True, required=False)
    types = serializers.ListField(child=serializers.CharField(), required=False)


class PlaceLiteResponseSerializer(serializers.Serializer):
    results = PlaceLiteSerializer(many=True)


class ShrineCollisionConflictSerializer(serializers.Serializer):
    """F-6B: place_id 解決が collision で拒否されたときの 409 body。

    `POST /api/places/resolve/` と `POST /api/shrines/ingest/` の両方が
    この形を返す。

    候補 Shrine の id は **意図的に含めない**。含めると client 側が
    「候補が 1 件だから」と自動束縛しうるため
    （AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED）。レビューは server log。

    docs/audit/place-id-shadow-identity-hardening.md §14.5
    """

    detail = serializers.CharField()
    code = serializers.CharField(help_text="shrine_collision_review_required")


class ShrineIngestRequestSerializer(serializers.Serializer):
    """F-6B: `POST /api/shrines/ingest/` の request body（schema 記述用）。"""

    place_id = serializers.CharField()
