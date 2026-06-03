
from rest_framework import serializers
from temples.models import ShrineReflection


class ShrineReflectionSerializer(serializers.ModelSerializer):
    shrine_name = serializers.CharField(source="shrine.name_jp", read_only=True)
    shrine_address = serializers.CharField(source="shrine.address", read_only=True)

    class Meta:
        model = ShrineReflection
        fields = [
            "id",
            "user",
            "shrine",
            "shrine_name",
            "shrine_address",
            "history_theme",
            "prompt",
            "answer",
            "mood_before",
            "mood_after",
            "created_at",
        ]
        read_only_fields = ["id", "user", "shrine_name", "shrine_address", "created_at"]
