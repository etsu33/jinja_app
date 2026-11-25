import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from temples.api.views.billing import BillingStatusSerializer
from temples.services.billing_state import get_billing_status
from users.services.apple_billing import apply_apple_notification, apply_apple_purchase
from users.services.apple_storekit import (
    AppleStoreKitInvalid,
    AppleStoreKitUnavailable,
    verify_apple_notification,
    verify_apple_transaction,
)
from users.services.billing import BillingOwnershipConflict

log = logging.getLogger(__name__)


class ApplePurchaseSerializer(serializers.Serializer):
    signed_transaction = serializers.CharField(max_length=65536, trim_whitespace=False)

    def validate(self, attrs):
        if set(self.initial_data) != {"signed_transaction"}:
            raise serializers.ValidationError("Only signed_transaction is accepted.")
        return attrs


class AppleNotificationSerializer(serializers.Serializer):
    signedPayload = serializers.CharField(max_length=262144, trim_whitespace=False)


@extend_schema(
    summary="Register an Apple StoreKit transaction",
    tags=["billing"],
    request=ApplePurchaseSerializer,
    responses={200: BillingStatusSerializer},
)
class ApplePurchaseView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = ApplePurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            purchase = verify_apple_transaction(serializer.validated_data["signed_transaction"])
            apply_apple_purchase(purchase, user=request.user)
        except AppleStoreKitInvalid:
            return Response({"detail": "Invalid Apple transaction."}, status=400)
        except AppleStoreKitUnavailable:
            return Response({"detail": "Apple verification is unavailable."}, status=503)
        except BillingOwnershipConflict:
            return Response(
                {"detail": "Apple purchase is already associated with a billing identity."},
                status=409,
            )

        return Response(BillingStatusSerializer(get_billing_status(user=request.user)).data)


@extend_schema(exclude=True)
class AppleNotificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AppleNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = verify_apple_notification(serializer.validated_data["signedPayload"])
            if notification is not None:
                apply_apple_notification(notification)
        except AppleStoreKitInvalid:
            return Response({"detail": "Invalid Apple notification."}, status=400)
        except AppleStoreKitUnavailable:
            return Response({"detail": "Apple verification is unavailable."}, status=503)
        except BillingOwnershipConflict:
            log.warning("Verified Apple notification conflicts with a local billing identity.")
            return Response(status=409)
        return Response(status=200)
