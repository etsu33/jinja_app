"""Compass MVP API.

See docs/product/compass-product-contract.md and
docs/product/compass-mvp-runtime-contract.md.

Deliberately independent from ConciergeChatView (Runtime Contract Section 6:
"Compass は Phase 4 において独立した新規オーケストレーション層を持つものと
し、既存 ConciergeChatView を実装の簡便さのために流用しない") -- this view
does not import from api_views_concierge.py and does not reuse its
compat-mode heuristics, quota gate, or request-shape resolution. It is a
thin HTTP wrapper around two already-tested pure services:
compass_runtime.build_compass_direction_runtime() and
compass_recommendation_orchestrator.get_compass_recommendations().
"""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from temples.services.compass_recommendation_orchestrator import (
    STATE_INVALID_PURPOSE,
    get_compass_recommendations,
)
from temples.services.compass_runtime import build_compass_direction_runtime

log = logging.getLogger(__name__)


class CompassRecommendationsView(APIView):
    """Compass の主API。month + direction + purpose + origin を受けて、

    Compass Runtime Authority（方向）と Recommendation Authority（神社）の
    両方を1リクエストで解決する。Free/Premium 判定・quota・thread は
    このViewの責務ではない（Phase 5時点でCompassはgatingなし、
    docs/product/compass-mvp-runtime-contractの対象外セクション参照）。
    """

    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    throttle_scope = "compass"

    def post(self, request, *args, **kwargs):
        data = request.data or {}

        purpose = str(data.get("purpose") or "").strip()
        birthdate = str(data.get("birthdate") or "").strip() or None
        target_date = str(data.get("target_date") or "").strip() or None
        raw_origin = data.get("origin")
        origin = raw_origin if isinstance(raw_origin, dict) else None

        try:
            direction_context = build_compass_direction_runtime(
                birthdate=birthdate,
                target_date=target_date,
            )
            result = get_compass_recommendations(
                purpose=purpose,
                origin=origin,
                direction_context=direction_context,
            )
        except Exception:
            log.exception("[compass/recommendations] resolve_failed")
            return Response(
                {"state": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        body = {
            "state": result.state,
            "purpose": result.purpose,
            "direction_context": result.direction_context,
            "recommendations": result.recommendations,
        }

        if result.state == STATE_INVALID_PURPOSE:
            return Response(body, status=status.HTTP_400_BAD_REQUEST)

        return Response(body, status=status.HTTP_200_OK)


__all__ = ["CompassRecommendationsView"]
