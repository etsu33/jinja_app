from rest_framework import serializers
from temples.models import ConciergeThread, Visit


class VisitSerializer(serializers.ModelSerializer):
    shrine_name = serializers.CharField(source="shrine.name_jp", read_only=True)
    shrine_address = serializers.CharField(source="shrine.address", read_only=True)
    thread_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    class Meta:
        model = Visit
        fields = [
            "id",
            "user",
            "shrine",
            "shrine_name",
            "shrine_address",
            "thread_id",
            "visited_at",
            "note",
            "status",
        ]

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
