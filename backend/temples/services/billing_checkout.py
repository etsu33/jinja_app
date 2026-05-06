from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.conf import settings

from temples.services.billing_state import provider
from users.models import UserProfile


@dataclass(frozen=True)
class CheckoutSession:
    session_id: str
    checkout_url: str


def _with_session_id(url: str, session_id: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["checkout_session_id"] = session_id
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _stripe_price_id() -> str:
    return (
        getattr(settings, "STRIPE_PREMIUM_PRICE_ID", "")
        or getattr(settings, "STRIPE_PRICE_ID", "")
        or ""
    ).strip()


def _field(obj: Any, name: str) -> str:
    value = getattr(obj, name, None)
    if value is None and isinstance(obj, dict):
        value = obj.get(name)
    return str(value or "")


def create_checkout_session(*, user, success_url: str, cancel_url: str) -> CheckoutSession:
    current_provider = provider()

    if current_provider != "stripe":
        session_id = f"stub_checkout_{getattr(user, 'pk', 'anonymous')}"
        return CheckoutSession(
            session_id=session_id,
            checkout_url=_with_session_id(success_url, session_id),
        )

    secret_key = (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
    price_id = _stripe_price_id()
    if not secret_key or not price_id:
        raise RuntimeError("stripe checkout is not configured")

    try:
        import stripe  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional deployment package
        raise RuntimeError("stripe sdk is not installed") from exc

    stripe.api_key = secret_key

    profile, _ = UserProfile.objects.get_or_create(user=user)
    customer_id = (getattr(profile, "stripe_customer_id", "") or "").strip()
    email = (getattr(user, "email", "") or "").strip()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id or None,
        customer_email=None if customer_id else (email or None),
        client_reference_id=str(user.pk),
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=_with_session_id(success_url, "{CHECKOUT_SESSION_ID}"),
        cancel_url=cancel_url,
        metadata={"user_id": str(user.pk)},
    )

    session_id = _field(session, "id")
    checkout_url = _field(session, "url")
    if not session_id or not checkout_url:
        raise RuntimeError("stripe checkout session response is invalid")

    return CheckoutSession(session_id=session_id, checkout_url=checkout_url)
