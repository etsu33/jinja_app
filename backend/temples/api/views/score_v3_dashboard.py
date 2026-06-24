from __future__ import annotations

from datetime import datetime

from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.services.concierge_observability import build_score_v3_dashboard_summary


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f"Invalid datetime: {value}")
    return parsed


class ScoreV3DashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            from_dt = _parse_optional_datetime(request.query_params.get("from"))
            to_dt = _parse_optional_datetime(request.query_params.get("to"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        summary = build_score_v3_dashboard_summary(from_dt=from_dt, to_dt=to_dt)
        return Response(summary)
