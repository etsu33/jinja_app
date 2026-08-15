"""Deep Dive Ask API(PR-B5): Thin API Boundary。

docs/product/deep-dive-answer-generation-contract.md §11 API Responsibilityの
実装。readiness判定・question classification・Fact取得・Evidence filtering・
LLM payload構築・provenance決定は一切ここで再実装しない。すべて
temples.services.deep_dive_answer.generate_deep_dive_answer()に委譲し、この
Viewはinput validationとHTTP status/shape変換のみを行う。

HTTP Contract:
  - shrine_idが未存在の神社 -> 404("shrine not found"、既存
    ShrineMeaningView/ShrineReflectionCreateViewの規約と同一)。
  - readiness="not_ready" -> 200(Knowledge不足という正常なProduct State。
    エラーではない。既存ConciergeChatViewのquota超過時と同じ、200+status
    fieldパターン)。
  - Fact 0件(zero-fact short circuit) -> 200(同上、Product State)。
  - LLM呼び出し失敗/未有効化 -> 200(generate_deep_dive_answer()が既に
    fixed messageへdeterministicに縮退させている。API層で追加のerror
    statusを割り当てない -- provider failureはこの機能の設計上、常に
    安全なanswer状態として現れ、HTTP例外にならない)。
  - request validation error(shrine_id欠如/型不正、question欠如、不正な
    JSON body) -> 400(DRFの標準serializer validation / parser挙動)。
  - 上記以外の予期しない例外 -> 500("detail"のみ、ShrineMeaningViewと同一
    パターン)。
"""

from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from temples.api.serializers.deep_dive import (
    DeepDiveAskRequestSerializer,
    DeepDiveAskResponseSerializer,
)
from temples.models import Shrine
from temples.services.deep_dive_answer import DeepDiveAnswer, generate_deep_dive_answer

log = logging.getLogger(__name__)


def _serialize_answer(result: DeepDiveAnswer) -> dict:
    """generate_deep_dive_answer()の戻り値をstable public JSON shapeへ変換する。

    値そのものの再解釈は行わない(型変換のみ): readiness/answer/question_type/
    limitations/unanswered_aspectsはそのまま、facts_used/sources_usedは
    frozen dataclassをdictへ変換するのみで、フィールドの追加・削除・意味変更は
    行わない(facts_used/sources_usedは元々、内部専用field(verification_status/
    confidence/content等)を持たないOutput Contract専用の型)。
    """
    return {
        "answer": result.answer,
        "readiness": result.readiness,
        "question_type": list(result.question_type),
        "facts_used": [
            {"type": f.type, "id": f.id, "label": f.label} for f in result.facts_used
        ],
        "sources_used": [
            {
                "id": s.id,
                "title": s.title,
                "publisher": s.publisher,
                "source_type": s.source_type,
                "url": s.url,
            }
            for s in result.sources_used
        ],
        "limitations": result.limitations,
        "unanswered_aspects": list(result.unanswered_aspects),
    }


class DeepDiveAskView(APIView):
    """POST /api/deep-dive/ask/ -- shrine_id + question -> Deep Dive answer。"""

    permission_classes = [AllowAny]
    throttle_scope = "deep_dive"

    @extend_schema(
        request=DeepDiveAskRequestSerializer,
        responses={200: DeepDiveAskResponseSerializer},
        tags=["DeepDive"],
        summary="Deep Dive answer generation",
    )
    def post(self, request, *args, **kwargs):
        serializer = DeepDiveAskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shrine_id = serializer.validated_data["shrine_id"]
        question = serializer.validated_data["question"]

        try:
            shrine = Shrine.objects.get(pk=shrine_id)
        except Shrine.DoesNotExist:
            return Response({"detail": "shrine not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = generate_deep_dive_answer(shrine_id=shrine.id, question_text=question)
        except Exception:
            log.exception("[deep_dive_ask] generate_deep_dive_answer raised unexpectedly")
            return Response(
                {"detail": "deep dive answer generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(_serialize_answer(result), status=status.HTTP_200_OK)


__all__ = ["DeepDiveAskView"]
