from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.models import Shrine
from temples.services.behavior_funnel import get_behavior_funnel_metrics


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f"Invalid datetime: {value}")
    return parsed


class DebugBehaviorFunnelView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            shrine_id_raw = request.query_params.get("shrine_id")
            shrine_id = int(shrine_id_raw) if shrine_id_raw else None
            from_dt = _parse_optional_datetime(request.query_params.get("from"))
            to_dt = _parse_optional_datetime(request.query_params.get("to"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        if shrine_id is not None and not Shrine.objects.filter(id=shrine_id).exists():
            return Response({"detail": "Shrine not found."}, status=404)

        metrics = get_behavior_funnel_metrics(
            shrine_id=shrine_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )

        return Response(asdict(metrics))
