from rest_framework import serializers


class JourneyEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    event_type = serializers.ChoiceField(
        choices=[
            "consultation_created",
            "recommendation_shown",
            "visit_completed",
            "reflection_created",
        ]
    )
    occurred_at = serializers.DateTimeField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    thread_id = serializers.IntegerField(allow_null=True)
    shrine_id = serializers.IntegerField(allow_null=True)
    shrine_name = serializers.CharField(allow_null=True)
    metadata = serializers.DictField()
