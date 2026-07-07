from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.api.serializers.journey import JourneyEventSerializer
from temples.services.journey_timeline import build_journey_timeline


class JourneyTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        events = build_journey_timeline(request.user)
        serializer = JourneyEventSerializer(events, many=True)
        return Response({"results": serializer.data})
