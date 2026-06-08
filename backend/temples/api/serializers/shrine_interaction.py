

from __future__ import annotations

from rest_framework import serializers

from temples.models import ConciergeThread, Shrine, ShrineInteractionLog


class ShrineInteractionLogCreateSerializer(serializers.Serializer):
    shrine_id = serializers.IntegerField(min_value=1)
    action_type = serializers.ChoiceField(choices=ShrineInteractionLog.ActionType.choices)
    source = serializers.CharField(required=False, allow_blank=True, max_length=64)
    thread_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    metadata = serializers.DictField(required=False)

    def validate_shrine_id(self, value: int) -> int:
        if not Shrine.objects.filter(id=value).exists():
            raise serializers.ValidationError("指定された神社が見つかりません。")
        return value

    def validate_thread_id(self, value: int | None) -> int | None:
        if value is None:
            return None

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("認証済みユーザーが必要です。")

        if not ConciergeThread.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("指定されたスレッドが見つかりません。")

        return value

    def create(self, validated_data: dict) -> ShrineInteractionLog:
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return ShrineInteractionLog.objects.create(
            user=user,
            shrine_id=validated_data["shrine_id"],
            action_type=validated_data["action_type"],
            source=validated_data.get("source") or "",
            thread_id=validated_data.get("thread_id"),
            metadata=validated_data.get("metadata") or {},
        )


class ShrineInteractionLogResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShrineInteractionLog
        fields = [
            "id",
            "shrine_id",
            "action_type",
            "source",
            "thread_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
