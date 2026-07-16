from rest_framework import serializers
from temples.models import ConciergeThread, ShrineReflection
from temples.services.reflection_state_change import build_reflection_state_change


class ShrineReflectionSerializer(serializers.ModelSerializer):
    shrine_name = serializers.CharField(source="shrine.name_jp", read_only=True)
    shrine_address = serializers.CharField(source="shrine.address", read_only=True)
    thread_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    state_change_direction = serializers.SerializerMethodField()
    state_change_summary = serializers.SerializerMethodField()
    next_need_hint = serializers.SerializerMethodField()
    next_history_theme_hint = serializers.SerializerMethodField()

    class Meta:
        model = ShrineReflection
        fields = [
            "id",
            "user",
            "shrine",
            "shrine_name",
            "shrine_address",
            "thread_id",
            "history_theme",
            "prompt",
            "answer",
            "mood_before",
            "mood_after",
            "created_at",
            "state_change_direction",
            "state_change_summary",
            "next_need_hint",
            "next_history_theme_hint",
        ]
        read_only_fields = ["id", "user", "shrine_name", "shrine_address", "created_at"]

    def validate_thread_id(self, value):
        if value is None:
            return None

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("認証済みユーザーが必要です。")

        if not ConciergeThread.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("指定されたスレッドが見つかりません。")

        return value

    def _state_change(self, obj):
        return build_reflection_state_change(obj)

    def get_state_change_direction(self, obj):
        return self._state_change(obj).state_change_direction

    def get_state_change_summary(self, obj):
        return self._state_change(obj).state_change_summary

    def get_next_need_hint(self, obj):
        return self._state_change(obj).next_need_hint

    def get_next_history_theme_hint(self, obj):
        return self._state_change(obj).next_history_theme_hint
