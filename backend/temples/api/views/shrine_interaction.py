

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.api.serializers.shrine_interaction import (
    ShrineInteractionLogCreateSerializer,
    ShrineInteractionLogResponseSerializer,
)


class ShrineInteractionLogCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["shrine-interactions"],
        summary="Create shrine interaction log",
        request=ShrineInteractionLogCreateSerializer,
        responses={201: ShrineInteractionLogResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = ShrineInteractionLogCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        log = serializer.save()
        response_serializer = ShrineInteractionLogResponseSerializer(log)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
