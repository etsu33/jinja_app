from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.models import Shrine
from temples.services.shrine_meaning_composer import compose_shrine_meaning_payload


class ShrineMeaningView(APIView):
    """Return ShrineMeaningPayloadV2 for a shrine detail page."""

    permission_classes = [AllowAny]
    throttle_scope = "shrines"

    def get(self, request, pk: int, *args, **kwargs):
        shrine = Shrine.objects.filter(pk=pk).first()
        if shrine is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            payload = compose_shrine_meaning_payload(shrine)
        except Exception:
            return Response(
                {"detail": "meaning payload generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(payload, status=status.HTTP_200_OK)
