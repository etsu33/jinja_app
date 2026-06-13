from __future__ import annotations

from rest_framework import serializers

from temples.models import ActionEvent, ConciergeThread, Shrine


class ActionEventCreateSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(choices=ActionEvent.ActionType.choices)
    action_suggestion_id = serializers.CharField(max_length=128)
    history_theme = serializers.CharField(required=False, allow_blank=True, max_length=32)
    action_category = serializers.CharField(required=False, allow_blank=True, max_length=32)
    source = serializers.CharField(required=False, allow_blank=True, max_length=64)
    shrine_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    thread_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    metadata = serializers.DictField(required=False)

    def validate_shrine_id(self, value: int | None) -> int | None:
        if value is None:
            return None
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

    def create(self, validated_data: dict) -> ActionEvent:
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return ActionEvent.objects.create(
            user=user,
            action_type=validated_data["action_type"],
            action_suggestion_id=validated_data["action_suggestion_id"],
            history_theme=validated_data.get("history_theme") or "",
            action_category=validated_data.get("action_category") or "",
            source=validated_data.get("source") or "",
            shrine_id=validated_data.get("shrine_id"),
            thread_id=validated_data.get("thread_id"),
            metadata=validated_data.get("metadata") or {},
        )


class ActionEventResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionEvent
        fields = [
            "id",
            "action_type",
            "action_suggestion_id",
            "history_theme",
            "action_category",
            "source",
            "shrine_id",
            "thread_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
