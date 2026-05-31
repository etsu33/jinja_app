from rest_framework import serializers
from temples.models import Visit


class VisitSerializer(serializers.ModelSerializer):
    shrine_name = serializers.CharField(source="shrine.name", read_only=True)
    shrine_address = serializers.CharField(source="shrine.address", read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id",
            "user",
            "shrine",
            "shrine_name",
            "shrine_address",
            "visited_at",
            "note",
            "status",
        ]
