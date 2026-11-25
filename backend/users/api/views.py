# users/api/views.py
from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from temples.models import GoshuinImage
from temples.api.views.billing import BillingStripeWebhookView
from users.models import UserProfile
from users.services.account_deletion import (
    AccountDataDeletionFailed,
    BillingCleanupFailed,
    BillingCustomerCleanupFailed,
    BillingStateSyncFailed,
    delete_user_account,
)

from .serializers import SignupSerializer, UserMeSerializer, UserProfileUpdateSerializer

log = logging.getLogger(__name__)


# アカウント削除失敗時の共通レスポンス。
# 内部のどの段階で止まったかは出さない（課金状態などが推測できてしまうため）。
ACCOUNT_DELETION_UNAVAILABLE_CODE = "account_deletion_unavailable"
ACCOUNT_DELETION_UNAVAILABLE_BODY = {
    "code": ACCOUNT_DELETION_UNAVAILABLE_CODE,
    "detail": "アカウント削除を完了できませんでした。時間をおいて再度お試しください。",
}


class AccountDeletionUnavailableSerializer(serializers.Serializer):
    """503 の schema 定義。実レスポンスは上の定数をそのまま返す。"""

    code = serializers.CharField()
    detail = serializers.CharField()


def _storage_limit_bytes() -> int:
    return int(getattr(settings, "STORAGE_LIMIT_BYTES", 200 * 1024 * 1024))


class MeStorageResponseSerializer(serializers.Serializer):
    total_bytes = serializers.IntegerField()
    total_images = serializers.IntegerField()
    limit_bytes = serializers.IntegerField()
    remaining_bytes = serializers.IntegerField()
    is_over_limit = serializers.BooleanField()


class MeStorageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="api_users_me_storage_retrieve",
        responses={200: MeStorageResponseSerializer},
        tags=["users"],
    )
    def get(self, request):
        qs = GoshuinImage.objects.filter(goshuin__user=request.user)
        agg = qs.aggregate(total_bytes=Sum("size_bytes"), total_images=Count("id"))

        total_bytes = int(agg["total_bytes"] or 0)
        total_images = int(agg["total_images"] or 0)

        limit_bytes = _storage_limit_bytes()
        remaining_bytes = max(0, limit_bytes - total_bytes)
        is_over_limit = total_bytes > limit_bytes

        return Response(
            {
                "total_bytes": total_bytes,
                "total_images": total_images,
                "limit_bytes": limit_bytes,
                "remaining_bytes": remaining_bytes,
                "is_over_limit": is_over_limit,
            }
        )


class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        summary="Get current user profile",
        responses={200: UserMeSerializer},
        tags=["users"],
    )
    def get(self, request):
        UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"nickname": request.user.username, "is_public": False},
        )
        user = type(request.user).objects.select_related("profile").get(pk=request.user.pk)
        return Response(UserMeSerializer(user, context={"request": request}).data)

    @extend_schema(
        summary="Update current user profile",
        request=UserProfileUpdateSerializer,
        responses={200: UserMeSerializer},
        tags=["users"],
    )
    def patch(self, request):
        prof, _ = UserProfile.objects.get_or_create(user=request.user)
        ser = UserProfileUpdateSerializer(prof, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

        user = type(request.user).objects.select_related("profile").get(pk=request.user.pk)
        return Response(UserMeSerializer(user, context={"request": request}).data)

    @extend_schema(
        summary="Delete current user account",
        description=(
            "Delete the authenticated user's account. Stripe billing is stopped first; "
            "if any step cannot be completed the account is left intact and 503 is returned."
        ),
        request=None,
        responses={
            204: OpenApiResponse(description="Account deleted."),
            503: OpenApiResponse(
                response=AccountDeletionUnavailableSerializer,
                description=(
                    "Deletion could not be completed. The account still exists and the "
                    "request can be retried. The response intentionally does not reveal "
                    "which internal step failed."
                ),
            ),
        },
        tags=["users"],
    )
    def delete(self, request):
        """アカウント削除。

        この view は薄く保つ。削除の順序・Stripe 呼び出し・DB 削除・Storage cleanup は
        すべて `users.services.account_deletion` が正本で、ここでは再実装しない。

        失敗時は内部のどの段階で止まったかを区別せず、単一の 503 へ畳む。
        段階を出し分けると「課金は止まったが Account は残っている」といった
        内部状態が外部から推測できてしまうため。調査に必要な情報は service 側が
        ERROR log へ残している。
        """
        try:
            delete_user_account(user=request.user)
        except (
            BillingCleanupFailed,
            BillingStateSyncFailed,
            BillingCustomerCleanupFailed,
            AccountDataDeletionFailed,
        ):
            # raw exception 本文・Stripe ID・email・secret は返さない。
            # `from None` は付けない（service 側で既に cause は切られている）。
            return Response(
                ACCOUNT_DELETION_UNAVAILABLE_BODY,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class SignupResponse(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class SignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Signup",
        request=SignupSerializer,
        responses={201: SignupResponse},
        tags=["users"],
    )
    def post(self, request):
        s = SignupSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

        # Signup は「User 作成」と「必須 UserProfile 生成」で 1 つのユースケース。
        # UserProfile は User の post_save signal（users.apps.ensure_profile）が
        # 作るため、User の INSERT まで rollback 対象に含める必要がある。
        # signal だけを atomic にしても User は残ってしまうので、境界は save() に置く。
        with transaction.atomic():
            user = s.save()

        return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)


@extend_schema(exclude=True)
@csrf_exempt
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    return BillingStripeWebhookView.as_view()(request)
