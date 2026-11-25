from __future__ import annotations

import logging
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import PremiumPassPurchase, UserProfile
from users.services.premium_pass import (
    get_pass_definition,
    grant_premium_pass,
    revoke_premium_pass_for_refund,
)

log = logging.getLogger(__name__)
User = get_user_model()


class StripeWebhookError(RuntimeError):
    pass


class StripeWebhookNotConfigured(StripeWebhookError):
    pass


class StripeWebhookInvalidSignature(StripeWebhookError):
    pass


def _stripe_object_to_plain(value: Any) -> Any:
    """Convert StripeObject-like values into plain Python containers.

    Stripe SDK versions may return nested StripeObject instances even when the
    top-level event behaves like a dict. The webhook handlers expect plain dicts,
    so normalize recursively before reading data.object / metadata.
    """
    if isinstance(value, dict):
        return {str(k): _stripe_object_to_plain(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_stripe_object_to_plain(v) for v in value]

    if hasattr(value, "to_dict_recursive"):
        try:
            return _stripe_object_to_plain(value.to_dict_recursive())
        except Exception:
            pass

    if hasattr(value, "to_dict"):
        try:
            return _stripe_object_to_plain(value.to_dict())
        except Exception:
            pass

    return value


def construct_stripe_event(*, payload: bytes, sig_header: str) -> dict[str, Any]:
    """
    Verify Stripe webhook signature and return a plain event dict.
    """
    try:
        import stripe  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional deployment package
        raise StripeWebhookNotConfigured("stripe sdk is not installed") from exc

    webhook_secret = (getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or "").strip()
    if not webhook_secret:
        raise StripeWebhookNotConfigured("STRIPE_WEBHOOK_SECRET is missing")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError as exc:
        raise StripeWebhookInvalidSignature("invalid stripe signature") from exc
    except ValueError as exc:
        raise StripeWebhookInvalidSignature("invalid stripe payload") from exc

    plain_event = _stripe_object_to_plain(event)
    if isinstance(plain_event, dict):
        return plain_event

    return {"type": getattr(event, "type", None), "data": {}}


def _get_event_type(event: dict[str, Any]) -> str:
    event_dict = _stripe_object_to_plain(event)
    if not isinstance(event_dict, dict):
        return ""
    t = event_dict.get("type")
    return t if isinstance(t, str) else ""


def _get_object(event: dict[str, Any]) -> dict[str, Any]:
    event_dict = _stripe_object_to_plain(event)
    if not isinstance(event_dict, dict):
        return {}

    data = _stripe_object_to_plain(event_dict.get("data") or {})
    if not isinstance(data, dict):
        return {}

    obj = _stripe_object_to_plain(data.get("object") or {})
    return obj if isinstance(obj, dict) else {}


def _extract_user_id_from_checkout_session(obj: dict[str, Any]) -> Optional[int]:
    # 1) metadata.user_id
    md = obj.get("metadata")
    if isinstance(md, dict):
        v = md.get("user_id")
        try:
            if isinstance(v, str) and v.strip():
                return int(v.strip())
        except Exception:
            pass

    # 2) client_reference_id
    v = obj.get("client_reference_id")
    try:
        if isinstance(v, str) and v.strip():
            return int(v.strip())
    except Exception:
        pass

    return None



def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _as_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


@transaction.atomic
def apply_stripe_event(*, event: dict[str, Any]) -> None:
    """
    Stripe event(dict) を受けて、買い切りの旅行パスの購入・返金を反映する。

    - checkout.session.completed（mode=payment、payment_status=paid）: 期限を延ばす。
    - charge.refunded（全額返金）: そのパスの日数を期限から引く。一部返金は何もしない（Stripe 側の記録だけ）。
    - 月額の自動更新（mode=subscription、customer.subscription.*）は扱わない。
    """
    etype = _get_event_type(event)
    obj = _get_object(event)
    if not etype or not obj:
        return

    if etype == "checkout.session.completed":
        _apply_checkout_session_completed(obj)
        return

    if etype == "charge.refunded":
        _apply_charge_refunded(obj)
        return

    return


def _apply_checkout_session_completed(obj: dict[str, Any]) -> None:
    """
    checkout.session.completed（買い切りの旅行パス）:
    - mode が payment で、payment_status が paid のときだけ期限を延ばす（Stripe の推奨どおり）。
      支払い方法はカードだけに絞っているので、遅れて確定する支払いは扱わない。
    - 客（customer）の ID を profile に保存する（退会のときに Stripe の客を消すため）。
    - パスの日数はサーバー側の表（metadata.pass_type）から決める。
    """
    if _as_str(obj.get("mode")) != "payment":
        return

    session_id = _as_str(obj.get("id"))
    user_id = _extract_user_id_from_checkout_session(obj)
    payment_status = _as_str(obj.get("payment_status"))

    if payment_status != "paid":
        log.warning(
            "[stripe] checkout session not paid session=%s status=%s",
            session_id,
            payment_status or None,
        )
        return

    if not session_id or user_id is None:
        log.warning("[stripe] checkout session missing id or user session=%s", session_id or None)
        return

    user = User.objects.filter(id=user_id).first()
    if user is None:
        log.warning("[stripe] checkout session user not found session=%s", session_id)
        return

    metadata = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    definition = get_pass_definition(metadata.get("pass_type"))
    if definition is None:
        log.error("[stripe] checkout session has unknown pass_type session=%s", session_id)
        return

    customer_id = _as_str(obj.get("customer"))
    if customer_id:
        profile, _ = UserProfile.objects.select_for_update().get_or_create(user=user)
        # 事故防止: 既に埋まってるなら上書きしない
        if not (profile.stripe_customer_id or "").strip():
            profile.stripe_customer_id = customer_id
            profile.save(update_fields=["stripe_customer_id", "updated_at"])

    grant_premium_pass(
        user=user,
        days=definition.days,
        source=PremiumPassPurchase.SOURCE_STRIPE,
        external_id=session_id,
        pass_type=definition.pass_type,
        amount=_as_int(obj.get("amount_total")),
        currency=_as_str(obj.get("currency")),
        payment_intent_id=_as_str(obj.get("payment_intent")),
    )


def _apply_charge_refunded(obj: dict[str, Any]) -> None:
    """
    charge.refunded:
    - 全額返金（refunded=true、または amount_refunded >= amount）のときだけ、パスの日数を期限から引く。
    - 一部返金は期限を変えない（Stripe 側に記録が残る）。
    """
    payment_intent_id = _as_str(obj.get("payment_intent"))
    if not payment_intent_id:
        return

    amount = _as_int(obj.get("amount"))
    amount_refunded = _as_int(obj.get("amount_refunded"))
    fully_refunded = obj.get("refunded") is True or (
        amount is not None and amount_refunded is not None and amount > 0 and amount_refunded >= amount
    )
    if not fully_refunded:
        log.info("[stripe] partial refund recorded only payment_intent=%s", payment_intent_id)
        return

    revoke_premium_pass_for_refund(
        source=PremiumPassPurchase.SOURCE_STRIPE,
        payment_intent_id=payment_intent_id,
    )
