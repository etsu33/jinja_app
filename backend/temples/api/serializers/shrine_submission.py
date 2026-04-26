from __future__ import annotations

from rest_framework import serializers

from temples.models import ShrineSubmission


class ShrineSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShrineSubmission
        fields = [
            "id",
            "name",
            "address",
            "lat",
            "lng",
            "goriyaku_tags",
            "note",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]

    def validate_goriyaku_tags(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("goriyaku_tags は配列で指定してください。")
        return value

    def validate(self, attrs):
        name = (attrs.get("name") or "").strip()
        address = (attrs.get("address") or "").strip()
        lat = attrs.get("lat")
        lng = attrs.get("lng")

        if not name:
            raise serializers.ValidationError({"name": ["この項目は必須です。"]})

        if not address:
            raise serializers.ValidationError({"address": ["この項目は必須です。"]})

        if (lat is None) != (lng is None):
            raise serializers.ValidationError(
                {"non_field_errors": ["lat と lng は両方指定するか、両方省略してください。"]}
            )

        attrs["name"] = name
        attrs["address"] = address
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return ShrineSubmission.objects.create(
            user=user,
            status=ShrineSubmission.Status.PENDING,
            **validated_data,
        )


class ShrineSubmissionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShrineSubmission
        fields = [
            "id",
            "name",
            "address",
            "lat",
            "lng",
            "goriyaku_tags",
            "note",
            "status",
            "created_at",
            "reviewed_at",
            "review_comment",
        ]
        read_only_fields = fields
