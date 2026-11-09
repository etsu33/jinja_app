from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.conf import settings

from temples.services.billing_state import provider
from users.models import UserProfile
from users.services.premium_pass import get_pass_definition

log = logging.getLogger(__name__)

# パスの種類 → Stripe の Price ID を持つ設定の名前（値は環境変数から読む）。
PASS_PRICE_SETTING_BY_TYPE: dict[str, str] = {
    "1d": "STRIPE_PASS_PRICE_ID_1D",
    "7d": "STRIPE_PASS_PRICE_ID_7D",
    "14d": "STRIPE_PASS_PRICE_ID_14D",
}


class UnknownPassType(ValueError):
    """知らないパスの種類が渡された。"""


@dataclass(frozen=True)
class CheckoutSession:
    session_id: str
    checkout_url: str


# Stripe が success_url の中で支払いの ID に置き換える目印。エンコードすると置き換えられない。
STRIPE_CHECKOUT_SESSION_ID_PLACEHOLDER = "{CHECKOUT_SESSION_ID}"


class CheckoutProviderError(RuntimeError):
    """Stripe がチェックアウトの作成で失敗した（値段の ID の誤りなど）。

    応答には決まった文だけを出す。Stripe のエラーの本文（値段の ID などが入りうる）は持たない。
    """


def _with_session_id(url: str, session_id: str) -> str:
    """success_url に checkout_session_id を足す。

    ほかの引数は今までどおりエンコードする。Stripe の目印 {CHECKOUT_SESSION_ID} だけは
    エンコードせずに付ける（Stripe が文字どおりの目印を探して置き換えるため）。
    """
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.pop("checkout_session_id", None)
    encoded = urlencode(query)
    if session_id == STRIPE_CHECKOUT_SESSION_ID_PLACEHOLDER:
        session_param = f"checkout_session_id={STRIPE_CHECKOUT_SESSION_ID_PLACEHOLDER}"
    else:
        session_param = urlencode({"checkout_session_id": session_id})
    new_query = f"{encoded}&{session_param}" if encoded else session_param
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _stripe_pass_price_id(pass_type: str) -> str:
    setting_name = PASS_PRICE_SETTING_BY_TYPE.get(pass_type, "")
    return (getattr(settings, setting_name, "") or "").strip() if setting_name else ""


def _field(obj: Any, name: str) -> str:
    value = getattr(obj, name, None)
    if value is None and isinstance(obj, dict):
        value = obj.get(name)
    return str(value or "")


def create_checkout_session(*, user, pass_type: str, success_url: str, cancel_url: str) -> CheckoutSession:
    """買い切りの旅行パス（1日・7日・14日）のチェックアウトを作る。

    - mode="payment"（自動更新しない）。支払い方法はカードだけ。
    - 客（Customer）を必ず作る（customer_creation="always"）。退会のときに Stripe の客を消す経路で使うため。
    - パスの種類は metadata と payment_intent_data.metadata に入れる。
      期限を延ばすのは Webhook（checkout.session.completed で payment_status が paid のとき）。
    """
    definition = get_pass_definition(pass_type)
    if definition is None:
        raise UnknownPassType(f"unknown pass_type: {pass_type!r}")

    current_provider = provider()

    if current_provider != "stripe":
        session_id = f"stub_checkout_{getattr(user, 'pk', 'anonymous')}"
        return CheckoutSession(
            session_id=session_id,
            checkout_url=_with_session_id(success_url, session_id),
        )

    secret_key = (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
    price_id = _stripe_pass_price_id(definition.pass_type)
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

    metadata = {"user_id": str(user.pk), "pass_type": definition.pass_type}
    params: dict[str, Any] = {
        "mode": "payment",
        "payment_method_types": ["card"],
        "client_reference_id": str(user.pk),
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": _with_session_id(success_url, "{CHECKOUT_SESSION_ID}"),
        "cancel_url": cancel_url,
        "metadata": metadata,
        "payment_intent_data": {"metadata": metadata},
    }
    if customer_id:
        params["customer"] = customer_id
    else:
        # customer_creation は payment / setup のときだけ指定できる（Stripe の仕様）。
        params["customer_creation"] = "always"
        if email:
            params["customer_email"] = email

    try:
        session = stripe.checkout.Session.create(**params)
    except stripe.StripeError as exc:
        # エラーの本文は値段の ID などを含みうるので、ログにも出さない。種類・code・request id だけを残す。
        log.error(
            "[stripe] checkout session create failed error_type=%s code=%s http_status=%s request_id=%s pass_type=%s",
            type(exc).__name__,
            getattr(exc, "code", None),
            getattr(exc, "http_status", None),
            getattr(exc, "request_id", None),
            definition.pass_type,
        )
        raise CheckoutProviderError("stripe checkout session creation failed") from None

    session_id = _field(session, "id")
    checkout_url = _field(session, "url")
    if not session_id or not checkout_url:
        raise RuntimeError("stripe checkout session response is invalid")

    return CheckoutSession(session_id=session_id, checkout_url=checkout_url)
