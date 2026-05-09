# temples/services/quota_policy.py
from __future__ import annotations

import os
from copy import deepcopy

QUOTA_POLICY = {
    "anonymous": {
        "concierge": {"limit": 3, "unlimited": False},
        "favorite": {"limit": 0, "unlimited": False},
        "goshuin_upload": {"limit": 0, "unlimited": False},
        "shrine_search": {"limit": None, "unlimited": True, "mode": "db_only"},
    },
    "free": {
        "concierge": {"limit": 3, "unlimited": False},
        "favorite": {"limit": 10, "unlimited": False},
        "goshuin_upload": {"limit": 5, "unlimited": False},
        "shrine_search": {"limit": None, "unlimited": True, "mode": "db_only"},
    },
    "premium": {
        "concierge": {"limit": None, "unlimited": True},
        "favorite": {"limit": None, "unlimited": True},
        "goshuin_upload": {"limit": None, "unlimited": True},
        "shrine_search": {"limit": None, "unlimited": True, "mode": "extended"},
    },
}


def _demo_concierge_limit() -> int | None:
    raw = os.getenv("CONCIERGE_DEMO_LIMIT", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def get_feature_policy(plan: str, feature: str) -> dict:
    policy = deepcopy(QUOTA_POLICY[plan][feature])

    demo_limit = _demo_concierge_limit()
    if feature == "concierge" and plan in {"anonymous", "free"} and demo_limit is not None:
        policy["limit"] = demo_limit
        policy["unlimited"] = False

    return policy
