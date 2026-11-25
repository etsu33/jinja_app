"""コンシェルジュの結果に添える「今月の方角」（2026-11-26 決定）.

ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」:
- 出すのは、マイページで生年月日を登録したログイン中の人の、日本語の相談のときだけ
- 結果の上に1回だけ month_direction、方角に当たる神社にだけ in_month_direction: true
- 合わない神社には何も付けない。並び順・点数・推薦理由は変えない
- 相談で送られた生年月日（本文・filters・profile_context）は使わない（PR #3464 のまま）
"""

from __future__ import annotations

import datetime
import json

import pytest
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken

from temples.models import Shrine
from temples.services import concierge_month_direction
from temples.services.compass_runtime import NoCommonDirectionResult
from temples.services.concierge_month_direction import (
    build_concierge_month_direction,
    resolve_registered_birthday,
)
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from users.models import UserProfile

TOKYO = {"lat": 35.681236, "lng": 139.767125}
BIRTHDATE = datetime.date(1990, 7, 15)

FIXED_RUNTIME = {
    "targetDate": "2026-11-26",
    "targetYear": 2026,
    "solarMonthIndex": 10,
    "referenceDirections": ["北"],
    "calculationMethod": "annual_monthly_kyusei_v1",
    "note": "年盤と月盤による参考情報です。日盤は使用していません。",
}


class _User:
    def __init__(self, *, authenticated: bool = True, birthday=None, has_profile: bool = True):
        self.is_authenticated = authenticated
        self._birthday = birthday
        self._has_profile = has_profile

    @property
    def profile(self):
        if not self._has_profile:
            raise UserProfile.DoesNotExist
        return type("Profile", (), {"birthday": self._birthday})()


def _recs():
    return [
        {"name": "北の神社", "latitude": TOKYO["lat"] + 0.05, "longitude": TOKYO["lng"]},
        {"name": "南の神社", "latitude": TOKYO["lat"] - 0.05, "longitude": TOKYO["lng"]},
        {"name": "位置なし"},
    ]


@pytest.fixture
def fixed_runtime(monkeypatch):
    calls = []

    def _fake(*, birthdate, target_date):
        calls.append(birthdate)
        return dict(FIXED_RUNTIME)

    monkeypatch.setattr(concierge_month_direction, "build_compass_direction_runtime", _fake)
    return calls


# ---------- 生年月日の読み方 ----------


def test_registered_birthday_only_for_logged_in_users_with_profile_birthday():
    assert resolve_registered_birthday(_User(birthday=BIRTHDATE)) == "1990-07-15"
    assert resolve_registered_birthday(_User(birthday=None)) is None
    assert resolve_registered_birthday(_User(authenticated=False, birthday=BIRTHDATE)) is None
    assert resolve_registered_birthday(_User(has_profile=False)) is None
    assert resolve_registered_birthday(None) is None


# ---------- 添え方 ----------


def test_marks_only_shrines_in_the_month_direction(fixed_runtime):
    recs = _recs()
    result = build_concierge_month_direction(
        user=_User(birthday=BIRTHDATE), language="ja", origin=TOKYO, recommendation_lists=[recs]
    )
    assert result == {
        "reference_directions": ["北"],
        "calculation_method": "annual_monthly_kyusei_v1",
        "target_date": "2026-11-26",
        "note": FIXED_RUNTIME["note"],
    }
    assert recs[0]["in_month_direction"] is True
    # 合わない神社・位置の無い神社には何も付けない（False も付けない）
    assert "in_month_direction" not in recs[1]
    assert "in_month_direction" not in recs[2]
    # 並び順は変えない
    assert [r["name"] for r in recs] == ["北の神社", "南の神社", "位置なし"]
    # 計算にはサーバーのプロフィールの生年月日を使う
    assert fixed_runtime == ["1990-07-15"]


def test_response_never_contains_the_birthday(fixed_runtime):
    result = build_concierge_month_direction(
        user=_User(birthday=BIRTHDATE), language="ja", origin=TOKYO, recommendation_lists=[_recs()]
    )
    assert "1990" not in json.dumps(result, ensure_ascii=False)


def test_without_origin_only_the_month_direction_is_returned(fixed_runtime):
    recs = _recs()
    result = build_concierge_month_direction(
        user=_User(birthday=BIRTHDATE), language="ja", origin=None, recommendation_lists=[recs]
    )
    assert result["reference_directions"] == ["北"]
    assert all("in_month_direction" not in r for r in recs)


@pytest.mark.parametrize(
    "user, language",
    [
        (_User(authenticated=False, birthday=BIRTHDATE), "ja"),
        (_User(birthday=None), "ja"),
        (_User(has_profile=False), "ja"),
        (None, "ja"),
        (_User(birthday=BIRTHDATE), "en"),
    ],
)
def test_nothing_is_added_when_conditions_are_not_met(fixed_runtime, user, language):
    recs = _recs()
    recs[0]["in_month_direction"] = True  # 前の値が残っていても外す
    assert (
        build_concierge_month_direction(
            user=user, language=language, origin=TOKYO, recommendation_lists=[recs]
        )
        is None
    )
    assert all("in_month_direction" not in r for r in recs)


def test_nothing_is_added_when_no_direction_this_month(monkeypatch):
    monkeypatch.setattr(
        concierge_month_direction,
        "build_compass_direction_runtime",
        lambda **_: NoCommonDirectionResult(),
    )
    recs = _recs()
    assert (
        build_concierge_month_direction(
            user=_User(birthday=BIRTHDATE), language="ja", origin=TOKYO, recommendation_lists=[recs]
        )
        is None
    )
    assert all("in_month_direction" not in r for r in recs)


def test_real_kyusei_calculation_returns_valid_directions():
    # 実際の九星の計算（コンパスと同じ）で、8方位のどれかが返ること。
    result = build_concierge_month_direction(
        user=_User(birthday=BIRTHDATE),
        language="ja",
        origin=TOKYO,
        recommendation_lists=[_recs()],
        target_date="2026-11-26",
    )
    if result is not None:
        assert set(result["reference_directions"]) <= {
            "北",
            "北東",
            "東",
            "南東",
            "南",
            "南西",
            "西",
            "北西",
        }
        assert result["calculation_method"] in {"annual_monthly_kyusei_v1", "monthly_kyusei_v1"}


# ---------- 相談の API ----------


def _shrine(name: str, *, lat: float, lng: float) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name, address=f"東京都千代田区{name}", latitude=lat, longitude=lng
    )
    attach_usable_deity_fact(shrine, display_name=f"{name}の祭神")
    return shrine


@pytest.fixture
def shrines(db, settings):
    settings.CONCIERGE_USE_LLM = False
    return [
        _shrine("北の神社", lat=TOKYO["lat"] + 0.02, lng=TOKYO["lng"]),
        _shrine("南の神社", lat=TOKYO["lat"] - 0.02, lng=TOKYO["lng"]),
    ]


def _post(body: dict, user=None):
    headers = {}
    if user is not None:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {RefreshToken.for_user(user).access_token}"
    return Client().post(
        "/api/concierge/chat/",
        data=json.dumps(body),
        content_type="application/json",
        HTTP_HOST="localhost",
        **headers,
    )


def _ranking(response) -> list:
    return [
        (rec["name"], rec.get("_score_total"), rec.get("reason"))
        for rec in response.json()["data"]["recommendations"]
    ]


@pytest.mark.django_db
def test_api_adds_month_direction_for_registered_user_without_changing_ranking(
    shrines, fixed_runtime, django_user_model
):
    registered = django_user_model.objects.create_user(
        username="month_dir_registered", password="x"
    )
    UserProfile.objects.update_or_create(
        user=registered, defaults={"birthday": BIRTHDATE, "nickname": "a"}
    )
    unregistered = django_user_model.objects.create_user(
        username="month_dir_unregistered", password="x"
    )

    body = {"query": "休みたい", **TOKYO}
    with_birthday = _post(body, registered)
    without_birthday = _post(body, unregistered)
    anonymous = _post(body)

    assert with_birthday.status_code == without_birthday.status_code == anonymous.status_code == 200
    payload = with_birthday.json()
    assert payload["month_direction"]["reference_directions"] == ["北"]
    marked = {
        rec["name"]: rec.get("in_month_direction") for rec in payload["data"]["recommendations"]
    }
    assert marked.get("北の神社") is True
    assert "in_month_direction" not in next(
        rec for rec in payload["data"]["recommendations"] if rec["name"] == "南の神社"
    )

    # 生年月日が無い人・ログインしていない人には出さない
    assert "month_direction" not in without_birthday.json()
    assert "month_direction" not in anonymous.json()
    # 並び順・点数・推薦理由は変わらない
    assert _ranking(with_birthday) == _ranking(without_birthday) == _ranking(anonymous)


@pytest.mark.django_db
def test_api_ignores_birthdate_sent_in_the_request(shrines, fixed_runtime):
    response = _post(
        {
            "query": "休みたい",
            **TOKYO,
            "birthdate": "1990-07-15",
            "profile_context": {"user_profile": {"birthday": "1990-07-15"}},
        }
    )
    assert response.status_code == 200
    assert "month_direction" not in response.json()
    assert fixed_runtime == []
