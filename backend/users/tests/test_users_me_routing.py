# backend/users/tests/test_users_me_routing.py
"""`/api/users/me/` の routing 正本が users_api:me 1本であることの回帰テスト。

以前は shrine_project/urls.py に直接 route（name="users-me"）があり、
users.api.urls 側の users_api:me と同一URL・同一Viewに対する2重登録になっていた。
reverse("users_api:me") だけでは重複を検知できないため、resolve 側と
legacy route name の不在をここで固定する。
"""

import pytest
from django.urls import NoReverseMatch, resolve, reverse
from users.api.views import MeView

ME_URL = "/api/users/me/"


def test_me_reverse_returns_canonical_url():
    assert reverse("users_api:me") == ME_URL


def test_me_resolves_to_users_api_namespace():
    match = resolve(ME_URL)
    assert match.view_name == "users_api:me"
    assert match.url_name == "me"
    assert match.namespaces == ["users_api"]


def test_me_resolves_to_api_me_view():
    assert resolve(ME_URL).func.view_class is MeView


def test_legacy_users_me_route_name_is_gone():
    with pytest.raises(NoReverseMatch):
        reverse("users-me")
