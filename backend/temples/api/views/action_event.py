from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.api.serializers.action_event import (
    ActionEventCreateSerializer,
    ActionEventResponseSerializer,
)


class ActionEventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["action-events"],
        summary="Create action event",
        request=ActionEventCreateSerializer,
        responses={201: ActionEventResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = ActionEventCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        response_serializer = ActionEventResponseSerializer(event)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
